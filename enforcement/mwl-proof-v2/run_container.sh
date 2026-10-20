#!/bin/bash
# run_container.sh — Launch the CIS pipeline in Docker
#
# Usage:
#   ./run_container.sh           — start container (interactive, logs to console)
#   ./run_container.sh -d        — start detached (background)
#   ./run_container.sh candidate — create but do not start a hardened candidate
#   ./run_container.sh stop      — stop and remove container
#   ./run_container.sh logs      — tail container logs
#   ./run_container.sh exec      — exec into container
#
# Prerequisites:
#   - Docker image cis-hermes:pipeline built
#   - /mnt/projects/cis/secrets.env with DEEPSEEK_API_KEY and OPENROUTER_API_KEY
#   - CIS repo at /mnt/projects/cis
#
# The container mounts:
#   /mnt/projects/cis  →  /workspace/cis   (code, read-only)
#   data/ and state/   →  nested read-write exceptions for the transitional
#                        combined control-plane container
#   secrets.env        →  /workspace/secrets.env  (API keys, read-only)
#
# SECRET HANDLING: this script runs as host root when systemd starts it, so it
# NEVER sources or executes the secrets file. The file is parsed as data by awk,
# a fixed allowlist of names is copied into a private 0600 env-file, and Docker
# receives that env-file. Sourcing a developer-writable file as root would hand
# repository write access a root shell, which is the boundary queue 4.37 exists
# to close.
#
# Port 5000 (pipeline API) is published to the host.
# Gateway ports (8644-8648) are internal to the container only.

set -e

IMAGE_TAG="cis-hermes:pipeline"
IMAGE=""
CONTAINER_NAME="cis-pipeline"
CIS_REPO="/mnt/projects/cis"
SECRETS_FILE="/mnt/projects/cis/secrets.env"
CONTROL_ROOT="/opt/cis-control"
CONTROL_RUNTIME="$CONTROL_ROOT/runtime"
WORKSPACE_ROOT="/mnt/cache/cis-workspaces/pipeline-control"
WORKSPACE_UID=1000
WORKSPACE_GID=1000

# The only names forwarded out of the secrets file. Anything else in that file
# stays out of the container environment, so a new line added to secrets.env
# cannot silently widen what the container sees.
FORWARDED_SECRET_NAMES="CIS_TG_BRAIN_TOKEN CIS_TG_DRAFT_TOKEN CIS_TG_REVIEW1_TOKEN CIS_TG_REVIEW2_TOKEN CIS_TG_MENTER_TOKEN CIS_TG_VERIFY_TOKEN CIS_TG_NOTIFY_TOKEN CIS_TG_HOME_CHANNEL"

case "${1:-start}" in

  start|-d|--detach|candidate)
    DOCKER_ACTION="run"
    PORT_FLAG="-p 5000:5000"
    if [ "${1:-start}" = "candidate" ]; then
        CONTAINER_NAME="cis-pipeline-candidate"
        DOCKER_ACTION="create"
    fi

    # Check if already running
    if sg docker -c "docker ps -q -f name=$CONTAINER_NAME" 2>/dev/null | grep -q .; then
        echo "Container $CONTAINER_NAME is already running."
        echo "Use '$0 stop' to stop it first, or '$0 logs' to see output."
        exit 1
    fi

    # Check secrets file — must be a real regular file, not a symlink and not a
    # directory. Docker creates a directory if the source path doesn't exist at
    # container creation time, which then blocks the bind mount forever, so
    # directory mistakes are caught early. A symlink is refused outright: it
    # would let a repository-writable link redirect secret delivery to any file
    # the root launcher can read.
    if [ -L "$SECRETS_FILE" ]; then
        echo "REFUSED: $SECRETS_FILE is a symlink; secrets must be a real file." >&2
        exit 1
    fi
    if [ ! -f "$SECRETS_FILE" ]; then
        if [ -d "$SECRETS_FILE" ]; then
            echo "REFUSED: $SECRETS_FILE is a directory, not a file." >&2
            echo "This happens if Docker created it as a directory on a previous run." >&2
            echo "Fix: rm -rf $SECRETS_FILE && create it as a file." >&2
        elif [ -e "$SECRETS_FILE" ]; then
            echo "REFUSED: $SECRETS_FILE is not a regular file." >&2
        else
            echo "REFUSED: $SECRETS_FILE not found." >&2
            echo "Create it with:" >&2
            echo "  echo 'DEEPSEEK_API_KEY=sk-...' > $SECRETS_FILE" >&2
            echo "  echo 'OPENROUTER_API_KEY=sk-or-...' >> $SECRETS_FILE" >&2
        fi
        exit 1
    fi

    # Transcribe the allowlisted names into a private env-file. awk only ever
    # reads bytes, so command substitution, backticks or a stray `rm -rf` inside
    # secrets.env are inert text here — unlike the `source` this replaced, which
    # executed the whole file with the launcher's authority. The env-file is
    # mode 0600, lives outside the repository, and is removed on exit.
    #
    # DEEPSEEK_API_KEY and OPENROUTER_API_KEY are deliberately NOT forwarded:
    # the container reads them from the read-only /workspace/secrets.env mount,
    # so they stay out of `docker inspect` output.
    ENV_FILE="$(mktemp /tmp/cis-container-env.XXXXXXXX)"
    chmod 600 "$ENV_FILE"
    trap 'rm -f "$ENV_FILE"' EXIT HUP INT TERM
    awk -v names="$FORWARDED_SECRET_NAMES" '
        BEGIN { count = split(names, list, " "); for (i = 1; i <= count; i++) allowed[list[i]] = 1 }
        {
            line = $0
            sub(/\r$/, "", line)
            if (line ~ /^[ \t]*#/) next
            position = index(line, "=")
            if (position == 0) next
            name = substr(line, 1, position - 1)
            value = substr(line, position + 1)
            gsub(/^[ \t]+|[ \t]+$/, "", name)
            sub(/^export[ \t]+/, "", name)
            if (!(name in allowed)) next
            if (length(value) >= 2) {
                first = substr(value, 1, 1)
                last = substr(value, length(value), 1)
                if ((first == "\"" && last == "\"") || (first == "\047" && last == "\047"))
                    value = substr(value, 2, length(value) - 2)
            }
            if (value == "") next
            printf "%s=%s\n", name, value
            found++
        }
        END { if (!found) print "[run_container] WARNING: no forwarded secret names found in secrets file" > "/dev/stderr" }
    ' "$SECRETS_FILE" >> "$ENV_FILE"

    # Retirement-ready launches trust only sealed host-control artifacts, not
    # the developer-writable repository copies. The operator promotes reviewed
    # bytes into these paths through true host-root authority. Missing or
    # incorrectly owned control files REFUSE the restart; there is no fallback
    # to repository or baked copies.
    ENTRYPOINT_SRC="$CONTROL_RUNTIME/entrypoint.sh"
    PROFILES_SRC="$CONTROL_RUNTIME/profiles"
    PLUGIN_SRC="$CONTROL_RUNTIME/plugin"
    MANAGED_CONFIG_SRC="$CONTROL_RUNTIME/managed-config.yaml"
    GATES_SRC="$CONTROL_RUNTIME/gates"
    GATE_RUNNER_SRC="$GATES_SRC/container_gate_runner.py"
    IMAGE_ID_SRC="$CONTROL_ROOT/policy/pipeline-image-id.txt"
    OVERRIDE_SRC="$CONTROL_ROOT/gate"
    for required in "$CONTROL_ROOT" "$ENTRYPOINT_SRC" "$PROFILES_SRC" "$PLUGIN_SRC" \
                    "$MANAGED_CONFIG_SRC" "$GATE_RUNNER_SRC" "$GATES_SRC" \
                    "$IMAGE_ID_SRC" "$OVERRIDE_SRC"; do
        if [ ! -e "$required" ]; then
            echo "REFUSED: required sealed control artifact is absent: $required" >&2
            exit 1
        fi
        if [ "$(stat -c %u "$required")" != "0" ]; then
            echo "REFUSED: sealed control artifact is not host-root-owned: $required" >&2
            exit 1
        fi
    done
    if find "$CONTROL_ROOT" -xdev \( -perm -0020 -o -perm -0002 \) -print -quit | grep -q .; then
        echo "REFUSED: /opt/cis-control contains group/world-writable paths" >&2
        exit 1
    fi
    IMAGE="$(tr -d '\r\n' < "$IMAGE_ID_SRC")"
    if ! printf '%s\n' "$IMAGE" | grep -Eq '^sha256:[0-9a-f]{64}$'; then
        echo "REFUSED: sealed pipeline image ID is malformed" >&2
        exit 1
    fi
    TAG_IMAGE_ID="$(sg docker -c "docker image inspect --format '{{.Id}}' $IMAGE_TAG" 2>/dev/null || true)"
    if [ "$TAG_IMAGE_ID" != "$IMAGE" ]; then
        echo "REFUSED: $IMAGE_TAG resolves to $TAG_IMAGE_ID, expected sealed $IMAGE" >&2
        exit 1
    fi
    if ! sg docker -c "docker image inspect $IMAGE" >/dev/null 2>&1; then
        echo "REFUSED: sealed pipeline image is not installed: $IMAGE" >&2
        exit 1
    fi
    # The contained worker runs as uid/gid 1000. When systemd starts this
    # launcher as host root (UMask=0077), a plain mkdir would leave the task
    # workspace root-owned and mode 0700 — unwritable to the worker, so every
    # task would fail with a permission error that looks like a code bug. Create
    # it with the worker's identity and no group/world access instead.
    #
    # An existing workspace is left as-is unless it is root-owned (a leftover
    # from an earlier root launch) or group/world-accessible, so a working
    # deployment is not disturbed and its contents are never recursively
    # rewritten.
    WORKSPACE_PARENT="$(dirname "$WORKSPACE_ROOT")"
    if [ ! -d "$WORKSPACE_PARENT" ]; then
        mkdir -p -m 0755 "$WORKSPACE_PARENT"
    fi
    if [ ! -d "$WORKSPACE_ROOT" ]; then
        mkdir -p "$WORKSPACE_ROOT"
        chmod 0700 "$WORKSPACE_ROOT"
        if [ "$(id -u)" = "0" ]; then
            chown "$WORKSPACE_UID:$WORKSPACE_GID" "$WORKSPACE_ROOT"
        fi
    else
        if [ "$(id -u)" = "0" ] && [ "$(stat -c %u "$WORKSPACE_ROOT")" = "0" ]; then
            chown "$WORKSPACE_UID:$WORKSPACE_GID" "$WORKSPACE_ROOT"
        fi
        if [ "$(stat -c %a "$WORKSPACE_ROOT")" != "700" ]; then
            if ! chmod go-rwx "$WORKSPACE_ROOT"; then
                echo "REFUSED: cannot remove group/world access from $WORKSPACE_ROOT" >&2
                exit 1
            fi
        fi
    fi
    if [ "$(stat -c %u:%g "$WORKSPACE_ROOT")" != "$WORKSPACE_UID:$WORKSPACE_GID" ]; then
        echo "REFUSED: $WORKSPACE_ROOT is owned by $(stat -c %u:%g "$WORKSPACE_ROOT"), expected $WORKSPACE_UID:$WORKSPACE_GID" >&2
        echo "The contained worker could not write its task workspace. Fix:" >&2
        echo "  sudo chown $WORKSPACE_UID:$WORKSPACE_GID $WORKSPACE_ROOT" >&2
        exit 1
    fi

    DETACH_FLAG=""
    if [ "${1:-start}" = "-d" ] || [ "${1:-start}" = "--detach" ]; then
        DETACH_FLAG="-d"
    fi

    # The six per-profile volumes preserve agent state (state.db, memories, the
    # split skill files) across the docker rm below. They also MASK the image at
    # that path: a named volume is seeded from the image only while it is empty,
    # and docker rm does not delete volumes — so after first creation, a rebuild
    # never refreshes anything inside those homes, the sealed plugin included.
    #
    # Hence the six nested :ro bind mounts added 2026-09-03. A deeper mount wins
    # over a shallower one, so the plugin alone comes from the repo on every
    # start while the rest of the home stays persistent. Read-only here is
    # KERNEL-enforced, which is stronger than the Dockerfile's root-owned 0444 —
    # that stops the worker, this stops root too.
    #
    # NOTE: no comments may go inside the docker run string below. It is one
    # double-quoted argument to `sg docker -c`, so a '#' would comment out the
    # remainder of the joined command.
    #
    # advisor and evaluator take the image copy — they have no volume to mask it.
    #
    # SECURITY STATUS: this is the transitional combined container, not the
    # queue 4.37 retirement-ready boundary. It still grants broad SWA writes and
    # writable data/state. Enforcement files now come only from root-owned
    # /opt/cis-control (the refusal block above), but do not treat a successful
    # start as proof of final containment. A replacement manifest must pass the
    # deterministic container-boundary gate before this running container is
    # recreated.
    #
    # THE OVERRIDE PLANE (2026-09-03, queue item 0.4). .gate-control is mounted
    # read-only at /opt/cis-control/gate, and the plugin checks
    # /opt/cis-control/gate/DISABLED as its first action on every tool call.
    # `touch .gate-control/DISABLED` on the host turns the wall off with no
    # restart; removing it turns the wall back on. Read-only means the agents
    # can read that file and can never create it — an override the constrained
    # agent can set is a self-disable, not an override. See .gate-control/README.md.
    echo "Starting $CONTAINER_NAME from sealed image $IMAGE ($IMAGE_TAG)..."

    # Remove old stopped container if exists
    sg docker -c "docker rm -f $CONTAINER_NAME" 2>/dev/null || true

    sg docker -c "docker $DOCKER_ACTION $DETACH_FLAG \
        --name $CONTAINER_NAME \
        $PORT_FLAG \
        --read-only \
        --cap-drop ALL \
        --security-opt no-new-privileges:true \
        --pids-limit 1024 \
        --tmpfs /tmp:rw,nosuid,nodev,size=2g \
        --tmpfs /run:rw,nosuid,nodev,size=64m \
        -v $CIS_REPO:/workspace/cis:ro \
        -v $CIS_REPO/data:/workspace/cis/data:rw \
        -v $CIS_REPO/state:/workspace/cis/state:rw \
        -v $WORKSPACE_ROOT:/workspace/output:rw \
        -v $CONTROL_ROOT:/control:ro \
        -v cis-claude-creds:/home/worker/.claude \
        -v /mnt/projects/swa-app:/workspace/swa-app:ro \
        -v /mnt/projects/swa:/workspace/swa:ro \
        -v /mnt/projects/secure-note-app:/workspace/swa-repos/secure-note-app:ro \
        -v /mnt/projects/hippa-case-management:/workspace/swa-repos/hippa-case-management:ro \
        -v /mnt/projects/cis-v1:/workspace/swa-repos/cis-v1:ro \
        -v $SECRETS_FILE:/workspace/secrets.env:ro \
        -v $OVERRIDE_SRC:/opt/cis-control/gate:ro \
        -v /mnt/models/huggingface:/opt/models/huggingface:ro \
        -v cis-agent-brain:/home/worker/.hermes-brain \
        -v cis-agent-draft:/home/worker/.hermes-draft \
        -v cis-agent-review1:/home/worker/.hermes-review1 \
        -v cis-agent-review2:/home/worker/.hermes-review2 \
        -v cis-agent-menter:/home/worker/.hermes-menter \
        -v cis-agent-verify:/home/worker/.hermes-verify \
        -v cis-agent-advisor:/home/worker/.hermes-advisor \
        -v cis-agent-evaluator:/home/worker/.hermes-evaluator \
        -v $PLUGIN_SRC:/home/worker/.hermes-brain/plugins/mwl-proof:ro \
        -v $PLUGIN_SRC:/home/worker/.hermes-draft/plugins/mwl-proof:ro \
        -v $PLUGIN_SRC:/home/worker/.hermes-review1/plugins/mwl-proof:ro \
        -v $PLUGIN_SRC:/home/worker/.hermes-review2/plugins/mwl-proof:ro \
        -v $PLUGIN_SRC:/home/worker/.hermes-menter/plugins/mwl-proof:ro \
        -v $PLUGIN_SRC:/home/worker/.hermes-verify/plugins/mwl-proof:ro \
        -v $PLUGIN_SRC:/home/worker/.hermes-advisor/plugins/mwl-proof:ro \
        -v $PLUGIN_SRC:/home/worker/.hermes-evaluator/plugins/mwl-proof:ro \
        -v $ENTRYPOINT_SRC:/opt/cis-control/entrypoint.sh:ro \
        -v $PROFILES_SRC:/etc/hermes/profiles:ro \
        -v $MANAGED_CONFIG_SRC:/etc/hermes/config.yaml:ro \
        -v $GATES_SRC:/opt/cis-gates:ro \
        -e CIS_BRAIN_API_KEY=cis-brainstorm-gateway-key-2026 \
        -e CIS_DRAFT_API_KEY=cis-drafter-gateway-key-2026 \
        -e CIS_REVIEW1_API_KEY=cis-qwen-reviewer-gateway-key-2026 \
        -e CIS_REVIEW2_API_KEY=cis-glm-reviewer-gateway-key-2026 \
        -e CIS_MENTER_API_KEY=cis-implementer-gateway-key-2026 \
        -e CIS_VERIFY_API_KEY=cis-verifier-gateway-key-2026 \
        --env-file $ENV_FILE \
        $IMAGE"

    if [ "${1:-start}" = "candidate" ]; then
        echo ""
        echo "Hardened candidate created but not started."
        echo "  Verify: python3 tools/gates/gate_container_boundary.py --container $CONTAINER_NAME"
        echo "  Remove: sg docker -c 'docker rm $CONTAINER_NAME'"
    elif [ -n "$DETACH_FLAG" ]; then
        echo ""
        echo "Container started in background."
        echo "  Pipeline API: http://localhost:5000"
        echo "  Logs: $0 logs"
        echo "  Stop: $0 stop"
    fi
    ;;

  stop)
    echo "Stopping $CONTAINER_NAME..."
    sg docker -c "docker stop $CONTAINER_NAME" 2>/dev/null || true
    sg docker -c "docker rm $CONTAINER_NAME" 2>/dev/null || true
    echo "Done."
    ;;

  logs)
    sg docker -c "docker logs -f $CONTAINER_NAME"
    ;;

  exec)
    sg docker -c "docker exec -it $CONTAINER_NAME bash"
    ;;

  *)
    echo "Usage: $0 {start|-d|candidate|stop|logs|exec}"
    exit 1
    ;;
esac
