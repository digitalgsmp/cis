#!/usr/bin/env python3
"""test_development_activity.py — behavioral tests for
tools/state/development_activity.py, the "Development Activity" area of the
Workbench Project Map (the micro trajectory of actual development evidence,
alongside the macro build trajectory tools/state/project_intelligence.py
already composes from build_path.py/destination_architecture.py).

Runs entirely against scratch SQLite databases built from the real migration
files (0037/0038/0039/0041) — never against production for anything whose
presence this module cannot assume. Two shapes are exercised deliberately:

  1. every optional table present — proposal/run links are classified at
     exactly the confidence they are known (authoritative FK, derived literal
     match, or not_yet_linked), and project_id alone never creates a link.
  2. every optional table absent — the module must still return a complete,
     honest, non-raising model.

Run:
    python3 tools/state/tests/test_development_activity.py
"""
import os
import sqlite3
import sys
import tempfile

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "state"))
import development_activity as dev_activity  # noqa: E402

MIGRATIONS_DIR = os.path.join(REPO_ROOT, "runtime", "schema", "migrations")

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def _exec_migration(conn, filename):
    path = os.path.join(MIGRATIONS_DIR, filename)
    with open(path, encoding="utf-8") as f:
        conn.executescript(f.read())


def make_full_db():
    """Every optional table present, built from the real migration files
    plus session_handoffs (matching runtime/schema/migrations/0014's shape,
    the one table here with no additive-migration file of its own)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _exec_migration(conn, "0037_card_runner.sql")
    _exec_migration(conn, "0038_workbench_action_proposals.sql")
    _exec_migration(conn, "0039_dev_continuity.sql")
    _exec_migration(conn, "0041_continuity_transactions.sql")
    conn.execute("""
        CREATE TABLE session_handoffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, title TEXT NOT NULL,
            summary TEXT NOT NULL, decisions TEXT, next_actions TEXT, claude_context TEXT,
            eric_feedback TEXT, gateway_status TEXT, git_head TEXT,
            is_current INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def make_bare_db():
    """No optional table at all — not even sqlite_master entries for them."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.commit()
    return conn


def _insert_run(conn, run_id, request_id, status="completed"):
    conn.execute(
        "INSERT INTO card_runner_runs (id, request_id, card_factory_card_id, card_path, "
        "card_fingerprint, mode, target, limits_json, authorized_by, permission_mode, status) "
        "VALUES (?, ?, 1, 'x', 'x', 'implement', 'claude', '{}', 'eric', 'x', ?)",
        (run_id, request_id, status),
    )


def _insert_proposal(conn, prop_id, project_id, request_id, card_runner_run_id=None):
    conn.execute(
        "INSERT INTO workbench_action_proposals (id, project_id, source_message_ids_json, "
        "user_words, kind, card_runner_run_id, request_id) "
        "VALUES (?, ?, '[]', 'do it', 'implementation', ?, ?)",
        (prop_id, project_id, card_runner_run_id, request_id),
    )


# ── 1. every optional table present ───────────────────────────────────────

def test_full_fixture_links_only_explicit_identifiers():
    conn = make_full_db()
    try:
        conn.execute(
            "INSERT INTO session_handoffs (date, title, summary, is_current) "
            "VALUES ('2026-10-12', 'test handoff', 'did a thing', 1)")
        conn.execute(
            "INSERT INTO dev_continuity_events (task, revision, kind, status, actor, summary) "
            "VALUES ('WB.1', 1, 'unfinished_work', 'open', 'claude_code', 'a finding')")
        _insert_run(conn, 1, "req-explicit")
        _insert_run(conn, 2, "req-literal-match")
        # Same project_id on all three proposals, deliberately, to prove
        # project_id alone is never read as a relationship.
        _insert_proposal(conn, 1, "proj-x", "req-explicit", card_runner_run_id=1)
        _insert_proposal(conn, 2, "proj-x", "req-literal-match", card_runner_run_id=None)
        _insert_proposal(conn, 3, "proj-x", "req-nothing", card_runner_run_id=None)
        conn.execute(
            "INSERT INTO continuity_transactions (transaction_id, kind, criticality, actor, "
            "operation, input_hash, output_hash, evidence_set_hash, contract_version, "
            "envelope_json, verdict, decision, check_json, checked_at) "
            "VALUES ('t1', 'PLAN', 'CANDIDATE', 'claude_code', 'plan_something', "
            "'h1', 'h2', 'h3', 'v1', '{}', 'ALIGNED', 'ALLOW', '{}', datetime('now'))")
        conn.commit()

        model = dev_activity.get_development_activity(conn, repo_root=REPO_ROOT)

        check("1a. the read model names itself",
              model["read_model"] == "cis_development_activity", model["read_model"])

        sh = model["session_handoff"]
        check("1b. the current session handoff is reported authoritative",
              sh["available"] and sh["handoff"]["title"] == "test handoff"
              and sh["confidence_class"] == "authoritative",
              sh)

        ev = model["continuity_events"]
        check("1c. the continuity ledger feed is available and carries the inserted row",
              ev["available"] and ev["total_count"] == 1
              and ev["events"][0]["summary"] == "a finding",
              ev)
        check("1d. no continuity event carries a manufactured link to anything else",
              all("dispatch_run" not in e for e in ev["events"]), ev["events"])

        proposals = {p["id"]: p for p in model["action_proposals"]["proposals"]}
        check("1e. an explicit stored foreign key is reported authoritative",
              proposals[1]["dispatch_run"]["confidence_class"] == "authoritative"
              and proposals[1]["dispatch_run"]["run"]["id"] == 1,
              proposals[1]["dispatch_run"])
        check("1f. a bare request_id match is derived, never upgraded",
              proposals[2]["dispatch_run"]["confidence_class"] == "derived_from_evidence"
              and proposals[2]["dispatch_run"]["run"]["id"] == 2,
              proposals[2]["dispatch_run"])
        check("1g. no identifier at all is reported not_yet_linked, with no run attached",
              proposals[3]["dispatch_run"]["confidence_class"] == "not_yet_linked"
              and proposals[3]["dispatch_run"]["run"] is None,
              proposals[3]["dispatch_run"])
        check("1h. project_id alone never creates a link, though all three share one",
              len({proposals[i]["project_id"] for i in (1, 2, 3)}) == 1
              and proposals[3]["dispatch_run"]["confidence_class"] == "not_yet_linked",
              "shared project_id must not be read as a relationship")
        check("1i. every not_yet_linked/derived link still carries zero or one evidence ref, "
              "never fabricated plural evidence",
              all(len(p["dispatch_run"]["authority_refs"]) <= 1 for p in proposals.values()),
              [p["dispatch_run"]["authority_refs"] for p in proposals.values()])

        ct = model["continuity_transactions"]
        check("1j. the semantic-transaction ledger is read when migration 0041 is applied",
              ct["available"] and ct["total_count"] == 1
              and ct["transactions"][0]["transaction_id"] == "t1",
              ct)

        wt = model["working_tree"]
        check("1k. working-tree facts are observed against the real repo without raising",
              wt["available"] is True and isinstance(wt["dirty_file_count"], int), wt)
    finally:
        conn.close()


# ── 2. every optional table absent ────────────────────────────────────────

def test_bare_fixture_is_honest_and_does_not_raise():
    conn = make_bare_db()
    try:
        model = dev_activity.get_development_activity(conn, repo_root=REPO_ROOT)

        check("2a. a missing session_handoffs table is reported, not fabricated",
              model["session_handoff"]["available"] is False
              and "session_handoffs" in model["session_handoff"]["note"],
              model["session_handoff"])
        check("2b. a missing dev_continuity_events table is reported, not fabricated",
              model["continuity_events"]["available"] is False
              and model["continuity_events"]["events"] == []
              and model["continuity_events"]["total_count"] == 0,
              model["continuity_events"])
        check("2c. a missing workbench_action_proposals table is reported, not fabricated",
              model["action_proposals"]["available"] is False
              and model["action_proposals"]["proposals"] == [],
              model["action_proposals"])
        check("2d. a missing continuity_transactions table names migration 0041 honestly",
              model["continuity_transactions"]["available"] is False
              and "0041" in model["continuity_transactions"]["note"],
              model["continuity_transactions"])
        check("2e. the model still builds completely — no missing optional table ever raises",
              model["read_model"] == "cis_development_activity", model["read_model"])
    finally:
        conn.close()


def test_action_proposals_present_but_card_runner_runs_absent():
    """Exactly production's current shape: workbench_action_proposals (0038)
    exists, card_runner_runs (0037) does not. No crash, and every proposal's
    dispatch_run is honestly not_yet_linked rather than attempting a lookup
    against a table that is not there."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    try:
        _exec_migration(conn, "0038_workbench_action_proposals.sql")
        _insert_proposal(conn, 1, "proj-x", "req-1", card_runner_run_id=1)
        conn.commit()

        feed = dev_activity.get_recent_action_proposals(conn)
        check("3a. the feed is available with card_runner_available reported False",
              feed["available"] is True and feed["card_runner_available"] is False,
              feed)
        check("3b. a stored card_runner_run_id with no target table is not_yet_linked, "
              "not a crash and not an invented authoritative claim",
              feed["proposals"][0]["dispatch_run"]["confidence_class"] == "not_yet_linked",
              feed["proposals"][0]["dispatch_run"])
    finally:
        conn.close()


# ── 3. working tree facts carry no semantic claim ─────────────────────────

def test_working_tree_facts_are_observational_only():
    facts = dev_activity.get_working_tree_facts(repo_root=REPO_ROOT)
    check("4a. working-tree facts are available against the real repo",
          facts["available"] is True, facts)
    check("4b. only observational keys are present — no inferred semantic field",
          set(facts) == {"available", "note", "dirty", "dirty_file_count", "files",
                         "head_sha", "branch"},
          sorted(facts))
    check("4c. each file entry is a raw git status code and a path, nothing else",
          all(set(f) == {"status", "path"} for f in facts["files"]), facts["files"][:3])
    check("4d. dirty_file_count matches the number of files reported",
          facts["dirty_file_count"] == len(facts["files"]), facts)
    check("4e. HEAD is a real commit sha from this repository",
          isinstance(facts["head_sha"], str) and len(facts["head_sha"]) == 40, facts["head_sha"])

    with tempfile.TemporaryDirectory() as tmp:
        degraded = dev_activity.get_working_tree_facts(repo_root=tmp)
        check("4f. a directory that is not a git repository degrades honestly, without raising",
              degraded["available"] is False and degraded["dirty"] is None
              and degraded["files"] == [],
              degraded)


def run():
    test_full_fixture_links_only_explicit_identifiers()
    test_bare_fixture_is_honest_and_does_not_raise()
    test_action_proposals_present_but_card_runner_runs_absent()
    test_working_tree_facts_are_observational_only()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
