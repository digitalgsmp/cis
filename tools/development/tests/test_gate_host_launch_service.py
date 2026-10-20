#!/usr/bin/env python3
"""Tests for the read-only host-launch gate.

All paths are injected into a temporary directory; the gate is never pointed at
the real /etc or /opt/cis-control, and visudo is not invoked.
"""
import os
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.development.gate_host_launch_service import evaluate


def _unit_text(launcher):
    return ("[Unit]\n"
            f"AssertPathExists={launcher}\n"
            "[Service]\n"
            f"ExecStart={launcher} -d\n"
            f"ExecStop={launcher} stop\n")


def _fixture(tmp, *, unit_text=None, launcher_mode=0o555, launcher=True):
    control = os.path.join(tmp, "control")
    unit = os.path.join(tmp, "etc", "systemd", "cis-pipeline.service")
    sudoers = os.path.join(tmp, "etc", "sudoers", "cis-pipeline")
    sealed_unit = os.path.join(control, "systemd", "cis-pipeline.service")
    sealed_sudoers = os.path.join(control, "policy", "cis-pipeline.sudoers")
    sealed_launcher = os.path.join(control, "bin", "cis-container")
    for path in (unit, sudoers, sealed_unit, sealed_sudoers, sealed_launcher):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    text = unit_text if unit_text is not None else _unit_text(sealed_launcher)
    for path in (unit, sealed_unit):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    for path in (sudoers, sealed_sudoers):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("eric ALL=(root) NOPASSWD: /usr/bin/systemctl restart cis-pipeline.service\n")
    if launcher:
        with open(sealed_launcher, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/bash\nexit 0\n")
        os.chmod(sealed_launcher, launcher_mode)
    os.chmod(unit, 0o444)
    os.chmod(sudoers, 0o440)
    return control, unit, sudoers


def _evaluate(control, unit, sudoers):
    return evaluate(
        control_root=control, unit_path=unit, sudoers_path=sudoers,
        expected_uid=os.getuid(), expected_gid=os.getgid(), run_visudo=False)


def test_matching_install_passes():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit, sudoers = _fixture(tmp)
        assert _evaluate(control, unit, sudoers)["passed"] is True


def test_modified_unit_fails():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit, sudoers = _fixture(tmp)
        os.chmod(unit, 0o644)
        with open(unit, "a", encoding="utf-8") as handle:
            handle.write("ExecStartPost=/bin/sh\n")
        os.chmod(unit, 0o444)
        result = _evaluate(control, unit, sudoers)
        assert result["passed"] is False
        assert any("bytes differ" in reason for reason in result["failures"])


def test_writable_sudoers_policy_fails():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit, sudoers = _fixture(tmp)
        os.chmod(sudoers, 0o660)
        result = _evaluate(control, unit, sudoers)
        assert result["passed"] is False
        assert any("mode" in reason for reason in result["failures"])


def test_absent_sealed_launcher_fails():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit, sudoers = _fixture(tmp, launcher=False)
        result = _evaluate(control, unit, sudoers)
        assert result["passed"] is False
        assert any("sealed program absent" in reason for reason in result["failures"])


def test_writable_sealed_launcher_fails():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit, sudoers = _fixture(tmp, launcher_mode=0o755)
        result = _evaluate(control, unit, sudoers)
        assert result["passed"] is False
        assert any("container_launcher mode" in reason
                   for reason in result["failures"])


def test_condition_path_exists_fails():
    with tempfile.TemporaryDirectory() as tmp:
        launcher = os.path.join(tmp, "control", "bin", "cis-container")
        text = ("[Unit]\n"
                f"ConditionPathExists={launcher}\n"
                "[Service]\n"
                f"ExecStart={launcher} -d\n")
        control, unit, sudoers = _fixture(tmp, unit_text=text)
        result = _evaluate(control, unit, sudoers)
        assert result["passed"] is False
        assert any("ConditionPathExists" in reason for reason in result["failures"])
        assert any("does not assert the sealed launcher" in reason
                   for reason in result["failures"])


def test_unit_running_another_program_fails():
    with tempfile.TemporaryDirectory() as tmp:
        launcher = os.path.join(tmp, "control", "bin", "cis-container")
        text = ("[Unit]\n"
                f"AssertPathExists={launcher}\n"
                "[Service]\n"
                f"ExecStart={launcher} -d\n"
                "ExecStartPost=/bin/sh -c 'curl http://evil'\n")
        control, unit, sudoers = _fixture(tmp, unit_text=text)
        result = _evaluate(control, unit, sudoers)
        assert result["passed"] is False
        assert any("program other than the sealed launcher" in reason
                   for reason in result["failures"])


def test_exec_condition_and_stop_post_are_covered():
    for directive in ("ExecCondition", "ExecStopPost"):
        with tempfile.TemporaryDirectory() as tmp:
            launcher = os.path.join(tmp, "control", "bin", "cis-container")
            text = (_unit_text(launcher)
                    + f"{directive}=/bin/sh -c 'exit 0'\n")
            control, unit, sudoers = _fixture(tmp, unit_text=text)
            result = _evaluate(control, unit, sudoers)
            assert result["passed"] is False
            assert any("program other than the sealed launcher" in reason
                       for reason in result["failures"])


def test_restart_policy_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        launcher = os.path.join(tmp, "control", "bin", "cis-container")
        text = _unit_text(launcher) + "Restart=always\n"
        control, unit, sudoers = _fixture(tmp, unit_text=text)
        result = _evaluate(control, unit, sudoers)
        assert result["passed"] is False
        assert any("restart policy" in reason for reason in result["failures"])


def test_symlinked_installed_unit_fails():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit, sudoers = _fixture(tmp)
        decoy = os.path.join(tmp, "decoy.service")
        os.replace(unit, decoy)
        os.symlink(decoy, unit)
        result = _evaluate(control, unit, sudoers)
        assert result["passed"] is False
        assert any("symlinked" in reason for reason in result["failures"])


def run():
    tests = [test_matching_install_passes, test_modified_unit_fails,
             test_writable_sudoers_policy_fails, test_absent_sealed_launcher_fails,
             test_writable_sealed_launcher_fails, test_condition_path_exists_fails,
             test_unit_running_another_program_fails,
             test_exec_condition_and_stop_post_are_covered,
             test_restart_policy_is_rejected,
             test_symlinked_installed_unit_fails]
    rows = []
    for test in tests:
        try:
            test()
            rows.append(f"{test.__name__}: PASS")
        except Exception as exc:
            rows.append(f"{test.__name__}: FAIL — {exc}")
    print("\n".join(rows))
    failed = [row for row in rows if ": FAIL" in row]
    print(f"\n{len(rows)-len(failed)}/{len(rows)} passed.")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
