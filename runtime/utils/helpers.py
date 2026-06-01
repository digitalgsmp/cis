"""
utils/helpers.py — Shared utility functions.
Timestamp, file I/O, and subprocess helpers used across all modules.
"""

import json
import subprocess
from datetime import datetime, timezone


def ts():
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def today():
    """Return current UTC date as YYYY-MM-DD string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_json(path):
    """Load and return parsed JSON from a file path."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """Serialize data to JSON and write to file path."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_command(cmd, timeout=300):
    """
    Run a shell command and return a result dict.
    Always returns: { success, stdout, stderr, returncode }
    Never raises — errors are captured in the return value.
    """
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {
            "success":    result.returncode == 0,
            "stdout":     result.stdout.strip(),
            "stderr":     result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}
