# CIS Primer Update Governance Contract v1.1
# Status: LOCKED — Amended
# Created: 2026-05-01
# Amended: 2026-05-01 — Single-surface workflow (primer_update_v3.py)
# Reviewed by: ChatGPT (constitutional review, 2026-05-01 — three passes)
# Amendment rationale: _update_staging/ model replaced with in-place
#   *_update_draft.md workflow. Operational simplification only.
#   All constitutional protections unchanged.
# Purpose: Define the lawful process by which CIS constitutional
#          institutional memory may be updated, reviewed, approved,
#          applied, and logged.
# Parent contracts: CIS_Verification_Layer_Contract_v1.md (ADR-033)
#                   CIS_Execution_Layer_Contract_v1.md (ADR-043)
# Canonical path: /mnt/projects/cis/docs/contracts/
#                 CIS_Primer_Update_Governance_Contract_v1.md

---

## 1. Why This Contract Exists

The CIS Project Primer began as operational documentation.

It is no longer documentation.

The primer files are now authoritative institutional memory — the
compressed constitutional state of the project inherited by every
AI model, every session, and eventually every autonomous agent
operating within CIS.

This changes the nature of updates fundamentally.

Updating a primer file is not an editorial act.
It is a governed state transition in constitutional project memory.

The project is transitioning from:

    AI-assisted software development

toward:

    governed institutional cognition

In that transition, memory governance, role separation, constitutional
review, and lawful state progression are not process overhead.
They are core infrastructure.

**Institutional memory legitimacy derives from lawful governance process,
not model confidence, conversational repetition, or runtime convenience.**

This is the philosophical center of this contract.
All provisions derive from it.

This contract defines the law governing that infrastructure.

---

## 2. Core Constitutional Principle

No model may rewrite, reinterpret, or canonize its own interpretation
of project state without independent review.

This is the foundational rule from which all other provisions derive.

It applies without exception to:
- Claude
- ChatGPT
- Gemini
- local models
- any future autonomous agent

The generator of candidate updates is never the approver of those updates.

---

## 3. Relationship to Existing Contracts

This contract extends:

- CIS_Verification_Layer_Contract_v1.md (ADR-033)
  Role separation between Builder, Verifier, and Auditor is extended
  here to cover institutional memory updates.

- CIS_Execution_Layer_Contract_v1.md (ADR-043)
  The human gate principle — human approves, does not continuously
  arbitrate — applies directly to primer update approval.

- CIS_Automation_Reduction_Contract_v1.md (ADR-046)
  Automation reduction applies: the human gate is for approval only,
  not for manual merging, routing, or review arbitration.

In any conflict between this contract and conversational reasoning,
this contract governs.

In any conflict between this contract and a locked ADR or
higher-authority contract, the higher-authority document governs
and the conflict must be logged to CIS_CONFLICT_REGISTER.md before
the update cycle proceeds.

---

## 4. Definitions

**Primer files**
The canonical AI-facing orientation documents located at:
/mnt/projects/cis/docs/claude_chat_transcripts/ChatGTP_Project_Primer/
These files are authoritative institutional memory. They are not
convenience summaries or working notes.

The primer folder is simultaneously:
- the authoritative constitutional memory surface
- the review surface
- the inheritance package surface for all AI model sessions

**Constitutional memory state**
The current authoritative representation of project architecture,
governance decisions, build sequence, risks, and operational reality
as encoded in the primer files. A state transition occurs when any
canonical primer file is updated.

**Candidate update**
A proposed new version of a primer file. Candidate updates exist as
*_update_draft.md files placed beside their canonical counterparts
in the primer folder. A candidate update is not canonical until it
has passed through the full update pipeline defined in Section 8.

**Draft file**
A file named <canonical_name>_update_draft.md placed beside its
canonical counterpart in the primer folder.
Example:
  01_CURRENT_STATE.md               — canonical (authoritative)
  01_CURRENT_STATE_update_draft.md  — candidate (not authoritative)

Draft files carry no constitutional authority. They are candidates only.
The canonical file governs until a successful governed apply replaces it.

**Preview diff**
The output of primer_update_v3.py --preview. The authoritative surface
for constitutional review. Must exist before any apply action.

**Update Scope Declaration**
A required artifact declaring the intended architectural scope, affected
primer domains, and expected governance impact of a given update cycle.

**Primer Update Review Record**
The required artifact documenting verifier findings, disagreements,
and approval decision for a given update cycle.

---

## 5. Authoritative Memory Rule

Only canonical primer files in the primer folder after successful
governed apply constitute authoritative institutional memory state.

Constitutional memory is intentionally conservative.
The burden of proof for canonization is higher than the burden of proof
for discussion, experimentation, or architectural speculation.

The following are NON-authoritative unless canonized through the
governed update pipeline defined in Section 8:

- conversation transcripts
- CIS Live session discussions
- draft files (*_update_draft.md)
- preview diffs
- model reasoning
- temporary manifests
- handoff files
- conversational conclusions of any kind

This rule applies regardless of how confidently a model states a
position in conversation, how many times a claim is repeated, or
how consistent the claim appears across sessions.

Conversational conclusions are not constitutional memory.
Repetition does not create canonization.
Model confidence does not create authority.

---

## 6. Runtime Discovery Rule

Runtime discoveries, architectural insights, conversational conclusions,
and implementation observations do not become constitutional memory
automatically.

All discoveries — regardless of source or significance — require:

1. candidate update generation by the Architect
2. independent Verifier review
3. Human Gate approval
4. lawful apply via primer_update_v3.py

before becoming authoritative institutional memory state.

This rule exists because:

The system will accumulate discussions, insights, and discoveries
faster than governed update cycles can process them.
Without this rule, models will gradually treat discussions as canon.
That drift is silent, cumulative, and eventually irreversible.

---

## 7. Role Definitions

### 7.1 Architect

**Purpose**
Generates candidate primer updates based on verified runtime events.

**Current actors:** Claude, ChatGPT

**Future actors:** Local planning and orchestration models
(after Section 13 conditions are met)

**Allowed actions**
- Propose primer updates
- Synthesize verified runtime state into draft files
- Place *_update_draft.md files in the primer folder for review
- Generate Update Scope Declaration

**Forbidden actions**
- Apply updates
- Self-approve candidate updates
- Bypass the review pipeline
- Act simultaneously as Verifier for the same update cycle

**Allowed sources for candidate updates**
- Runtime completion manifests
- Resolved CIS Live sessions
- Verified ADR closures
- Locked governance decisions

**Forbidden sources**
- Speculative planning
- Unresolved architectural debate
- Unverified implementation claims
- Conversational inference without runtime evidence

### 7.2 Verifier

**Purpose**
Performs independent constitutional review of candidate updates
before apply is permitted.

**Current actors**
ChatGPT (when Claude is Architect)
Claude (when ChatGPT is Architect)

**Future actors:** Local governance verifier models
(after Section 13 conditions are met)

**Responsibilities**
Review the preview diff against all seven constitutional check
categories defined in Section 9. Record findings in the Primer
Update Review Record.

**Forbidden actions**
- Generating the candidate updates being reviewed in the same cycle
- Bypassing disagreement logging
- Approving updates with unresolved constitutional concerns
- Reviewing updates that fall outside the declared Update Scope
  without flagging the scope violation

### 7.3 Human Gate

**Purpose**
Final constitutional approval authority.

**Responsibilities**
- Approve the update after verified review
- Reject and redirect if concerns are unresolved
- Resolve governance ambiguity that models cannot resolve

**Explicit non-responsibilities**
The human is NOT:
- A manual merger or file editor
- A continuous content reviewer
- A routing middleware between models
- A primary verifier

**Human Gate authority limits**

The Human Gate MAY:
- approve
- reject
- redirect
- defer

The Human Gate MAY NOT:
- bypass constitutional review requirements
- override locked governance contracts
- force unlawful canonization
- apply updates without Verifier review
- waive the independent review requirement for any reason

Governance authority is above operator convenience. Always.

### 7.4 Runtime Executor

**Purpose**
Applies already-approved updates mechanically.

**Current actor:** primer_update_v3.py

primer_update_v3.py is a mechanical executor only.
It carries no interpretive or constitutional authority.
Its constitutional keyword drift detection outputs are signals
to the Verifier — not decisions, not approvals.

**Responsibilities**
- Discover *_update_draft.md files beside canonical files
- Generate preview diffs
- Back up originals before apply
- Atomically replace canonical files with approved draft content
- Remove draft files after successful apply
- Detect and report constitutional keyword drift (signal only)
- Generate apply manifest

**Forbidden actions**
- Semantic interpretation of content
- Constitutional judgment
- Automatic approval
- Apply without prior human approval
- Partial apply

---

## 8. Required Update Pipeline

No deviation from this sequence is permitted unless:
- the deviation itself is lawful under this contract
AND
- the deviation is logged with explicit rationale

No deviation may bypass:
- independent Verifier review
- constitutional check categories
- apply atomicity
- Human Gate approval
- governance hierarchy constraints

```
Step 1  — Runtime event occurs and is verified
          (ADR closure, resolved Live session, completion manifest)

Step 2  — Session closes with required session close fields

Step 3  — Architect generates Update Scope Declaration
          Declares: intended scope, affected primer files,
          expected governance impact, runtime grounding events

Step 4  — Architect generates candidate primer updates
          grounded in verified runtime events only
          Places *_update_draft.md files beside canonical files
          in the primer folder

Step 5  — Preview diff generated
          python3 primer_update_v3.py --preview

Step 6  — Preview diff and Update Scope Declaration
          delivered to Verifier
          Verifier must be a different model than the Architect

Step 7  — Verifier review conducted
          All seven constitutional check categories reviewed
          Findings logged to Primer Update Review Record
          Scope compliance confirmed

Step 8  — Disagreement resolution
          If none: proceed to Step 9
          If any: Human Gate resolves, or redirects to Architect
          Silent override is not permitted under any circumstance

Step 9  — Human Gate approval

Step 10 — Apply (atomic)
          python3 primer_update_v3.py
          Apply Atomicity Rule enforced (see Section 10)
          Draft files removed after successful apply

Step 11 — Apply Manifest generated (immutable)

Step 12 — Primer Update Review Record archived
          Stored in /_backups/<timestamp>/
```

---

## 9. Constitutional Review Requirements

The Verifier must explicitly check and record findings for each
of the following categories. No category may be skipped.

### 9.1 Constitutional Drift
Changes to governance hierarchy, authority structure, constitutional
principles, or role definitions without a corresponding locked ADR
or contract.

### 9.2 Sequencing Drift
Changes that alter build order, collapse prerequisites, advance
deferred work prematurely, or misrepresent the current phase boundary.

### 9.3 Hidden Reframing
Subtle shifts in framing that change architectural intent without
flagging the change explicitly. Examples:
- Describing a transitional state as stable
- Softening an active risk into a resolved risk
- Changing a named architectural problem into a feature

### 9.4 Overstatement of Completion
Claiming a capability is operational when it is only partially
implemented. Examples:
- "operational" does not mean "fully governed"
- "queue ownership" does not mean "orchestration"
- "validated" does not mean "constitutionally closed" without a manifest

### 9.5 Omission Risk
Removal of content that must be preserved. Examples:
- Active architectural discoveries removed
- Known limitations erased
- Deferred risks hidden
- Transitional items removed before replacement is built

### 9.6 Governance Contradictions
New content that conflicts with locked ADRs, locked contracts,
or constitutional principles.

### 9.7 Scope Violation
Changes that fall outside the declared Update Scope Declaration.
Any out-of-scope change requires either scope amendment approved
by the Human Gate, or removal before apply proceeds.

---

## 10. Apply Atomicity Rule

Primer update apply operations use best-effort staged atomic replacement.

Each individual canonical file replacement is atomic at the filesystem
level via temp-file rename (Path.replace() on POSIX systems).

Cross-file rollback safety is provided through:
- immutable timestamped backups created before the commit phase
- failure-state preservation of all draft files on error
- explicit FAILED_APPLY cycle state with conflict register logging

True cross-file transactional atomicity is not guaranteed at the
filesystem layer. The governance guarantee is:

If apply fails mid-operation:
- each completed replacement remains valid (individual atomic writes)
- all remaining canonical files are unchanged
- backups are available for any replaced file
- the apply is marked FAILED_APPLY
- draft files are preserved for recovery
- the failure is logged to CIS_CONFLICT_REGISTER.md before proceeding

Partial apply states must be resolved from backups before the next
update cycle begins.

---

## 11. Canonical Conflict Rule

If a candidate update conflicts with:
- locked ADRs
- locked contracts
- the canonical governance hierarchy

the update cycle must halt immediately.

The cycle may resume only when:
- the conflict is resolved, OR
- superseding constitutional authority is explicitly established
  through a new locked ADR or contract

No candidate update may silently supersede locked governance state.
Silent constitutional overwrites are prohibited.

---

## 12. Required Artifacts

Every update cycle must produce all of the following artifacts.
A cycle is not complete without all artifacts present.

### 12.1 Update Scope Declaration
Required before draft files are generated.
Must declare:
- Intended architectural scope
- Affected primer files and domains
- Expected governance impact
- Runtime events grounding the update

### 12.2 Draft Files
Location: Primer folder, beside canonical files
Naming: <canonical_name>_update_draft.md
Status: Candidate only. Not canonical.
Rule: Draft files are removed automatically after successful apply.
      Failed or deferred cycles preserve draft files.

### 12.3 Preview Diff
Generated by: primer_update_v3.py --preview
Rule: Must exist and be reviewed before apply is permitted.

### 12.4 Primer Update Review Record
Filename: primer_update_review_<YYYYMMDD_HHMM>.md
Location: /_backups/<timestamp>/
Required fields:
- Update cycle timestamp
- Architect model
- Verifier model
- Update Scope Declaration (copy or reference)
- Verifier findings for all seven constitutional check categories
- Disagreements identified
- Disagreement resolution
- Approval decision
- Human Gate approval timestamp

### 12.5 Apply Manifest
Generated after successful apply by primer_update_v3.py.
Required fields:
- Files updated
- Timestamp
- Architect model
- Verifier model
- Human approval confirmation
- Backup location
- Constitutional keyword drift warnings (if any)

### 12.6 Artifact Immutability Rule

Primer Update Review Records and Apply Manifests are immutable
audit artifacts.

Once generated:
- they may not be edited in-place
- corrections require a superseding review record or manifest
  referencing the original by timestamp
- original artifacts must remain preserved in /_backups/

This rule exists to preserve audit integrity for future autonomous
governance, dispute tracing, and drift reconstruction.

---

## 13. Disagreement Handling

A Verifier disagreement blocks apply.

Disagreements must be:
- Logged in the Primer Update Review Record
- Resolved before apply, OR
- Explicitly deferred by Human Gate with logged rationale

Silent override is not permitted under any circumstance.

If the Architect and Verifier cannot resolve a disagreement,
the Human Gate decides within the bounds of this contract.

The Human Gate may not use its resolution authority to bypass
constitutional requirements or override locked governance documents.

---

## 14. Backup and Rollback Rules

Before any apply action:
- All canonical files to be modified are backed up
- Backups are timestamped and stored in /_backups/<timestamp>/
- Backups are immutable — they are never overwritten

Rollback procedure:
1. Identify target backup timestamp
2. Copy files from /_backups/<timestamp>/ to canonical locations
3. Log rollback in CIS_CONFLICT_REGISTER.md
4. Generate rollback manifest documenting what was restored and why

---

## 15. Primer Drift Audit Requirement

Primer files must be periodically reviewed against:
- Current runtime behavior
- Locked ADRs
- Active contracts
- Operational reality

to detect:
- Stale constitutional state
- Unresolved divergence between primer and runtime
- Institutional memory drift accumulation

Drift audits are themselves governed update cycles.
They must produce all required artifacts defined in Section 12.
Drift audit findings that require primer updates must pass through
the full update pipeline defined in Section 8.

Minimum frequency: at every major phase transition.

Runtime and primer WILL diverge silently over time without audits.
This requirement exists to make reconciliation lawful and traceable.

---

## 16. Future Model Participation

Local models may participate in Architect or Verifier roles only
after ALL of the following conditions are met:

1. Role constraints for that model are explicitly defined in a
   locked ADR
2. Verification pathways for that model's output are established
3. Constitutional review requirements are enforced for that model
4. Human Gate approval is obtained before the model's first
   governance action

No autonomous canonization is permitted under any model.
The requirement for independent review is not relaxable by automation.

When local models become primary Architects:
- Frontier models (Claude, ChatGPT) transition to Verifier roles
- Constitutional review requirements remain identical
- Human Gate authority is unchanged

**Future Orchestration Compliance Clause**

Future orchestration systems must obey this contract.

Automation may accelerate governance workflows.
Automation may not:
- weaken constitutional review requirements
- collapse role separation
- bypass human approval requirements
- enable independent verification by the generating model

Speed does not license governance bypass. Ever.

---

## 17. Governance Hierarchy

This contract is subordinate to:
- CIS_Verification_Layer_Contract_v1.md
- CIS_Execution_Layer_Contract_v1.md
- Locked ADRs

This contract governs primer updates within that hierarchy.

In any conflict, the higher-authority document governs and a conflict
must be logged to CIS_CONFLICT_REGISTER.md before the update cycle
proceeds.

---

## 18. Prohibited Actions (Summary)

These actions are prohibited under all circumstances:

- Treating conversational conclusions as canonical memory
- Treating conversation transcripts as constitutional authority
- Treating model reasoning as canonical memory
- Treating draft files or preview diffs as authoritative state
- Treating runtime discoveries as canonical without lawful apply
- Applying primer updates without an Update Scope Declaration
- Applying primer updates without preview generation
- Applying primer updates without independent Verifier review
- Applying primer updates without Human Gate approval
- A model acting as both Architect and Verifier in the same cycle
- Silent override of Verifier disagreements
- Generating candidate updates from unverified or conversational sources
- Autonomous apply by any model or script without human approval
- Partial apply
- Rollback without logging
- Human Gate bypassing constitutional requirements
- Human Gate overriding locked governance contracts
- Automation weakening review requirements

---

## 19. Update Cycle Failure States

Primer update cycles may terminate in one of the following states:

**APPROVED** — All pipeline steps completed. Apply succeeded.
Canonical memory updated. Draft files removed.

**REJECTED** — Human Gate rejected the candidate updates. Draft files
discarded by human decision. No canonical memory change.

**DEFERRED** — Human Gate deferred the decision. Draft files preserved
beside canonical files. No canonical memory change. Cycle must resume
explicitly.

**FAILED_APPLY** — Apply operation failed mid-execution. Rollback
triggered. Canonical memory unchanged. Draft files preserved.
Failure logged to conflict register.

**FAILED_REVIEW** — Verifier identified blocking constitutional concerns
that could not be resolved. Cycle halted. Draft files preserved.
No apply permitted until concerns resolved.

**CONFLICT_BLOCKED** — Candidate updates conflict with locked ADRs or
contracts. Cycle halted until conflict resolved or superseding authority
established. Draft files preserved.

A failed or deferred cycle does not modify canonical memory state.

All failed or deferred cycles must preserve:
- draft files
- preview diffs
- review records
- disagreement logs

Preservation is required for audit integrity and future orchestration
tracing.

---

## 20. Transitional Note

The _update_staging/ folder used in primer_update_v2.py is deprecated.

New workflow uses in-place *_update_draft.md files beside canonical
files in the primer folder. The primer folder is now the single
authoritative surface for both canonical memory and candidate updates.

primer_update_v2.py is superseded by primer_update_v3.py.
primer_update_v2.py must not be used for new update cycles.

The 7 candidate updates for ADR-045 closure must be regenerated
as *_update_draft.md files in the primer folder using the new
workflow before running the first governed update cycle.

---

## 21. Contract Lock Conditions

This contract is LOCKED as of ADR-049.

v1.1 amendment locked under the same ADR.
Amendment scope: operational workflow simplification only.
All constitutional protections unchanged from v1.
