# For Claude — Why the Spine Is Stale and Needs Rebuilding

**From:** Eric + Hermes V4 Pro  
**To:** Claude (external advisor)  
**Date:** 2026-07-01  
**Context:** Before you guide Eric through the container build, you need to understand why the database is producing stale handoffs and why we concluded it needs a ground-up restructure.

---

## Part 1: Why Latest Activities Don't Update to the DB

### The symptom

AGENTS.md was regenerated today (July 1, 12:22 UTC) from the spine. It is stale on arrival. Compare what it claims against what's actually true right now:

| AGENTS.md claims | Actual reality | Evidence |
|---|---|---|
| "Phase 0 IN PROGRESS… Build target: counter for identical ToolCallSignature" | **Built.** Loop-breaker deployed today. | `grep -c '_success_repeat_counts' tool_guardrails.py` → 4 matches |
| "BLK-SEED-006: Loop-breaker gap… Fix needed" | **Resolved.** Code deployed, tested. | Same grep |
| "Do Not Start — Discord/Telegram gateway" | **Telegram IS connected.** We're talking on it. | Gateway pid 1825472 listening on 8645 |
| Only MCP mention: "restart gateways for MCP" (a Next action for Eric) | **MCP has 18 tools** live. `cis-knowledge` connects in 408ms. | `grep -c '"name"' tools.py` → 18 |
| Session handoff says "June 27-29" | It's **July 1**. 3 days of work invisible. | `date` |
| No mention of container enforcement | Node 60 exists in build_plan_nodes but generators don't surface PENDING nodes well | `SELECT * FROM build_plan_nodes WHERE id=60` |
| "9 tools" in server.py docstring | Actually 18 tools | `grep -c '"name"' runtime/mcp_bridge/tools.py` → 18 |

### The root cause

AGENTS.md is regenerated from the spine by `tools/export/generate_agents_md.py`. That generator reads 7 tables: `workflow_runs`, `project_decisions`, `open_questions`, `build_plan_nodes`, `next_actions`, `active_blockers`, `project_state`, `eric_gate_approvals`, `session_handoffs`.

None of these tables track **operational reality**. They track **build-plan progress**. The spine was designed when CIS was a build-plan tracker. But CIS evolved into a multi-agent collaboration system with real-time operational awareness, knowledge accumulation, evidence-backed verification, and intention-to-outcome tracking.

Things the spine cannot represent:
- Which gateways are up or down (ss -tlnp output)
- How many MCP tools exist
- Whether loop-breaker code is deployed
- Whether Telegram is connected
- What was just discussed in chat
- Whether a claim has been verified by a reviewer
- What Eric's original intentions were vs. what was built

Every new need was solved by adding another table. The spine now has **32 non-FTS tables** — but 287,636 of the 287,700 total rows live in a single table (`knowledge_messages`). The original build-plan tables have 30 rows. The tail is wagging the dog.

---

## Part 2: What We Realized About the Database Design

### The frankenstein problem

Eric identified it directly: *"I have concerns that we are just making a frankenstein monster db at this point."*

The 32 tables represent 7+ different domains, each added at a different time for a different reason:

| Domain | Tables | Rows | Added when |
|---|---|---|---|
| Build plan | build_plan_nodes, build_plan_dependencies | 30 | Original design |
| Workflow execution | workflow_runs, deliberation_rounds, dispatch_log, dispatch_events, +2 artifacts | ~40 | Pipeline phase |
| Knowledge | knowledge_messages + FTS5, dam_assets, dam_extracted_text + FTS5 | 287K | Ingestion phase |
| Governance | project_decisions, open_questions, next_actions, active_blockers, eric_gate_approvals, goal_references, rejection_rationale, decision_trails, advisor_escalations ×3 | ~150 | Scattered across phases |
| Intentions | intent_map, anti_patterns, drift_indicators, functional_spec, reviewer_brief | ~30 | Early design, barely used |
| Session | session_handoffs, session_closeouts + FTS5 | ~5 | Handoff phase |
| Dev tracking | dev_pivot_status | 17 | Recent addition |
| State | project_state (114 rows, duplicate keys), lifecycle_events | ~120 | Scattered |

Every one of these is actually the same thing: **an observation** — something that happened with a timestamp, a source, a target, and content. The only differences are what it's about and how it's verified.

### The new design: 4 core tables instead of 32

Everything in CIS reduces to five activities:

1. **Something happens** — a message, a decision, a status change, an ingestion
2. **It's about something** — a gateway, a tier, a tool, a document
3. **It might make a claim** — that needs evidence and verification
4. **It relates to an intention** — what Eric originally asked for
5. **It's searchable** — full-text and semantic

These map to 4 tables:

```
observations        — the append-only event stream (replaces ~20 tables)
entities            — what observations are about (replaces structural columns of build_plan_nodes, dev_pivot_status, dam_assets)
intentions          — Eric's verbatim asks, linked to fulfilling observations
verification_queue  — a VIEW over observations WHERE evidence_type IS NOT NULL AND verified=0
```

**What an observation row looks like:**

```sql
observations (
    id, timestamp, source, type, target_entity, content, content_text,
    parent_id, evidence_type, evidence_cmd, evidence_expected, verified
)
```

**Concrete examples of what goes in it:**

| type | source | target_entity | content |
|---|---|---|---|
| `message` | eric | null | `{"text": "how do we take external session..."}` |
| `status_change` | system | gateway.8642 | `{"status": "DOWN", "evidence": "ss -tlnp"}` |
| `completion` | v4-impl | loop_breaker | `{"claim": "deployed", "evidence_cmd": "grep -c..."}` |
| `verification` | r1-reviewer | loop_breaker | `{"result": "PASS", "actual": "4"}` |
| `decision` | eric | container_enforcement | `{"decision": "APPROVED", "scope": "ADR-015/016"}` |
| `ingestion` | system | claude-session | `{"source": "claude-external-advisor", "count": 47}` |

**What disappears:** 20+ tables collapse into `observations`. `project_state` (114 rows of duplicate-key chaos) becomes the latest observation per entity. `build_plan_nodes` status becomes the latest completion observation per tier entity. Every new need is a new observation type or entity type, not a new table.

**What stays (different purpose):**
- `workflow_runs` + `deliberation_rounds` — pipeline execution has structured state machine semantics
- `dam_assets` + `dam_extracted_text` — document archive is a content store, not an event stream
- ChromaDB (external) — vector search is a separate engine

### Why this matters for the container build

The containerized Hermes should write to a **clean spine**, not the frankenstein. The old spine becomes read-only reference. The new spine is what the roadmap page queries, what the handoff packet is generated from, and what reviewers verify against.

Specifically:
- Every message from Eric → `observations` row
- Every agent action → `observations` row
- Every gateway status change → `observations` row
- Every verification → `observations` row
- Every decision → `observations` row

The roadmap page queries: `SELECT * FROM entities WHERE type='gateway'` then `SELECT content FROM observations WHERE target_entity='gateway.8642' ORDER BY timestamp DESC LIMIT 1` for current status. Always real-time. Never stale.

### The evidence-backed trust model

Eric made this explicit: *"This should be a trustless system where everything is proven by evidence, not model self-reporting without real proof acceptable to a model looking for certain signs of authentication."*

Every claim in the new spine has:
- `evidence_type` — 'command', 'file_contains', 'db_query', 'endpoint', 'git', 'docker'
- `evidence_command` — the exact command to verify
- `evidence_expected` — what output must match
- `evidence_actual` — what the reviewer got (null until verified)
- `verified_by` — which agent verified it

The reviewer model doesn't trust claims. It runs the evidence command and checks the output. Binary: PASS or REJECT.

---

## What This Means for Your Container Build

The container build spec (`CONTAINER_HERMES_BUILD_SPEC.md`) focuses on getting Hermes running sealed in Docker. That's the immediate priority — the enforcement walls must be proven permanent before any CIS work moves inside.

**The spine restructure is the NEXT phase**, not this one. It's explicitly listed as OUT OF SCOPE in the build spec. The sequence is:

1. **Container Hermes build** (your guide, Eric executes) — Hermes runs sealed in Docker, enforcement proven permanent
2. **Spine restructure** (design above, Hermes implements inside container) — 32 tables → 4 core tables, observations model, trustless evidence
3. **Roadmap page** — queries new spine live, always current
4. **Realtime ingestion** — gateway writes to observations, chat flows into spine continuously

But you need to know about the spine design because it affects how you think about the container. The containerized Hermes will be the agent that builds the new spine. It needs to understand what it's building toward.

---

## Key Files for Context

| File | What it tells you |
|---|---|
| `docs/CONTAINER_HERMES_BUILD_SPEC.md` | Your build guide — 8 steps, 11 acceptance criteria |
| `docs/DEV-PIVOT-17_ENFORCEMENT_ARCHITECTURE.md` | Architecture decisions (settled) |
| `docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md` | Full enforcement spec (703 lines) |
| `AGENTS.md` | Current state snapshot (stale — shows why we need the restructure) |
| `enforcement/mwl-proof-v2/` | POC proof files, Dockerfile, managed config |
