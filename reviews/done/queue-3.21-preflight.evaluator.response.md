# Advisor review — queue-3.21-preflight

- packet: `reviews/pending/queue-3.21-preflight.md`
- advisor: evaluator on port 8650, no tools
- run tag: queue-3.21-preflight @ 2026-09-08T22:21:53-05:00
- at: 2026-09-08T22:24:26
- prompt_tokens: 5795
- completion_tokens: 1421
- total_tokens: 7216
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

**1. What this design would fail to establish**

The design cannot satisfy 2.30's fourth question — "did it succeed" — and it knows it. Verification check 7 flags this directly: "the fourth has no source column in this schema." The proposed answer (join at read time from `workflow_runs` and `gate_outcomes`) is architecturally sound but materially impossible today because no column anywhere links a unified-list item number to a workflow run. Item 2.13 exists for exactly this reason. This makes "depends on: nothing" false. 3.21 depends on 2.13, or at minimum on some linking mechanism being built first.

It also fails to establish which of the two queue tables is live. The design proposes marking `build_plan_nodes` as superseded via item 2.32, but 2.32 is open, unimplemented, and the document itself notes that "supersession has no schema representation." Without 2.32, you have two queue tables in one spine with no programmatic way to distinguish them — which is the 2.12 failure the item exists to prevent.

It fails to establish what happens to the two live writers — `cis_adapter` and `swa_adapter` — that currently stage PROPOSED rows into `build_plan_nodes`. The design notes they exist and uses their existence to argue against extending that table, but never says where they write after 3.21 lands. If they keep writing to `build_plan_nodes`, you have a live writer targeting a "superseded" table. If they move to `queue_items`, you have agents extending a queue the design says only Eric authors.

It fails to establish `queue_edges` freshness. The 45 rows are from 2026-09-05/06, no code reads or writes them, and the design proposes adding a foreign key to `queue_items`. If any of those 45 edges reference item numbers that were removed or renumbered since extraction, the FK constraint makes the migration fail. Check 6 would surface this, but the design doesn't say whether stale edges get deleted (losing possibly-correct data from items that were renumbered) or whether the FK gets deferred.

**2. What would satisfy verification while still being wrong**

An extractor that produces 117 rows with the correct status distribution but incorrect `body_md` content. The verification checks row counts, form distribution, status distribution, and identity uniqueness — it never checks that `body_md` for item `2.15` actually contains the prose of item 2.15. A parser that shifts item boundaries by one line, or that captures the wrong tier header's text, would pass every check while producing a queue whose content is misattributed. Any downstream consumer reading `body_md` to understand what an item requires would get wrong answers with no check to catch it.

An extractor that shares its parsing logic with the verification script. The document already identifies this risk for check 4, but it applies to checks 1, 2, and 3 as well. If the same regex or boundary-detection logic drives both extraction and verification, the checks prove the parser is consistent with itself, not that it matches the file. A bug that causes the parser to skip items matching a certain pattern would produce fewer than 117 rows (caught by check 1), but a bug that *merges* two adjacent items into one while splitting another item into two would still produce 117 rows and pass.

An extractor that correctly classifies all status signals but misreads the "bare DONE" markers. The five bare `**DONE ...**` items (0.1, 0.2, 0.3, 1.1, 3.6) have no `**Need:**` key — they're just bold text inside the item body. If the extractor finds these by scanning for `**DONE` anywhere in the body, it would also match items that mentionDONE in a different context — "the previous approach was **DONE** differently" — and classify those items as completed. Check 3 only verifies the five known bare-DONE items are marked DONE; it doesn't verify that items *without* DONE markers aren't falsely classified as DONE. Check 4 verifies the count is 7, but if the wrong 7 items are marked DONE, the count still matches.

A stale `queue_items` table that passes check 8's staleness detection but is never regenerated. Check 8 compares `source_sha` against the file's current hash — it detects staleness but doesn't prevent it. If the regeneration hook fails silently (the `try: ... except: pass` pattern already exists in `app.py`), the queue becomes stale and the only signal is a hash mismatch that nothing is watching for. The design detects staleness but establishes no mechanism to act on it.

**LOAD-BEARING DECISION 1 — the answer is insufficient, it is rationalization.**

The proposed answer — mark `build_plan_nodes` as superseded via item 2.32 — is a prose solution to a structural problem. 2.32 is open, unimplemented, and the document itself states "supersession has no schema representation." Without that representation, "superseded" is a comment in a migration file, not an enforced constraint. The two adapters (`cis_adapter`, `swa_adapter`) will continue writing PROPOSED rows into `build_plan_nodes` because nothing in 3.21 redirects them. You get two live tables with no programmatic way to distinguish which is authoritative, which is 2.12 relocated.

`build_plan_nodes` should be migrated: its 30 rows moved into `queue_items` with a clear mapping (node_label becomes title, tier becomes tier, status mapped to need_status), and the adapters redirected to write into `queue_items`. This is more work but it's the only way to actually have one queue. The alternative — keeping both tables and claiming one is superseded — only works if 2.32 is done first, which makes 3.21 depend on 2.32, contradicting "depends on: nothing."

**LOAD-BEARING DECISION 2 — the join is not available today, and this makes 2.13 a hard prerequisite.**

The proposed answer — join at read time from `workflow_runs` and `gate_outcomes` — is architecturally correct. An agent asserting its own completion is indeed a failure mode. But the join requires a linking column between `queue_items.item_num` and `workflow_runs`, and the document states explicitly: "there is no column anywhere linking a unified-list item to a workflow_run, and item 2.13 is open for precisely that reason."

This means 3.21 can deliver three of 2.30's four questions (current item, dependencies, what was just done via commit hash) but cannot deliver the fourth (did it succeed) without 2.13. The design should state "depends on: 2.13" or at minimum "depends on: a linking mechanism." As written, 3.21 claims it depends on nothing while describing an end state that requires 2.13 to be complete. The proposed answer describes the right architecture but wrong timing — it's what 3.21 plus 2.13 together deliver, not what 3.21 delivers alone.

The markdown-as-authoritative decision itself is correct. The operator authors prose, the table is a projection, staleness is detectable. That part holds. The problem is only that the design overpromises on 2.30's fourth question.
