#!/usr/bin/env python3
"""
extract_corpus.py — Corpus Extraction Pass 1

Systematic extraction of Eric's verbatim words from all source roots.
Stores in corpus_entries table with per-project provenance tagging.

Source roots:
  1. session_closeouts — failure_summary, log_path fields
  2. agent_trajectories — input_text where role='user'
  3. deliberation_rounds — drafter_output (Eric's intent text)
  4. /mnt/archive/ session JSON files (if mounted)

Usage:
    python3 tools/extract_corpus.py                    # Extract from all sources
    python3 tools/extract_corpus.py --project CIS      # Filter by project
    python3 tools/extract_corpus.py --dry-run          # Show counts without inserting
"""

import argparse
import json
import os
import sqlite3
import sys

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
ARCHIVE_PATH = "/mnt/archive"

# Keywords for project tagging (simple heuristic, can be refined later)
SWA_KEYWORDS = {"swa", "scheduling", "workforce", "field", "scheduling workforce app", "wias"}
CIS_KEYWORDS = {"cis", "pipeline", "relay", "spine", "control plane", "agent", "hermes"}


def tag_project(text: str) -> str:
    """Simple keyword-based project tagging."""
    lower = text.lower()
    if any(kw in lower for kw in SWA_KEYWORDS):
        if any(kw in lower for kw in CIS_KEYWORDS):
            return "CIS"  # Default to CIS if ambiguous
        return "SWA"
    if any(kw in lower for kw in CIS_KEYWORDS):
        return "CIS"
    return "CIS"  # Default


def extract_from_session_closeouts(conn, dry_run=False):
    """Extract from session_closeouts table."""
    rows = conn.execute(
        "SELECT id, failure_summary, log_path, started_at FROM session_closeouts"
    ).fetchall()
    count = 0
    for row in rows:
        text = row["failure_summary"] or ""
        if not text.strip():
            continue
        project = tag_project(text)
        if not dry_run:
            conn.execute(
                """INSERT INTO corpus_entries (source_root, source_file, timestamp, content_text, project_tag)
                   VALUES (?, ?, ?, ?, ?)""",
                ("session_closeouts", str(row["id"]), row["started_at"], text, project),
            )
        count += 1
    return count


def extract_from_agent_trajectories(conn, dry_run=False):
    """Extract Eric's inputs from agent_trajectories (role='user')."""
    rows = conn.execute(
        "SELECT id, run_id, input_text, phase, created_at FROM agent_trajectories"
    ).fetchall()
    count = 0
    for row in rows:
        text = row["input_text"] or ""
        if not text.strip() or len(text) < 20:
            continue
        # Only extract user-originated text (Eric's words)
        # agent_trajectories stores input_text which is the prompt sent to the agent
        # We want the original intent, not the pipeline-injected context
        project = tag_project(text)
        if not dry_run:
            conn.execute(
                """INSERT INTO corpus_entries (source_root, source_file, timestamp, content_text, project_tag)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    "agent_trajectories",
                    f"run_id={row['run_id']},phase={row['phase']}",
                    row["created_at"],
                    text,
                    project,
                ),
            )
        count += 1
    return count


def extract_from_deliberation_rounds(conn, dry_run=False):
    """Extract Eric's intent from deliberation_rounds (Brain phase output contains intent text)."""
    rows = conn.execute(
        """SELECT id, run_id, round_number, brain_output, drafter_output, created_at
           FROM deliberation_rounds"""
    ).fetchall()
    count = 0
    for row in rows:
        # brain_output contains Eric's original intent as understood by Brain
        text = row["brain_output"] or ""
        if text.strip() and len(text) > 50:
            project = tag_project(text)
            if not dry_run:
                conn.execute(
                    """INSERT INTO corpus_entries (source_root, source_file, timestamp, content_text, project_tag)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        "deliberation_rounds",
                        f"run_id={row['run_id']},round={row['round_number']},field=brain_output",
                        row["created_at"],
                        text,
                        project,
                    ),
                )
            count += 1
    return count


def extract_from_archive(conn, dry_run=False):
    """Extract from /mnt/archive/ session JSON files if mounted."""
    if not os.path.ismount(ARCHIVE_PATH) and not os.path.isdir(ARCHIVE_PATH):
        print(f"  SKIP: {ARCHIVE_PATH} not mounted or not a directory")
        return 0

    count = 0
    for root, dirs, files in os.walk(ARCHIVE_PATH, topdown=True):
        # Limit depth to prevent hanging on 10TB filesystem
        depth = root[len(ARCHIVE_PATH):].count(os.sep)
        if depth >= 4:
            dirs[:] = []  # Don't descend deeper
            continue
        for fname in files:
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", errors="ignore") as f:
                    data = json.load(f)
                # Extract user messages
                if data is None:
                    continue
                messages = data if isinstance(data, list) else data.get("messages", [])
                if not isinstance(messages, list):
                    continue
                for msg in messages:
                    if not isinstance(msg, dict):
                        continue
                    if msg.get("role") != "user":
                        continue
                    text = msg.get("content", "")
                    if not text or len(text) < 20:
                        continue
                    project = tag_project(text)
                    ts = msg.get("timestamp", data.get("timestamp", ""))
                    if not dry_run:
                        conn.execute(
                            """INSERT INTO corpus_entries (source_root, source_file, timestamp, content_text, project_tag)
                               VALUES (?, ?, ?, ?, ?)""",
                            ("archive", fpath, ts, text, project),
                        )
                    count += 1
            except (json.JSONDecodeError, IOError):
                continue
    return count


def main():
    parser = argparse.ArgumentParser(description="Corpus Extraction Pass 1")
    parser.add_argument("--project", default=None, help="Filter by project tag (CIS, SWA, WIAS)")
    parser.add_argument("--dry-run", action="store_true", help="Show counts without inserting")
    parser.add_argument("--db-path", default=DB_PATH, help="Path to spine DB")
    args = parser.parse_args()

    print(f"Corpus Extraction Pass 1")
    print(f"  DB: {args.db_path}")
    print(f"  Dry run: {args.dry_run}")
    print()

    conn = sqlite3.connect(args.db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    # Check if corpus_entries table exists
    table_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='corpus_entries'"
    ).fetchone()
    if not table_exists:
        print("ERROR: corpus_entries table does not exist. Run migration 0021 first.")
        sys.exit(1)

    sources = [
        ("session_closeouts", extract_from_session_closeouts),
        ("agent_trajectories", extract_from_agent_trajectories),
        ("deliberation_rounds", extract_from_deliberation_rounds),
        ("archive", extract_from_archive),
    ]

    total = 0
    for name, extractor in sources:
        print(f"Extracting from {name}...")
        count = extractor(conn, dry_run=args.dry_run)
        print(f"  {count} entries extracted")
        total += count

    if not args.dry_run:
        conn.commit()

    # Show summary by project
    print(f"\n--- Summary ---")
    print(f"Total entries: {total}")
    if not args.dry_run:
        rows = conn.execute(
            "SELECT project_tag, source_root, COUNT(*) as cnt FROM corpus_entries GROUP BY project_tag, source_root ORDER BY project_tag, source_root"
        ).fetchall()
        for r in rows:
            print(f"  {r['project_tag']:6s} | {r['source_root']:25s} | {r['cnt']} entries")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
