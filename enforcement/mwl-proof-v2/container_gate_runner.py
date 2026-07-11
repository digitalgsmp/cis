#!/usr/bin/env python3
"""
container_gate_runner.py — Runtime gate enforcement for Docker container.

Called by the mwl-proof plugin's pre_tool_call hook. Receives tool name + args,
runs relevant security checks, returns JSON decision.

Usage (called from plugin):
    echo '{"tool_name":"terminal","args":{"command":"ls"}}' | python3 /opt/cis-gates/container_gate_runner.py

Decision shapes:
    {"action":"allow"}                    — allow the tool call
    {"action":"block","reason":"..."}     — block the tool call
"""
import sys, json, re, os, subprocess
from pathlib import Path

GATES_DIR = Path("/opt/cis-gates")
ART_DIR = Path("/workspace/cis")

SECRET_PATTERNS = [
    (r'(?:api[_-]?key|apikey)["\s:=]+["\']?[A-Za-z0-9_\-]{20,}["\']?', "API key"),
    (r'(?:secret|password|passwd|pwd)["\s:=]+["\']?[^\s"\']{8,}["\']?', "password/secret"),
    (r'(?:token|bearer|auth)["\s:=]+["\']?[A-Za-z0-9_\-\.]{20,}["\']?', "auth token"),
    (r'(?:AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}', "AWS key"),
    (r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', "private key"),
    (r'ghp_[A-Za-z0-9]{36,}', "GitHub token"),
    (r'sk-[A-Za-z0-9]{20,}', "OpenAI-style key"),
    (r'xox[baprs]-[A-Za-z0-9-]+', "Slack token"),
]

DANGEROUS_CMD_PATTERNS = [
    (r'\brm\s+-rf\s+/(?:\s|$)', "rm -rf / (recursive root delete)"),
    (r'\bmkfs\b', "mkfs (filesystem format)"),
    (r'\bdd\s+.*of=/dev/', "dd to device"),
    (r':\(\)\{\s*:\|:&\s*\};:', "fork bomb"),
    (r'\bchmod\s+-R\s+777\s+/', "chmod 777 on root"),
    (r'\bcurl\s+.*\|\s*sh', "curl pipe to shell"),
    (r'\bwget\s+.*\|\s*sh', "wget pipe to shell"),
    (r'\bshutdown\b', "shutdown"),
    (r'\breboot\b', "reboot"),
    (r'\bsystemctl\s+(?:stop|disable|mask)\s+', "systemctl stop/disable/mask"),
]

FORBIDDEN_WRITE_PATHS = [
    "/opt/cis-gates/",
    "/opt/cis-policy/",
    "/opt/cis-hooks/",
    "/etc/hermes/",
    "/usr/local/lib/hermes-agent/",
]

# MCP tool classifications
MCP_READONLY_TOOLS = {
    "mcp_filesystem_read_file", "mcp_filesystem_read_text_file",
    "mcp_filesystem_read_multiple_files", "mcp_filesystem_list_directory",
    "mcp_filesystem_list_directory_with_sizes", "mcp_filesystem_directory_tree",
    "mcp_filesystem_get_file_info", "mcp_filesystem_search_files",
    "mcp_filesystem_read_media_file",
}


def log(name, line):
    try:
        with open(ART_DIR / name, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def check_secrets(text):
    findings = []
    for pattern, label in SECRET_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            findings.append((label, m.group()[:50]))
    return findings


def check_dangerous_command(cmd):
    findings = []
    for pattern, label in DANGEROUS_CMD_PATTERNS:
        m = re.search(pattern, cmd)
        if m:
            findings.append((label, m.group()[:80]))
    return findings


def check_forbidden_write_path(path):
    for fp in FORBIDDEN_WRITE_PATHS:
        if path.startswith(fp):
            return fp
    return None


def evaluate(tool_name, args):
    """Run relevant gates for a tool call. Returns (action, reason)."""
    reasons = []

    # Extract text content from common arg shapes
    cmd = ""
    content = ""
    path = ""
    if isinstance(args, dict):
        cmd = str(args.get("command", args.get("cmd", "")))
        content = str(args.get("content", args.get("text", args.get("new_string", ""))))
        path = str(args.get("path", args.get("file_path", "")))

    # 1. Terminal tool: check dangerous commands + secrets
    if tool_name == "terminal" and cmd:
        danger = check_dangerous_command(cmd)
        for label, match in danger:
            reasons.append(f"BLOCKED: dangerous command — {label}")
        secrets = check_secrets(cmd)
        for label, match in secrets:
            reasons.append(f"BLOCKED: secret detected — {label}")

    # 2. Write tools: check forbidden paths + secrets in content
    if tool_name in ("write_file", "patch", "execute_code") and path:
        fp = check_forbidden_write_path(path)
        if fp:
            reasons.append(f"BLOCKED: write to forbidden path {fp}")
    if tool_name in ("write_file", "patch") and content:
        secrets = check_secrets(content)
        for label, match in secrets:
            reasons.append(f"BLOCKED: secret in file content — {label}")

    # 3. MCP write tools: block entirely
    if tool_name.startswith("mcp_filesystem_") and tool_name not in MCP_READONLY_TOOLS:
        reasons.append(f"BLOCKED: MCP write tool {tool_name} not allowed")

    # 4. Keep proof marker test
    if tool_name == "terminal" and "MWL_PROOF_BLOCK_ME" in cmd:
        reasons.append("MWL_PROOF: proof marker blocked by gate runner")

    if reasons:
        return ("block", "; ".join(reasons))
    return ("allow", "")


def main():
    raw = sys.stdin.read()
    log("gate_runner_payload.jsonl", raw)

    tool_name = ""
    args = {}
    try:
        data = json.loads(raw)
        tool_name = str(data.get("tool_name", ""))
        args = data.get("args", data.get("tool_input", {}))
        if not isinstance(args, dict):
            args = {"command": str(args)}
    except Exception:
        pass

    action, reason = evaluate(tool_name, args)
    log("gate_runner_decisions.log", f"{tool_name} → {action}: {reason}")

    if action == "block":
        print(json.dumps({"action": "block", "reason": reason}))
    else:
        print(json.dumps({"action": "allow"}))


if __name__ == "__main__":
    main()
