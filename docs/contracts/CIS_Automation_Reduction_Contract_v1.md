# CIS Automation Reduction Contract v1
# Status: LOCKED
# Created: 2026-04-30
# L3 Audit: PASS WITH CORRECTIONS — corrections applied 2026-04-30
# Purpose: Require that every CIS build action eliminates at least one manual
#          operator action connected to the item being built.
# Parent contracts: CIS_Execution_Layer_Contract_v1.md (ADR-043)
#                   CIS_Verification_Layer_Contract_v1.md (ADR-033)
# Canonical path: /mnt/projects/cis/docs/contracts/
#                 CIS_Automation_Reduction_Contract_v1.md

---

## 1. Purpose

The CIS build process has accumulated manual operator actions at every layer:
terminal commands to run scripts, file drags to start sessions, manual status
checks, copy/paste rituals, and repeated verification setup. These actions are
not architectural features. They are gaps — places where automation was deferred
and the human became the bridge.

This contract defines a standing build rule: every time a CIS component is
touched, at least one manual operator action connected to that component must
be identified and eliminated. Automation reduction is not optional and not
deferred. It is a first-class deliverable alongside the feature itself.

Human procedural burden is a first-class architectural problem.
This contract operationalizes that principle.

---

## 2. Scope

This contract applies to every significant build action performed during a CIS
session. A build action is considered significant if it:

- modifies runtime behavior
- creates or modifies scripts
- creates or modifies routes or API endpoints
- changes schemas or migrations
- changes startup or service lifecycle behavior
- changes verification flow
- changes dashboard or operator behavior
- writes canonical project files
- changes queue or worker behavior
- creates or modifies governance contracts

If uncertainty exists about whether an action is significant, treat it as significant.

Excluded: exploratory conversation, planning discussion, and ADR drafting
prior to locking. The contract triggers when something is declared built.

---

## 3. Core Rule

**Every build item must include at least one automation reduction.**

The builder must not declare a build action complete without identifying,
eliminating, and replacing at least one manual operator action connected to
the item being built.

If no automation reduction is possible, the builder must explicitly state:

> "NO AUTOMATION REDUCTION FOUND — justification required."

Omitting this statement when no reduction is included is a contract violation.
Justification must explain specifically why no reduction is achievable at this
build step and what precondition would enable it.

Repeated use of "NO AUTOMATION REDUCTION FOUND" across adjacent build steps
for the same subsystem requires architectural review and must be logged as
technical debt in the canonical operational state documentation. The clause
is not an escape hatch for sustained deferral.

---

## 4. Required Response Structure

Every build response for a significant action must include the following
five fields, in this order, after the implementation:

```
AUTOMATION REDUCTION RECORD
Feature built:         [one-line description]
Manual action removed: [exact description of what the operator no longer does]
Replacement:           [command / route / script / dashboard action that replaces it]
Verification command:  [how to confirm the replacement works]
Remaining human action: [what the human still must do, if anything — or "None"]
```

This record is produced immediately after the Completion Manifest required
by CIS_Verification_Layer_Contract_v1.md. It is not prose. It is structured
and scannable.

A build action missing the AUTOMATION REDUCTION RECORD is verification-incomplete
and may not pass final verification. Omission of this record blocks advancement
on the same basis as a missing Completion Manifest.

---

## 5. Automation Priority Order

When multiple manual actions could be reduced, prioritize in this order:

1. Replace copy/paste with generated files or API output
2. Replace terminal typing with scripts or operator routes
3. Replace repeated status checks with status endpoints or dashboard polling
4. Replace manual handoff assembly with generated handoff files
5. Replace manual verification setup with one-command verification
6. Replace manual session rituals with dashboard actions
7. Replace scattered log writes with canonical single-destination writes

Lower-priority reductions are valid. Priority order governs when a choice
must be made between competing reductions.

---

## 6. Constraints

### 6.1 Governance is not bypassed

Automation reduction may not:
- Remove a human approval gate required by ADR-043 or ADR-044
- Bypass verification steps required by ADR-033 or ADR-034
- Execute directly without queue ownership once ADR-045 is implemented
- Promote artifacts without human validation

Automation replaces friction. It does not replace governance.

### 6.2 UI expansion is not the default

New dashboard UI may not be added to achieve automation reduction unless
required by a locked contract or explicitly approved. Prefer:
- Scripts
- Generated files
- API routes
- Status endpoints
- Canonical log writes
- Reuse of existing dashboard surface

### 6.3 Transitional gaps must be named

If a manual action cannot be eliminated at the current build step but is
known to have a future resolution, the builder must name it explicitly as
a transitional gap with a target ADR or build step. Unnamed transitional
gaps are invisible debt and are prohibited.

### 6.4 Automation reductions must be logged canonically

Automation reductions that affect runtime operation, verification flow, or
operator burden must be reflected in canonical handoff and/or operational
state documentation before session close. A reduction that exists only
conversationally is not a reduction — it is invisible and will not survive
institutional memory.

### 6.5 Cognitive load is the target, not keystrokes

Automation reduction must prefer reducing cognitive load, not merely reducing
keystrokes. Builders may not optimize trivial actions while leaving
high-burden orchestration intact. The measure of a valid reduction is whether
the operator is removed from a decision or monitoring loop, not merely whether
a command is shorter.

---

## 7. Application to ADR-045 Implementation

This contract applies to ADR-045 immediately upon locking.

Each ADR-045 build step must satisfy the automation reduction requirement:

| Step | Feature | Minimum Automation Reduction |
|---|---|---|
| Step 1 | execution_jobs table | Migration script eliminates manual sqlite3 commands |
| Step 2 | api/queue.py | Test script eliminates manual route testing |
| Step 3 | Background worker | Flask-started worker eliminates manual worker terminal |
| Step 4 | verify_contract job type | Operator button eliminates manual script invocation |
| Step 5 | Dashboard polling | Auto-refresh eliminates manual job status checking |
| Step 6 | run_l2 job type | Queued L2 eliminates manual vLLM terminal invocation |
| Step 7 | Cold start recovery | Recovery logic eliminates manual job triage after restart |

The Flask-started worker is the required implementation for Step 3.
A separate manual worker terminal is not acceptable unless verification
demonstrates Flask-started worker is unsafe, and that finding is logged
as an ADR.

---

## 8. Failure Handling

| Failure type | Response |
|---|---|
| No automation reduction included and no "NO AUTOMATION REDUCTION FOUND" statement | Contract violation — block treated as incomplete |
| "NO AUTOMATION REDUCTION FOUND" without justification | Block treated as incomplete — justification required before advancing |
| Automation reduction bypasses a governance gate | Reduction is invalid — redesign required |
| New UI added without contract authority | Reduction is invalid — non-UI replacement required |

---

## 9. Relationship to Existing Contracts

This contract operates alongside, not above, existing governance:

- CIS_Verification_Layer_Contract_v1.md governs proof of work.
  This contract governs burden reduction. Both apply simultaneously.
- CIS_Execution_Layer_Contract_v1.md governs what execution is legal.
  This contract governs how that execution reaches the operator.
- ADR-044 governs operator abstraction.
  This contract requires that abstraction actively reduces burden, not
  merely wraps existing manual actions in a button.
- ADR-045 governs queue ownership.
  This contract requires queue-backed execution to eliminate manual
  script invocations, not preserve them behind a new route.

---

## 10. Contract Authority

This contract is LOCKED.
Changes require a new ADR.
This file lives at:
/mnt/projects/cis/docs/contracts/CIS_Automation_Reduction_Contract_v1.md
