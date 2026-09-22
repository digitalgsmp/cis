#!/usr/bin/env python3
"""process_identity.py — deterministic host/container process identity
(CARD 04, queue 4.32 BEFORE_STAGE_CLOSEOUT discovery, revision 3).

Resolves the discovery recorded during Card 03 verification: the host
killed the cis-pipeline container's main process on port 5000, mistaking
it for a standalone dev Flask process, because the container's repo is
bind-mounted at the same path the host would use to run it standalone
(/mnt/projects/cis) and its command line ("python -c 'from
runtime.container_app import app; app.run(...)'" / "python3
runtime/app.py") looks the same in a host `ps` either way.

Reproduced live on this host (see evidence.md): the cis-pipeline
container's actual port-5000 process is visible in host `ps`/`ss` output
as an ordinary python process under the bind-mounted repo path -- process
name, cmdline shape, working directory, and port are NOT sufficient to
tell it apart from a genuinely standalone host process.

One host-kernel-enforced fact that cannot be spoofed by path/name
similarity is cgroup membership: every process's own /proc/<pid>/cgroup
is written by the kernel, and a process created by `docker run` (or, on
this host's cgroup v2 setup, any process forked inside dockerd's damon
control) is placed under a `.../docker-<64 hex>.scope` (cgroup v2) or
`.../docker/<64 hex>` (cgroup v1) cgroup path naming the container's own
ID -- a container cannot place itself outside that cgroup, and a
standalone host process is never placed inside one. This module reads
that fact and, best-effort only, cross-references the container ID
against `docker ps` for a human-readable name. The docker lookup is
optional: the host/container distinction itself never depends on it, so
this still works with no docker socket available (e.g. run from inside a
contained worker -- see runtime/container_app.py's own note that Docker
management is unavailable there).

Revision 7 correction (2026-09-22, Codex independent review of Card 04):
the docker-scope cgroup path is NOT always present for a real container.
cis-pipeline runs with cgroup-namespace virtualization (the modern Docker
default), so a process's own view of /proc/<pid>/cgroup inside that
container reads exactly "0::/" -- no docker scope name at all, the same
shape a host process outside any slice would show. Verified live: `docker
exec cis-pipeline cat /proc/self/cgroup` returns "0::/" on this host.
Absence of a docker cgroup scope is therefore evidence of nothing, not
proof of host. The secondary, independent signal used to break that tie
is /.dockerenv: Docker creates this marker file at the container's root
filesystem on every container it starts, regardless of cgroup namespace
mode, and it is checked via /proc/<pid>/root/.dockerenv (verified present
live in cis-pipeline). If that check itself cannot be performed (e.g.
permission denied crossing into another process's mount namespace), the
result is "unknown", never a guessed "host".

Correction R1 (2026-09-22, second independent-review round): revision 7's
own fix was still not sufficient. A root cgroup reading exactly "0::/" is
not just "no docker scope name" -- it is the SAME shape a plain host
process outside any slice shows, so it carries no information either way.
For that specific ambiguous shape, this module no longer treats a
confirmed-absent /.dockerenv marker as proof of host: the marker's
absence is real evidence, but it does not rule out a container running in
some environment this module has not seen where the marker was removed,
relocated, or never created (Docker does not guarantee /.dockerenv exists
under every possible container runtime configuration, and nothing prevents
its removal after creation) -- an unqualified "no marker => host" claim
overstates what has actually been verified. "0::/" + confirmed-absent
marker is therefore "unknown", not "host". A non-ambiguous cgroup shape
(anything showing real host-slice structure, e.g. systemd user/app slices)
combined with a confirmed-absent marker remains established host evidence,
because that cgroup content itself is informative, unlike bare "0::/".
Also fixed: the marker check itself previously could not tell "the marker
file is absent" apart from "the target process exited mid-check", both of
which raise FileNotFoundError on the same stat call when read through
/proc/<pid>/root/. A process that disappears while being classified is
reported as unknown with that reason, never silently folded into "marker
absent".

Contract:
- Read-only: inspects /proc and (failures reported explicitly, never
  swallowed into a guess) shells out to `docker ps`/`ss`. Never signals,
  kills, or otherwise touches the processes it inspects.
- Every classification names its own evidence (the raw cgroup line, the
  /.dockerenv check result, or why either could not be read) rather than
  asserting host/container from process name, PID, port, or cwd alone.
- "host" is only ever returned on positive evidence: a non-ambiguous
  cgroup (not bare "0::/") carrying no docker scope, AND a confirmed-absent
  /.dockerenv marker. For the ambiguous "0::/" cgroup shape specifically,
  a confirmed-absent marker is NOT treated as sufficient for host, because
  that shape alone does not rule out a container -- the result is
  "unknown" instead. Ambiguous or unreadable input (PID gone mid-check,
  /proc unreadable, permission denied, /.dockerenv check inconclusive) is
  reported as identity="unknown" with a reason -- never defaulted to
  "host" or "container" by guesswork.
- A probe that could not run at all (docker unavailable, ss unavailable)
  is reported as an explicit error/probe_errors entry, distinct from the
  probe running cleanly and finding nothing -- losing that distinction is
  how a real listening socket on an unreachable-docker host previously
  got reported as not listening at all.

Usage:
    python3 -m tools.development.process_identity --pid 12345
    python3 -m tools.development.process_identity --port 5000
"""
import argparse
import json
import os
import re
import subprocess
import sys

_CONTAINER_ID_RE = re.compile(
    r"docker[/-]([0-9a-f]{64})(?:\.scope)?"
)


def read_cgroup(pid):
    """Default cgroup reader: the real /proc/<pid>/cgroup on this host."""
    with open(f"/proc/{pid}/cgroup", "r") as f:
        return f.read()


def run_docker_ps(with_ports=False, timeout=3):
    """Default docker lookup: real `docker ps`. Any failure (no docker
    binary, no socket access, timeout) is the caller's problem to catch --
    this raises rather than guessing, so a caller can tell 'no docker
    available' apart from 'docker said nothing'."""
    fmt = "{{.ID}}\t{{.Names}}\t{{.Ports}}" if with_ports else "{{.ID}}\t{{.Names}}"
    proc = subprocess.run(
        ["docker", "ps", "--no-trunc", "--format", fmt],
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"docker ps exited {proc.returncode}: {proc.stderr.strip()}")
    return proc.stdout


def run_ss(timeout=3):
    """Default port->pid lookup: real `ss -H -t -n -l -p`."""
    proc = subprocess.run(
        ["ss", "-H", "-t", "-n", "-l", "-p"],
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ss exited {proc.returncode}: {proc.stderr.strip()}")
    return proc.stdout


def _extract_container_id(cgroup_text):
    """Full 64-hex container ID out of a /proc/<pid>/cgroup blob, or None
    if no docker cgroup line is present (cgroup v1: '.../docker/<id>';
    cgroup v2 unified hierarchy: '.../docker-<id>.scope')."""
    m = _CONTAINER_ID_RE.search(cgroup_text)
    return m.group(1) if m else None


def _docker_name_for_id(container_id, docker_ps_fn=run_docker_ps):
    """Best-effort friendly container name for a full container ID. Returns
    None on any failure (no docker, no permission, unknown ID) -- this is
    decoration on top of the cgroup-derived identity, never load-bearing
    for the host/container distinction itself."""
    try:
        listing = docker_ps_fn()
    except Exception:
        return None
    for line in listing.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[0] == container_id:
            return parts[1]
    return None


def check_dockerenv_marker(pid, stat_fn=os.stat):
    """Secondary, independent container signal for when cgroup evidence is
    inconclusive (cgroup-namespace virtualization can make a real
    container's own /proc/<pid>/cgroup read "0::/", identical in shape to
    a host process outside any cgroup slice -- reproduced live against
    cis-pipeline). Docker creates /.dockerenv at a container's root
    filesystem on every container it starts, regardless of cgroup
    namespace mode, so this checks it via /proc/<pid>/root/.dockerenv --
    resolved in the pid's own mount namespace.

    Returns (True, None) if the marker exists (positive container
    evidence), (False, None) if it definitely does not (positive absence --
    combined with non-ambiguous host-slice cgroup evidence, this is what
    "host" is allowed to rest on; combined with the ambiguous bare "0::/"
    cgroup shape, classify_pid treats this as "unknown", not host), or
    (None, reason) if the check itself could not be performed. That
    inconclusive case covers two distinct failures, both surfaced with
    their own reason rather than collapsed into False:
    - permission denied crossing into another process's mount namespace, or
    - the target pid disappeared between being asked about and this check
      running (a FileNotFoundError on /proc/<pid>/root/.dockerenv is
      identical in shape whether the marker is genuinely absent inside a
      live container's root, or the process (and its /proc/<pid>/root
      view) no longer exists at all -- so a second, explicit check of
      /proc/<pid> itself disambiguates before reporting False."""
    root_path = f"/proc/{pid}/root"
    marker_path = f"{root_path}/.dockerenv"
    try:
        stat_fn(marker_path)
        return True, None
    except FileNotFoundError:
        try:
            stat_fn(f"/proc/{pid}")
        except FileNotFoundError:
            return None, f"process {pid} no longer exists (disappeared during the marker check)"
        except OSError as e:
            return None, (
                f"could not confirm process {pid} still exists while checking "
                f"{marker_path}: {type(e).__name__}: {e}"
            )
        return False, None
    except OSError as e:
        return None, f"could not check {marker_path}: {type(e).__name__}: {e}"


def _is_ambiguous_root_cgroup(cgroup_text):
    """True when the cgroup text carries no informative content at all --
    the cgroup v2 unified-hierarchy root, '0::/', with nothing after the
    trailing slash. This is the exact shape a container running with
    cgroup-namespace virtualization shows (verified live: `docker exec
    cis-pipeline cat /proc/self/cgroup`) AND the shape a bare host process
    outside any cgroup slice shows -- neither can be distinguished from the
    other by this text alone, so it is treated as ambiguous rather than as
    "no docker scope, therefore host-leaning" evidence."""
    lines = [line.strip() for line in cgroup_text.strip().splitlines() if line.strip()]
    return len(lines) == 1 and lines[0] in ("0::/", "0::")


def classify_pid(pid, read_cgroup_fn=read_cgroup, docker_ps_fn=run_docker_ps,
                  dockerenv_check_fn=check_dockerenv_marker):
    """Classify one PID as identity in {"container", "host", "unknown"}.

    cgroup membership is the primary, host-kernel-enforced signal -- never
    process name, cmdline, port, or cwd, all of which can be identical
    between a bind-mounted container process and a standalone host
    process (the Card 03 incident). But absence of a docker cgroup scope
    name is NOT sufficient proof of host (revision 7 correction): a
    container running with cgroup-namespace virtualization shows the same
    "0::/" shape a host process would. /.dockerenv is checked as
    independent positive evidence before concluding host, and "unknown"
    is returned rather than guessed host/container when neither check
    lands on positive evidence."""
    try:
        cgroup_text = read_cgroup_fn(pid)
    except (OSError, IOError) as e:
        return {
            "pid": pid, "identity": "unknown", "container_id": None,
            "container_name": None,
            "evidence": f"could not read /proc/{pid}/cgroup: {type(e).__name__}: {e}",
        }
    container_id = _extract_container_id(cgroup_text)
    if container_id is not None:
        return {
            "pid": pid, "identity": "container", "container_id": container_id,
            "container_name": _docker_name_for_id(container_id, docker_ps_fn),
            "evidence": f"/proc/{pid}/cgroup places this pid in docker container {container_id}",
        }

    ambiguous_cgroup = _is_ambiguous_root_cgroup(cgroup_text)
    has_dockerenv, marker_error = dockerenv_check_fn(pid)
    if has_dockerenv is True:
        return {
            "pid": pid, "identity": "container", "container_id": None,
            "container_name": None,
            "evidence": (
                f"/proc/{pid}/cgroup carries no docker container scope "
                f"({cgroup_text.strip()!r}, consistent with cgroup-namespace "
                "virtualization inside a container) but /proc/"
                f"{pid}/root/.dockerenv exists, which docker only creates "
                "inside a container's own root filesystem"
            ),
        }
    if has_dockerenv is False:
        if ambiguous_cgroup:
            return {
                "pid": pid, "identity": "unknown", "container_id": None,
                "container_name": None,
                "evidence": (
                    f"/proc/{pid}/cgroup is the ambiguous root shape "
                    f"({cgroup_text.strip()!r}), which a container under "
                    "cgroup-namespace virtualization and a bare host process "
                    "both show identically, and no /.dockerenv marker was "
                    "found -- but a confirmed-absent marker on this "
                    "uninformative cgroup shape alone is not proof of host "
                    "(the marker's creation is not guaranteed under every "
                    "container runtime configuration and nothing rules out "
                    "its removal), so this stays unknown rather than "
                    "defaulting to host"
                ),
            }
        return {
            "pid": pid, "identity": "host", "container_id": None,
            "container_name": None,
            "evidence": (
                f"/proc/{pid}/cgroup carries no docker container scope and "
                f"shows real host-slice structure ({cgroup_text.strip()!r}, "
                "not the uninformative root shape) and no /.dockerenv marker "
                f"exists in /proc/{pid}/root -- positive evidence of host, "
                "not merely absence of the docker cgroup signal"
            ),
        }
    return {
        "pid": pid, "identity": "unknown", "container_id": None,
        "container_name": None,
        "evidence": (
            f"/proc/{pid}/cgroup carries no docker container scope "
            f"({cgroup_text.strip()!r}), and the /.dockerenv secondary check "
            f"could not be performed: {marker_error}"
        ),
    }


def docker_port_publisher(port, docker_ps_fn=run_docker_ps):
    """Which running container (if any) publishes host TCP `port`, straight
    from Docker's own port-publish metadata (docker ps --format Ports).

    This is the second, independent identity signal alongside cgroup-based
    PID classification, and it matters for a case reproduced live on this
    host (see evidence.md): when Docker publishes a port via iptables DNAT
    only (no `docker-proxy` process, the modern default), the container's
    listening socket lives entirely inside the container's own network
    namespace -- `ss -p` on the host sees the LISTEN state for the
    published port but resolves NO owning pid at all, so find_pids_on_port
    alone would wrongly conclude nothing is there. Docker's own publish
    metadata still names the container regardless of proxy mode, so it is
    checked independently rather than being derived from ss/pid at all.

    Returns (publisher_or_None, probe_error). probe_error is None when the
    docker probe itself ran (whether or not it found a match); it is a
    string when the probe could not run at all (no docker binary, no
    socket access, timeout, caller injected a 2-column docker_ps_fn) --
    that distinction matters because "docker was unreachable" must not be
    silently folded into "no container publishes this port" by a caller
    deciding whether anything is listening."""
    try:
        listing = docker_ps_fn(with_ports=True)
    except TypeError:
        # docker_ps_fn injected by a caller/test that doesn't take
        # with_ports (older 2-column ID/Names form) -- no port data available.
        return None, "docker_ps_fn does not support with_ports; no port-publish data available"
    except Exception as e:
        return None, f"docker port-publish probe unavailable: {type(e).__name__}: {e}"
    needle = f":{port}->"
    for line in listing.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        container_id, name, ports = parts
        if needle in ports:
            return {"container_id": container_id, "container_name": name}, None
    return None, None


def find_pids_on_port(port, ss_fn=run_ss):
    """Host PIDs currently LISTENing on a TCP port, via `ss -p` (needs no
    special privilege for a process's own-user sockets, which is the case
    for every process this module has been asked to classify so far).

    Returns (pids, listening_line_seen, error). listening_line_seen is
    True whenever a LISTEN line matching the port was present, even if no
    owning pid could be extracted from it (hidden pid / other network
    namespace) -- kept separate from `pids` so a caller does not conflate
    "nothing is listening" with "something is listening but its pid
    isn't visible", the exact gap that previously let a real listening
    socket be reported as not listening when the pid was hidden and the
    docker probe was also unavailable."""
    try:
        output = ss_fn()
    except Exception as e:
        return None, None, f"could not enumerate listening sockets: {type(e).__name__}: {e}"
    pids = set()
    listening_line_seen = False
    port_suffix = f":{port}"
    for line in output.splitlines():
        fields = line.split()
        if len(fields) < 4 or not fields[3].endswith(port_suffix):
            continue
        listening_line_seen = True
        for pid_match in re.finditer(r"pid=(\d+)", line):
            pids.add(int(pid_match.group(1)))
    return sorted(pids), listening_line_seen, None


def classify_port(port, ss_fn=run_ss, read_cgroup_fn=read_cgroup, docker_ps_fn=run_docker_ps,
                   dockerenv_check_fn=check_dockerenv_marker):
    """Classify every process currently listening on `port`. This is the
    entry point recovery_packet.py uses in place of a bare 'is the port
    open' check, so an operator (or automated recovery tooling) has
    host-verifiable evidence before treating anything on that port as
    safe to kill.

    Two independent signals are combined because either alone can miss the
    container case: a host-visible pid is classified via its cgroup (and,
    when cgroup evidence is inconclusive, /.dockerenv), and Docker's own
    port-publish metadata is checked separately (it still names the
    container even when no pid is host-visible at all -- see
    docker_port_publisher's docstring for the reproduced iptables-only-
    publish case). A LISTEN line seen on the port but attributable to
    neither a pid nor a docker publisher is still reported as listening,
    with the unresolved probe(s) named explicitly rather than the socket
    being silently dropped."""
    pids, listening_line_seen, error = find_pids_on_port(port, ss_fn=ss_fn)
    if error is not None:
        return {"port": port, "listening": None, "processes": [], "error": error}

    processes = [
        classify_pid(pid, read_cgroup_fn=read_cgroup_fn, docker_ps_fn=docker_ps_fn,
                     dockerenv_check_fn=dockerenv_check_fn)
        for pid in pids
    ]

    publisher, docker_error = docker_port_publisher(port, docker_ps_fn=docker_ps_fn)
    already_named = {p["container_id"] for p in processes if p.get("container_id")}
    if publisher and publisher["container_id"] not in already_named:
        processes.append({
            "pid": None,
            "identity": "container",
            "container_id": publisher["container_id"],
            "container_name": publisher["container_name"],
            "evidence": (
                f"docker reports container {publisher['container_name']} "
                f"({publisher['container_id'][:12]}) publishes host port {port}; "
                "no host-visible owning pid (iptables/NAT-only publish, not a "
                "userland proxy process)"
            ),
        })
    elif listening_line_seen and not pids:
        # ss saw a LISTEN line for this port but resolved no owning pid,
        # and docker's publish metadata named no container either -- do
        # not drop the socket silently; say plainly what could and could
        # not be established.
        note = (
            f"a LISTEN socket on port {port} was observed via ss but no "
            "owning pid was visible on it (hidden pid or other network "
            "namespace)"
        )
        note += (
            f", and the docker port-publish probe could not confirm a "
            f"container either: {docker_error}"
            if docker_error is not None
            else ", and no docker container publishes this port"
        )
        processes.append({
            "pid": None, "identity": "unknown", "container_id": None,
            "container_name": None, "evidence": note,
        })

    result = {
        "port": port,
        "listening": bool(pids) or listening_line_seen or publisher is not None,
        "processes": processes,
    }
    if docker_error is not None:
        result["probe_errors"] = {"docker": docker_error}
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pid", type=int)
    g.add_argument("--port", type=int)
    args = ap.parse_args()
    if args.pid is not None:
        print(json.dumps(classify_pid(args.pid), indent=2))
    else:
        print(json.dumps(classify_port(args.port), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
