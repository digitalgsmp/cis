# Advisor review — next-actions-determination

- packet: `reviews/pending/next-actions-determination.md`
- advisor: evaluator on port 8650
- run tag: next-actions-determination @ 2026-09-13T05:55:40-05:00
- at: 2026-09-13T06:05:45
- prompt_tokens: 147918
- completion_tokens: 4987
- total_tokens: 152905
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

Good. All claims verified. Now let me answer the three questions.

---

## Claim verification summary

| Claim | Verdict | Evidence |
|-------|---------|----------|
| V12: migrations 0032/0033 applied | CONFIRMED | PRAGMA table_info(queue_items) returns status_changed_at, status_changed_by, check_class; sqlite_master confirms queue_item_events + queue_sections |
| V13: 3.21 still OPEN | CONFIRMED | cis_get_queue_item('3.21') returns need_status='OPEN', need_raw='OPEN' |
| Queue count 123 | CONFIRMED | SELECT COUNT(*) FROM queue_items → 123. Breakdown: 56 NULL, 44 OPEN, 11 UNASSESSED, 8 DONE, 4 HALF_DONE — exact match |
| D1: sandbox built + kernel wall | CONFIRMED | Commit 60703c8: "Sandbox Claude Code (kernel wall) — launcher + §14 evidence + cards" |
| 11→15 commits | CONFIRMED | Git log shows 4 new commits above the original verification set: 60703c8, d6bc889, 2d8b077, e4319cf |
| queue_set.py exists | CONFIRMED | tools/queue/queue_set.py found via cis_search_files |
| ask_history.py stuck (CL3) | CONFIRMED | 5 runs at run-4bbeea78056e2607-*, statuses: ERIC_GATE, ESCALATED, ERROR, ERROR, ESCALATED. Most recent (run-...140226) sits at ERIC_GATE — it is Eric's to act on, not abandoned |
| Reviewer access: 21 read-only tools | CONFIRMED | I am using them right now |

---

## Q1: ORDER

The spine itself already answers this. `cis_get_current_phase` reports:

> "Container transition (Eric directed 2026-09-12): TG2 two-way report (queue 3.31) is current. Then Author consolidation, 3.29 result-size caps, 3.30 spine persistence."

This is Eric's stated priority as of yesterday. The correct order is:

**1. Execute 3.31 (TG2 two-way report)** — this is the active work item Eric directed. It is OPEN, scoped to tools/pause_notify.py + enforcement/mwl-proof-v2/entrypoint.sh + tools/advisor_review.sh. Nothing blocks it.

**2. Close 3.21 with evidence via queue_set.py** — the schema is live, the work is visibly done (columns exist, tables exist, first reader committed at a6e1a80). This is deterministic housekeeping: `python3 tools/queue/queue_set.py 3.21 --status DONE`. It takes seconds and clears a confusing OPEN item that is actually complete.

**3. Execute V1–V15 commit verification** — retrospective, does not unblock anything forward. Do it after 3.31 lands. It is valuable for the audit trail but not urgent.

**4. ask_history.py runs** — do not abandon. The most recent (run-...140226, 2026-08-31) is at ERIC_GATE status. That is Eric's decision. The 4 earlier runs (ERROR/ESCALATED) are already terminal. No action needed from reviewers — just note them in the record.

**Rationale**: Eric gave a direct order on 2026-09-12. Following it is the highest-leverage move. Closing 3.21 is second because it removes a false-positive OPEN that could confuse future queue triage. Commit verification is third because it is pure audit — it changes no state and blocks no one.

---

## Q2: TOOL SPLIT

**DETERMINISTIC (script-collected, no LLM judgment needed):**

- V1–V15 commit verification: git log, git show, cis_hash_file against expected hashes, cis_query against spine tables. Every commit either has the expected files changed or it doesn't. A shell loop with cis_git_show + cis_hash_file produces a pass/fail matrix.
- Closing 3.21: queue_set.py invocation + post-state PRAGMA check.
- Queue count reconciliation: one SELECT with GROUP BY.
- Verifying schema migration application: PRAGMA table_info + sqlite_master queries.

**NON-DETERMINISTIC (requires reviewer judgment):**

- Whether 3.31's scope (tools/pause_notify.py + entrypoint.sh + advisor_review.sh) is correctly defined for "two-way report" — this requires reading Eric's intent from KB history.
- Whether the 15-commit verification scope is sufficient or whether older commits (a6e1a80 through 4d8d2e8, the queue-authority phase) also need re-verification against the live schema.
- Alignment check: does the current build trajectory (3.31 → 3.29 → 3.30) actually serve Eric's stated vision, or is it drifting into infrastructure-for-infrastructure's-sake? This is the kind of question that needs a reviewer reading KB intent history.
- Whether the ask_history.py ERIC_GATE run should be approved, vetoed, or refined — that is Eric's call, but reviewers could prepare a summary of what happened across the 5 attempts.

**Recommendation**: Build a deterministic verification script for the V1–V15 matrix now. It is pure data collection. Reserve reviewer deliberation rounds for 3.31 scope review and trajectory alignment.

---

## Q3: SCOPE — is 11→15 the right reconciliation?

**Partially.** The 4 new commits (60703c8, d6bc889, 2d8b077, e4319cf) are real work that landed during the sandbox/wiring phase. They need verification. But the smarter approach is:

**Don't verify commits — verify outcomes.** The question is not "did commit X touch the right files?" but "does the live system match what the build list says is DONE?"

Concretely:
- 60703c8 (sandbox): verify by checking enforcement/mwl-proof-v2/ for the launcher + §14 evidence files. cis_list_dir already shows the directory exists.
- d6bc889 (Telegram bots): verify by checking that the bot wiring files exist and the integration test passes.
- 2d8b077 (docstring fix): trivial — cis_hash_file on tools.py, compare to pre-fix hash.
- e4319cf (reviewer blindness + MCP trim): verify by checking that reviewer MCP tool surface is what cis_get_current_phase claims (21 tools).

This outcome-based approach scales better than per-commit verification. As more commits land, you verify the system state, not the commit log. The commit log is evidence for the audit trail; the system state is evidence for "is it done."

**Missing from this packet**: I do not have the list of which 11 commits were in the original verification scope, so I cannot confirm the exact boundary between "old 11" and "new 4." The packet should include the commit hash list for both sets.
