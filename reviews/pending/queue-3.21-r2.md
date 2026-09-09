# PRE-FLIGHT REVIEW — 3.21 rewrite, second packet

**Nothing below has been built.** No table, no migration, no extractor. This is
a design under review before any of that.

Answer exactly this:

1. **What would this design fail to establish?**
2. **What result would satisfy its verification while still being wrong?**

Two decisions are marked **LOAD-BEARING**. Answer those where they appear.

---

## THIS IS A REWRITE. Here is what the first packet got wrong.

An earlier version was reviewed on 2026-09-08 by two lineages. It produced three
premise failures and one design gap. Each is addressed below and labelled, so you
can judge whether the fix answers the objection or only its wording. **Say
plainly if any remains unfixed.**

### CORRECTION 1 — I gave you a false premise, and you both built on it

The first packet stated that `cis_adapter.py` and `swa_adapter.py` are live
writers staging `PROPOSED` rows into `build_plan_nodes`. **That was wrong.** Both
lineages used it: one made adapter redirection "a hard prerequisite," the other
proposed migrating `build_plan_nodes` wholesale on the strength of it.

The complete evidence, measured 2026-09-09:

```
$ grep -rn "build_plan_nodes" runtime/tier7r/adapters/
cis_adapter.py:12:  C3 — REQUIREMENTS_RECOVERY → stage build_plan_nodes with status=PROPOSED
swa_adapter.py:292:            # Per §8.1, SWA Phase 45 should stage 4 candidate build_plan_nodes

$ sed -n '12p' cis_adapter.py     ->   a line of the module docstring
$ sed -n '292p' swa_adapter.py    ->   a comment; the code below it appends to a
                                       local `candidates` list of SWA labels

$ grep -c "INSERT\|UPDATE\|create_node" on both files
cis_adapter.py: 0
swa_adapter.py: 0

Only writers of build_plan_nodes anywhere in the repo:
  tools/build_plan/seed_build_plan.py       (manual CLI, seeds nodes)
  tools/build_plan/sync_project_state.py    (manual CLI, syncs project_state)
```

**Nothing automated has written that table since June 2026.** Both remedies built
on the false version collapse. This changes the disposition question below, so
please re-derive it rather than carrying your previous answer forward.

### CORRECTION 2 — the extractor contract could never complete a run

You found this. The first contract said any item whose status "cannot be
classified" becomes `UNPARSED`, and that any `UNPARSED` exits non-zero. **56 of
119 items carry no status prose at all**, so the extractor would have exited
non-zero on every run and imported nothing, ever.

The defect was conflating two different conditions. The rewrite separates them —
see **The extractor's contract** below.

### CORRECTION 3 — the verification shared a parser with the thing it verified

You both raised this; one extended it to the counts, the other to `body_md`
content. **See STEP 2 — how the check avoids sharing a parser**, which is now a
section of its own and answers the `body_md` objection directly.

### THE DESIGN GAP — 2.13, which you both found independently

You both said "Depends on: nothing" was false and that 2.13 is a hard
prerequisite. **That was accepted. Eric folded 2.13 into 3.21 on 2026-09-09** and
the build list now records the two as one design. What that means for this packet
is in **LOAD-BEARING DECISION 2**.

---

## Measured state, all verified 2026-09-09

### The list

```
total items                       119     (98 as '### N.M', 21 as '- **N.M**')
duplicate item numbers              0
tier-header vs number mismatch      1     2.38 sits under '# TIER 3' (line 2802)
file length                     3,284 lines
```

Status is prose in four spellings, classified per item with boundaries at the
next item start of either form or the next `# TIER` header:

```
**Need:** OPEN                                    42 items
**Need:** UNASSESSED                              11 items
**Need: DONE ...** / **Need: HALF DONE ...**       5 items   (key inside the bold)
bare **DONE ...**, no Need key anywhere            5 items
no status prose of any kind                       56 items
                                                 ---
                                                 119
```

The 10 completion-bearing items, by number:

```
bare **DONE**       0.1  0.2  0.3  1.1  3.6
**Need: DONE**      1.17 3.22
**Need: HALF DONE** 0.4  1.20 1.22
```

A parser keyed on the literal `**Need:**` finds **53 of 119** and reports **all
ten** as absent — including 3.6, closed 2026-09-07, and 0.4, whose half-done
state is the entire basis of item 0.6.

**These counts moved since the first packet** (117 items, OPEN 40). Two items
were added in the interval. Every number in this packet was re-measured today
rather than carried forward; the queue's own item 2.39 exists because that does
not happen by default.

### The two existing structures

```
build_plan_nodes            30 rows   26 COMPLETE, 3 DEFERRED, 1 PENDING
                                      newest completed_at 2026-06-28
build_plan_dependencies     25 rows
```

Readers: `runtime/db/build_plan.py`, `runtime/app.py:1077` (the dashboard roadmap
panel, inside a bare `try/except Exception: pass`), `runtime/db/database.py:89`.
Writers: the two manual CLI scripts named in CORRECTION 1. It holds the **June
2026 dependency-graph build plan** — `Tier 8 — MCP Bridge`, `Tier 12 — Knowledge
Base Ingestion` — and shares no item numbering with the unified list.

```
queue_edges                 45 rows   extracted 2026-09-05/06, by hand
  kinds present             blocks, depends_on, related
  kinds allowed but unused  blocked_by, supersedes, same_root
  endpoints resolving against the current 119 items:  45 of 45, zero failures
  code that reads it:  none.   code that writes it:  none.
```

Note `supersedes` is already in its CHECK constraint and has never been used —
item 2.32 says supersession has no schema representation, and half of one exists.

### Adjacent facts

```
mined_tasks                 40 rows;  25 have an empty in_build_list;
                            15 reference the list BY LINE NUMBER, all now stale
goal_references             30 rows;  30 empty dependency_node,
                                      30 empty tier_advanced      <- 2.13's real symptom
no migration-tracking table exists                                (item 2.5)
next free migration number  0031
nothing in tools/ or runtime/ parses docs/UNIFIED_BUILD_LIST.md
```

---

## LOAD-BEARING DECISION 1 — create `queue_items`; leave both existing structures untouched

**Proposed: create `queue_items`. Do not extend, migrate, drop, or mark anything.
`build_plan_nodes` and `queue_edges` are left exactly as they are.**

This replaces the first packet's proposal, which was to mark `build_plan_nodes`
superseded in the same change. **You both rejected that and you were right:** the
justification depended on item 2.32 supplying a supersession representation that
does not exist, so the decision rested on a feature the design did not include.
One of you called it circular. The rewrite drops the claim rather than restating
it.

The reasoning now offered instead, which you should attack:

- **`build_plan_nodes` is inert, as a matter of fact rather than of intent.** No
  automated writer exists (CORRECTION 1), 29 of 30 rows are COMPLETE or DEFERRED,
  and the newest completion is 2026-06-28 — over ten weeks old. It is read by a
  dashboard panel that displays a historical roadmap, which is a legitimate thing
  for it to be.
- **Extending it was never viable.** `tier` holds labels like `7.5a` and
  `ENFORCEMENT`; `sequence` is a total order the unified list does not have;
  identity is `node_label`, not a dotted number. And `app.py:1077` selects
  `WHERE project_id='cis' ORDER BY sequence` with no other filter, so 119 new
  rows would change what it renders with no code change anywhere (item 2.38).
- **`queue_edges` gets no foreign key in this change.** All 45 endpoints resolve
  today, so an FK would succeed — and would bind a new table to 45 rows that
  nothing regenerates and nothing reads. That is a dependency on stale hand-made
  data wearing a constraint. It stays as it is, explicitly not integrated.

**The objection this invites, stated so you can press on it:** three
queue-shaped structures in one spine, with nothing in the schema saying which is
authoritative, is item 2.12's two-lists failure with an extra list.

**The proposed answer:** 2.12 is a failure of two sources being *authoritative
and drifting*. A table with no writer cannot drift; a table with no reader and no
writer is not a queue, it is 45 rows of sediment. What is missing is not a
supersession flag but the fact — which is now measured and recorded in the build
list rather than asserted in a migration comment.

**Is that sufficient, or is it the same rationalization with better evidence?**
If the honest answer is that `queue_items` must not be created until
`build_plan_nodes` is dispositioned, say so — retiring it is explicitly outside
this card, so that answer blocks the work rather than shaping it, and it should
be given anyway if it is right.

---

## LOAD-BEARING DECISION 2 — where the 2.13 join key lives

2.13 is folded in. The fourth of item 2.30's questions — **did it succeed** — has
no join key today, and supplying one is 2.13.

**Carry 2.13's own correction forward.** It was rescoped on 2026-09-07 and its
original text is wrong in a way that matters here:

- 2.13 said the Eric Gate briefing's *Dependency Node* and *Tier Advanced* fields
  render blank because `build_plan_nodes.workflow_run_id` is NULL.
- **They do not.** `build_plan_nodes` appears **zero times** in
  `tools/eric_gate/build_briefing.py`. Both fields come from `goal_references`
  (`build_briefing.py:252-283`, rendered at `568-569`).
- **All 30 `goal_references` rows are empty in both columns** — measured again
  today. That is the real cause.
- So a fix that populates `build_plan_nodes.workflow_run_id` would pass its own
  verification and leave the reported symptom untouched.

**Proposed: the link is a column on `workflow_runs`, not on `queue_items`.**

```sql
ALTER TABLE workflow_runs ADD COLUMN queue_item_num TEXT REFERENCES queue_items(item_num);
```

The reasoning, which you should attack:

- `queue_items` stays a **read-only projection** regenerated from the markdown.
  If the link lived on `queue_items`, an agent completing work would write into
  the projection, and the next regeneration would either destroy that write or
  have to preserve it — at which point it is no longer derived and 2.12 is back.
- A run already knows what it is working on at intake. `workflow_runs` is the
  row that exists at the moment the link becomes true.
- *Did it succeed* is then a join from `queue_items` through `workflow_runs` to
  `gate_outcomes`, none of it authored by the agent whose work is being judged.
  An agent writing its own completion into the queue is failure mode 1 given a
  schema to live in.

**The objection this invites:** this is a schema change to `workflow_runs`, the
busiest table in the spine, proposed in the same breath as a new table. Its blast
radius is not enumerated here, and item 2.38 exists because that is how a schema
change goes wrong.

**Two further things I do not have answers for, and would rather you name than
I guess:**

1. **Who writes `queue_item_num`, and when?** Intake is the honest moment, but
   nothing at intake currently knows the build-list item number. If the answer is
   "the operator states it on the card," that is a human step in the middle of
   the mechanism, and it should be recorded as one rather than discovered later.
2. **Does this actually answer 2.30's fourth question, or relocate it?** A run
   linked to an item tells you a run happened. Whether it *succeeded* comes from
   `gate_outcomes` / the run's terminal state — and item 1.24 records that phase
   rows say `success` on runs that failed downstream. If the join inherits that,
   the fourth question is answered wrongly rather than not at all, which is
   worse.

---

## The proposed schema

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
);
```

`tier` comes from the integer part of `item_num`, **not** from the enclosing
`# TIER` header — they already disagree once (2.38 under Tier 3), and the number
is what every cross-reference in the file uses.

`source_line` is recorded and is explicitly not an identity. `mined_tasks`
references this list by line number in 15 rows and every one of them is stale;
that is the mistake this column must not repeat.

---

## The extractor's contract — rewritten

The first version failed because it treated **absent** and **unrecognizable** as
one condition. They are different, and only one is an error.

1. Parse both item forms — `### N.M` and `- **N.M**`.
2. Derive `tier` from the item number.
3. Recognise all four status spellings, including the two where the key sits
   inside the bold and the bare `**DONE ...**` markers with no key.
4. **An item with no status prose gets `need_status = NULL`, `need_raw = NULL`.
   This is a normal, expected outcome and today applies to 56 of 119 items.** It
   is not an error and does not fail the run.
5. **`UNPARSED` means something narrower: status prose is present but its value
   is not in the known vocabulary.** The literal text is kept in `need_raw`.
   Today this should apply to **zero** items.
6. The extractor **exits non-zero only if `UNPARSED > 0`**, and prints the item
   numbers so the spelling can be added. A new status spelling appearing in the
   markdown is the one condition that should stop the import, because it is the
   one condition where the extractor knows it is losing information.

**The failure this still permits, named rather than hidden:** an item that states
its status in prose the parser does not recognise *as status prose at all* is
indistinguishable from an item with no status. It lands in the 56 as NULL, and
nothing fires. Rule 5 catches unknown *values*, not unknown *shapes*. I do not
have a check for that and would rather say so than imply the contract is closed.

---

## STEP 2 — how the check avoids sharing a parser with the extractor

You both raised this. It cannot be fully solved — a parser's output checked by
the same program proves self-consistency and nothing more. Three measures, in
descending order of independence, and I will say which is weak.

**1. Lossless round-trip. This is the real one.** Concatenate every row's
`body_md` in `source_line` order and diff the result against the source file.
Byte equality proves the partition is a partition: no item merged with its
neighbour, none split in two, none truncated, none misattributed. This does not
share the parser's *judgement* — it tests whether the parse loses anything, and
it fails loudly when the parser is wrong in a way that is internally consistent.
**It answers the `body_md` objection directly:** the first packet had no check
that item 2.15's row contained item 2.15's prose, and a boundary shifted by one
line would have passed everything.

```
concat(body_md ORDER BY source_line) == the source file, byte for byte
```

**2. A hand-enumerated fixture.** The 10 completion-bearing item numbers listed
earlier in this packet were read off the file by eye and written down. The check
asserts those exact numbers carry those exact statuses. If the parser drifts,
this fails against a list no parser produced.

**3. Literal-anchor counts — this one is weak and I am not claiming otherwise.**
Total counts cross-checked with `grep -c '^### [0-9]'` and `grep -c '^- \*\*[0-9]'`
in the shell. Different program, different regex engine, same *idea* — so it
catches an implementation slip and would not catch a shared misconception about
what an item is.

**What none of the three establishes:** that the 119 items the parser found are
the 119 items a human would agree are items. Every measure above is anchored to
the same definition. If that definition is wrong, all three agree and all three
are wrong together.

---

## The verification — every claim a command that can fail

```sql
-- 1. inventory
SELECT count(*) FROM queue_items;                      -- expect 119
SELECT form, count(*) FROM queue_items GROUP BY 1;     -- expect heading 98, bullet 21

-- 2. nothing silently defaulted; the run should not have completed otherwise
SELECT count(*) FROM queue_items WHERE need_status='UNPARSED';   -- expect 0

-- 3. the fixture — 10 items, by number, read off the file by hand
SELECT item_num, need_status FROM queue_items
 WHERE item_num IN ('0.1','0.2','0.3','1.1','3.6','1.17','3.22','0.4','1.20','1.22');
       -- expect DONE on 0.1 0.2 0.3 1.1 3.6 1.17 3.22
       --        HALF_DONE on 0.4 1.20 1.22
       --        none OPEN, none NULL, none UNPARSED

-- 4. distribution (shares the parser — see STEP 2 item 3)
SELECT need_status, count(*) FROM queue_items GROUP BY 1;
       -- expect OPEN 42, UNASSESSED 11, DONE 7, HALF_DONE 3, NULL 56   (= 119)

-- 5. identity is the number, not the line
SELECT count(*) FROM queue_items WHERE item_num IS NULL OR item_num='';   -- expect 0
SELECT item_num FROM queue_items GROUP BY 1 HAVING count(*)>1;            -- expect empty

-- 6. tier came from the number, not the header — the check the first packet lacked
SELECT item_num, tier FROM queue_items
 WHERE tier <> CAST(substr(item_num, 1, instr(item_num,'.')-1) AS INTEGER);
       -- expect empty; 2.38 is the row that fails if the header was used

-- 7. LOSSLESS ROUND-TRIP — run outside SQL, the one independent check
--    concat(body_md ORDER BY source_line) diffed against the source file
--    expect: no differences

-- 8. staleness is detectable
SELECT DISTINCT source_sha FROM queue_items;   -- one value; compare to sha256sum of the file

-- 9. 2.30's four questions, one query each, from one place
--    current item / dependencies / what was just done / DID IT SUCCEED
--    The fourth depends on LOAD-BEARING DECISION 2 and is the point of the item.
```

**Check 4 is the weak one and is labelled as such.** If the extractor and the
check share a parser, it proves the parser agrees with itself. Checks 3, 6 and 7
are the ones that can fail against something the parser did not produce.

**No check is offered for `queue_edges`.** It is not integrated by this change,
so there is nothing to verify — but that also means the dependency half of
2.30's second question is answered by a table nothing regenerates. If you think
that makes the design incomplete rather than merely staged, say so.

---

## The backup, before anything runs

```bash
sqlite3 /mnt/projects/cis/data/cis_memory.db \
  ".dump queue_edges build_plan_nodes build_plan_dependencies workflow_runs" \
  > data/backups/queue_pre_3.21_$(date -u +%Y%m%dT%H%M%SZ).sql
test -s data/backups/queue_pre_3.21_*.sql || { echo "BACKUP EMPTY — STOP"; exit 1; }
cp docs/UNIFIED_BUILD_LIST.md \
   data/backups/UNIFIED_BUILD_LIST_$(date -u +%Y%m%dT%H%M%SZ).md
```

`workflow_runs` is in the dump because DECISION 2 proposes altering it.

---

## What you are NOT being asked

Not whether the queue should move into the spine — decided, recorded as 3.21 and
2.30. Not which UI renders it; 3.21 was rewritten on 2026-09-06 specifically to
stop a presentation venue gating a data structure. Not whether to retire
`build_plan_nodes` or `queue_edges` — explicitly outside this card. Not the
wording of any build-list item.

Only: **would this design and its verification prove what they claim, what could
pass every check above while still being wrong, and are the two LOAD-BEARING
decisions right?**
