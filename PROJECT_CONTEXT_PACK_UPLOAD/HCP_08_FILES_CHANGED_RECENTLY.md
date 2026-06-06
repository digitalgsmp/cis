# Files Changed Recently
Last updated: 2026-06-06 (Tier 0–4 complete — HCP reconciliation)

## Tier 4 — SQLite Spine (2026-06-06)

### runtime/schema/ — New
- `runtime/schema/spine_schema.sql` — workflow_runs + deliberation_rounds DDL (`88ea25f`)

### runtime/db/ — New
- `runtime/db/database.py` — write/read layer with allowlist validation (`0c19b4d`)

### tools/gates/ — New
- `tools/gates/gate_db_state.py` — deterministic DB verification gate (`ec14615`)

### data/ — Runtime (gitignored)
- `data/cis_memory.db` — seeded with smoke test data

## Tier 2–3 — Kanban + Smoke Test (2026-06-06)

### .gitignore
- Added `data/` and `proposals/` rules

### docs/
- `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` — updated for lane limitation, card schema (`2989c5b`)

### runtime/config/systemd/ — New
- Gateway service templates (5 files) — backed up with EnvironmentFile= (`b7e920c`)
- `ENV_MANIFEST.md` — documented required env vars per profile (`26d2ee5`)

### ~/.config/systemd/user/ — Live (outside repo)
- Four service files updated with EnvironmentFile=
- Prime HERMES_HOME corrected (OQ-009 resolved)

### Kanban Runtime — gitignored
- `cis-pipeline` board created on shared kanban.db
- Canary card `t_e7ed2d7b` and smoke card `t_5bde980a` (archived)

## Previous: Tier 0/1 (2026-06-05/06)
- `runtime/orchestrator.py` + `runtime/orchestrator_config.yaml` (`9d84351`)
- `tools/gates/gate_git_state.sh` (`bc49beb`)
- `tools/gates/gate_service_health.sh` (`a5b123a`)
- `tools/gates/gate_endpoint.sh` (`14fd08d`)
- `tools/gates/gate_no_secrets.sh` (`82b506a`)
- `tools/gates/gate_file_exists.sh` (`dac9d6a`)
- `tools/gates/gate_runner.sh` (`635a646`)
