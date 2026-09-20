#!/usr/bin/env python3
"""test_discovery.py — CARD 3 behavioral tests for discovery.py.

Temporary SQLite fixtures only. Run: python3 tools/development/tests/test_discovery.py
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from tools.development import continuity_store as cs
from tools.development import discovery

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def make_fixture_db(path):
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE queue_items (
            item_num TEXT PRIMARY KEY, tier INTEGER, title TEXT,
            body_md TEXT, form TEXT, scope TEXT, need_status TEXT,
            need_raw TEXT, source_line INTEGER, source_sha TEXT,
            extracted_at TEXT, status_changed_at TEXT, status_changed_by TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO queue_items (item_num, tier, title, body_md, form, need_status, "
        "source_line, source_sha) VALUES ('WB.1TEST', 0, 'Test task', 'body', 'heading', 'OPEN', 1, 'x')"
    )
    conn.commit()
    return conn


def test_valid_dispositions_accepted():
    tmp = tempfile.mkdtemp(prefix="dev_discovery_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        r1 = discovery.record_discovery(
            conn, task="WB.1TEST", actor="claude_code", summary="Found X, handled inline",
            disposition="RESOLVED_NOW", resolution_result="Fixed in the same edit, tests re-run.",
            expected_prev_revision=0,
        )
        check("valid RESOLVED_NOW accepted", r1["revision"] == 1, r1)

        r2 = discovery.record_discovery(
            conn, task="WB.1TEST", actor="claude_code", summary="Needs a decision before this stage closes",
            disposition="BEFORE_STAGE_CLOSEOUT", originating_stage="WB.1TEST", blocking=True,
            expected_prev_revision=1,
        )
        check("valid BEFORE_STAGE_CLOSEOUT accepted", r2["revision"] == 2, r2)

        r3 = discovery.record_discovery(
            conn, task="WB.1TEST", actor="claude_code", summary="Genuinely downstream work",
            disposition="EXPLICITLY_DEFERRED", reason="Belongs to the contained pipeline, not the host.",
            destination="WB.2", trigger="When WB.2 starts.", blocking=False,
            expected_prev_revision=2,
        )
        check("valid EXPLICITLY_DEFERRED accepted", r3["revision"] == 3, r3)

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_invalid_records_rejected():
    tmp = tempfile.mkdtemp(prefix="dev_discovery_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        try:
            discovery.record_discovery(
                conn, task="WB.1TEST", actor="claude_code", summary="no disposition given",
                disposition="NOT_A_REAL_DISPOSITION", expected_prev_revision=0,
            )
            check("missing/unknown disposition rejected", False, "no exception raised")
        except discovery.DiscoveryValidationError:
            check("missing/unknown disposition rejected", True)

        try:
            discovery.record_discovery(
                conn, task="WB.1TEST", actor="claude_code", summary="deferred, no destination",
                disposition="EXPLICITLY_DEFERRED", reason="some reason", trigger="some trigger",
                blocking=False, expected_prev_revision=0,
            )
            check("deferred item missing destination rejected", False, "no exception raised")
        except discovery.DiscoveryValidationError:
            check("deferred item missing destination rejected", True)

        try:
            discovery.record_discovery(
                conn, task="WB.1TEST", actor="claude_code", summary="deferred, no reason",
                disposition="EXPLICITLY_DEFERRED", destination="WB.2", trigger="some trigger",
                blocking=False, expected_prev_revision=0,
            )
            check("deferred item missing reason rejected", False, "no exception raised")
        except discovery.DiscoveryValidationError:
            check("deferred item missing reason rejected", True)

        try:
            discovery.record_discovery(
                conn, task="WB.1TEST", actor="claude_code", summary="deferred, no trigger",
                disposition="EXPLICITLY_DEFERRED", destination="WB.2", reason="x",
                blocking=False, expected_prev_revision=0,
            )
            check("deferred item missing trigger/dependency rejected", False, "no exception raised")
        except discovery.DiscoveryValidationError:
            check("deferred item missing trigger/dependency rejected", True)

        try:
            discovery.record_discovery(
                conn, task="WB.1TEST", actor="claude_code", summary="closeout item, no stage",
                disposition="BEFORE_STAGE_CLOSEOUT", blocking=True, expected_prev_revision=0,
            )
            check("before-stage-closeout item missing originating_stage rejected", False, "no exception raised")
        except discovery.DiscoveryValidationError:
            check("before-stage-closeout item missing originating_stage rejected", True)

        try:
            discovery.record_discovery(
                conn, task="WB.1TEST", actor="claude_code", summary="resolved now, no result",
                disposition="RESOLVED_NOW", expected_prev_revision=0,
            )
            check("RESOLVED_NOW item missing resolution_result rejected", False, "no exception raised")
        except discovery.DiscoveryValidationError:
            check("RESOLVED_NOW item missing resolution_result rejected", True)

        count = conn.execute(
            "SELECT count(*) FROM dev_continuity_events WHERE task='WB.1TEST'"
        ).fetchone()[0]
        check("none of the six rejected attempts wrote a row (rejected before write, not after)",
              count == 0, count)

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_closeout_gate_behavior():
    tmp = tempfile.mkdtemp(prefix="dev_discovery_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        clean = discovery.check_closeout(conn, "WB.1TEST")
        check("clean state (no events at all) returns ready_to_close=True",
              clean["ready_to_close"] is True and clean["blockers"] == [], clean)
        check("machine-readable result exists (JSON-serializable dict with required keys)",
              json.dumps(clean) and {"task", "ready_to_close", "blockers", "evidence_checked"} <= set(clean), clean)

        r_closeout = discovery.record_discovery(
            conn, task="WB.1TEST", actor="claude_code", summary="must resolve before closing",
            disposition="BEFORE_STAGE_CLOSEOUT", originating_stage="WB.1TEST", blocking=True,
            expected_prev_revision=0,
        )
        blocked = discovery.check_closeout(conn, "WB.1TEST")
        check("unresolved BEFORE_STAGE_CLOSEOUT item blocks closeout",
              blocked["ready_to_close"] is False and
              any(b["type"] == "unresolved_before_stage_closeout" and b["revision"] == r_closeout["revision"]
                  for b in blocked["blockers"]),
              blocked)

        discovery.resolve_discovery(
            conn, task="WB.1TEST", actor="claude_code", discovery_revision=r_closeout["revision"],
            resolution_result="Decision made: proceed with option A.",
            expected_prev_revision=r_closeout["revision"],
        )
        resolved = discovery.check_closeout(conn, "WB.1TEST")
        check("resolved item stops blocking", resolved["ready_to_close"] is True, resolved)

        # A RESOLVED_NOW item never blocks in the first place. (revision 2
        # was consumed by the reconciliation event resolve_discovery() just
        # published, so the next event is revision 3.)
        r_resolved_now = discovery.record_discovery(
            conn, task="WB.1TEST", actor="claude_code", summary="handled inline",
            disposition="RESOLVED_NOW", resolution_result="done", expected_prev_revision=2,
        )
        still_clean = discovery.check_closeout(conn, "WB.1TEST")
        check("RESOLVED_NOW item never blocks closeout", still_clean["ready_to_close"] is True, still_clean)

        # A validly-formed EXPLICITLY_DEFERRED item never blocks THIS task.
        discovery.record_discovery(
            conn, task="WB.1TEST", actor="claude_code", summary="genuinely downstream",
            disposition="EXPLICITLY_DEFERRED", reason="downstream work", destination="WB.2",
            trigger="on WB.2 start", blocking=False,
            expected_prev_revision=r_resolved_now["revision"],
        )
        still_clean2 = discovery.check_closeout(conn, "WB.1TEST")
        check("validly-formed EXPLICITLY_DEFERRED item never blocks this task's closeout",
              still_clean2["ready_to_close"] is True, still_clean2)

        # Unrelated task's own open discovery must not block THIS task.
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, need_status, "
            "source_line, source_sha) VALUES ('WB.1OTHER', 0, 'x', 'y', 'heading', 'OPEN', 1, 'x')"
        )
        conn.commit()
        discovery.record_discovery(
            conn, task="WB.1OTHER", actor="claude_code", summary="a different task's blocker",
            disposition="BEFORE_STAGE_CLOSEOUT", originating_stage="WB.1OTHER", blocking=True,
            expected_prev_revision=0,
        )
        still_clean3 = discovery.check_closeout(conn, "WB.1TEST")
        check("unrelated task's own open discovery does not block this task",
              still_clean3["ready_to_close"] is True, still_clean3)
        other_blocked = discovery.check_closeout(conn, "WB.1OTHER")
        check("...but it DOES correctly block that other task's own closeout",
              other_blocked["ready_to_close"] is False, other_blocked)

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_malformed_deferral_blocks_closeout():
    """A discovery-tagged event that somehow reached the database in a
    broken state (bypassing record_discovery's own validation — simulated
    here via a direct publish_event call, the way a future caller outside
    this module's own writer might) must still be caught and block
    closeout, not be silently treated as valid."""
    tmp = tempfile.mkdtemp(prefix="dev_discovery_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        broken_payload = json.dumps({
            "_record_type": "discovery", "disposition": "EXPLICITLY_DEFERRED",
            # deliberately missing destination/trigger/blocking
            "reason": "incomplete on purpose",
        })
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="unfinished_work", status="EXPLICITLY_DEFERRED",
            actor="claude_code", summary="malformed deferral", body=broken_payload,
            expected_prev_revision=0,
        )
        listed = discovery.list_discoveries(conn, "WB.1TEST")
        check("malformed deferral is detected as malformed by list_discoveries",
              any(d["revision"] == row["revision"] and d["malformed"] for d in listed), listed)

        result = discovery.check_closeout(conn, "WB.1TEST")
        check("malformed deferral blocks closeout",
              result["ready_to_close"] is False and
              any(b["type"] == "malformed_deferral_or_discovery" and b["revision"] == row["revision"]
                  for b in result["blockers"]),
              result)

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_plain_unfinished_work_and_contradiction_block():
    """Non-discovery-tagged unfinished_work/contradiction events (the kind
    R1/R2 already used for ordinary during-work notes) are also checked by
    the closeout gate on their own terms, per Card 3's explicit
    requirement — separate from the discovery-disposition system."""
    tmp = tempfile.mkdtemp(prefix="dev_discovery_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        plain = cs.publish_event(
            conn, task="WB.1TEST", kind="unfinished_work", status="open", actor="codex",
            summary="a plain unfinished-work note, not a discovery record",
            expected_prev_revision=0,
        )
        result = discovery.check_closeout(conn, "WB.1TEST")
        check("plain (non-discovery) unfinished_work event blocks closeout",
              result["ready_to_close"] is False and
              any(b["type"] == "unresolved_unfinished_work" and b["revision"] == plain["revision"]
                  for b in result["blockers"]),
              result)

        contra = cs.publish_event(
            conn, task="WB.1TEST", kind="contradiction", status="unresolved", actor="codex",
            summary="an unresolved contradiction", expected_prev_revision=plain["revision"],
        )
        result2 = discovery.check_closeout(conn, "WB.1TEST")
        check("unresolved contradiction event also blocks closeout",
              any(b["type"] == "unresolved_contradiction" and b["revision"] == contra["revision"]
                  for b in result2["blockers"]),
              result2)

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_dev_schema_not_initialized_blocks():
    tmp = tempfile.mkdtemp(prefix="dev_discovery_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        # Deliberately do NOT init_schema — simulates a database that
        # hasn't had migration 0039 applied yet.
        result = discovery.check_closeout(conn, "WB.1TEST")
        check("uninitialized dev_continuity schema is itself a blocker (machine-readable)",
              result["ready_to_close"] is False and
              any(b["type"] == "dev_continuity_not_initialized" for b in result["blockers"]),
              result)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cli_enforcement_exit_codes():
    """CLI: machine-readable output always; nonzero exit exactly when
    blocked, zero exactly when clean — the enforcement contract."""
    tmp = tempfile.mkdtemp(prefix="dev_discovery_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        conn.close()

        clean_proc = subprocess.run(
            [sys.executable, "-m", "tools.development.cli", "--db", db, "closeout-check", "WB.1TEST"],
            cwd=os.path.join(os.path.dirname(__file__), "..", "..", ".."),
            capture_output=True, text=True,
        )
        check("cli closeout-check: clean state returns exit 0", clean_proc.returncode == 0, clean_proc.stdout)
        parsed_clean = json.loads(clean_proc.stdout)
        check("cli closeout-check: clean output is valid JSON with ready_to_close true",
              parsed_clean["ready_to_close"] is True, clean_proc.stdout)

        record_proc = subprocess.run(
            [sys.executable, "-m", "tools.development.cli", "--db", db, "discovery-record", "WB.1TEST",
             "--actor", "claude_code", "--summary", "blocks closeout",
             "--disposition", "BEFORE_STAGE_CLOSEOUT", "--originating-stage", "WB.1TEST",
             "--blocking", "true", "--expect-revision", "0"],
            cwd=os.path.join(os.path.dirname(__file__), "..", "..", ".."),
            capture_output=True, text=True,
        )
        check("cli discovery-record: valid record exits 0", record_proc.returncode == 0, record_proc.stdout)

        blocked_proc = subprocess.run(
            [sys.executable, "-m", "tools.development.cli", "--db", db, "closeout-check", "WB.1TEST"],
            cwd=os.path.join(os.path.dirname(__file__), "..", "..", ".."),
            capture_output=True, text=True,
        )
        check("cli closeout-check: enforcement command returns nonzero on blocker",
              blocked_proc.returncode == 1, blocked_proc.stdout)
        parsed_blocked = json.loads(blocked_proc.stdout)
        check("cli closeout-check: blocked output clearly identifies the blocking item's revision",
              parsed_blocked["blockers"][0]["revision"] == 1, blocked_proc.stdout)

        rejected_proc = subprocess.run(
            [sys.executable, "-m", "tools.development.cli", "--db", db, "discovery-record", "WB.1TEST",
             "--actor", "claude_code", "--summary", "bad deferral",
             "--disposition", "EXPLICITLY_DEFERRED", "--expect-revision", "1"],
            cwd=os.path.join(os.path.dirname(__file__), "..", "..", ".."),
            capture_output=True, text=True,
        )
        check("cli discovery-record: invalid record rejected with exit 2",
              rejected_proc.returncode == 2 and "BLOCKED" in rejected_proc.stderr, rejected_proc.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    test_valid_dispositions_accepted()
    test_invalid_records_rejected()
    test_closeout_gate_behavior()
    test_malformed_deferral_blocks_closeout()
    test_plain_unfinished_work_and_contradiction_block()
    test_dev_schema_not_initialized_blocks()
    test_cli_enforcement_exit_codes()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
