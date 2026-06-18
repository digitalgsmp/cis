# CIS Front Door — End-to-End Pipeline Activation Specification

## Specification Document v1.0

## Eric Gate Status: PENDING_APPROVAL

This document defines the architectural direction for wiring the remaining
functionality that blocks Eric from using the CIS application as designed.
It is NOT an implementation directive. No code shall be written, no files
modified, and no spine rows updated under this document alone. Implementation
proceeds only after Eric Gate approval is recorded.

**Author:** R1 Reviewer (deepseek-v4-pro)
**Date:** 2026-06-17
**Status:** DRAFT — awaiting Eric Gate review
**Gating dependency:** None — all prerequisite tiers are COMPLETE (24/24 active)

---

## 1. Purpose

### 1.1 What this tier solves

CIS has 24 completed build nodes and a fully functional adversarial pipeline
(Drafter → Reviewer → Implementer → Eric Gate). But Eric cannot use it. He
interacts with Hermes bots directly on Telegram, bypassing the entire CIS
system on every interaction. The router never classifies intents. The
deliberation engine never fires. The gates never trigger. CIS is a ghost town
with all the lights on.

Additionally, two tiers marked COMPLETE (MCP Bridge, Chroma/VDB) exist only
as build-plan records — no code was written, no packages installed, nothing
is accessible. The archive drives containing Eric's vision and knowledge base
material are not connected to anything.

### 1.2 Core capability

> **Eric brainstorms with Prime (flash model, 8642) naturally. When an idea
> crystallizes, CIS detects the intent and routes it through the full adversarial
> pipeline (Drafter → dual review → Eric Gate → Implementer). The pipeline fires
> FROM discovery, not instead of it. Prime remains Eric's research partner.**

### 1.3 What changes for Eric

| Before | After |
|--------|-------|
| Eric talks to @cis_hermes_r1bot directly — pipeline bypassed | Eric brainstorms with Prime (8642). When ready, intent routes to CIS pipeline automatically. |
| No connection between discovery and execution | Discovery with Prime → intent crystallizes → pipeline fires → results delivered |
| MCP Bridge marked COMPLETE but `runtime/mcp/` is empty | MCP server running, profiles communicate through it |
| Chroma/VDB marked COMPLETE but chromadb not installed | Archive indexed, semantic search available to all profiles |
| Eric manually routes work between bots | CIS router classifies and dispatches |
| No knowledge base for agents to reference | Archive searchable through VDB via MCP |

---

## 2. Access Boundaries

### 2.1 What this tier SHALL touch

| Asset | Permission | Reason |
|-------|-----------|--------|
| Telegram bot (new: CIS entry point) | Create | Single front door for Eric |
| `runtime/mcp/` directory | Create files | MCP server implementation |
| Python packages (chromadb, mcp) | Install | Required for VDB and MCP |
| Archive drives (`/mnt/archive/`) | Read only | Index for semantic search |
| `data/cis_memory.db` | Read/write via existing paths | Intent routing, gate state |
| Existing pipeline scripts | Invoke via router | Drafter dispatch, deliberation, implementer |

### 2.2 What this tier SHALL NOT touch

| Asset | Reason |
|-------|--------|
| Hermes profiles/configs | Hardening v2.0 complete — no config changes needed |
| Gate scripts | Shell hooks enforce existing gates — no changes |
| CIS UI (Tier 10) | UI overhaul is a separate phase (Penpot/Webstudio later) |
| External escalation (ChatGPT/Claude) | Wiring preserved but not activated |
| SWA application | Removed from CIS — separate project |
| Build plan schema | No migrations needed |

---

## 3. Relationship to Existing Flow

### 3.1 Current state (broken)

```
Eric ──Telegram──→ @cis_hermes_r1bot ──→ R1 responds directly
                     ↑
              Pipeline NEVER fires
              Router NEVER classifies  
              Drafter NEVER dispatched
              Eric Gate NEVER triggers
              Prime (flash) not involved in discovery
```

### 3.2 Target state — Two Phases

**Phase 1: Discovery (Prime — unchanged)**

```
Eric ──Telegram──→ @cis_kernel_bot (Prime, 8642, flash model)
                      │
                      ▼
              Brainstorming, research, discussion
              Ideas form naturally. No pipeline yet.
              
              When idea crystallizes:
              Eric says "draft this" or system detects intent
                      │
                      ▼
              ┌──────────────────┐
              │ INTENT BRIDGE    │ ← Transition point
              │ (detects/accepts │
              │  crystallized    │
              │  intent signal)  │
              └────────┬─────────┘
                       │
                       ▼
              [Phase 2: Pipeline]
```

**Phase 2: Pipeline (unchanged from existing CIS)**

```
              ┌──────────────┐
              │ CIS Router   │ ← classifies intent
              │ (existing)   │
              └──────┬───────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    CIS Intent   WIAS Intent  Unknown
         │           │           │
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐  "I don't
    │Drafter  │ │WIAS     │   understand"
    │dispatch │ │adapter  │
    └────┬────┘ └────┬────┘
         │           │
         ▼           ▼
    ┌─────────────────────┐
    │ Deliberation Engine │ ← R1 + Qwen review
    │ (reviewer_reconcile)│
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────┐
    │   Eric Gate     │ ← Telegram approval
    │ (approve/revise)│
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  Implementer    │ ← builds approved directive
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  Result → Eric  │ ← back to Telegram
    └─────────────────┘
```

Prime remains Eric's research partner. The pipeline does not replace Prime —
it executes work that crystallizes FROM the Prime discussion.

---

## 4. Minimum Architecture

### 4.1 The Intent Bridge — From Discovery to Pipeline

Prime (8642, flash model) remains Eric's research and brainstorming partner.
This does not change. The Intent Bridge is the TRANSITION mechanism that
fires when a Prime discussion crystallizes into actionable work.

The Intent Bridge:
1. Monitors Prime discussions for intent signals — Eric saying "draft this,"
   "spec this out," "build this," or explicit commands
2. When an intent is detected, extracts the crystallized work description
3. Passes it to the CIS Router for classification and dispatch
4. Does NOT respond to Eric directly — Prime handles the conversation

Eric's workflow:
- Brainstorm with Prime (8642) as he always does
- When ready: "Ok, draft a specification for this" or "Turn this into a directive"
- Intent Bridge detects the signal → Router classifies → Pipeline fires
- Eric receives deliberation results → approves from phone → Implementer builds

### 4.2 MCP Bridge — Actually Build It

Tier 8 is marked COMPLETE but `runtime/mcp/` is empty. Need:

| File | Purpose |
|------|---------|
| `runtime/mcp/mcp_server.py` | MCP server exposing CIS tools to profiles |
| `runtime/mcp/tools/draft_spec.py` | Drafter dispatch via MCP |
| `runtime/mcp/tools/review_proposal.py` | Reviewer dispatch via MCP |
| `runtime/mcp/tools/implement_directive.py` | Implementer dispatch via MCP |
| `runtime/mcp/tools/query_spine.py` | Read-only spine queries for all profiles |
| `runtime/mcp/tools/search_knowledge.py` | VDB semantic search through MCP |

The MCP server runs alongside the existing Flask app. Profiles communicate
through MCP instead of direct HTTP calls. This is the abstraction layer
that future-proofs CIS against Hermes updates.

### 4.3 Chroma/VDB — Actually Install and Index

Tier 9 is marked COMPLETE but `chromadb` is not installed. Need:

1. Install `chromadb` package
2. Create indexing pipeline for archive drives
3. Index Eric's documents into Chroma collections
4. Wire the `search_knowledge` MCP tool to Chroma
5. Verify semantic search returns relevant archive content

### 4.4 Files to Create

| File | Purpose |
|------|---------|
| `tools/intent_bridge.py` | Intent detection + transition from Prime discussion to CIS pipeline |
| `runtime/mcp/mcp_server.py` | MCP server entry point |
| `runtime/mcp/tools/__init__.py` | Tool registry |
| `runtime/mcp/tools/draft_spec.py` | Drafter dispatch tool |
| `runtime/mcp/tools/review_proposal.py` | Reviewer dispatch tool |
| `runtime/mcp/tools/implement_directive.py` | Implementer dispatch tool |
| `runtime/mcp/tools/query_spine.py` | Spine query tool |
| `runtime/mcp/tools/search_knowledge.py` | VDB search tool |
| `tools/index_archive.py` | Archive indexing pipeline |

### 4.5 Technology Choices

| Choice | Rationale |
|--------|-----------|
| Telegram bot (existing Hermes messaging) | Eric is on Telegram. Use what works. |
| MCP (Model Context Protocol) | Hermes-native protocol. Profiles connect natively. |
| ChromaDB | Already specified in Tier 9. Lightweight, local, Python-native. |
| Existing router (`runtime/router.py`) | Already built. Just needs to be wired to the entry bot. |
| Existing pipeline scripts | `reviewer_reconcile.py`, `gate_runner.sh` — already tested. |

---

## 5. Required Tables, Files, and Schemas

### 5.1 New database tables

None. The existing spine tables handle intent routing and gate state.

### 5.2 Existing tables used

| Table | Purpose |
|-------|---------|
| `workflow_runs` | Track pipeline runs triggered by entry bot |
| `deliberation_rounds` | Store dual-review results |
| `build_plan_nodes` | Context for agents (current tier, blockers) |

### 5.3 New Python packages

| Package | Version | Purpose |
|---------|---------|---------|
| `chromadb` | latest | Vector database for archive search |
| `mcp` | latest | MCP SDK for server implementation |

### 5.4 Directory structure

```
/mnt/projects/cis/
├── tools/
│   ├── intent_bridge.py              ← NEW: Discovery → Pipeline transition
│   └── index_archive.py              ← NEW: Archive → VDB indexing
└── runtime/
    └── mcp/
        ├── mcp_server.py             ← NEW: MCP server
        └── tools/
            ├── __init__.py
            ├── draft_spec.py
            ├── review_proposal.py
            ├── implement_directive.py
            ├── query_spine.py
            └── search_knowledge.py
```

---

## 6. Security and Approval Boundaries

### 6.1 Environment isolation

The entry bot runs in the existing CIS venv. MCP server runs on localhost.
No new network exposure.

### 6.2 Data access

Archive drives are read-only. The indexing pipeline reads documents, never
writes to the archive. VDB writes go to `data/chroma/`.

### 6.3 Network access

- Entry bot: Telegram API (outbound only)
- MCP server: localhost only
- Chroma: local filesystem only

### 6.4 Approval boundaries

The Eric Gate remains the final authority. The entry bot routes intents
through the FULL pipeline — no shortcuts. Eric must explicitly approve
before the Implementer executes. The shell hooks from hardening v2.0
enforce gate sequence on all write operations.

### 6.5 Audit trail

Every intent → pipeline run → deliberation → Eric Gate decision → implementation
is recorded in `workflow_runs` and `deliberation_rounds`. The entry bot logs
every received message and its routing decision.

---

## 7. Deterministic Acceptance Criteria

### 7.1 Functional acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| A1 | Intent → router fires | Eric says "draft this" in Prime discussion | Intent Bridge detects signal. Router classifies as CIS intent. Drafter dispatched. | Check workflow_runs for new row |
| A2 | Deliberation fires | Drafter produces spec | R1 + Qwen review triggered automatically. Deliberation rounds recorded. | Check deliberation_rounds |
| A3 | Eric Gate delivers to Telegram | Deliberation complete | Eric receives approval request on Telegram with summary | Manual verification |
| A4 | Implementer executes on approval | Eric approves | Implementer builds per directive. Evidence returned. | Check git log, file system |
| A5 | Non-CIS intent handled | Eric sends "What's the weather?" | Router classifies as non-CIS. Responds directly without pipeline. | No workflow_runs row created |
| A6 | MCP tools accessible | Profile queries `search_knowledge("WIAS workflow")` | Returns relevant archive excerpts | Direct MCP tool call |
| A7 | VDB search returns results | Query archive for "creative pipeline stages" | Chroma returns ranked results from Eric's documents | Python test script |
| A8 | Shell hooks still enforce | Implementer tries write without gate | Blocked by cis_pre_tool_gate.sh | Verified per hardening A1 |

### 7.2 Security acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| S1 | MCP only on localhost | External request to MCP port | Connection refused | netcat from external |
| S2 | Archive read-only | Indexing pipeline attempts write to /mnt/archive | Permission denied or blocked | Test script |
| S3 | No pipeline bypass via entry bot | Eric sends "implement X" without prior deliberation | Router requires deliberation first | Check rejection message |

### 7.3 Integration acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| I1 | Full end-to-end | Eric sends intent → approves → receives result | All pipeline stages fire in sequence | Trace workflow_runs |
| I2 | Existing gates unchanged | gate_runner.sh run after MCP/VDB added | Same 5 gates. All PASS. | Compare to pre-MCP baseline |
| I3 | Qwen deliberation via MCP | R1 dispatches review to Qwen through MCP | Qwen returns independent review | Check deliberation_rounds |

---

## 8. Required Tests and Gates

### 8.1 Pre-implementation gates

| Gate | What It Checks | Method |
|------|---------------|--------|
| G1: Git clean | No uncommitted changes conflict with new files | `git status --short` |
| G2: Archive accessible | `/mnt/archive/` is mounted and readable | `ls /mnt/archive/ | head -5` |
| G3: Python 3.11+ | Required for chromadb and mcp packages | `python3 --version` |
| G4: Disk space | Sufficient for Chroma index (~2GB estimated) | `df -h /mnt/projects/cis/` |

### 8.2 Post-implementation verification gates

| Gate | What It Checks | Method |
|------|---------------|--------|
| G5: MCP server running | `runtime/mcp/mcp_server.py` responds to tools/list | MCP client test |
| G6: Chroma collection exists | `data/chroma/` has indexed documents | `python3 -c "import chromadb; ..."` |
| G7: Archive search works | Semantic search returns relevant results | Test queries against known documents |
| G8: Entry bot routes correctly | CIS intent → pipeline fires. Non-CIS → direct response. | Manual test via Telegram |
| G9: Shell hooks survive | Write to CIS dir still requires gate clearance | Hardening A1 test |

---

## 9. Out of Scope

| Item | Reason |
|------|--------|
| Penpot/Webstudio integration | UI design phase — after CIS is usable |
| Profiles migration (5→1) | Deferred — current architecture works |
| External escalation (ChatGPT/Claude) | Paused — wiring preserved, API keys not activated |
| SWA application | Removed from CIS — separate project |
| WIAS full operationalization | After CIS pipeline is functional |
| UI overhaul | After pipeline is proven in daily use |
| Hermes dashboard extensions | After profiles migration |

---

## 10. Eric Gate Approval Required

### 10.1 Gating conditions

Implementation shall not begin until ALL of:

| # | Condition | Verification |
|---|-----------|-------------|
| 1 | This specification approved by Eric Gate | Eric's explicit message |
| 2 | Dual-review complete (R1 + Qwen) | CONSENSUS_REACHED in deliberation_rounds |
| 3 | Qwen independently verified approach | Per Eric's directive |
| 4 | Eric explicitly issues PROCEED or IMPLEMENT | Not automatic |

### 10.2 What happens after approval

1. Build_plan_nodes created in spine: Front Door, MCP Bridge (build), VDB (build)
2. Eric issues IMPLEMENT → Implementer (8646) executes per phased plan
3. Each phase verified before next begins
4. Eric tests the entry bot — sends a real intent through the pipeline
5. Closeout only after Eric confirms pipeline fires automatically

---

## 11. Phased Build Plan

### 11.1 Build nodes

| Node | Label | Depends On | Scope |
|------|-------|-----------|-------|
| FD.1 | MCP Server + Tools | None | Build `runtime/mcp/` with 6 tools |
| FD.2 | Chroma/VDB | None | Install chromadb, index archive |
| FD.3 | Intent Bridge | FD.1, FD.2 | Build `intent_bridge.py` — Prime → Router transition |
| FD.4 | Integration Test | FD.3 | Full end-to-end: intent → pipeline → result |

### 11.2 Dependency graph

```
FD.1 (MCP Server) ──┐
                    ├── FD.3 (Entry Bot) ── FD.4 (Integration)
FD.2 (VDB) ────────┘
```

### 11.3 What each node does NOT include

| Node | Exclusions |
|------|------------|
| FD.1 | Does not modify existing pipeline scripts. Does not touch Hermes configs. |
| FD.2 | Does not write to archive drives. Does not modify existing databases. |
| FD.3 | Does not change Eric Gate flow. Does not bypass shell hooks. |
| FD.4 | Does not deploy to production. Does not modify AGENTS.md. |

---

## 12. Recommendation

Approve this specification. It addresses the critical blocker preventing Eric
from using the CIS application: the missing bridge from discovery to execution.
Eric brainstorms with Prime (flash model, 8642) as he always has. When an idea
crystallizes, the Intent Bridge detects the signal and routes it through the
full adversarial pipeline — Drafter, dual review (R1+Qwen), Eric Gate,
Implementer — automatically. It also delivers the two paper-COMPLETE tiers
(MCP Bridge, Chroma/VDB) that exist only as build-plan records. Once complete,
Eric's workflow is: discuss with Prime → intent crystallizes → pipeline fires →
approve from phone → receive results. The Penpot/Webstudio UI phase follows
naturally from a working pipeline. Prime is never replaced — it's the
discovery engine that feeds the pipeline.

---

## Appendix A: Evidence References

### A.1 MCP Bridge is empty

```
COMMAND: ls /mnt/projects/cis/runtime/mcp/ 2>/dev/null
OUTPUT: (empty — directory exists but contains no files)
```

### A.2 ChromaDB not installed

```
COMMAND: python3 -c "import chromadb; print(chromadb.__version__)" 2>&1
OUTPUT: ModuleNotFoundError: No module named 'chromadb'
```

### A.3 All 5 gateways healthy

```
COMMAND: for port in 8642 8643 8644 8645 8646; do curl -s -o /dev/null -w "Port $port: %{http_code}\n" http://127.0.0.1:$port/health; done
OUTPUT:
Port 8642: 200
Port 8643: 200
Port 8644: 200
Port 8645: 200
Port 8646: 200
```

### A.4 Build plan — 24/24 active COMPLETE

```
COMMAND: sqlite3 data/cis_memory.db "SELECT status, COUNT(*) FROM build_plan_nodes GROUP BY status;"
OUTPUT:
COMPLETE|24
DEFERRED|3
```

### A.5 Shell hooks deployed

```
COMMAND: for home in /home/eric/.hermes /home/eric/.hermes-r1 /home/eric/.hermes-v4pro /home/eric/.hermes-v4impl; do
  HERMES_HOME=$home hermes hooks list 2>&1 | grep "cis_pre_tool_gate" | grep -o '[✓✗] \w*'
done
OUTPUT:
✓ allowed  (×4 profiles)
```

### A.6 Penpot MCP Server exists

```
SOURCE: https://penpot.app/penpot-mcp-server
Penpot MCP Server enables AI assistants to programmatically create,
modify, and manage designs through 76+ MCP tools.
```

---

*End of CIS Front Door Specification v1.0*
*Status: DRAFT — awaiting Eric Gate review*
*Next: Qwen independent review → Eric reads → approves → IMPLEMENT*
