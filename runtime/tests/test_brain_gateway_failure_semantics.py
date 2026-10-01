"""
test_brain_gateway_failure_semantics.py — WB1-D16.

The Brain/Hermes gateway answers HTTP 200 even when upstream generation
FAILED, and puts the provider's error text where a model answer would go.
Before this suite, workbench_app._call_brain_gateway() checked only the HTTP
status and that content was nonempty, so a provider outage was persisted as a
COMPLETED role='brain' conversational turn whose content was the provider's
error string — the conversation surface reported someone else's failure as
Braingate's own answer.

These tests pin the boundary closed in both directions, at two levels:

  * the gateway call itself (real _call_brain_gateway, httpx stubbed), and
  * the activated Braingate conversation surface end-to-end
    (braingate_conversation_bp over HTTP against a real temp spine), where
    the invariant that actually matters is a DATABASE invariant:

        an upstream generation failure must never create a completed
        role='brain' message containing the provider error.

The failure envelope used below is the one OBSERVED LIVE on 2026-10-01
against the real gateway at 127.0.0.1:8644 with an invalid upstream provider
credential — HTTP 200, finish_reason='error', hermes.failed=true,
hermes.completed=false, hermes.error_code='agent_error' — not an invented
shape. No paid model call happens anywhere in this file: httpx is stubbed.

Run: python3 runtime/tests/test_brain_gateway_failure_semantics.py
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Auth is fail-CLOSED (runtime/workbench_auth.py): an unset CIS_PIPELINE_API_KEY
# denies every request with 503 rather than granting anonymous access. A real
# key is configured and presented below, exactly as a real caller would.
TEST_API_KEY = "test-workbench-key"
os.environ["CIS_PIPELINE_API_KEY"] = TEST_API_KEY

REPO_SRC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MIGRATIONS_DIR = os.path.join(REPO_SRC, "runtime", "schema", "migrations")
MIGRATION_0035 = os.path.join(MIGRATIONS_DIR, "0035_workbench.sql")
MIGRATION_0038 = os.path.join(MIGRATIONS_DIR, "0038_workbench_action_proposals.sql")

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
"""

# ── The exact live failure envelope (2026-10-01, invalid provider credential).
# The provider's own already-masked key suffix is reproduced verbatim because
# the point of the test is that this entire string must NEVER become a brain
# message's content. No real secret value appears here or in the codebase.
PROVIDER_ERROR_TEXT = (
    "HTTP 401: Authentication Fails, Your api key: ****0000 is invalid "
    "(request_id: 00000000-0000-0000-0000-000000000000)"
)
LIVE_FAILURE_ENVELOPE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "created": 1790874091,
    "model": "agent",
    "choices": [{
        "index": 0,
        "message": {"role": "assistant", "content": PROVIDER_ERROR_TEXT},
        "finish_reason": "error",
    }],
    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    "hermes": {
        "completed": False,
        "partial": False,
        "failed": True,
        "error": PROVIDER_ERROR_TEXT,
        "error_code": "agent_error",
    },
}

GOOD_ANSWER = "Braingate's real answer to that question."
SUCCESS_ENVELOPE = {
    "id": "chatcmpl-test-ok",
    "object": "chat.completion",
    "model": "agent",
    "choices": [{
        "index": 0,
        "message": {"role": "assistant", "content": GOOD_ANSWER},
        "finish_reason": "stop",
    }],
    "usage": {"prompt_tokens": 10, "completion_tokens": 7, "total_tokens": 17},
    "hermes": {"completed": True, "partial": False, "failed": False,
               "error": None, "error_code": None},
}


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, raise_exc=None, bad_json=False):
        self.status_code = status_code
        self._payload = payload
        self._raise_exc = raise_exc
        self._bad_json = bad_json

    def raise_for_status(self):
        if self._raise_exc is not None:
            raise self._raise_exc

    def json(self):
        if self._bad_json:
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return self._payload


class _FakeHttpx:
    """Stands in for the httpx module inside workbench_app. Records every call
    so a test can prove a second model call did NOT happen on a replay."""

    def __init__(self):
        self.calls = []
        self.queue = []

    def post(self, url, json=None, headers=None, timeout=None):  # noqa: A002
        self.calls.append({"url": url, "json": json})
        if not self.queue:
            raise AssertionError("gateway called more times than the test queued responses")
        nxt = self.queue.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


def run():
    results = []

    def check(label, cond, detail=""):
        results.append((label, bool(cond)))
        print(f"{'PASS' if cond else 'FAIL'}  {label}" + (f"  -- {detail}" if not cond else ""))

    tmp_root = tempfile.mkdtemp(prefix="brain_gateway_failure_test_")
    db_path = os.path.join(tmp_root, "test_spine.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(KNOWLEDGE_MESSAGES_SCHEMA)
    for mig in (MIGRATION_0035, MIGRATION_0038):
        with open(mig) as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()

    orig_db_path_env = os.environ.get("CIS_SPINE_PATH")
    os.environ["CIS_SPINE_PATH"] = db_path

    import workbench_app  # noqa: E402
    import braingate_conversation  # noqa: E402

    workbench_app.DB_PATH = db_path
    orig_httpx = workbench_app.httpx
    fake = _FakeHttpx()
    workbench_app.httpx = fake

    from flask import Flask
    # The ACTIVATED surface, not workbench_bp: this is what a signed-in human
    # actually reaches at this stage.
    app = Flask(__name__)
    app.register_blueprint(braingate_conversation.braingate_conversation_bp)
    client = app.test_client()
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_API_KEY}"

    def new_project(name):
        r = client.post("/api/workbench/projects", json={"name": name})
        assert r.status_code == 201, r.get_json()
        return r.get_json()["project"]["id"]

    def send(project_id, message, request_id):
        return client.post(
            f"/api/workbench/projects/{project_id}/messages",
            json={"message": message, "request_id": request_id, "mode": "chat"},
        )

    def brain_rows(project_id):
        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in c.execute(
                "SELECT * FROM workbench_messages WHERE project_id = ? AND role = 'brain' "
                "ORDER BY id", (project_id,)).fetchall()]
        finally:
            c.close()

    def user_rows(project_id):
        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in c.execute(
                "SELECT * FROM workbench_messages WHERE project_id = ? AND role = 'user' "
                "ORDER BY id", (project_id,)).fetchall()]
        finally:
            c.close()

    try:
        # ══ 1. UNIT LEVEL — the envelope classifier itself ══════════════
        #
        # Positive failure signals only. Absence of an indicator must never
        # read as failure, or a plain OpenAI-compatible gateway (no `hermes`
        # key) would be broken by this fix.
        f = workbench_app._brain_envelope_failure
        check("1a. live failure envelope is classified as a failure",
              f(LIVE_FAILURE_ENVELOPE) is not None)
        check("1b. success envelope is classified as a success",
              f(SUCCESS_ENVELOPE) is None, f(SUCCESS_ENVELOPE))
        check("1c. hermes.failed=true alone is a failure",
              f({"choices": [{"message": {"content": "x"}, "finish_reason": "stop"}],
                 "hermes": {"failed": True}}) is not None)
        check("1d. hermes.completed=false alone is a failure",
              f({"choices": [{"message": {"content": "x"}, "finish_reason": "stop"}],
                 "hermes": {"completed": False}}) is not None)
        check("1e. finish_reason='error' alone is a failure",
              f({"choices": [{"message": {"content": "x"}, "finish_reason": "error"}]}) is not None)
        check("1f. no hermes block at all + finish_reason='stop' is a SUCCESS "
              "(a plain OpenAI-compatible gateway must keep working)",
              f({"choices": [{"message": {"content": "x"}, "finish_reason": "stop"}]}) is None)
        check("1g. finish_reason='length' is a SUCCESS — a truncated but real "
              "generation is not an error",
              f({"choices": [{"message": {"content": "x"}, "finish_reason": "length"}],
                 "hermes": {"completed": True, "failed": False}}) is None)
        check("1h. a non-object JSON body is a failure, not a crash",
              f(["not", "an", "object"]) is not None)
        err = f(LIVE_FAILURE_ENVELOPE)
        check("1i. the failure names every indicator it saw, coherently, as ONE error",
              all(k in err for k in ("hermes.failed=true", "hermes.completed=false",
                                     "finish_reason='error'")), err)
        check("1j. the failure carries the gateway's stable error_code",
              "agent_error" in err, err)

        # The boundary must read the gateway's machine-readable fields, not
        # provider error PROSE. Prose is the upstream vendor's, varies per
        # provider and is unversioned; a string-matching boundary silently
        # reopens this hole the first time a provider rewords a message.
        check("1k. provider error PROSE with no failure indicator is NOT "
              "treated as failure by prose-matching (fields are the contract)",
              f({"choices": [{"message": {"content": PROVIDER_ERROR_TEXT},
                              "finish_reason": "stop"}],
                 "hermes": {"completed": True, "failed": False}}) is None)

        # ══ 2. GATEWAY CALL LEVEL — real _call_brain_gateway, httpx stubbed ══
        fake.queue = [_FakeResponse(payload=SUCCESS_ENVELOPE)]
        content, error = workbench_app._call_brain_gateway([{"role": "user", "content": "hi"}])
        check("2a. successful envelope -> content returned, no error",
              content == GOOD_ANSWER and error is None, (content, error))

        fake.queue = [_FakeResponse(payload=LIVE_FAILURE_ENVELOPE)]
        content, error = workbench_app._call_brain_gateway([{"role": "user", "content": "hi"}])
        check("2b. HTTP-200 failure envelope -> error returned and content is None "
              "(the provider error string is NOT returned as an answer)",
              content is None and error is not None, (content, error))
        check("2c. the provider error text is not mistaken for an answer",
              content is None, content)

        fake.queue = [_FakeResponse(raise_exc=RuntimeError("Server error '502 Bad Gateway'"))]
        content, error = workbench_app._call_brain_gateway([{"role": "user", "content": "hi"}])
        check("2d. HTTP transport/provider error -> honest error",
              content is None and error is not None and "502" in error, (content, error))

        fake.queue = [_FakeResponse(bad_json=True)]
        content, error = workbench_app._call_brain_gateway([{"role": "user", "content": "hi"}])
        check("2e. malformed (non-JSON) upstream body -> honest failure",
              content is None and error is not None, (content, error))

        fake.queue = [_FakeResponse(payload={"choices": [], "hermes": {"completed": True}})]
        content, error = workbench_app._call_brain_gateway([{"role": "user", "content": "hi"}])
        check("2f. empty choices list -> honest failure, not a crash and not a success",
              content is None and error is not None, (content, error))

        fake.queue = [_FakeResponse(payload={
            "choices": [{"message": {"content": ""}, "finish_reason": "stop"}],
            "hermes": {"completed": True, "failed": False}})]
        content, error = workbench_app._call_brain_gateway([{"role": "user", "content": "hi"}])
        check("2g. empty content with a success envelope -> honest failure",
              content is None and error is not None, (content, error))

        # ══ 3. SURFACE LEVEL — normal successful Brain response ═════════
        p1 = new_project("D16 scenario 1 (success)")
        fake.queue = [_FakeResponse(payload=SUCCESS_ENVELOPE)]
        resp = send(p1, "what is the state of the pipeline?", "d16-success-1")
        body = resp.get_json()
        check("3a. successful send -> HTTP 200", resp.status_code == 200, resp.status_code)
        check("3b. brain_message is completed with the model's real content",
              body["brain_message"]["status"] == "completed"
              and body["brain_message"]["content"] == GOOD_ANSWER, body["brain_message"])
        rows1 = brain_rows(p1)
        check("3c. exactly one brain row, persisted normally",
              len(rows1) == 1 and rows1[0]["status"] == "completed"
              and rows1[0]["content"] == GOOD_ANSWER and rows1[0]["error"] is None, rows1)

        # ══ 4. SURFACE LEVEL — HTTP transport/provider error ════════════
        p2 = new_project("D16 scenario 2 (transport error)")
        fake.queue = [_FakeResponse(raise_exc=RuntimeError("Server error '502 Bad Gateway'"))]
        resp = send(p2, "will this fail honestly?", "d16-transport-1")
        body = resp.get_json()
        check("4a. transport error -> brain_message failed with an error, no content",
              body["brain_message"]["status"] == "failed"
              and body["brain_message"]["content"] is None
              and body["brain_message"]["error"], body["brain_message"])
        rows2 = brain_rows(p2)
        check("4b. NO successful brain turn exists for a transport failure",
              len(rows2) == 1 and rows2[0]["status"] == "failed"
              and rows2[0]["content"] is None, rows2)

        # ══ 5. SURFACE LEVEL — HTTP-200 envelope, hermes.failed=true ════
        # This is the WB1-D16 regression itself, end to end.
        p3 = new_project("D16 scenario 3 (hermes.failed envelope)")
        fake.queue = [_FakeResponse(payload=LIVE_FAILURE_ENVELOPE)]
        resp = send(p3, "the credential is invalid upstream", "d16-envelope-1")
        body = resp.get_json()
        check("5a. HTTP-200 failure envelope -> brain_message is FAILED, not completed",
              body["brain_message"]["status"] == "failed", body["brain_message"])
        check("5b. the provider error string is NOT the brain message's content",
              body["brain_message"]["content"] is None, body["brain_message"])
        check("5c. an honest application error is exposed to the caller",
              bool(body["brain_message"]["error"]), body["brain_message"])
        rows3 = brain_rows(p3)
        check("5d. DB INVARIANT: no completed role='brain' row exists for a failed "
              "upstream generation",
              not any(r["status"] == "completed" for r in rows3), rows3)
        check("5e. DB INVARIANT: the provider error string is persisted in `error`, "
              "never in any brain row's `content`",
              all(r["content"] is None for r in rows3)
              and any(PROVIDER_ERROR_TEXT in (r["error"] or "") for r in rows3), rows3)
        check("5f. the user's own submitted message is still preserved",
              len(user_rows(p3)) == 1
              and user_rows(p3)[0]["content"] == "the credential is invalid upstream"
              and user_rows(p3)[0]["status"] == "completed", user_rows(p3))
        check("5g. the conversation is not left showing work still in flight",
              not any(r["status"] == "pending" for r in rows3), rows3)

        # ══ 6. SURFACE LEVEL — HTTP-200, finish_reason='error' only ═════
        # A gateway that reports the terminal state but omits the hermes
        # block must still fail closed.
        p4 = new_project("D16 scenario 4 (finish_reason only)")
        fake.queue = [_FakeResponse(payload={
            "choices": [{"index": 0,
                         "message": {"role": "assistant", "content": PROVIDER_ERROR_TEXT},
                         "finish_reason": "error"}],
            "usage": {"total_tokens": 0}})]
        resp = send(p4, "finish reason error only", "d16-finishreason-1")
        body = resp.get_json()
        check("6a. finish_reason='error' with no hermes block -> failed, honest error",
              body["brain_message"]["status"] == "failed"
              and body["brain_message"]["content"] is None
              and body["brain_message"]["error"], body["brain_message"])
        check("6b. DB INVARIANT: no completed brain turn, and the error text never "
              "becomes content",
              all(r["status"] != "completed" and r["content"] is None
                  for r in brain_rows(p4)), brain_rows(p4))

        # ══ 7. SURFACE LEVEL — empty/malformed upstream response ════════
        p5 = new_project("D16 scenario 5 (malformed)")
        fake.queue = [_FakeResponse(bad_json=True)]
        resp = send(p5, "malformed upstream", "d16-malformed-1")
        check("7a. malformed upstream body -> honest failure, no completed brain turn",
              resp.get_json()["brain_message"]["status"] == "failed"
              and all(r["status"] != "completed" for r in brain_rows(p5)),
              resp.get_json()["brain_message"])

        p6 = new_project("D16 scenario 6 (empty content)")
        fake.queue = [_FakeResponse(payload={
            "choices": [{"message": {"role": "assistant", "content": ""},
                         "finish_reason": "stop"}],
            "hermes": {"completed": True, "partial": False, "failed": False}})]
        resp = send(p6, "empty upstream", "d16-empty-1")
        check("7b. empty upstream content -> honest failure, no completed brain turn",
              resp.get_json()["brain_message"]["status"] == "failed"
              and all(r["status"] != "completed" for r in brain_rows(p6)),
              resp.get_json()["brain_message"])

        # ══ 8. Duplicate request replay AFTER a failed model attempt ════
        # The existing explicit request-id semantics: the same request_id
        # resolves to the SAME rows and makes NO second model call. It must
        # not invent a success, and it must not retry behind Eric's back.
        calls_before = len(fake.calls)
        fake.queue = []  # any gateway call here raises -> proves no second call
        resp = send(p3, "the credential is invalid upstream", "d16-envelope-1")
        body = resp.get_json()
        check("8a. replay of a failed request is reported as a duplicate",
              body["duplicate"] is True, body)
        check("8b. the replay makes NO second model call",
              len(fake.calls) == calls_before, (calls_before, len(fake.calls)))
        check("8c. the replay returns the SAME failed brain turn — no invented success",
              body["brain_message"]["status"] == "failed"
              and body["brain_message"]["content"] is None
              and body["brain_message"]["id"] == rows3[0]["id"], body["brain_message"])
        check("8d. the replay created no additional brain row",
              len(brain_rows(p3)) == len(rows3), brain_rows(p3))
        check("8e. the replay created no additional user row",
              len(user_rows(p3)) == 1, user_rows(p3))

        # ══ 9. No fabrication, no silent provider substitution ══════════
        # Every gateway call this suite made went to the ONE configured Brain
        # gateway URL. A fix that quietly failed over to another provider to
        # make conversation "work" would show up as a second distinct URL.
        urls = {c["url"] for c in fake.calls}
        check("9a. every call went to exactly one configured gateway URL — no "
              "silent fallback to another provider",
              urls == {workbench_app.BRAIN_GATEWAY_URL}, urls)

    finally:
        workbench_app.httpx = orig_httpx
        if orig_db_path_env is None:
            os.environ.pop("CIS_SPINE_PATH", None)
        else:
            os.environ["CIS_SPINE_PATH"] = orig_db_path_env
        shutil.rmtree(tmp_root, ignore_errors=True)

    failed = [l for l, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
