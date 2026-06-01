# CIS Current State
Version: 2.4
Date: 2026-05-31
Authority: Eric (Architect)
Maintained by: Updated at start of each session by the active advisor
Status: LIVE — update when state changes, never let this go stale

---

## Current Objective

Infrastructure stabilization before Phase 4B. The AdvisorChat.jsx truncation
event proved that git versioning is now a blocking infrastructure need.
Immediate priority: GitHub/git versioning, then UI layout/readability
improvements, then router usability validation, then Archon-style verifier
DAG planning. Phase 4B knowledge base extraction is deferred until the tool
is stable enough to work beyond infrastructure.

**AdvisorChat Input Router v0.1 is COMPLETE.** The routing layer now
automatically classifies user prompts and dispatches to the correct agent.
The user is no longer the manual API between agents.

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

### Advisor Gateways (Router v0.1 COMPLETE — all gates + router)

| Gateway | Port | HERMES_HOME | Model | Guardrails | Status |
|---------|------|-------------|-------|------------|--------|
| Research/Evidence (prime) | 8642 → NeMo 8800 | /home/eric/.hermes | deepseek-v4-flash | NeMo native on 8800 | Running |
| V4 Drafter (v4pro) | 8645 | /home/eric/.hermes-v4pro | deepseek-v4-pro (thinking) | Direct (NeMo incompatible) | Running |
| V4 Reviewer (r1) | 8643 | /home/eric/.hermes-r1 | deepseek-v4-pro (thinking) | Direct (NeMo incompatible) | Running |
| V4 Implementer (v4impl) | 8646 | /home/eric/.hermes-v4impl | deepseek-v4-pro (thinking, xhigh) | Direct (NeMo incompatible) | Running |
| Qwen Worker/Judge | 8644 | /home/eric/.hermes-qwen | qwen3-vl-30b (local) | None | Running (deferred from UI) |

Service files (all user-mode systemd):
- `hermes-gateway.service` — Research/Evidence (HERMES_HOME=/home/eric/.hermes — OQ-009 anomaly)
- `hermes-gateway-r1.service` — V4 Reviewer (HERMES_HOME=/home/eric/.hermes-r1)
- `hermes-gateway-qwen.service` — Qwen (HERMES_HOME=/home/eric/.hermes-qwen)
- `hermes-gateway-v4pro.service` — V4 Drafter (HERMES_HOME=/home/eric/.hermes-v4pro)
- `hermes-gateway-v4impl.service` — V4 Implementer (HERMES_HOME=/home/eric/.hermes-v4impl, NEW)
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
3. No notes capture mechanism
4. Claude and ChatGPT sessions not imported to SQLite
5. ~~R1 role description stale~~ — RESOLVED (Gate 3: R1 now deepseek-v4-pro Critic)
6. Qwen lacks CIS-specific context injection
7. Shared knowledge base for adversarial deliberation not yet built (current)
8. ~~Advisor Chat Deliberate button UNTESTED~~ — RESOLVED (Gate 3: reconciliation works)
9. ~~Model role enforcement not automated~~ — RESOLVED (Gate 7: Advisor loop enforces roles via preflight/gating)
10. V4-Pro and R1 cannot pass through NeMo (architecture incompatible with thinking models — accepted limitation)
11. ~~NeMo Fast missing Tavily API key~~ — RESOLVED (Gate 6B)
12. ~~Execution-claim blocking not implemented~~ — RESOLVED (Gate 6C-7D)
13. ~~NeMo pattern matching too greedy~~ — RESOLVED (Gate 6C/7C/7D: pass-through intents tuned)
14. NeMo semantic intent classifier requires manual compensation for new query types (accepted limitation)
15. Deterministic Archon-style verifier DAG not yet implemented
16. DeepEval regression/semantic testing layer not yet implemented
17. Handoff generator source hierarchy has known gap around scratchpad/next_actions (OQ-010 partial)

---

## Next Safe Action

**Router v0.1 is complete.** The Advisor loop is verified end-to-end with automatic
routing, evidence firewall, and adversarial review. Corrected next session queue:

1. GitHub/git versioning — protect CIS source files before further edits (blocking)
2. Post-implementation verification gate design — evidence-based completion checks
3. AdvisorChat UI layout/readability improvements
4. Router usability validation — confirm one-input workflow
5. Archon-style verifier DAG planning (deferred until verification gate is designed)
6. Phase 4B — knowledge base extraction from Google Drive transcripts (deferred)

**Phase 4B** — 12 files (3.4MB) downloaded at
/mnt/projects/ai_execution_infrastructure/03_CHAT_CAPTURE/raw/drive_imports/,
not yet extracted. Deferred until infrastructure is stable and verification
gates are in place.

---

## Accepted Limitations (Gate 7)

- **NeMo semantic classifier:** Uses embedding-based intent matching. When new query
  types appear that are incorrectly routed, pass-through intents must be manually added.
- **V4-Pro direct routing:** V4-Pro R1/R2 cannot pass through NeMo because NeMo strips
  `reasoning_content` and `reasoning_tokens` from DeepSeek thinking models.
- **Preflight evidence only:** V4-Pro preflight uses NeMo for evidence collection,
  then calls V4-Pro direct. NeMo does not validate V4-Pro's output.
- **V4 Implementer self-report not trusted:** Implementer completion claims are not
  accepted as truth. A separate deterministic verification gate must confirm results
  against directive scope using git diff, test output, DB queries, endpoint responses,
  service health, browser/UI state, or independent reviewer pass/fail before
  marking any implementation work as PASS.
- **No deterministic verifier:** Archon-style DAG verification not yet built.
  Current verification relies on human review + adversarial critique.
- **No DeepEval:** Regression and semantic testing deferred.
- **Handoff generator gap:** Generator reads CIS_CURRENT_STATE.md as primary authority
  but scratchpad/next_actions may hold more current information (OQ-010 partial).
  Generator improved in Gate 7E to cover more sources but gap remains.

---

## Do Not Start Yet

- Pass 5 implementation (project promotion, schema migration)
- Unified memory build
- Wiring V4-Pro/R1 through NeMo (architecturally blocked)
- Briefing Center UI redesign
- Notes/Open Items database implementation
- VDB pipeline rebuild
- Discord/Telegram gateway
- Schedule field-use work
- CIS Foundation Build Plan Phases 1–3 (gateway config, KB wiring, UI reorganization)
- Snapshot trigger work (CIS-INFRA-STORAGE-002)

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
**Stabilization — Git versioning, verification gate, UI layout, router validation, verifier DAG** ← CURRENT
**Phase 4B — Knowledge Base Extraction & Role Enforcement** (deferred until infrastructure is stable)
**Phase 5 — Notes and Open Items**

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
