# UI Build & Deploy Cycle

> Reference for editing, building, and deploying the CIS Control Panel UI.
> Path: `runtime/ui/` (host: /mnt/projects/cis/runtime/ui/, container: /workspace/cis/runtime/ui/)

## Stack
- React 19 + Vite 8
- Built to `dist/`, served at `/ui/` by `container_app.py` (Flask)
- 5 tabs: Project (default landing), Brain, Pipeline, Runs, System
- v1.2.0 as of 2026-07-12

## Edit → Build → Deploy Cycle

1. Edit React source in `runtime/ui/src/` (host side, any editor)
2. Build: `cd /mnt/projects/cis/runtime/ui && npm run build`
3. Output goes to `runtime/ui/dist/` — NO container restart needed
4. Flask serves from the mounted volume, so changes appear immediately on refresh

## Key Files
- `src/App.jsx` — main app, tab routing, health state
- `src/SystemDashboard.jsx` — System tab (docker containers, gateway health)
- `src/BrainChat.jsx` — Brain tab (chat with Brain gateway)
- `src/api.js` — API client, all endpoint calls
- `src/index.css` — all styling

## Backend Endpoints (Flask, port 5000)
- `/api/relay/brain/chat` — Brain chat relay
- `/api/relay/brain/history/<session>` — Brain chat history
- `/api/relay/system/health` — System health (docker + gateways + services)
- `/api/relay/system/restart` — Restart container
- `/api/relay/system/restart-all` — Restart all
- `/api/relay/system/logs/<container>` — Container logs
- `/api/relay/runs` — Pipeline runs list
- `/api/relay/run/<run_id>` — Specific run details
- `/api/health` — Simple health check

## Troubleshooting
- **Black screen after build:** Check `dist/` exists and `container_app.py` is serving it
- **API calls fail:** Verify Flask is running (`curl http://localhost:5000/api/health`)
- **System tab empty:** Docker socket not mounted or worker not in docker group (GID 982)
- **Changes not showing:** Hard refresh browser (Ctrl+Shift+R) — Vite hashes filenames

## Penpot (Visual Design)
- Self-hosted at http://192.168.1.15:9001
- Docker at /mnt/projects/penpot/ (7 containers)
- MCP server included for programmatic access
- Eric's tool for designing control plane layout visually
- Early HTML mockups at runtime/ui_mockups/ are "first imaginations" — superseded by Penpot
