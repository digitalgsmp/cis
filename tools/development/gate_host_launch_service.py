#!/usr/bin/env python3
"""Fail-closed verifier for the narrow host pipeline launch service.

Read-only. It proves four things about an installed launch package: the unit and
sudoers policy match their sealed bytes, mode and root ownership; the sealed
launcher the unit runs is itself root-owned and 0555; the unit runs nothing but
that launcher and asserts (not merely conditions on) its presence; and the
installed sudoers policy still parses.
"""

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_check(name, sealed, installed, mode, uid=0, gid=0):
    row = {"name": name, "sealed": sealed, "installed": installed,
           "passed": False}
    failures = []
    for label, path in (("sealed", sealed), ("installed", installed)):
        if os.path.islink(path) or not os.path.isfile(path):
            failures.append(f"{label} file absent, non-regular, or symlinked: {path}")
    if failures:
        row["failures"] = failures
        return row
    sealed_hash = _sha256(sealed)
    installed_hash = _sha256(installed)
    row.update({"sealed_sha256": sealed_hash,
                "installed_sha256": installed_hash})
    if sealed_hash != installed_hash:
        failures.append(f"installed bytes differ from sealed {name}")
    installed_stat = os.stat(installed)
    actual_mode = stat.S_IMODE(installed_stat.st_mode)
    row["mode"] = format(actual_mode, "04o")
    row["owner"] = f"{installed_stat.st_uid}:{installed_stat.st_gid}"
    if actual_mode != mode:
        failures.append(
            f"installed {name} mode is {actual_mode:04o}, expected {mode:04o}")
    if (installed_stat.st_uid, installed_stat.st_gid) != (uid, gid):
        failures.append(
            f"installed {name} owner is {installed_stat.st_uid}:{installed_stat.st_gid}, "
            f"expected {uid}:{gid}")
    row["failures"] = failures
    row["passed"] = not failures
    return row


def _sealed_program_check(name, path, mode, uid=0, gid=0):
    """Check a sealed program the unit will run as root, with no installed twin."""
    row = {"name": name, "sealed": path, "passed": False}
    failures = []
    if os.path.islink(path) or not os.path.isfile(path):
        failures.append(f"sealed program absent, non-regular, or symlinked: {path}")
        row["failures"] = failures
        return row
    info = os.stat(path)
    actual_mode = stat.S_IMODE(info.st_mode)
    row.update({"sealed_sha256": _sha256(path),
                "mode": format(actual_mode, "04o"),
                "owner": f"{info.st_uid}:{info.st_gid}"})
    if actual_mode != mode:
        failures.append(
            f"sealed {name} mode is {actual_mode:04o}, expected {mode:04o}")
    if (info.st_uid, info.st_gid) != (uid, gid):
        failures.append(
            f"sealed {name} owner is {info.st_uid}:{info.st_gid}, expected {uid}:{gid}")
    row["failures"] = failures
    row["passed"] = not failures
    return row


def _unit_contract_check(unit_path, launcher_path):
    """Check the installed unit launches only the sealed launcher, and asserts it.

    ConditionPathExists is rejected on purpose: a failed condition makes systemd
    skip the unit and report success, which is a silent gate failure. An Assert
    fails the unit loudly, which is what a missing trust root should do.
    """
    row = {"name": "unit_contract", "installed": unit_path, "passed": False}
    failures = []
    if os.path.islink(unit_path) or not os.path.isfile(unit_path):
        row["failures"] = [f"installed unit absent, non-regular, or symlinked: {unit_path}"]
        return row
    with open(unit_path, encoding="utf-8", errors="replace") as handle:
        lines = [line.strip() for line in handle]
    directives = [line for line in lines if line and not line.startswith("#")]
    if any(line.startswith("ConditionPathExists=") for line in directives):
        failures.append(
            "unit uses ConditionPathExists, which silently skips the unit; "
            "AssertPathExists is required")
    if f"AssertPathExists={launcher_path}" not in directives:
        failures.append(f"unit does not assert the sealed launcher path {launcher_path}")
    exec_lines = [line for line in directives
                  if line.startswith(("ExecStart=", "ExecStop=", "ExecStartPre=",
                                      "ExecStartPost=", "ExecStopPost=",
                                      "ExecCondition=", "ExecReload="))]
    if not any(line.startswith("ExecStart=") for line in exec_lines):
        failures.append("unit declares no ExecStart")
    for line in exec_lines:
        command = line.split("=", 1)[1].strip().lstrip("-+!@")
        if not command.split(" ")[0] == launcher_path:
            failures.append(f"unit runs a program other than the sealed launcher: {line}")
    restart_lines = [line for line in directives if line.startswith("Restart=")]
    for line in restart_lines:
        if line.split("=", 1)[1].strip().lower() != "no":
            failures.append(f"unit delegates lifecycle to systemd restart policy: {line}")
    row["directives"] = exec_lines
    row["restart_directives"] = restart_lines
    row["failures"] = failures
    row["passed"] = not failures
    return row


def evaluate(*, control_root="/opt/cis-control",
             unit_path="/etc/systemd/system/cis-pipeline.service",
             sudoers_path="/etc/sudoers.d/cis-pipeline",
             expected_uid=0, expected_gid=0, run_visudo=True,
             launcher_path=None):
    launcher_path = launcher_path or os.path.join(control_root, "bin/cis-container")
    checks = [
        _file_check(
            "systemd_unit",
            os.path.join(control_root, "systemd/cis-pipeline.service"),
            unit_path, 0o444, expected_uid, expected_gid),
        _file_check(
            "sudoers_policy",
            os.path.join(control_root, "policy/cis-pipeline.sudoers"),
            sudoers_path, 0o440, expected_uid, expected_gid),
        _sealed_program_check(
            "container_launcher", launcher_path, 0o555, expected_uid, expected_gid),
        _unit_contract_check(unit_path, launcher_path),
    ]
    if run_visudo and checks[1]["passed"]:
        result = subprocess.run(
            ["/usr/sbin/visudo", "-cf", sudoers_path],
            capture_output=True, text=True, timeout=15)
        checks.append({
            "name": "sudoers_syntax",
            "passed": result.returncode == 0,
            "evidence": (result.stdout + result.stderr).strip(),
        })
    failures = []
    for row in checks:
        if not row["passed"]:
            failures.extend(row.get("failures") or [
                f"{row['name']} failed: {row.get('evidence', '')}"])
    return {"passed": not failures, "checks": checks, "failures": failures}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-root", default="/opt/cis-control")
    parser.add_argument("--unit-path", default="/etc/systemd/system/cis-pipeline.service")
    parser.add_argument("--sudoers-path", default="/etc/sudoers.d/cis-pipeline")
    parser.add_argument("--launcher-path",
                        help="sealed launcher the unit must run; "
                             "defaults to <control-root>/bin/cis-container")
    parser.add_argument("--skip-visudo", action="store_true")
    args = parser.parse_args(argv)
    result = evaluate(
        control_root=args.control_root, unit_path=args.unit_path,
        sudoers_path=args.sudoers_path, launcher_path=args.launcher_path,
        run_visudo=not args.skip_visudo)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
