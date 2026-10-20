#!/usr/bin/env python3
"""Install the sealed CIS host-launch package without starting the pipeline.

This program is intended to be promoted into /opt/cis-control and invoked once
with native sudo.  It deliberately does not stop or start the live container;
that handoff remains a separately verified operation after installation.

Three properties make it safe to run as root on a host that is already serving:

* It executes only sealed /opt/cis-control programs, and only after proving each
  is a root-owned, exact-mode, regular, non-symlinked file.
* It is transactional.  The pre-existing unit, sudoers policy and enabled state
  are snapshotted first; any failure restores all three and daemon-reloads, so a
  half-installed launch package is never left behind.
* It proves the end state by querying systemd (``is-enabled``, ``is-active``)
  rather than asserting it.  The reported evidence is what systemd said.
"""

import hashlib
import json
import os
import stat
import subprocess
import sys


CONTROL_ROOT = "/opt/cis-control"
UNIT_NAME = "cis-pipeline.service"
UNIT_PATH = f"/etc/systemd/system/{UNIT_NAME}"
SUDOERS_PATH = "/etc/sudoers.d/cis-pipeline"
# Leading dot: sudo ignores /etc/sudoers.d entries containing a dot, so the
# staged copy cannot take effect before it has been syntax-checked and renamed.
SUDOERS_TEMP_NAME = ".cis-pipeline.installing"

VISUDO = "/usr/sbin/visudo"
INSTALL = "/usr/bin/install"
SYSTEMCTL = "/usr/bin/systemctl"

# Modes declared for these artifacts by config/control-plane-release.json. The
# installer refuses to act on bytes that do not already carry them.
SEALED_UNIT_MODE = 0o444
SEALED_SUDOERS_MODE = 0o440
SEALED_PROGRAM_MODE = 0o555
INSTALLED_UNIT_MODE = 0o444
INSTALLED_SUDOERS_MODE = 0o440


class HostLaunchInstallError(RuntimeError):
    """Installation refusal or failure, carrying rollback and command evidence."""

    def __init__(self, message, *, rollback=None, commands=None):
        super().__init__(message)
        self.rollback = list(rollback or [])
        self.commands = list(commands or [])


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_sealed(path, expected_mode, expected_uid=0, expected_gid=0,
                     control_root=None):
    """Return evidence for a sealed artifact, or refuse.

    Called before anything is executed or copied: a symlinked, non-regular,
    wrong-owner or wrong-mode artifact is not evidence of a reviewed promotion,
    so there is nothing here worth running with root authority.
    """
    if os.path.islink(path):
        raise HostLaunchInstallError(f"sealed source is a symlink: {path}")
    if not os.path.isfile(path):
        raise HostLaunchInstallError(f"sealed source is absent or non-regular: {path}")
    info = os.stat(path)
    actual_mode = stat.S_IMODE(info.st_mode)
    if (info.st_uid, info.st_gid) != (expected_uid, expected_gid):
        raise HostLaunchInstallError(
            f"sealed source is {info.st_uid}:{info.st_gid}, expected "
            f"{expected_uid}:{expected_gid}: {path}")
    if actual_mode != expected_mode:
        raise HostLaunchInstallError(
            f"sealed source mode is {actual_mode:04o}, expected {expected_mode:04o}: {path}")
    if control_root is not None:
        root = os.path.realpath(control_root)
        current = os.path.realpath(os.path.dirname(path))
        if current != root and not current.startswith(root + os.sep):
            raise HostLaunchInstallError(
                f"sealed source escapes the control root: {path}")
        while True:
            parent_info = os.stat(current)
            parent_mode = stat.S_IMODE(parent_info.st_mode)
            if (parent_info.st_uid, parent_info.st_gid) != (expected_uid, expected_gid):
                raise HostLaunchInstallError(
                    f"sealed ownership chain is {parent_info.st_uid}:{parent_info.st_gid}, "
                    f"expected {expected_uid}:{expected_gid}: {current}")
            if parent_mode & (stat.S_IWGRP | stat.S_IWOTH):
                raise HostLaunchInstallError(
                    f"sealed ownership chain is group/world writable: {current}")
            if current == root:
                break
            current = os.path.dirname(current)
    return {
        "path": path,
        "sha256": _sha256(path),
        "mode": format(actual_mode, "04o"),
        "owner": f"{info.st_uid}:{info.st_gid}",
    }


def _validate_destination(path, label):
    """Refuse a destination that could redirect a root write somewhere else."""
    parent = os.path.dirname(path)
    if os.path.islink(parent) or not os.path.isdir(parent):
        raise HostLaunchInstallError(
            f"{label} parent directory is absent, non-directory, or symlinked: {parent}")
    if os.path.islink(path):
        raise HostLaunchInstallError(f"{label} destination is a symlink: {path}")
    if os.path.lexists(path) and not os.path.isfile(path):
        raise HostLaunchInstallError(
            f"{label} destination exists and is not a regular file: {path}")


class _Snapshot:
    """Pre-installation state of one destination file, restorable on failure."""

    def __init__(self, path):
        self.path = path
        self.existed = os.path.lexists(path)
        self.payload = None
        self.mode = None
        self.uid = None
        self.gid = None
        if self.existed and not os.path.islink(path) and os.path.isfile(path):
            info = os.stat(path)
            self.mode = stat.S_IMODE(info.st_mode)
            self.uid, self.gid = info.st_uid, info.st_gid
            with open(path, "rb") as handle:
                self.payload = handle.read()

    def describe(self):
        if not self.existed:
            return {"path": self.path, "existed": False}
        return {"path": self.path, "existed": True,
                "mode": format(self.mode, "04o") if self.mode is not None else None,
                "owner": f"{self.uid}:{self.gid}" if self.uid is not None else None,
                "sha256": hashlib.sha256(self.payload).hexdigest()
                          if self.payload is not None else None}

    def restore(self):
        if not self.existed:
            if os.path.lexists(self.path):
                os.unlink(self.path)
                return f"removed {self.path}; it did not exist before installation"
            return f"left {self.path} absent, as it was before installation"
        if self.payload is None:
            return f"left {self.path} untouched; it was not a regular file before installation"
        staging = f"{self.path}.cis-rollback"
        with open(staging, "wb") as handle:
            handle.write(self.payload)
        os.chmod(staging, self.mode)
        try:
            os.chown(staging, self.uid, self.gid)
        except OSError:
            pass
        os.replace(staging, self.path)
        return f"restored {self.path} from its pre-installation snapshot ({self.mode:04o})"


def _subprocess_runner(argv):
    return subprocess.run(argv, capture_output=True, text=True, timeout=180)


class _Commands:
    """Thin command log around an injectable runner, so the sequence is evidence."""

    def __init__(self, runner=None):
        self._runner = runner or _subprocess_runner
        self.log = []

    def run(self, argv, *, allow_failure=False):
        argv = [str(item) for item in argv]
        result = self._runner(argv)
        code = int(getattr(result, "returncode", 1))
        stdout = (getattr(result, "stdout", "") or "").strip()
        stderr = (getattr(result, "stderr", "") or "").strip()
        self.log.append({"argv": argv, "returncode": code})
        if code != 0 and not allow_failure:
            raise HostLaunchInstallError(
                f"command failed (exit {code}): {' '.join(argv)}: {stderr or stdout}")
        return code, stdout, stderr

    def state(self, argv):
        """Query systemd for a one-word state, reporting whatever it actually said."""
        _, stdout, stderr = self.run(argv, allow_failure=True)
        text = stdout or stderr or "unknown"
        return text.splitlines()[0].strip() or "unknown"


def _rollback(commands, snapshots, sudoers_temp, prior_enabled, unit_name):
    """Undo everything this run changed. Never raises; records what it did."""
    actions = []
    if os.path.lexists(sudoers_temp):
        try:
            os.unlink(sudoers_temp)
            actions.append(f"removed staging file {sudoers_temp}")
        except OSError as exc:
            actions.append(f"could not remove staging file {sudoers_temp}: {exc}")
    # Remove any enablement symlink while the newly installed unit still
    # exists, then restore the prior files.  Disabling after restoring an
    # absent prior unit can miss a dangling wants/ symlink.
    code, _, _ = commands.run([SYSTEMCTL, "disable", unit_name], allow_failure=True)
    actions.append(f"disabled newly installed {unit_name} before file restore (exit {code})")
    for snapshot in snapshots:
        try:
            actions.append(snapshot.restore())
        except OSError as exc:
            actions.append(f"could not restore {snapshot.path}: {exc}")
    code, _, _ = commands.run([SYSTEMCTL, "daemon-reload"], allow_failure=True)
    actions.append(f"reloaded systemd after file restore (exit {code})")
    if prior_enabled == "enabled":
        code, _, _ = commands.run([SYSTEMCTL, "enable", unit_name], allow_failure=True)
        actions.append(f"re-enabled {unit_name} to match prior state (exit {code})")
    observed = commands.state([SYSTEMCTL, "is-enabled", unit_name])
    actions.append(
        f"observed rollback enabled state {observed!r}; prior state was "
        f"{prior_enabled!r}")
    if observed != prior_enabled:
        actions.append(
            f"ROLLBACK VERIFICATION FAILED: expected is-enabled={prior_enabled!r}, "
            f"observed {observed!r}")
    return actions


def install(*, control_root=CONTROL_ROOT, unit_path=UNIT_PATH,
            sudoers_path=SUDOERS_PATH, sudoers_temp=None, unit_name=UNIT_NAME,
            expected_uid=0, expected_gid=0, runner=None, geteuid=None):
    geteuid = geteuid or os.geteuid
    if geteuid() != 0:
        raise HostLaunchInstallError(
            "native root authority is required; run: "
            f"sudo {control_root}/bin/cis-host-launch-install")

    sealed_unit = os.path.join(control_root, "systemd", unit_name)
    sealed_sudoers = os.path.join(control_root, "policy", "cis-pipeline.sudoers")
    sealed_gate = os.path.join(control_root, "bin", "cis-host-launch-gate")
    sealed_launcher = os.path.join(control_root, "bin", "cis-container")
    if sudoers_temp is None:
        sudoers_temp = os.path.join(os.path.dirname(sudoers_path), SUDOERS_TEMP_NAME)

    # Validate every sealed artifact before executing or copying any of them.
    # The launcher is validated too: enabling a unit whose ExecStart is a
    # developer-writable or symlinked file would install a root-run bypass.
    sealed = {
        "systemd_unit": _validate_sealed(
            sealed_unit, SEALED_UNIT_MODE, expected_uid, expected_gid, control_root),
        "sudoers_policy": _validate_sealed(
            sealed_sudoers, SEALED_SUDOERS_MODE, expected_uid, expected_gid, control_root),
        "host_launch_gate": _validate_sealed(
            sealed_gate, SEALED_PROGRAM_MODE, expected_uid, expected_gid, control_root),
        "container_launcher": _validate_sealed(
            sealed_launcher, SEALED_PROGRAM_MODE, expected_uid, expected_gid, control_root),
    }

    _validate_destination(unit_path, "systemd unit")
    _validate_destination(sudoers_path, "sudoers policy")
    _validate_destination(sudoers_temp, "staged sudoers policy")

    commands = _Commands(runner)
    prior_enabled = commands.state([SYSTEMCTL, "is-enabled", unit_name])
    snapshots = [_Snapshot(sudoers_path), _Snapshot(unit_path)]
    prior = {"enabled_state": prior_enabled,
             "files": [snapshot.describe() for snapshot in snapshots]}

    try:
        commands.run([VISUDO, "-cf", sealed_sudoers])

        # Stage, syntax-check and only then atomically rename into place, so a
        # rejected policy never becomes the active one.
        commands.run([INSTALL, "-o", "root", "-g", "root", "-m",
                      format(INSTALLED_SUDOERS_MODE, "04o"),
                      sealed_sudoers, sudoers_temp])
        try:
            commands.run([VISUDO, "-cf", sudoers_temp])
            os.replace(sudoers_temp, sudoers_path)
        finally:
            if os.path.lexists(sudoers_temp):
                os.unlink(sudoers_temp)

        commands.run([INSTALL, "-o", "root", "-g", "root", "-m",
                      format(INSTALLED_UNIT_MODE, "04o"),
                      sealed_unit, unit_path])
        commands.run([SYSTEMCTL, "daemon-reload"])

        # Gate the installed bytes BEFORE granting the unit boot authority: an
        # enabled unit that fails its own gate is exactly the silent-gate
        # failure this package exists to prevent.
        gate_code, gate_stdout, gate_stderr = commands.run(
            [sealed_gate, "--control-root", control_root, "--unit-path", unit_path,
             "--sudoers-path", sudoers_path], allow_failure=True)
        try:
            gate_result = json.loads(gate_stdout)
        except ValueError:
            raise HostLaunchInstallError(
                "sealed host-launch gate produced unreadable output: "
                f"{(gate_stderr or gate_stdout)[:400]}")
        if gate_code != 0 or not gate_result.get("passed"):
            raise HostLaunchInstallError(
                "installed host-launch package did not pass its sealed gate: "
                + json.dumps(gate_result.get("failures") or gate_result))

        commands.run([SYSTEMCTL, "enable", unit_name])

        # Prove the end state instead of declaring it.
        enabled_state = commands.state([SYSTEMCTL, "is-enabled", unit_name])
        if enabled_state != "enabled":
            raise HostLaunchInstallError(
                f"systemctl reports is-enabled={enabled_state!r} after enable")
        active_state = commands.state([SYSTEMCTL, "is-active", unit_name])
        if active_state != "inactive":
            raise HostLaunchInstallError(
                f"systemctl reports is-active={active_state!r}; installation must "
                "leave the service enabled and not running")
    except (HostLaunchInstallError, OSError) as exc:
        actions = _rollback(commands, snapshots, sudoers_temp, prior_enabled, unit_name)
        raise HostLaunchInstallError(
            str(exc), rollback=actions, commands=commands.log) from exc

    return {
        "passed": True,
        "enabled": enabled_state == "enabled",
        "started": active_state == "active",
        "systemctl_is_enabled": enabled_state,
        "systemctl_is_active": active_state,
        "prior": prior,
        "sealed": sealed,
        "installed": {
            unit_path: sealed["systemd_unit"]["sha256"],
            sudoers_path: sealed["sudoers_policy"]["sha256"],
        },
        "gate": gate_result,
        "commands": commands.log,
        "next": "Return to Codex for the separately verified live-service handoff.",
    }


def main():
    try:
        result = install()
    except HostLaunchInstallError as exc:
        payload = {"passed": False, "error": str(exc)}
        if exc.rollback:
            payload["rollback"] = exc.rollback
        if exc.commands:
            payload["commands"] = exc.commands
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, indent=2),
              file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
