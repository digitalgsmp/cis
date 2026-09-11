#!/usr/bin/env python3
"""ingest_advisor_rounds.py — backfill the advisor loop's knowledge record.

BUILD LIST 1.22: the advisor loop must write its own record into
knowledge_messages with source='advisor_loop', so an exchange survives without
being quoted inside a Claude Code transcript. This tool applies that same write
to every review round already present in deliberation_rounds.

Idempotent on source_key ('advisor/<card>/<lineage>/<round>'): delete any
existing row for the key, then insert. Re-running changes nothing.

Reconcile rows (run_id 'advisor-reconcile-*') are excluded: they are a derived
cross-feed artifact, already persisted in reviews/done/*.reconcile.md and in
deliberation_rounds, and they carry no frame/verdict to record in the
self-describing header this write produces.

Usage:
  python3 tools/queue/ingest_advisor_rounds.py            # dry-run: print plan
  python3 tools/queue/ingest_advisor_rounds.py --apply    # write the rows
"""
import argparse
import json
import os
import sqlite3
import sys

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")


def parse_run_id(run_id, reviewer_role):
    """Return the card id embedded in an advisor review run_id.

    run_id is 'advisor-<card>-<profile>', and reviewer_role is that profile,
    so the card is the run_id with both the 'advisor-' prefix and the
    '-<profile>' suffix removed.
    """
    if not run_id.startswith("advisor-"):
        return None
    body = run_id[len("advisor-"):]
    if reviewer_role and body.endswith("-" + reviewer_role):
        body = body[: -(len(reviewer_role) + 1)]
    return body or None


def entry_of(row):
    try:
        parsed = json.loads(row)
    except Exception:
        return {}
    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
        return parsed[0]
    if isinstance(parsed, dict):
        return parsed
    return {}


def rows_to_write(conn):
    """Yield (source_key, content) for every advisor review round."""
    cur = conn.execute(
        "SELECT run_id, reviewer_role, round_number, objections_json, created_at "
        "FROM deliberation_rounds "
        "WHERE run_id LIKE 'advisor-%' "
        "  AND run_id NOT LIKE 'advisor-reconcile-%' "
        "  AND reviewer_role IN ('advisor','evaluator') "
        "ORDER BY run_id, round_number"
    )
    for run_id, lineage, rnd, obj_json, created_at in cur.fetchall():
        card = parse_run_id(run_id, lineage)
        if card is None:
            continue
        e = entry_of(obj_json)
        frame = e.get("frame_verdict", "") or ""
        verdict = e.get("verdict", "") or ""
        text = e.get("objection", "") or ""
        src_key = f"advisor/{card}/{lineage}/{rnd}"
        head = f"[advisor {card} round {rnd} {lineage}] frame={frame} verdict={verdict}"
        content = head + "\n" + (text[:4000] if text else "")
        yield src_key, content, created_at


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write rows (default is dry-run)")
    ap.add_argument("--db", default=DB)
    a = ap.parse_args()

    conn = sqlite3.connect(a.db)
    plan = list(rows_to_write(conn))

    print(f"{len(plan)} advisor review round(s) to write")
    for src_key, content, _ts in plan[:8]:
        print(f"  {src_key}: {content.splitlines()[0] if content else '(empty)'}")
    if len(plan) > 8:
        print(f"  ... and {len(plan) - 8} more")

    if not a.apply:
        print("dry-run — pass --apply to write")
        conn.close()
        return 0

    written = 0
    for src_key, content, created_at in plan:
        conn.execute(
            "DELETE FROM knowledge_messages WHERE source_key=?", (src_key,))
        conn.execute(
            "INSERT INTO knowledge_messages "
            "(role, content, source, source_key, timestamp) VALUES (?,?,?,?,?)",
            ("assistant", content, "advisor_loop", src_key, created_at))
        written += 1
    conn.commit()

    total = conn.execute(
        "SELECT count(*) FROM knowledge_messages WHERE source='advisor_loop'"
    ).fetchone()[0]
    print(f"wrote {written} row(s); advisor_loop total now {total}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
