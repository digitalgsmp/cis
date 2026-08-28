# CIS Container Architecture Reference

## Core Topology

**One container, six profiles** — not six separate containers.

```
┌─────────────────────────────────────────────────────┐
│  cis-pipeline container (image: cis-hermes:pipeline)│
│                                                     │
│  ┌─────────────────┐    ┌─────────────────────────┐ │
│  │ Flask API        │    │ 6 Internal Gateways     │ │
│  │ container_app.py │    │ (entrypoint.sh launches)│ │
│  │ port 5000        │    │ 127.0.0.1:8643-8648    │ │
│  └────────┬────────┘    └──────────┬──────────────┘ │
│           │  dispatch.py            │                │
│           │  BASE_URL=              │                │
│           │  http://127.0.0.1       │                │
│           └─────────────────────────┘                │
│                                                     │
│  Only port 5000 published to host                   │
│  Gateways are internal — not accessible from host   │
└─────────────────────────────────────────────────────┘
```

## Gateway Port Map (Internal)

| Role    | Port | Model           | Container Profile Dir       |
|---------|------|-----------------|-----------------------------|
| Brain   | 8644 | deepseek-v4-pro | /home/worker/.hermes-brain  |
| Draft   | 8645 | deepseek-v4-pro | /home/worker/.hermes-draft  |
| Review1 | 8643 | qwen3.7-max     | /home/worker/.hermes-review1|
| Review2 | 8647 | glm-5.2         | /home/worker/.hermes-review2|
| Menter  | 8646 | deepseek-v4-pro | /home/worker/.hermes-menter |
| Verify  | 8648 | glm-5.2         | /home/worker/.hermes-verify |

## What Does NOT Exist in the Architecture

- **Separate gateway containers** (cis-brainstorm, cis-drafter, etc. on image cis-hermes:v2, ports 874x) — these were leftover artifacts from the build phase. The decision was explicitly "one container, six profiles" over "six separate containers — lighter on resources." They were removed on 2026-07-12.
- **cis-hermes (image cis-hermes:pinned)** — leftover enforcement proof-of-concept container. Runs `sleep infinity`, not serving any active purpose. The pipeline container (`cis-hermes:pipeline`) supersedes it entirely. Can be removed.

## What IS Kept Running (Intentionally)

- **Host-side systemd gateway services** on 127.0.0.1:864x — these are Eric's intentional fallback for root-required work and repairs the contained system can't do itself. Do NOT recommend stopping or removing them. Eric is not a coder and needs the host side as a safety net. This is not a mistake or legacy — it's a deliberate operational decision.

## Docker Access from Host

Eric is in the docker group but not in the active session group. Use `sg docker -c "command"` to run any docker command without sudo. Do NOT claim docker commands are impossible — find the access path first.

```bash
sg docker -c "docker ps"
sg docker -c "docker restart cis-pipeline"
sg docker -c "docker exec cis-hermes ls /home/worker/.hermes/"
```

## Commit vs Push (Eric's Expectation)

When Eric says "commit" or asks if something is "committed," he means **pushed to GitHub** — not just a local commit. A local commit without push is NOT a backup. Always `git push origin master` after committing, or clarify "local commit only, not pushed yet" if a push is deferred.

## Self-Restart Pattern

When restarting `cis-pipeline` from within itself, return the HTTP response BEFORE executing the restart. Otherwise the connection is killed mid-response.

```python
if container == "cis-pipeline":
    import threading, time
    def _delayed_restart():
        time.sleep(0.5)
        subprocess.run(["docker", "restart", container], ...)
    threading.Thread(target=_delayed_restart, daemon=True).start()
    return jsonify({"status": "ok", "note": "self-restart scheduled"})
```

## System Dashboard Health Check

The health check in `container_app.py` `_system_health()` must check **internal gateways** on `127.0.0.1:864x`, NOT external Docker container port mappings (874x). The Flask process runs inside the container — `localhost` from its perspective is the container's own loopback, where the 6 gateways live.

The API response now includes a `gateways` array (6 entries with name, port, model, healthy) separate from the `containers` array (Docker container overview). The UI renders these as separate sections: "Pipeline Gateways (Internal)" and "Docker Containers."

### Correct pattern:
```python
# Check internal gateways
for label, (port, model) in _GATEWAY_PORTS.items():
    hresult = subprocess.run(
        ["curl", "-s", "--max-time", "3", f"http://127.0.0.1:{port}/health"],
        capture_output=True, text=True, timeout=5
    )
    ok = hresult.returncode == 0 and "ok" in hresult.stdout.lower()
```

### Wrong pattern (does NOT work from inside the container):
```python
# This tries to reach host-mapped ports — not accessible from inside container
port_match = re.search(r"0\.0\.0\.0:(\d+)->", ports)  # gets 874x
curl http://localhost:{874x}/api/health  # FAILS — connection reset
```

## Investigation Checklist for CIS Infrastructure

Before declaring anything broken, verify against live evidence:

1. **Recent commits**: `git log --oneline -10`
2. **Session history**: `session_search` for what was done recently
3. **Pipeline runs**: `sqlite3 data/cis_memory.db "SELECT id, status, created_at FROM workflow_runs ORDER BY created_at DESC LIMIT 5;"`
4. **Agent trajectories**: `sqlite3 data/cis_memory.db "SELECT id, run_id, role, phase, outcome FROM agent_trajectories WHERE run_id = '<run_id>' ORDER BY id;"`
5. **Health endpoint**: `curl http://localhost:5000/api/relay/system/health`
6. **Internal gateways**: `for port in 8643 8644 8645 8646 8647 8648; do curl -s http://127.0.0.1:$port/health; done`
7. **Container processes**: `cat /proc/$(pgrep -f container_app)/net/tcp` to see what ports are actually listening inside the container

**Key lesson**: A handoff doc's "Known Issues" section describes problems as of the last session. The system may have been working since. Verify claims against live evidence before acting on them. If the user says "I thought we've been using this for days," you skipped the verification step.

**Don't claim you can't do something** — find the alternative path before telling the user it's impossible. If a direct command fails with permission denied, check for `sg docker -c`, API endpoints, or other access patterns. The user called this out explicitly: "You have been accessing the container all along but you keep making the statement that you cannot do things."

## Pre-Commit Hook Behavior

The CIS repo has a pre-commit hook that auto-regenerates HCP exports and AGENTS.md from the
SQLite spine. Key behaviors:

- `git commit` regenerates 13 export artifacts and auto-stages them
- `git commit --amend --no-edit` produces NEW timestamp diffs (hook runs again)
- This is expected, NOT a bug — don't try to "fix" the timestamp drift
- Warning "expected 12 artifacts, found 13" is benign — manifest count hasn't been updated
- After commit, working tree shows modified export files (timestamps) — this is normal

## Key Files

| File | Purpose |
|------|---------|
| `runtime/container_app.py` | Flask app + system dashboard routes (runs inside container) |
| `runtime/abstraction/dispatch.py` | Profile dispatch map + gateway health (BASE_URL=127.0.0.1) |
| `runtime/abstraction/pipeline_relay.py` | Pipeline state machine + provenance |
| `enforcement/mwl-proof-v2/Dockerfile` | Container image build (cis-hermes:pipeline) |
| `enforcement/mwl-proof-v2/entrypoint.sh` | Launches 6 gateways + Flask API |
| `enforcement/mwl-proof-v2/managed-config.yaml` | Sealed enforcement config (root-owned) |
| `enforcement/mwl-proof-v2/profiles/*.yaml` | Per-profile config with port settings |
| `runtime/ui/src/SystemDashboard.jsx` | System tab React component (gateways + containers + services) |
