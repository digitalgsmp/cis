# CIS Current State
Version: 2.3
Date: 2026-05-31
Authority: Eric (Architect)
Maintained by: Updated at start of each session by the active advisor
Status: LIVE — update when state changes, never let this go stale

---

## Current Objective

Phase 4B — Knowledge Base Extraction & Shared Model Context. Extract
Eric's raw intent statements from Google Drive chat transcripts and archive
files. Build a shared knowledge base that Fast, V4-Pro R1, R2/Critic, and
Qwen all access as common ground truth for adversarial deliberation.
Claude and ChatGPT function as escalation guardrails via HCP upload and
manual relay. Google Drive is connected (read-only).

---

## Model Roles (Gate 7 — 2026-05-31)

| Label | Agent | Gateway | Port | Model | Function | Boundaries |
|-------|-------|---------|------|-------|----------|------------|
| Fast | hermes-prime | NeMe → 8642 | 8800 | deepseek-v4-flash | Evidence firewall + conversational strategist | No code, no files, no terminal |
| V4-Pro R1 | hermes-v4pro | Direct | 8645 | deepseek-v4-pro (thinking) | Proposal author, directive drafter | No execution, no file edits |
| V4-Pro R2/Critic | hermes-r1 | Direct | 8643 | deepseek-v4-pro (thinking) | Adversarial reviewer, validator | No execution, no code generation |
| Qwen Worker/Judge | hermes-qwen | Direct | 8644 | qwen3-vl-30b (local) | Execute FINAL_DIRECTIVE or judge JUDGE_REQUEST only | No deliberation, no architecture proposals |

### Advisor Loop Architecture (Gate 7D verified)

```
User prompt
  → Fast/NeMo:8800 (evidence firewall)
     ├─ pass-through → deepseek-v4-flash:8642
     ├─ system config → local DB/port evidence
     ├─ external facts → Tavily web evidence
     └─ execution claims → FAST_EXECUTION_BLOCKED

  → V4-Pro R1:8645 (proposal drafting, receives NeMo preflight evidence)
  → V4-Pro R2:8643 (adversarial critique)
  → V4-Pro R1:8645 (final directive incorporating critique)
  → Qwen:8644 (gated — accepts only FINAL_DIRECTIVE or JUDGE_REQUEST)
     └─ reports VERDICT/ACTION/EVIDENCE/MISSING PROOF/NEXT REPAIR
```

**Architecture principle:** NeMo is the behavioral/evidence firewall, not the reasoning
validator. V4-Pro R1/R2 adversarial loop is the reasoning gate. Qwen is the
execution/evidence gate.

**Why V4-Pro is direct (not through NeMo):** NeMo's response pipeline strips
`reasoning_content` and `reasoning_tokens` from DeepSeek thinking models (Gate 5C).
V4-Pro preflight uses NeMo for evidence collection, then calls V4-Pro direct.

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

### Advisor Gateways (Phase 2 COMPLETE — Gates 2-4A)

| Gateway | Port | HERMES_HOME | Model | Guardrails | Status |
|---------|------|-------------|-------|------------|--------|
| Fast (prime) | 8642 → NeMo 8800 | /home/eric/.hermes | deepseek-v4-flash | NeMo native on 8800 | Running |
| V4-Pro R1 | 8645 | /home/eric/.hermes-v4pro | deepseek-v4-pro (thinking) | Direct (NeMo incompatible) | Running |
| V4-Pro R2/Critic | 8643 | /home/eric/.hermes-r1 | deepseek-v4-pro (thinking) | Direct (NeMo incompatible) | Running |
| Qwen Worker/Judge | 8644 | /home/eric/.hermes-qwen | qwen3-vl-30b (local) | None | Running |

Service files (all user-mode systemd):
- `hermes-gateway.service` — Prime (HERMES_HOME=/home/eric/.hermes-r1 — OQ-009 anomaly)
- `hermes-gateway-r1.service` — R1 (HERMES_HOME=/home/eric/.hermes-r1)
- `hermes-gateway-qwen.service` — Qwen (HERMES_HOME=/home/eric/.hermes-qwen)
- `hermes-gateway-v4pro.service` — V4-Pro Reasoner (HERMES_HOME=/home/eric/.hermes-v4pro)
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
- Advisor Chat: four-panel UI (Fast, V4-Pro R1, V4-Pro R2/Critic, Qwen Worker/Judge) with Direct/Parallel modes
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

**Gate 7 closeout is complete.** The Advisor loop is verified end-to-end.
Next session should:
1. Review this updated handoff
2. Decide between:
   - Small usability test in AdvisorChat UI (verify the full loop in the browser)
   - Begin Phase 4B (knowledge base extraction from Google Drive transcripts)
   - Begin deterministic verifier DAG planning (Archon-style)

**Phase 4B — Extract Eric's intent from Google Drive chat transcripts** remains
the canonical next build objective. 12 files (3.4MB) downloaded, not yet extracted.

---

## Accepted Limitations (Gate 7)

- **NeMo semantic classifier:** Uses embedding-based intent matching. When new query
  types appear that are incorrectly routed, pass-through intents must be manually added.
- **V4-Pro direct routing:** V4-Pro R1/R2 cannot pass through NeMo because NeMo strips
  `reasoning_content` and `reasoning_tokens` from DeepSeek thinking models.
- **Preflight evidence only:** V4-Pro preflight uses NeMo for evidence collection,
  then calls V4-Pro direct. NeMo does not validate V4-Pro's output.
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
**Phase 4B — Knowledge Base Extraction & Role Enforcement** ← CURRENT
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
