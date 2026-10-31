# CIS Clean — Three-Lineage Work Plan

One ordered plan merged from three independent sources, with the reviewer's
objections applied. Supersedes the bootstrap order in both postmortems.

| Lineage | Source |
|---|---|
| A — Claude | `agent_handoffs/CIS-CLEAN-DERAILMENT-POSTMORTEM-2026-10-30/POSTMORTEM.md` |
| B — Codex | `.codex-attachments/ff05bc44-.../CODEX_POSTMORTEM.md` |
| C — Reviewer | Hermes Review1, `qwen/qwen3.7-max`, verdict **OBJECTIONS** (3 material) |

Reviewer receipt — the audit anchor for this plan:

```
generation_id    chatcmpl-a03b9b53105a4743a8fce92a78093
packet_sha256    da90e0cfc009a4eaa645e39aacab2866d9cbf81f4362f7456be2ce55759d829e
response_sha256  9b9471176b4c2b99bc69e289b2e732c784156499854a9e2fa7cb8df98f5c45f9
role             hermes-r1   reasoning_tokens 0
```

Anchor: `/mnt/projects/cis-clean`, HEAD
`588f4c98b2f72021d2f0ec8139c2d352b243d74f`, branch
`wip/queue-4.37-controller-integration-2026-10-20`.

---

## WHAT THE REVIEWER CHANGED

The order proposed in lineage A was **defective in three ways**. Each fix is
folded into the sequence below; none is optional.

| Objection | Fix in this plan |
|---|---|
| `MISSING_TRANSITION_HOST_APPLICATION` — the order jumped from promotion decision straight to the contained controller. `PromotionRecorder` returns `host_action: NONE_RECORD_ONLY`; `HostPromotionGate` has no production caller. An end-to-end proof is therefore unsatisfiable as stated. | **W4** added as its own step, before any end-to-end claim. Lineage B had this; lineage A dropped it. |
| `DEPENDENCY_INVERSION_R1_WORKER_LIFECYCLE` — ambiguous whether the route receipt producer subsumes or depends on the governed reviewer worker lifecycle. `record_route_receipt` needs `worker_sessions`, `worker_model_requests`, `worker_session_events`, `backend_runs` and `evidence_records` rows; `HermesReviewer` creates none of them. Built as written it could be a thin wrapper that fails at runtime. | **W2 explicitly subsumes the worker lifecycle.** It is one step, not two, and it is not done until those rows exist. |
| `UNMITIGATED_BOOTSTRAP_WINDOW` — the first increment is executed by the same uncontained orchestrator both documents identify as root cause, with no control in the order itself. | **W1 makes the pre-dispatch guard mandatory** for every dispatch until W6 activates. It was an appendix; it is now a gate. |

---

## THE TWO PHASES

**Phase 1 — bootstrap, host-driven and guarded (W0–W5).** The contained
controller that would constrain the orchestrator is itself what is being built,
so this phase cannot be container-driven. That is the bootstrap paradox, and the
2026-10-25 reviewed card already named it: *"the transitional host sandbox, used
once to bootstrap your replacement contained controller."* W1 bounds this window.

**Phase 2 — container-driven (W6 onward).** CIS runs the plan, builds the
features, and calls host-level agents as contained roles under one-use lease.
This is the end state asked for. It is not available until Phase 1 completes,
and claiming otherwise is what produced the last two days.

---

## STATE VOCABULARY — from lineage B, binding on every step

These are separate states. **Never compress any of them into "completed."**

```
process exit success       is not   candidate success
candidate creation         is not   candidate custody
candidate custody          is not   deterministic verification
a Workbench Qwen response  is not   a governed review-route receipt
a promotion decision       is not   host application
files present in the tree  is not   runtime activation
a model report             is never evidence that any transition occurred
```

A step is done when its transition is recorded in authority by a sanctioned
writer. Not when a run exits 0, and not when an agent says so.

---

# PHASE 1 — BOOTSTRAP

## W0 — Return point and image provenance

**Blocking. Nothing else starts.**

Now: `git status --porcelain` → 181 entries (31 modified, 150 untracked). The
running image contains code committed nowhere. Nothing is reproducible.

Do: inventory the 150 untracked files for secrets — none may enter the snapshot.
Then commit or tag, and record the running image digest beside the commit it was
built from.

**Done when:** HEAD contains the route-receipt change; a tag names the prior
state; and a recorded note binds image digest to commit.

## W1 — Make the pre-dispatch guard mandatory

**Blocking for every dispatch in Phase 1.** This is reviewer objection 3.

Install the guard from lineage A Appendix A and run it before every card
dispatched in this phase. It refuses when declared prerequisites are absent, when
no production caller for `record_route_receipt` exists, or when the tree holds
unadmitted drift.

It is **advisory** — a host agent can bypass it, exactly as one was bypassed on
10-30 at 18:22:01. Its purpose is to make a bypass a deliberate, visible act
rather than an accident. That is the most this phase can have, and it is the
reason Phase 1 must be short.

**Done when:** the guard exists, is wired into the dispatch path for this phase,
and one refusal has been observed and recorded.

## W2 — Governed reviewer worker lifecycle AND the route receipt producer

**One step. Not two.** This is reviewer objection 2.

Now: `record_route_receipt` (`src/cis/assurance/authority.py:788`) has zero
production callers. It also requires durable rows that do not exist —
`worker_sessions: 0`, `worker_model_requests: 0`, `worker_session_events: 0`.
The current `HermesReviewer` path creates none of them.

So this step is **not** "add a caller." It is: execute the Qwen review through
the governed reviewer worker lifecycle so the durable facts exist, then record a
route receipt bound to them.

Two different reviewers, and conflating them produces a receipt that fails
binding validation:

- `cis.assurance.reviewer.Reviewer` — deterministic, records a review via
  `facade.record_review`
- `cis.reviewer.hermes.HermesReviewer` — Qwen over OpenRouter, records nothing

The conjunction needs both: the recorded deterministic review, and a receipt
binding its `review_id` to the governed Qwen execution for the same packet hash.

**Done when:** `worker_sessions` and `worker_model_requests` carry rows for a
real governed reviewer execution, **and**
`verified_route_receipt_for_review(review_id)` returns a receipt that
revalidates. No change to `verify_stored_route_receipt_row`. No synthetic
receipt. **A thin wrapper that calls `record_route_receipt` without the worker
lifecycle does not satisfy this step.**

## W3 — The assurance coordinator, as a CLI subcommand

Now: `src/cis/assurance/chain.py` does not exist. `Verifier.verify` and
`PromotionRecorder.decide` have one production caller each
(`recovery_execution.py`), reachable only after a failure already exists.

Do: one module, one `cis` subcommand, running verification → deterministic
review → route receipt → promotion decision for one `task_contract_id`, printing
the recorded decision and `reason_code` verbatim.

`tools/prove_authored_source_pipeline.py` is 88 lines and already drives
instruction → freeze → contained run → verify → review → promote against a real
`--authority` path. **Lift it; do not reimplement it. Do not delete it** — it
remains the independent check that the lifted code still behaves.

Build it **inside the container**: `cis` CLI, the authority at
`/var/lib/cis-clean/workbench.db` (rw), the Qwen socket at `/run/cis-reviewer`
and the Menter socket at `/run/cis-menter` are all present there. The host has
none of that mounted.

Add no HTTP route. `src/cis/interface/api.py:121-127` states that exclusion
deliberately; overriding it is a separate decision gated on authentication.

**Done when:** `cis <subcommand> --task-contract <id>` records a promotion
decision. **A `PROMOTION_DENIED` with a correct reason code is success.** Do not
retry, widen, or alter the conjunction to reach `PROMOTION_AUTHORIZED`.

## W4 — Governed multi-file host application

**This is reviewer objection 1. Lineage A omitted it entirely.**

Now: `PromotionRecorder` returns `host_action: "NONE_RECORD_ONLY"` — the decision
records and by design does not act. `HostPromotionGate`
(`src/cis/host/promotion_gate.py`) has no production caller; the only reference
in `src/` is the re-export at `src/cis/host/__init__.py:3`. Per `README.md:14-17`
it applies only a promotion-authorized, evidence-matching candidate and can
restore prior bytes from append-only authority alone.

Do: give it a caller, and make it a complete **multi-file** application
mechanism with a recoverable return point per application.

Keep it **operator-invoked**, even in Phase 2. Automatic application of bytes to
the live tree is a separate decision to make deliberately rather than inherit.

**Done when:** a recorded `PROMOTION_AUTHORIZED` decision can be applied to the
live tree by an explicit operator command, the gate refuses on its own evidence
check when bindings do not match, the outcome is recorded, and a prior state can
be restored from authority alone.

## W5 — One real end-to-end proof

Only now is this satisfiable. Both admission (W2, W3) and application (W4) must
exist first — that was the reviewer's point.

Do: issue one instruction through `POST /instruction`, let it freeze a task
contract and emit the canonical card, run Menter against that card, run W3's
coordinator, then apply through W4.

Use `pilot/SPEC.md` + `pilot/run_verification.py` — a ready-made sample task
whose harness treats a zero-test run or an unimportable module as a **HARNESS
FAILURE** rather than a pass. Do not invent a task.

**Done when:** one `task_contract_id` has a verification result, a deterministic
review, a route receipt, a promotion decision, and — if authorized — a recorded
host application, all readable from authority. Report every state reached and
every state not reached.

---

# PHASE 2 — CONTAINER-DRIVEN

## W6 — The contained controller

Execute the existing reviewed card
`docs/review_packets/4.37-contained-roles-bootstrap/MENTER_CARD_CONTAINED_CLAUDE_CONTROLLER.md`
(2026-10-25, **`CONSENSUS_REACHED`**) as written — all of `CM-01`–`CM-10`, its
allowed-files list unchanged. **Do not redesign it. Do not widen it.** It was
specified, independently reviewed, and skipped once already; five days later the
failure it prevents occurred.

Why it is the real fix: its reviewed boundary item 3 gives the model container
**only Read, Edit, Write, Glob, Grep — Bash, Task/subagent, web, MCP and session
persistence denied.** No Bash means no bootstrap applier and no script
execution. The 18:22:01 write is not discouraged under that boundary; it is
impossible. Boundary item 7 states the rule that was violated: *"Only promotion
authority may update the live CIS Clean checkout."*

**Build in parallel with W2–W5. Activate only after W5.** CM-09 keeps every seam
injectable and every test offline with no Docker containers created, so parallel
development is safe. The card's own Objective forbids activation in its
increment. A contained agent producing candidates that still cannot land is the
same failure with better isolation.

**Done when:** `claude_container.py`, its tests and its contract exist and pass
offline; and separately, after W5, activation is recorded as an explicit
decision.

## W7 — Close the four gates

Only after W6 do these bind rather than advise.

- **Gate A — done means admitted.** A step ledger written *only* by the
  coordinator recording a promotion decision. A COMPLETED Menter receipt never
  counts. This is the feedback signal whose absence caused the drift: an agent
  can ask "is step N done?" and get a real answer instead of inferring from an
  unchanged tree.
- **Gate B — grant minting refuses on unmet prerequisites.** Cards declare
  required steps; minting checks the ledger. The chokepoint already exists:
  `submit_semantic_review` (`src/cis/workbench/service.py:468-510`) mints a
  single-use Menter grant only when the submitted card equals
  `card_factory.card(task_contract_id)`, and both run routes require `grant`.
  **No grant, no run.** `task_contracts` already carries
  `required_checks_json`.
- **Gate C — tree-versus-authority drift, pre-dispatch.** Refuse to dispatch when
  the tree holds content with no admitting promotion decision. Receipts already
  carry `base_sha256` and per-file digests. Replaces W1's advisory guard.
- **Gate D — the gap-closure review kind.** `pre_menter_card` review cannot see a
  missing upstream producer; that is why eleven honest PASSes were returned on
  cards that composed into nothing. For any card claiming to close a gap, the
  packet must state the call path and ask whether the gap closes. **This plan is
  itself the proof it works** — the same reviewer that passed eleven cards
  returned three material objections when asked the right question.

## W8 — Brain drives the loop

Now: `POST /brain/sessions/{start,turn,close}` works and returns a parsed
provider-neutral `DeliberationResult`. **You can hold a real conversation with
Brain at the Workbench today.** What does not work: nothing records that result
(`src/cis/brain/deliberation.py` — *"nothing here records it, and nothing here
grants an ALLOW"*), `src/cis/card_factory/` holds only `projection.py` which is
downstream of issuance, and `/instruction` accepts verbatim human text only.

Do, in order, one step per card:

1. Record the deliberation result as advisory evidence through a sanctioned
   writer, addressable by id. No ALLOW, no authority.
2. Card Factory intake: a recorded deliberation yields a draft work card, stored
   as a draft.
3. Join draft card → `POST /instruction` → frozen task contract, with the draft
   id recorded against the transaction. Do not bypass the authorization envelope.
4. Card Runner: auto-review pre-Menter, and on PASS auto-submit the Menter job.
   One attempt per card, no retry loop.
5. Auto-invoke W3's coordinator on recorded job completion, exactly once.

`src/cis/brain/codex_app_server.py` is already a running continuous process and
already parses `DeliberationResult`. This orchestration belongs there rather
than in a new daemon.

**Only after this is "give Brain the plan and let it work through the steps"
actually available.** Until then the steps are hand-carried, and saying otherwise
is the error that cost two days.

## W9 — Failure detection, recovery, supervision

- **OSA-BR (queue 4.36):** the operational event/evidence contract, failure
  taxonomy and maintenance-incident state machine. `assurance.recovery`,
  `recovery_attempt` and `recovery_execution` are all built; what is missing is
  the layer that *notices* a failure, classifies it, and produces the objection
  recovery consumes.
- **Give `recovery_execution` a caller.** It has none —
  `grep -rn "recovery_execution" src/` outside the module returns only the error
  class at `src/cis/errors.py:179`.
- **Wire `SupervisedExecutionCoordinator`**
  (`src/cis/execution/worker_supervisor.py:493`). Substantial, fully tested, zero
  production callers. It advances the loop under a bounded plan with checkpoints,
  resumable after restart.

## W10 — Authentication

**No dependencies. Can start any time. Must land before W9's supervision runs
unattended.**

Now: `grep -nE "check_auth|Depends|Authorization|api_key|authenticate"
src/cis/interface/api.py` returns **nothing**. Eight POST routes carry no
application-level check, including `/instruction` (creates authority), `/execute`
(dispatches work), `/menter/runs` and `/reviewer/reviews` (spend budget), and
`/brain/profiles/sign-in` (initiates an OAuth flow against your ChatGPT account
and writes a credential). These are internet-reachable via the `cloudflared`
tunnel from `workbench.creative-intelligence-system.com` → `127.0.0.1:8099`.

Sole control is Cloudflare Access, recorded default-deny with a two-user allow
policy, **unverified from the host** — confirm in the dashboard. The older
`cis-pipeline` container gained a fail-closed in-application check
(`runtime/workbench_auth.check_auth()`) at revision 127; cis-clean never
inherited it.

## W11 — Recover the stranded work

**Only after W2–W5.** 101 candidate workspaces, 80 HMAC'd receipts. Worth
keeping: the two fixture fixes, `0017_reconstruction_promotions.sql` plus its
`store.py` change, `reconstruction_promotion_plan.py`,
`reconstruction_promotion.py`.

The code does not need rewriting — it is hash-verified and preserved at mode
`0555`. The binding does: receipts are HMAC-bound to hand-authored cards, so
their `card_sha256` cannot match a canonical card issued later. Issue properly
and re-run against the canonical card.

**Settle before starting, not during:** `0017_reconstruction_promotions` is *new*
promotion storage. `PromotionRecorder`, its conjunction and
`review_route_receipts` (migration 0015) already exist and are correct. Determine
whether 0017 connects to that machinery or duplicates it. If it duplicates it,
admitting it adds a fifth build-with-no-caller component and will read as
progress.

## W12 — Retire the bypass

`tools/bootstrap/apply_reviewed_async_workbench_successor.py` exists as a
candidate and has already executed once against the live tree. Decide
explicitly: delete it, or keep it under a name stating it is an ungoverned
applier, with every use recorded. It must not remain an undeclared second
admission path.

The six files it applied at 18:22:01 should be re-derived through the governed
path once W4 exists, or explicitly accepted with a recorded note saying they were
admitted by bypass.

## W13 — Operator visibility

`GET /trajectory`, `/trajectory/<tx>`, `/assurance`,
`/assurance/task/<task_contract_id>` exist and work. None of them knows about
job state, draft cards, dispatch state, incidents, host applications or
supervision plans. Extend as each step lands; do not leave to the end.

**Done when:** one read-only surface shows, for any objective: deliberation,
draft card, frozen contract, job state, assurance state, promotion decision and
reason code, host application, and any incident.

---

## RULES BINDING EVERY CARD FROM THIS PLAN

- **One step per card. Never two.** Merged steps produced the misleading reports.
- **A card must name how its output lands** — the route, command or admission
  step that puts it in the tree and in authority. A card whose output cannot be
  admitted must not be run.
- **A card must be issued through `POST /instruction`** so it becomes a frozen
  task contract. The assurance chain is keyed on `task_contract_id`; work with no
  contract is unadmittable by construction, however good it is.
- **"Completed" means admitted.** A COMPLETED receipt with an unchanged tree is a
  pipeline failure and must be reported as one, not retried or routed around.
- **A fail-closed denial with a correct reason code is a successful run.**
- **Never weaken a conjunction, validator or invariant to make a step pass.** If a
  step cannot be done without changing one, that is a different card and Eric's
  decision.
- **Never build a second mechanism beside an existing correct one.** Four
  components are already built-with-no-caller; a fifth reads as progress.
- **Re-derive before acting.** Every status claim in this plan carries its
  command. If your result disagrees, report the disagreement with its output —
  do not adopt either silently.
- **Record outcomes** as a `dev_continuity_events` revision and a queue item
  through sanctioned writers.

---

## HOW TO VERIFY ANYTHING ANY AGENT TELLS YOU

Four checks. None requires reading code.

**Did it actually land?** `git status --porcelain | wc -l` and
`git log --oneline -3`. A COMPLETED receipt with an unchanged tree means
stranded, not done.

**Is a review receipt real?** `response_sha256` must equal the SHA-256 of
`{verdict, objections, summary}`. If a quoted summary and its hash disagree,
either the quote is truncated or the receipt is wrong — ask for the computed
value printed next to the claimed one. Truncated quoting is the likelier cause.

**Did a transition get recorded?** Read the authority table counts. Today:
`review_route_receipts 0`, `promotion_decisions 0`, `verification_results 1`,
`worker_sessions 0`. Any claim of progress through the chain must move one of
those numbers.

**Was it governed?** A real card has a row in `task_contracts` whose
`allowed_paths_json` matches the work. No row means it was hand-fed and cannot
be admitted regardless of quality.

A model report is never evidence. Ask for the command and its output.
