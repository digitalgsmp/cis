"""CIS Fast No-Guessing Proxy (port 8800).

Receives OpenAI chat completion requests, checks if the question is about
system configuration / routing / model / port / API key / status questions.
If yes, responds with verified local evidence from DB + port scan.
If no, proxies to the downstream Hermes Fast gateway on 8642.
"""

import http.client
import json
import logging
import os
import re
import sqlite3
import subprocess
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("cis-fast-proxy")

DB_PATH = "/mnt/projects/cis/runtime/db/cis_memory.db"
DOWNSTREAM_URL = "http://127.0.0.1:8642"
DOWNSTREAM_KEY = "5a51effab04a740206e3038ec23da119e154a534b80ad39d"

# Patterns that trigger local verification instead of guessing
SYSTEM_PATTERNS = [
    (r"what\s+model", "model query"),
    (r"what\s+port", "port query"),
    (r"what\s+gateway", "gateway query"),
    (r"what\s+config", "config query"),
    (r"is\s+thinking", "thinking query"),
    (r"what\s+api\s+key", "API key query"),
    (r"routing", "routing query"),
    (r"agent\s+instance", "agent instance query"),
    (r"current\s+status", "status query"),
    (r"(is|are)\s+\w+\s+(complete|done|finished)", "completion query"),
    (r"check\s+if\s+\w+\s+(is\s+)?(done|complete|finished)", "completion query"),
    (r"has\s+\w+\s+been\s+(finished|completed)", "completion query"),
    (r"what\s+version", "version query"),
]


def get_agent_instances():
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


def check_ports():
    """Run ss -tlnp and return listening port info for known CIS ports."""
    ports = {}
    try:
        result = subprocess.run(
            ["ss", "-tlnp"], capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            for port in ("8642", "8643", "8644", "8645"):
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


def verify_local_routing(query=""):
    """Build a verified report from local evidence."""
    agents = get_agent_instances()
    ports = check_ports()

    if not agents and not ports:
        return (
            "I cannot verify system configuration from local evidence right now. "
            "The system database and port checks are both unavailable. "
            "Please check manually or contact the operator."
        )

    lines = ["Here is what I verified from local evidence:\n"]

    if agents:
        lines.append("**Agent Routing Table:**")
        for a in agents:
            port = a["gateway_url"].split(":")[-1] if a["gateway_url"] else ""
            port_status = ""
            if port in ports:
                p = ports[port]
                port_status = f" [port {port}: active, PID {p['pid']}]" if p.get("pid") else f" [port {port}: active]"
            elif port:
                port_status = f" [port {port}: not checked]"
            active_str = "active" if a["active"] else "inactive"
            lines.append(
                f"- **{a['name']}** ({a['role']}) → {a['gateway_url']} "
                f"model={a['model']} ({active_str}){port_status}"
            )

    if ports:
        lines.append("\n**Verified Listening Ports:**")
        for port, info in sorted(ports.items()):
            state = f"PID {info['pid']}" if info.get("pid") else "listening"
            lines.append(f"- port {port}: {state}")

    lines.append(
        "\nI verified this from local database and port scan. "
        "I do not guess about system state. "
        "If you need information not listed here, check the config files or ask an operator."
    )
    return "\n".join(lines)


def is_system_question(text):
    """Return True if the user is asking about system/configuration topics."""
    for pattern, _ in SYSTEM_PATTERNS:
        if re.search(pattern, text.lower()):
            return True
    return False


def proxy_to_downstream(messages, model):
    """Forward the request to the Hermes Fast gateway and return its response."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        f"{DOWNSTREAM_URL}/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DOWNSTREAM_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read())
        return body


class NoGuessHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path == "/v1/rails/configs":
            self.send_json([{"id": "cis_fast"}])
        elif self.path == "/health":
            self.send_json({"status": "ok"})
        elif self.path == "/v1/models":
            self.send_json({
                "object": "list",
                "data": [{"id": "deepseek-v4-flash", "object": "model"}]
            })
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            self.handle_chat_completion()
        elif self.path == "/v1/rails/configs":
            self.send_json([{"id": "cis_fast"}])
        else:
            self.send_error(404, "Not found")

    def handle_chat_completion(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        messages = data.get("messages", [])
        model = data.get("model", "deepseek-v4-flash")

        # Get the last user message
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break

        logger.info(
            "PROXY agent=hermes-prime model=%s downstream=%s len(question)=%d system_check=%s",
            model, DOWNSTREAM_URL, len(last_user),
            is_system_question(last_user),
        )

        # If system question, respond with local verification
        if is_system_question(last_user):
            logger.info("GUARDRAIL triggered for: %.100s", last_user)
            report = verify_local_routing(query=last_user)
            response = {
                "id": f"chatcmpl-cis-fast-{os.urandom(4).hex()}",
                "object": "chat.completion",
                "model": model,
                "created": __import__("time").time(),
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": report},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        else:
            # Proxy to downstream
            try:
                response = proxy_to_downstream(messages, model)
            except Exception as e:
                logger.error("Downstream proxy failed: %s", e)
                response = {
                    "id": f"chatcmpl-cis-fast-{os.urandom(4).hex()}",
                    "object": "chat.completion",
                    "model": model,
                    "created": __import__("time").time(),
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"Downstream gateway error: {e}",
                        },
                        "finish_reason": "stop",
                    }],
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                }

        self.send_json(response)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logger.info("HTTP %s", format % args)


def run():
    port = 8800
    server = HTTPServer(("0.0.0.0", port), NoGuessHandler)
    logger.info("CIS Fast No-Guess Proxy listening on port %d", port)
    logger.info("Downstream: %s (model=deepseek-v4-flash)", DOWNSTREAM_URL)
    logger.info("System patterns loaded: %d", len(SYSTEM_PATTERNS))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    run()
