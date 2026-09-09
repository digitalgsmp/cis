#!/usr/bin/env python3
"""Render a pause stop as something Eric can decide on, and send it to Telegram.

BUILD LIST 1.21 + 2.25. The pause halts the loop and writes a row; until now it
showed nothing, so a stop was only visible to whoever was watching the terminal.

2.25 SETTLED THE TRANSPORT AND THIS FOLLOWS IT EXACTLY:
  * HOST scope. An HTTP POST from the loop script using the host bot token.
  * NOT root Hermes — the VM pipeline is being retired and the feed must not
    depend on it. Nothing here starts a Hermes process; the token is read from a
    file and posted with urllib.
  * NOT a container agent — messaging is a transport, not a role. An agent given
    the job inherits its loadout, which is how cis-knowledge handed pipeline
    dispatch to a read-only advisor (2.23).

DESTINATION IS THE DM, NOT TELEGRAM_HOME_CHANNEL. All seven host .env files
still name the group Eric deleted on 2026-09-02 (-5563618057); posting there
gets a 403. The destination is his uid, which is what TELEGRAM_ALLOWED_USERS
already holds. 2.25 flagged the stale value and left it; this script routes
around it rather than depending on it.

VERDICTS ARE READ FROM THE RECORD, NOT SUMMARISED. Everything about a lineage's
answer comes from deliberation_rounds.objections_json — the verdict, the packet
hash, the token cost, and the opening of the objection as the model wrote it.
Claude Code's account of a review is not what goes in the message.

ONE-WAY. There is no reply consumer. See the module note at the bottom.

Usage:
    python3 tools/pause_notify.py <id> <stop> [--dry-run]
    stops: card-written | reviews-landed | result-reviewed
"""
import json
import os
import re
import sqlite3
import sys
import urllib.parse
import urllib.request

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
REPO = "/mnt/projects/cis"
ENV_FILE = os.environ.get("CIS_TG_ENV", "/home/eric/.hermes/.env")
LIMIT = 3500          # Telegram hard-caps at 4096; leave room.
OBJ_CHARS = 300       # per lineage, so two lineages stay phone-readable


def read_env(path):
    out = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^([A-Z_]+)=(.*)$", line.strip())
                if m:
                    out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def rounds_for(item_id, round_number):
    """Every lineage's row for one round, straight out of the record."""
    conn = sqlite3.connect(DB)
    try:
        rows = conn.execute(
            "SELECT run_id, reviewer_role, reviewer_signal, objections_json "
            "FROM deliberation_rounds "
            "WHERE run_id LIKE ? AND round_number = ? AND reviewer_role != 'pause' "
            "ORDER BY run_id",
            ("advisor-" + item_id + "-%", round_number)).fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()

    out = []
    for run_id, role, signal, oj in rows:
        try:
            e = json.loads(oj)[0]
        except Exception:
            e = {}
        out.append({
            "role": role,
            "signal": signal,
            "verdict": e.get("verdict") or "",
            "hash": e.get("packet_hash", ""),
            "hash_status": e.get("packet_hash_status", ""),
            "tokens": e.get("prompt_tokens", 0),
            "objection": (e.get("objection") or "").strip(),
        })
    return out


def first_prose(text, n):
    """The opening of the model's own answer, minus headers and blank lines."""
    body = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("---"):
            continue
        if re.match(r"^\**VERDICT:", s, re.I):
            continue
        body.append(s)
        if sum(len(b) for b in body) > n:
            break
    joined = " ".join(body)
    return (joined[:n] + "…") if len(joined) > n else joined


def render(item_id, stop):
    packet = os.path.join(REPO, "reviews/pending", item_id + ".md")
    L = []

    if stop == "card-written":
        L.append("CARD WRITTEN — not yet reviewed")
        L.append("card: %s" % item_id)
        L.append("")
        if os.path.exists(packet):
            text = open(packet, encoding="utf-8").read()
            title = next((l.lstrip("# ").strip() for l in text.split("\n")
                          if l.startswith("#")), item_id)
            L.append("What it is: %s" % title)
            intent = [l.strip() for l in text.split("\n")
                      if l.strip() and not l.startswith("#")][:3]
            if intent:
                L.append("")
                L.append("Opening: " + first_prose("\n".join(intent), 400))
            L.append("")
            L.append("Nothing has run. %d KB on disk." % (len(text) // 1024))
        else:
            L.append("NO PACKET at reviews/pending/%s.md" % item_id)
        L.append("")
        L.append("Next: round 1 review by both lineages.")

    elif stop == "reviews-landed":
        rows = rounds_for(item_id, 1)
        L.append("REVIEWS LANDED — nothing has executed")
        L.append("card: %s" % item_id)
        L.append("")
        if not rows:
            L.append("No round-1 rows recorded. Check the terminal.")
        else:
            hashes = {r["hash"] for r in rows}
            L.append("Both lineages saw one packet: %s"
                     % ("YES" if len(hashes) == 1 else "NO — HASHES DIFFER"))
            L.append("")
            for r in rows:
                L.append("--- %s" % r["role"])
                L.append("signal: %s%s" % (
                    r["signal"], ("  verdict: " + r["verdict"]) if r["verdict"] else ""))
                L.append("tokens: %s   hash: %s" % (r["tokens"], r["hash_status"]))
                L.append(first_prose(r["objection"], OBJ_CHARS))
                L.append("")
            L.append("What is unique to each lineage is NOT computed here — "
                     "it needs both objections read side by side, and a guess "
                     "at it would be Claude Code's account rather than theirs.")
        L.append("")
        L.append("Full text: reviews/done/%s.<lineage>.response.md" % item_id)
        L.append("Release from the terminal:")
        L.append("  bash tools/advisor_review.sh %s --continue" % item_id)

    elif stop == "result-reviewed":
        rows = rounds_for(item_id, 3)
        L.append("RESULT REVIEWED — the work has already run")
        L.append("card: %s" % item_id)
        L.append("")
        if not rows:
            L.append("No round-3 rows recorded. Check the terminal.")
        else:
            verdicts = [r["verdict"] for r in rows]
            if verdicts and all(v == "ESTABLISHED" for v in verdicts):
                L.append("BOTH LINEAGES: ESTABLISHED")
            elif "NOT_ESTABLISHED" in verdicts:
                L.append("*** NOT_ESTABLISHED — the evidence did not carry a claim")
            L.append("")
            for r in rows:
                L.append("--- %s: %s" % (r["role"], r["verdict"] or r["signal"]))
                L.append(first_prose(r["objection"], OBJ_CHARS))
                L.append("")
        L.append("Full text: reviews/done/%s.<lineage>.result.md" % item_id)
        L.append("Verification output is in the result packet, not inlined here.")
        L.append("")
        L.append("Release from the terminal:")
        L.append("  bash tools/advisor_review.sh %s --continue" % item_id)
    else:
        L.append("Unknown stop: %s" % stop)

    msg = "\n".join(L)
    return msg[:LIMIT] + ("\n…truncated" if len(msg) > LIMIT else "")


def send(text):
    env = read_env(ENV_FILE)
    token = os.environ.get("CIS_TG_TOKEN") or env.get("TELEGRAM_BOT_TOKEN", "")
    # TELEGRAM_HOME_CHANNEL names the group deleted 2026-09-02 and 403s.
    chat = (os.environ.get("CIS_TG_CHAT_ID")
            or env.get("TELEGRAM_ALLOWED_USERS", "").split(",")[0].strip())
    if not token or not chat:
        return False, "no token or chat id (looked in %s)" % ENV_FILE

    data = urllib.parse.urlencode({
        "chat_id": chat,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode()
    url = "https://api.telegram.org/bot%s/sendMessage" % token
    try:
        with urllib.request.urlopen(url, data=data, timeout=20) as resp:
            body = json.loads(resp.read().decode())
    except Exception as exc:                       # noqa: BLE001
        return False, "%s: %s" % (type(exc).__name__, exc)

    # CHECK THE PAYLOAD, NOT THE STATUS. Build list 1.11: a 200 can carry a
    # failure. Telegram answers ok:false inside a 200 for a blocked chat.
    if not body.get("ok"):
        return False, "telegram returned ok=false: %s" % body.get("description")
    return True, "message_id=%s" % body.get("result", {}).get("message_id")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) != 2:
        sys.stderr.write(__doc__)
        return 2
    item_id, stop = args
    text = render(item_id, stop)
    print("---------------- message ----------------")
    print(text)
    print("----------------- %d chars --------------" % len(text))
    if dry:
        print("(dry run — nothing sent)")
        return 0
    ok, detail = send(text)
    print("telegram: %s (%s)" % ("SENT" if ok else "FAILED", detail))
    # A failed notification must not fail the pause. The stop is already
    # recorded in the spine; losing the message loses visibility, not state.
    return 0


if __name__ == "__main__":
    sys.exit(main())

# THE REPLY PATH IS NOT WIRED, DELIBERATELY.
#
# 2.25 records that Eric's replies arrive with no reply_to_message field, so
# Telegram's own threading cannot say which card a reply answers. Its two
# options were: one card waits at a time, or each message carries a tag the
# reply must quote. The first is what 1.21 already gives.
#
# Consuming a reply needs something polling getUpdates. That is a long-running
# process, and 1.21's whole point is that the waiting state is a ROW and not a
# blocked process — a poller dies with its terminal and takes the loop's
# position with it, which is the failure the row was chosen to avoid. Wiring one
# here would contradict the design this feed exists to serve.
#
# So the feed is ONE-WAY: Eric reads the stop on his phone and releases it from
# the terminal with --continue. That is worse than replying "go" and better than
# a stop he never sees.
