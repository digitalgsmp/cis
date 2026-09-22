# CIS — AGENTS.md
Generated: 2026-09-22 07:01 UTC | Run: run-ef2d372e0a1c | Latest pipeline: run-4bbeea78056e2607-1788140226
Source: SQLite spine + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_agents_md.py

## 1. Current Build Phase
Phase PD CLOSED. Phase 0 CLOSED (loop-breaker deployed, BLK-SEED-006 RESOLVED). Current: Control Plane Observation Pipeline — spec phase REVISION 3, 4 review rounds complete. Pipeline team: Brainstorm (8644), Drafter (8645), Qwen Reviewer (8643), GLM Reviewer (8647), Implementer (8646), GLM Verifier (8648).
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
| Brain | hermes-brainstorm | 8644 | deepseek-v4-pro | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Draft | hermes-v4pro | 8645 | deepseek-v4-pro | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Review1 | hermes-r1 | 8643 | qwen/qwen3.7-max | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Review2 | hermes-glm-reviewer | 8647 | z-ai/glm-5.2 | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Menter | sandboxed-claude-code | n/a (kernel sandbox) | claude-code (sandboxed coder) | n/a | No | Sandboxed — dispatched via tools/run_claude_sandbox.sh (R1, menter-reviewer-connection) |
| Verify | hermes-glm-verifier | 8648 | z-ai/glm-5.2 | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Prime/Chat | hermes-prime | 8642 | deepseek-v4-pro | medium | Yes | Running — verified 2026-07-07 via ss -tlnp |

### Hermes Source Patches
- /home/eric/.hermes/hermes-agent/run_agent.py:9782 — Added api.deepseek.com to _supports_reasoning_extra_body() allowlist
- /home/eric/.hermes/hermes-agent/plugins/model-providers/deepseek/__init__.py — DeepSeekProfile with build_api_kwargs_extras() for thinking params
- /home/eric/.hermes/hermes-agent/gateway/platforms/api_server.py:1255 — Extracts reasoning_content from agent result, surfaces in API response
- /home/eric/.hermes/hermes-agent/agent/usage_pricing.py:731 — Added completion_tokens_details.reasoning_tokens fallback

## 4. Active Decisions
Full text/reasoning of any decision: `project_decisions` table in the spine DB — `sqlite3 data/cis_memory.db "SELECT * FROM project_decisions WHERE id='<ID>'"`. This table is the canonical source; the list below is an index, not a summary.
- [ADR-SEED-016] Enforcement Primitive Approved
- [ADR-SEED-015] Enforcement architecture: three-layer process isolation
- [ADR-SEED-014] BLK-SEED-005 refresh-bug root cause: get_default_hermes_root collapses onto prime unit
- [ADR-SEED-012] Orchestrator validation contract
- [ADR-SEED-013] Retire Kanban as required pipeline transport
- [ADR-SEED-010] Project isolation model: --project-root
- [ADR-SEED-006] Spine migration strategy
- [ADR-SEED-005] HERMES_CIS_BRIEFING_PATH is transitional
- [ADR-SEED-004] Browser role enforcement at router layer
- [ADR-SEED-003] Role identity must be runtime-derived
- [ADR-SEED-002] Verification-hardening rule
- [ADR-SEED-001] Dependency graph build order
- [ADR-SEED-009] HCP export is currently CIS-scoped
- [ADR-SEED-008] External advisor packet remains permanent
- [ADR-SEED-007] AGENTS.md gateway loading mechanism

## 5. Open Questions
- [OQ-SEED-006] deliberation_rounds schema is lossy: no reviewer_output column exists, only reviewer_signal. Reviewer reasoning and full output are discarded at the spine layer — they exist only in orchestrator stdout. This undercuts the project goal of preserving actual reasoning. Schema needs a reviewer_output TEXT column to durably persist reviewer deliberation content.
- [OQ-SEED-003] Should stale context pack folder cleanup (Tier 5.7) wait for first successful generate_all.py run or be done manually before Tier 5 build begins?
- [OQ-SEED-001] Google Drive backup integrity unverified
- [OQ-SEED-004] Closeout trigger design: define how CIS automatically requires closeout when a dependency-graph/build-plan node changes to COMPLETE. Should closeout be state-write triggered (node completion), gate-gated (runner must pass), or externally pulsed (cron watchdog)? Implementation likely in Tier 6 Pipeline Integration.

## 6. Next Actions
- [Enforcement — Container Isolation (ADR-015/016)] (Tier ENFORCEMENT) Enforcement — Container Isolation (ADR-015/016)

## 7. Active Blockers
- [BLK-SEED-004] Google Drive backup integrity unverified

## 8. Recent Pipeline Runs (last 5)
- [run-4bbeea78056e2607-1788140226] Modify tools/ask_history.py so it merges keyword (FTS5) results with its existin — PENDING (0 rounds, incomplete)
- [run-4bbeea78056e2607-1788129615] Modify tools/ask_history.py so it merges keyword (FTS5) results with its existin — PENDING (0 rounds, incomplete)
- [run-4bbeea78056e2607-1788126284] Modify tools/ask_history.py so it merges keyword (FTS5) results with its existin — PENDING (0 rounds, incomplete)
- [run-4bbeea78056e2607-1788122307] Modify tools/ask_history.py so it merges keyword (FTS5) results with its existin — PENDING (0 rounds, incomplete)
- [run-4bbeea78056e2607-1788121167] Modify tools/ask_history.py so it merges keyword (FTS5) results with its existin — PENDING (0 rounds, incomplete)

## 9. Eric Gate Status
- Workflow run: run-e70293544935a92e-1787973534
- Status: APPROVE
- Decided at: 2026-08-30T17:35:14Z
- Goal: Write one short markdown file to enforcement/mwl-proof-v2/RESULTS/ recording whether runtime/abstraction/pipeline_relay.py still sanitizes FTS5 keywords with a character class that omits the forward s

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

## 11.6. External Advisor Role
Until CIS is self-reliant, ChatGPT and Claude function as external
advisor-deliberators for the build. They temporarily provide the
proposal/review challenge layer that the internal DRAFT → REVIEW loop
is intended to automate later. They do not execute, do not maintain
canonical state, and do not bypass Eric Gate. Their role is to help
Eric evaluate Hermes proposals, identify gaps, challenge scope, and
produce bounded directives before V4 Implementer executes.

ChatGPT reads this repo through Codex, connected to private repo
digitalgsmp/cis. Codex sees ONLY the pushed tree -- not the VM, running
containers, /data (gitignored), or Hermes state volumes. Ask Eric for
those; never assume the repo is the whole system.

Codex's standing duty is the lineage check: trace a claim, card, or build
item back through commit history to the decision that created it, and say
plainly when the lineage does not hold -- a doc asserting what no commit
supports, two docs disagreeing, or an INVALIDATED DEV-PIVOT that still has
live dependents. Claude Code works the same repo from inside the VM.
Disagreement between them is the point; Eric Gate resolves it.

Model reality (2026-09-14): DeepSeek and OpenRouter credit is exhausted,
all keys revoked, those gateways DEAD until repointed. Claude Code and
Codex run on Eric's subscriptions. Do not propose work that assumes a
paid per-token gateway.

Host continuity: tools/development/cli.py (see CLAUDE.md for detail).

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
