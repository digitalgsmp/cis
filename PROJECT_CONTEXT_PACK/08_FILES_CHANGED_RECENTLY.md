# Files Changed Recently
Last updated: 2026-05-31 (Phase 0 Recovery)

## Phase 0 Recovery — Git Versioning + Gateway Repair

### .gitignore (new)
- Created at /mnt/projects/cis/.gitignore
- Excludes: databases, .env, venvs, node_modules, archives, logs,
  transcripts, memory archives, generated context packs, screenshots

### Gateway .env files (4 files)
- /home/eric/.hermes-v4pro/.env — added HERMES_CIS_BRIEFING_PATH
- /home/eric/.hermes-r1/.env — added HERMES_CIS_BRIEFING_PATH
- /home/eric/.hermes-v4impl/.env — added HERMES_CIS_BRIEFING_PATH
- /home/eric/.hermes-qwen/.env — added HERMES_CIS_BRIEFING_PATH
- Timestamped backups created for all four

### Canonical Docs
- docs/CIS_CURRENT_STATE.md (v2.4 → v2.5)
- cis_kernel/build/CIS_SCRATCHPAD.md — Phase 0 entry appended
- PROJECT_CONTEXT_PACK/01_CURRENT_STATE.md — synced
- PROJECT_CONTEXT_PACK/07_RECENT_HANDOFF.md — rewritten
- PROJECT_CONTEXT_PACK/08_FILES_CHANGED_RECENTLY.md — this file
- PROJECT_CONTEXT_PACK/05_NEXT_ACTIONS.md — updated

### No Source Code Changes
- No application code modified
- No config files modified (models were already correct)
- No services changed except restart to pick up env vars
