#!/usr/bin/env python3
"""test_card5_verify_completion.py — CARD 5 tests for
discovery.verify_completion_artifact() / CLI `verify-completion`
(WB.1C-R1 addendum item B: a completion artifact must not become
authoritative merely because a file exists).

Temporary SQLite fixtures only. Run:
    python3 tools/development/tests/test_card5_verify_completion.py
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


def test_untrusted_when_no_closeout_ever_happened():
    tmp = tempfile.mkdtemp(prefix="card5_vc_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        cfile = os.path.join(tmp, "completion.json")
        with open(cfile, "w") as f:
            json.dump({"card_id": "WB.1TEST", "status": "READY_FOR_CHATGPT_REVIEW"}, f)

        result = discovery.verify_completion_artifact(conn, cfile, expected_task="WB.1TEST")
        check("a completion claim with NO prior close-task is untrustworthy",
              result["trustworthy"] is False, result)
        check("reason explains the actual gap (closeout not verified)",
              any("NOT verified" in r for r in result["reasons"]), result)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_trusted_after_real_close_task():
    tmp = tempfile.mkdtemp(prefix="card5_vc_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        discovery.close_task(conn, task="WB.1TEST", actor="claude_code", expected_prev_revision=0)

        cfile = os.path.join(tmp, "completion.json")
        with open(cfile, "w") as f:
            json.dump({"card_id": "WB.1TEST", "status": "READY_FOR_CHATGPT_REVIEW"}, f)

        result = discovery.verify_completion_artifact(conn, cfile, expected_task="WB.1TEST")
        check("a completion claim backed by a real close_task() is trustworthy",
              result["trustworthy"] is True, result)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_new_blocker_after_closure_flips_trust():
    tmp = tempfile.mkdtemp(prefix="card5_vc_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        closed = discovery.close_task(conn, task="WB.1TEST", actor="claude_code", expected_prev_revision=0)
        discovery.record_discovery(
            conn, task="WB.1TEST", actor="codex", summary="found after closure claimed",
            disposition="BEFORE_STAGE_CLOSEOUT", originating_stage="WB.1TEST", blocking=True,
            expected_prev_revision=closed["revision"],
        )
        cfile = os.path.join(tmp, "completion.json")
        with open(cfile, "w") as f:
            json.dump({"card_id": "WB.1TEST", "status": "READY_FOR_CHATGPT_REVIEW"}, f)
        result = discovery.verify_completion_artifact(conn, cfile, expected_task="WB.1TEST")
        check("a stale completion claim is untrustworthy once a new blocker exists",
              result["trustworthy"] is False, result)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_self_labeled_verified_flagged():
    tmp = tempfile.mkdtemp(prefix="card5_vc_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)
        discovery.close_task(conn, task="WB.1TEST", actor="claude_code", expected_prev_revision=0)
        cfile = os.path.join(tmp, "completion.json")
        with open(cfile, "w") as f:
            json.dump({"card_id": "WB.1TEST", "status": "VERIFIED"}, f)
        result = discovery.verify_completion_artifact(conn, cfile, expected_task="WB.1TEST")
        check("a self-labeled VERIFIED/PASS status is flagged as an additional trust concern "
              "(this project's own convention: no card may self-label VERIFIED)",
              result["trustworthy"] is False and
              any("self-labels VERIFIED" in r for r in result["reasons"]), result)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_or_malformed_file_handled_without_raising():
    tmp = tempfile.mkdtemp(prefix="card5_vc_")
    try:
        db = os.path.join(tmp, "fixture.db")
        conn = make_fixture_db(db)
        cs.init_schema(conn, db_path=db)

        missing = discovery.verify_completion_artifact(conn, os.path.join(tmp, "nope.json"),
                                                         expected_task="WB.1TEST")
        check("a missing completion file is reported untrustworthy, not an exception",
              missing["trustworthy"] is False, missing)

        bad_json = os.path.join(tmp, "bad.json")
        with open(bad_json, "w") as f:
            f.write("{not valid json")
        malformed = discovery.verify_completion_artifact(conn, bad_json, expected_task="WB.1TEST")
        check("malformed JSON is reported untrustworthy, not an exception",
              malformed["trustworthy"] is False, malformed)

        task_mismatch_file = os.path.join(tmp, "mismatch.json")
        with open(task_mismatch_file, "w") as f:
            json.dump({"card_id": "SOME-OTHER-TASK", "status": "READY_FOR_CHATGPT_REVIEW"}, f)
        mismatch = discovery.verify_completion_artifact(conn, task_mismatch_file, expected_task="WB.1TEST")
        check("a completion file claiming a DIFFERENT task than expected is flagged",
              mismatch["trustworthy"] is False and
              any("caller expected" in r for r in mismatch["reasons"]), mismatch)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cli_verify_completion_exit_codes():
    tmp = tempfile.mkdtemp(prefix="card5_vc_")
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

        cfile = os.path.join(tmp, "completion.json")
        with open(cfile, "w") as f:
            json.dump({"card_id": "WB.1TEST", "status": "READY_FOR_CHATGPT_REVIEW"}, f)

        p1 = run("verify-completion", "WB.1TEST", cfile)
        check("cli verify-completion: untrusted (never closed) exits 1", p1.returncode == 1, p1.stdout)

        run("close-task", "WB.1TEST", "--actor", "claude_code", "--expect-revision", "0")
        p2 = run("verify-completion", "WB.1TEST", cfile)
        check("cli verify-completion: trusted (after real close-task) exits 0", p2.returncode == 0, p2.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    test_untrusted_when_no_closeout_ever_happened()
    test_trusted_after_real_close_task()
    test_new_blocker_after_closure_flips_trust()
    test_self_labeled_verified_flagged()
    test_missing_or_malformed_file_handled_without_raising()
    test_cli_verify_completion_exit_codes()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
