import json
import subprocess
from datetime import datetime
from pathlib import Path

ART = Path("/workspace")
GATE_RUNNER = "/opt/cis-gates/container_gate_runner.py"


def _log(name, line):
    try:
        with open(ART / name, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _pre_tool_call(tool_name=None, args=None, task_id="", **kwargs):
    _log("hook_seen.log", f"{datetime.now().isoformat()} FIRED tool={tool_name}")

    try:
        _log("hook_payload.jsonl", json.dumps(
            {"tool_name": tool_name, "args": args, "task_id": task_id}, default=str))
    except Exception:
        pass

    # Invoke container_gate_runner for real enforcement
    try:
        payload = json.dumps({"tool_name": tool_name, "args": args or {}})
        result = subprocess.run(
            ["python3", GATE_RUNNER],
            input=payload,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            decision = json.loads(result.stdout)
            if decision.get("action") == "block":
                msg = decision.get("reason", "blocked by container gate runner")
                return {
                    "action": "block",
                    "decision": "block",
                    "message": msg,
                    "reason": msg,
                }
    except Exception as e:
        _log("gate_runner_errors.log", f"{datetime.now().isoformat()} ERROR: {e}")

    return None


def register(ctx):
    _log("plugin_load.log", f"{datetime.now().isoformat()} LOADED register() ran")
    ctx.register_hook("pre_tool_call", _pre_tool_call)
