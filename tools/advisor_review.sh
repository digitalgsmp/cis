#!/usr/bin/env bash
# advisor_review.sh — send a review packet to the advisor (advisor, 8649)
# and write its reply back into the repo.
#
# The advisor has no tools. It reasons only from what the packet hands it.
# That is the point: an agent that cannot search cannot report that something
# is absent when it simply could not reach it (UNIFIED_BUILD_LIST 2.7, the
# absence-from-outside-scope variant, observed 2026-09-02).
#
# Usage:  bash tools/advisor_review.sh <id>                  # round 1: review
#         bash tools/advisor_review.sh <id> --reply <file>   # round 2: answer it
#         bash tools/advisor_review.sh <id> --result <file>  # round 3: result review
#         bash tools/advisor_review.sh <id> --pause <stop>   # halt the loop here
#         bash tools/advisor_review.sh <id> --continue       # release the halt
#         bash tools/advisor_review.sh <id> --supersede      # card replaced, not approved
#         reads   reviews/pending/<id>.md
#         writes  reviews/done/<id>.<profile>.response.md   (round 1)
#                 reviews/done/<id>.<profile>.reply.md      (round 2)
#                 reviews/done/<id>.<profile>.result.md     (round 3)
#         records each round in deliberation_rounds as
#         run_id advisor-<id>-<profile>, and each pause as
#         run_id advisor-<id>-pause
#
# DUAL LINEAGE IS THE DEFAULT (BUILD LIST 1.20). One invocation sends the
# SAME packet to GLM (advisor, 8649) and Qwen (evaluator, 8650). The packet is
# built once and hashed once, so both reviews are provably of one artifact --
# without that, 'the two models disagreed' cannot be distinguished from 'the
# two models saw different things'.
#
# 1.20's measure is the count of findings only one lineage raised. Run
# 2026-09-07 on the 3.6 card: GLM 5, Qwen 2, and neither found the other's
# most serious. Set CIS_ADVISOR_PROFILE / CIS_ADVISOR_PORT to force one.
#
# run_id carries the profile because UNIQUE(run_id, round_number) would
# otherwise reject the second lineage's round 1, through the same IntegrityError
# now reported as a collision rather than as a cap.
#
# ROUNDS 2 AND 3 ARE BUILT PER LINEAGE. They used to be built once, outside the
# lineage loop, from a fixed path reviews/done/<id>.response.md. Dual lineage
# writes <id>.<profile>.response.md, so round 2 exited 1 before contacting
# anyone -- and had that path resolved, both lineages would have been handed the
# SAME lineage's objection to answer. Never caught because round 2 had only ever
# run with CIS_ADVISOR_PROFILE forcing one lineage. The packet is still read and
# hashed ONCE, outside the loop: what varies per lineage is only which prior
# objection it is being asked to answer.
#
# THE REPLY ROUND — BUILD LIST 1.19. Round 1 is a verdict nobody can answer,
# which is the failure 1.19 names: on 2026-09-02 the advisor reported three
# existing backups as missing, and one round with `ls` output would have
# retracted it. Round 2 hands the advisor its own objection plus evidence and
# asks it to WITHDRAW or HOLD.
#
# NO SCHEMA CHANGE. reviewer_signal stays inside its existing five values --
# HELD maps to OBJECTIONS, WITHDRAWN maps to CONSENSUS_REACHED -- so the four
# existing validators pass unchanged (database.py ALLOWED_SIGNALS,
# gate_review_round_valid.sh, gate_consensus_signal_valid.sh, the CHECK).
# The verdict itself lives in objections_json as an ARRAY OF OBJECTS, which is
# the shape build_briefing.py:355 already parses -- it reads item['objection']
# first. An array keeps every existing iterator working; a string-expecting
# reader fails loudly on a dict instead of silently rendering garbage.
#
# THERE IS NO TWO-ROUND CAP. This block used to claim one: "UNIQUE(run_id,
# round_number) -- a third call is refused by the database." That is false and
# was false when written. The constraint refuses a DUPLICATE round number for a
# run_id; it does not cap how many rounds a run may have. deliberation_rounds
# already holds round numbers up to 11 (57 rows at round 3), so round 3 needs no
# schema change and no workaround. The IntegrityError handler below said "cap
# reached" for what is actually a collision -- a wrong reason reported
# confidently, which is the failure this script exists to catch in others.
#
# ROUND 3 -- THE RESULT REVIEW, BUILD LIST 1.18's SECOND HALF. Rounds 1 and 2
# both review a PROPOSAL. Nothing has ever reviewed what the work actually
# produced. Round 3 sends the approved card plus the real command output and
# diff, and asks two questions: does this evidence establish what the card
# claimed, and what would look like success while still being wrong. Same
# packet, same hash discipline, both lineages.
#
# THE PAUSE -- BUILD LIST 1.21, minimum viable form. Three stops, at the points
# where UNDERSTANDING COULD HAVE DIVERGED rather than where a write could occur
# (the 2026-07-03 design record):
#     1  card-written    the card exists, before it goes to review
#     2  reviews-landed  the reviews are in, before anything executes
#     3  result-reviewed the result review is in, before the next queue item
# Stop 2 and stop 3 are set by this script when those rounds complete. Stop 1 is
# set by whatever wrote the card, with --pause card-written. Every gateway call
# refuses to run while a pause is unresolved, so no path reaches an advisor
# without an explicit --continue. No timeout, no default-continue.
#
# THE WAITING STATE IS A ROW, NOT A BLOCKED PROCESS. A script that blocks on
# read dies with its terminal and takes the loop's position with it; a row
# survives a restart and can be read from the spine by something that was not
# running when the pause was set. That is 1.21's own check. The row is a
# deliberation_rounds row with reviewer_signal='PENDING' under run_id
# advisor-<id>-pause -- PENDING is already in the CHECK constraint, so this adds
# no schema. Releasing it sets CONSENSUS_REACHED; that value means "released
# here", and the pause's own record of what it was waiting for stays in
# objections_json.
#
# run_id is advisor-<id>, deliberately NOT a pipeline run. Every reader of
# deliberation_rounds is scoped WHERE run_id = ?, so an advisor thread cannot
# surface in the Eric Gate briefing for a real run.
#
# REPOINTED 2026-09-07. This no longer borrows a pipeline reviewer.
#
# It used to target review2 on 8647, which only worked while review2 was
# stripped for advisor use. That strip lived in a Docker volume, and the
# 2026-09-04 rebuild overwrote it from the repo profile — review2 became a
# full pipeline reviewer again and nobody was told. This script would have
# gone on sending review packets to it at ~15,900 prompt tokens a call, with
# the three cis_dispatch_* tools in its loadout (2.23).
#
# The advisor is now its own profile: enforcement/mwl-proof-v2/profiles/advisor.yaml,
# port 8649, permanently stripped BY DESIGN rather than by dev mode — 79 skills
# disabled, platform_toolsets empty, cis-knowledge off. Measured 2026-09-07:
# 396 prompt tokens against review2's 15,848.
#
# The gateway key is read from the profile's own .env at line ~79, so changing
# CIS_ADVISOR_PROFILE carries the key with it. Do not hardcode a key here.
#
# NOTE — 8647 means two different agents depending on where you are. Inside the
# container it is review2; on the HOST it is the VM's hermes-gateway-glm-reviewer
# service, which is also on 8647 and answers 200. This script uses docker exec,
# so it always means the container. A curl from the host does not.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${CIS_CONTAINER:-cis-pipeline}"
# Default: both lineages. An explicit override forces one.
if [[ -n "${CIS_ADVISOR_PROFILE:-}" || -n "${CIS_ADVISOR_PORT:-}" ]]; then
    LINEAGES=("${CIS_ADVISOR_PROFILE:-advisor}:${CIS_ADVISOR_PORT:-8649}")
else
    LINEAGES=("advisor:8649" "evaluator:8650")
fi
TIMEOUT="${CIS_ADVISOR_TIMEOUT:-560}"
MAX_TOKENS="${CIS_ADVISOR_MAX_TOKENS:-2000}"

# This said "You are reviewing a result packet" until 2026-09-08, while every
# packet it had ever been sent was a proposal. Both lineages were told they were
# looking at a result and were looking at a design. Round 3 is where the word
# result now belongs.
SCOPE_LINE='You are reviewing a proposal packet — work that has NOT been done yet. You have no file access and no tools. Everything you need is in this message. If something you would need is not here, say what is missing — never report that it does not exist.'

RESULT_LINE='You are reviewing the RESULT of work that has ALREADY been executed. Below is the card that was approved, then the actual command output and diff produced when it ran. You have no file access and no tools; everything is in this message. Answer two questions: does this evidence establish what the card claimed, and what would look like success while still being wrong? Begin your reply with exactly one line reading VERDICT: ESTABLISHED or VERDICT: NOT_ESTABLISHED, then your reasoning. If the evidence is not enough to decide, answer NOT_ESTABLISHED and say what is missing — never treat what you cannot see as absent.'

REPLY_FILE=""
RESULT_FILE=""
MODE="review"
PAUSE_STOP=""
if [[ $# -eq 1 ]]; then
    :
elif [[ $# -eq 2 && "$2" == "--continue" ]]; then
    MODE="continue"
elif [[ $# -eq 2 && "$2" == "--supersede" ]]; then
    MODE="supersede"
elif [[ $# -eq 3 && "$2" == "--reply" ]]; then
    REPLY_FILE="$3"
    [[ -f "$REPLY_FILE" ]] || { echo "no evidence file at $REPLY_FILE" >&2; exit 1; }
elif [[ $# -eq 3 && "$2" == "--result" ]]; then
    RESULT_FILE="$3"
    [[ -f "$RESULT_FILE" ]] || { echo "no evidence file at $RESULT_FILE" >&2; exit 1; }
elif [[ $# -eq 3 && "$2" == "--pause" ]]; then
    MODE="pause"
    PAUSE_STOP="$3"
    case "$PAUSE_STOP" in
        card-written|reviews-landed|result-reviewed) ;;
        *) echo "unknown stop: $PAUSE_STOP" >&2
           echo "stops are: card-written, reviews-landed, result-reviewed" >&2
           exit 2 ;;
    esac
else
    echo "usage: bash tools/advisor_review.sh <id>" >&2
    echo "       bash tools/advisor_review.sh <id> --reply  <evidence-file>" >&2
    echo "       bash tools/advisor_review.sh <id> --result <evidence-file>" >&2
    echo "       bash tools/advisor_review.sh <id> --pause  <card-written|reviews-landed|result-reviewed>" >&2
    echo "       bash tools/advisor_review.sh <id> --continue" >&2
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

# ---------------------------------------------------------------- THE PAUSE --
# check  : exit 3 if an unresolved pause exists for this id, printing it
# set    : record a pause; a second set while one is open is a no-op
# release: resolve the newest open pause
# Round numbers increase monotonically per id, so re-pausing at the same stop
# cannot collide with UNIQUE(run_id, round_number).
pause_state() {
    ID="$ID" python3 - "$@" <<'PY'
import json, os, sqlite3, sys, datetime

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
RUN = "advisor-" + os.environ["ID"] + "-pause"
mode = sys.argv[1]
now = datetime.datetime.now(datetime.timezone.utc).isoformat()

conn = sqlite3.connect(DB)
open_row = conn.execute(
    "SELECT round_number, objections_json FROM deliberation_rounds "
    "WHERE run_id=? AND reviewer_signal='PENDING' "
    "ORDER BY round_number DESC LIMIT 1", (RUN,)).fetchone()

def entry_of(row):
    try:
        return json.loads(row[1])[0]
    except Exception:
        return {}

if mode == "check":
    if open_row:
        e = entry_of(open_row)
        print("PAUSED at stop: " + e.get("stop", "?"))
        if e.get("what_next"):
            print(e["what_next"])
        sys.exit(3)
    sys.exit(0)

if mode == "set":
    stop = sys.argv[2]
    what = sys.argv[3] if len(sys.argv) > 3 else ""
    if open_row:
        e = entry_of(open_row)
        print("already paused at stop: " + e.get("stop", "?"))
        sys.exit(0)
    nxt = conn.execute(
        "SELECT COALESCE(MAX(round_number),0)+1 FROM deliberation_rounds "
        "WHERE run_id=?", (RUN,)).fetchone()[0]
    entry = {"stop": stop, "what_next": what, "paused_at": now}
    conn.execute(
        "INSERT INTO deliberation_rounds "
        "(run_id, round_number, drafter_role, drafter_output, reviewer_role, "
        " reviewer_signal, objections_json, revision_number, "
        " requires_eric_review, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (RUN, nxt, "claude_code", what, "pause", "PENDING",
         json.dumps([entry]), 1, 1, now))
    conn.commit()
    print("PAUSED at stop: " + stop)
    if what:
        print(what)
    sys.exit(0)

if mode in ("release", "supersede"):
    verb = "continue" if mode == "release" else "supersede"
    if not open_row:
        print("no open pause for this id — nothing to " + verb)
        sys.exit(0)
    e = entry_of(open_row)
    e["released_at"] = now
    # CONTINUED means the stop was read and the work proceeds. SUPERSEDED means
    # the card was replaced and the work never proceeded from here. Both leave
    # reviewer_signal='CONSENSUS_REACHED' because that column's CHECK allows only
    # five values and none of them means "abandoned" -- adding one is a schema
    # change. The distinction that matters therefore lives in `resolution`, and a
    # reader that only looks at reviewer_signal cannot tell an approved card from
    # a discarded one. Recorded here rather than papered over.
    e["resolution"] = "CONTINUED" if mode == "release" else "SUPERSEDED"
    conn.execute(
        "UPDATE deliberation_rounds SET reviewer_signal='CONSENSUS_REACHED', "
        "objections_json=? WHERE run_id=? AND round_number=?",
        (json.dumps([e]), RUN, open_row[0]))
    conn.commit()
    print(e["resolution"] + " from stop: " + e.get("stop", "?"))
    sys.exit(0)

sys.stderr.write("pause_state: unknown mode " + mode + "\n")
sys.exit(2)
PY
}

# BUILD LIST 2.25 — render the stop and DM it to Eric. Host-side HTTP POST, no
# agent on either end. A failed send must never fail the pause: the stop is
# already a row in the spine, so losing the message loses visibility, not state.
notify_stop() {
    python3 "$REPO_ROOT/tools/pause_notify.py" "$ID" "$1" || \
        echo "NOTE: pause is set; the Telegram notice did not send" >&2
}

if [[ "$MODE" == "pause" ]]; then
    case "$PAUSE_STOP" in
        card-written)    _WHAT="the card is written; next is round 1 review of $ID" ;;
        reviews-landed)  _WHAT="the reviews are in; next is executing $ID" ;;
        result-reviewed) _WHAT="the result review is in; next is the following queue item" ;;
    esac
    pause_state set "$PAUSE_STOP" "$_WHAT"
    notify_stop "$PAUSE_STOP"
    exit 0
fi

if [[ "$MODE" == "continue" ]]; then
    pause_state release
    exit 0
fi

if [[ "$MODE" == "supersede" ]]; then
    pause_state supersede
    exit 0
fi

# Every gateway call passes through here. A pause is not advisory.
if ! pause_state check; then
    echo "" >&2
    echo "refusing to proceed while paused. Read the stop above, then:" >&2
    echo "    bash tools/advisor_review.sh $ID --continue" >&2
    exit 3
fi

# Build the request body. Python does the JSON quoting so packet content can
# contain quotes, backslashes and newlines without breaking the payload.
# RUN_TAG makes every call unique. Without it the gateway serves an identical
# prompt from its OpenRouter response cache: the reply looks fresh, arrives in
# 0.4s, and reports usage as 0 — so a re-review of a CHANGED packet could be
# answered by a stale cached review, and the recorded cost would be zero.
RUN_TAG="$ID @ $(date -Iseconds)"

# The packet hash binds a reply to the exact packet version it answers. Round 2
# compares it against the hash stored in round 1 and records MISMATCH rather
# than silently accepting a reply to a packet that has since changed. This is
# the structural form of the 2.24 cache guard, borrowed from
# advisor_escalation_packets.packet_hash.
PACKET_HASH="$(sha256sum "$PACKET" | cut -c1-16)"

if [[ -n "$REPLY_FILE" ]]; then
    ROUND=2
    OUT="$OUTDIR/$ID.reply.md"
elif [[ -n "$RESULT_FILE" ]]; then
    ROUND=3
    OUT="$OUTDIR/$ID.result.md"
else
    ROUND=1
fi

REPLY_LINE='You previously reviewed this packet and raised the objection below. Claude Code has answered it with evidence. Decide: WITHDRAWN if the evidence resolves your objection, HELD if it does not. Begin your reply with exactly one line reading VERDICT: WITHDRAWN or VERDICT: HELD, then a short paragraph of reasoning. If the evidence is not enough to decide, HOLD and say what is missing — never treat what you cannot see as absent.'

# build_body <prior-file> — rounds 2 and 3 need the prior review from THEIR OWN
# lineage, so this is called inside the loop. The packet is the same file and
# the same hash for every lineage; only the prior differs.
build_body() {
    SCOPE_LINE="$SCOPE_LINE" REPLY_LINE="$REPLY_LINE" RESULT_LINE="$RESULT_LINE" \
    MAX_TOKENS="$MAX_TOKENS" RUN_TAG="$RUN_TAG" ROUND="$ROUND" PRIOR="$1" \
    python3 - "$PACKET" "${REPLY_FILE:-}${RESULT_FILE:-}" <<'PY'
import json, os, sys
packet = open(sys.argv[1], encoding="utf-8").read()
rnd = os.environ["ROUND"]

if rnd == "2":
    try:
        prior = open(os.environ["PRIOR"], encoding="utf-8").read()
    except OSError:
        sys.stderr.write("round 2 needs " + os.environ["PRIOR"] + " from round 1\n")
        sys.exit(1)
    evidence = open(sys.argv[2], encoding="utf-8").read()
    prompt = (
        os.environ["REPLY_LINE"]
        + "\n\n(Reply run: " + os.environ["RUN_TAG"] + ")\n\n"
        + "=== THE PACKET YOU REVIEWED ===\n" + packet
        + "\n\n=== YOUR OBJECTION ===\n" + prior
        + "\n\n=== CLAUDE CODE EVIDENCE ===\n" + evidence
    )
elif rnd == "3":
    # The prior review is included when it exists, so the lineage can see
    # whether the result answers what it originally objected to. It is not
    # required: a card may be executed without ever having been reviewed.
    try:
        prior = open(os.environ["PRIOR"], encoding="utf-8").read()
    except OSError:
        prior = "(this lineage did not review the proposal)"
    evidence = open(sys.argv[2], encoding="utf-8").read()
    prompt = (
        os.environ["RESULT_LINE"]
        + "\n\n(Result run: " + os.environ["RUN_TAG"] + ")\n\n"
        + "=== THE CARD THAT WAS APPROVED ===\n" + packet
        + "\n\n=== YOUR REVIEW OF IT, BEFORE IT RAN ===\n" + prior
        + "\n\n=== WHAT ACTUALLY HAPPENED — COMMAND OUTPUT AND DIFF ===\n" + evidence
    )
else:
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
}

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

# One call per lineage. A failure in one is reported and the other still
# records -- a half-review that says so beats a silent single review.
FAILED=0
for _lin in "${LINEAGES[@]}"; do
PROFILE="${_lin%%:*}"
PORT="${_lin##*:}"
if [[ ${#LINEAGES[@]} -gt 1 ]]; then
    OUT="$OUTDIR/$ID.$PROFILE.response.md"
    [[ -n "$REPLY_FILE" ]]  && OUT="$OUTDIR/$ID.$PROFILE.reply.md"
    [[ -n "$RESULT_FILE" ]] && OUT="$OUTDIR/$ID.$PROFILE.result.md"
    PRIOR_FILE="$OUTDIR/$ID.$PROFILE.response.md"
else
    PRIOR_FILE="$OUTDIR/$ID.response.md"
fi
echo "--- lineage: $PROFILE on $PORT ---"

BODY="$(build_body "$PRIOR_FILE")" || {
    echo "FAILED: $PROFILE — could not build the request body" >&2
    FAILED=$((FAILED+1)); continue; }

RESP="$(printf '%s' "$BODY" | docker exec -i -u worker "$CONTAINER" \
    sh -c "$REMOTE_SH" -- "$PROFILE" "$PORT" "$TIMEOUT")" || {
    echo "FAILED: $PROFILE on $PORT did not answer — other lineages continue" >&2
    FAILED=$((FAILED+1)); continue; }
if [[ -z "$RESP" ]]; then
    echo "FAILED: $PROFILE on $PORT returned an empty body" >&2
    FAILED=$((FAILED+1)); continue
fi

# CHECK THE PAYLOAD, NOT THE EXIT CODE. The gateway answers HTTP 200 with an
# error object in the body — BUILD LIST 1.11 recorded exactly this (a billing
# 402 delivered as a successful completion) and it happened again on 2026-09-07
# with {"error":{"code":"agent_incomplete"}} after four truncation retries.
# docker exec exits 0, RESP is non-empty, and the failure only surfaces inside
# the recorder, whose sys.exit(1) kills the whole script under `set -e` — so one
# lineage failing took the other down with it. Guarding the transport is not
# guarding the result.
ERR="$(printf '%s' "$RESP" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception as e:
    print("not JSON: " + str(e)[:120]); sys.exit(0)
if isinstance(d, dict) and d.get("error"):
    e = d["error"]
    print((e.get("code","") + ": " + e.get("message","")) if isinstance(e, dict) else str(e)[:200])
    sys.exit(0)
if not (isinstance(d, dict) and d.get("choices")):
    print("no choices in response"); sys.exit(0)
' 2>/dev/null || echo "response could not be parsed")"

if [[ -n "$ERR" ]]; then
    echo "FAILED: $PROFILE on $PORT — $ERR" >&2
    echo "        other lineages continue; this one recorded nothing" >&2
    FAILED=$((FAILED+1)); continue
fi

# Split the reply out of the response and record the token cost alongside it,
# so the cost of a review is in the artifact rather than in someone's memory.
# The response goes to a temp FILE, not a pipe: `python3 -` takes its program
# from stdin, so a heredoc program and piped data cannot coexist — the pipe is
# silently discarded and sys.stdin.read() returns empty.
RESP_TMP="$(mktemp)"
LOG_TMP="$(mktemp)"
printf '%s' "$RESP" > "$RESP_TMP"

ID="$ID" PROFILE="$PROFILE" PORT="$PORT" RUN_TAG="$RUN_TAG" \
    ROUND="$ROUND" PACKET_HASH="$PACKET_HASH" REPLY_FILE="${REPLY_FILE:-}" \
    RESULT_FILE="${RESULT_FILE:-}" \
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

# --- Record the turn in deliberation_rounds (BUILD LIST 1.19, 1.22) ---
# The thread is an ARRAY OF OBJECTS. build_briefing.py:355 pulls
# item["objection"] out of dicts, so this renders as prose, not raw JSON.
import sqlite3

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
run_id = "advisor-" + os.environ["ID"] + "-" + os.environ["PROFILE"]
rnd = int(os.environ["ROUND"])
reply_file = os.environ.get("REPLY_FILE") or os.environ.get("RESULT_FILE") or ""

verdict = ""
head = content.strip().splitlines()[0].upper() if content.strip() else ""
if rnd == 2:
    if "WITHDRAWN" in head:
        verdict = "WITHDRAWN"
    elif "HELD" in head:
        verdict = "HELD"
    else:
        verdict = "UNPARSED"
elif rnd == 3:
    # NOT_ESTABLISHED is tested first: it contains ESTABLISHED as a substring,
    # so testing the other way round reads every rejection as an acceptance.
    if "NOT_ESTABLISHED" in head or "NOT ESTABLISHED" in head:
        verdict = "NOT_ESTABLISHED"
    elif "ESTABLISHED" in head:
        verdict = "ESTABLISHED"
    else:
        verdict = "UNPARSED"

# HELD -> OBJECTIONS, WITHDRAWN -> CONSENSUS_REACHED, ESTABLISHED ->
# CONSENSUS_REACHED. Round 1 is always OBJECTIONS: it is a review awaiting an
# answer, and OBJECTIONS is what keeps it visible to
# check_escalation_required. UNPARSED holds rather than assumes.
signal = ("CONSENSUS_REACHED"
          if verdict in ("WITHDRAWN", "ESTABLISHED") else "OBJECTIONS")

sent_hash = os.environ["PACKET_HASH"]
hash_status = "MATCH"
if rnd in (2, 3):
    prior_hash = ""
    try:
        _c = sqlite3.connect(DB)
        _r = _c.execute("SELECT objections_json FROM deliberation_rounds "
                        "WHERE run_id=? AND round_number=1", (run_id,)).fetchone()
        _c.close()
        if _r and _r[0]:
            _p = json.loads(_r[0])
            if isinstance(_p, list) and _p and isinstance(_p[0], dict):
                prior_hash = _p[0].get("packet_hash", "")
    except Exception:
        pass
    if prior_hash and prior_hash != sent_hash:
        hash_status = "MISMATCH"

evidence_text = ""
if reply_file:
    try:
        evidence_text = open(reply_file, encoding="utf-8").read()[:4000]
    except OSError:
        pass

entry = {
    "objection": content[:4000],
    "evidence": evidence_text,
    "verdict": verdict,
    "packet_hash": sent_hash,
    "packet_hash_status": hash_status,
    "round": rnd,
    "run_tag": os.environ["RUN_TAG"],
    "prompt_tokens": pt,
}

try:
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO deliberation_rounds "
        "(run_id, round_number, drafter_role, drafter_output, "
        " reviewer_role, reviewer_signal, objections_json, "
        " revision_number, requires_eric_review, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (run_id, rnd, "claude_code", evidence_text,
         os.environ["PROFILE"], signal, json.dumps([entry]),
         1, 1, datetime.datetime.now(datetime.timezone.utc).isoformat()))
    conn.commit()
    conn.close()
    print(f"recorded: {run_id} round {rnd} signal={signal} "
          f"verdict={verdict or chr(45)} hash={hash_status}")
except sqlite3.IntegrityError:
    print(f"NOT recorded: {run_id} round {rnd} already exists — a duplicate "
          f"round number for this run_id, not a cap. Nothing limits how many "
          f"rounds a run may have.")
except Exception as e:
    print(f"NOT recorded ({type(e).__name__}: {e}) — the artifact on disk stands")
PY

rm -f "$RESP_TMP" "$LOG_TMP"
done

if [[ $FAILED -gt 0 ]]; then
    echo ""
    echo "WARNING: $FAILED of ${#LINEAGES[@]} lineage(s) failed. The reviews above"
    echo "are incomplete — do not read a single-lineage result as a dual review."
    exit 1
fi

# Stops 2 and 3. Set only when every lineage answered: pausing after a partial
# review would present half a dual review as the thing to decide on. A failed
# run leaves no pause, and the operator re-runs it.
echo ""
if [[ "$ROUND" == "1" ]]; then
    pause_state set reviews-landed \
        "reviews are in for $ID — read reviews/done/$ID.*.response.md before executing"
    notify_stop reviews-landed
elif [[ "$ROUND" == "3" ]]; then
    pause_state set result-reviewed \
        "result review is in for $ID — read reviews/done/$ID.*.result.md before the next item"
    notify_stop result-reviewed
fi
