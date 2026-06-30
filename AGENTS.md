# CIS — AGENTS.md
Generated: 2026-06-30 06:01 UTC | Run: run-51bc771dd9d5 | Latest pipeline: run-1010c3076e084
Source: SQLite spine + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_agents_md.py

## 1. Current Build Phase
Phase PD CLOSED (enforcement primitive PROVEN 2026-06-24). Phase 0 IN PROGRESS: loop-breaker for successful-repeat tool calls. Root cause identified in tool_guardrails.py — successful identical calls invisible to counter. Config-first test (hard_stop_enabled) pending. Build target: extend ToolCallSignature counter to count regardless of success/failure.
Direction: Phase 0: Close the loop-breaker gap. Enforcement primitive proven (5 walls held, all passes). Loop-breaker root cause: successful repeated identical tool calls not caught by guardrail. First test config-only (hard_stop_enabled + same_tool threshold). Build target: counter for identical ToolCallSignature regardless of success/failure.
Build order authority: docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md

## 2. Do Not Start
- Pass 5 implementation (project promotion, schema migration)
- Unified memory build
- Wiring V4-Pro through NeMo (architecturally blocked)
- Briefing Center UI redesign
- Notes/Open Items database implementation
- VDB pipeline rebuild
- Discord/Telegram gateway
- Schedule field-use work (SWA)
- CIS Foundation Build Plan Phases 1-3
- Snapshot trigger work (CIS-INFRA-STORAGE-002)
- Any artifact not in the approved Dependency Graph Build Plan v2.0

## 3. Active Architecture

### Infrastructure
- proxmox_host: wander at 192.168.1.200, PVE 9.1.6
- primary_vm: creative-vm (VM 100), Ubuntu 24.04, 192.168.1.15
- storage: virtio0 500G local-lvm, virtio1 250G local-lvm
- passthrough: virtio2 10TB archive, virtio3/5/6 SSDs
- snapshot_status: RESOLVED — cis-snapshot deployed on root@wander
- backup_status: local archive at /mnt/archive/cis_backup_20260524_112430.tar.gz
- github_repo: https://github.com/digitalgsmp/cis

### Gateways
| Label | Profile | Port | Model | Reasoning | NeMo | Status |
|-------|---------|------|-------|-----------|------|--------|
| Flash/Research | hermes-prime | 8642 → NeMo 8800 | deepseek-v4-flash | none | Yes | DOWN — verified 2026-06-29 via ss -tlnp |
| V4 Drafter | hermes-v4pro | 8645 | deepseek-v4-pro | xhigh | No | Running |
| V4 Reviewer | hermes-r1 | 8643 | deepseek-v4-pro | xhigh | No | Running |
| V4 Implementer | hermes-v4impl | 8646 | deepseek-v4-pro | xhigh | No | Running |
| Qwen | hermes-qwen | 8644 | qwen3-vl-30b | none | No | Running |

### Hermes Source Patches
- /home/eric/.hermes/hermes-agent/run_agent.py:9782 — Added api.deepseek.com to _supports_reasoning_extra_body() allowlist
- /home/eric/.hermes/hermes-agent/plugins/model-providers/deepseek/__init__.py — DeepSeekProfile with build_api_kwargs_extras() for thinking params
- /home/eric/.hermes/hermes-agent/gateway/platforms/api_server.py:1255 — Extracts reasoning_content from agent result, surfaces in API response
- /home/eric/.hermes/hermes-agent/agent/usage_pricing.py:731 — Added completion_tokens_details.reasoning_tokens fallback

## 4. Active Decisions
- [ADR-SEED-016] Enforcement Primitive Approved: TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md approved via dual-review (Claude + ChatGPT audit) + Eric approval. Three-layer process isolation: CIS control plane → Hermes worker in Docker container with RO /opt/cis-control. 15 acceptance tests (A–O). No implementation until §14 raw-evidence plan executed.
- [ADR-SEED-015] Enforcement architecture: three-layer process isolation: CIS enforces Hermes via root-owned /opt/cis-control mounted read-only into Docker worker. Worker writes only to /mnt/cache/catalog/<run_id>/. Two enforcement walls: kernel (Docker RO mount) + policy hook (pre_tool_call). Trust root: constrained agent cannot author its own contract. Override plane (.GATE_DISABLED) built/tested before hook is trusted. See DEV-PIVOT-17 for full text.
- [ADR-SEED-014] BLK-SEED-005 refresh-bug root cause: get_default_hermes_root collapses onto prime unit: FALSE CLAIM — RESOLVED (verified 2026-06-16). Investigation found prime was never actively poisoned. The --replace process was the managed systemd service with correct HERMES_HOME (/home/eric/.hermes). BLK-SEED-005 closed as false positive. ROOT CAUSE (documented for audit trail): get_default_hermes_root() in hermes_constants.py (line 71) returns sibling HERMES_HOME paths like ~/.hermes-r1 as the default root — the fallthrough logic treats any HERMES_HOME outside ~/.hermes/ as a Docker/custom home and returns it verbatim. _profile_suffix() then sees home == default, collapses suffix to empty string, derives service name hermes-gateway (the DEFAULT/prime unit), and refresh_systemd_unit_if_needed() can overwrite the prime systemd unit with a non-prime HERMES_HOME. Verified against source and live empirical test. The collapse bug is a LATENT architectural risk, not an active runtime issue on prime. Fix: relocate sibling homes into ~/.hermes/profiles/ layout, or apply Patch#7.
- [ADR-SEED-012] Orchestrator validation contract: Orchestrator validates state-transition signals only via FINAL_JSON block. Freeform model body is stored as documentation and never parsed for routing. Every Drafter and Reviewer response must end with a FINAL_JSON block containing role, status, summary, recommendation, next_action. Role-scoped status values: Drafter emits PROPOSAL_READY or REVISION_READY only. Reviewer emits CONSENSUS_REACHED, OBJECTIONS, or ESCALATE only. If FINAL_JSON is missing or malformed, orchestrator issues one repair prompt then falls back to constrained text-scanning. Markdown heading presence (### Summary, ### Recommendation) must never cause validation failure.
- [ADR-SEED-013] Retire Kanban as required pipeline transport: Kanban is no longer required for router, orchestrator, gate, or closeout execution. workflow_runs is the authoritative in-flight work object. deliberation_rounds stores per-round Drafter/Reviewer history. Router creates a workflow_runs row and returns run_id. Orchestrator accepts --run-id and reads topic from workflow_runs. Gates verify from SQLite. Kanban code paths are commented out and preserved as legacy. kanban_card_id is null on all new pipeline runs.
- [ADR-SEED-010] Project isolation model: --project-root: Each CIS-managed project has its own git repo / project root. The CIS toolchain (generators, gates, database layer, static config templates) may be copied or bootstrapped into a new project repo. Projects do not share one runtime spine. Projects do not import a central CIS repo as a live dependency for generated context or state. Cross-project contamination is avoided through filesystem and repo isolation. A second project initializes its own repo with its own spine, static config, and generated outputs. The --project-root model requires no database schema migration, no generator refactoring, and no multi-project routing logic. It is a zero-implementation decision.
- [ADR-SEED-006] Spine migration strategy: spine_schema.sql is the verified Tier 4.1 two-table minimum. Extensions use numbered migration files under runtime/schema/migrations/. Verified artifacts are never rewritten.
- [ADR-SEED-005] HERMES_CIS_BRIEFING_PATH is transitional: Retired at Tier 5.3 after AGENTS.md canary passes all 4 active profiles. Not before.
- [ADR-SEED-004] Browser role enforcement at router layer: Role badge derived from gateway endpoint/profile only. Implementation directives route only to hermes-v4impl port 8646. Drafter and Reviewer endpoints blocked from execution actions. Enforced at Tier 7.
- [ADR-SEED-003] Role identity must be runtime-derived: Hermes role identity must come from HERMES_HOME and gateway endpoint, not from briefing text or model self-description. Terminal sessions must print HERMES_HOME before any FINAL_DIRECTIVE.
- [ADR-SEED-002] Verification-hardening rule: V4 Implementer self-report is not a source of truth. Completion accepted only after deterministic evidence: git diff, test output, DB queries, endpoint responses, service health, browser/UI state, independent reviewer pass/fail.
- [ADR-SEED-001] Dependency graph build order: CIS is built tier by tier per CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md. Nothing built before its dependencies exist.
- [ADR-SEED-009] HCP export is currently CIS-scoped: generate_hcp.py assumes the CIS infrastructure project, including CIS-specific static config, output packet location, and current single-project spine structure. Before CIS manages a second project, HCP export must be refactored to project-agnostic parameterization. The refactor is gated on a project isolation model decision: per-project repos/project roots with separate spines versus one shared spine with project_id filtering.
- [ADR-SEED-008] External advisor packet remains permanent: PROJECT_CONTEXT_PACK_UPLOAD/HCP_* remains the canonical external-model context packet for ChatGPT, Claude, and other frontier-model escalation after Tier 5. AGENTS.md serves Hermes-native context; HCP serves external advisor context.
- [ADR-SEED-007] AGENTS.md gateway loading mechanism: AGENTS.md is loaded from cwd or TERMINAL_CWD in gateway mode, not automatically from git root. Gateway processes require TERMINAL_CWD=/mnt/projects/cis to load CIS AGENTS.md. CLI sessions may load CIS AGENTS.md when launched from the CIS repo root.

## 5. Open Questions
- [OQ-SEED-006] deliberation_rounds schema is lossy: no reviewer_output column exists, only reviewer_signal. Reviewer reasoning and full output are discarded at the spine layer — they exist only in orchestrator stdout. This undercuts the project goal of preserving actual reasoning. Schema needs a reviewer_output TEXT column to durably persist reviewer deliberation content.
- [OQ-SEED-003] Should stale context pack folder cleanup (Tier 5.7) wait for first successful generate_all.py run or be done manually before Tier 5 build begins?
- [OQ-SEED-001] Google Drive backup integrity unverified
- [OQ-SEED-004] Closeout trigger design: define how CIS automatically requires closeout when a dependency-graph/build-plan node changes to COMPLETE. Should closeout be state-write triggered (node completion), gate-gated (runner must pass), or externally pulsed (cron watchdog)? Implementation likely in Tier 6 Pipeline Integration.

## 6. Next Actions
- [NA-SEED-017] (Tier front-door) FD.1 BASELINE VERIFIED: 11 existing MCP tools (docstring stale — says 9, actual 11). chromadb 1.5.9, s-transformers 5.5.0, 8 router routes, runtime/mcp/ clear. 3 dispatch tool names (cis_dispatch_drafter, _reviewer, _implementer) confirmed no collision. ADR-SEED-014 caveat RETIRED for FD.1 — drafter_start.py hardcodes /mnt/projects/cis, no home resolution. Durability note: hardcoded path breaks if repo relocates. FD.1 target: 14 tools total after adding 3 dispatch tools. Scope unchanged: add 3 dispatch tools + symlink only.
- [NA-SEED-018] (Tier Phase 0) Build loop-breaker for successful-repeat tool calls. Root cause: tool_guardrails.py only counts failures/no-progress reads. Successful identical calls (same tool_name+args) are invisible. FIRST test config-only: hard_stop_enabled:true + same_tool threshold. BUILD TARGET: extend ToolCallSignature counter to count regardless of success/failure, halt after N.

## 7. Active Blockers
- [BLK-SEED-006] Loop-breaker gap: successful repeated identical tool calls (same tool_name+args) are invisible to the built-in guardrail. agent/tool_guardrails.py counters only key on failures and no-progress reads. Model can loop ~20x issuing the same successful call (e.g. skill_view) with zero intervention. Fix needed in Phase 0 before autonomous operation.
- [BLK-SEED-004] Google Drive backup integrity unverified

## 8. Recent Pipeline Runs (last 5)
- [run-1010c3076e084] Add a dark-mode toggle to the portal settings panel — ESCALATE (3 rounds, 2026-06-24T18:33:44.980801+00:00)
- [run-efd77a31b50c4] Add a dark-mode toggle to the portal settings panel. — CONSENSUS_REACHED (0 rounds, incomplete)
- [run-5d2a0f1ceda54] test wiring — CONSENSUS_REACHED (0 rounds, incomplete)
- [run-5f1b4fe87b7f4] Chat-to-Pipeline Inference Trigger — connect Chat tab to CIS pipeline via model- — CONSENSUS_REACHED (0 rounds, incomplete)
- [run-f69f096ebadb4] test from portal — ERROR (0 rounds, incomplete)

## 9. Eric Gate Status
- Workflow run: N/A (direct Eric Gate — no deliberation run)
- Status: IMPLEMENTED
- Decided at: 2026-06-13 07:41 UTC
- Goal: Tier 10 CIS UI / Custom Display Views specification approved and implemented
- Scope: Tier 10 implemented per approved specification (docs/CIS_TIER_10_CIS_UI_CUSTOM_DISPLAY_VIEWS_SPECIFICATION.md, commit c2a3f20).
6 React display views, 1 Flask blueprint (8 GET endpoints), 57 passing tests, 5 gate scripts.
No write endpoints, no pipeline bypass, no secrets in frontend.
Commit: IMPLEMENTED at <latest>.

## 10. Verification Hardening Rule
V4 Implementer self-report is not a source of truth.
Completion is accepted only after deterministic evidence verifies the result.
Accepted evidence:
  1. git diff / file system state
  2. build and test command output
  3. database queries
  4. endpoint/curl responses
  5. service health checks
  6. browser/UI verification
  7. independent reviewer/verifier pass/fail
Implementer reports claimed changes → separate verification gate checks
deterministic evidence → PASS only if evidence matches directive scope.
Missing/ambiguous/self-reported evidence → status remains UNVERIFIED.

## 11. Role Identity Rule
Hermes role identity must be derived from HERMES_HOME and gateway endpoint,
not from briefing text or model self-description.
Terminal sessions must print HERMES_HOME before any FINAL_DIRECTIVE.
Browser app: role badge derived from gateway endpoint/profile only.
Implementation directives route only to hermes-v4impl port 8646.

## 11.5. READ_ONLY_STANDING_BY Startup Protocol
On fresh session start, context handoff, or ambiguous startup/orientation prompt,
Hermes enters READ_ONLY_STANDING_BY mode. In this mode Hermes may only read context
and run inspection-only commands to confirm HEAD, dirty status, current completed
tier, and next allowed action. Inspection-only commands are: git status, git rev-parse,
grep, sed, cat, sqlite3 SELECT, and file listing. Hermes must not modify files, run
imports, apply migrations, patch code, alter databases, stage files, commit, or start
implementation. Hermes exits READ_ONLY_STANDING_BY only after Eric gives an explicit
execution instruction, such as PROCEED, IMPLEMENT, FINAL_DIRECTIVE, or an unambiguous
approval to perform a specific action. The required startup response ends with
'Standing by' and no next action is executed. This rule applies to all active Hermes
profiles regardless of which profile receives the session start signal.

## 12. Seed Intent — Eric's Own Words
Do not summarize, rephrase, or replace with model interpretation. Reproduce verbatim.

Source: session_20260520_215551_16187f.json
> I don't want summaries, I am trying to build a system that works from the raw files.
> let me explain what I am trying to do. yesterday I installed three hermes folders one
> for deepseek v4, one for deepseek r1 and one for qwen 30b MOE. then made a ui interface
> with a chat for each so that I can have the models verify each others opinions on topics
> and check the code thats written since they all have different training data and different
> blind spots. I then was to build a knowledge base in the sqlite db that will vectorized
> and saved to a vdb.

Source: session_20260525_232304_b2d3b2.json
> the LLMs are the tools, I am trying to get LLMs to help me think by contributing
> factual information and expertise. when I sit down and interact with the LLMs they
> don't remember anything and the overall vision is not apparent to combine the vision
> of where I am trying to get to, to why we are working on the immediate task.

Source: session_20260518_203801_265262.json
> I need checks and balance, I am not a coder and if I don't trust something one of
> you says I have to be able to paste it for another model to evaluate and give me
> independent analysis. that is what claude and chatgpt did to each other. I need a
> worker who is constrained to my working methods and two objective reviewers as
> expert advisors.

## 13. Session Handoff (from spine)
**June 27-29: Front Door, Claude Audit, Reconciliation** — 2026-06-29
Git HEAD: `9523663`

**Built:** June 27 (Hermes): Built CIS front door - adapter API on port 5000, intent alignment, knowledge base (287K messages FTS5+ChromaDB), human-readable status endpoint, 6-phase roadmap. June 28 (Claude): Audited all work - PASS. Caught near-miss (therapy notes staged). Committed 4c3d396. June 29 (Hermes): Port check verified 8642 DOWN. Fixed agents_static.yaml. Pre-commit hook built (auto-regen HCP+AGENTS.md on commit). Session handoff spine table added.
**Decisions:** Model decision: Portal stays local Qwen+GLM. Claude API too expensive for regular rotation - manual copy-paste only. Claude handoff document: docs/PHASE1_ROOT_DIRECTIVE_FOR_CLAUDE.md (5 tasks, only 1/3/4 active - Tasks 2+5 deferred per DEV-PIVOT-06 §6).
**Eric:** Leave portal as-is (local Qwen+GLM). Claude manual only. If you can fix it go ahead. The LAN issue is a red herring - single user network. The pivot trajectory is still valid.
**Gateway:** Verified 2026-06-29: 8642 DOWN, 8643-8646 UP, NeMo 8800 UP, Qwen llama-server 8002 LAN-exposed (0.0.0.0)
**Next:** 1. Eric gives Claude PHASE1_ROOT_DIRECTIVE - do Tasks 1,3,4 only (Qwen bind fix, start prime 8642, restart gateways for MCP). 2. Eric does exhaustive legacy review, creates intentions roadmap. 3. Use pipeline to compare intentions with current state. 4. Build what Eric asked for.
**Claude context:** Working dir: /mnt/projects/cis/. Flask on 127.0.0.1:5000. ChromaDB: data/chroma_data/. Spine: data/cis_memory.db. Hermes config: ~/.hermes-v4pro/config.yaml. HCP auto-regenerated by pre-commit hook. Claude: read HCP_01 first, treat spine as authoritative.

## 14. Evidence-Backed Response Rule
CIS must not rely on trust-based agent self-reporting.
Every consequential agent response must be accompanied by one of:
  1. Raw local evidence:
     - command and raw terminal output
     - git status/show output
     - file contents or grep output
     - database query output
     - test output
     - generated artifact path plus verification output
  2. External research evidence:
     - cited source
     - retrieved document reference
     - quoted or summarized source material with citation
Agent summaries may follow evidence, but must not replace it.
Claims such as "passed," "clean," "unchanged," "verified,"
"no mutation," "ready to commit," or "complete" are incomplete
unless accompanied by evidence.
Required report pattern:
  1. State the command or source.
  2. Paste the raw evidence.
  3. Then provide a short interpretation.
The operator should not be required to manually rerun routine
verification commands unless Hermes lacks access, the command
requires operator-only credentials, or an external advisor
explicitly requests independent human verification.
The Verification Hardening Rule (Section 9) is the V4 Implementer-
specific application of this general principle.
