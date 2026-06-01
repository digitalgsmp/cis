# CIS Phase Log

## 2026-05-22

### Phase 0 — Architecture Freeze
CHAT_FIRST_CIS_ARCHITECTURE_v1.md written and approved. Prototype state frozen.

### Phase 1 — Advisor Chat Direct Mode
Removed hardcoded auto-routing from api/advisor.py. Prime→R1 and R1→Prime loops removed. `/api/advisor/chat` now returns only `{'agent': agent_name, 'content': reply}`. AdvisorChat.jsx required no changes. Direct Mode tests passed for Prime and R1; Qwen errored with HTTP 503 (see below).

### Qwen Diagnosis and Resolution
llama-server-qwen.service had been in a crash loop since May 19 21:18 (52+ hours). Root cause: VRAM exhaustion. Both llama-slot1 (Qwen3.6-35B-A3B-MXFP4_MOE.gguf, port 8001) and llama-server-qwen (qwen3-vl-30b-a3b-instruct-q4_k_m.gguf, port 8002) were configured with full GPU offload and cannot coexist on a single RTX 4090 (24 GB). Startup ordering test confirmed Qwen works when started first, but Slot 1 fails.

### llama-slot1.service — Disabled
llama-slot1.service disabled intentionally for current Advisor Chat architecture. Qwen3.6-35B-A3B-MXFP4_MOE.gguf cannot coexist with qwen3-vl-30b-a3b-instruct-q4_k_m.gguf on a single 24GB GPU when both use full GPU offload. Prime and R1 confirmed API-backed with no active dependency on port 8001. Slot 1 is disabled for now and should not be re-enabled without explicit architecture review. Qwen owns the local GPU role as Slot 3 worker for Advisor Chat Phase 2. The previous systemd ordering fix is no longer needed while Slot 1 remains disabled.

### Phase 2 — Parallel Compare Mode (COMPLETE)
Added POST /api/advisor/parallel endpoint (advisor.py lines 190–263). Frozen context snapshot built before any gateway calls — all three agents receive identical messages. Concurrent gateway calls via ThreadPoolExecutor (max_workers=3). Sequential DB writes after all calls complete. Individual failures do not abort sibling calls. Response: `{"results": [{"agent":"...","content":"...","ok":true,"error":null}, ...]}`.

AdvisorChat.jsx: Added Direct/Parallel mode toggle (lines 297–311). Parallel mode hides per-agent inputs, shows single shared input with "Compare" button calling /api/advisor/parallel. AgentPanel accepts mode prop — shows "Parallel mode — use shared input above" when active. Loading indicator below panels during parallel calls. Direct mode unchanged.

All three agents verified independent — no agent sees another's answer during first parallel round. No cross-contamination.

Files changed: advisor.py (268→344 lines), AdvisorChat.jsx (367→417 lines). No schema changes. No scope creep. No Reconcile Mode logic added.

## 2026-05-23

### Phase 3 — Reconcile Mode (COMPLETE)
Reconcile Mode implemented and live-verified.
- New file: /mnt/projects/cis/runtime/api/reconciliation.py
- New endpoint: POST /api/reconciliation/reconcile
- app.py registered reconciliation_bp
- advisor_messages: nullable batch_id TEXT column added
- New table: advisor_reconciliations (id, thread_id, batch_id, agent_name, model, synthesis_content, reconciliation_json, created_at)
- Parallel Compare endpoint now generates and returns batch_id (UUID)
- All four rows per parallel round (1 user + 3 assistant) stamped with same batch_id
- Reconcile button and result panel added inside AdvisorChat — not a separate page
- Direct Mode verified unchanged — batch_id NULL on all direct messages
- Parallel Mode verified unchanged after Reconcile additions
- Live test batch_id: e296b867-c8d5-4446-bff7-c015dff7ed47
- DB insert verified in advisor_reconciliations (id=1, thread_id=4, agent_name=hermes-prime)
- No Phase 4 auto-structuring added
- Files changed: advisor.py, reconciliation.py, app.py, AdvisorChat.jsx, cis_memory.db

### Phase 4 — Auto-Structure (COMPLETE)
Idea drafts with domain classification, AI-suggested domains, inline review panel, Structure This button. Drafts save/promote to CIS ideas. Documented in CHAT_FIRST_CIS_ARCHITECTURE_v1.md. Phase log entry from original architecture reset on May 22.

### Streaming — ChatConsole + AdvisorChat (COMPLETE)

**ChatConsole**: SSE streaming endpoint `/api/collab/rounds/<id>/send-to-hermes-stream`. Frontend uses fetch + ReadableStream + flushSync + 10ms paint yield for word-by-word streaming with blinking cursor. Anti-buffering headers (Cache-Control, X-Accel-Buffering, Connection).

**AdvisorChat Prime**: `/api/advisor/chat-stream` SSE endpoint. AgentPanel.send() uses streaming for hermes-prime (later extended to hermes-v4pro). streamingRef guard prevents polling overwrite during active streams. flushSync + 10ms delay for visible word-by-word rendering.

**Qwen context size**: llama-server-qwen.service updated from `--ctx-size 8192` to `--ctx-size 32768`. Resolved context-exceeded errors that caused Qwen to silently fail.

## 2026-05-24

### Architecture Reset — 4-Panel Advisor Chat (Pass 2 COMPLETE)

**New role architecture:**

| Panel | Agent | Model | Role |
|-------|-------|-------|------|
| R1 | hermes-r1 | deepseek-reasoner | Deep Reasoning |
| V4-Pro | hermes-v4pro | deepseek-v4-pro | Deep Analyst |
| Prime | hermes-prime | deepseek-v4-flash | Fast Chat |
| Worker | hermes-qwen | qwen3-vl-30b (local) | Execute |

**Key changes:**
- `hermes-v4pro` added to agent_instances table (port 8642, same gateway as Prime)
- `DELIBERATION_AGENTS = ('hermes-r1', 'hermes-v4pro')` in advisor.py
- Parallel mode restricted to R1 + V4-Pro only (max_workers=2)
- Prime excluded from deliberation (fast chat only)
- Qwen excluded from deliberation (execution only)
- R1 structured response wrapper (CORE JUDGMENT / REASONING / RISKS / RECOMMENDED NEXT ACTION)
- Frontend: 2×2 grid layout, model badges in panel headers
- V4-Pro streaming enabled (same condition as Prime)
- Parallel mode messages per role: deliberation agents show "Deliberating", Prime shows "not part of deliberation", Worker shows "final directives only"
- Parallel button renamed "Deliberate", placeholder "Ask R1 + V4-Pro to deliberate…"

### Pass 2B — R1 UX Improvements (COMPLETE)

- **R1 phased loading**: "Submitting to R1…" (0-2s), "Reasoning in progress…" (2-8s), "Reasoning: Ns" (8s+). Elapsed timer with 1s interval.
- **R1 structured output rendering**: R1StructuredMessage component parses CORE JUDGMENT / REASONING / RISKS / RECOMMENDED NEXT ACTION headers. Renders as labeled color-coded blocks. Falls back to plain text if <2 sections found.
- **V4-Pro critique refresh**: v4ProRefreshKey state in parent. Critique button calls onCritiqueV4Pro() after saving. refreshKey in polling useEffect dependency array triggers immediate V4-Pro panel refresh.
- R1 input placeholder: "Ask R1 something hard…"

### Pass 3 — External Review Capture (COMPLETE)

**New table**: `advisor_external_reviews` — captures Claude/ChatGPT paste-back reviews.
- Columns: id, thread_id, batch_id, source, escalation_prompt, response_text, recommendation_summary, risks, proposed_next_action, verdict, status, timestamps
- Verdicts: approve / revise / reject / unclear
- Statuses: captured / reviewed / reconciled / superseded

**New file**: `api/advisor_external.py` — 5 endpoints:
- `POST /api/advisor/external-reviews` — create review
- `GET /api/advisor/external-reviews?thread_id=N` — list reviews
- `GET /api/advisor/external-reviews/<id>` — single review
- `PATCH /api/advisor/external-reviews/<id>` — update (verdict, status, fields)
- `POST /api/advisor/escalation-prompt` — generates prompt from thread context

**Frontend**: External Reviews collapsible section below 2×2 grid. Add Review form with source/verdict selectors, prompt/response textareas, optional fields. Review cards with source/verdict badges, Edit button. "Escalate →" button on R1 and V4-Pro assistant responses.

### Pass 4 — Reconciliation Redesign (COMPLETE)

**Schema**: `external_review_ids TEXT` column added to `advisor_reconciliations`.

**reconciliation.py rewrite**:
- Synthesis caller: `hermes-v4pro` (was `hermes-prime`)
- Inputs: R1 + V4-Pro only (Prime and Qwen excluded)
- External reviews: fetched from `advisor_external_reviews` where status IN ('captured','reviewed')
- New JSON schema: divergence_map keys (r1, v4pro, claude, chatgpt), consensus field, external_reviews_included count
- External reviews marked `reconciled` in same transaction as reconciliation save
- Returns `external_reviews_included` count

**Frontend**: Reconciliation display shows "· N external review(s) included" when count > 0.

### Pass 4B — Execute From Approved Reconciliation (COMPLETE)

**execute_directive() rewrite** in advisor.py:
- Fetches latest reconciliation from `advisor_reconciliations ORDER BY id DESC LIMIT 1`
- Returns 409 with `code: NO_RECONCILIATION` if none exists
- Returns 409 with `code: NO_NEXT_ACTION` if reconciliation lacks approved next_action
- Builds clean directive: reconciliation synthesis, approved next action, unresolved items
- No raw thread dump — old phrases "FULL DELIBERATION" and "Extract the final agreed-upon" removed
- Qwen receives only approved directive, not raw deliberation
- Returns reconciliation_id, next_action, confidence in response

**Frontend**:
- Execute button: green "⚡ Execute" when reconciliation exists, slate "⚡ Execute (checks reconciliation)" when null
- Success label: "✓ Sent to Worker" (was "✓ Sent to Qwen")
- 409 error handling with alert for NO_RECONCILIATION / NO_NEXT_ACTION

**Smoke test**: WORKER_OK returned in 23 seconds. Qwen 30B local model, GPU 100% during generation.

---

## Current State Summary

**Active file**: `/mnt/projects/cis/runtime/ui/src/pages/infra/AdvisorChat.jsx` (1096 lines)

**Agent instances** (cis_memory.db):
| name | role | model | gateway |
|------|------|-------|---------|
| hermes-prime | coordinator | deepseek-v4-flash | :8642 |
| hermes-r1 | senior-advisor | deepseek-reasoner | :8643 |
| hermes-qwen | worker | qwen3-vl-30b (local) | :8644 |
| hermes-v4pro | deep-analyst | deepseek-v4-pro | :8642 |

**Backend blueprints**: advisor, advisor_external, reconciliation, idea_drafts, collab, collab_rounds

**Tables**: advisor_threads, advisor_messages, advisor_reconciliations, advisor_external_reviews, agent_instances, idea_drafts

**Streaming**: Prime (flash) and V4-Pro stream via SSE. R1 and Worker are blocking.

**Deliberation**: R1 + V4-Pro in Parallel mode. Reconciliation uses V4-Pro as synthesis caller.

**Execution**: Qwen receives approved reconciliation directives only (Pass 4B).

**Pending**: Pass 5 (Project Promotion), Pass 6 (KB wiring / VDB). Claude/ChatGPT live API routing explicitly deferred.
