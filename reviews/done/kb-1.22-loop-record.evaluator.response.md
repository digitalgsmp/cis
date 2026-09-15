# Advisor review — kb-1.22-loop-record

- packet: `reviews/pending/kb-1.22-loop-record.md`
- advisor: evaluator on port 8650, no tools
- run tag: kb-1.22-loop-record @ 2026-09-10T00:04:20-05:00
- at: 2026-09-10T00:05:33
- prompt_tokens: 2313
- completion_tokens: 289
- total_tokens: 2602
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: CANNOT_TELL

The card explicitly states it solves capture but not retrieval, and that retrieval is what actually blocks 1.18-1.21. Capture is logically a prerequisite for retrieval, so this could be the right first half of a two-step unblock—but I cannot confirm that from what's here. I need to know: does the other half of 1.22 (packet assembly/retrieval) exist as a separate card, and is there a hard dependency requiring capture to land first? If retrieval work is ready to go and can be done in parallel or immediately after, this sequencing makes sense. If the other half doesn't exist yet, this card lands a solution that unblocks nothing.

---

Review of the proposal itself:

The technical design is sound. Writing at round time rather than closeout is correct—intermediate readers see the exchange as it happens. One row per round with a self-describing header is the right granularity; parsing prose into findings would be fabrication. Idempotency on source_key prevents duplication. The backfill prevents losing the 26 existing rounds.

Check 4 is the critical verification and is correctly identified as load-bearing. The failure mode it catches (counts going up from transcript ingestion, not from the loop itself) is exactly how this card could appear done while actually doing nothing.

Step 1's gate is appropriate—if advisor sources already exist in knowledge_messages, the premise is stale and the work should stop.

The exclusions are clearly stated and reasonable. Schema changes, retrieval, and commits are out of scope.

One gap: the backup instruction says to record row count before and after as "the reversible fact," but if the build fails mid-way and you need to restore, you'd need to delete rows by source_key pattern, not just verify a count. The backup of the script is sufficient for code rollback, but the data rollback path is implicit rather than explicit.

The verification sequence is thorough. Running backfill twice to confirm idempotency, and requiring a source-verified search hitthat didn't come from a transcript ensures the loop actually wrote the data rather than just counting accidental ingestions.

The proposal is technically sound. The design choices are correct, the verification is thorough, and the exclusions are appropriate. The only missing piece is explicit data rollback instructions beyond "restore from backup"—you'd need to delete rows where source='advisor_loop' if the build fails partway through.

The card is well-scoped and addresses a real gap. Whether it's the right work at the right time depends on the retrieval half of 1.22 existing and being sequenced to follow.
