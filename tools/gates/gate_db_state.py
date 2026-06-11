#!/usr/bin/env python3
"""
gate_db_state.py — Deterministic SQLite Spine Verification Gate
Tier 4.3 — Query cis_memory.db for expected values via allowlisted tables/columns.

Usage:
    gate_db_state.py value <table> <check_column> <expected_value>
        --where <col> <val> [--where <col> <val> ...]
    
    gate_db_state.py count <table> <expected_count>
        --where <col> <val> [--where <col> <val> ...]
    
    gate_db_state.py not-null <table> <check_column>
        --where <col> <val> [--where <col> <val> ...]

Exit 0: PASS — query matches expected
Exit 1: FAIL — query returned wrong value/count or NULL
Exit 2: ERROR — usage, config, DB, or allowlist error
"""

import sys
import sqlite3
import argparse
from pathlib import Path


DEFAULT_DB = "/mnt/projects/cis/data/cis_memory.db"

ALLOWED_TABLES = {
    "workflow_runs",
    "deliberation_rounds",
    "project_decisions",
    "open_questions",
    "next_actions",
    "active_blockers",
    "workflow_run_artifacts",
    "workflow_run_legacy_links",
    "project_state",
    "goal_references",
    "decision_trails",
    "drift_indicators",
    "rejection_rationale",
    "advisor_escalations",
    "advisor_escalation_packets",
    "advisor_responses",
    "eric_gate_approvals",
}

ALLOWED_COLUMNS = {
    # workflow_runs
    "id", "topic", "result", "status", "route", "updated_at",
    "requires_eric_review", "max_rounds", "max_consecutive_revisions",
    "rounds_completed", "final_objections_json", "created_at", "completed_at",
    "eric_approved_at",
    # deliberation_rounds
    "run_id", "round_number", "drafter_role", "drafter_output",
    "reviewer_role", "reviewer_signal", "objections_json", "revision_number",
    # project_decisions
    "label", "decision", "reason", "status", "decided_at", "superseded_by",
    # open_questions
    "question", "resolution", "opened_at", "resolved_at",
    # next_actions
    "tier", "description", "depends_on", "updated_at",
    # active_blockers (id, description, status, resolution, created_at, resolved_at covered above)
    # project_state columns
    "key", "value", "source", "evidence_hash", "evidence_run_id", "superseded_at",
    # advisor_escalations
    "workflow_run_id", "trigger_class", "trigger_reason", "escalation_scope",
    "reconciliation_disposition", "reconciliation_note",
    "advisor_divergence_summary", "advisor_positions_json",
    "reconciled_at", "abandoned_at", "abandoned_reason", "superseded_by",
    # advisor_escalation_packets
    "escalation_id", "packet_version", "packet_raw", "packet_hash",
    "git_head", "advisor_target", "requested_response_type", "packet_status",
    "transmitted_at",
    # advisor_responses
    "packet_id", "advisor", "transmission_mode", "response_raw",
    "responded_packet_hash", "hash_match_status",
    "primary_type", "secondary_flags",
    "classification_source", "classification_status",
    "response_status", "received_at", "ingested_at",
    # eric_gate_approvals
    "decision", "decided_at", "decided_by",
    "goal_reference_id", "briefing_hash", "briefing_json",
    "drift_snapshot_json", "decision_trail_snapshot_json",
    "is_current", "supersedes_approval_id", "rationale",
}


def fail(code, msg):
    print(f"FAIL: {msg}")
    sys.exit(code)


def error(msg):
    print(f"ERROR: {msg}")
    sys.exit(2)


def validate_table(table):
    if table not in ALLOWED_TABLES:
        error(f"Table '{table}' not allowlisted. Allowed: {', '.join(sorted(ALLOWED_TABLES))}")


def validate_column(col):
    if col not in ALLOWED_COLUMNS:
        error(f"Column '{col}' not allowlisted.")


def build_where(where_pairs):
    """Build WHERE clause and params from list of (col, val) pairs."""
    if not where_pairs:
        error("At least one --where <column> <value> pair is required.")
    clauses = []
    params = []
    for col, val in where_pairs:
        validate_column(col)
        clauses.append(f"{col} = ?")
        params.append(val)
    return " AND ".join(clauses), params


def cmd_value(args):
    """Check that check_column equals expected_value for rows matching WHERE."""
    validate_table(args.table)
    validate_column(args.check_column)
    where_clause, params = build_where(args.where)
    db_path = args.db or DEFAULT_DB

    if not Path(db_path).exists():
        error(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        row = conn.execute(
            f"SELECT {args.check_column} FROM {args.table} WHERE {where_clause}",
            params,
        ).fetchone()
    except sqlite3.Error as e:
        error(f"Database error: {e}")
    finally:
        conn.close()

    if row is None:
        fail(1, f"no row matching WHERE in {args.table}")
    actual = row[0]
    if str(actual) != str(args.expected_value):
        fail(1, f"expected '{args.expected_value}', got '{actual}'")
    print(f"PASS: {args.table}.{args.check_column} = '{args.expected_value}'")
    sys.exit(0)


def cmd_count(args):
    """Check that COUNT(*) equals expected_count for rows matching WHERE."""
    validate_table(args.table)
    where_clause, params = build_where(args.where)
    db_path = args.db or DEFAULT_DB

    try:
        expected = int(args.expected_count)
    except ValueError:
        error(f"Expected count must be an integer: {args.expected_count}")

    if not Path(db_path).exists():
        error(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        row = conn.execute(
            f"SELECT COUNT(*) FROM {args.table} WHERE {where_clause}",
            params,
        ).fetchone()
    except sqlite3.Error as e:
        error(f"Database error: {e}")
    finally:
        conn.close()

    actual = row[0]
    if actual != expected:
        fail(1, f"expected count {expected}, got {actual}")
    print(f"PASS: COUNT({args.table}) = {actual}")
    sys.exit(0)


def cmd_not_null(args):
    """Check that check_column is not NULL for rows matching WHERE."""
    validate_table(args.table)
    validate_column(args.check_column)
    where_clause, params = build_where(args.where)
    db_path = args.db or DEFAULT_DB

    if not Path(db_path).exists():
        error(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        row = conn.execute(
            f"SELECT {args.check_column} FROM {args.table} WHERE {where_clause}",
            params,
        ).fetchone()
    except sqlite3.Error as e:
        error(f"Database error: {e}")
    finally:
        conn.close()

    if row is None:
        fail(1, f"no row matching WHERE in {args.table}")
    actual = row[0]
    if actual is None:
        fail(1, f"column {args.check_column} is NULL")
    print(f"PASS: {args.table}.{args.check_column} is not NULL")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic SQLite spine verification gate"
    )
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Database path (default: {DEFAULT_DB})")
    sub = parser.add_subparsers(dest="command", required=True)

    # value
    pv = sub.add_parser("value", help="Check exact column value")
    pv.add_argument("table", help="Allowlisted table name")
    pv.add_argument("check_column", help="Column to check")
    pv.add_argument("expected_value", help="Expected value")
    pv.add_argument("--where", nargs=2, action="append", dest="where",
                    metavar=("COL", "VAL"), required=True,
                    help="WHERE filter (repeatable)")

    # count
    pc = sub.add_parser("count", help="Check row count")
    pc.add_argument("table", help="Allowlisted table name")
    pc.add_argument("expected_count", help="Expected count")
    pc.add_argument("--where", nargs=2, action="append", dest="where",
                    metavar=("COL", "VAL"), required=True,
                    help="WHERE filter (repeatable)")

    # not-null
    pn = sub.add_parser("not-null", help="Check column is not NULL")
    pn.add_argument("table", help="Allowlisted table name")
    pn.add_argument("check_column", help="Column to check")
    pn.add_argument("--where", nargs=2, action="append", dest="where",
                    metavar=("COL", "VAL"), required=True,
                    help="WHERE filter (repeatable)")

    args = parser.parse_args()

    if args.command == "value":
        cmd_value(args)
    elif args.command == "count":
        cmd_count(args)
    elif args.command == "not-null":
        cmd_not_null(args)


if __name__ == "__main__":
    main()
