"""
test_workbench_app.py — Flask endpoint tests for runtime/workbench_app.py
(queue item WB.1A).

Uses a temporary on-disk SQLite database (migration 0035 applied directly,
not the live 5.9GB spine) and a monkeypatched Brain gateway call — no
network calls, no paid model calls, no mutation of the real KB.

Run: python3 runtime/tests/test_workbench_app.py
"""
import json
import os
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Auth is fail-CLOSED (runtime/workbench_auth.py): an unset CIS_PIPELINE_API_KEY
# denies every request with 503 rather than granting anonymous access. This
# suite therefore configures a real key and presents it as a real caller would
# (see client.environ_base below). It is deliberately NOT set to "" — a blank
# key is "server not configured", not "authenticated".
TEST_API_KEY = "test-workbench-key"
os.environ["CIS_PIPELINE_API_KEY"] = TEST_API_KEY

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "schema", "migrations")
MIGRATION_PATH = os.path.join(MIGRATIONS_DIR, "0035_workbench.sql")
# 0038 (workbench_action_proposals) is queried unconditionally by
# send_message()'s duplicate-lookup, even in plain 'chat' mode (queue item
# WB.1B-2B) — the fixture needs it present regardless of which test
# exercises the proposal workflow itself.
MIGRATION_0038_PATH = os.path.join(MIGRATIONS_DIR, "0038_workbench_action_proposals.sql")


def make_fixture_db(path):
    conn = sqlite3.connect(path)
    with open(MIGRATION_PATH) as f:
        conn.executescript(f.read())
    with open(MIGRATION_0038_PATH) as f:
        conn.executescript(f.read())
    # workbench_app's _kb_search expects this table/FTS name to exist or
    # fails closed to [] — create a minimal FTS index so the KB-context
    # contract (source ids + excerpt) is actually exercised.
    conn.execute(
        "CREATE VIRTUAL TABLE knowledge_messages_fts USING fts5(content, source)"
    )
    conn.execute(
        "INSERT INTO knowledge_messages_fts (content, source) VALUES (?, ?)",
        ("The workbench keeps Braingate conversation-only in this slice.", "kb-300459"),
    )
    conn.commit()
    conn.close()


def run():
    results = []

    def check(label, cond, detail=""):
        if cond:
            results.append(f"{label}: PASS")
        else:
            results.append(f"{label}: FAIL — {detail}")

    tmp_root = tempfile.mkdtemp(prefix="workbench_app_test_")
    db_path = os.path.join(tmp_root, "test_spine.db")
    make_fixture_db(db_path)

    orig_db_path_env = os.environ.get("CIS_SPINE_PATH")
    os.environ["CIS_SPINE_PATH"] = db_path

    import workbench_app  # noqa: E402 — imported after CIS_SPINE_PATH is set
    workbench_app.DB_PATH = db_path

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(workbench_app.workbench_bp)
    client = app.test_client()
    # Every request from this client carries the configured credential, so the
    # existing checks below exercise authenticated behavior. Fail-closed auth
    # itself is covered by test_braingate_conversation_boundary.py.
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_API_KEY}"

    orig_gateway = workbench_app._call_brain_gateway

    try:
        # ── 1. Create project, no repo path required ───────────────────
        resp = client.post("/api/workbench/projects", json={"name": "My New Idea"})
        check("1a. create project -> 201", resp.status_code == 201, resp.status_code)
        body = resp.get_json()
        project = body["project"]
        check("1b. project has no repo_path requirement", project["repo_path"] is None, project)
        check("1c. kind defaults to planning", project["kind"] == "planning", project["kind"])
        project_id = project["id"]

        # ── 2. Reopen project (persistence across "reload") ─────────────
        resp = client.get(f"/api/workbench/projects/{project_id}")
        check("2. reopen project by id", resp.status_code == 200 and
              resp.get_json()["project"]["name"] == "My New Idea", resp.get_json())

        # ── 3. Second project — isolation ───────────────────────────────
        resp = client.post("/api/workbench/projects", json={"name": "Second Project"})
        project_id_2 = resp.get_json()["project"]["id"]
        check("3a. second project has distinct id", project_id_2 != project_id, project_id_2)

        # ── 4. Successful reply + context rendering contract ────────────
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: (
            "READY TO PROCEED — understood.", None
        )
        resp = client.post(
            f"/api/workbench/projects/{project_id}/messages",
            json={"message": "workbench conversation", "request_id": "req-1"},
        )
        check("4a. send message -> 200", resp.status_code == 200, resp.status_code)
        body = resp.get_json()
        check("4b. not flagged duplicate", body["duplicate"] is False, body)
        check("4c. brain message completed", body["brain_message"]["status"] == "completed",
              body["brain_message"])
        check("4d. brain content present", "READY TO PROCEED" in body["brain_message"]["content"],
              body["brain_message"])
        check("4e. kb_context carries source id", body["brain_message"]["kb_context"] and
              body["brain_message"]["kb_context"][0]["source"] == "kb-300459",
              body["brain_message"]["kb_context"])
        check("4f. kb_limitations stated", bool(body["brain_message"]["kb_limitations"]),
              body["brain_message"])

        # Isolation: project 2 has no messages from project 1
        resp = client.get(f"/api/workbench/projects/{project_id_2}/messages")
        check("4g. second project has no messages (isolation)",
              resp.get_json()["messages"] == [], resp.get_json())

        # ── 5. Reload recovery: messages persisted for project 1 ────────
        resp = client.get(f"/api/workbench/projects/{project_id}/messages")
        msgs = resp.get_json()["messages"]
        check("5. two persisted messages (user + brain)", len(msgs) == 2, msgs)

        # ── 6. Provider failure is shown honestly, not as success ───────
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: (
            None, "ConnectError: [Errno 111] connection refused"
        )
        resp = client.post(
            f"/api/workbench/projects/{project_id}/messages",
            json={"message": "Second question.", "request_id": "req-2"},
        )
        body = resp.get_json()
        check("6a. failed status surfaced (not completed)",
              body["brain_message"]["status"] == "failed", body["brain_message"])
        check("6b. content is not populated on failure",
              not body["brain_message"]["content"], body["brain_message"])
        check("6c. error text present", "connection refused" in body["brain_message"]["error"],
              body["brain_message"])

        # ── 7. Malformed input ───────────────────────────────────────────
        resp = client.post(
            f"/api/workbench/projects/{project_id}/messages",
            json={"message": "", "request_id": "req-3"},
        )
        check("7a. empty message -> 400", resp.status_code == 400, resp.status_code)

        resp = client.post(
            f"/api/workbench/projects/{project_id}/messages",
            json={"message": "no request id"},
        )
        check("7b. missing request_id -> 400", resp.status_code == 400, resp.status_code)

        resp = client.post("/api/workbench/projects", json={"name": ""})
        check("7c. empty project name -> 400", resp.status_code == 400, resp.status_code)

        resp = client.post(
            f"/api/workbench/projects/does-not-exist/messages",
            json={"message": "hi", "request_id": "req-4"},
        )
        check("7d. unknown project -> 404", resp.status_code == 404, resp.status_code)

        # ── 8. Duplicate-send behavior ───────────────────────────────────
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: ("first reply", None)
        resp1 = client.post(
            f"/api/workbench/projects/{project_id}/messages",
            json={"message": "duplicate test", "request_id": "req-dup"},
        )
        before = client.get(f"/api/workbench/projects/{project_id}/messages").get_json()["messages"]
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: (
            None, "should not be called"
        )
        resp2 = client.post(
            f"/api/workbench/projects/{project_id}/messages",
            json={"message": "duplicate test", "request_id": "req-dup"},
        )
        after = client.get(f"/api/workbench/projects/{project_id}/messages").get_json()["messages"]
        check("8a. duplicate resend flagged", resp2.get_json()["duplicate"] is True, resp2.get_json())
        check("8b. no new rows created on duplicate resend", len(before) == len(after),
              (len(before), len(after)))
        check("8c. duplicate resend returns original reply, not a fabricated one",
              resp2.get_json()["brain_message"]["content"] == "first reply",
              resp2.get_json())

        # ── 9. Interrupted state reconciliation ──────────────────────────
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO workbench_messages (project_id, role, content, status, request_id, created_at) "
            "VALUES (?, 'brain', NULL, 'pending', 'req-stale', datetime('now', '-1 hour'))",
            (project_id,),
        )
        conn.commit()
        conn.close()
        resp = client.get(f"/api/workbench/projects/{project_id}/messages")
        stale = [m for m in resp.get_json()["messages"] if m["status"] in ("pending", "interrupted")]
        check("9a. stale pending row reconciled to interrupted",
              len(stale) == 1 and stale[0]["status"] == "interrupted", stale)
        check("9b. interrupted row carries an honest explanation",
              bool(stale[0]["error"]), stale[0])

        # ── 10. No pipeline-start route is exposed by this blueprint ────
        route_paths = [r.rule for r in app.url_map.iter_rules()]
        check("10. no /start or /run route registered by workbench_bp",
              not any("start" in p or p.endswith("/run") for p in route_paths), route_paths)

        # ── 11. Optional direction note ──────────────────────────────────
        resp = client.patch(
            f"/api/workbench/projects/{project_id}",
            json={"direction_note": "Focus on the conversation flow first."},
        )
        check("11a. direction note saved -> 200", resp.status_code == 200, resp.status_code)
        check("11b. direction note round-trips",
              resp.get_json()["project"]["direction_note"] == "Focus on the conversation flow first.",
              resp.get_json())

    finally:
        workbench_app._call_brain_gateway = orig_gateway
        if orig_db_path_env is None:
            os.environ.pop("CIS_SPINE_PATH", None)
        else:
            os.environ["CIS_SPINE_PATH"] = orig_db_path_env
        import shutil
        shutil.rmtree(tmp_root, ignore_errors=True)

    for r in results:
        print(r)
    failed = [r for r in results if "FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
