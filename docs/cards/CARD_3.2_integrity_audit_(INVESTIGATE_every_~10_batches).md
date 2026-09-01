## CARD 3.2 — integrity audit (INVESTIGATE — every ~10 batches)

```
Read-only.
PROOF: paste
  select count(*) from mining_candidates where status!='PENDING' and (verdict_reason is null or verdict_reason='')
  select count(*) from mining_candidates where status='TASK' and (task_title is null or task_title='')
  select count(*) from mining_candidates where status='ALREADY_BUILT' and verdict_reason not like '%:%'
  select id,status,verdict_reason,task_title,substr(excerpt,1,250) from mining_candidates where status!='PENDING' order by random() limit 10

EXPECT: first three counts are 0. Any row failing them goes back to PENDING.
The sample is for me to read.
```

---

# STAGE 4 — the list
