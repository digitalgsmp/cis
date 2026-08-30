# SPEC INVENTORY — the specs exist. They were never implemented.

**Date:** 2026-08-29
**Method:** filesystem search of the CIS directory, several levels down, for
specs/contracts/ADRs/proposals. Cross-checked against the 20 live issues in
`docs/ISSUE_FINDINGS.md`, which were mined from the knowledge base.

## The headline

`ISSUE_FINDINGS.md` reports things the corpus says are MISSING. This inventory
finds that **the specifications for most of them exist on disk, are written in
full, and in several cases are LOCKED.** The gap is not specification. It is
implementation, and in three cases it is a verification step that was never run.

That changes what the findings mean. "No governance rule for what happens when
verification fails" is not an unanswered question — it is an answered question
whose answer was never wired.

---

## 1. The three "missing Phase 0 contracts" — THEY EXIST

The corpus states repeatedly that these block Phase 1:

> "Foundational Prerequisites: the missing Phase 0 contracts (source manifest, processing profile, review states) must be written before any Phase [1 work]."
> "Write missing Phase 0 contracts — source manifest, processing profile, review states."
> "Schema files missing: source manifest, processing profile, review states, project object, segment. Spec docs missing: everything."

All three are in `docs/contracts/`:

| contract | lines | status | ADR |
|---|---|---|---|
| CIS Source Manifest Contract.md | 239 | **DRAFT — awaiting verification** | ADR-007 |
| CIS Processing Profile Contract.md | 210 | **DRAFT — awaiting verification** | ADR-007, ADR-037 |
| CIS Review States Contract.md | 239 | **DRAFT — awaiting verification** | ADR-020 |

688 lines of specification. Each has Purpose, canonical fields, state machine,
mutability rules, promotion/demotion paths. The Source Manifest contract is at
v2.1 and the other two at v1.1 — they were revised, not abandoned.

**They were never "missing." They are stuck in DRAFT awaiting a verification
step that never ran.** That is the same failure as every other item in the
findings: the thing exists and the last mile was never connected.

---

## 2. The Execution Layer — the "missing foundational layer" has a 782-line LOCKED contract

The corpus calls this the root cause:

> "The Execution Layer is the missing foundational layer that makes everything else real."
> "The root cause of recurring context and orientation loss is NOT missing features but a missing execution layer."
> "Execution layer does not exist as unified, deterministic system — exists only as fragmented shell scripts and manual st[eps]."

`docs/contracts/CIS_Execution_Layer_Contract_v1.md` — **ADR-043, 782 lines,
Status: LOCKED — Pending Verification (L1 + L2 + L3), created 2026-04-28.**

Its 30 sections specify, by name, things `ISSUE_FINDINGS.md` reports as missing:

| findings item said missing | contract section that specifies it |
|---|---|
| F19 — no rule for what a FAIL means | **§21 Failure Routing** |
| F19 — no retry or escalation logic | **§19 Retry Rules**, §20 Timeout Rules |
| F5 — no schema versioning or migration | **§16 Schema Versioning Rule** |
| F21 — cold start recovery deferred | **§26 Cold Start Rule** |
| F1 — no validation layer | §13 Verification Requirements Per Step, §14 Verification Failure Types, §15 Process Record (schema + validation) |
| F31 — no validation of agent claims | **§17 Evidence Binding Rule** |
| F32 — silent failure patterns | §21: *"No failure may silently terminate processing."* |
| F25 — operator routes bypass pipeline | §24 Orchestrator Constraints, §29 Non-Permitted Behaviors |
| F3/F12 — no feedback loops | §25 Logging Requirements, §15 Process Record |
| — | §22 Human Redirect State, §23 Human Gate Positions, §18 Idempotency Rule, §27 Build Sequence Enforcement, §28 System Entry Condition |

**§21 verbatim:**

> "No failure may silently terminate processing. Every failure state has a defined next action."
>
> | failed | → human_review_required; reason logged; no retry |
> | failed_timeout | → retry_pending if retries remain; else → human_review_required |
> | contradiction_detected | → human_review_required; contradiction record created |
> | human_review_required | → awaiting_approval; human sees item with full failure context |
> | rejected | → extracted; rejection note attached; Architect re-assigned |
> | human_redirected | → target_state defined by human OTHER instruction; redirect logged |

**§19 verbatim:** max retries 3, retry delay 60 seconds, escalation after max
retries → `human_review_required`.

The pipeline running today has BLOCK-mode guardrails that kill a run and
ADVISORY ones that are ignored, with nothing in between — which is exactly the
gap this contract closed on paper sixteen months ago.

---

## 3. Other LOCKED contracts that are not implemented

| contract | status | created | what it governs |
|---|---|---|---|
| CIS_Verification_Layer_Contract_v1.md | **LOCKED** | 2026-04-25 | ADR-033. Proof-of-work verification before any build action counts as complete |
| CIS_Verification_Layer_Contract_v1_Addendum_A.md | LOCKED | — | addendum to the above |
| CIS_Automation_Reduction_Contract_v1.md | **LOCKED**, L3 audit PASS | 2026-04-30 | every build action must eliminate at least one manual step |
| CIS_PD5_Operational_Governance_Contract_v1.md | — | — | operational governance |
| CIS_Primer_Update_Governance_Contract_v1.md | — | — | primer update governance — bears on F35 (primer/runtime drift) |
| CIS Session Transcript Extraction Contract v1.md | — | — | the 7-section distillation format; ran by hand April 2026 |

**The Automation Reduction Contract is worth singling out.** Its core rule is
that every build action must eliminate a manual step, and the corpus contains
the enforcement artifact for it:

> "No automation reduction included and no 'NO AUTOMATION REDUCTION FOUND' statement | Contract violation — block treated as incomplete."
> "Missing Automation Reduction Record blocks verification."

That is a locked, audited contract with a defined violation condition. Nothing
enforces it.

---

## 4. ADRs on disk

`docs/ADRs/`:

| file | bears on |
|---|---|
| ADR-041_Artifact_Registry_Schema.md | artifact registry |
| ADR-045_Execution_Queue_Ownership_Layer.md | **F28 — no worker layer**; the execution queue |
| ADR-047_SCOPE_PREDRAFT.md | **F6 — the two manifest directories**. This is the one ADR worth checking |
| ADR-048_SCOPE_PREDRAFT.md | staged draft intake |
| ADR-048_Staged_Draft_Intake_Layer.md | **F33 — the commit route**; intake ownership |

Also in `drafts/inbox/`: ADR-041 and ADR-045 again, plus `.cis_staged` copies —
i.e. they went through a staging path that then stopped.

---

## 5. Proposals

`proposals/`:

- PROPOSAL_TIER_7_ROUTER_RECLASSIFICATION.md — routing (see F7, superseded)
- PROPOSAL_TIER_7_5_DAM_TEXT_INGEST.md — DAM text ingest
- PROPOSAL_BUILD_STATE_REMEDIATION.md — build state
- PROPOSAL_INTENTION_MAP_BRIDGE.md — intention map
- CIS_SPINE_NATIVE_CLOSEOUT_NEXT_SESSION_DIRECTIVE.md — closeout
- four-panel-layout-v1.md, 4-independent-hermes-installs.md
- Foundation Hardening Phase.txt, Kanban Conflict audit.txt, Proposal Flask SQLite.txt

`session_handoffs/` also holds PROPOSAL_RETIRE_KANBAN_SPINE_API.md and
2026-06-19_16_FAILURE_MODES_FOUR_PILLARS.md — the latter is the origin of the
sixteen failure modes now in CLAUDE.md.

---

## 6. Where else specs are buried

Counts of spec-like files by directory, several levels down:

| directory | files |
|---|---|
| data/drive_imports | 151 |
| docs | 58 |
| cis_kernel/extraction/functional_intents | 49 (derived extraction analyses, not source specs) |
| enforcement/mwl-proof-v2/tagging_input + tagging_results | 30 |
| docs/claude_chat_transcripts/drive-download-…-3-001 | 12 |
| docs/contracts | 11 |
| enforcement/mwl-proof-v2/cis-skills-per-role/*/references | 39 across six roles |
| cards/intentions | 11 |
| docs/ADRs | 5 |
| proposals | 5 |

`data/drive_imports` (151) is the largest and is gitignored — see working-queue
item 15.

---

## What this changes

**The findings document's verdicts need one more column.** For most of the 20
live issues the question is no longer "was this ever specified" — it was. The
questions are now:

1. Is the spec still correct for the container architecture?
2. What blocked implementation?
3. For the three DRAFT contracts: what verification step was awaited, and why
   did it never run?

**Three concrete actions this inventory produces:**

- **Read `CIS_Execution_Layer_Contract_v1.md` before building anything in
  Tier 2.** It already specifies failure routing, retry, timeout, idempotency,
  evidence binding and schema versioning. Building those from scratch would
  duplicate a locked contract.
- **Resolve the three DRAFT Phase 0 contracts.** They are 688 lines away from
  done and have been waiting on "verification" since v1.1/v2.1.
- **Check ADR-047 (manifest directories) and ADR-048 (staged intake).** They map
  directly onto F6 and F33, the two Tier-1/Tier-3 items with no owner.

**And the pattern this confirms.** F15 says placeholders are not marked as
placeholders. This is the same failure one level up: **specifications that are
complete and locked are indistinguishable, from the outside, from
specifications that were never written.** Nothing in the system reports
"specified, locked, not implemented" — so the corpus kept recording these as
missing, and every session re-derived them.
