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
# Mechanism already proven (enforcement/mwl-proof-v2/RESULTS/s14_evidence_20260912.md):
#   a read-only mount rejects every write ("Read-only file system").
#
# Usage:
#   ./run_claude_sandbox.sh "your prompt / card text here"
#   ./run_claude_sandbox.sh --run-id <id> --card-scope '<json>' "<prompt>"
#
# Output lands in /mnt/cache/catalog/claude-output/<run_id>/ (single writable dir).
#
# COMPLETION HOOK (R2): when --run-id is given, this script invokes
# tools/pipeline/menter_closeout.py after the sandbox exits (success OR failure)
# so the pipeline records MENTER_COMPLETE + evidence and dispatches reviewers.

set -uo pipefail

IMAGE="cis-hermes:pipeline"
REPO="/mnt/projects/cis"
OUTPUT_ROOT="/mnt/cache/catalog/claude-output"
RUN_ID="$(date -u +%Y%m%d_%H%M%S)"
OUTDIR="$OUTPUT_ROOT/$RUN_ID"
SECRETS_FILE="$REPO/secrets.env"

# ── Parse optional flags; the prompt is the positional ─────────────────
RUN_ID_ARG=""
CARD_SCOPE_ARG=""
PROMPT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID_ARG="$2"; shift 2 ;;
    --card-scope) CARD_SCOPE_ARG="$2"; shift 2 ;;
    *) PROMPT="$1"; shift ;;
  esac
done

if [[ -z "$PROMPT" ]]; then
  echo "usage: $0 [--run-id <id> --card-scope '<json>'] '<prompt>'" >&2
  exit 1
fi

# Load the Claude Code OAuth token from the gitignored secrets file.
CLAUDE_CODE_OAUTH_TOKEN="$(grep '^CLAUDE_CODE_OAUTH_TOKEN=' "$SECRETS_FILE" | head -1 | cut -d= -f2-)"
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
  echo "ERROR: CLAUDE_CODE_OAUTH_TOKEN not found in $SECRETS_FILE" >&2
  exit 1
fi

mkdir -p "$OUTDIR"

# ── Restore .claude.json if missing (config persistence fix) ───────────
# The creds volume persists /home/worker/.claude (a directory), but Claude Code
# reads its config from /home/worker/.claude.json (a FILE in the home dir).
# That file is outside the volume and is lost on every --rm run. The CLI keeps
# backups inside the persisted dir; restore the newest one so the config survives.
RESTORE_CMD='
if [ ! -f /home/worker/.claude.json ]; then
  latest=$(ls -t /home/worker/.claude/backups/.claude.json.backup.* 2>/dev/null | head -1)
  if [ -n "$latest" ]; then
    cp "$latest" /home/worker/.claude.json
    echo "[sandbox] restored /home/worker/.claude.json from $latest"
  fi
fi
claude -p "$1" --allowedTools "Read,Write,Bash(grep:*),Bash(find:*),Bash(cat:*),Bash(ls:*),Bash(wc:*),Bash(head:*),Bash(tail:*),Bash(sqlite3:*),Bash(git:*),Bash(python3:*),Bash(py_compile:*),Bash(diff:*),Bash(patch:*),Bash(cp:*),Bash(mkdir:*),Bash(chmod:*),Bash(echo:*),Bash(printf:*)" --output-format text
'

# --entrypoint sh: override the image CMD (which launches 8 gateways + API and
# waits) to run claude directly as a one-shot coder run.
docker run --rm \
  --entrypoint sh \
  -e CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN" \
  -v "$REPO":/workspace/cis:ro \
  -v "$OUTDIR":/workspace/output:rw \
  -v cis-claude-creds:/home/worker/.claude \
  -w /workspace/output \
  "$IMAGE" \
  -c "$RESTORE_CMD" _ "$PROMPT"
DOCKER_EXIT=$?

echo ""
echo "docker run exit code: $DOCKER_EXIT"
echo "output dir: $OUTDIR"

# ── Completion hook (R2) ───────────────────────────────────────────────
# Fire menter_closeout.py regardless of exit code, so a failed build still
# records evidence and returns the run to the reviewers/revision path.
if [[ -n "$RUN_ID_ARG" ]]; then
  echo "[sandbox] firing completion hook: menter_closeout.py --run-id $RUN_ID_ARG"
  python3 "$REPO/tools/pipeline/menter_closeout.py" \
    --run-id "$RUN_ID_ARG" \
    --output-dir "$OUTDIR" \
    --exit-code "$DOCKER_EXIT" || {
      echo "[sandbox] WARNING: menter_closeout.py failed (see above)"
    }
fi

exit "$DOCKER_EXIT"
