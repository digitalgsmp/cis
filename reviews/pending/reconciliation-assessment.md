# Reconciliation & Assessment — comprehensive task list (pre-Menter)

- VERSION: 3
- CHANGES: added transition mechanism + functionality map; recorded reviewer-fix (container restarted to reload evaluator MCP); D1 resolved (Claude = sandboxed coder).

## Intent (verbatim)

> "we have to reconcile the queue with all of this new reframing and design docs
> as well as verifying the drafter claims of the last few days… we need a new
> assessment… a comprehensive task list to this point including the unfinished
> claims."

## Reconciled priority order

**Phase 0 — VERIFY (blocking, do first)**
- V1–V11: each of the 11 commits, execution evidence not self-report (git diff / run / endpoint).
- V12: were migrations `0032_queue_authority.sql` and `0033_check_class.sql` applied to the live spine?
- V13: is queue item 3.21 (queue-into-spine) actually CLOSED, or still OPEN while C2/C3 claim it done? The queue can't track its own completion — needs a closure mechanism.

**Phase 1 — DECISION (Eric's call)**
- D1: Claude-as-coder — **RESOLVED:** Claude is sandboxed as the coder (Eric confirmed).

**Phase 2 — AUTHOR ROLE (build)**
- B1: consolidate Brain+Draft → one Author (V2 card ready).
- B2: un-strip Author — re-enable `cis-knowledge` MCP read-only, exclude `cis_dispatch_*`.
- B3: wire Author chat path (braingate bot, two-way).

**Phase 3 — QUEUE**
- B4: load design-spec items into `queue_items`.
- Q1: reconcile the 120 existing queue rows — which are obsolete, which still valid.
- Q2: close item 3.21 (V13's closure mechanism).

**Phase 4 — CLEANUP (explicit tasks, not just "decided")**
- CL1: retire host pipeline (workflow_runs, dispatch_log, gate_runner) — implementation step.
- CL2: remove HCP/AGENTS.md auto-regeneration from the pre-commit hook.
- CL3: retire or explicitly abandon the in-flight `ask_history.py` run (`run-4bbeea78056e2607-1788140226`, currently ERIC_GATE).

**Phase 5 — TELEGRAM (parallel with Phase 2/3)**
- TG1: add `CIS_TG_ADVISOR_TOKEN` + `CIS_TG_EVALUATOR_TOKEN` to `run_container.sh` + `entrypoint.sh` (slots currently empty).
- TG2: two-way report script for advisor/evaluator (own bots, Eric replies from phone).

**Phase 6 — ENFORCEMENT (separate track, parallel)**
- ADR-015/016 three-layer isolation — specified, not built.

## Reviewer flags on the 11 claims (round 1)

- All 11 commits are real, none fabricated. But "committed" ≠ "verified working."
- C3 (queue authority, `0869c97`) — highest risk: DB still shows 3.21 OPEN.
- C11 (`a3f7dea`) — 98% documentation, no runnable artifact; treat as docs, not code.
- C2 (`16a30bf`) — introduces migration 0033; application unconfirmed.

## Transition mechanism (how host → container retires)

Retirement criterion — the host pipeline is "truly retired" only when ALL hold:
1. Eric interacts with the consolidated Author bot (Telegram) for daily brainstorm → confirm → card.
2. A card runs review → implement → verify end-to-end inside the container, with evidence reaching Eric's phone.
3. Eric sees evidence, not self-report.

Sequence: verify claims (Phase 0) → build Author + wire bots (Phase 2/5) → Eric uses the Author bot → confirm the full loop runs → retire host + drop HCP (Phase 4) → enforcement gates (Phase 6).

## Functionality map (external advisors → pipeline agents)

| Eric's need | External (manual) | Pipeline (container) |
|---|---|---|
| Constrained worker | Claude Code | Menter (Claude, sandboxed) |
| Two objective reviewers | Claude + ChatGPT | Review1(Qwen)+Review2(GLM); Advisor(GLM)+Evaluator(Qwen) |
| Independent analysis | paste claim to other model | advisor loop (dual lineage, evidence-gated) |
| Brainstorm | Claude.ai / ChatGPT chat | Author (DeepSeek) |
| Context transport | HCP packet (hand-built) | spine DB + queue + cards |

## Open sub-decisions not yet tracked

- Whether two-way Telegram fully replaces the host `--continue` release path, or both coexist during the transition.
