#!/usr/bin/env bash
# advisor_review.sh — send a review packet to the borrowed advisor (review2, 8647)
# and write its reply back into the repo.
#
# The advisor has no tools. It reasons only from what the packet hands it.
# That is the point: an agent that cannot search cannot report that something
# is absent when it simply could not reach it (UNIFIED_BUILD_LIST 2.7, the
# absence-from-outside-scope variant, observed 2026-09-02).
#
# Usage:  bash tools/advisor_review.sh <id>
#         reads   reviews/pending/<id>.md
#         writes  reviews/done/<id>.response.md
#
# DEV MODE 2026-09-02: this depends on review2 being stripped for advisor use.
# When review2 is restored as a pipeline reviewer, this script stops being the
# right way to reach it.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${CIS_CONTAINER:-cis-pipeline}"
PROFILE="${CIS_ADVISOR_PROFILE:-review2}"
PORT="${CIS_ADVISOR_PORT:-8647}"
TIMEOUT="${CIS_ADVISOR_TIMEOUT:-560}"
MAX_TOKENS="${CIS_ADVISOR_MAX_TOKENS:-2000}"

SCOPE_LINE='You are reviewing a result packet. You have no file access and no tools. Everything you need is in this message. If something you would need is not here, say what is missing — never report that it does not exist.'

if [[ $# -ne 1 ]]; then
    echo "usage: bash tools/advisor_review.sh <id>" >&2
    echo "       expects reviews/pending/<id>.md" >&2
    exit 2
fi

ID="$1"
PACKET="$REPO_ROOT/reviews/pending/$ID.md"
OUTDIR="$REPO_ROOT/reviews/done"
OUT="$OUTDIR/$ID.response.md"

if [[ ! -f "$PACKET" ]]; then
    echo "no packet at $PACKET" >&2
    exit 1
fi

mkdir -p "$OUTDIR"

# Build the request body. Python does the JSON quoting so packet content can
# contain quotes, backslashes and newlines without breaking the payload.
# RUN_TAG makes every call unique. Without it the gateway serves an identical
# prompt from its OpenRouter response cache: the reply looks fresh, arrives in
# 0.4s, and reports usage as 0 — so a re-review of a CHANGED packet could be
# answered by a stale cached review, and the recorded cost would be zero.
RUN_TAG="$ID @ $(date -Iseconds)"

BODY="$(SCOPE_LINE="$SCOPE_LINE" MAX_TOKENS="$MAX_TOKENS" RUN_TAG="$RUN_TAG" python3 - "$PACKET" <<'PY'
import json, os, sys
packet = open(sys.argv[1], encoding="utf-8").read()
prompt = (
    os.environ["SCOPE_LINE"]
    + "\n\n(Review run: " + os.environ["RUN_TAG"] + ")\n\n"
    + packet
)
print(json.dumps({
    "model": "agent",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": int(os.environ["MAX_TOKENS"]),
}))
PY
)"

# The gateway listens on the container's loopback only, so the call is made
# from inside the container. The key never appears in the command line.
# The remote script is passed as an argument, not a heredoc: a heredoc would
# take over stdin and the payload piped in below would never arrive.
REMOTE_SH='
set -eu
profile="$1"; port="$2"; timeout="$3"
cat > /tmp/advisor_payload.json
key=$(grep "^API_SERVER_KEY=" "/home/worker/.hermes-$profile/.env" | cut -d= -f2- | tr -d "\r\n \"")
curl -s -m "$timeout" -X POST "http://127.0.0.1:$port/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $key" \
    --data-binary @/tmp/advisor_payload.json
rm -f /tmp/advisor_payload.json
'

RESP="$(printf '%s' "$BODY" | docker exec -i -u worker "$CONTAINER" \
    sh -c "$REMOTE_SH" -- "$PROFILE" "$PORT" "$TIMEOUT")"

# Split the reply out of the response and record the token cost alongside it,
# so the cost of a review is in the artifact rather than in someone's memory.
# The response goes to a temp FILE, not a pipe: `python3 -` takes its program
# from stdin, so a heredoc program and piped data cannot coexist — the pipe is
# silently discarded and sys.stdin.read() returns empty.
RESP_TMP="$(mktemp)"
LOG_TMP="$(mktemp)"
trap 'rm -f "$RESP_TMP" "$LOG_TMP"' EXIT
printf '%s' "$RESP" > "$RESP_TMP"

ID="$ID" PROFILE="$PROFILE" PORT="$PORT" RUN_TAG="$RUN_TAG" \
    python3 - "$OUT" "$PACKET" "$RESP_TMP" "$LOG_TMP" <<'PY'
import json, os, sys, datetime

out_path, packet_path, resp_path, log_path = sys.argv[1:5]
raw = open(resp_path, encoding="utf-8").read()

try:
    data = json.loads(raw)
except json.JSONDecodeError:
    sys.stderr.write("gateway did not return JSON:\n" + raw[:2000] + "\n")
    sys.exit(1)

if "choices" not in data or not data["choices"]:
    sys.stderr.write("gateway returned no choices:\n" + raw[:2000] + "\n")
    sys.exit(1)

msg = data["choices"][0].get("message", {})
content = (msg.get("content") or msg.get("reasoning_content") or "").strip()
usage = data.get("usage", {})
pt = usage.get("prompt_tokens", 0)
ct = usage.get("completion_tokens", 0)
tt = usage.get("total_tokens", 0)

# Zeros mean the reply came from the gateway's response cache despite the run
# tag. Say so rather than recording 0 as the cost of a review.
source = "gateway response usage"
if pt == 0 and ct == 0:
    source = ("gateway reported 0 — the reply was served from its response "
              "cache, so this is not a fresh measurement")
turns = "1 (single-turn: the advisor has no tools, so there is nothing to iterate on)"

with open(out_path, "w", encoding="utf-8") as f:
    f.write(f"# Advisor review — {os.environ['ID']}\n\n")
    f.write(f"- packet: `{os.path.relpath(packet_path)}`\n")
    f.write(f"- advisor: {os.environ['PROFILE']} on port {os.environ['PORT']}, no tools\n")
    f.write(f"- run tag: {os.environ['RUN_TAG']}\n")
    f.write(f"- at: {datetime.datetime.now().isoformat(timespec='seconds')}\n")
    f.write(f"- prompt_tokens: {pt}\n")
    f.write(f"- completion_tokens: {ct}\n")
    f.write(f"- total_tokens: {tt}\n")
    f.write(f"- token source: {source}\n")
    f.write(f"- model turns: {turns}\n")
    f.write(f"- finish_reason: {data['choices'][0].get('finish_reason')}\n\n")
    f.write("---\n\n")
    f.write(content + "\n")

print(f"wrote {out_path}")
print(f"prompt_tokens={pt} completion_tokens={ct} total_tokens={tt}")
print(f"token source: {source}")
PY
