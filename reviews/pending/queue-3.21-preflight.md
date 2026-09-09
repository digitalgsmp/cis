# PRE-FLIGHT REVIEW — 3.21, moving the task queue into the spine

**Nothing below has been built.** No table has been created, no migration
written, no extractor run. This is a design under review before any of that.

Answer exactly this:

1. **What would this design fail to establish?**
2. **What result would satisfy its verification while still being wrong?**

A third question is asked inline at the two decisions marked **LOAD-BEARING**.
Answer those where they appear.

---

## The item as written

> **3.21 Move the queue out of markdown and into the spine.** The build list is a
> markdown document, so any UI that shows it has to parse prose. `mined_tasks`
> already proved the structural form this needs. Moving the queue into the spine
> as a table gives a UI something to read directly, and it removes the two-lists
> failure permanently — 2.12 exists because a second queue drifted from the
> first, and prose is what makes that drift possible.
>
> **The one check that settles the scope:** can a stateless agent read the
> current item, its dependencies, and the last completion status from one place?
>
> **Depends on:** nothing.

Item 2.30 records the requirement 3.21 serves: a stateless agent needs one place
answering **what is the current item, what does it depend on, what was just
done, and did it succeed.** Today that is four places — a markdown queue, git
history, `workflow_runs`, and the previous session's output.

**"Depends on: nothing" is one of the things you are being asked to test.** The
state below was measured today and was not known when that line was written.

---

## Measured state, all verified 2026-09-08 against `data/cis_memory.db` and the repo

### There is already a queue table in the spine, holding a different queue

```
build_plan_nodes           30 rows
build_plan_dependencies    25 rows
```

`build_plan_nodes` holds the **June 2026 dependency-graph build plan** — tiers 0
through 13, `Tier 8 — MCP Bridge`, `Tier 12 — Knowledge Base Ingestion`, most
rows COMPLETE with 2026-06 timestamps, one PENDING (`Enforcement — Container
Isolation`). It is not the unified build list and shares no item numbering with
it.

It has live production readers and writers:

```
runtime/db/build_plan.py      create_node, create_dependency, promote_unblocked,
                              complete_node, sync_project_state_from_build_plan
runtime/app.py:1077           SELECT ... FROM build_plan_nodes WHERE project_id='cis'
                              ORDER BY sequence     -> the dashboard's roadmap panel
runtime/tier7r/adapters/cis_adapter.py   stages nodes with status=PROPOSED
runtime/tier7r/adapters/swa_adapter.py   stages 4 candidate nodes (SWA Phase 45)
runtime/db/database.py:89     existence probe
```

Its DDL, as of migration 0030 yesterday:

```sql
CREATE TABLE build_plan_nodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL DEFAULT 'cis' REFERENCES projects(id),
    node_label      TEXT NOT NULL,
    tier            TEXT NOT NULL,
    sequence        INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING','IN_PROGRESS','COMPLETE',
                                      'BLOCKED','DEFERRED','PROPOSED')),
    blocked_reason  TEXT,
    required_role   TEXT,
    allowed_mode    TEXT,
    workflow_run_id TEXT REFERENCES workflow_runs(id),
    evidence_path   TEXT,
    commit_hash     TEXT,
    completed_at    TEXT,
    approved_at     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(project_id, node_label)
);
```

The `app.py` read is wrapped in `try: ... except Exception: pass`, so the roadmap
panel renders empty on any error and says nothing. That is item 2.10 in the
flesh, on the one surface that would display this work.

### A partial extraction of the unified list already exists, and the list does not know

```
queue_edges                45 rows, 29 distinct from_num, extracted_at 2026-09-05/06
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

Its `from_num` values are unified-list item numbers (`1.12`, `3.21`, `4.18`).
**No code in the repo reads or writes this table** — grep over `tools/`,
`runtime/`, `config/` for `queue_edges` returns only two prose mentions in the
build list itself, and both call it *"the proposed `queue_edges`"* (items 2.32
and 3.25). It was materialized by a session running SQL directly and left there.

So the edges half of 3.21 exists as orphaned data of unknown freshness, and two
open items are written on the belief that it does not exist.

### The list's own shape

```
total items                 117
  as '### N.M TITLE'         96
  as '- **N.M** text'        21
duplicate item numbers        0
tier-header vs number         1 mismatch: 2.38 sits under '# TIER 3'
```

Status is not a field. It is prose, written four ways. Classified per item, with
item boundaries taken at the next item start of either form or the next
`# TIER` header:

```
**Need:** OPEN                                    40 items
**Need:** UNASSESSED                              11 items
**Need: DONE ...** / **Need: HALF DONE ...**       5 items   (key inside the bold)
bare **DONE ...**, no Need key anywhere            5 items
no status signal of any kind                      56 items
                                                 ---
                                                 117
```

The 5 bare markers are 0.1, 0.2, 0.3, 1.1 in item bodies, and 3.6 as
`**DONE 2026-09-07 — runtime/schema/migrations/0030_...sql**` inside a bullet.
The 5 key-inside-bold are 0.4, 1.17, 1.20, 1.22, 3.22.

A parser keyed on the literal `**Need:**` therefore finds 51 of 117 items, reads
two values, and **silently reports all 10 completed or half-completed items as
absent** — including 3.6, closed yesterday, and 0.4, whose half-done state is
what item 0.6 was opened against.

No item contradicts itself: nothing says `**Need:** OPEN` while also carrying a
DONE marker. That was checked, because it would make the field unresolvable
rather than merely unparsed.

### References into the list rot by line number

`mined_tasks.in_build_list` (40 rows) stores its link as free text carrying a
line number:

```
2.15 Thirty-three of fifty-one gate scripts have never fired (UNIFIED_BUILD_LIST.md:759)
3.2  No pre-delete or archive-policy validation. Checked: absent (UNIFIED_BUILD_LIST.md:851)
```

25 of the 40 rows have this field empty. The line numbers in the other 15 are
already wrong: 117 lines were inserted into the file today, above most of them.

### Adjacent facts

```
no migration-tracking table exists          (item 2.5 — migrations 0011..0030 exist,
                                             nothing records which ran)
next free migration number                  0031
nothing in tools/ or runtime/ parses docs/UNIFIED_BUILD_LIST.md
  (the one grep hit, tools/advisor_review.sh, only mentions it in a comment)
```

---

## LOAD-BEARING DECISION 1 — a new table, not an extension of `build_plan_nodes`

**Proposed: create `queue_items`. Do not put unified-list items into
`build_plan_nodes`.**

The reasoning, which you should attack:

- `build_plan_nodes` has five production readers and a dashboard panel that
  selects `WHERE project_id='cis' ORDER BY sequence` with no other filter.
  Inserting 117 unified-list rows changes what every one of those returns, from
  30 rows to 147, with no code change anywhere. Item 2.38 exists because a
  schema change's blast radius was not enumerated; this is that.
- The two schemas disagree semantically. `build_plan_nodes.tier` holds labels
  like `7.5a` and `ENFORCEMENT`; the unified list's tiers are 0–4 and its
  identity is a dotted item number, not a `node_label`. `sequence` is a total
  order the unified list does not have.
- `cis_adapter` and `swa_adapter` **write** PROPOSED rows into
  `build_plan_nodes`. A queue that agents can extend is a different object from
  a queue Eric authors.

**The objection this invites, stated so you can press on it:** two queue tables
in one spine is the 2.12 two-lists failure moved inside the database, and 3.21
exists to remove that failure permanently rather than relocate it.

**The proposed answer:** `build_plan_nodes` is a *completed historical plan*, not
a live rival queue — 29 of 30 rows COMPLETE or DEFERRED, newest completion
2026-06-28. It should be marked superseded in the same change, which is exactly
what item 2.32 (supersession has no schema representation) is asking for. Two
tables where one is explicitly recorded as superseded is not two queues; two
tables where nothing says which is live is.

**Is that answer sufficient, or is it a rationalization?** If `build_plan_nodes`
should instead be extended, migrated, or dropped, say which and what breaks.

---

## LOAD-BEARING DECISION 2 — the table is DERIVED from the markdown, one way

**Proposed: `docs/UNIFIED_BUILD_LIST.md` stays authoritative. `queue_items` is
regenerated from it. Nothing writes prose back.**

The reasoning, which you should attack:

- The operator is not a coder and authors the queue by editing prose. A table
  that is authoritative means queue edits become SQL.
- The repo already has this exact relationship: `AGENTS.md` is auto-generated by
  `tools/export/generate_agents_md.py` and carries a DO-NOT-EDIT banner, with a
  pre-commit hook regenerating it. A derived projection with a regeneration hook
  is one queue with an index, not two queues.
- 2.12's failure is two **authoritative** sources drifting. A projection that is
  rebuilt from its source cannot drift from it; it can only be stale, which is a
  detectable condition and not a silent one.

**The objection this invites, stated so you can press on it:** 2.30 requires the
spine to answer *"what was just done, and did it succeed."* A read-only
projection cannot accept a completion write from an agent, so 3.21 would satisfy
three of 2.30's four questions and not the fourth.

**The proposed answer:** completion is not authored into the queue at all. It is
joined at read time from `workflow_runs`, `gate_outcomes` and commit hashes,
which are already the evidence-bearing tables. An agent asserting its own
completion into a queue row is failure mode 1 — self-reported completion without
evidence — given a schema to live in.

**Is that join actually available today?** Note there is no column anywhere
linking a unified-list item to a `workflow_run`, and item 2.13 is open for
precisely that reason. If this makes 2.13 a hard prerequisite to 3.21, say so —
the item currently claims it depends on nothing.

---

## The proposed schema

```sql
CREATE TABLE queue_items (
    item_num        TEXT PRIMARY KEY,          -- '1.12', '3.21'
    tier            INTEGER NOT NULL,          -- from the item number, not the header
    title           TEXT NOT NULL,
    body_md         TEXT NOT NULL,             -- the item's prose, verbatim
    form            TEXT NOT NULL CHECK (form IN ('heading','bullet')),
    scope           TEXT,                      -- CONTAINER | REPO | NOT_IN_CONTAINER_PATH | ...
    need_status     TEXT CHECK (need_status IN
                        ('OPEN','UNASSESSED','HALF_DONE','DONE','UNPARSED')),
    need_raw        TEXT,                      -- the literal prose the status came from
    source_line     INTEGER NOT NULL,          -- position at extraction, not an identity
    source_sha      TEXT NOT NULL,             -- sha256 of the markdown file
    extracted_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
```

`queue_edges` is kept as it stands and gains two edge kinds already asked for by
open items — `documents` (item 3.25, the REFERENCE DOCUMENTS table maps ten
documents to the items they cover and nothing treats it as an edge) and a
`supersedes` use for the `Recorded, not queued` section (item 2.32). A foreign
key from `queue_edges.from_num`/`to_num` to `queue_items.item_num` is proposed;
note that 45 rows already exist and some may reference numbers that no longer
resolve.

---

## The extractor's stated contract

1. Parse both item forms — `### N.M` and `- **N.M**`.
2. Derive `tier` from the item number, **not** from the enclosing `# TIER`
   header. They disagree once already (2.38 under Tier 3), and the number is the
   identity used by every cross-reference in the file.
3. Recognise all four status spellings, including the two where the key sits
   inside the bold, and the bare `**DONE ...**` markers with no key.
4. Any item whose status cannot be classified is written with
   `need_status='UNPARSED'` and its `need_raw` preserved — never defaulted to
   OPEN.
5. **The extractor exits non-zero if any item is UNPARSED.** A partial queue is
   not imported.

---

## The verification — every claim a command that can fail

```sql
-- 1. every item is present, both forms
SELECT count(*) FROM queue_items;                      -- expect 117
SELECT form, count(*) FROM queue_items GROUP BY 1;     -- expect heading 96, bullet 21

-- 2. nothing was silently defaulted
SELECT count(*) FROM queue_items WHERE need_status='UNPARSED';   -- expect 0

-- 3. the ten completions a naive parser loses are present and not OPEN
SELECT item_num, need_status FROM queue_items
 WHERE item_num IN ('0.1','0.2','0.3','0.4','1.1','1.17','1.20','1.22','3.6','3.22');
                                    -- expect DONE on 0.1,0.2,0.3,1.1,3.6,1.17,3.22
                                    --        HALF_DONE on 0.4,1.20,1.22
                                    --        none OPEN, none NULL, none UNPARSED

-- 4. status distribution matches the file, not a default
SELECT need_status, count(*) FROM queue_items GROUP BY 1;
                                    -- expect OPEN 40, UNASSESSED 11, DONE 7,
                                    --        HALF_DONE 3, NULL 56       (sums to 117)

-- 5. identity is the number, not the line
SELECT count(*) FROM queue_items WHERE item_num IS NULL OR item_num='';   -- expect 0
SELECT item_num, count(*) FROM queue_items GROUP BY 1 HAVING count(*)>1;  -- expect empty

-- 6. every edge resolves to an item
SELECT from_num FROM queue_edges WHERE from_num NOT IN (SELECT item_num FROM queue_items)
 UNION
SELECT to_num FROM queue_edges WHERE to_num NOT IN (SELECT item_num FROM queue_items);
                                    -- expect empty; any row here is a stale 2026-09-05 edge

-- 7. 2.30's four questions, as one query each, from one place
--    current item / its dependencies / what was just done / did it succeed
--    QUESTION FOR YOU: the fourth has no source column in this schema.

-- 8. staleness is detectable
SELECT source_sha FROM queue_items LIMIT 1;
   -- compare against sha256sum docs/UNIFIED_BUILD_LIST.md; a mismatch means stale
```

**Check 4 is the one that certifies whatever the extractor produced if its
arithmetic is wrong.** An earlier draft of this packet asserted OPEN 40 /
UNASSESSED 11 / NULL 57, taken from raw `grep` counts over the file. Per-item
classification gives NULL 56, and the two figures disagreed because a `grep`
counts occurrences while the queue needs items. The numbers above are the
per-item counts. **They are still one script's output, not an independent
measure** — if the extractor and this check share a parser, check 4 proves only
that the parser is consistent with itself.

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

---

## What you are NOT being asked

Not whether the queue should move into the spine — that is decided and recorded
as 3.21 and 2.30. Not which UI renders it; 3.21 was rewritten on 2026-09-06
specifically to stop a presentation venue gating a data structure. Not the
wording of any build-list item.

Only: **would this design and its verification prove what they claim, what could
pass every check above while still being wrong, and are the two LOAD-BEARING
decisions right?**
