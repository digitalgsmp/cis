"""
server.py — CIS MCP Bridge stdio server entry point.

Uses the mcp Python package (same SDK as Hermes native MCP client).
Registers 9 read-only CIS spine tools and handles stdio transport.

Usage (by Hermes MCP config):
  command: ~/.hermes/hermes-agent/venv/bin/python
  args: ["-m", "cis_mcp_bridge.server"]
  env:
    CIS_SPINE_PATH: /mnt/projects/cis/data/cis_memory.db

The module must be importable — PYTHONPATH must include
/mnt/projects/cis/runtime.
"""
import json
import sys
import traceback

from . import tools


def create_mcp_server():
    """
    Create and configure the MCP server.

    Uses the mcp.server.stdio transport. Registers all 9 tools
    from tools.TOOLS and dispatches calls to tools.HANDLERS.
    """
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool

    server = Server("cis-mcp-bridge")

    # ── Register tool list ────────────────────────────
    @server.list_tools()
    async def handle_list_tools():
        """Return all registered CIS tools."""
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"],
            )
            for t in tools.TOOLS
        ]

    # ── Handle tool calls ─────────────────────────────
    @server.call_tool()
    async def handle_call_tool(name, arguments):
        """Dispatch tool call to the correct handler."""
        handler = tools.HANDLERS.get(name)
        if handler is None:
            return {
                "content": [{"type": "text", "text": json.dumps(
                    {"error": "Unknown tool: {}".format(name)}
                )}],
                "isError": True,
            }

        try:
            result = handler(arguments)
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "isError": False,
            }
        except Exception as exc:
            tb = traceback.format_exc()
            return {
                "content": [{"type": "text", "text": json.dumps(
                    {"error": str(exc), "traceback": tb}
                )}],
                "isError": True,
            }

    return server, stdio_server


async def main():
    """Entry point: create MCP server and run stdio transport."""
    server, transport = create_mcp_server()

    async with transport() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run():
    """Synchronous entry point for -m invocation."""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    run()
