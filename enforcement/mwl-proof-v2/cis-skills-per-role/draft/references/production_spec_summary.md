# Production Spec Summary (REV-2)

Condensed from `docs/SPEC_PRODUCTION_PIPELINE_RELAY.md` — 2026-07-08

## Key Design Decisions (made by expert, not Eric)

1. **One container, six profiles** — blast radius risk accepted (personal system, state survives crash)
2. **SQLite WAL with safeguards** — busy_timeout=5000, retry with backoff, append-only trajectory writes
3. **11C/11D dispatch_log as relay** — PENDING → INFLIGHT → SUCCESS. Kanban retired (ADR-013)
4. **workflow_runs as pipeline_state** — ADR-043's table is workflow_runs in practice
5. **asyncio + httpx for parallel calls** — not threads
6. **Brain and Verify wrap 11C/11D** — 11C/11D cover Draft→Review. Brain is entry, Verify is exit
7. **Verify works from clean checkout** — not Menter's workspace. Re-runs tests.
8. **Compensation on Verify FAIL** — git stash, Eric decides
9. **FINAL_JSON for all agent signals** — per ADR-SEED-012, not regex
10. **Trajectory retrieval wraps content as data** — clear delimiters, outcome filter, run_id exclusion

## Mandatory Pre-Discovery (§3.0)

Before ANY agent is dispatched, pipeline_relay.py runs:
1. Spine FTS5 search (knowledge_messages_fts)
2. Filesystem scan (search_files across docs/, data/drive_imports/, cis_kernel/, etc.)
3. Trajectory search (agent_trajectories WHERE outcome='success' AND run_id != current)
4. Web search (Brain and Draft only)
5. Results injected as `[PRE-DISCOVERY RESULTS]` prefix in agent prompt

This prevents agents from ignoring existing work on disk. The pipeline searches
FOR the agent — the agent can't be ignorant because context is provided before
it starts thinking.

## Dual-Review Pattern

Eric suggested: "you have deepseek and qwen at your disposal you might as well
use them for their differences to see what you may have missed."

How to do it:
1. Send the spec to Review1 (port 8643, qwen) via gateway HTTP call
2. Send the same spec to Review2 (port 8647, glm) in parallel
3. Both review independently — different training data, different blind spots
4. Synthesize: both-agree issues are blocking, unique catches are high priority
5. Update spec, incorporate all feedback, acknowledge reviewers

This caught 10+ blocking issues in the production spec that I missed alone.

## Error States (from dual-review feedback)

- `WAITING_FOR_HUMAN` — Brain emitted HUMAN_QUESTION, pipeline paused, 72h timeout
- `ESCALATED` — max rounds exceeded, run needs Eric intervention
- `VERIFY_FAILED` — Verify returned FAIL, Menter's changes git stashed
- `STALE` — HUMAN_QUESTION timeout exceeded (72h)
- `ERROR` — unexpected crash, state preserved in workflow_runs for recovery

## Container Multi-Profile Setup

Image: `cis-hermes:pipeline` (built from `enforcement/mwl-proof-v2/Dockerfile`)
- 6 profile configs at `/etc/hermes/profiles/{brain,draft,review1,review2,menter,verify}.yaml`
- Launch script: `/opt/cis-control/launch_profiles.sh` starts all 6 gateway processes
- Each profile has mandatory search instructions in personality prompt
- Per-role tool restrictions enforced by managed config + gate runner
- Verify terminal is an allowlist (git diff, git status, git log, pytest, ls, cat, grep) — NOT a blacklist

## Schema Migration 0015

File: `runtime/schema/migrations/0015_production_pipeline.sql`
- deliberation_rounds: added reviewer1_output, reviewer2_output, brain_output, verify_output, human_question, human_answer
- workflow_runs: added directive_hash
- New table: agent_trajectories (run_id, role, phase, input_text, output_text, feedback_text, outcome, config_version, marginal_utility)
- New FTS5: agent_trajectories_fts with triggers for sync
- Note: drafter_output already existed — do NOT re-add
- Note: intent_map, anti_patterns, functional_spec, reviewer_brief tables already existed
