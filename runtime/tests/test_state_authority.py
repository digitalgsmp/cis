#!/usr/bin/env python3
"""test_state_authority.py — negative tests for project_state single-valued
authority enforcement (runtime/db/state_authority.py, migration 0040, and
the strengthened tools/gates/gate_build_state_coherence.py).

EVERY TEST HERE IS A REGRESSION ASSERTION, not just a feature check. Each
one reproduces the DEFECTIVE rule inline — the exact SQL the repository
used before this card — asserts that it produces the wrong answer on the
scenario, and then asserts the corrected mechanism produces the right one.
A test that only exercised the new code would not prove the old code was
broken, and "this scenario must fail against the defective implementation
and pass after correction" is the card's own requirement.

The defective rules, verbatim in shape:

  DEFECT_A  newest-live-wins:  superseded_at IS NULL AND id = MAX(id)
            (was runtime/db/database.get_project_state and the coherence
            gate's own loader)
  DEFECT_B  recency-wins:      ORDER BY created_at DESC, id DESC LIMIT 1,
            superseded_at not consulted at all
            (was tools/state/build_path._latest_state)
  DEFECT_C  append-only write:  INSERT with no supersession
            (was runtime/db/database.insert_project_state, with
            supersede_project_state as a separate, never-called function)

ISOLATION. Every test builds its own temporary SQLite file under a private
tmpdir and deletes it. Nothing here opens, reads or writes
data/cis_memory.db, and nothing here introduces a contradictory record
anywhere near production — the only live-spine interaction in this file is
the final read-only check that historical rows are intact, which opens the
spine with mode=ro.

Run: python3 runtime/tests/test_state_authority.py
"""
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_HERE, ".."))  # runtime/
sys.path.insert(0, _REPO_ROOT)

from db import state_authority as sa  # noqa: E402
from db import database as dbmod  # noqa: E402

MIGRATION_0040 = os.path.join(
    _REPO_ROOT, "runtime", "schema", "migrations", "0040_project_state_single_live.sql")
GATE = os.path.join(_REPO_ROOT, "tools", "gates", "gate_build_state_coherence.py")
LIVE_SPINE = os.environ.get(
    "CIS_SPINE_PATH", os.path.join(_REPO_ROOT, "data", "cis_memory.db"))

results = []


def check(label, condition, detail=""):
    results.append(f"{label}: {'PASS' if condition else 'FAIL'}"
                   + (f"  [{detail}]" if detail and not condition else ""))
    return bool(condition)


# ── the project_state schema, exactly as 0002_project_state.sql declares it ──

PROJECT_STATE_DDL = """
CREATE TABLE project_state (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key             TEXT NOT NULL,
    value           TEXT NOT NULL,
    source          TEXT NOT NULL CHECK (source IN ('git', 'gate', 'manual')),
    evidence_hash   TEXT,
    evidence_run_id TEXT,
    created_at      TEXT NOT NULL,
    superseded_at   TEXT,
    superseded_by   INTEGER REFERENCES project_state(id)
);
CREATE INDEX idx_project_state_key_created ON project_state(key, created_at);
"""


def fresh_db(tmpdir, name="spine.db", with_migration_0040=False):
    path = os.path.join(tmpdir, name)
    conn = sqlite3.connect(path)
    conn.executescript(PROJECT_STATE_DDL)
    if with_migration_0040:
        with open(MIGRATION_0040) as f:
            conn.executescript(f.read())
    conn.commit()
    conn.row_factory = sqlite3.Row
    return path, conn


def raw_insert(conn, key, value, source="manual", created_at="2026-01-01T00:00:00+00:00",
               superseded_at=None, superseded_by=None):
    """A write that bypasses every sanctioned path — the direct-database
    mutation case. Used to manufacture the conflicts a resolver must
    detect, never to repair anything."""
    cur = conn.execute(
        "INSERT INTO project_state (key, value, source, created_at, superseded_at, "
        "superseded_by) VALUES (?,?,?,?,?,?)",
        (key, value, source, created_at, superseded_at, superseded_by))
    conn.commit()
    return cur.lastrowid


# ── the defective rules, reproduced so they can be asserted broken ────────

def defect_a_newest_live_wins(conn, key):
    """runtime/db/database.get_project_state, before this card."""
    row = conn.execute(
        """SELECT key, value, id FROM project_state
           WHERE superseded_at IS NULL
             AND id = (SELECT MAX(id) FROM project_state ps2
                        WHERE ps2.key = project_state.key
                          AND ps2.superseded_at IS NULL)
             AND key = ?""", (key,)).fetchone()
    return None if row is None else {"id": row["id"], "value": row["value"]}


def defect_b_recency_wins(conn, key):
    """tools/state/build_path._latest_state, before this card."""
    row = conn.execute(
        "SELECT id, key, value, source, created_at FROM project_state "
        "WHERE key = ? ORDER BY created_at DESC, id DESC LIMIT 1", (key,)).fetchone()
    return None if row is None else {"id": row["id"], "value": row["value"]}


# ── 1. two sanctioned inserts cannot leave two live rows ──────────────────

def test_1_two_sanctioned_inserts_leave_one_live_row():
    tmp = tempfile.mkdtemp(prefix="cis-sa-1-")
    try:
        path, conn = fresh_db(tmp)

        # DEFECTIVE: append-only insert, twice. Two live rows.
        defective = sqlite3.connect(os.path.join(tmp, "defective.db"))
        defective.executescript(PROJECT_STATE_DDL)
        for v in ("first", "second"):
            defective.execute(
                "INSERT INTO project_state (key, value, source, created_at) "
                "VALUES ('build_phase', ?, 'manual', '2026-01-01T00:00:00+00:00')", (v,))
        defective.commit()
        n_defective = defective.execute(
            "SELECT COUNT(*) FROM project_state "
            "WHERE key='build_phase' AND superseded_at IS NULL").fetchone()[0]
        defective.close()
        check("1a. DEFECT_C append-only writer leaves 2 live rows after 2 writes",
              n_defective == 2, f"got {n_defective}")

        # CORRECTED: the sanctioned writer, twice.
        r1 = sa.set_state(conn, "build_phase", "first", "manual")
        r2 = sa.set_state(conn, "build_phase", "second", "manual")
        live = conn.execute(
            "SELECT id, value FROM project_state "
            "WHERE key='build_phase' AND superseded_at IS NULL").fetchall()
        check("1b. sanctioned writer leaves exactly 1 live row after 2 writes",
              len(live) == 1, f"got {len(live)}")
        check("1c. the live row is the second write", live and live[0]["value"] == "second",
              live and live[0]["value"])

        old = conn.execute("SELECT superseded_at, superseded_by FROM project_state "
                           "WHERE id = ?", (r1["new_row_id"],)).fetchone()
        check("1d. the first row is superseded, with superseded_at set",
              old["superseded_at"] is not None)
        check("1e. the first row's superseded_by points at the second row",
              old["superseded_by"] == r2["new_row_id"],
              f"{old['superseded_by']} != {r2['new_row_id']}")
        check("1f. history is preserved — both rows still exist",
              conn.execute("SELECT COUNT(*) FROM project_state "
                           "WHERE key='build_phase'").fetchone()[0] == 2)

        # And the same holds through the preserved public API.
        dbmod.insert_project_state(conn, "build_phase", "third", "manual")
        conn.commit()
        check("1g. database.insert_project_state (unchanged signature) also "
              "leaves exactly 1 live row",
              conn.execute("SELECT COUNT(*) FROM project_state WHERE key='build_phase' "
                           "AND superseded_at IS NULL").fetchone()[0] == 1)
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 2. concurrent writes cannot produce conflicting current records ───────

def test_2_concurrent_writes_cannot_conflict():
    tmp = tempfile.mkdtemp(prefix="cis-sa-2-")
    try:
        path, setup = fresh_db(tmp)
        sa.set_state(setup, "next_tier", "5", "gate")
        setup.close()

        # DEFECTIVE: the read-then-write shape the old code required of a
        # caller — read which row is live, insert, then supersede what you
        # read. Two threads interleaved on it leave two live rows, because
        # each supersedes only the row it saw.
        dpath = os.path.join(tmp, "defective.db")
        dconn = sqlite3.connect(dpath)
        dconn.executescript(PROJECT_STATE_DDL)
        dconn.execute("INSERT INTO project_state (key, value, source, created_at) "
                      "VALUES ('next_tier','5','gate','2026-01-01T00:00:00+00:00')")
        dconn.commit()
        dconn.close()

        barrier = threading.Barrier(2)

        def defective_writer(value):
            c = sqlite3.connect(dpath, timeout=10)
            live = c.execute("SELECT id FROM project_state WHERE key='next_tier' "
                             "AND superseded_at IS NULL").fetchall()
            barrier.wait()          # both threads have now read the same live set
            time.sleep(0.02)
            cur = c.execute("INSERT INTO project_state (key, value, source, created_at) "
                            "VALUES ('next_tier', ?, 'gate', '2026-01-02T00:00:00+00:00')",
                            (value,))
            for row in live:
                c.execute("UPDATE project_state SET superseded_at='2026-01-02T00:00:00+00:00', "
                          "superseded_by=? WHERE id=?", (cur.lastrowid, row[0]))
            c.commit()
            c.close()

        threads = [threading.Thread(target=defective_writer, args=(v,)) for v in ("6", "7")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        dconn = sqlite3.connect(dpath)
        n_defective = dconn.execute(
            "SELECT COUNT(*) FROM project_state WHERE key='next_tier' "
            "AND superseded_at IS NULL").fetchone()[0]
        dconn.close()
        check("2a. DEFECT_C read-then-write under concurrency leaves 2 live rows",
              n_defective == 2, f"got {n_defective}")

        # CORRECTED: the same two writers, through set_state. Its
        # BEGIN IMMEDIATE serializes the read-modify-write, so the second
        # writer re-reads and supersedes the row the first one created.
        errors = []

        def sanctioned_writer(value):
            c = sqlite3.connect(path, timeout=15)
            c.execute("PRAGMA busy_timeout = 15000")
            try:
                barrier2.wait()
                sa.set_state(c, "next_tier", value, "gate")
            except Exception as e:  # noqa: BLE001 — recorded, then asserted on
                errors.append(f"{type(e).__name__}: {e}")
            finally:
                c.close()

        barrier2 = threading.Barrier(2)
        threads = [threading.Thread(target=sanctioned_writer, args=(v,)) for v in ("6", "7")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        live = conn.execute("SELECT id, value FROM project_state WHERE key='next_tier' "
                            "AND superseded_at IS NULL").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM project_state "
                             "WHERE key='next_tier'").fetchone()[0]
        check("2b. two concurrent sanctioned writes leave exactly 1 live row",
              len(live) == 1, f"got {len(live)}: {[dict(r) for r in live]}; errors={errors}")
        check("2c. a write that lost the race either committed or refused — never "
              "half-applied", total in (2, 3), f"{total} rows total")
        res = sa.resolve_current(conn, "next_tier")
        check("2d. the resolver reports RESOLVED after the race",
              res["status"] == sa.RESOLVED, f"{res['status']}: {res['note']}")
        chain_broken, _ = sa.supersession_violations(conn, "next_tier")
        check("2e. no supersession violation survives the race", not chain_broken,
              str(chain_broken))
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 3. a conflict created outside the sanctioned writer is detected ───────

def test_3_unsanctioned_conflict_is_detected():
    tmp = tempfile.mkdtemp(prefix="cis-sa-3-")
    try:
        path, conn = fresh_db(tmp)
        a = raw_insert(conn, "next_action", "do A", created_at="2026-01-01T00:00:00+00:00")
        b = raw_insert(conn, "next_action", "do B", created_at="2026-01-02T00:00:00+00:00")

        # DEFECTIVE: both readers answer confidently, and they answer with
        # one of the two candidates as though it had won.
        da = defect_a_newest_live_wins(conn, "next_action")
        db_ = defect_b_recency_wins(conn, "next_action")
        check("3a. DEFECT_A silently serves one of two live rows",
              da is not None and da["id"] == b, str(da))
        check("3b. DEFECT_B silently serves one of two live rows",
              db_ is not None and db_["id"] == b, str(db_))

        # CORRECTED: the resolver reports a conflict and names both rows.
        res = sa.resolve_current(conn, "next_action")
        check("3c. resolver reports CONFLICT, not a value",
              res["status"] == sa.CONFLICT and res["value"] is None, str(res["status"]))
        check("3d. resolver names both conflicting rows",
              sorted(r["id"] for r in res["live_rows"]) == sorted([a, b]),
              str([r["id"] for r in res["live_rows"]]))
        check("3e. conflict result carries enough to identify the rows "
              "(id, value, source, created_at)",
              all(k in res["live_rows"][0] for k in ("id", "value", "source", "created_at")))
        check("3f. current_value(strict=True) raises rather than guessing",
              _raises(sa.AmbiguousStateError, sa.current_value, conn, "next_action"))
        view = sa.current_state_map(conn)
        check("3g. the {key: value} reader yields a ConflictMarker, not a candidate value",
              isinstance(view.get("next_action"), sa.ConflictMarker), repr(view.get("next_action")))
        check("3h. the ConflictMarker's text names the key and both row ids",
              all(s in str(view["next_action"]) for s in ("next_action", str(a), str(b))),
              str(view["next_action"]))
        check("3i. the sanctioned writer refuses to write on top of the conflict",
              _raises(sa.AmbiguousStateError, sa.set_state, conn, "next_action",
                      "do C", "manual"))
        check("3j. the refused write wrote nothing",
              conn.execute("SELECT COUNT(*) FROM project_state "
                           "WHERE key='next_action'").fetchone()[0] == 2)
        conn.close()

        # And with migration 0040 applied, the database itself refuses the
        # second live row — direct mutation included.
        path2, conn2 = fresh_db(tmp, "guarded.db", with_migration_0040=True)
        raw_insert(conn2, "next_action", "do A")
        check("3k. with migration 0040 applied, a direct INSERT creating a second "
              "live row is rejected by the database",
              _raises(sqlite3.IntegrityError, raw_insert, conn2, "next_action", "do B"))
        check("3l. the sanctioned writer still works with the index in place",
              sa.set_state(conn2, "next_action", "do B", "manual")["new_row_id"] is not None)
        check("3m. and still leaves exactly 1 live row",
              conn2.execute("SELECT COUNT(*) FROM project_state WHERE key='next_action' "
                            "AND superseded_at IS NULL").fetchone()[0] == 1)
        conn2.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 4. the coherence gate fails on duplicate live authoritative rows ──────

def _gate_fixture(tmp, name, duplicate=False, broken_chain=False):
    """A spine the coherence gate can actually run against: project_state
    plus the completed_tier/build_phase/next_tier values checks 1-3 need."""
    path, conn = fresh_db(tmp, name)
    sa.set_state(conn, "completed_tier", "7.5b", "gate")
    sa.set_state(conn, "build_phase", "Tier 8 — MCP Bridge", "gate")
    sa.set_state(conn, "next_tier", "8", "gate")
    if duplicate:
        raw_insert(conn, "next_action", "do A", created_at="2026-01-01T00:00:00+00:00")
        raw_insert(conn, "next_action", "do B", created_at="2026-01-02T00:00:00+00:00")
    if broken_chain:
        # superseded_by set while the row is still live: it is both current
        # and replaced, which the schema cannot mean.
        rid = raw_insert(conn, "current_queue_item", "4.32")
        conn.execute("UPDATE project_state SET superseded_by = ? WHERE id = ?", (rid, rid + 1))
        raw_insert(conn, "current_queue_item", "4.33", superseded_by=rid)
        conn.commit()
    conn.commit()
    conn.close()
    return path


def _run_gate(db_path):
    config = os.path.join(_REPO_ROOT, "config", "agents_static.yaml")
    proc = subprocess.run([sys.executable, GATE, "--db", db_path, "--config", config],
                          capture_output=True, text=True, timeout=180, cwd=_REPO_ROOT)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def test_4_gate_fails_on_duplicate_live_rows():
    tmp = tempfile.mkdtemp(prefix="cis-sa-4-")
    try:
        clean = _gate_fixture(tmp, "clean.db")
        rc, out = _run_gate(clean)
        check("4a. gate PASSES on a coherent, single-valued spine", rc == 0, out[-700:])
        check("4b. and says the single-valued contract holds",
              "single-valued authority holds" in out, out[-400:])

        dup = _gate_fixture(tmp, "dup.db", duplicate=True)
        rc, out = _run_gate(dup)
        check("4c. gate FAILS (exit 1) on duplicate live authoritative rows",
              rc == 1, f"exit {rc}: {out[-700:]}")
        check("4d. the failure names the affected key", "project_state.next_action" in out,
              out[-500:])
        check("4e. the failure names the conflicting record ids",
              re.search(r"ids 1?\d+, 1?\d+", out) is not None, out[-500:])
        check("4f. the gate still reports the pre-existing checks "
              "(behaviour not weakened)", "build state is coherent" in out, out[-500:])

        broken = _gate_fixture(tmp, "broken.db", broken_chain=True)
        rc, out = _run_gate(broken)
        check("4g. gate FAILS on a broken supersession relationship", rc == 1,
              f"exit {rc}: {out[-700:]}")
        check("4h. and names it as a schema-contract violation",
              "supersession relationship violates the schema contract" in out, out[-500:])

        # DEFECTIVE: the gate's own loader, before this card, could not see
        # the second row at all — which is why it passed with 161 and 166
        # both live.
        dconn = sqlite3.connect(dup)
        dconn.row_factory = sqlite3.Row
        seen = defect_a_newest_live_wins(dconn, "next_action")
        dconn.close()
        check("4i. DEFECT_A loader returns one row and is structurally blind to the "
              "duplicate (why the gate used to pass)", seen is not None, str(seen))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 5. a later-created superseded row is never current ───────────────────

def test_5_later_created_superseded_row_is_never_current():
    tmp = tempfile.mkdtemp(prefix="cis-sa-5-")
    try:
        path, conn = fresh_db(tmp)
        # The live row is OLDER than a superseded row. This is the exact
        # shape under which recency-wins picks a replaced record.
        #
        # The superseded row is left UNLINKED (superseded_by NULL) on
        # purpose: that is the dominant historical pattern on the real
        # spine (104 rows), it is schema-legal, and it keeps this test
        # about recency alone. Pointing it at the older live row would
        # instead be a successor_predates_predecessor chain violation,
        # which test 6 covers separately.
        live_id = raw_insert(conn, "pipeline_roadmap", "LIVE ROADMAP",
                             created_at="2026-01-01T00:00:00+00:00")
        stale_id = raw_insert(conn, "pipeline_roadmap", "SUPERSEDED ROADMAP",
                              created_at="2026-06-01T00:00:00+00:00",
                              superseded_at="2026-06-02T00:00:00+00:00",
                              superseded_by=None)

        db_ = defect_b_recency_wins(conn, "pipeline_roadmap")
        check("5a. DEFECT_B (recency wins) selects the SUPERSEDED row",
              db_ is not None and db_["id"] == stale_id, str(db_))

        res = sa.resolve_current(conn, "pipeline_roadmap")
        check("5b. resolver selects the live row, not the newer superseded one",
              res["status"] == sa.RESOLVED and res["row_id"] == live_id,
              f"{res['status']} row={res['row_id']}")
        check("5c. and the value is the live row's value",
              res["value"] == "LIVE ROADMAP", str(res["value"]))

        # Through the real read model that used to hold DEFECT_B.
        sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "state"))
        import build_path  # noqa: E402  (imported here: it needs tools/state on the path)
        row = build_path._latest_state(conn, "pipeline_roadmap")
        check("5d. build_path._latest_state (the corrected reader) returns the live row",
              row is not None and row["id"] == live_id, str(row))

        # The all-superseded case is reported, never backfilled from history.
        conn.execute("UPDATE project_state SET superseded_at='2026-07-01T00:00:00+00:00' "
                     "WHERE id=?", (live_id,))
        conn.commit()
        res = sa.resolve_current(conn, "pipeline_roadmap")
        check("5e. with every row superseded the resolver reports ABSENT, not the "
              "newest row", res["status"] == sa.ABSENT and res["value"] is None,
              f"{res['status']} {res['value']!r}")
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 6. broken supersession relationships are detected ────────────────────

def test_6_broken_supersession_is_detected():
    tmp = tempfile.mkdtemp(prefix="cis-sa-6-")
    try:
        cases = {}

        # (a) live row claiming a successor
        path, conn = fresh_db(tmp, "a.db")
        r1 = raw_insert(conn, "build_phase", "one")
        conn.execute("UPDATE project_state SET superseded_by=? WHERE id=?", (r1, r1))
        # self-reference AND live-claims-successor at once; split them:
        conn.execute("UPDATE project_state SET superseded_by=NULL WHERE id=?", (r1,))
        r2 = raw_insert(conn, "build_phase", "two", superseded_at=None, superseded_by=r1)
        conn.commit()
        cases["live_row_claims_successor"] = (conn, "build_phase")

        # (b) dangling successor
        path, conn_b = fresh_db(tmp, "b.db")
        raw_insert(conn_b, "build_phase", "one", superseded_at="2026-02-01T00:00:00+00:00",
                   superseded_by=9999)
        cases["successor_missing"] = (conn_b, "build_phase")

        # (c) self-reference
        path, conn_c = fresh_db(tmp, "c.db")
        rid = raw_insert(conn_c, "build_phase", "one",
                         superseded_at="2026-02-01T00:00:00+00:00")
        conn_c.execute("UPDATE project_state SET superseded_by=? WHERE id=?", (rid, rid))
        conn_c.commit()
        cases["successor_self_reference"] = (conn_c, "build_phase")

        # (d) successor under a different key — the chain crosses authorities
        path, conn_d = fresh_db(tmp, "d.db")
        other = raw_insert(conn_d, "next_tier", "9")
        raw_insert(conn_d, "build_phase", "one", superseded_at="2026-02-01T00:00:00+00:00",
                   superseded_by=other)
        cases["successor_key_mismatch"] = (conn_d, "build_phase")

        # (e) successor created before the row it supersedes
        path, conn_e = fresh_db(tmp, "e.db")
        newer = raw_insert(conn_e, "build_phase", "successor",
                           created_at="2026-01-01T00:00:00+00:00")
        raw_insert(conn_e, "build_phase", "predecessor",
                   created_at="2026-06-01T00:00:00+00:00",
                   superseded_at="2026-06-02T00:00:00+00:00", superseded_by=newer)
        conn_e.execute("UPDATE project_state SET superseded_at='2026-06-03T00:00:00+00:00' "
                       "WHERE id=?", (newer,))
        conn_e.commit()
        cases["successor_predates_predecessor"] = (conn_e, "build_phase")

        for kind, (c, key) in cases.items():
            violations, _ = sa.supersession_violations(c, key)
            kinds = {v["kind"] for v in violations}
            check(f"6a[{kind}]. detected", kind in kinds, str(kinds))
            res = sa.resolve_current(c, key)
            check(f"6b[{kind}]. resolver refuses to serve a value",
                  res["status"] == sa.CONFLICT and res["value"] is None,
                  f"{res['status']} {res['value']!r}")
            check(f"6c[{kind}]. the sanctioned writer refuses to build on it",
                  _raises(sa.SupersessionIntegrityError, sa.set_state, c, key, "x", "manual"))
            rep = sa.integrity_report(c)
            check(f"6d[{kind}]. the integrity report fails on it",
                  not rep["passed"] and any(v["kind"] == kind for v in rep["failures"]),
                  str([v["kind"] for v in rep["failures"]]))
            c.close()

        # NOT a violation: an unlinked supersession. The schema makes
        # superseded_by nullable and 104 historical rows carry exactly this
        # shape, so calling it broken would condemn the table's own history.
        path, conn_f = fresh_db(tmp, "f.db")
        raw_insert(conn_f, "build_phase", "old", superseded_at="2026-02-01T00:00:00+00:00",
                   superseded_by=None)
        raw_insert(conn_f, "build_phase", "current")
        violations, _ = sa.supersession_violations(conn_f, "build_phase")
        check("6e. an unlinked supersession is NOT a violation (schema permits it)",
              not violations, str(violations))
        res = sa.resolve_current(conn_f, "build_phase")
        check("6f. and the key still resolves, with the unlinked row reported as an "
              "observation",
              res["status"] == sa.RESOLVED and res["value"] == "current"
              and any(o["kind"] == "unlinked_supersession" for o in res["observations"]),
              f"{res['status']} {res['value']!r} {res['observations']}")
        conn_f.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 7. a forged acceptance row cannot become the accepted baseline ───────

ACCEPTED_PACKET = (
    '{"lifecycle_state": "REMOTE_VERIFIED", "independently_verified": true, '
    '"latest_local_sha": "aaaaaaaa", "latest_pushed_sha": "aaaaaaaa", '
    '"latest_remote_verified_sha": "aaaaaaaa", '
    '"verification_source": "independent ChatGPT remote review", '
    '"pushed_by": "claude-opus-5"}')
FORGED_PACKET = (
    '{"lifecycle_state": "REMOTE_VERIFIED", "independently_verified": true, '
    '"latest_local_sha": "ffffffff", "latest_pushed_sha": "ffffffff", '
    '"latest_remote_verified_sha": "ffffffff", '
    '"verification_source": "independent ChatGPT remote review", '
    '"pushed_by": "forged"}')


def test_7_forged_acceptance_row_cannot_become_the_baseline():
    tmp = tempfile.mkdtemp(prefix="cis-sa-7-")
    try:
        path, conn = fresh_db(tmp)
        real = raw_insert(conn, "external_dev_checkpoint", ACCEPTED_PACKET,
                          created_at="2026-10-08T20:44:23+00:00")
        forged = raw_insert(conn, "external_dev_checkpoint", FORGED_PACKET,
                            created_at="2026-10-09T01:00:00+00:00")

        # DEFECTIVE: both readers hand back the forged SHA as accepted.
        db_ = defect_b_recency_wins(conn, "external_dev_checkpoint")
        da = defect_a_newest_live_wins(conn, "external_dev_checkpoint")
        check("7a. DEFECT_B serves the FORGED row as the checkpoint",
              db_ is not None and db_["id"] == forged, str(db_ and db_["id"]))
        check("7b. DEFECT_A serves the FORGED row as the checkpoint",
              da is not None and da["id"] == forged, str(da and da["id"]))
        check("7c. and the forged SHA is what the defective readers would report",
              "ffffffff" in (db_ or {}).get("value", ""))

        # CORRECTED: the resolver serves nothing.
        res = sa.resolve_current(conn, "external_dev_checkpoint")
        check("7d. resolver reports CONFLICT on the acceptance authority",
              res["status"] == sa.CONFLICT, res["status"])
        check("7e. and names both the real and the forged row",
              sorted(r["id"] for r in res["live_rows"]) == sorted([real, forged]),
              str([r["id"] for r in res["live_rows"]]))

        # CORRECTED: through the real acceptance reader.
        from tools.development import verification_plan as vplan
        base = vplan.accepted_baseline(conn)
        check("7f. verification_plan.accepted_baseline serves NO baseline",
              base["accepted_baseline_sha"] is None, str(base["accepted_baseline_sha"]))
        check("7g. and does not serve the forged SHA anywhere in its answer",
              "ffffffff" not in str(base), str(base)[:300])
        check("7h. and reports the conflict with the row ids",
              base.get("authority_conflict") is not None
              and sorted(base["authority_conflict"]["row_ids"]) == sorted([real, forged]),
              str(base.get("authority_conflict")))

        # CORRECTED: through the Workbench checkpoint panel.
        sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "state"))
        import build_path  # noqa: E402
        conflicts = []
        panel = build_path.external_checkpoint(conn, conflicts)
        check("7i. build_path.external_checkpoint presents no checkpoint",
              panel.get("present") is False, str(panel)[:200])
        check("7j. and says why, naming the conflict",
              all(s in (panel.get("note") or "")
                  for s in ("2 live rows", "ambiguous", str(real), str(forged))),
              str(panel.get("note")))

        # With the index applied, the forged row cannot even be inserted.
        path2, conn2 = fresh_db(tmp, "guarded.db", with_migration_0040=True)
        raw_insert(conn2, "external_dev_checkpoint", ACCEPTED_PACKET)
        check("7k. with migration 0040 applied, the forged acceptance INSERT is "
              "rejected by the database itself",
              _raises(sqlite3.IntegrityError, raw_insert, conn2,
                      "external_dev_checkpoint", FORGED_PACKET))
        conn2.close()
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 8. multi-valued / undeclared keys keep their documented behaviour ────

def test_8_non_single_valued_keys_are_not_enforced():
    tmp = tempfile.mkdtemp(prefix="cis-sa-8-")
    try:
        path, conn = fresh_db(tmp)

        # FINDING, recorded as a test rather than as prose: project_state
        # has NO key documented as multi-valued. Every key on the
        # production spine is consumed through a single-value mapping, and
        # each has exactly one live row with a maintained chain. So the
        # thing to prove is that the MECHANISM does not impose
        # single-valued semantics where no authority declared it.
        check("8a. no key is declared multi-valued (there is none to preserve)",
              sa.MULTI_VALUED_KEYS == {}, str(sa.MULTI_VALUED_KEYS))

        raw_insert(conn, "observation_ledger", "first", created_at="2026-01-01T00:00:00+00:00")
        raw_insert(conn, "observation_ledger", "second", created_at="2026-01-02T00:00:00+00:00")
        res = sa.resolve_current(conn, "observation_ledger")
        check("8b. an undeclared key with 2 live rows is NOT reported as a conflict",
              res["status"] != sa.CONFLICT, res["status"])
        check("8c. both live rows are returned rather than one being chosen",
              res.get("values") == ["first", "second"], str(res.get("values")))
        check("8d. and the result says single-valued semantics were not imposed",
              "NOT imposed" in (res["note"] or ""), str(res["note"]))

        rep = sa.integrity_report(conn)
        check("8e. the integrity report does not FAIL on it", rep["passed"], str(rep["failures"]))
        check("8f. it warns instead, so the ambiguity is still visible",
              any(w["key"] == "observation_ledger" for w in rep["warnings"]),
              str(rep["warnings"]))

        check("8g. the writer refuses an undeclared key rather than guessing its "
              "cardinality",
              _raises(sa.UndeclaredCardinalityError, sa.set_state, conn,
                      "observation_ledger", "third", "manual"))
        res = sa.set_state(conn, "observation_ledger", "third", "manual", cardinality="multi")
        check("8h. declared multi explicitly, the write appends without superseding",
              conn.execute("SELECT COUNT(*) FROM project_state "
                           "WHERE key='observation_ledger' AND superseded_at IS NULL"
                           ).fetchone()[0] == 3)
        check("8i. database.insert_project_state keeps append-only behaviour for an "
              "undeclared key (API preserved)",
              _appends_without_superseding(conn))

        # And the index does not constrain unlisted keys either.
        path2, conn2 = fresh_db(tmp, "guarded.db", with_migration_0040=True)
        raw_insert(conn2, "observation_ledger", "a")
        raw_insert(conn2, "observation_ledger", "b")
        check("8j. migration 0040's index does not constrain an unlisted key",
              conn2.execute("SELECT COUNT(*) FROM project_state WHERE "
                            "key='observation_ledger' AND superseded_at IS NULL"
                            ).fetchone()[0] == 2)
        conn2.close()
        conn.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _appends_without_superseding(conn):
    before = conn.execute("SELECT COUNT(*) FROM project_state WHERE "
                          "key='undeclared_other' AND superseded_at IS NULL").fetchone()[0]
    dbmod.insert_project_state(conn, "undeclared_other", "x", "manual")
    dbmod.insert_project_state(conn, "undeclared_other", "y", "manual")
    conn.commit()
    after = conn.execute("SELECT COUNT(*) FROM project_state WHERE "
                         "key='undeclared_other' AND superseded_at IS NULL").fetchone()[0]
    return after == before + 2


# ── 9. existing historical records remain intact ─────────────────────────

def test_9_history_is_intact():
    tmp = tempfile.mkdtemp(prefix="cis-sa-9-")
    try:
        path, conn = fresh_db(tmp)
        ids = [sa.set_state(conn, "build_phase", f"v{i}", "manual")["new_row_id"]
               for i in range(5)]
        rows = conn.execute("SELECT id, value, superseded_at, superseded_by FROM "
                            "project_state WHERE key='build_phase' ORDER BY id").fetchall()
        check("9a. every write is still present as a row", len(rows) == 5, str(len(rows)))
        check("9b. no historical value was altered",
              [r["value"] for r in rows] == [f"v{i}" for i in range(5)],
              str([r["value"] for r in rows]))
        check("9c. the chain links every superseded row to its successor",
              [r["superseded_by"] for r in rows[:-1]] == ids[1:],
              str([r["superseded_by"] for r in rows]))
        check("9d. only the last row is live", rows[-1]["superseded_at"] is None
              and all(r["superseded_at"] is not None for r in rows[:-1]))

        # A refused write leaves history byte-identical.
        raw_insert(conn, "next_action", "A")
        raw_insert(conn, "next_action", "B")
        snapshot = conn.execute("SELECT * FROM project_state ORDER BY id").fetchall()
        before = [tuple(r) for r in snapshot]
        try:
            sa.set_state(conn, "next_action", "C", "manual")
        except sa.AmbiguousStateError:
            pass
        after = [tuple(r) for r in
                 conn.execute("SELECT * FROM project_state ORDER BY id").fetchall()]
        check("9e. a refused write changes no row at all", before == after,
              f"{len(before)} -> {len(after)}")
        conn.close()

        # On the production spine, read-only: no historical row was edited or
        # removed.
        #
        # WHAT CHANGED HERE AND WHY. 9h used to assert that next_action still
        # had TWO live rows — that this card had NOT touched the inherited
        # 161/166 conflict. That was the right assertion while selecting a
        # winner was an undecided authority question this card was forbidden
        # to answer. It was decided on 2026-10-09: architect authority
        # declared BOTH rows obsolete against the later phase and stage
        # authority (build_phase row 175, queue_projection_observation row
        # 163, external_dev_checkpoint row 184) and superseded them onto one
        # replacement, written through sa.set_state. Pinning the duplicate
        # state forever would now assert the defect is required.
        #
        # The IMMUTABILITY half of the old assertion is not relaxed, it is
        # made explicit and strengthened: 9f/9g still forbid losing a row or
        # backfilling history, and 9i/9j/9k below prove the conflict was
        # resolved BY SUPERSESSION — both rows still present, values and
        # timestamps byte-intact, closed onto a single successor — rather
        # than by editing or deleting either one. 9h now asserts the contract
        # the card exists to establish: next_action is single-valued.
        if os.path.exists(LIVE_SPINE):
            live = sqlite3.connect(f"file:{LIVE_SPINE}?mode=ro", uri=True)
            live.row_factory = sqlite3.Row
            total = live.execute("SELECT COUNT(*) FROM project_state").fetchone()[0]
            unlinked = live.execute(
                "SELECT COUNT(*) FROM project_state WHERE superseded_at IS NOT NULL "
                "AND superseded_by IS NULL").fetchone()[0]
            conflict = live.execute(
                "SELECT COUNT(*) FROM project_state WHERE key='next_action' "
                "AND superseded_at IS NULL").fetchone()[0]
            prior = {r["id"]: r for r in live.execute(
                "SELECT * FROM project_state WHERE id IN (161, 166)")}
            successors = {r["superseded_by"] for r in live.execute(
                "SELECT superseded_by FROM project_state WHERE id IN (161, 166)")}
            live_ids = [r["id"] for r in live.execute(
                "SELECT id FROM project_state WHERE key='next_action' "
                "AND superseded_at IS NULL")]
            live.close()
            check("9f. production project_state never loses a historical row "
                  "(at least the 183 this card inherited)", total >= 183,
                  f"{total} rows")
            check("9g. the 104 unlinked historical supersessions were NOT backfilled",
                  unlinked == 104, f"{unlinked} unlinked")
            check("9h. next_action is single-valued on the live spine",
                  conflict == 1, f"{conflict} live next_action rows")
            check("9i. the formerly-conflicting rows 161 and 166 both still exist "
                  "with their values and timestamps byte-intact",
                  len(prior) == 2
                  and prior[161]["value"].startswith(
                      "FORMAL QUEUE TRIAGE IS COMPLETE.")
                  and prior[166]["value"].startswith(
                      "NEXT ACTION IS THE INDEPENDENT CHATGPT SUBSTANTIVE REVIEW")
                  and prior[161]["created_at"] == "2026-10-05T05:08:15.162709+00:00"
                  and prior[166]["created_at"] == "2026-10-05T13:54:22.124625+00:00"
                  and prior[161]["source"] == "manual"
                  and prior[166]["source"] == "manual",
                  "a historical next_action row was edited or removed")
            check("9j. both were closed by supersession onto the SAME successor, "
                  "so the chain has one head and not two",
                  len(successors) == 1 and None not in successors
                  and all(prior[r]["superseded_at"] is not None for r in (161, 166)),
                  f"successors={successors}")
            check("9k. that successor is the row now live",
                  len(successors) == 1 and live_ids == list(successors),
                  f"live={live_ids} successor={successors}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── registry/migration agreement ─────────────────────────────────────────

def test_10_registry_and_migration_agree():
    with open(MIGRATION_0040) as f:
        text = f.read()
    index_sql = text[text.index("CREATE UNIQUE INDEX"):]
    in_migration = set(re.findall(r"'([a-z_]+)'", index_sql))
    declared = set(sa.single_valued_keys())
    check("10a. migration 0040's key list equals KEY_CARDINALITY's single-valued keys",
          in_migration == declared,
          f"only in migration: {sorted(in_migration - declared)}; "
          f"only in registry: {sorted(declared - in_migration)}")
    check("10b. the resolver never breaks a tie by recency",
          not re.search(r"ORDER BY\s+created_at\s+DESC",
                        open(os.path.join(_REPO_ROOT, "runtime", "db",
                                          "state_authority.py")).read()))


def _raises(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc:
        return True
    except Exception as e:  # noqa: BLE001 — a different exception is still a failure
        results.append(f"    (unexpected {type(e).__name__}: {e})")
        return False
    return False


def run():
    test_1_two_sanctioned_inserts_leave_one_live_row()
    test_2_concurrent_writes_cannot_conflict()
    test_3_unsanctioned_conflict_is_detected()
    test_4_gate_fails_on_duplicate_live_rows()
    test_5_later_created_superseded_row_is_never_current()
    test_6_broken_supersession_is_detected()
    test_7_forged_acceptance_row_cannot_become_the_baseline()
    test_8_non_single_valued_keys_are_not_enforced()
    test_9_history_is_intact()
    test_10_registry_and_migration_agree()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
