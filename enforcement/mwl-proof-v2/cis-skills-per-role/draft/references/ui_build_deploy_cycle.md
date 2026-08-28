# UI Build → Deploy Cycle

The CIS control panel UI is a React 19 + Vite 8 SPA in `runtime/ui/`.
Source files in `runtime/ui/src/`, built to `runtime/ui/dist/`, served
at `/ui/` by `container_app.py` inside the `cis-pipeline` container.

The CIS repo is mounted as a volume (`/mnt/projects/cis` → `/workspace/cis`),
so built assets are immediately visible inside the container — no image
rebuild needed for UI changes.

## Standard Edit-Build-Deploy Cycle

```bash
# 1. Edit source (on host)
#    e.g. runtime/ui/src/ProjectCenter.jsx

# 2. Build (on host, from the ui directory)
cd /mnt/projects/cis/runtime/ui && npm run build

# 3. Restart container (picks up new dist/ assets)
sg docker -c "docker restart cis-pipeline"

# 4. Wait for startup (~8 seconds for all 6 gateways)
sleep 8

# 5. Verify health endpoint
curl -s http://localhost:5000/health

# 6. Verify the specific API endpoint you changed
curl -s http://localhost:5000/api/relay/project/cis/overview | python3 -m json.tool
```

## React Component Black Screen (Silent Crash)

When a React component throws a `ReferenceError` (e.g. referencing an
undefined variable), the entire component renders as a **black screen**
with no error message visible to the user. There is no error boundary
in the current app.

### Root Cause Pattern

API response data is fetched asynchronously and stored in state. If a
component references a field from the response **without optional chaining**
before the fetch completes, the variable is `undefined` and any operation
on it (like `.reduce()`) throws.

### Example Fix (2026-07-12)

PipelineLive.jsx line 80 referenced `gates` as a bare variable, but
`gates` was never destructured from `feed`. The fix:

```jsx
// WRONG — crashes if feed hasn't loaded yet
const gatesByPhase = (gates || []).reduce((acc, g) => { ... })

// CORRECT — optional chaining on the async state
const gatesByPhase = (feed?.gates || []).reduce((acc, g) => { ... })
```

### Debugging Steps

1. Check browser DevTools console for `ReferenceError` or `TypeError`
2. Read the component source — look for variables that come from API
   responses but aren't guarded with `?.` or default values
3. The error is almost always a missing `feed?.` or `overview?.` prefix
4. Fix, rebuild, restart

### Prevention

Always use optional chaining for async state:
```jsx
const data = feed?.gates || []
const stats = overview?.stats || {}
```

Never assume the fetch has completed on first render.

## Adding New API Endpoints

When adding a new endpoint to `runtime/api/relay.py`:

1. Add the route function with `@relay_bp.route(...)` decorator
2. Restart container: `sg docker -c "docker restart cis-pipeline"`
3. If the route returns 404, Python's `__pycache__` may be stale —
   the restart usually clears it. If not, remove `__pycache__` dirs.
4. Test with: `curl -s http://localhost:5000/api/relay/<endpoint>`

## Adding New UI Components

1. Create `runtime/ui/src/ComponentName.jsx`
2. Import and add to `App.jsx` as a new tab or route
3. Add API methods to `runtime/ui/src/api.js`
4. Add CSS to `runtime/ui/src/index.css`
5. Build + restart (see cycle above)

## Current UI Components (as of 2026-07-12)

| Component | Tab | Purpose |
|-----------|-----|---------|
| ProjectCenter | Project (default) | Build plan, runs, ADRs, dev pivots, start work |
| BrainChat | Brain | Pre-pipeline conversation with Brain, KB search |
| PipelineLive | Pipeline | Live observation feed, all 6 role outputs, gates, backchannel |
| RunsList | Runs | Recent run history, click to observe |
| SystemDashboard | System | Gateway health, container overview, Docker logs |

## Penpot for Visual Layout Design

Penpot is self-hosted at `http://192.168.1.15:9001` for visual design
of the control plane layout. Eric is a visual thinker who needs to
drag-and-drop shapes to design the real layout, not describe it in text.

See [penpot_visual_design_setup.md](penpot_visual_design_setup.md) for
full setup details.
