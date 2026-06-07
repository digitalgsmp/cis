# Files Changed Recently
Last updated: 2026-06-07 (Tier 5.3 closeout)

## Tier 5.3 — Context Retirement (`80f934c`)
- `runtime/config/systemd/hermes-gateway.service` — updated template backup

## Tier 5.2E — Gateway Repair (`353cef5`)
- `runtime/config/systemd/hermes-gateway.service` — restored from repo backup (HERMES_HOME=/home/eric/.hermes)

## Tier 5.1 — AGENTS.md Generator (`ee8eb25`)
- `tools/export/generate_agents_md.py` — new file
- `config/agents_static.yaml` — new file
- `AGENTS.md` — generated from spine, 8,384 bytes

## Tier 4.4 — Context Export State Tables (`b2e6c98`)
- `runtime/schema/migrations/0001_context_export_state.sql` — new file (4 tables)
- `runtime/db/database.py` — extended (+4 constants, +4 insert functions, +migration check)
- `tools/gates/gate_db_state.py` — extended (+4 tables, +12 columns)

### DB-only (no commit):
- Spine seed: 6 decisions, 3 questions, 7 actions, 4 blockers
- Corrections: ADR-SEED-007, BLK-SEED-005

## Tier 0–4 Pre-T5 (prior to this session)
- `runtime/orchestrator.py` + config (`9d84351`)
- `tools/gates/` — 6 gate scripts (`bc49beb`–`ec14615`)
- `runtime/schema/spine_schema.sql` — 2-table minimum (`88ea25f`)
- `runtime/db/database.py` — write/read layer (`0c19b4d`)
- `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` (`0ef6177`, amended `2989c5b`)
- `runtime/config/systemd/` — service templates (`b7e920c`)
- `.gitignore` — data/ + proposals/ (`3f8bf1c`, `efff168`)
