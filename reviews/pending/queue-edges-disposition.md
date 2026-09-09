# CARD: QUEUE-EDGES-DISPOSITION

**Status: written, not run. This card exists because a deferral whose follow-on
is only "recorded on the queue" is the deferral becoming permanent.**

It is the follow-on Qwen made its r2 approval conditional on, and the answer to
GLM's objection that `queue_edges` drifts against `queue_items` the moment the
markdown changes. It is **not** part of 3.21 and must not be run inside it.

---

## The measured state, 2026-09-09

```
queue_edges                45 rows, extracted BY HAND 2026-09-05/06
  kinds present            depends_on, blocks, related
  kinds allowed, unused    blocked_by, supersedes, same_root
  endpoints resolving against the current 119 items:   45 of 45
  code that reads it:      none
  code that writes it:     none
```

```sql
CREATE TABLE queue_edges(
  from_num TEXT NOT NULL, to_num TEXT NOT NULL, kind TEXT NOT NULL
   CHECK(kind IN('depends_on','blocks','blocked_by','related','supersedes','same_root')),
  evidence TEXT NOT NULL,
  confidence TEXT NOT NULL CHECK(confidence IN('explicit','prose')),
  extracted_at TEXT DEFAULT(datetime('now')),
  PRIMARY KEY(from_num,to_num,kind));
```

**`supersedes` is already in that CHECK constraint and has never been used.**
Item 2.32 says supersession has no schema representation anywhere in the spine —
and half of one has existed since 2026-09-05, unused and unrecorded. 2.32 should
be corrected when this card runs, not left to be rediscovered.

**All 45 endpoints resolving is not evidence that the edges are current.** It
proves every item number mentioned still exists. It says nothing about whether
the edges are still correct, or whether edges that should exist are missing. The
file has grown by roughly 500 lines since the extraction, including six new items
(2.39, 2.40, 2.41, 0.6, 1.27, 1.28) that have dependency prose and **zero** edges.

---

## THE DISPOSITION: regenerate. Keep the table, discard the rows.

Three options were available. The reasoning for each:

| Option | Verdict |
|---|---|
| **Integrate the 45 rows as they stand** | **No.** They are a hand extraction from a file that has moved. Binding `queue_items` to them with a foreign key would make a fresh projection depend on stale hand-made data wearing a constraint. GLM's drift objection is correct and integration is what it warns against. |
| **Delete the table** | **No.** The schema is sound, the kind vocabulary is right, and it is the natural home for the two edge kinds items 2.32 and 3.25 are waiting on. Deleting it means rebuilding the same thing under a different name. |
| **Regenerate — keep the table, discard the rows** | **Yes.** |

**What that means concretely:**

1. `DELETE FROM queue_edges` — all 45 rows. They are superseded by regeneration,
   not preserved. Backed up in the dump first.
2. `queue_edges` becomes a **derived projection**, rebuilt by the same extractor
   run that builds `queue_items`, from the same source file and stamped with the
   same `source_sha`. One run, one source, two tables — so they cannot drift
   against each other, which is the whole of GLM's objection.
3. Edges are drawn from **explicit prose markers only**: `**Depends on:**`,
   `**Blocks**`, `**Related:**`. The existing `confidence` column already
   distinguishes `explicit` from `prose` and is the right place to record the
   difference in certainty between a `Depends on:` line and a `Related:` list.
4. Add the missing edge kind `documents` at that point — item 3.25 needs it for
   the REFERENCE DOCUMENTS table, which maps ten documents to the items they
   cover and is a real dependency map nothing treats as one. Not before; a kind
   with no extractor is what produced the unused `supersedes`.
5. Add a foreign key from `queue_edges` to `queue_items` **only after** step 2,
   when both tables come from one run.

**Why regeneration and not repair.** Repairing 45 hand-made rows requires knowing
which are still right, and that judgement is the same work as re-extracting them
with none of the reproducibility. A regenerated edge set can be re-derived after
any edit to the list; a repaired one is a second hand extraction with a fresher
date on it.

---

## What this card does NOT decide

- **Whether `build_plan_nodes` is retired.** Separate structure, separate
  decision, still open.
- **Whether the `Related:` lines should produce edges at all.** They are prose
  lists, often long, and an edge set that treats every `Related:` mention as a
  dependency will be dense and low-signal. The `confidence` column makes the
  distinction recordable; whether a `prose` edge should be *returned* to a caller
  is a question for whoever builds the reader.
- **Supersession semantics.** `supersedes` exists in the CHECK and is unused.
  This card notes that and corrects 2.32's claim; it does not define what a
  supersession edge means or which items carry one.

---

## Verification, when this card runs

```sql
-- 1. the hand-made rows are gone
SELECT count(*) FROM queue_edges WHERE extracted_at < '2026-09-09';   -- expect 0

-- 2. edges and items come from the same extraction
SELECT DISTINCT source_sha FROM queue_items;    -- one value
--    and queue_edges rows carry the same run's stamp

-- 3. every endpoint resolves
SELECT from_num FROM queue_edges WHERE from_num NOT IN (SELECT item_num FROM queue_items)
 UNION
SELECT to_num FROM queue_edges WHERE to_num NOT IN (SELECT item_num FROM queue_items);
                                                -- expect empty

-- 4. the six items added since 2026-09-05 now have edges
SELECT from_num, count(*) FROM queue_edges
 WHERE from_num IN ('0.6','1.27','1.28','2.39','2.40','2.41') GROUP BY 1;
                                                -- expect all six present

-- 5. explicit and prose edges are distinguishable
SELECT confidence, count(*) FROM queue_edges GROUP BY 1;   -- expect both kinds
```

**What this verification does not establish:** that the regenerated edge set is
*complete*. Nothing counts the dependencies a human would find in the prose
against the ones the extractor found. An extractor that silently drops every
`Related:` line passes all five checks above with a smaller, cleaner, wrong edge
set. That gap should be stated in the packet if this card is ever sent for
review.

---

## Related queue items

**2.32** — supersession has no schema representation. **Correct it:** half of one
exists in this table's CHECK constraint, unused since 2026-09-05.
**3.25** — the REFERENCE DOCUMENTS table is a dependency map with no edge kind.
This card adds `documents`.
**3.21** — creates `queue_items`; this card is its follow-on and the condition
Qwen attached to approving the deferral.
**2.12** — two queues drifting. Regeneration from one source in one run is the
structural answer to it here.
