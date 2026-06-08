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
| 2A — Session-start context injection | **Absorbed** | Tier 8 (MCP Bridge) — query tools feed Drafter context without full AGENTS.md regeneration. Also partially covered by Tier 5 (AGENTS.md auto-loading + HCP packet). |
| 2B — FTS5 lexical search (POST /api/knowledge/search) | **Absorbed** | Tier 9 (Chroma/VDB) — vector index replaces FTS5. Same goal, better retrieval. |
| 2C — Import Claude/ChatGPT transcripts | **Dependency-blocked** | Requires session import pipeline stable + VDB (Tier 9) to index. Transcripts exist in docs/claude_chat_transcripts/. import_session.py exists but only handles Hermes sessions. |
| 2D — Notes capture (capture_notes table + /note command) | **Deferred-unscheduled** | No v2.0 tier assigned. Self-contained — no upstream dependencies. Could be built at any time. |

Verdict: Knowledge search and context injection have homes at Tiers 8-9. Transcript import is blocked on VDB. Notes capture is the only item with no scheduled home.

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
| cards | No | **Dependency-blocked** — needs Tier 7 Kanban integration |
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
| Absorbed | 11 | Gateway config (7), context injection, FTS5, UI reorg (3) |
| Deferred-scheduled | 1 | export_manifests table (Tier 6) |
| Deferred-unscheduled | 9 | Notes capture, Quick Capture, 6 spine tables |
| Dependency-blocked | 2 | Claude/ChatGPT import, cards table |
| Superseded | 2 | Brave search, review_rounds table |
| Cancelled | 0 | — |

## Open Questions for Review

1. Should notes capture (2D) be explicitly scheduled as a standalone Tier or bundled into Tier 10?
2. Should Claude/ChatGPT import run before VDB (Tier 9) or after? Transcripts must be imported before they can be indexed.
3. Are the 8 deferred spine tables needed before Tier 8 (MCP Bridge) which queries spine state?
4. Does the "cards" table need to exist before Tier 7 (Router Kanban integration)?

---

*DRAFT status: This document is a Hermes-generated proposal. It does not represent an Eric-approved decision. Items classified as Deferred-unscheduled are NOT cancelled — they await scheduling by Eric after external advisor review.*
