# CARD REVIEW — a current-item pointer, so the first slate does not propose finished work

**Nothing below has been built.** This is a card under review before it runs.

Then: **what would this card fail to establish, and what would look like success
while still being wrong?**

---

## WHY

GLM, 2026-09-09, on the slate build: *"The current-item pointer is the one thing
to build alongside it, because without it every slate will propose done items and
Eric will lose trust in the slate before the loop has a chance to improve."*

The frame gate and slate emission shipped as the previous card. This is the
second half GLM named. Nothing anywhere designates which build-list item is
being worked right now.

---

## THE CHANGE

**No schema change and no new table.** `project_state` already exists for this:
117 rows, 12 live, keys including `build_phase`, `current_direction` and
`next_action`, with supersession columns (`superseded_at`, `superseded_by`)
already used.

Add one key, `current_queue_item`, holding a build-list item number.

```
key    current_queue_item
value  '3.30'
source 'manual'          -- the CHECK allows git | gate | manual; Eric picks, so manual
```

**Why not a column on `queue_items`.** That table is regenerated wholesale from
`docs/UNIFIED_BUILD_LIST.md` on every extraction — a pointer stored there is
destroyed the next time anyone edits the markdown. `project_state` is a different
table and survives.

**Writing it.** A small helper, `tools/queue/set_current_item.py <item_num>`,
which supersedes the previous row rather than updating it, so the sequence of
what was worked is recoverable. It refuses an item number that does not exist in
`queue_items`.

**Reading it.** `spine.query_queue_item()` already returns an `answers_2_30`
block that currently says `what_is_the_current_item: "NOT AVAILABLE - nothing
designates one"`. That string becomes the item number when one is set.

---

## WHAT THIS CARD DOES NOT DO

- **It does not make the slate consult it.** The slate is prose from a model
  reading markdown. Whether it respects the pointer is not enforceable by this
  card, and claiming otherwise would be the tier-order illusion GLM already
  named: a property that appears to hold because the model happened to comply.
- **It does not decide who sets it.** Today Eric picks and someone runs the
  helper. Whether the loop sets it automatically after a pick is later work.
- **It does not mark anything DONE.** Completion still comes from the markdown.

---

## VERIFICATION

```sql
-- 1. the key exists and holds a real item
SELECT value FROM project_state
 WHERE key='current_queue_item' AND superseded_at IS NULL;
-- 2. it resolves to an actual row
SELECT count(*) FROM queue_items WHERE item_num =
  (SELECT value FROM project_state WHERE key='current_queue_item' AND superseded_at IS NULL);
                                                        -- expect 1
-- 3. exactly one live pointer, ever
SELECT count(*) FROM project_state
 WHERE key='current_queue_item' AND superseded_at IS NULL;   -- expect 1
-- 4. setting a second supersedes the first rather than duplicating it
-- 5. the helper REFUSES an item number that is not in queue_items
-- 6. the reader reports it: query_queue_item()['answers_2_30']
--    ['what_is_the_current_item'] returns the number, not "NOT AVAILABLE"
-- 7. re-run the extractor, then re-check 1 — the pointer SURVIVES regeneration
```

**Check 7 is the one that matters.** It is the whole reason the pointer is not a
column on `queue_items`.

---

## KNOWN WEAKNESS, STATED

A pointer that someone must remember to set is the same class of defect as build
list item 2.39 — a human remembering. If it is not set, check 1 returns nothing
and the reader honestly says NOT AVAILABLE, which is a safe failure. But a
**stale** pointer left on a finished item is worse than none: it would assert
something false rather than admit ignorance, and no check here detects it.

---

## MEASURED STATE

```
project_state       117 rows, 12 live, supersession columns in use
queue_items         120 rows, regenerated wholesale from the markdown
2.30's questions    one of four answered
current item        designated nowhere
```

## WHAT YOU ARE NOT BEING ASKED

Not whether the loop should exist. Not the slate's format. Not who sets the
pointer in the long run.
