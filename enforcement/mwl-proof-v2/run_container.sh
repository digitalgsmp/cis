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
#   - /tmp/cis-secrets.env with DEEPSEEK_API_KEY and OPENROUTER_API_KEY
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
SECRETS_FILE="/tmp/cis-secrets.env"

case "${1:-start}" in

  start|-d|--detach)
    # Check if already running
    if sg docker -c "docker ps -q -f name=$CONTAINER_NAME" 2>/dev/null | grep -q .; then
        echo "Container $CONTAINER_NAME is already running."
        echo "Use '$0 stop' to stop it first, or '$0 logs' to see output."
        exit 1
    fi

    # Check secrets file
    if [ ! -f "$SECRETS_FILE" ]; then
        echo "ERROR: $SECRETS_FILE not found."
        echo "Create it with:"
        echo "  echo 'DEEPSEEK_API_KEY=sk-...' > $SECRETS_FILE"
        echo "  echo 'OPENROUTER_API_KEY=sk-or-...' >> $SECRETS_FILE"
        exit 1
    fi

    DETACH_FLAG=""
    if [ "$1" = "-d" ] || [ "$1" = "--detach" ]; then
        DETACH_FLAG="-d"
    fi

    echo "Starting $CONTAINER_NAME from image $IMAGE..."

    # Remove old stopped container if exists
    sg docker -c "docker rm -f $CONTAINER_NAME" 2>/dev/null || true

    sg docker -c "docker run $DETACH_FLAG \
        --name $CONTAINER_NAME \
        -p 5000:5000 \
        -v $CIS_REPO:/workspace/cis \
        -v $SECRETS_FILE:/workspace/secrets.env:ro \
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
