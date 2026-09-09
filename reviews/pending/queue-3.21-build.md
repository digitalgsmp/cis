# PRE-FLIGHT REVIEW — 3.21 rewrite, third packet

**Nothing below has been built.** No table, no migration, no extractor. This is
a design under review before any of that.

Answer exactly this:

1. **What would this design fail to establish?**
2. **What result would satisfy its verification while still being wrong?**

Two decisions are marked **LOAD-BEARING**. Answer those where they appear.

---

## WHAT CHANGED SINCE THE PACKET YOU REVIEWED ON 2026-09-08

Three changes, each traceable to a specific objection you raised. **Judge whether
each fix answers the objection or only its wording.**

### CHANGE 1 — a reader is now named (Qwen's finding, raised by one lineage only)

> *"No code is proposed to query `queue_items`. The verification proves the table
> is correct; nothing proves it is useful. If no reader is built, this is 119
> rows of sediment alongside the other two structures."*

That was correct and it was the sharpest finding in either review. A table with
no consumer is item 2.37 — nothing tests the artifacts for whether anything
exercises them — being built deliberately. **See THE FIRST READER below**, which
names the query, its caller, and what it returns.

### CHANGE 2 — the *did it succeed* field is REMOVED, not fixed

> **GLM:** *"A join that returns a false positive is worse than no join at all."*
> **Qwen:** *"The join inherits that defect. The fourth of 2.30's questions is
> relocated from `queue_items` to `workflow_runs` but not resolved."*

You independently reached the same conclusion and Eric acted on it, 2026-09-09.
The previous packet proposed `workflow_runs.queue_item_num` to answer 2.30's
fourth question. **That column is withdrawn.** It is not deferred, not
implemented-but-unpopulated: it is not in this design.

The reasoning is yours: the join would inherit item 1.24's defect — phase rows
marked `success` on runs that failed downstream — so it would answer the fourth
question *wrongly* rather than not at all.

**The absence is recorded in the schema itself, not only here**, so that a reader
six months from now finds a decision rather than an oversight. See the `COMMENT`
convention in the DDL below.

**2.13 stays folded in.** It remains the prerequisite for eventually answering
the fourth question. What changed is that 3.21 no longer claims to answer it.

### CHANGE 3 — the round-trip check is restated at its real strength

> **Qwen:** *"If the parser's definition of 'item' is wrong — if it merges two
> items, or splits one, or includes a preamble as part of an item — the
> concatenation still equals the source file."*

Correct, and the previous packet oversold it. I offered the round-trip as the one
genuinely independent check. It is not: it proves **no bytes were lost**, not
that the partition is the one a human would make. Restated below with what it
does and does not establish.

### AND ONE CHANGE YOU DID NOT ASK FOR — the claim of "three of four" was wrong

Re-checked 2026-09-09 while naming the reader. The previous packet said this
design answers three of 2.30's four questions. **It does not, and the error was
mine in both prior packets.** See **WHAT 2.30 ACTUALLY GETS** below. This is the
most important correction in this packet and nothing in your reviews prompted it.

---

## Measured state, re-measured 2026-09-09

Every count below was taken today. The previous packet's figures had drifted
from 117 items to 119 in a single day, so nothing here is carried forward.

### The list

```
total items                       119     (98 as '### N.M', 21 as '- **N.M**')
duplicate item numbers              0
tier-header vs number mismatch      1     2.38 sits under '# TIER 3'
```

```
**Need:** OPEN                                    42 items
**Need:** UNASSESSED                              11 items
**Need: DONE ...** / **Need: HALF DONE ...**       5 items   (key inside the bold)
bare **DONE ...**, no Need key anywhere            5 items
no status prose of any kind                       56 items
                                                 ---
                                                 119
```

The 10 completion-bearing items, by number, read off the file by eye:

```
bare **DONE**       0.1  0.2  0.3  1.1  3.6
**Need: DONE**      1.17 3.22
**Need: HALF DONE** 0.4  1.20 1.22
```

A parser keyed on the literal `**Need:**` finds **53 of 119** and reports all ten
as absent — including 3.6, closed 2026-09-07, and 0.4, whose half-done state is
the basis of item 0.6.

### The adapter retraction, carried forward unchanged

The first packet claimed `cis_adapter.py` and `swa_adapter.py` write to
`build_plan_nodes`. **That was false and both of you built remedies on it.**

```
$ grep -rn "build_plan_nodes" runtime/tier7r/adapters/
cis_adapter.py:12:  C3 — REQUIREMENTS_RECOVERY → stage build_plan_nodes with status=PROPOSED
swa_adapter.py:292:            # Per §8.1, SWA Phase 45 should stage 4 candidate build_plan_nodes

cis_adapter.py:12   -> a line of the module docstring
swa_adapter.py:292  -> a comment; the code below it appends to a local list

$ grep -c "INSERT\|UPDATE\|create_node"   cis_adapter.py: 0    swa_adapter.py: 0

Only writers anywhere in the repo:
  tools/build_plan/seed_build_plan.py       (manual CLI)
  tools/build_plan/sync_project_state.py    (manual CLI)
```

### The two existing structures

```
build_plan_nodes       30 rows   26 COMPLETE, 3 DEFERRED, 1 PENDING
                                 newest completed_at 2026-06-28
queue_edges            45 rows   hand-extracted 2026-09-05/06
                                 no reader, no writer
                                 45 of 45 endpoints resolve against the 119 items
```

### Adjacent facts

```
mined_tasks       40 rows;  15 reference the list BY LINE NUMBER, all now stale
goal_references   30 rows;  30 empty dependency_node, 30 empty tier_advanced
project_state    117 rows;  build_phase = "Tier 6.5 COMPLETE. Tier 7 next."  (June)
next_actions      20 rows;  all in the old tier vocabulary
next free migration number   0031
```

---

## WHAT 2.30 ACTUALLY GETS — the correction neither review prompted

Item 2.30 asks for one place answering four questions. Both prior packets claimed
this design answers three. **Checked properly today, it answers one outright.**

| 2.30's question | What this design delivers |
|---|---|
| **What is the current item?** | **Derivable, not stored.** Nothing anywhere designates a current item. `project_state.build_phase` still reads *"Tier 6.5 COMPLETE. Tier 7 Router Reclassification next."* — June vocabulary, not unified-list items. The list's own rule is "work it in tier order," which a human applies. It becomes computable as *lowest tier, then lowest number, among items whose `need_status` is OPEN and whose `depends_on` edges are all DONE* — **but that requires current edges.** |
| **What does it depend on?** | **Requires current edges.** `queue_edges` is 45 hand-made rows from 2026-09-05 that nothing regenerates. Six items added since have dependency prose and zero edges. |
| **What was just done?** | **Delivered.** The 10 completion-bearing items, correctly classified, from `queue_items` alone. |
| **Did it succeed?** | **Absent by decision** — CHANGE 2 above. |

**So `queue_items` alone answers one of four, and two more become answerable only
when `queue_edges` is regenerated.** That is a materially weaker claim than either
prior packet made, and it is the honest one.

**This is why the `queue_edges` disposition is no longer optional.** GLM said so
in r2 — *"you are building half a queue"* — and was more right than the reasoning
given at the time. Qwen conditioned its approval of the deferral on a follow-on
card existing. **That card now exists**: `reviews/pending/queue-edges-disposition.md`,
written alongside this one. Its disposition is *regenerate*: keep the table,
discard the 45 hand-made rows, rebuild edges in the same extractor run from the
same `source_sha`, so the two tables cannot drift against each other.

**The question this puts to you:** given that two of 2.30's four questions depend
on it, should the edge regeneration be **inside** 3.21 rather than a follow-on?
The counter-argument is that merging them makes one change that creates a table,
deletes 45 rows, and builds two extractors — a blast radius item 2.38 exists to
warn about. I do not have a confident answer and would rather you name one.

---

## THE FIRST READER — named, with the hole it fills

**The reader-shaped hole already exists and is already wired to agents.**

`runtime/mcp_bridge/tools.py` exposes 18 MCP tools over the `cis-knowledge`
server, which is enabled in **six** agent profiles (`brain`, `draft`, `menter`,
`review1`, `review2`, `verify`). One of them is:

```python
"name": "cis_get_build_status"          # tools.py:31
def handle_get_build_status(arguments):  # tools.py:384
    return spine.query_build_status(arguments["node_label"])

def query_build_status(node_label, ...):  # spine.py:109
    SELECT node_label, status, tier, ... FROM build_plan_nodes WHERE node_label = ?
```

**An agent asking about item `3.21` today calls that tool and gets
`No build_plan_node found with label: 3.21`** — because the tool reads the June
build plan, keyed by a label the unified list does not use. The stateless agent
already reaches for a queue and already finds the wrong one.

**The first reader, concretely:**

- **Query:** `SELECT item_num, tier, title, need_status, scope FROM queue_items
  WHERE item_num = ?`, plus that item's `depends_on` and `blocks` edges from
  `queue_edges`.
- **Backed by:** a new `spine.query_queue_item(item_num)` in
  `runtime/mcp_bridge/spine.py`, following `query_build_status`'s existing shape
  and its read-only connection.
- **Called by:** container agents via a new MCP tool `cis_get_queue_item`,
  registered alongside the existing 18 in `runtime/mcp_bridge/tools.py`. No new
  transport, no new server, no profile change — the six profiles that carry
  `cis-knowledge` get it by existing wiring.
- **Returns:** the item, its status, its scope, and its dependency edges.

**What it deliberately does not do:** there is no `cis_get_current_queue_item`.
"Current" is not stored (see the table above), and a tool that computed it from
stale edges would be confidently wrong — the exact failure that removed the
fourth field in CHANGE 2. It becomes buildable when the edges are regenerated.

**The honest weakness in this reader.** Its dependency half returns rows from a
table nothing regenerates. Until the disposition card runs, `cis_get_queue_item`
answers "what is this item" correctly and "what does it depend on" from a
2026-09-05 snapshot. **Should the reader omit the edges entirely until they are
regenerated, rather than return stale ones?** I lean yes and have not made the
change, because it would leave the reader answering a single question and I want
your view on whether that is still worth shipping.

---

## LOAD-BEARING DECISION 1 — create `queue_items`; leave both existing structures untouched

Unchanged from r2, and you split on it.

> **GLM:** *"Is it sufficient? No… you are building half a queue."*
> **Qwen:** *"Sufficient for this card… a deferral, not a failure… acceptable if
> the deferral is recorded and the next card addresses it."*

**What has changed since you disagreed:** the follow-on card exists (path above),
which satisfies Qwen's stated condition. And the correction in **WHAT 2.30
ACTUALLY GETS** concedes GLM's substance — this *is* half a queue until the edges
are regenerated, and the packet now says so rather than arguing otherwise.

`build_plan_nodes` is still proposed to be left untouched: inert as a matter of
fact, no automated writer since June, read by a dashboard panel showing a
historical roadmap, and extending it would make `app.py:1077` render 119 extra
rows with no code change (item 2.38).

**Does the existence of the follow-on card change either of your answers?** GLM,
does it address the drift objection or only schedule it? Qwen, is the condition
met, or does the dependency of two of 2.30's questions on that card make it a
prerequisite rather than a follow-on?

---

## LOAD-BEARING DECISION 2 — the fourth question is absent by design, and says so in the schema

The withdrawn column is replaced by nothing. What takes its place is a recorded
absence:

```sql
CREATE TABLE queue_items (
    item_num        TEXT PRIMARY KEY,          -- '1.12', '3.21'
    tier            INTEGER NOT NULL,          -- from the item NUMBER, never the header
    title           TEXT NOT NULL,
    body_md         TEXT NOT NULL,             -- the item's prose, verbatim
    form            TEXT NOT NULL CHECK (form IN ('heading','bullet')),
    scope           TEXT,
    need_status     TEXT CHECK (need_status IS NULL OR need_status IN
                        ('OPEN','UNASSESSED','HALF_DONE','DONE','UNPARSED')),
    need_raw        TEXT,                      -- the literal prose the status came from
    source_line     INTEGER NOT NULL,          -- position at extraction, NOT an identity
    source_sha      TEXT NOT NULL,             -- sha256 of the whole markdown file
    extracted_at    TEXT NOT NULL DEFAULT (datetime('now'))

    -- DELIBERATELY ABSENT: any column linking an item to the run that advanced
    -- it, or to whether that run succeeded. Proposed 2026-09-08 as
    -- workflow_runs.queue_item_num and WITHDRAWN 2026-09-09 on dual-lineage
    -- review: the join would inherit item 1.24 (phase rows marked 'success' on
    -- runs that failed downstream) and answer 2.30's fourth question WRONGLY
    -- rather than not at all. Item 2.13 is the prerequisite for answering it
    -- properly. This is a decision, not an oversight. Do not add the column
    -- without reading 1.24 and 2.13 first.
);
```

SQLite preserves comments inside stored DDL, so `.schema queue_items` returns
that paragraph to anyone who asks the database what the table is.

**Is a comment sufficient to record a decision?** It is not enforced by anything
and a future migration can drop it silently by rebuilding the table — which is
exactly what migration 0030 did to two indexes on 2026-09-07, caught only because
one lineage looked for it. If you think this needs to be somewhere a rebuild
cannot erase, say where.

---

## The extractor's contract

The r2 contract could never complete a run: it said anything unclassifiable
becomes `UNPARSED` and any `UNPARSED` exits non-zero, while 56 of 119 items carry
no status prose at all. **Absent and unrecognizable are different conditions and
only one is an error.**

1. Parse both item forms — `### N.M` and `- **N.M**`.
2. Derive `tier` from the item number, never the enclosing `# TIER` header. They
   disagree once already (2.38 under Tier 3), and the number is what every
   cross-reference uses.
3. Recognise all four status spellings, including the two with the key inside the
   bold and the bare `**DONE ...**` markers with no key.
4. **No status prose → `need_status = NULL`, `need_raw = NULL`.** Normal,
   expected, today 56 of 119. Not an error; does not fail the run.
5. **`UNPARSED` means status prose is present but its value is unknown.** The
   literal text is kept in `need_raw`. Today this should be zero.
6. **Exit non-zero only if `UNPARSED > 0`**, printing the item numbers, so a new
   spelling can be added. That is the one condition where the extractor knows it
   is losing information.

**The failure this still permits, named rather than hidden:** an item stating its
status in prose the parser does not recognise *as status prose at all* — Qwen's
`"Status: BLOCKED on 2.13"` example — lands in the 56 as NULL and nothing fires.
Rule 5 catches unknown values, not unknown shapes. There is no check for it and I
am not claiming otherwise.

`source_line` is recorded and is explicitly not an identity. `mined_tasks`
references this list by line number in 15 rows and all 15 are stale; that is the
mistake this column must not repeat.

---

## The verification — and what each check actually proves

```sql
-- 1. inventory
SELECT count(*) FROM queue_items;                      -- expect 119
SELECT form, count(*) FROM queue_items GROUP BY 1;     -- expect heading 98, bullet 21

-- 2. nothing silently defaulted
SELECT count(*) FROM queue_items WHERE need_status='UNPARSED';   -- expect 0

-- 3. THE FIXTURE — 10 item numbers read off the file by hand, not parsed
SELECT item_num, need_status FROM queue_items
 WHERE item_num IN ('0.1','0.2','0.3','1.1','3.6','1.17','3.22','0.4','1.20','1.22');
       -- expect DONE on 0.1 0.2 0.3 1.1 3.6 1.17 3.22
       --        HALF_DONE on 0.4 1.20 1.22;  none OPEN, NULL, or UNPARSED

-- 4. distribution  (SHARES THE PARSER — proves self-consistency only)
SELECT need_status, count(*) FROM queue_items GROUP BY 1;
       -- expect OPEN 42, UNASSESSED 11, DONE 7, HALF_DONE 3, NULL 56   (= 119)

-- 5. identity is the number, not the line
SELECT count(*) FROM queue_items WHERE item_num IS NULL OR item_num='';   -- expect 0
SELECT item_num FROM queue_items GROUP BY 1 HAVING count(*)>1;            -- expect empty

-- 6. tier came from the number, not the header
SELECT item_num, tier FROM queue_items
 WHERE tier <> CAST(substr(item_num,1,instr(item_num,'.')-1) AS INTEGER);
       -- expect empty; 2.38 is the row that fails if the header was used

-- 7. ROUND-TRIP — see the restatement below
--    concat(body_md ORDER BY source_line) diffed against the source file

-- 8. staleness detectable
SELECT DISTINCT source_sha FROM queue_items;   -- one value; compare to sha256sum

-- 9. THE READER RETURNS SOMETHING
--    call cis_get_queue_item('3.21') and get the item back, not an error.
--    Today the equivalent call returns "No build_plan_node found with label: 3.21".
```

**Check 7 restated at its real strength.** Byte equality proves **no bytes were
lost** — nothing truncated, nothing dropped between items. It does **not** prove
the partition is the one a human would make: merge two adjacent items into one
row, or split one item across two, and the concatenation still equals the file.
Qwen said this in r2 and it is correct. The check catches loss, not
misclassification.

**What nothing in this card establishes:** that the 119 items the parser found
are the 119 a human would agree are items. Checks 1, 3, 4, 5, 6 and 7 are all
anchored to one definition of "an item." If that definition is wrong, every check
agrees and every check is wrong together. Check 3 is the only one anchored to
something no parser produced, and it covers 10 items out of 119.

---

## The backup, before anything runs

```bash
sqlite3 /mnt/projects/cis/data/cis_memory.db \
  ".dump queue_edges build_plan_nodes build_plan_dependencies" \
  > data/backups/queue_pre_3.21_$(date -u +%Y%m%dT%H%M%SZ).sql
test -s data/backups/queue_pre_3.21_*.sql || { echo "BACKUP EMPTY — STOP"; exit 1; }
cp docs/UNIFIED_BUILD_LIST.md \
   data/backups/UNIFIED_BUILD_LIST_$(date -u +%Y%m%dT%H%M%SZ).md
```

`workflow_runs` is no longer in the dump — the column that would have altered it
is withdrawn.

---

## What you are NOT being asked

Not whether the queue should move into the spine — decided, recorded as 3.21 and
2.30. Not which UI renders it. Not whether to retire `build_plan_nodes`. Not the
contents of the `queue_edges` disposition card, which is written but not being
reviewed here.

Only: **would this design and its verification prove what they claim, what could
pass every check above while still being wrong, and are the two LOAD-BEARING
decisions right?**
