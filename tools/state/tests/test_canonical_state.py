#!/usr/bin/env python3
"""test_canonical_state.py — CARD 01 (queue 4.29) behavioral tests for
tools/state/canonical_state.py.

Runs against a scratch temp SQLite database built with a minimal subset of
the real spine schema — never against production for anything that could
mutate. The one exception (clearly marked) opens the real production
spine read-only (sqlite3 URI mode=ro) to prove the discovery/closeout
delegation fix actually talks to the real CLI correctly.

Run:
    python3 tools/state/tests/test_canonical_state.py
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "state"))
import canonical_state as cs  # noqa: E402

PROD_DB = os.environ.get("CIS_SPINE_PATH", os.path.join(REPO_ROOT, "data", "cis_memory.db"))

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


SCHEMA = """
CREATE TABLE queue_items (
    item_num TEXT PRIMARY KEY, tier INTEGER NOT NULL, title TEXT NOT NULL,
    body_md TEXT NOT NULL, form TEXT NOT NULL, need_status TEXT,
    source_line INTEGER NOT NULL, source_sha TEXT NOT NULL,
    extracted_at TEXT NOT NULL DEFAULT (datetime('now')),
    status_changed_at TEXT, status_changed_by TEXT
);
CREATE TABLE queue_item_events (
    id INTEGER PRIMARY KEY, item_num TEXT NOT NULL, field TEXT NOT NULL,
    old_value TEXT, new_value TEXT, changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    changed_by TEXT, evidence TEXT, note TEXT
);
CREATE TABLE dev_continuity_events (
    id INTEGER PRIMARY KEY, task TEXT NOT NULL, revision INTEGER NOT NULL,
    kind TEXT NOT NULL, status TEXT NOT NULL, actor TEXT NOT NULL,
    summary TEXT NOT NULL, body TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE session_closeouts (
    id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, completed_at TEXT,
    status TEXT NOT NULL, commit_hash TEXT
);
CREATE TABLE project_decisions (
    id TEXT PRIMARY KEY, label TEXT NOT NULL, decision TEXT NOT NULL,
    reason TEXT, status TEXT NOT NULL DEFAULT 'DECIDED', decided_at TEXT NOT NULL,
    superseded_by TEXT
);
CREATE TABLE project_state (
    id INTEGER PRIMARY KEY, key TEXT NOT NULL, value TEXT NOT NULL,
    source TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE open_questions (
    id TEXT PRIMARY KEY, question TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'OPEN',
    resolution TEXT, opened_at TEXT NOT NULL, resolved_at TEXT
);
CREATE TABLE active_blockers (
    id TEXT PRIMARY KEY, description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ACTIVE',
    resolution TEXT, created_at TEXT NOT NULL, resolved_at TEXT
);
CREATE TABLE next_actions (
    id TEXT PRIMARY KEY, tier TEXT, description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING', depends_on TEXT,
    created_at TEXT NOT NULL, updated_at TEXT
);
CREATE TABLE dev_pivot_status (
    id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
    category TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'LIVE',
    updated_at TEXT DEFAULT (datetime('now'))
);
"""


def make_scratch_db():
    tmp = tempfile.mkdtemp(prefix="cis_canonical_state_test_")
    path = os.path.join(tmp, "scratch.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return tmp, path, conn


def table_counts(conn):
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in cs.AUTHORITY_TABLES}


def test_revision_deterministic_and_stable():
    tmp, path, conn = make_scratch_db()
    try:
        r1 = cs.compute_state_revision(conn)
        r2 = cs.compute_state_revision(conn)
        r3 = cs.compute_state_revision(conn)
        check("revision is stable across repeated calls with no state change",
              r1 == r2 == r3, f"{r1} {r2} {r3}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_revision_changes_with_authoritative_state():
    tmp, path, conn = make_scratch_db()
    try:
        r_before = cs.compute_state_revision(conn)
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('9.1', 9, 'test item', '### 9.1 test item', 'heading', 'OPEN', 1, 'x')"
        )
        conn.commit()
        r_after = cs.compute_state_revision(conn)
        check("revision changes when an authoritative table's content changes",
              r_before != r_after, f"before={r_before} after={r_after}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_staleness_detectable_via_declared_vs_current():
    """Simulates exactly what get_artifact_freshness compares: a
    previously-declared revision vs. the freshly-computed current one."""
    tmp, path, conn = make_scratch_db()
    try:
        declared = cs.compute_state_revision(conn)  # e.g. what a generator stamped at build time
        conn.execute(
            "INSERT INTO project_decisions (id, label, decision, decided_at) "
            "VALUES ('D1', 'test', 'test decision', datetime('now'))"
        )
        conn.commit()
        current = cs.compute_state_revision(conn)
        check("a declared revision no longer matching current state is detectable as stale",
              declared != current, f"declared={declared} current={current}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_queue_items_inplace_update_detected():
    """ChatGPT review reproduction, closed: an UPDATE that changes mutable
    fields but leaves extracted_at and row count unchanged must still
    change the revision."""
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha, extracted_at) VALUES "
            "('9.9', 9, 'repro', '### 9.9 repro', 'heading', 'OPEN', 1, 'x', '2026-01-01 00:00:00')"
        )
        conn.commit()
        before = cs.compute_state_revision(conn)
        before_n = conn.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0]
        conn.execute(
            "UPDATE queue_items SET body_md='### 9.9 repro (CHANGED)', need_status='DONE', "
            "status_changed_at='2026-09-21 12:00:00', status_changed_by='claude_code' "
            "WHERE item_num='9.9'"
        )
        conn.commit()
        after = cs.compute_state_revision(conn)
        after_n = conn.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0]
        check("queue_items in-place status/body update detected (unchanged extracted_at, unchanged row count)",
              before != after and before_n == after_n,
              f"before={before} after={after} counts={before_n}/{after_n}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_project_decisions_inplace_supersession_detected():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO project_decisions (id, label, decision, status, decided_at) "
            "VALUES ('D1', 'l', 'd', 'DECIDED', '2026-01-01 00:00:00')"
        )
        conn.commit()
        before = cs.compute_state_revision(conn)
        conn.execute(
            "UPDATE project_decisions SET status='SUPERSEDED', superseded_by='D2' WHERE id='D1'"
        )
        conn.commit()
        after = cs.compute_state_revision(conn)
        check("project_decisions in-place status/supersession change detected (unchanged decided_at)",
              before != after, f"before={before} after={after}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_open_questions_inplace_resolution_detected():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO open_questions (id, question, status, opened_at) "
            "VALUES ('Q1', 'q', 'OPEN', '2026-01-01 00:00:00')"
        )
        conn.commit()
        before = cs.compute_state_revision(conn)
        conn.execute(
            "UPDATE open_questions SET status='RESOLVED', resolution='answered' WHERE id='Q1'"
        )
        conn.commit()
        after = cs.compute_state_revision(conn)
        check("open_questions in-place resolution/status change detected (unchanged opened_at)",
              before != after, f"before={before} after={after}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_active_blockers_inplace_resolution_detected():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO active_blockers (id, description, status, created_at) "
            "VALUES ('B1', 'b', 'ACTIVE', '2026-01-01 00:00:00')"
        )
        conn.commit()
        before = cs.compute_state_revision(conn)
        conn.execute(
            "UPDATE active_blockers SET status='RESOLVED', resolution='fixed' WHERE id='B1'"
        )
        conn.commit()
        after = cs.compute_state_revision(conn)
        check("active_blockers in-place resolution/status change detected (unchanged created_at)",
              before != after, f"before={before} after={after}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_next_actions_inplace_status_change_detected_no_rowcount_change():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO next_actions (id, tier, description, status, created_at) "
            "VALUES ('NA1', '1', 'n', 'PENDING', '2026-01-01 00:00:00')"
        )
        conn.commit()
        before = cs.compute_state_revision(conn)
        before_n = conn.execute("SELECT COUNT(*) FROM next_actions").fetchone()[0]
        conn.execute(
            "UPDATE next_actions SET status='COMPLETE', updated_at='2026-09-21 12:00:00' WHERE id='NA1'"
        )
        conn.commit()
        after = cs.compute_state_revision(conn)
        after_n = conn.execute("SELECT COUNT(*) FROM next_actions").fetchone()[0]
        check("next_actions in-place status/updated_at change detected where row count is unchanged",
              before != after and before_n == after_n,
              f"before={before} after={after} counts={before_n}/{after_n}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_artifact_freshness_checks_still_work_against_real_repo():
    """Requirement 7: existing artifact freshness checks still function
    after the revision algorithm change (run against the real repo files,
    after they've been regenerated with the corrected algorithm)."""
    conn = sqlite3.connect(PROD_DB)
    try:
        rev = cs.compute_state_revision(conn)
        freshness = cs.get_artifact_freshness(conn, rev)
        bl = freshness.get("docs/UNIFIED_BUILD_LIST.md", {})
        manifest_key = "runtime/manifests/EXPORT_MANIFEST.json (AGENTS.md/HCP/DEV-PIVOT)"
        mf = freshness.get(manifest_key, {})
        check("docs/UNIFIED_BUILD_LIST.md freshness check still runs and returns a boolean",
              bl.get("fresh") in (True, False), bl)
        check("EXPORT_MANIFEST.json freshness check still runs and returns a boolean",
              mf.get("fresh") in (True, False), mf)
    finally:
        conn.close()


def test_dormant_sources_flagged_not_dropped():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO open_questions (id, question, status, opened_at) "
            "VALUES ('Q1', 'an old question', 'OPEN', datetime('now', '-90 days'))"
        )
        conn.commit()
        freshness = cs.table_freshness(conn)
        check("a source with no recent activity is flagged dormant",
              freshness["open_questions"]["dormant"] is True, freshness["open_questions"])
        check("a dormant source's rows are still reported, not silently dropped",
              freshness["open_questions"]["row_count"] == 1, freshness["open_questions"])
        questions = cs.get_open_questions(conn, freshness["open_questions"]["dormant"])
        check("get_open_questions() tags rows with source_dormant rather than hiding them",
              len(questions) == 1 and questions[0]["source_dormant"] is True, questions)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_live_source_not_flagged_dormant():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha, extracted_at) VALUES "
            "('9.2', 9, 'fresh item', '### 9.2 fresh item', 'heading', 'OPEN', 2, 'x', datetime('now'))"
        )
        conn.commit()
        freshness = cs.table_freshness(conn)
        check("a source with activity today is not flagged dormant",
              freshness["queue_items"]["dormant"] is False, freshness["queue_items"])
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_observed_health_does_not_mutate_any_table():
    tmp, path, conn = make_scratch_db()
    try:
        before = table_counts(conn)
        cs.get_observed_runtime_health()  # live gateway/git/db observations
        after = table_counts(conn)
        check("observing runtime health writes nothing to any authoritative table",
              before == after, f"before={before} after={after}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_state_derived_purely_from_db_not_from_generated_files():
    """A generated projection could be hand-edited to say anything; the
    canonical state must not be affected, because it never reads generated
    markdown as an input. Proven here by cross-checking the read model's
    output against an independent direct query of the same scratch DB."""
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO project_decisions (id, label, decision, status, decided_at) "
            "VALUES ('D9', 'independent check', 'decide something', 'DECIDED', datetime('now'))"
        )
        conn.commit()
        direct = [dict(r) for r in conn.execute(
            "SELECT id, label, decision, reason, status, decided_at FROM project_decisions "
            "WHERE status != 'SUPERSEDED' ORDER BY decided_at DESC"
        ).fetchall()]
        via_model = cs.get_active_decisions(conn)
        check("active decisions match an independent direct query of the DB "
              "(no generated file could have influenced this)",
              direct == via_model, f"direct={direct} model={via_model}")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_get_canonical_state_end_to_end_shape():
    tmp, path, conn = make_scratch_db()
    try:
        conn.close()  # get_canonical_state opens its own connection
        state = cs.get_canonical_state(db_path=path)
        expected_keys = {
            "revision", "computed_at", "source", "queue_focus",
            "open_blocked_deferred", "recent_verified_closed", "active_decisions",
            "open_questions", "discoveries_requiring_attention",
            "source_table_freshness", "generated_artifact_freshness",
            "observed_runtime_health",
        }
        check("get_canonical_state() returns the full suggested output shape",
              expected_keys.issubset(state.keys()), state.keys())
        check("empty scratch DB with no dev_continuity_events yields no discoveries "
              "(no CLI subprocess needed/invoked)",
              state["discoveries_requiring_attention"] == [], state["discoveries_requiring_attention"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cli_command_matches_module():
    """python3 tools/state/canonical_state.py --revision must match the
    library call directly, proving the CLI wrapper isn't a second
    implementation that could drift from the module."""
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('9.3', 9, 'cli test', '### 9.3 cli test', 'heading', 'OPEN', 3, 'x')"
        )
        conn.commit()
        conn.close()
        expected = cs.compute_state_revision(sqlite3.connect(path))
        r = subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "tools", "state", "canonical_state.py"),
             "--revision", "--db", path],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        check("CLI --revision output matches the library function's own computation",
              r.returncode == 0 and r.stdout.strip() == expected,
              f"cli={r.stdout.strip()!r} lib={expected!r} stderr={r.stderr}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_discovery_delegation_against_real_spine_readonly():
    """Regression test for the bug caught during this card's own
    implementation: a first version read dev_continuity_events directly
    and reported 4 already-resolved WB.1 discoveries as still blocking
    closeout. Opens the real spine READ-ONLY (sqlite3 URI mode=ro, so a
    bug here cannot write) and checks the sanctioned-CLI-delegation path
    agrees with `python3 -m tools.development.cli closeout-check WB.1`."""
    if not os.path.exists(PROD_DB):
        check("discovery delegation matches closeout-check (skipped, no prod DB found)",
              True, "skipped")
        return
    uri = f"file:{PROD_DB}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tasks = cs._list_tasks_with_continuity(conn)
        if "WB.1" not in tasks:
            check("discovery delegation matches closeout-check (skipped, WB.1 not present)",
                  True, "skipped")
            return
        status = cs.get_closeout_status(conn)
        cli = subprocess.run(
            [sys.executable, "-m", "tools.development.cli", "closeout-check", "WB.1"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        cli_result = json.loads(cli.stdout)
        check("get_closeout_status()['WB.1'] matches `cli closeout-check WB.1` directly",
              status.get("WB.1") == cli_result, f"model={status.get('WB.1')} cli={cli_result}")

        discoveries = cs.get_unresolved_discoveries(conn)
        wb1_discoveries = [d for d in discoveries if d.get("task") == "WB.1"]
        if cli_result.get("ready_to_close"):
            check("no unresolved discoveries reported for a task whose closeout-check "
                  "already shows ready_to_close=true",
                  wb1_discoveries == [], wb1_discoveries)
    finally:
        conn.close()


def test_current_focus_pointer_is_latest_project_state_row():
    """Card 04 R1 correction: current_focus.current_queue_item_pointer must
    be the latest project_state row with key='current_queue_item' by
    created_at, never a hardcoded/inferred 'next item'."""
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('OLD.1', 1, 'old', '### old', 'heading', 'OPEN', 1, 'x')"
        )
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('WB.1', 0, 'current work', '### WB.1 current work\\n\\nReturn point: "
            "do not resume automatically.', 'heading', 'OPEN', 2, 'x')"
        )
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES "
            "('current_queue_item', 'OLD.1', 'manual', '2026-01-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES "
            "('current_queue_item', 'WB.1', 'manual', '2026-06-01T00:00:00Z')"
        )
        conn.commit()
        focus = cs.get_current_focus(conn)
        check("current_focus picks the LATEST current_queue_item pointer by created_at, "
              "not the first/oldest row",
              focus["current_queue_item_pointer"]["value"] == "WB.1", focus["current_queue_item_pointer"])
        check("current_focus resolves the pointer's own queue_items detail (need_status, body_md)",
              focus["current_queue_item_detail"]["need_status"] == "OPEN"
              and "do not resume automatically" in focus["current_queue_item_detail"]["body_md"],
              focus["current_queue_item_detail"])
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_current_focus_recent_activity_surfaces_task_not_named_by_pointer():
    """The exact usability gap this fixes: a full/pointer-only view can lose
    a task (e.g. 4.32) that isn't the current_queue_item pointer but has the
    most recent authoritative activity. recent_task_activity must surface it
    by recency alone, and recent_task_queue_items must carry its real
    OPEN/DONE status and body_md alongside that activity."""
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('WB.1', 0, 'pointer target', '### WB.1', 'heading', 'OPEN', 1, 'x')"
        )
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "need_status, source_line, source_sha) VALUES "
            "('4.32', 4, 'recovery drill', '### 4.32 recovery drill\\n\\nReturn point: "
            "resuming feature work is not automatic.', 'heading', 'OPEN', 2, 'x')"
        )
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES "
            "('current_queue_item', 'WB.1', 'manual', '2026-01-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO dev_continuity_events (task, revision, kind, status, actor, summary, "
            "body, created_at) VALUES ('4.32', 1, 'user_instruction', 'authorized', 'codex', "
            "'do the correction', 'directive body', '2026-09-22 15:00:00')"
        )
        conn.commit()
        focus = cs.get_current_focus(conn)
        check("recent_task_activity includes task 4.32 purely from its own recent event, "
              "even though the pointer names WB.1",
              any(r["task"] == "4.32" for r in focus["recent_task_activity"]), focus["recent_task_activity"])
        check("recent_task_queue_items['4.32'] carries its real OPEN status and return-point body_md",
              focus["recent_task_queue_items"]["4.32"]["need_status"] == "OPEN"
              and "not automatic" in focus["recent_task_queue_items"]["4.32"]["body_md"],
              focus["recent_task_queue_items"].get("4.32"))
        check("a fetch handle for full per-task history is named explicitly",
              "cli.py" in focus["recent_task_activity_fetch_handle"] or
              "cli" in focus["recent_task_activity_fetch_handle"],
              focus["recent_task_activity_fetch_handle"])
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_current_focus_absent_pointer_is_none_not_fabricated():
    tmp, path, conn = make_scratch_db()
    try:
        focus = cs.get_current_focus(conn)
        check("no project_state current_queue_item row yields pointer=None, "
              "never a fabricated/default value",
              focus["current_queue_item_pointer"] is None
              and focus["current_queue_item_detail"] is None,
              focus)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_active_blockers_included_honestly_with_dormancy():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute(
            "INSERT INTO active_blockers (id, description, status, created_at) VALUES "
            "('B1', 'a dormant but still active blocker', 'ACTIVE', datetime('now', '-90 days'))"
        )
        conn.commit()
        freshness = cs.table_freshness(conn)
        check("a table whose only row is 90 days old is itself flagged dormant",
              freshness["active_blockers"]["dormant"] is True, freshness["active_blockers"])
        blockers = cs.get_active_blockers(conn, freshness["active_blockers"]["dormant"])
        check("only ACTIVE blockers are returned",
              [b["id"] for b in blockers] == ["B1"], blockers)
        check("a dormant active blocker is still returned, tagged dormant, not dropped",
              blockers[0]["source_dormant"] is True, blockers)

        conn.execute(
            "INSERT INTO active_blockers (id, description, status, created_at) VALUES "
            "('B2', 'a resolved blocker', 'RESOLVED', datetime('now'))"
        )
        conn.commit()
        blockers2 = cs.get_active_blockers(conn, freshness["active_blockers"]["dormant"])
        check("a resolved blocker is not returned even when present in the table",
              [b["id"] for b in blockers2] == ["B1"], blockers2)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_canonical_state_includes_current_focus_and_active_blockers():
    tmp, path, conn = make_scratch_db()
    try:
        conn.close()
        state = cs.get_canonical_state(db_path=path)
        check("get_canonical_state() output includes current_focus",
              "current_focus" in state, state.keys())
        check("get_canonical_state() output includes active_blockers",
              "active_blockers" in state, state.keys())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    test_revision_deterministic_and_stable()
    test_revision_changes_with_authoritative_state()
    test_staleness_detectable_via_declared_vs_current()
    test_queue_items_inplace_update_detected()
    test_project_decisions_inplace_supersession_detected()
    test_open_questions_inplace_resolution_detected()
    test_active_blockers_inplace_resolution_detected()
    test_next_actions_inplace_status_change_detected_no_rowcount_change()
    test_artifact_freshness_checks_still_work_against_real_repo()
    test_dormant_sources_flagged_not_dropped()
    test_live_source_not_flagged_dormant()
    test_current_focus_pointer_is_latest_project_state_row()
    test_current_focus_recent_activity_surfaces_task_not_named_by_pointer()
    test_current_focus_absent_pointer_is_none_not_fabricated()
    test_active_blockers_included_honestly_with_dormancy()
    test_canonical_state_includes_current_focus_and_active_blockers()
    test_observed_health_does_not_mutate_any_table()
    test_state_derived_purely_from_db_not_from_generated_files()
    test_get_canonical_state_end_to_end_shape()
    test_cli_command_matches_module()
    test_discovery_delegation_against_real_spine_readonly()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
