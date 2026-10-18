#!/usr/bin/env python3
"""Tests for the sealed host-launch installer.

Every test runs against injected temporary paths and a fake command runner, so
nothing here touches the real /etc, the real /opt/cis-control, or systemd. The
fake host simulates `install`, `visudo`, `systemctl` and the sealed gate, which
lets the tests exercise the actual install sequence — including its ordering and
its rollback — rather than re-asserting the implementation's own claims.
"""
import json
import os
import stat
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.development import install_host_launch_service as installer
from tools.development.install_host_launch_service import (
    HostLaunchInstallError, _sha256, _validate_sealed, install)

UNIT_NAME = "cis-pipeline.service"
PRIOR_UNIT_BYTES = b"[Service]\nExecStart=/bin/true\n"
PRIOR_SUDOERS_BYTES = b"eric ALL=(root) NOPASSWD: /usr/bin/systemctl status old.service\n"


class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeHost:
    """Records every command and simulates only what the installer depends on."""

    def __init__(self, *, gate_passed=True, prior_enabled="disabled",
                 active_state="inactive", enable_works=True):
        self.log = []
        self.gate_passed = gate_passed
        self.enabled = prior_enabled
        self.active_state = active_state
        self.enable_works = enable_works
        self.started = False

    def __call__(self, argv):
        self.log.append(list(argv))
        name = os.path.basename(argv[0])
        if name == "visudo":
            return _Result(0)
        if name == "install":
            return self._install(argv)
        if name == "systemctl":
            return self._systemctl(argv)
        if name == "cis-host-launch-gate":
            payload = {"passed": self.gate_passed, "checks": [],
                       "failures": [] if self.gate_passed else ["installed bytes differ"]}
            return _Result(0 if self.gate_passed else 1, json.dumps(payload))
        raise AssertionError(f"installer ran an unexpected command: {argv}")

    def _install(self, argv):
        mode = int(argv[argv.index("-m") + 1], 8)
        source, destination = argv[-2], argv[-1]
        with open(source, "rb") as handle:
            payload = handle.read()
        # Coreutils install replaces an unwritable destination; the tests run
        # unprivileged, so the read-only prior file is unlinked the same way.
        if os.path.lexists(destination):
            os.unlink(destination)
        with open(destination, "wb") as handle:
            handle.write(payload)
        os.chmod(destination, mode)
        return _Result(0)

    def _systemctl(self, argv):
        verb = argv[1]
        if verb == "daemon-reload":
            return _Result(0)
        if verb == "enable":
            if self.enable_works:
                self.enabled = "enabled"
            return _Result(0)
        if verb == "disable":
            self.enabled = "disabled"
            return _Result(0)
        if verb == "is-enabled":
            return _Result(0 if self.enabled == "enabled" else 1, f"{self.enabled}\n")
        if verb == "is-active":
            return _Result(0 if self.active_state == "active" else 3,
                           f"{self.active_state}\n")
        if verb in ("start", "restart"):
            # A start here would be the defect requirement 5 exists to catch.
            self.started = True
            raise AssertionError("the installer must never start the service")
        raise AssertionError(f"unexpected systemctl verb: {verb}")

    def verbs(self):
        return [os.path.basename(argv[0]) + " " + " ".join(argv[1:2]) for argv in self.log]


def _sealed_tree(tmp, *, launcher_mode=0o555, gate_mode=0o555):
    """Build a sealed /opt/cis-control stand-in plus empty /etc destinations."""
    control = os.path.join(tmp, "control")
    for folder in ("systemd", "policy", "bin"):
        path = os.path.join(control, folder)
        os.makedirs(path, exist_ok=True)
        os.chmod(path, 0o755)
    os.chmod(control, 0o755)
    unit_dest = os.path.join(tmp, "etc", "systemd", "system", UNIT_NAME)
    sudoers_dest = os.path.join(tmp, "etc", "sudoers.d", "cis-pipeline")
    for path in (unit_dest, sudoers_dest):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    launcher = os.path.join(control, "bin", "cis-container")
    sealed_unit = os.path.join(control, "systemd", UNIT_NAME)
    sealed_sudoers = os.path.join(control, "policy", "cis-pipeline.sudoers")
    sealed_gate = os.path.join(control, "bin", "cis-host-launch-gate")

    with open(sealed_unit, "w", encoding="utf-8") as handle:
        handle.write("[Unit]\n"
                     f"AssertPathExists={launcher}\n"
                     "[Service]\n"
                     f"ExecStart={launcher} -d\n")
    with open(sealed_sudoers, "w", encoding="utf-8") as handle:
        handle.write("eric ALL=(root) NOPASSWD: /usr/bin/systemctl "
                     "restart cis-pipeline.service\n")
    for path in (launcher, sealed_gate):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nexit 0\n")
    os.chmod(sealed_unit, 0o444)
    os.chmod(sealed_sudoers, 0o440)
    os.chmod(launcher, launcher_mode)
    os.chmod(sealed_gate, gate_mode)
    return control, unit_dest, sudoers_dest


def _install(control, unit_dest, sudoers_dest, host, **overrides):
    kwargs = {
        "control_root": control,
        "unit_path": unit_dest,
        "sudoers_path": sudoers_dest,
        "unit_name": UNIT_NAME,
        "expected_uid": os.getuid(),
        "expected_gid": os.getgid(),
        "runner": host,
        "geteuid": lambda: 0,
    }
    kwargs.update(overrides)
    return install(**kwargs)


def _seed_prior_install(unit_dest, sudoers_dest):
    for path, payload, mode in ((unit_dest, PRIOR_UNIT_BYTES, 0o444),
                                (sudoers_dest, PRIOR_SUDOERS_BYTES, 0o440)):
        with open(path, "wb") as handle:
            handle.write(payload)
        os.chmod(path, mode)


# --- sealed-source validation -------------------------------------------------

def test_hash_is_stable():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sealed")
        with open(path, "wb") as handle:
            handle.write(b"cis\n")
        assert _sha256(path) == _sha256(path)


def test_matching_sealed_file_passes():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sealed")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("sealed\n")
        os.chmod(path, 0o444)
        evidence = _validate_sealed(
            path, 0o444, expected_uid=os.getuid(), expected_gid=os.getgid())
        assert len(evidence["sha256"]) == 64
        assert evidence["mode"] == "0444"


def test_wrong_mode_fails():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sealed")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("sealed\n")
        os.chmod(path, 0o644)
        try:
            _validate_sealed(
                path, 0o444, expected_uid=os.getuid(), expected_gid=os.getgid())
        except HostLaunchInstallError as exc:
            assert "mode" in str(exc)
        else:
            raise AssertionError("writable sealed file was accepted")


def test_symlink_fails():
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "target")
        link = os.path.join(tmp, "sealed")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("sealed\n")
        os.chmod(target, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        os.symlink(target, link)
        try:
            _validate_sealed(
                link, 0o444, expected_uid=os.getuid(), expected_gid=os.getgid())
        except HostLaunchInstallError as exc:
            assert "symlink" in str(exc)
        else:
            raise AssertionError("symlinked sealed file was accepted")


# --- install sequence ---------------------------------------------------------

def test_non_root_is_refused_before_anything_runs():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        host = FakeHost()
        try:
            _install(control, unit_dest, sudoers_dest, host, geteuid=lambda: 1000)
        except HostLaunchInstallError as exc:
            assert "root authority" in str(exc)
        else:
            raise AssertionError("installer ran without root authority")
        assert host.log == []
        assert not os.path.exists(unit_dest)


def test_successful_install_is_ordered_and_gated_before_enable():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        host = FakeHost()
        result = _install(control, unit_dest, sudoers_dest, host)

        assert result["passed"] is True
        assert host.verbs() == [
            "systemctl is-enabled",
            "visudo -cf",
            "install -o",
            "visudo -cf",
            "install -o",
            "systemctl daemon-reload",
            "cis-host-launch-gate --control-root",
            "systemctl enable",
            "systemctl is-enabled",
            "systemctl is-active",
        ]
        # The gate must be proven before the unit gains boot authority.
        gate_index = next(i for i, argv in enumerate(host.log)
                          if argv[0].endswith("cis-host-launch-gate"))
        enable_index = next(i for i, argv in enumerate(host.log)
                            if argv[:2] == [installer.SYSTEMCTL, "enable"])
        assert gate_index < enable_index
        # Reported state is the queried string, not a literal.
        assert result["systemctl_is_enabled"] == "enabled"
        assert result["systemctl_is_active"] == "inactive"
        assert result["enabled"] is True
        assert result["started"] is False
        assert result["prior"]["enabled_state"] == "disabled"
        with open(unit_dest, "rb") as handle:
            assert b"AssertPathExists" in handle.read()
        assert stat.S_IMODE(os.stat(unit_dest).st_mode) == 0o444
        assert stat.S_IMODE(os.stat(sudoers_dest).st_mode) == 0o440


def test_installer_never_starts_the_service():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        host = FakeHost()
        _install(control, unit_dest, sudoers_dest, host)
        assert host.started is False
        for argv in host.log:
            assert "start" not in argv, f"installer issued a start: {argv}"
            assert "restart" not in argv, f"installer issued a restart: {argv}"


def test_running_service_after_install_is_a_failure():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        _seed_prior_install(unit_dest, sudoers_dest)
        host = FakeHost(active_state="active")
        try:
            _install(control, unit_dest, sudoers_dest, host)
        except HostLaunchInstallError as exc:
            assert "is-active" in str(exc)
            assert exc.rollback
        else:
            raise AssertionError("installer accepted a running service")
        with open(unit_dest, "rb") as handle:
            assert handle.read() == PRIOR_UNIT_BYTES


def test_enable_that_does_not_take_effect_is_a_failure():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        host = FakeHost(enable_works=False)
        try:
            _install(control, unit_dest, sudoers_dest, host)
        except HostLaunchInstallError as exc:
            assert "is-enabled" in str(exc)
        else:
            raise AssertionError("installer trusted enable without proof")


# --- rollback -----------------------------------------------------------------

def test_gate_failure_rolls_back_files_and_enabled_state():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        _seed_prior_install(unit_dest, sudoers_dest)
        host = FakeHost(gate_passed=False, prior_enabled="disabled")
        try:
            _install(control, unit_dest, sudoers_dest, host)
        except HostLaunchInstallError as exc:
            assert "did not pass its sealed gate" in str(exc)
            assert any("restored" in action for action in exc.rollback)
            assert any("reloaded systemd after file restore" in action
                       for action in exc.rollback)
            assert any("observed rollback enabled state" in action
                       for action in exc.rollback)
        else:
            raise AssertionError("a failed gate was treated as a successful install")

        with open(unit_dest, "rb") as handle:
            assert handle.read() == PRIOR_UNIT_BYTES
        with open(sudoers_dest, "rb") as handle:
            assert handle.read() == PRIOR_SUDOERS_BYTES
        assert stat.S_IMODE(os.stat(unit_dest).st_mode) == 0o444
        assert stat.S_IMODE(os.stat(sudoers_dest).st_mode) == 0o440
        # Never enabled, and left not enabled.
        assert host.enabled == "disabled"
        assert [argv for argv in host.log
                if argv[:2] == [installer.SYSTEMCTL, "enable"]] == []
        assert host.log[-1][:2] == [installer.SYSTEMCTL, "is-enabled"]
        assert not os.path.exists(
            os.path.join(os.path.dirname(sudoers_dest),
                         installer.SUDOERS_TEMP_NAME))


def test_rollback_removes_files_that_did_not_exist_before():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        host = FakeHost(gate_passed=False)
        try:
            _install(control, unit_dest, sudoers_dest, host)
        except HostLaunchInstallError:
            pass
        else:
            raise AssertionError("a failed gate was treated as a successful install")
        assert not os.path.exists(unit_dest)
        assert not os.path.exists(sudoers_dest)


def test_rollback_restores_a_previously_enabled_unit():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        _seed_prior_install(unit_dest, sudoers_dest)
        host = FakeHost(gate_passed=False, prior_enabled="enabled")
        try:
            _install(control, unit_dest, sudoers_dest, host)
        except HostLaunchInstallError as exc:
            assert any("re-enabled" in action for action in exc.rollback)
        else:
            raise AssertionError("a failed gate was treated as a successful install")
        assert host.enabled == "enabled"


# --- refusals before the transaction opens ------------------------------------

def test_sealed_ownership_mismatch_refuses():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        host = FakeHost()
        try:
            _install(control, unit_dest, sudoers_dest, host,
                     expected_uid=os.getuid() + 1)
        except HostLaunchInstallError as exc:
            assert "expected" in str(exc)
        else:
            raise AssertionError("sealed artifact with the wrong owner was accepted")
        assert host.log == []


def test_sealed_launcher_mode_is_validated():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp, launcher_mode=0o755)
        host = FakeHost()
        try:
            _install(control, unit_dest, sudoers_dest, host)
        except HostLaunchInstallError as exc:
            assert "cis-container" in str(exc) and "mode" in str(exc)
        else:
            raise AssertionError("a writable sealed launcher was accepted")
        assert host.log == []


def test_symlinked_destination_refuses():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        decoy = os.path.join(tmp, "decoy.service")
        with open(decoy, "w", encoding="utf-8") as handle:
            handle.write("[Service]\n")
        os.symlink(decoy, unit_dest)
        host = FakeHost()
        try:
            _install(control, unit_dest, sudoers_dest, host)
        except HostLaunchInstallError as exc:
            assert "symlink" in str(exc)
        else:
            raise AssertionError("symlinked destination was accepted")
        assert host.log == []
        with open(decoy, encoding="utf-8") as handle:
            assert handle.read() == "[Service]\n"


def test_symlinked_destination_directory_refuses():
    with tempfile.TemporaryDirectory() as tmp:
        control, unit_dest, sudoers_dest = _sealed_tree(tmp)
        real = os.path.join(tmp, "real-sudoers.d")
        os.makedirs(real)
        linked = os.path.join(tmp, "linked-sudoers.d")
        os.symlink(real, linked)
        host = FakeHost()
        try:
            _install(control, unit_dest, os.path.join(linked, "cis-pipeline"), host)
        except HostLaunchInstallError as exc:
            assert "symlinked" in str(exc)
        else:
            raise AssertionError("symlinked destination directory was accepted")
        assert host.log == []


# --- config contracts ---------------------------------------------------------

def _read(relative):
    with open(os.path.join(REPO_ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def test_unit_asserts_the_launcher_and_does_not_condition_on_it():
    unit = _read("config/systemd/cis-pipeline.service")
    assert "AssertPathExists=/opt/cis-control/bin/cis-container" in unit
    assert "ConditionPathExists=" not in unit
    assert "Wants=network-online.target" in unit
    assert "After=docker.service" in unit
    for directive in ("ExecStart=", "ExecStop="):
        line = next(line for line in unit.splitlines() if line.startswith(directive))
        assert line.split("=", 1)[1].startswith("/opt/cis-control/bin/cis-container")


def test_manifest_declares_the_host_launch_package_at_installer_modes():
    manifest = json.loads(_read("config/control-plane-release.json"))
    by_destination = {artifact["destination"]: artifact
                      for artifact in manifest["artifacts"]}
    expected = {
        "systemd/cis-pipeline.service": installer.SEALED_UNIT_MODE,
        "policy/cis-pipeline.sudoers": installer.SEALED_SUDOERS_MODE,
        "bin/cis-container": installer.SEALED_PROGRAM_MODE,
        "bin/cis-host-launch-gate": installer.SEALED_PROGRAM_MODE,
        "bin/cis-host-launch-install": installer.SEALED_PROGRAM_MODE,
    }
    for destination, mode in expected.items():
        assert destination in by_destination, f"manifest omits {destination}"
        assert int(by_destination[destination]["mode"], 8) == mode, (
            f"{destination} mode disagrees with the installer's expectation")
    assert by_destination["bin/cis-container"]["source"] == (
        "enforcement/mwl-proof-v2/run_container.sh")


def test_sudoers_scope_is_limited_to_three_systemctl_verbs():
    policy = _read("config/sudoers/cis-pipeline")
    assert policy.count("Cmnd_Alias") == 1
    commands = [item.strip() for item in
                policy.split("CIS_PIPELINE_CONTROL =", 1)[1]
                .splitlines()[0].split(",")]
    assert commands == [
        "/usr/bin/systemctl start cis-pipeline.service",
        "/usr/bin/systemctl stop cis-pipeline.service",
        "/usr/bin/systemctl restart cis-pipeline.service",
    ]
    assert "ALL" not in commands
    assert "eric ALL=(root) NOPASSWD: CIS_PIPELINE_CONTROL" in policy


def test_launcher_never_sources_the_secrets_file():
    launcher = _read("enforcement/mwl-proof-v2/run_container.sh")
    assert "source \"$SECRETS_FILE\"" not in launcher
    assert ". \"$SECRETS_FILE\"" not in launcher
    assert "--env-file $ENV_FILE" in launcher
    assert "-v $SECRETS_FILE:/workspace/secrets.env:ro" in launcher
    assert '[ -L "$SECRETS_FILE" ]' in launcher
    assert "WORKSPACE_UID=1000" in launcher
    assert "--restart unless-stopped" not in launcher


def test_writable_control_parent_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        control = os.path.join(tmp, "control")
        bindir = os.path.join(control, "bin")
        os.makedirs(bindir)
        path = os.path.join(bindir, "sealed")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("sealed\n")
        os.chmod(path, 0o555)
        os.chmod(bindir, 0o775)
        try:
            installer._validate_sealed(
                path, 0o555, expected_uid=os.getuid(), expected_gid=os.getgid(),
                control_root=control)
        except installer.HostLaunchInstallError as exc:
            assert "group/world writable" in str(exc)
        else:
            raise AssertionError("writable sealed parent was accepted")


def run():
    tests = [
        test_hash_is_stable,
        test_matching_sealed_file_passes,
        test_wrong_mode_fails,
        test_symlink_fails,
        test_non_root_is_refused_before_anything_runs,
        test_successful_install_is_ordered_and_gated_before_enable,
        test_installer_never_starts_the_service,
        test_running_service_after_install_is_a_failure,
        test_enable_that_does_not_take_effect_is_a_failure,
        test_gate_failure_rolls_back_files_and_enabled_state,
        test_rollback_removes_files_that_did_not_exist_before,
        test_rollback_restores_a_previously_enabled_unit,
        test_sealed_ownership_mismatch_refuses,
        test_sealed_launcher_mode_is_validated,
        test_symlinked_destination_refuses,
        test_symlinked_destination_directory_refuses,
        test_unit_asserts_the_launcher_and_does_not_condition_on_it,
        test_manifest_declares_the_host_launch_package_at_installer_modes,
        test_sudoers_scope_is_limited_to_three_systemctl_verbs,
        test_launcher_never_sources_the_secrets_file,
        test_writable_control_parent_is_refused,
    ]
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
