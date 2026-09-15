#!/usr/bin/env python3
"""
notify_menter_result.py — R5: notify Eric of the implementation-review verdict.

Reuses the same TG2 bot reply_consumer.py already polls (CIS_TG_NOTIFY_TOKEN).
The verdict + evidence handle go to Eric's phone; no terminal required.

Usage:
  python3 tools/pipeline/notify_menter_result.py --run-id <id> --routing <X> [--dry-run]
"""

import argparse
import json
import os
import sqlite3
import sys
import urllib.request

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def load_token():
    tok = os.environ.get("CIS_TG_NOTIFY_TOKEN", "")
    if tok:
        return tok
    # fallback: secrets.env
    for p in ("/mnt/projects/cis/secrets.env", "/workspace/secrets.env"):
        if os.path.isfile(p):
            for line in open(p):
                line = line.strip()
                if line.startswith("CIS_TG_NOTIFY_TOKEN="):
                    return line.split("=", 1)[1]
    return ""


def main():
    parser = argparse.ArgumentParser(description="Notify Eric of menter result")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--routing", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = get_db()
    run = db.execute("SELECT * FROM workflow_runs WHERE id = ?", (args.run_id,)).fetchone()
    if run is None:
        print(f"REFUSED: workflow_run not found: {args.run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    ev = db.execute(
        "SELECT content FROM workflow_run_artifacts "
        "WHERE run_id = ? AND artifact_type = 'menter_build_evidence' "
        "ORDER BY id DESC LIMIT 1",
        (args.run_id,)).fetchone()
    evidence = json.loads(ev["content"]) if ev else {}
    patch_hash = evidence.get("patch_hash", "")
    output_dir = evidence.get("output_dir", "")

    rounds = db.execute(
        "SELECT reviewer_role, reviewer_signal FROM deliberation_rounds "
        "WHERE run_id = ? ORDER BY id DESC LIMIT 2",
        (args.run_id,)).fetchall()
    signals = {r["reviewer_role"]: r["reviewer_signal"] for r in rounds}

    msg = (
        f"CIS build verdict — {args.run_id}\n"
        f"routing: {args.routing}\n"
        f"review1: {signals.get('review1', 'n/a')}\n"
        f"review2: {signals.get('review2', 'n/a')}\n"
        f"patch_hash: {patch_hash[:16]}\n"
        f"output_dir: {output_dir}\n"
    )

    if args.dry_run:
        print(msg)
        db.close()
        sys.exit(0)

    token = load_token()
    if not token:
        print("ERROR: CIS_TG_NOTIFY_TOKEN not set", file=sys.stderr)
        db.close()
        sys.exit(1)

    home = os.environ.get("TELEGRAM_HOME_CHANNEL", "-5563618057")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps({"chat_id": home, "text": msg}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("ok"):
            print(f"telegram: SENT (message_id={data['result']['message_id']})")
        else:
            print(f"telegram: FAILED {data}", file=sys.stderr)
            sys.exit(1)
    except Exception as exc:
        print(f"telegram: ERROR {exc}", file=sys.stderr)
        sys.exit(1)

    db.close()


if __name__ == "__main__":
    main()
