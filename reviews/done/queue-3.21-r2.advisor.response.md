# Advisor review — queue-3.21-r2

- packet: `reviews/pending/queue-3.21-r2.md`
- advisor: advisor on port 8649, no tools
- run tag: queue-3.21-r2 @ 2026-09-08T23:11:24-05:00
- at: 2026-09-08T23:12:11
- prompt_tokens: 5685
- completion_tokens: 2638
- total_tokens: 8323
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

1. WHAT THIS DESIGN WOULD FAIL TO ESTABLISH

It fails to establish the correctness of the 56 items with NULL need_status. The contract admits it cannot distinguish between "no status prose" and "status prose in an unrecognized shape." An item could state its status in a format the parser misses, land in the 56 NULLs, and the inventory would be wrong while remaining perfectly self-consistent.

It fails to establish how dependencies are maintained going forward. By leaving queue_edges completely unintegrated, the design provides the nodes (queue_items) but orphans the edges. queue_edges is hand-made, unregenerated, and unread by code. If queue_items is regenerated but queue_edges is not, dependencies will drift. The design leaves 2.30's second question (dependencies) answered by stale data.

It fails to establish the mechanism for populating workflow_runs.queue_item_num. The packet admits nothing at intake currently knows the item number. If this is a manual operator step, the integrity of the "Did it succeed" check depends on human accuracy, which is unchecked. If no mechanism exists, the column stays empty.

It fails to establish the validity of the "Did it succeed" result. The packet notes item 1.24 records that phase rows say success on runs that failed downstream. If the join from queue_items through workflow_runs to gate_outcomes inherits that false positive, the design relocates the problem and reports a wrong answer rather than no answer.

2. WHAT RESULT WOULD SATISFY ITS VERIFICATION WHILE STILL BEING WRONG

The Hidden Status: An item contains status prose in an unrecognized shape (e.g., "State: Resolved"). The parser reads need_status = NULL. The lossless round-trip (Check 7) passes because body_md is intact. Check 4 passes (counts 56 NULLs). Check 3 passes. The design reports 56 items with no status, but one is actually DONE. The inventory is wrong but passes every check.

The False Success: Check 9 passes. A workflow_run is linked to queue_item_num '3.21'. The join reaches gate_outcomes, which reports success. The query returns success for 3.21. However, the run actually failed downstream (item 1.24 issue). The verification proves the join works, but the answer to 2.30's fourth question is wrong.

The Wrong Link: The operator manually enters the wrong queue_item_num at intake. Check 9 executes successfully, returning a result for the wrong item. The verification cannot detect this because it trusts the link.

LOAD-BEARING DECISION 1

Is it sufficient? No. Leaving build_plan_nodes inert is defensible, but leaving queue_edges unintegrated makes the design incomplete. queue_edges provides dependencies (2.30's second question), but it is hand-made, unregenerated, and unread by code. By creating queue_items without a dependency strategy, you are building half a queue. The objection that this is 2.12's failure with an extra list is valid because queue_edges will drift relative to queue_items the moment the markdown changes. queue_edges must either be integrated or explicitly superseded by a regenerated structure.

LOAD-BEARING DECISION 2

Is the join key on workflow_runs right? Yes, keeping queue_items as a read-only projection is the correct architecture. If the link lived on queue_items, regeneration would destroy it or violate the projection model.

Are the two problems fatal? Yes. The first (who writes it) means the column might remain empty, making Check 9 return nothing. The second (false success) means Check 9 might return a lie. The design must define the intake mechanism and must address the gate_outcomes reliability issue before this join answers anything. A join that returns a false positive is worse than no join at all.
