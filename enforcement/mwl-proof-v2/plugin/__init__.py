import json
import subprocess
from datetime import datetime
from pathlib import Path

ART = Path("/workspace/cis")
GATE_RUNNER = "/opt/cis-gates/container_gate_runner.py"

# OVERRIDE PLANE — queue item 0.4. Host dir .gate-control mounted read-only at
# /opt/cis-control/gate, so this file is readable here and creatable only from
# the host. `touch` it to disable the wall, `rm` it to re-arm; both take effect
# on the next tool call with no restart.
GATE_OVERRIDE = Path("/opt/cis-control/gate/DISABLED")


def _log(name, line):
    try:
        with open(ART / name, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _pre_tool_call(tool_name=None, args=None, task_id="", **kwargs):
    # ── OVERRIDE PLANE. FIRST STATEMENT. DO NOT MOVE BELOW ANYTHING. ──────
    # The record: "Every gate in this architecture checks the override plane as
    # its first line. You are never more than one `touch` command from a working
    # system." It sits above the logging and above the subprocess so that a hook
    # which cannot log, or a runner which will not start, can still be overridden
    # — those are precisely the states an override exists for.
    #
    # An unreadable override falls through to normal enforcement rather than
    # disabling it: the failure of the off switch must not itself be an off
    # switch.
    try:
        if GATE_OVERRIDE.exists():
            _log("gate_override.log",
                 f"{datetime.now().isoformat()} OVERRIDE ACTIVE — allowed "
                 f"tool={tool_name} task={task_id}")
            return None
    except Exception:
        pass

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
