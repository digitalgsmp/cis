# §14 raw-evidence capture — override-plane mount-semantics test

VERSION 1 — the first step the reviewers directed (Card 1 of the split).

GOAL_ALIGNMENT: seed intent 3 (checks and balances). This is the load-bearing
evidence gate (ADR-SEED-016) that must clear before the coder sandbox — or any
enforcement implementation — can proceed. It is the unblock that makes the
sandbox card real.

## Problem

ADR-SEED-016 gates ALL enforcement implementation on: "No implementation until
§14 raw-evidence plan executed." §14 (spec §14, docs/TASK_CONTRACT_ENFORCEMENT_
PRIMITIVE_V1.md) requires six evidence items captured and Eric-approved before
any /opt/cis-control, hooks, or Docker mounts are created.

§14 was BLOCKED by a structural contradiction (spine NA-SEED-014): the §7
override-plane test needs /opt/cis-control to exist, but §14 forbids creating it.
Amendment 1 (docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1_AMENDMENT_1.md) resolved
the deadlock with a disposable test root. The follow-on execution node
NA-SEED-016 ("execute §7 Parts A+B test against disposable root") is PENDING and
has never been run. The sandbox card is correctly gated behind this evidence.

## Requirement

Capture §14 evidence items 1–2 (the bare-shell override-plane test and the Docker
wall test) against the disposable test root per Amendment 1, and present the raw
output for Eric approval. No production /opt/cis-control, no policy hook, no
compiler, no Hermes worker — this is a bare-shell mount-semantics proof only.

## Scope

§14 items 1 and 2 ONLY:
- Item 1: bare-shell override test — all 9 steps of §7 Parts A+B, with exit codes
  and file-existence checks.
- Item 2: Docker wall test — `touch /mnt/projects/cis/breach.txt` in a test
  container with a read-only mount, expecting "Read-only file system" and no
  breach file on the host.

§14 items 3–6 (control_manifest.json generation, contract compiler validation,
policy-hook dry-run, Hermes-in-constrained-container) are OUT OF SCOPE: they
require building enforcement artifacts, which is the gated implementation itself.
They remain separate, later, still-gated work.

## Mechanism

R1. Disposable test root (Amendment 1 §2–4). Create
    `/mnt/cache/catalog/override-plane-test/<run_id>/` with two SEPARATE host
    directories: `control/` (root-owned, operator-only writable, mounted RO →
    `/contract` in the container) and `workspace/` (eric-owned, worker-writable,
    mounted RW → `/mnt/cache/catalog/<run_id>`). Capture `stat` ownership and
    `realpath` separation evidence (Amendment 1 §3–4).

R2. Docker wall test (§14 item 2). In a disposable container with the repo RO,
    run `touch /mnt/projects/cis/breach.txt`; capture the "Read-only file system"
    error and confirm no breach file appears on the host.

R3. §7 Parts A+B 9-step test (Amendment 1 §7). Operator creates the
    `.GATE_DISABLED` sentinel on the host via sudo; worker verifies it cannot
    write/remove the sentinel (`/contract/` is RO); override is honored while the
    sentinel is present; Docker wall is never bypassed even with override; the
    wall re-engages after the operator removes the sentinel and the container
    restarts.

R4. Evidence discipline (Amendment 1 §8). Every command records
    COMMAND / OUTPUT / EXIT / INTERPRETATION. Final result is PASS / FAIL /
    BLOCKED. PASS requires all six conditions (a)–(f) of Amendment 1 §8.

## Operator boundary (the point of the test)

The sentinel create/remove steps are OPERATOR actions on the host, run as root
via sudo. The worker (non-root, inside the container) cannot create, modify, or
remove the sentinel. The test is only valid if the operator steps and the worker
steps run under the real privilege boundary — not both as root. The operator
steps must be run by Eric (or the implementer with explicit sudo), and the exact
sudo commands must be provided verbatim for the operator to run.

## Decisions

D1. Disposable root, NOT production /opt/cis-control (Amendment 1 §2).
D2. Bare-shell test only — no Hermes worker, no hook binary, no compiler
    (Amendment 1 §6.4–6.5). This proves mount semantics, not the full primitive.
D3. No enforcement files outside `/mnt/cache/catalog/override-plane-test/`
    (Amendment 1 §6.3).
D4. This card implements the approved gate (ADR-016 + Amendment 1), not a new
    design. If implement-time findings conflict with the live spec, the spec
    wins and the divergence is reported.

## Open questions (resolve at implement time, files win)

O1. Who runs the operator-side sudo steps? Eric is the operator; if he does not
    want to run them, a named executor with sudo must be agreed before start.
O2. Is the repo mount in the CURRENT cis-pipeline container read-only or
    read-write? The June spec §3 records RO; the sandbox card draft claimed RW.
    Resolve with `docker inspect` before asserting either.
O3. The `$100 Claude credit` noted in FRONTIER_HANDOFF_CARD_LIST — is it available
    for this container test work, or unrelated?

## DONE-WHEN

- Disposable test root created with root-owned control/ and separate eric-owned
  workspace/, with stat + realpath evidence.
- Docker wall test shows "Read-only file system" and no host breach file.
- All 9 §7 steps run against the disposable root with raw output captured.
- Final result PASS per Amendment 1 §8 (conditions a–f).
- Evidence (all commands + output + exit codes) captured as artifacts and
  presented to Eric for approval — the §14 gate pass.
- No production /opt/cis-control, hooks, or compiler were created.
