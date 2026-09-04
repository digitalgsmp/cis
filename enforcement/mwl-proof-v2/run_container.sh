#!/bin/bash
# run_container.sh — Launch the CIS pipeline in Docker
#
# Usage:
#   ./run_container.sh           — start container (interactive, logs to console)
#   ./run_container.sh -d        — start detached (background)
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
#   /mnt/projects/cis  →  /workspace/cis   (code + SQLite spine, read-write)
#   /tmp/cis-secrets.env  →  /workspace/secrets.env  (API keys, read-only)
#
# Port 5000 (pipeline API) is published to the host.
# Gateway ports (8644-8648) are internal to the container only.

set -e

IMAGE="cis-hermes:pipeline"
CONTAINER_NAME="cis-pipeline"
CIS_REPO="/mnt/projects/cis"
SECRETS_FILE="/mnt/projects/cis/secrets.env"

case "${1:-start}" in

  start|-d|--detach)
    # Check if already running
    if sg docker -c "docker ps -q -f name=$CONTAINER_NAME" 2>/dev/null | grep -q .; then
        echo "Container $CONTAINER_NAME is already running."
        echo "Use '$0 stop' to stop it first, or '$0 logs' to see output."
        exit 1
    fi

    # Check secrets file — must be a regular file (Docker creates a directory
    # if the source path doesn't exist at container creation time, which then
    # blocks the bind mount forever — so we catch directory mistakes early)
    if [ ! -f "$SECRETS_FILE" ]; then
        if [ -d "$SECRETS_FILE" ]; then
            echo "ERROR: $SECRETS_FILE is a directory, not a file."
            echo "This happens if Docker created it as a directory on a previous run."
            echo "Fix: rm -rf $SECRETS_FILE && create it as a file."
        else
            echo "ERROR: $SECRETS_FILE not found."
            echo "Create it with:"
            echo "  echo 'DEEPSEEK_API_KEY=sk-...' > $SECRETS_FILE"
            echo "  echo 'OPENROUTER_API_KEY=sk-or-...' >> $SECRETS_FILE"
        fi
        exit 1
    fi

    # The source entrypoint.sh in the repo is authoritative; the baked image
    # may be stale. Volume-mount the correct version so fixes take effect
    # without a full image rebuild.
    ENTRYPOINT_SRC="$CIS_REPO/enforcement/mwl-proof-v2/entrypoint.sh"
    if [ -f "$ENTRYPOINT_SRC" ]; then
        ENTRYPOINT_MOUNT="-v $ENTRYPOINT_SRC:/opt/cis-control/entrypoint.sh:ro"
    else
        ENTRYPOINT_MOUNT=""
        echo "WARNING: $ENTRYPOINT_SRC not found — using baked entrypoint (may be stale)"
    fi

    # Same for profile configs — the baked image may have stale configs.
    # Volume-mount the authoritative profiles directory from the repo.
    PROFILES_SRC="$CIS_REPO/enforcement/mwl-proof-v2/profiles"
    if [ -d "$PROFILES_SRC" ]; then
        PROFILES_MOUNT="-v $PROFILES_SRC:/etc/hermes/profiles:ro"
    else
        PROFILES_MOUNT=""
        echo "WARNING: $PROFILES_SRC not found — using baked profile configs (may be stale)"
    fi

    DETACH_FLAG=""
    if [ "$1" = "-d" ] || [ "$1" = "--detach" ]; then
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
    # THE OVERRIDE PLANE (2026-09-03, queue item 0.4). .gate-control is mounted
    # read-only at /opt/cis-control/gate, and the plugin checks
    # /opt/cis-control/gate/DISABLED as its first action on every tool call.
    # `touch .gate-control/DISABLED` on the host turns the wall off with no
    # restart; removing it turns the wall back on. Read-only means the agents
    # can read that file and can never create it — an override the constrained
    # agent can set is a self-disable, not an override. See .gate-control/README.md.
    echo "Starting $CONTAINER_NAME from image $IMAGE..."

    # Remove old stopped container if exists
    sg docker -c "docker rm -f $CONTAINER_NAME" 2>/dev/null || true

    sg docker -c "docker run $DETACH_FLAG \
        --name $CONTAINER_NAME \
        -p 5000:5000 \
        -v $CIS_REPO:/workspace/cis \
        -v cis-claude-creds:/home/worker/.claude \
        -v /mnt/projects/swa-app:/workspace/swa-app:rw \
        -v /mnt/projects/swa:/workspace/swa:rw \
        -v /mnt/projects/secure-note-app:/workspace/swa-repos/secure-note-app:ro \
        -v /mnt/projects/hippa-case-management:/workspace/swa-repos/hippa-case-management:ro \
        -v /mnt/projects/cis-v1:/workspace/swa-repos/cis-v1:ro \
        -v $SECRETS_FILE:/workspace/secrets.env:ro \
        -v $CIS_REPO/.gate-control:/opt/cis-control/gate:ro \
        -v /mnt/models/huggingface:/opt/models/huggingface:ro \
        -v cis-agent-brain:/home/worker/.hermes-brain \
        -v cis-agent-draft:/home/worker/.hermes-draft \
        -v cis-agent-review1:/home/worker/.hermes-review1 \
        -v cis-agent-review2:/home/worker/.hermes-review2 \
        -v cis-agent-menter:/home/worker/.hermes-menter \
        -v cis-agent-verify:/home/worker/.hermes-verify \
        -v $CIS_REPO/enforcement/mwl-proof-v2/plugin:/home/worker/.hermes-brain/plugins/mwl-proof:ro \
        -v $CIS_REPO/enforcement/mwl-proof-v2/plugin:/home/worker/.hermes-draft/plugins/mwl-proof:ro \
        -v $CIS_REPO/enforcement/mwl-proof-v2/plugin:/home/worker/.hermes-review1/plugins/mwl-proof:ro \
        -v $CIS_REPO/enforcement/mwl-proof-v2/plugin:/home/worker/.hermes-review2/plugins/mwl-proof:ro \
        -v $CIS_REPO/enforcement/mwl-proof-v2/plugin:/home/worker/.hermes-menter/plugins/mwl-proof:ro \
        -v $CIS_REPO/enforcement/mwl-proof-v2/plugin:/home/worker/.hermes-verify/plugins/mwl-proof:ro \
        $ENTRYPOINT_MOUNT \
        $PROFILES_MOUNT \
        -e CIS_BRAIN_API_KEY=cis-brainstorm-gateway-key-2026 \
        -e CIS_DRAFT_API_KEY=cis-drafter-gateway-key-2026 \
        -e CIS_REVIEW1_API_KEY=cis-qwen-reviewer-gateway-key-2026 \
        -e CIS_REVIEW2_API_KEY=cis-glm-reviewer-gateway-key-2026 \
        -e CIS_MENTER_API_KEY=cis-implementer-gateway-key-2026 \
        -e CIS_VERIFY_API_KEY=cis-verifier-gateway-key-2026 \
        -e CIS_TG_BRAIN_TOKEN \
        -e CIS_TG_DRAFT_TOKEN \
        -e CIS_TG_REVIEW1_TOKEN \
        -e CIS_TG_REVIEW2_TOKEN \
        -e CIS_TG_MENTER_TOKEN \
        -e CIS_TG_VERIFY_TOKEN \
        -e CIS_TG_HOME_CHANNEL \
        --restart unless-stopped \
        $IMAGE"

    if [ -n "$DETACH_FLAG" ]; then
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
    echo "Usage: $0 {start|-d|stop|logs|exec}"
    exit 1
    ;;
esac
