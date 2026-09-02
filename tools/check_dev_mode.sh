#!/usr/bin/env bash
# check_dev_mode.sh — refuse to proceed while any agent is stripped for dev use.
#
# Queue item 1.17: a comment saying MUST BE RESTORED is not a check. Both
# dev-mode blocks in review2's config say exactly that, and nothing enforces it.
# This is the check. Rules become checks or they do not exist.
#
# Reads every /home/worker/.hermes-*/config.yaml inside the container, looks for
# the DEV MODE marker, and reports what each stripped agent is missing.
#
# Exit 0 — all six agents clean, safe to run the pipeline.
# Exit 1 — at least one agent is in dev mode. Named, with what was stripped.
# Exit 2 — could not check (container down, no configs). Not the same as clean:
#          an unverifiable state must not read as a pass.
#
# Usage:  bash tools/check_dev_mode.sh          # human-readable
#         bash tools/check_dev_mode.sh --quiet  # exit code only

set -uo pipefail

CONTAINER="${CIS_CONTAINER:-cis-pipeline}"
QUIET=0
[[ "${1:-}" == "--quiet" ]] && QUIET=1

say() { [[ $QUIET -eq 1 ]] || printf '%s\n' "$*"; }

if ! docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true; then
    say "CANNOT CHECK — container '$CONTAINER' is not running."
    say "An unverifiable state is not a clean state. Start the container and re-run."
    exit 2
fi

# -i is required: without it the container's stdin is closed and the heredoc
# below never reaches python, which then reads an empty program and prints
# nothing — a silent pass-shaped failure.
REPORT="$(docker exec -i "$CONTAINER" python3 - <<'PY'
import glob, sys

try:
    import yaml
except ImportError:
    print("ERROR|could not import yaml inside the container")
    sys.exit(0)

MARKER = "DEV MODE"
paths = sorted(glob.glob("/home/worker/.hermes-*/config.yaml"))

if not paths:
    print("ERROR|no agent configs found under /home/worker/.hermes-*/")
    sys.exit(0)

print(f"COUNT|{len(paths)}")

for path in paths:
    agent = path.split("/")[-2].replace(".hermes-", "")
    try:
        raw = open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"UNREADABLE|{agent}|{e}")
        continue

    if MARKER not in raw:
        print(f"CLEAN|{agent}")
        continue

    # Marked as dev mode. Say what is actually stripped, read from the parsed
    # config rather than from the comment — the comment is what we distrust.
    findings = []
    try:
        cfg = yaml.safe_load(raw) or {}
    except yaml.YAMLError as e:
        print(f"DIRTY|{agent}|config does not parse: {e}")
        continue

    skills = cfg.get("skills") or {}
    if isinstance(skills, dict):
        n = len(skills.get("disabled") or [])
        if n:
            findings.append(f"{n} skills disabled globally")
        for platform, names in (skills.get("platform_disabled") or {}).items():
            if names:
                findings.append(f"{len(names)} skills disabled on {platform}")

    for platform, toolsets in (cfg.get("platform_toolsets") or {}).items():
        if isinstance(toolsets, list):
            if not toolsets:
                findings.append(f"ALL toolsets removed on {platform}")
            else:
                findings.append(
                    f"toolsets trimmed on {platform} to: {', '.join(map(str, toolsets))}"
                )

    for name, spec in (cfg.get("mcp_servers") or {}).items():
        if isinstance(spec, dict) and spec.get("enabled") is False:
            findings.append(f"MCP server '{name}' disabled")

    if not findings:
        findings.append("marker present but nothing measurably stripped — check by hand")

    print(f"DIRTY|{agent}|" + "; ".join(findings))
PY
)"

if [[ -z "$REPORT" ]]; then
    say "CANNOT CHECK — no output from the container."
    exit 2
fi

if grep -q '^ERROR|' <<<"$REPORT"; then
    say "CANNOT CHECK — $(grep '^ERROR|' <<<"$REPORT" | cut -d'|' -f2)"
    exit 2
fi

total="$(grep '^COUNT|' <<<"$REPORT" | cut -d'|' -f2)"
dirty="$(grep -c '^DIRTY|' <<<"$REPORT")"
unreadable="$(grep -c '^UNREADABLE|' <<<"$REPORT")"

if [[ "$dirty" -eq 0 && "$unreadable" -eq 0 ]]; then
    say "PASS — all $total agents clean. No DEV MODE markers found."
    exit 0
fi

say "DEV MODE IN EFFECT — the pipeline must not run."
say ""
while IFS='|' read -r status agent detail; do
    case "$status" in
        DIRTY)      say "  $agent — $detail" ;;
        UNREADABLE) say "  $agent — config unreadable: $detail" ;;
    esac
done < <(grep -E '^(DIRTY|UNREADABLE)\|' <<<"$REPORT")
say ""
say "$dirty of $total agents are stripped for dev use. Restoring means removing"
say "the DEV MODE blocks from those configs. See queue item 1.17."
exit 1
