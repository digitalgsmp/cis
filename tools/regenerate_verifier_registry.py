#!/usr/bin/env python3
"""
regenerate_verifier_registry.py — Regenerate the verifier registry from live system.

Runs every validation_command, updates values from ground truth, sets valid/invalid
status, and writes the updated registry.

Usage:
  python3 tools/regenerate_verifier_registry.py          # Dry run — print changes
  python3 tools/regenerate_verifier_registry.py --write  # Write updated registry
"""

import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(2)


def run_command(command: str, workdir: str = "") -> tuple[str, int]:
    """Run a command and return (stdout, exit_code)."""
    if not workdir:
        workdir = os.environ.get("CIS_ROOT", os.getcwd())

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=workdir,
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 124
    except Exception as e:
        return f"ERROR: {e}", 1


def parse_value(raw_output: str, expected) -> object:
    """Parse command output into the same type as expected value."""
    if expected is None:
        lines = [l.strip() for l in raw_output.split("\n") if l.strip()]
        if len(lines) == 1 and " " not in lines[0]:
            try:
                return int(lines[0])
            except ValueError:
                return lines[0]
        return lines

    if isinstance(expected, list):
        return sorted(raw_output.split())

    if isinstance(expected, int):
        try:
            return int(raw_output.strip())
        except ValueError:
            return raw_output.strip()

    return raw_output


def main():
    write = "--write" in sys.argv or "-w" in sys.argv

    registry_path = os.environ.get(
        "CIS_REGISTRY_PATH",
        os.path.join(os.getcwd(), "runtime/config/verifier_registry.yaml"),
    )

    if not os.path.exists(registry_path):
        print(f"ERROR: Registry not found at {registry_path}")
        sys.exit(2)

    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    facts = registry.get("facts", [])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    changed = 0
    errors = 0

    for fact in facts:
        key = fact["key"]
        command = fact.get("validation_command", "")
        if not command:
            continue

        output, exit_code = run_command(command)

        if exit_code != 0:
            print(f"  ERROR {key}: command failed (exit {exit_code})")
            print(f"         {output[:200]}")
            fact["valid"] = False
            errors += 1
            continue

        old_value = fact.get("value")
        new_value = parse_value(output, old_value)

        if old_value != new_value:
            print(f"  UPDATE {key}: {str(old_value)[:60]} → {str(new_value)[:60]}")
            fact["value"] = new_value
            fact["last_validated"] = now
            fact["valid"] = True
            changed += 1
        else:
            fact["last_validated"] = now
            fact["valid"] = True

    if write:
        with open(registry_path, "w") as f:
            yaml.dump(registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"\nRegistry written: {registry_path}")
    else:
        print(f"\nDry run — {changed} entries would be updated, {errors} errors.")
        if changed > 0:
            print("Run with --write to apply changes.")

    sys.exit(0 if errors == 0 else 1)


if __name__ == "__main__":
    main()
