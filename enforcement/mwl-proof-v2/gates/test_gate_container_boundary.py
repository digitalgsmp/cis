#!/usr/bin/env python3
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.gates.gate_container_boundary import evaluate


def _base():
    return [{
        "Config": {"User": "worker"},
        "HostConfig": {
            "Privileged": False, "ReadonlyRootfs": True,
            "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges:true"],
        },
        "Mounts": [
            {"Source": "/mnt/projects/cis", "Destination": "/workspace/cis", "RW": False},
            {"Source": "/mnt/projects/cis/secrets.env", "Destination": "/workspace/secrets.env", "RW": False},
            {"Source": "/opt/cis-control", "Destination": "/control", "RW": False},
            {"Source": "/opt/cis-control/runtime/entrypoint.sh", "Destination": "/opt/cis-control/entrypoint.sh", "RW": False},
            {"Source": "/opt/cis-control/runtime/profiles", "Destination": "/etc/hermes/profiles", "RW": False},
            {"Source": "/opt/cis-control/runtime/managed-config.yaml", "Destination": "/etc/hermes/config.yaml", "RW": False},
            {"Source": "/opt/cis-control/runtime/gates", "Destination": "/opt/cis-gates", "RW": False},
            {"Source": "/opt/cis-control/gate", "Destination": "/opt/cis-control/gate", "RW": False},
            {"Source": "/mnt/cache/cis-workspaces/run-1", "Destination": "/workspace/output", "RW": True},
        ] + [
            {"Source": "/opt/cis-control/runtime/plugin",
             "Destination": f"/home/worker/.hermes-{role}/plugins/mwl-proof",
             "RW": False}
            for role in ("brain", "draft", "review1", "review2", "menter", "verify",
                         "advisor", "evaluator")
        ],
    }]


def test_retirement_ready_fixture_passes():
    result = evaluate(_base())
    assert result["passed"] is True, result


def test_live_shape_fails_broad_writes_and_missing_hardening():
    value = _base()
    host = value[0]["HostConfig"]
    host["ReadonlyRootfs"] = False
    host["CapDrop"] = None
    host["SecurityOpt"] = None
    value[0]["Mounts"].append(
        {"Source": "/mnt/projects/swa", "Destination": "/workspace/swa", "RW": True})
    value[0]["Mounts"] = [m for m in value[0]["Mounts"]
                           if not str(m["Source"]).startswith("/opt/cis-control")]
    result = evaluate(value)
    assert result["passed"] is False
    assert "read_only_rootfs" in result["failed_checks"]
    assert "all_capabilities_dropped" in result["failed_checks"]
    assert "no_new_privileges" in result["failed_checks"]
    assert "no_broad_project_write_mounts" in result["failed_checks"]
    assert "root_control_plane_mounted_read_only" in result["failed_checks"]
    assert "all_enforcement_origins_are_sealed" in result["failed_checks"]


def test_docker_socket_always_fails():
    value = _base()
    value[0]["Mounts"].append(
        {"Source": "/var/run/docker.sock", "Destination": "/var/run/docker.sock", "RW": True})
    result = evaluate(value)
    assert result["passed"] is False
    assert "no_docker_socket" in result["failed_checks"]


def test_developer_repo_override_origin_fails():
    value = _base()
    for mount in value[0]["Mounts"]:
        if mount["Destination"] == "/opt/cis-control/gate":
            mount["Source"] = "/mnt/projects/cis/.gate-control"
    result = evaluate(value)
    assert result["passed"] is False
    assert "all_enforcement_origins_are_sealed" in result["failed_checks"]


def run():
    tests = [test_retirement_ready_fixture_passes,
             test_live_shape_fails_broad_writes_and_missing_hardening,
             test_docker_socket_always_fails,
             test_developer_repo_override_origin_fails]
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
