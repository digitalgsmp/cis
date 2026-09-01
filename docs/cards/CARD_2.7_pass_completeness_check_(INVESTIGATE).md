## CARD 2.7 — pass completeness check (INVESTIGATE)

```
Read-only.

PROOF: paste
  sqlite3 data/cis_memory.db "select found_by, count(*) from mining_candidates group by found_by"
  sqlite3 data/cis_memory.db "select origin, count(*) from mining_candidates group by origin"
  sqlite3 data/cis_memory.db "select count(distinct km_id) from mining_candidates where origin='kb'"

Then answer, in plain language: what parts of the corpus do you believe are
still unmined, and what pass would reach them?

Eric, 2026-08-30: "are you satisfied you have exhausted the search and have a
complete list from the information available to you?" Answer that honestly,
including if the answer is no.
```

---

# STAGE 3 — adjudicate, in batches
