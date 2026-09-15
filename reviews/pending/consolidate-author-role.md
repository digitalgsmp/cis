# Consolidate Brain + Draft into one Author role (container)

- VERSION: 2
- CHANGES: fixed port (8645); added blast-radius (dispatch topology); scoped MCP re-enable to read tools only; chat path = Telegram; added disposition/rollback/migration.

## Intent (verbatim)

> "it should be collapsed but the real question is that I need to transfer from
> right now working with the host drafter to the consolidated brain drafter in
> the container."

## Summary

Merge `brain.yaml` (8644, divergent) and `draft.yaml` (8645, convergent) into a
single **Author** profile that does explore → confirm → draft, so Eric's daily
brainstorming and card-writing moves from the host Drafter into the container.
This is a **pipeline topology change**, not just a profile merge — the dispatch
code that points at 8644/8645 must be updated in the same change.

## Decisions (resolving round-1 objections)

1. **Port:** Author answers on **8645** (the draft seat, already the primary
   dispatch target). **8644 is retired.**
2. **Chat path:** **Telegram** — the Author runs its own bot. The mechanism
   already exists: `run_container.sh` passes `CIS_TG_BRAIN_TOKEN` (and
   siblings) into the container; `entrypoint.sh` writes `TELEGRAM_BOT_TOKEN`
   + allowed users into the profile `.env`. The **`@cis_braingate_bot`** token
   is already provided by Eric and stored in the gitignored `secrets.env` as
   `CIS_TG_BRAIN_TOKEN`. Activation = container restart (the `.env` is read at
   gateway startup). This keeps Eric on Telegram with no new interface.
3. **MCP:** re-enable the `cis-knowledge` bridge but **read tools only** —
   exclude `cis_dispatch_drafter/_reviewer/_implementer` (the self-dispatch
   surface that was the reason for the 2026-09-04 disable, BUILD LIST 2.23).

## Scope + blast radius (files that reference 8644/8645 and must change)

- `enforcement/mwl-proof-v2/profiles/brain.yaml` + `draft.yaml` → new `author.yaml`
- `enforcement/mwl-proof-v2/entrypoint.sh` — start `author`, stop `brain`/`draft`
- `runtime/pipeline_run.py` — `("draft", 8645, ...)` mapping
- `runtime/app.py` — gateway registry (`v4pro→8645`, `qwen→8644` is stale and wrong)
- `runtime/orchestrator.py` — `drafter_agent` / `drafter_gateway_url`
- `runtime/rails/configs/cis_v4pro_r1/config.yml` — routes to 8645 via NeMo 8801
- `runtime/mcp_bridge/tools.py` — `cis_dispatch_drafter` → `drafter_start.py`

## Acceptance criteria (DONE WHEN)

- One profile answers on **8645**; **8644 is gone** from the container.
- Author calls a `cis-knowledge` **read** tool and returns a real result (not
  just `sqlite3` returning rows — that proves the DB, not the bridge).
- A test card lands in `queue_items` (row id returned).
- Eric receives a reply from the Author over Telegram (message id).
- `git grep 8644` returns no active dispatch reference (only history).

## Disposition / rollback / migration

- **Disposition:** `brain.yaml` and `draft.yaml` are archived (kept in repo,
  removed from `entrypoint.sh`), not deleted — they are the rollback path.
- **Rollback:** revert `author.yaml` → restore `brain.yaml`/`draft.yaml` in
  `entrypoint.sh`, rebuild — the old setup is one config swap away.
- **Migration:** build Author on 8645 and verify end-to-end **before** removing
  8644; the two old profiles stay warm during the transition.

## Out of scope (separate cards)

- Loading the design-spec items into the queue.
- The enforcement gates (ADR-015/016) — those constrain the worker, not the Author.
