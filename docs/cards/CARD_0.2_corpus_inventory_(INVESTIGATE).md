## CARD 0.2 — corpus inventory (INVESTIGATE)

```
Read-only.

PROOF: paste
  sqlite3 data/cis_memory.db "select source, count(*), sum(length(content)) from knowledge_messages group by source order by 2 desc"
  sqlite3 data/cis_memory.db "select min(created_at), max(created_at) from knowledge_messages"
and the Chroma collection count.

State which sources are the BUILD corpus and which are the archive that is
excluded by decision. Confirm the 900-char rechunk covered every build source —
if any source still has oversized chunks, semantic mining will miss inside them
and I need to know that before we start.
```

---

# STAGE 1 — the queue
