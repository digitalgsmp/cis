# Sandbox Claude Code (enforcement primitive for the coder)

VERSION 1 — queue item to be assigned (prerequisite to CARD-claude-code-submit-loop).

GOAL_ALIGNMENT: seed intent 3 (checks and balances). A coder that can write
anywhere in the repo cannot actually be constrained by reviewers — the reviewers'
hold is advisory until the write boundary is enforced at the OS level. This card
builds that boundary. It is the prerequisite Eric named: sandbox Claude before
wiring any implementation review.

## Problem

Claude Code is the coder (Eric-confirmed, recorded as D1 in queue-framing-v3).
It currently runs inside the `cis-pipeline` container with the repo mounted
read-WRITE (`/mnt/projects/cis` → `/workspace/cis` rw, verified via `docker
inspect`). There is no OS-level write restriction: Claude can write anywhere in
the repo, so a reviewer hold is a suggestion, not a constraint.

The approved enforcement primitive has never been implemented:
- ADR-SEED-015: three-layer process isolation — CIS enforces the worker via a
  root-owned `/opt/cis-control` mounted read-only; the worker writes only to
  `/mnt/cache/catalog/<run_id>/`; two walls (kernel Docker RO mount + policy hook
  `pre_tool_call`); trust root = the constrained agent cannot author its own
  contract; override plane (`.GATE_DISABLED`) built/tested before the hook is
  trusted.
- ADR-SEED-016: the primitive is APPROVED but explicitly NOT implemented —
  "No implementation until §14 raw-evidence plan executed."

`CARD-claude-code-submit-loop` (2026-09-11) explicitly excludes this work: its
"NOT IN THIS CARD" section says it does not change the enforcement primitive and
does not add mid-execution interception. So the sandbox is the missing
foundation that card assumes but does not build.

The `reviewer-isolation` card established the OS-level-over-prompt-level
philosophy for the reviewers, but no equivalent write-isolation was ever built
for the coder.

## Requirement

Claude Code runs constrained at the kernel level: the repo is read-only, and the
only writable location is a designated output dir. Enforcement is OS-level
(Docker read-only mount) plus a policy hook — not prompt instructions and not a
command blacklist.

## Mechanism

R1. Execution context. Claude Code runs against the repo mounted READ-ONLY, with
    a single writable output dir (e.g. `/mnt/cache/catalog/<run_id>/` per
    ADR-015, or `/workspace/output`). Build artifacts go to the output dir.

R2. Two enforcement walls (ADR-015). (1) Kernel wall: Docker read-only mount of
    the repo. (2) Policy wall: a `pre_tool_call` hook that denies any write tool
    call whose target is outside the output dir.

R3. Trust root. The constrained Claude Code cannot author its own contract — the
    contract lives in the root-owned `/opt/cis-control`, mounted read-only, so
    the coder cannot rewrite the rules that constrain it.

R4. Override plane first. Build and test `.GATE_DISABLED` before the policy hook
    is trusted (ADR-015). The hook must have a tested escape path, or it is a
    footgun, not a wall.

## Decisions

D1. OS-level enforcement, not prompt-level and not command-blacklist (consistent
    with ADR-015/016 and the reviewer-isolation card's rejection of blacklists).

D2. This card IMPLEMENTS an already-approved decision (ADR-015/016). It is not a
    new design. If implement-time findings conflict with the ADR, the live ADR
    text wins and the divergence is reported, not silently "fixed."

## Open questions (resolve at implement time, files win)

O1. Where does Claude Code run — the existing `cis-pipeline` container with an
    added RO mount + hook, or a separate sandbox container? Implementer decides
    based on the live container layout.
O2. ADR-016 gates implementation on a "§14 raw-evidence plan." Verify whether
    that plan exists / has been executed; if it is still an unmet gate, executing
    it is the first sub-step of this card, not a reason to defer.
O3. What is the writable output dir's exact path in the container, and how do
    reviewer evidence reads reach it (they must be able to read the build
    evidence, read-only).

## DONE-WHEN

- Claude Code runs headless (`claude -p`) with the repo read-only.
- A deliberate write OUTSIDE the output dir is denied at the kernel level —
  demonstrated by a test that attempts the write and shows it refused (raw
  output, not a claim).
- The `pre_tool_call` policy hook denies an out-of-bounds write tool call.
- The `.GATE_DISABLED` override plane is built and exercised before the hook is
  trusted.
- If ADR-016's §14 gate applies, it is executed (or its status confirmed) first.
- Evidence: raw denied-write test output + the mount/hook configuration, both
  captured as artifacts.
