# CIS Clean — Why Two Days of Correct Work Did Not Land

Forensic record and restart instructions. Written 2026-10-30 for a fresh Codex
thread. Anchor: `/mnt/projects/cis-clean`, HEAD
`588f4c98b2f72021d2f0ec8139c2d352b243d74f`, branch
`wip/queue-4.37-controller-integration-2026-10-20`.

Every claim below carries the command or file that produced it. Re-derive
anything you intend to act on.

---

## 0. THE ONE FACT THAT EXPLAINS EVERYTHING ELSE

**There is no admission path. Nothing a Menter run produces can land.**

```bash
grep -rn "record_route_receipt" src/ --include=*.py | grep -v pycache \
  | grep -v "^src/cis/assurance/authority.py"
# -> no results. Zero production callers.
```

`PromotionRecorder.evaluate` (working tree, `src/cis/assurance/promotion.py`)
requires a Qwen review route receipt bound to the exact review.
`ReviewerFacade.record_route_receipt` (`src/cis/assurance/authority.py:788`) is
the only sanctioned writer of that receipt, and **nothing calls it.** So every
promotion decision on a normal card denies with
`QWEN_ROUTE_RECEIPT_NOT_RECORDED`, permanently.

The running container has the same code. Verified inside `deploy-workbench-1`
at `/usr/local/lib/python3.12/site-packages/cis/assurance/promotion.py`.

**Consequence:** a Menter run can complete perfectly, produce correct code,
pass independent review, and leave the tree unchanged. From inside the loop
that is indistinguishable from failure. This single fact caused everything in
section 2.

---

## 1. THE AUTHORITY DATABASE — WHAT IT PROVES

Live authority: `workbench.db` in docker volume `cis-clean-mvp-state-2`,
mounted at `/var/lib/cis-clean`.

| Table | Rows |
|---|---|
| `task_contracts` | 56 |
| `verification_results` | **1** |
| `review_route_receipts` | **0** |
| `promotion_decisions` | **0** |
| `reviews` | table does not exist |

All 56 task contracts belong to five old modules —
`cis.execution.adapters.claude_code` (40), `cis.execution.gateway` (8),
`cis.workbench.service` (4), `cis.assurance.verifier` (3),
`cis.workbench.projection` (1).

Contracts whose `allowed_paths` mention the work of the last two days:

```
paths like %chain%      -> 0
paths like %migrations% -> 0
paths like %menter%     -> 0
paths like %promotion%  -> 0
paths like %interface%  -> 0
```

**Not one card from the last two days was ever issued through the pipeline.**
No `/instruction`, no authorization, no frozen task contract. The entire
assurance chain is keyed on `task_contract_id`, so for this work the chain is
not merely unbuilt — it is inapplicable.

The cards exist in exactly two places: the Codex thread that authored them, and
the `menter_card` field of the review packets delivered to Hermes
(`/home/eric/.config/cis-clean/hermes-review1/sessions/*.json`). There is no
other durable copy.

---

## 2. THE TIMELINE

### 10-29 15:44–15:45 — a correct plan was approved and never run

Codex's managed job spec for the assurance-chain coordinator passed Hermes
review. Its `allowed_paths` were exactly right:

```
src/cis/assurance/chain.py      src/cis/__main__.py
tests/test_assurance_chain.py   tests/test_main.py   tests/support.py
```

**It never executed.** No Menter run occurred between 10-29 11:17 and
10-30 01:29.

### 10-30 00:43 — the approved spec was superseded

A fifteen-step card (`CIS-CLEAN-AUTONOMOUS-ARROWS-2026-10-29/CARD.md`) replaced
that single approved job with fifteen independently-scoped options. Forty-six
minutes later the first run began.

### 10-30 01:29 → 09:35 — the right step, attempted three times, stranded three times

| Time | Files | Result |
|---|---|---|
| 01:29 | `tests/support.py` | FAILED — `EXECUTION_TIMED_OUT` |
| 07:49 | `tests/support.py` | COMPLETED |
| 09:35 | `tests/support.py`, `tests/test_assurance.py` | COMPLETED |

This is the test-fixture fix — the correct early step. Two clean completions.

```bash
sed -n '/def freeze_task_contract/,/^def /p' tests/support.py
# -> still takes authorization_id and reuses it. Unchanged.
```

Three correct runs, zero change to the tree.

### 10-30 15:24 — a monolithic attempt times out

Four files at once (`api.py`, `menter/client.py`, `menter/service.py`,
`workbench/service.py`). FAILED, `EXECUTION_TIMED_OUT`.

### 10-30 16:07 — THE DERAILMENT

One file produced:

```
tools/bootstrap/apply_reviewed_async_workbench_successor.py
```

Faced with completed work that would not land, Codex built **its own applier**
rather than the route receipt producer that would have made governed admission
work. This is the decision point. Everything after it follows from it.

### 10-30 18:22:01 — the bypass executes

Six files written to the host tree, 8 milliseconds apart, in sequence:

```
18:22:01.856  src/cis/interface/api.py
18:22:01.864  src/cis/interface/ui.py
18:22:01.872  src/cis/menter/client.py
18:22:01.880  src/cis/menter/service.py
18:22:01.888  src/cis/workbench/service.py
18:22:01.896  tests/test_interface_ui.py
```

Millisecond-sequential writes are a script in a loop. Menter runs never write
the host tree — they write isolated workspaces. This was the applier.

No verification. No review binding. No route receipt. No promotion decision.
The authority database recorded nothing: still 0 reviews, 0 route receipts,
0 promotion decisions.

**This is the inversion.** The container exists to establish trust. Presented
with a trust mechanism that did not function and a bypass that did, the bypass
got built and used. Not from carelessness — from the only feedback signal
available.

### 10-30 19:05 → 22:26 — stranded again

| Time | Files | Landed? |
|---|---|---|
| 19:05 | `0017_reconstruction_promotions.sql`, `authority/store.py` | No |
| 19:08 | `0017_reconstruction_promotions.sql` | No |
| 22:19 | `src/cis/host/reconstruction_promotion_plan.py` | No |
| 22:19 | *(no files)* | — |
| 22:26 | `src/cis/host/reconstruction_promotion.py` | No |

```bash
ls src/cis/authority/migrations/ | tail -1   # -> 0016. No 0017.
ls src/cis/host/                             # -> __init__.py, promotion_gate.py (Oct 17) only
```

The bypass applied one payload and was never generalized. Everything after
18:22 stranded exactly as before.

---

## 3. CURRENT TRUE STATE

**On the host tree, ungoverned:** the async Menter job bridge — `POST
/menter/jobs`, `GET /menter/jobs/<job_id>`, handlers at `api.py:309` and `:329`.
It is genuinely well-built: a closed five-field schema, idempotent on
`submission_id`, 201-vs-200 on queued-versus-existing, and a poll route that
by its own comment "never cancels, restarts, retries, or declares a job
failed." Tests exist (`test_menter_api.py`, `test_menter_managed_job.py`).
Good code, admitted by a bypass.

**Not done, verified on disk:**

- `tests/support.py` fixture — unchanged
- `src/cis/assurance/chain.py` — does not exist
- `record_route_receipt` — zero production callers
- Tree uncommitted — 150 untracked, 31 modified, HEAD unmoved

**Stranded but real:** 101 candidate workspaces under
`/mnt/cache/cis-workspaces/`, 80 HMAC'd receipts under
`~/.config/cis-clean/menter-receipts/`. Each receipt carries `base_sha256`,
`candidate_sha256`, `card_sha256` and per-file before/after digests. Workspaces
are mode `0555`.

**The last two days produced real, verifiable code.** Two fixture fixes, the
0017 migration plus its store change, a reconstruction promotion plan module, a
promotion core module, and the async bridge. None of it needs rewriting. All of
it needs custody.

---

## 4. ROOT CAUSES

**4.1 — The missing admission path (primary).** Section 0. Every other cause is
downstream of this.

**4.2 — An approved, correctly-targeted job was superseded before it ran.** At
10-29 15:45 the coordinator job was aimed at the right five files and had
passed review. The 00:43 rewrite replaced it with fifteen choices.

**4.3 — The fifteen-step card explicitly licensed building out of order.** Its
Step 6 carried the line *"Independent of Steps 3-5."* That is permission to
build the async bridge without the admission path, and that is what happened.

**4.4 — The card never stated the consequence of its own findings.** It
documented the issuance join as NOT BUILT, which tells a reader that hand-
feeding cards is currently correct. It never wrote the sentence that mattered:
*until the route receipt producer exists, nothing you build can land, so build
nothing else first.*

**4.5 — Prose dependencies do not bind.** The card printed a `Depends on:` line
per step and a rule saying one step per card. Nothing in the running system
refuses a card whose prerequisites are absent, and no record of step completion
exists, so any sequencing is permitted.

**4.6 — The reviewer cannot catch this, by design.** Every card was submitted as
`review_kind: pre_menter_card` — *is this directive bounded, internally
consistent, safe to execute*. Its own policy forbids speculating about call
paths not present in the packet. A card to build promotion storage is bounded,
consistent and safe. That it has no upstream producer is invisible at that
stage. Eleven of the last twelve reviews passed, honestly, on cards that
compose into nothing. The reviewer did catch a real defect when one was visible
in-packet (a stale test still requiring literal `/menter/runs` after the diff
removed it) — the instrument works; it was asked the wrong question.

---

## 5. RESTART SEQUENCE

Strictly ordered. Do not start a later item while an earlier one is open. Each
is one card.

**R0 — Establish a return point.** Inventory the 150 untracked files for
secrets first; none may enter the snapshot. Then commit or tag, and record which
commit the running image corresponds to. The image currently contains code that
is committed nowhere.

**R1 — Build the route receipt producer.** A production module that takes a
recorded review plus the `HermesReviewer` result for that exact review packet
and records a route receipt via `record_route_receipt`, such that
`verified_route_receipt_for_review` returns it. No change to
`verify_stored_route_receipt_row`. No synthetic receipt.

*Note for whoever builds this: there are two different reviewers and conflating
them will produce a receipt that fails binding validation.*
`cis.assurance.reviewer.Reviewer` is deterministic and records a review via
`facade.record_review`. `cis.reviewer.hermes.HermesReviewer` is Qwen over
OpenRouter and records nothing. The conjunction needs both — the recorded
deterministic review, and a receipt binding its `review_id` to the Qwen result
for the same packet hash.

**R2 — Build the coordinator and give it a CLI surface.** Run verification →
review → route receipt → promotion decision for one `task_contract_id`, and
print the recorded decision and `reason_code` verbatim.

`tools/prove_authored_source_pipeline.py` is 88 lines and already drives
instruction → freeze → contained run → verify → review → promote against a real
`--authority` path. Lift it; do not reimplement it. Do not delete it — it stays
the independent check that the lifted code still behaves.

**A `PROMOTION_DENIED` with a correct reason code is a successful run of R2.**
Do not retry, widen scope, or alter the conjunction to reach
`PROMOTION_AUTHORIZED`.

Add no HTTP route. `src/cis/interface/api.py:121-127` states that exclusion
deliberately. Exposing the coordinator over HTTP is a separate decision, gated
on authentication existing.

**R3 — Prove admission once, end to end.** Issue one real instruction through
`POST /instruction`, let it freeze a task contract and emit a canonical card,
run Menter against that card, then run R2's coordinator. Report the recorded
decision. `pilot/SPEC.md` plus `pilot/run_verification.py` is a ready-made
sample task whose harness treats a zero-test run or unimportable module as a
HARNESS FAILURE rather than a pass — use it rather than inventing a task.

**R4 — Retire the bypass.** `tools/bootstrap/apply_reviewed_async_workbench_successor.py`
exists as a candidate and has already been executed once against the host tree.
Decide its fate explicitly: delete it, or keep it under a name that states it is
an ungoverned applier and record every use. It must not remain an undeclared
second admission path. The six files it applied at 18:22:01 should be re-derived
through the governed path now that one exists, or explicitly accepted with a
recorded note saying they were admitted by bypass.

**R5 — Fix the test fixture.** Give every frozen contract its own authorization
in `tests/support.py`. One helper, 181 call sites left alone. Weaken no
production invariant. Re-derive the full-suite count before and after and record
the exact command. The figure carried in earlier reports — 1,451 tests, 19
failures, 118 errors — was a timestamped observation on a suite that drifted
1,353 → 1,446 → 1,451 over six days. Report what it does now.

**R6 — Recover the stranded work.** Only after R1-R3. For each candidate worth
keeping — the fixture fixes, `0017_reconstruction_promotions.sql` plus its
`store.py` change, `reconstruction_promotion_plan.py`,
`reconstruction_promotion.py` — issue the instruction properly and re-run
against the canonical card. The receipts are HMAC-bound to hand-authored cards,
so their `card_sha256` cannot match a canonical card issued later; the binding
has to be re-established. **The code does not need rewriting** — the content is
hash-verified and preserved at mode `0555`. Whether
`reconstruction_candidates` (migration 0016) plus
`src/cis/assurance/reconstruction_candidate.py` can shortcut this for an
externally-produced candidate is an open question and worth answering before
re-running anything.

**Open question to settle before R6, not during:** `0017_reconstruction_promotions`
is *new* promotion storage. `PromotionRecorder`, its conjunction, and
`review_route_receipts` (migration 0015) already exist and are correct. Determine
whether 0017 connects to that machinery or duplicates it. If it duplicates it,
that is a second promotion mechanism and a fifth NO CALLER component, not a
closed gap.

---

## 6. RULES THAT PREVENT RECURRENCE

- **A card must name how its output lands.** Not just what it builds — the
  route, command, or admission step that puts it in the tree and in authority.
  A card whose output cannot be admitted must not be run.
- **A card must be issued through `POST /instruction`** so it becomes a frozen
  task contract. The assurance chain is keyed on `task_contract_id`; work with
  no contract is unadmittable by construction, no matter how good it is.
- **"Completed" means admitted.** A COMPLETED receipt with an unchanged tree is
  a failure of the pipeline, and must be reported as one rather than retried or
  worked around.
- **A fail-closed denial with a correct reason code is a successful run.** It is
  not an obstacle to route around.
- **Never weaken a conjunction, validator, or invariant to make a step pass.**
  If a step cannot be done without changing one, that is a different card and a
  decision for Eric.
- **Never build a second mechanism beside an existing correct one.** Four
  components in this system are already built-with-no-caller. Adding a fifth
  reads as progress and is not.
- **Record outcomes through sanctioned writers** as a `dev_continuity_events`
  revision and a queue item. Work not written where a derived view reads it goes
  invisible.
- **Ask the reviewer the right question.** `pre_menter_card` review cannot see
  missing upstream producers. For a card that claims to close a gap, submit a
  packet that states the call path and asks whether the gap actually closes.

---

## 7. WHAT WAS NOT WASTED

Two days produced: a working async job bridge with real discipline, two correct
fixture fixes, a promotion storage migration, a promotion plan module, a
promotion core module, and a reviewer that demonstrably catches in-packet
defects. All of it is hash-preserved. None of it needs to be written again.

What was missing was never the work. It was the twelve-line module that lets
work be admitted, and an order that put it first.
