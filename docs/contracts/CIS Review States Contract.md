# CIS Review States Contract v1.1
# Path: /mnt/projects/cis/docs/contracts/CIS Review States Contract.md
# Status: DRAFT — awaiting verification
# ADR reference: ADR-020 (review page is the human validation surface),
#                ADR-037 (source manifest defines review as a pipeline stage)

---

## Purpose

The review states contract defines the trust states that govern how a
knowledge_record moves from raw system output to trusted system knowledge.
Review states are the human validation layer — they determine whether a
record is eligible for retrieval, workflow use, and application display.

Review state is a property of the knowledge_record, not the source manifest.
The source manifest tracks intake_state. The knowledge_record tracks
review_state.

---

## When Review State Is Assigned

A knowledge_record is created with review_state = draft at the moment
cis_normalize.py writes the canonical JSON output.

Review state advances only through explicit human action via cis_review.py
or the Review surface in the CIS dashboard.

The pipeline does not self-promote records beyond draft.
No automated process may promote a record to approved or locked.

---

## Allowed Review States

Exactly five states are defined. No state outside this list is valid.

### draft
The record has been produced by the pipeline and written to disk.
It has not been reviewed by a human.
Retrieval priority: low — draft records are excluded from workflow use
and application display by default.
Eligible for: promotion to checked, deprecation.

### checked
A human has performed a basic sanity check on the record.
The record is structurally sound and the extracted content is plausible,
but has not been fully validated.
Retrieval priority: medium — checked records may appear in retrieval
results but are flagged as unvalidated.
Eligible for: promotion to approved, demotion to draft, deprecation.

### approved
A human has validated the record and accepted it for workflow use.
The extracted content is accurate and the record is trustworthy.
Retrieval priority: high — approved records are the primary retrieval
target for workflow and application use.
Eligible for: promotion to locked, demotion to checked, deprecation.

### locked
The record is stable and should not change without explicit human intent.
Locked records represent high-confidence, high-value knowledge.
Retrieval priority: highest — locked records take precedence in retrieval.
Eligible for: deprecation only. Locked records may not be demoted to any
lower review state. Correction requires creating a new version and
deprecating the locked version.

### deprecated
The record has been superseded, found to be incorrect, or is no longer
relevant. It is retained for lineage and audit purposes but is not
surfaced in retrieval or workflow use.
Retrieval priority: none — deprecated records are hidden from standard
retrieval; accessible only via direct lookup by record_id.
Deprecated is a terminal state. No promotion or demotion is permitted
from deprecated. A deprecated record cannot be re-deprecated.
If a deprecated record must be corrected or restored, a new version
must be created and promoted through the review path.

---

## Promotion Path

Standard forward path:
draft → checked → approved → locked

Steps may not be skipped in the forward direction.
A record may not advance from draft directly to approved.
A record may not advance from checked directly to locked.

---

## Demotion Rules

Demotion is permitted for correction and quality control.

Allowed demotion paths:
- checked → draft
- approved → checked

Locked records may not be demoted. See locked state definition above.
Deprecated records may not be demoted. Deprecated is terminal.

---

## Deprecation Rules

Any non-deprecated state may transition to deprecated via explicit
human action. Deprecated is a terminal state — once set, it cannot
be changed.

Deprecated records are never deleted — they are retained for lineage.

When a record is deprecated:
- If deprecated without a replacement: set is_current = false
- If deprecated because a new version replaces it: the new version
  becomes is_current = true; the deprecated version becomes
  is_current = false
- In both cases, no current-but-deprecated record may exist

If a deprecated record is found to have been deprecated in error,
a new version must be created from it and promoted through the
review path. The deprecated version is not restored.

---

## Retrieval Priority

The system must apply retrieval priority in this order:
1. locked (highest)
2. approved
3. checked
4. draft (lowest — excluded from standard retrieval by default)
5. deprecated (hidden — not returned in standard retrieval)

When multiple versions of a record exist, only the version where
is_current = true is returned by default.
A deprecated record always has is_current = false.

---

## Versioning Interaction

Review state changes and content version changes are separate operations.

Review state transitions (draft → checked → approved → locked,
demotions, deprecations):
- update review_state on the existing record
- update last_updated
- do not create a new content version
- do not increment the version number

A new content version is created only when:
- record content is being corrected or improved
- a locked record requires correction (mandatory — locked records
  may not be modified in place)

When a new content version is created:
- the new version begins at review_state = draft regardless of the
  prior version's review state
- the prior version's is_current flag is set to false
- the prior version retains its review state for audit purposes
- only one version may have is_current = true at any time

---

## Field Definition

The review_state field on knowledge_record:
- type: string, required
- allowed values: draft, checked, approved, locked, deprecated
- default at creation: draft
- mutability: controlled — advances via human action only;
  pipeline may not modify review_state after initial assignment at draft

---

## Relationship to cis_review.py

cis_review.py is the pipeline script that surfaces records for human
review and processes state transitions.

cis_review.py must:
- present draft records to the human operator for review
- accept human input to promote, demote, or deprecate a record
- write the updated review_state to the canonical JSON record
- update last_updated on any state change
- log all state transitions with timestamp and actor

cis_review.py must not:
- promote records automatically without human input
- skip states in the promotion path
- modify locked records directly
- create a new content version solely because review_state changed

---

## Relationship to Dashboard Review Surface

The Review surface in the CIS dashboard (ADR-020) is the primary human
interface for review state management. It must reflect the same rules
defined in this contract.

The dashboard Review surface and cis_review.py are two interfaces to the
same underlying review state system. They must produce identical outcomes
for identical inputs.

---

## What Review State Is Not

- It is not a pipeline processing state (that is intake_state on the manifest)
- It is not a quality score
- It is not automatically assigned based on extraction confidence
- It is not modified by re-extraction unless the human explicitly resets it
- It does not trigger a new content version on its own

---

## Schema File

Review state rules must be reflected in the knowledge_record schema at:
/mnt/projects/cis/runtime/schemas/knowledge_v1.json

The contract (this file) is the authoritative specification.
If the schema file and this contract conflict, this contract governs.

---

## Contract Status

Draft v1:   2026-04-26 — Claude (builder)
Draft v1.1: 2026-04-26 — updated after Layer 3 audit pass 1 (FAIL)
            Changes: separated review-state transitions from content
            versioning; defined is_current behavior on deprecation;
            clarified deprecated as terminal — only non-deprecated states
            may transition to deprecated
Author: Claude (builder) — requires Layer 3 audit by separate frontier model
Verification: pending cis_verify.py pass
