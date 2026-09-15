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
            "frame": e.get("frame_verdict", ""),
            "objection": (e.get("objection") or "").strip(),
        })
    return out


def reconcile_for(item_id):
    """Both lineages' reconciliation rows, from the cross-feed round.
    Run_id prefix is advisor-reconcile-<id>-<profile>, distinct from the review
    thread's advisor-<id>-<profile> so this query never sees round-1 reviews."""
    conn = sqlite3.connect(DB)
    try:
        rows = conn.execute(
            "SELECT reviewer_role, reviewer_signal, objections_json "
            "FROM deliberation_rounds "
            "WHERE run_id LIKE ? AND reviewer_role != 'pause' "
            "ORDER BY run_id",
            ("advisor-reconcile-" + item_id + "-%",)).fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()
    out = []
    for role, signal, oj in rows:
        try:
            e = json.loads(oj)[0]
        except Exception:
            e = {}
        out.append({
            "role": role,
            "reconcile": e.get("reconcile") or "",
            "own_hash": e.get("own_hash", ""),
            "peer_hash": e.get("peer_hash", ""),
            "objection": (e.get("objection") or "").strip(),
        })
    return out


def resolve_for(item_id):
    """Read the resolve artifact's DECISIONS FOR ERIC and AMENDMENT REQUEST.

    The resolve round is the final step before Eric: it triages the unresolved
    items into authority decisions (his call) and spec amendments (drafter's).
    Returns {section: text} or None if no resolve artifact exists yet.
    """
    path = os.path.join(REPO, "reviews", "done", item_id + ".resolve.md")
    if not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8").read()
    out = {}
    for section in ("DECISIONS FOR ERIC", "AMENDMENT REQUEST"):
        m = re.search(
            r"## " + re.escape(section) + r"[^\n]*\n(.*?)(?=\n## |\n---|\Z)",
            text, re.S)
        if m:
            body = m.group(1).strip()
            if body:
                out[section] = body
    return out or None


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



def other_open_stops(this_id):
    """Other stops waiting on Eric right now. He cannot see them from one
    message, and a stop he does not know about is a stop that does not exist."""
    conn = sqlite3.connect(DB)
    try:
        rows = conn.execute(
            "SELECT run_id, objections_json FROM deliberation_rounds "
            "WHERE reviewer_role='pause' AND reviewer_signal='PENDING'").fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()
    out = []
    for run_id, oj in rows:
        card = run_id[len("advisor-"):-len("-pause")]
        if card == this_id:
            continue
        try:
            stop = json.loads(oj)[0].get("stop", "?")
        except Exception:
            stop = "?"
        out.append((card, stop))
    return out


def frame_line(rows):
    """The one fact Eric can actually judge: did the reviewers think this is the
    right work. Everything else in a round-1 record is machinery."""
    verdicts = {r["frame"] for r in rows if r["frame"]}
    if not verdicts:
        return "Reviewers did not answer the frame question."
    if verdicts == {"RIGHT_WORK"}:
        return "Both reviewers: this is the RIGHT WORK to do now."
    if "WRONG_WORK" in verdicts:
        return "*** A REVIEWER SAYS THIS IS THE WRONG WORK. Read before releasing."
    if "CANNOT_TELL" in verdicts:
        return "A reviewer could not tell if this is the right work."
    return "Frame verdicts: " + ", ".join(sorted(verdicts))


def card_ask(item_id):
    """The card's plain-language 'what this is for', for the message.

    notify-format (BUILD LIST 2.25): Eric does not remember card names between
    sessions. The message names what he asked for, in the card's own words —
    INTENT line first, then the heading, then the id as a last resort.
    """
    path = os.path.join(REPO, "reviews/pending", item_id + ".md")
    if not os.path.exists(path):
        return item_id
    lines = [l.strip() for l in open(path, encoding="utf-8").read().split("\n")]
    for s in lines:
        if s.upper().startswith("INTENT:"):
            v = s.split(":", 1)[1].strip()
            if v:
                return v[:160]
    for i, s in enumerate(lines):
        if s.startswith("# "):
            v = s[2:].strip()
            stripped = re.sub(r"^CARD[-_A-Za-z0-9]*\b\s*[-—:]*\s*", "", v).strip()
            if stripped:
                return stripped[:160]
            # heading is just "CARD-xxx" — the summary is the next non-empty line
            for nxt in lines[i + 1:]:
                if nxt and not nxt.startswith("#"):
                    return nxt[:160]
            break
    return item_id


def action_lines(item_id, cmd):
    """The command Eric runs, and what happens if he does nothing."""
    return ["To proceed, run in the terminal:", "  " + cmd,
            "Do nothing and it stays stopped. Nothing is lost."]


def build_context():
    """The overall-build view, compressed for a phone. Same shape as
    tools/where_are_we.py, because the operator said a notification that does
    not place the work in the whole build leaves him more detached than moving
    cards by hand."""
    try:
        sys.path.insert(0, os.path.join(REPO, "tools"))
        from where_are_we import latest_slate
        conn = sqlite3.connect(DB)
        entries = latest_slate(conn)
        conn.close()
    except Exception:
        return []
    if not entries:
        return []
    out = ["WHERE THE BUILD STANDS", ""]
    for e in entries[:5]:
        works = e.get("WORKS TODAY", "")
        head = works.split("\u2014")[0].split("--")[0].strip().rstrip(".").upper()
        flag = {"YES": "YES", "PARTLY": "PARTLY", "NO": "NO"}.get(head, "?")
        want = re.sub(r"\s*\[[^\]]*\]", "", e["WANTED"]).strip(" .")
        if len(want) > 88:
            want = want[:88].rsplit(" ", 1)[0] + "…"
        out.append("%-6s %s" % (flag, want))
    out.append("")
    return out


def render(item_id, stop):
    """Render a pause stop as a phone message Eric can act on.

    notify-format (BUILD LIST 2.25), the reviewers' spec 2026-09-09: every
    message opens with the action signal (READY TO REVIEW / READY TO RUN /
    DECISION NEEDED / DONE), names what Eric asked for in plain language, and
    drops the machinery — the NEEDS YOU banner, card names, reviewer verdicts
    (UNPARSED / NOT_ESTABLISHED), file paths, and the WANTED/WORKS/NEEDED dump.
    A message exists only because there is a stop to release; the first line
    says what the stop is for.
    """
    cmd = "bash tools/advisor_review.sh %s --continue" % item_id
    L = []

    if stop == "card-written":
        L.append("READY TO REVIEW")
        L.append("")
        L.append(card_ask(item_id))
        L.append("")
        L.append("Nothing has run yet. To start the review:")
        L.append("  bash tools/advisor_review.sh %s" % item_id)
        L.append("Do nothing and it stays here. Nothing is lost.")

    elif stop == "reviews-landed":
        res = resolve_for(item_id)
        if res:
            L.append("DECISION NEEDED")
            L.append("")
            L.append(card_ask(item_id))
            L.append("")
            if "DECISIONS FOR ERIC" in res:
                L.append("The reviewers have questions only you can answer:")
                L.append(res["DECISIONS FOR ERIC"])
                L.append("")
            if "AMENDMENT REQUEST" in res:
                L.append("For the drafter (not you):")
                L.append(res["AMENDMENT REQUEST"])
                L.append("")
            L += action_lines(item_id, cmd)
        else:
            L.append("READY TO RUN")
            L.append("")
            L.append(card_ask(item_id))
            L.append("")
            L.append("Both reviewers checked it. To run it:")
            L.append("  " + cmd)
            L.append("Do nothing and it stays stopped. Nothing is lost.")

    elif stop == "result-reviewed":
        rows = rounds_for(item_id, 3)
        verdicts = [r["verdict"] for r in rows]
        bad = "NOT_ESTABLISHED" in verdicts
        L.append("DECISION NEEDED" if bad else "DONE")
        L.append("")
        L.append(card_ask(item_id))
        L.append("")
        if not rows:
            L.append("No result review recorded. Check the terminal.")
        elif bad:
            L.append("The work ran, but the evidence did not prove everything the card claimed.")
        else:
            L.append("The work ran and the reviewers' evidence supports it.")
        L.append("")
        L += action_lines(item_id, cmd)

    else:
        L.append("Unknown stop: %s" % stop)

    msg = "\n".join(L)
    return msg[:LIMIT] + ("\n…truncated" if len(msg) > LIMIT else "")


def send(text):
    env = read_env(ENV_FILE)
    # Prefer the dedicated notify-reply bot (TG2) so the push and the reply
    # consumer use the SAME token — Eric's "go"/"hold" reply must land on the
    # bot the consumer polls. Falls back to the host bot for legacy one-way push.
    token = (os.environ.get("CIS_TG_NOTIFY_TOKEN")
             or read_env("/mnt/projects/cis/secrets.env").get("CIS_TG_NOTIFY_TOKEN", "")
             or os.environ.get("CIS_TG_TOKEN")
             or env.get("TELEGRAM_BOT_TOKEN", ""))
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
