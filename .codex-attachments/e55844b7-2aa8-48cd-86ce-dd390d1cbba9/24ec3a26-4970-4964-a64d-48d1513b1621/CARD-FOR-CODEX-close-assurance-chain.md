# CARD — CIS Clean: Close the Assurance Chain

## ROLE

Act as managed-job author. Produce **one bounded managed execution-job
specification** for Eric's approval, covering the remediation scope defined in
section 4 of this card.

Do not implement anything. Do not repair, promote, rebuild, restart, commit, or
call mutating endpoints. Your output is a job spec, not a change.

This card supplies findings that were already derived from the tree. **Re-derive
each one with the command given** — do not confirm it from this card's text, and
do not characterise a subset measurement as a whole-tree result. Where your
re-derivation disagrees with this card, report the disagreement with its
command output; do not silently adopt either number.

## 1. ANCHOR

| | |
|---|---|
| Repository | `/mnt/projects/cis-clean` |
| HEAD | `588f4c98b2f72021d2f0ec8139c2d352b243d74f` |
| Branch | `wip/queue-4.37-controller-integration-2026-10-20` |
| Protected reference (do not modify) | `/mnt/projects/cis` |
| Live workbench | `deploy-workbench-1`, `127.0.0.1:8099`, restarts 0 |
| Live brain worker | `deploy-brain-worker-1`, restarts 0 |
| Reviewer relay | `127.0.0.1:8653`, `cis-clean-reviewer-relay.service` |

All findings below were observed at this HEAD on 2026-10-29.

## 2. THE PRIMARY FINDING — the chain has no production caller

**The assurance chain is complete as components and unreachable as a path.**
Three consecutive links have no production caller outside the recovery module.

Reproduce (run each from `/mnt/projects/cis-clean`):

```bash
# Link 1 — the deterministic verifier
grep -rn "from .verifier import Verifier\|from cis.assurance.verifier import Verifier" src/ tests/ --include=*.py | grep -v pycache

# Link 2 — the review route receipt writer
grep -rn "record_route_receipt" src/ tests/ --include=*.py | grep -v pycache | grep -v "^src/cis/assurance/authority.py"

# Link 3 — the promotion decision
grep -rn "PromotionRecorder" src/ tests/ --include=*.py | grep -v pycache
```

Expected result:

| Link | Production callers | Test callers |
|---|---|---|
| `Verifier.verify` | `src/cis/assurance/recovery_execution.py:52` only (plus a lazy re-export at `src/cis/assurance/__init__.py:12`) | 7 test modules |
| `ReviewerFacade.record_route_receipt` | **none** | `tests/support.py:568`, `tests/test_review_route_authority.py:240,270,300` |
| `PromotionRecorder.decide` | `src/cis/assurance/recovery_execution.py:168` only (plus re-export at `__init__.py:21`) | 3 test modules |

### Why this is the block

- `POST /instruction` works. On an `ALLOW` verdict with
  `scope.operation == "reconstruct_module"`, `src/cis/workbench/service.py:825`
  calls `reconstruction_issuance.issue(...)`, which **freezes the task contract
  and emits the canonical task card**. This step is built and reachable.
- `POST /menter/runs` works and produces HMAC'd receipts. Every receipt hardcodes
  `"promotion": "NONE"` (`src/cis/menter/service.py:240,267,302,329`) and line
  `438` **refuses** any payload where `promotion != "NONE"`. The same refusal is
  at `src/cis/execution/adapters/claude_code.py:483-485`. The Menter path is
  structurally incapable of promoting.
- `POST /reviewer/reviews` works — read-only semantic review.
- **Then nothing.** No route and no CLI subcommand (`cis verify|demo|serve|
  menter-run`, see `src/cis/__main__.py:384-418`) reaches the verifier, the route
  receipt writer, or the promotion recorder.

`PromotionRecorder.evaluate` (`src/cis/assurance/promotion.py:94-156`) is a
correct fail-closed conjunction. Because nothing writes the rows it requires, a
promotion decision on a normally-issued task contract denies with
`VERIFICATION_NOT_RECORDED` (`promotion.py:56`). Permanently, by construction.

The only production module that drives the full chain is
`recovery_execution.py`, whose entry condition is a **verified objection** — an
already-recorded failure. So the chain can presently only run *after* something
has failed, and never on a first pass.

**Consequence to state plainly in the job spec:** no sequence of calls to the
live API can produce `PROMOTION_AUTHORIZED`. This is why no end-to-end run has
ever been performed. It was not neglect and not a stale candidate.

### The deliberate exclusion you must address, not bypass

`src/cis/interface/api.py:121-127` states the exclusion as intentional:

> "The assurance increment is reachable from here through its READ MODEL only.
> The compiler, the authority facades, the verifier, the reviewer and the
> promotion recorder are deliberately absent from this surface: freezing,
> verifying, reviewing and promoting are privileged in-process seams in this
> increment, exactly as evidence admission is, and a route that reached one of
> them would be a route that could manufacture assurance on request."

Your job spec must carry this quotation and name overriding it as an explicit
decision for Eric, not an implementation detail. **Do not delete or weaken that
docstring without recording the decision.**

### Independent review already obtained on the proposed remedy

A read-only Hermes Review1 pass (`qwen/qwen3.7-max` via OpenRouter, reasoning
tokens 0) was run through the live `POST /reviewer/reviews` route on the
proposed remedy described in section 4, Task A.

| | |
|---|---|
| Verdict | **PASS**, zero objections |
| `generation_id` | `chatcmpl-47f39a4fd4ca4aa39fc209cd6a5fa` |
| `packet_sha256` | `ca986ba1b7e2638e94334ba16a5dd2f7fdab5c22496a4551373b58a571bfd886` |
| `response_sha256` | `3a6cb68deffcd67eb5425adfe972a3ce7dc90937ed45633b21ec4eb8fe21fb90` |
| Role | `hermes-r1` |

It found the safety argument holds "because the new module supplies no verdict
or evidence of its own; authorization remains derived solely from `evaluate()`
over recorded rows with hash bindings, and every write is validated by the
component that performs it," and ruled that whether the route contradicts the
`api.py` stance "is a design choice, not a material defect."

**Limits of that review, to be restated in the job spec:** it was a semantic
review of a *proposal*, not deterministic verification of an implementation; it
reviewed only the evidence in the submitted packet and ran no independent
greps; and its `review_kind` was not one of the reviewer's known stages, so its
summary refers to `pre_menter_card` framing. It does not substitute for the
post-implementation review the new path will itself produce.

## 3. SECONDARY FINDINGS

Each is real and none of them is the primary block. Do not reorder them ahead of
Task A.

**3.1 — No application-layer authentication on the live console.**

```bash
grep -nE "check_auth|Depends|Authorization|api_key|authenticate" src/cis/interface/api.py   # returns nothing
```

Eight POST routes are exposed with no in-application check: `/instruction`
(creates authority), `/execute` (dispatches backend work), `/menter/runs` and
`/reviewer/reviews` (spend model budget), `/brain/sessions/{start,turn,close}`,
and `/brain/profiles/sign-in` (initiates an OAuth flow against Eric's ChatGPT
account and writes a credential — a third category, neither authority nor
spend). `workbench.creative-intelligence-system.com` routes to
`http://127.0.0.1:8099` through a live `cloudflared` tunnel, so these are
internet-reachable.

The sole control is Cloudflare Access, recorded as default-deny with a
two-user allow policy. **That could not be verified from the host** and must be
confirmed in the Cloudflare dashboard. The older `cis-pipeline` container gained
a fail-closed in-application check (`runtime/workbench_auth.check_auth()`) at
revision 127; cis-clean has no equivalent. There is no defense in depth.

**3.2 — Uncommitted tree.** `git status --porcelain` returns 181 entries: 31
modified tracked files (`git diff --stat`: 3,655 insertions, 142 deletions) and
150 untracked. There is no return point before any image rebuild or service
restart.

**3.3 — The test-suite failures are a fixture, not runtime.** The large failure
cluster terminates in `tests/support.py` at `freeze_task_contract()`, which
reuses a single authorization to freeze contract after contract. The current
invariant correctly refuses the second freeze, because one `ALLOW` authorizes
exactly one attempt. That is the architecture working. The helper is called from
181 sites across `tests/`, which is why one defect presents as a large count.
**The count itself must be re-derived** — the figure carried forward (137 failing
of 1,451: 19 failures, 118 errors) was a timestamped observation on a suite that
has drifted 1,353 → 1,446 → 1,451 over six days. Report what the full suite does
now; do not confirm that number, and do not report a focused subset as the
whole-tree result.

**3.4 — No asynchronous Menter job bridge.** `grep -rn "menter/jobs" src/`
returns nothing. `POST /menter/runs` is synchronous and blocks the caller; a job
cannot be fired and polled. The async bridge exists only in the preserved,
unadmitted candidate.

**3.5 — The preserved candidate's base is probably stale.** Candidate
`menter-e468adf81a5a4078a9957c0c7e874410` captured its base 2026-10-27 18:15;
the host tree has moved since. Expect admission to come back BLOCKED on base
mismatch. That blocks the candidate, not the pipeline. The candidate workspace
is mode `0555` and its receipt carries an HMAC with `base_sha256`,
`candidate_sha256`, `card_sha256` and per-file digests — **do not rerun the
implementation worker or modify the candidate.**

Note an ordering collision: the candidate modifies
`src/cis/interface/api.py` — the same file an in-application auth check would
touch, and the same file Task A adds a route to. Three changes converge on one
file. The job spec must sequence them deliberately.

## 4. REMEDIATION SCOPE FOR THE JOB SPEC

Produce a spec with these tasks, in this order, each with its own acceptance
test and its own stop condition.

**Task 0 — establish a return point.** Commit or tag the current tree before any
mutation, and name the rollback path. No later task may run until this is done.
Blocking.

**Task A — the chain join. The job's purpose.** Add one production module, and
one surface reaching only it, that for a normally-issued `task_contract_id`:

1. requires the task contract via `ledger.require_task_contract`;
2. calls the existing `Verifier.verify` to produce and record the deterministic
   verification result;
3. submits the post-implementation review packet to the configured
   `HermesReviewer` and records the review bound to that verification result;
4. calls the existing `ReviewerFacade.record_route_receipt`
   (`src/cis/assurance/authority.py:788`) binding `review_id`,
   `verification_result_id` and the review packet hash;
5. calls `PromotionRecorder.decide(task_contract_id)` and returns the recorded
   decision verbatim.

Out of scope, and the spec must say so: no change to
`PromotionRecorder.evaluate` or its conjunction; no change to `Verifier`,
`HermesReviewer`, or `record_route_receipt` validation; no new authority, verdict,
bypass, or override parameter; no host action — the decision is recorded, acting
on it stays the host's separate concern; no change to the Menter
`promotion: "NONE"` invariant.

The spec must decide and record **one** open question: whether the surface is an
HTTP route on the workbench API, or a CLI subcommand only. A route widens the
internet-reachable surface described in 3.1 and interacts with the `api.py`
exclusion; a CLI subcommand does not, and is sufficient for a first end-to-end
run. **Recommend the CLI subcommand first** and name the route as a follow-on,
so Task A does not depend on resolving Task B.

**Task B — decide the auth posture.** Either add a fail-closed in-application
check to cis-clean mirroring revision 127, or confirm Cloudflare Access is
enforcing and record it as the sole control so it stops being invisible. A
decision either way is acceptable; leaving it undecided is not. If Access cannot
be verified, the spec must emit an **interim containment recommendation as an
immediate action for Eric** — not folded in among other decisions — because the
exposure stays live while any of this runs.

**Task C — fix the test fixture.** Repair `freeze_task_contract()` in
`tests/support.py` so each frozen contract carries its own authorization. One
helper. **Do not propose individual repairs at the call sites.** Re-derive the
full-suite count before and after.

**Task D — first end-to-end run.** Using Task A's surface, drive one real chain:
instruction → card issuance → Menter implementation → verification → review →
route receipt → promotion decision. Report the recorded decision and
`reason_code` verbatim, whatever it is. A `PROMOTION_DENIED` with a correct
reason code is a successful run of the path and must be reported as such — not
retried, widened, or worked around.

**Task E — durable record.** The outcome lands as a `dev_continuity_events`
revision and a queue item, not only as a document. State this as a requirement:
this project's characteristic failure is work that was never written to an
authority a derived view reads — which is how the SWA project went invisible for
months.

## 5. EXPLICITLY DEFERRED — name these, do not build them

These are unbuilt subsystems, not defects. Folding new construction into a
remediation job is how prior jobs drifted. The spec must list them as deferred
with these reasons, so nothing is lost.

- **Card Runner / autonomous orchestration.** `card_factory.projection` builds a
  canonical card from a frozen task contract, but nothing turns a Brain
  objective into a dispatched card on its own. Card Runner is a recovered design
  concept, not confirmed built. This is the real missing automation and the
  reason cards have been hand-fed all week. It is a separate build.
- **OSA-BR (queue 4.36)** — the operational event/evidence contract, failure
  taxonomy and maintenance-incident state machine. `assurance.recovery`,
  `recovery_attempt`, `recovery_execution` and `worker_supervisor` are all built;
  what is missing is the layer that would *notice* a failure, classify it, and
  invoke recovery. Until it exists, recovery is a mechanism a human reaches for.
  Separate build.
- **Async `/menter/jobs`** (3.4) — lives in the unadmitted candidate; depends on
  the candidate decision, which depends on the base mismatch in 3.5.
- **Candidate admission** (3.5) — gate on Task 0 and on the `api.py` ordering
  collision.
- **Multi-user permissioned platform.** CIS today is a single local operator on
  loopback with no caller identity, and the manifest defers security trust
  boundaries deliberately. That is an architectural step, not an increment.
  Nothing in this card narrows it.

## 6. WHAT THE JOB SPEC MUST NOT DO

- Must not attribute pre-existing containers to any job's work. Both containers
  predate the last several dispatches; `deploy-workbench-1` has restarts 0.
- Must not report a focused test subset as a whole-tree result.
- Must not treat code presence in an image as executable capability.
- Must not rerun the implementation worker or modify the preserved candidate.
- Must not mutate anything before Task 0 records a return point.
- Must not widen beyond section 4. Items in section 5 are deferred by decision.

## 7. STOP CONDITIONS

Halt and return to Eric rather than proceeding if:

- Task 0 cannot establish a return point.
- Cloudflare Access cannot be verified **and** no interim containment has been
  decided. Inability to verify Access blocks any claim that the public path is
  safe.
- Task A cannot be implemented without modifying `PromotionRecorder.evaluate`,
  `Verifier`, `HermesReviewer`, or `record_route_receipt` validation. If the
  conjunction must change, that is a different card.
- Re-derivation materially contradicts section 2's call-site table. That table is
  the card's foundation; if it is wrong, stop rather than build on it.

## 8. ACCEPTANCE

The job spec is acceptable when: every finding in sections 2 and 3 is
independently re-derived with output shown; Task A is specified to the level of
named modules and functions with its surface decision recorded; Tasks B through
E each carry an acceptance test and a stop condition; section 5 is reproduced as
deferred scope; and the whole thing is bounded enough that Eric can approve or
refuse it in one read.

Return the spec. Do not execute it.
