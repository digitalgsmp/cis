# CIS Current State
Version: 2.5
Date: 2026-06-01
Authority: Eric (Architect)
Maintained by: Updated at start of each session by the active advisor
Status: LIVE — update when state changes, never let this go stale

---

## Current Objective

**Build CIS deterministic pipeline — Phase A substrate verification.**

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

**Context briefing:** All four gateway profiles now have `HERMES_CIS_BRIEFING_PATH` in their `.env` files. All three active V4 roles verified to load and answer from the briefing.

Service files (all user-mode systemd):
- `hermes-gateway.service` — Research/Evidence (HERMES_HOME=/home/eric/.hermes — OQ-009 anomaly)
- `hermes-gateway-r1.service` — V4 Reviewer (HERMES_HOME=/home/eric/.hermes-r1)
- `hermes-gateway-qwen.service` — Qwen (HERMES_HOME=/home/eric/.hermes-qwen)
- `hermes-gateway-v4pro.service` — V4 Drafter (HERMES_HOME=/home/eric/.hermes-v4pro)
- `hermes-gateway-v4impl.service` — V4 Implementer (HERMES_HOME=/home/eric/.hermes-v4impl, NEW)
- `nemo-fast.service` — NeMo Guardrails on port 8800 (Gate 6B: persistent, Tavily key from /home/eric/.config/cis-rails.env)

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

**Phase A — Hermes substrate verification.** Run verification commands and
return raw terminal output. No code build begins until Phase A output is reviewed.

Phase A checks:
- `hermes --version` — confirm installed version and Kanban support
- `hermes kanban --help` — confirm Kanban CLI availability
- `hermes kanban boards list` — check existing boards
- Find `kanban.db` under all HERMES_HOME paths — confirm shared vs profile-scoped
- AGENTS.md canary loading test from `/mnt/projects/cis`
- Grep `HERMES_CIS_BRIEFING_PATH` across all profile `.env` files
- Verify Kanban dependency/assignment/worktree/gate features if available
- Verify git worktree status

**Hard stop:** No Phase B–I build begins until Phase A raw output is reviewed
and Kanban scoping is confirmed or contingency (Flask/CIS DB task tables) is selected.

**Approved build order:**
1. Phase A — Substrate verification ← CURRENT
2. Phase B — Deterministic gate scripts
3. Phase C — Kanban board + profile configuration
4. Phase D — SQLite spine schema (workflow-event organized)
5. Phase E — AGENTS.md export pipeline (Hermes-native context)
6. Phase F — HCP export pipeline (ChatGPT/Claude)
7. Phase G — Router reclassification
8. Phase H — MCP bridge (later)
9. Phase I — Chroma/VDB (later)

**Sequencing rule:** Nothing in Phase C or later begins until Phase A
verification commands return known-good results. Nothing writes to the spine
until Phase B gates exist and pass.

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
  deterministic evidence (verification-hardening rule).
- **Kanban profile-scoping unverified:** Phase A must confirm whether `kanban.db`
  is shared across all profiles or siloed per-profile. If Kanban is unavailable
  or profile-scoped, the existing Flask/CIS database serves as the coordination
  layer for pipeline tasks.

---

## Do Not Start Yet

- Phase B gate scripts (Phase A first)
- Phase C Kanban configuration (Phase A first)
- Phase D SQLite spine schema (Phase B gates first)
- Phase E AGENTS.md export (Phase D spine first)
- Phase F HCP export pipeline (Phase E AGENTS.md first)
- Phase G Router reclassification
- Phase H MCP bridge
- Phase I Chroma/VDB
- Pass 5 implementation
- Unified memory build (after pipeline foundation)
- Wiring V4-Pro through NeMo (architecturally blocked)
- Briefing Center UI redesign
- Notes/Open Items database implementation
- Discord/Telegram gateway
- UI-003 layout pass (after pipeline foundation)

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
**Phase A — Hermes Substrate Verification** ← CURRENT
**Phase B — Deterministic Gate Scripts** (next, gated on Phase A)
**Phase C — Kanban Board + Profile Configuration** (gated on Phase B)
**Phase D — SQLite Spine Schema** (workflow-event organized, gated on Phase C)
**Phase E — AGENTS.md Export Pipeline** (gated on Phase D)
**Phase F — HCP Export Pipeline** (gated on Phase E)
**Phase G — Router Reclassification** (gated on Phase F)
**Phase H — MCP Bridge** (later)
**Phase I — Chroma/VDB** (later)

---

## Open Questions

| ID | Question | Status |
|----|----------|--------|
| OQ-003 | Is the Google Drive backup intact? | Open |
| OQ-006 | R1 role/context loading — when to inject CIS role knowledge? | Open |
| OQ-007 | Claude/ChatGPT API capture design for unified memory | Open |
| OQ-008 | Hermes capabilities audit scope | Open |
| OQ-009 | hermes-gateway.service HERMES_HOME anomaly | Open |
| OQ-010 | Generator source hierarchy vs Project Context Pack | RESOLVED (2026-05-30) |

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
