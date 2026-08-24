# CIS Spec — POST /api/relay/run: Direct Draft-Gateway Run Endpoint

**Date:** 2026-08-22
**Status:** DRAFT (pre-review)
**Target file:** runtime/container_app.py
**Authority:** SPEC_PRODUCTION_PIPELINE_RELAY.md §6.4 (relay API family) + pipeline_run.py (proven gateway call pattern)
**Supersedes:** pipeline_run.py as the ad-hoc CLI path for single-shot drafts (CLI stays for debugging; the endpoint becomes the supported path)

---

## 1. What This Is

A synchronous HTTP endpoint on the pipeline container's Flask app (port 5000)
that takes a draft prompt, calls the Draft gateway directly (port 8645), and
writes the raw response to /workspace/cis/artifacts/<run_id>/draft.md.

Distinction from existing endpoints:

- POST /api/relay/start runs the FULL pipeline (Brain → Review → Draft → Eric Gate). Heavy, multi-round, stateful.
- POST /api/relay/run runs ONLY Draft. One call, one file on disk. For when Eric wants a draft right now without deliberation overhead.

---

## 2. Motivation

1. pipeline_run.py already proves the pattern works (draft → /workspace/cis/artifacts/<run_id>/draft.md), but it is a CLI script — not reachable from the control plane UI, Telegram, or external tooling.
2. The full relay has no "draft only" escape hatch. Every quick question currently costs a full pipeline round.
3. Downstream consumers (reviewer loops, artifact viewers) need a stable HTTP contract for "draft this and put it on disk".

---

## 3. Request Contract

```
POST /api/relay/run
Content-Type: application/json
Authorization: Bearer <CIS_PIPELINE_API_KEY>   (only if key is configured — same rule as the rest of api/relay.py)
```

Body:

| Field     | Type   | Required | Default | Notes |
|-----------|--------|----------|---------|-------|
| prompt    | string | YES      | —       | The draft prompt, sent as the user message to the gateway |
| run_id    | string | no       | generated | Must match ^[A-Za-z0-9_-]{1,64}$. Used verbatim as the artifact directory name |
| model     | string | no       | deepseek-v4-pro | Override for the gateway model field |
| timeout   | int    | no       | 1800 | Gateway timeout seconds, clamped to [1, 3600] |

Generated run_id format when omitted: "run-" + sha256(prompt).hexdigest()[:16]
(consistent with workflow_runs id prefix conventions in api/relay.py).

---

## 4. Response Contract

201 Created:

```json
{
  "run_id": "run-<hash16>",
  "artifact_path": "/workspace/cis/artifacts/run-<hash16>/draft.md",
  "draft_bytes": 8123,
  "model": "deepseek-v4-pro"
}
```

Error matrix:

| Status | Condition | Body |
|--------|-----------|------|
| 400 | prompt missing/empty, run_id fails the allowed charset, timeout out of range | {"error": "..."} |
| 401 | Bearer token mismatch (only when CIS_PIPELINE_API_KEY set) | {"error": "Unauthorized", ...} — same shape as api/relay.py _check_auth |
| 502 | Draft gateway unreachable or non-200 from gateway | {"error": "Draft gateway failed", "detail": "<underlying error>"} |
| 500 | CIS_DRAFT_API_KEY unset, artifact dir unwritable, or unexpected exception | {"error": "..."} |

---

## 5. Gateway Call (Layer 3)

Canonical pattern is pipeline_run.py call() — reuse it, do not invent a new one:

```
POST http://127.0.0.1:8645/v1/chat/completions
Authorization: Bearer <CIS_DRAFT_API_KEY>
{"model": "deepseek-v4-pro",
 "messages": [{"role": "user", "content": "<prompt>"}]}
```

Response extraction: body["choices"][0]["message"]["content"] (OpenAI-compatible).

Port source: read from abstraction/dispatch.py PROFILES["draft"]["port"] — that file
is the declared single source of truth for port mapping (DEV-PIVOT-05 §5). Fall back
to the existing _GATEWAY_PORTS["Draft"] constant in container_app.py if the import
fails, so the endpoint degrades to the same behavior as the rest of container_app.py.

API key: os.environ["CIS_DRAFT_API_KEY"] — same env var pipeline_run.py uses.
Raise 500 with a clear message if unset (do NOT fail silently with an empty token).

Timeout: urllib.request.urlopen(..., timeout=<clamped request value>).

---

## 6. Artifact Write

```
out = pathlib.Path("/workspace/cis/artifacts") / run_id
out.mkdir(parents=True, exist_ok=True)
(out / "draft.md").write_text(content)
```

Requirements:

1. SANITIZE run_id BEFORE building the path. Regex ^[A-Za-z0-9_-]{1,64}$ or reject with 400.
   This is the path-traversal guard — run_id comes from the client and lands in a filesystem path.
2. Write draft.md with UTF-8, no transformation of the gateway response (raw draft, verbatim).
3. exist_ok=True is acceptable: re-running the same run_id overwrites draft.md (last write wins, matches pipeline_run.py).
4. No metadata sidecar in v1. Consumers that need provenance use the response JSON or the spine DB.

---

## 7. Implementation Notes

- Where: new @app.route("/api/relay/run", methods=["POST"]) in runtime/container_app.py,
  placed in the relay section next to the existing /api/relay/system/* handlers. The relay_bp
  blueprint (runtime/api/relay.py) already owns /api/relay/start etc.; this endpoint lives in
  container_app.py per the request, keeping the minimal-app layout intact. If it later grows
  (retry, async), it should be moved into relay_bp.
- Auth: import and call _check_auth from api.relay to keep the token rule identical across the family.
- Synchronous by design: the request blocks until Draft responds or times out. This is the
  accepted tradeoff for a single-shot endpoint; document it in the docstring. If 1800s blockages
  become a problem in the UI, v2 adds a background thread + poll, mirroring _run_pipeline_background.
- No spine DB writes in v1. The full relay remains the record of record; /run is a convenience path.
  (Flagged as an open question below.)
- Concurrency: no shared state; each request is independent. No locking needed beyond mkdir
  being idempotent.

---

## 8. Verification (acceptance tests)

1. curl with valid key + prompt → 201, file exists at the returned artifact_path, content non-empty.
2. curl without prompt → 400.
3. curl with run_id "..%2F..%2Fescape" → 400 (sanitizer rejects).
4. curl with run_id "my-run-1" → file at /workspace/cis/artifacts/my-run-1/draft.md.
5. Stop/block gateway 8645 (e.g. wrong port override in test) → 502 with detail.
6. Unset CIS_DRAFT_API_KEY → 500 with explicit message.
7. Re-run same prompt → idempotent path (same run_id, file overwritten), 201 both times.
8. Existing relay endpoints unaffected: /api/relay/start and GET /api/relay/<run_id> still behave as before.

---

## 9. Open Questions (for reviewers)

1. Should /run record anything to workflow_runs / workflow_run_artifacts so the knowledge
   surface can index these drafts? (v1: no. Cost: these drafts are invisible to MCP search.)
2. Is 1800s sync acceptable to the caller, or does v1 need an async variant immediately?
3. Should prompt be named "topic" for consistency with /api/relay/start's "intent" field?
   (v1: "prompt" — it is a raw gateway message, not an intent statement.)
4. Overwrite semantics: OK to overwrite an existing run_id's draft.md silently, or should a
   second call with the same run_id return 409?
