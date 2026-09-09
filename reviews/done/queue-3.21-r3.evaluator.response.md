# Advisor review — queue-3.21-r3

- packet: `reviews/pending/queue-3.21-r3.md`
- advisor: evaluator on port 8650, no tools
- run tag: queue-3.21-r3 @ 2026-09-08T23:30:40-05:00
- at: 2026-09-08T23:32:48
- prompt_tokens: 5801
- completion_tokens: 2889
- total_tokens: 8690
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

...continuing from the verification analysis:

**Check 9 is the weakest check in the packet.** It says "call cis_get_queue_item('3.21') and get the item back, not an error." That proves the function executes and returns a non-null result. It does not prove the returned scope, title, body_md, or need_status are correct for 3.21. A reader that returns item 3.22's data when asked for 3.21 passes this check. The verification needs at minimum: assert the returned item_num equals the requested item_num, and assert at least one field (title or need_status) matches a hand-verified value for that specific item.

**Check 3 covers 10 of 119 items for status only.** It does not verify that the body_md for those 10 items is correct, that their title is correct, that their tier is correct, or that their scope is correct. A parser that correctly extracts need_status but mangles everything else for those 10 items still passes check 3. And the remaining 109 items have zero fixture-based verification of any field.

**Check 4 shares the parser with the extractor.** The expected distribution (OPEN 42, UNASSESSED 11, DONE 7, HALF_DONE 3, NULL 56) was produced by the same classification logic the extractor uses. If the parser's definition of "OPEN" includes items a human would call UNASSESSED, both the extractor and check 4 agree, and both are wrong. This is acknowledged in the packet but worth restating: check 4 proves internal consistency, not external correctness.

---

**What the design fails to establish:**

One: that any agent will actually call the new tool instead of the old one. The packet shows that cis_get_build_status exists, is wired to six profiles, and returns wrong results for unified-list items. The new cis_get_queue_item is added alongside it. Nothing in this design removes, deprecates, or redirects the old tool. An agent that learned to call cis_get_build_status("3.21") in June will continue to do so and continue to get "No build_plan_node found." The reader exists but nothing routes callers to it. The design establishes that a correct answer is available, not that it will be found.

Two: that returning stale edges is better than returning none. The reader's dependency half pulls from queue_edges, which is a 2026-09-05 snapshot with 45 hand-made rows. Six items added since have dependency prose and zero edges. An agent asking "what does 3.25 depend on" gets either stale data (if 3.25 happened to be in the 45) or nothing (if it was added after). The packet names this honestly and asks whether the reader should omit edges until they are regenerated. My answer: yes, omit them. A tool that returns partial dependency data from a snapshot nothing refreshes will cause agents to plan around edges that no longer exist or miss edges that do. Returning nothing forces the agent to say "I don't know." Returning stale data lets it say "I know" when it doesn't.

Three: that the comment-based decision record in the DDL survives the next table rebuild. The packet itself documents that migration 0030 silently dropped two indexes on 2026-09-07, caught only because one lineage looked for it. A COMMENT in SQLite DDL is preserved by .schema but is not preserved by a dump-and-reload cycle unless the dump uses .dump (which preserves CREATE TABLE verbatim) rather than a schema-generation tool. If migration 0032 or any future change rebuilds queue_items — even with identical columns — the comment is gone unless the author of that migration copies it forward by hand. The packet asks where else this should live. My answer: the decision should be recorded in a file that lives alongside the migrations — something like docs/decisions/0031-queue-items-no-success-link.md — referenced from the migration itself. A file in version control survives any table rebuild because it is not inside the table.

Four: that the 119 count is a stable target. The packet notes it drifted from 117 to 119 in one day. The extractor runs against a file that is actively being edited. The verification expects exactly 119. If someone adds an item between the count being taken and the extractor running, the verification fails on a correct extraction. The count check should be ">= 119" or should re-read the expected count from a fresh parse of the source file at verification time, not hardcode a number taken today.

---

**What passes every check while still being wrong:**

A parser that correctly identifies all 119 item boundaries and correctly classifies the 10 fixture items' statuses, but systematically misclassifies the remaining 109 items' statuses — for example, treating all "no Need key" items as NULL when some of them contain status information in non-standard prose — passes checks 1, 2, 3, 4, 5, 6, 7, 8, and 9. The packet acknowledges this gap (the "Status: BLOCKED on 2.13" example) and names it honestly. No objection there, except to note that the verification suite has no mechanism for discovering this class of error after deployment. A periodic sample — hand-verify 10 randomly chosen items monthly — would cost almost nothing and catch it.

A parser that correctly extracts item_num, tier, and need_status but truncates body_md at the first blank line within an item passes check 7 (the round-trip) if the truncation is compensated by the next item's body_md including a preamble. The concatenation still equals the source file. Check 7 catches lost bytes, not misallocated bytes. The packet says this. I agree. But no check addresses it, and the reader returns body_md to agents who will use it as the item's description.

---

**LOAD-BEARING DECISION 1: Create queue_items, leave existing structures untouched.**

The follow-on card for queue_edges exists, which satisfies Qwen's stated condition from r2. But the honest correction in "WHAT 2.30 ACTUALLY GETS" changes the calculus. Two of 2.30's four questions depend on regenerated edges. The packet concedes this is half a queue. The question it asks — should edge regeneration be inside 3.21 rather than a follow-on — needs an answer.

My answer: keep them separate, but change what the reader returns. Ship queue_items and the extractor in 3.21. Ship the reader without the dependency half. The reader answers "what is this item" — its number, tier, title, scope, status, body. That alone is strictly better than the current state, where agents get "No build_plan_node found." Ship the edge regeneration in the follow-on card, and add the dependency half to the reader in that same card. This avoids the blast radius of merging (item 2.38's warning), satisfies the condition that the follow-on exists and is scheduled, and avoids shipping a tool that returns stale dependency data to six agent profiles.

GLM's objection — "you are building half a queue" — is factually correct and remains correct under this answer. But half a queue that answers one question correctly is better than the current state, which answers zero questions correctly. The follow-on card completes the other half. The risk of merging is that a single change creates a table, deletes 45 rows, and builds two extractors — and if the edge extractor has a bug, the whole thing blocks. Separate cards let the item table ship and provide value even if the edge card is delayed.

**LOAD-BEARING DECISION 2: Fourth question absent by design, recorded in schema comment.**

The decision to withdraw the column is correct. The reasoning is sound — the join would inherit item 1.24's defect and answer wrongly rather than not at all. No objection to the withdrawal.

The recording mechanism is insufficient. A COMMENT in SQLite DDL is a good first step but is not durable against table rebuilds, as the packet itself demonstrates with migration 0030. The comment should exist AND the decision should be recorded in a version-controlled file outside the database — a decision record document referenced by the migration number. The migration file itself should contain a one-line reference to that document. This way, even if a future migration rebuilds the table and drops the comment, the decision record still exists in the repository and the migration history still points to it.

Is this worth blocking the card over? No. The comment is a meaningful improvement over no record at all, and the decision record file can be added as a trivial follow-up. But it should be named as a known gap in the same way the parser's blind spot for non-standard status prose is named.

---

**Summary of findings:**

The design is honest about what it does not establish, which is a significant improvement over the prior packets. The three changes directly address prior objections rather than their wording. The self-correction on "three of four" to "one of four" is the most important change in the packet and was not prompted by review — that is a sign of careful re-examination.

What it fails to establish: agent routing to the new tool, durability of the decision comment, stability of the 119 count, and correctness of body_md extraction for non-fixture items.

What passes verification while wrong: systematic misclassification of the 109 non-fixture items' statuses, and misallocation of body text across items that preserves byte-level round-trip equality.

The two load-bearing decisions are sound in substance. Decision 1 should ship with the reader omitting edges until they are regenerated. Decision 2's recording mechanism should be supplemented with a version-controlled decision record outside the database.
