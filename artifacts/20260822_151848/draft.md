Spec written to /workspace/cis/docs/SPEC_RELAY_RUN_ENDPOINT.md.

Key decisions grounded in the existing codebase:

- Gateway call follows the proven pipeline_run.py pattern: POST http://127.0.0.1:8645/v1/chat/completions with Bearer CIS_DRAFT_API_KEY, model deepseek-v4-pro, extracting choices[0].message.content.
- Port is read from abstraction/dispatch.py PROFILES["draft"] as the canonical source, with _GATEWAY_PORTS as fallback.
- run_id is client-supplied or generated as run-<sha256(prompt)[:16]>, and it's sanitized against ^[A-Za-z0-9_-]{1,64}$ before touching the filesystem — that's the path-traversal guard since run_id lands in the artifact path.
- Auth reuses the existing _check_auth rule from api/relay.py so the token behavior is identical across the relay family.
- Error matrix: 400 validation, 401 token, 502 gateway failure, 500 missing key/unwritable dir.
- Synchronous by design, documented as the accepted tradeoff for a single-shot endpoint; async variant flagged as a v2 question.
- Four open questions at the end for reviewers: spine DB indexing of these drafts, sync-vs-async, field naming (prompt vs intent), and overwrite semantics (silent overwrite vs 409).

One caveat: I tried routing this through the CIS adapter first, but the dispatch endpoint returned 404, so I wrote the spec directly. If you want, I can push it through the Drafter/dual-review pipeline later when the adapter is back up — or just implement the endpoint now from this spec.