# Penpot Visual Design Setup

Penpot is self-hosted on the CIS VM for visual design of the control plane
layout. Eric is a visual thinker, not a coder — he needs to drag-and-drop
shapes to figure out what the UI should actually look like, rather than
describing it in text to an agent.

## What's Running

```bash
# Docker Compose project: penpot
# Location: /mnt/projects/penpot/docker-compose.yaml
# URL: http://192.168.1.15:9001
```

7 containers:
- `penpot-frontend` — visual editor (port 9001)
- `penpot-backend` — API server
- `penpot-mcp` — MCP server (66+ tools for AI agents to read designs)
- `penpot-exporter` — SVG/PNG export
- `penpot-postgres` — database
- `penpot-valkey` — Redis replacement for websockets
- `penpot-mailcatch` — email catch (port 1080)

## Configuration

- `PENPOT_PUBLIC_URI`: `http://192.168.1.15:9001` (LAN accessible from iPad)
- `PENPOT_FLAGS`: `disable-email-verification enable-smtp enable-prepl-server disable-secure-session-cookies enable-mcp`
- `PENPOT_SECRET_KEY`: generated via `openssl rand -hex 32`
- Registration is open — no email verification needed
- Email field is just a username (use anything like `eric@cis.local`)

## MCP Server

The MCP server is built into the Penpot Docker Compose stack. It provides
66+ tools for AI agents to read and manipulate designs programmatically.

Endpoints (inside the penpot Docker network):
- Modern Streamable HTTP: `http://0.0.0.0:4401/mcp`
- Legacy SSE: `http://0.0.0.0:4401/sse`
- WebSocket: `ws://0.0.0.0:4402`
- REPL: `http://0.0.0.0:4403`

Tools include: `execute_code`, `high_level_overview`, `penpot_api_info`,
`export_shape`, and many more for reading shapes, text, components, and
layouts from Penpot design files.

## How It Connects to the Pipeline

1. Eric designs the control plane layout in Penpot (drag-and-drop)
2. The MCP server exposes the design to AI agents
3. The CIS pipeline can read the Penpot design via MCP and understand
   the intended layout (zones, components, positions)
4. Pipeline agents build React components matching the design

## Webstudio (Considered, Not Deployed)

Webstudio was also identified as a complementary tool (visual website
builder, like Webflow but open-source). However, self-hosting the Builder
is "not recommended for production" per their docs, and for the CIS use
case (internal tool UI, not a website), Penpot → pipeline → React code
is the better path. Webstudio can be added later for standalone site
projects.

## Complementary Tool: popular-web-designs Skill

The `popular-web-designs` skill (54 real design systems as HTML/CSS —
Stripe, Linear, Vercel, etc.) can serve as design references when
figuring out the control plane layout. Load it for visual inspiration.

## Eric's Control Plane Vision (from early chats)

The original vision (April 2026) was a three-zone layout:
- **Left:** Stream Deck-style collapsible controls (navigation, pipeline actions, knowledge, WIAS filters)
- **Center:** Active workspace / project panel / live thread
- **Right:** Intelligence sidebar (Brain chat, backchannel, agent outputs)

Early HTML mockups exist in `runtime/ui_mockups/` but Eric explicitly said
these were "first imaginations" — the real layout needs to be figured out
in Penpot based on actual workflow needs after building the real thing.

## Lifecycle Commands

```bash
# Start Penpot
cd /mnt/projects/penpot && sg docker -c "docker compose -p penpot -f docker-compose.yaml up -d"

# Stop Penpot
cd /mnt/projects/penpot && sg docker -c "docker compose -p penpot -f docker-compose.yaml down"

# Check status
sg docker -c "docker ps --filter name=penpot --format '{{.Names}} {{.Status}}'"

# View MCP server logs
sg docker -c "docker logs penpot-penpot-mcp-1"
```
