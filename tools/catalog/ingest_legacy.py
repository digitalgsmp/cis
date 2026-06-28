#!/usr/bin/env python3
"""
Ingest all legacy concept files, ChatGPT exports, Claude transcripts,
CIS kernel, SWA files, WIASW spreadsheets into knowledge_messages.

Sources:
  1. ChatGPT export (chatgtp_data.zip) — 187 conversations
  2. Claude chat transcripts — ~135 markdown files
  3. CIS v1 Obsidian vault — ~201 markdown files
  4. CIS kernel (identity, source, build, extraction) — ~478 files
  5. CIS legacy X-files and _archive — ~73 files
  6. PVE Architecture sessions — ~41 files  
  7. CIS ADRs, contracts, handoffs, drafts, ingest
  8. Gemini conversation, Claude standalone files
  9. WIASW spreadsheets (.xlsx)
  10. SWA project files (.md, .py, .txt, .csv)
  11. AI Lab structure notes

Strategy:
  - Chunk large files into messages (max 4000 chars each)
  - Tag source as 'legacy_concept' to distinguish from existing 'archive'/'cis_docs'
  - Deduplicate by source_key (skip files already in knowledge_messages)
  - Insert in batches of 500 for performance
"""
import sqlite3
import os
import sys
import json
import zipfile
import hashlib
from pathlib import Path

DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
CHUNK_SIZE = 4000  # max chars per knowledge_messages row
BATCH_SIZE = 500

# ── Source definitions ──────────────────────────────────────────
SOURCES = [
    # (base_path, source_label, globs, recursive)
    ("/mnt/backup-win/projects-backup/cis/cis_kernel", "cis_kernel", ["*.md", "*.txt", "*.json", "*.yaml", "*.py", "*.cfg"], True),
    ("/mnt/backup-win/projects-backup/cis/docs/ADRs", "cis_adrs", ["*.md"], True),
    ("/mnt/backup-win/projects-backup/cis/docs/contracts", "cis_contracts", ["*.md"], True),
    ("/mnt/backup-win/projects-backup/cis/docs/claude_chat_transcripts", "claude_transcripts", ["*.md", "*.txt"], True),
    ("/mnt/backup-win/projects-backup/cis/docs/CIS_Creative_Intelligence_System_v1", "cis_v1_vault", ["*.md", "*.json", "*.py"], True),
    ("/mnt/backup-win/projects-backup/cis/docs/_archive", "cis_legacy_archive", ["*.md", "*.txt"], True),
    ("/mnt/backup-win/projects-backup/cis/handoff", "cis_handoffs", ["*.md"], True),
    ("/mnt/backup-win/projects-backup/cis/ingest", "cis_ingest", ["*.md", "*.txt"], True),
    ("/mnt/backup-win/projects-backup/cis/drafts", "cis_drafts", ["*.md", "*.txt"], True),
    ("/mnt/backup-win/AI_Lab_StrucutreNotes", "ai_lab_notes", ["*.md", "*.txt"], True),
    ("/mnt/backup-win/PVE_AI_Lab_StructureNotes", "pve_architecture", ["*.md", "*.txt", "*.pdf"], True),
    ("/mnt/backup-win", "backup_standalone", ["*.md", "*.txt"], False),  # root-level files only
    ("/mnt/archive/WIAS", "wiasw", ["*.md", "*.txt", "*.xlsx"], True),
    ("/mnt/projects/swa", "swa_project", ["*.md", "*.txt", "*.py", "*.csv", "*.yaml", "*.json"], True),
]


def get_existing_source_keys(conn):
    """Return set of all source_key values already in knowledge_messages."""
    rows = conn.execute("SELECT DISTINCT source_key FROM knowledge_messages").fetchall()
    return {r[0] for r in rows}


def read_file_content(filepath):
    """Read a file, return text content or None if unreadable/binary."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception:
        return None


def chunk_text(text, max_len=CHUNK_SIZE):
    """Split text into chunks of max_len characters, trying to break at newlines."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while len(text) > max_len:
        # Find last newline within limit
        split_at = text.rfind('\n', 0, max_len)
        if split_at == -1 or split_at < max_len // 2:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip('\n')
    if text:
        chunks.append(text)
    return chunks


def ingest_chatgpt_export(conn, existing_keys, zip_path):
    """Extract and ingest ChatGPT conversations from zip."""
    print(f"\n📦 ChatGPT Export: {zip_path}")
    if not os.path.exists(zip_path):
        print("  SKIP: file not found")
        return 0

    inserted = 0
    with zipfile.ZipFile(zip_path) as zf:
        for fname in sorted(zf.namelist()):
            if not fname.startswith('conversations-') or not fname.endswith('.json'):
                continue
            print(f"  Processing {fname}...")
            with zf.open(fname) as f:
                data = json.load(f)

            batch = []
            for conv in data:
                title = conv.get('title', 'Untitled')[:200]
                conv_id = conv.get('id', conv.get('conversation_id', 'unknown'))
                source_key = f"chatgpt_export/{conv_id}"

                if source_key in existing_keys:
                    continue

                # Extract messages from mapping (ChatGPT export format)
                mapping = conv.get('mapping', {})
                full_text_parts = []
                # Sort by create_time if available, otherwise process in mapping order
                sorted_msgs = sorted(
                    mapping.items(),
                    key=lambda x: (x[1].get('message', {}).get('create_time') or 0)
                    if isinstance(x[1], dict) else 0
                )
                for msg_id, msg_node in sorted_msgs:
                    if not isinstance(msg_node, dict):
                        continue
                    msg = msg_node.get('message')
                    if not msg:
                        continue
                    author = msg.get('author', {})
                    role = author.get('role', 'unknown') if isinstance(author, dict) else 'unknown'
                    content = msg.get('content', {})
                    if isinstance(content, dict):
                        parts = content.get('parts', [])
                        text = ' '.join(str(p) for p in parts if isinstance(p, str))
                    elif isinstance(content, str):
                        text = content
                    else:
                        text = str(content)
                    if text.strip():
                        full_text_parts.append(f"[{role}] {text}")

                full_text = f"# {title}\n\n" + '\n\n'.join(full_text_parts)

                # Chunk
                chunks = chunk_text(full_text)
                for i, chunk in enumerate(chunks):
                    batch.append((
                        chunk,
                        'chatgpt_export',
                        'chatgpt_conversation',
                        source_key,
                    ))

                if len(batch) >= BATCH_SIZE:
                    conn.executemany(
                        "INSERT INTO knowledge_messages (content, source, role, source_key) VALUES (?, ?, ?, ?)",
                        batch,
                    )
                    inserted += len(batch)
                    batch = []
                    print(f"    {inserted} messages inserted...")

            # Flush remaining
        if batch:
            conn.executemany(
                "INSERT INTO knowledge_messages (content, source, role, source_key) VALUES (?, ?, ?, ?)",
                batch,
            )
            inserted += len(batch)

    print(f"  ✅ ChatGPT: {inserted} messages ingested")
    return inserted


def ingest_file_sources(conn, existing_keys):
    """Ingest all file-based sources defined in SOURCES list."""
    total = 0
    skipped = 0

    for base_path, source_label, globs, recursive in SOURCES:
        if not os.path.exists(base_path):
            print(f"\n⚠️  {source_label}: path not found — {base_path}")
            continue

        print(f"\n📁 {source_label}: {base_path}")
        files = []
        for g in globs:
            pattern = f"**/{g}" if recursive else g
            found = list(Path(base_path).glob(pattern))
            files.extend(found)

        # Deduplicate
        files = list(set(files))
        print(f"  Found {len(files)} files")

        batch = []
        file_count = 0

        for filepath in sorted(files):
            rel_path = str(filepath.relative_to(base_path))
            source_key = f"{source_label}/{rel_path}"

            if source_key in existing_keys:
                skipped += 1
                continue

            content = read_file_content(str(filepath))
            if content is None or not content.strip():
                continue

            # Determine role from extension/path
            ext = filepath.suffix.lower()
            if ext == '.py':
                role = 'code'
            elif ext == '.json':
                role = 'data'
            elif ext in ('.xlsx', '.xlsb', '.csv'):
                role = 'spreadsheet'
            elif ext == '.yaml' or ext == '.cfg':
                role = 'config'
            elif ext == '.pdf':
                role = 'document'
            else:
                role = 'document'

            chunks = chunk_text(content)
            for i, chunk in enumerate(chunks):
                batch.append((
                    chunk,
                    source_label,
                    role,
                    source_key,
                ))

            file_count += 1
            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT INTO knowledge_messages (content, source, role, source_key) VALUES (?, ?, ?, ?)",
                    batch,
                )
                total += len(batch)
                batch = []
                print(f"    {file_count} files, {total} messages...")

        # Flush remaining
        if batch:
            conn.executemany(
                "INSERT INTO knowledge_messages (content, source, role, source_key) VALUES (?, ?, ?, ?)",
                batch,
            )
            total += len(batch)

        print(f"  ✅ {source_label}: {file_count} files → {len(batch) if batch else 0} messages (this batch)")

    print(f"\n📊 Total file-source messages: {total}, Skipped (already ingested): {skipped}")
    return total


def rebuild_fts(conn):
    """Rebuild the FTS5 index."""
    print("\n🔨 Rebuilding FTS5 index...")
    conn.execute("INSERT INTO knowledge_messages_fts(knowledge_messages_fts) VALUES('rebuild')")
    conn.commit()
    print("  ✅ FTS5 index rebuilt")


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    print("=" * 60)
    print("LEGACY CONCEPT FILE INGESTION")
    print("=" * 60)

    # Get existing keys for dedup
    print("\n🔍 Loading existing source keys...")
    existing = get_existing_source_keys(conn)
    print(f"  {len(existing)} existing source_keys in knowledge_messages")

    total = 0

    # 1. ChatGPT export
    total += ingest_chatgpt_export(
        conn, existing,
        "/mnt/backup-win/chatgtp_data.zip"
    )

    # 2. All file-based sources
    total += ingest_file_sources(conn, existing)

    # 3. Rebuild FTS
    rebuild_fts(conn)

    conn.close()

    print(f"\n{'=' * 60}")
    print(f"✅ INGESTION COMPLETE — {total} new messages")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
