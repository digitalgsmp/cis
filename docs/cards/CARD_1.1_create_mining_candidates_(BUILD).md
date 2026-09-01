## CARD 1.1 — create mining_candidates (BUILD)

```
Back up data/cis_memory.db first. State where. Create one table only.

CREATE TABLE mining_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  origin TEXT NOT NULL,          -- 'kb' or 'file'
  km_id INTEGER,                 -- knowledge_messages.id when origin='kb'
  file_path TEXT,                -- when origin='file'
  source TEXT,
  created_at TEXT,
  found_by TEXT NOT NULL,        -- which pass found it, e.g. 'P3-semantic-gaps'
  query_used TEXT,               -- the exact query or pattern
  excerpt TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
     -- PENDING | TASK | ALREADY_IN_LIST | ALREADY_BUILT | NOT_A_TASK | DUPLICATE
  verdict_reason TEXT,
  task_title TEXT,
  existing_item TEXT,
  adjudicated_at TEXT,
  batch INTEGER
);
CREATE INDEX idx_mc_status ON mining_candidates(status);
CREATE UNIQUE INDEX idx_mc_km ON mining_candidates(km_id) WHERE km_id IS NOT NULL;
CREATE UNIQUE INDEX idx_mc_file ON mining_candidates(file_path) WHERE file_path IS NOT NULL;

The unique indexes make every pass safe to re-run — a chunk already queued is
skipped, not duplicated. found_by records which pass caught it first.

PROOF: .schema mining_candidates, and the row count (0).
```

---

# STAGE 2 — mining passes

**Run these one at a time.** Each ends with a count of NEW candidates. A pass
adding few new rows means that topic is exhausted — report it, don't pad it.

Semantic returns a ranked top-N per query, so no single query is comprehensive.
Coverage comes from many varied queries. **Use n_results=50 or higher per query
and take everything above the relevance floor, not the top 5.**
