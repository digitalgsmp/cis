# Evidence answering one objection

Answering your objection headed **"workflow_runs still broken"**:

> The background identifies `workflow_runs.project_id TEXT DEFAULT 'cis'` as part
> of the disagreement, but the card touches only `build_plan_nodes`. All five
> VERIFY queries pass while `workflow_runs` retains **any uppercase values it may
> hold**. The card doesn't claim to fix `workflow_runs`, but the EXPECT gives no
> signal that the wider problem persists.

## The command, and its raw output

```
$ python3.12 -c "
import sqlite3
c=sqlite3.connect('/mnt/projects/cis/data/cis_memory.db')
print('workflow_runs.project_id distinct values and counts:')
for r in c.execute('select project_id, count(*) from workflow_runs group by 1'): print('   ', r)
print('uppercase rows in workflow_runs:', c.execute(
    'select count(*) from workflow_runs where project_id <> lower(project_id)').fetchone()[0])
print('plain join workflow_runs -> projects:', c.execute(
    'select count(*) from workflow_runs w join projects p on w.project_id=p.id').fetchone()[0],
    'of', c.execute('select count(*) from workflow_runs').fetchone()[0])
"

workflow_runs.project_id distinct values and counts:
    ('cis', 105)

uppercase rows in workflow_runs: 0

plain join workflow_runs -> projects: 105 of 105
```

## What this establishes

`workflow_runs` holds **105 rows, all `'cis'`, zero uppercase**. Its plain join to
`projects.id` already returns **105 of 105** — no `COLLATE NOCASE` needed.

`workflow_runs` is not broken and has nothing to fix. Its `DEFAULT 'cis'` is the
**correct** side of the disagreement; `build_plan_nodes.DEFAULT 'CIS'` is the
wrong side, and it is the only one the card changes. Fixing `build_plan_nodes`
does not leave a "wider problem" in `workflow_runs` — it removes the last
disagreement between the two.

The specific claim under objection was that `workflow_runs` "retains any
uppercase values it may hold." It holds none.

## What this does NOT establish, stated so you do not have to infer it

This evidence speaks only to the `workflow_runs` objection. **Your other four
objections are not addressed and I am not contesting them.** In particular:

- **The DEFAULT is never verified** — correct, and it is the most serious of the
  five. The card's own central claim is untested by its own EXPECT.
- **The backup step is pseudo-code** — correct, it would produce nothing.
- **The new table schema is elided** — correct, column order is unverifiable as
  written.
- **UNIQUE is claimed but unchecked** — correct.

Those four stand and the card needs rewriting because of them.

## The question

Does the output above resolve your `workflow_runs` objection specifically —
`VERDICT: WITHDRAWN` — or does it not — `VERDICT: HELD`?
