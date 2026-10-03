# Queue Triage — Blocking Set

Produced: 2026-10-03 · HEAD `99b1c30b4f05b7cdc88c18a9c33544d7c71e513d` (= origin/master)
Actor: claude-opus-5 · Authority for this pass: Eric (parallel-triage exception, ADR-PIPE-007)

Nothing was written to `queue_items` or `queue_edges`. This document states why,
with the commands that establish it.

---

## 1. What triage is defined to be

ADR-PIPE-001, verbatim:

> THEN QUEUE TRIAGE: a bounded mechanical pass classifying **scope and
> need_status** on the 56 queue_items rows that currently carry neither,
> **using existing queue tools**; no item redesign during triage; purpose is
> to make later P4/P5 ordering trustworthy.

ADR-PIPE-006, verbatim:

> Structural problems discovered during triage become SEPARATELY REVIEWED
> work, not in-line fixes.

So triage is a **two-field** write (`scope` *and* `need_status`), it must use
**existing tools**, and a structural obstacle found while doing it may **not**
be fixed in line. Those three clauses together are what produce the block below.

---

## 2. Blocker A — no existing tool can write `queue_items.scope`

`queue_set.py` is the sanctioned write path and it writes `need_status` only:

```
tools/queue/queue_set.py:69
    "UPDATE queue_items SET need_status=?, status_changed_at=?, status_changed_by=? "
```

Exhaustive sweep of every `UPDATE queue_items` in the repository, excluding
vendored venvs:

```
$ grep -rn "UPDATE queue_items" --include="*.py" --include="*.sh" --include="*.sql" . \
    | grep -v "/\.venv/"
tools/queue/classify_check.py:163   SET check_class=?
tools/queue/queue_set.py:69         SET need_status=?, status_changed_at=?, status_changed_by=?
tools/development/tests/test_launcher_execution.py:574   (test)
tools/state/tests/test_canonical_state.py:170            (test)
tools/development/tests/test_continuity.py:568,582,590,595,599,608,634  (test)
```

**In production code the only writable classification columns are
`need_status` and `check_class`. `scope` is not writable by any tool.**

`queue_add.py` — the creation path — does not carry scope either:

```
tools/queue/queue_add.py:132
    "INSERT INTO queue_items (item_num, tier, title, body_md, form, need_status, ...)"
$ grep -n "scope" tools/queue/queue_add.py
34:authority), and not something this card's scope calls for fixing.
```

The only code that has ever written `scope` is the extractor, which parses it
out of the markdown body:

```
tools/queue/extract_queue_items.py:207
def extract_scope(body):
    m = re.search(r"\*\*Scope:?\*\*[:\s]*([^\n]+)", body)
```

and that tool is **LOCKED**, by its own contract:

> LOCKED — the queue is no longer extracted from the markdown. queue_items
> (the spine) is the authority. Re-extracting here would overwrite the
> authority — and any status_changed_at / queue_item_events history — with a
> copy.

Confirmed by running it:

```
$ python3 tools/queue/extract_queue_items.py
LOCKED — the queue is no longer extracted from the markdown.
```

**Consequence.** Writing `scope` requires either raw SQL — which `queue_set.py`
forbids in its own contract ("a status change goes through this tool, never raw
SQL, so every change carries an append-only event row") — or adding a scope
write path, which is a source-code change. ADR-PIPE-006 forbids making that
change in line during triage.

---

## 3. Blocker B — the need_status half cannot reach the generated projection

ADR-PIPE-006 records that `docs/UNIFIED_BUILD_LIST.md` is a generated
projection of the queue. `render_build_list.py` puts a status into the markdown
only by **rewriting an existing status marker**:

```
tools/queue/render_build_list.py:rewrite_status()
    Shape 1 -- '**Need:** VALUE'
    Shape 2 -- '**Need: VALUE ...**'
    Shape 3 -- bare '**DONE ...**'
    return body_md          # <- unchanged when no marker is present
```

All 56 unclassified items have **no marker of any shape** — which is precisely
why their `need_status` is NULL. Measured directly against the real function:

```
unclassified items total: 56
rewrite_status would CHANGE body (status visible in markdown):  0  []
rewrite_status leaves body UNCHANGED (status invisible):       56
unclassified items carrying a **Scope marker: 0  []
unclassified items carrying a **Need:  marker: 0  []
```

**Consequence.** A `need_status` written through `queue_set.py` would live in
the spine column and be **invisible in the committed markdown for all 56
items**. Worse, the documented recovery path (`extract_queue_items.py --force`,
"to rebuild the table from a hand-edited markdown during recovery") reads status
*from the markdown* — so all 56 classifications would be silently reset to NULL
if recovery were ever run. The audit trail in `queue_item_events` would survive;
the classification itself would not.

Making the projection carry these 56 statuses means teaching `rewrite_status`
to *insert* a marker where none exists. That is a source-code change.

---

## 4. Why the available half was not written anyway

`need_status` alone is mechanically writable for all 56 today. It was not
written, for one reason:

`project_intelligence.py:build_queue()` computes

```python
awaiting = item.get("need_status") is None and (item.get("scope") is None ...)
```

so **setting `need_status` alone flips all 56 rows from AWAITING TRIAGE to
CLASSIFIED** while `scope` stays NULL on every one of them. The Project Map
would report `unclassified: 0` — triage complete — for a pass that ADR-PIPE-001
defines as two-field and that would in fact be half done, with the missing half
invisible in the count.

That is the same failure shape as the premature "P0 COMPLETE" value that
independent ChatGPT/Codex review rejected: a completion signal that outruns the
evidence. Declining to produce a second one is the whole reason this stops here.

---

## 5. The decision required

One of the following, which only the architect can give:

**Option 1 — authorize a scope write path (recommended).**
A separately reviewed card adds `--scope` to `queue_set.py` (same event-row
discipline, `field='scope'`, which `queue_item_events` already supports — it
carries `body_md` rows today) and teaches `render_build_list.py` to insert a
`**Scope:**` / `**Need:**` marker where none exists. Then triage proceeds as
ADR-PIPE-001 defines it, in one pass, fully projected and fully auditable.
This is the only option that satisfies ADR-PIPE-001 as written.

**Option 2 — redefine triage as need_status-only.**
Amend ADR-PIPE-001 to drop `scope` from the triage definition, and amend the
Project Map's `awaiting_triage` rule so "classified" cannot be claimed on a
single field. Cheaper, but it narrows an accepted ADR and leaves `scope` NULL
on 69 of 132 rows with no path to ever fill it.

**Option 3 — accept spine-only classification.**
Write `need_status` via `queue_set.py`, accept that the markdown projection will
not show it, and record that `extract_queue_items.py --force` must never be run
again. Not recommended: it makes the documented recovery path destructive.

The proposed classification for all 56 items is already prepared and is in
`PROPOSED_CLASSIFICATION.md` beside this file. Under Option 1 it can be applied
directly.

---

## 6. Two conflicts found during the pass, reported not resolved

**C1 — three items depend on a mechanism ADR-PIPE-006 declares retired.**
ADR-PIPE-006: "`build_plan_nodes` = the RETIRED tier-plan mechanism."
Items **2.13**, **2.16** and **2.18** all rest on `build_plan_nodes`:

```
$ sqlite3 data/cis_memory.db "SELECT COUNT(*), SUM(workflow_run_id IS NULL) FROM build_plan_nodes;"
30|30
```

2.13 is entirely about `build_plan_nodes.workflow_run_id` being NULL on all 30
rows; 2.16 asks whether `runtime/tier7r/` should stop being counted COMPLETE
across nodes 7R.1–7R.7; 2.18 cites the same NULL column as an instance.
Classifying these OPEN asserts live work on a retired mechanism. Classifying
them obsolete discards recorded findings. **Architect decision — proposed
`NEEDS_ERIC` for all three.** (Card stop condition 5.)

**C2 — `docs/UNIFIED_BUILD_LIST.md` is stale at HEAD, benignly.**
Pre-existing, not caused by this pass. The divergence is the banner line only;
every item body is byte-identical:

```
$ python3 tools/queue/render_build_list.py --verify
STALE — run tools/queue/render_build_list.py
$ diff docs/UNIFIED_BUILD_LIST.md <(render --stdout) | wc -l
4
3c3
< <!-- state_revision: d5d3a10186e51275 -->
> <!-- state_revision: 7663d83277ffa285 -->
```

No content gap. Reported so it is not mistaken for damage from this pass.

---

## 7. State preserved

| | |
|---|---|
| P0 | ACTIVATED / CLOSEOUT BLOCKED — unchanged |
| P1 | NOT BEGUN — unchanged |
| WIASW | NOT_ACTIVATED — unchanged |
| `queue_items` | 132 rows, 56 unclassified — unchanged |
| `queue_edges` | 45 — unchanged |
| `project_state.pipeline_roadmap` | unchanged |
| `project_state.build_phase` | unchanged |
| provider credentials | not touched |
| P0 browser proof | not attempted |
