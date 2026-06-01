"""CIS V4-Pro R1 Action: verify_local_routing_action.

Registered with @action decorator for native NeMo Guardrails discovery.
Returns verified local evidence from DB + port scan.

Secrets are not included in the output.
"""

import logging
import sqlite3
import subprocess

from nemoguardrails.actions import action

logger = logging.getLogger(__name__)

DB_PATH = "/mnt/projects/cis/runtime/db/cis_memory.db"


def _get_agent_instances():
    results = []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT name, role, gateway_url, model, active FROM agent_instances ORDER BY id"
        ).fetchall()
        conn.close()
        for r in rows:
            d = dict(r)
            results.append({
                "name": d["name"], "role": d["role"],
                "gateway_url": d["gateway_url"], "model": d["model"],
                "active": bool(d["active"]),
            })
    except Exception as e:
        logger.error("DB query failed: %s", e)
    return results


def _check_ports():
    ports = {}
    try:
        result = subprocess.run(
            ["ss", "-tlnp"], capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            for port in ("8642", "8643", "8644", "8645", "8800", "8801"):
                if f":{port}" in line:
                    pid = None
                    if "pid=" in line:
                        try:
                            pid_str = line.split("pid=")[1].split(",")[0]
                            pid = int(pid_str)
                        except (IndexError, ValueError):
                            pass
                    ports[port] = {"listening": True, "pid": pid}
    except Exception as e:
        logger.error("ss check failed: %s", e)
    return ports


@action(name="verify_local_routing_action")
def verify_local_routing_action(**kwargs):
    query = kwargs.get("query", "")
    logger.info("verify_local_routing_action called (query length=%d)", len(query))

    agents = _get_agent_instances()
    ports = _check_ports()

    if not agents and not ports:
        return (
            "NATIVE_ACTION_OK\n\n"
            "I cannot verify system configuration from local evidence right now. "
            "The system database and port checks are both unavailable. "
            "Please check manually or contact the operator."
        )

    lines = ["NATIVE_ACTION_OK", ""]

    if agents:
        lines.append("Agent Routing Table:")
        for a in agents:
            port = a["gateway_url"].split(":")[-1] if a["gateway_url"] else ""
            port_status = ""
            if port in ports:
                p = ports[port]
                port_status = f" [port {port}: active PID {p['pid']}]" if p.get("pid") else f" [port {port}: active]"
            elif port:
                port_status = f" [port {port}: not checked]"
            active_str = "active" if a["active"] else "inactive"
            lines.append(
                f"  - {a['name']} ({a['role']}) -> {a['gateway_url']} "
                f"model={a['model']} ({active_str}){port_status}"
            )

    if ports:
        lines.append("")
        lines.append("Listening Ports:")
        for port, info in sorted(ports.items()):
            state = f"PID {info['pid']}" if info.get("pid") else "listening"
            lines.append(f"  - port {port}: {state}")

    lines.append("")
    lines.append("Verified from local DB and port scan. No guessing.")

    return "\n".join(lines)
