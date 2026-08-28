# Pitfalls and Solutions (Session 2026-07-12/13)

## read_file → write_file pipe corruption
`read_file` returns content with `N|` line number prefixes (e.g., `33|export CIS_BRAIN...`).
If you pass this output directly to `write_file`, the line numbers get embedded in the file,
corrupting it. Fix: use `terminal("cat <file>")` for raw content, or strip `N|` prefixes before
writing, or use `patch` (matches against actual file content, not the line-numbered display).

## Docker entrypoint stale keys
When the Docker image bakes in an entrypoint with truncated/placeholder values
(e.g., `cis-br...2026` instead of `cis-brainstorm-gateway-key-2026`):
1. Fix the file on host: `awk '{gsub(/cis-br\.\.\.2026/, "cis-brainstorm-gateway-key-2026"); print}' entrypoint.sh > fixed.sh && mv fixed.sh entrypoint.sh`
2. Mount the corrected file: `-v /mnt/projects/cis/enforcement/mwl-proof-v2/entrypoint.sh:/opt/cis-control/entrypoint.sh:ro`
3. **`docker restart` does NOT re-run the entrypoint** — it just restarts the process with old env vars.
   Must `docker stop && docker rm && docker run` to force the entrypoint to re-execute.

## secrets.env mount path
Correct: `/mnt/projects/cis/secrets.env` (a file)
Wrong: `/mnt/projects/cis/enforcement/mwl-proof-v2/secrets.env` (a directory — Docker creates it
as an empty dir if the source path is wrong, causing "not found" on source command)

## React component black screen
An undefined bare variable in a JSX component (e.g., `gates` when code meant `feed?.gates`)
throws a `ReferenceError` that crashes the ENTIRE React component — rendering a black screen
with no error visible to the user. Always use optional chaining (`feed?.gates || []`) for
data that arrives from async polling. The error is silent in production builds.

## Auto-scroll on polled data
When a React component polls an API every 2 seconds, an auto-scroll `useEffect` keyed on `[feed]`
fires on every poll — causing the page to snap to the bottom continuously, even for completed data.
Fix: track a `phaseCount` ref and only scroll when the count increases (new phase added):
```jsx
const phaseCount = feed?.phases?.length || 0
const prevPhaseCount = useRef(0)
useEffect(() => {
  if (scrollRef.current && phaseCount > prevPhaseCount.current) {
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }
  prevPhaseCount.current = phaseCount
}, [phaseCount])
```

## Penpot visual design integration
Penpot self-hosted via Docker Compose (7 containers: frontend:9001, backend, exporter, mcp, postgres:5432, valkey:6379, mailcatch:1080).
- Config at `/mnt/projects/penpot/docker-compose.yaml`
- Built-in MCP server (tools: execute_code, high_level_overview, penpot_api_info, export_shape) on port 4401 inside penpot network
- Registration open (disable-email-verification flag), no email needed
- Eric uses Penpot to visually design UI layouts — pipeline agents can read designs via MCP
- Penpot + Webstudio identified as complementary: Penpot for design, Webstudio for code generation

## Uncommitted code changes are not live in a running Flask server

Flask loads all routes at import time. If you add or modify an endpoint
in `container_app.py` (or any Flask app module) and the running server
process predates the file change, the new route returns 405 Method Not
Allowed — even though the code is correct and a fresh `app.url_map`
import shows the route registered.

This is especially insidious when code was written by a prior pipeline
run (e.g. run-578251939d8bece7 added `/api/relay/run` to
`container_app.py`) but the server was never restarted. The code exists
in the working tree (uncommitted), `app.url_map` confirms it when you
import the module in a separate Python process, but the live server
process still has the old code in memory.

Verification:
```bash
# Compare process start time vs file mtime
ps -p $(pgrep -f container_app) -o lstart --no-headers
stat -c '%y' runtime/container_app.py
# If file mtime > process start, server has stale code

# Quick check: does the route return 405?
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:5000/api/relay/run \
  -H "Content-Type: application/json" -d '{"intent":"test"}'
# 405 = route not in running server's url_map
# 200 = route is live
```

Fix: restart the server (or `docker restart cis-pipeline`) after any
change to Flask route definitions. Also: commit code changes —
uncommitted working-tree changes are invisible to `git log` and can
cause confusion about when a feature was added.

## Gateway API key chain
The relay (Flask on port 5000) calls gateways using `CIS_{ROLE}_API_KEY` env vars.
Gateways authenticate locally with these keys, then call upstream model providers
(DeepSeek, OpenRouter) using keys from `secrets.env` → profile `.env` files.
If the relay gets "Invalid API key" → gateway key mismatch (check entrypoint exports).
If the relay gets "HTTP 401: Authentication Fails, Your api key: ****.KEY is invalid" →
the upstream provider key is wrong/missing (check secrets.env and .env propagation).
