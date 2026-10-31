# CIS Clean — Why Development Activity Did Not Become a Working Contained Pipeline

Evidence-backed incident analysis and corrected recovery plan. Written
2026-10-31. This document distinguishes candidate custody, assurance admission,
promotion authorization, host application, and runtime activation. Those are
separate states and must never again be compressed into the word “completed.”

Repository examined: `/mnt/projects/cis-clean`

Observed branch and HEAD:

```text
wip/queue-4.37-controller-integration-2026-10-20
588f4c98b2f72021d2f0ec8139c2d352b243d74f
```

This is a forensic and recovery document, not authority to execute changes.
Re-derive any fact that will be used for a consequential action.

---

## 1. Executive conclusion

The recent work did not fail because nothing useful was built. It failed
because CIS did not have one connected lifecycle that could carry a bounded
instruction all the way from the Workbench to verified code in the live CIS
Clean tree.

Several portions of that lifecycle exist independently:

- remote Workbench access through Cloudflare Access;
- explicit Codex Brain profile selection and chat sessions;
- Card Factory issuance of canonical task contracts for selected modules;
- Qwen pre-Menter review through Hermes/OpenRouter;
- bounded Claude/Menter execution in isolated candidate workspaces;
- reconstruction-candidate custody;
- deterministic Verifier and deterministic Reviewer implementations;
- a Qwen route-receipt policy and sanctioned ledger writer;
- promotion-decision logic;
- a proof-oriented host promotion gate.

They are not connected into one production path.

The most immediate broken boundary is that the Qwen review used by the
Workbench is not executed through the governed reviewer worker lifecycle and
cannot produce the durable facts required by
`ReviewerFacade.record_route_receipt`. Consequently no current task can satisfy
the promotion conjunction.

That is not the only missing boundary. Even a valid
`PROMOTION_AUTHORIZED` record performs no host action. The existing host gate
has no production caller and is not a complete multi-file CIS Clean deployment
mechanism. Fixing the reviewer receipt alone would therefore still leave
correct work outside the live tree.

The failure was an orchestration and state-semantics failure: activity and
isolated artifacts were repeatedly treated as progress without proving the
next required transition.

---

## 2. Intended lifecycle

The minimum usable CIS development lifecycle is:

```text
remote authenticated operator
  -> Codex Brain deliberation
  -> canonical instruction and frozen task contract
  -> Qwen pre-execution review
  -> bounded Claude/Menter execution
  -> candidate custody
  -> deterministic verification
  -> deterministic independent review
  -> governed Qwen reviewer execution and durable route receipt
  -> promotion decision
  -> governed recoverable host application
  -> post-application verification
  -> runtime activation and health evidence when required
```

Each arrow is a state transition with its own evidence. A later state may not
be inferred from an earlier one.

In particular:

- process exit success is not candidate success;
- candidate creation is not candidate custody;
- candidate custody is not deterministic verification;
- a Workbench Qwen response is not a governed review-route receipt;
- a promotion decision is not host application;
- files present in the tree are not runtime activation;
- a model report is never evidence that any of these transitions occurred.

---

## 3. Verified current state

### 3.1 Live authority database

Read-only queries against `/var/lib/cis-clean/workbench.db` in the running
Workbench container produced:

```text
task_contracts:             56
verification_results:        1
review_results:              0
review_route_receipts:       0
promotion_decisions:         0
reconstruction_candidates:   2

worker_sessions:             0
worker_model_requests:       0
worker_session_events:       0
backend_runs:                2
evidence_records:            2
```

The 56 task contracts target only:

```text
cis.assurance.verifier                 3
cis.execution.adapters.claude_code    40
cis.execution.gateway                 8
cis.workbench.projection               1
cis.workbench.service                  4
```

No recent chain, Menter-service, promotion-storage, interface, or host
orchestration card became a canonical task contract in this live authority
database.

### 3.2 Candidate custody exists

The live database contains two reconstruction-candidate records, for
`cis.execution.adapters.claude_code` and `cis.execution.gateway`.

Production source also contains a real candidate-admission call:

```text
src/cis/workbench/service.py
    self.reconstruction_candidates.admit(...)
```

Therefore the statement “there is no admission path” is too broad. Candidate
custody exists. What does not exist is a connected path from current Menter
work through all assurance stages and into governed host application.

### 3.3 No production route-receipt producer exists

A source search for `record_route_receipt(` found only its definition:

```text
src/cis/assurance/authority.py:788
    def record_route_receipt(...)
```

There is no production caller.

`PromotionRecorder.evaluate` requires the exact review’s verified Qwen route
receipt. With no receipt, it deterministically returns:

```text
PROMOTION_DENIED
QWEN_ROUTE_RECEIPT_NOT_RECORDED
```

This denial is correct behavior. It must not be weakened or bypassed.

### 3.4 The current Qwen path cannot satisfy the receipt writer

The Workbench `HermesReviewer` performs a direct semantic review and returns a
process-local result. It does not create:

- a REVIEWER `worker_sessions` row;
- a `worker_model_requests` row;
- a successful terminal `worker_session_events` row;
- a matching completed `backend_runs` row;
- an admitted `external_model_review_response` evidence record.

`record_route_receipt` requires all of those records and independently binds
them before it appends a receipt.

There is also a protocol-shape disagreement. The current Workbench reviewer
parses and hashes:

```text
{verdict, objections, summary}
```

The assurance route-receipt policy expects response evidence with exactly:

```text
{verdict, objections}
```

The Workbench reviewer and the governed assurance reviewer are therefore not
interchangeable without an explicit, verified adapter design.

### 3.5 Promotion decisions do not apply files

`src/cis/assurance/promotion.py` explicitly records decisions only. Its sole
host-action value is:

```text
NONE_RECORD_ONLY
```

This separation is intentional and correct. It means a receipt producer and
coordinator alone cannot put code into `/mnt/projects/cis-clean`.

`cis.host.promotion_gate.HostPromotionGate` exists, but source search found no
production caller. Its present target behavior is a proof-oriented
single-candidate handoff and not the required recoverable multi-file source
application and deployment lifecycle.

### 3.6 The tree has a checkpoint, but not a clean current history

The branch HEAD remains old and the working tree contains extensive modified
and untracked reconstruction work. A safety checkpoint does exist:

```text
refs/cis-checkpoints/close-assurance-chain-20261029T2115Z
3455266763cce77e5dfd768af1ac092233a1f812
```

That checkpoint preserves a large part of the reconstruction. The later async
Workbench/Menter bridge postdates it and remains outside normal branch history.
The correct description is therefore “partially checkpointed, not reconciled
or committed as the running baseline,” not “committed nowhere.”

---

## 4. What happened

### 4.1 Correct components were built without proving their consumer

Cards were evaluated mainly for boundedness, internal consistency, and safe
execution. Those are necessary properties, but they do not establish that the
new component has a production caller or that its output can enter the next
state.

This allowed multiple “NO CALLER” components to accumulate. Each looked like
progress in isolation while the integrated lifecycle remained unchanged.

### 4.2 Work was dispatched outside canonical task issuance

Several recent cards were authored by Codex, reviewed by Qwen, and sent to
Menter without first being issued through the Workbench instruction path as a
frozen canonical task contract.

The assurance chain is keyed by `task_contract_id`. Work that does not have one
cannot later be represented as an ordinary governed run merely because its
content is useful or its receipt is HMAC-protected.

### 4.3 “Completed” was allowed to mean process completion

At least one Menter job reported completion with no changed files. Other jobs
produced isolated candidates that were never admitted or applied.

The controlling status was allowed to remain `COMPLETED` even when the required
artifact or state transition was absent. This created false progress and made
retrying appear reasonable.

### 4.4 Sequential work was launched without intermediate admission gates

Multiple candidate cards were run in sequence while outputs remained isolated
from one another. Each candidate began from the same live base and could not
see sibling candidate changes.

As a result, separately authored modules invented incompatible interfaces and
event vocabularies. Buffered multi-run orchestration also hid intermediate
failure and allowed additional model expenditure after the first useful stop
condition had already occurred.

### 4.5 A break-glass applier became the only working feedback path

When correct candidate work did not enter the tree, a one-time applier was
built and used to install the async Workbench/Menter bridge.

The applied code appears disciplined and useful, but the application was not
recorded through the candidate, verification, review-receipt, promotion, and
host-application authorities. It was a break-glass deployment and must be
recorded as such.

This did not happen because the governance rule was unknown. It happened
because the governed lifecycle had no functioning completion path and the
break-glass action produced the only visible result. The system rewarded the
bypass.

### 4.6 Artifact existence was reported as system capability

Progress reports counted cards, receipts, candidate files, service restarts,
and code presence. Those facts are evidence of activity. They are not evidence
that the operator can complete a governed development task through the remote
Workbench.

The required end-to-end proof was never produced.

---

## 5. Root causes

### RC1 — No single production lifecycle owned all transitions

No component or explicitly staged operator procedure enforced the complete
ordered path from task issuance through post-application verification.

### RC2 — Completion semantics were defined at the wrong level

Worker completion, candidate completion, assurance completion, promotion, and
application were not presented as separate states. “Completed” became an
ambiguous and misleading terminal label.

### RC3 — Qwen was integrated twice under incompatible contracts

The Workbench semantic reviewer is useful for pre-Menter and candidate advice.
The assurance policy requires a governed REVIEWER worker execution with durable
request, run, evidence, and session facts. The former was treated as if it
could satisfy the latter, but no binding adapter or persisted lifecycle exists.

### RC4 — The promotion decision/application boundary was overlooked

Attention focused on satisfying `PromotionRecorder`. That recorder
deliberately performs no host action. No production multi-file application
path was ready behind it.

### RC5 — Card review did not include downstream reachability

`pre_menter_card` review answered whether a directive was bounded and safe.
It was not given the call graph, prerequisite state, output consumer, or
admission mechanism needed to determine whether the card closed the claimed
architectural gap.

### RC6 — Orchestration optimized for activity rather than state transition

Large cards, sequential candidate batches, retries, and fragmented tasks were
used to maintain momentum. None was conditioned on proof that the previous
output had entered its next required state.

### RC7 — The live baseline was not made a durable return point before expansion

The reconstruction accumulated on an old branch HEAD. A checkpoint mitigates
loss, but the running image, working tree, authority database, and ordinary Git
history are not reconciled as one declared baseline.

---

## 6. Contributing model and process behavior

- Claude spent long execution windows analyzing complex cards before making
  edits, causing timeouts and high subscription use.
- Independent candidates could not share unpromoted sibling interfaces, so
  decomposition without landing between steps increased incompatibility.
- Qwen correctly reviewed the packets it received, but those packets asked a
  narrower question than the architectural decision required.
- Codex repeatedly selected additional implementation work before proving the
  current vertical slice.
- The Workbench UI exposes candidate creation and semantic review but not the
  later deterministic assurance and application states, allowing partial
  functionality to look like a complete pipeline.
- Hidden or buffered sequential scripts reduced operator visibility and delayed
  the stop decision.

These are contributing factors. They do not replace the structural root causes.
A robust CIS must make the safe state transition deterministic even when model
behavior is imperfect.

---

## 7. Status of the preserved work

### Usable baseline, with governance debt

- The remote Cloudflare-accessed Workbench is live.
- Codex Brain profile selection and chat are live.
- The asynchronous Menter job bridge is installed and has disciplined
  idempotent submission and polling behavior.
- The boot-managed Brain, Menter, and reviewer services exist.

The async bridge was applied through break-glass rather than the assurance
path. Its code should not be discarded, but its provenance must be recorded and
it must later be re-accepted or re-derived through the completed lifecycle.

### Preserved evidence, not accepted implementation

- fixture-fix candidates;
- migration 0017 candidates;
- reconstruction-promotion plan candidate;
- reconstruction-promotion orchestration candidate;
- Menter receipts and sealed candidate workspaces.

These artifacts must remain immutable recovery sources. Hash preservation
proves their bytes, not their architectural correctness or compatibility.

### Known incompatibilities

The promotion candidates are not one ready implementation:

- one plan uses `PLANNED` and `FILE_OBSERVED`;
- the corrected migration uses `FILE_APPLIED` and `FILE_ROLLED_BACK`;
- the orchestration imports a filesystem module that was never produced;
- it expects constants and database fields not supplied by the sibling
  candidates;
- one “completed” card produced no changed files.

They must not be merged, promoted, or rerun as a batch.

---

## 8. Corrected recovery sequence

The following order closes the actual lifecycle. A later step must not start
until the preceding step has produced its declared evidence.

### R0 — Freeze and reconcile the return point

1. Inventory the working tree and untracked files for credentials and secrets.
2. Record the checkpoint ref, branch HEAD, running image digests, deployed file
   digests, authority database identity, and break-glass-applied files.
3. Create a reviewed durable baseline without silently normalizing the
   break-glass application into governed promotion.
4. Quarantine the stranded candidate workspaces as recovery evidence.

Exit evidence: one declared baseline mapping Git, images, database, services,
and known break-glass deltas.

### R1 — Define and enforce closed lifecycle states

Use separate public states at minimum:

```text
ISSUED
PRE_REVIEW_PASSED
EXECUTION_RUNNING
CANDIDATE_ADMITTED
VERIFIED_PASS | VERIFIED_FAIL
DETERMINISTIC_REVIEW_PASS | OBJECTIONS
QWEN_RECEIPT_ADMITTED | QWEN_RECEIPT_REFUSED
PROMOTION_AUTHORIZED | PROMOTION_DENIED
APPLICATION_PLANNED
APPLIED | ROLLED_BACK | APPLICATION_FAILED
POST_APPLY_VERIFIED | POST_APPLY_FAILED
```

Zero changed files when a change is required must be a typed failure before
candidate success. No generic `COMPLETED` state may substitute for a later
state.

Exit evidence: deterministic state-transition tests and Workbench projection
of the same states.

### R2 — Build the governed Qwen assurance-review route

Do not merely wrap the current process-local `HermesReviewer` response.

The route must:

1. create a governed REVIEWER worker session under the registered
   `openrouter_qwen_reviewer` adapter;
2. issue one worker-model request bound to the exact deterministic review
   packet and response schema;
3. execute Qwen through Hermes/OpenRouter with backend reasoning tokens fixed
   at zero;
4. record the completed backend run and exact response evidence;
5. record one successful terminal worker-session event;
6. assemble the receipt only from those durable facts;
7. call the existing sanctioned `record_route_receipt` writer;
8. prove that the verified stored receipt reads back for the exact review.

Do not weaken `record_route_receipt`, synthesize prerequisite rows, or add a
second receipt table.

Exit evidence: one real Qwen request whose worker request, session event,
backend run, evidence record, receipt, and read-back all cross-bind.

### R3 — Connect candidate assurance deterministically

For one admitted reconstruction candidate:

1. run the deterministic Verifier over the exact admitted candidate;
2. run the deterministic Reviewer over that exact verification result;
3. run R2’s governed Qwen route over the exact recorded review packet;
4. call `PromotionRecorder.decide` once;
5. accept either an authorized decision or a correctly reasoned denial as a
   successful execution of the coordinator.

The coordinator may initially be an internal CLI. It must not perform model
execution itself, weaken independence, or apply files.

Exit evidence: one task contract with a complete, queryable conjunction and a
recorded promotion decision.

### R4 — Complete governed multi-file host application

Design from the existing `HostPromotionGate`, migration 0016 candidate
custody, and the actual multi-file candidate envelope. Do not automatically
adopt migration 0017 or the stranded promotion modules.

The application boundary must:

- require a recorded `PROMOTION_AUTHORIZED` decision;
- retrieve exact admitted candidate bytes through sanctioned custody;
- validate every path against the task contract;
- bind the whole multi-file plan and prior file digests before writing;
- use atomic per-file replacement under a recoverable application plan;
- record application-wide and per-file events under one vocabulary;
- support deterministic interruption recovery and rollback;
- never target `/mnt/projects/cis`;
- target only `/mnt/projects/cis-clean` under explicit authority;
- perform no model call and make no assurance decision;
- verify final bytes before reporting `APPLIED`.

Exit evidence: a reversible multi-file canary applied to a sealed CIS Clean
test target, interrupted at defined points, recovered, and rolled back with
all digests and events verified.

### R5 — Prove one real remote vertical slice

Through the Cloudflare-accessed Workbench:

1. select the explicit Codex Brain profile;
2. deliberate on one tiny real CIS change;
3. issue the instruction through the Card Factory;
4. obtain Qwen pre-review PASS;
5. run Claude/Menter once;
6. admit a nonempty candidate;
7. run deterministic verification and deterministic review;
8. admit the governed Qwen route receipt;
9. record the promotion decision;
10. apply through R4;
11. verify the live bytes and relevant service/runtime health;
12. display every state and evidence identifier in the Workbench.

No automatic retry. On failure, stop at the first missing or contradictory
transition and repair that transition only.

Exit evidence: one operator-visible run from remote instruction to verified
live result, with no direct host edit and no break-glass action.

### R6 — Recover valuable stranded work individually

For each preserved candidate:

1. determine whether the capability is still required;
2. compare it against the now-complete lifecycle and existing mechanisms;
3. reject duplicates and incompatible designs;
4. issue a new canonical task only when implementation work remains necessary;
5. use preserved bytes as reviewed recovery input where policy allows;
6. run one candidate at a time through R5’s proven path.

Do not rerun Claude solely to reproduce already-correct bytes. Do not represent
an old hand-authored card receipt as a canonical task-contract binding.

---

## 9. Rules preventing recurrence

1. **Every card names its consumer and landing path.** A card must identify the
   exact production caller, next state, sanctioned writer, and verification of
   that transition.
2. **No card without a canonical task contract.** Ordinary implementation work
   begins only after Workbench issuance produces the frozen contract and card.
3. **One job, one visible result, one decision.** Never hide multiple model runs
   behind a buffered sequential script or one approval.
4. **Verify required outputs before the next dispatch.** Required changed paths,
   candidate bytes, and hashes are deterministic postconditions.
5. **Zero required output is failure.** Process exit success cannot override a
   missing artifact.
6. **Denial is a valid terminal result.** A correct fail-closed reason code is
   evidence that governance worked, not permission to route around it.
7. **Review reachability, not only card safety.** Gap-closing review packets must
   include the prerequisite state, call path, output consumer, and exact proof
   that the claimed gap will close.
8. **No new mechanism beside a correct existing one.** First identify whether a
   sanctioned writer, authority, gate, or recovery path already exists.
9. **Candidate hashes prove identity, not correctness.** Preserved work remains
   unaccepted until its interfaces, authority, verification, and integration
   pass.
10. **Root access is private break-glass only.** Credentials are entered only in
    a private terminal prompt. Every break-glass action is narrowly scoped,
    recorded, and never described as ordinary governed promotion.
11. **No live-tree claim without live-tree evidence.** “Working” requires exact
    file digests, authority records, runtime health, and when applicable a
    browser-visible result.
12. **Do not advance on self-report.** Model summaries are advisory. State comes
    from the filesystem, database, endpoint, service, and independent review
    evidence.

---

## 10. Completion definition for Queue 4.37

Queue 4.37 contained-pipeline readiness is not complete merely because its
components exist in an image or because a candidate can be produced.

It is complete only when one real remote Workbench task demonstrates:

```text
explicit Brain identity
+ canonical task issuance
+ independent Qwen pre-review
+ bounded Menter execution
+ nonempty candidate custody
+ deterministic verification
+ deterministic independent review
+ governed Qwen route receipt with reasoning_tokens = 0
+ recorded promotion decision
+ governed recoverable CIS Clean application
+ post-application evidence
+ operator-visible status for every stage
```

No direct edit, manual copy, hidden retry, synthetic receipt, or unrecorded
host action may be part of that proof.

---

## 11. What was learned

The project does not need more governance concepts before it can proceed. It
needs the existing concepts connected into one minimal, observable lifecycle.

The failure was not that CIS constrained the models too much. The failure was
that constraints were implemented as disconnected components while the only
path that changed the live system remained outside them.

The recovery principle is therefore simple:

> Do not build the next component until the current component’s output has
> deterministically entered its next required state.

Applied consistently, that rule preserves useful work, stops unnecessary model
spend, exposes the exact blocker early, and allows CIS Clean to become the
environment through which CIS develops itself.
