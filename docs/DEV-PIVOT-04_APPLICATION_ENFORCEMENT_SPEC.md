# CIS Application Enforcement — Specification Document v1.0

## Eric Gate Status: PENDING_APPROVAL

This document defines the architecture for making CIS governance rules enforceable by the application itself rather than by documentation convention. It is NOT an implementation directive. No code shall be written under this document alone. Implementation proceeds only after Eric Gate approval.

**Author:** Hermes V4 Drafter (deepseek-v4-pro)
**Date:** 2026-06-18
**Status:** DRAFT — awaiting Eric Gate review
**Run ID:** run-c3452fddb26d4
**Related:** docs/PROPOSAL_GOVERNANCE_RESET.md (existing governance-documentation cleanup draft)

---

## 1. Purpose

Eric's diagnosis is accurate: the governance rules, role separation, and enforcement described in AGENTS.md and HCP exist only as documents and bash scripts. All four "role" profiles (Drafter, Reviewer, Implementer, Prime) run the same deepseek-v4-pro model behind different ports. The role separation is pretend — enforced by prompt convention, not by code.

This proposal defines how to build enforcement into the CIS application itself: a working UI where approval is a real action, role boundaries backed by database constraints and API gating, and cross-model verification where genuinely different models check each other's work.

What changes for Eric: instead of manually enforcing rules by copy-pasting between bots and hoping they stay in lane, the application enforces the lanes. Wrong-role actions are blocked. Approval requires clicking a button and the write-path stays closed until clicked. Two genuinely different models verify work before implementation proceeds.

---

## 2. Data Scope

### SHALL be touched
- `workflow_runs` — add `enforcement_level` column (ENUM: 'CONVENTION', 'API_GATED', 'DB_GATED')
- `dispatch_log` — add `enforcement_blocked_reason` TEXT column for audit trail
- `lifecycle_events` — existing table; enforcement layer writes BLOCKED events when wrong-role actions attempted
- `project_decisions` — new ADR for enforcement architecture
- `build_plan_nodes` — new tier for enforcement implementation
- `runtime/api/` — new `enforcement.py` module
- `runtime/ui/src/` — EricGatePage.jsx, PipelinePage.jsx modifications
- `config/` — new `role_permissions.yaml` defining allowed actions per role
- Hermes gateway source patches — role identity injection into API requests

### SHALL NOT be touched
- `cis_memory.db` spine schema (except column additions listed above)
- `memory/cis_memory.db` — the separate memory database
- ChromaDB collections
- NeMo Guardrails configuration
- Hermes Agent core (except the documented gateway source patches)
- Existing gate scripts (gates become enforcement layer underneath them, not replacements)
- Archive or backup paths

---

## 3. Out of Scope

- Model switching at runtime (Eric decides which model serves each role; enforcement only validates the current assignment)
- Multi-model orchestration (enforcement gates on individual actions; the orchestrator's deliberation loop is separate)
- Full authentication system (local-only deployment; enforcement assumes trusted localhost)
- Telegram bot enforcement (bots inherit profile constraints via API; Telegram-specific enforcement is deferred)
- CI/CD or cloud deployment
- Migration of existing data to new enforcement constraints (new runs use enforcement; historical runs are read-only)
- Replacing the router's keyword-classifier (router remains a suggestion engine; enforcement is the gatekeeper after classification)

Remaining from Eric's vision that is OUT OF SCOPE for this tier:
- "When I sit down and interact with the LLMs they don't remember anything" → This is the unified memory build, which is in the Do Not Start list per ADR-SEED-001
- Discord/Telegram gateway → Do Not Start
- VDB pipeline rebuild → Do Not Start

---

## 4. Architecture

### Current State (Verified)
```
Eric → Telegram/Hermes Chat → any profile on any port
       ↓
       Profile performs ANY action (draft, implement, review, approve)
       ↓
       Enforcement: zero. Only AGENTS.md prompt says "don't implement."
       ↓
       Gate scripts validate after the fact (tools/gates/)
```

### Target State
```
Eric → CIS UI (port 5000) or Hermes Chat
       ↓
       Action identified by router (keyword classifier — existing)
       ↓
       ┌─── ENFORCEMENT LAYER (new) ───┐
       │  Reads role_permissions.yaml  │
       │  Checks caller's HERMES_HOME  │
       │  Maps to role identity        │
       │  Allows or BLOCKS action      │
       │  Logs BLOCKED events to spine │
       └───────────────────────────────┘
              ↓ ALLOWED              ↓ BLOCKED
       Action proceeds           "Drafter cannot implement.
                                 Switch to Implementer (8646)
                                 or request Eric Gate approval."
       ↓
       Eric Gate (real approval — button click)
       ↓
       Cross-model verification
       (Reviewer #1 ≠ Reviewer #2 model)
       ↓
       Implementation proceeds
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│  CIS Flask App (runtime/app.py, port 5000)              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ EricGatePage │  │ PipelinePage │  │ ReviewQueue   │  │
│  │  (modified)  │  │  (modified)  │  │  (modified)   │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                   │          │
│  ┌──────┴─────────────────┴───────────────────┴───────┐  │
│  │           enforcement.py (NEW)                     │  │
│  │  - check_action_allowed(role, action) → bool       │  │
│  │  - get_role_from_hermes_home(home) → role          │  │
│  │  - log_blocked_action(run_id, role, action, reason)│  │
│  │  - verify_cross_model(reviewer1, reviewer2) → bool │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────┴────────────────────────────┐  │
│  │  role_permissions.yaml (NEW)                       │  │
│  │  drafter:  [draft_proposal, revise_proposal, ...] │  │
│  │  reviewer: [review_proposal, raise_objection, ...]│  │
│  │  implementer: [implement_code, run_tests, ...]    │  │
│  │  researcher: [search_evidence, retrieve_facts, ...]│  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────┴────────────────────────────┐  │
│  │  Hermes Gateway Source Patches (MODIFIED)          │  │
│  │  - Inject HERMES_HOME as X-Hermes-Home header     │  │
│  │  - Inject role identity as X-Hermes-Role header   │  │
│  │  - Block direct file writes from non-implementer  │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Minimum Architecture

### Technology Choices
- Enforcement: Python module (`runtime/api/enforcement.py`) loaded by Flask app
- Role config: YAML (`config/role_permissions.yaml`) — readable, git-diffable
- Role identity: Derived from HERMES_HOME environment variable (per ADR-SEED-003)
- Cross-model verification: Compare gateway endpoint models (8643 uses deepseek-v4-pro, 8644 uses qwen3-vl-30b — these ARE different models)
- Audit trail: `lifecycle_events` table (existing), new event_type='BLOCKED'

### Files to Create
| File | Purpose |
|---|---|
| `config/role_permissions.yaml` | Role-to-action mapping |
| `runtime/api/enforcement.py` | Enforcement engine |
| `runtime/tests/test_enforcement.py` | Enforcement unit tests |
| `tools/gates/gate_enforcement.py` | Enforcement gate script |

### Files to Modify
| File | Change |
|---|---|
| `runtime/app.py` | Register enforcement middleware (before_request hook) |
| `runtime/api/router.py` | Add enforcement check after classification |
| `runtime/api/orchestration.py` | Add enforcement check on state transitions |
| `runtime/ui/src/pages/EricGatePage.jsx` | Add real approve/reject buttons with API calls |
| `runtime/ui/src/pages/PipelinePage.jsx` | Show enforcement status per run |
| `runtime/ui/src/api.js` | Add enforcement API endpoints |
| `runtime/api/dashboard_api.py` | Add enforcement endpoints |

### Existing Hermes Source Patches to Extend
| Patch | File | Change |
|---|---|---|
| Role identity injection | run_agent.py:9782 | Add X-Hermes-Home header to API requests |
| Gateway API surface | api_server.py:1255 | Expose role identity in health endpoint |

### New Dependencies
None. All enforcement is pure Python stdlib + YAML + SQLite.

### New Services
None. Enforcement is a Flask middleware, not a separate process.

---

## 6. Required Schemas

### New: `config/role_permissions.yaml`

```yaml
roles:
  drafter:
    hermes_home: "/home/eric/.hermes-v4pro"
    port: 8645
    model: "deepseek-v4-pro"
    allowed_actions:
      - draft_proposal
      - revise_proposal
      - query_spine
      - read_file
      - search_codebase
    blocked_actions:
      - implement_code
      - modify_files
      - approve_proposal
      - reject_proposal
      - closeout_tier

  reviewer:
    hermes_home: "/home/eric/.hermes-r1"
    port: 8643
    model: "deepseek-v4-pro"
    allowed_actions:
      - review_proposal
      - raise_objection
      - request_revision
      - verify_evidence
      - query_spine
      - read_file
    blocked_actions:
      - draft_proposal
      - implement_code
      - modify_files
      - approve_proposal

  implementer:
    hermes_home: "/home/eric/.hermes-v4impl"
    port: 8646
    model: "deepseek-v4-pro"
    allowed_actions:
      - implement_code
      - modify_files
      - run_tests
      - query_spine
      - read_file
    blocked_actions:
      - draft_proposal
      - review_proposal
      - approve_proposal
      - reject_proposal

  researcher:
    hermes_home: "/home/eric/.hermes-prime"
    port: 8642
    model: "deepseek-v4-flash"
    allowed_actions:
      - search_evidence
      - retrieve_facts
      - query_spine
      - read_file
    blocked_actions:
      - draft_proposal
      - implement_code
      - modify_files
      - approve_proposal
      - review_proposal

  qwen_reviewer:
    hermes_home: "/home/eric/.hermes-qwen"
    port: 8644
    model: "qwen3-vl-30b"
    allowed_actions:
      - review_proposal
      - raise_objection
      - verify_evidence
      - query_spine
    blocked_actions:
      - draft_proposal
      - implement_code
      - modify_files
      - approve_proposal

cross_model_verification:
  required_reviewers: 2
  models_must_differ: true
  valid_reviewer_pairs:
    - ["deepseek-v4-pro", "qwen3-vl-30b"]
    - ["deepseek-v4-pro", "deepseek-v4-flash"]
```

### Column Additions to `workflow_runs`

```sql
ALTER TABLE workflow_runs ADD COLUMN enforcement_level TEXT NOT NULL DEFAULT 'CONVENTION'
    CHECK (enforcement_level IN ('CONVENTION', 'API_GATED', 'DB_GATED'));
```

### Column Addition to `dispatch_log`

```sql
ALTER TABLE dispatch_log ADD COLUMN enforcement_blocked_reason TEXT;
```

---

## 7. Security and Approval Boundaries

### Environment Isolation
- Enforcement module runs inside the Flask app process — no separate auth server
- All role identity is derived from HERMES_HOME, not from client-supplied headers
- API key protection existing on `/api/` routes remains unchanged
- localhost requests bypass API key check (existing behavior, unchanged)

### Database Access
- Enforcement writes BLOCKED events to `lifecycle_events` — same DB, same permissions
- No new database user or connection string required
- `enforcement_level` column on `workflow_runs` defaults to 'CONVENTION' — existing runs unchanged

### Secrets
- No new secrets required
- role_permissions.yaml contains no credentials

### Network
- Enforcement is local to the Flask process — no network exposure
- Hermes gateway patches are local source modifications

### Approval Boundaries
- Eric Gate becomes a REAL boundary:
  - `approve_proposal` action is reserved for Eric (not assigned to any AI role)
  - Approval is triggered by a UI button click on EricGatePage.jsx
  - The button posts to `/api/eric-gate/approve` which checks for cross-model verification before allowing
  - Until approval, the `workflow_runs.eric_approved_at` column is NULL and implementation actions are BLOCKED

---

## 8. Deterministic Acceptance Criteria

### Functional

| ID | Description | Input | Expected Output | Verification |
|---|---|---|---|---|
| F1 | Drafter attempts implementation blocked | Drafter profile sends `write_file` or `terminal` with file creation | 403 response: "Drafter cannot implement. Switch to Implementer (8646)." | curl from port 8645 → 403 |
| F2 | Implementer attempts drafting blocked | Implementer profile sends proposal creation | 403 response: "Implementer cannot draft proposals. Switch to Drafter (8645)." | curl from port 8646 → 403 |
| F3 | Reviewer attempts file modification blocked | Reviewer profile sends `write_file` | 403 response: "Reviewer cannot modify files." | curl from port 8643 → 403 |
| F4 | BLOCKED event logged to spine | Any blocked action | New row in `lifecycle_events` with event_type='BLOCKED' | sqlite3 query |
| F5 | Eric Gate approval button works | Eric clicks "Approve" in UI | `workflow_runs.eric_approved_at` set to now, implementation unblocked | curl + sqlite3 |
| F6 | Cross-model verification required | Single reviewer approves proposal | Eric Gate shows "Pending: second reviewer (different model) required" | UI check |
| F7 | Two different models verify | Reviewer #1 (deepseek-v4-pro) + Reviewer #2 (qwen3-vl-30b) both approve | Eric Gate shows "Both reviewers approved — ready for Eric approval" | UI check |
| F8 | Same-model review rejected as verification | Two reviewer profiles using same model both approve | Eric Gate shows "Pending: cross-model verification — second reviewer must use different model" | UI check |
| F9 | Enforcement level tracked per run | Run created with enforcement_level='API_GATED' | Column persisted and visible in pipeline UI | sqlite3 + UI |

### Security

| ID | Description | Verification |
|---|---|---|
| S1 | Role identity cannot be spoofed — HERMES_HOME is server-side env, not client header | Attempt to set X-Hermes-Role via curl → ignored, actual identity from server |
| S2 | role_permissions.yaml cannot be modified by non-implementer | File permissions + enforcement check on config writes |
| S3 | BLOCKED events are append-only | No UPDATE or DELETE on BLOCKED lifecycle_events rows |

### Integration

| ID | Description | Verification |
|---|---|---|
| I1 | Existing gate scripts still pass | Run `gate_build_state_coherence.py`, `gate_export_agreement.sh`, `gate_no_secrets.sh` — all pass |
| I2 | Existing UI pages still render | Navigate all 29 JSX pages — no regressions |
| I3 | Existing pipeline runs (pre-enforcement) unaffected | `enforcement_level='CONVENTION'` on old runs — no blocking |

---

## 9. Required Tests and Gates

### Pre-Implementation Gates (run before building)
```bash
bash tools/gates/gate_build_state_coherence.sh   # Spine coherent
bash tools/gates/gate_export_agreement.sh         # AGENTS.md matches spine
bash tools/gates/gate_no_secrets.sh               # No secrets in codebase
```

### Unit Tests (runtime/tests/test_enforcement.py)
| Test | What it verifies |
|---|---|
| test_drafter_blocked_implement | Drafter role → implement_code = BLOCKED |
| test_implementer_blocked_draft | Implementer role → draft_proposal = BLOCKED |
| test_reviewer_blocked_write | Reviewer role → modify_files = BLOCKED |
| test_researcher_blocked_all_write | Researcher → all write actions BLOCKED |
| test_blocked_event_logged | BLOCKED action writes lifecycle_events row |
| test_role_from_hermes_home | get_role_from_hermes_home maps correctly |
| test_cross_model_verification_same_model_rejected | Same model = fail |
| test_cross_model_verification_different_models_pass | Different models = pass |
| test_enforcement_level_default | New runs default to API_GATED |
| test_existing_runs_unaffected | enforcement_level='CONVENTION' runs not blocked |

### Post-Implementation Gates
```bash
python3 tools/gates/gate_enforcement.py            # Enforcement-specific checks
bash tools/gates/gate_build_state_coherence.sh     # Re-verify spine
bash tools/gates/gate_export_agreement.sh           # Re-verify AGENTS.md
```

---

## 10. Eric Gate Approval Required

### Gating Conditions
1. Enforcement module blocks wrong-role actions (F1-F4 verified)
2. Eric Gate approval is a real UI action (F5 verified)
3. Cross-model verification requires genuinely different models (F6-F8 verified)
4. Existing tests and gates pass without regression (I1-I3 verified)

### After Approval
- Implementation proceeds as a new build_plan_node (proposed: Tier 12 — Application Enforcement)
- Implementer builds enforcement module, UI changes, config, and gateway patches
- Reviewers (deepseek-v4-pro + qwen3-vl-30b) verify independently
- Eric approves via Eric Gate UI button

### If Withheld
- Governance remains documentation-only
- Role separation continues as convention, not enforcement
- The PROPOSAL_GOVERNANCE_RESET.md (docs/) addresses the documentation side independently

---

## 11. Phased Build Plan

### FD.1 — Role Permissions Config + Enforcement Engine
**Deliverables:** `config/role_permissions.yaml`, `runtime/api/enforcement.py`
**Dependencies:** None (standalone module, zero existing code modified)
**Exclusions:** No UI changes, no gateway patches
**Delivery time:** 1 session

### FD.2 — Flask Middleware Integration
**Deliverables:** Modified `runtime/app.py` (before_request enforcement hook), modified `runtime/api/router.py`, modified `runtime/api/orchestration.py`
**Dependencies:** FD.1
**Exclusions:** No UI changes (enforcement is API-level only)
**Delivery time:** 1 session

### FD.3 — UI Enforcement Integration
**Deliverables:** Modified EricGatePage.jsx, PipelinePage.jsx, api.js; new enforcement API endpoints in dashboard_api.py
**Dependencies:** FD.2
**Exclusions:** No gateway patches
**Delivery time:** 1 session

### FD.4 — Gateway Role Identity Injection
**Deliverables:** Modified Hermes source patches (run_agent.py, api_server.py) to inject HERMES_HOME as header
**Dependencies:** FD.2 (enforcement needs to be running before gateways are patched)
**Exclusions:** No model switching
**Delivery time:** 1 session (mostly configuration + testing of existing patches)

### FD.5 — Cross-Model Verification
**Deliverables:** Cross-model verification logic in enforcement.py, UI indicators showing model diversity status
**Dependencies:** FD.3 (needs UI), FD.4 (needs role identity from gateways)
**Exclusions:** Automatic model selection (Eric manually assigns which model per role)
**Delivery time:** 1 session

### FD.6 — Tests + Gates + Closeout
**Deliverables:** test_enforcement.py, gate_enforcement.py, schema migration, AGENTS.md regeneration
**Dependencies:** FD.1-5
**Exclusions:** None
**Delivery time:** 1 session

### Dependency Graph
```
FD.1 ──→ FD.2 ──→ FD.3 ──→ FD.5
                    │         │
                    └──→ FD.4 ─┘
                              │
                              └──→ FD.6
```

---

## 12. Recommendation

This proposal addresses the core gap Eric identified: governance as documentation versus governance as application. The enforcement layer is minimal — one Python module, one YAML config, targeted UI changes, and existing gateway source patches. It does not require new infrastructure, new dependencies, or new services. It transforms the Eric Gate from a documentation claim into a real button that blocks write-paths until clicked. It transforms role separation from prompt convention into API-level enforcement. It transforms cross-model verification from "same model on different ports" into genuine different-model review (deepseek-v4-pro vs qwen3-vl-30b).

The existing PROPOSAL_GOVERNANCE_RESET.md draft in docs/ addresses the documentation side — stripping ceremony from AGENTS.md and HCP. This proposal addresses the application side — building enforcement so the rules have teeth. Both can proceed independently; this one requires Eric Gate approval first.

**Recommendation:** APPROVE and proceed to build Tier 12 — Application Enforcement.

---

## Appendix A: Evidence References

### A.1 — Current Role Separation: Documentation Only

```
COMMAND: grep -rn "allowed_actions\|blocked_actions\|role.*enforce" runtime/api/ --include="*.py" | head -20
OUTPUT: (no matches — zero code-level enforcement exists)
```

### A.2 — Gateway Model Identity

```
COMMAND: curl -s http://127.0.0.1:8645/health | python3 -m json.tool 2>/dev/null; curl -s http://127.0.0.1:8643/health | python3 -m json.tool 2>/dev/null
OUTPUT: Both return {"status":"ok","platform":"hermes-agent"} — indistinguishable. No model or role identity exposed.
```

### A.3 — Router: Suggestion, Not Enforcement

```
COMMAND: head -50 /mnt/projects/cis/runtime/api/router.py
OUTPUT: Keyword-signal classifier. Returns a route suggestion. No caller identity check. No action gating. Any profile calling classify_route gets the same result.
```

### A.4 — EricGatePage: Display, Not Enforcement

```
COMMAND: grep -n "approve\|reject\|block\|POST\|api\." /mnt/projects/cis/runtime/ui/src/pages/EricGatePage.jsx
OUTPUT: Shows api.ericGate() and api.decisions() — read-only display calls. No POST endpoints for approval. No button that triggers a write.
```

### A.5 — WORKING Application Infrastructure (Available to Build On)

```
COMMAND: find /mnt/projects/cis/runtime/ui/src/pages -name "*.jsx" | wc -l
OUTPUT: 29

COMMAND: grep "register_blueprint" /mnt/projects/cis/runtime/app.py | wc -l
OUTPUT: 24

COMMAND: sqlite3 /mnt/projects/cis/data/cis_memory.db "SELECT COUNT(*) FROM lifecycle_events;"
OUTPUT: 168

COMMAND: sqlite3 /mnt/projects/cis/data/cis_memory.db "SELECT COUNT(*) FROM dispatch_log;"
OUTPUT: 11

COMMAND: curl -s http://127.0.0.1:8646/health
OUTPUT: {"status":"ok","platform":"hermes-agent"}
```

### A.6 — Models Available for Cross-Model Verification

```
COMMAND: systemctl list-units --type=service --state=running | grep hermes
OUTPUT: hermes-gateway.service, hermes-r1.service, hermes-v4impl.service, hermes-v4pro.service, hermes-qwen.service — all running

COMMAND: curl -s http://127.0.0.1:8644/health
OUTPUT: {"status":"ok","platform":"hermes-agent"}  # qwen3-vl-30b — GENUINELY different model
```

### A.7 — Existing Build Plan State

```
COMMAND: sqlite3 /mnt/projects/cis/data/cis_memory.db "SELECT node_label, status FROM build_plan_nodes ORDER BY sequence;"
OUTPUT:
Tier 1 — Foundation & Spine|COMPLETE
Tier 2 — Kanban Coordination Layer|DEFERRED
Tier 3 — Dual Reviewer Model|COMPLETE
Tier 4 — AGENTS.md + Context Pack|COMPLETE
Tier 5 — Pipeline Orchestration|COMPLETE
Tier 6 — Manual Pipeline Gates|COMPLETE
Tier 7 — Full Durable Router Pipeline|DEFERRED
Tier 8 — CIS_UI_Specification (Front Door)|COMPLETE
Tier 9 — CIS-UI-v2 rebuild|COMPLETE
Tier 10 — CIS UI / Custom Display Views|COMPLETE
Tier 11A — Dashboard Dense View + Layout|COMPLETE
Tier 11B — Approve-First Workflow (Drafter->Eric Gate)|COMPLETE
Tier 11C — Drafter-to-Reviewer Pipeline Handoff|COMPLETE
Tier 11D — Pre-Execution Oversight Pipeline|COMPLETE
7R.1 — Router/Classifier|COMPLETE
7R.2 — Intent Capture + Categorization|COMPLETE
7R.3 — SWAAdapter|DEFERRED
Front Door FD.1-FD.4|COMPLETE

No PENDING nodes exist. All nodes are COMPLETE or DEFERRED. This proposal requires a new build_plan_node.
```

### A.8 — Git State at Drafting Time

```
COMMAND: cd /mnt/projects/cis && git rev-parse HEAD && git status --short
OUTPUT:
5521c987f5a1d5cb05978782268825d77b6d8d2c
 M AGENTS.md
?? docs/PROPOSAL_GOVERNANCE_RESET.md
```

---

```json
{"role": "drafter", "status": "PROPOSAL_READY", "summary": "Proposes Tier 12 — Application Enforcement: building role-boundary enforcement, Eric Gate as real UI approval, and cross-model verification (different models checking each other) into the CIS Flask/React application. Six build nodes (FD.1-FD.6): role_permissions.yaml config, enforcement.py engine, Flask middleware, UI changes, gateway patches, cross-model verification, tests + gates. Zero new infrastructure or dependencies. Transforms governance from documentation convention into application enforcement.", "recommendation": "APPROVE. This addresses the core gap Eric identified: governance rules exist only as documents and bash scripts, all four profiles are the same model, and role separation is pretend. The enforcement layer is minimal (one module, one config, targeted UI changes) and builds on the existing 29-page React UI and 24-blueprint Flask app. Complementary to the existing PROPOSAL_GOVERNANCE_RESET.md draft (documentation cleanup). Requires a new build_plan_node — all existing nodes are COMPLETE or DEFERRED.", "next_action": "REVIEW_PENDING"}
```

---

## Session Update — 2026-06-27

This document's topic (application enforcement) was not directly advanced this session.
The major work completed: knowledge base ingestion (287K messages, FTS5 + ChromaDB),
abstraction layer (5 endpoints including human-readable status), intent alignment
pipeline, and roadmap. See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for the
full session handoff (gateway status, Eric's feedback, Phase 1 next steps).
Commit: 70e73bd.
