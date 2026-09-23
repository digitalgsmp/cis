# Card 03 System Context — test summary

All results below are **fresh runs** taken while preparing commit `9e0a749`, not
copies of the historical Card 03 numbers. Raw output: `test_output.txt`.

## Backend — run against the real spine

Run from `/mnt/projects/cis`. These suites read `data/cis_memory.db` (~5.9 GB,
gitignored), so they cannot run in a bare checkout. They are read-only; Card 03
proved non-mutation via `test_no_mutation_from_repeated_reads`.

| Suite | Command | Result | Card 03 / R1 historical |
|---|---|---|---|
| System Context API | `python3 runtime/tests/test_system_context_api.py` | **39/39 passed**, exit 0 | 39/39 (Card 03) |
| Canonical state | `python3 tools/state/tests/test_canonical_state.py` | **32/32 passed** | 21/21 (Card 03), 33/33 (R1) |
| Recovery packet | `python3 tools/state/tests/test_recovery_packet.py` | **46/46 passed** | 34/34 (Card 03), 46/46 (R1) |

`test_canonical_state.py` reports 32 rather than R1's 33 because one assertion is
conditional on WB.1 state that is not present at this baseline; it is reported as
`PASS (skipped, WB.1 not present)`. No failures.

## Frontend — run against the exact committed tree

Run from `runtime/ui/` inside a detached worktree checked out at `9e0a749`, so
these results describe what a fresh clone gets, not the developer working tree.
`node_modules` was symlinked from the main checkout; no other file was supplied.

| Suite | Command | Result | Card 03 / R1 historical |
|---|---|---|---|
| Vitest | `npx vitest run` | **24/24 passed**, 2 files | 23/23 (Card 03), SystemContext 8/8 (R1) |
| Production build | `npx vite build` | **27 modules transformed**, exit 0 | 27 modules (Card 03) |

The 24 are 16 in `App.test.jsx` (baseline, unchanged) and 8 in
`SystemContext.test.jsx` (Card 04 R1 version). The module count matching Card 03's
recorded 27 independently corroborates that the reconstructed `App.jsx`, `api.js`
and `index.css` are faithful.

## Fresh-checkout coherence (§10)

Checked in the same isolated worktree at `9e0a749`:

| Requirement | Result |
|---|---|
| Python imports resolve | `import container_app` succeeds |
| System Context backend module exists | `runtime/api/system_context.py` present |
| API tests can import the implementation | 39/39 pass |
| React imports resolve | build transforms 27 modules, no unresolved import |
| No unresolved `SystemContext` import | build exit 0 |
| UI test resolves its component | `SystemContext.test.jsx` 8/8 |
| `container_app.py` imports no absent module | no `chroma_health` reference; both routes exposed |

Route inventory from that tree: `route_inventory.txt`. Both System Context routes
present; Card Factory, Card Runner, `/api/workbench/projects`, confirm-direction
and approve all **ABSENT**.

## Not run, and why

No live activation was performed: no migration applied, no container restart, no
Auth0 or Cloudflare configuration, no paid model call, no agent subprocess. The
live `cis-pipeline` container was not touched by this work.
