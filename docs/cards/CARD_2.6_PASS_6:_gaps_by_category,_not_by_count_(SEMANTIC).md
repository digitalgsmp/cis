## CARD 2.6 — PASS 6: gaps by category, not by count (SEMANTIC)

```
Eric, 2026-08-29: "instead of eliminating because of number counts, look at
what they say and align them by category."

Take the categories the pipeline actually has — retrieval, gates, approval,
review, verification, ingestion, storage, agent behaviour, operator interface,
failure handling, self-improvement — and run semantic queries against each one
asking what is missing or broken in it.

This catches things the other passes missed because nobody phrased them as a
problem. found_by='P6-category'.

PROOF: per category, the query used, hits, and new rows. Plus any category that
returned nothing — that is either a clean subsystem or an unsearched one, and
I want to know which you think it is.
```
