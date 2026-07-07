#!/bin/bash
# CIS Profile Container Harness
# Launches all 6 pipeline profile containers based on cis-hermes:pinned image.
# Uses sg docker (Eric group access). Run from: /mnt/projects/cis/enforcement/
set -e

IMAGE="cis-hermes:pinned"
BASE="/mnt/projects/cis/enforcement/profiles"
WORKSPACE_BASE="/mnt/cache/catalog"

# Profile definitions: name, container name
PROFILES=(
  "brainstorm cis-brainstorm"
  "drafter cis-drafter"
  "qwen-reviewer cis-qwen-reviewer"
  "glm-reviewer cis-glm-reviewer"
  "implementer cis-implementer"
  "verifier cis-verifier"
)

echo "=== CIS Profile Container Launcher ==="
echo "Image: $IMAGE"
echo ""

# Get worker UID from any running container or default
WORKER_UID=$(sg docker -c "timeout 5 docker run --rm $IMAGE id -u worker" 2>/dev/null || echo "1001")
echo "Worker UID: $WORKER_UID"

for entry in "${PROFILES[@]}"; do
  read -r name container <<< "$entry"
  
  CONFIG_FILE="$BASE/$name/config.yaml"
  ENV_SOURCE="$BASE/$name/.env"
  WORKSPACE="$WORKSPACE_BASE/cis-$name"
  STATE_VOLUME="cis-${name}-state"
  
  echo ""
  echo "--- $container ($name) ---"
  
  # Ensure workspace exists
  mkdir -p "$WORKSPACE"
  
  # Seed .env into the state volume if not already present
  # (state volumes persist across container rebuilds)
  ENV_EXISTS=$(sg docker -c "docker run --rm -v $STATE_VOLUME:/state alpine:latest sh -c 'test -f /state/.env && echo yes || echo no'" 2>/dev/null)
  if [ "$ENV_EXISTS" = "no" ]; then
    echo "  Seeding .env into volume..."
    sg docker -c "docker run --rm \
      -v $ENV_SOURCE:/seed/.env:ro \
      -v $STATE_VOLUME:/state \
      alpine:latest sh -c 'cp /seed/.env /state/.env && chown ${WORKER_UID}:${WORKER_UID} /state/.env && chmod 600 /state/.env'" 2>/dev/null
  else
    echo "  .env already in volume (preserved)"
  fi
  
  # Remove old container, ignore if not exists
  sg docker -c "docker rm -f $container" 2>/dev/null || true
  
  # Launch container
  sg docker -c "docker run -d \
    --name $container \
    --add-host=host.docker.internal:host-gateway \
    -v $CONFIG_FILE:/etc/hermes/config.yaml:ro \
    -v $STATE_VOLUME:/home/worker/.hermes \
    -v /mnt/projects/cis:/source/cis:ro \
    -v /mnt/archive:/source/archive:ro \
    -v /mnt/projects/swa:/source/swa:ro \
    -v $WORKSPACE:/workspace \
    $IMAGE sleep infinity"
  
  echo "  ✓ Launched ($(sg docker -c "docker inspect -f '{{.Id}}' $container" 2>/dev/null | cut -c1-12))"
done

echo ""
echo "=== All profile containers running ==="
sg docker -c "docker ps --filter 'name=cis-' --format 'table {{.Names}}\t{{.Status}}'"
echo ""
echo "=== Enforcement walls active on all profiles ==="
echo "  1. Kernel RO mounts: /source/cis, /source/swa, /source/archive"
echo "  2. Managed config scope: model, plugins, tool_loop_guardrails locked"
echo "  3. Plugin immutability: mwl-proof plugin root-owned, chmod/chown blocked"
echo ""
echo "Verification: sg docker -c 'docker exec <container> hermes doctor'"
