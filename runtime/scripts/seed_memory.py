#!/usr/bin/env python3
"""
seed_memory.py — One-shot deep backfill of all existing data into unified memory.

Re-processes:
  1. All 1,536 extraction analysis files (CIS + SWA) → memory_records + vectors
  2. All 189 Hermes session files → extracted signals → memory_records + vectors
  3. All existing LMS/course content (if ChromaDB `course_content` exists)

This catches up everything that existed before the memory system was built.
After this runs, only new sessions/archives need processing.

Usage:
    python3 seed_memory.py                              # full backfill
    python3 seed_memory.py --sessions-only               # sessions only
    python3 seed_memory.py --extractions-only            # extractions only
    python3 seed_memory.py --dry-run                     # show what would be done
    python3 seed_memory.py --sample 5                    # test with N files
"""

import sys
import os
from pathlib import Path

RUNTIME_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RUNTIME_DIR))


def seed_extractions(dry_run=False, sample=0):
    """Re-process all extraction analysis files into memory_records."""
    from scripts.ingest_extractions import parse_extraction, _index_into_memory, generate_spine_id
    from memory.memory_store import MemoryStore

    # Ensure tables exist
    ms = MemoryStore()
    ms.ensure_tables()

    # Find extraction files
    cis_dir = Path("/mnt/projects/cis/cis_kernel/extraction/functional_intents")
    swa_dir = Path("/mnt/projects/social_work_ai/swa_kernel/extraction/functional_intents")

    files = []
    for d in [cis_dir, swa_dir]:
        if d.exists():
            for f in sorted(d.glob("*.md")):
                files.append(f)

    if sample:
        import random
        random.seed(42)
        files = random.sample(files, min(sample, len(files)))

    print(f"Processing {len(files)} extraction files...")
    done = 0
    errors = 0
    records_created = 0

    for i, filepath in enumerate(files):
        project = "cis" if "/cis/" in str(filepath) else "swa"
        label = filepath.name[:50]
        print(f"  [{i+1}/{len(files)}] {filepath.name:.55s}...", end=" ", flush=True)

        try:
            parsed = parse_extraction(filepath)
            source_group = parsed["metadata"].get("group", "unknown")
            source_filename = parsed["metadata"].get("source", filepath.name)
            if "/" in source_filename:
                source_filename = source_filename.rsplit("/", 1)[-1]
            if source_filename.endswith(".md"):
                source_filename = source_filename[:-3]
            subject = source_filename
            spine_id = generate_spine_id(project, filepath.name)

            if dry_run:
                disc_count = len(parsed.get("discoveries", []))
                section_count = len(parsed.get("sections", []))
                print(f"✓ {disc_count} discoveries, {section_count} sections [DRY-RUN]")
                done += 1
                continue

            _index_into_memory(parsed, spine_id, project, subject, source_group)
            records_created += 1 + min(len(parsed.get("discoveries", [])), 12)
            print(f"✓")
            done += 1

        except Exception as e:
            print(f"✗ {e}")
            errors += 1

    print(f"\nExtractions: {done} done, {errors} errors, ~{records_created} memory records")
    return {"done": done, "errors": errors, "records": records_created}


def seed_sessions(dry_run=False, sample=0):
    """Process Hermes session files into memory_records."""
    from memory.session_extract import process_session_file, sweep
    from memory.memory_store import MemoryStore

    ms = MemoryStore()
    ms.ensure_tables()

    sessions_dir = Path.home() / ".hermes" / "sessions"
    if not sessions_dir.exists():
        print(f"Session directory not found: {sessions_dir}")
        return {"done": 0, "errors": 0}

    session_files = sorted(sessions_dir.glob("session_*.json"), key=lambda p: p.stat().st_mtime)
    if sample:
        session_files = session_files[-sample:]  # most recent

    # Check which are already processed
    already_done = set()
    try:
        cur = ms.conn.cursor()
        rows = cur.execute(
            "SELECT session_id FROM memory_sessions WHERE status='done'"
        ).fetchall()
        already_done = {r[0] for r in rows}
    except Exception:
        pass

    print(f"Found {len(session_files)} session files ({len(already_done)} already processed)")
    done = 0
    skipped = 0
    errors = 0
    records_created = 0

    for path in session_files:
        file_key = path.stem
        if file_key in already_done:
            skipped += 1
            continue

        if dry_run:
            print(f"  Would process: {path.name}")
            done += 1
            continue

        result = process_session_file(path)
        if result.get("error"):
            errors += 1
        else:
            records_created += result.get("nodes", 0)
            done += 1

    print(f"\nSessions: {done} processed, {skipped} skipped, {errors} errors, ~{records_created} records")
    return {"done": done, "skipped": skipped, "errors": errors, "records": records_created}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed unified memory from all existing data")
    parser.add_argument("--sessions-only", action="store_true")
    parser.add_argument("--extractions-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample", type=int, default=0)
    args = parser.parse_args()

    results = {}

    if not args.extractions_only:
        print("=" * 60)
        print("  SEED: Session Files")
        print("=" * 60)
        results["sessions"] = seed_sessions(dry_run=args.dry_run, sample=args.sample)

    if not args.sessions_only:
        print("\n" + "=" * 60)
        print("  SEED: Extraction Analysis Files")
        print("=" * 60)
        results["extractions"] = seed_extractions(dry_run=args.dry_run, sample=args.sample)

    print("\n" + "=" * 60)
    print("  SEED COMPLETE")
    print("=" * 60)
    total_records = sum(r.get("records", 0) for r in results.values())
    print(f"  Total memory records created: ~{total_records}")
    print(f"  Run 'python3 memory/sweep.py' to process new sessions going forward")


if __name__ == "__main__":
    main()
