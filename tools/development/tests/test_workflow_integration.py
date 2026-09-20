#!/usr/bin/env python3
"""test_workflow_integration.py — CARD 4 behavioral tests for
discovery.close_task/verify_closeout and card_contract.py.

Temporary SQLite fixtures only. Run:
    python3 tools/development/tests/test_workflow_integration.py
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from tools.development import card_contract
from tools.development import continuity_store as cs
from tools.development import discovery

results = []
REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")


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
        CREATE TABLE queue_item_events (
            id INTEGER PRIMARY KEY, item_num TEXT, field TEXT,
            old_value TEXT, new_value TEXT, changed_at TEXT,
            changed_by TEXT, evidence TEXT, note TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO queue_items (item_num, tier, title, body_md, form, need_status, "
        "source_line, source_sha) VALUES ('WB.1TEST', 0, 'Test task', 'body', 'heading', 'OPEN', 1, 'x')"
    )
    conn.commit()
    return conn


def test_close_task_integration_calls_closeout_validation():
    """close_task() must call check_closeout() — proven by observing its
    behavior track check_closeout()'s own, not merely returning success
    unconditionally."""
    tmp = tempfile.mkdtemp(prefix="dev_wfi_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        clean = discovery.check_closeout(conn, "WB.1TEST")
        row = discovery.close_task(
            conn, task="WB.1TEST", actor="claude_code", expected_prev_revision=0,
        )
        check("close_task: clean state allows the claimed completion path",
              row["status"] == "stage_closed" and row["revision"] == 1, row)
        check("close_task: durable record embeds the actual check_closeout() result",
              json.loads(row["body"])["ready_to_close"] == clean["ready_to_close"] == True, row)

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_close_task_blocking_state_prevents_completion():
    tmp = tempfile.mkdtemp(prefix="dev_wfi_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        blocker = discovery.record_discovery(
            conn, task="WB.1TEST", actor="claude_code", summary="must resolve first",
            disposition="BEFORE_STAGE_CLOSEOUT", originating_stage="WB.1TEST", blocking=True,
            expected_prev_revision=0,
        )
        try:
            discovery.close_task(
                conn, task="WB.1TEST", actor="claude_code",
                expected_prev_revision=blocker["revision"],
            )
            check("close_task: blocking state prevents the claimed completion path", False,
                  "no exception raised")
        except discovery.CloseoutBlockedError as e:
            check("close_task: blocking state prevents the claimed completion path", True)
            check("close_task: refusal names the actual blocker",
                  any(b["revision"] == blocker["revision"] for b in e.result["blockers"]), e.result)

        count = conn.execute(
            "SELECT count(*) FROM dev_continuity_events WHERE task='WB.1TEST' AND status='stage_closed'"
        ).fetchone()[0]
        check("close_task: refused closeout writes nothing (no stage_closed row)", count == 0, count)

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_malformed_deferral_fails_close_task():
    tmp = tempfile.mkdtemp(prefix="dev_wfi_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        broken_payload = json.dumps({
            "_record_type": "discovery", "disposition": "EXPLICITLY_DEFERRED",
            "reason": "incomplete on purpose",
        })
        row = cs.publish_event(
            conn, task="WB.1TEST", kind="unfinished_work", status="EXPLICITLY_DEFERRED",
            actor="claude_code", summary="malformed deferral", body=broken_payload,
            expected_prev_revision=0,
        )
        try:
            discovery.close_task(conn, task="WB.1TEST", actor="claude_code",
                                  expected_prev_revision=row["revision"])
            check("malformed deferral fails close_task", False, "no exception raised")
        except discovery.CloseoutBlockedError as e:
            check("malformed deferral fails close_task", True)
            check("malformed deferral: refusal identifies it by type",
                  any(b["type"] == "malformed_deferral_or_discovery" for b in e.result["blockers"]),
                  e.result)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_verify_closeout_level_3():
    """verify_closeout must re-derive from current state, not trust a
    stale past success."""
    tmp = tempfile.mkdtemp(prefix="dev_wfi_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        never = discovery.verify_closeout(conn, "WB.1TEST")
        check("verify_closeout: never-closed task reports verified=False",
              never["verified"] is False, never)

        closed = discovery.close_task(conn, task="WB.1TEST", actor="claude_code",
                                       expected_prev_revision=0)
        ok = discovery.verify_closeout(conn, "WB.1TEST")
        check("verify_closeout: freshly closed clean task reports verified=True",
              ok["verified"] is True and ok["closed_at_revision"] == closed["revision"], ok)

        # A NEW blocker appearing after closure must make verify_closeout
        # report False again — it must not trust the stale past success.
        discovery.record_discovery(
            conn, task="WB.1TEST", actor="codex", summary="found after closure",
            disposition="BEFORE_STAGE_CLOSEOUT", originating_stage="WB.1TEST", blocking=True,
            expected_prev_revision=closed["revision"],
        )
        stale = discovery.verify_closeout(conn, "WB.1TEST")
        check("verify_closeout: a NEW blocker after closure flips verified back to False "
              "(does not trust the stale past success)",
              stale["verified"] is False and "current_blockers" in stale, stale)

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_launcher_stale_packet_refusal_still_active():
    """Confirms the existing R1 mechanism (launch_with_packet refuses a
    stale packet) is still exactly as strong post-Card-4 — 'stale
    continuity state should prevent sanctioned dependent handoff where
    already supported' was already achieved before this card; this proves
    it was not weakened."""
    tmp = tempfile.mkdtemp(prefix="dev_wfi_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        from tools.development import packet as packet_mod
        from tools.development import launcher

        pkt = packet_mod.prepare_packet(conn, task="WB.1TEST", actor="claude_code")
        cs.publish_event(conn, task="WB.1TEST", kind="decision", status="x", actor="codex",
                          summary="invalidate", expected_prev_revision=0)
        fake = os.path.join(tmp, "fake_claude.sh")
        with open(fake, "w") as f:
            f.write("#!/bin/sh\ncat >/dev/null\necho ran\n")
        os.chmod(fake, 0o755)
        result = launcher.launch_with_packet(conn, fake, pkt, tmp, tool="claude", dry_run=False)
        check("launch_with_packet still refuses a stale packet (unweakened by Card 4)",
              result["launched"] is False and "stale" in result["reason"], result)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_card_contract_validates():
    tmp = tempfile.mkdtemp(prefix="dev_wfi_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        valid = card_contract.record_card_contract(
            conn, task="WB.1TEST", actor="claude_code", task_id="CARD-99",
            allowed_scope=["tools/development/"], forbidden_areas=["auth/", "UI/"],
            required_checks=["python3 tools/development/tests/test_continuity.py"],
            required_evidence=["diff", "test output"], stage_closeout_required=True,
            next_return_point="CARD 100", expected_prev_revision=0,
        )
        check("structured card contract fields validate when well-formed",
              valid["revision"] == 1, valid)

        shown = card_contract.get_card_contract(conn, "WB.1TEST")
        check("card-contract-show retrieves the recorded contract",
              shown is not None and shown["fields"]["task_id"] == "CARD-99", shown)

        for missing_field, kwargs in [
            ("required_checks", dict(required_checks=[])),
            ("allowed_scope", dict(allowed_scope=[])),
            ("next_return_point", dict(next_return_point="")),
        ]:
            base = dict(
                task="WB.1TEST", actor="claude_code", task_id="CARD-99",
                allowed_scope=["x"], forbidden_areas=[], required_checks=["x"],
                required_evidence=["x"], stage_closeout_required=True,
                next_return_point="CARD 100", expected_prev_revision=1,
            )
            base.update(kwargs)
            try:
                card_contract.record_card_contract(conn, **base)
                check(f"malformed card contract ({missing_field}) rejected", False, "no exception")
            except card_contract.CardContractValidationError:
                check(f"malformed card contract ({missing_field}) rejected", True)

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cli_wiring():
    tmp = tempfile.mkdtemp(prefix="dev_wfi_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        conn.close()

        def run(*args):
            return subprocess.run(
                [sys.executable, "-m", "tools.development.cli", "--db", db, *args],
                cwd=REPO_ROOT, capture_output=True, text=True,
            )

        p1 = run("close-task", "WB.1TEST", "--actor", "claude_code", "--expect-revision", "0")
        check("cli close-task: clean state exits 0", p1.returncode == 0, p1.stdout + p1.stderr)

        p2 = run("verify-closeout", "WB.1TEST")
        check("cli verify-closeout: verified task exits 0", p2.returncode == 0, p2.stdout)

        p3 = run("discovery-record", "WB.1TEST", "--actor", "codex", "--summary", "blocks",
                  "--disposition", "BEFORE_STAGE_CLOSEOUT", "--originating-stage", "WB.1TEST",
                  "--blocking", "true", "--expect-revision", "1")
        check("cli discovery-record after close_task: exits 0", p3.returncode == 0, p3.stdout)

        p4 = run("verify-closeout", "WB.1TEST")
        parsed4 = json.loads(p4.stdout)
        check("cli verify-closeout: new blocker after closure -> exit 1, verified false",
              p4.returncode == 1 and parsed4["verified"] is False, p4.stdout)

        p5 = run("card-contract-record", "WB.1TEST", "--actor", "claude_code",
                  "--task-id", "CARD-99", "--allowed-scope", "tools/development/",
                  "--required-check", "pytest", "--required-evidence", "diff",
                  "--stage-closeout-required", "true", "--next-return-point", "CARD 100",
                  "--expect-revision", "2")
        check("cli card-contract-record: valid contract exits 0", p5.returncode == 0, p5.stdout)

        p6 = run("card-contract-show", "WB.1TEST")
        check("cli card-contract-show: exits 0 and returns the recorded contract",
              p6.returncode == 0 and json.loads(p6.stdout)["fields"]["task_id"] == "CARD-99", p6.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    test_close_task_integration_calls_closeout_validation()
    test_close_task_blocking_state_prevents_completion()
    test_malformed_deferral_fails_close_task()
    test_verify_closeout_level_3()
    test_launcher_stale_packet_refusal_still_active()
    test_card_contract_validates()
    test_cli_wiring()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
