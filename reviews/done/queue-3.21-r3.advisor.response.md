# Advisor review — queue-3.21-r3

- packet: `reviews/pending/queue-3.21-r3.md`
- advisor: advisor on port 8649, no tools
- run tag: queue-3.21-r3 @ 2026-09-08T23:30:40-05:00
- at: 2026-09-08T23:31:23
- prompt_tokens: 5539
- completion_tokens: 3784
- total_tokens: 9323
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

1. WHAT THIS DESIGN FAILS TO ESTABLISH

The packet names its own central gap honestly: the 119 items the parser finds may not be the 119 a human would agree are items. Checks 1, 3, 4, 5, 6, and 7 are all anchored to one definition of "an item." If that definition is wrong, every check agrees and every check is wrong together. Check 3 is the only parser-independent anchor and it covers 10 of 119. The design does not establish — and does not claim to establish — item boundaries beyond those 10.

Second, it fails to establish that dependency edges are current. The reader returns edges from a 2026-09-05 snapshot. Six items added since have dependency prose and zero edges. The packet says this. The follow-on card would fix it, but as proposed today, the reader answers "what does it depend on" from stale data — or omits it, which the packet leans toward but has not decided.

Third, it fails to catch status prose whose shape it does not recognize as status prose. Rule 5 catches unknown values, not unknown shapes. "Status: BLOCKED on 2.13" lands as NULL, not UNPARSED, and nothing fires. The packet names this. It is an acknowledged blind spot, not a hidden one.

Fourth, it does not establish what the current item is. Nothing stores it. project_state.build_phase reads June vocabulary. The packet says this is derivable once edges are current, but they are not current, so it is not derivable today.


2. WHAT RESULT WOULD SATISFY THE VERIFICATION WHILE STILL BEING WRONG

The strongest example: the parser merges two adjacent items into one row, or splits one item across two. The round-trip check passes because concatenation still equals the file. The count is 119. The form distribution is 98/21. The fixture covers 10 items, all correct. The other 109 could be mis-partitioned and every check passes — checks 1, 4, 5, 6, 7 all agree because they share the parser's definition. The design would be wrong about item boundaries and the verification would not detect it.

A second example: an item carries status prose in a shape the parser does not recognize as status prose — Qwen's "Status: BLOCKED on 2.13." It lands as NULL alongside the 56 items that genuinely carry no status prose. Check 2 reports zero UNPARSED. Check 4 shows 56 NULL, matching the expected count — because the misclassified item replaced one of the genuinely-absent ones, or because the genuinely-absent count was never independently verified beyond the 10-item fixture. The verification passes. The item is wrong.

A third: the reader returns stale edges and check 9 passes. The reader returns something, not an error. The edges are from 2026-09-05. The agent receives dependency information that is weeks old and treats it as current because the tool gives no staleness signal. Check 9 proves the reader is wired; it does not prove the reader is truthful.


THE THREE CHANGES

Change 1 (reader named): Answers the objection, not just its wording. The objection was that a table with no consumer is sediment. The reader is concrete: a named query, a named caller, an existing hole it fills — agents today call cis_get_build_status('3.21') and get the wrong answer. The reader fixes that. The honest weakness (stale edges) is named, not hidden. The open question — whether to omit edges entirely until regeneration — is the right question to be asking.

Change 2 (did-it-succeed field removed): Answers the objection. The objection was that the join inherits item 1.24's defect and answers the fourth question wrongly. Removing the column rather than fixing the join is the correct response. You cannot fix a join that depends on a known-bad signal. The absence is the answer.

Change 3 (round-trip restated): Answers the objection. The previous packet oversold the check as independent. It is now stated at its real strength: it catches byte loss, not misclassification. This matches Qwen's objection exactly.

The unasked correction (three-of-four was wrong): This is the most important change in the packet. The previous packets claimed three of four; the honest answer is one of four. This reframes the value proposition. A design that answers one question outright, with two more conditional on a follow-on card, is materially weaker than what was claimed before — and it is the honest framing.


LOAD-BEARING DECISION 1 — create queue_items; leave both existing structures untouched

The follow-on card addresses the drift objection by scheduling it, not by preventing it. Between 3.21 and the follow-on, the reader either returns stale edges (confidently wrong) or omits them (honestly incomplete). The packet leans toward omitting. If the reader omits edges, shipping the half-queue is defensible: it answers one question honestly and names what it cannot answer. If the reader includes stale edges, it is not defensible.

GLM's substance — this is half a queue — is now conceded in the packet itself. The follow-on card does not change that; it records the obligation. Qwen's condition (a follow-on card exists) is formally met. But the dependency of two of 2.30's four questions on that card makes it a prerequisite in substance if 2.30 is the requirement being satisfied. The counter-argument about blast radius is real — merging them creates, deletes, and builds in one change, which item 2.38 warns about.

My answer: keep them separate, and ship the reader without edges. A reader that says "this item exists, here is its status and scope, I cannot tell you its dependencies yet" is more useful than one that returns stale dependencies. The half-queue is honest when it names its limits. The follow-on card is the right boundary. But the reader must omit edges, not return them silently stale. That is the one change the packet has not yet committed to, and it should.


LOAD-BEARING DECISION 2 — the fourth question is absent by design, recorded in a COMMENT

A comment is necessary but not sufficient. The packet itself demonstrates why: migration 0030 silently dropped two indexes by rebuilding a table, caught only because one lineage looked for it. A comment in stored DDL survives until someone rebuilds the table, at which point it vanishes without error.

The comment should stay — it is the third line of defense and the one a developer running .schema will actually see. But the decision should also be recorded in two places a rebuild cannot erase:

First, the migration file that creates this table. A migration is version-controlled and reviewed. A comment in the migration header saying "do not add a run-linking column without reading 1.24 and 2.13" persists in source control even if the table is later rebuilt.

Second, a schema_decisions table — a single row with table_name, decision, rationale, decided_at — that any future migration must preserve or explicitly drop. This is not enforced by the database engine, but it is enforced by review: a migration that drops a row from schema_decisions forces a reviewer to ask why, which is the check that caught migration 0030's index drop.

Neither of these is invulnerable. But they move the decision from one location that a single rebuild erases to three locations that require simultaneous erasure, and the third is version-controlled source that no migration touches.
