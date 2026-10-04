#!/usr/bin/env python3
"""test_recovery_status_vocabulary.py — OQ-TRIAGE-002: the recovery vocabulary.

THE DEFECT THIS LOCKS DOWN. queue_items.need_status's CHECK permits ten values.
extract_queue_items.py -- the documented `--force` recovery path -- could read
five of them. The other five (PARTLY, UNCLEAR, PRESENT_UNPROVEN, NEEDS_ERIC,
NO_CHECK_WRITTEN) parsed to UNPARSED, and the extractor's rule 6 fails the WHOLE
recovery run on UNPARSED > 0 -- so one item carrying a legitimate stored status
took the other 131 down with it and imported nothing.

AND IT WAS NOT FIXABLE BY ADDING FIVE STRINGS TO `KNOWN`, which is the trap this
file exists to keep shut. render_build_list.py canonicalises underscores to
spaces, so NO_CHECK_WRITTEN reaches the parser as three words, and _normalise()
joined at most TWO -- 'NO CHECK WRITTEN' normalised to 'NO' no matter what the
vocabulary contained. The normalisation and the vocabulary are ONE contract, and
every test here drives it through the real rendering rather than a synthetic
underscore form, because the synthetic form passed while the real one failed.

WHAT IS PROVEN, all through the REAL scripts as subprocesses against scratch temp
databases (CIS_SPINE_PATH / CIS_QUEUE_DB / CIS_QUEUE_SRC):

  1  every one of the nine stored statuses is writable through queue_set.py with
     no override flag
  2  each renders to its exact canonical marker text
  3  the recovery path reads all nine back with UNPARSED: 0
  4  scope AND need_status survive the round trip on every item
  5  the recovered table re-renders to the same markdown
  6  BUILT is still read as DONE, and RESOLVED still maps to DONE
  7  NO_CHECK_WRITTEN specifically: DB -> '**Need: NO CHECK WRITTEN.**' -> DB
  8  an unknown token still yields UNPARSED > 0, a nonzero exit, and a table
     that is byte-identical afterwards -- fail-on-unknown is NOT weakened
  9  two markers in one item still fail the same way
 10  queue_set.py now FAILS CLOSED: a recovery path it cannot inspect refuses a
     status write instead of permitting it, while a scope-only write still works

Production is opened read-only, once, to assert it was not touched. Run:
    python3 tools/queue/tests/test_recovery_status_vocabulary.py
"""
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
QUEUE_DIR = os.path.join(REPO_ROOT, "tools", "queue")
QUEUE_SET = os.path.join(QUEUE_DIR, "queue_set.py")
RENDER = os.path.join(QUEUE_DIR, "render_build_list.py")
EXTRACT = os.path.join(QUEUE_DIR, "extract_queue_items.py")
PROD_DB = os.path.join(REPO_ROOT, "data", "cis_memory.db")

# The complete legitimate stored vocabulary, in the order the fixture lays the
# items out. UNPARSED is NOT here: it is the extractor's own sentinel for "a
# marker was present and unreadable", and requirement 3 of this card is that it
# keeps failing recovery rather than round-tripping.
STATUSES = [
    "OPEN", "UNASSESSED", "HALF_DONE", "DONE", "PARTLY",
    "UNCLEAR", "PRESENT_UNPROVEN", "NEEDS_ERIC", "NO_CHECK_WRITTEN",
]

# The marker text render_build_list.py produces for each: underscores become
# spaces. Written out literally rather than computed, so a change to the
# rendering form fails this file instead of being absorbed by it.
CANONICAL_MARKER = {
    "OPEN": "**Need: OPEN.**",
    "UNASSESSED": "**Need: UNASSESSED.**",
    "HALF_DONE": "**Need: HALF DONE.**",
    "DONE": "**Need: DONE.**",
    "PARTLY": "**Need: PARTLY.**",
    "UNCLEAR": "**Need: UNCLEAR.**",
    "PRESENT_UNPROVEN": "**Need: PRESENT UNPROVEN.**",
    "NEEDS_ERIC": "**Need: NEEDS ERIC.**",
    "NO_CHECK_WRITTEN": "**Need: NO CHECK WRITTEN.**",
}

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

# One item per status, plus two compatibility items.
#   1.1 .. 1.9   heading items with NO marker, so the insertion branch runs --
#                the branch triage actually takes, and the branch that first
#                let these statuses reach the markdown at all
#   2.1          a BULLET item with no marker, to prove the three-word status
#                also survives inside a list line's body slice
#   2.2          holds DONE with a '**Need: BUILT ...**' marker, the shape the
#                table was first extracted FROM, and is never written through
#                queue_set.py -- so status_changed_at stays NULL, render emits the
#                body byte-for-byte, and the round trip proves the pre-table
#                spelling still comes back as the stored DONE
#   2.3          same, with a bare '**RESOLVED ...**' marker (shape 3)
BULLET_STATUS = "NO_CHECK_WRITTEN"


def fixture_items():
    """(item_num, tier, title, form, source_line, body_md, preset_need_status)."""
    items = []
    for i, status in enumerate(STATUSES, start=1):
        num = "1.%d" % i
        items.append((
            num, 1, "Item for %s" % status, "heading", 100 + i * 10,
            "### %s Item for %s\n"
            "**Checked:** prose that states no status of its own.\n"
            "\n"
            "---\n" % (num, status),
            None,
        ))
    items.append((
        "2.1", 2, "Bullet item", "bullet", 300,
        "- **2.1** a bullet item whose body is a list line, with no marker.\n",
        None,
    ))
    items.append((
        "2.2", 2, "Pre-table BUILT marker", "heading", 310,
        "### 2.2 Pre-table BUILT marker\n"
        "**Need: BUILT 2026-09-09, ONE-WAY.**\n",
        "DONE",
    ))
    items.append((
        "2.3", 2, "Bare RESOLVED marker", "heading", 320,
        "### 2.3 Bare RESOLVED marker\n"
        "**RESOLVED 2026-09-01 in the relay.**\n",
        "DONE",
    ))
    return items


results = []


def check(label, cond, detail=""):
    results.append("%s: PASS" % label if cond else "%s: FAIL — %s" % (label, detail))
    return bool(cond)


def make_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    for num, tier, title, form, line, body, preset in fixture_items():
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "source_line, source_sha, need_status) "
            "VALUES (?,?,?,?,?,?,'fixturesha',?)",
            (num, tier, title, body, form, line, preset))
    conn.execute(
        "INSERT INTO queue_sections (seq, kind, content, tier, source_sha, source_line) "
        "VALUES (0, 'preamble', '# CIS UNIFIED BUILD LIST\n\nScratch preamble.', "
        "NULL, 'fixturesha', 1)")
    conn.execute(
        "INSERT INTO queue_sections (seq, kind, content, tier, source_sha, source_line) "
        "VALUES (2, 'tier_header', '# TIER 1 — statuses', 1, 'fixturesha', 50)")
    conn.execute(
        "INSERT INTO queue_sections (seq, kind, content, tier, source_sha, source_line) "
        "VALUES (3, 'tier_header', '# TIER 2 — compatibility', 2, 'fixturesha', 290)")
    conn.commit()
    conn.close()


def run(script, *args, **env_over):
    env = dict(os.environ)
    env.update(env_over)
    return subprocess.run([sys.executable, script, *args], cwd=REPO_ROOT,
                          capture_output=True, text=True, env=env)


def classification(db):
    conn = sqlite3.connect(db)
    try:
        return {r[0]: (r[1], r[2]) for r in conn.execute(
            "SELECT item_num, need_status, scope FROM queue_items")}
    finally:
        conn.close()


def table_snapshot(db):
    """Every column of every queue row, for the zero-mutation assertions."""
    conn = sqlite3.connect(db)
    try:
        return (conn.execute("SELECT * FROM queue_items ORDER BY item_num").fetchall(),
                conn.execute("SELECT * FROM queue_sections ORDER BY seq").fetchall())
    finally:
        conn.close()


def write_all_statuses(db):
    """Drive every status through the real write path. Requirement 11: none of
    these may need --allow-unrecoverable-status any more."""
    needed_override = []
    for i, status in enumerate(STATUSES, start=1):
        p = run(QUEUE_SET, "1.%d" % i, "--status", status,
                "--scope", "CONTAINER — fixture for %s." % status,
                "--evidence", "fixture evidence for %s" % status,
                "--by", "test", CIS_SPINE_PATH=db)
        if p.returncode != 0:
            needed_override.append((status, p.returncode, p.stdout.strip()))
    p = run(QUEUE_SET, "2.1", "--status", BULLET_STATUS,
            "--scope", "REPO — the bullet.", "--evidence", "fixture evidence",
            "--by", "test", CIS_SPINE_PATH=db)
    if p.returncode != 0:
        needed_override.append((BULLET_STATUS + " (bullet)", p.returncode, p.stdout.strip()))
    return needed_override


# ── 1, 2, 6, 7, 11, 15: the full round trip ─────────────────────────────────

def test_every_status_round_trips():
    tmp = tempfile.mkdtemp(prefix="cis_vocab_rt_")
    try:
        db = os.path.join(tmp, "scratch.db")
        src = os.path.join(tmp, "UNIFIED_BUILD_LIST.md")
        make_db(db)

        refused = write_all_statuses(db)
        check("1. every legitimate status is writable with NO override flag",
              not refused, "; ".join("%s rc=%d %s" % r for r in refused))

        r = run(RENDER, CIS_SPINE_PATH=db, CIS_QUEUE_SRC=src)
        if not check("2a. the projection renders", r.returncode == 0,
                     r.stdout[-400:] + r.stderr[-400:]):
            return
        md = open(src, encoding="utf-8").read()

        # Requirement 7: assert the ACTUAL canonical rendering form, not a
        # synthetic underscore spelling. The underscore form always parsed; the
        # rendered form is what did not.
        missing = [s for s in STATUSES if CANONICAL_MARKER[s] not in md]
        check("2b. each status renders to its exact canonical marker text",
              not missing,
              "absent from the projection: %s"
              % ", ".join("%s -> %r" % (s, CANONICAL_MARKER[s]) for s in missing))

        # The MARKER, specifically: the fixture's scope prose names the status in
        # its underscore form, so a bare 'not in md' would be asserting nothing.
        check("2c. the three-word status's MARKER renders with spaces, not underscores",
              "**Need: NO CHECK WRITTEN.**" in md
              and "**Need: NO_CHECK_WRITTEN" not in md,
              "projection does not carry the canonicalised three-word marker")

        check("6a. an untouched pre-table BUILT marker is projected verbatim",
              "**Need: BUILT 2026-09-09, ONE-WAY.**" in md, md[-600:])

        # Projection -> documented recovery path -> a fresh table.
        db2 = os.path.join(tmp, "recovered.db")
        make_db(db2)
        ex = run(EXTRACT, "--force", CIS_QUEUE_DB=db2, CIS_QUEUE_SRC=src)
        if not check("3. the recovery path reads the whole projection, UNPARSED: 0",
                     ex.returncode == 0 and "UNPARSED          : 0" in ex.stdout,
                     ex.stdout[-800:] + ex.stderr[-400:]):
            return

        before, after = classification(db), classification(db2)
        diffs = [(n, before[n], after.get(n)) for n in before
                 if before[n] != after.get(n)]
        check("4. scope AND need_status survive the round trip on EVERY item",
              not diffs,
              "; ".join("%s: %r -> %r" % d for d in diffs))

        # Named per-status result, so a failure says WHICH status broke rather
        # than that something did.
        for i, status in enumerate(STATUSES, start=1):
            num = "1.%d" % i
            got = after.get(num, (None, None))[0]
            check("4.%d %s round-trips DB -> %s -> DB"
                  % (i, status, CANONICAL_MARKER[status]),
                  got == status, "came back as %r" % got)

        check("4.10 %s round-trips inside a BULLET item's body too" % BULLET_STATUS,
              after.get("2.1", (None,))[0] == BULLET_STATUS,
              "came back as %r" % (after.get("2.1", (None,))[0],))

        check("6b. stored DONE survives a verbatim BUILT marker — BUILT reads as DONE",
              before.get("2.2", (None,))[0] == "DONE"
              and after.get("2.2", (None,))[0] == "DONE",
              "2.2 %r -> %r" % (before.get("2.2"), after.get("2.2")))

        check("6c. stored DONE survives a bare RESOLVED marker — RESOLVED reads as DONE",
              before.get("2.3", (None,))[0] == "DONE"
              and after.get("2.3", (None,))[0] == "DONE",
              "2.3 %r -> %r" % (before.get("2.3"), after.get("2.3")))

        # Requirement 9, stated on its own because it is the one the two-word
        # normaliser made structurally impossible.
        conn = sqlite3.connect(db2)
        try:
            raw = conn.execute(
                "SELECT need_status, need_raw FROM queue_items WHERE item_num=?",
                ("1.9",)).fetchone()
        finally:
            conn.close()
        check("7. NO_CHECK_WRITTEN: DB -> '**Need: NO CHECK WRITTEN.**' -> DB",
              raw[0] == "NO_CHECK_WRITTEN" and raw[1] == "NO CHECK WRITTEN",
              "need_status=%r need_raw=%r" % raw)

        # Requirement 15's last leg: the recovered table re-renders equivalently.
        again = run(RENDER, "--stdout", CIS_SPINE_PATH=db2, CIS_QUEUE_SRC=src)
        body_a = "\n".join(l for l in md.splitlines() if not l.startswith("<!--"))
        body_b = "\n".join(l for l in again.stdout.splitlines()
                           if not l.startswith("<!--"))
        check("5. re-rendering the recovered table reproduces the same markdown",
              body_a == body_b,
              "projection is not idempotent across a recovery cycle")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 8, 9: the negative paths, which must NOT have been weakened ─────────────

def _negative(label_prefix, mutate, expect_in_stdout):
    """Render a good projection, corrupt ONE marker in it, and prove the
    recovery run fails and writes nothing. The file under test is the real
    rendered output, so the corruption sits in genuine canonical context."""
    tmp = tempfile.mkdtemp(prefix="cis_vocab_neg_")
    try:
        db = os.path.join(tmp, "scratch.db")
        src = os.path.join(tmp, "UNIFIED_BUILD_LIST.md")
        make_db(db)
        write_all_statuses(db)
        run(RENDER, CIS_SPINE_PATH=db, CIS_QUEUE_SRC=src)
        md = open(src, encoding="utf-8").read()
        corrupted = mutate(md)
        if corrupted == md:
            check("%sa. the fixture marker was actually corrupted" % label_prefix,
                  False, "mutation did not change the projection")
            return
        with open(src, "w", encoding="utf-8") as f:
            f.write(corrupted)

        # A fresh target that ALREADY HOLDS ROWS, so "imported nothing" is a
        # claim about mutation and not just about an empty table staying empty.
        db2 = os.path.join(tmp, "target.db")
        make_db(db2)
        write_all_statuses(db2)
        snap_before = table_snapshot(db2)

        ex = run(EXTRACT, "--force", CIS_QUEUE_DB=db2, CIS_QUEUE_SRC=src)
        snap_after = table_snapshot(db2)

        unparsed_line = next(
            (l for l in ex.stdout.splitlines() if l.startswith("UNPARSED")), "")
        count = unparsed_line.split(":")[-1].strip() if unparsed_line else ""
        check("%sa. UNPARSED > 0" % label_prefix,
              count.isdigit() and int(count) > 0,
              "UNPARSED line was %r" % unparsed_line)
        check("%sb. the recovery run exits nonzero" % label_prefix,
              ex.returncode != 0, "rc=%d" % ex.returncode)
        check("%sc. the message names the cause" % label_prefix,
              expect_in_stdout in ex.stdout, ex.stdout[-600:])
        check("%sd. the target table is byte-identical — NOTHING imported"
              % label_prefix,
              snap_before == snap_after,
              "the failed recovery run mutated the table")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_unknown_status_still_fails():
    _negative(
        "8",
        lambda md: md.replace("**Need: OPEN.**", "**Need: TOTALLY UNKNOWN STATUS.**", 1),
        "STATUS PROSE PRESENT BUT UNRECOGNISED")


def test_ambiguous_marker_still_fails():
    _negative(
        "9",
        lambda md: md.replace("**Need: PARTLY.**",
                              "**Need: PARTLY.**\n\n**Need: DONE.**", 1),
        "markers in one item")


# ── 10: queue_set.py fails CLOSED ───────────────────────────────────────────

def _broken_tree(tmp, name, extractor_source):
    """A copy of queue_set.py beside a deliberately unusable extractor.

    queue_set.py locates the extractor relative to its OWN file and imports it,
    so copying the pair into a scratch directory is what lets the unreadable case
    be exercised at all -- without touching the real tools.
    """
    d = os.path.join(tmp, name)
    os.makedirs(d)
    shutil.copy(QUEUE_SET, os.path.join(d, "queue_set.py"))
    if extractor_source is not None:
        with open(os.path.join(d, "extract_queue_items.py"), "w",
                  encoding="utf-8") as f:
            f.write(extractor_source)
    return os.path.join(d, "queue_set.py")


def test_queue_set_fails_closed():
    tmp = tempfile.mkdtemp(prefix="cis_vocab_closed_")
    try:
        cases = [
            ("10a", "missing", None, "does not exist"),
            ("10b", "syntaxerr", "def KNOWN(  # unbalanced\n", "could not be imported"),
            ("10c", "empty", "KNOWN = set()\nSTORE_AS = {}\n", "EMPTY KNOWN"),
        ]
        for label, name, source, expect in cases:
            db = os.path.join(tmp, "%s.db" % name)
            make_db(db)
            tool = _broken_tree(tmp, name, source)
            before = table_snapshot(db)

            p = run(tool, "1.1", "--status", "OPEN", "--evidence", "x",
                    "--by", "test", CIS_SPINE_PATH=db)
            check("%s. an un-inspectable recovery path REFUSES a status write (%s)"
                  % (label, name),
                  p.returncode == 2
                  and "cannot determine what the recovery path can read back" in p.stdout
                  and expect in p.stdout
                  and table_snapshot(db) == before,
                  "rc=%d %s" % (p.returncode, p.stdout[-400:] + p.stderr[-300:]))

            # The override is NOT a way past an uninspectable recovery path.
            p = run(tool, "1.1", "--status", "OPEN", "--evidence", "x",
                    "--by", "test", "--allow-unrecoverable-status",
                    CIS_SPINE_PATH=db)
            check("%s-override. --allow-unrecoverable-status does not bypass it (%s)"
                  % (label, name),
                  p.returncode == 2 and table_snapshot(db) == before,
                  "rc=%d %s" % (p.returncode, p.stdout[-400:]))

            # Requirement 10, second half: a scope write asserts nothing about
            # the status vocabulary and must not be taken down with it.
            p = run(tool, "1.1", "--scope", "CONTAINER — still writable.",
                    "--note", "scope does not consult the extractor",
                    "--by", "test", CIS_SPINE_PATH=db)
            check("%s-scope. a scope-only write still succeeds (%s)" % (label, name),
                  p.returncode == 0
                  and classification(db)["1.1"] == (None, "CONTAINER — still writable."),
                  "rc=%d %s row=%r" % (p.returncode, p.stdout[-300:],
                                       classification(db).get("1.1")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── the vocabulary guard itself ──────────────────────────────────────────────

def test_guard_covers_the_check_constraint():
    """The drift that caused OQ-TRIAGE-002, asserted directly rather than via its
    symptoms: everything the column can hold is readable, except the one value
    deliberately excluded."""
    sys.path.insert(0, QUEUE_DIR)
    import importlib
    qs = importlib.import_module("queue_set")
    readable, err = qs.recovery_readable_statuses()
    check("A. the recovery vocabulary is inspectable from the write path",
          readable is not None, str(err))
    if readable is None:
        return
    uncovered = (qs.KNOWN - readable) - {"UNPARSED"}
    check("B. every CHECK value except UNPARSED is recovery-readable",
          not uncovered, "unreadable: %s" % ", ".join(sorted(uncovered)))
    check("C. UNPARSED stays deliberately unreadable",
          "UNPARSED" not in readable,
          "the parse-failure sentinel must not round-trip as a status")


# ── production untouched ─────────────────────────────────────────────────────

def production_snapshot():
    conn = sqlite3.connect("file:%s?mode=ro" % PROD_DB, uri=True)
    try:
        return conn.execute(
            "SELECT (SELECT COUNT(*) FROM queue_items), "
            "(SELECT COUNT(*) FROM queue_items WHERE need_status IS NULL AND scope IS NULL), "
            "(SELECT COUNT(*) FROM queue_items WHERE need_status IS NOT NULL), "
            "(SELECT COUNT(*) FROM queue_items WHERE scope IS NOT NULL), "
            "(SELECT COUNT(*) FROM queue_edges), "
            "(SELECT COUNT(*) FROM queue_item_events)").fetchone()
    finally:
        conn.close()


def main():
    before = production_snapshot()
    test_every_status_round_trips()
    test_unknown_status_still_fails()
    test_ambiguous_marker_still_fails()
    test_queue_set_fails_closed()
    test_guard_covers_the_check_constraint()
    after = production_snapshot()
    check("Z. no production queue row, edge or event changed during these tests",
          before == after, "%s -> %s" % (before, after))

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print("\n%d/%d passed." % (len(results) - len(failed), len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
