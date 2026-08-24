# CIS Pipeline — State as of 2026-08-22

## Core finding
pipeline_relay.py (runtime/abstraction/, 3577 lines) is a
complete governed orchestrator. It was never broken. It
needs the Hermes venv interpreter, not system python3:
  /usr/local/lib/hermes-agent/venv/bin/python

## Invocation
  --intent "text"   start a run
  --status <id>     check status
  --resume <id>     continue a run
Launch detached with docker exec -d and redirect to a log.
The docker exec client times out at 600s and orphans the
process; the run itself is fine.

## Confirmed working 2026-08-22
- 6 gateways healthy: brain 8644, draft 8645, review1 8643,
  review2 8647, menter 8646, verify 8648
- Full cycle ran: pre-discovery, brain, draft, dual review,
  consensus, ERIC_GATE
- Gate approval via HTTP:
  POST localhost:5000/api/relay/<run_id>/gate
  body: {"decision":"APPROVE","rationale":"..."}
- Run run-578251939d8bece7-1787416463 reached PATTERN_CATALOG
  then the process died with the exec client. Resumable.

## Fixed this session
- api/adapter.py sent gateway requests with no Authorization
  header. Source of all "rejected invalid API key" 401s in
  brain.log and menter.log. Patched to resolve
  CIS_<ROLE>_API_KEY and send Bearer. Backup at adapter.py.bak. NOT YET LIVE: Flask PID 71 needs restart.
- runtime/pipeline_run.py: restored main guard, timeout
  1800 to 300 to match AGENT_TIMEOUTS.

## Known defect (confirmed, unfixed)
_notify_eric_gate reads CIS_TELEGRAM_BOT_TOKEN and
CIS_TELEGRAM_CHAT_ID. Container has CIS_TG_*_TOKEN and
CIS_TG_HOME_CHANNEL. Names never match, so gate notification
silently no-ops and runs sit at ERIC_GATE until the 72h
timeout flips them to ESCALATED. This killed runs on
2026-07-16 and 2026-07-24.
FIX: alias the two names in entrypoint.sh, restart container.

## Also unmounted
POST /api/adapter/dispatch returns 404 - blueprint exists in
api/adapter.py but is not registered in container_app.py.
Same class: /api/relay/run is likewise unrouted.

## Ruled out (do not re-investigate)
- Read-only mount blocking writes
- Root vs container env var mismatch on gateway keys
- PROFILES role-key casing mismatch (keys are correct)
- Missing httpx (wrong interpreter, not a missing dep)
- pipeline_relay.py absent (it is in abstraction/)
- Host processes calling gateways (only 5000 is published)
- rails/configs/cis_fast/actions.py (uses ss, targets 8642)

## Already built, do not rebuild
api/reconciliation.py, api/collab_rounds.py, api/router.py,
api/advisor.py, runtime/orchestrator.py, cis_verify.py,
cis_review.py, queue_worker.py

## Retrospective finding
226 cards, 32 in inbox. card_runner.py reports 2 DONE,
30 TODO. assessment.db fabrications: 29 sampled claims,
2 verified. Repeat asks were caused by fabricated completion
reports, not unclear specs. Three separate multi-month
blockers were all env var name mismatches.

## Next session
1. Restart Flask PID 71 so the adapter auth fix goes live
2. Alias CIS_TELEGRAM_* in entrypoint.sh, restart container
3. Resume run-578251939d8bece7-1787416463 detached, watch it
   past ERIC_GATE through menter and verify
