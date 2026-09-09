# Advisor review — queue-3.21-build

- packet: `reviews/pending/queue-3.21-build.md`
- advisor: advisor on port 8649, no tools
- run tag: queue-3.21-build @ 2026-09-09T00:02:47-05:00
- at: 2026-09-09T00:03:03
- prompt_tokens: 8570
- completion_tokens: 652
- total_tokens: 9222
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

VERDICT: NOT_ESTABLISHED

Four of the five claims are supported by the evidence. One is not, and it matters.

Claims 1-4 are established:

1. queue_items exists and is populated — migration 0031 ran, extractor output shows 119 rows, checks 1a/1b confirm count and form distribution.

2. Reader returns correct item by identity — checks 9b (3.21 returns '3.21'), 9d (3.22 returns '3.22'), 9e (missing returns None), plus 9c (hand-verified field matches). This is real.

3. Old tool no longer returns a wrong answer silently — checks 10a-10f confirm the redirect, correct item carried, no regression on real node_labels. The call-site survey corroborates the behavior change.

4. Reader serves no dependency edges — check 9g confirms `expect: False, actual: False`.

Claim 5 is NOT established. The card claims "the withdrawn success-field decision is recorded in project_decisions as ADR-3.21-001, not only in a DDL comment." Nothing in the diff, command output, or file listing shows any file named project_decisions, any ADR-3.21-001, or any write to a decisions table. The diff contains modifications to spine.py, tools.py, advisor_review.sh, two status markdown files, and new files under reviews/ and tools/queue/. None is an ADR record. The card's own LOAD-BEARING DECISION 2 section asked whether a comment was sufficient and raised the exact risk that a rebuild could erase it — the evidence shows the DDL comment exists (migration 0031 is in the diff) but does not show the ADR it was supposed to complement. This claim was made and not substantiated.

What would look like success while still being wrong:

1. The 119-item partition problem, which the card itself names. If the parser merges two real items into one row or splits one across two, checks 1, 5, 6, and 7 all pass because they share the parser's definition of "an item." Check 3 covers 10 of 119 by hand. The other 109 could be mis-partitioned and every check would agree.

2. Unrecognized status shapes hiding in NULL. An item stating "Status: BLOCKED on 2.13" in a shape the parser doesn't recognize as status prose lands in the 56 NULL rows. Check 2 confirms zero UNPARSED — but UNPARSED only fires on known shapes with unknown values. Check 4's NULL count of 56 matches, which proves self-consistency, not correctness.

3. The test suite was never run. pytest is not installed. Three test files were inspected and their asserted paths checked against the UNCHANGED set, but inspection is not execution. A test that importsa callable and checks a status code could still fail on import, on argument shape, or on a redirect it doesn't assert — and nothing was executed.

4. The round-trip check (7a-7d) is stronger than the card proposed. The card offered only byte concatenation and honestly flagged that it cannot catch merges or splits. The actual verification added three structural checks: 7b catches overlapping ranges (a split), 7c catches non-contiguous gaps (truncation compensated by a neighbor), and 7d catches item markers outside all rows (a merge that swallowed a marker). This is materially better than what was designed. But it still cannot catch the case where the parser's definition of an item boundary is wrong in a way that preserves contiguity — e.g., if a preamble line between two items is absorbed into the first item's body and the second item starts cleanly. Ranges are contiguous, non-overlapping, and every marker is inside a row, but the partition is still wrong. This is narrower than before but not closed.

5. The redirect on the old tool (check 10a-10d) proves the route no longer silently returns the wrong answer. It does not prove any caller was updated. The call-site survey lists two LIVE call sites — pipeline_views.py:40 and cis_dashboard.html:1672 — and both go through the redirect. But the redirect returns a different response shape (keys include 'item', 'reason', 'redirected_from') and any client code that unpacks the old shape will break silently or noisily. No check tests the client side of that route.

6. No agent has called cis_get_queue_item. Check 10e/10f prove the tool is registered and wired into HANDLERS. Nothing proves any agent will discover or use it. The card is honest about this ("does not prove callers were updated") but the claim as stated — "the old tool no longer returns a wrong answer silently" — is about the tool, not the callers, and that claim is established.

What is missing to fully establish the fifth claim (ADR-3.21-001):

- A file at a path like docs/decisions/ADR-3.21-001.md or a row in a project_decisions table, showing the withdrawn column decision recorded outside the DDL comment.
- Or grep output confirming the ADR reference exists somewhere other than the migration file.
- The migration file itself may contain the comment, but the claim distinguished "not only in a DDL comment" and the evidence does not show a second location.

If that ADR exists in a file not shown in the diff (because it was created in a prior packet), the claim could still be true — but the evidence does not show it, and I cannot treat what I cannot see as present.
