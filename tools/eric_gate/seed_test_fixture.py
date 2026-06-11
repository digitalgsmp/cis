#!/usr/bin/env python3
"""
seed_test_fixture.py — Eric Gate Test Fixture Seeder (Component 3)

Creates isolated test workflow runs with controlled properties for
acceptance testing. Uses --db-path to target a specific database
(should be a temp copy, not the live spine).

Scenarios:
    consensus_reached   — CONSENSUS_REACHED run with deliberation
    no_deliberation     — Run with no deliberation rounds
    with_drift          — Run with open blocking drift indicator
    with_escalation     — Run with unreconciled mandatory escalation
    approved            — Run with current APPROVE decision
    vetoed              — Run with current VETO decision
    veto_then_approve   — VETO → APPROVE history
    stale_briefing      — Approved run, then mutated state
    clean               — Clean run with no Eric Gate decisions

Usage:
    python3 tools/eric_gate/seed_test_fixture.py \
      --db-path /tmp/test_cis.db \
      --scenario consensus_reached

    # Clean up all test data:
    python3 tools/eric_gate/seed_test_fixture.py \
      --db-path /tmp/test_cis.db \
      --scenario clean
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

SPINE_PATH = os.environ.get(
    "CIS_SPINE_PATH",
    "/mnt/projects/cis/data/cis_memory.db",
)

SCENARIOS = [
    "consensus_reached", "no_deliberation", "with_drift",
    "with_escalation", "approved", "vetoed",
    "veto_then_approve", "stale_briefing", "clean",
]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def init_schema(conn):
    """Ensure minimal schema exists for tests."""
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            result TEXT NOT NULL,
            requires_eric_review INTEGER NOT NULL DEFAULT 1,
            max_rounds INTEGER NOT NULL DEFAULT 3,
            max_consecutive_revisions INTEGER NOT NULL DEFAULT 3,
            rounds_completed INTEGER NOT NULL DEFAULT 0,
            final_objections_json TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL DEFAULT 'COMPLETE',
            route TEXT,
            updated_at TEXT,
            eric_approved_at TEXT
        );

        CREATE TABLE IF NOT EXISTS deliberation_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL REFERENCES workflow_runs(id),
            round_number INTEGER NOT NULL,
            drafter_role TEXT NOT NULL,
            drafter_output TEXT NOT NULL,
            reviewer_role TEXT NOT NULL,
            reviewer_signal TEXT NOT NULL,
            objections_json TEXT,
            revision_number INTEGER NOT NULL DEFAULT 1,
            requires_eric_review INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            UNIQUE(run_id, round_number)
        );

        CREATE TABLE IF NOT EXISTS goal_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id),
            goal_label TEXT NOT NULL,
            dependency_node TEXT NOT NULL,
            tier_advanced TEXT,
            advancement_type TEXT NOT NULL,
            authored_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS drift_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id TEXT,
            indicator_type TEXT NOT NULL,
            description TEXT NOT NULL,
            detected_by TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'RAISED',
            resolution_note TEXT,
            raised_at TEXT NOT NULL,
            status_updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS eric_gate_approvals (
            id TEXT PRIMARY KEY,
            workflow_run_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            decided_at TEXT NOT NULL,
            decided_by TEXT NOT NULL DEFAULT 'Eric',
            goal_reference_id INTEGER NOT NULL,
            briefing_hash TEXT NOT NULL,
            briefing_json TEXT NOT NULL,
            drift_snapshot_json TEXT NOT NULL,
            decision_trail_snapshot_json TEXT NOT NULL,
            is_current INTEGER NOT NULL DEFAULT 1,
            supersedes_approval_id TEXT,
            rationale TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS advisor_escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id TEXT,
            trigger_class TEXT NOT NULL,
            trigger_reason TEXT NOT NULL,
            escalation_scope TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS decision_trails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id TEXT NOT NULL,
            trail_sequence INTEGER NOT NULL,
            problem_statement TEXT NOT NULL,
            proposed_action TEXT NOT NULL,
            round_count INTEGER NOT NULL DEFAULT 1,
            consensus_signal TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rejection_rationale (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_trail_id INTEGER NOT NULL,
            workflow_run_id TEXT NOT NULL,
            rejected_option_label TEXT NOT NULL,
            rejected_option_summary TEXT NOT NULL,
            rejection_reason TEXT NOT NULL,
            rejection_detail TEXT NOT NULL,
            rejected_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)


def seed_consensus_reached(conn):
    """Seed a clean CONSENSUS_REACHED run with deliberation."""
    run_id = "test-consensus-001"
    t = now()
    conn.execute(
        "INSERT OR REPLACE INTO workflow_runs "
        "(id, topic, result, max_rounds, status, created_at, completed_at) "
        "VALUES (?, ?, 'CONSENSUS_REACHED', 3, 'COMPLETE', ?, ?)",
        (run_id, "Test: consensus reached", t, t),
    )
    conn.execute(
        "INSERT OR REPLACE INTO deliberation_rounds "
        "(run_id, round_number, drafter_role, drafter_output, "
        "reviewer_role, reviewer_signal, created_at) "
        "VALUES (?, 1, 'Drafter', 'Test draft output', "
        "'Reviewer', 'OBJECTIONS', ?)",
        (run_id, t),
    )
    conn.execute(
        "INSERT OR REPLACE INTO deliberation_rounds "
        "(run_id, round_number, drafter_role, drafter_output, "
        "reviewer_role, reviewer_signal, created_at) "
        "VALUES (?, 2, 'Drafter', 'Revised draft', "
        "'Reviewer', 'CONSENSUS_REACHED', ?)",
        (run_id, t),
    )
    conn.execute(
        "INSERT OR REPLACE INTO goal_references "
        "(workflow_run_id, goal_label, dependency_node, tier_advanced, "
        "advancement_type, authored_by, created_at) "
        "VALUES (?, 'Test goal', 'Tier-TEST', 'Tier-TEST', "
        "'CLOSES_NODE', 'DRAFTER', ?)",
        (run_id, t),
    )
    return run_id


def seed_no_deliberation(conn):
    """Seed a run with no deliberation rounds."""
    run_id = "test-no-delib-001"
    t = now()
    conn.execute(
        "INSERT OR REPLACE INTO workflow_runs "
        "(id, topic, result, max_rounds, status, created_at) "
        "VALUES (?, ?, 'CONSENSUS_REACHED', 3, 'COMPLETE', ?)",
        (run_id, "Test: no deliberation", t),
    )
    conn.execute(
        "INSERT OR REPLACE INTO goal_references "
        "(workflow_run_id, goal_label, dependency_node, tier_advanced, "
        "advancement_type, authored_by, created_at) "
        "VALUES (?, 'Test goal', 'Tier-TEST', 'Tier-TEST', "
        "'CLOSES_NODE', 'DRAFTER', ?)",
        (run_id, t),
    )
    return run_id


def seed_with_drift(conn):
    """Seed a run with open blocking drift."""
    run_id = seed_consensus_reached(conn)
    t = now()
    conn.execute(
        "INSERT OR REPLACE INTO drift_indicators "
        "(workflow_run_id, indicator_type, description, "
        "detected_by, status, raised_at) "
        "VALUES (?, 'TEMPORARY_DEPENDENCY_NO_RETIREMENT', "
        "'Test drift indicator', 'GATE_SCRIPT', 'RAISED', ?)",
        (run_id, t),
    )
    return run_id


def seed_with_escalation(conn):
    """Seed a run with unreconciled mandatory escalation."""
    run_id = seed_consensus_reached(conn)
    t = now()
    conn.execute(
        "INSERT OR REPLACE INTO advisor_escalations "
        "(workflow_run_id, trigger_class, trigger_reason, "
        "escalation_scope, status, created_at) "
        "VALUES (?, 'MANDATORY', 'Test unreconciled escalation', "
        "'Component 3', 'OPEN', ?)",
        (run_id, t),
    )
    return run_id


def seed_approved(conn):
    """Seed a run with current APPROVE decision."""
    run_id = seed_consensus_reached(conn)
    goal_id = conn.execute(
        "SELECT id FROM goal_references WHERE workflow_run_id = ? LIMIT 1",
        (run_id,),
    ).fetchone()[0]
    t = now()
    briefing = json.dumps({
        "briefing_schema_version": "1.0.0",
        "workflow_run_id": run_id,
        "source_fingerprint": {"git_head": "0" * 40},
        "briefing": {
            "action_summary": {"plain_language_summary": "Test"},
            "goal_trace": {"goal_reference_id": goal_id},
            "decision_trail": {"problem": "Test"},
            "drift_indicators": {"open_drift_count": 0},
        },
    }, sort_keys=True, separators=(",", ":"))
    import hashlib
    hash_payload = json.loads(briefing)
    hash_payload.pop("generated_at", None)
    hash_val = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    conn.execute(
        "INSERT INTO eric_gate_approvals "
        "(id, workflow_run_id, decision, decided_at, goal_reference_id, "
        "briefing_hash, briefing_json, drift_snapshot_json, "
        "decision_trail_snapshot_json, is_current, created_at) "
        "VALUES (?, ?, 'APPROVE', ?, ?, ?, ?, '{}', '{}', 1, ?)",
        (f"ega-test-approved-{run_id}", run_id, t, goal_id,
         hash_val, briefing, t),
    )
    conn.execute(
        "UPDATE workflow_runs SET eric_approved_at = ?, updated_at = ? "
        "WHERE id = ?",
        (t, t, run_id),
    )
    return run_id


def seed_vetoed(conn):
    """Seed a run with current VETO decision."""
    run_id = seed_consensus_reached(conn)
    goal_id = conn.execute(
        "SELECT id FROM goal_references WHERE workflow_run_id = ? LIMIT 1",
        (run_id,),
    ).fetchone()[0]
    t = now()
    briefing = json.dumps({
        "briefing_schema_version": "1.0.0",
        "workflow_run_id": run_id,
        "source_fingerprint": {"git_head": "0" * 40},
        "briefing": {
            "action_summary": {"plain_language_summary": "Test"},
            "goal_trace": {"goal_reference_id": goal_id},
            "decision_trail": {"problem": "Test"},
            "drift_indicators": {"open_drift_count": 0},
        },
    }, sort_keys=True, separators=(",", ":"))
    import hashlib
    hash_payload = json.loads(briefing)
    hash_payload.pop("generated_at", None)
    hash_val = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    conn.execute(
        "INSERT INTO eric_gate_approvals "
        "(id, workflow_run_id, decision, decided_at, goal_reference_id, "
        "briefing_hash, briefing_json, drift_snapshot_json, "
        "decision_trail_snapshot_json, is_current, created_at) "
        "VALUES (?, ?, 'VETO', ?, ?, ?, ?, '{}', '{}', 1, ?)",
        (f"ega-test-vetoed-{run_id}", run_id, t, goal_id,
         hash_val, briefing, t),
    )
    return run_id


def seed_veto_then_approve(conn):
    """Seed VETO → APPROVE history."""
    run_id = seed_consensus_reached(conn)
    goal_id = conn.execute(
        "SELECT id FROM goal_references WHERE workflow_run_id = ? LIMIT 1",
        (run_id,),
    ).fetchone()[0]
    t1 = now()
    briefing = json.dumps({
        "briefing_schema_version": "1.0.0",
        "workflow_run_id": run_id,
        "source_fingerprint": {"git_head": "0" * 40},
        "briefing": {
            "action_summary": {"plain_language_summary": "Test"},
            "goal_trace": {"goal_reference_id": goal_id},
            "decision_trail": {"problem": "Test"},
            "drift_indicators": {"open_drift_count": 0},
        },
    }, sort_keys=True, separators=(",", ":"))
    import hashlib
    hash_payload = json.loads(briefing)
    hash_payload.pop("generated_at", None)
    hash_val = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    # VETO
    veto_id = f"ega-test-veto-{run_id}"
    conn.execute(
        "INSERT INTO eric_gate_approvals "
        "(id, workflow_run_id, decision, decided_at, goal_reference_id, "
        "briefing_hash, briefing_json, drift_snapshot_json, "
        "decision_trail_snapshot_json, is_current, created_at) "
        "VALUES (?, ?, 'VETO', ?, ?, ?, ?, '{}', '{}', 1, ?)",
        (veto_id, run_id, t1, goal_id, hash_val, briefing, t1),
    )

    # APPROVE supersedes VETO
    t2 = now()
    approve_id = f"ega-test-approve-{run_id}"
    conn.execute(
        "UPDATE eric_gate_approvals SET is_current = 0 WHERE id = ?",
        (veto_id,),
    )
    conn.execute(
        "INSERT INTO eric_gate_approvals "
        "(id, workflow_run_id, decision, decided_at, goal_reference_id, "
        "briefing_hash, briefing_json, drift_snapshot_json, "
        "decision_trail_snapshot_json, is_current, "
        "supersedes_approval_id, created_at) "
        "VALUES (?, ?, 'APPROVE', ?, ?, ?, ?, '{}', '{}', 1, ?, ?)",
        (approve_id, run_id, t2, goal_id, hash_val, briefing, veto_id, t2),
    )
    conn.execute(
        "UPDATE workflow_runs SET eric_approved_at = ?, updated_at = ? "
        "WHERE id = ?",
        (t2, t2, run_id),
    )
    return run_id


def clean(conn):
    """Remove all test data."""
    conn.execute("DELETE FROM eric_gate_approvals WHERE id LIKE 'ega-test-%' OR workflow_run_id LIKE 'test-%'")
    conn.execute(
        "DELETE FROM rejection_rationale WHERE workflow_run_id LIKE 'test-%'"
    )
    conn.execute(
        "DELETE FROM drift_indicators WHERE workflow_run_id LIKE 'test-%'"
    )
    conn.execute(
        "DELETE FROM advisor_escalations WHERE workflow_run_id LIKE 'test-%'"
    )
    conn.execute(
        "DELETE FROM decision_trails WHERE workflow_run_id LIKE 'test-%'"
    )
    conn.execute(
        "DELETE FROM deliberation_rounds WHERE run_id LIKE 'test-%'"
    )
    conn.execute(
        "DELETE FROM goal_references WHERE workflow_run_id LIKE 'test-%'"
    )
    conn.execute(
        "DELETE FROM workflow_runs WHERE id LIKE 'test-%'"
    )
    conn.execute("COMMIT")


SCENARIO_FUNCTIONS = {
    "consensus_reached": seed_consensus_reached,
    "no_deliberation": seed_no_deliberation,
    "with_drift": seed_with_drift,
    "with_escalation": seed_with_escalation,
    "approved": seed_approved,
    "vetoed": seed_vetoed,
    "veto_then_approve": seed_veto_then_approve,
    "stale_briefing": seed_approved,  # same as approved, mutation happens in test
    "clean": clean,
}


def main():
    parser = argparse.ArgumentParser(
        description="Eric Gate Test Fixture Seeder (Component 3)"
    )
    parser.add_argument(
        "--db-path", required=True,
        help="Database path (use temp copy, NOT live spine)",
    )
    parser.add_argument(
        "--scenario", required=True, choices=SCENARIOS,
        help="Test scenario to seed",
    )
    args = parser.parse_args()

    db_path = os.path.abspath(args.db_path)
    if db_path == os.path.abspath(SPINE_PATH):
        print("ERROR: Refusing to seed test data into live spine. "
              "Use --db-path to specify a temp copy.", file=sys.stderr)
        sys.exit(2)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        init_schema(conn)

        if args.scenario == "clean":
            clean(conn)
            print("Test data cleaned")
        else:
            run_id = SCENARIO_FUNCTIONS[args.scenario](conn)
            conn.commit()
            print(f"Scenario '{args.scenario}' seeded: {run_id}")
            if args.scenario in ("approved", "vetoed", "veto_then_approve"):
                rows = conn.execute(
                    "SELECT COUNT(*) FROM eric_gate_approvals "
                    "WHERE workflow_run_id = ?",
                    (run_id,),
                ).fetchone()[0]
                print(f"  Eric Gate rows: {rows}")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
