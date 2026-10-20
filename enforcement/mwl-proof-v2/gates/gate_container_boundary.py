#!/usr/bin/env python3
"""Fail-closed gate for the queue 4.37 retirement-ready worker boundary.

Input is ordinary ``docker inspect`` JSON.  The gate does not inspect model
behavior; it checks the kernel/container boundary that must exist before a
model is allowed to work.  Unknown or missing fields fail rather than pass.
"""
import argparse
import json
import subprocess
import sys


def evaluate(inspect_value):
    checks = []

    def check(name, passed, evidence):
        checks.append({"name": name, "passed": bool(passed), "evidence": evidence})

    if not isinstance(inspect_value, list) or len(inspect_value) != 1:
        return {"passed": False, "checks": [],
                "errors": ["inspect input must contain exactly one container"]}
    container = inspect_value[0]
    host = container.get("HostConfig") or {}
    config = container.get("Config") or {}
    mounts = container.get("Mounts")
    if not isinstance(mounts, list):
        return {"passed": False, "checks": [],
                "errors": ["inspect input has no Mounts list"]}

    user = config.get("User")
    check("non_root_runtime_user", bool(user) and str(user) not in {"0", "root"}, user)
    check("not_privileged", host.get("Privileged") is False, host.get("Privileged"))
    check("read_only_rootfs", host.get("ReadonlyRootfs") is True,
          host.get("ReadonlyRootfs"))
    cap_drop = host.get("CapDrop") or []
    check("all_capabilities_dropped", "ALL" in cap_drop, cap_drop)
    security = [str(v).lower() for v in (host.get("SecurityOpt") or [])]
    check("no_new_privileges", any("no-new-privileges" in v for v in security), security)

    destinations = {m.get("Destination"): m for m in mounts}
    repo = destinations.get("/workspace/cis")
    check("cis_source_read_only", bool(repo) and repo.get("RW") is False, repo)
    secret = destinations.get("/workspace/secrets.env")
    check("secret_mount_read_only", bool(secret) and secret.get("RW") is False, secret)

    docker_socket = [m for m in mounts if m.get("Source") == "/var/run/docker.sock"
                     or m.get("Destination") == "/var/run/docker.sock"]
    check("no_docker_socket", not docker_socket, docker_socket)

    control_mounts = [m for m in mounts
                      if str(m.get("Source", "")).startswith("/opt/cis-control")]
    check("root_control_plane_mounted_read_only",
          bool(control_mounts) and all(m.get("RW") is False for m in control_mounts),
          control_mounts)

    sealed_origins = {
        "/control": "/opt/cis-control",
        "/opt/cis-control/entrypoint.sh": "/opt/cis-control/runtime/entrypoint.sh",
        "/etc/hermes/profiles": "/opt/cis-control/runtime/profiles",
        "/etc/hermes/config.yaml": "/opt/cis-control/runtime/managed-config.yaml",
        "/opt/cis-gates": "/opt/cis-control/runtime/gates",
        "/opt/cis-control/gate": "/opt/cis-control/gate",
    }
    sealed_origin_evidence = []
    sealed_origins_ok = True
    for destination, source in sealed_origins.items():
        mount = destinations.get(destination)
        passed = bool(mount) and mount.get("Source") == source and mount.get("RW") is False
        sealed_origins_ok = sealed_origins_ok and passed
        sealed_origin_evidence.append({"destination": destination, "source": source,
                                       "mount": mount, "passed": passed})
    plugin_destinations = {
        f"/home/worker/.hermes-{role}/plugins/mwl-proof"
        for role in ("brain", "draft", "review1", "review2", "menter", "verify",
                     "advisor", "evaluator")
    }
    for destination in sorted(plugin_destinations):
        mount = destinations.get(destination)
        passed = (bool(mount)
                  and mount.get("Source") == "/opt/cis-control/runtime/plugin"
                  and mount.get("RW") is False)
        sealed_origins_ok = sealed_origins_ok and passed
        sealed_origin_evidence.append(
            {"destination": destination,
             "source": "/opt/cis-control/runtime/plugin",
             "mount": mount, "passed": passed})
    check("all_enforcement_origins_are_sealed", sealed_origins_ok,
          sealed_origin_evidence)

    repo_enforcement = [m for m in mounts
                        if str(m.get("Source", "")).startswith("/mnt/projects/cis")
                        and ("plugin" in str(m.get("Destination", ""))
                             or str(m.get("Destination", "")).startswith("/opt/cis-control"))]
    check("enforcement_not_sourced_from_developer_repo", not repo_enforcement,
          repo_enforcement)

    writable_project_mounts = [
        m for m in mounts
        if m.get("RW") is True and str(m.get("Source", "")).startswith("/mnt/projects/")
        and m.get("Destination") not in {"/workspace/cis/data", "/workspace/cis/state"}
    ]
    check("no_broad_project_write_mounts", not writable_project_mounts,
          writable_project_mounts)

    output_mounts = [m for m in mounts if m.get("Destination") == "/workspace/output"]
    check("declared_output_workspace_present",
          len(output_mounts) == 1 and output_mounts[0].get("RW") is True,
          output_mounts)

    failures = [row for row in checks if not row["passed"]]
    return {"passed": not failures, "checks": checks,
            "failed_checks": [row["name"] for row in failures], "errors": []}


def main(argv=None):
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--inspect-file")
    source.add_argument("--container")
    args = parser.parse_args(argv)
    try:
        if args.inspect_file:
            with open(args.inspect_file, encoding="utf-8") as handle:
                value = json.load(handle)
        else:
            run = subprocess.run(["docker", "inspect", args.container],
                                 capture_output=True, text=True, timeout=30)
            if run.returncode != 0:
                raise RuntimeError(run.stderr.strip() or "docker inspect failed")
            value = json.loads(run.stdout)
        result = evaluate(value)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        result = {"passed": False, "checks": [], "failed_checks": [],
                  "errors": [str(exc)]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
