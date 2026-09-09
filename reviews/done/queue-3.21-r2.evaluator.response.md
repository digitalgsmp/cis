# Advisor review — queue-3.21-r2

- packet: `reviews/pending/queue-3.21-r2.md`
- advisor: evaluator on port 8650, no tools
- run tag: queue-3.21-r2 @ 2026-09-08T23:11:24-05:00
- at: 2026-09-08T23:14:31
- prompt_tokens: 5993
- completion_tokens: 2977
- total_tokens: 8970
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

**1. What this design would fail to establish**

The design establishes that a faithful projection of the markdown exists in SQL. It does not establish:

- That the projection will be read. No code is proposed to query `queue_items`. The verification proves the table is correct; nothing proves it is useful. If no reader is built, this is 119 rows of sediment alongside the other two structures.

- That the markdown's status classifications mean what the schema says they mean. An item with no status prose gets NULL. That is a normal outcome per the contract — but it is also the outcome for an item whose status is stated in a form the parser does not recognize as status prose. The contract names this failure and does not check for it. 56 items land in NULL; the design cannot distinguish "no status stated" from "status stated in an unrecognized shape."

- That the join key from DECISION 2 will be populated. The design proposes the column but does not propose the writer. If nothing writes `workflow_runs.queue_item_num`, the fourth of 2.30's questions — did it succeed — remains unanswered. The schema exists; the mechanism does not.

- That the join answers the right question. Even if the key is populated, a run linked to an item tells you a run happened. Whether it succeeded depends on `gate_outcomes` and terminal state, and item 1.24 records that phase rows say `success` on runs that failed downstream. The join inherits that defect. The design relocates the question from `queue_items` to `workflow_runs` but does not resolve it.

- That `queue_items` is authoritative. DECISION 1 explicitly defers the disposition of `build_plan_nodes` and `queue_edges`. That is a valid staging choice, but it means this design does not establish which of the three structures is the source of truth. It establishes that `queue_items` is the projection of the unified build list; it does not establish that the other two are retired, subordinate, or integrated.

**2. What would satisfy verification while still being wrong**

- The parser could consistently misidentify item boundaries, and the round-trip check would pass. If the parser's definition of "item" is wrong — if it merges two items, or splits one, or includes a preamble as part of an item — the concatenation still equals the source file. The lossless round-trip proves no bytes are lost; it does not prove the partition is the partition a human would make. All three verification measures share the parser's definition of what an item is. If that definition is wrong, all three agree and all three are wrong together. The design names this and does not check for it.

- The 56 NULL items could include items whose status is stated in prose the parser does not recognize as status. The extractor contract treats absent and unrecognizable as the same condition (both NULL). A run with zero UNPARSED items passes check 2. But if one of those 56 items says "Status: BLOCKED on 2.13" and the parser does not recognize "Status:" as a key, the item lands in NULL and the run succeeds. The contract catches unknown values; it does not catch unknown shapes.

- The join key could be populated incorrectly. If intake writes the wrong item number, or writes it at the wrong time, the verification has no check for this. Check 9 proposes four queries but does not propose a check that the join key is correct — only that it exists. A run linked to item 3.21 when it actually worked on 3.22 passes every check.

- The table could be created and never queried. Every verification check passes; no code reads the table. The design proves the projection is faithful; it does not prove the projection is used. This is not a verification failure — it is a failure the verification does not attempt to catch.

**LOAD-BEARING DECISION 1 — create `queue_items`, leave both existing structures untouched**

The reasoning is sufficient for this card. `build_plan_nodes` is inert as a matter of fact: no automated writer, 29 of 30 rows complete or deferred, newest completion ten weeks old, read only by a dashboard panel displaying a historical roadmap. Extending it is not viable: different schema, different identity, and `app.py:1077` would render 119 new rows with no code change. `queue_edges` is 45 rows of hand-made sediment with no reader and no writer; binding it with an FK would be a dependency on stale data.

The objection — three queue-shaped structures with no authority — is real, but it is a deferral, not a failure. The design explicitly states that retiring `build_plan_nodes` is outside this card. That is a staging decision. The design establishes `queue_items` as the projection of the unified build list; it does not establish what happens to the other two. That gap is acknowledged and postponed.

The honest answer is not that `queue_items` must not be created until `build_plan_nodes` is dispositioned. The honest answer is that this design creates a third structure and defers the authority question. That is acceptable if the deferral is recorded and the next card addresses it. If the next card does not exist, the deferral becomes permanent and the design is incomplete. The packet does not state whether a follow-on card exists.

**LOAD-BEARING DECISION 2 — the join key on `workflow_runs`**

The placement is correct. If the key lived on `queue_items`, an agent completing work would write into the projection, and the next regeneration would destroy that write or have to preserve it — at which point the table is no longer derived. Putting the key on `workflow_runs` keeps `queue_items` read-only.

The mechanism is incomplete. The design does not establish who writes `queue_item_num` or when. If the answer is "the operator states it on the card," that is a human step in the mechanism, and it should be recorded as one. If the answer is "intake derives it," nothing at intake currently knows the build-list item number, so the mechanism does not exist.

The design does not establish that the join answers "did it succeed." A run linked to an item tells you a run happened. Whether it succeeded comes from `gate_outcomes` and terminal state, and item 1.24 records that phase rows say `success` on runs that failed downstream. The join inherits that defect. The fourth of 2.30's questions is relocated from `queue_items` to `workflow_runs` but not resolved.

The blast radius of altering `workflow_runs` is not enumerated. Item 2.38 exists because that is how a schema change goes wrong. The design should state which code touches `workflow_runs` and whether the new column affects any of it.

**What is missing**

- A reader for `queue_items`. The verification proves the table is correct; nothing proves it is used.

- A writer for `workflow_runs.queue_item_num`. The design proposes the column but not the mechanism that populates it.

- A check that the join answers "did it succeed" rather than "did a run happen." The design names the defect (item 1.24) but does not resolve it.

- A statement of whether a follow-on card exists to disposition `build_plan_nodes` and `queue_edges`. If it does not, the deferral is permanent.

- An enumeration of what touches `workflow_runs` and whether the new column affects any of it.
