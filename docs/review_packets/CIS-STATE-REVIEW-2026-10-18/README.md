# CIS state review — 2026-10-18

**For:** an independent external reviewer (ChatGPT), working from GitHub.
**Prepared by:** Claude Code (implementer lineage), read-only except where stated.
**Why this exists:** Codex is at its usage limit. This packet carries the state an
external reviewer needs in order to work without re-deriving it, and names exactly
what is and is not visible from GitHub.

---

## 1. Read this first — what you can and cannot see

Two repositories, both public:

| Repository | What it is |
|---|---|
| `digitalgsmp/cis` | The **reference environment**. Protected archaeological evidence. Not the build target any more. |
| `digitalgsmp/cis-clean` | The **clean-room reconstruction**. This is where current development happens. Published 2026-10-18. |

**Not reachable from GitHub, by design:**

- `data/cis_memory.db` — the SQLite spine, the project's actual authority store.
  `/data/*` is gitignored. It holds `project_decisions`, `open_questions`,
  `queue_items`, `queue_edges` and `dev_continuity_events`.
- `data/agent_handoffs/` — all inter-agent handoff material.

**Reachable, as generated projections of that database:**

- `PROJECT_CONTEXT_PACK_UPLOAD/HCP_03_DECISIONS_LOG.md` — every accepted decision,
  including `ADR-ARCH-001` … `ADR-ARCH-004` recorded 2026-10-13.
- `PROJECT_CONTEXT_PACK_UPLOAD/HCP_04_OPEN_QUESTIONS.md` — open questions, including
  `OQ-ARCH-009` (RESOLVED).
- `docs/UNIFIED_BUILD_LIST.md` — the task queue. **The only queue.** Worked in tier order.
- `CONTINUITY-EVIDENCE.md`, beside this file — the development history for tasks 4.37,
  `CIS.OSA-BR`, and WB.1 from revision 174, extracted from the database for this packet.

These are **projections, never authority** (ADR-ARCH-002). If a projection disagrees
with the database, the database is right and the projection is stale.

---

## 2. Measured state, not claimed state

Everything in this section was executed on 2026-10-18 and is reproducible.

### The clean room runs end to end

```
cd /mnt/projects/cis-clean
PYTHONPATH=src python3 -m cis verify     -> exit 0
PYTHONPATH=src python3 -m cis demo       -> exit 0
python3 -m unittest discover -s tests -t .  -> 355 tests, OK, 7.5s, no network
```

`verify` validates 29 module contracts at 16 semantic fields each and derives the
dependency order. `demo` runs the whole slice: verbatim instruction → continuity
classification → ALLOW/HOLD → governed backend run → deterministic verification →
independent review → bounded objections → record-only promotion decision. It also
correctly refuses a stale authorization after an objective redirection.

Macro stages 1–6 are COMPLETE. **`STEP_7_RESUME_PIPELINE_BUILD` is ACTIVE.**

### The honest gap

The machinery runs end to end. **The work does not.** In the clean room's own words,
the contained worker "does not yet run arbitrary model-authored source code, and it
cannot promote its own output." No real model-authored code task has gone end to end.

### The reference pipeline is effectively dormant

`workflow_runs`: 106 total, 28 `CONSENSUS_REACHED`, and **one run since 2026-10-01**.
Development has moved to the clean room.

### What blocks a live contained pipeline

Six revisions of task 4.37 (8 through 13) are parked on one phrase:
`ACTIVATION_BLOCKED` / `NATIVE_ACTIVATION_REQUIRED`. A sealed host-launch package exists
at `/opt/cis-control` and awaits one native `sudo` install. That installer was
independently reviewed by Claude on 2026-10-18 — behaviour matches its stated design on
all four properties, its sudoers grant is genuinely narrow (user `eric`, three
`systemctl` verbs on one unit, no wildcards), and the review recommended authorizing it.
It has **not** been run.

---

## 3. The destination the operator is driving toward

Queue **4.39 — Closed-loop capability reconciliation and completion planning**, approved
as a destination 2026-10-18. In plain terms: CIS assesses its own verified functional
state against the complete authoritative record, produces a reproducible capability
matrix with explicit dispositions (`ENFORCED`, `PARTIALLY_ENFORCED`, `DOCUMENTED_ONLY`,
`NOT_PRESENT`, `CONFLICTING`, `SUPERSEDED`, `UNKNOWN`), and emits dependency-ordered,
bounded implementation recommendations to authorized development workers — then reruns
the affected checks after each accepted increment. A recursive development loop.

`ENFORCED` requires a mapped deterministic mechanism **plus** independently executed
passing evidence. Documentation, model confidence, skipped tests and implementer
self-report cannot satisfy it.

Dependency chain, read from `queue_edges`:

```
4.20 -> 4.37 -> 4.36 -> 4.35 -> 4.39
```

| Item | Title | State |
|---|---|---|
| 4.20 | Contained-pipeline deterministic-enforcement capability set | OPEN |
| 4.37 | Trusted host control plane, contained pipeline, retirement gate | OPEN, in flight, 26 revisions |
| 4.36 | Operational Self-Assessment and Bounded Recovery (OSA-BR) | OPEN — **recorded only, explicitly no implementation** |
| 4.35 | Operator-compensation detection and capability-gap learning | OPEN — **recorded only** |
| 4.39 | The closed loop itself | OPEN — destination only |

Also feeding in: **1.27** (the system still cannot classify a failure; sequenced before
routing/retry), **2.7** (never-guess gate), **4.17** (automated intake — today "nothing
adds to this list but a person," which is the loop's input side).

**One structural blocker worth your attention:** `cis.review.cross_lineage_external` is a
*deliberately deferred* module. The clean room's reviewer satisfies author-is-not-verifier
*within* the environment, but genuine separate-lineage review is still an external model
reached by the operator pasting text. For a loop that dispatches recommendations to
external developers, that relay is the remaining manual seam — and queue WB.1 already
records the relay itself as a defect to remove.

---

## 4. Deterministic gates already enforced

In the clean room, each with a code location and tests:

- contract validator — 16 fields, non-collapse rule, one-owner-per-authority, L1/L2/L3 rules
- MASTER/TASK policy compiler with automatic policy-source admission
- execution gateway as the sole Layer-2 call path, with a leak test asserting no backend
  name, port, path or config file appears above it
- deterministic verifier
- independent reviewer on a separate input port, registry-forbidden from depending on the verifier
- bounded objections — three cycles then `ESCALATED`, a fourth blocked at API, ledger and SQL
- promotion conjunction — requires recorded `VERIFIED_PASS` **and** review `PASS`
- contained nonroot execution — no network, read-only root, dropped capabilities, resource
  and wall-time bounds, host-verified teardown
- sanctioned host apply with authority-only rollback
- projection regeneration — two fresh builds, per-surface hashes, cold-start equivalence
- append-only authority enforced by SQLite trigger, not convention

Still live in the reference environment: `closeout-check`, export agreement, build-state
coherence, KB source coverage, state-authority integrity, and the sealed host-launch gate.

---

## 5. An open question this packet cannot answer

**Queue 4.20 is recorded OPEN, but task 4.37 revisions 23–26 appear to implement
enforcement capability** — policy compiler, closed evidence/check mapping, strict
verified-value semantics, mandatory gateway/nonroot-worker binding. Whether 4.20 is now
partially or wholly satisfied cannot currently be determined deterministically by anyone.

That is precisely the gap queue 4.39 exists to close, and it is already biting. A reviewer
may find this the most useful thing in this packet.

---

## 6. What the reviewer is asked to do

1. Review `digitalgsmp/cis-clean` against the frozen architecture (`ADR-ARCH-001` … `004`
   in `HCP_03_DECISIONS_LOG.md`) and say whether the reconstruction honours it.
2. Give a view on sequencing: is activating the host-launch service the right next act,
   and is 4.36 (OSA-BR) the right next build, or should 4.20 be resolved or re-scoped first?
3. Say what 4.39 needs that is not yet recorded anywhere.

**Please request anything else you need rather than inferring it.** The database holds a
great deal that is not on GitHub — full decision text, queue item bodies, queue edges,
continuity event bodies, test output, container evidence, prior review packets. Any of it
can be extracted and published on request. Specifically, ask if you want:

- the full body of any queue item (the summaries here are truncated)
- the complete text of any `ADR-*` decision or `OQ-*` open question
- full `body` fields of any continuity revision (this packet carries summaries only)
- the independent architecture handoff preserved at revision 136
- the `/opt/cis-control` host-launch package source, gate, unit and sudoers policy
- any test run, executed live, with real output

Nothing in this packet is an authorization. Recording a review does not close WB.1,
activate P1, authorize reconstruction beyond what is already approved, or constitute an
Eric Gate approval.
