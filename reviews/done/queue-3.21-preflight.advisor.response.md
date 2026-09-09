# Advisor review — queue-3.21-preflight

- packet: `reviews/pending/queue-3.21-preflight.md`
- advisor: advisor on port 8649, no tools
- run tag: queue-3.21-preflight @ 2026-09-08T22:21:53-05:00
- at: 2026-09-08T22:22:29
- prompt_tokens: 5515
- completion_tokens: 1681
- total_tokens: 7196
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

1. WHAT THIS DESIGN WOULD FAIL TO ESTABLISH

The fourth question. 2.30 requires four answers from one place; the schema and the verification together deliver three. Check 7 says so explicitly: "the fourth has no source column in this schema." There is no column anywhere linking a unified-list item to a workflow_run, a gate_outcome, or a commit. The design's own answer to LOAD-BEARING DECISION 2 says the join exists at read time from those evidence tables, but the join key does not exist. So the design does not establish the one thing 2.30 was opened to get.

"Depends on: nothing" is therefore false. 3.21 depends on 2.13, which is open and exists for exactly this reason. The packet asks me to say so plainly: 2.13 is a hard prerequisite. Without it, the spine can answer "what is the current item" and "what does it depend on" but cannot answer "what was just done, and did it succeed" from any place, joined or otherwise.

Second, the status model contradicts itself. The extractor contract (point 4) says any item whose status "cannot be classified" is written as UNPARSED, and point 5 says the extractor exits non-zero if any item is UNPARSED. The measured state says 56 items carry "no status signal of any kind." If "no status signal" means "cannot be classified," those 56 are all UNPARSED, the extractor exits non-zero, and nothing imports. If "no status signal" is different from "cannot be classified," the design never says how, and check 4 expects those 56 as NULL — a value the contract never instructs the extractor to write. The design does not establish what UNPARSED means versus NULL, so it does not establish that the extractor can ever complete a successful run.

Third, queue_edges has no regeneration path. The proposal regenerates queue_items from the markdown and detects its staleness via source_sha. queue_edges is 45 rows from September 5-6, materialized by hand, read by nothing, and the proposal adds foreign keys and two new edge kinds but no extractor, no regeneration hook, and no staleness check. Check 6 verifies that existing edges resolve to items; it does not verify that edges are complete, current, or that a re-extraction would produce them. So the design establishes freshness detection for one half of the queue and nothing for the other.

Fourth, the regeneration hook for queue_items is described as a pattern (the AGENTS.md analogy) but not specified. No pre-commit hook, no CI step, no cron entry is defined. The design says "a projection that is rebuilt from its source cannot drift" but does not establish the mechanism that rebuilds it. A projection with no rebuild trigger is stale by default.

Fifth, supersession of build_plan_nodes has no schema representation. The proposal says it "should be marked superseded in the same change" but specifies no column, no status value (the existing CHECK constraint has no SUPERSEDED), and no migration. Item 2.32 is open for exactly this. The design invokes 2.32 as support while leaving 2.32 unaddressed.

2. WHAT RESULT WOULD SATISFY THE VERIFICATION WHILE STILL BEING WRONG

The cleanest wrong-but-passing result: all eight checks pass and the spine still cannot answer "did it succeed." Check 7 is incomplete by design — the fourth question has no command. Nothing in the verification can fail on the fourth question because no command tests it. A design that delivers three of four answers passes every check and is wrong about the one 2.30 was created to secure.

Beyond that:

Check 4 certifies the status distribution, but the packet itself admits the numbers come from "one script's output, not an independent measure." If the extractor and check 4 share a parser, check 4 proves the parser agrees with itself. A parser that systematically misclassifies the 56 no-signal items — as NULL, or as UNPARSED,or as anything else — produces a distribution that matches itself and passes check 4. The only independent fact in the packet is that 117 items exist with 96 heading-form and 21 bullet-form, and that 10 specific items carry completion markers. Checks 1, 2, and 3 test those. Check 4 tests nothing the extractor did not already decide.

Check 8 detects staleness by comparing source_sha against the file on disk. But it does not detect a stale-but-matched state: if the markdown was edited and the extractor was re-run, the sha matches, but any completion that happened in the session — recorded in workflow_runs, gate_outcomes, or git — is invisible to the queue because no column links them. The projection is fresh. The answer to "did it succeed" is still nowhere. Check 8 passes and the fourth question is still unanswered.

Check 6 verifies that every edge resolves to an item. It does not verify that every item's dependencies are present as edges. The design claims the spine answers "its dependencies" (2.30's second question), but check 6 only proves the edges that exist are valid, not that the edges that should exist do. A queue_items table with 117 rows and zero edges in queue_edges passes check 6 (the UNION returns empty because there are no edges to violate) and the dependency question is silently unanswerable. The verification has no cardinality check on queue_edges against the dependency markers in the markdown prose.

Check 3 verifies 10 specific items. It does not verify that the 40 OPEN items are actually open. An extractor that defaults everything it cannot classify to OPEN would pass checks 1 and 5, and would pass check 2 only if it never writes UNPARSED. The contract says it must, but the verification cannot distinguish an extractor that obeys the contract from one that silently writes OPEN for unparseable items and then passes check 2 by construction. Check 4 would catch the distribution mismatch — unless the 56 no-signal items are genuinely ambiguous and the extractor's choice of OPEN for some subset produces a distribution that the same parser already computed. The packet warns about exactly this and the warning is correct.

A subtler wrong-but-passing result: the extractor derives tier from the item number, not the header. Check 4 does not verify tier values. The one known mismatch (2.38 under a Tier 3 header) is handled by design. But there is no check that the tier column matches the item number's integer part for all 117 rows. An extractor that misparses the integer from the dotted number on even one row passes every check, because no check reads tier.

Finally, the backup verifies that queue_edges, build_plan_nodes, and build_plan_dependencies are dumped and non-empty. It does not back up docs/UNIFIED_BUILD_LIST.md before the extractor modifies it — but the extractor does not modify the markdown, so that is fine. More importantly, it does not back up any table the migration might touch that is not listed. If the migration adds a SUPERSEDED status to build_plan_nodes' CHECK constraint, that is a schema change to a table with five production readers, and the backup does not cover the schema, only the data. A schema-only change that breaks the dashboard panel's try/except (which silently swallows the error and renders empty) would not be caught by any verification check in this packet.

LOAD-BEARING DECISION 1

The answer is a rationalization as stated, but the conclusion is probably correct. Here is the problem: "two tables where one is explicitly recorded as superseded is not two queues" is true only if the supersession is actually recorded. The proposal says build_plan_nodes "should be marked superseded in the same change" but specifies no mechanism. The existing CHECK constraint has no SUPERSEDED value. No column records supersession. Item 2.32 is open for precisely this. So the design invokes supersession as its defense against the two-queues objection while leaving the representation of supersession unspecified. That is circular: the decision is justified by a feature the design does not include.

The objection — two queue tables is 2.12 moved inside the database — is real but not decisive. build_plan_nodes is a completed historical plan with live readers who select WHERE project_id='cis' ORDER BY sequence with no filter. The right answer is not to extend build_plan_nodes (the semantic mismatch is genuine, and the five production readers would all change behavior), and not to drop it (the dashboard reads it, the adapters write to it, and dropping it breaks the roadmap panel that item 2.10 is already failing on). The right answer is to freeze it: add a supersession marker, which requires resolving 2.32 first, and stop writing to it. The adapters (cis_adapter, swa_adapter) that write PROPOSED rows are the actual problem — they are still writing to a table the design says is historical. The design does not address them. Until those writers are redirected or stopped, build_plan_nodes is not historical, it is live, and two live queue tables is the 2.12 failure relocated.

So: the decision to create queue_items separately is correct. The justification is incomplete because it depends on supersession being recorded, which is unspecified, and on the adapters being stopped, which is unaddressed. 2.32 is a soft prerequisite for the justification, not for the table creation. The adapter redirection is a hard prerequisite for the claim that build_plan_nodes is no longer a live queue.

LOAD-BEARING DECISION 2

The proposed answer — completion is joined at read time from evidence tables — is correct in principle and unexecutable today. There is no join key. The packet says so and asks me to confirm: 2.13 is a hard prerequisite. Without a column linking item_num to workflow_run_id or equivalent, the join the design depends on cannot be written. The design's answer to the fourth question is "join at read time" and the join does not exist. This is not a gap in verification; it is a gap in the design itself.

The deeper problem: even with the join key, a read-only projection cannot record what an agent just did in the current session. workflow_runs captures runs, but the link from a run to a queue item is what 2.13 is asking for. If 2.13 is resolved by adding a column to queue_items — say, last_workflow_run_id — then the projection is no longer read-only; an agent completing work writes to that column, and the "nothing writes prose back" promise is preserved only by a technicality (it writes a foreign key, not prose). If 2.13 is resolved by adding a column to workflow_runs, then workflow_runs gains a queue_item_num column and the join works, but the extraction of queue_items from markdown is still read-only and the completion write goes to a different table. That is probably the right architecture, but the design does not commit to it, and the verification has no check for it.

The AGENTS.md analogy is sound for the extraction direction. The pre-commit regeneration model works when the source is a file and the projection is derived. It does not work for the completion direction, because completion is not in the file and never will be. The design needs two paths: markdown to queue_items (regeneration, read-only, staleness-detectable), and evidence tables to the fourth question (join, requires 2.13, not yet built). The design describes the first path and invokes the second without specifying it.

So: the decision that the markdown stays authoritative and queue_items is derived is correct. The claim that this satisfies 2.30 is false until 2.13 is resolved. "Depends on: nothing" should read "Depends on: 2.13." The verification should include a check that the join key exists and that the fourth question returns a non-empty answer for at least one item. Without that, every check can pass and the spine still does not do what 2.30 requires.
