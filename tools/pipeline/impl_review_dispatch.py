#!/usr/bin/env python3
"""
impl_review_dispatch.py — R3+R4: dispatch implementation review to both pipeline
reviewers (review1 8643 + review2 8647), reconcile verdicts, route to APPLY_READY /
IMPL_REVISE_REQUESTED / IMPL_ESCALATED, and notify Eric (R5).

The reviewers assess the BUILD against deterministic evidence AND check the code
itself — this absorbs Verify's former code-checking job (D5). Two different
lineages (Qwen + GLM) = the cross-lineage check.

Usage:
  python3 tools/pipeline/impl_review_dispatch.py --run-id <id> [--done-when-file <path>]
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
REPO_ROOT = os.environ.get("CIS_REPO_ROOT", "/mnt/projects/cis")

REVIEW1_ENDPOINT = os.environ.get("CIS_REVIEW1_ENDPOINT", "http://127.0.0.1:8643")
REVIEW2_ENDPOINT = os.environ.get("CIS_REVIEW2_ENDPOINT", "http://127.0.0.1:8647")
REVIEW1_API_KEY = os.environ.get("CIS_REVIEW1_API_KEY", "cis-qwen-reviewer-gateway-key-2026")
REVIEW2_API_KEY = os.environ.get("CIS_REVIEW2_API_KEY", "cis-glm-reviewer-gateway-key-2026")

REVIEW_SYSTEM = (
    "You are a CIS pipeline implementation reviewer. Review the BUILD, not the "
    "design. Judge whether the produced code actually implements the card's "
    "DONE-WHEN against the deterministic evidence handle. CHECK THE CODE ITSELF: "
    "does it apply cleanly, does it compile, does it do what the card says, and "
    "does it touch ONLY the declared scope. Emit FINAL_JSON with role=reviewer, "
    "status in {CONSENSUS_REACHED, OBJECTIONS, ESCALATE}, summary, recommendation."
)


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


def call_reviewer(endpoint, api_key, prompt, timeout=900):
    """Call one reviewer gateway and return (content, usage_or_none)."""
    import urllib.request
    body = json.dumps({
        "model": "auto",
        "messages": [
            {"role": "system", "content": REVIEW_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{endpoint}/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    return content, data.get("usage")


def extract_final_json(text):
    import re
    fence = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass
    # raw JSON at end
    lines = text.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith("{"):
            try:
                return json.loads("\n".join(lines[i:]))
            except json.JSONDecodeError:
                pass
            break
    return None


def main():
    parser = argparse.ArgumentParser(description="Implementation review dispatch")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--done-when-file", default=None)
    args = parser.parse_args()

    db = get_db()
    run = db.execute("SELECT * FROM workflow_runs WHERE id = ?", (args.run_id,)).fetchone()
    if run is None:
        print(f"REFUSED: workflow_run not found: {args.run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    proposal_id = resolve_proposal_id(args.run_id, db)
    if not proposal_id:
        print(f"REFUSED: no proposal_id for run {args.run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import get_current_state, transition_state, create_dispatch

    current = get_current_state(proposal_id, db)
    if current != "IMPL_REVIEW_PENDING":
        print(f"NOTE: current state '{current}', expected IMPL_REVIEW_PENDING", file=sys.stderr)
        db.close()
        sys.exit(1)

    session_id = resolve_session_id(args.run_id, db)

    # Evidence handle + DONE-WHEN for the review prompt
    ev = db.execute(
        "SELECT content FROM workflow_run_artifacts "
        "WHERE run_id = ? AND artifact_type = 'menter_build_evidence' "
        "ORDER BY id DESC LIMIT 1",
        (args.run_id,)).fetchone()
    evidence = ev["content"] if ev else "{}"
    done_when = ""
    if args.done_when_file:
        with open(args.done_when_file) as f:
            done_when = f.read()

    prompt = (
        f"Review this implementation build.\n\n"
        f"RUN_ID: {args.run_id}\n"
        f"CARD_SCOPE: {run['card_scope']}\n"
        f"BUILD_EVIDENCE: {evidence}\n"
        f"DONE_WHEN:\n{done_when or '(not provided — assess against evidence handle)'}\n"
    )

    # IMPL_REVIEW_PENDING -> IMPL_REVIEWING
    r0 = transition_state(
        proposal_id, session_id, "IMPL_REVIEW_PENDING", "IMPL_REVIEWING",
        "impl_review_dispatch.py", db=db)
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (args.run_id, r0))
    db.commit()

    # Call both reviewers (parallel where possible; sequential fallback)
    verdicts = {}
    reviewer_outputs = {}
    for label, endpoint, key in (("review1", REVIEW1_ENDPOINT, REVIEW1_API_KEY),
                                 ("review2", REVIEW2_ENDPOINT, REVIEW2_API_KEY)):
        try:
            content, usage = call_reviewer(endpoint, key, prompt)
            verdicts[label] = content
            reviewer_outputs[label] = content
            print(f"verdict[{label}]: {content[:200]}")
        except Exception as exc:
            verdicts[label] = None
            reviewer_outputs[label] = None
            print(f"verdict[{label}]: ERROR {exc}", file=sys.stderr)

    parsed = {}
    for label in ("review1", "review2"):
        if reviewer_outputs.get(label):
            fj = extract_final_json(reviewer_outputs[label])
            parsed[label] = fj.get("status") if fj else None
        else:
            parsed[label] = None

    s1, s2 = parsed.get("review1"), parsed.get("review2")
    # Reconcile (R4): any ESCALATE -> escalate; any OBJECTIONS -> revise;
    # both CONSENSUS_REACHED -> apply-ready.
    if "ESCALATE" in (s1, s2):
        routing = "IMPL_ESCALATED"
    elif "OBJECTIONS" in (s1, s2) or None in (s1, s2):
        routing = "IMPL_REVISE_REQUESTED"
    elif s1 == "CONSENSUS_REACHED" and s2 == "CONSENSUS_REACHED":
        routing = "APPLY_READY"
    else:
        routing = "IMPL_ESCALATED"

    # Record deliberation rounds for the two reviewers
    for label, sig in (("review1", s1), ("review2", s2)):
        db.execute(
            "INSERT INTO deliberation_rounds "
            "(run_id, round_number, reviewer_role, reviewer_signal, "
            " created_at) VALUES (?, ?, ?, ?, ?)",
            (args.run_id, (run["rounds_completed"] or 0) + 1,
             label, sig or "OBJECTIONS",
             datetime.now(timezone.utc).isoformat()))

    # IMPL_REVIEWING -> IMPL_REVIEW_COMPLETE -> routing
    rc = transition_state(
        proposal_id, session_id, "IMPL_REVIEWING", "IMPL_REVIEW_COMPLETE",
        "impl_review_dispatch.py", db=db,
        notes=f"verdicts={json.dumps(parsed)}")
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (args.run_id, rc))
    db.commit()

    rr = transition_state(
        proposal_id, session_id, "IMPL_REVIEW_COMPLETE", routing,
        "impl_review_dispatch.py", db=db,
        notes=f"verdicts={json.dumps(parsed)}")
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (args.run_id, rr))
    db.commit()

    # If revise requested, return dispatch to Menter
    if routing == "IMPL_REVISE_REQUESTED":
        did = create_dispatch(
            proposal_id=proposal_id,
            source_actor="reviewer",
            target_agent="menter",
            target_endpoint="sandbox:tools/run_claude_sandbox.sh",
            lifecycle_state_at="IMPL_REVISE_REQUESTED",
            payload=json.dumps({"run_id": args.run_id, "revise": True}),
            initiated_by="impl_review_dispatch.py",
            eric_approved=1,
            db=db)
        db.execute(
            "UPDATE dispatch_log SET workflow_run_id = ? WHERE dispatch_id = ?",
            (args.run_id, did))
        db.commit()

    # Notify Eric (R5) — best effort
    try:
        subprocess.run(
            ["python3", "tools/pipeline/notify_menter_result.py",
             "--run-id", args.run_id, "--routing", routing],
            capture_output=True, text=True, timeout=60, cwd=REPO_ROOT)
    except Exception as exc:
        print(f"notify warning: {exc}", file=sys.stderr)

    print("IMPLEMENTATION REVIEW COMPLETE")
    print(f"verdicts: {json.dumps(parsed)}")
    print(f"routing: {routing}")

    db.close()


if __name__ == "__main__":
    main()
