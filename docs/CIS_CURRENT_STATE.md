# CIS Current State
Version: 2.5
Date: 2026-05-31
Authority: Eric (Architect)
Maintained by: Updated at start of each session by the active advisor
Status: LIVE — update when state changes, never let this go stale

---

## Current Objective

Phase 0 recovery complete. GitHub private repo exists at
https://github.com/digitalgsmp/cis with initial commit `b1bcf7d`.
All three V4 Pro gateways (Drafter/Reviewer/Implementer) are healthy,
context-aware via HERMES_CIS_BRIEFING_PATH, and correctly modeled as
deepseek-v4-pro with xhigh reasoning. Qwen is paused. R1/DeepSeek Reasoner
is retired from active assumptions.

Next objective: minimal orchestrator scaffold (orchestrator.py state machine)
to remove Eric from the manual relay role. Judge (deterministic NeMo/Python
checklist) and Verifier (post-execution evidence check) follow after.

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

## Model Roles (Corrected — 2026-05-31 Phase 0)

| Role | Agent | Gateway | Port | Model | Reasoning | NeMo? | Function |
|------|-------|---------|------|-------|-----------|-------|----------|
| Flash / Research | hermes-prime | NeMo → 8642 | 8800 | deepseek-v4-flash | — | Yes | Fast context, research, brainstorming |
| V4 Drafter | hermes-v4pro | Direct | 8645 | deepseek-v4-pro | xhigh | No | Proposal author, directive drafter |
| V4 Reviewer | hermes-r1 | Direct | 8643 | deepseek-v4-pro | xhigh | No | Adversarial reviewer, PASS/FAIL with critique |
| V4 Implementer | hermes-v4impl | Direct | 8646 | deepseek-v4-pro | xhigh | No | Bounded executor, FINAL_DIRECTIVE only |
| **Judge** | — | NeMo 8800 | — | — | — | IS NeMo | Deterministic checklist gate, PASS/FAIL only |
| **Orchestrator** | — | `orchestrator.py` | — | — | — | No | Backend state machine, not a model |

**Important naming corrections:**
- `hermes-gateway-r1` is a stale service/profile name only. Actual role is V4 Reviewer.
- R1/DeepSeek Reasoner is retired from active assumptions.
- Qwen (hermes-qwen, port 8644) is paused / out of active implementation.
- Judge is NOT a reasoning model. NOT Qwen. NOT Flash. Deterministic NeMo + Python action only.
- Orchestrator is NOT Flash. Backend Python state machine. Rule-based transitions only.

### Advisor Loop Architecture (Designed — Not Yet Implemented)

```
User prompt
  → Orchestrator decides: research needed?
     ├─ YES → Flash/Research (NeMo:8800 → Flash:8642) gathers context
     └─ NO  → skip directly to Drafter
  → V4 Drafter (8645) — proposes structured directive
  → V4 Reviewer (8643) — adversarial challenge
     ├─ FAIL → return critique to Drafter (max 3 cycles)
     ├─ DEADLOCK (3 cycles) → human-in-the-loop (H2)
     └─ PASS → converged directive
  → NeMo Judge (8800) — deterministic PASS/FAIL checklist
     ├─ FAIL → return failed criteria to Drafter/Reviewer
     └─ PASS → pending human approval (H1)
  → Human approves → V4 Implementer (8646) — FINAL_DIRECTIVE
  → Post-Execution Verifier — deterministic evidence check (H3 if FAIL)
```

**Why V4 Drafter/Reviewer/Implementer are direct (not through NeMo):** NeMo's
response pipeline strips `reasoning_content` and `reasoning_tokens` from
DeepSeek thinking models (Gate 5C).

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
- `hermes-gateway.service` — Flash/Research (HERMES_HOME=/home/eric/.hermes)
- `hermes-gateway-r1.service` — V4 Reviewer (stale name: "r1", HERMES_HOME=/home/eric/.hermes-r1)
- `hermes-gateway-qwen.service` — Qwen (paused, HERMES_HOME=/home/eric/.hermes-qwen)
- `hermes-gateway-v4pro.service` — V4 Drafter (HERMES_HOME=/home/eric/.hermes-v4pro)
- `hermes-gateway-v4impl.service` — V4 Implementer (HERMES_HOME=/home/eric/.hermes-v4impl)
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
15. Orchestrator state machine not yet built (next phase)
16. Deterministic Judge (NeMo/Python checklist) not yet built
17. Deterministic Verifier (post-execution evidence check) not yet built
18. DeepEval regression/semantic testing layer not yet implemented

## Next Safe Action

**Phase 0 recovery complete.** Git versioning protects the source tree.
All gateways are healthy and context-aware. Correct architecture designed.

Next safe phase: **minimal orchestrator scaffold** (orchestrator.py state machine
with Drafter→Reviewer deliberation loop). No Judge, no Verifier, no UI changes.
The goal is to remove Eric from the manual API relay role.

Judge (deterministic NeMo/Python checklist) and Verifier (post-execution
evidence check) follow after the orchestrator scaffold is stable.

**Phase 4B** — 12 files (3.4MB) downloaded, knowledge base extraction deferred
until infrastructure is stable and verification gates are in place.

---

## Accepted Limitations (Phase 0)

- **NeMo semantic classifier:** Uses embedding-based intent matching. Pass-through intents must be manually added for new query types.
- **V4-Pro direct routing:** V4 Drafter/Reviewer/Implementer cannot pass through NeMo because NeMo strips `reasoning_content` and `reasoning_tokens` from DeepSeek thinking models.
- **V4 Implementer self-report not trusted:** A separate deterministic verification gate must confirm results against directive scope before marking any implementation work as PASS.
- **No orchestrator yet:** Eric still manually relays between agents. Orchestrator state machine (Phase 1) will remove this.
- **No deterministic Judge yet:** Pre-execution directive validation is not automated.
- **No deterministic Verifier yet:** Post-execution evidence checking is manual.
- **Stale service names:** `hermes-gateway-r1` and `hermes-gateway-qwen` have names that no longer match their actual roles.

---

## Do Not Start Yet

- Pass 5 implementation (project promotion, schema migration)
- Unified memory build
- Wiring V4-Pro through NeMo (architecturally blocked)
- Briefing Center UI redesign
- Notes/Open Items database implementation
- VDB pipeline rebuild
- Discord/Telegram gateway
- Schedule field-use work
- CIS Foundation Build Plan Phases 1–3
- Snapshot trigger work (CIS-INFRA-STORAGE-002)
- Orchestrator implementation (approved next phase, not started)
- Judge implementation
- Verifier implementation

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
**Phase 0 Recovery — GitHub Versioning + Gateway Repair + Context Injection** ✅ COMPLETE (2026-05-31)
**Phase 1 — Minimal Orchestrator Scaffold (orchestrator.py)** ← NEXT
**Phase 2 — Deterministic NeMo/Python Judge**
**Phase 3 — Deterministic Post-Execution Verifier**
**Phase 4B — Knowledge Base Extraction** (deferred)
**Phase 5 — Notes and Open Items**

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
