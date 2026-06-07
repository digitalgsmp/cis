# CIS Current State
Version: 2.7
Date: 2026-06-07
Authority: Eric (Architect)
Status: TIER 5.3 COMPLETE — AGENTS.md is live context; HERMES_CIS_BRIEFING_PATH retired

---

## Current Objective

**Tier 4.4 COMPLETE. Tier 5 Context Export Pipeline — IN PROGRESS. Tier 5.3 retirement done.**

**HEAD:** `80f934c`. All 4 active gateways load AGENTS.md as sole project context.
HERMES_CIS_BRIEFING_PATH permanently removed from all 5 profile .env files.
TERMINAL_CWD=/mnt/projects/cis required in all .env files for gateway AGENTS.md discovery.

**Remaining Tier 5:** Tier 5.4 generate_hcp.py → 5.5 generate_all.py → 5.6 gate_export_agreement.sh → 5.7 stale cleanup.
Do NOT start Tier 6, Judge, UI, VDB/Chroma, router reclassification, or MCP before Tier 5.4–5.6 complete.

**Context architecture:** AGENTS.md serves Hermes-native internal context for all 4 active gateways. HCP_* files in PROJECT_CONTEXT_PACK_UPLOAD/ are the permanent external advisor packet for ChatGPT, Claude, and frontier-model escalation. HCP is not deprecated; manual drift is what Tier 5 eliminates by generating HCP from spine.

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
Smoke card created with Tier 2.8 schema. Orchestrator completed 3 DRAFT→REVIEW rounds.
Result: ESCALATE with substantive unresolved objections (Research gateway missing, role
boundary violation, deadlock breaker). gate_runner.sh: all 5 gates PASS. No manual relay.

**Tier 4 — SQLite Spine (committed `88ea25f`, `0c19b4d`, `ec14615`):**
Two-table minimum schema: `workflow_runs` + `deliberation_rounds`. `database.py` write/read
layer with allowlist validation. `gate_db_state.py` deterministic verification gate.
DB at `data/cis_memory.db` (gitignored). Smoke test seeded with real data.

**Known limitation:** Orchestrator `--output` preserves only final-round detail.
Per-round output preservation is Tier 6 backlog.

**Tier 5 — Context Export Pipeline (next, not started):** Per Dependency Graph
Build Plan v2.0 (`docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md`). AGENTS.md generation,
canary test, HERMES_CIS_BRIEFING_PATH retirement.

**Phase A findings (corrected 2026-06-07):**
- Hermes Agent v0.13.0 — Kanban fully available
- Kanban shareable via `HERMES_KANBAN_DB` + `HERMES_KANBAN_HOME` — confirmed
- Cross-profile Kanban visibility confirmed
- AGENTS.md loaded from cwd or TERMINAL_CWD in gateway mode, NOT automatically from git root. Gateway processes require TERMINAL_CWD=/mnt/projects/cis to load CIS AGENTS.md. CLI sessions load when launched from CIS repo root.
- `HERMES_CIS_BRIEFING_PATH` RETIRED from all profiles at Tier 5.3 (commit `80f934c`)
- Preferred architecture: AGENTS.md (context) + gate scripts (verification) + SQLite spine (knowledge) + HCP export (external advisors)

CIS is a Hermes-native adversarial deliberation engine. The pipeline is the product.
The state spine is bidirectional: it briefs the pipeline from verified history and
receives verified outputs from completed pipeline runs.

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

**Phase 0 recovery is COMPLETE.** Git versioning at github.com/digitalgsmp/cis (commit `b1bcf7d`).
All three V4 Pro gateways healthy, context-aware, deepseek-v4-pro xhigh. Qwen paused.

**AdvisorChat Input Router v0.1 is COMPLETE.** classify_route() dispatches to correct agent.

**Verification-hardening rule (2026-05-31):** V4 Implementer self-report is not
a source of truth. Completion is accepted only after deterministic evidence
verifies the result. Accepted evidence: (1) git diff / file system state,
(2) build and test command output, (3) database queries, (4) endpoint/curl
responses, (5) service health checks, (6) browser/UI verification,
(7) independent reviewer/verifier pass/fail. Implementer reports claimed
changes → separate verification gate checks deterministic evidence → PASS
only if evidence matches directive scope. Missing/ambiguous/self-reported
evidence → status remains UNVERIFIED.

---

## Model Roles (Router v0.1 — 2026-05-31)

| Label | Agent | Gateway | Port | Model | Function | Boundaries |
|-------|-------|---------|------|-------|----------|------------|
| Research / Evidence | hermes-prime | NeMo → 8642 | 8800 | deepseek-v4-flash | Evidence firewall + current-facts search | No code, no files, no terminal |
| V4 Drafter | hermes-v4pro | Direct | 8645 | deepseek-v4-pro (thinking) | Proposal author, directive drafter | No execution, no file edits |
| V4 Reviewer | hermes-r1 | Direct | 8643 | deepseek-v4-pro (thinking) | Adversarial reviewer, validator | No execution, no code generation |
| V4 Implementer | hermes-v4impl | Direct | 8646 | deepseek-v4-pro (thinking, xhigh) | Execute FINAL_DIRECTIVE only | No deliberation, no architecture proposals |

**Qwen (hermes-qwen)** remains active on port 8644 but is removed from the main
AdvisorChat UI and routing flow. Deferred from implementation work. JUDGE_REQUEST
remains backend-capable but not exposed in the UI.

### Advisor Loop Architecture (Router v0.1 verified)

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
- Proxmox host: wander at 192.168.1.200, PVE 9.1.6
- creative-vm (VM 100): running, Ubuntu 24.04, 192.168.1.15
- VM storage: virtio0 (500G, local-lvm), virtio1 (250G, local-lvm)
- Passthrough drives: virtio2 (10TB archive), virtio3/5/6 (SSDs)
- Snapshot status: RESOLVED — cis-snapshot deployed on root@wander (CIS-INFRA-STORAGE-001)
- Backup status: local archive at /mnt/archive/cis_backup_20260524_112430.tar.gz
- Google Drive backup integrity: UNVERIFIED
- **GitHub versioning: COMPLETE** — private repo at https://github.com/digitalgsmp/cis, commit `b1bcf7d`

### Advisor Gateways (Phase 0 Recovery COMPLETE)

| Gateway | Port | HERMES_HOME | Model | Reasoning | NeMo? | Status |
|---------|------|-------------|-------|-----------|-------|--------|
| Flash/Research (prime) | 8642 → NeMo 8800 | /home/eric/.hermes | deepseek-v4-flash | — | Yes | Running |
| V4 Drafter (v4pro) | 8645 | /home/eric/.hermes-v4pro | deepseek-v4-pro | xhigh | Direct | Running, context-aware |
| V4 Reviewer (r1) | 8643 | /home/eric/.hermes-r1 | deepseek-v4-pro | xhigh | Direct | Running, context-aware |
| V4 Implementer (v4impl) | 8646 | /home/eric/.hermes-v4impl | deepseek-v4-pro | xhigh | Direct | Running, context-aware |
| Qwen (paused) | 8644 | /home/eric/.hermes-qwen | qwen3-vl-30b (local) | — | None | Running but paused |

**Context:** AGENTS.md auto-loaded by all 4 active gateways via TERMINAL_CWD=/mnt/projects/cis. HERMES_CIS_BRIEFING_PATH retired.

Service files (all user-mode systemd — topology repaired 2026-06-07):
- `hermes-gateway.service` — Flash/Research (HERMES_HOME=/home/eric/.hermes, port 8642)
- `hermes-gateway-r1.service` — V4 Reviewer (HERMES_HOME=/home/eric/.hermes-r1, port 8643)
- `hermes-gateway-v4pro.service` — V4 Drafter (HERMES_HOME=/home/eric/.hermes-v4pro, port 8645)
- `hermes-gateway-v4impl.service` — V4 Implementer (HERMES_HOME=/home/eric/.hermes-v4impl, port 8646)
- `hermes-gateway-qwen.service` — Qwen (HERMES_HOME=/home/eric/.hermes-qwen, port 8644, paused)
- `nemo-fast.service` — NeMo Guardrails on port 8800

NeMo path: `/mnt/projects/cis/runtime/rails/` (venv at `.venv`, configs at `configs/`)

### Hermes Source Patches (permanent — Gate 2/5C)

Four patches applied to the Hermes Agent codebase at `/home/eric/.hermes/hermes-agent/`:
1. `run_agent.py:9782` — Added `api.deepseek.com` to `_supports_reasoning_extra_body()` allowlist
2. `plugins/model-providers/deepseek/__init__.py` — `DeepSeekProfile` with `build_api_kwargs_extras()` for thinking params
3. `gateway/platforms/api_server.py:1255` — Extracts `reasoning_content` from agent result, surfaces in API response
4. `agent/usage_pricing.py:731` — Added `completion_tokens_details.reasoning_tokens` fallback

NeMo patch (Gate 5C):
- `server/schemas/utils.py:generation_response_to_chat_completion()` — Passes through `reasoning_content` in `ChatCompletionMessage`

### CIS Application
- Flask backend: running at 127.0.0.1:5000
- React UI: running, accessible at http://127.0.0.1:5000/ui
- Database: three SQLite databases (cis_memory.db, cis_app.db, runtime/db/cis_memory.db)
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

### Google Drive Connection (NEW — 2026-05-30)
- OAuth connected via google-workspace skill (read-only)
- 12 chat transcript files downloaded: 3.4MB total
- Path: /mnt/projects/ai_execution_infrastructure/03_CHAT_CAPTURE/raw/drive_imports/
- Scope: drive.readonly only — no write, delete, or share permissions

### Phase 3A Context Loader (IMPLEMENTED/PASS — 2026-05-29)
- Command: `python3 /mnt/projects/cis/tools/generate_context_briefing.py --write`
- Output: `/mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md`
- Now reads 8 source files (updated 2026-05-30)
- Verifier updated to match — all 8 static sources checked
- OQ-010 RESOLVED — generator source hierarchy confirmed
- Eric no longer has to manually assemble the handoff

### Phase 3B — Automated Session Continuation (PASS — 2026-05-29)
- Briefing auto-loads via ~/.hermes/.env + run_agent.py injection
- Eric fully removed from manual paste loop

### Phase 4A — Deterministic Verification (PASS — 2026-05-29)
- Standalone verifier: /mnt/projects/cis/tools/verify_context_briefing_freshness.py
- 9/9 tests passed. Exit-code convention documented.
- Integration PASS: /home/eric/.local/bin/hermes wrapper runs freshness check
  before every interactive Hermes command. Fail-closed.

### Seed Intent Corpus (Phase 3A — 2026-05-29)
- /mnt/projects/cis/seed_intent_corpus/ created
- SEED_INTENT_EXCERPTS.md — 6 core excerpts from Eric's raw session archive
- SESSION_ORIENTATION_PROMPT.md — session-start briefing template
- 1,367 session files scanned; top 5 candidates identified by signal phrase density
- Excerpts preserve Eric's exact words — no model summaries

---

## Active Blockers

1. Google Drive backup integrity unverified
2. ~~No automatic session-start context loading~~ — RESOLVED (Phase 3B/4A)
3. ~~GitHub/git versioning~~ — RESOLVED (2026-05-31, Phase 0)
4. ~~Context briefing missing from gateway profiles~~ — RESOLVED (2026-05-31, Phase 0)
5. No notes capture mechanism
6. Claude and ChatGPT sessions not imported to SQLite
7. ~~R1 role description stale~~ — RESOLVED (Phase 0: r1 is V4 Reviewer; Reasoner retired)
8. ~~Qwen role confusion~~ — RESOLVED (Qwen is paused/out of active implementation)
9. Shared knowledge base for adversarial deliberation not yet built
10. V4-Pro cannot pass through NeMo (architecture incompatible with thinking models — accepted limitation)
11. ~~NeMo Fast missing Tavily API key~~ — RESOLVED (Gate 6B)
12. ~~Execution-claim blocking not implemented~~ — RESOLVED (Gate 6C-7D)
13. ~~NeMo pattern matching too greedy~~ — RESOLVED (Gate 6C/7C/7D)
14. NeMo semantic intent classifier requires manual compensation (accepted limitation)
15. **Multiple competing context sources** — HCP files, canonical docs, briefing generator, runtime state diverge
16. **Stale context pack folders** — PROJECT_CONTEXT_PACK/, _GENERATED/, _UPLOAD_GENERATED/ outdated
17. **No automated closeout mechanism** — HCP updates, git commits, and backup are manual

---

## Next Safe Action

**Tier 5 — Context Export Pipeline.** Per Dependency Graph Build Plan v2.0.
Not started. Scope: `generate_agents_md.py`, AGENTS.md canary test, retirement
of HERMES_CIS_BRIEFING_PATH, `generate_hcp.py`, HCP export verification.

**Judge checklist (`tools/judge/judge_checklist.py`) is NOT the next artifact**
unless explicitly re-approved. The Dependency Graph Build Plan says Tier 5
Context Export before Tier 6 Pipeline Integration.

**Approved build order:**
1. Tier 0 — Orchestrator scaffold ✅ COMPLETE (`9d84351`, 2026-06-05)
2. Tier 1 — Deterministic gate suite ✅ COMPLETE (`bc49beb`–`635a646`, 2026-06-06)
3. Tier 2 — Kanban coordination layer ✅ COMPLETE (`2989c5b`, 2026-06-06)
4. Tier 3 — Pipeline smoke test ✅ PASS_WITH_LIMITATIONS (2026-06-06)
5. Tier 4 — SQLite spine schema + DB layer + DB gate ✅ COMPLETE (`88ea25f`, `0c19b4d`, `ec14615`, 2026-06-06)
6. Tier 5 — Context Export Pipeline ← CURRENT (not started)
7. Tier 6 — Pipeline Integration (gated on Tier 5)
8. Tier 7 — Router Reclassification (gated on Tier 6)
9. Tier 8 — MCP Bridge (later)
10. Tier 9 — Chroma/VDB (later)
11. Tier 10 — CIS UI/custom display views (later)

---

## Accepted Limitations

- **NeMo semantic classifier:** Uses embedding-based intent matching. New query
  types may need manual pass-through intents.
- **V4-Pro direct routing:** V4-Pro cannot pass through NeMo because NeMo strips
  `reasoning_content` and `reasoning_tokens` from DeepSeek thinking models
  (accepted architectural limitation).
- **No deterministic verifier:** Gate scripts not yet built. Phase B.
- **No DeepEval:** Regression and semantic testing deferred.
- **HCP files manually maintained:** Migration to generated exports is Phase F.
  Current HCP_ files are edited by LLM via patch/write_file — same pipeline
  that can corrupt files.
- **Multiple context sources diverge:** `HERMES_CIS_BRIEFING_PATH` is transitional.
  Target: AGENTS.md auto-loaded by all profiles (Phase E).
- **V4 Implementer self-report:** Not a source of truth. Completion requires
- **No deterministic verifier:** Verifier (Tier 4) not yet built. Gate scripts (Tier 1)
  provide point checks; end-to-end verifier is gated on Tier 3 Judge.
- **Kanban profile-scoping:** RESOLVED. Kanban IS shareable via env vars
  (HERMES_KANBAN_DB + HERMES_KANBAN_HOME). Phase A verified. Gateway restart pending (Tier 2).
- **Gateway restart required for env vars:** `HERMES_KANBAN_DB` and `HERMES_KANBAN_HOME`
  have been added to all profile `.env` files but running gateway processes have not
  been restarted. Kanban sharing will not take effect in gateway context until Phase C
  restart. CLI testing confirmed the mechanism works.

---

## Do Not Start Yet

- Tier 5 Context Export Pipeline (approved next, not started)
- Tier 6–10 (all gated on predecessors)
- Judge checklist unless explicitly re-approved (Tier 6, gated on Tier 5)
- SQLite schema expansion (Tier 6 integration)
- Orchestrator per-round output preservation (Tier 6 backlog)
- Retirement of HERMES_CIS_BRIEFING_PATH (Tier 5)
- UI changes
- Pass 5 implementation
- Any artifact not in the approved Dependency Graph Build Plan v2.0

---

## Execution Order

**Phase 0 — Boundary docs** ✅ COMPLETE
**Phase 1 — Proxmox snapshot fix** ✅ COMPLETE (2026-05-28)
**Phase 2 — Gateway verification and repair** ✅ COMPLETE (2026-05-29)
**Phase 3A — Automatic Context Loader + Seed Intent** ✅ COMPLETE (2026-05-29)
**Phase 3B — Automated Hermes-to-Hermes continuation** ✅ COMPLETE (2026-05-29)
**Phase 4A — Deterministic Freshness Verifier** ✅ COMPLETE (2026-05-29)
**Phase 4A Integration — Wrapper Freshness Gate** ✅ COMPLETE (2026-05-29)
**Gate 2 — V4-Pro Thinking Gateway** ✅ COMPLETE (2026-05-30)
**Gate 3 — Wire Four Roles** ✅ COMPLETE (2026-05-30)
**Gate 4A — Persist V4-Pro Gateway** ✅ COMPLETE (2026-05-30)
**Gate 5A/B — NeMo Guardrails for Fast** ✅ COMPLETE (2026-05-30)
**Gate 5C — NeMo Incompatibility with Reasoning Models** ✅ COMPLETE (2026-05-30)
**Gate 6A — Tavily Web Evidence Preflight** ✅ COMPLETE (2026-05-30)
**Gate 6B — NeMo Persistent + Tavily Key Loaded** ✅ COMPLETE (2026-05-31)
**Gate 6C — Fix Fast NeMo Rail Precision + Execution-Claim Blocking** ✅ COMPLETE (2026-05-31)
**Gate 7A — V4-Pro Preflight Evidence Injection** ✅ COMPLETE (2026-05-31)
**Gate 7B — Qwen Worker/Judge Gate** ✅ COMPLETE (2026-05-31)
**Gate 7C — Mixed Prompt Classification Tuning** ✅ COMPLETE (2026-05-31)
**Gate 7D — Full Advisor Loop Smoke Test** ✅ COMPLETE (2026-05-31)
**Router v0.1 — AdvisorChat Input Router** ✅ COMPLETE (2026-05-31)
**Phase 0 Recovery — Git versioning, gateway repair, context injection** ✅ COMPLETE (2026-05-31)
**Context-Source Correction — HCP update, architecture principle** ✅ COMPLETE (2026-06-01)
**Claude Proposal — Unified Shared Knowledge Foundation** ✅ COMPLETE (2026-06-01)
**CIS Deterministic Pipeline Decision — Deliberation converged** ✅ COMPLETE (2026-06-01)
**Phase A — Hermes Substrate Verification** ✅ COMPLETE (2026-06-01)
**Tier 0 — Orchestrator scaffold** ✅ COMPLETE (`9d84351`, 2026-06-05)
**Tier 1 — Deterministic gate suite (5 gates + runner)** ✅ COMPLETE (`bc49beb`–`635a646`, 2026-06-06)
**Dependency Graph Build Plan v2.0 committed** ✅ COMPLETE (`0ef6177`, 2026-06-06)
**Tier 2 — Kanban Coordination Layer** ✅ COMPLETE (`2989c5b`, 2026-06-06)
**Tier 3 — Pipeline Smoke Test** ✅ PASS_WITH_LIMITATIONS (2026-06-06)
**Tier 5.1 — AGENTS.md Generator + Static Config** ✅ COMPLETE (`ee8eb25`, 2026-06-06)
**Tier 5.2 — AGENTS.md Canary** ✅ COMPLETE (4/4 PASS, 2026-06-07)
**Tier 5.2E — Gateway Topology Repair** ✅ COMPLETE (`353cef5`, 2026-06-07)
**Tier 5.3 — HERMES_CIS_BRIEFING_PATH Retirement** ✅ COMPLETE (`80f934c`, 2026-06-07)
**Tier 5.4 — generate_hcp.py** ← NEXT, not started
**Tier 5.5 — generate_all.py + export manifest** (gated on 5.4)
**Tier 5.6 — gate_export_agreement.sh** (gated on 5.5)
**Tier 5.7 — stale context pack cleanup** (gated on 5.6)
**Tier 6 — Pipeline Integration** (gated on Tier 5)
**Tier 7 — Router Reclassification** (gated on Tier 6)
**Tier 8 — MCP Bridge** (later)
**Tier 9 — Chroma/VDB** (later)
**Tier 10 — CIS UI/Custom Display Views** (later)

---

## Open Questions

| ID | Question | Status |
|----|----------|--------|
| OQ-003 | Is the Google Drive backup intact? | Open |
| OQ-006 | R1 role/context loading | Open |
| OQ-007 | Claude/ChatGPT API capture design | Open |
| OQ-008 | Hermes capabilities audit scope | Open |
| OQ-009 | hermes-gateway.service HERMES_HOME anomaly | REOPENED (service repaired at 353cef5; auto-overwrite root cause unmitigated) |
| OQ-010 | Generator source hierarchy vs Project Context Pack | RESOLVED |

---

## DB Spine State (2026-06-07)

| Table | Rows |
|-------|------|
| workflow_runs | 1 |
| deliberation_rounds | 3 |
| project_decisions | 8 (7 seed + 1 test) |
| open_questions | 4 |
| next_actions | 8 |
| active_blockers | 6 (5 seed + 1 test) |

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
