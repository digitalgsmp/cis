#!/bin/bash
set -e

IMAGE="cis-hermes:pinned"
CONTAINER="cis-hermes"

echo "=== Rebuilding image (if Dockerfile changed) ==="
sudo docker build -t "$IMAGE" -f Dockerfile .

echo "=== Removing old container (if exists) ==="
sudo docker rm -f "$CONTAINER" 2>/dev/null || true

echo "=== Launching sealed worker ==="
sudo docker run -d \
  --name "$CONTAINER" \
  --add-host=host.docker.internal:host-gateway \
  -v /mnt/projects/cis:/source/cis:ro \
  -v /mnt/archive:/source/archive:ro \
  -v /mnt/projects/swa:/source/swa:ro \
  -v /opt/cis-control:/cis-control:ro \
  -v /mnt/cache/catalog/cis-hermes:/workspace \
  -v cis-hermes-state:/home/worker/.hermes \
  "$IMAGE" sleep infinity

echo "=== Container started: $CONTAINER ==="
sudo docker ps --filter "name=$CONTAINER"
