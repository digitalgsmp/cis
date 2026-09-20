"""
test_card_factory_app.py — Flask endpoint tests for
runtime/card_factory_app.py (queue item WB.1B-1, incl. the bounded-control
correction addendum on card C1).

Uses a temporary on-disk SQLite database with the real knowledge_messages
table, its real FTS5 index and triggers (copied from
runtime/schema/spine_schema.sql, not the live 5.9GB spine), and migration
0036 applied. The generator's HTTP-level effect is monkeypatched at
`_call_generator` for the route tests (no paid model calls); a separate
section mocks `subprocess.run` directly to exercise `_call_generator`'s own
argv/stdin/timeout/error-shape handling. The gate is the REAL
tools/card_gate.py, run as a real subprocess against the temp db, since it
is free and deterministic.

Run: python3 runtime/tests/test_card_factory_app.py
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault("CIS_PIPELINE_API_KEY", "")

MIGRATION_PATH = os.path.join(
    os.path.dirname(__file__), "..", "schema", "migrations", "0036_card_factory.sql"
)

# Real knowledge_messages schema (runtime/schema/spine_schema.sql), so the
# FTS-findability requirement is exercised against the real trigger wiring,
# not a stand-in.
KNOWLEDGE_MESSAGES_SCHEMA = """
CREATE TABLE knowledge_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    source_key TEXT,
    timestamp TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE knowledge_messages_fts USING fts5(
    content, source, role, content='knowledge_messages', content_rowid='id'
);
CREATE TRIGGER km_ai AFTER INSERT ON knowledge_messages BEGIN
    INSERT INTO knowledge_messages_fts(rowid, content, source, role)
    VALUES (new.id, new.content, new.source, new.role);
END;
CREATE TRIGGER km_ad AFTER DELETE ON knowledge_messages BEGIN
    INSERT INTO knowledge_messages_fts(knowledge_messages_fts, rowid, content, source, role)
    VALUES ('delete', old.id, old.content, old.source, old.role);
END;
CREATE TRIGGER km_au AFTER UPDATE ON knowledge_messages BEGIN
    INSERT INTO knowledge_messages_fts(knowledge_messages_fts, rowid, content, source, role)
    VALUES ('delete', old.id, old.content, old.source, old.role);
    INSERT INTO knowledge_messages_fts(rowid, content, source, role)
    VALUES (new.id, new.content, new.source, new.role);
END;
"""

QUOTE_A = "this is definitely a fifteen char quote for testing"
QUOTE_B = "a totally different but still eric verbatim quote"

MODEL_CARD_TEXT = f"""CARD test-quote-slug: Add a thing
SOURCE: message 1, 2026-09-17
INTENT (Eric, verbatim): "{QUOTE_A}"
BUILD: Eric sees a new button on the page.
DONE WHEN:
  - Eric clicks the button and sees a result.
EVIDENCE:
  - curl -s http://127.0.0.1:5000/ok
NOT IN THIS CARD: dashboards, refactors, other features, docs, migrations, telegram
"""


def make_fixture_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(KNOWLEDGE_MESSAGES_SCHEMA)
    with open(MIGRATION_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def run():
    results = []
    failures = []

    def check(label, cond, detail=""):
        if cond:
            results.append(f"{label}: PASS")
        else:
            results.append(f"{label}: FAIL — {detail}")
            failures.append(label)

    tmp_root = tempfile.mkdtemp(prefix="card_factory_app_test_")
    db_path = os.path.join(tmp_root, "test_spine.db")
    inbox_dir = os.path.join(tmp_root, "inbox")
    history_dir = os.path.join(tmp_root, "history")
    make_fixture_db(db_path)

    orig_db_path_env = os.environ.get("CIS_SPINE_PATH")
    os.environ["CIS_SPINE_PATH"] = db_path

    import card_factory_app  # noqa: E402 — imported after CIS_SPINE_PATH is set
    card_factory_app.DB_PATH = db_path
    card_factory_app.CARDS_INBOX_DIR = inbox_dir      # never write into the real cards/inbox/
    card_factory_app.CARDS_HISTORY_DIR = history_dir  # never write into the real cards/history/

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(card_factory_app.card_factory_bp)
    client = app.test_client()

    orig_generator = card_factory_app._call_generator
    orig_subprocess_run = subprocess.run

    def mock_ok(text=MODEL_CARD_TEXT, usage=None):
        return lambda payload: (text, None, usage)

    try:
        # ── 1. Submit ask ────────────────────────────────────────────────
        resp = client.post("/api/cardfactory/asks", json={
            "project": "cis",
            "ask_text": QUOTE_A,
            "done_when_text": "I can see it work.",
        })
        check("1a. submit ask -> 201", resp.status_code == 201, resp.status_code)
        ask = resp.get_json()["ask"]
        ask_id = ask["id"]
        check("1b. ask persists project", ask["project"] == "cis", ask)
        check("1c. ask starts at revision 1", ask["revision"] == 1, ask)

        # ── 2. knowledge_messages insert is findable by FTS ─────────────
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT role, content FROM knowledge_messages_fts "
            "WHERE knowledge_messages_fts MATCH ?",
            ('"fifteen char quote for testing"',),
        ).fetchone()
        check("2a. ask text findable via FTS", row is not None, row)
        check("2b. inserted with Eric's role (human)",
              row is not None and row[0] == "human", row)
        conn.close()

        # ── 3. Generate requires a request_id ────────────────────────────
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate", json={})
        check("3a. generate without request_id -> 400", resp.status_code == 400, resp.status_code)

        # ── 4. Generate -> PASS ──────────────────────────────────────────
        card_factory_app._call_generator = mock_ok()
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-1"})
        check("4a. generate -> 201", resp.status_code == 201, (resp.status_code, resp.get_json()))
        card = resp.get_json()["card"]
        card_id = card["id"]
        check("4b. gate PASS -> status pass", card["status"] == "pass", card)
        check("4c. gate exit code 0", card["gate_exit_code"] == 0, card)
        check("4d. PASS card saved to cards/inbox/",
              card["saved_path"] and os.path.exists(card["saved_path"]), card)
        check("4e. not stale against its own ask revision", card["stale"] is False, card)
        check("4f. eligible for dispatch", card["eligible_for_dispatch"] is True, card)
        check("4g. lineage_id set to its own id", card["lineage_id"] == card_id, card)
        check("4h. card_revision starts at 1", card["card_revision"] == 1, card)

        # ── 5. Repeating the same request_id does not call the generator again ──
        card_factory_app._call_generator = lambda payload: (_ for _ in ()).throw(
            AssertionError("generator must not be called again for a replayed request_id"))
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-1"})
        check("5a. replayed request_id -> 200, no second model call", resp.status_code == 200,
              resp.status_code)
        check("5b. flagged duplicate", resp.get_json()["duplicate"] is True, resp.get_json())
        check("5c. returns the same card id", resp.get_json()["card"]["id"] == card_id,
              resp.get_json())

        # ── 6. Concurrent generation of the same ask revision is refused ────
        # Simulate an in-flight generation by inserting the pending lock row
        # directly (as generate_card itself would, before calling the model).
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO card_factory_cards (ask_id, ask_revision, card_revision, is_current, "
            "status, request_id) VALUES (?, 1, 1, 1, 'pending', 'gen-inflight')",
            (ask_id,),
        )
        conn.commit()
        conn.close()
        card_factory_app._call_generator = lambda payload: (_ for _ in ()).throw(
            AssertionError("generator must not run when refused for concurrency"))
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-2-different"})
        check("6a. concurrent generate -> 409", resp.status_code == 409, resp.status_code)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "DELETE FROM card_factory_cards WHERE request_id = 'gen-inflight'"
        )
        conn.commit()
        conn.close()

        # ── 7. Generate -> FAIL (banned word) ────────────────────────────
        fail_text = MODEL_CARD_TEXT.replace(
            "BUILD: Eric sees a new button on the page.",
            "BUILD: Eric sees a robust new button on the page.",
        )
        card_factory_app._call_generator = mock_ok(fail_text)
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-3"})
        card_fail = resp.get_json()["card"]
        check("7a. banned word -> status fail", card_fail["status"] == "fail", card_fail)
        check("7b. non-zero gate exit code", card_fail["gate_exit_code"] != 0, card_fail)
        check("7c. failed-gate card not saved to inbox", card_fail["saved_path"] is None, card_fail)

        # ── 8. Generate -> SKIP (NO_CARD) ────────────────────────────────
        card_factory_app._call_generator = mock_ok("NO_CARD")
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-4"})
        card_skip = resp.get_json()["card"]
        check("8a. NO_CARD -> status skip", card_skip["status"] == "skip", card_skip)
        check("8b. SKIP has exit code 0", card_skip["gate_exit_code"] == 0, card_skip)

        # ── 9. Generation error (never becomes a dispatchable card) ──────
        card_factory_app._call_generator = lambda payload: (None, "generator timed out after 90s", None)
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-5"})
        check("9a. generation error -> 502", resp.status_code == 502, resp.status_code)
        check("9b. plain error body, no card object", "card" not in resp.get_json(), resp.get_json())
        check("9c. error text present", "timed out" in resp.get_json().get("error", ""),
              resp.get_json())

        # ── 10. Oversized generator output is rejected, not truncated ────
        card_factory_app._call_generator = mock_ok(
            "CARD x: y\n" + ("z" * (card_factory_app.MAX_GENERATOR_OUTPUT_CHARS + 500))
        )
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-6"})
        check("10a. oversized output -> 502", resp.status_code == 502, resp.status_code)
        check("10b. bound named in error", "exceeds" in resp.get_json().get("error", ""),
              resp.get_json())

        # ── 11. Stale-generation guard: ask edited mid-generation ────────
        def generator_that_mutates_ask(payload):
            c = sqlite3.connect(db_path)
            c.execute(
                "UPDATE card_factory_asks SET ask_text = ?, revision = revision + 1 WHERE id = ?",
                ("a mid-flight edit that changes everything", ask_id),
            )
            c.commit()
            c.close()
            return MODEL_CARD_TEXT, None, None
        card_factory_app._call_generator = generator_that_mutates_ask
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-7"})
        check("11a. ask changed mid-generation -> 409", resp.status_code == 409, resp.status_code)
        check("11b. discarded, not gated", "discarded" in resp.get_json().get("error", ""),
              resp.get_json())
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT status, card_text FROM card_factory_cards WHERE request_id = 'gen-7'"
        ).fetchone()
        check("11c. discarded attempt stored as error, no card_text kept",
              row[0] == "error" and row[1] is None, row)
        conn.close()

        # Ask is now at revision 2 (from the mid-flight mutation above). All
        # cards generated at revision 1 are now stale, and card 4's PASS
        # file should have been archived out of the active inbox as part of
        # that edit — but this mutation went straight to the DB, bypassing
        # edit_ask's archiving step, precisely to isolate the "generator
        # already ran, ask moved on" race from the "user explicitly edited"
        # path tested next. Confirm the ask's revision did move:
        conn = sqlite3.connect(db_path)
        rev_after = conn.execute(
            "SELECT revision FROM card_factory_asks WHERE id = ?", (ask_id,)
        ).fetchone()[0]
        conn.close()
        check("11d. ask revision incremented", rev_after == 2, rev_after)
        resp = client.get(f"/api/cardfactory/cards/{card_id}")
        check("11e. old PASS card now reads as stale",
              resp.get_json()["card"]["stale"] is True, resp.get_json())
        check("11f. stale card is not eligible for dispatch",
              resp.get_json()["card"]["eligible_for_dispatch"] is False, resp.get_json())

        # ── 12. Editing an ask (through the API) archives inboxed PASS cards ──
        # Build a fresh ask/card pair to test the API-driven edit path in
        # isolation from the direct-DB mutation used in step 11.
        card_factory_app._call_generator = orig_generator  # restore before next mock
        resp = client.post("/api/cardfactory/asks", json={
            "project": "cis", "ask_text": QUOTE_B,
        })
        ask2_id = resp.get_json()["ask"]["id"]
        card_factory_app._call_generator = mock_ok(
            MODEL_CARD_TEXT.replace(QUOTE_A, QUOTE_B)
        )
        resp = client.post(f"/api/cardfactory/asks/{ask2_id}/generate",
                            json={"request_id": "gen-ask2-1"})
        card2 = resp.get_json()["card"]
        check("12a. second ask's card -> pass", card2["status"] == "pass", card2)
        inbox_path_before = card2["saved_path"]
        check("12b. file exists in active inbox before edit",
              inbox_path_before and os.path.exists(inbox_path_before), inbox_path_before)

        resp = client.patch(f"/api/cardfactory/asks/{ask2_id}",
                             json={"ask_text": "a completely rewritten ask now"})
        check("12c. edit ask -> 200", resp.status_code == 200, resp.status_code)
        check("12d. ask revision bumped", resp.get_json()["ask"]["revision"] == 2,
              resp.get_json())

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT content FROM knowledge_messages WHERE id = "
            "(SELECT knowledge_message_id FROM card_factory_asks WHERE id = ?)",
            (ask2_id,),
        ).fetchone()
        check("12e. edited ask text propagates to knowledge_messages",
              row is not None and "completely rewritten" in row[0], row)
        card2_after = conn.execute(
            "SELECT saved_path FROM card_factory_cards WHERE id = ?", (card2["id"],)
        ).fetchone()
        conn.close()
        check("12f. inbox file archived out of the active inbox",
              not os.path.exists(inbox_path_before), inbox_path_before)
        check("12g. archived file now lives under cards/history/",
              card2_after[0] and card2_after[0].startswith(history_dir), card2_after)
        check("12h. archived file actually exists at its new path",
              card2_after[0] and os.path.exists(card2_after[0]), card2_after)

        # ── 13. Edit card text -> new revision, old row retired ──────────
        broken_text = MODEL_CARD_TEXT.replace(
            f'"{QUOTE_A}"', '"an invented quote nobody ever actually said at all"')
        resp = client.patch(f"/api/cardfactory/cards/{card_id}", json={"card_text": broken_text})
        check("13a. edit -> 201 (new revision row)", resp.status_code == 201, resp.status_code)
        edited = resp.get_json()["card"]
        check("13b. new row has a new id", edited["id"] != card_id, edited)
        check("13c. same lineage as the original", edited["lineage_id"] == card_id, edited)
        check("13d. card_revision incremented", edited["card_revision"] == 2, edited)
        check("13e. supersedes the original id", edited["supersedes_id"] == card_id, edited)
        check("13f. invented quote fails the gate again", edited["status"] == "fail", edited)

        resp = client.get(f"/api/cardfactory/cards/{card_id}")
        check("13g. original row now is_current=false",
              resp.get_json()["card"]["is_current"] is False, resp.get_json())

        # ── 14. Editing a superseded (non-current) revision is refused ───
        resp = client.patch(f"/api/cardfactory/cards/{card_id}", json={"card_text": "irrelevant"})
        check("14a. editing a superseded row -> 409", resp.status_code == 409, resp.status_code)
        check("14b. names the current revision id",
              resp.get_json().get("current_revision_id") == edited["id"], resp.get_json())

        # ── 15. Explicit re-gate route (no new revision) ─────────────────
        resp = client.post(f"/api/cardfactory/cards/{edited['id']}/regate")
        check("15a. re-gate -> 200", resp.status_code == 200, resp.status_code)
        check("15b. re-gate reproduces the same fail verdict, same id",
              resp.get_json()["card"]["status"] == "fail" and
              resp.get_json()["card"]["id"] == edited["id"], resp.get_json())

        # ── 16. List / get ─────────────────────────────────────────────
        resp = client.get(f"/api/cardfactory/cards?ask_id={ask_id}")
        check("16a. list cards scoped by ask_id -> 200", resp.status_code == 200, resp.status_code)

        resp = client.get(f"/api/cardfactory/cards/{edited['id']}")
        check("16b. get single card -> 200", resp.status_code == 200, resp.status_code)

        resp = client.get("/api/cardfactory/cards/999999")
        check("16c. unknown card -> 404", resp.status_code == 404, resp.status_code)

        # ── 16d-16f. Review-fix regressions ──────────────────────────────
        # (1) Reusing a request_id after the ask moved on is refused, never
        # silently served as if it were still current. `ask_id` is now at
        # revision 2 (bumped in step 11); 'gen-1' was used back at revision 1.
        card_factory_app._call_generator = lambda payload: (_ for _ in ()).throw(
            AssertionError("generator must not run for a revision-stale request_id replay"))
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-1"})
        check("16d. stale-revision request_id replay -> 409, not a silent 200",
              resp.status_code == 409, resp.status_code)
        check("16e. names the ask-changed reason",
              "earlier ask" in resp.get_json().get("error", ""), resp.get_json())

        # (2) A pending row stuck since before a crash/restart is reconciled
        # (to 'error') rather than permanently holding the per-ask-revision
        # generation lock, and a fresh generate() then succeeds.
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO card_factory_cards (ask_id, ask_revision, card_revision, is_current, "
            "status, request_id, created_at) VALUES (?, 2, 1, 1, 'pending', 'gen-stuck', "
            "datetime('now', ?))",
            (ask_id, f"-{card_factory_app.PENDING_STALE_SECONDS + 30} seconds"),
        )
        conn.commit()
        conn.close()
        card_factory_app._call_generator = mock_ok()
        resp = client.post(f"/api/cardfactory/asks/{ask_id}/generate",
                            json={"request_id": "gen-unstick"})
        check("16f. generate succeeds after a stuck pending row is reconciled",
              resp.status_code == 201, (resp.status_code, resp.get_json()))
        conn = sqlite3.connect(db_path)
        stuck = conn.execute(
            "SELECT status, error FROM card_factory_cards WHERE request_id = 'gen-stuck'"
        ).fetchone()
        conn.close()
        check("16g. stuck row reconciled to error",
              stuck[0] == "error" and "restarted or crashed" in stuck[1], stuck)

        # (3) Editing a card whose generation is still in flight is refused.
        conn = sqlite3.connect(db_path)
        cur = conn.execute(
            "INSERT INTO card_factory_cards (ask_id, ask_revision, card_revision, is_current, status) "
            "VALUES (?, 2, 1, 1, 'pending')",
            (ask_id,),
        )
        pending_card_id = cur.lastrowid
        conn.execute(
            "UPDATE card_factory_cards SET lineage_id = ? WHERE id = ?",
            (pending_card_id, pending_card_id),
        )
        conn.commit()
        conn.close()
        resp = client.patch(f"/api/cardfactory/cards/{pending_card_id}",
                             json={"card_text": "irrelevant"})
        check("16h. editing an in-flight (pending) card -> 409",
              resp.status_code == 409, resp.status_code)
        check("16i. names the in-progress reason",
              "in progress" in resp.get_json().get("error", ""), resp.get_json())

        # (4) Re-gating a PASS card that now fails archives its inbox file —
        # a stale/failing card must not keep looking dispatch-eligible just
        # because nobody edited it.
        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE card_factory_cards SET card_text = ? WHERE id = ?",
            (MODEL_CARD_TEXT.replace(
                "BUILD: Eric sees a new button on the page.",
                "BUILD: Eric sees a robust new button on the page.",
            ), card2["id"]),
        )
        conn.commit()
        conn.close()
        regressed_path = card2["saved_path"]
        # card2's file was already archived in step 12 (its ask was edited);
        # re-inbox it here to isolate this test's own scenario.
        os.makedirs(inbox_dir, exist_ok=True)
        conn = sqlite3.connect(db_path)
        refreshed_path = os.path.join(inbox_dir, os.path.basename(regressed_path))
        with open(refreshed_path, "w") as f:
            f.write("placeholder")
        conn.execute(
            "UPDATE card_factory_cards SET saved_path = ? WHERE id = ?",
            (refreshed_path, card2["id"]),
        )
        conn.commit()
        conn.close()
        resp = client.post(f"/api/cardfactory/cards/{card2['id']}/regate")
        check("16j. regate -> 200", resp.status_code == 200, resp.status_code)
        check("16k. verdict flips to fail on regate",
              resp.get_json()["card"]["status"] == "fail", resp.get_json())
        check("16l. file removed from the active inbox on regate-to-fail",
              not os.path.exists(refreshed_path), refreshed_path)
        check("16m. saved_path now points into cards/history/",
              resp.get_json()["card"]["saved_path"] and
              resp.get_json()["card"]["saved_path"].startswith(history_dir),
              resp.get_json())

        # ── 16n-16p. Second review-round fixes ───────────────────────────
        # (5) A PASS verdict reached AFTER the ask changed during the GATE
        # call (not the generator call) must not be written to the inbox.
        resp = client.post("/api/cardfactory/asks", json={
            "project": "cis", "ask_text": "a fresh ask for the gate-window race test",
        })
        ask3_id = resp.get_json()["ask"]["id"]
        card_factory_app._call_generator = mock_ok(
            MODEL_CARD_TEXT.replace(QUOTE_A, "a fresh ask for the gate-window race test")
        )
        orig_run_gate = card_factory_app._run_gate

        def gate_that_mutates_ask(card_text):
            c = sqlite3.connect(db_path)
            c.execute(
                "UPDATE card_factory_asks SET ask_text = ?, revision = revision + 1 WHERE id = ?",
                ("mutated mid-gate", ask3_id),
            )
            c.commit()
            c.close()
            return orig_run_gate(card_text)
        card_factory_app._run_gate = gate_that_mutates_ask
        try:
            resp = client.post(f"/api/cardfactory/asks/{ask3_id}/generate",
                                json={"request_id": "gen-gate-race"})
        finally:
            card_factory_app._run_gate = orig_run_gate
        card3 = resp.get_json()["card"]
        check("16n. gate-window race -> gate's own verdict kept (pass)",
              card3["status"] == "pass", card3)
        check("16o. but never written to the active inbox", card3["saved_path"] is None, card3)
        check("16p. reads as stale / not eligible", card3["stale"] is True and
              card3["eligible_for_dispatch"] is False, card3)

        # (3) At most one is_current=1 row per lineage — enforced at the DB
        # level (idx_cf_cards_lineage_current), not only by edit_card's own
        # ordering. Two concurrent edits racing to insert a second current
        # tip in the same lineage must not both succeed.
        conn = sqlite3.connect(db_path)
        raised = False
        try:
            conn.execute(
                "INSERT INTO card_factory_cards (ask_id, ask_revision, lineage_id, "
                "card_revision, is_current, status) VALUES (?, 1, ?, 99, 1, 'pass')",
                (edited["ask_id"], edited["lineage_id"]),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raised = True
        conn.close()
        check("16q. DB refuses a second is_current row in the same lineage",
              raised, "expected sqlite3.IntegrityError")

        # ── 17. Malformed input ────────────────────────────────────────
        resp = client.post("/api/cardfactory/asks", json={"project": "", "ask_text": "x" * 20})
        check("17a. empty project -> 400", resp.status_code == 400, resp.status_code)
        resp = client.post("/api/cardfactory/asks", json={"project": "cis", "ask_text": ""})
        check("17b. empty ask_text -> 400", resp.status_code == 400, resp.status_code)
        resp = client.post("/api/cardfactory/asks/999999/generate", json={"request_id": "x"})
        check("17c. generate on unknown ask -> 404", resp.status_code == 404, resp.status_code)
        resp = client.post("/api/cardfactory/asks", json={
            "project": "cis", "ask_text": "x" * (card_factory_app.MAX_ASK_TEXT_CHARS + 1)})
        check("17d. over-length ask_text -> 400", resp.status_code == 400, resp.status_code)

    finally:
        card_factory_app._call_generator = orig_generator
        subprocess.run = orig_subprocess_run
        if orig_db_path_env is None:
            os.environ.pop("CIS_SPINE_PATH", None)
        else:
            os.environ["CIS_SPINE_PATH"] = orig_db_path_env
        import shutil
        shutil.rmtree(tmp_root, ignore_errors=True)

    # ── 18-22. _call_generator's own subprocess contract (mocked at the
    # subprocess.run level, not at _call_generator itself) ────────────────
    class FakeCompletedProcess:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def with_fake_subprocess(fake_run):
        subprocess.run = fake_run
        try:
            return card_factory_app._call_generator(
                {"id": 1, "date": "2026-09-17", "project": "cis", "text": "hello"})
        finally:
            subprocess.run = orig_subprocess_run

    captured_call = {}

    def capture_and_succeed(cmd, **kwargs):
        captured_call["cmd"] = cmd
        captured_call["input"] = kwargs.get("input")
        captured_call["timeout"] = kwargs.get("timeout")
        return FakeCompletedProcess(0, json.dumps({
            "result": "NO_CARD", "is_error": False,
            "usage": {"input_tokens": 111, "output_tokens": 22}, "total_cost_usd": 0.001,
        }))
    result_text, error, usage = with_fake_subprocess(capture_and_succeed)
    check("18a. real argv uses configured GENERATOR_COMMAND",
          captured_call["cmd"] == card_factory_app.GENERATOR_COMMAND, captured_call.get("cmd"))
    check("18b. GENERATOR_COMMAND disables tools", "--tools" in captured_call["cmd"] and
          captured_call["cmd"][captured_call["cmd"].index("--tools") + 1] == "",
          captured_call["cmd"])
    check("18c. GENERATOR_COMMAND uses --safe-mode", "--safe-mode" in captured_call["cmd"],
          captured_call["cmd"])
    check("18d. prompt file content + payload sent on stdin",
          "CARD GENERATOR" in captured_call["input"] and '"text": "hello"' in captured_call["input"],
          captured_call["input"][:200])
    check("18e. timeout matches GENERATOR_TIMEOUT_SECONDS",
          captured_call["timeout"] == card_factory_app.GENERATOR_TIMEOUT_SECONDS, captured_call)
    check("18f. success result parsed", result_text == "NO_CARD" and error is None, (result_text, error))
    check("18g. usage parsed from JSON", usage == {"input_tokens": 111, "output_tokens": 22, "cost_usd": 0.001},
          usage)

    def raise_timeout(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout"))
    result_text, error, usage = with_fake_subprocess(raise_timeout)
    check("19a. subprocess timeout -> error, not an exception", result_text is None and error is not None,
          (result_text, error))
    check("19b. timeout error names the bound", "timed out" in error, error)

    def nonzero_exit(cmd, **kwargs):
        return FakeCompletedProcess(1, "", "boom: something broke")
    result_text, error, usage = with_fake_subprocess(nonzero_exit)
    check("20a. nonzero exit -> error", result_text is None and "boom" in error, error)

    def malformed_json(cmd, **kwargs):
        return FakeCompletedProcess(0, "not json at all {{{")
    result_text, error, usage = with_fake_subprocess(malformed_json)
    check("21a. malformed JSON -> error, not a crash", result_text is None and "malformed" in error, error)

    def json_but_not_object(cmd, **kwargs):
        return FakeCompletedProcess(0, json.dumps([1, 2, 3]))
    result_text, error, usage = with_fake_subprocess(json_but_not_object)
    check("21b. valid JSON that is not an object -> error, not a crash",
          result_text is None and "malformed" in error, error)

    def empty_result(cmd, **kwargs):
        return FakeCompletedProcess(0, json.dumps({"result": "", "is_error": False}))
    result_text, error, usage = with_fake_subprocess(empty_result)
    check("22a. empty result -> error", result_text is None and "empty" in error, error)

    def is_error_true(cmd, **kwargs):
        return FakeCompletedProcess(0, json.dumps({"result": "oops", "is_error": True}))
    result_text, error, usage = with_fake_subprocess(is_error_true)
    check("22b. is_error true -> error even though result text is present",
          result_text is None and "error" in error.lower(), error)

    # ── 23. Gate subprocess failure is a recorded error, not a bare 500 ──
    def gate_timeout(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout"))
    subprocess.run = gate_timeout
    try:
        status, exit_code, output = card_factory_app._run_gate(MODEL_CARD_TEXT)
    finally:
        subprocess.run = orig_subprocess_run
    check("23a. gate timeout -> status error, not an exception", status == "error", status)
    check("23b. gate timeout reason recorded", "timed out" in output, output)

    for r in results:
        print(r)
    print(f"\n{len(results) - len(failures)}/{len(results)} passed.")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    run()
