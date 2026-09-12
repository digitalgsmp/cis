#!/usr/bin/env bash
# advisor_review.sh — send a review packet to the advisor (advisor, 8649)
# and write its reply back into the repo.
#
# The advisor has read-only measurement instruments (cis_* read tools); it may verify against the repo and spine, but not write.
# That is the point: an agent that cannot search cannot report that something
# is absent when it simply could not reach it (UNIFIED_BUILD_LIST 2.7, the
# absence-from-outside-scope variant, observed 2026-09-02).
#
# Usage:  bash tools/advisor_review.sh <id>                  # round 1: review
#         bash tools/advisor_review.sh <id> --reconcile      # cross-feed: reconcile round-1 findings
#         bash tools/advisor_review.sh <id> --reply <file>   # round 2: answer it
#         bash tools/advisor_review.sh <id> --result <file>  # round 3: result review
#         bash tools/advisor_review.sh <id> --pause <stop>   # halt the loop here
#         bash tools/advisor_review.sh <id> --continue       # release the halt
#         bash tools/advisor_review.sh <id> --supersede      # card replaced, not approved
#         reads   reviews/pending/<id>.md
#         writes  reviews/done/<id>.<profile>.response.md   (round 1)
#                 reviews/done/<id>.<profile>.reconcile.md  (cross-feed)
#                 reviews/done/<id>.reconcile.md            (final reconciled artifact)
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
SCOPE_LINE='FRAME FIRST — ANSWER THIS BEFORE ANYTHING ELSE. Is this the right work? Not whether the design is correct — whether this is the right ITEM, at the right TIME, for what this project is for. Begin your reply with exactly one line reading FRAME: RIGHT_WORK or FRAME: WRONG_WORK or FRAME: CANNOT_TELL, then one short paragraph of reasoning. Do not pad that paragraph to look diligent — if the answer is obviously yes, say so in a sentence and move on. If you cannot tell from what you were given, say what you would need. Only then review what follows. You are reviewing a proposal packet — work that has NOT been done yet. Use your read-only measurement instruments (cis_read_file, cis_search_files, cis_git_log, cis_git_show, cis_hash_file, cis_list_dir, and the cis_get_* spine queries) to verify any claim before you assert it, and cite the file, query, commit, or hash you checked. You may NOT write, edit, dispatch, or execute. If something you would need is not here, say what is missing — never report that it does not exist.'

RESULT_LINE='FRAME FIRST, AND IT FEEDS THE SLATE. The work below is already done, so this question cannot stop it — it is asked because the answer is what the slate is built from. Was this the right work, and what does the result imply about what should come next? Begin your reply with exactly one line reading FRAME: RIGHT_WORK or FRAME: WRONG_WORK or FRAME: CANNOT_TELL, then one short paragraph. Do not pad it. You are reviewing the RESULT of work that has ALREADY been executed. Below is the card that was approved, then the actual command output and diff produced when it ran. Use your read-only measurement instruments (cis_read_file, cis_search_files, cis_git_log, cis_git_show, cis_hash_file, cis_list_dir, and the cis_get_* spine queries) to verify the evidence before you assert, and cite the file, query, commit, or hash you checked. You may NOT write, edit, dispatch, or execute. Answer two questions: does this evidence establish what the card claimed, and what would look like success while still being wrong? Begin your reply with exactly one line reading VERDICT: ESTABLISHED or VERDICT: NOT_ESTABLISHED, then your reasoning. If the evidence is not enough to decide, answer NOT_ESTABLISHED and say what is missing — never treat what you cannot see as absent. THEN PRODUCE A SLATE, after your verdict. WRITE IT FOR A NON-CODER WHO DOES NOT READ CODE AND DOES NOT REMEMBER COMPONENT NAMES. The reader is the operator who commissions this work. He thinks in exactly one shape: I asked for something -- is it doing that yet -- and if not, what has to happen to make it work. That is what he is choosing from, so that is how you write it. For each candidate, exactly three lines. WANTED: the capability in plain language, as a thing the system should DO for him. No file names, no table names, no function names, no acronyms. WORKS TODAY: yes, partly, or no -- and in ONE sentence what actually happens right now. NEEDED: what has to be built or fixed for it to work, in plain language. Rank them so the one that unblocks the most comes first. Do NOT use an item number as the headline; if you know one, put it in brackets at the end of the WANTED line. Do NOT assume he remembers any previous card, review, or decision -- each entry must stand alone. If the right next work is not on the build list at all, say so as its own entry: a list that only repeats what someone already wrote down cannot surface what is missing.'

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
elif [[ $# -eq 2 && "$2" == "--reconcile" ]]; then
    MODE="reconcile"
elif [[ $# -eq 2 && "$2" == "--resolve" ]]; then
    MODE="resolve"
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
    echo "       bash tools/advisor_review.sh <id> --reconcile" >&2
    echo "       bash tools/advisor_review.sh <id> --resolve" >&2
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

REPLY_LINE='FRAME FIRST — ANSWER THIS BEFORE ANYTHING ELSE. Is this the right work? Not whether the design is correct — whether this is the right ITEM, at the right TIME, for what this project is for. Begin your reply with exactly one line reading FRAME: RIGHT_WORK or FRAME: WRONG_WORK or FRAME: CANNOT_TELL, then one short paragraph of reasoning. Do not pad that paragraph to look diligent — if the answer is obviously yes, say so in a sentence and move on. If you cannot tell from what you were given, say what you would need. Only then review what follows. You previously reviewed this packet and raised the objection below. Claude Code has answered it with evidence. Decide: WITHDRAWN if the evidence resolves your objection, HELD if it does not. Begin your reply with exactly one line reading VERDICT: WITHDRAWN or VERDICT: HELD, then a short paragraph of reasoning. If the evidence is not enough to decide, HOLD and say what is missing — never treat what you cannot see as absent.'

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

# ------------------------------------------------------------- RECONCILE ----
# BUILD LIST 2.3 — the reconciliation phase. Eric's 2026-07-03 design record:
# "the reviewers have to stop to deliberate and reconcile any differences."
# Round 1 froze two independent findings sets; until now nothing ever let one
# lineage see the other's, so `sequential_review` had nothing to guard (2.3:
# "the phase it belongs to was never built"). This round cross-feeds the frozen
# round-1 findings and each lineage produces the item-by-item reconciliation
# CARD-01 DONE-WHEN 4 names: agreements, disagreements, what each missed. The
# harness then writes ONE reconciled artifact referencing both round-1 hashes,
# preserving dissent rather than forcing consensus (CARD-01: "side by side is
# not reconciliation").
RECONCILE_LINE='RECONCILE — you are one of two reviewer lineages. You already reviewed the packet below in round 1, independently. Your round-1 findings were frozen and hashed. You are now shown, for the first time, the OTHER lineage'"'"'s frozen round-1 findings. Do not re-review the packet from scratch. Deliberate: reconcile your findings with theirs, item by item. Begin with exactly one line reading RECONCILE: COMPLETE or RECONCILE: INCOMPLETE (INCOMPLETE if the other lineage'"'"'s findings are missing or empty). Then produce, item by item: AGREED — findings you both raised, in your own words, citing the specific finding; DISAGREE — findings where you differ, and why; THEY MISSED (I caught) — your findings the other lineage did not raise; I MISSED (they caught) — their findings you did not raise, and whether you now accept each; UNRESOLVED — differences neither of you can settle from the packet alone, and what evidence would settle each. Preserve dissent. Do not invent consensus. If you cannot verify a claim against the packet, say so rather than agreeing. Use your read-only measurement instruments (cis_read_file, cis_search_files, cis_git_log, cis_git_show, cis_hash_file, cis_list_dir, and the cis_get_* spine queries) to verify the evidence before you assert, and cite the file, query, commit, or hash you checked. You may NOT write, edit, dispatch, or execute.'

if [[ "$MODE" == "reconcile" ]]; then
    if [[ ${#LINEAGES[@]} -ne 2 ]]; then
        echo "reconcile needs both lineages (unset CIS_ADVISOR_PROFILE / CIS_ADVISOR_PORT)" >&2
        exit 2
    fi
    R1_ADVISOR="$OUTDIR/$ID.advisor.response.md"
    R1_EVALUATOR="$OUTDIR/$ID.evaluator.response.md"
    for _f in "$R1_ADVISOR" "$R1_EVALUATOR"; do
        [[ -f "$_f" ]] || {
            echo "round 1 missing: $_f" >&2
            echo "run: bash tools/advisor_review.sh $ID first" >&2
            exit 1; }
    done
    R1_ADVISOR_HASH="$(sha256sum "$R1_ADVISOR" | cut -c1-16)"
    R1_EVALUATOR_HASH="$(sha256sum "$R1_EVALUATOR" | cut -c1-16)"
    RECONCILE_AT="$(date -Iseconds)"
    echo "cross-feed: advisor $R1_ADVISOR_HASH <-> evaluator $R1_EVALUATOR_HASH"

    build_reconcile_body() {
        RECONCILE_LINE="$RECONCILE_LINE" MAX_TOKENS="$MAX_TOKENS" RUN_TAG="$RUN_TAG" \
        PEER_NAME="$1" \
        python3 - "$PACKET" "$2" "$3" <<'PY'
import json, os, sys
packet = open(sys.argv[1], encoding="utf-8").read()
own = open(sys.argv[2], encoding="utf-8").read()
peer = open(sys.argv[3], encoding="utf-8").read()
prompt = (
    os.environ["RECONCILE_LINE"]
    + "\n\n(Reconcile run: " + os.environ["RUN_TAG"] + ")\n\n"
    + "=== THE PACKET ===\n" + packet
    + "\n\n=== YOUR FROZEN ROUND-1 FINDINGS ===\n" + own
    + "\n\n=== THE OTHER LINEAGE'S FROZEN ROUND-1 FINDINGS ("
    + os.environ["PEER_NAME"] + ") ===\n" + peer
)
print(json.dumps({
    "model": "agent",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": int(os.environ["MAX_TOKENS"]),
}))
PY
    }

    RECON_FAILED=0
    declare -A RECON_HASH
    for _lin in "${LINEAGES[@]}"; do
        PROFILE="${_lin%%:*}"; PORT="${_lin##*:}"
        if [[ "$PROFILE" == "advisor" ]]; then
            OWN="$R1_ADVISOR"; PEER="$R1_EVALUATOR"; PEER_NAME="evaluator (Qwen)"
            OWN_HASH="$R1_ADVISOR_HASH"; PEER_HASH="$R1_EVALUATOR_HASH"
        else
            OWN="$R1_EVALUATOR"; PEER="$R1_ADVISOR"; PEER_NAME="advisor (GLM)"
            OWN_HASH="$R1_EVALUATOR_HASH"; PEER_HASH="$R1_ADVISOR_HASH"
        fi
        OUT_RECON="$OUTDIR/$ID.$PROFILE.reconcile.md"
        echo "--- reconcile: $PROFILE on $PORT ---"

        BODY="$(build_reconcile_body "$PEER_NAME" "$OWN" "$PEER")" || {
            echo "FAILED: $PROFILE — could not build reconcile body" >&2
            RECON_FAILED=$((RECON_FAILED+1)); continue; }

        RESP="$(printf '%s' "$BODY" | docker exec -i -u worker "$CONTAINER" \
            sh -c "$REMOTE_SH" -- "$PROFILE" "$PORT" "$TIMEOUT")" || {
            echo "FAILED: $PROFILE on $PORT did not answer" >&2
            RECON_FAILED=$((RECON_FAILED+1)); continue; }
        if [[ -z "$RESP" ]]; then
            echo "FAILED: $PROFILE on $PORT returned an empty body" >&2
            RECON_FAILED=$((RECON_FAILED+1)); continue
        fi

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
            RECON_FAILED=$((RECON_FAILED+1)); continue
        fi

        RESP_TMP="$(mktemp)"
        printf '%s' "$RESP" > "$RESP_TMP"

        ID="$ID" PROFILE="$PROFILE" RUN_TAG="$RUN_TAG" PACKET_HASH="$PACKET_HASH" \
            OWN_HASH="$OWN_HASH" PEER_HASH="$PEER_HASH" PEER_NAME="$PEER_NAME" \
            RECONCILE_AT="$RECONCILE_AT" \
            python3 - "$OUT_RECON" "$PACKET" "$RESP_TMP" <<'PY'
import json, os, sys, datetime, sqlite3
out_path, packet_path, resp_path = sys.argv[1:4]
raw = open(resp_path, encoding="utf-8").read()
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    sys.stderr.write("gateway did not return JSON:\n" + raw[:2000] + "\n"); sys.exit(1)
if "choices" not in data or not data["choices"]:
    sys.stderr.write("gateway returned no choices:\n" + raw[:2000] + "\n"); sys.exit(1)
msg = data["choices"][0].get("message", {})
content = (msg.get("content") or msg.get("reasoning_content") or "").strip()
usage = data.get("usage", {})
pt = usage.get("prompt_tokens", 0); ct = usage.get("completion_tokens", 0); tt = usage.get("total_tokens", 0)
source = "gateway response usage"
if pt == 0 and ct == 0:
    source = "gateway reported 0 — reply served from its response cache, not a fresh measurement"

with open(out_path, "w", encoding="utf-8") as f:
    f.write(f"# Reconciliation — {os.environ['ID']}\n\n")
    f.write(f"- lineage: {os.environ['PROFILE']}\n")
    f.write(f"- packet: `{os.path.relpath(packet_path)}`\n")
    f.write(f"- own round-1 hash: {os.environ['OWN_HASH']}\n")
    f.write(f"- peer round-1 hash: {os.environ['PEER_HASH']} ({os.environ['PEER_NAME']})\n")
    f.write(f"- run tag: {os.environ['RUN_TAG']}\n")
    f.write(f"- at: {os.environ['RECONCILE_AT']}\n")
    f.write(f"- prompt_tokens: {pt}\n- completion_tokens: {ct}\n- total_tokens: {tt}\n")
    f.write(f"- token source: {source}\n\n---\n\n")
    f.write(content + "\n")

head = content.strip().splitlines()[0].upper() if content.strip() else ""
if "INCOMPLETE" in head:
    reconcile_ok = "INCOMPLETE"
elif "COMPLETE" in head:
    reconcile_ok = "COMPLETE"
else:
    reconcile_ok = "UNPARSED"

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
# run_id prefix is advisor-reconcile-, NOT advisor-<id>-reconcile-. The review
# thread already uses advisor-<id>-<profile>, and pause_notify.rounds_for() reads
# that with LIKE 'advisor-<id>-%'. A reconcile row under the same prefix would be
# returned as a round-1 review and the notification would double-count lineages.
run_id = "advisor-reconcile-" + os.environ["ID"] + "-" + os.environ["PROFILE"]
entry = {
    "reconcile": reconcile_ok,
    "own_hash": os.environ["OWN_HASH"],
    "peer_hash": os.environ["PEER_HASH"],
    "peer": os.environ["PEER_NAME"],
    "packet_hash": os.environ["PACKET_HASH"],
    "objection": content[:4000],
    "run_tag": os.environ["RUN_TAG"],
}
try:
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO deliberation_rounds "
        "(run_id, round_number, drafter_role, drafter_output, reviewer_role, "
        " reviewer_signal, objections_json, revision_number, "
        " requires_eric_review, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (run_id, 1, "claude_code", os.environ["PEER_NAME"],
         os.environ["PROFILE"], "OBJECTIONS", json.dumps([entry]),
         1, 1, datetime.datetime.now(datetime.timezone.utc).isoformat()))
    conn.commit(); conn.close()
    print(f"recorded: {run_id} reconcile={reconcile_ok}")
except sqlite3.IntegrityError:
    print(f"NOT recorded: {run_id} already exists (duplicate round for this run_id)")
except Exception as e:
    print(f"NOT recorded ({type(e).__name__}: {e}) — artifact on disk stands")

print(f"wrote {out_path}")
print(f"prompt_tokens={pt} completion_tokens={ct} total_tokens={tt}")
PY
        rm -f "$RESP_TMP"
        [[ -f "$OUT_RECON" ]] && RECON_HASH["$PROFILE"]="$(sha256sum "$OUT_RECON" | cut -c1-16)"
    done

    if [[ $RECON_FAILED -gt 0 ]]; then
        echo ""
        echo "WARNING: $RECON_FAILED of ${#LINEAGES[@]} lineage(s) failed to reconcile."
        echo "No final reconciled artifact written — a half-reconciliation is not a result."
        exit 1
    fi

    # The final reconciled artifact is harness-written, not model-written. It
    # preserves dissent by keeping BOTH per-lineage reconciliations verbatim and
    # references both frozen round-1 hashes (CARD-01 DONE-WHEN 4 and 5).
    FINAL_RECON="$OUTDIR/$ID.reconcile.md"
    {
        echo "# Reconciled review — $ID"
        echo ""
        echo "- packet hash: $PACKET_HASH"
        echo "- advisor round-1 hash: $R1_ADVISOR_HASH"
        echo "- evaluator round-1 hash: $R1_EVALUATOR_HASH"
        echo "- advisor reconcile hash: ${RECON_HASH[advisor]:-missing}"
        echo "- evaluator reconcile hash: ${RECON_HASH[evaluator]:-missing}"
        echo "- at: $RECONCILE_AT"
        echo ""
        echo "The two reviewer lineages reviewed the same packet independently (round 1),"
        echo "then each saw the other's frozen findings and reconciled (round 2)."
        echo "Dissent is preserved below; nothing here forces consensus."
        echo ""
        echo "---"
        echo ""
        echo "## advisor (GLM) reconciliation"
        echo ""
        cat "$OUTDIR/$ID.advisor.reconcile.md" 2>/dev/null || echo "(missing)"
        echo ""
        echo "---"
        echo ""
        echo "## evaluator (Qwen) reconciliation"
        echo ""
        cat "$OUTDIR/$ID.evaluator.reconcile.md" 2>/dev/null || echo "(missing)"
    } > "$FINAL_RECON"
    echo "wrote final reconciled artifact: $FINAL_RECON"

    exit 0
fi

# -------------------------------------------------------------- RESOLVE ----
# The reconciliation round surfaces UNRESOLVED items it could not settle. This
# round resolves them by triage. Each lineage tags every unresolved item as:
#   [FACT]       — settlable by checking the repo/spine; it must CHECK it with
#                  its read-only instruments and cite the evidence.
#   [AUTHORITY]  — the operator's decision (threat model / scope / risk); it
#                  states the binary choice but does NOT decide it.
#   [SPEC]       — the card is underspecified; it names the exact amendment.
# The harness then aggregates AUTHORITY items into a decision list for Eric and
# SPEC items into an amendment request for the drafter. This is the resolution
# the 2026-07-03 design record means by "reconcile any differences" — the
# differences that remain are routed to whoever can actually settle them.
RESOLVE_LINE='RESOLVE — you and the other lineage reviewed a card independently, then reconciled. Some items were left UNRESOLVED. Now resolve each one. Begin with exactly one line reading RESOLVE: COMPLETE or RESOLVE: INCOMPLETE. Then go item by item; EACH item on ONE line starting with exactly one of these tags, then the content on the same line: [FACT] — settlable by checking the repo or spine: USE your read-only instruments (cis_read_file, cis_search_files, cis_git_log, cis_git_show, cis_hash_file, or a spine query) to CHECK it now, then state the answer and cite the exact file/query/hash. [AUTHORITY] — the operator'"'"'s decision (threat model, scope, risk tolerance): state the exact binary choice the operator must make, both options, then your recommendation with a one-line reason; do NOT decide it yourself. [SPEC] — the card is underspecified: state the exact clause that must be added or changed, and where in the card. Be concise. Preserve dissent. If a FACT item cannot be checked because it is outside your read scope, mark it [AUTHORITY] and say why.'

if [[ "$MODE" == "resolve" ]]; then
    FINAL_RECON="$OUTDIR/$ID.reconcile.md"
    [[ -f "$FINAL_RECON" ]] || {
        echo "no reconciled artifact at $FINAL_RECON" >&2
        echo "run: bash tools/advisor_review.sh $ID --reconcile first" >&2
        exit 1; }
    RESOLVE_AT="$(date -Iseconds)"
    echo "resolving UNRESOLVED items from $FINAL_RECON"

    build_resolve_body() {
        RESOLVE_LINE="$RESOLVE_LINE" MAX_TOKENS="$MAX_TOKENS" RUN_TAG="$RUN_TAG" \
        python3 - "$PACKET" "$FINAL_RECON" <<'PY'
import json, os, sys
packet = open(sys.argv[1], encoding="utf-8").read()
recon = open(sys.argv[2], encoding="utf-8").read()
prompt = (
    os.environ["RESOLVE_LINE"]
    + "\n\n(Resolve run: " + os.environ["RUN_TAG"] + ")\n\n"
    + "=== THE PACKET ===\n" + packet
    + "\n\n=== THE RECONCILED REVIEW (resolve the UNRESOLVED items) ===\n" + recon
)
print(json.dumps({
    "model": "agent",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": int(os.environ["MAX_TOKENS"]),
}))
PY
    }

    RESOLVE_FAILED=0
    declare -A RESOLVE_HASH
    for _lin in "${LINEAGES[@]}"; do
        PROFILE="${_lin%%:*}"; PORT="${_lin##*:}"
        OUT_RESOLVE="$OUTDIR/$ID.$PROFILE.resolve.md"
        echo "--- resolve: $PROFILE on $PORT ---"

        BODY="$(build_resolve_body)" || {
            echo "FAILED: $PROFILE — could not build resolve body" >&2
            RESOLVE_FAILED=$((RESOLVE_FAILED+1)); continue; }

        RESP="$(printf '%s' "$BODY" | docker exec -i -u worker "$CONTAINER" \
            sh -c "$REMOTE_SH" -- "$PROFILE" "$PORT" "$TIMEOUT")" || {
            echo "FAILED: $PROFILE on $PORT did not answer" >&2
            RESOLVE_FAILED=$((RESOLVE_FAILED+1)); continue; }
        if [[ -z "$RESP" ]]; then
            echo "FAILED: $PROFILE on $PORT returned an empty body" >&2
            RESOLVE_FAILED=$((RESOLVE_FAILED+1)); continue
        fi

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
            RESOLVE_FAILED=$((RESOLVE_FAILED+1)); continue
        fi

        RESP_TMP="$(mktemp)"
        printf '%s' "$RESP" > "$RESP_TMP"

        ID="$ID" PROFILE="$PROFILE" RUN_TAG="$RUN_TAG" RESOLVE_AT="$RESOLVE_AT" \
            python3 - "$OUT_RESOLVE" "$RESP_TMP" <<'PY'
import json, os, sys
out_path, resp_path = sys.argv[1:3]
raw = open(resp_path, encoding="utf-8").read()
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    sys.stderr.write("gateway did not return JSON:\n" + raw[:2000] + "\n"); sys.exit(1)
if "choices" not in data or not data["choices"]:
    sys.stderr.write("gateway returned no choices:\n" + raw[:2000] + "\n"); sys.exit(1)
msg = data["choices"][0].get("message", {})
content = (msg.get("content") or msg.get("reasoning_content") or "").strip()
usage = data.get("usage", {})
pt = usage.get("prompt_tokens", 0); ct = usage.get("completion_tokens", 0); tt = usage.get("total_tokens", 0)
with open(out_path, "w", encoding="utf-8") as f:
    f.write(f"# Resolution — {os.environ['ID']}\n\n")
    f.write(f"- lineage: {os.environ['PROFILE']}\n")
    f.write(f"- run tag: {os.environ['RUN_TAG']}\n")
    f.write(f"- at: {os.environ['RESOLVE_AT']}\n")
    f.write(f"- prompt_tokens: {pt}\n- completion_tokens: {ct}\n- total_tokens: {tt}\n\n---\n\n")
    f.write(content + "\n")
print(f"wrote {out_path}")
print(f"prompt_tokens={pt} completion_tokens={ct} total_tokens={tt}")
PY
        rm -f "$RESP_TMP"
        [[ -f "$OUT_RESOLVE" ]] && RESOLVE_HASH["$PROFILE"]="$(sha256sum "$OUT_RESOLVE" | cut -c1-16)"
    done

    if [[ $RESOLVE_FAILED -gt 0 ]]; then
        echo ""
        echo "WARNING: $RESOLVE_FAILED of ${#LINEAGES[@]} lineage(s) failed to resolve."
        echo "No final resolution artifact written — a half-resolution is not a result."
        exit 1
    fi

    # Aggregate. AUTHORITY items become a decision list for Eric; SPEC items an
    # amendment request for the drafter. Both are extracted from the tagged
    # lines each lineage produced; both lineages' full resolutions are preserved
    # verbatim below so dissent is not collapsed.
    FINAL_RESOLVE="$OUTDIR/$ID.resolve.md"
    {
        echo "# Resolution — $ID"
        echo ""
        echo "- at: $RESOLVE_AT"
        echo "- advisor resolve hash: ${RESOLVE_HASH[advisor]:-missing}"
        echo "- evaluator resolve hash: ${RESOLVE_HASH[evaluator]:-missing}"
        echo ""
        echo "## DECISIONS FOR ERIC (authority)"
        echo ""
        for _p in advisor evaluator; do
            _f="$OUTDIR/$ID.$_p.resolve.md"
            [[ -f "$_f" ]] && { grep -E '^\[AUTHORITY\]' "$_f" 2>/dev/null | sed 's/^\[AUTHORITY\] //' || true; }
        done
        echo ""
        echo "## AMENDMENT REQUEST (spec gaps — drafter)"
        echo ""
        for _p in advisor evaluator; do
            _f="$OUTDIR/$ID.$_p.resolve.md"
            [[ -f "$_f" ]] && { grep -E '^\[SPEC\]' "$_f" 2>/dev/null | sed 's/^\[SPEC\] //' || true; }
        done
        echo ""
        echo "---"
        echo ""
        echo "## advisor (GLM) resolution"
        echo ""
        cat "$OUTDIR/$ID.advisor.resolve.md" 2>/dev/null || echo "(missing)"
        echo ""
        echo "---"
        echo ""
        echo "## evaluator (Qwen) resolution"
        echo ""
        cat "$OUTDIR/$ID.evaluator.resolve.md" 2>/dev/null || echo "(missing)"
    } > "$FINAL_RESOLVE"
    echo "wrote final resolution artifact: $FINAL_RESOLVE"

    pause_state set reviews-landed \
        "resolution is in for $ID — read $FINAL_RESOLVE before executing"
    notify_stop reviews-landed
    exit 0
fi

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
turns = "(see gateway agent.log for the per-turn tool-use breakdown)"

with open(out_path, "w", encoding="utf-8") as f:
    f.write(f"# Advisor review — {os.environ['ID']}\n\n")
    f.write(f"- packet: `{os.path.relpath(packet_path)}`\n")
    f.write(f"- advisor: {os.environ['PROFILE']} on port {os.environ['PORT']}\n")
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

# THE RATIFICATION DETECTOR. Both lineages, 2026-09-09: a gate obeyed as a
# format instruction is indistinguishable from a gate that functions. The frame
# verdict is recorded per review so "has this gate EVER fired" is a query rather
# than an impression. If it reads RIGHT_WORK for N consecutive reviews, the gate
# has gone decorative and that is a measurable state, not a feeling.
frame = ""
for _line in content.strip().splitlines()[:3]:
    _u = _line.upper()
    if "FRAME:" in _u:
        for _v in ("WRONG_WORK", "CANNOT_TELL", "RIGHT_WORK"):
            if _v in _u:
                frame = _v
                break
        break
if not frame:
    frame = "ABSENT"

entry = {
    "frame_verdict": frame,
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
    # BUILD LIST 1.22 — the loop writes its own knowledge record (source
    # 'advisor_loop'), so the exchange survives without a Claude Code
    # transcript. One row per round, self-describing, idempotent on
    # source_key. 'advisor_loop' is distinct from 'claude-external-advisor'
    # (which arrives by transcript ingestion, not by the loop writing).
    _ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _src_key = "advisor/%s/%s/%d" % (os.environ["ID"], os.environ["PROFILE"], rnd)
    _kb_head = "[advisor %s round %d %s] frame=%s verdict=%s" % (
        os.environ["ID"], rnd, os.environ["PROFILE"], frame, verdict or "-")
    _kb_content = _kb_head + "\n" + content[:4000]
    conn.execute("DELETE FROM knowledge_messages WHERE source_key=?", (_src_key,))
    conn.execute(
        "INSERT INTO knowledge_messages (role, content, source, source_key, timestamp) "
        "VALUES (?,?,?,?,?)",
        ("assistant", _kb_content, "advisor_loop", _src_key, _ts))
    conn.commit()
    conn.close()
    print(f"recorded: {run_id} round {rnd} signal={signal} "
          f"frame={frame} verdict={verdict or chr(45)} hash={hash_status}")
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

# Stops 2 and 3. Stop 2 (reviews-landed) is set by --reconcile, not round 1:
# round 1 produces two INDEPENDENT opinions, and Eric's 2026-07-03 design
# record says the reviewers "stop to deliberate and reconcile any differences"
# before anything reaches him. Presenting two raw round-1 opinions as the thing
# to decide on is the "side by side is not reconciliation" failure CARD-01
# names. Round 3 still sets its own stop. Both are set only when every lineage
# answered: pausing after a partial review would present half a dual review.
echo ""
if [[ "$ROUND" == "3" ]]; then
    pause_state set result-reviewed \
        "result review is in for $ID — read reviews/done/$ID.*.result.md before the next item"
    notify_stop result-reviewed
fi
