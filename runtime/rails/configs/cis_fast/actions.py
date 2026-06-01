"""CIS Fast No-Guessing Action: verify_local_routing_action.

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
    """Query the agent_instances table."""
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
    """Run ss -tlnp and return listening port info for CIS ports."""
    ports = {}
    try:
        result = subprocess.run(
            ["ss", "-tlnp"], capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            for port in ("8642", "8643", "8644", "8645", "8800"):
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
    """NeMo action: verify system routing from local evidence.

    Called by NeMo Guardrails when a system-config/routing question is detected.
    Returns a plain string containing verified report.
    Does not log user prompts or API secrets.
    """
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


# ── Tavily Web Evidence Action ──────────────────────────────────────────

import datetime
import json
import os


@action(name="verify_web_evidence_action")
def verify_web_evidence_action(**kwargs):
    """NeMo action: answer current external facts using Tavily web search.

    Uses Tavily API if TAVILY_API_KEY is configured.
    Returns NEEDS_TAVILY_API_KEY if the key is missing.
    Never answers current external facts from training data.
    """
    query = kwargs.get("query", "")
    logger.info("verify_web_evidence_action called (query length=%d)", len(query))

    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not api_key:
        return (
            "NEEDS_TAVILY_API_KEY\n\n"
            "I cannot answer this question from my training data alone. "
            "To look up current external facts, set TAVILY_API_KEY in the environment.\n\n"
            "Limitations:\n"
            "- TAVILY_API_KEY is not configured\n"
            "- I do not answer current model names, API versions, "
            "package versions, or pricing from memory\n"
            "- No guessing; no training-data fallback"
        )

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        result = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )
    except ImportError:
        return (
            "NEEDS_TAVILY_API_KEY\n\n"
            "tavily-python is not installed. Install with: pip install tavily-python"
        )
    except Exception as e:
        logger.error("Tavily search failed: %s", e)
        return (
            "WEB_EVIDENCE_ERROR\n\n"
            f"Web search failed: {e}"
        )

    retrieved_at = datetime.datetime.utcnow().isoformat()
    sources = result.get("results", [])
    answer = result.get("answer", "")

    lines = [
        "WEB_EVIDENCE_OK",
        "",
        f"Query: {query}",
        f"Retrieved at: {retrieved_at} (UTC)",
        f"Provider: Tavily",
        f"Search depth: advanced",
        "",
    ]

    if answer:
        lines.append(f"AI Summary: {answer}")
        lines.append("")

    if sources:
        lines.append(f"Sources ({len(sources)}):")
        for i, src in enumerate(sources, 1):
            title = src.get("title", "Untitled")
            url = src.get("url", "")
            snippet = src.get("content", "")[:200]
            lines.append(f"  {i}. {title}")
            if url:
                lines.append(f"     URL: {url}")
            if snippet:
                lines.append(f"     {snippet}")
            lines.append("")
    else:
        lines.append("No sources returned.")
        lines.append("")

    lines.append("Limitations:")
    lines.append("- Web evidence is a snapshot, not real-time")
    lines.append("- Verify critical facts against primary sources")
    lines.append("- I do not answer from training data alone")
    lines.append("- No guessing; evidence-grounded only")

    return "\n".join(lines)


# ── Execution / Completion Claim Blocking ──────────────────────────────

@action(name="block_execution_claim")
def block_execution_claim(**kwargs):
    """NeMo action: blocks execution and completion claims for Fast Chat.

    Fast cannot execute, write files, modify code, run commands, restart
    services, or claim task/phase completion.  These must escalate to
    V4-Pro R1 for proposal or Qwen Worker for execution.
    """
    return (
        "FAST_EXECUTION_BLOCKED\n\n"
        "Fast Chat cannot execute or claim completion.\n"
        "Escalate this to V4-Pro R1 for proposal or Qwen Worker "
        "for execution after reconciliation."
    )


# ── Pass-Through Query ─────────────────────────────────────────────────

import urllib.request
import json as _json

FAST_API_URL = "http://127.0.0.1:8642/v1/chat/completions"
FAST_API_KEY = "5a51effab04a740206e3038ec23da119e154a534b80ad39d"


@action(name="pass_through_query")
def pass_through_query(**kwargs):
    """Pass a query through to deepseek-v4-flash on port 8642.

    Used for general questions and creative prompts that should not
    be intercepted by guardrails.  Bypasses NeMo's LLM call entirely.
    """
    query = kwargs.get("query", "")
    logger.info("pass_through_query called (query length=%d)", len(query))

    body = _json.dumps({
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": query}],
        "max_tokens": 500,
    }).encode()

    req = urllib.request.Request(
        FAST_API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FAST_API_KEY}",
        },
    )

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = _json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("Fast pass-through failed: %s", e)
        return (
            "PASS_THROUGH_ERROR\n\n"
            f"Fast Chat could not reach the backend model: {e}"
        )
