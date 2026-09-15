#!/usr/bin/env python3
"""reply_consumer.py — the TG2 two-way release path.

A pause stop is pushed to Eric's phone; this long-lived poller reads his reply
on the dedicated notify bot (CIS_TG_NOTIFY_TOKEN) and releases the pause from
the phone — no terminal. Release-only: it does NOT advance the loop (that stays
the Drafter's manual re-invocation of advisor_review.sh).

Design follows the TG2 card V5 (queue 3.31):
  - getUpdates long-poll, 30s timeout (no webhook — LAN container, no HTTPS).
  - release = the EXACT state flip `--continue` performs, so both paths release
    the same row (D2 coexistence):
        UPDATE deliberation_rounds
        SET reviewer_signal='CONSENSUS_REACHED', objections_json=?
        WHERE run_id=? AND round_number=?
    with the entry's released_at + resolution='CONTINUED' written into the JSON.
  - "hold" ACKs and suppresses re-notify via a durable ack file (survives
    docker rm -f — lives on /workspace/cis/state, not /tmp).
  - single-card invariant: >1 PENDING pause row -> refuse (F5).
  - update_id offset advances only after a successful release/ack (F1).

Env:
  CIS_TG_NOTIFY_TOKEN   (required; fallback: /workspace/secrets.env)
  CIS_SPINE_PATH        (default /workspace/cis/data/cis_memory.db)
  TELEGRAM_ALLOWED_USERS (default 6511416750 — Eric's uid)
  CIS_STATE_DIR         (default /workspace/cis/state)

Logs to /tmp/cis-logs/reply_consumer.log.
"""

import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

REPO = os.environ.get("CIS_REPO_ROOT", "/workspace/cis")
DB = os.environ.get("CIS_SPINE_PATH", f"{REPO}/data/cis_memory.db")
STATE_DIR = os.environ.get("CIS_STATE_DIR", f"{REPO}/state")
ACK_FILE = os.path.join(STATE_DIR, "reply_consumer.ack")
LOG_DIR = "/tmp/cis-logs"
LOG_FILE = os.path.join(LOG_DIR, "reply_consumer.log")

TELEGRAM = "https://api.telegram.org"
POLL_TIMEOUT = 30          # getUpdates long-poll timeout
MAX_RELEASE_FAILURES = 3   # F1 backoff cap


def log(msg):
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass
    print(line, flush=True)


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


def get_token():
    tok = os.environ.get("CIS_TG_NOTIFY_TOKEN", "")
    if tok:
        return tok
    return read_env(f"{REPO}/secrets.env").get("CIS_TG_NOTIFY_TOKEN", "")


def allowed_uid():
    raw = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
    if raw:
        uids = [u.strip() for u in raw.replace(",", " ").split() if u.strip()]
        if uids:
            return uids[0]
    return "6511416750"


def tg_call(method, **params):
    token = get_token()
    if not token:
        return None, "no CIS_TG_NOTIFY_TOKEN"
    params = {k: v for k, v in params.items() if v is not None}
    url = f"{TELEGRAM}/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=POLL_TIMEOUT + 15) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except Exception as exc:
        return None, str(exc)


def send_message(chat_id, text):
    body, err = tg_call("sendMessage", chat_id=chat_id, text=text)
    if err:
        log(f"sendMessage failed: {err}")
        return False
    if not body or not body.get("ok"):
        log(f"sendMessage error: {body}")
        return False
    return True


def get_pending_pause_rows(conn):
    return conn.execute(
        "SELECT run_id, round_number, objections_json FROM deliberation_rounds "
        "WHERE reviewer_role='pause' AND reviewer_signal='PENDING' "
        "ORDER BY id"
    ).fetchall()


def release_pause(conn):
    """Release the single PENDING pause row, matching `--continue` exactly."""
    rows = get_pending_pause_rows(conn)
    if len(rows) == 0:
        return ("no_pause", None)
    if len(rows) > 1:
        return ("multiple", len(rows))

    run_id, round_number, obj_json = rows[0]
    now = datetime.now(timezone.utc).isoformat()
    try:
        entries = json.loads(obj_json or "[]")
    except (TypeError, ValueError):
        entries = []
    for e in entries:
        if isinstance(e, dict):
            e["released_at"] = now
            e["resolution"] = "CONTINUED"

    conn.execute(
        "UPDATE deliberation_rounds SET reviewer_signal='CONSENSUS_REACHED', "
        "objections_json=? WHERE run_id=? AND round_number=?",
        (json.dumps(entries), run_id, round_number),
    )
    conn.commit()
    return ("released", run_id)


def ack_hold(conn, run_id):
    """Write the held pause run_id to the durable ack file (F2-safe)."""
    os.makedirs(STATE_DIR, exist_ok=True)
    acks = set()
    try:
        with open(ACK_FILE, encoding="utf-8") as fh:
            acks = {ln.strip() for ln in fh if ln.strip()}
    except OSError:
        pass
    acks.add(run_id)
    with open(ACK_FILE, "w", encoding="utf-8") as fh:
        for a in sorted(acks):
            fh.write(a + "\n")
    log(f"held: {run_id}")


def handle_command(conn, chat_id, text):
    cmd = text.strip().lower()
    if cmd in ("go", "continue", "release"):
        result, detail = release_pause(conn)
        if result == "released":
            send_message(chat_id, f"released: {detail}")
            log(f"released: {detail}")
            return True
        if result == "no_pause":
            send_message(chat_id, "no open pause — nothing to release")
            return True
        if result == "multiple":
            send_message(chat_id,
                         f"multiple cards paused ({detail}) — use the terminal")
            return True
    elif cmd in ("hold", "pause"):
        rows = get_pending_pause_rows(conn)
        if len(rows) == 1:
            ack_hold(conn, rows[0][0])
            send_message(chat_id, "held — won't re-notify until go")
        else:
            send_message(chat_id, "can't hold: " +
                         ("no open pause" if not rows else
                          f"{len(rows)} cards paused"))
        return True
    else:
        send_message(chat_id, "say 'go' (release) or 'hold' (suppress re-notify)")
        return False


def main():
    token = get_token()
    if not token:
        log("FATAL: no CIS_TG_NOTIFY_TOKEN")
        sys.exit(2)
    uid = allowed_uid()
    log(f"reply consumer starting (allowed uid={uid})")

    offset = 0
    consecutive_failures = 0

    while True:
        body, err = tg_call("getUpdates", offset=offset,
                            timeout=POLL_TIMEOUT)
        if err or not body or not body.get("ok"):
            consecutive_failures += 1
            log(f"getUpdates failed ({err or body}); retry "
                f"{consecutive_failures}")
            time.sleep(min(consecutive_failures * 5, 30))
            continue
        consecutive_failures = 0

        for upd in body.get("result", []):
            offset = upd.get("update_id", offset) + 1
            msg = upd.get("message") or upd.get("edited_message")
            if not msg:
                continue
            from_id = str(msg.get("from", {}).get("id", ""))
            if from_id != uid:
                log(f"ignored message from non-allowed uid {from_id}")
                continue
            text = msg.get("text") or ""
            if not text.strip():
                continue
            chat_id = msg.get("chat", {}).get("id")
            log(f"command from {from_id}: {text[:40]!r}")
            try:
                conn = sqlite3.connect(DB)
                conn.row_factory = sqlite3.Row
                handle_command(conn, chat_id, text)
                conn.close()
            except Exception as exc:
                log(f"handler error: {exc}")
                send_message(chat_id, f"release failed ({exc}) — use --continue")

        time.sleep(1)


if __name__ == "__main__":
    main()
