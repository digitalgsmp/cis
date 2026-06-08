# Plan Reconciliation — Foundation Plan v1.4 vs Dependency Graph Plan v2.0

**DRAFT — pending Eric / external advisor review. Not authoritative.**

Prepared: 2026-06-08 | Source: git log, spine, AGENTS.md, HCP_*

---

## Purpose

Map every item from `docs/BUILD_PLAN_CIS_FOUNDATION.md` (v1.4, 2026-05-26)
against `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` (v2.0, 2026-06-05)
with explicit disposition. This resolves the ambiguity created when v2.0
stated "Nothing is added. Nothing is removed" but silently deferred
Foundation Plan items without scheduling them.

## Disposition Key

| Disposition | Meaning |
|---|---|
| **Absorbed** | Mapped to specific dependency graph tier |
| **Deferred-scheduled** | In plan at specific future tier |
| **Deferred-unscheduled** | Still required, no tier assigned in v2.0 |
| **Dependency-blocked** | Still required, blocked on upstream tier completion |
| **Superseded** | Replaced by newer architecture |
| **Cancelled** | Explicitly not being built |

---

## Phase 1 — Gateway Configuration (Foundation Plan)

| Foundation Item | Disposition | Where |
|---|---|---|
| 1.1 — Fix Prime HERMES_HOME | **Absorbed** | Tier 2.1-2.2 (Gateway readiness + restart) |
| 1.2 — Named providers in Prime config | **Absorbed** | Pre-Tier 0 (Phase 0 gateway repair) |
| 1.3 — Named providers in R1 config | **Absorbed** | Pre-Tier 0 (Phase 0 gateway repair) |
| 1.4 — Fix Qwen restart loop | **Absorbed** | Pre-Tier 0 (Phase 0 gateway repair) |
| 1.5 — Behavioral verification of advisors | **Absorbed** | Pre-Tier 0 (Phase 0 verification) |
| 1.6 — Enable web search (Brave) | **Superseded** | NeMo + Tavily replaced Brave; NeMo is evidence firewall |
| 1.7 — Per-role personalities | **Absorbed** | Pre-Tier 0 (personality configs in gateway profiles) |

Verdict: Phase 1 fully absorbed into pre-Tier 0 gateway repair + Tier 2 Kanban coordination.

---

## Phase 2 — Knowledge Base Wiring (Foundation Plan)

| Foundation Item | Disposition | Where / Why |
|---|---|---|
| 2A — Session-start context injection | **Partially absorbed** | Tier 5 AGENTS/HCP exports provide current-state briefing. Future enhancement scheduled for Tier 8 MCP Bridge (query tools). |
| 2B — FTS5 lexical search (POST /api/knowledge/search) | **Deferred-scheduled** | Tier 9 retrieval layer. Open question: FTS5 + Chroma hybrid vs Chroma-only. |
| 2C — Import Claude/ChatGPT transcripts | **Deferred-unscheduled** | Blocked on import schema/design, not VDB. VDB indexing depends on imported corpus. Transcripts exist in docs/claude_chat_transcripts/. import_session.py exists but only handles Hermes sessions. |
| 2D — Notes capture (capture_notes table + /note command) | **Deferred-unscheduled** | No v2.0 tier assigned. Self-contained — no upstream dependencies. Could be built at any time. |

Verdict: Context injection partially covered by Tier 5 exports, fully at Tier 8. Knowledge search deferred to Tier 9 with hybrid approach open question. Transcript import and notes capture remain unscheduled.

---

## Phase 3 — UI Layout Reorganization (Foundation Plan)

| Foundation Item | Disposition | Where / Why |
|---|---|---|
| 3.1 — Remove standalone Chat from nav | **Absorbed** | Tier 10 (CIS UI/custom display views) |
| 3.2 — Advisor Chat as primary, Infra separate | **Absorbed** | Tier 10 (CIS UI/custom display views) |
| 3.3 — Separate CIS Core from Project Mgmt | **Absorbed** | Tier 10 (CIS UI/custom display views) |
| 3.4 — Quick Capture panel on Advisor Chat | **Deferred-unscheduled** | Depends on notes capture (2D). No v2.0 tier assigned. |

Verdict: UI reorg has a home at Tier 10 but Quick Capture is blocked on notes capture being scheduled.

---

## Phase D — SQLite Spine (13 tables from Build Proposal v1.0)

| Table | Built? | Disposition |
|---|---|---|
| workflow_runs | Yes (Tier 4) | Complete |
| cards | No | **Deferred-scheduled** | Not a Tier 7 blocker unless Router Reclassification requires querying card history from SQLite spine. Hermes Kanban `kanban.db` remains coordination source. |
| research_artifacts | No | **Deferred-unscheduled** — no v2.0 tier |
| proposals | No | **Deferred-unscheduled** — no v2.0 tier |
| review_rounds | No | **Superseded** by deliberation_rounds table |
| consensus_records | No | **Deferred-unscheduled** — no v2.0 tier |
| final_directives | No | **Deferred-unscheduled** — no v2.0 tier |
| implementation_artifacts | No | **Deferred-unscheduled** — no v2.0 tier |
| verification_runs | No | **Deferred-unscheduled** — no v2.0 tier |
| project_state | Yes (Tier 6.5 remediation) | **Complete** — this document's parent remediation |
| decisions | Yes (Tier 4.4) | Complete |
| open_questions | Yes (Tier 4.4) | Complete |
| next_actions | Yes (Tier 4.4) | Complete |
| file_changes | No | **Deferred-unscheduled** — no v2.0 tier |
| export_manifests | Partial (JSON file) | **Deferred-scheduled** — Tier 6 integration |

Verdict: 6 of 15 tables built. project_state added in remediation. 8 remain deferred with no clear trigger.

---

## Summary

| Status | Count | Items |
|---|---|---|
| Absorbed | 8 | Gateway config (7), UI reorg 3.1-3.3 |
| Partially absorbed | 1 | Session-start context injection (Tier 5 + Tier 8) |
| Deferred-scheduled | 4 | FTS5/search (Tier 9), export_manifests (Tier 6), cards table (Tier 7+), UI Quick Capture (Tier 10) |
| Deferred-unscheduled | 9 | Notes capture, Claude/ChatGPT import, 6 spine tables, Quick Capture panel |
| Dependency-blocked | 0 | — |
| Superseded | 2 | Brave search, review_rounds table |
| Cancelled | 0 | — |

**Scheduling note:** Notes capture is operational infrastructure, not merely UI.
Consider scheduling as Tier 7.5 or Tier 8 prerequisite, rather than deferring to Tier 10.
Quick Capture panel (3.4) should follow the capture backend, not precede it.

## Open Questions for Review

1. Should notes capture (2D) be explicitly scheduled as Tier 7.5 or Tier 8 prerequisite rather than deferred to Tier 10?
2. Should Claude/ChatGPT import be scheduled before VDB (Tier 9)? Transcripts must be imported before they can be indexed.
3. Are the 8 deferred spine tables needed before Tier 8 (MCP Bridge) which queries spine state?
4. Does the cards table need to exist before Tier 7 (Router Kanban integration)? Current assessment: not a blocker.
5. **Should Tier 9 retrieval use FTS5 + Chroma hybrid search or Chroma-only?** FTS5 excels at exact phrase/keyword matching; Chroma excels at semantic similarity. A hybrid approach could combine both strengths.

---

*DRAFT status: This document is a Hermes-generated proposal. It does not represent an Eric-approved decision. Items classified as Deferred-unscheduled are NOT cancelled — they await scheduling by Eric after external advisor review.*
