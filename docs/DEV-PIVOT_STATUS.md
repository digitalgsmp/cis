# DEV-PIVOT Status Report
Generated: 2026-07-09 04:45 UTC | Run: run-47deac6fb82e
Source: SQLite spine (dev_pivot_status table)
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_dev_pivot_manifest.py

Each DEV-PIVOT document represents a problem important enough to spec.
INVALIDATED = progress solved it. LIVE = problem still unsolved.

---

## INVALIDATED — Capability progress made these obsolete

### DEV-PIVOT-08: Front Door Spec
**Invalidated by:** `mcp_semantic_search`
**Reason:** MCP bridge now live with 17 tools. ChromaDB installed with 3125 indexed docs. runtime/mcp_bridge/ exists.
**Affected sections:** §4.2, §4.3, §4.4, §11.1, Appendix A.1, A.2

### DEV-PIVOT-15: Session Open Items (June 14)
**Invalidated by:** `time_passed`
**Reason:** Date-stamped session snapshot from June 14. Superseded by 16 days of subsequent work.

## PARTIALLY INVALIDATED — Assumptions changed under them

### DEV-PIVOT-02: Enforcement Architecture V3
**Changed by:** `mcp_semantic_search`
**What changed:** Threat model assumes agents only have Hermes-native tools (write_file, patch, terminal). MCP adds second access channel to spine data.
**Remaining gap:** Enforcement model assumes smaller attack surface
**Affected sections:** §0.2, §2

### DEV-PIVOT-09: Front Door Build Plan
**Changed by:** `mcp_semantic_search`
**What changed:** FD.1 partially built (17 tools, server.py). FD.2 complete (ChromaDB). FD.3-FD.4 not started.
**Remaining gap:** FD.3 Intent Bridge, FD.4 Integration Test not built
**Affected sections:** §11.1, §11.2

### DEV-PIVOT-17: Enforcement Architecture — Process Isolation
**Changed by:** `mcp_semantic_search`
**What changed:** Assumes agents cannot self-query spine. MCP bridge gives all profiles cis_search_knowledge + 8 spine query tools.
**Remaining gap:** Threat model needs update for MCP query surface
**Affected sections:** §Trust Root, §The Core Realization

## STILL LIVE — Unsolved problems (12 docs)

### Governance

- **DEV-PIVOT-01**: Governance Reset Proposal
  - Depends on: `governance_in_application`
  - Gap: Governance still in bash scripts, not embedded in app
- **DEV-PIVOT-10**: ADR-SEED-014 Contract
  - Depends on: `router_tier_7r`
  - Gap: Temporary draft initiation still needed before Router

### Enforcement

- **DEV-PIVOT-03**: Hermes Hardening Spec
  - Depends on: `enforcement_primitive`
  - Gap: Guardrails are hooks, not kernel-level enforcement
- **DEV-PIVOT-04**: Application Enforcement Spec
  - Depends on: `enforcement_primitive`
  - Gap: Spec exists, no implementation

### Architecture & Direction

- **DEV-PIVOT-05**: Integration Assessment (16 Failure Modes)
  - Depends on: `failure_mode_audit`
  - Gap: 16 modes cataloged, re-audit needed against current capability
- **DEV-PIVOT-06**: Build Direction
  - Depends on: `standalone_app`
  - Gap: Direction approved, front door not built
- **DEV-PIVOT-07**: Next Major Project
  - Depends on: `front_door`
  - Gap: Post-hardening priorities unresolved

### Data & Cataloging

- **DEV-PIVOT-11**: Corpus Scraping Proposal
  - Depends on: `intent_extraction`
  - Gap: Archive drives not fully scraped for intent extraction
- **DEV-PIVOT-12**: Two-Pass Catalog Design
  - Depends on: `catalog_implementation`
  - Gap: Designed, not built
- **DEV-PIVOT-13**: Catalog Implementation Spec
  - Depends on: `catalog_implementation`
  - Gap: Spec exists, implementation not done

### Operations

- **DEV-PIVOT-14**: Closeout Instruction
  - Gap: Operational procedure — still valid
- **DEV-PIVOT-16**: Verifier Registry Spec
  - Depends on: `verifier_registry`
  - Gap: 7 verifiers spec'd — implementation status unverified

---

**Summary:** 2 invalidated, 3 partially invalidated, 12 live — 17 total
