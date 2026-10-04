#!/usr/bin/env python3
"""test_recovery_identity.py — OQ-TRIAGE-003 / ADR-PIPE-009.

The recovery cycle must preserve the COMPLETE queue item set, each item's
identity, and scope exactly including NULL. Two items were previously lost
SILENTLY with the run exiting 0 (WB.1, whose alphabetic prefix no regex
accepted; 4.10, whose bullet carries its title inside the bold span), and 9 of
132 scope values came back wrong, 6 of them FABRICATED from prose onto rows the
authority holds as NULL.

Every test runs the REAL scripts as subprocesses against scratch temp databases
(CIS_SPINE_PATH / CIS_QUEUE_DB / CIS_QUEUE_SRC). Production is opened read-only.

THE ZERO-MUTATION TESTS USE A TARGET THAT ALREADY CONTAINS ROWS, and assert the
target database file is BYTE-IDENTICAL afterwards. An empty target staying empty
proves nothing.

Run: python3 tools/queue/tests/test_recovery_identity.py
"""
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
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

results = []


def check(label, cond, detail=""):
    results.append(f"{label}: PASS" if cond else f"{label}: FAIL — {detail}")


def sh256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def make_db(path, items, sections=None):
    """items: [(item_num, tier, title, form, source_line, body_md, scope, need_status)]"""
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    for num, tier, title, form, line, body, scope, status in items:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "source_line, source_sha, scope, need_status) VALUES (?,?,?,?,?,?,'fx',?,?)",
            (num, tier, title, body, form, line, scope, status))
    sections = sections if sections is not None else [
        (0, "preamble", "# SCRATCH BUILD LIST\n\nPreamble.\n\n---", None, 1),
        (2, "tier_header", "# TIER 0 — trust preconditions\n", 0, 5),
        (4, "tier_header", "# TIER 4 — after the infrastructure works\n", 4, 400),
    ]
    for seq, kind, content, tier, line in sections:
        conn.execute("INSERT INTO queue_sections (seq, kind, content, tier, "
                     "source_sha, source_line) VALUES (?,?,?,?,'fx',?)",
                     (seq, kind, content, tier, line))
    conn.commit()
    conn.close()


def render(db, src, extra=()):
    env = dict(os.environ, CIS_SPINE_PATH=db, CIS_QUEUE_SRC=src)
    return subprocess.run([sys.executable, RENDER, *extra], cwd=REPO_ROOT,
                          capture_output=True, text=True, env=env)


def recover(db, src):
    env = dict(os.environ, CIS_QUEUE_DB=db, CIS_QUEUE_SRC=src)
    return subprocess.run([sys.executable, EXTRACT, "--force"], cwd=REPO_ROOT,
                          capture_output=True, text=True, env=env)


def rows(db):
    conn = sqlite3.connect(db)
    try:
        return {r[0]: r for r in conn.execute(
            "SELECT item_num, tier, title, form, scope, need_status FROM queue_items")}
    finally:
        conn.close()


# ── 8.1-8.4: every identifier form survives, and the set is complete ────────

HEAD_NUM = ("4.20", 4, "Deterministic card contract layer", "heading", 410,
            "### 4.20 Deterministic card contract layer\n"
            "Some prose about the contract layer.\n\n---\n", None, None)
# For a bullet the title is the text FOLLOWING the bold span on that line, so
# the fixture's stored title is that first line's text exactly -- the same
# convention the production table already holds.
BULLET_NUM = ("4.3", 4, "What the container regulates itself vs what needs a human",
              "bullet", 420,
              "- **4.3** What the container regulates itself vs what needs a human\n"
              "  trigger. Approval must never automate.\n", None, None)
# The REAL canonical rendering form for the WB-style id, taken from production:
# '### WB.1 — <title>', em-dash separator, title stored WITHOUT the separator.
HEAD_WB = ("WB.1", 0, "CURRENT PRIORITY: conversation-first pipeline workbench",
           "heading", 2,
           "### WB.1 — CURRENT PRIORITY: conversation-first pipeline workbench\n"
           "**Need: OPEN.** Eric prioritized this on 2026-09-17.\n", "CONTAINER", "OPEN")
# The historical bullet form that lost 4.10: identifier AND title inside the bold.
BULLET_TITLED = ("4.10", 4, "THE HARNESS SELF-IMPROVEMENT LOOP — Eric's design, 2026-08-30.",
                 "bullet", 430,
                 "- **4.10 THE HARNESS SELF-IMPROVEMENT LOOP — Eric's design, 2026-08-30.**\n"
                 "  *\"The pipeline should go through its code and make recommendations.\"*\n",
                 None, None)


def test_identifier_forms():
    tmp = tempfile.mkdtemp(prefix="cis_identity_")
    try:
        cases = [
            ("8.1. a numeric '### N.M' heading is recoverable", [HEAD_NUM]),
            ("8.2. a numeric '- **N.M**' bullet is recoverable", [BULLET_NUM]),
            ("8.3. a WB-style '### WB.1 — Title' heading is recoverable", [HEAD_WB]),
            ("8.3b. the historical '- **N.M TITLE.**' bullet is recoverable",
             [BULLET_TITLED]),
        ]
        for label, items in cases:
            d = tempfile.mkdtemp(dir=tmp)
            db, db2 = os.path.join(d, "a.db"), os.path.join(d, "r.db")
            src = os.path.join(d, "BUILD_LIST.md")
            make_db(db, items)
            make_db(db2, [HEAD_NUM])  # target already has a row
            render(db, src)
            ex = recover(db2, src)
            got, want = rows(db2), rows(db)
            check(label, ex.returncode == 0 and set(got) == set(want)
                  and got[items[0][0]][:6] == want[items[0][0]][:6],
                  f"rc={ex.returncode} got={sorted(got)} {ex.stdout[-400:]}")

        # 8.4 — all four forms in ONE projection, nothing missing.
        d = tempfile.mkdtemp(dir=tmp)
        db, db2 = os.path.join(d, "a.db"), os.path.join(d, "r.db")
        src = os.path.join(d, "BUILD_LIST.md")
        allfour = [HEAD_WB, HEAD_NUM, BULLET_NUM, BULLET_TITLED]
        make_db(db, allfour)
        make_db(db2, [HEAD_NUM])
        render(db, src)
        ex = recover(db2, src)
        got, want = rows(db2), rows(db)
        missing = set(want) - set(got)
        check("8.4. a mixed projection recovers the COMPLETE set, nothing missing",
              ex.returncode == 0 and set(got) == set(want) and not missing
              and all(got[k][:6] == want[k][:6] for k in want),
              f"rc={ex.returncode} missing={missing} "
              + "; ".join(f"{k}: {want[k]} -> {got.get(k)}" for k in want))

        # tier for a prefixed id comes from document position, not int('WB')
        check("8.4b. WB.1 recovers tier 0 from its position before every tier header",
              got["WB.1"][1] == 0, f"tier={got['WB.1'][1]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 8.6, 8.7: structural failures fail LOUDLY and mutate nothing ───────────

def test_structural_failures_mutate_nothing():
    tmp = tempfile.mkdtemp(prefix="cis_idneg_")
    try:
        # An apparent queue item whose form the grammar does not accept: the
        # identifier is there, after a real item prefix, but the bold span is
        # never closed so no accepted form matches.
        unsupported = (
            "# SCRATCH BUILD LIST\n\nPreamble.\n\n---\n"
            "# TIER 4 — after the infrastructure works\n"
            "### 4.20 Deterministic card contract layer\n"
            "Some prose.\n\n"
            "- **4.44 AN ITEM WHOSE BOLD SPAN IS NEVER CLOSED\n"
            "  and whose text continues here.\n")
        duplicate = (
            "# SCRATCH BUILD LIST\n\nPreamble.\n\n---\n"
            "# TIER 4 — after the infrastructure works\n"
            "### 4.20 Deterministic card contract layer\n"
            "First copy.\n\n"
            "### 4.20 Deterministic card contract layer\n"
            "Second copy.\n")
        cases = [
            ("8.6. an apparent item the grammar cannot read fails the run",
             unsupported, "APPARENT QUEUE ITEM THE PARSER CANNOT READ", "4.44"),
            ("8.7. a duplicate item identity fails before mutation",
             duplicate, "DUPLICATE ITEM IDENTITY", "4.20"),
        ]
        for label, text, banner, needle in cases:
            d = tempfile.mkdtemp(dir=tmp)
            db2 = os.path.join(d, "target.db")
            src = os.path.join(d, "BUILD_LIST.md")
            make_db(db2, [HEAD_NUM, BULLET_NUM])  # target ALREADY has rows
            open(src, "w", encoding="utf-8").write(text)
            before_hash, before_rows = sh256(db2), rows(db2)
            ex = recover(db2, src)
            check(label,
                  ex.returncode != 0 and banner in ex.stdout and needle in ex.stdout
                  and "NOTHING WAS IMPORTED" in ex.stdout
                  and sh256(db2) == before_hash and rows(db2) == before_rows,
                  f"rc={ex.returncode} hash_changed={sh256(db2) != before_hash} "
                  f"{ex.stdout[-600:]}")

        # And the diagnostic must name the offending LINE, not just complain.
        d = tempfile.mkdtemp(dir=tmp)
        db2 = os.path.join(d, "t.db")
        src = os.path.join(d, "B.md")
        make_db(db2, [HEAD_NUM])
        open(src, "w", encoding="utf-8").write(unsupported)
        ex = recover(db2, src)
        # The unsupported bullet is the 10th line of that fixture.
        check("8.6b. the diagnostic identifies the offending line number",
              "line 10" in ex.stdout, ex.stdout[-400:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 9.1, 9.2, 9.6, 9.7: scope is a marker, never prose ─────────────────────

# The exact false-positive class measured in production: a '**Scope:**' label
# that begins a WRAPPED PROSE PARAGRAPH. The old parser captured to
# end-of-line and turned the line-wrap boundary into a classification.
PROSE_FULLSPEC = ("4.29", 4, "Single authority contract", "heading", 440,
                  "### 4.29 Single authority contract\n"
                  "The read model and the live database disagree.\n\n"
                  "**Scope:** Full spec:\n"
                  "`data/agent_handoffs/CARD_01_SINGLE_AUTHORITY_CONTRACT.md`.\n"
                  "Inventory existing DB-backed authority, implement one canonical\n"
                  "host-side read model over it.\n\n---\n", None, None)
PROSE_REVIEWER = ("4.28", 4, "Independent verification of WB.1A", "heading", 450,
                  "### 4.28 Independent verification of WB.1A\n"
                  "Nothing has independently verified these cards.\n\n"
                  "**Scope:** An independent reviewer (Codex, matching the WB.1B-2A/2B/3\n"
                  "pattern) reads WB.1A's own card, evidence.md and completion.json.\n\n"
                  "---\n", None, None)
PROSE_CONTAINED = ("4.20", 4, "Deterministic card contract layer", "heading", 460,
                   "### 4.20 Deterministic card contract layer\n"
                   "Prose above.\n\n"
                   "**Scope:** CONTAINED PIPELINE — everything below is about the in-container\n"
                   "system, not the host-side tooling that already exists.\n\n---\n",
                   None, None)
# A legitimate scope that ALSO wraps -- the case that makes line-containment
# useless as a distinguisher. Authority holds a value; it must come back exactly.
WRAPS_LEGIT = ("3.26", 3, "Prompt assembly", "heading", 470,
               "### 3.26 Prompt assembly\n"
               "**Scope:** CONTAINER — prompt assembly in `pipeline_relay.py`,\n"
               "and the tables it reads.\n\n---\n",
               "CONTAINER — prompt assembly in `pipeline_relay.py`", None)
# The legacy value that must NOT be normalised (ADR-PIPE-009 clause 9).
LEGACY_NEWLINE = ("1.20", 1, "Repointed evaluator", "heading", 480,
                  "### 1.20 Repointed evaluator\n"
                  "**Scope — REPOINTED 2026-09-07. It is `evaluator` on 8650.**\n"
                  "This item was written 2026-09-02.\n\n---\n",
                  "**Scope — REPOINTED 2026-09-07. It is `evaluator` on 8650.**\n"
                  "This item was written 2026-09-02, when review1 was the only Qwen",
                  None)
QUOTED = ("2.19", 2, "Quoted scope", "heading", 490,
          "### 2.19 Quoted scope\n" "Prose.\n\n---\n",
          'CONTAINER — agent.log says "registered 18 tools" on 2026-08-29', None)
ARROWY = ("2.20", 2, "Arrow scope", "heading", 495,
          "### 2.20 Arrow scope\n" "Prose.\n\n---\n",
          "REPO — INSERT OR REPLACE --> append, and a > b", None)


def test_scope_contract():
    tmp = tempfile.mkdtemp(prefix="cis_scope3_")
    try:
        d = tempfile.mkdtemp(dir=tmp)
        db, db2 = os.path.join(d, "a.db"), os.path.join(d, "r.db")
        src = os.path.join(d, "BUILD_LIST.md")
        items = [PROSE_FULLSPEC, PROSE_REVIEWER, PROSE_CONTAINED, WRAPS_LEGIT,
                 LEGACY_NEWLINE, QUOTED, ARROWY, HEAD_WB]
        make_db(db, items)
        make_db(db2, [HEAD_NUM])
        r = render(db, src)
        md = open(src, encoding="utf-8").read()
        ex = recover(db2, src)
        got, want = rows(db2), rows(db)

        check("9.1. prose-only '**Scope:**' paragraphs recover as NULL, not a value",
              ex.returncode == 0
              and got["4.29"][4] is None and got["4.28"][4] is None
              and got["4.20"][4] is None,
              f"rc={ex.returncode} 4.29={got.get('4.29', (None,)*5)[4]!r} "
              f"4.28={got.get('4.28', (None,)*5)[4]!r} "
              f"4.20={got.get('4.20', (None,)*5)[4]!r} {ex.stdout[-400:]}")

        check("9.6. the measured false-positive strings never become a scope",
              all(got[k][4] is None for k in ("4.29", "4.28", "4.20"))
              and "Full spec:" not in {got[k][4] for k in got}
              and all(got[k][4] != "An independent reviewer (Codex, matching the "
                                   "WB.1B-2A/2B/3" for k in got),
              str({k: got[k][4] for k in got}))

        check("9.1b. the author's prose is still in the document, untouched",
              "**Scope:** Full spec:" in md
              and "**Scope:** An independent reviewer (Codex, matching the "
                  "WB.1B-2A/2B/3" in md,
              "historical prose was rewritten or dropped")

        check("9.2. every explicit canonical marker recovers EXACTLY",
              all(got[k][4] == want[k][4] for k in want),
              "; ".join(f"{k}: {want[k][4]!r} -> {got.get(k, (None,)*5)[4]!r}"
                        for k in want if got.get(k, (None,)*5)[4] != want[k][4]))

        check("9.2b. a legitimate scope whose prose paragraph WRAPS still recovers",
              got["3.26"][4] == want["3.26"][4],
              f"{want['3.26'][4]!r} -> {got['3.26'][4]!r}")

        check("9.2c. a legacy scope containing a NEWLINE round-trips unnormalised",
              got["1.20"][4] == want["1.20"][4] and "\n" in got["1.20"][4],
              f"{want['1.20'][4]!r} -> {got['1.20'][4]!r}")

        check("9.2d. a scope containing a double quote round-trips",
              got["2.19"][4] == want["2.19"][4], f"-> {got['2.19'][4]!r}")

        check("9.2e. a scope containing '-->' cannot close the comment early",
              got["2.20"][4] == want["2.20"][4]
              and "cis:scope" in md and md.count("-->\n") >= 1,
              f"-> {got['2.20'][4]!r}")

        # Re-rendering the recovered table must reproduce the same markdown:
        # after recovery the stored body_md CONTAINS the marker, so a render
        # that appended rather than replaced would drift every cycle.
        src2 = os.path.join(d, "AGAIN.md")
        render(db2, src2)
        a = [l for l in md.splitlines() if not l.startswith("<!-- state_revision")]
        b = [l for l in open(src2, encoding="utf-8").read().splitlines()
             if not l.startswith("<!-- state_revision")]
        check("9.2f. re-rendering the recovered table is byte-idempotent",
              a == b, "projection drifts across a recovery cycle")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_malformed_scope_marker_fails():
    """9.7 — absence is allowed; present-but-unreadable is NOT silently NULL."""
    tmp = tempfile.mkdtemp(prefix="cis_scopeneg_")
    try:
        head = ("# SCRATCH BUILD LIST\n\nPreamble.\n\n---\n"
                "# TIER 4 — after the infrastructure works\n")
        cases = [
            ("9.7a. an unterminated cis:scope marker fails the run",
             '<!-- cis:scope="CONTAINER — unterminated -->\n', "malformed"),
            ("9.7b. a cis:scope value that is not valid JSON fails the run",
             '<!-- cis:scope=CONTAINER —  bare -->\n', "malformed"),
            ("9.7c. a cis:scope value that is not a string fails the run",
             '<!-- cis:scope=12345 -->\n', "malformed"),
            ("9.7d. an empty cis:scope value fails the run",
             '<!-- cis:scope="   " -->\n', "empty"),
            ("9.7e. two cis:scope markers in one item fail the run",
             '<!-- cis:scope="CONTAINER — one" -->\n\n'
             '<!-- cis:scope="REPO — two" -->\n', "ambiguous"),
        ]
        for label, marker, needle in cases:
            d = tempfile.mkdtemp(dir=tmp)
            db2 = os.path.join(d, "target.db")
            src = os.path.join(d, "B.md")
            make_db(db2, [HEAD_NUM, BULLET_NUM])  # target ALREADY has rows
            open(src, "w", encoding="utf-8").write(
                head + "### 4.20 Deterministic card contract layer\nProse.\n\n"
                + marker)
            before_hash, before_rows = sh256(db2), rows(db2)
            ex = recover(db2, src)
            check(label,
                  ex.returncode != 0
                  and "SCOPE CLASSIFICATION PRESENT BUT UNREADABLE" in ex.stdout
                  and needle in ex.stdout
                  and "NOTHING WAS IMPORTED" in ex.stdout
                  and sh256(db2) == before_hash and rows(db2) == before_rows,
                  f"rc={ex.returncode} hash_changed={sh256(db2) != before_hash} "
                  f"{ex.stdout[-500:]}")

        # The other half of the same rule: NO marker is NOT a failure.
        d = tempfile.mkdtemp(dir=tmp)
        db2 = os.path.join(d, "t.db")
        src = os.path.join(d, "B.md")
        make_db(db2, [HEAD_NUM])
        open(src, "w", encoding="utf-8").write(
            head + "### 4.20 Deterministic card contract layer\n"
                   "Prose with no marker at all.\n")
        ex = recover(db2, src)
        check("9.7f. NO marker is a normal outcome and recovers NULL without failing",
              ex.returncode == 0 and rows(db2)["4.20"][4] is None, ex.stdout[-300:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 8.5, 9.3, 9.4, 9.5: the whole-queue production-copy proof ──────────────

def test_production_copy_whole_queue():
    tmp = tempfile.mkdtemp(prefix="cis_prodcopy_")
    try:
        auth = os.path.join(tmp, "authority.db")
        recov = os.path.join(tmp, "recovered.db")
        src = os.path.join(tmp, "projection.md")
        src2 = os.path.join(tmp, "again.md")

        # Copy production read-only. BOTH copies are full, so the recovery
        # target already contains every row before the run.
        s = sqlite3.connect(f"file:{PROD_DB}?mode=ro", uri=True)
        for p in (auth, recov):
            d = sqlite3.connect(p)
            s.backup(d)
            d.close()
        s.close()

        A = rows(auth)
        r = render(auth, src)
        ex = recover(recov, src)
        R = rows(recov)

        check("8.5a. the production-copy recovery runs clean",
              r.returncode == 0 and ex.returncode == 0
              and "UNPARSED          : 0" in ex.stdout
              and "apparent unparsed : 0" in ex.stdout
              and "duplicate ids     : 0" in ex.stdout
              and "scope errors      : 0" in ex.stdout,
              f"render={r.returncode} extract={ex.returncode} {ex.stdout[-700:]}")

        check("8.5b. the recovered item_num SET equals the authoritative set",
              set(A) == set(R),
              f"missing={sorted(set(A) - set(R))} unexpected={sorted(set(R) - set(A))}")

        check("8.5c. the recovered item COUNT equals the authoritative count",
              len(A) == len(R), f"{len(A)} vs {len(R)}")

        check("8.5d. WB.1 and 4.10 are both in the recovered table",
              "WB.1" in R and "4.10" in R, f"WB.1={'WB.1' in R} 4.10={'4.10' in R}")

        mm = [(k, A[k][4], R[k][4]) for k in A if A[k][4] != R[k][4]]
        check("9.3. every production scope value survives EXACTLY, NULL included",
              not mm, "; ".join(f"{k}: {a!r} -> {b!r}" for k, a, b in mm[:6]))

        # 9.4 + 9.5: the nine rows the card named, by name.
        NINE = ("3.29", "3.30", "3.31", "4.20", "4.28", "4.29", "4.30", "4.31", "4.32")
        check("9.4/9.5. all nine previously-mismatched rows now round-trip exactly",
              all(A[k][4] == R[k][4] for k in NINE),
              "; ".join(f"{k}: {A[k][4]!r} -> {R[k][4]!r}"
                        for k in NINE if A[k][4] != R[k][4]))
        check("9.4b. the six authoritative-NULL rows recover NULL, not a fabrication",
              all(R[k][4] is None for k in
                  ("4.20", "4.28", "4.29", "4.30", "4.31", "4.32")),
              str({k: R[k][4] for k in ("4.20", "4.28", "4.29", "4.30", "4.31", "4.32")}))

        sm = [(k, A[k][5], R[k][5]) for k in A if A[k][5] != R[k][5]]
        check("10a. every production need_status survives exactly (ADR-PIPE-008)",
              not sm, "; ".join(f"{k}: {a!r} -> {b!r}" for k, a, b in sm[:6]))

        tm = [(k, A[k][1], R[k][1]) for k in A if A[k][1] != R[k][1]]
        check("10b. every tier survives exactly, including WB.1's position-derived 0",
              not tm, str(tm[:6]))

        ttl = [(k, A[k][2], R[k][2]) for k in A if A[k][2] != R[k][2]]
        check("10c. every title survives exactly", not ttl, str(ttl[:4]))

        # Re-render the recovered database and compare to the projection.
        render(recov, src2)
        def body(p):
            return [l for l in open(p, encoding="utf-8").read().splitlines()
                    if not l.startswith("<!-- state_revision")]
        check("10d. re-rendering the recovered table reproduces the projection "
              "(state_revision excepted: it is derived from DB content, and these "
              "are two different databases)",
              body(src) == body(src2), "queue CONTENT drifted across the cycle")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── production untouched ────────────────────────────────────────────────────

def production_snapshot():
    conn = sqlite3.connect(f"file:{PROD_DB}?mode=ro", uri=True)
    try:
        return conn.execute(
            "SELECT (SELECT COUNT(*) FROM queue_items), "
            "(SELECT COUNT(*) FROM queue_edges), "
            "(SELECT COUNT(*) FROM queue_item_events), "
            "(SELECT COUNT(*) FROM queue_sections), "
            "(SELECT COUNT(*) FROM queue_items WHERE scope IS NOT NULL), "
            "(SELECT COUNT(*) FROM queue_items WHERE need_status IS NOT NULL)"
        ).fetchone()
    finally:
        conn.close()


def run():
    before = production_snapshot()
    test_identifier_forms()
    test_structural_failures_mutate_nothing()
    test_scope_contract()
    test_malformed_scope_marker_fails()
    test_production_copy_whole_queue()
    after = production_snapshot()
    check("11. no production queue row, edge, event or section changed",
          before == after, f"{before} -> {after}")

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
