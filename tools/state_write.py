#!/usr/bin/env python3
"""
state_write.py — CIS Tier 6.x STATE_WRITE Executor
Consumes verified gate-results JSON, writes approved state to SQLite spine.

Usage:
  python3 tools/state_write.py --run-id <id> --gate-results <path>
      [--db-path <path>] [--manifest-dir <path>]

Architecture:
  - Reads gate-results JSON produced by gate_closeout_complete.sh v2.
  - VALIDATES: all required fields present, tier_6_4_markers all true,
    review_signal is valid and not OBJECTIONS.
  - WRITES: one workflow_runs row to spine, closeout manifest JSON.
  - Does NOT: read Kanban, run gates, call generate_all, call closeout, git commit.

Exit codes:
  0 — STATE_WRITE PASSED (or UPDATED on idempotent re-run)
  1 — Spine write failure
  2 — Input validation failure (missing file, bad JSON, missing markers, blocked signal)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# ── Constants ──────────────────────────────────────────────────────────

VALID_REVIEW_SIGNALS = {"CONSENSUS_REACHED", "ESCALATE"}
TIER_6_4_MARKER_KEYS = [
    "research_present",
    "proposal_valid",
    "review_signal",
    "consensus_valid",
    "eric_approved",
    "implementation_present",
]
REQUIRED_TOP_LEVEL = [
    "run_id",
    "node_id",
    "node_description",
    "timestamp_started",
    "git_head",
    "tier_6_4_markers",
    "gates",
]


# ── Helpers ────────────────────────────────────────────────────────────

def fail(msg, exit_code=2):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(exit_code)


def load_gate_results(path):
    """Load and parse gate-results JSON. Fail-closed on any issue."""
    if not os.path.isfile(path):
        fail(f"gate-results file not found: {path}")
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        fail(f"cannot read gate-results: {e}")
    if not isinstance(data, dict):
        fail("gate-results JSON is not a dictionary")
    return data


def validate_top_level(data):
    """Ensure all required top-level fields are present and non-null."""
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            fail(f"missing required field: {field}")
        if data[field] is None:
            fail(f"required field is null: {field}")


def validate_tier_6_4_markers(markers):
    """Validate tier_6_4_markers object. Fail-closed on any issue."""
    if not isinstance(markers, dict):
        fail("tier_6_4_markers is not an object")

    for key in TIER_6_4_MARKER_KEYS:
        if key not in markers:
            fail(f"tier_6_4_markers missing key: {key}")

    # All boolean markers must be true
    bool_keys = [k for k in TIER_6_4_MARKER_KEYS if k != "review_signal"]
    for key in bool_keys:
        if markers[key] is not True:
            fail(f"tier_6_4_markers.{key} is false — closeout blocked")

    # review_signal must be valid and not OBJECTIONS
    signal = markers.get("review_signal")
    if signal is None or not isinstance(signal, str) or not signal.strip():
        fail("tier_6_4_markers.review_signal is missing or empty")

    signal = signal.strip()
    if signal == "OBJECTIONS":
        fail("OBJECTIONS — closeout blocked")

    if signal not in VALID_REVIEW_SIGNALS:
        fail(f"invalid review_signal: {signal} (valid: CONSENSUS_REACHED, ESCALATE)")

    return signal


def validate_gates(gates):
    """Ensure at least one Phase 1 gate has PASS status."""
    if not isinstance(gates, list) or len(gates) == 0:
        fail("gates array is empty — no verification data")
    # Note: We don't require ALL gates to be PASS — SKIP is valid for optional gates.
    # But if NO gate has PASS, we can't trust the verification.
    pass_count = sum(1 for g in gates if g.get("status") == "PASS")
    if pass_count == 0:
        fail("no gate has PASS status — nothing verified")


def write_spine(db_path, run_id, result):
    """Write or update workflow_runs row. Returns 'INSERTED' or 'UPDATED'."""
    # Dynamic import to keep database.py dependency optional until needed
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "runtime"))
    try:
        from db import database
    except ImportError:
        fail("cannot import database.py — check path", 1)

    conn = database.init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()

    # Check if run_id already exists (idempotency)
    cursor = conn.execute("SELECT id FROM workflow_runs WHERE id = ?", (run_id,))
    existing = cursor.fetchone()

    if existing:
        conn.execute(
            """UPDATE workflow_runs
               SET result = ?, completed_at = ?
               WHERE id = ?""",
            (result, now, run_id),
        )
        conn.commit()
        conn.close()
        return "UPDATED"
    else:
        database.insert_workflow_run(
            conn,
            id=run_id,
            topic=f"Closeout: {result}",
            result=result,
            requires_eric_review=1,
            created_at=now,
            completed_at=now,
        )
        conn.commit()
        conn.close()
        return "INSERTED"


def write_manifest(manifest_dir, run_id, data, markers):
    """Write closeout manifest JSON."""
    os.makedirs(manifest_dir, exist_ok=True)
    manifest_path = os.path.join(manifest_dir, f"CLOSEOUT_{run_id}.json")

    manifest = {
        "run_id": run_id,
        "node_id": data["node_id"],
        "node_description": data["node_description"],
        "timestamp_started": data["timestamp_started"],
        "timestamp_completed": datetime.now(timezone.utc).isoformat(),
        "git_head": data["git_head"],
        "tier_6_4_markers": markers,
        "gates": [
            {
                "name": g.get("name", ""),
                "phase": g.get("phase", ""),
                "command": g.get("command", ""),
                "exit_code": g.get("exit_code", -1),
                "status": g.get("status", "UNKNOWN"),
                "output_excerpt": (g.get("output_excerpt", "") or "")[:500],
            }
            for g in data.get("gates", [])
        ],
        "state_write": {
            "status": "PASS",
            "rows_written_or_updated": 1,
            "error": None,
        },
        "export": {
            "status": "SKIP",
            "manifest_path": "",
        },
        "closeout_file_path": "",
        "final_git_status": "",
        "next_action": "",
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


# ── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CIS STATE_WRITE Executor")
    parser.add_argument("--run-id", required=True, help="Run identifier")
    parser.add_argument("--gate-results", required=True, help="Path to gate-results JSON")
    parser.add_argument("--db-path", default="/mnt/projects/cis/data/cis_memory.db",
                        help="SQLite database path")
    parser.add_argument("--manifest-dir", default="/mnt/projects/cis/runtime/manifests",
                        help="Directory for closeout manifest JSON")
    args = parser.parse_args()

    # 1. Load and validate gate-results JSON
    data = load_gate_results(args.gate_results)
    validate_top_level(data)

    # 2. Validate tier_6_4_markers
    markers = data["tier_6_4_markers"]
    review_signal = validate_tier_6_4_markers(markers)

    # 3. Validate gates
    validate_gates(data["gates"])

    # 4. Write to spine
    action = write_spine(args.db_path, args.run_id, review_signal)

    # 5. Write closeout manifest
    write_manifest(args.manifest_dir, args.run_id, data, markers)

    # 6. Report
    if action == "UPDATED":
        print("STATE_WRITE UPDATED")
    else:
        print("STATE_WRITE PASSED")


if __name__ == "__main__":
    main()
