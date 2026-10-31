# CARD — CIS Clean: Every Arrow to an Autonomous Contained Pipeline

Anchor: `/mnt/projects/cis-clean`, HEAD `588f4c98b2f72021d2f0ec8139c2d352b243d74f`,
branch `wip/queue-4.37-controller-integration-2026-10-20`, observed 2026-10-29.

This card replaces the earlier `CIS-CLEAN-ASSURANCE-CHAIN-JOIN-2026-10-29` card,
which described **one** of the steps below (Step 4) in a way that could be read
as the last step needed. It is not. It is one of fifteen.

---

## HOW TO READ THIS — status vocabulary

Every step carries exactly one status. Nothing is described as working unless a
route or command that reaches it is named.

| Status | Meaning |
|---|---|
| **REACHABLE** | Built, and an HTTP route or `cis` subcommand reaches it. You can use it today. The route is named. |
| **NO CALLER** | The code is written and tested, but no route, no subcommand, and no production module invokes it. You cannot reach it. Test files and `tools/prove_*.py` scripts do not count as a caller. |
| **NO PRODUCER** | Something requires this input, and nothing anywhere writes it. Strictly worse than NO CALLER: the chain is not merely unreachable, it is blocked. |
| **NOT BUILT** | The module or function does not exist. |

**NO CALLER does not mean nearly done.** It means the join is missing, and the
join is the work. Four separate components in this system are NO CALLER, and
their existence has repeatedly been reported as the pipeline being nearly
operational. It is not the same thing.

---

## THE ROOT CAUSE — found 2026-10-29, not previously recorded

The pipeline is not blocked because the assurance machinery was never built. It
is blocked because **a requirement was added to the working tree without the
thing that satisfies it.**

```bash
# At the committed HEAD, the promotion conjunction has three members:
git show HEAD:src/cis/assurance/promotion.py | grep -oE "REASON_[A-Z_]+ ="
#   -> 8 reason codes. No route-receipt codes.

# The uncommitted working tree adds a fourth member:
git diff --stat src/cis/assurance/promotion.py
#   -> 55 insertions. Adds QWEN_ROUTE_RECEIPT_NOT_RECORDED and three siblings.

# Nothing in production writes what the new member requires:
grep -rn "record_route_receipt" src/ --include=*.py | grep -v pycache \
  | grep -v "^src/cis/assurance/authority.py"
#   -> no results.
```

`PromotionRecorder.evaluate` in the working tree requires a Qwen review route
receipt bound to the exact review. `ReviewerFacade.record_route_receipt`
(`src/cis/assurance/authority.py:788`) is the only sanctioned writer of that
receipt and it has **zero production callers**. So every promotion decision on
the normal path denies with `QWEN_ROUTE_RECEIPT_NOT_RECORDED`, permanently.

**The running container has the same change.** Verified inside
`deploy-workbench-1` at
`/usr/local/lib/python3.12/site-packages/cis/assurance/promotion.py`: the
route-receipt member and both reason codes are present. So the image was built
from the uncommitted tree, not from HEAD. The container cannot promote either.

**Why this matters for how you read past reports.** At HEAD,
`tools/prove_authored_source_pipeline.py` (88 lines, last touched 2026-10-20,
commit `7e1fdf4`) drives instruction → freeze → contained run →
`Verifier.verify` → `Reviewer.review` → `PromotionRecorder.decide` and asserts
`decision == "PROMOTION_AUTHORIZED"` with `host_action == "NONE_RECORD_ONLY"`.
That is the "autonomous record-only promotion" the README line at `README.md:23`
refers to. It is a **proof program**, run by hand against a fresh throwaway
authority database, for the `verify_authored_source.v1` path only. It is not the
operational pipeline and it never was. Whether it still passes at HEAD today is
**unverified** — it needs a contained worker image and I did not run it.

---

## SHORTCUTS THAT ALREADY EXIST — read before starting any step

**Three steps are a lift, not a build.** `tools/prove_*.py` are not throwaway
demos. They take `--authority <real path>` and `--output`, not in-memory
databases, and they drive the real components in the real order:

| Script | Lines | Drives | Serves |
|---|---|---|---|
| `prove_authored_source_pipeline.py` | 88 | instruction → freeze → contained run → verify → review → promote | **Step 4** |
| `prove_recovery_pipeline.py` | 176 | recovery + recovery_attempt + recovery_execution → verify → review → promote | **Step 13** |
| `prove_worker_supervision.py` | 372 | supervision plan / route / start / checkpoint / finish | **Step 14** |
| `prove_contained_worker.py` | 308 | the contained worker adapter | Step 6 reference |

Step 4's coordinator does not need designing. 88 lines already do nearly all of
it; what is missing is the route receipt insert (Step 3) and a `cis` subcommand
wrapper. Treat these as proven semantics to lift into `src/`, not as prior art
to reimplement — and do not delete the proof scripts, which remain the only
independent check that the lifted code still behaves.

**The two reviewers are different things.** Conflating them will build the
wrong thing in Step 3:

- `cis.assurance.reviewer.Reviewer` — **deterministic**; records a review via
  `facade.record_review` (`reviewer.py:603`)
- `cis.reviewer.hermes.HermesReviewer` — **Qwen over OpenRouter**; returns a
  receipt and records nothing

The promotion conjunction needs **both**: the recorded deterministic review,
*and* a route receipt binding that review's `review_id` to the Qwen result for
the same packet hash. Step 3 is the bridge between two different reviewers.

**The subcommand pattern is already worn in.** `cmd_demo`
(`src/cis/__main__.py:172-262`) constructs Workbench + Conductor + WorkbenchApi
in-process and walks eleven steps; registration is at lines 384-418. Copy its
guard too: it refuses to run against a non-empty authority rather than printing
narration that would be false.

**There is a ready-made end-to-end job.** `pilot/SPEC.md` plus
`pilot/run_verification.py` is a canonical sample task (`parse_duration`) whose
harness treats a zero-test run or an unimportable module as a **HARNESS
FAILURE** rather than a pass. The first real end-to-end run needs no invented
task, and the harness will not let a vacuous success through.

**A daemon is already running.** `src/cis/brain/codex_app_server.py` is one of
only three continuous processes and already parses `DeliberationResult`. Steps
7-11 orchestration probably belongs there rather than in a new daemon —
extending a process that already runs and already speaks the right type beats
introducing a sixteenth component with no caller.

---

## THE FIFTEEN STEPS

Dependency-ordered. Each is one card. Do not merge two steps into one card: the
reason this list exists is that merged steps are what produced the misleading
status reports.

---

### STEP 0 — Commit the tree and reconcile the running image

**Status: NOT BUILT** (this is housekeeping, not code)

What is true now: `git status --porcelain` returns 181 entries — 31 modified
tracked files (3,655 insertions, 142 deletions) and 150 untracked. The running
image contains changes that are not committed anywhere. There is no return
point before any rebuild or restart, and no way to reproduce what is running.

Missing: a commit or tag, and a recorded statement of which commit the running
image corresponds to.

**Done when:** HEAD contains the route-receipt change; a tag names the
pre-existing state; and a recorded note states the image digest and the commit
it was built from. Before committing, inventory the 150 untracked files for
secrets — none may enter the snapshot.

**Depends on:** nothing. Nothing else in this list is safe or reproducible
until this is done.

---

### STEP 1 — Authentication, before anything runs unattended

**Status: NOT BUILT**

What is true now: `grep -nE "check_auth|Depends|Authorization|api_key|
authenticate" src/cis/interface/api.py` returns **nothing**. Eight POST routes
have no application-level check: `/instruction` (creates authority), `/execute`
(dispatches backend work), `/menter/runs` and `/reviewer/reviews` (spend model
budget), `/brain/sessions/{start,turn,close}`, and `/brain/profiles/sign-in`
(initiates an OAuth flow against your ChatGPT account and writes a credential).
`workbench.creative-intelligence-system.com` routes to `127.0.0.1:8099` through
a live `cloudflared` tunnel, so these are internet-reachable.

The sole control is Cloudflare Access, recorded as default-deny with a two-user
allow policy. **That could not be verified from the host** — confirm it in the
Cloudflare dashboard. The older `cis-pipeline` container gained a fail-closed
in-application check (`runtime/workbench_auth.check_auth()`) at revision 127;
cis-clean never inherited it.

**Done when:** either a fail-closed in-application check exists, or Access is
confirmed enforcing and recorded as the sole control. A loop that runs
unattended behind an unverified control is the one combination on this list that
is actively unsafe.

**Depends on:** nothing — which is why it is first.

**Gates:** Step 14. A supervising loop must never run unattended behind an
unverified control. This is also the only item on the list that is a live risk
*today*, before anything else is built, because the eight routes above are
internet-reachable right now.

---

### STEP 2 — Fix the test fixture so test signal means something

**Status: NOT BUILT** (the defect is live; the fix does not exist)

What is true now: the large failure cluster in the suite terminates in
`tests/support.py` at `freeze_task_contract()`, which reuses a single
authorization to freeze contract after contract. The current invariant
correctly refuses the second freeze, because one `ALLOW` authorizes exactly one
attempt. **That is the architecture working.** The helper is called from 181
sites across `tests/`, which is why one defect presents as a large count.

```bash
grep -rn "freeze_task_contract(" tests/ --include=*.py | wc -l   # -> 181
```

Missing: a corrected helper in which each frozen contract carries its own
authorization. **Do not propose individual repairs at the 181 call sites, and
do not weaken the production invariant to make the fixture pass.**

Re-derive the full-suite count before and after. The figure carried in earlier
reports — 1,451 tests with 19 failures and 118 errors — was a timestamped
observation on a suite that drifted 1,353 → 1,446 → 1,451 over six days. Report
what the suite does now; do not confirm that number, and never report a focused
subset as a whole-tree result.

**Done when:** `freeze_task_contract()` gives every frozen contract its own
authorization; the full suite is re-run through the project's own runner and the
before and after counts are both recorded alongside the exact command that
produced them; and no production invariant, conjunction or assertion was
weakened to get there.

**Why this is early rather than cleanup:** until it is fixed you cannot
distinguish a real regression from fixture noise, so every later step's
verification is unreliable. It is a prerequisite for trusting the other
thirteen, not a tidy-up.

**Depends on:** Step 0.

---

### STEP 3 — Write the Qwen route receipt producer

**Status: NO PRODUCER** — this is the actual block

What exists: `ReviewerFacade.record_route_receipt`
(`src/cis/assurance/authority.py:788`, inserting into `review_route_receipts` at
line 1003), migration `0015_review_route_receipts.sql`, and the validator
`verify_stored_route_receipt_row` (`src/cis/assurance/review_route.py:442`).
The receipt must bind `task_contract_id`, `verification_result_id`, `review_id`
and `review_packet_hash`, with verdict PASS and no objections.

Missing: any production code that calls it. The only callers are
`tests/support.py:568` and `tests/test_review_route_authority.py`.

**Done when:** a production module takes a recorded review plus the Qwen
`HermesReviewer` result for that exact review packet and records a route
receipt through `record_route_receipt`, and `verified_route_receipt_for_review`
returns it. No change to the validator. No synthetic receipt.

**Depends on:** Step 0.

---

### STEP 4 — Join verification, review, receipt and promotion into one coordinator

**Status: NO CALLER** for every link in the chain

What exists, and where its only callers are:

| Component | Location | Production callers |
|---|---|---|
| `Verifier.verify` | `src/cis/assurance/verifier.py` | `recovery_execution.py:52` only |
| `Reviewer.review` | `src/cis/assurance/reviewer.py:595-620` | `recovery_execution.py` and `tools/prove_*.py` only |
| `record_route_receipt` | `authority.py:788` | **none** (Step 3) |
| `PromotionRecorder.decide` | `promotion.py` | `recovery_execution.py:168` only |

Missing: a coordinator that runs them in order on a normally-issued
`task_contract_id`, and a `cis` subcommand that invokes it. `src/cis/__main__.py`
registers only `verify`, `demo`, `serve` and `menter_run` (lines 384-418) — none
of them reach the assurance chain.

**Done when:** `cis <subcommand> --task-contract <id>` runs verification →
review → route receipt → promotion decision and prints the recorded decision
and `reason_code` verbatim. **A `PROMOTION_DENIED` with a correct reason code is
a successful run of this step.** Do not retry, widen, or modify the conjunction
to reach `PROMOTION_AUTHORIZED`.

Do not add an HTTP route here. `src/cis/interface/api.py:121-127` states the
exclusion deliberately. Overriding it — exposing the coordinator over HTTP — is a
separate decision for later, and it is gated on Step 1 being closed first.

**Depends on:** Steps 0, 2 and 3.

---

### STEP 5 — Give the host promotion gate a caller

**Status: NO CALLER**

What exists: `HostPromotionGate` (`src/cis/host/promotion_gate.py`). Per
`README.md:14-17` it applies only a promotion-authorized, evidence-matching
candidate and can restore prior bytes from append-only authority alone.

Missing: any caller. The only reference in `src/` is the re-export at
`src/cis/host/__init__.py:3`. Note also that `PromotionRecorder` returns
`host_action: "NONE_RECORD_ONLY"` — the decision records, and by design does
not act.

**Done when:** an explicit operator-invoked command passes a recorded
`PROMOTION_AUTHORIZED` decision to the gate, the gate applies or refuses on its
own evidence check, and the outcome is recorded. Keep this operator-invoked
even after the loop exists — automatic application of bytes is a separate
decision you should make deliberately, not inherit.

**Depends on:** Step 4.

---

### STEP 6 — Make the Menter run asynchronous and give completion a record

**Status: NOT BUILT** in the live tree

What exists: `POST /menter/runs` is **synchronous** and blocks the caller. The
Menter service has real job hygiene — systemd unit with `Restart=always`, a
600-second wall-time ceiling, a $5 cost cap, and HMAC'd receipts carrying base,
candidate and card hashes. Receipts through 2026-10-29 11:17 prove runs complete
and get recorded.

Missing: `grep -rn "menter/jobs" src/` returns nothing. There is no job record
to create, poll, or react to. If the caller dies mid-run, nothing notices. The
async bridge exists only in the preserved, unadmitted candidate
`menter-e468adf81a5a4078a9957c0c7e874410`, whose base was captured 2026-10-27
18:15 and probably no longer matches — expect that candidate to be BLOCKED on
base mismatch. Do not rerun or modify it; the workspace is mode `0555` and the
receipt is HMAC-bound.

**Done when:** a job can be submitted, returns an id immediately, and its
completion is a durable record that a later step can detect without the
submitter still being alive.

**Depends on:** Step 0. Independent of Steps 3-5.

---

### STEP 7 — Record the Brain deliberation result

**Status: REACHABLE** for the conversation, **NOT BUILT** for the recording

What exists and works today: `POST /brain/sessions/start`, `POST
/brain/sessions/turn`, `POST /brain/sessions/close`. The turn route returns a
parsed, provider-neutral `DeliberationResult` — the closed structured result an
upstream Brain role must produce before Card Factory sees a draft work card
(`src/cis/brain/deliberation.py`, `dev_continuity_events:4.37:45`). The parser
is fail-closed and the UI already calls these routes
(`src/cis/interface/ui.py:333,352,375`).

**This is the step that makes "go to the Workbench and chat with Brain" real
today** — you can hold the conversation and get a structured result back.

Missing: the result is returned to the caller and then discarded. Its own
docstring is explicit: *"A parsed result is advisory evidence for Card Factory
and governance to read; nothing here records it, and nothing here grants an
ALLOW."*

**Done when:** a deliberation result is recorded as advisory evidence through a
sanctioned authority writer, addressable by id, and readable by a later step.
It grants no ALLOW and creates no authority.

**Depends on:** Step 0.

---

### STEP 8 — Build Card Factory intake: deliberation → draft work card

**Status: NOT BUILT**

What exists: `src/cis/card_factory/` contains **only** `projection.py`. Its
`card(task_contract_id)` projects the canonical card from an **already-frozen
task contract** — it is downstream of issuance, not upstream of it. There is no
intake surface.

Missing: anything that accepts a recorded deliberation result and produces a
draft work card for review. This is the component the recovered September design
history called Card Factory, and it is not in this tree.

**Done when:** a recorded deliberation result yields a draft work card, stored
as a draft with no authority and no ALLOW, reviewable before it becomes an
instruction.

**Depends on:** Step 7.

---

### STEP 9 — Join draft work card → instruction → frozen task contract

**Status: REACHABLE** downstream, **NOT BUILT** at the join

What exists and works today: `POST /instruction` → `Conductor.ingest_instruction`
→ on `ALLOW` with `scope.operation == "reconstruct_module"`,
`src/cis/workbench/service.py:825` calls `reconstruction_issuance.issue(...)`,
which freezes the task contract and emits the canonical card. This is genuinely
automatic and it is the one arrow in the whole loop that already closes itself.

Missing: `/instruction` accepts **verbatim human text only** — `{"verbatim":
"..."}`. Nothing converts a draft work card into that instruction. Steps 8 and 9
do not meet.

**Done when:** an approved draft work card becomes a submitted instruction
through the existing Conductor path, with the draft card id recorded against the
resulting transaction. Do not bypass `/instruction` or the authorization
envelope.

**Depends on:** Step 8.

---

### STEP 10 — Auto-dispatch: Card Runner

**Status: NOT BUILT**

What exists: `POST /reviewer/reviews` with `review_kind: "pre_menter_card"` and
a `task_card` exactly equal to the current `card_factory.card(task_contract_id)`
projection mints a **single-use Menter grant** on PASS
(`src/cis/workbench/service.py:468-510`). A stale, malformed or tampered card
mints nothing and never fails the review itself. This works today.

Missing: anything that performs that review and the subsequent dispatch without
a human doing it. Card Runner is a recovered design concept, not code in this
tree. **This is why cards have been hand-fed all week.**

**Done when:** a newly frozen task contract is automatically reviewed
pre-Menter, and on PASS the minted grant is automatically used to submit a
Menter job, with every step recorded. One attempt per card. No retry loop.

**Depends on:** Steps 6 and 9.

---

### STEP 11 — Auto-invoke assurance on run completion

**Status: NOT BUILT**

Missing: the trigger. Step 6 produces a completion record; Step 4 produces a
coordinator. Nothing connects them. This step is the connection and nothing
else.

**Done when:** a recorded Menter job completion automatically invokes the Step 4
coordinator for that task contract, exactly once, and records the promotion
decision whatever it is.

**Depends on:** Steps 4 and 6.

---

### STEP 12 — Build OSA-BR: notice a failure, classify it, raise an objection

**Status: NOT BUILT** — queue 4.36

What exists: `assurance.recovery` (turns a verified objection into a bounded
assessment), `recovery_attempt` (lineage to the replacement contract), and
`src/cis/assurance/recovery_execution.py`. Slice 6 per `README.md:26-30` begins
bounded recovery with operational self-assessment, and that assessment
"deliberately grants no execution authority."

Missing: the operational event and evidence contract, the failure taxonomy, and
the maintenance-incident state machine. This is the layer that would *notice* a
failure, classify it, and produce the objection the recovery machinery consumes.
Without it, recovery is a mechanism a human has to reach for.

**Done when:** a failed run, a verification failure, a review objection or a
promotion denial is detected, classified against a fixed taxonomy, and recorded
as an incident with the evidence that justifies its class.

**Depends on:** Step 11.

---

### STEP 13 — Give recovery execution a caller

**Status: NO CALLER**

What exists: `recovery_execution.py` is the one module that already drives
gateway → `Verifier.verify` → `Reviewer` → `PromotionRecorder.decide` for an
independently authorized replacement contract. `worker_supervisor` provides
per-attempt budgets, checkpoints and bounded fallback routing.

Missing: any caller at all. `grep -rn "recovery_execution" src/` outside the
module itself returns only the error class at `src/cis/errors.py:179`. Its entry
condition is a **verified objection**, which is what Step 12 produces.

**Done when:** a recorded incident with a verified objection invokes bounded
recovery execution, within its attempt budget, and the replacement contract's
own promotion decision is recorded.

**Depends on:** Steps 4 and 12.

---

### STEP 14 — Wire the supervising loop

**Status: NO CALLER**

What exists: `SupervisedExecutionCoordinator`
(`src/cis/execution/worker_supervisor.py:493`) — a bounded resumable coordinator
with plan creation, route resolution, start/checkpoint/finish and typed failure
classes. It is substantial and fully tested.

Missing: any caller. Only `tests/test_worker_supervisor.py` and
`tests/test_contained_worker_adapter.py` construct it. Nothing in this system
runs as a continuous process except the Menter service, the reviewer socket
relay and the Codex app server — none of which advance the assurance loop.

**Done when:** a single supervised process advances Steps 10 → 11 → 12 → 13
without human initiation, under a bounded plan with checkpoints, resumable
after a restart, and every transition recorded. This is the step that makes the
word "autonomous" true, and it is last for a reason: it can only supervise
arrows that already close.

**Depends on:** Steps 10, 11, 12 and 13.

---

### STEP 15 — Operator visibility of the loop

**Status: REACHABLE** for today's states, **NOT BUILT** for the new ones

What exists and works today: `GET /trajectory` (macro projection with a derived
you-are-here marker), `GET /trajectory/<transaction_id>` (micro steps),
`GET /assurance` (progress, declared flow, A-O order reconciliation),
`GET /assurance/task/<task_contract_id>`. The UI at `src/cis/interface/ui.py`
renders these.

Missing: none of these know about job state (Step 6), draft cards (Step 8),
dispatch state (Step 10), incidents (Step 12) or supervision plans (Step 14).

**Done when:** one read-only surface shows, for any objective: its deliberation,
its draft card, its frozen contract, its job state, its assurance state, its
promotion decision and reason code, and any incident — so you can tell where
the loop is without reading a database.

**Depends on:** whichever of Steps 6-14 have landed. Extend it as each lands;
do not leave it to the end.

---

## WHAT YOU CAN ACTUALLY DO TODAY, BEFORE ANY STEP IS BUILT

So this is not misread again — the complete list of what works right now:

1. Open the Workbench and **hold a real conversation with Brain**, getting a
   structured deliberation result back. (Step 7, conversation half)
2. Submit a verbatim instruction and get an authorization verdict with its
   canonical basis.
3. On an `ALLOW` for `reconstruct_module`, **automatically** get a frozen task
   contract and a canonical task card. (Step 9, downstream half)
4. Have that card independently reviewed pre-Menter by Qwen, and on PASS receive
   a single-use Menter grant. (Step 10, review half)
5. Submit one Menter run against that grant and get an HMAC'd receipt back —
   synchronously, blocking, one at a time.
6. Read the trajectory and assurance projections.

**That is where it stops.** Nothing verifies the result, nothing reviews the
implementation, nothing records a route receipt, nothing decides promotion,
nothing applies anything, nothing notices failure, nothing advances itself.

## WHAT "AUTONOMOUS" WILL AND WILL NOT MEAN AFTER ALL FIFTEEN

**Will:** a Brain conversation produces a deliberation; it becomes a draft card;
approved, it becomes an instruction and a frozen contract; it is reviewed and
dispatched; the run completes and is detected; verification, review, receipt and
promotion run and record a decision; failures are classified and routed to
bounded recovery; and a supervised process advances all of it and survives
restart.

**Will not, unless you decide otherwise later:** apply promoted bytes to the
host automatically (Step 5 stays operator-invoked by recommendation); grant any
authority without an authorization envelope; or operate as a permissioned
multi-user platform. CIS today is a single local operator on loopback with no
caller identity, and the manifest defers security trust boundaries deliberately.
That is an architectural step and nothing in this card narrows it.

## RULES FOR EVERY CARD DERIVED FROM THIS LIST

- One step per card. Never two.
- Re-derive the status with the command in the step. If your result disagrees
  with this card, report the disagreement with its output — do not adopt either.
- A fail-closed denial with a correct reason code is a successful run, not a
  failure to work around.
- Never weaken a conjunction, a validator, or an invariant to make a step pass.
  If a step cannot be done without changing one, that is a different card and a
  decision for Eric.
- Never report a focused subset as a whole-tree measurement.
- Never report code presence in an image as executable capability.
- Record the outcome through sanctioned writers as a `dev_continuity_events`
  revision and a queue item. Work that is not written to an authority a derived
  view reads is work that goes invisible — which is what happened to SWA.
