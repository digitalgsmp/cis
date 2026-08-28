---
name: cis-pipeline-architecture
description: "Design and build the CIS multi-agent pipeline: three-layer architecture, agent relay (Brain→Review→Draft→Review→Menter→Verify), MATM transactive memory, intent provenance + drift detection, spec-before-build workflow."
---

# CIS Pipeline Architecture

## When to Use
- Designing, building, or modifying the CIS multi-agent pipeline
- Wiring agent relay between Hermes gateways
- Extending the spine DB for trajectory recording
- Adding/changing agent roles in the pipeline
- Any work that touches the three-layer architecture (UI, Abstraction Layer, Hermes Backend)

## The Three Layers

```
Layer 1: UI / Control Plane (port 5000) — what Eric sees and controls
Layer 2: Abstraction Layer — adapter between UI and Hermes (dispatch.py, pipeline_relay.py, router.py)
Layer 3: Hermes Backend — 6 gateways (8643-8648) in Docker containers with gate enforcement
```

The abstraction layer exists so Hermes can be updated without rewriting the app.
When Hermes changes ports, APIs, or config format, only the abstraction layer changes.

## Container Enforcement Principle

Eric's direct correction: "the container is meant to ensure it cooperates. why does it have an option."

The container must **ENFORCE** output contracts, not just detect violations. When an agent produces output without the required `FINAL_JSON` format, the container issues ONE repair prompt (re-dispatch with format instructions), then escalates if still non-compliant. Agents do not have the *option* to skip the format — the container re-prompts them.

This is implemented via `_enforce_output_contract()` in `pipeline_relay.py` (commit c63a5aa, 2026-07-11). The helper is wired into all 7 pipeline phases:

| Phase | Role | Required Statuses |
|-------|------|-------------------|
| Brain | brain | READY, NEEDS_CLARIFICATION |
| Intent Review | review1, review2 | CONSENSUS_REACHED, OBJECTIONS, ESCALATE |
| Draft | draft | PROPOSAL_READY, REVISION_READY |
| Proposal Review | review1, review2 | CONSENSUS_REACHED, OBJECTIONS, ESCALATE |
| Pattern Catalog | brain | READY |
| Code Review (Menter) | menter | CHUNK_READY |
| Code Review (Consensus) | review1 | APPROVED, CHANGES_REQUESTED |
| Menter Execution | menter | CONSENSUS_REACHED, DONE, COMPLETE |
| Verification | verify | PASS, FAIL |

**Guardrail blocks escalate immediately** — a guardrail block is a policy violation (e.g., secrets detected, forbidden write), not a format issue. No repair prompt for guardrail blocks.

**Format violations get one repair prompt, then escalate.** Per ADR-SEED-012: "If FINAL_JSON is missing or malformed, orchestrator issues one repair prompt then falls back to constrained text-scanning."

## The Pipeline Relay

```
Eric's raw intent
    ↓
  BRAIN (8644) — explores intent, produces structured understanding
    ↓                   ↑ can emit HUMAN_QUESTION → Eric answers → continues
  REVIEW1 (8643) ─┐
                  ├─ parallel — both check Brain's understanding
  REVIEW2 (8647) ─┘
    ↓                    ↓
  consensus → DRAFT      objections → back to BRAIN (max 2 rounds, then escalate)
    ↓
  DRAFT (8645) — writes spec using Brain's clarified intent + reviewer feedback
    ↓
  REVIEW1 (8643) ─┐
                  ├─ parallel — both critique the proposal
  REVIEW2 (8647) ─┘
    ↓                    ↓
  consensus → ERIC GATE   objections → back to DRAFT (max 3 rounds, then escalate)
    ↓
  ERIC GATE — Eric approves/rejects/revises
    ↓
  PATTERN_CATALOG — Brain reads codebase, identifies patterns + completion criteria,
                    lists files Menter will create/modify. Catalog saved to disk.
    ↓
  CODE_REVIEW_GATE — per file (chunk):
    Menter builds (with universal rules in prompt) → L1 universal checks
    → Reviewer A (first pass, fresh eyes)
    → Reviewer B (second pass, sees A's output, builds on it)
    → Reviewer A consensus (sees B's output, delivers verdict)
    → APPROVED → incorporate, CHANGES_REQUESTED → revise (max 3)
    ↓
  VERIFICATION (8648) — independent evidence check (NO shared context with Menter)
    ↓
  PASS / FAIL → Eric
```

### Role names are model-agnostic
- Brain (8644), Draft (8645), Review1 (8643), Review2 (8647), Menter (8646), Verify (8648)
- Source of truth: `config/agents_static.yaml` and `enforcement/profiles/*/config.yaml`
- Never use model names (DeepSeek, Qwen, GLM) in identity, descriptions, or routing
- See `container-gate-wiring` skill for enforcement details

## MATM — Transactive Memory (Shared Brain)

Based on MATM paper (arXiv 2606.19911, CMU/UC Berkeley):
- Every agent is both **producer** and **consumer** of trajectories
- Producer: agent writes its output + reasoning to `agent_trajectories` table
- Consumer: before starting work, agent queries prior trajectories for similar situations
- State-conditioned key-value indexing: recent history = retrieval key, next steps = stored value
- Marginal utility tracking: did retrieving a prior trajectory actually help?

Based on Self-Evolving Agents paper (Ant Group/HKUST/Tsinghua):
- Deployed agent = composite policy (base LLM + in-context harness + memory + tools + guardrails)
- Container = data proxy that captures ATDP trajectories
- Evolution control plane = the pipeline relay itself decides when behavior changes
- Different failures require different intervention surfaces (prompt fix vs gate tightening vs config change)

See `references/matm_research_findings.md` for the full paper summaries and how they map to CIS.

## Spec Before Build — CRITICAL WORKFLOW RULE

**Eric's explicit correction**: "Doesn't the whole structure need to be spect out before just start building?"

Before writing ANY production code for the pipeline:
1. Write a spec document covering all three layers (UI, Abstraction, Hermes Backend)
2. Identify what exists vs what needs building vs what needs replacing
3. Define the DB schema changes needed
4. Define the container environment changes needed
5. Define how the UI interacts with all of it
6. Get Eric's review before building

**Test scaffolding ≠ production code.** What exists in `runtime/orchestrator.py` and `runtime/api/advisor.py` is test code that proved the gateways work. It is NOT production architecture. Don't extend it — replace it.

**Research before proposing.** Eric said: "Those people are engineers, I'm just guessing what the structure and flow should be." Look at published frameworks (EvoAgentX, MASLab, AgentWorkforce) and research papers before proposing architecture. Don't guess.

## Production Spec

The current production spec is at `docs/SPEC_PRODUCTION_PIPELINE_RELAY.md` (REV-2,
post dual-review). It covers:
- Three-layer architecture (UI/Control Plane, Abstraction Layer, Hermes Backend)
- Pipeline relay state machine with error states (ESCALATED, VERIFY_FAILED, STALE, ERROR)
- Mandatory pre-discovery (§3.0) — pipeline searches KB + filesystem + trajectories + web before every agent dispatch
- Mandatory search behavior in personality prompts (§5.5) — agents instructed to cite sources, not work from training data alone
- DB schema extensions (agent_trajectories table, deliberation_rounds extension, directive_hash)
- Container environment (mounts, per-role tool restrictions, Verify terminal allowlist)
- HUMAN_QUESTION lifecycle (FINAL_JSON detection, Telegram delivery, 72h timeout, stale-run reaper)
- Crash recovery, circuit breaker, concurrent run protection
- Saga/compensation pattern (git stash on Verify FAIL)
- Build order (14 steps, corrected per dual-review)

### Build Progress (verified 2026-07-08 via filesystem + spine recovery)
- ✅ Step 1: Container setup — `cis-hermes:pipeline` image built with 6 profile configs + launch_profiles.sh
- ✅ Step 2: Schema migration — migration 0015 applied (agent_trajectories, deliberation_rounds columns, directive_hash, FTS5 + triggers)
- ✅ Step 3: Intent memory tables — already existed (intent_map, anti_patterns, functional_spec, reviewer_brief)
- ✅ Step 4: Spine write mechanism — WAL mode + migration applied. `_db_connect()` sets `PRAGMA busy_timeout=5000`
- ✅ Step 5: pipeline_relay.py — built, tested, and **PROVEN end-to-end** (2026-07-08, commit b888d5f).
  Async state machine: Brain→Review1+2→Draft→Review1+2→EricGate→Menter→Verify→CONSENSUS_REACHED.
  Circuit breaker, crash recovery, pre-discovery, FINAL_JSON parsing, saga compensation, MATM trajectory recording.
  **Full end-to-end test completed**: Brain→IntentReview→Draft (objections→revision)→ProposalReview (consensus)→ERIC_GATE (approved via API)→Menter→Verify (PASS)→CONSENSUS_REACHED.
  Run `run-892e86ca512a0056-1783535751` — 9 rounds, 11 trajectories, Verify ran git diff as evidence.
  Repairable gates work — reviewers objected on round 1, Draft revised, reviewers reached consensus on round 2.
  Added `_resolve_api_key()` for gateway auth (see [Gateway API Key Discovery](references/gateway_api_key_discovery.md)).
  Added `WAITING_FOR_HUMAN` state (was missing — Brain's `NEEDS_CLARIFICATION` was routing to `ESCALATE`).
  Added `start_sync()` method for Flask API integration (creates run without blocking, launches async in background thread).
  Fixed `_start_round()` to auto-increment round_number from DB (spine has `UNIQUE(run_id, round_number)` — see pitfalls).
  Fixed `_execution()` to store Menter's output in `deliberation_rounds.drafter_output` via `_complete_round` extra dict.
  Added per-role `AGENT_TIMEOUTS`: verify/menter=600s, brain/draft=300s, default=180s (see pitfalls).
- ✅ Step 6: Pipeline API endpoints — `runtime/api/relay.py` blueprint with 6 endpoints:
  `POST /api/relay/start`, `GET /api/relay/<run_id>`, `POST /api/relay/<run_id>/answer`,
  `POST /api/relay/<run_id>/gate`, `GET /api/relay/<run_id>/verify`, `GET /api/relay/<run_id>/trace`.
  Registered in `runtime/app.py`. Gate endpoint INSERT fixed (populates `goal_reference_id=0`,
  `briefing_hash=directive_hash`, marks previous approvals as non-current).
  All endpoints tested: status returns full trajectory, gate writes immutable audit record, trace returns full history.
- ✅ Step 10: Eric Gate — immutable audit record, directive hash freezing, API auth. Gate endpoint in `runtime/api/relay.py` writes to `eric_gate_approvals` with all NOT NULL columns populated, marks previous approvals `is_current=0`.
- ✅ Step 11: cis_verify.py L1+L2 — `_run_l1_checks()` captures git diff stat, full diff, changed file existence/size, untracked files. Wired into verify phase: L1 evidence fed to verify agent as structured report before directive. Verify agent does L2 semantic check on top of L1 evidence.
- ✅ Step 12: Verify isolation — `_run_isolated_l1()` creates a **git worktree** at pre-execution HEAD, applies Menter's diff as patch, runs L1 checks in the clean worktree, cleans up. True isolation — Menter never touched the worktree. Falls back to in-place with explicit "NO ISOLATION" warning if worktree fails. Compensation on FAIL: actually runs `git stash` with run_id in stash message (not just printing).
- ✅ Step 13: Trajectory recording + retrieval (MATM) — `_record_trajectory()` now captures `config_version` (git HEAD short hash). `_update_trajectory_outcome()` marks trajectories `success`/`failed` based on actual results (not unconditionally). Called in all 6 phases including error handlers. Verify phase trajectory retrieval uses phase-aware exclusion: excludes only same-run Menter trajectories (per spec §3.4), other phases exclude all same-run trajectories.
- ✅ **Zombie gateway detection (commit bafca21)** — Root cause of pipeline unreliability identified and fixed: stale gateway processes that accept connections but return empty responses. `check_gateway()` now validates response content (JSON, choices, content). `_call_agent()` raises `ConnectionError` on empty responses, tripping circuit breaker. Reviewer retry on empty/ambiguous output (retry once before escalating as incomplete). Three-state consensus model: consensus / objection / incomplete. Incomplete reviews are NOT objections — the reviewer didn't complete its role.
- ✅ **Default-to-success antipattern eliminated (commit 1ad844d)** — Full audit of pipeline_relay.py found 10 more bugs where the system reported success when it hadn't actually succeeded. Root pattern: every state defaulted to "success" and only failed if explicitly detected. Flipped to "default to incomplete, only succeed when explicitly verified." Fixes: (1) Verify with no FINAL_JSON now escalates instead of auto-PASS, (2) Menter output stored in new `menter_output` column (migration 0016) — Verify reads Draft's directive not Menter's self-report, (3) new rounds start as PENDING not CONSENSUS_REACHED, (4) `workflow_runs.result` defaults to PENDING, (5) Brain/Draft/Menter output validated before proceeding, (6) circuit breaker persisted to DB (migration 0017), (7) pre-discovery errors reported to agent not silently swallowed, (8) config_version captures errors not silently empty, (9) worktree tempdir cleaned up on creation failure, (10) Verify FAIL stash ref stored in DB audit trail. See [Default-to-Success Antipattern](references/default_to_success_antipattern.md).
- ✅ **Code Review Gate spec written + IMPLEMENTED + TESTED (commits 06e8e8d, 7682ad1, 056a360, e44268f, 44cfd1c)** — `docs/SPEC_CODE_REVIEW_GATE.md` (REV-2). Design for the gate between ERIC GATE and VERIFICATION. **IMPLEMENTED in pipeline_relay.py** (658 lines, commit e44268f): `_pattern_catalog()`, `_code_review_gate()`, `_review_single_chunk()`, `_run_chunk_l1()`, `_read_codebase_overview()`, `MENTER_UNIVERSAL_RULES` constant. Migration 0018 (`code_review_chunks` table). API relay.py updated: Eric Gate approval routes to PATTERN_CATALOG, not EXECUTION. **Sequential three-pass review** (not parallel): Reviewer A (less competent) reviews first → Reviewer B (more competent) reviews seeing A's output → Reviewer A consensus seeing B's output, delivers one consolidated directive to Menter. Universal rules baked into Menter's system prompt (8 rules: default to incomplete, handle errors, no secrets, no debug, claims match reality, clean up, state persists, validate before proceeding). **END-TO-END TEST PASSED** (commit 44cfd1c): run `run-fcb0058efcaa0f28-1783570097` — Brain → Intent Review → Draft (2 rounds) → Proposal Review (consensus) → ERIC GATE → Pattern Catalog (Brain produced 6,683-char catalog with 12 pattern criteria) → Code Review Gate (Menter built `/api/health` endpoint, Reviewer A found all 12 criteria pass, Reviewer B built on A and found A missed py_compile check, A consensus APPROVED, chunk incorporated) → Verification (timed out but pipeline state correct). See [Code Review Gate Design](references/code_review_gate_design.md).
- ✅ **Self-evolution bridge IMPLEMENTED + VERIFIED (commits ffd3c1c, 8e620ec)** — Pipeline narrative now flows into the FTS5 knowledge base. `_ingest_to_kb()` writes content to `knowledge_messages` with source tags (`pipeline_{phase}`). `_ingest_round_to_kb()` extracts all outputs from a deliberation round. `_complete_round()` auto-triggers ingestion at all 28 call sites — no manual wiring needed. Code review chunks: all 3 passes ingested on APPROVED and CHANGES_REQUESTED (revision directives = searchable objections). Trajectory outcomes fixed for code review (review1/review2/consensus now `success`, were `pending`). The loop is closed: run → KB → FTS5 → next run's pre-discovery. **Verified end-to-end 2026-07-09**: run `run-e4aac6f86dc70fd4-1783600639` produced 22 KB entries across 6 phases (brain, draft, intent_review, proposal_review, pattern_catalog, code_review). FTS5 search confirmed pipeline entries at top of results. See [Knowledge Base Self-Evolution Gap](references/knowledge_base_evolution_gap.md).
- ⬜ Step 14: UI pipeline view — not started. API endpoints exist (status, trace, gate, verify), need frontend page.
  **UPDATE 2026-07-10: Step 14 is NOW COMPLETE.** Built as Component 1 of the Control Plane build spec. `RelayPage.jsx` wraps all relay API endpoints with intent submission, live run view, Eric Gate panel, deliberation viewer, and run history. Route at `/relay`. See [Control Plane Build — Complete Evidence](references/control_plane_build_complete.md).
- ✅ **Control Plane Build COMPLETE (2026-07-10)** — All 14 components built directly by GLM Verifier (Verifier-as-Builder pattern). Spec at `docs/SPEC_CONTROL_PLANE_BUILD.md`. 4 phases: A (foundation: _db_connect fix, KB search, corpus extraction, multi-project), B (interface: RelayPage UI, Eric Gate mobile, soul injection, SWA bootstrap), C (hardening: task decomposition, git workflow, verification depth, error recovery), D (production: monitoring, remote access, state sync). 5 migrations (0021-0025), 10 files created, 5 modified. See [Control Plane Build — Complete Evidence](references/control_plane_build_complete.md).
- ⬜ **Container transition** — Docker images exist (`cis-hermes:pipeline`, 5.7GB) with 6 profile configs, launch script, and gate enforcement. 4 gaps remain: (1) CIS repo not mounted in container, (2) host path assumptions need `CIS_SPINE_PATH` env var, (3) API keys need to be passed as secrets, (4) port 5000 needs publishing. Flask API also needs to be added to `launch_profiles.sh`. See [Container Transition Gaps](references/container_transition_gaps.md).
- ✅ **Container transition COMPLETE (2026-07-09)** — All 4 gaps resolved. CIS repo mounted at `/workspace/cis`, `CIS_SPINE_PATH` + `CIS_PROJECT_ROOT` env vars set, API keys passed via `/workspace/secrets.env`, port 5000 published. Project root injection in agent prompts fixes the "file not found" failure. Three additional fixes required for full end-to-end operation: (1) dispatch.py `hermes_profile` values updated from host names to container role-based names for API key resolution, (2) `hooks_auto_accept: true` + `approvals.mode: "off"` in Menter/Verify container profiles for headless operation, (3) `from dispatch` → `from abstraction.dispatch` import fix in relay.py health endpoint. **Full 7-phase pipeline run proven (2026-07-09, run `run-ef8d1a812b994a03-1783623679`):** Brain → Intent Review → Draft → Proposal Review → Eric Gate → Pattern Catalog → Code Review (Menter built code, Review1/Review2 consensus) → Verification → CONSENSUS_REACHED. See `container-gate-wiring` skill [Container Pipeline Smoke Test](references/container_pipeline_smoke_test.md).
- ✅ **Pipeline relay bug fixes (2026-07-09, 3 bugs + 2 bonus fixes)** — Found during 14-component large-intent testing (run `run-12d5aa6946666b73-1783630035` → ERROR). All fixed and verified in re-run (`run-12d5aa6946666b73-1783641453`): (1) **Brain revision feedback injection** — `_brain_phase()` now fetches reviewer1_output + reviewer2_output on round >1 and injects as `## Reviewer Feedback` section; previously Brain got the same prompt with no idea what was wrong and produced 0 chars; (2) **FTS5 search sanitization** — `_pre_discovery()` strips FTS5 special chars (`.`, `"`, `*`, `(`, etc.) from search keywords; previously every intent with periods broke KB search with "syntax error near '.'"; (3) **Intent truncation** — removed `intent_text[:500]` in `_create_run()`; full 4220-char intent now stored; (4) **Stale pidfile cleanup** — `entrypoint.sh` now removes all role pidfiles on startup; previously `docker restart` caused "already running (pid 33)" false positives, skipping 2/6 gateways; (5) **Docker image name** — correct image is `cis-hermes:pipeline` (not `cis-hermes:pinned` which has bare `sleep infinity` CMD). Adversarial review also caught Brain fabricating `SPEC_CONTROL_PLANE_OBSERVATION.md` — validates the dual-reviewer design. See [Pipeline Revision Feedback Gap](references/pipeline_revision_feedback_gap.md).
- ✅ **execute_code approval block fix (2026-07-10)** — Root cause of 7+ failed file-mutation runs found and fixed. `check_execute_code_guard()` in Hermes `tools/approval.py` blocks `execute_code` in gateway context when `approvals.mode` is "manual" (default). Profile configs had `approvals.mode: "off"` but managed config (`/etc/hermes/config.yaml`) did not pin it — managed config is authoritative and overrides profile config. Fix: added `approvals: mode: "off"` to `enforcement/mwl-proof-v2/managed-config.yaml`, rebuilt image. Verified: run `run-86bc4d1009b8fb44-1783645778` completed full 7-phase pipeline with Menter code review + Verify (CONSENSUS_REACHED) — first successful file mutation inside the container. The enforcement architecture (mwl-proof plugin + container isolation + hardline blocklist) is unaffected — `approvals.mode` is a UX prompt layer, not a security control. See `container-gate-wiring` skill approvals.mode pitfall.
- ✅ **Reviewer degradation + escalation notification (2026-07-10)** — Two fixes for pipeline resilience: (1) `MAX_REVIEWER_RETRIES` increased from 1 to 2 (3 total attempts) to survive transient model failures; (2) `_check_consensus()` now implements single-reviewer degradation: if one reviewer fails but the other has OBJECTIONS, Brain gets sent back with the valid objections instead of escalating. Only escalates if BOTH fail. (3) `_set_run_status()` now intercepts terminal failures (ESCALATED, ERROR, VERIFY_FAILED) and sends a Telegram notification via `_notify_terminal_failure()` — Eric gets a push message with run ID, phase, signal, and intent preview instead of having to manually poll. Requires `CIS_TELEGRAM_BOT_TOKEN` and `CIS_TELEGRAM_CHAT_ID` in `/workspace/secrets.env`. See [Reviewer Degradation + Escalation Notification](references/reviewer_degradation_escalation_notification.md).
- ✅ **Tier 1 Guardrails WIRED (2026-07-10, commit f6a9143)** — 10 deterministic guardrails in `runtime/abstraction/guardrails.py`, wired into all 6 pipeline phases (Brain, Draft, both Review rounds, Menter, Verify). 3 BLOCK guardrails (claim-action verifier, output schema validator, path contract validator) halt the pipeline on FAIL. 7 ADVISORY guardrails (sycophancy detector, scope compliance, code quality, content specificity, honesty reporter, unverified claim block, tool result sandboxing) log warnings. Results stored in `gate_outcomes` table (migration 0026) for self-evolving harness feedback. `GET /api/relay/guardrails` endpoint for UI display. Key techniques: negation-aware sycophancy detection (distinguishes "no issues" from "issue found"), claim path extraction with preceding-character anchor to avoid false matches on relative paths. See [Tier 1 Guardrail Implementation](references/tier1_guardrail_implementation.md).
- ✅ **Tier 2 Guardrails WIRED (2026-07-10, commit 141d742)** — 10 more guardrails added to `guardrails.py`, bringing total to 20 (Tier 1 + Tier 2). 3 new BLOCK guardrails: loop detector (hash + Jaccard near-duplicate detection), model diversity enforcement (same model reviewing itself), output sanitizer (zero-width chars, homoglyphs, control chars, mixed scripts). 7 new ADVISORY guardrails: context budget monitor, mode collapse detector, goal anchoring check (drift threshold gets stricter per round), trajectory monitor (queries agent_trajectories for repeated outputs/failures), verbosity/density metric, sequential review enforcer, version drift check. `run_guardrails()` signature extended with `previous_outputs`, `round_num`, `conn`, `run_id`. All pipeline_relay.py call sites updated. See [Tier 2 Guardrail Implementation](references/tier2_guardrail_implementation.md).
- ✅ **Tier 3 Guardrails WIRED (2026-07-10, commit 2f57391)** — 10 deeper-analysis guardrails added to `guardrails.py`, bringing total to 30 (all tiers). 3 new BLOCK guardrails: intent compliance checker (AST parse + stub detection — `pass`/`return None`/empty returns), evidence hash chain (git HEAD before/after + file timestamp freshness), context injection gate (required soul markers `ROLE_OVERLAY`/`PROJECT_BRIEF`/`KB_CONTEXT` + 500 char minimum). 7 new ADVISORY guardrails: semantic spot check (verify claimed functions exist in claimed files via regex), consensus independence check (reasoning keyword overlap + shared evidence citation), hardcode detector (AST: hardcoded keys/ports/timeouts in assignments), error handling checker (AST: external calls without try/except), position randomizer (multi-option prompts need positional randomization), raw source preservation (deliberation_rounds column length check for truncation), bias drift detector (enterprise/legacy keywords not in intent — microservice, kubernetes, CQRS, etc.). **Key pitfall discovered**: `_ast.SyntaxError` doesn't exist — `SyntaxError` is a Python builtin, not an `ast` module attribute. All AST guardrails use `except SyntaxError` not `except _ast.SyntaxError`. See [Tier 3 Guardrail Implementation](references/tier3_guardrail_implementation.md).\n- ✅ **Tier 4 Guardrails WIRED (2026-07-10, commit 94b3658)** — 4 advanced guardrails added to `guardrails.py`, bringing total to **34 (ALL TIERS COMPLETE)**. 2 new BLOCK guardrails: randomized evaluation timing (85% eval / 15% skip on non-critical phases — prevents alignment faking), capability claim verifier (extracts "I created/implemented/fixed X" claims, verifies through file/function/git/test checks). 2 new ADVISORY guardrails: example diversifier (hash-based example repetition tracking across runs), effort metric (output complexity vs task complexity ratio — detects sandbagging). Key pitfalls: don't lowercase before regex matching "I" (becomes "i", matches inside words), don't stop claim extraction at periods (file paths have .py), effort ratio threshold must account for simple tasks.
See `container-gate-wiring` skill [External Gate Timing](#external-gate-timing-in-pipeline-2026-07-11).\n
- **Verification phase gate fixes (2026-07-11, commit 8ef52eb)** — After the timing fix, the verification phase's external gates still failed because 5 additional issues: (1) `gate_service_health` checked retired port 8642 instead of 5000; (2) `gate_endpoint` checked `/health` (404) instead of `/api/health`; (3) `gate_build_state_coherence.py` crashed — system Python lacked pyyaml (Hermes venv had it but gate scripts run with system python); (4) `gate_eric_approval.py` (BLOCK) failed because `workflow_runs.result` was still PENDING — the pipeline only set it AFTER external gates fired, but the gate checks it BEFORE; (5) `gate_eric_approval_present.sh` (BLOCK) failed because `eric_approved_at` was never set by the gate approval endpoint. Fixes: set `workflow_runs.result` before external gates fire, set `eric_approved_at` in the approval endpoint, add `/health` route alias in `container_app.py`, `pip3 install pyyaml` in Dockerfile, skip checks 3-6 in `gate_eric_approval.py` when placeholder data detected. See [Verification Phase Gate Fixes](references/verification_phase_gate_fixes.md).
- **Container output contract enforcement (2026-07-11, commit c63a5aa)** — All 7 pipeline phases had the same enforcement gap: detect missing FINAL_JSON, immediately escalate. The container was a detection layer, not an enforcement layer. Eric's correction: "the container is meant to ensure it cooperates. why does it have an option." Fix: added `_enforce_output_contract()` async helper that issues ONE repair prompt before escalating (per ADR-SEED-012). Also separated guardrail blocks (policy violations → immediate escalate) from format violations (missing FINAL_JSON → repair prompt first) in Drafter, Menter Execution, and Verify phases where they were merged in single `if` conditions. Wired into all 7: Brain, Drafter, Pattern Catalog, Code Review Consensus, Menter Code Review, Menter Execution, Verify. See [Container Output Contract Enforcement](references/container_output_contract_enforcement.md).

## Build Order (from spec REV-2, corrected per dual-review)

The build order was revised after dual-review by Review1 (Qwen) + Review2 (GLM).
Both reviewers independently found that container setup must come BEFORE pipeline
code (can't test enforcement without the container), and several hidden
dependencies were missing.

1. Container setup with per-profile configs (prerequisite for all testing)
2. Schema migration (fix drafter_output already exists, add missing columns)
3. Intent memory tables (prerequisite for Brain + reviewers)
4. Spine write mechanism (WAL mode, busy_timeout, retry, storage verification)
5. pipeline_relay.py core (async state machine, error states, pre-discovery injection)
6. Pipeline API endpoints (Eric can see the system here — steps 1-5 have no UI)
7. HUMAN_QUESTION mechanism (FINAL_JSON detection, Telegram delivery, timeout)
8. Brain phase (intent clarification, pre-discovery review)
9. Parallel reviewers (async dispatch, FINAL_JSON consensus, objection routing)
10. Eric Gate (immutable audit record, directive hash, API auth)
11. cis_verify.py L1 + L2 (deterministic + semantic verification)
12. Verify phase (clean checkout isolation, evidence re-run, compensation on FAIL)
13. Trajectory recording + retrieval (MATM with run_id exclusion, outcome marking)
14. UI pipeline view (relay status, agent outputs, Eric Gate, trace view)

**First build is manual** (steps 1-5 by Verify agent) because the pipeline
doesn't exist yet to dispatch through. After step 5, future work goes through
the pipeline properly (Brain→Review→Draft→Menter→Verify).

### Mandatory Pre-Discovery (§3.0 of spec)

Before ANY agent is dispatched, pipeline_relay.py runs a discovery query and
injects results into the agent's prompt. This prevents the "ignorance of
existing work on disk" failure — agents search first, think second.

1. Spine FTS5 search (knowledge_messages_fts)
2. Filesystem scan (search_files across docs/, data/drive_imports/, cis_kernel/)
3. Trajectory search (agent_trajectories WHERE outcome='success' AND run_id != current)
4. Web search (Brain and Draft only — current research and best practices)
5. Results injected as `[PRE-DISCOVERY RESULTS]` prefix, wrapped as data not instructions

This is the mechanism that prevents an agent from ignoring existing work.
The agent doesn't choose whether to search — the pipeline searches FOR it.

### Mandatory Search in Personality Prompts (§5.5 of spec)

Each agent's managed config includes instructions to:
- Review pre-discovery results before producing output
- Cite what was found (file paths, URLs)
- State explicitly if nothing relevant was found
- Not work from training data alone

These are baked into root-owned managed configs — agents cannot remove them.

## Session Ingestion

To ingest Hermes sessions into the knowledge base:
- Script: `tools/catalog/ingest_sessions.py`
- Scans `~/.hermes-*/sessions/session_*.json` across all profiles
- Extracts user+assistant messages, chunks at 4000 chars
- Deduplicates by `source_key` (format: `hermes_session/<profile>/<session_id>/<chunk>`)
- Batch inserts to `knowledge_messages` table
- Rebuilds FTS5 index after insertion
- Can be re-run safely (skips already-ingested sessions)

## Key Reference Files

- **[MATM Research Findings](references/matm_research_findings.md)** — Full paper summaries and CIS mappings
- **[Production Spec Summary](references/production_spec_summary.md)** — Condensed spec decisions
- **[Session Ingestion Pattern](references/session_ingestion_pattern.md)** — KB ingestion technique
- **[Session State Recovery](references/session_recovery_technique.md)** — Reconstructing build state after credit gap or context loss (state.db, request dumps, git, spine, Docker)
- **[Spine Schema Constraints](references/spine_schema_constraints.md)** — Actual workflow_runs + deliberation_rounds column names, CHECK constraints, and correct INSERT/UPDATE patterns (spec ≠ reality)
- **[Gateway API Key Discovery](references/gateway_api_key_discovery.md)** — How gateway auth keys are stored (.env vs config.yaml), the `_resolve_api_key()` pattern, and all 6 gateway key locations
- **[Knowledge Base Schema Gaps](references/knowledge_base_schema_gaps.md)** — Missing DDL for knowledge_messages table, FTS5 source_key query bug in pipeline_relay.py, gateway health check false positives
- **[Flask + Async Integration](references/flask_async_integration.md)** — How to expose the async pipeline_relay.py behind synchronous Flask endpoints: start_sync() + background thread pattern, cross-round output aggregation, python3.12 requirement
- **[Gateway Stale Process Diagnosis](references/gateway_stale_process.md)** — How to diagnose and fix stale gateway processes that serve empty responses after systemd service crash. Recurring pattern on creative-vm.
- **[Data Integrity Patterns](references/data_integrity_patterns.md)** — 4 bugs where DB records lied about reality (empty=consensus, signal stored before check, outcome marked success on failure, single reviewer failure ignored). Fixes and unit tests.
- **[Default-to-Success Antipattern](references/default_to_success_antipattern.md)** — Second audit: 10 more bugs where the system reported success when it hadn't succeeded. The fundamental LLM-built-code disease, the meta-lesson about peer review, and the Code Review Gate design decision.
- **[Code Review Gate Design](references/code_review_gate_design.md)** — Full design for the chunk-based code review gate: pattern catalog technique (Brain reads codebase, identifies structural patterns and completion criteria), universal vs pattern-specific checks, knowledge base integration with Claude/ChatGPT review patterns, chunk parameters, and the 7 structural patterns found in pipeline_relay.py as a worked example.
- **[Knowledge Base Self-Evolution Gap](references/knowledge_base_evolution_gap.md)** — Critical finding: 58 trajectories exist but ZERO are in the FTS5 knowledge base. Pipeline narratives (objections, consensus, code review findings, pattern catalogs) don't flow back to `knowledge_messages`. No self-evolution — each run is an island. The connection diagram and proposed fixes. **Now includes end-to-end verification procedure.**
- **[Pipeline Testing Commands](references/pipeline_testing_commands.md)** — How to start, resume, monitor, and approve pipeline runs. Container lifecycle (correct Docker image: `cis-hermes:pipeline`), gateway health checks, state transitions, and monitoring queries. Includes container API submission via curl and the `sg docker -c` pattern for Docker access.
- **[Intent Submission Guidelines](references/intent_submission_guidelines.md)** — How to craft and submit intents to the pipeline. Intent truncation is now FIXED (was `[:500]`, now full text stored). Good/bad intent patterns, monitoring submitted runs, and verification queries.
- **[Agent Call Retry Pattern](references/agent_call_retry_pattern.md)** — Retry-with-backoff for sequential agent calls in the code review gate. Includes the `str(e)` empty string bug for httpx exceptions and the `repr(e)` fallback fix.
- **[Container Transition Gaps](references/container_transition_gaps.md)** — What's needed to move the pipeline from host (dev) into Docker (production). 4 gaps: CIS repo not in image, host path assumptions, API keys, port publishing. Includes the target `docker run` command.
- **[Pipeline Testing Commands](references/pipeline_testing_commands.md)**
- **[Local LLM Inference Setup](references/local_llm_inference_setup.md)** — Qwen3-VL-30B on RTX 4090 via llama.cpp (port 8002). DeepSeek budget: ~$2 left — use local LLMs for build-time analysis.
- **[Pipeline Revision Feedback Gap](references/pipeline_revision_feedback_gap.md)** — Three bugs found during large-intent testing (2026-07-09): (1) Brain revision doesn't inject reviewer feedback — `_brain_phase()` sends the same prompt on round 2 with no objections, causing Brain to produce empty output and error; (2) FTS5 pre-discovery search breaks on periods in intent text — KB search returns syntax error for any intent containing file paths; (3) Agent hallucination pattern — Brain fabricated a spec document with convincing detail, caught by adversarial review.
- **[Deterministic Guardrail Gap](references/deterministic_guardrail_gap.md)** — Critical finding (2026-07-10): the 51 gate scripts baked into the container are DEAD CODE — nothing calls them during pipeline runs. The pipeline relies 100% on LLM judgment for factual accuracy. L1 checks only run post-hoc in verification. Token cost analysis (~200K per run vs 2-3 rounds in Eric's manual process). Five optimization options (skip Brain for clear intents, merge Brain+Draft, Draft self-verify, sequential reviewers, wire deterministic pre-checks). HASE connection: optimized harness enables smaller/cheaper models. Full spec (now including Part 6: Self-Evolving Harness Strategy with `gate_outcomes` table schema and three-phase adaptive threshold build order) at `docs/DETERMINISTIC_GUARDRAIL_SPECIFICATION.md`.
- **[Gate Scripts Analysis](references/gate_scripts_analysis.md)** — Detailed categorization of all 49 gate scripts at `enforcement/mwl-proof-v2/gates/`. 3 will work as-is, 15 need DB path fixes, 5+ have wrong schema assumptions, 4 depend on old CLI tools, 13 are UI/tier-specific (stale), 7 security gates are already wired. Key insight: even though scripts won't run directly in the container, they serve as **functional blueprints** — they specify what to check, what pass/fail looks like, and when to fire. The scripts cover "did it happen?" checks but NOT "is it any good?" checks (sycophancy, scope drift, content depth) — those need to be written from scratch.
- **[Control Plane Build Spec](references/control_plane_build_spec.md)** — The 14-component CIS Control Plane and SWA Development Infrastructure spec at `docs/SPEC_CONTROL_PLANE_BUILD.md`. Written by GLM Verifier (2026-07-10) from pipeline run `run-12d5aa6946666b73-1783649571` (6 rounds, consensus). Incorporates Reviewer 1's 3 critical objections and Reviewer 2's 8 concerns. Verified codebase state: relay.py (540 lines, 7 routes), pipeline_relay.py (2,447 lines), 22 migrations (next: 0021), deliberation_rounds has all output columns, goal_references table exists. Documents the `_db_connect` bug, 5 new migrations (0021-0025), 4 build phases (A-D), and Menter directives.
- **[Comprehensive Failure Mode Taxonomy](references/failure_mode_taxonomy.md)** — 34 failure modes from two sources: (1) Eric's own words in the KB (10 categories: enterprise bias, self-report lies, quick-fix chasing, fabrication, session amnesia, etc.) and (2) external harness research (14 categories: task drift, sycophancy, mode collapse, degeneration loops, reward hacking, alignment faking, specification gaming ladder, context exhaustion, etc.). 4-tier implementation priority (34 guardrails, 10 zero-token Tier 1 checks). Full spec at `docs/DETERMINISTIC_GUARDRAIL_SPECIFICATION.md`.
- **[Phase A Build Evidence](references/phase_a_build_evidence.md)** — Evidence for Phase A of the Control Plane build (2026-07-10): _db_connect fix, MCP bridge bug fix, 3 new relay endpoints, migration 0021 (corpus_entries), migration 0022 (projects table), extract_corpus.py (213 entries), multi-project routing. Built directly by GLM Verifier to save tokens.
- **[Control Plane Build — Complete Evidence](references/control_plane_build_complete.md)** — All 14 components built directly by GLM Verifier (2026-07-10). Phases A-D complete: UI (RelayPage.jsx + 9 API methods), Eric Gate (mobile-responsive), soul injection (role_overlays.yaml + _build_soul_document), SWA bootstrap (repo + spine + AGENTS.md), task decomposition, git workflow, verification depth (pytest execution + scope check), error recovery (retry + DLQ + Eric Gate notification), monitoring (metrics + token tracking), remote access docs, spine schema sync. 10 files created, 5 modified, 5 migrations.
- **[Reviewer Degradation + Escalation Notification](references/reviewer_degradation_escalation_notification.md)** — Two resilience fixes (2026-07-10): (1) `MAX_REVIEWER_RETRIES` increased to 2 + single-reviewer degradation in `_check_consensus()` — if one reviewer fails but the other has OBJECTIONS, Brain gets sent back instead of escalating; (2) `_set_run_status()` now sends Telegram notifications on terminal failures (ESCALATED, ERROR, VERIFY_FAILED) — Eric gets a push message instead of having to poll.
- **[Tier 1 Guardrail Implementation](references/tier1_guardrail_implementation.md)** — 10 deterministic guardrails (3 BLOCK, 7 ADVISORY) wired into all 6 pipeline phases (2026-07-10, commit f6a9143). Includes: negation-aware sycophancy detection technique, claim path extraction regex patterns, wiring pattern for pipeline_relay.py, gate_outcomes table schema (migration 0026), and the self-evolving harness feedback loop architecture.
- **[Tier 2 Guardrail Implementation](references/tier2_guardrail_implementation.md)** — 10 more deterministic guardrails (3 BLOCK, 7 ADVISORY) wired into all 6 pipeline phases (2026-07-10, commit 141d742). Includes: loop detection via hash + Jaccard, steganography detection (zero-width chars, homoglyphs, mixed scripts), goal anchoring with per-round drift thresholds, trajectory monitor querying agent_trajectories, model diversity enforcement, version drift baseline tracking, context budget thresholds, verbosity/density metrics, `run_guardrails()` signature extension.
- **[Harness Engineering and RSI](references/harness_engineering_rsi.md)** — Lilian Weng's harness engineering article (July 2026), HASE paper (arXiv:2607.03935), and how CIS maps to the RSI roadmap. CIS is a harness at the "harness code" optimization stage. Three design patterns (workflow automation, file system as memory, sub-agent jobs) map directly to pipeline architecture. Next step: self-improving harness meta-loop that reads spine failure patterns and proposes fixes.
- **[Guardrail Evaluation and Pruning](references/guardrail_evaluation_pruning.md)** — Methodology for evaluating which guardrails are irrelevant (delete) vs broken (fix) after wiring. Pipeline execution order diagram showing which DB tables are available before vs after guardrails fire. 6 guardrails pruned, 2 fixed (2026-07-10).
- **[Container Output Contract Enforcement](references/container_output_contract_enforcement.md)** — Container must enforce output contracts, not just detect violations. `_enforce_output_contract()` helper: parse → repair prompt → escalate. Guardrail blocks (policy) escalate immediately; format violations (missing FINAL_JSON) get one repair. 7 sites fixed (2026-07-11).

## Verifier-as-Spec-Author Workflow (2026-07-10)

**Eric's explicit directive**: "I don't want to waste tokens, you should produce the complete spec, then tell menter to build it. you can fix anything that's not right during verification."

When the pipeline has already done Brain → Draft → Review → revised Draft → Review (consensus reached), the analysis is COMPLETE. Running another full pipeline round to produce a final spec wastes ~200K tokens. Instead:

1. **Verifier reads all pipeline output** — Brain's intent understanding, Draft's proposal (both rounds), Reviewer 1's objections, Reviewer 2's concerns, the revised draft
2. **Verifier verifies against actual codebase** — file paths, line counts, migration numbers, schema columns, DB tables, existing mechanisms. This is the Claim-Action Verifier pattern from the guardrail spec applied to the pipeline's own output.
3. **Verifier writes the final spec** — incorporates reviewer fixes, corrects wrong paths/numbers, removes scope that duplicates existing mechanisms, adds verified codebase state as ground truth for Menter
4. **Verifier approves the pipeline run** — `POST /api/relay/<run_id>/gate` with APPROVE
5. **Menter builds from the spec** — the pipeline dispatches to Menter with the pipeline's draft, but the spec doc is available at a known path for reference
6. **Verifier fixes during verification** — when Menter reports completion, Verifier checks against the spec and fixes anything wrong

**When to use this pattern:**
- Pipeline has reached CONSENSUS_REACHED or ERIC_GATE after 2+ draft rounds
- The intent is complex (multi-component, not a trivial one-line change)
- The reviewer objections revealed real issues that were addressed in revision
- The Verifier can independently verify codebase claims (file paths, schema, existing mechanisms)

**Verifier-as-Builder (extension):** When Eric says "let's just get it done" or similar, the Verifier doesn't just write the spec — the Verifier BUILDS it directly, skipping the Menter dispatch entirely. This saves another ~100K+ tokens (no Menter LLM call, no verification round). The Verifier:
1. Writes the spec (as above)
2. Approves the pipeline run to move it past ERIC_GATE
3. Builds each component directly using terminal, write_file, patch tools
4. Verifies each step with deterministic checks (py_compile, sqlite3 queries, functional tests)
5. Reports with evidence at each step (file paths, command output, git diff)

**When to use Verifier-as-Builder:**
- Eric explicitly says "let's just get it done" or "get it done" — direct signal
- The spec is complete and verified against codebase
- The work is primarily file creation/modification with clear specifications
- Building directly is faster than Menter dispatch + review + verification cycle

**When NOT to use Verifier-as-Builder:**
- Complex architecture decisions need LLM reasoning — let Menter handle it
- Eric hasn't seen the pipeline output — he must approve first
- The work requires multi-step reasoning that benefits from code review gate

**When NOT to use Verifier-as-Spec-Author:**
- Simple intents (one-line changes, single endpoint additions) — pipeline handles these fine
- First run of a new topic — let the pipeline do its full analysis
- When Eric hasn't reviewed the pipeline output yet — Eric must see what the pipeline produced

**Spec document from this session**: `docs/SPEC_CONTROL_PLANE_BUILD.md` — 14-component CIS Control Plane build spec, written by GLM Verifier from pipeline run `run-12d5aa6946666b73-1783649571` (6 rounds, consensus reached). Incorporates Reviewer 1's 3 critical objections (duplicate features, wrong migration numbers, scope inflation) and Reviewer 2's 8 concerns (multi-project DB switching, concurrency, corpus tagging, prompt length budget, mobile CSS, Playwright availability, FK fix, build order swap).

## Self-Evolving Guardrail Threshold Tuning (2026-07-10)

Eric's insight: the false positive problem in deterministic guardrails is exactly what self-evolving harness strategy addresses. A static harness has a fixed false positive rate — if the threshold is wrong for 30% of tasks, you either live with it or manually tune. A self-evolving harness treats the threshold as a learned parameter.

### The Loop
1. Guardrail fires — flags output as e.g. SCOPE_DRIFT
2. Pipeline continues — reviewer sees the flagged output
3. Reviewer accepts it (false positive) or rejects it (true positive)
4. Harness records the outcome alongside the flag
5. Next run — threshold adjusts based on accumulated evidence

### Why This Is RSI at the Harness Layer
The models are the swappable parts — they change, their biases shift, their failure modes evolve. The harness is the thing that survives. If the harness can tune its own thresholds based on observed accuracy, it adapts when you swap DeepSeek for Qwen for GLM, because different models produce different false positive profiles. The harness learns each model's blind spots through observed behavior, not hardcoded assumptions.

### Build Order
1. **Wire deterministic gates** — ~~static thresholds~~ **DONE (2026-07-10, commits f6a9143 + 141d742 + 2f57391 + 94b3658)** — **34 guardrails (ALL 4 TIERS)** in `guardrails.py`, 11 BLOCK + 23 ADVISORY, wired into all 6 pipeline phases. Outcomes stored in `gate_outcomes` table (migration 0026). **Tier 5 (commit ab7e629)**: 22 external gate scripts from `tools/gates/` wired via `run_external_gates()` subprocess wrapper. 4 security gates fire on ALL phases, 18 phase-specific gates fire at brain/draft/review/pre_menter/menter/verify/closeout. See [Tier 5](references/tier5_external_gate_wiring.md). See [Tier 1](references/tier1_guardrail_implementation.md), [Tier 2](references/tier2_guardrail_implementation.md), [Tier 3](references/tier3_guardrail_implementation.md), and [Tier 4](references/tier4_guardrail_implementation.md) references. **Pipeline test verified (commit 983cbae)** — 46 guardrail outcomes across Brain + Intent Review, 40 PASS, 1 FAIL (ADVISORY), 5 SKIP, 0 BLOCK failures. Randomized eval timing proven (Reviewer 1 randomly skipped at 15% rate). See [Guardrail Pipeline Test Results](references/guardrail_pipeline_test_results.md). **Tier 5 (commit ab7e629)** — 22 external gate scripts wired via `run_external_gates()` subprocess wrapper, 4 security + 18 phase-specific. See [Tier 5](references/tier5_external_gate_wiring.md).
2. **Add feedback loop** — `gate_outcomes` table: run_id, gate_name, result (PASS/FAIL/SKIP), final_outcome (accepted/rejected/revised), was_false_positive (derived post-hoc) — **Table created (migration 0026), recording implemented. Feedback analysis pending 20-30 runs of data.**
3. **Add threshold tuning** — compute false positive rates per gate per task type, adjust thresholds from observed data. Promote reliable ADVISORY gates to BLOCK. Demote noisy BLOCK gates to ADVISORY. **Not started — requires feedback data first.**

This connects directly to the [Harness Engineering and RSI](references/harness_engineering_rsi.md) reference — CIS moves from "harness code" optimization stage to "self-improving harness meta-loop" stage. The spine already has the feedback signal (every run ends with accepted/rejected/revised). Storing guardrail outcomes alongside that signal creates the training dataset.

### Performance Justification
- Deterministic checks add ~10-15 seconds total (negligible vs 30-120s per LLM call)
- Token cost is **negative** — each fabrication caught before reviewer saves ~80K tokens of wasted revision rounds
- The trade-off is "10 seconds of deterministic checks vs 80K tokens of wasted LLM revision rounds"
- Real risk is false positives, not performance — managed by starting soft checks as ADVISORY and tuning from real data
## Design Principles for Agent Interaction (Eric's Vision)

**Adversarial in quality, collaborative in task completion.** Eric's explicit direction (2026-07-10):

- **Menter should ask reviewers for clarification** — if reviewer feedback is vague or uninterpretable, Menter should have a mechanism to ask the reviewer to clarify, not just fail. This is bidirectional communication, not one-way rejection.
- **Reviewers or other models should assist Menter** — if Menter produces bad code, a reviewer or another model should step in to help correct it, not just reject and send back. The system should be collaborative in finishing the task.
- **Transient model failures should log and rerun** — when a model returns empty output (rate limit, timeout, API error), the pipeline should log the failure to the DB and automatically retry. Not just retry twice and escalate.
- **Logs should be written to the DB** — all agent gateway logs, error responses, and HTTP status details should be persisted to the spine, not just stdout. If logs have the potential to solve problems, they must survive container restarts.
- **The system should challenge each other but help each other finish** — adversarial review is about quality, not about blocking. The goal is completing the task to the highest standard, not failing runs.

These principles map to the Self-Harness propose-evaluate-accept loop and the MATM transactive memory pattern. The key insight: the evaluator and the builder are on the same team — they share the goal of a correct result. The adversarial part is the challenge; the collaborative part is finishing.

## Related Skills
- `container-gate-wiring` — Docker image gate enforcement, container_gate_runner.py pattern
- `cis-soul` — CIS profile behavior, Ten Commandments, G.O.D. Protocol

## Remote Access
- **[Remote UI Access — Sunshine/Moonlight/Tailscale](references/remote_access_sunshine_moonlight.md)** — Low-latency remote desktop via Sunshine (NVENC on RTX 4090) + Moonlight client + Tailscale tunnel. Best for real-time UI monitoring of the control plane. Supersedes Tailscale Serve / nginx / SSH tunnel for interactive use. Setup plan, architecture diagram, and headless display notes.

## Pitfalls

See references/pitfalls.md for the full list. Append new pitfalls THERE, not here.
Also see references/pitfalls-and-solutions.md (2026-07 snapshot).
