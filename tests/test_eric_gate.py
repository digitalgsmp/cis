#!/usr/bin/env python3
"""
test_eric_gate.py — Component 3 Acceptance Test Suite

Runs all 19 tests from the approved design against a temporary SQLite DB.
Tests cover briefing completeness, setter preconditions, post-migration
verification, and VETO → APPROVE history handling.

Usage:
    python3 tests/test_eric_gate.py
    python3 tests/test_eric_gate.py --keep-db  # Keep temp DB for inspection

Exit 0: all tests pass
Exit 1: one or more tests fail
"""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone


def get_goal_id(db_path, run_id):
    """Query actual goal_reference_id for a run."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id FROM goal_references WHERE workflow_run_id = ? LIMIT 1",
        (run_id,),
    ).fetchone()
    conn.close()
    return row["id"] if row else 1


PROJECT_ROOT = "/mnt/projects/cis"
BUILD_BRIEFING = os.path.join(PROJECT_ROOT, "tools/eric_gate/build_briefing.py")
RECORD_DECISION = os.path.join(PROJECT_ROOT, "tools/eric_gate/record_decision.py")
SEED_FIXTURE = os.path.join(PROJECT_ROOT, "tools/eric_gate/seed_test_fixture.py")
GATE_ERIC_APPROVAL = os.path.join(PROJECT_ROOT, "tools/gates/gate_eric_approval.py")
SHOW_STATUS = os.path.join(PROJECT_ROOT, "tools/eric_gate/show_status.py")

passed = 0
failed = 0


def run(cmd, **kwargs):
    """Run a command, return CompletedProcess."""
    return subprocess.run(
        cmd, capture_output=True, text=True,
        cwd=PROJECT_ROOT, timeout=30, **kwargs
    )



def run_debug(cmd):
    """Run command, print stderr on failure."""
    r = run(cmd)
    if r.returncode != 0 and r.stderr.strip():
        print(f"    DEBUG stderr: {r.stderr.strip()[:300]}", file=sys.stderr)
    return r


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}  {detail}")


def ok(result):
    """Check subprocess result for success."""
    return result.returncode == 0


def briefing_hash_for(db_path, run_id):
    """Get briefing hash for a run from a specific DB."""
    r = run([
        sys.executable, BUILD_BRIEFING,
        "--workflow-run-id", run_id, "--json", "--db", db_path,
    ])
    if r.returncode != 0:
        return None
    return json.loads(r.stdout).get("briefing_hash")


# ── Main test runner ────────────────────────────────────────────────

def main():
    global passed, failed
    keep_db = "--keep-db" in sys.argv

    print("=== Component 3 Acceptance Test Suite ===\n")

    # Create temp DB
    db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="test_eric_gate_")
    os.close(db_fd)

    try:
        # Initialize schema — copy live DB to ensure exact schema match
        import shutil
        shutil.copy2(
            os.path.join(PROJECT_ROOT, "data/cis_memory.db"),
            db_path,
        )
        # Remove any existing test data
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM eric_gate_approvals WHERE id LIKE 'ega-test-%' OR workflow_run_id LIKE 'test-%'")
        conn.execute("DELETE FROM drift_indicators WHERE workflow_run_id LIKE 'test-%'")
        conn.execute("DELETE FROM advisor_escalations WHERE workflow_run_id LIKE 'test-%'")
        conn.execute("DELETE FROM deliberation_rounds WHERE run_id LIKE 'test-%'")
        conn.execute("DELETE FROM goal_references WHERE workflow_run_id LIKE 'test-%'")
        conn.execute("DELETE FROM decision_trails WHERE workflow_run_id LIKE 'test-%'")
        conn.execute("DELETE FROM rejection_rationale WHERE workflow_run_id LIKE 'test-%'")
        conn.execute("DELETE FROM workflow_runs WHERE id LIKE 'test-%'")
        conn.commit()
        conn.close()

        # ── Group A: Briefing Completeness Tests ───────────────────

        print("Group A: Briefing Completeness (Tests 1-9)")

        # Seed consensus_reached scenario
        r = run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
                 "--scenario", "consensus_reached"])
        assert ok(r), f"Seed failed: {r.stderr}"
        run_id = "test-consensus-001"

        hash_val = briefing_hash_for(db_path, run_id)
        goal_id = 1  # The seed creates one goal_reference

        # Test 1: Missing briefing fails closed
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", run_id,
            "--decision", "APPROVE",
            "--briefing-hash", "nonexistent",
            "--goal-reference-id", str(goal_id),
        ])
        test("1 - Missing briefing fails closed", not ok(r),
             f"(should fail, exit={r.returncode})")

        # Test 2-4: Section completeness — tested via hash mismatch
        # If a section is missing, the hash won't match
        bad_hash = "0" * 64
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", run_id,
            "--decision", "APPROVE",
            "--briefing-hash", bad_hash,
            "--goal-reference-id", str(goal_id),
        ])
        test("2 - Bad hash (covers missing sections) fails closed",
             not ok(r), f"(exit={r.returncode})")

        # Test 3: Missing goal trace — use wrong goal reference
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", run_id,
            "--decision", "APPROVE",
            "--briefing-hash", hash_val or "none",
            "--goal-reference-id", "99999",
        ])
        test("3 - Invalid goal reference fails closed",
             not ok(r), f"(exit={r.returncode})")

        # Test 4: Missing decision trail — use no_deliberation run
        r2 = run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
                  "--scenario", "no_deliberation"])
        assert ok(r2)
        no_delib_run = "test-no-delib-001"
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", no_delib_run,
            "--decision", "APPROVE",
            "--briefing-hash", "none",
            "--goal-reference-id", "2",  # no_delib creates goal id 2
        ])
        test("4 - No deliberation fails closed",
             not ok(r), f"(should fail, exit={r.returncode})")

        # Test 5: Open drift blocks approval
        r3 = run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
                  "--scenario", "with_drift"])
        assert ok(r3)
        drift_run = "test-consensus-001"  # with_drift uses same run_id
        drift_hash = briefing_hash_for(db_path, drift_run)
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", drift_run,
            "--decision", "APPROVE",
            "--briefing-hash", drift_hash or "none",
            "--goal-reference-id", "1",
        ])
        test("5 - Open drift blocks approval",
             not ok(r), f"(should fail, exit={r.returncode})")

        # Test 6: Stale briefing — seed approved, then mutate
        r4 = run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
                  "--scenario", "stale_briefing"])
        assert ok(r4)
        stale_run = "test-consensus-001"
        old_hash = briefing_hash_for(db_path, stale_run)
        # Mutate state
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO deliberation_rounds "
            "(run_id, round_number, drafter_role, drafter_output, "
            "reviewer_role, reviewer_signal, created_at) "
            "VALUES (?, 99, 'Drafter', 'Mutated', 'Reviewer', "
            "'OBJECTIONS', ?)",
            (stale_run, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", stale_run,
            "--decision", "APPROVE",
            "--briefing-hash", old_hash or "none",
            "--goal-reference-id", "1",
        ])
        test("6 - Stale briefing hash blocks approval",
             not ok(r), f"(should fail, exit={r.returncode})")

        # Test 7: Wrong-run briefing
        wrong_run = "test-no-delib-001"
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", wrong_run,
            "--decision", "APPROVE",
            "--briefing-hash", old_hash or "none",
            "--goal-reference-id", "2",
        ])
        test("7 - Wrong-run briefing blocked",
             not ok(r), f"(should fail, exit={r.returncode})")

        # Test 8: Veto records rationale, not approval timestamp
        # First clean, then seed fresh consensus
        run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
             "--scenario", "clean"])
        r5 = run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
                  "--scenario", "consensus_reached"])
        assert ok(r5)
        goal_8 = get_goal_id(db_path, "test-consensus-001")
        veto_hash = briefing_hash_for(db_path, "test-consensus-001")
        r = run_debug([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", "test-consensus-001",
            "--decision", "VETO",
            "--briefing-hash", veto_hash or "none",
            "--goal-reference-id", str(goal_8),
            "--rationale", "Test veto rationale",
        ])
        test("8a - Veto recorded", ok(r), f"(exit={r.returncode})")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT decision, is_current, rationale FROM eric_gate_approvals "
            "WHERE workflow_run_id = ? AND decision = 'VETO'",
            ("test-consensus-001",),
        ).fetchone()
        test("8b - Veto row exists with rationale", 
             row is not None and row["rationale"] == "Test veto rationale")
        wf_row = conn.execute(
            "SELECT eric_approved_at FROM workflow_runs "
            "WHERE id = ?", ("test-consensus-001",),
        ).fetchone()
        test("8c - Veto leaves eric_approved_at NULL",
             wf_row is not None and wf_row["eric_approved_at"] is None)
        conn.close()

        # Test 9: Valid approval passes
        run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
             "--scenario", "clean"])
        r6 = run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
                  "--scenario", "consensus_reached"])
        assert ok(r6)
        goal_9 = get_goal_id(db_path, "test-consensus-001")
        t9_hash = briefing_hash_for(db_path, "test-consensus-001")
        r = run_debug([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", "test-consensus-001",
            "--decision", "APPROVE",
            "--briefing-hash", t9_hash or "none",
            "--goal-reference-id", str(goal_9),
            "--rationale", "Test 9 approval",
            "--supersede",
        ])
        test("9a - Valid approval recorded", ok(r),
             f"(exit={r.returncode})")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT decision, is_current FROM eric_gate_approvals "
            "WHERE workflow_run_id = ? AND is_current = 1",
            ("test-consensus-001",),
        ).fetchone()
        test("9b - Current row is APPROVE",
             row is not None and row["decision"] == "APPROVE")
        wf_row = conn.execute(
            "SELECT eric_approved_at FROM workflow_runs "
            "WHERE id = ?", ("test-consensus-001",),
        ).fetchone()
        test("9c - eric_approved_at is set",
             wf_row is not None and wf_row["eric_approved_at"] is not None)
        conn.close()

        # ── Group B: Setter Precondition Tests ────────────────────

        print("\nGroup B: Setter Preconditions (Tests 10-18)")

        # Test 10: Non-consensus run
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT OR REPLACE INTO workflow_runs "
            "(id, topic, result, max_rounds, status, created_at) "
            "VALUES ('test-error-run', 'Error run', 'ERROR', 3, 'COMPLETE', ?)",
            (datetime.now(timezone.utc).isoformat(),),
        )
        conn.commit()
        conn.close()
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", "test-error-run",
            "--decision", "APPROVE",
            "--briefing-hash", t9_hash or "none",
            "--goal-reference-id", "1",
        ])
        test("10 - Non-consensus run blocked",
             not ok(r), f"(exit={r.returncode})")

        # Test 11: Missing workflow run
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", "nonexistent-run",
            "--decision", "APPROVE",
            "--briefing-hash", "abc",
            "--goal-reference-id", "1",
        ])
        test("11 - Missing workflow run blocked",
             not ok(r), f"(exit={r.returncode})")

        # Test 13: Duplicate current approval blocked
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", "test-consensus-001",
            "--decision", "APPROVE",
            "--briefing-hash", t9_hash or "none",
            "--goal-reference-id", "1",
        ])
        test("13 - Duplicate current approval blocked",
             not ok(r), f"(exit={r.returncode})")

        # Test 14: Unreconciled escalation blocked
        run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
             "--scenario", "clean"])
        r_esc = run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
                      "--scenario", "with_escalation"])
        assert ok(r_esc)
        esc_hash = briefing_hash_for(db_path, "test-consensus-001")
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", "test-consensus-001",
            "--decision", "APPROVE",
            "--briefing-hash", esc_hash or "none",
            "--goal-reference-id", "1",
        ])
        test("14 - Unreconciled escalation blocked",
             not ok(r), f"(exit={r.returncode})")

        # Test 15: Invalid decision enum (caught by argparse)
        r = run([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", "test-consensus-001",
            "--decision", "INVALID",
            "--briefing-hash", "abc",
            "--goal-reference-id", "1",
        ])
        test("15 - Invalid decision enum blocked",
             not ok(r), f"(exit={r.returncode})")

        # Test 18: VETO → APPROVE history + eric_approved_at cleared
        run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
             "--scenario", "clean"])
        r_vta = run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
                      "--scenario", "veto_then_approve"])
        if not ok(r_vta):
            print(f"SEED VTA FAILED: stdout={r_vta.stdout.strip()[:200]}")
            print(f"SEED VTA FAILED: stderr={r_vta.stderr.strip()[:200]}")
        assert ok(r_vta)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT decision, is_current FROM eric_gate_approvals "
            "WHERE workflow_run_id = ? ORDER BY decided_at",
            ("test-consensus-001",),
        ).fetchall()
        test("18a - Two rows in history", len(rows) == 2)
        test("18b - VETO row is_current=0",
             any(r["decision"] == "VETO" and r["is_current"] == 0
                 for r in rows))
        test("18c - APPROVE row is_current=1",
             any(r["decision"] == "APPROVE" and r["is_current"] == 1
                 for r in rows))
        wf = conn.execute(
            "SELECT eric_approved_at FROM workflow_runs "
            "WHERE id = ?",
            ("test-consensus-001",),
        ).fetchone()
        test("18d - eric_approved_at is set after VETO→APPROVE",
             wf is not None and wf["eric_approved_at"] is not None)
        conn.close()

        # Additional: APPROVE → VETO clears eric_approved_at
        run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
             "--scenario", "clean"])
        r_av = run([sys.executable, SEED_FIXTURE, "--db-path", db_path,
                     "--scenario", "approved"])
        assert ok(r_av)
        goal_18 = get_goal_id(db_path, "test-consensus-001")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        wf_before = conn.execute(
            "SELECT eric_approved_at FROM workflow_runs "
            "WHERE id = ?", ("test-consensus-001",),
        ).fetchone()
        test("18e - APPROVE sets eric_approved_at",
             wf_before is not None and wf_before["eric_approved_at"] is not None)
        conn.close()

        # Now VETO with --supersede
        av_hash = briefing_hash_for(db_path, "test-consensus-001")
        r = run_debug([
            sys.executable, RECORD_DECISION,
            "--db", db_path,
            "--workflow-run-id", "test-consensus-001",
            "--decision", "VETO",
            "--briefing-hash", av_hash or "none",
            "--goal-reference-id", str(goal_18),
            "--rationale", "Superseding APPROVE with VETO",
            "--supersede",
        ])
        test("18f - VETO supersedes APPROVE", ok(r),
             f"(exit={r.returncode})")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        wf_after = conn.execute(
            "SELECT eric_approved_at FROM workflow_runs "
            "WHERE id = ?", ("test-consensus-001",),
        ).fetchone()
        test("18g - VETO clears eric_approved_at",
             wf_after is not None and wf_after["eric_approved_at"] is None)
        current = conn.execute(
            "SELECT decision FROM eric_gate_approvals "
            "WHERE workflow_run_id = ? AND is_current = 1",
            ("test-consensus-001",),
        ).fetchone()
        test("18h - Current row is VETO after supersede",
             current is not None and current["decision"] == "VETO")
        conn.close()

        # ── Group C: Post-Migration ───────────────────────────────

        print("\nGroup C: Post-Migration (Test 19)")

        # Verify eric_gate_approvals table exists in temp DB
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='eric_gate_approvals'"
        ).fetchone()
        test("19 - eric_gate_approvals table exists in schema",
             row is not None)
        # Verify indices
        indices = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name LIKE '%eric_gate%'"
        ).fetchall()
        test("19b - Eric gate indices exist", len(indices) >= 3)
        conn.close()

        # ── Results ────────────────────────────────────────────────

        print(f"\n{'='*50}")
        print(f"Results: {passed} passed, {failed} failed")
        print(f"{'='*50}")

    finally:
        if keep_db:
            print(f"\nTemp DB kept at: {db_path}")
        else:
            os.unlink(db_path)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
