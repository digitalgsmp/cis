# Reconciliation & Assessment — comprehensive task list (pre-Menter)

- VERSION: 4
- CHANGES: D1 PROVEN (sandbox built + kernel wall verified + reviewer wiring live, not just "confirmed"); V12 RESOLVED (migrations 0032/0033 applied to live spine — verified via sqlite PRAGMA); V13 CONFIRMED (3.21 still OPEN, closure mechanism never run); queue count corrected 120→123 (with status breakdown); verification scope expanded 11→15 commits (4 new Drafter commits since 2026-09-12); folded all 5 reviewer gaps (port names, rollback path, retirement checkpoint, Menter contingency note, open_questions row).

## Intent (verbatim)

> "we have to reconcile the queue with all of this new reframing and design docs
> as well as verifying the drafter claims of the last few days… we need a new
> assessment… a comprehensive task list to this point including the unfinished
> claims."

## Reconciled priority order

**Phase 0 — VERIFY (blocking, do first)**
- V1–V15: each of the 15 commits, execution evidence not self-report (git diff / run / endpoint). The original 11 plus 4 new ones landed during the sandbox/wiring work.
  - NEW since 2026-09-12: `60703c8` (sandbox Claude launcher + §14 evidence), `d6bc889` (wire advisor/evaluator TG bots), `2d8b077` (tools.py docstring), `e4319cf` (reviewer blindness fix + MCP surface trim).
  - ORIGINAL 11: `3f7359c` (intent_bridge.py), `16a30bf` (queue authority phase 2), `0869c97` (queue authority phase 1), `d9bc5ca` (pause notifications), `4df51dd` (advisor knowledge record), `198fc71` (semantic cache + FTS), `6fdeefe` (KB search + cis_list_dir), `0c5fbc1` (--resolve triage), `e58abac` (un-blind reviewers), `185ac25` (round-2 reconciliation), `a3f7dea` (docs merge).
- V12: migrations `0032_queue_authority.sql` + `0033_check_class.sql` applied to live spine? — **RESOLVED: APPLIED.** Verified via `PRAGMA table_info(queue_items)`: columns `status_changed_at`, `status_changed_by`, `check_class` present; tables `queue_item_events` + `queue_sections` exist.
- V13: queue item 3.21 CLOSED or OPEN? — **CONFIRMED OPEN.** `item_num='3.21'` → `need_status='OPEN'`, `need_raw='OPEN'`, `check_class='RUNNABLE'`, `status_changed_at`/`status_changed_by` both NULL (queue_set.py closure never run). Closure mechanism exists but has never been executed against 3.21.

**Phase 1 — DECISION (Eric's call)**
- D1: Claude-as-coder — **PROVEN:** Claude Code sandbox is built and verified live (`tools/run_claude_sandbox.sh`, repo read-only mount, kernel wall blocks writes, real task completed with output to its out dir). Implementation-review wiring to reviewers 8643+8647 works (first live run returned OBJECTIONS — the loop functions). Menter (8646) is superseded by sandboxed Claude.

**Phase 2 — AUTHOR ROLE (build)**
- B1: consolidate Brain (8644) + Draft (8645) → one Author.
- B2: un-strip Author — re-enable `cis-knowledge` MCP read-only, exclude `cis_dispatch_*`.
- B3: wire Author chat path (braingate bot, two-way).

**Phase 3 — QUEUE**
- B4: load design-spec items into `queue_items`.
- Q1: reconcile the 123 existing queue rows — which are obsolete, which still valid. (Breakdown: 56 NULL-status, 44 OPEN, 11 UNASSESSED, 8 DONE, 4 HALF_DONE.)
- Q2: close item 3.21 with evidence (V13's closure mechanism now demonstrably available — migrations applied).

**Phase 4 — CLEANUP (explicit tasks, not just "decided")**
- CL1: retire host pipeline (workflow_runs, dispatch_log, gate_runner) — implementation step.
- CL2: remove HCP/AGENTS.md auto-regeneration from the pre-commit hook.
- CL3: retire or explicitly abandon the in-flight `ask_history.py` run (`run-4bbeea78056e2607-1788140226`, currently ERIC_GATE).

**Phase 5 — TELEGRAM (parallel with Phase 2/3)**
- TG1: add `CIS_TG_ADVISOR_TOKEN` + `CIS_TG_EVALUATOR_TOKEN` to `run_container.sh` + `entrypoint.sh`. — **PARTLY DONE:** entrypoint.sh now references the env vars; confirm run_container.sh passes them.
- TG2: two-way report script for advisor/evaluator (own bots, Eric replies from phone).

**Phase 6 — ENFORCEMENT (separate track, parallel)**
- ADR-015/016 three-layer isolation — sandbox mount proven; full §14 9-step test still to be run with raw artifacts (review2 flagged the current evidence as prose self-report, not the 9-step raw test).

## Reviewer flags on the claims

- All commits are real, none fabricated. But "committed" ≠ "verified working."
- C3 (queue authority, `0869c97`) — was highest risk because 3.21 showed OPEN; now RESOLVED on the migration-applied half (columns/tables present), still OPEN on the closure half.
- C11 (`a3f7dea`) — 98% documentation, no runnable artifact; treat as docs, not code.
- C2 (`16a30bf`) — migration 0033 now confirmed applied (check_class column present).

## Transition mechanism (how host → container retires)

Retirement criterion — the host pipeline is "truly retired" only when ALL hold:
1. Eric interacts with the consolidated Author bot (Telegram) for daily brainstorm → confirm → card.
2. A card runs review → implement → verify end-to-end inside the container, with evidence reaching Eric's phone.
3. Eric sees evidence, not self-report.
4. CHECKPOINT (added): a named verifier confirms the evidence actually reached Eric's phone — not Eric's subjective report alone.

Sequence: verify claims (Phase 0) → build Author + wire bots (Phase 2/5) → Eric uses the Author bot → confirm the full loop runs → retire host + drop HCP (Phase 4) → enforcement gates (Phase 6).

ROLLBACK (added): if Phase 0 reveals a broken commit (e.g., a migration applied against a live DB that then fails), stop and re-plan before touching the spine further. Verification failures are a stop-work signal, not a "fix quietly and continue" signal.

## Functionality map (external advisors → pipeline agents)

| Eric's need | External (manual) | Pipeline (container) |
|---|---|---|
| Constrained worker | Claude Code | Claude Code (sandboxed, kernel wall) — PROVEN, supersedes Menter |
| Two objective reviewers | Claude + ChatGPT | Review1(Qwen)+Review2(GLM); Advisor(GLM)+Evaluator(Qwen) |
| Independent analysis | paste claim to other model | advisor loop (dual lineage, evidence-gated) |
| Brainstorm | Claude.ai / ChatGPT chat | Author (DeepSeek, merged Brain 8644 + Draft 8645) |
| Context transport | HCP packet (hand-built) | spine DB + queue + cards |

## Open sub-decisions

- OQ-1: whether two-way Telegram fully replaces the host `--continue` release path, or both coexist during the transition.
