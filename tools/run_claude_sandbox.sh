#!/bin/bash
# run_claude_sandbox.sh — run Claude Code (the coder) in a KERNEL sandbox.
#
# The repo is mounted READ-ONLY; the ONLY writable location is a per-run output
# dir. Claude Code runs headless (claude -p) as the non-root worker (uid 1000,
# the image default — no --user flag needed, Dockerfile line 186).
#
# Why this exists: the Hermes-side enforcement (sealed plugin, shell-hook
# consent, managed config) is baked into the image and constrains the Hermes
# gateway agents — but Claude Code is invoked headless and is NOT a Hermes
# agent, so none of that reaches it. The coder's only real wall is the kernel:
# a read-only repo mount. `--allowedTools` is a secondary policy layer.
#
# Research (Dockerfile + run_fable.sh, 2026-09-12):
#   - claude CLI is baked: Dockerfile line 35 (npm install -g @anthropic-ai/claude-code)
#   - image default user is worker/uid 1000: lines 125-127, 186
#   - proven headless invocation: run_fable.sh (claude -p ... --allowedTools ... --output-format text)
#   - creds volume: cis-claude-creds -> /home/worker/.claude (run_container.sh line 117)
#   - auth: long-lived OAuth token via CLAUDE_CODE_OAUTH_TOKEN (claude setup-token),
#     stored in secrets.env (gitignored).
#
# Mechanism already proven (enforcement/mwl-proof-v2/RESULTS/s14_evidence_20260912.md):
#   a read-only mount rejects every write ("Read-only file system").
#
# Usage:
#   ./run_claude_sandbox.sh "your prompt / card text here"
#
# Output lands in /mnt/cache/catalog/claude-output/<run_id>/ (single writable dir).

set -euo pipefail

IMAGE="cis-hermes:pipeline"
REPO="/mnt/projects/cis"
OUTPUT_ROOT="/mnt/cache/catalog/claude-output"
RUN_ID="$(date -u +%Y%m%d_%H%M%S)"
OUTDIR="$OUTPUT_ROOT/$RUN_ID"
SECRETS_FILE="$REPO/secrets.env"

PROMPT="${1:?usage: $0 '<prompt>'}"

# Load the Claude Code OAuth token from the gitignored secrets file.
CLAUDE_CODE_OAUTH_TOKEN="$(grep '^CLAUDE_CODE_OAUTH_TOKEN=' "$SECRETS_FILE" | head -1 | cut -d= -f2-)"
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
  echo "ERROR: CLAUDE_CODE_OAUTH_TOKEN not found in $SECRETS_FILE" >&2
  exit 1
fi

mkdir -p "$OUTDIR"

# --entrypoint sh: the image CMD is /opt/cis-control/entrypoint.sh (launches all
# 8 gateways + pipeline API and waits). We do NOT want that for a one-shot
# sandboxed coder run — override the entrypoint to run claude directly.
docker run --rm \
  --entrypoint sh \
  -e CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN" \
  -v "$REPO":/workspace/cis:ro \
  -v "$OUTDIR":/workspace/output:rw \
  -v cis-claude-creds:/home/worker/.claude \
  -w /workspace/output \
  "$IMAGE" \
  -c 'claude -p "$1" --allowedTools "Read,Write,Bash(grep:*),Bash(find:*),Bash(cat:*),Bash(ls:*),Bash(wc:*),Bash(head:*),Bash(tail:*),Bash(sqlite3:*),Bash(git:*)" --output-format text' _ "$PROMPT"

echo ""
echo "output dir: $OUTDIR"
