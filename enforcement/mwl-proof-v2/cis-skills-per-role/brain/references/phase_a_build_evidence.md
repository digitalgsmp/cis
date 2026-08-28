# Phase A Build Evidence (2026-07-10)

Phase A of the Control Plane build spec (`docs/SPEC_CONTROL_PLANE_BUILD.md`) built directly by GLM Verifier, bypassing pipeline to save tokens.

## A1: `_db_connect` Bug Fix
- **File**: `runtime/abstraction/pipeline_relay.py`
- **Change**: `_db_connect()` now accepts `db_path` parameter (line 175). `PipelineRelay.__init__` calls `_db_connect(self.db_path)` (line 1347).
- **Verify**: `python3 -c "from pipeline_relay import _db_connect; c=_db_connect('/tmp/test.db'); c.execute('CREATE TABLE t(x)'); c.execute('INSERT INTO t VALUES(42)'); assert c.execute('SELECT x FROM t').fetchone()[0]==42; print('OK')"`
- **Result**: Custom path creates and queries a separate DB correctly.

## A2: MCP Bridge Bug Fix + KB Search Endpoints
- **File**: `runtime/mcp_bridge/spine.py` line 203
- **Change**: `workflow_run_id` → `run_id` in `workflow_run_artifacts` query
- **Verify**: `sqlite3 data/cis_memory.db "SELECT * FROM workflow_run_artifacts WHERE run_id = 'run-86bc4d1009b8fb44-1783645778'"` — no error
- **New endpoints in `runtime/api/relay.py`**:
  - `GET /api/relay/runs?limit=50` — list recent runs
  - `GET /api/relay/kb/search?q=<query>&top_k=10` — FTS5 search across 287K messages
  - `GET /api/relay/kb/decisions` — open project decisions (ADRs)
- **Note**: `project_decisions.status` uses `DECIDED`/`OPEN`, not `active`. Fixed query to `WHERE status IN ('DECIDED', 'OPEN')`.
- **Verify**: FTS5 search for "control plane" returns 32 results.

## A3: Corpus Extraction
- **Migration**: `runtime/schema/migrations/0021_corpus_entries.sql` — creates `corpus_entries` table + `corpus_entries_fts` virtual table with sync triggers
- **Script**: `tools/extract_corpus.py` — extracts from session_closeouts, agent_trajectories, deliberation_rounds, and /mnt/archive/ (depth-limited to 4 levels on 10TB filesystem)
- **Result**: 213 entries extracted (165 from agent_trajectories, 31 from deliberation_rounds, 17 from session_closeouts, 0 from archive)
- **Verify**: `sqlite3 data/cis_memory.db "SELECT COUNT(*) FROM corpus_entries_fts WHERE corpus_entries_fts MATCH 'control plane'"` → 32

## A4: Multi-Project Support
- **Migration**: `runtime/schema/migrations/0022_projects_table.sql` — creates `projects` table, registers CIS as default, adds `project_id TEXT DEFAULT 'cis'` to `workflow_runs`
- **Changes to `runtime/api/relay.py`**:
  - `_db()` helper accepts optional `db_path` parameter
  - `POST /api/relay/start` accepts `project` field, looks up `spine_path` from `projects` table, passes to `PipelineRelay(db_path=...)`
  - `_run_pipeline_background()` passes `db_path` through to PipelineRelay
  - `GET /api/projects` — list all registered projects
  - `POST /api/projects` — register a new project
- **Verify**: `sqlite3 data/cis_memory.db "SELECT * FROM projects"` → CIS registered. `PRAGMA table_info(workflow_runs)` shows `project_id` column.

## Pitfalls Encountered
- `session_closeouts` uses `started_at`, not `created_at` — extraction script fixed
- `project_decisions.status` uses `DECIDED`/`OPEN`, not `active` — endpoint query fixed
- `/mnt/archive/` is 10TB — `os.walk()` hangs without depth limit. Fixed with `topdown=True` + depth check at 4 levels
- `json.load()` can return `None` or non-list types from archive JSON files — added type guards
