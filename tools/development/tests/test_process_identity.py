#!/usr/bin/env python3
"""test_process_identity.py — CARD 04 behavioral tests for
process_identity.py (queue 4.32 BEFORE_STAGE_CLOSEOUT discovery,
revision 3: host killed the cis-pipeline container's main process,
mistaking it for a standalone dev Flask process on port 5000).

Deterministic fixture tests (fake /proc/cgroup content, fake docker/ss
subprocess output via injected functions) plus one live check against
this real host reproducing the exact incident shape: the cis-pipeline
container's actual port-5000 process, classified with no fixtures at all.

Run: python3 tools/development/tests/test_process_identity.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from tools.development import process_identity as pi

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


CGROUP_V2_DOCKER = (
    "0::/system.slice/docker-24cef29748cd7e5ba7e60479204a68ef52fb68a70ccb5f99e94e3d200d748dcf.scope\n"
)
CGROUP_V1_DOCKER = (
    "12:pids:/docker/24cef29748cd7e5ba7e60479204a68ef52fb68a70ccb5f99e94e3d200d748dcf\n"
    "11:cpu,cpuacct:/docker/24cef29748cd7e5ba7e60479204a68ef52fb68a70ccb5f99e94e3d200d748dcf\n"
)
CGROUP_HOST = "0::/user.slice/user-1000.slice/user@1000.service/app.slice/vte-spawn-abc.scope\n"

EXPECTED_ID = "24cef29748cd7e5ba7e60479204a68ef52fb68a70ccb5f99e94e3d200d748dcf"


def test_cgroup_v2_docker_scope_is_container():
    result = pi.classify_pid(9001, read_cgroup_fn=lambda pid: CGROUP_V2_DOCKER)
    check("cgroup v2 'docker-<id>.scope' classified as container",
          result["identity"] == "container" and result["container_id"] == EXPECTED_ID,
          result)


def test_cgroup_v1_docker_path_is_container():
    result = pi.classify_pid(9002, read_cgroup_fn=lambda pid: CGROUP_V1_DOCKER)
    check("cgroup v1 '/docker/<id>' classified as container",
          result["identity"] == "container" and result["container_id"] == EXPECTED_ID,
          result)


def test_plain_host_cgroup_is_host():
    result = pi.classify_pid(
        9003, read_cgroup_fn=lambda pid: CGROUP_HOST,
        dockerenv_check_fn=lambda pid: (False, None),
    )
    check("cgroup with no docker scope AND no dockerenv marker classified as host "
          "(positive evidence, not mere absence of the docker cgroup signal)",
          result["identity"] == "host" and result["container_id"] is None,
          result)


def test_namespace_virtualized_cgroup_with_dockerenv_marker_is_container():
    """Revision 7 correction: cis-pipeline runs with cgroup-namespace
    virtualization, so its own /proc/self/cgroup reads '0::/' -- verified
    live via `docker exec cis-pipeline cat /proc/self/cgroup` -- the same
    shape a genuine host process shows. Absence of a docker cgroup scope
    name must not, by itself, be classified as host. /.dockerenv (also
    verified live in cis-pipeline) is the independent tie-breaker."""
    result = pi.classify_pid(
        9010, read_cgroup_fn=lambda pid: "0::/\n",
        dockerenv_check_fn=lambda pid: (True, None),
    )
    check("cgroup-namespace-virtualized container ('0::/') with a /.dockerenv "
          "marker present is classified as container, not host",
          result["identity"] == "container", result)


def test_namespace_virtualized_cgroup_with_no_dockerenv_check_available_is_unknown():
    """The same inconclusive cgroup shape, but the secondary /.dockerenv
    check itself cannot be performed (e.g. permission denied crossing into
    another process's mount namespace) -- must not be guessed as host."""
    def boom(pid):
        return None, "could not check /proc/9011/root/.dockerenv: PermissionError: denied"
    result = pi.classify_pid(9011, read_cgroup_fn=lambda pid: "0::/\n", dockerenv_check_fn=boom)
    check("inconclusive cgroup with an unperformable dockerenv check classified as "
          "unknown, never defaulted to host",
          result["identity"] == "unknown", result)


def test_dockerenv_marker_probe_fixture_semantics():
    """Marker file absent, but the process itself is confirmed still
    present (the /proc/<pid> disambiguation stat succeeds) -- genuine
    marker absence, not a disappeared process."""
    calls = []
    def fake_stat(path):
        calls.append(path)
        if path.endswith("/.dockerenv"):
            raise FileNotFoundError(path)
        return object()  # /proc/<pid> itself still exists
    present, err = pi.check_dockerenv_marker(4242, stat_fn=fake_stat)
    check("check_dockerenv_marker checks /proc/<pid>/root/.dockerenv and reports False when the "
          "marker is absent but the process itself is confirmed still present",
          present is False and err is None and calls[0] == "/proc/4242/root/.dockerenv",
          (present, err, calls))


def test_dockerenv_marker_disappearing_process_is_unknown_not_absent():
    """Revision R1 correction: /proc/<pid>/root/.dockerenv raises the same
    FileNotFoundError whether the marker is genuinely absent inside a live
    container root, or the pid itself has disappeared. If /proc/<pid>
    itself is also gone, that must be reported as unknown (process
    disappeared), never silently folded into 'marker absent'."""
    def fake_stat(path):
        raise FileNotFoundError(path)  # both the marker AND /proc/<pid> are gone
    present, err = pi.check_dockerenv_marker(9999, stat_fn=fake_stat)
    check("check_dockerenv_marker reports unknown (None, reason) when the process disappears "
          "mid-check, rather than False (marker absent)",
          present is None and err is not None and "disappeared" in err,
          (present, err))


def test_ambiguous_root_cgroup_with_confirmed_absent_marker_is_unknown_not_host():
    """R1 correction: the ambiguous '0::/' cgroup shape plus a
    confirmed-absent /.dockerenv marker is NOT sufficient for host --
    that shape alone cannot rule out a container, and the marker's
    creation/removal is not guaranteed under every runtime, so this must
    stay unknown."""
    result = pi.classify_pid(
        9012, read_cgroup_fn=lambda pid: "0::/\n",
        dockerenv_check_fn=lambda pid: (False, None),
    )
    check("ambiguous root cgroup ('0::/') with confirmed-absent dockerenv marker "
          "classified as unknown, not host",
          result["identity"] == "unknown", result)


def test_ambiguous_root_cgroup_with_disappearing_process_is_unknown():
    """R1 correction: a process that disappears while its /.dockerenv
    marker is being checked, on top of the ambiguous root cgroup shape,
    must classify as unknown -- never as host from a False that was
    actually a disappeared-process artifact."""
    def disappearing(pid):
        return None, f"process {pid} no longer exists (disappeared during the marker check)"
    result = pi.classify_pid(
        9013, read_cgroup_fn=lambda pid: "0::/\n",
        dockerenv_check_fn=disappearing,
    )
    check("ambiguous root cgroup with a process that disappeared during the marker check "
          "classified as unknown, not host",
          result["identity"] == "unknown" and "disappeared" in result["evidence"],
          result)


def test_non_ambiguous_host_cgroup_with_confirmed_absent_marker_still_host():
    """A cgroup that carries real host-slice structure (not the bare
    uninformative '0::/' root) combined with a confirmed-absent marker
    remains established host evidence -- the R1 correction narrows the
    ambiguous case only, it does not weaken every host classification."""
    result = pi.classify_pid(
        9014, read_cgroup_fn=lambda pid: CGROUP_HOST,
        dockerenv_check_fn=lambda pid: (False, None),
    )
    check("non-ambiguous host-slice cgroup with confirmed-absent dockerenv marker "
          "still classified as host",
          result["identity"] == "host", result)


def test_unreadable_cgroup_is_unknown_not_defaulted():
    def boom(pid):
        raise PermissionError("denied")
    result = pi.classify_pid(9004, read_cgroup_fn=boom)
    check("unreadable /proc/<pid>/cgroup classified as unknown (never defaulted host/container)",
          result["identity"] == "unknown" and "PermissionError" in result["evidence"],
          result)


def test_docker_name_resolved_when_available():
    listing = f"{EXPECTED_ID}\tcis-pipeline\n"
    result = pi.classify_pid(
        9005, read_cgroup_fn=lambda pid: CGROUP_V2_DOCKER,
        docker_ps_fn=lambda **kw: listing,
    )
    check("docker ps cross-reference resolves the friendly container name",
          result["container_name"] == "cis-pipeline", result)


def test_identity_survives_docker_unavailable():
    def no_docker(**kw):
        raise FileNotFoundError("docker: command not found")
    result = pi.classify_pid(
        9006, read_cgroup_fn=lambda pid: CGROUP_V2_DOCKER, docker_ps_fn=no_docker,
    )
    check("container identity is correct even with no docker socket available "
          "(cgroup alone is sufficient; matters when this runs from inside a "
          "contained worker, per container_app.py's own note)",
          result["identity"] == "container" and result["container_name"] is None,
          result)


def test_find_pids_on_port_parses_ss_output():
    ss_output = (
        "LISTEN 0 4096 127.0.0.1:11434 0.0.0.0:*\n"
        "LISTEN 0 128  127.0.0.1:8642  0.0.0.0:* users:((\"python\",pid=1355184,fd=20))\n"
        "LISTEN 0 128  127.0.0.1:5000  0.0.0.0:* users:((\"python\",pid=3396511,fd=6))\n"
    )
    pids, listening_line_seen, error = pi.find_pids_on_port(5000, ss_fn=lambda: ss_output)
    check("find_pids_on_port extracts exactly the pid bound to the requested port",
          error is None and listening_line_seen is True and pids == [3396511],
          (pids, listening_line_seen, error))


def test_find_pids_on_port_no_match():
    ss_output = "LISTEN 0 4096 127.0.0.1:11434 0.0.0.0:*\n"
    pids, listening_line_seen, error = pi.find_pids_on_port(5000, ss_fn=lambda: ss_output)
    check("find_pids_on_port returns empty and listening_line_seen False, not an error, "
          "when nothing is on that port",
          error is None and listening_line_seen is False and pids == [],
          (pids, listening_line_seen, error))


def test_find_pids_on_port_line_seen_but_no_pid_visible():
    """A LISTEN line matches the port but carries no users:((...,pid=...))
    suffix (pid hidden/other namespace) -- must be distinguished from 'no
    line at all' rather than silently collapsed to the same empty result."""
    ss_output = "LISTEN 0 4096 0.0.0.0:5000 0.0.0.0:*\n"
    pids, listening_line_seen, error = pi.find_pids_on_port(5000, ss_fn=lambda: ss_output)
    check("find_pids_on_port reports listening_line_seen True with an empty pid list "
          "when the line matches but no pid is extractable",
          error is None and listening_line_seen is True and pids == [],
          (pids, listening_line_seen, error))


def test_incident_shape_reproduced_deterministically():
    """The exact Card 03 incident, fully fixture-driven: a process bound to
    port 5000 that is host-visible via ss (so the naive 'kill whatever's on
    5000' operator move would find it) but whose cgroup places it inside
    the cis-pipeline container -- must classify as container, not host."""
    ss_output = "LISTEN 0 128 0.0.0.0:5000 0.0.0.0:* users:((\"python\",pid=3396511,fd=6))\n"
    def fake_docker_ps(with_ports=False):
        return (f"{EXPECTED_ID}\tcis-pipeline\t0.0.0.0:5000->5000/tcp\n" if with_ports
                else f"{EXPECTED_ID}\tcis-pipeline\n")
    result = pi.classify_port(
        5000,
        ss_fn=lambda: ss_output,
        read_cgroup_fn=lambda pid: CGROUP_V2_DOCKER,
        docker_ps_fn=fake_docker_ps,
    )
    check("reproduced incident: port-5000 pid classified as container, not killable-as-standalone",
          result["listening"] is True
          and len(result["processes"]) == 1
          and result["processes"][0]["identity"] == "container"
          and result["processes"][0]["container_name"] == "cis-pipeline",
          result)


def test_iptables_only_publish_with_no_visible_pid_still_identifies_container():
    """Reproduced live on this host (see evidence.md): Docker's default
    iptables-only port publish leaves NO host-visible pid on `ss -p` at
    all for the published port. find_pids_on_port alone would wrongly
    report nothing listening; docker_port_publisher must still identify
    the container from Docker's own publish metadata."""
    ss_output = "LISTEN 0 4096 0.0.0.0:5000 0.0.0.0:*\n"  # no users:(...) — no visible pid
    result = pi.classify_port(
        5000,
        ss_fn=lambda: ss_output,
        read_cgroup_fn=lambda pid: (_ for _ in ()).throw(AssertionError("no pid to classify")),
        docker_ps_fn=lambda **kw: f"{EXPECTED_ID}\tcis-pipeline\t0.0.0.0:5000->5000/tcp\n",
    )
    check("iptables-only publish (no visible pid) still identifies the container",
          result["listening"] is True
          and len(result["processes"]) == 1
          and result["processes"][0]["identity"] == "container"
          and result["processes"][0]["pid"] is None,
          result)


def test_no_pid_no_docker_publisher_is_not_listening():
    result = pi.classify_port(
        5000,
        ss_fn=lambda: "LISTEN 0 4096 127.0.0.1:11434 0.0.0.0:*\n",
        docker_ps_fn=lambda **kw: "",
    )
    check("nothing on the port and no docker publisher -> listening False",
          result["listening"] is False and result["processes"] == [], result)


def test_genuine_standalone_host_process_classified_as_host():
    """The other side of the distinction: a real standalone host process on
    a different port must not be mistaken for a container either."""
    ss_output = "LISTEN 0 128 127.0.0.1:5001 0.0.0.0:* users:((\"python3\",pid=42424,fd=6))\n"
    result = pi.classify_port(
        5001,
        ss_fn=lambda: ss_output,
        read_cgroup_fn=lambda pid: CGROUP_HOST,
        docker_ps_fn=lambda **kw: "",
        dockerenv_check_fn=lambda pid: (False, None),
    )
    check("genuine standalone host process (no docker cgroup, no dockerenv marker, "
          "no publisher) classified as host",
          result["listening"] is True
          and len(result["processes"]) == 1
          and result["processes"][0]["identity"] == "host",
          result)


def test_visible_listen_hidden_pid_and_unavailable_docker_still_reports_listening():
    """The exact scenario from the Codex review finding: a fixture with a
    visible LISTEN socket, no resolvable pid, and an unavailable Docker
    probe must not collapse to listening=False -- that would silently
    drop a real socket just because neither identity signal resolved."""
    ss_output = "LISTEN 0 4096 0.0.0.0:5000 0.0.0.0:*\n"
    def no_docker(**kw):
        raise FileNotFoundError("docker: command not found")
    result = pi.classify_port(5000, ss_fn=lambda: ss_output, docker_ps_fn=no_docker)
    check("visible LISTEN line + hidden pid + unavailable docker probe -> "
          "listening True, with the docker probe failure named explicitly "
          "and an 'unknown' process entry instead of a dropped socket",
          result["listening"] is True
          and result.get("probe_errors", {}).get("docker") is not None
          and len(result["processes"]) == 1
          and result["processes"][0]["identity"] == "unknown"
          and result["processes"][0]["pid"] is None,
          result)


def test_ss_failure_reported_as_error_not_false_negative():
    def boom():
        raise RuntimeError("ss: permission denied")
    result = pi.classify_port(5000, ss_fn=boom, docker_ps_fn=lambda **kw: "")
    check("ss failure surfaces as an explicit error, not a silent 'not listening'",
          result["listening"] is None and "error" in result, result)


def test_live_real_host_reproduces_incident_identity():
    """No fixtures: ask the real host about the real cis-pipeline
    container's real published port right now. Skips cleanly (reported,
    not silently passed) if docker or the container isn't present in this
    environment."""
    try:
        import subprocess
        probe = subprocess.run(["docker", "inspect", "cis-pipeline", "--format", "{{.Id}}"],
                                capture_output=True, text=True, timeout=3)
    except Exception as e:
        check("live host check skipped (docker unavailable in this environment)",
              True, f"{type(e).__name__}: {e}")
        return
    if probe.returncode != 0 or not probe.stdout.strip():
        check("live host check skipped (cis-pipeline container not running here)",
              True, probe.stderr)
        return
    container_id = probe.stdout.strip()
    result = pi.classify_port(5000)
    matched = [p for p in result["processes"]
               if p.get("container_id") == container_id and p["identity"] == "container"]
    check("live: real cis-pipeline container correctly identified on real port 5000, "
          "with the exact evidence path that would have prevented the Card 03 incident",
          result["listening"] is True and len(matched) >= 1,
          result)


def test_live_real_container_process_classified_as_container_from_inside():
    """Revision 7 finding: `docker exec cis-pipeline` classification of its
    own PID was falsely returning host, because that process's real
    /proc/self/cgroup reads '0::/' (cgroup-namespace virtualization) with
    no docker scope name at all. Pull the container's actual cgroup text
    and actual /.dockerenv presence via read-only `docker exec` and feed
    that real evidence through classify_pid -- must come out container,
    not host. Skips cleanly (reported, not silently passed) if docker or
    the container isn't present in this environment."""
    import subprocess

    def run_in_container(args):
        return subprocess.run(
            ["docker", "exec", "cis-pipeline"] + args,
            capture_output=True, text=True, timeout=3,
        )

    try:
        cgroup_probe = run_in_container(["cat", "/proc/self/cgroup"])
    except Exception as e:
        check("live container-identity check skipped (docker unavailable in this environment)",
              True, f"{type(e).__name__}: {e}")
        return
    if cgroup_probe.returncode != 0:
        check("live container-identity check skipped (cis-pipeline container not running here)",
              True, cgroup_probe.stderr)
        return

    real_cgroup_text = cgroup_probe.stdout
    dockerenv_probe = run_in_container(["test", "-e", "/.dockerenv"])
    real_dockerenv_present = dockerenv_probe.returncode == 0

    result = pi.classify_pid(
        1,  # the pid this cgroup/.dockerenv evidence was actually read from, inside the container
        read_cgroup_fn=lambda pid: real_cgroup_text,
        dockerenv_check_fn=lambda pid: (real_dockerenv_present, None),
    )
    check("live: real cis-pipeline internal process cgroup text "
          f"({real_cgroup_text.strip()!r}) classified as container via the /.dockerenv "
          "fallback, not falsely as host",
          result["identity"] == "container", result)


def run():
    test_cgroup_v2_docker_scope_is_container()
    test_cgroup_v1_docker_path_is_container()
    test_plain_host_cgroup_is_host()
    test_namespace_virtualized_cgroup_with_dockerenv_marker_is_container()
    test_namespace_virtualized_cgroup_with_no_dockerenv_check_available_is_unknown()
    test_dockerenv_marker_probe_fixture_semantics()
    test_dockerenv_marker_disappearing_process_is_unknown_not_absent()
    test_ambiguous_root_cgroup_with_confirmed_absent_marker_is_unknown_not_host()
    test_ambiguous_root_cgroup_with_disappearing_process_is_unknown()
    test_non_ambiguous_host_cgroup_with_confirmed_absent_marker_still_host()
    test_unreadable_cgroup_is_unknown_not_defaulted()
    test_docker_name_resolved_when_available()
    test_identity_survives_docker_unavailable()
    test_find_pids_on_port_parses_ss_output()
    test_find_pids_on_port_no_match()
    test_find_pids_on_port_line_seen_but_no_pid_visible()
    test_incident_shape_reproduced_deterministically()
    test_iptables_only_publish_with_no_visible_pid_still_identifies_container()
    test_no_pid_no_docker_publisher_is_not_listening()
    test_genuine_standalone_host_process_classified_as_host()
    test_visible_listen_hidden_pid_and_unavailable_docker_still_reports_listening()
    test_ss_failure_reported_as_error_not_false_negative()
    test_live_real_host_reproduces_incident_identity()
    test_live_real_container_process_classified_as_container_from_inside()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
