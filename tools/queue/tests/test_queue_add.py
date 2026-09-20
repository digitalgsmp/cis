#!/usr/bin/env python3
"""test_queue_add.py — CARD 5 behavioral tests for tools/queue/queue_add.py.

Runs the real script as a subprocess (CIS_SPINE_PATH pointed at a scratch
temp database) — never against production. Run:
    python3 tools/queue/tests/test_queue_add.py
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
QUEUE_ADD = os.path.join(REPO_ROOT, "tools", "queue", "queue_add.py")

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def make_fixture_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE queue_items (
            item_num TEXT PRIMARY KEY, tier INTEGER NOT NULL, title TEXT NOT NULL,
            body_md TEXT NOT NULL, form TEXT NOT NULL CHECK (form IN ('heading','bullet')),
            scope TEXT,
            need_status TEXT CHECK (need_status IS NULL OR need_status IN
                ('OPEN','UNASSESSED','HALF_DONE','DONE','UNPARSED','PARTLY','UNCLEAR',
                 'PRESENT_UNPROVEN','NEEDS_ERIC','NO_CHECK_WRITTEN')),
            need_raw TEXT, source_line INTEGER NOT NULL, source_sha TEXT NOT NULL,
            extracted_at TEXT NOT NULL DEFAULT (datetime('now')),
            status_changed_at TEXT, status_changed_by TEXT,
            check_class TEXT CHECK (check_class IN ('RUNNABLE','JUDGMENT','NO_CHECK'))
        );
        CREATE TABLE queue_item_events (
            id INTEGER PRIMARY KEY, item_num TEXT NOT NULL, field TEXT NOT NULL,
            old_value TEXT, new_value TEXT, changed_at TEXT NOT NULL DEFAULT (datetime('now')),
            changed_by TEXT, evidence TEXT, note TEXT
        );
        CREATE TABLE queue_sections (
            seq INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK (kind IN ('preamble','tier_header')),
            content TEXT NOT NULL, tier INTEGER, source_sha TEXT NOT NULL, source_line INTEGER
        );
        """
    )
    conn.execute(
        "INSERT INTO queue_items (item_num, tier, title, body_md, form, need_status, "
        "source_line, source_sha) VALUES ('4.19', 4, 'existing item', 'existing body', "
        "'heading', 'OPEN', 3458, 'realsha')"
    )
    conn.execute(
        "INSERT INTO queue_sections (kind, content, tier, source_sha, source_line) "
        "VALUES ('tier_header', '# TIER 4 — after the infrastructure works', 4, 'realsha', 3217)"
    )
    conn.commit()
    conn.close()


def run_queue_add(db_path, *args):
    env = dict(os.environ)
    env["CIS_SPINE_PATH"] = db_path
    return subprocess.run(
        [sys.executable, QUEUE_ADD, *args],
        cwd=REPO_ROOT, capture_output=True, text=True, env=env,
    )


def test_valid_creation_and_provenance_and_history():
    tmp = tempfile.mkdtemp(prefix="queue_add_")
    try:
        db = os.path.join(tmp, "fixture.db")
        make_fixture_db(db)
        body_file = os.path.join(tmp, "body.md")
        with open(body_file, "w") as f:
            f.write("### 4.20 A new capability\n\nDescription of the new capability.\n")

        p = run_queue_add(
            db, "4.20", "--tier", "4", "--title", "A new capability",
            "--body-file", body_file, "--form", "heading", "--need-status", "OPEN",
            "--actor", "claude_code", "--evidence", "CARD 5 test: valid creation",
        )
        check("valid task creation exits 0", p.returncode == 0, p.stdout + p.stderr)

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM queue_items WHERE item_num='4.20'").fetchone()
        check("created item is actually present in queue_items", row is not None, p.stdout)
        check("created item has the requested tier/title/form/need_status",
              row["tier"] == 4 and row["title"] == "A new capability" and
              row["form"] == "heading" and row["need_status"] == "OPEN", dict(row))
        check("created item's source_line sorts after the existing item/section max (3458)",
              row["source_line"] > 3458, row["source_line"])

        events = conn.execute(
            "SELECT * FROM queue_item_events WHERE item_num='4.20'"
        ).fetchall()
        check("creation history/event recorded", len(events) == 1, len(events))
        check("provenance recorded (actor + evidence on the creation event)",
              events[0]["changed_by"] == "claude_code" and
              events[0]["evidence"] == "CARD 5 test: valid creation" and
              events[0]["field"] == "created", dict(events[0]))

        unrelated = conn.execute(
            "SELECT title, body_md, source_line FROM queue_items WHERE item_num='4.19'"
        ).fetchone()
        check("unrelated (pre-existing) queue entry is unchanged",
              unrelated["title"] == "existing item" and unrelated["body_md"] == "existing body"
              and unrelated["source_line"] == 3458, dict(unrelated))

        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_duplicate_id_rejected():
    tmp = tempfile.mkdtemp(prefix="queue_add_")
    try:
        db = os.path.join(tmp, "fixture.db")
        make_fixture_db(db)
        body_file = os.path.join(tmp, "body.md")
        with open(body_file, "w") as f:
            f.write("### 4.19 duplicate attempt\n\nshould be refused.\n")

        p = run_queue_add(
            db, "4.19", "--tier", "4", "--title", "duplicate attempt",
            "--body-file", body_file, "--form", "heading", "--actor", "claude_code",
            "--evidence", "CARD 5 test: duplicate rejection",
        )
        check("duplicate item_num rejected (nonzero exit)", p.returncode != 0, p.stdout + p.stderr)

        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT title, body_md FROM queue_items WHERE item_num='4.19'"
        ).fetchone()
        check("duplicate rejection did not overwrite the existing item",
              row[0] == "existing item" and row[1] == "existing body", row)
        events = conn.execute(
            "SELECT count(*) FROM queue_item_events WHERE item_num='4.19'"
        ).fetchone()[0]
        check("duplicate rejection wrote no spurious event", events == 0, events)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_malformed_task_rejected():
    tmp = tempfile.mkdtemp(prefix="queue_add_")
    try:
        db = os.path.join(tmp, "fixture.db")
        make_fixture_db(db)
        body_file = os.path.join(tmp, "body.md")
        with open(body_file, "w") as f:
            f.write("### 4.21 x\n\nbody\n")

        # missing --evidence (argparse itself rejects, but also test the
        # script's own explicit empty-evidence guard by passing an
        # all-whitespace value which argparse WOULD accept syntactically).
        p1 = run_queue_add(
            db, "4.21", "--tier", "4", "--title", "x", "--body-file", body_file,
            "--form", "heading", "--actor", "claude_code", "--evidence", "   ",
        )
        check("malformed task (blank evidence) rejected", p1.returncode != 0, p1.stdout)

        p2 = run_queue_add(
            db, "4.22", "--tier", "4", "--title", "x", "--body-file", body_file,
            "--form", "not-a-real-form", "--actor", "claude_code", "--evidence", "x",
        )
        check("malformed task (invalid form choice) rejected by argparse",
              p2.returncode != 0, p2.stderr)

        empty_body_file = os.path.join(tmp, "empty.md")
        open(empty_body_file, "w").close()
        p3 = run_queue_add(
            db, "4.23", "--tier", "4", "--title", "x", "--body-file", empty_body_file,
            "--form", "heading", "--actor", "claude_code", "--evidence", "x",
        )
        check("malformed task (empty body) rejected", p3.returncode != 0, p3.stdout)

        conn = sqlite3.connect(db)
        count = conn.execute(
            "SELECT count(*) FROM queue_items WHERE item_num IN ('4.21','4.22','4.23')"
        ).fetchone()[0]
        check("none of the three malformed attempts created a row", count == 0, count)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_dry_run_writes_nothing():
    tmp = tempfile.mkdtemp(prefix="queue_add_")
    try:
        db = os.path.join(tmp, "fixture.db")
        make_fixture_db(db)
        body_file = os.path.join(tmp, "body.md")
        with open(body_file, "w") as f:
            f.write("### 4.24 dry run item\n\nshould not be written.\n")

        p = run_queue_add(
            db, "4.24", "--tier", "4", "--title", "dry run item", "--body-file", body_file,
            "--form", "heading", "--actor", "claude_code", "--evidence", "dry run test",
            "--dry-run",
        )
        check("dry-run exits 0", p.returncode == 0, p.stdout)
        check("dry-run output says DRY RUN, names what would happen",
              "DRY RUN" in p.stdout and "4.24" in p.stdout, p.stdout)

        conn = sqlite3.connect(db)
        item_count = conn.execute(
            "SELECT count(*) FROM queue_items WHERE item_num='4.24'"
        ).fetchone()[0]
        event_count = conn.execute(
            "SELECT count(*) FROM queue_item_events WHERE item_num='4.24'"
        ).fetchone()[0]
        check("dry-run wrote no queue_items row", item_count == 0, item_count)
        check("dry-run wrote no queue_item_events row", event_count == 0, event_count)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_source_build_list_synchronization_remains_valid():
    """After a real creation, render_build_list.py must be able to
    regenerate the markdown from the table without error, and --verify
    must correctly report fresh immediately after regeneration."""
    tmp = tempfile.mkdtemp(prefix="queue_add_")
    try:
        db = os.path.join(tmp, "fixture.db")
        make_fixture_db(db)
        body_file = os.path.join(tmp, "body.md")
        with open(body_file, "w") as f:
            f.write("### 4.25 sync test item\n\nbody text.\n")
        p = run_queue_add(
            db, "4.25", "--tier", "4", "--title", "sync test item", "--body-file", body_file,
            "--form", "heading", "--actor", "claude_code", "--evidence", "sync test",
        )
        check("setup: creation for sync test succeeded", p.returncode == 0, p.stdout)

        env = dict(os.environ)
        env["CIS_SPINE_PATH"] = db
        md_path = os.path.join(tmp, "BUILD_LIST.md")
        env["CIS_QUEUE_SRC"] = md_path
        render_script = os.path.join(REPO_ROOT, "tools", "queue", "render_build_list.py")

        p_render = subprocess.run(
            [sys.executable, render_script], cwd=REPO_ROOT, capture_output=True, text=True, env=env,
        )
        check("render_build_list.py succeeds against the new table state",
              p_render.returncode == 0, p_render.stdout + p_render.stderr)
        check("regenerated markdown includes the newly created item",
              os.path.isfile(md_path) and "4.25 sync test item" in open(md_path).read(),
              md_path)

        p_verify = subprocess.run(
            [sys.executable, render_script, "--verify"],
            cwd=REPO_ROOT, capture_output=True, text=True, env=env,
        )
        check("render --verify reports fresh immediately after regeneration",
              p_verify.returncode == 0 and "fresh" in p_verify.stdout, p_verify.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    test_valid_creation_and_provenance_and_history()
    test_duplicate_id_rejected()
    test_malformed_task_rejected()
    test_dry_run_writes_nothing()
    test_source_build_list_synchronization_remains_valid()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
