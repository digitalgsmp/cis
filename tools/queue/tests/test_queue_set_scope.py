#!/usr/bin/env python3
"""test_queue_set_scope.py — OQ-TRIAGE-001 option 1: the audited scope write path.

Covers the scope half of the queue classification contract that queue_set.py
gained on 2026-10-03, the build-list projection's marker insertion, and the
round trip through the documented recovery path.

Every test runs the REAL scripts as subprocesses against scratch temp databases
(CIS_SPINE_PATH / CIS_QUEUE_DB / CIS_QUEUE_SRC). Production is opened read-only,
once, to assert it was not touched. Run:
    python3 tools/queue/tests/test_queue_set_scope.py
"""
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
QUEUE_SET = os.path.join(REPO_ROOT, "tools", "queue", "queue_set.py")
RENDER = os.path.join(REPO_ROOT, "tools", "queue", "render_build_list.py")
EXTRACT = os.path.join(REPO_ROOT, "tools", "queue", "extract_queue_items.py")
PROD_DB = os.path.join(REPO_ROOT, "data", "cis_memory.db")

SCHEMA = """
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

# Two items that mirror the real shapes triage has to write into:
#   1.3  a heading item with NO marker of any kind -- 56 of 56 production
#        unclassified rows look like this, so insertion is the live path
#   1.4  a heading item that ALREADY carries a '**Need:' marker, so the update
#        path is exercised too
#   3.1  a BULLET item with no marker, because body_md for a bullet is a list
#        line and a column-0 marker has to stay inside the item's own body slice
ITEMS = [
    ("1.3", 1, "Failure routing — NOT IN CODE", "heading", 10,
     "### 1.3 Failure routing — NOT IN CODE\n"
     "**Checked:** the four states appear 0 times in the relay.\n"
     "\n"
     "---\n"),
    ("1.4", 1, "Retry and escalation", "heading", 20,
     "### 1.4 Retry and escalation\n"
     "**Need: UNASSESSED 2026-08-01.**\n"
     "Some prose about retries.\n"),
    ("3.1", 3, "ask_history does not merge FTS5", "bullet", 30,
     "- **3.1** `ask_history` does not merge FTS5 with vector search. The relay\n"
     "  does; `ask_history` does not.\n"),
]

results = []


def check(label, cond, detail=""):
    results.append(f"{label}: PASS" if cond else f"{label}: FAIL — {detail}")


def make_db(path, with_scope_block_trigger=False):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    for num, tier, title, form, line, body in ITEMS:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "source_line, source_sha) VALUES (?,?,?,?,?,?,'fixturesha')",
            (num, tier, title, body, form, line))
    conn.execute(
        "INSERT INTO queue_sections (seq, kind, content, tier, source_sha, source_line) "
        "VALUES (0, 'preamble', '# CIS UNIFIED BUILD LIST\n\nScratch preamble.', "
        "NULL, 'fixturesha', 1)")
    conn.execute(
        "INSERT INTO queue_sections (seq, kind, content, tier, source_sha, source_line) "
        "VALUES (2, 'tier_header', '# TIER 1 — the pipeline', 1, 'fixturesha', 5)")
    conn.execute(
        "INSERT INTO queue_sections (seq, kind, content, tier, source_sha, source_line) "
        "VALUES (4, 'tier_header', '# TIER 3 — the knowledge base', 3, 'fixturesha', 25)")
    if with_scope_block_trigger:
        # Forces the scope UPDATE to abort at the DB layer so the two-field
        # transaction's rollback can be observed rather than assumed.
        conn.execute(
            "CREATE TRIGGER block_scope BEFORE UPDATE OF scope ON queue_items "
            "BEGIN SELECT RAISE(ABORT, 'scope blocked'); END")
    conn.commit()
    conn.close()


def run_set(db, *args):
    env = dict(os.environ)
    env["CIS_SPINE_PATH"] = db
    return subprocess.run([sys.executable, QUEUE_SET, *args],
                          cwd=REPO_ROOT, capture_output=True, text=True, env=env)


def row(db, num):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(
            "SELECT need_status, scope, status_changed_at FROM queue_items "
            "WHERE item_num=?", (num,)).fetchone()
    finally:
        conn.close()


def events(db, num=None, field=None):
    conn = sqlite3.connect(db)
    try:
        q = "SELECT item_num, field, old_value, new_value, changed_by, evidence, note " \
            "FROM queue_item_events WHERE 1=1"
        p = []
        if num:
            q += " AND item_num=?"
            p.append(num)
        if field:
            q += " AND field=?"
            p.append(field)
        return conn.execute(q + " ORDER BY id", p).fetchall()
    finally:
        conn.close()


# ── 1-5, 12-13: the write path ──────────────────────────────────────────────

def test_write_path():
    tmp = tempfile.mkdtemp(prefix="cis_qsscope_")
    try:
        db = os.path.join(tmp, "scratch.db")
        make_db(db)

        p = run_set(db, "1.3", "--scope", "CONTAINER — the relay state machine.",
                    "--evidence", "grep -c returned 0", "--by", "test")
        check("1. scope can be written through queue_set",
              p.returncode == 0 and row(db, "1.3")[1] == "CONTAINER — the relay state machine.",
              f"rc={p.returncode} {p.stdout}{p.stderr}")

        p = run_set(db, "1.3", "--status", "OPEN", "--evidence", "grep -c returned 0",
                    "--by", "test")
        check("2. need_status can still be written",
              p.returncode == 0 and row(db, "1.3")[0] == "OPEN",
              f"rc={p.returncode} {p.stdout}{p.stderr}")

        ev = events(db, "1.3", "scope")
        check("3. scope mutation creates a queue_item_events row with its evidence",
              len(ev) == 1 and ev[0][1] == "scope"
              and ev[0][5] == "grep -c returned 0" and ev[0][4] == "test",
              str(ev))

        p = run_set(db, "1.3", "--scope", "REPO — moved after review.",
                    "--note", "repointed", "--by", "test")
        ev = events(db, "1.3", "scope")
        check("4. the old scope value is preserved in the audit trail",
              p.returncode == 0 and len(ev) == 2
              and ev[1][2] == "CONTAINER — the relay state machine."
              and ev[1][3] == "REPO — moved after review.",
              str(ev))

        before = row(db, "1.4")
        for bad, label in ((" ", "whitespace-only"), ("", "empty")):
            p = run_set(db, "1.4", "--scope", bad, "--note", "x")
            if p.returncode != 2 or row(db, "1.4") != before:
                check(f"5. a {label} scope is rejected", False,
                      f"rc={p.returncode} row={row(db, '1.4')}")
                break
        else:
            check("5. an empty or whitespace-only scope is rejected and writes nothing", True)

        p = run_set(db, "1.4", "--scope", "CONTAINER\nsecond line", "--note", "x")
        check("13a. a multi-line scope is rejected (projection is one line)",
              p.returncode == 2 and "newline" in p.stdout, p.stdout)

        p = run_set(db, "1.4", "--scope", "CONTAINER — " + "x" * 400, "--note", "x")
        check("13b. a scope over 300 chars is rejected (extractor truncates there)",
              p.returncode == 2 and "300" in p.stdout, p.stdout)

        p = run_set(db, "1.4", "--scope", "CONTAINER — ok")
        check("13c. a scope with neither evidence nor note is rejected",
              p.returncode == 2 and "required with --scope" in p.stdout, p.stdout)

        p = run_set(db, "1.4", "--scope", "SOMETHING_ELSE — off convention",
                    "--note", "deliberate")
        check("13d. an off-convention scope is written but reported, not enforced",
              p.returncode == 0 and row(db, "1.4")[1] == "SOMETHING_ELSE — off convention"
              and "does not open with a scope token" in p.stdout, p.stdout)

        p = run_set(db, "1.4")
        check("13e. passing neither field is refused",
              p.returncode == 2 and "nothing to write" in p.stdout, p.stdout)

        # The guard that keeps the projection recoverable.
        p = run_set(db, "3.1", "--status", "NEEDS_ERIC", "--note", "Eric decides")
        check("12a. a status the recovery path cannot read back is refused",
              p.returncode == 2 and "cannot survive the documented recovery path" in p.stdout
              and row(db, "3.1")[0] is None, p.stdout)

        p = run_set(db, "3.1", "--status", "NEEDS_ERIC", "--note", "Eric decides",
                    "--allow-unrecoverable-status")
        check("12b. the same status is written when the override is passed explicitly",
              p.returncode == 0 and row(db, "3.1")[0] == "NEEDS_ERIC", p.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 6: atomicity ────────────────────────────────────────────────────────────

def test_two_field_atomicity():
    tmp = tempfile.mkdtemp(prefix="cis_qsatomic_")
    try:
        db = os.path.join(tmp, "scratch.db")
        make_db(db)
        p = run_set(db, "1.3", "--status", "OPEN", "--scope", "CONTAINER — both.",
                    "--evidence", "output here", "--by", "test")
        r = row(db, "1.3")
        check("6a. both fields written together land together",
              p.returncode == 0 and r[0] == "OPEN" and r[1] == "CONTAINER — both."
              and len(events(db, "1.3")) == 2, f"rc={p.returncode} row={r} {p.stdout}")

        # Same command, but the scope UPDATE aborts at the DB layer. The status
        # half must not survive on its own.
        db2 = os.path.join(tmp, "blocked.db")
        make_db(db2, with_scope_block_trigger=True)
        p = run_set(db2, "1.3", "--status", "OPEN", "--scope", "CONTAINER — both.",
                    "--evidence", "output here", "--by", "test")
        r = row(db2, "1.3")
        check("6b. a two-field write that fails mid-way leaves NO half-classification",
              p.returncode != 0 and r[0] is None and r[1] is None
              and r[2] is None and len(events(db2, "1.3")) == 0,
              f"rc={p.returncode} row={r} events={len(events(db2, '1.3'))}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 7-9, 14: the projection and the round trip ──────────────────────────────

def test_projection_and_round_trip():
    tmp = tempfile.mkdtemp(prefix="cis_qsproj_")
    try:
        db = os.path.join(tmp, "scratch.db")
        make_db(db)
        src = os.path.join(tmp, "UNIFIED_BUILD_LIST.md")

        env = dict(os.environ)
        env["CIS_SPINE_PATH"] = db
        env["CIS_QUEUE_SRC"] = src

        # Baseline: nothing classified, so nothing may be rewritten.
        base = subprocess.run([sys.executable, RENDER, "--stdout"], cwd=REPO_ROOT,
                              capture_output=True, text=True, env=env)
        check("14a. an unclassified item is projected byte-for-byte",
              base.returncode == 0
              and "### 1.3 Failure routing — NOT IN CODE" in base.stdout
              and "**Scope:**" not in base.stdout
              and "**Need: OPEN.**" not in base.stdout,
              base.stdout[:300] + base.stderr[:300])

        # 1.3 heading, no marker -> both markers inserted
        run_set(db, "1.3", "--status", "OPEN", "--scope", "CONTAINER — the relay.",
                "--evidence", "grep -c returned 0", "--by", "test")
        # 1.4 heading, existing marker -> status updated in place, scope inserted
        run_set(db, "1.4", "--status", "DONE", "--scope", "REPO — the hook.",
                "--evidence", "it is done", "--by", "test")
        # 3.1 bullet, no marker -> insertion must stay inside the bullet's body
        run_set(db, "3.1", "--status", "HALF_DONE", "--scope", "REPO — ask_history.py.",
                "--note", "partly built", "--by", "test")

        r = subprocess.run([sys.executable, RENDER], cwd=REPO_ROOT,
                           capture_output=True, text=True, env=env)
        md = open(src, encoding="utf-8").read()
        check("7. markers are INSERTED into items that had none",
              r.returncode == 0
              and "**Scope:** CONTAINER — the relay." in md
              and "**Need: OPEN.**" in md
              and "**Scope:** REPO — ask_history.py." in md
              and "**Need: HALF DONE.**" in md, md[:400] + r.stderr[:200])

        check("8. an existing marker is updated, not duplicated",
              md.count("**Need:") == 3 and "**Need: DONE.**" in md
              and "UNASSESSED" not in md,
              f"need markers={md.count('**Need:')}")

        # Item 1.3's body ended with a '---' item separator. Both inserted
        # markers must land above it, so the rule still separates the items
        # rather than being buried inside one.
        seg = md[md.index("### 1.3"):md.index("### 1.4")]
        check("14b. inserted markers sit above the item's trailing '---' rule",
              seg.index("**Need: OPEN.**") < seg.index("**Scope:** CONTAINER — the relay.")
              < seg.index("---\n"),
              repr(seg))

        # Round trip: projection -> documented recovery path -> a fresh table.
        db2 = os.path.join(tmp, "recovered.db")
        make_db(db2)
        env2 = dict(os.environ)
        env2["CIS_QUEUE_DB"] = db2
        env2["CIS_QUEUE_SRC"] = src
        ex = subprocess.run([sys.executable, EXTRACT, "--force"], cwd=REPO_ROOT,
                            capture_output=True, text=True, env=env2)
        check("9a. the documented recovery path reads the projection without failing",
              ex.returncode == 0 and "UNPARSED          : 0" in ex.stdout,
              ex.stdout[-500:] + ex.stderr[-300:])

        same = []
        for num in ("1.3", "1.4", "3.1"):
            a, b = row(db, num), row(db2, num)
            same.append((num, a[0], b[0], a[1], b[1]))
        ok = all(s[1] == s[2] and s[3] == s[4] for s in same)
        check("9b. round trip preserves BOTH scope and need_status on every item",
              ok, "; ".join(f"{n}: status {x!r}->{y!r} scope {u!r}->{v!r}"
                            for n, x, y, u, v in same))

        # And the recovered table re-renders to the same markdown.
        env3 = dict(os.environ)
        env3["CIS_SPINE_PATH"] = db2
        env3["CIS_QUEUE_SRC"] = src
        again = subprocess.run([sys.executable, RENDER, "--stdout"], cwd=REPO_ROOT,
                               capture_output=True, text=True, env=env3)
        body_a = "\n".join(l for l in md.splitlines() if not l.startswith("<!--"))
        body_b = "\n".join(l for l in again.stdout.splitlines()
                           if not l.startswith("<!--"))
        check("9c. re-rendering the recovered table reproduces the same markdown",
              body_a == body_b,
              "projection is not idempotent across a recovery cycle")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 10: read-model triage semantics ─────────────────────────────────────────

def test_read_model_requires_both_fields():
    tmp = tempfile.mkdtemp(prefix="cis_qsread_")
    try:
        db = os.path.join(tmp, "scratch.db")
        make_db(db)
        run_set(db, "1.3", "--status", "OPEN", "--evidence", "x", "--by", "test")
        run_set(db, "1.4", "--status", "DONE", "--scope", "REPO — done.",
                "--evidence", "x", "--by", "test")

        sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "state"))
        import build_path as bp
        import project_intelligence as pi

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        try:
            counts = bp.queue_classification(conn)
            q = pi.build_queue(conn, {}, {})
        finally:
            conn.close()

        by = {i["item_num"]: i for i in q["items"]}
        check("10a. a row carrying only need_status is NOT reported triage-complete",
              by["1.3"]["triage_complete"] is False
              and by["1.3"]["triage_missing_fields"] == ["scope"]
              and by["1.3"]["triage_status"] == "PARTIALLY CLASSIFIED",
              str({k: by["1.3"][k] for k in
                   ("triage_complete", "triage_missing_fields", "triage_status")}))

        check("10b. a row carrying both fields IS reported triage-complete",
              by["1.4"]["triage_complete"] is True
              and by["1.4"]["triage_status"] == "CLASSIFIED", str(by["1.4"]["triage_status"]))

        check("10c. fully_classified counts only two-field rows, on both read models",
              counts["fully_classified"] == 1 and q["fully_classified"] == 1
              and counts["partially_classified"] == 1
              and q["partially_classified"] == 1, str(counts))

        check("10d. ADR-PIPE-006's unclassified count stays 'neither field', unwidened",
              counts["unclassified"] == 1 and q["awaiting_triage"] == 1
              and by["3.1"]["awaiting_triage"] is True,
              f"unclassified={counts['unclassified']}")

        check("10e. the two counts plus the subject partition the table exactly",
              counts["unclassified"] + counts["partially_classified"]
              + counts["fully_classified"] == counts["total_items"] == 3,
              str(counts))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 11: production untouched ────────────────────────────────────────────────

def production_snapshot():
    conn = sqlite3.connect(f"file:{PROD_DB}?mode=ro", uri=True)
    try:
        return conn.execute(
            "SELECT (SELECT COUNT(*) FROM queue_items), "
            "(SELECT COUNT(*) FROM queue_items WHERE need_status IS NULL AND scope IS NULL), "
            "(SELECT COUNT(*) FROM queue_items WHERE scope IS NOT NULL), "
            "(SELECT COUNT(*) FROM queue_edges), "
            "(SELECT COUNT(*) FROM queue_item_events)").fetchone()
    finally:
        conn.close()


def run():
    before = production_snapshot()
    test_write_path()
    test_two_field_atomicity()
    test_projection_and_round_trip()
    test_read_model_requires_both_fields()
    after = production_snapshot()
    check("11. no production queue row, edge or event changed during these tests",
          before == after, f"{before} -> {after}")

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
