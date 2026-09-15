# Advisor review — queue-authority-and-audit

- packet: `reviews/pending/queue-authority-and-audit.md`
- advisor: evaluator on port 8650, no tools
- run tag: queue-authority-and-audit @ 2026-09-10T00:21:45-05:00
- at: 2026-09-10T00:22:42
- prompt_tokens: 2602
- completion_tokens: 1431
- total_tokens: 4033
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The queue is broken (56 items silent, nothing derived from code, audit would evaporate), the two phases are genuinely one job (authority must move first or assessment is erased), and the card builds in the right checkpoint—Step 5 reports the classification ratio before the expensive work runs, so Eric can kill it if the audit turns out to be mostly opinion. Eric decided this today.

---

**Review of the proposal:**

The design is sound. Phase 1 establishes persistence before phase 2 does assessment, which is the correct order. The gate between them (check 1 must pass) is appropriate and load-bearing.

**Strengths:**

Step 1 is read-only and asks the right diagnostic questions, including whether the spine is in git (which determines whether the queue stays in version control). The card correctly notes that if it's untracked, Step 3D is the answer, but the fact should be reported first.

Step 2 backs up the markdown as the true rollback, which is correct—if this is wrong, the file is still the entire queue.

Step 3D is the key architectural decision: the markdown becomes a generated artifact from the table, wired into the pre-commit hook. This keeps the queue in version control (readable history) while making the database authoritative. The analogy to AGENTS.md is apt.

Step 4's check 1 is correctly marked LOAD-BEARING: a table that cannot reproduce the file is not the authority. The instruction to stop and restore on failure, not repair forward, is right.

Step 5 is the right checkpoint: classify before assessing, report the ratio, let Eric decide if the audit is worth the cost. The card is honest that if most items are JUDGMENT or NO_CHECK, the audit is worth less than it costs.

Step 6's rule is the core improvement: "an item may only be marked from command output. No item is marked because Claude Code believes it." The PRESENT_UNPROVEN mark for the container pipeline path is honest and correct given the stated facts (1.23 never completed, 3.28 pytest not installed).

Step 7 correctly refuses to guess on JUDGMENT items and marks NO_CHECK items as such, making both lists deliverables rather than failures.

**Concerns:**

None that invalidate the work. The card is honest about scale ("long card"), builds in progress reporting, and has the right stop conditions.

**Missing from the packet:**

Nothing needed for review. The card states what it needs (the 120 items, the checks, the current state) and will discover the rest in Step 1 and Step 5.

**Recommendation:**

Proceed. The design is correct, the gates are appropriate, and the card is honest about uncertainty and cost.
