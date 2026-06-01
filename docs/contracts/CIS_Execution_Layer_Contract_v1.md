# CIS Execution Layer Contract v1
# ADR-043
# Status: LOCKED — Pending Verification (L1 + L2 + L3)
# Created: 2026-04-28
# Purpose: Define the authoritative control system for all CIS pipeline
#          execution, state transitions, role enforcement, and human gates.
# Parent contracts: CIS_Verification_Layer_Contract_v1.md (ADR-033)
#                   CIS_Verification_Layer_Contract_v1_Addendum_A.md (ADR-033)
# Canonical path: /mnt/projects/cis/docs/contracts/
#                 CIS_Execution_Layer_Contract_v1.md


---


## 1. Purpose


The Execution Layer defines the authoritative control system for CIS.


It ensures that:


- all pipeline operations are deterministic
- all state transitions are enforced, not inferred
- all outputs are verified before acceptance
- the human is removed from continuous arbitration and reduced to
  explicit approval gates only


No system behavior is trusted.
All behavior is constrained, validated, and logged.


---


## 2. Core System Principle


The system must not be trusted to behave correctly.
It must be forced to behave correctly through enforced constraints.


---


## 3. Relationship to Existing Contracts


This contract extends and depends on:


- CIS_Verification_Layer_Contract_v1.md (ADR-033)
- CIS_Verification_Layer_Contract_v1_Addendum_A.md (ADR-033 extension)


The three-layer verification architecture defined in those contracts
(L1 deterministic script, L2 local model, L3 external frontier model)
applies to every pipeline step governed by this contract.


Where this contract conflicts with the parent contracts, the parent
contracts take precedence. Changes to the parent contracts that affect
execution behavior require a corresponding update to this contract.


---


## 4. System Architecture


The Execution Layer consists of three enforced components:


### 4.1 Orchestrator


Responsible for:
- reading pipeline state
- determining next valid step
- dispatching tasks to scripts or models


Constraint:
- may not interpret semantic meaning of outputs
- may not override transition rules
- may not skip verification steps


### 4.2 Process Integrity Layer


Responsible for:
- validating all state transitions
- enforcing role separation
- enforcing verification requirements
- enforcing evidence requirements


This logic is embedded in transition rules.
It is not a separate service — it is the enforcement condition
checked before every state change.


### 4.3 Human Gate Layer


Responsible for:
- binary approval decisions (YES / NO / OTHER)
- appearing only at predefined checkpoints


Human does not:
- route tasks
- interpret outputs continuously
- manage execution


---


## 5. State Authority


All pipeline state must be stored and read exclusively from the
pipeline_state table in cis_memory.db.


No system component may infer state from logs, file presence,
or model output.


State is the single source of truth. If state says an item is
in `classified`, it is in `classified` — regardless of what files
exist on disk.


### State Write Atomicity Rule


All state transitions must be written atomically.


A transition must execute in this exact order:
1. Write Process Record to disk
2. Validate Process Record (L1 check)
3. Commit state change to pipeline_state table


If any step in this sequence fails:
- state must not change
- partial writes must be rolled back
- failure logged to execution_log.md


No partial state transitions are permitted under any condition.


### Step Ownership Lock Rule


Before executing a step, the orchestrator must acquire a lock
on the pipeline item.


While locked:
- no other process may modify or execute steps for that item


Lock must be released after:
- successful state transition
- failure routing completes


This rule applies even in single-threaded execution mode.
It exists to prevent future concurrency bugs and accidental
double execution.


---


## 6. Execution Model


Execution Mode v1:
- Single-threaded orchestrator loop
- One transition processed at a time
- No parallel execution allowed


---


## 7. Core Execution Loop
INGEST → STATE → TASK → MODEL → OUTPUT → VERIFY → VALIDATE → ADVANCE → LOG


---


## 8. State Machine


Each pipeline item must exist in exactly one state at all times.


### Active States (eligible for further processing)


| State | Meaning |
|---|---|
| ingested | File received and registered. Manifest created. |
| classified | Processing profile assigned. Document type identified. |
| preprocessed | File converted to model-ready format. |
| extracted | First-pass structured output produced by Architect role. |
| verified | Extraction output passed L1 + L2 verification. |
| contradiction_checked | Cross-document consistency check completed by Verifier role. |
| synthesis_ready | All documents verified. Contradictions logged. Ready for plan. |
| awaiting_approval | Human gate reached. Item queued for human decision. |
| rejected | Human said NO. Item returned with rejection note. |
| retry_pending | Step failed, retry authorized, waiting for retry. |
| contradiction_detected | Cross-document conflict found requiring resolution. |
| human_review_required | Ambiguity or edge case requiring human judgment. |
| human_redirected | Human said OTHER. Item redirected with instruction. |


### Terminal States (no further processing)


| State | Meaning |
|---|---|
| approved | Human said YES. Item accepted. Pipeline complete for this item. |
| deprecated | Item superseded or removed from active pipeline. |
| failed | Verification failed and max retries exceeded. No further processing. |
| failed_timeout | Step exceeded maximum execution time and retry limit. |


Terminal states are final. No transition out of a terminal state
is permitted except by explicit human intervention logged as a
new pipeline entry.


---


## 9. Allowed Transitions (Complete Table)


A transition is only permitted when ALL listed conditions are satisfied.
If any condition fails, state does not advance.


| From State | To State | Required Conditions |
|---|---|---|
| ingested | classified | manifest exists; source_type identified; processing_profile assigned |
| classified | preprocessed | processing_profile loaded; preprocessing completed without error; working/ folder created |
| preprocessed | extracted | model-ready inputs exist; Architect role assigned; structured output produced; Process Record created |
| extracted | verified | Process Record exists; L1 PASS; L2 PASS |
| extracted | retry_pending | L1 FAIL; retry count below max |
| extracted | failed | L1 FAIL; max retries exceeded |
| extracted | failed_timeout | execution time exceeded maximum; timeout recorded |
| verified | contradiction_checked | all batch documents at verified state; Verifier role assigned; contradiction report produced; Process Record created |
| verified | contradiction_detected | Verifier identifies cross-document conflict during contradiction_checked step |
| verified | failed_timeout | execution time exceeded maximum; timeout recorded |
| contradiction_checked | synthesis_ready | all contradictions logged; open questions recorded; no HARD_FAILs unresolved; Skeptic role has reviewed |
| contradiction_checked | failed_timeout | execution time exceeded maximum; timeout recorded |
| contradiction_detected | human_review_required | contradiction cannot be auto-resolved |
| synthesis_ready | awaiting_approval | synthesis document produced; evidence ledger populated; Process Record created; L1 PASS; L2 PASS; L3 PASS |
| awaiting_approval | approved | human decision = YES; recorded in pipeline_state |
| awaiting_approval | rejected | human decision = NO; rejection note recorded |
| awaiting_approval | human_redirected | human decision = OTHER; redirect instruction recorded |
| rejected | extracted | rejection note attached; Architect role re-assigned |
| human_redirected | [target_state] | target_state is a valid active state; redirect instruction logged; re-entry recorded |
| human_review_required | awaiting_approval | human has reviewed; resolution logged; resolution note attached |
| retry_pending | extracted | retry authorized; step re-dispatched |
| retry_pending | human_review_required | retry limit exceeded |
| failed_timeout | retry_pending | timeout retry authorized; retry count below max |
| failed_timeout | human_review_required | timeout retry limit exceeded |


### Approved Transition Rule


approved → [next pipeline phase]


Constraint:
- next state must be explicitly defined in the active pipeline definition
- orchestrator may not infer next state
- if no next state is defined, item remains in approved state
  until pipeline definition is updated


---


## 10. Contradiction Detection Rule


Contradictions may ONLY be detected during the contradiction_checked step.


No other step may assign contradiction_detected state.


This rule prevents:
- random model-triggered contradictions during other steps
- inconsistent pipeline behavior
- uncontrolled state branching


---


## 11. Transition Enforcement Rules


A state transition is permitted ONLY if all conditions are true:


1. Correct role executed the step
2. Required inputs exist and are registered in pipeline_state
3. Output matches required schema version for that step
4. Required verification layers passed (see Section 13)
5. Evidence is recorded in the Process Record
6. Process Record is written and L1-validated before transition executes
7. Step ownership lock is held by the orchestrator


If ANY condition fails:
- State remains unchanged
- Transition denied
- Denial reason logged to execution_log.md
- Item routed per failure rules (see Section 21)


---


## 12. Role Enforcement


| Role | May Do | May Not Do |
|---|---|---|
| Architect | Propose, extract, synthesize | Verify own output, approve |
| Verifier | Verify, check consistency, flag contradictions | Propose, approve |
| Skeptic | Challenge, red-team, identify drift | Propose, verify, approve |
| Implementer | Expand accepted plan into build steps | Validate, verify, approve |
| Orchestrator | Read state, dispatch steps, advance state | Interpret meaning, override verification |


No role may evaluate its own output.
The model that produced a step's output may not serve as its verifier.
This rule applies to all roles without exception.


---


## 13. Verification Requirements Per Step


Each pipeline step has defined verification requirements.
A step may not advance until its required layers have passed.


| Step | L1 | L2 | L3 | Notes |
|---|---|---|---|---|
| Manifest creation | REQUIRED | NO | NO | Structural check only |
| Classification | REQUIRED | NO | NO | Profile assignment verified |
| Preprocessing | REQUIRED | NO | NO | Output files exist check |
| Extraction (first pass) | REQUIRED | REQUIRED | NO | Semantic quality required |
| Cross-document verification | REQUIRED | REQUIRED | NO | Contradiction report reviewed |
| Synthesis / plan skeleton | REQUIRED | REQUIRED | REQUIRED | All layers required |
| Contract creation | REQUIRED | REQUIRED | REQUIRED | Per parent contract mandate |
| Reorientation file update | REQUIRED | REQUIRED | REQUIRED | Per parent contract mandate |
| Process Record creation | REQUIRED | NO | NO | Schema compliance check |
| Human gate package assembly | REQUIRED | REQUIRED | NO | Package must be complete |


Confidence thresholds:
- L2 PASS requires confidence ≥ 0.7
- L2 UNCERTAIN triggers automatic escalation to L3
- L3 REVIEW verdict routes item to human_review_required


---


## 14. Verification Failure Types


| Type | Definition | Behavior |
|---|---|---|
| HARD_FAIL | Required output missing, schema invalid, forbidden strings detected | Cannot proceed. Human intervention required. |
| SOFT_FAIL | Output exists but quality below threshold | Retry permitted up to max_retry count |
| UNCERTAIN | L2 cannot determine pass or fail | Escalate to L3 automatically |
| MALFORMED | Verification response did not follow required format | Re-run verification. Do not advance. |


---


## 15. Process Record (Required Artifact)


Every step must produce a Process Record before state advances.
No transition may occur without a valid, L1-validated Process Record.


### Schema (v1)
PROCESS RECORD Schema_version: v1 Step: [step name] Role: [role name and model slot used] Input: [list of input document IDs or record IDs] Output: [list of output record IDs or file paths] Verification: L1: [PASS | FAIL | n/a] L2: [PASS | FAIL | UNCERTAIN | n/a] L3: [PASS | FAIL | REVIEW | PENDING | n/a] Evidence: [list of source citations or record IDs] Decision: [ADVANCE | HOLD] Failure_note: [required if Decision = HOLD; empty string if ADVANCE] Timestamp: [UTC]


### Storage
/mnt/projects/cis/logs/process_records/ [pipeline_type]/[item_id]/[step_name]_[timestamp].json


### Validation


Process Records are validated by L1 before the transition executes.
A Process Record that fails L1 validation blocks the transition.
The item remains in its current state.


---


## 16. Schema Versioning Rule


Each step schema must include a version number.


If a schema changes:
- version must increment
- old records must remain valid under their original schema version
- no step may assume the latest schema implicitly


The schema version is recorded in the Process Record under
`Schema_version`. The orchestrator validates that the schema version
matches the version expected for that step before executing.


---


## 17. Evidence Binding Rule


Every decision that advances state must include at least one traceable
evidence reference in the Process Record.


Evidence reference format:
source: [record_id or document path] claim: [what this source supports]


No evidence → transition denied.
Unsupported claims → HARD_FAIL.


---


## 18. Idempotency Rule


All steps must be idempotent.


Re-running a step must not:
- duplicate outputs
- corrupt state
- incorrectly advance pipeline


If a step is re-run on an item already in a later state,
the step logs a warning and exits without modifying state.


---


## 19. Retry Rules


| Parameter | Default Value |
|---|---|
| Max retries | 3 |
| Retry delay | 60 seconds |
| Escalation after max retries | → human_review_required |


Each step may define a custom max retry count in its step specification.
If not defined, default values apply.


---


## 20. Timeout Rules


Default timeout: 300 seconds (5 minutes).


Steps with known long execution times must declare their timeout
explicitly in the step specification.


If timeout is exceeded:
- state → failed_timeout
- reason logged to execution_log.md
- item routed to retry_pending or human_review_required per retry rules


---


## 21. Failure Routing


No failure may silently terminate processing.
Every failure state has a defined next action.


| Failure State | Routing |
|---|---|
| failed | → human_review_required; reason logged; no retry |
| failed_timeout | → retry_pending if retries remain; else → human_review_required |
| contradiction_detected | → human_review_required; contradiction record created |
| human_review_required | → awaiting_approval; human sees item with full failure context |
| rejected | → extracted; rejection note attached; Architect re-assigned |
| human_redirected | → target_state defined by human OTHER instruction; redirect logged |


---


## 22. Human Redirect State


State: human_redirected


When the human selects OTHER at any approval gate, the item enters
human_redirected state.


Required fields logged at redirect:
- reason: what the human specified
- target_state: which valid active state the item re-enters
- notes: any additional instruction


The orchestrator may not infer target_state.
The human must specify it explicitly.
The redirect is logged in pipeline_state and execution_log.md.


---


## 23. Human Gate Positions


The human appears at exactly these points:


| Gate | Trigger | Human Sees |
|---|---|---|
| Synthesis approval | state = awaiting_approval after synthesis_ready | Plan skeleton, evidence ledger, contradiction log, confidence levels |
| Contradiction resolution | state = human_review_required after contradiction_detected | Contradiction record, conflicting sources, Skeptic findings |
| Failure review | state = human_review_required after max retries | Failure log, last Process Record, recommended action |
| Final plan acceptance | state = awaiting_approval after full plan elaboration | Complete Build Plan v2, verification summary, open questions |


At every gate, the human has exactly three options:
- YES → approved; pipeline advances
- NO → rejected; item returns to prior step with rejection note
- OTHER → human_redirected; human must specify target state and instruction


### Human Authority Boundary


Human decisions do not override system rules.


A human decision may:
- approve
- reject
- redirect


A human decision may NOT:
- bypass verification requirements
- force invalid state transitions
- skip steps defined in this contract


System integrity is not subject to human override.


---


## 24. Orchestrator Constraints


The orchestrator may:
- read state from pipeline_state table
- acquire and release step ownership locks
- trigger steps based on transition rules
- validate rule conditions before transition
- update state after successful transition
- log all actions to execution_log.md


The orchestrator may NOT:
- interpret semantic meaning of content
- override verification results
- skip steps
- resolve contradictions
- make approval decisions
- infer state from anything other than pipeline_state table
- release a lock before transition completes or failure routes


---


## 25. Logging Requirements


### Logging Separation Rule


Three distinct log destinations. No mixing.


| Log | Location | Contains |
|---|---|---|
| Process Records | /mnt/projects/cis/logs/process_records/ | Structured JSON per step per item |
| Verification log | /mnt/projects/cis/logs/verification_log.md | L1, L2, L3 results (per parent contract) |
| Execution log | /mnt/projects/cis/logs/execution_log.md | State transitions, model calls, human decisions, locks |


Every action must log:
- state transitions (from_state, to_state, timestamp, trigger)
- model calls (model_slot, step, input_ids, output_ids, duration)
- lock acquisition and release events
- verification results (layer, verdict, timestamp)
- human decisions (gate, decision, timestamp, notes)


Logs must be append-only and immutable.
No log entry may be modified after writing.


---


## 26. Cold Start Rule


On orchestrator startup, the system must:


1. Scan the pipeline_state table
2. Identify all items not in terminal states
3. Resume processing from each item's current state


No item may be skipped or reset on startup.
No assumption may be made about state based on file presence.
State table is the sole authority on restart.


---


## 27. Build Sequence Enforcement


The Execution Layer must be built in this exact order.
No component may be built before the component above it is verified.


1. This contract — verified (L1 + L2 + L3) and locked as ADR-043
2. pipeline_state table — schema defined, created in cis_memory.db, verified
3. cis_orchestrator.py — core loop built against contract, verified
4. Approval queue panel — dashboard UI for human gates, verified
5. Pipeline activation — first document batch ingested and processed


---


## 28. System Entry Condition


The pipeline may begin processing documents ONLY if:


- this contract is verified (L1 + L2 + L3) and locked
- pipeline_state table exists and is verified
- orchestrator is implemented and verified
- approval queue panel is implemented and verified


No document batch may enter the pipeline before all four conditions are met.


---


## 29. Non-Permitted Behaviors


The system must never:


- infer state from anything other than pipeline_state table
- skip verification layers defined as required for a step
- allow a role to evaluate its own output
- advance state without a valid Process Record
- accept unverifiable output into the knowledge layer
- allow undefined state transitions
- permit partial state writes
- execute a step without holding the item lock
- route a human_redirected item without a defined target_state
- exit a terminal state without explicit human intervention and new pipeline entry


---


## 30. Final Principle


No implicit behavior is allowed.
No undefined state is allowed.
No unverifiable output is allowed.
No transition occurs without a Process Record.
No human arbitration occurs outside defined gate positions.
No state is written non-atomically.


---


## Contract Authority


This contract governs all CIS pipeline execution behavior.
Locked under ADR-043.
Parent contracts take precedence in cases of conflict.
Changes require a new ADR.
This file lives at:
/mnt/projects/cis/docs/contracts/CIS_Execution_Layer_Contract_v1.md
________________


All 10 of ChatGPT's fixes are integrated:
1. State Write Atomicity Rule — Section 5
2. Step Ownership Lock Rule — Section 5
3. "any active state" replaced with explicit states — Section 9 transition table
4. Contradiction detection timing locked to one step — Section 10
5. approved → next state constrained — Section 9 Approved Transition Rule
6. Schema Versioning Rule — Section 16
7. Logging separation into three distinct destinations — Section 25
8. Cold Start Rule — Section 26
9. Terminal States explicitly defined — Section 8
10. Human authority boundary — Section 23
