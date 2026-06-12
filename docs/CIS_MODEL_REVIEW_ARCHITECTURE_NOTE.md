# Architecture Note: Model-Based Implementation Review
## Proposal / Decision Draft

**Author:** Hermes V4 Implementer
**Date:** 2026-06-12
**Status:** PROPOSED — Decision Proposal for Eric Gate review

---

## 1. Problem

ADR-SEED-002 (Verification Hardening Rule) states:

> V4 Implementer self-report is not a source of truth. Completion accepted
> only after deterministic evidence: git diff, test output, DB queries,
> endpoint responses, service health, browser/UI state, independent
> reviewer pass/fail.

This is correct. Deterministic gates confirm that something happened — a file
was created, a test passed, a diff exists. They answer "did it happen?"

But deterministic gates do not answer:

- Does this implementation match the scope of the approved directive?
- Is the code brittle, over-engineered, or duplicating existing patterns?
- Did the implementer quietly add files outside the approved manifest?
- Are there silent failure modes the gates don't catch?
- Is the design direction still correct given what was actually built?

These are qualitative model-review questions. They require a reasoning model
to evaluate. They cannot be answered by `grep`, `sqlite3`, or `wc -l`.

## 2. Proposed Architecture

Add a MODEL_REVIEW lane to the CIS pipeline after VERIFY and before ERIC_ACCEPT.

Current pipeline (simplified):
```
IMPLEMENT → VERIFY → ERIC_ACCEPT → STATE_WRITE / EXPORT / DONE
```

Proposed pipeline:
```
IMPLEMENT → VERIFY → MODEL_REVIEW → ERIC_ACCEPT → STATE_WRITE / EXPORT / DONE
```

The model reviewer (Drafter or Reviewer profile, default: Reviewer/hermes-r1)
receives the implementation evidence and produces a ModelReviewReport.

## 3. What the Model Reviewer Must Review

The model reviewer receives as input:

| Evidence | Source | How Obtained |
|----------|--------|-------------|
| Original approved directive | FINAL_DIRECTIVE / workflow_runs topic | Spine query |
| Approved file manifest | FINAL_DIRECTIVE parsed manifest | Spine query |
| git diff or commit diff | `git diff IMPLEMENT^..IMPLEMENT` | Gate output or direct |
| Changed files list | `git diff --name-only IMPLEMENT^..IMPLEMENT` | Gate output or direct |
| Test output | `tests/test_*.py` or gate-gathered results | Gate output or direct |
| Gate output | stdout of all verification gates | Gate runner |
| Relevant DB state | `sqlite3 ... SELECT` of affected tables | Gate or spine query |
| Export regeneration output | `generate_all.py` stdout | Gate or direct |

The model reviewer produces a ModelReviewReport with these sections:

1. **Scope Check**
   - Does the diff match the approved file manifest?
   - Are any files modified or created outside the manifest?
   - Are any out-of-scope tiers, projects, or domains touched?

2. **Design Quality**
   - Is the approach consistent with existing patterns in the codebase?
   - Is there duplication of existing functionality?
   - Are there signs of over-engineering for the problem size?

3. **Brittleness Assessment**
   - Are there hardcoded values that should be configurable?
   - Are error paths handled or silently swallowed?
   - Are there assumptions about file paths, DB schemas, or service availability?

4. **Overreach Check**
   - Did the implementer go beyond the approved directive scope?
   - Are there forward-looking features that should be deferred?
   - Are there accidental modifications to unrelated files?

5. **Recommendation**
   - ACCEPT — implementation is correct and in scope
   - ACCEPT_WITH_NOTES — minor issues noted, accept and defer fixes
   - RETURN_TO_IMPLEMENT — specific issues must be addressed before Eric review
   - ESCALATE — architectural problem requiring broader deliberation

## 4. Governing Rules

### 4.1 Model review is advisory

The model reviewer's output is a recommendation, not a gate. Only deterministic
gates can fail a pipeline stage. Only Eric Gate can approve or veto.

### 4.2 Model review cannot replace deterministic gates

If gate_build_state_coherence.sh fails, MODEL_REVIEW does not run. Deterministic
verification always precedes model review. If a deterministic gate fails, the
pipeline stops immediately — model review is irrelevant.

### 4.3 Model review runs on a reasoning-capable profile

The reviewer must be a profile with high reasoning capability (hermes-r1 or
hermes-v4pro, not hermes-prime or hermes-qwen). The reviewer must operate
in read-only mode — it reads evidence, produces a report, and does not
modify files or DB rows.

### 4.4 Model review is optional and Eric-skippable

Eric may skip MODEL_REVIEW for trivial or well-understood changes. The
pipeline accepts a --skip-model-review flag. Skipping is logged.

### 4.5 Model review evidence is preserved

The ModelReviewReport is stored in workflow_runs or deliberation_rounds and
referenced in closeout evidence. It becomes part of the implementation's
audit trail.

## 5. Relationship to Existing Architecture

### 5.1 Complement to ADR-SEED-002

ADR-SEED-002 requires deterministic evidence. MODEL_REVIEW adds a second
layer: evidence interpretation. The gates prove facts. The model reviewer
interprets whether those facts indicate quality.

### 5.2 Not a replacement for Eric Gate

Eric still makes the final accept/reject decision. The model reviewer gives
Eric an independent second opinion — like ChatGPT auditing a Claude design
in the current Foundation Hardening workflow.

### 5.3 Compatible with OQ-SEED-005 (File Manifest)

The approved file manifest enforcement (OQ-SEED-005) is a deterministic gate
concern. MODEL_REVIEW adds qualitative review of the files that passed the
manifest gate. The two are complementary, not overlapping.

### 5.4 Future placement in Tier 7R pipeline

MODEL_REVIEW fits within Tier 7R.5 (Human Approval Gate Integration) or as
a separate 7R.5a node. The Process Manager (7R.4) would route IMPLEMENT →
VERIFY → MODEL_REVIEW → ERIC_GATE → STATE_WRITE.

## 6. Acceptance Test (when implemented)

```
Given: An IMPLEMENT commit with a deliberate scope overreach
       (file created outside approved manifest)
When:  MODEL_REVIEW runs
Then:  ModelReviewReport.overreach_check = TRUE
       ModelReviewReport.recommendation = RETURN_TO_IMPLEMENT
       Eric sees the report before accepting
```

```
Given: An IMPLEMENT commit that is fully in scope, clean tests, clean gates
When:  MODEL_REVIEW runs
Then:  ModelReviewReport.scope_check = PASS
       ModelReviewReport.recommendation = ACCEPT
       Eric sees a clean recommendation alongside gate evidence
```

## 7. What This Does NOT Change

- Does not weaken ADR-SEED-002 (deterministic evidence still required)
- Does not add a new gate (model review is advisory, not pass/fail)
- Does not change Eric Gate authority
- Does not change Tier 7R node structure
- Does not implement enforcement code
- Does not start 7R.2 implementation

---

*End of Architecture Note*
*Next step: Eric Gate review → APPROVE / DEFER / RETURN_TO_DRAFT*
