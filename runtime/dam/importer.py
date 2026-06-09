"""
dam/importer.py — DAM Session File Importer (Tier 7.5b)
Imports Hermes session files into the DAM spine (dam_assets + dam_extracted_text + FTS5).
Handles two formats: session_*.json (newer) and request_dump_*.json (older).
Dedup via SHA256 file hash.
"""

import json
import hashlib
import os
import sys
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Allow running from tools/ or runtime/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db.dam_db import (
    ensure_dam_schema,
    asset_exists_by_hash,
    insert_asset,
    insert_extracted_text_batch,
    dam_stats,
)


def sha256_file(filepath):
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_filename_date(filename):
    """Extract YYYY-MM-DD from filenames like session_20260531_134614_defb30.json
    or request_dump_20260513_093446_7029655f_20260513_110509_664188.json."""
    parts = filename.replace(".json", "").split("_")
    for part in parts:
        if len(part) == 8 and part.isdigit() and part.startswith("202"):
            return f"{part[:4]}-{part[4:6]}-{part[6:8]}"
    return None


def extract_messages(data, filename):
    """Extract messages from a parsed session JSON. Returns list of dicts
    with keys: role, content, timestamp.
    Handles two formats:
      1. New: {messages: [{role, content}, ...], session_start: ...}
      2. Old: {request: {body: {messages: [{role, content}, ...]}}}
    """
    messages = []

    # Format 1: session_*.json — direct messages array
    if "messages" in data and isinstance(data["messages"], list):
        session_start = data.get("session_start")
        for msg in data["messages"]:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                content = msg["content"]
                if content is None:
                    content = ""
                messages.append({
                    "role": msg["role"],
                    "content": str(content),
                    "timestamp": msg.get("timestamp") or session_start,
                })

    # Format 2: request_dump_*.json — messages in request.body.messages
    elif "request" in data and isinstance(data["request"], dict):
        body = data["request"].get("body", {})
        if "messages" in body and isinstance(body["messages"], list):
            timestamp = data.get("timestamp")
            for msg in body["messages"]:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    content = msg["content"]
                    if content is None:
                        content = ""
                    messages.append({
                        "role": msg["role"],
                        "content": str(content),
                        "timestamp": msg.get("timestamp") or timestamp,
                    })

    return messages


def import_directory(conn, directory, source_profile, limit=None, dry_run=False):
    """Import session files from a directory into the DAM.
    Returns dict with import stats.
    """
    directory = Path(directory)
    if not directory.exists():
        print(f"  SKIP: directory not found: {directory}")
        return {"files_scanned": 0, "assets_imported": 0, "texts_inserted": 0, "duplicates_skipped": 0}

    files = sorted(directory.glob("*.json"))
    if not files:
        print(f"  SKIP: no .json files in {directory}")
        return {"files_scanned": 0, "assets_imported": 0, "texts_inserted": 0, "duplicates_skipped": 0}

    scanned = 0
    imported = 0
    texts = 0
    skipped_dup = 0
    skipped_parse = 0

    total = min(len(files), limit) if limit else len(files)
    print(f"  Scanning {total} files from {directory} (profile={source_profile})...")

    for fp in files:
        if limit and imported >= limit:
            break

        scanned += 1
        filename = fp.name
        file_size = fp.stat().st_size

        # Compute hash
        file_hash = sha256_file(str(fp))

        # Dedup check
        if not dry_run and asset_exists_by_hash(conn, file_hash):
            skipped_dup += 1
            if scanned % 50 == 0:
                print(f"    ... {scanned}/{total} scanned, {imported} imported, {skipped_dup} duplicates")
            continue

        # Parse JSON
        try:
            with open(fp, encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            skipped_parse += 1
            continue

        # Extract messages
        messages = extract_messages(data, filename)
        if not messages:
            skipped_parse += 1
            continue

        if dry_run:
            imported += 1
            texts += len(messages)
            continue

        # Extract metadata
        session_id = data.get("session_id")
        session_start = data.get("session_start") or data.get("timestamp")
        inferred_date = parse_filename_date(filename)
        if not session_start and inferred_date:
            session_start = f"{inferred_date}T00:00:00"
        imported_at = datetime.now(timezone.utc).isoformat()

        # Insert asset
        asset_id = insert_asset(
            conn, str(fp), file_hash, file_size, source_profile,
            session_id, session_start, len(messages), imported_at
        )

        # Build text rows
        text_rows = []
        for idx, msg in enumerate(messages):
            ts = msg.get("timestamp") or session_start
            text_rows.append((
                asset_id, idx, msg["role"], msg["content"], ts
            ))

        # Batch insert
        insert_extracted_text_batch(conn, text_rows)
        conn.commit()

        imported += 1
        texts += len(messages)

        if scanned % 10 == 0 or imported % 10 == 0:
            print(f"    ... {scanned}/{total}, {imported} imported, {texts} messages")

    return {
        "files_scanned": scanned,
        "assets_imported": imported,
        "texts_inserted": texts,
        "duplicates_skipped": skipped_dup,
        "parse_failures": skipped_parse,
    }


def run_import(source_dirs, db_path=None, limit_per_dir=None, dry_run=False):
    """Main import entry point.
    source_dirs: list of (directory_path, source_profile) tuples.
    """
    db_path = db_path or "/mnt/projects/cis/data/cis_memory.db"
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_dam_schema(conn)

    total_assets = 0
    total_texts = 0
    total_dupes = 0
    total_scanned = 0

    for directory, profile in source_dirs:
        print(f"\n--- {profile}: {directory} ---")
        result = import_directory(conn, directory, profile, limit=limit_per_dir, dry_run=dry_run)
        total_scanned += result["files_scanned"]
        total_assets += result["assets_imported"]
        total_texts += result["texts_inserted"]
        total_dupes += result["duplicates_skipped"]
        print(f"  Result: {result['assets_imported']} imported, "
              f"{result['duplicates_skipped']} duplicates skipped, "
              f"{result.get('parse_failures', 0)} parse failures")

    print(f"\n=== IMPORT SUMMARY ===")
    print(f"  Files scanned:   {total_scanned}")
    print(f"  Assets imported: {total_assets}")
    print(f"  Texts inserted:  {total_texts}")
    print(f"  Dups skipped:    {total_dupes}")

    stats = dam_stats(conn)
    print(f"  DB assets now:   {stats['assets']}")
    print(f"  DB texts now:    {stats['extracted_text_rows']}")
    print(f"  DB FTS5 rows:    {stats['fts_rows']}")

    conn.close()
    return {
        "scanned": total_scanned,
        "imported": total_assets,
        "texts": total_texts,
        "dupes": total_dupes,
        "db_assets": stats["assets"],
        "db_texts": stats["extracted_text_rows"],
        "db_fts": stats["fts_rows"],
    }


def run_import_from_manifest(manifest_path, db_path=None, limit=None):
    """Import session files from a frozen manifest (one file path per line).
    Deduces source_profile from directory path (e.g., '.../hermes-v4impl/sessions' -> 'v4impl').
    """
    db_path = db_path or "/mnt/projects/cis/data/cis_memory.db"
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_dam_schema(conn)

    # Profile inference from path
    profile_map = {
        "hermes-v4impl": "v4impl",
        "hermes-v4pro": "v4pro",
        "hermes-r1": "r1",
        ".hermes/sessions": "prime",
    }

    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        conn.close()
        return {"scanned": 0, "imported": 0, "texts": 0, "dupes": 0}

    file_paths = [line.strip() for line in manifest_path.read_text().splitlines() if line.strip()]
    total = min(len(file_paths), limit) if limit else len(file_paths)
    print(f"Frozen manifest: {total} files")

    scanned = 0
    imported = 0
    texts = 0
    skipped_dup = 0
    skipped_parse = 0

    for fp in file_paths:
        if limit and imported >= limit:
            break

        fp_path = Path(fp)
        if not fp_path.exists():
            skipped_parse += 1
            continue

        scanned += 1
        file_size = fp_path.stat().st_size

        # Deduce profile
        source_profile = "unknown"
        fp_str = str(fp_path)
        for key, profile in profile_map.items():
            if key in fp_str:
                source_profile = profile
                break

        # Compute hash
        file_hash = sha256_file(fp_str)

        # Dedup check
        if asset_exists_by_hash(conn, file_hash):
            skipped_dup += 1
            continue

        # Parse JSON
        try:
            with open(fp_path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError):
            skipped_parse += 1
            continue

        # Extract messages
        messages = extract_messages(data, fp_path.name)
        if not messages:
            skipped_parse += 1
            continue

        # Extract metadata
        session_id = data.get("session_id")
        session_start = data.get("session_start") or data.get("timestamp")
        inferred_date = parse_filename_date(fp_path.name)
        if not session_start and inferred_date:
            session_start = f"{inferred_date}T00:00:00"
        imported_at = datetime.now(timezone.utc).isoformat()

        # Insert asset
        asset_id = insert_asset(
            conn, fp_str, file_hash, file_size, source_profile,
            session_id, session_start, len(messages), imported_at
        )

        # Build text rows
        text_rows = []
        for idx, msg in enumerate(messages):
            ts = msg.get("timestamp") or session_start
            text_rows.append((asset_id, idx, msg["role"], msg["content"], ts))

        insert_extracted_text_batch(conn, text_rows)
        conn.commit()

        imported += 1
        texts += len(messages)

        if scanned % 500 == 0:
            print(f"    ... {scanned}/{total}, {imported} imported, {skipped_dup} duplicates")

    print(f"\n=== MANIFEST IMPORT SUMMARY ===")
    print(f"  Files scanned:   {scanned}")
    print(f"  Assets imported: {imported}")
    print(f"  Texts inserted:  {texts}")
    print(f"  Dups skipped:    {skipped_dup}")

    stats = dam_stats(conn)
    print(f"  DB assets now:   {stats['assets']}")
    print(f"  DB texts now:    {stats['extracted_text_rows']}")
    print(f"  DB FTS5 rows:    {stats['fts_rows']}")

    conn.close()
    return {
        "scanned": scanned,
        "imported": imported,
        "texts": texts,
        "dupes": skipped_dup,
        "db_assets": stats["assets"],
        "db_texts": stats["extracted_text_rows"],
        "db_fts": stats["fts_rows"],
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DAM Session File Importer")
    parser.add_argument("--manifest", type=str, default=None,
                        help="Path to frozen manifest file (one file path per line)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit import to N files")
    args = parser.parse_args()

    if args.manifest:
        run_import_from_manifest(args.manifest, limit=args.limit)
    else:
        source_dirs = [
            ("/home/eric/.hermes/sessions", "prime"),
            ("/home/eric/.hermes-v4impl/sessions", "v4impl"),
            ("/home/eric/.hermes-r1/sessions", "r1"),
            ("/home/eric/.hermes-v4pro/sessions", "v4pro"),
        ]
        run_import(source_dirs, limit_per_dir=args.limit)
