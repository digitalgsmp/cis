#!/usr/bin/env python3
"""
validate_verifier_registry.py — Validate every registry entry against the live system.

Each entry in verifier_registry.yaml has a validation_command. This script runs
every command, compares output to validation_expected, and reports which entries
are valid/stale/broken.

Exit 0: all entries valid
Exit 1: one or more entries invalid or errors
"""

import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(2)


def load_registry(path: str) -> dict:
    """Load the verifier registry YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def run_validation(command: str, workdir: str = "") -> tuple[str, int]:
    """Run a validation command and return (stdout, exit_code)."""
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
        output = result.stdout.strip() + result.stderr.strip()
        return output, result.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 124
    except Exception as e:
        return f"ERROR: {e}", 1


def compare_output(actual: str, expected) -> bool:
    """Compare validation output to expected value."""
    if expected is None:
        # No expected value — any successful run is valid
        return True

    if isinstance(expected, list):
        # Compare as sorted newline-separated list
        actual_lines = sorted(actual.split())
        expected_lines = sorted(expected)
        return actual_lines == expected_lines

    if isinstance(expected, str):
        return actual == expected

    if isinstance(expected, int):
        try:
            return int(actual.strip()) == expected
        except ValueError:
            return False

    return False


def main():
    registry_path = os.environ.get(
        "CIS_REGISTRY_PATH",
        os.path.join(os.getcwd(), "runtime/config/verifier_registry.yaml"),
    )

    if not os.path.exists(registry_path):
        print(f"ERROR: Registry not found at {registry_path}")
        sys.exit(2)

    registry = load_registry(registry_path)
    facts = registry.get("facts", [])

    if not facts:
        print("ERROR: No facts in registry")
        sys.exit(2)

    valid_count = 0
    invalid_count = 0
    error_count = 0
    total = len(facts)

    print(f"Validating {total} registry entries against live system...\n")

    for fact in facts:
        key = fact["key"]
        command = fact.get("validation_command", "")
        expected = fact.get("validation_expected")
        description = fact.get("description", "")

        if not command:
            print(f"  SKIP  {key}: no validation_command")
            continue

        output, exit_code = run_validation(command)

        if exit_code != 0:
            print(f"  ERROR {key}: command failed (exit {exit_code})")
            print(f"         command: {command}")
            print(f"         output:  {output[:200]}")
            error_count += 1
            continue

        if compare_output(output, expected):
            print(f"  PASS  {key}")
            valid_count += 1
        else:
            print(f"  FAIL  {key}: output does not match expected")
            if expected is not None:
                print(f"         expected: {str(expected)[:100]}")
                print(f"         actual:   {output[:100]}")
            invalid_count += 1

    print(f"\n─── Results ───")
    print(f"  Total:   {total}")
    print(f"  Passed:  {valid_count}")
    print(f"  Failed:  {invalid_count}")
    print(f"  Errors:  {error_count}")

    if invalid_count == 0 and error_count == 0:
        print("\nAll registry entries validated successfully.")
        sys.exit(0)
    else:
        print(f"\nRegistry validation FAILED: {invalid_count + error_count} issue(s).")
        sys.exit(1)


if __name__ == "__main__":
    main()
