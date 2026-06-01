# Open Questions — Hermes Harness
Last updated: 2026-05-18

## OQ-001 — Hermes Gateway API timeout
The send-to-hermes endpoint times out on complex stenographer synthesis requests.
This is no longer a blocking issue for the wizard since capture-exchange does not
call Hermes Gateway. The timeout remains relevant for future post-capture synthesis
jobs (HHR-014B).
Status: MITIGATED — wizard no longer depends on synchronous Hermes synthesis.
  Resolution target: async synthesis jobs with polling (HHR-014B).

## OQ-002 — Flask API_SERVER_KEY startup
Flask previously required manual env injection of API_SERVER_KEY.
Fixed: cis-flask.service uses EnvironmentFile=/home/eric/.config/cis-flask.env.
Key format corrected from `export KEY=value` to `KEY=value` (systemd syntax).
Verified: /proc/<pid>/environ shows API_SERVER_KEY loaded at startup.
Status: RESOLVED — HHR-014A.
Evidence: proc environ grep, systemctl cat cis-flask.service, live 401/200 auth test.

## OQ-003 — VDB pipeline rebuild
Previous hybrid SQLite/ChromaDB attempt produced low-signal output.
Root cause: extraction operated on processed summaries not raw source text.
Correct approach identified: chunk raw collab_session_messages.content with message_index as citation anchor.
Status: OPEN — not yet started, depends on capture-first flow being stable (HHR-014E/G done).

## OQ-004 — Project Context Pack update trigger
What constitutes a "significant task" that triggers a pack update?
Needs a clear rule so Hermes knows when to update without over-updating.
Status: OPEN — needs definition.

## OQ-005 — Hermes TUI copy/paste
TUI copy/paste via Ctrl+Shift+C does not work in current setup.
/paste slash command may be the correct path.
Status: OPEN — not investigated.

## OQ-006 — Self-referential Hermes API deadlock during testing
When Hermes (the agent) calls its own Gateway API, the API spawns a new agent
session that competes for the same agent process, causing deadlock/timeout.
This is a testing artifact — does not affect production where the API is called
by Flask or external clients. Still worth noting for test design.
Status: OBSERVED — testing artifact, not a production bug.

## OQ-007 — Synthesis Step Fortification
Status: DESIGNED, NOT YET BUILT.

Approved design (ChatGPT + Claude consensus 2026-05-18):

Architecture: Async job + polling (Option B)
Later additions: Retry from stored packet (Option C), Streaming UX (Option A)

Build sequence:
HHR-014B — Recoverable synthesis jobs
- New table: collab_synthesis_jobs
  Fields: id, round_id, status, request_payload, hermes_response,
  session_path, import_id, error, created_at, started_at, completed_at, updated_at
- POST /api/collab/rounds/<id>/synthesis-jobs — creates job, starts background worker, returns job_id immediately
- GET /api/collab/synthesis-jobs/<job_id> — returns status: queued/running/completed/failed/recoverable
- POST /api/collab/synthesis-jobs/<job_id>/retry — retries from stored payload
- React polls every 3 seconds until completed or failed
- On complete: show synthesis, confirm session import
- On failed: show Retry button

HHR-014C — UX improvements
- Progress indicator with elapsed time
- "Still running..." status message
- Retry button on failure
- Streaming tokens (optional, add last)

Core requirements per ChatGPT:
- Persist packet BEFORE sending to Hermes
- Return job_id immediately to React
- Background worker calls Hermes Gateway
- Worker stores response, detects session_api JSON, runs import
- Links import_id + session_id to job and round_id
- All retry attempts linked to same round_id

Note: Since HHR-014E decoupled capture from synthesis, HHR-014B/C can be built
independently without blocking the wizard's primary save path.

## OQ-008 — (reserved)

## OQ-009 — Verify hermes-gateway.service HERMES_HOME target
Status: OPEN
Note: Phase 3B Step 2 inspection reported hermes-gateway.service using
`HERMES_HOME=/home/eric/.hermes-r1` in its systemd unit file, while the
Prime gateway profile is at `/home/eric/.hermes`. Confirm later whether
this is a reporting artifact, intentional service routing (e.g., Prime
gateway now uses R1 home for a reason), or a regression from the Phase 2
HERMES_HOME repair that should be reverted.
Discovered: 2026-05-29, Phase 3B Step 2 inspection.

## OQ-010 — Clarify generator source hierarchy vs Project Context Pack
Status: OPEN
Note: Phase 4A design inspection found generate_context_briefing.py reads
docs/CIS_CURRENT_STATE.md, docs/CIS_CONTEXT_CONTRACT.md,
docs/CIS_CORE_BOUNDARY.md, seed_intent_corpus files, and latest
session_handoffs/HANDOFF_*.md, but does NOT read maintained
PROJECT_CONTEXT_PACK/01_CURRENT_STATE.md, 05_NEXT_ACTIONS.md, or
07_RECENT_HANDOFF.md. Resolve later whether this is an intentional
source hierarchy (generator reads raw canonical docs, not the curated
pack) or a divergence that needs alignment.
Discovered: 2026-05-29, Phase 4A design inspection.
