## CARD 2.3 — PASS 3: keyword sweep for what semantic misses (FTS5)

```
Supplement, not the primary. Semantic misses exact identifiers, file names,
error strings and table names — things with no semantic neighbourhood.

FTS5 over the build corpus. found_by='P3-keyword'.
  TODO, FIXME, XXX, HACK
  not implemented, never built, never wired, does not exist
  deferred, postponed, blocked on, waiting on
  .py .sh .md .sql file references
  table and column names that appear in a complaint
  error strings and exception names

Dedup against what P1 and P2 already queued — the unique index handles it;
report how many were already present versus genuinely new.

PROOF: new rows, already-present count, and the pattern breakdown.
EXPECT: a smaller number than P1/P2. If it is larger, the semantic passes were
under-run and I want to know that.
```
