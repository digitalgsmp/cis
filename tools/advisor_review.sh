#!/usr/bin/env bash
# advisor_review.sh — send a review packet to the advisor (advisor, 8649)
# and write its reply back into the repo.
#
# The advisor has no tools. It reasons only from what the packet hands it.
# That is the point: an agent that cannot search cannot report that something
# is absent when it simply could not reach it (UNIFIED_BUILD_LIST 2.7, the
# absence-from-outside-scope variant, observed 2026-09-02).
#
# Usage:  bash tools/advisor_review.sh <id>                 # round 1: review
#         bash tools/advisor_review.sh <id> --reply <file>  # round 2: answer it
#         reads   reviews/pending/<id>.md
#         writes  reviews/done/<id>.response.md   (round 1)
#                 reviews/done/<id>.reply.md      (round 2)
#         records each round in deliberation_rounds as
#         run_id advisor-<id>-<profile>
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
# otherwise reject the second lineage's round 1 -- and reject it through the
# same IntegrityError that implements the two-round cap, reporting 'cap
# reached' for what is actually a collision.
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
# TWO-ROUND CAP IS THE SCHEMA'S: UNIQUE(run_id, round_number). A third call is
# refused by the database, not by a counter in this script.
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

SCOPE_LINE='You are reviewing a result packet. You have no file access and no tools. Everything you need is in this message. If something you would need is not here, say what is missing — never report that it does not exist.'

REPLY_FILE=""
if [[ $# -eq 1 ]]; then
    :
elif [[ $# -eq 3 && "$2" == "--reply" ]]; then
    REPLY_FILE="$3"
    [[ -f "$REPLY_FILE" ]] || { echo "no evidence file at $REPLY_FILE" >&2; exit 1; }
else
    echo "usage: bash tools/advisor_review.sh <id>" >&2
    echo "       bash tools/advisor_review.sh <id> --reply <evidence-file>" >&2
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

# The packet hash binds a reply to the exact packet version it answers. Round 2
# compares it against the hash stored in round 1 and records MISMATCH rather
# than silently accepting a reply to a packet that has since changed. This is
# the structural form of the 2.24 cache guard, borrowed from
# advisor_escalation_packets.packet_hash.
PACKET_HASH="$(sha256sum "$PACKET" | cut -c1-16)"

if [[ -n "$REPLY_FILE" ]]; then
    ROUND=2
    OUT="$OUTDIR/$ID.reply.md"
else
    ROUND=1
fi

REPLY_LINE='You previously reviewed this packet and raised the objection below. Claude Code has answered it with evidence. Decide: WITHDRAWN if the evidence resolves your objection, HELD if it does not. Begin your reply with exactly one line reading VERDICT: WITHDRAWN or VERDICT: HELD, then a short paragraph of reasoning. If the evidence is not enough to decide, HOLD and say what is missing — never treat what you cannot see as absent.'

BODY="$(SCOPE_LINE="$SCOPE_LINE" REPLY_LINE="$REPLY_LINE" MAX_TOKENS="$MAX_TOKENS" RUN_TAG="$RUN_TAG" ROUND="$ROUND" PRIOR="$OUTDIR/$ID.response.md" python3 - "$PACKET" "${REPLY_FILE:-}" <<'PY'
import json, os, sys
packet = open(sys.argv[1], encoding="utf-8").read()
if os.environ["ROUND"] == "2":
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

# One call per lineage. A failure in one is reported and the other still
# records -- a half-review that says so beats a silent single review.
FAILED=0
for _lin in "${LINEAGES[@]}"; do
PROFILE="${_lin%%:*}"
PORT="${_lin##*:}"
if [[ ${#LINEAGES[@]} -gt 1 ]]; then
    OUT="$OUTDIR/$ID.$PROFILE.response.md"
    [[ -n "$REPLY_FILE" ]] && OUT="$OUTDIR/$ID.$PROFILE.reply.md"
fi
echo "--- lineage: $PROFILE on $PORT ---"

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
reply_file = os.environ.get("REPLY_FILE") or ""

verdict = ""
if rnd == 2:
    head = content.strip().splitlines()[0].upper() if content.strip() else ""
    if "WITHDRAWN" in head:
        verdict = "WITHDRAWN"
    elif "HELD" in head:
        verdict = "HELD"
    else:
        verdict = "UNPARSED"

# HELD -> OBJECTIONS, WITHDRAWN -> CONSENSUS_REACHED. Round 1 is always
# OBJECTIONS: it is a review awaiting an answer, and OBJECTIONS is what keeps
# it visible to check_escalation_required. UNPARSED holds rather than assumes.
signal = "CONSENSUS_REACHED" if verdict == "WITHDRAWN" else "OBJECTIONS"

sent_hash = os.environ["PACKET_HASH"]
hash_status = "MATCH"
if rnd == 2:
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
    print(f"NOT recorded: {run_id} round {rnd} exists — two-round cap reached")
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
