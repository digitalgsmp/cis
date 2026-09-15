#!/usr/bin/env python3
"""
apply_gate.py — R6: the deterministic apply gate. The SOLE writer to the repo.

This is the verifier. It is CODE, not an LLM. It applies a Menter patch into the
repo ONLY when ALL conditions are already recorded as spine rows or verified here:

  (a) both review1 (8643) and review2 (8647) returned CONSENSUS_REACHED;
  (b) the diff touches ONLY files declared in workflow_runs.card_scope;
  (c) the patch APPLIES cleanly (git apply --check);
  (d) every emitted Python file COMPILES (py_compile).

No rows / no clean apply / no compile -> BLOCK, no write, and a spine row records
the refusal. A model cannot argue with it; it checks rows and refuses otherwise.

MUST run as root or a privileged control-plane user — never inside the worker
container (where the repo is read-only to agents).

Usage:
  python3 tools/pipeline/apply_gate.py --run-id <id>
"""

import argparse
import fnmatch
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
REPO_ROOT = os.environ.get("CIS_APPLY_REPO_ROOT", "/mnt/projects/cis")


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def resolve_proposal_id(run_id, db):
    row = db.execute(
        "SELECT DISTINCT proposal_id FROM lifecycle_events "
        "WHERE workflow_run_id = ? ORDER BY id DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    return row["proposal_id"] if row else None


def resolve_session_id(run_id, db):
    row = db.execute(
        "SELECT session_id FROM lifecycle_events "
        "WHERE workflow_run_id = ? AND session_id IS NOT NULL "
        "ORDER BY id DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    if row and row["session_id"]:
        return row["session_id"]
    return datetime.now(timezone.utc).isoformat()


def gate_hash():
    p = os.path.realpath(__file__)
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def dual_consensus(run_id, db):
    rows = db.execute(
        "SELECT reviewer_role, reviewer_signal FROM deliberation_rounds "
        "WHERE run_id = ? AND reviewer_role IN ('review1','review2') "
        "ORDER BY id DESC",
        (run_id,),
    ).fetchall()
    sig = {}
    for r in rows:
        sig.setdefault(r["reviewer_role"], r["reviewer_signal"])
    return sig.get("review1") == "CONSENSUS_REACHED" and \
           sig.get("review2") == "CONSENSUS_REACHED"


def files_touched_by_patch(patch_path):
    """Return repo-relative paths the patch would touch, parsed from diff headers."""
    touched = []
    try:
        for line in open(patch_path, errors="replace"):
            if line.startswith("diff --git "):
                # diff --git a/<path> b/<path>
                parts = line.strip().split(" ")
                if len(parts) >= 4:
                    touched.append(parts[2][2:])  # strip "a/"
            elif line.startswith("+++ b/") or line.startswith("--- a/"):
                pass  # already captured via diff --git
    except OSError:
        pass
    return touched


def scope_allows(touched, card_scope):
    """Every touched file must match at least one declared scope glob."""
    if not touched:
        return False
    for f in touched:
        if not any(fnmatch.fnmatch(f, g) for g in card_scope):
            return False
    return True


def block(db, run_id, proposal_id, session_id, reason, gh):
    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import transition_state
    try:
        rid = transition_state(
            proposal_id, session_id, "APPLY_READY", "APPLY_BLOCKED",
            "apply_gate.py", db=db, notes=f"BLOCK: {reason}")
        db.execute(
            "UPDATE lifecycle_events SET workflow_run_id = ? "
            "WHERE id = ? AND workflow_run_id IS NULL",
            (run_id, rid))
    except Exception:
        # If state isn't APPLY_READY, don't crash — still refuse.
        db.execute(
            "INSERT INTO workflow_run_artifacts (run_id, artifact_type, content) "
            "VALUES (?, 'apply_gate_record', ?)",
            (run_id, json.dumps({"result": "BLOCK", "reason": reason,
                                 "gate_hash": gh})))
    db.commit()
    print(f"BLOCK: {reason}", file=sys.stderr)
    return 1


def main():
    parser = argparse.ArgumentParser(description="Deterministic apply gate")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    gh = gate_hash()
    db = get_db()
    run = db.execute("SELECT * FROM workflow_runs WHERE id = ?", (args.run_id,)).fetchone()
    if run is None:
        print(f"BLOCK: workflow_run not found: {args.run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    proposal_id = resolve_proposal_id(args.run_id, db)
    if not proposal_id:
        print(f"BLOCK: no proposal_id for run {args.run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)
    session_id = resolve_session_id(args.run_id, db)

    # (a) dual consensus
    if not dual_consensus(args.run_id, db):
        sys.exit(block(db, args.run_id, proposal_id, session_id,
                       "missing dual-review CONSENSUS_REACHED", gh))

    # (b) scope
    try:
        card_scope = json.loads(run["card_scope"] or "[]")
    except json.JSONDecodeError:
        card_scope = []
    if not card_scope:
        sys.exit(block(db, args.run_id, proposal_id, session_id,
                       "workflow_runs.card_scope is empty", gh))

    # locate the patch + new files from the latest build evidence
    ev = db.execute(
        "SELECT content FROM workflow_run_artifacts "
        "WHERE run_id = ? AND artifact_type = 'menter_build_evidence' "
        "ORDER BY id DESC LIMIT 1",
        (args.run_id,)).fetchone()
    if not ev:
        sys.exit(block(db, args.run_id, proposal_id, session_id,
                       "no build evidence artifact", gh))
    evidence = json.loads(ev["content"])
    output_dir = evidence.get("output_dir", "")
    if not output_dir or not os.path.isdir(output_dir):
        sys.exit(block(db, args.run_id, proposal_id, session_id,
                       f"output_dir missing: {output_dir}", gh))
    patch_path = os.path.join(output_dir, "changes.patch")
    if not os.path.isfile(patch_path):
        sys.exit(block(db, args.run_id, proposal_id, session_id,
                       "no changes.patch in output_dir", gh))

    # (b) scope — enforce against the ACTUAL touched files
    touched = files_touched_by_patch(patch_path)
    if not scope_allows(touched, card_scope):
        sys.exit(block(db, args.run_id, proposal_id, session_id,
                       f"diff touches files outside card_scope: "
                       f"{[t for t in touched if not any(fnmatch.fnmatch(t, g) for g in card_scope)]}",
                       gh))

    # (c) patch applies cleanly — verify against a COPY, never mutate live repo yet
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        for f in os.listdir(REPO_ROOT):
            src = os.path.join(REPO_ROOT, f)
            dst = os.path.join(tmp, f)
            if os.path.isdir(src):
                shutil.copytree(src, dst, symlinks=True,
                                ignore=shutil.ignore_patterns(".git"))
            else:
                shutil.copy2(src, dst)
        check = subprocess.run(
            ["git", "apply", "--check", patch_path],
            capture_output=True, text=True, cwd=tmp)
        if check.returncode != 0:
            sys.exit(block(db, args.run_id, proposal_id, session_id,
                           f"patch does not apply cleanly: {check.stderr[:300]}", gh))

    # (d) compile every emitted Python file
    new_dir = os.path.join(output_dir, "new")
    modified_dir = os.path.join(output_dir, "modified")
    py_files = []
    for base in (new_dir, modified_dir):
        if os.path.isdir(base):
            for root, _, files in os.walk(base):
                for fn in files:
                    if fn.endswith(".py"):
                        py_files.append(os.path.join(root, fn))
    for pyf in py_files:
        rc = subprocess.run(["python3", "-m", "py_compile", pyf],
                            capture_output=True, text=True)
        if rc.returncode != 0:
            sys.exit(block(db, args.run_id, proposal_id, session_id,
                           f"py_compile failed for {pyf}: {rc.stderr[:300]}", gh))

    # ── ALL CONDITIONS MET — apply into the real repo ──────────────────
    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import transition_state

    apply = subprocess.run(["git", "apply", patch_path],
                           capture_output=True, text=True, cwd=REPO_ROOT)
    if apply.returncode != 0:
        sys.exit(block(db, args.run_id, proposal_id, session_id,
                       f"git apply failed: {apply.stderr[:300]}", gh))

    # copy new files
    copied = []
    if os.path.isdir(new_dir):
        for root, _, files in os.walk(new_dir):
            for fn in files:
                if fn.endswith(".pyc") or "__pycache__" in root:
                    continue
                src = os.path.join(root, fn)
                rel = os.path.relpath(src, new_dir)
                dst = os.path.join(REPO_ROOT, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(rel)

    # record apply as a spine row (the deterministic evidence)
    record = json.dumps({
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "run_id": args.run_id,
        "diff_scope": sorted(touched),
        "gate_hash": gh,
        "patch_hash": evidence.get("patch_hash", ""),
        "copied_new": copied,
    })
    db.execute(
        "INSERT INTO workflow_run_artifacts (run_id, artifact_type, content) "
        "VALUES (?, 'apply_gate_record', ?)",
        (args.run_id, record))
    db.commit()

    rid = transition_state(
        proposal_id, session_id, "APPLY_READY", "APPLIED",
        "apply_gate.py", db=db, evidence_ref=gh, notes="deterministic apply gate")
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (args.run_id, rid))
    db.commit()

    print("APPLIED")
    print(f"run_id: {args.run_id}")
    print(f"touched: {sorted(touched)}")
    print(f"copied_new: {copied}")
    print(f"gate_hash: {gh}")

    db.close()


if __name__ == "__main__":
    main()
