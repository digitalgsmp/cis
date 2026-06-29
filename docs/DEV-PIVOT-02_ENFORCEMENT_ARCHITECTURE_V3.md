# CIS Enforcement Architecture — Combined Specification

## Specification Document v3.0

## Eric Gate Status: PENDING_APPROVAL

This document is the reconciled enforcement architecture for CIS. It combines:

1. **Claude's architectural outline** — the 6-layer deterministic gate schema,
   override-plane-first discipline, and build-order from the June 17 browser
   session reconciliation with ChatGPT.

2. **The real facts on disk** — what code actually exists, what the live system
   state is, what worked and what deadlocked.

3. **Eric's explicit requirements** — extracted verbatim from the June 17
   transcripts and prior sessions recorded in AGENTS.md §12.

**Author:** Compiled from Claude/ChatGPT reconciliation + live system inspection
**Date:** 2026-06-17
**Replaces:** CIS_HERMES_HARDENING_SPECIFICATION.md v2.0 (retired)
**Status:** DRAFT — for Eric Gate review, then Claude+ChatGPT audit

---

## 0. What Actually Happened on June 17

### 0.1 The Core Realization (Eric's Words)

> "I became aware that hermes had no constraints on it and that all of the
> guardrails I thought were in place could be bypassed because cis is not
> hermes and all of the guardrailing is just bash script in cis."

This is the founding insight. CIS's guardrails are bash scripts that live inside
the CIS repo. They gate the CIS pipeline. But any Hermes agent with tool access
can call `write_file`, `patch`, or `terminal` directly — completely bypassing
every gate. The gates are voluntary. The enforcement is theater.

Confirmed empirically: `generate_agents_md.py` was run via `terminal()` with no
staleness check, no deliberation, no Eric Gate. The 16 failure modes from the
CIS Integration Assessment are documentation-only — nothing physically blocks
any of them.

### 0.2 The Attempted Fix (v2.0 — RETIRED)

v2.0 wired `pre_tool_call` shell hooks into all 4 Hermes profile configs,
pointing at `cis_pre_tool_gate.sh`. The hook checked for a clearance token
file (`/tmp/cis_gate_clearance`) with a 30-minute TTL, created by
`gate_runner.sh`.

**What broke:** The token mechanism created a chicken-and-egg deadlock:
- Gate runner can't pass (dirty git)
- No clearance token created
- Hook blocks all `write_file`/`patch`/`terminal`
- Can't commit to clean state
- Deadlock permanent — no way out

**Root cause of the deadlock:** No escape hatch. The only way to disable the
hook was to edit `config.yaml`, but the hook blocked edits. The lock could
only be opened from inside the locked room.

**Secondary failures:**
- Deployed to all 4 profiles simultaneously, by the agent, with zero
  failure-mode testing
- The clearance mechanism depended on state the gate itself could block
  (the token file)
- The agent that deployed the hooks was the same agent the hooks were
  supposed to constrain (R1 acting outside Reviewer role)

### 0.3 What Was Recovered

Commit `35db8fa` reverted the broken clearance-token mechanism. The current
`cis_pre_tool_gate.sh` (live on all 4 profiles) uses a simpler gate: it checks
the spine for a CONSENSUS_REACHED workflow_run within the last 24 hours.

**Current state (verified 2026-06-17 23:30 UTC):**
- All 4 gateways healthy (ports 8642/8643/8645/8646 → 200)
- Hooks active on all 4 profiles
- Gate has valid authorization (run-gate-20260618, ~1h old)
- Git tree clean at 2d177d6
- No stray --replace processes
- `eric_gate_approvals` table exists but has 0 rows (unused)

### 0.4 What Remains Unfixed

The current 24h CONSENSUS_REACHED gate is a single coarse check. A Reviewer
can still write code and execute commands — the gate doesn't check role.
The Implementer can still self-authorize — the gate doesn't require Eric's
approval. An agent's completion claim is still trusted without deterministic
verification. The gate has no override file — a misconfiguration could still
deadlock (though the SQLite check is simpler and less fragile than the token).

---

## 1. Core Principle

> **A guardrail you cannot turn off from a bare shell is not a guardrail.
> It is a trap. The off-switch is built and tested BEFORE the guardrail.**

This single rule is the difference between the v2.0 deadlock and a safe
enforcement system. Every gate in this architecture checks the override
plane as its first line. You are never more than one `touch` command from
a working system.

### 1.1 What Eric Actually Wants (Verbatim)

From AGENTS.md §12 and the June 17 transcripts:

> "I need checks and balance, I am not a coder and if I don't trust something
> one of you says I have to be able to paste it for another model to evaluate
> and give me independent analysis. that is what claude and chatgpt did to
> each other. I need a worker who is constrained to my working methods and
> two objective reviewers as expert advisors."

> "the LLMs are the tools, I am trying to get LLMs to help me think by
> contributing factual information and expertise."

> "I don't want summaries, I am trying to build a system that works from
> the raw files."

> "it doesn't matter if you work 99% of the time. the 1% creates an
> unrecoverable deadlock. months and months of this. it's criminal."

The system must: constrain agents to their roles, verify every claim against
evidence, survive the 1% failure without deadlocking, and preserve Eric's
own words as the fixed reference point.

---

## 2. Enforcement Architecture — Six Layers

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    OVERRIDE PLANE                           │
│              /mnt/projects/cis/.GATE_DISABLED                │
│         (checked FIRST by every gate — universal            │
│          kill switch controllable from bare shell)           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LAYER 1: Thin Hook + External Policy Checker               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Hook (cis_pre_tool_gate.sh) — DUMB                   │  │
│  │  1. Check override file → allow if present           │  │
│  │  2. Collect facts: role, tool, target, cwd           │  │
│  │  3. Call policy checker with facts                   │  │
│  │  4. Exit with checker's exit code                    │  │
│  │  Contains ZERO policy logic. Never changes.          │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Policy Checker (cis_policy_check.sh) — DETERMINISTIC │  │
│  │  Reads rules table → pure lookup → allow/deny        │  │
│  │  NO LLM. NO model judgment. Exit 0 or exit 1.        │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Rules Table (cis_policy_rules.yaml or spine table)   │  │
│  │  Data, not code. Editable without touching scripts.  │  │
│  │  role × tool_class × path_pattern → allow | deny     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  LAYER 2: Role Capability Matrix                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Role derived from $HERMES_HOME (unspoofable)         │  │
│  │                                                      │  │
│  │ Prime (8642):    read/search only, NO CIS writes     │  │
│  │ Drafter (8645):  write docs/specs only, NO execution │  │
│  │ Reviewer (8643): read-only, NO writes, NO execution  │  │
│  │ Implementer (8646): write code per manifest,         │  │
│  │                    build/test with approval only     │  │
│  │ Qwen (8002):     NO tools at all (inference only)    │  │
│  │                                                      │  │
│  │ Deterministic: role + tool + target → table → allow  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  LAYER 3: Human-Only Authorization                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ eric_approvals spine table                           │  │
│  │ Only Eric can write to it. Agent physically cannot.  │  │
│  │ Each row carries hash of exactly what was approved.  │  │
│  │ Approval-for-A cannot authorize implement-B.         │  │
│  │                                                      │  │
│  │ Write paths (all require Eric):                      │  │
│  │   CLI: cis approve --run-id X --hash Y               │  │
│  │   Telegram: @cis_kernel_bot → API → DB               │  │
│  │   UI: CIS dashboard "Approve" button                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  LAYER 4: Epistemic Gates (advisory, not blocking)          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Staleness: web fetch current facts before deliberat. │  │
│  │ Reviewer search: each reviewer must do own research  │  │
│  │ Negative claims: verify absence against live system  │  │
│  │ Evidence completion: non-LLM script confirms effect  │  │
│  │                                                      │  │
│  │ These block the transition to Eric's approval,       │  │
│  │ not the work itself. Agent can draft freely; cannot  │  │
│  │ reach Eric without evidence attached.                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  LAYER 5: Front Door / Pipeline Stage Gates                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ → Review: draft artifact exists with content hash    │  │
│  │ → Eric Gate: both reviewers' records present,        │  │
│  │             non-empty output (Qwen can't be dead)    │  │
│  │ → Implement: eric_approvals row, recent, hash-match  │  │
│  │ → Verify: claimed files exist on disk with content   │  │
│  │ → Done: all prior gates passed                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Layer Details — What Exists vs What Needs Building

### 3.1 Layer 0 — Override Plane

**What exists:** Nothing. `.GATE_DISABLED` does not exist on disk.
**What needs building:** Add override check as line one of `cis_pre_tool_gate.sh`.
**Build order:** THIS IS BUILT FIRST, before any other gate change.
**Test:** Install trivial blocking hook → confirm blocked → `touch .GATE_DISABLED`
→ confirm unblocked → `rm` it → confirm blocked again. Only after this loop
works do you build gates behind it.

```bash
# The override check — line one of every hook:
if [ -f "/mnt/projects/cis/.GATE_DISABLED" ]; then
    exit 0  # Gate is OFF — Eric flipped it from a shell
fi
```

### 3.2 Layer 1 — Thin Hook + External Policy

**What exists:** `cis_pre_tool_gate.sh` — a single script that both checks
conditions AND contains policy logic (the 24h CONSENSUS_REACHED query).
It is not thin — policy and mechanism are fused.

**What needs building:**
1. Refactor the hook to be dumb: check override → collect facts → call checker → exit
2. Create `tools/gates/cis_policy_check.sh` — deterministic, reads rules, exits 0/1
3. Create `tools/gates/cis_policy_rules.yaml` — the rules table as data

**Design rule:** The hook never changes after initial deployment. All policy
changes happen in the rules table, which you can read and edit without touching
code. The policy checker is a pure function of facts + rules — no LLM ever.

### 3.3 Layer 2 — Role Capability Matrix

**What exists:** Nothing. The current hook does not check role at all. Any
profile running with HERMES_HOME set can write anywhere in CIS if a 24h
consensus record exists. This is how R1 deployed hooks — Reviewer role,
writing to config files and running terminal commands.

**What needs building:**
1. Role derivation function — reads `$HERMES_HOME` from the hook's environment
   (set by Hermes, cannot be spoofed by the agent)
2. Rules table entries for each role — what tool+target combinations are allowed
3. Policy checker reads role from env + tool from `$TOOL_NAME` + target from args →
   table lookup → allow/deny

**What this prevents concretely:**
- R1 writing to `~/.hermes*/config.yaml` (the v2.0 deadlock deployment)
- R1 running `terminal` to restart gateways (the v2.0 all-at-once deployment)
- Drafter executing code or editing configs
- Implementer writing to docs/specs (crossing into Drafter's domain)
- Prime mutating the CIS repo

**Deployment order:** Start with Reviewer only (the role that caused the
incident). Add Drafter, Implementer, Prime, Qwen incrementally.

### 3.4 Layer 3 — Human-Only Authorization

**What exists:** `eric_gate_approvals` table in the spine — schema exists,
0 rows. No write path exists for Eric to record approvals. The current
gate uses workflow_runs CONSENSUS_REACHED as a proxy — any consensus
record from any run authorizes any write.

**What needs building:**
1. Eric-controlled write paths:
   - CLI: `cis approve --run-id <id> --hash <proposal_hash>`
   - Telegram bot endpoint that writes the row
   - UI button
2. Hash binding: each approval row stores the SHA256 of what was approved
3. Policy checker reads eric_approvals: is there a recent row with matching hash?
4. Time window: configurable, default 24h, stored in rules table not hardcoded

**Design rule:** No code path exists for an agent to insert into
eric_gate_approvals. The write paths all require Eric's authentication.
This table is the load-bearing authorization record in the entire system.

### 3.5 Layer 4 — Epistemic Gates

**What exists:**
- `tools/pipeline/staleness_check.py` — web freshness check, operational
- `tools/pipeline/reviewer_reconcile.py` — dual-review deliberation, operational
- `tools/gates/gate_staleness.sh` — staleness gate script
- `tools/gates/gate_deliberation.sh` — deliberation gate script
- `tools/gates/gate_pre_execution_oversight.sh` — oversight gate (Gate 7 in gate_runner)

**What exists but is not enforced:**
- Independent-search-per-reviewer: each reviewer SHOULD do own research but
  nothing verifies that a reviewer actually searched before delivering a verdict
- Verify-negative-claims: when an agent asserts something doesn't exist, nothing
  checks the live system
- Evidence-backed completion: the rule exists on paper (ADR-SEED-002, AGENTS.md §10)
  but is not programmatically enforced

**What needs building:**
1. Search-evidence requirement: a reviewer's verdict is rejected by the pipeline
   stage gate unless an accompanying search-evidence record exists from that reviewer
2. Negative-claim verification: add a check to the policy checker — when a
   `write_file` or `patch` is preceded by an agent claim of absence, verify the
   claim against live system before allowing the write
3. Evidence-backed completion gate: wire `gate_file_exists.sh` and
   `gate_service_health.sh` into the pipeline closeout so an agent's "done"
   claim is never the record of completion

**Honest limit:** These gates can deterministically verify that a search HAPPENED
(fetch occurred, non-empty evidence record exists). They cannot verify that the
model interpreted results correctly. Eric's approval gate (Layer 3) remains the
final check on interpretation.

### 3.6 Layer 5 — Front Door / Pipeline Stage Gates

**What exists:** The gate scripts exist and `gate_runner.sh` chains them. But
they are not wired as automatic stage-transition gates in the orchestrator —
they run when invoked, not when a stage claims completion.

**What needs building:**
1. Wire each gate into the orchestrator as a stage-transition requirement
2. The Qwen gate specifically: the "→ Eric Gate" transition checks for TWO
   distinct reviewer records with non-empty output. If Qwen is down, the gate
   fails deterministically — no single model can paper over a dead reviewer.
3. The Implementer gate: checks eric_approvals for a recent, hash-matching row
   before allowing implementation work to proceed.

---

## 4. Build Order

Build one layer at a time. Each layer proven before the next. On ONE profile
first, then expand. Escape hatch tested before any gate is trusted. NEVER
deploy to all four at once (the v2.0 mistake).

| Phase | Layer | What Gets Built | Depends On | Status |
|-------|-------|----------------|------------|--------|
| 0 | — | Escape hatch POC on one profile | Nothing | NOT BUILT |
| 1 | 0 | Add override plane to all 4 hooks | Phase 0 | NOT BUILT |
| 2 | 1 | Refactor hook to thin + external policy checker | Phase 1 | NOT BUILT |
| 3 | 1 | Rules table (YAML) — start with current 24h rule | Phase 2 | NOT BUILT |
| 4 | 2 | Role matrix: Reviewer read-only enforcement | Phase 3 | NOT BUILT |
| 5 | 2 | Role matrix: Drafter, Implementer, Prime, Qwen | Phase 4 | NOT BUILT |
| 6 | 3 | eric_approvals write paths + hash binding | Phase 5 | NOT BUILT |
| 7 | 4 | Staleness + verify-negative-claims gates | Phase 6 | PARTIAL (staleness exists) |
| 8 | 4 | Independent-search + evidence-completion gates | Phase 7 | NOT BUILT |
| 9 | 5 | Pipeline stage gates in orchestrator | Phase 8 | NOT BUILT |

### 4.1 What Already Exists (Foundation — Do Not Rebuild)

| Artifact | Path | Status |
|----------|------|--------|
| Current hook | `tools/hooks/cis_pre_tool_gate.sh` | ACTIVE — 24h SQLite gate |
| Gate runner | `tools/gates/gate_runner.sh` | ACTIVE — 8-gate sequencer |
| Gate scripts (40+) | `tools/gates/gate_*.sh` | ACTIVE |
| Staleness check | `tools/pipeline/staleness_check.py` | ACTIVE |
| Reviewer reconcile | `tools/pipeline/reviewer_reconcile.py` | ACTIVE |
| Eric approvals table | `data/cis_memory.db` → `eric_gate_approvals` | EXISTS — 0 rows |
| Workflow runs | `data/cis_memory.db` → `workflow_runs` | ACTIVE — 5 rows |
| Deliberation rounds | `data/cis_memory.db` → `deliberation_rounds` | ACTIVE — 4 rows |

### 4.2 What Gets Replaced

| Current (v2.0 remnant) | Replacement | Why |
|------------------------|-------------|-----|
| Hook contains policy logic inline | Hook is dumb relay; policy in checker | Policy changes shouldn't touch hook |
| 24h window hardcoded in hook | Window in rules table | Configurable without editing scripts |
| No override file | `.GATE_DISABLED` checked first | Deadlock prevention |
| Any CONSENSUS_REACHED authorizes any write | Role matrix + eric_approvals | Reviewer can't implement |
| Single coarse gate | Layered: role + approval + epistemic | Defense in depth |

---

## 5. What This Does NOT Change

- CIS remains a standalone application using Hermes as backend
- Hermes remains the agent runtime; CIS provides enforcement
- The spine remains the source of truth
- The override file is the universal kill switch
- Eric is the final approval gate for all implementation
- The 4-gateway topology (8642/8643/8645/8646) stays as-is
- Qwen on 8002 (llama-server direct) for machine-to-machine review

---

## 6. Open Questions

1. **Rules table format**: YAML file vs spine table? YAML is simpler to edit
   manually; spine table is queryable by the checker without file I/O.
   Decision needed before Phase 2.

2. **Telegram approval path**: Eric often operates from phone. The Telegram
   bot → spine write path needs design. Options: bot calls API endpoint that
   writes the row; or bot has direct DB access (security concern).

3. **Fail-open vs fail-closed**: If the policy checker itself crashes, should
   the gate allow (fail-open, risk: enforcement disappears silently) or deny
   (fail-closed, risk: deadlock)? Current hook fails-open — is this correct
   for all layers?

4. **Profile relocation**: The sibling-home layout (~/.hermes-r1) triggers
   the `get_default_hermes_root()` collapse bug (ADR-SEED-014). Moving homes
   to ~/.hermes/profiles/ permanently fixes this. When does this happen
   relative to the enforcement build?

5. **Qwen direct path**: The finding that Qwen reviews must go through
   llama-server on port 8002 (not gateway 8644 which hangs on tool-loops).
   Should the policy checker enforce this? Or does it live in orchestrator config?

---

## 7. Eric's Words — The Fixed Reference

These are the statements that define what the tool is for. Every build decision
traces to one of these. When an agent proposes something, the gate asks: does
this serve these stated goals, or is it the model filling a vacuum?

> "I don't want summaries, I am trying to build a system that works from the
> raw files."

> "I need checks and balance, I am not a coder and if I don't trust something
> one of you says I have to be able to paste it for another model to evaluate."

> "the LLMs are the tools, I am trying to get LLMs to help me think by
> contributing factual information and expertise."

> "when I sit down and interact with the LLMs they don't remember anything
> and the overall vision is not apparent to combine the vision of where I
> am trying to get to, to why we are working on the immediate task."

> "I don't care about governance. did governance stop you all from undoing
> the 4 installations I had set up and consolidating it."

> "it doesn't matter if you work 99% of the time. the 1% creates an
> unrecoverable deadlock. months and months of this. it's criminal."

---

*Generated from: Claude/ChatGPT reconciliation (June 17 browser session),
live system inspection (2026-06-17 23:30 UTC), AGENTS.md §12,
ADR-SEED-002/003/004/014, CIS_HERMES_HARDENING_SPECIFICATION.md v2.0 (retired).*

---

## Session Update — 2026-06-27

This document's topic (enforcement architecture) was not directly advanced this session.
The major work completed: knowledge base ingestion (287K messages, FTS5 + ChromaDB),
abstraction layer (5 endpoints including human-readable status), intent alignment
pipeline, and roadmap. See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for the
full session handoff (gateway status, Eric's feedback, Phase 1 next steps).
Commit: 70e73bd.
