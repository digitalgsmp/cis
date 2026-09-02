# CIS Current State
Version: 2.8
Date: 2026-09-02
Authority: Eric (Architect)
Status: Phase PD CLOSED. Phase 0 CLOSED (loop-breaker deployed, BLK-SEED-006 RESOLVED). Current: Control Plane Observation Pipeline — spec phase REVISION 3, 4 review rounds complete. Pipeline team: Brainstorm (8644), Drafter (8645), Qwen Reviewer (8643), GLM Reviewer (8647), Implementer (8646), GLM Verifier (8648).
Direction: Phase 0: Close the loop-breaker gap. Enforcement primitive proven (5 walls held, all passes). Loop-breaker root cause: successful repeated identical tool calls not caught by guardrail. First test config-only (hard_stop_enabled + same_tool threshold). Build target: counter for identical ToolCallSignature regardless of success/failure.

Generated: 2026-09-02 09:45 UTC | Run: run-a09f7491e2ef
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

---

## Current Objective

**Phase PD CLOSED. Phase 0 CLOSED (loop-breaker deployed, BLK-SEED-006 RESOLVED). Current: Control Plane Observation Pipeline — spec phase REVISION 3, 4 review rounds complete. Pipeline team: Brainstorm (8644), Drafter (8645), Qwen Reviewer (8643), GLM Reviewer (8647), Implementer (8646), GLM Verifier (8648).**

**HEAD:** `e13ec03`.

**AGENTS.md-native context architecture.**
AGENTS.md serves Hermes-native internal context for all 4 active gateways.
HCP_* files in PROJECT_CONTEXT_PACK_UPLOAD/ are the permanent external advisor
packet for ChatGPT, Claude, and frontier-model escalation.
HCP is not deprecated; manual drift is what Tier 5 eliminates by generating HCP from spine.
AGENTS.md is auto-loaded by all 4 active gateways via TERMINAL_CWD=/mnt/projects/cis.
HERMES_CIS_BRIEFING_PATH is permanently retired from all 5 profile .env files.

Do NOT start Tier 7, Judge, UI, VDB/Chroma, router reclassification, or MCP.

**Tier 0 — Orchestrator (committed `9d84351`):** `runtime/orchestrator.py` +
`runtime/orchestrator_config.yaml`. Drafter→Reviewer deliberation loop functional.
Acceptance test: PASS (CONSENSUS_REACHED in Round 2, ~256s). Removes Eric from
manual API relay role. Bounded: per-agent timeouts, input truncation, test mode.

**Tier 1 — Deterministic Gate Suite (committed `bc49beb`–`635a646`):**
Five base gates + runner at `tools/gates/`. All executable, syntax-clean, individually
tested. Runner chains gates in sequence, exits on first failure.

**Tier 2 — Kanban Coordination Layer (committed `2989c5b`):**
Gateway env normalization, shared `cis-pipeline` board created, systemd templates
backed up to `runtime/config/systemd/`, ENV_MANIFEST.md documented. Kanban cross-profile
visibility confirmed. Limitation: Hermes v0.13 has no custom lanes — CIS stages encoded
in card title/body metadata.

**Tier 3 — Pipeline Smoke Test (PASS_WITH_LIMITATIONS):**
Orchestrator completed 3 DRAFT→REVIEW rounds (Kanban retired per ADR-013).
Result: ESCALATE with substantive unresolved objections (Research gateway missing, role
boundary violation, deadlock breaker). gate_runner.sh: all 5 gates PASS. No manual relay.

**Tier 4 — SQLite Spine (committed `88ea25f`, `0c19b4d`, `ec14615`):**
Two-table minimum schema plus 4 context export state tables (6 total): `workflow_runs`,
`deliberation_rounds`, `project_decisions`, `open_questions`, `next_actions`,
`active_blockers`. `database.py` write/read layer with allowlist validation.
`gate_db_state.py` deterministic verification gate. DB at `data/cis_memory.db`.

**Known limitation:**
- Orchestrator `--output` preserves only final-round detail (Tier 6 backlog)
- Hermes Kanban v0.13 has no custom lanes (CIS stages in card metadata)
- HCP files manually reconciled until Tier 5.4–5.6 complete
- TERMINAL_CWD required for gateway AGENTS.md discovery (deprecated but functionally required)

**Tier 5 — Context Export Pipeline:** Per Dependency Graph
Build Plan v2.0 (`docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md`).

**Phase A findings (corrected 2026-06-07):**
- Hermes Agent v0.13.0 — Kanban fully available
- Kanban shareable via `HERMES_KANBAN_DB` + `HERMES_KANBAN_HOME` — confirmed
- Cross-profile Kanban visibility confirmed
- AGENTS.md loaded from cwd or TERMINAL_CWD in gateway mode, NOT automatically from git root.
  Gateway processes require TERMINAL_CWD=/mnt/projects/cis. CLI sessions load when launched from CIS repo root.
- `HERMES_CIS_BRIEFING_PATH` RETIRED from all profiles at Tier 5.3 (commit `80f934c`)
- Preferred architecture: AGENTS.md (context) + gate scripts (verification) + SQLite spine (knowledge) + HCP export (external advisors)

CIS is a Hermes-native adversarial deliberation engine. The pipeline is the product. The state spine is bidirectional: it briefs the pipeline from verified history and receives verified outputs from completed pipeline runs.

**Claude + ChatGPT deliberation converged (2026-06-01):** The next build is not
generic unified memory. It is the deterministic pipeline foundation, gated by
Phase A substrate verification before any code build begins.

**Pipeline architecture:**
```
TRIAGE → RESEARCH → DRAFT → REVIEW ↔ LOOP → CONSENSUS → ERIC_GATE
→ IMPLEMENT → VERIFY → STATE_WRITE → EXPORT → DONE
```

- **TRIAGE:** Topic classifier assigns Research profile via Kanban card
- **RESEARCH:** hermes-prime grounds topic in evidence (NeMo firewall + Tavily)
- **DRAFT:** hermes-v4pro generates structured proposal from research + spine briefing
- **REVIEW:** hermes-r1 adversarially challenges proposal; emits OBJECTIONS (loop back)
  or CONSENSUS_REACHED (promote)
- **CONSENSUS:** Waiting for Eric. Pass → IMPLEMENT. Redirect/Insight → DRAFT with note
- **ERIC_GATE:** Human sanity/output gate. Eric reviews resolved proposal. Not bypassable.
- **IMPLEMENT:** hermes-v4impl executes FINAL_DIRECTIVE only. No deliberation.
- **VERIFY:** Deterministic bash/Python gate scripts check evidence. PASS or FAIL.
  On FAIL: returns to IMPLEMENT with failure reason.
- **STATE_WRITE:** Gated worker writes verified results to SQLite spine (only after VERIFY PASS).
  Triggers AGENTS.md + HCP export pipeline. Git commit.
- **EXPORT:** AGENTS.md (all Hermes profiles) + HCP_ files (ChatGPT/Claude). Generated, not manual.
- **DONE:** Pipeline run complete. Blackboard artifacts archived. Spine enriched.

**Phase 0 recovery is COMPLETE.** Git versioning at github.com/digitalgsmp/cis.
All four V4 Pro gateways healthy. Qwen active — port 8644, model qwen3-vl-30b, serving as second reviewer/evaluator. Deliberation is DeepSeek v4-pro draft + DeepSeek v4-pro & Qwen dual review.
**AdvisorChat Input Router v0.1 is COMPLETE.** classify_route() dispatches to correct agent.

**Verification-hardening rule (2026-05-31):** V4 Implementer self-report is not a source of truth. Completion is accepted only after deterministic evidence verifies the result. Accepted evidence:   1. git diff / file system state   2. build and test command output   3. database queries   4. endpoint/curl responses   5. service health checks   6. browser/UI verification   7. independent reviewer/verifier pass/fail Implementer reports claimed changes → separate verification gate checks deterministic evidence → PASS only if evidence matches directive scope. Missing/ambiguous/self-reported evidence → status remains UNVERIFIED.

**Evidence-Backed Response Rule**

CIS must not rely on trust-based agent self-reporting.
Every consequential agent response must be accompanied by one of:
  1. Raw local evidence: command output, git status/show, file contents,
     DB query output, test output, generated artifact path plus verification.
  2. External research evidence: cited source, retrieved document,
     quoted or summarized source material with citation.
Agent summaries may follow evidence, but must not replace it.
Claims such as "passed," "clean," "unchanged," "verified," "no mutation,"
"ready to commit," or "complete" are incomplete unless accompanied by evidence.
Report pattern: state command/source → paste raw evidence → short interpretation.
The operator should not be required to manually rerun routine verification
commands unless Hermes lacks access, the command requires operator-only credentials,
or an external advisor explicitly requests independent human verification.
The Verification Hardening Rule is the V4 Implementer-specific application of
this general principle.

---

## Model Roles (Router v0.1)

| Label | Agent | Gateway | Port | Model | Function | Boundaries |
|-------|-------|---------|------|-------|----------|------------|
| Research / Evidence | hermes-prime | NeMo → 8642 | 8800 | deepseek-v4-flash | Evidence firewall + current-facts search | No code, no files, no terminal |
| V4 Drafter | hermes-v4pro | Direct | 8645 | deepseek-v4-pro (thinking) | Proposal author, directive drafter | No execution, no file edits |
| V4 Reviewer | hermes-r1 | Direct | 8643 | deepseek-v4-pro (thinking) | Adversarial reviewer, validator | No execution, no code generation |
| V4 Implementer | hermes-v4impl | Direct | 8646 | deepseek-v4-pro (thinking, xhigh) | Execute FINAL_DIRECTIVE only | No deliberation, no architecture proposals |

**Qwen (hermes-qwen)** remains active on port 8644 but is removed from the main
AdvisorChat UI and routing flow. Deferred from implementation work. JUDGE_REQUEST
remains backend-capable but not exposed in the UI.

### Advisor Loop Architecture (Router v0.1)

```
User prompt
  → classify_route() — 8-pass classifier
     ├─ Research signals → Research/Evidence (NeMo:8800 → Flash:8642)
     ├─ Drafter signals → V4 Drafter (8645)
     ├─ Reviewer signals → V4 Reviewer (8643)
     ├─ Research + Drafter → multihop (NeMo preflight → V4 Drafter)
     ├─ FINAL_DIRECTIVE prefix → V4 Implementer (8646, deterministic)
     ├─ JUDGE_REQUEST prefix → Qwen (8644, deterministic, backend)
     └─ Ambiguous → V4 Drafter (8645, low confidence)

  → POST /api/advisor/route (auth-gated, X-CIS-API-Key)
  → routing_decisions table — all routes logged
```

**Architecture principle:** NeMo is the behavioral/evidence firewall. The
classify_route() 8-pass classifier is the routing gate. V4 Implementer is the
execution gate. Qwen is deferred — future judge/evaluator role only.

**Why V4 Drafter/Reviewer/Implementer are direct (not through NeMo):** NeMo's
response pipeline strips `reasoning_content` and `reasoning_tokens` from
DeepSeek thinking models (Gate 5C). NeMo preflight is used for evidence
collection, then calls go direct.

Claude and ChatGPT: Tier 3 escalation — pass/fail review when deliberation
does not satisfy Eric. No direct execution authority.

---

## Current System State

### Infrastructure
- proxmox_host: wander at 192.168.1.200, PVE 9.1.6
- primary_vm: creative-vm (VM 100), Ubuntu 24.04, 192.168.1.15
- storage: virtio0 500G local-lvm, virtio1 250G local-lvm
- passthrough: virtio2 10TB archive, virtio3/5/6 SSDs
- snapshot_status: RESOLVED — cis-snapshot deployed on root@wander
- backup_status: local archive at /mnt/archive/cis_backup_20260524_112430.tar.gz
- github_repo: https://github.com/digitalgsmp/cis

### Advisor Gateways

| Gateway | Port | HERMES_HOME | Model | Reasoning | NeMo? | Status |
|---------|------|-------------|-------|-----------|-------|--------|
| Brain (hermes-brainstorm) | 8644 | /home/eric/.hermes-brainstorm | deepseek-v4-pro | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Draft (hermes-v4pro) | 8645 | /home/eric/.hermes-v4pro | deepseek-v4-pro | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Review1 (hermes-r1) | 8643 | /home/eric/.hermes-r1 | qwen/qwen3.7-max | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Review2 (hermes-glm-reviewer) | 8647 | /home/eric/.hermes-glm-reviewer | z-ai/glm-5.2 | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Menter (hermes-v4impl) | 8646 | /home/eric/.hermes-v4impl | deepseek-v4-pro | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Verify (hermes-glm-verifier) | 8648 | /home/eric/.hermes-glm-verifier | z-ai/glm-5.2 | xhigh | No | Running — verified 2026-07-07 via ss -tlnp |
| Prime/Chat (hermes-prime) | 8642 | /home/eric/.hermes | deepseek-v4-pro | medium | Yes | Running — verified 2026-07-07 via ss -tlnp |

**Context:** AGENTS.md auto-loaded by all 4 active gateways via TERMINAL_CWD=/mnt/projects/cis. HERMES_CIS_BRIEFING_PATH retired.

Service files (all user-mode systemd — topology repaired 2026-06-07):
- `hermes-gateway.service` — Flash/Research (HERMES_HOME=/home/eric/.hermes, port 8642)
- `hermes-gateway-r1.service` — V4 Reviewer (HERMES_HOME=/home/eric/.hermes-r1, port 8643)
- `hermes-gateway-v4pro.service` — V4 Drafter (HERMES_HOME=/home/eric/.hermes-v4pro, port 8645)
- `hermes-gateway-v4impl.service` — V4 Implementer (HERMES_HOME=/home/eric/.hermes-v4impl, port 8646)
- `hermes-gateway-qwen.service` — Qwen (HERMES_HOME=/home/eric/.hermes-qwen, port 8644, active — second reviewer/evaluator)
- `nemo-fast.service` — NeMo Guardrails on port 8800

NeMo path: `/mnt/projects/cis/runtime/rails/` (venv at `.venv`, configs at `configs/`)

### Hermes Source Patches (permanent — Gate 2/5C)

1. `/home/eric/.hermes/hermes-agent/run_agent.py:9782` — Added api.deepseek.com to _supports_reasoning_extra_body() allowlist
2. `/home/eric/.hermes/hermes-agent/plugins/model-providers/deepseek/__init__.py` — DeepSeekProfile with build_api_kwargs_extras() for thinking params
3. `/home/eric/.hermes/hermes-agent/gateway/platforms/api_server.py:1255` — Extracts reasoning_content from agent result, surfaces in API response
4. `/home/eric/.hermes/hermes-agent/agent/usage_pricing.py:731` — Added completion_tokens_details.reasoning_tokens fallback

### CIS Application
- Flask backend: running at 127.0.0.1:5000
- React UI: running, accessible at http://127.0.0.1:5000/ui
- Database: SQLite at data/cis_memory.db (spine) + data/kanban.db (coordination)
- Advisor Chat: four-panel UI (Research/Evidence, V4 Drafter, V4 Reviewer, V4 Implementer)
  with shared input and automatic routing via POST /api/advisor/route
- Router: classify_route() 8-pass classifier, routing_decisions table, auth-gated
- Qwen: removed from main UI, deferred from implementation, JUDGE_REQUEST backend-capable
- Reconciliation feature: POST /api/reconciliation/reconcile, divergent/consensus maps
- Collab Tracker: built and functional
- Advisor Round Wizard: built, 7-step flow working
- Session import pipeline: import_session.py working, auto-import implemented

### Knowledge Base
- collab_session_messages table: exists, stores raw Hermes session content
- Claude/ChatGPT sessions: NOT being imported
- Vector DB: NOT YET BUILT
- Layer 2 retrieval: NOT YET BUILT

### Google Drive Connection
- OAuth connected via google-workspace skill (read-only)
- 12 chat transcript files downloaded: 3.4MB total
- Path: /mnt/projects/ai_execution_infrastructure/03_CHAT_CAPTURE/raw/drive_imports/
- Scope: drive.readonly only — no write, delete, or share permissions

### Phase 3A Context Loader (PASS — 2026-05-29)
- Command: `python3 /mnt/projects/cis/tools/generate_context_briefing.py --write`
- Output: `/mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md`
- Reads 8 source files. OQ-010 RESOLVED — generator source hierarchy confirmed.
- Eric no longer has to manually assemble the handoff

### Phase 3B — Automated Session Continuation (PASS — 2026-05-29)
- Briefing auto-loads via ~/.hermes/.env + run_agent.py injection
- Eric fully removed from manual paste loop

### Phase 4A — Deterministic Verification (PASS — 2026-05-29)
- Standalone verifier: /mnt/projects/cis/tools/verify_context_briefing_freshness.py
- 9/9 tests passed. Exit-code convention documented.
- Integration PASS: wrapper runs freshness check before every interactive Hermes command

### Seed Intent Corpus (Phase 3A — 2026-05-29)
- /mnt/projects/cis/seed_intent_corpus/ created
- SEED_INTENT_EXCERPTS.md — 6 core excerpts from Eric's raw session archive
- SESSION_ORIENTATION_PROMPT.md — session-start briefing template
- 1,367 session files scanned; top 5 candidates identified by signal phrase density
- Excerpts preserve Eric's exact words — no model summaries

---

## Active Blockers

1. [BLK-SEED-004] Google Drive backup integrity unverified

---

## Next Safe Action

**Enforcement — Container Isolation (ADR-015/016) (Tier ENFORCEMENT)**

**Approved build order:**
1. Tier 0 — Deliberation Engine ✅ COMPLETE
2. Tier 1 — Deterministic Verification Gates ✅ COMPLETE
3. Tier 2 — Kanban Coordination Layer ⏸ DEFERRED
4. Tier 3 — Pipeline Smoke Test ✅ COMPLETE
5. Tier 4 — SQLite Spine ✅ COMPLETE
6. Tier 5 — Context Export Pipeline ✅ COMPLETE
7. Tier 6 — Pipeline Integration ✅ COMPLETE
8. Tier 7 — Full Durable Router Pipeline ⏸ DEFERRED
9. Tier 7.1 — Router Reclassification (archive route) ✅ COMPLETE
10. Tier 7.5a — Corpus Audit ✅ COMPLETE
11. Tier 7.5b — Clean Subset Import + FTS5 ✅ COMPLETE
12. Tier 8 — MCP Bridge ✅ COMPLETE
13. Tier 9 — Chroma/VDB ✅ COMPLETE
14. Tier 10 — CIS UI / Custom Display Views ✅ COMPLETE
15. Component 3.5 — Build-Plan Spine Authority ✅ COMPLETE
16. Tier 7R — Intent-to-Workflow Architecture Specification ✅ COMPLETE
17. 7R.1 — WorkIntent schema + scope registry + Micro1 exclusion ✅ COMPLETE
18. 7R.2 — CISAdapter (CIS domain only) ✅ COMPLETE
19. 7R.3 — SWAAdapter (validation use case) ⏸ DEFERRED
20. 7R.4 — Process Manager (state machine) ✅ COMPLETE
21. 7R.5 — Human approval gate integration ✅ COMPLETE
22. 7R.6 — Dead Letter / blocked handling ✅ COMPLETE
23. 7R.7 — Acceptance test suite ✅ COMPLETE
24. Tier 11A — Dashboard, Navigation, System Overview ✅ COMPLETE
25. Tier 11B — Eric Gate Approval Record ✅ COMPLETE
26. Tier 11C — Drafter-to-Reviewer Handoff ✅ COMPLETE
27. Tier 11D — Reviewer-Side Handoff ✅ COMPLETE
28. Tier 12 — Knowledge Base Ingestion ✅ COMPLETE
29. Tier 13 — Abstraction Layer ✅ COMPLETE
30. Enforcement — Container Isolation (ADR-015/016) ⬜ PENDING
31. Tier 3.5 — Complete Build-Plan Spine Authority: finish generator switchover so AGENTS.md Sections 6-7 read from build_plan_nodes, sync stale blockers/actions, regenerate context, pass export gates. ✅ COMPLETE
32. Tier 5 — Build Tier 5.1: generate_agents_md.py — reads spine + static config, writes AGENTS.md under 20000 chars ✅ COMPLETE
33. Tier 5 — Build Tier 5.1a: config/agents_static.yaml — static Layer B content: infrastructure, gateway table, source patches, seed intent, verification rule ✅ COMPLETE
34. Tier 5 — Run Tier 5.2: AGENTS.md canary test across all 4 active profiles ✅ COMPLETE
35. Tier 5 — Tier 5.3: Retire HERMES_CIS_BRIEFING_PATH from all 5 .env files after canary passes ✅ COMPLETE
36. Tier 5 — Build Tier 5.4: generate_hcp.py — reads spine, writes HCP_00 through HCP_09 ✅ COMPLETE
37. Tier 5 — Build Tier 5.5: generate_all.py — runs both generators, writes export manifest with SHA256 ✅ COMPLETE
38. Tier 5 — Build Tier 5.6: gate_export_agreement.sh — verifies AGENTS.md and HCP hashes match manifest ✅ COMPLETE
39. Tier 5 — Tier 5.7: archive stale context packs (PROJECT_CONTEXT_PACK, _GENERATED, _UPLOAD_GENERATED), keep PROJECT_CONTEXT_PACK_UPLOAD active ✅ COMPLETE
40. Tier 5 — Decide project isolation model for future CIS-managed projects before onboarding a second project or generating non-CIS HCP packets. Options: --project-root per-project structure, or --project-id shared spine structure. ✅ COMPLETE
41. Tier 5 — Build Tier 5 context export pipeline ✅ COMPLETE
42. Tier 6 — Closeout trigger design: define how CIS automatically triggers closeout when a dependency-graph/build-plan node changes to COMPLETE, PASS, or PASS_WITH_LIMITATIONS. Closeout validated by deterministic gates before next tier can start. Cron is passive watchdog only (stale exports, dirty git, failed gates, missing closeout) — not primary trigger. Implementation area: Tier 6 Pipeline Integration (STATE_WRITE → EXPORT → CLOSEOUT → DONE). ✅ COMPLETE
43. Tier 6 — Harden Exact-Format Instruction Rule: ensure external advisors (ChatGPT, Claude) receive the exact-format instruction in durable HCP context. Advisors must request only COMMAND + OUTPUT + Proceed/Blocked without asking for interpretation, summary, result, or evidence reference. Current placement is in hcp_static.yaml under hcp_06 — verify it survives HCP regeneration and is visible in the advisor protocol section. ✅ COMPLETE
44. Tier ControlPlane — Complete Control Plane spec through review 🔄 IN PROGRESS
45. Tier Phase 0 — Build loop-breaker for successful-repeat tool calls. Root cause: tool_guardrails.py only counts failures/no-progress reads. Successful identical calls (same tool_name+args) are invisible. FIRST test config-only: hard_stop_enabled:true + same_tool threshold. BUILD TARGET: extend ToolCallSignature counter to count regardless of success/failure, halt after N. ⬜ PENDING
46. Tier enforcement — Draft TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md as proposal only. Route through Claude audit + ChatGPT audit + Eric approval before any /opt/cis-control file lands. ✅ COMPLETE
47. Tier enforcement — Execute §14 raw-evidence capture plan from TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md. Start with operator-only override-plane test (bare-shell, 9 steps per §7 Parts A+B). No implementation until evidence captured and Eric-approved. 🚫 BLOCKED
48. Tier enforcement — Draft §7/§14 Test-Rig Amendment to TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md. Resolve structural contradiction by allowing override-plane evidence test against disposable test root /mnt/cache/catalog/override-plane-test/<run_id>/control/. ✅ COMPLETE
49. Tier enforcement — Execute §7 Parts A+B override-plane evidence test (9 steps) against disposable test root per Amendment 1 (revised). Requires: (1) root-owned control directory with sentinel created/removed via sudo, (2) separate control and workspace host directories with RO/RW mounts respectively, (3) stat/realpath/docker inspect/mount evidence before the 9-step test. No production /opt/cis-control. No hooks. No Hermes worker. ✅ COMPLETE
50. Tier front-door — FD.1 BASELINE VERIFIED: 11 existing MCP tools (docstring stale — says 9, actual 11). chromadb 1.5.9, s-transformers 5.5.0, 8 router routes, runtime/mcp/ clear. 3 dispatch tool names (cis_dispatch_drafter, _reviewer, _implementer) confirmed no collision. ADR-SEED-014 caveat RETIRED for FD.1 — drafter_start.py hardcodes /mnt/projects/cis, no home resolution. Durability note: hardcoded path breaks if repo relocates. FD.1 target: 14 tools total after adding 3 dispatch tools. Scope unchanged: add 3 dispatch tools + symlink only. 🔄 IN PROGRESS

---

## Accepted Limitations

- **NeMo semantic classifier:** Uses embedding-based intent matching. New query
  types may need manual pass-through intents.
- **V4-Pro direct routing:** V4-Pro cannot pass through NeMo because NeMo strips
  `reasoning_content` and `reasoning_tokens` from DeepSeek thinking models
  (accepted architectural limitation).
- **No deterministic verifier:** Verifier (Tier 4) not yet built. Gate scripts (Tier 1)
  provide point checks; end-to-end verifier is gated on Tier 3 Judge.
- **HCP files now generated:** Previously manually maintained. Now generated by
  `tools/export/generate_hcp.py` from SQLite spine. Manual edits are wiped on regeneration.
- **V4 Implementer self-report:** Not a source of truth. Completion requires
  deterministic evidence (git diff, test output, DB queries, endpoint responses,
  service health, browser/UI state, independent reviewer pass/fail).
- "Kanban pipeline transport:" RETIRED per ADR-013. workflow_runs is the authoritative work object.

---

## Do Not Start Yet

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

---

## Execution Order

**Tier 3.5 — Complete Build-Plan Spine Authority: finish generator switchover so AGENTS.md Sections 6-7 read from build_plan_nodes, sync stale blockers/actions, regenerate context, pass export gates.** ✅ COMPLETE
**Tier 5 — Build Tier 5.1: generate_agents_md.py — reads spine + static config, writes AGENTS.md under 20000 chars** ✅ COMPLETE
**Tier 5 — Build Tier 5.1a: config/agents_static.yaml — static Layer B content: infrastructure, gateway table, source patches, seed intent, verification rule** ✅ COMPLETE
**Tier 5 — Run Tier 5.2: AGENTS.md canary test across all 4 active profiles** ✅ COMPLETE
**Tier 5 — Tier 5.3: Retire HERMES_CIS_BRIEFING_PATH from all 5 .env files after canary passes** ✅ COMPLETE
**Tier 5 — Build Tier 5.4: generate_hcp.py — reads spine, writes HCP_00 through HCP_09** ✅ COMPLETE
**Tier 5 — Build Tier 5.5: generate_all.py — runs both generators, writes export manifest with SHA256** ✅ COMPLETE
**Tier 5 — Build Tier 5.6: gate_export_agreement.sh — verifies AGENTS.md and HCP hashes match manifest** ✅ COMPLETE
**Tier 5 — Tier 5.7: archive stale context packs (PROJECT_CONTEXT_PACK, _GENERATED, _UPLOAD_GENERATED), keep PROJECT_CONTEXT_PACK_UPLOAD active** ✅ COMPLETE
**Tier 5 — Decide project isolation model for future CIS-managed projects before onboarding a second project or generating non-CIS HCP packets. Options: --project-root per-project structure, or --project-id shared spine structure.** ✅ COMPLETE
**Tier 5 — Build Tier 5 context export pipeline** ✅ COMPLETE
**Tier 6 — Closeout trigger design: define how CIS automatically triggers closeout when a dependency-graph/build-plan node changes to COMPLETE, PASS, or PASS_WITH_LIMITATIONS. Closeout validated by deterministic gates before next tier can start. Cron is passive watchdog only (stale exports, dirty git, failed gates, missing closeout) — not primary trigger. Implementation area: Tier 6 Pipeline Integration (STATE_WRITE → EXPORT → CLOSEOUT → DONE).** ✅ COMPLETE
**Tier 6 — Harden Exact-Format Instruction Rule: ensure external advisors (ChatGPT, Claude) receive the exact-format instruction in durable HCP context. Advisors must request only COMMAND + OUTPUT + Proceed/Blocked without asking for interpretation, summary, result, or evidence reference. Current placement is in hcp_static.yaml under hcp_06 — verify it survives HCP regeneration and is visible in the advisor protocol section.** ✅ COMPLETE
**Tier ControlPlane — Complete Control Plane spec through review** 🔄 IN_PROGRESS
**Tier Phase 0 — Build loop-breaker for successful-repeat tool calls. Root cause: tool_guardrails.py only counts failures/no-progress reads. Successful identical calls (same tool_name+args) are invisible. FIRST test config-only: hard_stop_enabled:true + same_tool threshold. BUILD TARGET: extend ToolCallSignature counter to count regardless of success/failure, halt after N.** ⬜ PENDING
**Tier enforcement — Draft TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md as proposal only. Route through Claude audit + ChatGPT audit + Eric approval before any /opt/cis-control file lands.** ✅ COMPLETE
**Tier enforcement — Execute §14 raw-evidence capture plan from TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md. Start with operator-only override-plane test (bare-shell, 9 steps per §7 Parts A+B). No implementation until evidence captured and Eric-approved.** 🚫 BLOCKED
**Tier enforcement — Draft §7/§14 Test-Rig Amendment to TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md. Resolve structural contradiction by allowing override-plane evidence test against disposable test root /mnt/cache/catalog/override-plane-test/<run_id>/control/.** ✅ COMPLETE
**Tier enforcement — Execute §7 Parts A+B override-plane evidence test (9 steps) against disposable test root per Amendment 1 (revised). Requires: (1) root-owned control directory with sentinel created/removed via sudo, (2) separate control and workspace host directories with RO/RW mounts respectively, (3) stat/realpath/docker inspect/mount evidence before the 9-step test. No production /opt/cis-control. No hooks. No Hermes worker.** ✅ COMPLETE
**Tier front-door — FD.1 BASELINE VERIFIED: 11 existing MCP tools (docstring stale — says 9, actual 11). chromadb 1.5.9, s-transformers 5.5.0, 8 router routes, runtime/mcp/ clear. 3 dispatch tool names (cis_dispatch_drafter, _reviewer, _implementer) confirmed no collision. ADR-SEED-014 caveat RETIRED for FD.1 — drafter_start.py hardcodes /mnt/projects/cis, no home resolution. Durability note: hardcoded path breaks if repo relocates. FD.1 target: 14 tools total after adding 3 dispatch tools. Scope unchanged: add 3 dispatch tools + symlink only.** 🔄 IN_PROGRESS

---

## Open Questions

| ID | Question | Status |
|----|----------|--------|
| q-001 | ComfyUI role in CIS/WIAS — is it running? How integrated? | OPEN |
| q-002 | Archive drives — /mnt/archive/ mounted? Contents? | OPEN |
| q-003 | CIS Flask app (Tier 10 UI) — running? What does Eric see? | OPEN |
| q-004 | Build plan FD.1-FD.4 — pending dual review + Eric approval | OPEN |
| q-005 | Escalation wiring — what is actually wired for ChatGPT/Claude? | OPEN |
| q-006 | Remaining gaps — anything else needed before CIS usable? | OPEN |
| OQ-SEED-006 | deliberation_rounds schema is lossy: no reviewer_output column exists, only reviewer_signal. Reviewe | OPEN |
| OQ-SEED-007 | 4-independent-installs migration scope contradiction: Qwen (port 8644) is out-of-scope in the spec b | RESOLVED (Resolved 2026-06-17) |
| OQ-SEED-005 | Implementer scope expansion from inferred deliverables: Tier 6.4 exposed a scope-control gap. V4 Imp | RESOLVED (Resolved 2026-06-17) |
| OQ-SEED-003 | Should stale context pack folder cleanup (Tier 5.7) wait for first successful generate_all.py run or | OPEN |
| OQ-SEED-002 | hermes-gateway.service HERMES_HOME anomaly (OQ-009) — prime profile HERMES_HOME confirmed /home/eric | DEFERRED (Deferred — BLK-SEED-005 resolved as false positive) |
| OQ-SEED-001 | Google Drive backup integrity unverified | OPEN |
| OQ-T44-001 | Tier 4.4 migration applied cleanly? | RESOLVED (Verified by gate) |
| OQ-SEED-004 | Closeout trigger design: define how CIS automatically requires closeout when a dependency-graph/buil | OPEN |

---

## DB Spine State

| Table | Rows |
|-------|------|
| workflow_runs | 105 |
| deliberation_rounds | 361 |
| project_decisions | 16 |
| open_questions | 14 |
| next_actions | 20 |
| active_blockers | 7 |

---

## Reference Files

- CIS_CORE_BOUNDARY.md — what CIS is and is not
- CIS_CONTEXT_CONTRACT.md — session briefing rules and source hierarchy
- /mnt/projects/cis/docs/BUILD_PLAN_CIS_FOUNDATION.md — Foundation build plan v1.4
- /mnt/projects/cis/cis_kernel/build/CIS_SCRATCHPAD.md — running scratchpad
- /mnt/projects/cis/seed_intent_corpus/SEED_INTENT_EXCERPTS.md — Eric's words
- /mnt/projects/cis/seed_intent_corpus/SESSION_ORIENTATION_PROMPT.md — session briefing template
- /mnt/projects/cis/session_handoffs/ — structured handoff output directory
- /mnt/projects/ai_execution_infrastructure/03_CHAT_CAPTURE/raw/drive_imports/ — downloaded transcripts
