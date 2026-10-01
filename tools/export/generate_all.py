#!/usr/bin/env python3
"""
generate_all.py — Tier 5.5
Orchestrates AGENTS.md, HCP, and DEV-PIVOT manifest generation with a shared run ID.
Produces a hash manifest at runtime/manifests/EXPORT_MANIFEST.json.

Usage: python3 tools/export/generate_all.py [--db PATH] [--skip-agents] [--skip-hcp]
"""

import argparse
import atexit
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "data" / "cis_memory.db"
MANIFEST_PATH = REPO_ROOT / "runtime" / "manifests" / "EXPORT_MANIFEST.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "state"))
import canonical_state  # noqa: E402

GENERATE_AGENTS = REPO_ROOT / "tools" / "export" / "generate_agents_md.py"
GENERATE_HCP = REPO_ROOT / "tools" / "export" / "generate_hcp.py"
GENERATE_DEV_PIVOT = REPO_ROOT / "tools" / "export" / "generate_dev_pivot_manifest.py"
AGENTS_CONFIG = REPO_ROOT / "config" / "agents_static.yaml"
HCP_CONFIG = REPO_ROOT / "config" / "hcp_static.yaml"

AGENTS_OUT = REPO_ROOT / "AGENTS.md"
HCP_OUT_DIR = REPO_ROOT / "PROJECT_CONTEXT_PACK_UPLOAD"
DEV_PIVOT_OUT = REPO_ROOT / "docs" / "DEV-PIVOT_STATUS.md"

HCP_FILES = [
    "READ_FIRST_HERMES_CONTEXT.md",
    "HCP_00_README_START_HERE.md",
    "HCP_01_CURRENT_STATE.md",
    "HCP_02_ACTIVE_ARCHITECTURE.md",
    "HCP_03_DECISIONS_LOG.md",
    "HCP_04_OPEN_QUESTIONS.md",
    "HCP_05_NEXT_ACTIONS.md",
    "HCP_06_MODEL_ROLES_AND_PROTOCOL.md",
    "HCP_07_RECENT_HANDOFF.md",
    "HCP_08_FILES_CHANGED_RECENTLY.md",
    "HCP_09_TERMS_AND_NAMING.md",
]

# HCP_10 is written by generate_hcp.py but is not a manifest artifact. It still
# has to be known here: the pre-commit safety pass below reasons about every
# path this pipeline *writes*, not just the ones it hashes. Leaving it out is
# what let it drift (WB1-D13 — see the module note under "pre-commit safety").
HCP_WRITTEN_ONLY = ["HCP_10_DEV_PIVOT_STATUS.md"]


# ── pre-commit safety (WB1-D13) ────────────────────────────────────────────
#
# The pre-commit hook runs this pipeline on every commit. Before this guard it
# did so unconditionally and in place, which made two silent failures possible:
#
#   1. Generator-source drift. generate_hcp.py sat with a large uncommitted
#      rewrite for weeks. Every unrelated commit executed that unreviewed
#      source, and the projections it produced were committed while the source
#      that produced them was not — the repository could not regenerate its own
#      committed exports from its own committed code.
#
#   2. Pre-existing dirty output absorption. The generators overwrote their
#      output paths before anything checked whether the author already had
#      uncommitted work there, and the hook then `git add`-ed any export path
#      that looked dirty — unable to tell "this run just wrote it" from "the
#      author was midway through editing it". Unrelated work could be destroyed
#      and the replacement folded into someone else's commit.
#
# --precommit answers both: nothing executes from unstaged generator source,
# generation happens in a scratch tree so a refusal costs no bytes on disk, and
# only paths this run actually produced are reported as stageable.

GENERATOR_SOURCES = [
    "tools/export/generate_all.py",
    "tools/export/generate_agents_md.py",
    "tools/export/generate_hcp.py",
    "tools/export/generate_dev_pivot_manifest.py",
    "tools/state/canonical_state.py",
    "config/agents_static.yaml",
    "config/hcp_static.yaml",
]

# Every path the pipeline writes, repo-relative.
OUTPUT_PATHS = (
    ["AGENTS.md"]
    + [f"PROJECT_CONTEXT_PACK_UPLOAD/{f}" for f in HCP_FILES + HCP_WRITTEN_ONLY]
    + ["docs/DEV-PIVOT_STATUS.md", "runtime/manifests/EXPORT_MANIFEST.json"]
)

EXIT_DIRTY_SOURCE = 3
EXIT_DIRTY_OUTPUT = 4

# "Generated: <utc> | Run: run-<hex>" — the generators' own non-determinism.
# Two runs of identical code over an identical DB differ here and nowhere else,
# so this line alone cannot distinguish generator churn from authored content.
STAMP_RE = re.compile(r"^Generated: .* \| Run: .*$", re.MULTILINE)


def _git(*args):
    """Run a git command at REPO_ROOT. Returns CompletedProcess."""
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=REPO_ROOT, timeout=30
    )


def unstaged(paths):
    """Of `paths`, those whose working-tree content differs from the index.

    Index, not HEAD: a staged change is a version the author has explicitly
    presented for this commit, which the card's contract accepts as "an
    explicitly verified/staged version". An *unstaged* change is the hazard —
    code or content nobody has offered for review driving a commit.
    """
    existing = [p for p in paths if (REPO_ROOT / p).exists()]
    if not existing:
        return []
    r = _git("diff", "--name-only", "--", *existing)
    if r.returncode != 0:
        # Fail closed: if git cannot tell us, we cannot claim the tree is safe.
        raise RuntimeError(f"git diff failed: {r.stderr.strip()}")
    return [p for p in r.stdout.split("\n") if p]


def strip_stamp(text):
    return STAMP_RE.sub("", text)


def read_or_none(path):
    try:
        return Path(path).read_bytes()
    except FileNotFoundError:
        return None


def check_generator_sources():
    """Refuse to execute generators that have unstaged modifications."""
    dirty = unstaged(GENERATOR_SOURCES)
    if dirty:
        print("")
        print("═══════════════════════════════════════════════════════════")
        print("  EXPORT BLOCKED: generator source has unstaged changes")
        print("═══════════════════════════════════════════════════════════")
        print("")
        for p in dirty:
            print(f"  modified (unstaged): {p}")
        print("")
        print("These files produce the committed export projections. Running")
        print("them from unreviewed working-tree state would generate exports")
        print("this repository cannot reproduce from its own committed source.")
        print("")
        print("Stage the generator change (git add) to commit it deliberately,")
        print("or revert it. Nothing has been generated or modified.")
        print("")
        return False
    return True


def classify_outputs(staged_root, dirty_before):
    """Compare freshly generated content against what is on disk.

    Returns (to_install, violations). `to_install` is [(repo_rel, staged_path)]
    for paths this run genuinely changed and may safely overwrite+stage.
    `violations` are paths the author had uncommitted work in whose content
    this run would have altered in substance — never touched, always fatal.
    """
    to_install, violations = [], []
    for rel in OUTPUT_PATHS:
        staged_file = staged_root / rel
        if not staged_file.exists():
            continue  # generator legitimately skipped it (e.g. --skip-hcp)
        new = staged_file.read_bytes()
        cur = read_or_none(REPO_ROOT / rel)
        if cur == new:
            continue  # byte-identical; not part of this commit's scope
        if rel not in dirty_before:
            to_install.append((rel, staged_file))
            continue
        # Dirty before we started. The only safe overwrite is one that loses
        # nothing: content equal apart from the generation stamp means the
        # existing dirt is a previous run's stamp churn, not authored work.
        cur_txt = (cur or b"").decode("utf-8", "replace")
        if strip_stamp(cur_txt) == strip_stamp(new.decode("utf-8", "replace")):
            to_install.append((rel, staged_file))
        else:
            violations.append(rel)
    return to_install, violations


def report_violations(violations):
    print("")
    print("═══════════════════════════════════════════════════════════")
    print("  EXPORT BLOCKED: uncommitted work in a generated file")
    print("═══════════════════════════════════════════════════════════")
    print("")
    for p in violations:
        print(f"  would be overwritten: {p}")
    print("")
    print("These paths are generated, but they hold uncommitted changes that")
    print("regeneration does not reproduce. Overwriting them would destroy")
    print("work, and staging the result would fold it into this commit.")
    print("")
    print("Commit, stash, or discard those changes deliberately, then retry.")
    print("Nothing has been generated or modified.")
    print("")


def generate_run_id():
    """Generate a unique pipeline run ID: run-<12 hex chars>"""
    return "run-" + uuid.uuid4().hex[:12]


def get_git_head(repo_root):
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=repo_root, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def sha256_file(path):
    """Return hex SHA256 digest of file content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def file_stats(path):
    """Return (size_bytes, char_count, line_count) for a text file."""
    content = Path(path).read_text()
    return len(content.encode("utf-8")), len(content), content.count("\n") + (1 if content and not content.endswith("\n") else 0)


def run_generator(command, label):
    """Run a generator subprocess. Return (success_bool, stdout_text)."""
    print(f"[generate_all] Running: {' '.join(command)}")
    try:
        r = subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=REPO_ROOT)
        stdout = r.stdout.strip()
        stderr = r.stderr.strip()
        if r.returncode != 0:
            print(f"[generate_all] ERROR: {label} exited with code {r.returncode}")
            if stderr:
                print(f"[generate_all] stderr: {stderr}")
            if stdout:
                print(f"[generate_all] stdout: {stdout}")
            return False, stdout
        if stderr:
            print(f"[generate_all] {label} stderr: {stderr}")
        print(f"[generate_all] {label}: {stdout.split(chr(10))[-1] if stdout else 'OK'}")
        return True, stdout
    except Exception as e:
        print(f"[generate_all] ERROR: {label} failed: {e}")
        return False, ""


def get_state_revision(db_path):
    """The canonical state revision (CARD_01_SINGLE_AUTHORITY_CONTRACT.md,
    queue 4.29) this run's artifacts were generated against. Lets a caller
    compare a stored manifest's state_revision to a freshly-computed one
    (canonical_state.compute_state_revision) to detect staleness relative
    to the DB, not just relative to this manifest's own git_head/run_id."""
    conn = sqlite3.connect(db_path)
    try:
        return canonical_state.compute_state_revision(conn)
    finally:
        conn.close()


def build_manifest(run_id, artifacts, git_head, db_path, state_revision):
    """Construct the export manifest dict."""
    return {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": git_head,
        "state_revision": state_revision,
        "generator": "tools/export/generate_all.py",
        "db_path": str(db_path),
        "source_configs": [
            "config/agents_static.yaml",
            "config/hcp_static.yaml",
        ],
        "commands": [
            f"python3 tools/export/generate_agents_md.py --run-id {run_id}",
            f"python3 tools/export/generate_hcp.py --run-id {run_id}",
            f"python3 tools/export/generate_dev_pivot_manifest.py --run-id {run_id}",
        ],
        "artifacts": artifacts,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate AGENTS.md + HCP + DEV-PIVOT files with manifest")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--skip-agents", action="store_true", help="Skip AGENTS.md generation")
    parser.add_argument("--skip-hcp", action="store_true", help="Skip HCP generation")
    parser.add_argument(
        "--precommit", action="store_true",
        help="Pre-commit safety mode (WB1-D13): refuse to run from unstaged "
             "generator source, generate to a scratch tree so a refusal "
             "mutates nothing, never overwrite uncommitted work in a "
             "generated file, and report exactly the paths this run produced.",
    )
    parser.add_argument(
        "--stage-list", default=None,
        help="With --precommit: write the newline-separated set of paths this "
             "run produced to this file. The caller may stage those and only "
             "those.",
    )
    args = parser.parse_args()

    db_path = args.db
    if not Path(db_path).exists():
        print(f"ERROR: DB not found: {db_path}", file=sys.stderr)
        sys.exit(2)

    # ── Pre-commit safety: source check happens before anything runs ──
    scratch = None
    if args.precommit:
        if not check_generator_sources():
            sys.exit(EXIT_DIRTY_SOURCE)
        dirty_before = unstaged(OUTPUT_PATHS)
        if dirty_before:
            print("[generate_all] Pre-existing uncommitted generated files "
                  "(protected from overwrite):")
            for p in dirty_before:
                print(f"[generate_all]   {p}")
        scratch = Path(tempfile.mkdtemp(prefix="cis-export-"))
        # Generator failure exits straight out of main(); don't leak the tree.
        atexit.register(shutil.rmtree, scratch, True)
        out_root = scratch
        (out_root / "PROJECT_CONTEXT_PACK_UPLOAD").mkdir(parents=True, exist_ok=True)
        (out_root / "docs").mkdir(parents=True, exist_ok=True)
        (out_root / "runtime" / "manifests").mkdir(parents=True, exist_ok=True)
    else:
        dirty_before = []
        out_root = REPO_ROOT

    agents_out = out_root / "AGENTS.md"
    hcp_out_dir = out_root / "PROJECT_CONTEXT_PACK_UPLOAD"
    dev_pivot_out = out_root / "docs" / "DEV-PIVOT_STATUS.md"
    manifest_out = out_root / "runtime" / "manifests" / "EXPORT_MANIFEST.json"

    run_id = generate_run_id()
    git_head = get_git_head(REPO_ROOT)
    print(f"[generate_all] Run ID: {run_id}")
    print(f"[generate_all] Git HEAD: {git_head}")
    print(f"[generate_all] DB: {db_path}")

    # ── Step 1: Generate AGENTS.md ──
    agents_ok = True
    if not args.skip_agents:
        cmd = [
            "python3", str(GENERATE_AGENTS),
            "--db", db_path,
            "--config", str(AGENTS_CONFIG),
            "--out", str(agents_out),
            "--run-id", run_id,
        ]
        agents_ok, _ = run_generator(cmd, "generate_agents_md.py")
        if not agents_ok:
            print("[generate_all] ABORT: generate_agents_md.py failed. Not writing manifest.")
            sys.exit(1)
    else:
        print("[generate_all] Skipping AGENTS.md generation (--skip-agents)")

    # ── Step 2: Generate HCP files ──
    hcp_ok = True
    if not args.skip_hcp:
        cmd = [
            "python3", str(GENERATE_HCP),
            "--db", db_path,
            "--hcp-config", str(HCP_CONFIG),
            "--agents-config", str(AGENTS_CONFIG),
            "--out-dir", str(hcp_out_dir),
            "--run-id", run_id,
        ]
        hcp_ok, _ = run_generator(cmd, "generate_hcp.py")
        if not hcp_ok:
            print("[generate_all] ABORT: generate_hcp.py failed. Not writing manifest.")
            sys.exit(1)
    else:
        print("[generate_all] Skipping HCP generation (--skip-hcp)")

    # ── Step 3: Generate DEV-PIVOT manifest ──
    cmd = [
        "python3", str(GENERATE_DEV_PIVOT),
        "--db", db_path,
        "--out", str(dev_pivot_out),
        "--run-id", run_id,
    ]
    dev_pivot_ok, _ = run_generator(cmd, "generate_dev_pivot_manifest.py")
    if not dev_pivot_ok:
        print("[generate_all] WARNING: generate_dev_pivot_manifest.py failed. Continuing.")

    # ── Step 4: Build manifest ──
    artifacts = []

    # AGENTS.md
    if not args.skip_agents:
        size, chars, lines = file_stats(agents_out)
        sha = sha256_file(agents_out)
        artifacts.append({
            "path": "AGENTS.md",
            "type": "agents_context",
            "generator": "tools/export/generate_agents_md.py",
            "sha256": sha,
            "size_bytes": size,
            "char_count": chars,
            "line_count": lines,
        })

    # HCP files
    if not args.skip_hcp:
        for fname in HCP_FILES:
            fpath = hcp_out_dir / fname
            if not fpath.exists():
                print(f"[generate_all] WARNING: Expected HCP file not found: {fpath}")
                continue
            size, chars, lines = file_stats(fpath)
            sha = sha256_file(fpath)
            artifacts.append({
                "path": f"PROJECT_CONTEXT_PACK_UPLOAD/{fname}",
                "type": "hcp_context",
                "generator": "tools/export/generate_hcp.py",
                "sha256": sha,
                "size_bytes": size,
                "char_count": chars,
                "line_count": lines,
            })

    # DEV-PIVOT manifest
    if dev_pivot_out.exists():
        size, chars, lines = file_stats(dev_pivot_out)
        sha = sha256_file(dev_pivot_out)
        artifacts.append({
            "path": "docs/DEV-PIVOT_STATUS.md",
            "type": "dev_pivot_manifest",
            "generator": "tools/export/generate_dev_pivot_manifest.py",
            "sha256": sha,
            "size_bytes": size,
            "char_count": chars,
            "line_count": lines,
        })

    state_revision = get_state_revision(db_path)
    manifest = build_manifest(run_id, artifacts, git_head, db_path, state_revision)

    # ── Step 5: Write manifest ──
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"[generate_all] Manifest written: {manifest_out}")
    print(f"[generate_all] Artifacts: {len(artifacts)}")

    # ── Step 6: Install from scratch tree (--precommit only) ──
    #
    # Everything so far went to a scratch directory, so the repository is still
    # byte-for-byte as the author left it. This is the last point at which a
    # refusal is free, and the only point at which we can compare what was
    # generated against what the author already had.
    if args.precommit:
        to_install, violations = classify_outputs(out_root, dirty_before)
        if violations:
            report_violations(violations)
            shutil.rmtree(scratch, ignore_errors=True)
            sys.exit(EXIT_DIRTY_OUTPUT)

        for rel, src in to_install:
            dest = REPO_ROOT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
        shutil.rmtree(scratch, ignore_errors=True)

        produced = [rel for rel, _ in to_install]
        if args.stage_list:
            Path(args.stage_list).write_text(
                "".join(f"{p}\n" for p in produced))
        # Scope observability: the author can see the exact set before the
        # commit is accepted, and it is the only set the hook may stage.
        print(f"[generate_all] Produced {len(produced)} changed export file(s):")
        for p in produced:
            print(f"[generate_all]   {p}")
        for p in dirty_before:
            if p not in produced:
                print(f"[generate_all]   (left untouched, pre-existing: {p})")

    print(f"[generate_all] PASS — Run {run_id} complete.")


if __name__ == "__main__":
    main()
