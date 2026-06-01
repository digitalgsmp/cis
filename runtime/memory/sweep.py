#!/usr/bin/env python3
"""
sweep.py — Cron: process unprocessed Hermes session files into unified memory.

Called by cron every 10 minutes. Scans ~/.hermes/sessions/ for any new
session JSON files not yet in memory_sessions, extracts signals, stores
as memory_records + vectors.

Usage:
    python3 sweep.py                          # normal run
    python3 sweep.py --dry-run                # show what would be done
    python3 sweep.py --force                  # re-process even done sessions

This is intended to be run as a cron job:
    hermes cron create --schedule 'every 10m' --script 'python3 /mnt/projects/cis/runtime/memory/sweep.py'
"""

import sys
from pathlib import Path

RUNTIME_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(RUNTIME_DIR.parent))

from memory.session_extract import sweep as session_sweep


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sweep unprocessed sessions into unified memory")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print("[SWEEP] Dry run mode — no changes will be made")

    # Ensure memory tables exist
    from memory.memory_store import MemoryStore
    ms = MemoryStore()
    ms.ensure_tables()

    # Run the session sweep
    results = session_sweep()

    # Print stats
    stats = ms.get_stats()
    print(f"\n[SWEEP] Memory store status:")
    print(f"  Memory records:   {stats['memory_records']}")
    print(f"  Sessions tracked: {stats['memory_sessions']}")
    print(f"  Pending sessions: {stats['pending_sessions']}")
    print(f"  Chroma vectors:   {stats['chroma_vectors']}")

    return results


if __name__ == "__main__":
    main()
