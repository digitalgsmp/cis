# Container Transition Gap Analysis (2026-07-09)

What's needed to move the CIS pipeline from host (dev) into Docker (production target).

**STATUS: ALL 4 GAPS RESOLVED (2026-07-09).** Container is fully operational.
Smoke test `run-3f1a189b54aff9ad-1783613651` progressed through Brain→IntentReview→
Draft→ProposalReview→ERIC_GATE inside the container.

## What's Already Built

- **Docker images exist**: `cis-hermes:pipeline` (5.7GB), `cis-hermes:gated`, `cis-hermes:pinned`
- **Dockerfile** at `enforcement/mwl-proof-v2/Dockerfile` — installs Hermes 0.17.0, bakes in 51 gate scripts, container_gate_runner.py, managed config (root-owned), 6 profile configs, creates unprivileged `worker` user
- **6 profile configs** in `enforcement/mwl-proof-v2/profiles/` — brain.yaml, draft.yaml, review1.yaml, review2.yaml, menter.yaml, verify.yaml. Each has model, reasoning effort, personality, port, mwl-proof plugin enabled
- **Launch script** (`launch_profiles.sh`) — starts all 6 gateways inside the container on ports 8644-8648, health checks, keeps container alive
- **Gate enforcement** — worker can't modify config, can't disable plugins, can't overwrite gate scripts

## What's Missing (4 gaps)

### 1. CIS codebase not in the image

The pipeline code (`pipeline_relay.py`, `dispatch.py`, Flask API) and the SQLite spine
(`cis_memory.db`) live at `/mnt/projects/cis/` on the host. The container doesn't have them.
Profile configs reference `/source/cis/data/cis_memory.db` but that path doesn't exist in
the image yet.

**Fix**: Volume mount the CIS repo into the container. Volume mount is better than COPY
for dev (changes show up immediately without rebuilding). For production, COPY at build
time for immutability.

```bash
sg docker -c "docker run -v /mnt/projects/cis:/source/cis:rw \
  -p 5000:5000 cis-hermes:pipeline"
```

### 2. Pipeline assumes host paths

`pipeline_relay.py` hardcodes:
```python
DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
BASE_URL = "http://127.0.0.1"
```

And derives `project_dir` from `DB_PATH.rsplit("/", 1)[0]` for git operations
(worktree, diff, rev-parse). Inside the container, paths would be different
(e.g. `/source/cis/`).

**Fix**: The code already supports `CIS_SPINE_PATH` env var — just set it in the
container:
```dockerfile
ENV CIS_SPINE_PATH=/source/cis/data/cis_memory.db
```
Or pass at runtime:
```bash
sg docker -c "docker run -e CIS_SPINE_PATH=/source/cis/data/cis_memory.db ..."
```
The `project_dir` derivation will then resolve to `/source/cis/` automatically.

### 3. API keys not in the image

Each gateway needs its API key:
- Brain/Draft/Menter: DeepSeek API key
- Review1/Review2/Verify: OpenRouter API key

On the host these are in `~/.hermes-*/.env` files (`API_SERVER_KEY=...`). The container's
profile configs have hardcoded placeholder keys like `cis-brainstorm-gateway-key-2026`.

**Fix**: Pass real API keys as environment variables or mount `.env` files as secrets:
```bash
sg docker -c "docker run \
  -v /home/eric/.hermes-brainstorm/.env:/secrets/brain.env:ro \
  -v /home/eric/.hermes-v4pro/.env:/secrets/draft.env:ro \
  ..."
```

Or use `--env-file` with a combined env file. The `_resolve_api_key()` function in
`pipeline_relay.py` reads from `~/.{hermes_profile}/.env` — inside the container,
`HERMES_HOME` is set per-profile by `launch_profiles.sh`, so the `.env` files need to be
at the right paths inside the container.

### 4. Port publishing / networking

Inside the container, all 6 gateways talk to each other on `127.0.0.1:864x`.
The pipeline relay also runs inside and calls those same ports. But the Flask API
(port 5000) and the Eric Gate need to be reachable from outside the container.

**Fix**: Publish port 5000 so you can reach the pipeline API from outside:
```bash
sg docker -c "docker run -p 5000:5000 ..."
```
Gateway-to-gateway traffic stays internal (all on 127.0.0.1 inside the container).

## Full Run Command (target)

```bash
sg docker -c "docker run -d \
  --name cis-pipeline \
  -v /mnt/projects/cis:/source/cis:rw \
  -e CIS_SPINE_PATH=/source/cis/data/cis_memory.db \
  -p 5000:5000 \
  cis-hermes:pipeline"
```

The `launch_profiles.sh` CMD starts all 6 gateways. The Flask API (`runtime/app.py`)
needs to be started separately (or added to the launch script).

## What Still Needs To Be Done

1. ~~**Add Flask API to the launch script**~~ — DONE. `entrypoint.sh` starts the minimal
   `container_app.py` (relay blueprint only) on port 5000 after all gateways are up.
2. ~~**Test that `pipeline_relay.py` can find git inside the container**~~ — git is available
   in the `nikolaik/python-nodejs` base image. Verified during smoke test (L1 checks ran).
3. ~~**Verify the SQLite spine works with volume mount**~~ — WAL mode works on the bind-mounted
   volume. Worker UID 1000 matches host user for read/write access.
4. ~~**Verify `agent_trajectories_fts` works inside container**~~ — FTS5 is compiled into
   SQLite by default. Pre-discovery search works (brain phase received trajectory results).
5. **Add `KillMode=control-group` to systemd service files** — prevents stale processes
   when restarting host gateways (separate issue, not container-blocking).

## Resolution Summary (2026-07-09)

All 4 original gaps fixed:
1. **CIS codebase in container** — volume mount `/mnt/projects/cis` → `/workspace/cis`
2. **Host path assumptions** — `CIS_SPINE_PATH` + `CIS_PROJECT_ROOT` env vars in Dockerfile
3. **API keys** — `/tmp/cis-secrets.env` mounted at `/workspace/secrets.env`, entrypoint
   creates per-profile `.env` files with gateway + model provider keys
4. **Port publishing** — `-p 5000:5000` in `run_container.sh`

Additional fixes applied during container transition:
- `container_app.py` — minimal Flask app (relay blueprint only, avoids 30+ legacy imports)
- `entrypoint.sh` — per-profile .env creation, correct venv python path, `cd /workspace/cis`
  before gateway launch
- Profile configs — `platforms.api_server.extra.port` added (Hermes reads port from here,
  not top-level `api_server.port`)
- Managed config — removed model pinning (was forcing all profiles to same model)
- Worker UID 1000 — matches host user for volume-mounted SQLite write access
- File permissions — `0600` → `0644` on runtime files worker needs to read
- Project root injection in `_call_agent()` — agents find codebase at `/workspace/cis`
- Health endpoint import fix — `from dispatch` → `from abstraction.dispatch`
