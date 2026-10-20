"""Deterministic tests; no model, network, or live spine is touched."""

import json
import os
import shutil
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from continuity_interceptor import (  # noqa: E402
    BOUNDED_ALLOWED_FIELDS, BOUNDED_FIELDS, CONTRACT_VERSION,
    LEDGER_MARK_MIGRATION_ABSENT, LEDGER_MARK_RECORDED, SemanticTransaction,
    assert_permitted, bounded_authorization_dict, content_hash, decision_for,
    evaluate, is_missing_ledger_table, persist_check,
)

MIGRATION = os.path.join(os.path.dirname(__file__), "..", "schema", "migrations",
                         "0041_continuity_transactions.sql")


def fixture(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE knowledge_messages (
            id INTEGER PRIMARY KEY, content TEXT, source TEXT,
            role TEXT, source_key TEXT
        );
        CREATE VIRTUAL TABLE knowledge_messages_fts USING fts5(
            content, source, role, content='knowledge_messages', content_rowid='id'
        );
        CREATE TRIGGER km_ai AFTER INSERT ON knowledge_messages BEGIN
            INSERT INTO knowledge_messages_fts(rowid, content, source, role)
            VALUES (new.id, new.content, new.source, new.role);
        END;
    """)
    rows = (
        ("The system is recursive. Four nested loops feed material, workflow, "
         "system learning, and documentation back into one another.",
         "cis_docs", "user", "vision/four-loops:184"),
        ("Research occurs between every domain transition. WIAS domains "
         "accumulate; they are not five separate pipelines.",
         "hermes_session", "user", "session/20260512/4.0"),
        ("A later assistant summarized a generic recursive enterprise pipeline.",
         "assistant_summary", "assistant", "summary/late"),
    )
    conn.executemany(
        "INSERT INTO knowledge_messages(content,source,role,source_key) VALUES(?,?,?,?)",
        rows,
    )
    conn.executescript(open(MIGRATION, encoding="utf-8").read())
    conn.commit()
    return conn


def transaction(**changes):
    values = dict(
        kind="PLAN", criticality="CANDIDATE", actor="workbench",
        operation="Turn recursive loops and domain transitions into a plan",
        input_payload={"memory": "loops within loops between domains"},
        proposed_output={"plan": "four nested loops and domain transitions"},
        project_id="cis", domain="universal-kernel",
        process="research-to-plan", loop="system-learning",
        input_refs=("user-turn:1",), request_id="request-1",
    )
    values.update(changes)
    return SemanticTransaction(**values)


def report(_messages):
    return json.dumps({
        "verdict": "ANTECEDENT_FOUND",
        "summary": "The plan recovers the nested-loop model.",
        "concepts": ["four nested loops", "domains accumulate"],
        "source_refs": ["vision/four-loops:184", "session/20260512/4.0"],
        "required_changes": [],
        "uncertainty": "Execution has not tested it.",
    }), None


def run():
    results = []

    def check(label, condition):
        results.append((label, bool(condition)))

    temp = tempfile.mkdtemp(prefix="continuity_")
    conn = fixture(os.path.join(temp, "spine.db"))
    try:
        semantic = lambda _query, _limit: [{  # noqa: E731
            "source_ref": "vision/four-loops:184", "source": "cis_docs",
            "role": "user", "content": "The system is recursive. Four nested loops."
        }, {
            "source_ref": "semantic/new", "source": "session_archive",
            "role": "user", "content": "Knowledge objects recurse across domains."
        }]
        tx = transaction()
        auth = evaluate(conn, tx, report, semantic_retriever=semantic)
        check("hybrid retrieval merges and deduplicates",
              len(auth.antecedents) == 4 and
              sum(h["source_ref"] == "vision/four-loops:184"
                  for h in auth.antecedents) == 1)
        check("retrieval reports both paths",
              any(n.startswith("fts:ok") for n in auth.retrieval_notes) and
              any(n.startswith("semantic:ok") for n in auth.retrieval_notes))
        check("original user language ranks before assistant summary",
              auth.antecedents[0]["role"] == "user")
        check("authorization binds all current material",
              auth.contract_version == CONTRACT_VERSION and
              auth.permits(tx, auth.evidence_set_hash))
        check("changed output rejected", not auth.permits(transaction(
            transaction_id=tx.transaction_id,
            proposed_output={"plan": "generic linear pipeline"}),
            auth.evidence_set_hash))
        check("changed input rejected", not auth.permits(transaction(
            transaction_id=tx.transaction_id, input_payload={"changed": True}),
            auth.evidence_set_hash))
        check("changed evidence rejected", not auth.permits(
            tx, evidence_set_hash="0" * 64))

        persist_check(conn, tx, auth)
        persist_check(conn, tx, auth, status="COMMITTED")
        conn.commit()
        # Same request and kind must permit a distinct transaction/evaluation.
        tx2 = transaction()
        auth2 = evaluate(conn, tx2, report)
        persist_check(conn, tx2, auth2)
        conn.commit()
        check("ledger is append-only", conn.execute(
            "SELECT count(*) FROM continuity_transactions"
        ).fetchone()[0] == 3)
        check("multiple same-kind request transactions allowed", conn.execute(
            "SELECT count(DISTINCT transaction_id) FROM continuity_transactions "
            "WHERE request_id='request-1' AND kind='PLAN'"
        ).fetchone()[0] == 2)

        row = conn.execute(
            "SELECT envelope_json,check_json FROM continuity_transactions LIMIT 1"
        ).fetchone()
        stored = row["envelope_json"] + row["check_json"]
        check("ledger JSON excludes prompts and excerpts",
              "loops within loops" not in stored and
              "The system is recursive" not in stored and
              "generic" not in stored)

        bounded = auth.bounded_dict()
        bounded_text = json.dumps(bounded)
        check("bounded_dict drops antecedents (raw excerpt text)",
              "antecedents" not in bounded and
              "The system is recursive" not in bounded_text)
        check("bounded_dict still carries the binding hashes/decision",
              bounded["transaction_id"] == tx.transaction_id and
              bounded["decision"] == "ALLOW")
        check("bounded_dict is exactly the metadata allowlist",
              set(bounded) == set(BOUNDED_FIELDS))
        check("bounded_dict drops every model-generated free-form field",
              not any(key in bounded for key in
                      ("summary", "concepts", "required_changes", "uncertainty")))
        check("bounded_dict carries none of the backend's own analysis text",
              "The plan recovers the nested-loop model." not in bounded_text and
              "four nested loops" not in bounded_text and
              "Execution has not tested it." not in bounded_text)
        check("the full in-memory authorization still holds that text for the "
              "immediate HOLD explanation",
              auth.summary == "The plan recovers the nested-loop model." and
              "summary" in auth.as_dict() and "antecedents" in auth.as_dict())
        check("bounded_authorization_dict drops anything outside the allowlist "
              "and keeps the ledger marks",
              bounded_authorization_dict({
                  **bounded, "summary": "leaked", "antecedents": [{"excerpt": "leaked"}],
                  "ledger_recorded": True, "ledger_status": LEDGER_MARK_RECORDED,
              }) == {**bounded, "ledger_recorded": True,
                     "ledger_status": LEDGER_MARK_RECORDED})
        check("the ledger marks are inside the allowlist and the free-form "
              "fields are not",
              {"ledger_recorded", "ledger_status"} <= BOUNDED_ALLOWED_FIELDS and
              not ({"summary", "antecedents", "uncertainty"} & BOUNDED_ALLOWED_FIELDS))

        # Degradation is permitted for exactly one persistence failure: an
        # absent migration 0041, identified by SQLite's own message.
        no_ledger = sqlite3.connect(os.path.join(temp, "no_ledger.db"))
        no_ledger.row_factory = sqlite3.Row
        try:
            persist_check(no_ledger, tx, auth)
            absent = None
        except sqlite3.OperationalError as exc:
            absent = exc
        finally:
            no_ledger.close()
        check("an absent ledger table is identified as absent migration 0041",
              absent is not None and is_missing_ledger_table(absent) and
              LEDGER_MARK_MIGRATION_ABSENT == "migration_0041_not_applied")
        check("other SQLite persistence errors are NOT the absent-migration case",
              not is_missing_ledger_table(sqlite3.OperationalError("database is locked")) and
              not is_missing_ledger_table(
                  sqlite3.OperationalError("attempt to write a readonly database")) and
              not is_missing_ledger_table(sqlite3.OperationalError("no such table: other")) and
              not is_missing_ledger_table(sqlite3.IntegrityError(
                  "UNIQUE constraint failed: continuity_transactions.ledger_event_id")))

        persist_check(conn, tx, auth, status="INVALIDATED")
        conn.commit()
        try:
            assert_permitted(auth, tx, auth.evidence_set_hash, conn=conn)
            invalidated_blocked = False
        except PermissionError:
            invalidated_blocked = True
        check("invalidated authorization rejected", invalidated_blocked)

        try:
            conn.execute("BEGIN IMMEDIATE")
            evaluate(conn, transaction(), report)
            lock_guarded = False
        except RuntimeError:
            lock_guarded = True
        finally:
            conn.rollback()
        check("model work forbidden under write lock", lock_guarded)

        unavailable = evaluate(conn, transaction(criticality="AUTHORITATIVE"),
                               lambda _m: (None, "offline"))
        check("authoritative backend failure holds",
              unavailable.verdict == "UNAVAILABLE" and
              unavailable.decision == "HOLD")
        check("observe failure annotates",
              decision_for("OBSERVE", "UNAVAILABLE") == "ANNOTATE")

        def broken_semantic(_query, _limit):
            raise RuntimeError("offline")

        fallback = evaluate(conn, transaction(), report,
                            semantic_retriever=broken_semantic)
        check("semantic failure is explicit and FTS remains usable",
              any(n == "semantic:failed:RuntimeError"
                  for n in fallback.retrieval_notes) and bool(fallback.antecedents))
    finally:
        conn.close()
        shutil.rmtree(temp, ignore_errors=True)

    for label, passed in results:
        print(f"{'PASS' if passed else 'FAIL'}  {label}")
    failed = [label for label, passed in results if not passed]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
