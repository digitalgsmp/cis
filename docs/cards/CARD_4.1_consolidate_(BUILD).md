## CARD 4.1 — consolidate (BUILD)

```
Requires PENDING = 0. Paste that proof first.

CREATE TABLE mined_tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL, description TEXT NOT NULL,
  category TEXT, evidence_count INTEGER NOT NULL,
  first_raised TEXT, last_raised TEXT, sources TEXT,
  candidate_ids TEXT NOT NULL, in_build_list TEXT,
  depends_on TEXT
);

Every TASK candidate maps to exactly one row. None dropped. Group by category,
not by frequency.

PROOF:
  select count(*) from mined_tasks
  select sum(evidence_count) from mined_tasks
  select count(*) from mining_candidates where status='TASK'
EXPECT: the last two are equal.
```
