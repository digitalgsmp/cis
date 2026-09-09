# Advisor review — queue-3.21-build

- packet: `reviews/pending/queue-3.21-build.md`
- advisor: evaluator on port 8650, no tools
- run tag: queue-3.21-build @ 2026-09-09T00:02:47-05:00
- at: 2026-09-09T00:04:18
- prompt_tokens: 8479
- completion_tokens: 2789
- total_tokens: 11268
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

VERDICT: NOT_ESTABLISHED

The evidence establishes almost everything the card claimed. The table exists, the row counts and distributions match, the ten hand-verified items are correct, the reader returns items by identity, the old tool redirects properly, and dependency edges are correctly withheld. However, the card explicitly claimed that the withdrawn success-field decision is recorded in the project_decisions table as ADR-3.21-001, not just in a DDL comment. There is no evidence of this in the diff, the migration files, or the verification output. The verification script does not even check for it. Since I cannot see this action being taken, the evidence is insufficient to confirm that specific claim.

As for what would look like success while still being wrong, the most prominent risk is a semantic mismatch in how the parser defines an item. If the extractor merges two logical items into one row or splits a single item into two, but does so while preserving line contiguity and byte equality, the structural checks will still pass. The verification is largely self-referential, anchored to the parser's own rules rather than human intent. Additionally, if an item contains status prose in an unrecognized shape, it silently falls into the NULL bucket and passes the check for zero unparsed rows, losing information without failing the run. Finally, while the old tool redirects successfully, the tests could not be executed and no agent callers were verified to have been updated, meaning the system could still fail in live usage despite passing all local checks.
