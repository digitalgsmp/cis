#!/usr/bin/env python3
"""
update_prefill.py — Update the prefill_messages_file for Hermes session-start context.

Queries the most recent meaningful memory records (excluding cron noise and
system-generated garbage) and writes a JSON file that Hermes injects into
every API call as a prefill message.

Session memory records and extraction records are queried separately and 
merged with session records prioritized. This prevents extraction pipeline
re-runs from drowning out actual conversation context.

Called by cron every 30 minutes. The prefill file is pointed to by
~/.hermes/config.yaml's `prefill_messages_file` setting.

Usage:
    python3 update_prefill.py                          # normal run
    python3 update_prefill.py --output /path/to/file   # custom output path
    python3 update_prefill.py --dry-run                 # show what would be written
"""

import json
import sys
import os
from pathlib import Path

RUNTIME_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = RUNTIME_DIR / "memory" / "current_context.json"


def build_prefill(limit=8, output_path=None, dry_run=False):
    """Query memory store and write prefill JSON file."""
    sys.path.insert(0, str(RUNTIME_DIR))
    from memory.memory_store import MemoryStore

    ms = MemoryStore()
    ms.ensure_tables()

    # ── Query session records and extraction records separately ──
    # Session records: corrections, decisions, preferences, current_state
    # Extraction records: discoveries, extractions, extraction_sections
    # We want session records to dominate the prefill.

    NOISE_SOURCE_TYPES = {"cron"}

    def is_noise(rec):
        """Check if a record is noise that shouldn't reach the prefill."""
        s = rec.get("summary", "")
        if not s or len(s) < 10:
            return True
        # System-generated bullet points
        if s.startswith("• User corrected") or s.startswith("[System note"):
            return True
        if s.startswith("Review the conversation above and update"):
            return True
        # Cron sessions
        sid = rec.get("session_id", "")
        if sid.startswith("cron_"):
            return True
        sp = rec.get("source_path", "")
        if "cron" in sp:
            return True
        return False

    # Pull more records to account for extraction flooding
    session_recent = ms.query_recent(limit=200)
    session_recent = [r for r in session_recent if r.get("category") not in ("extraction", "extraction_section", "discovery", "test")]
    session_recent = [r for r in session_recent if not is_noise(r)]

    # Also pull extraction records separately
    extraction_recent = ms.query_recent(limit=50)
    extraction_recent = [r for r in extraction_recent if r.get("category") in ("discovery", "extraction")]
    extraction_recent = [r for r in extraction_recent if not is_noise(r)]

    # Priority order for session records
    SESSION_ORDER = {
        "correction": 0,
        "decision": 1,
        "preference": 2,
        "current_state": 3,
    }

    def session_sort_key(rec):
        cat = rec.get("category", "")
        cat_priority = SESSION_ORDER.get(cat, 99)
        created = rec.get("created_at", "")
        return (cat_priority, created or "")

    session_recent.sort(key=session_sort_key)

    # Deduplicate by summary (keep the highest-priority one)
    seen = set()
    deduped_session = []
    for r in session_recent:
        s = r.get("summary", "")[:100]
        if s not in seen:
            seen.add(s)
            deduped_session.append(r)
    session_recent = deduped_session

    # Take top N session records, fill remaining with extraction discoveries
    session_limit = min(limit, len(session_recent))
    top_session = session_recent[:session_limit]
    remaining = limit - session_limit

    top_extraction = []
    if remaining > 0 and extraction_recent:
        # Take the most recent discoveries
        top_extraction = extraction_recent[:remaining]

    # Build the content
    lines = ["[SYSTEM: Recent memory context from previous sessions]"]

    # Session records with marker per category
    for record in top_session:
        cat = record.get("category", "?")
        summary = record.get("summary", "")
        created = (record.get("created_at") or "")[:19]
        importance = record.get("importance", 1)
        marker = "•" if cat in ("correction", "decision") or importance >= 2 else "-"
        lines.append("{marker} [{cat}] ({created}) {summary}".format(
            marker=marker, cat=cat, created=created, summary=summary[:200]
        ))

    # Extraction records
    for record in top_extraction:
        cat = record.get("category", "?")
        summary = record.get("summary", "")
        created = (record.get("created_at") or "")[:19]
        lines.append("- [{cat}] ({created}) {summary}".format(
            cat=cat, created=created, summary=summary[:200]
        ))

    content = "\n".join(lines)

    # Build the prefill messages array
    prefill = [
        {
            "role": "system",
            "content": content,
        }
    ]

    if dry_run:
        print("=" * 60)
        print("  PREFILL PREVIEW (would write to {})".format(output_path or DEFAULT_OUTPUT))
        print("=" * 60)
        print(content)
        print("=" * 60)
        total_looked_at = len(session_recent)
        print("  {} records written (from {} session + {} extraction candidates)".format(
            len(top_session) + len(top_extraction),
            total_looked_at,
            len(extraction_recent)
        ))
        cat_counts = {}
        for r in top_session + top_extraction:
            c = r.get("category", "?")
            cat_counts[c] = cat_counts.get(c, 0) + 1
        print("  Breakdown: {}".format(cat_counts))
        return

    # Write to file
    out_path = output_path or DEFAULT_OUTPUT
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(prefill, f, indent=2)

    total_records = len(top_session) + len(top_extraction)
    print("[PREFILL] Wrote {} records to {}".format(total_records, out_path))
    print("[PREFILL] Content size: {} chars".format(len(content)))
    print("[PREFILL] Session sources: {} | Extraction fillers: {}".format(
        len(top_session), len(top_extraction)
    ))
    cat_counts = {}
    for r in top_session + top_extraction:
        c = r.get("category", "?")
        cat_counts[c] = cat_counts.get(c, 0) + 1
    print("[PREFILL] Breakdown: {}".format(cat_counts))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update prefill context file for Hermes")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output path for prefill JSON")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written without saving")
    parser.add_argument("--limit", type=int, default=10, help="Number of memory records to include")
    args = parser.parse_args()

    build_prefill(limit=args.limit, output_path=args.output, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
