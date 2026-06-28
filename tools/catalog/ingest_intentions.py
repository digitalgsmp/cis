#!/usr/bin/env python3
"""Phase 7 Ingestion: Intent Alignment → SQLite Fast DB + Chroma VDB

Reads tagged output files (directive v3.1 format), extracts intention items,
and writes CONFIRMED intentions to both the SQLite spine and ChromaDB.

Usage:
    python3 tools/catalog/ingest_intentions.py --dry-run
    python3 tools/catalog/ingest_intentions.py --tagged-dir enforcement/mwl-proof-v2/tagging_results/
    python3 tools/catalog/ingest_intentions.py --all
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
CHROMA_PATH = "/mnt/projects/cis/data/chroma_data"
TAGGING_RESULTS_DIR = "/mnt/projects/cis/enforcement/mwl-proof-v2/tagging_results"


# ── SQLite Schema ──────────────────────────────────────────────────────────

MIGRATION_SQL = """
-- Phase 7: Intent Alignment tables
-- Migration 0014: intent_map, anti_patterns, functional_spec, reviewer_brief

CREATE TABLE IF NOT EXISTS intent_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_text TEXT NOT NULL,
    model_interpretation TEXT,
    mapped_layer TEXT,
    mapped_component TEXT,
    source_file TEXT NOT NULL,
    source_line INTEGER,
    source_timestamp TEXT,
    voice TEXT NOT NULL DEFAULT 'eric-verbatim',
    categories TEXT,
    review_decision TEXT NOT NULL DEFAULT 'CONFIRMED',
    revision_note TEXT,
    eric_confirmed_at TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_intent_map_layer ON intent_map(mapped_layer);
CREATE INDEX IF NOT EXISTS idx_intent_map_component ON intent_map(mapped_component);
CREATE INDEX IF NOT EXISTS idx_intent_map_voice ON intent_map(voice);

CREATE TABLE IF NOT EXISTS anti_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eric_asked TEXT,
    model_produced TEXT,
    friction_type TEXT,
    guardrail_mechanism TEXT,
    source_file TEXT NOT NULL,
    source_line INTEGER,
    failure_flag TEXT,
    review_decision TEXT NOT NULL DEFAULT 'CONFIRMED',
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_anti_patterns_flag ON anti_patterns(failure_flag);
CREATE INDEX IF NOT EXISTS idx_anti_patterns_friction ON anti_patterns(friction_type);

CREATE TABLE IF NOT EXISTS functional_spec (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    layer TEXT NOT NULL,
    description TEXT,
    wiasw_origin TEXT,
    intent_source_ids TEXT,
    build_status TEXT DEFAULT 'unspecified',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_functional_spec_layer ON functional_spec(layer);
CREATE INDEX IF NOT EXISTS idx_functional_spec_component ON functional_spec(component_name);

CREATE TABLE IF NOT EXISTS reviewer_brief (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterion TEXT NOT NULL,
    category TEXT NOT NULL,
    detail TEXT,
    source_file TEXT,
    source_line INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_reviewer_brief_category ON reviewer_brief(category);
"""


# ── Tagged File Parser ────────────────────────────────────────────────────

def parse_tagged_file(filepath):
    """Parse v2/v3.1 tagged output file into a list of tagged blocks.

    Format: text block, then ---, then metadata block, then ---, repeat.
    Pairs each text block with the metadata that follows it.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split on --- lines (with newlines around them)
    parts = re.split(r'\n---\n', content)

    results = []
    # Walk through parts in pairs: text part, then metadata part
    i = 0
    while i < len(parts) - 1:
        text_block = parts[i].strip()
        meta_block = parts[i + 1].strip()

        # Skip header/intro blocks (no metadata fields)
        has_meta = any(meta_block.startswith(k) for k in
                       ['SPEAKER:', 'VOICE:', 'SUBJECT:', 'CATEGORIES:',
                        'BUILD TARGET:', 'FUNCTIONALITY:', 'INTENT:',
                        'FAILURE FLAG:', 'INTENT (if'])
        if not has_meta:
            i += 1
            continue

        if not text_block or len(text_block) < 10:
            i += 2
            continue

        fields = {
            'speaker': '', 'voice': '', 'subject': '', 'categories': '',
            'build_target': '', 'functionality': '', 'intent': '',
            'failure_flag': '', 'text': text_block,
        }

        for line in meta_block.split('\n'):
            line = line.strip()
            if line.startswith('SPEAKER:'):
                fields['speaker'] = line.split(':', 1)[1].strip()
            elif line.startswith('VOICE:'):
                fields['voice'] = line.split(':', 1)[1].strip()
            elif line.startswith('SUBJECT:'):
                fields['subject'] = line.split(':', 1)[1].strip()
            elif line.startswith('CATEGORIES:'):
                fields['categories'] = line.split(':', 1)[1].strip()
            elif line.startswith('BUILD TARGET:'):
                fields['build_target'] = line.split(':', 1)[1].strip()
            elif line.startswith('FUNCTIONALITY:'):
                fields['functionality'] = line.split(':', 1)[1].strip()
            elif line.startswith('INTENT (if'):
                fields['intent'] = line.split(':', 1)[1].strip()
            elif line.startswith('INTENT:'):
                fields['intent'] = line.split(':', 1)[1].strip()
            elif line.startswith('FAILURE FLAG (if'):
                fields['failure_flag'] = line.split(':', 1)[1].strip()
            elif line.startswith('FAILURE FLAG:'):
                fields['failure_flag'] = line.split(':', 1)[1].strip()

        results.append(fields)
        i += 2

    return results


# ── Ingestion Logic ───────────────────────────────────────────────────────

def apply_migration(db_path):
    """Create Phase 7 tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    conn.executescript(MIGRATION_SQL)
    conn.commit()
    conn.close()
    return True


def ingest_to_sqlite(db_path, tagged_blocks, source_file, dry_run=False):
    """Ingest tagged blocks into SQLite tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    counts = {'intent_map': 0, 'anti_patterns': 0, 'functional_spec': 0, 'reviewer_brief': 0}

    for block in tagged_blocks:
        voice = block.get('voice', '').strip()
        categories = block.get('categories', '').strip()
        build_target = block.get('build_target', '').strip()
        functionality = block.get('functionality', '').strip()
        failure_flag = block.get('failure_flag', '').strip()
        intent = block.get('intent', '').strip()
        text = block.get('text', '').strip()
        subject = block.get('subject', '').strip()

        # ── intent_map: eric-verbatim blocks
        if voice == 'eric-verbatim' and text:
            if not dry_run:
                cursor.execute("""
                    INSERT INTO intent_map (intent_text, model_interpretation,
                        mapped_layer, mapped_component, source_file, voice, categories)
                    VALUES (?, ?, ?, ?, ?, 'eric-verbatim', ?)
                """, (text, intent, build_target, functionality, source_file, categories))
            counts['intent_map'] += 1

        # ── anti_patterns: blocks with failure flags
        if failure_flag and failure_flag not in ('none', 'n/a', 'NA', '-', ''):
            if not dry_run:
                cursor.execute("""
                    INSERT INTO anti_patterns (eric_asked, model_produced,
                        friction_type, source_file, failure_flag)
                    VALUES (?, ?, ?, ?, ?)
                """, (text[:500], intent, failure_flag, source_file, failure_flag))
            counts['anti_patterns'] += 1

        # ── functional_spec: blocks mapped to specific components
        if functionality and functionality not in ('none', 'n/a', 'needs Drafter assignment', '', 'N/A'):
            if not dry_run:
                cursor.execute("""
                    INSERT INTO functional_spec (component_name, layer, description)
                    VALUES (?, ?, ?)
                """, (functionality, build_target, text[:1000]))
            counts['functional_spec'] += 1

        # ── reviewer_brief: reviewer-measurement blocks
        if build_target == 'reviewer-measurement' or 'reviewer-brief' in categories or 'measurement-criteria' in categories:
            if not dry_run:
                cursor.execute("""
                    INSERT INTO reviewer_brief (criterion, category, detail, source_file)
                    VALUES (?, ?, ?, ?)
                """, (subject, categories, text[:1000], source_file))
            counts['reviewer_brief'] += 1

    if not dry_run:
        conn.commit()
    conn.close()
    return counts


def setup_chroma(chroma_path):
    """Initialize ChromaDB with intent_memory and anti_patterns collections."""
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False))

    collections = {}
    for name in ['intent_memory', 'anti_patterns']:
        try:
            col = client.get_collection(name)
            collections[name] = col
        except Exception:
            col = client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            collections[name] = col

    return client, collections


def ingest_to_chroma(collections, tagged_blocks, source_file, dry_run=False):
    """Embed tagged blocks into ChromaDB collections."""
    counts = {'intent_memory': 0, 'anti_patterns': 0}

    for i, block in enumerate(tagged_blocks):
        voice = block.get('voice', '').strip()
        failure_flag = block.get('failure_flag', '').strip()
        text = block.get('text', '').strip()
        categories = block.get('categories', '').strip()
        build_target = block.get('build_target', '').strip()
        functionality = block.get('functionality', '').strip()

        if not text:
            continue

        # ── intent_memory: all eric-verbatim + reviewer-measurement blocks
        if voice == 'eric-verbatim' or build_target == 'reviewer-measurement':
            if not dry_run and 'intent_memory' in collections:
                collections['intent_memory'].add(
                    documents=[text],
                    metadatas=[{
                        'source_file': source_file,
                        'voice': voice,
                        'categories': categories,
                        'build_target': build_target,
                        'functionality': functionality,
                    }],
                    ids=[f"{source_file}_{i}_intent"]
                )
            counts['intent_memory'] += 1

        # ── anti_patterns: blocks with failure flags
        if failure_flag and failure_flag not in ('none', 'n/a', 'NA', '-', ''):
            if not dry_run and 'anti_patterns' in collections:
                collections['anti_patterns'].add(
                    documents=[text],
                    metadatas=[{
                        'source_file': source_file,
                        'failure_flag': failure_flag,
                        'categories': categories,
                    }],
                    ids=[f"{source_file}_{i}_antipat"]
                )
            counts['anti_patterns'] += 1

    return counts


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Phase 7: Ingest tagged intentions into SQLite + ChromaDB')
    parser.add_argument('--dry-run', action='store_true', help='Parse files but do not write')
    parser.add_argument('--tagged-dir', default=TAGGING_RESULTS_DIR, help='Directory with tagged output files')
    parser.add_argument('--all', action='store_true', help='Process all tagged files in dir')
    parser.add_argument('--db', default=DB_PATH, help='SQLite database path')
    parser.add_argument('--chroma', default=CHROMA_PATH, help='ChromaDB path')
    parser.add_argument('--migrate-only', action='store_true', help='Only apply SQLite migration, no ingestion')
    args = parser.parse_args()

    print(f"=== Phase 7: Intent Alignment Ingestion ===\n")
    print(f"Database: {args.db}")
    print(f"ChromaDB: {args.chroma}")
    print(f"Tagged dir: {args.tagged_dir}\n")

    # ── Step 1: Apply migration
    print("[1/4] Applying SQLite migration...")
    apply_migration(args.db)
    # Verify
    conn = sqlite3.connect(args.db)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for t in ['intent_map', 'anti_patterns', 'functional_spec', 'reviewer_brief']:
        status = '✓' if t in tables else '✗'
        print(f"  {status} {t}")
    conn.close()

    if args.migrate_only:
        print("\nMigration complete. Tables created.")
        return

    # ── Step 2: Discover tagged files
    print("\n[2/4] Discovering tagged files...")
    tagged_files = []
    if os.path.isdir(args.tagged_dir):
        for f in os.listdir(args.tagged_dir):
            if f.endswith('.txt'):
                tagged_files.append(os.path.join(args.tagged_dir, f))
    print(f"  Found {len(tagged_files)} tagged files")

    if not tagged_files:
        print("  No tagged files found. Run the tagging pipeline first.")
        return

    # ── Step 3: Parse and ingest
    print("\n[3/4] Parsing and ingesting...")
    total_sqlite = {'intent_map': 0, 'anti_patterns': 0, 'functional_spec': 0, 'reviewer_brief': 0}
    total_chroma = {'intent_memory': 0, 'anti_patterns': 0}

    # Setup ChromaDB (optional — skip if import fails)
    collections = {}
    try:
        client, collections = setup_chroma(args.chroma)
    except (ImportError, ModuleNotFoundError) as e:
        print(f"  ChromaDB skipped (import failed: {e})")
    except Exception as e:
        print(f"  ChromaDB skipped ({e})")

    for tf in tagged_files:
        fname = os.path.basename(tf)
        blocks = parse_tagged_file(tf)
        print(f"  {fname}: {len(blocks)} blocks")

        # Ingest to SQLite
        sql_counts = ingest_to_sqlite(args.db, blocks, fname, dry_run=args.dry_run)
        for k, v in sql_counts.items():
            total_sqlite[k] += v

        # Ingest to ChromaDB
        chroma_counts = ingest_to_chroma(collections, blocks, fname, dry_run=args.dry_run)
        for k, v in chroma_counts.items():
            total_chroma[k] += v

    # ── Step 4: Verify
    print("\n[4/4] Verification")
    print(f"\n  SQLite (fast DB):")
    for table, count in total_sqlite.items():
        print(f"    {table}: {count} rows")
    print(f"\n  ChromaDB (VDB):")
    for col_name, count in total_chroma.items():
        try:
            actual = collections[col_name].count()
            print(f"    {col_name}: {actual} documents ({count} attempted)")
        except Exception as e:
            print(f"    {col_name}: ERROR - {e}")

    # Quick query test
    if not args.dry_run:
        conn = sqlite3.connect(args.db)
        total = conn.execute("SELECT COUNT(*) FROM intent_map").fetchone()[0]
        print(f"\n  ✓ intent_map total: {total} confirmed intentions")
        conn.close()

        try:
            results = collections['intent_memory'].query(query_texts=["checks and balance"], n_results=2)
            print(f"  ✓ ChromaDB query works: {len(results['ids'][0])} results for 'checks and balance'")
        except Exception as e:
            print(f"  ChromaDB query test: {e}")

    print("\n=== Phase 7 ingestion complete ===")


if __name__ == '__main__':
    main()
