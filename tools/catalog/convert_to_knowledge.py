#!/usr/bin/env python3
"""
Convert Claude export + CIS docs + archive text → knowledge_messages.
Inserts into cis_memory.db with FTS5 indexing (triggers auto-sync).
"""
import json
import os
import sqlite3
import sys
from datetime import datetime

DB_PATH = "/mnt/projects/cis/data/cis_memory.db"


def insert_message(conn, role, content, source, source_key=None, timestamp=None):
    """Insert one message into knowledge_messages."""
    conn.execute(
        """INSERT INTO knowledge_messages (role, content, source, source_key, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        (role, content, source, source_key, timestamp),
    )


def convert_claude_export(conn, path):
    """Convert Anthropic Claude export JSON to knowledge_messages."""
    print(f"Converting Claude export: {path}")
    with open(path) as f:
        data = json.load(f)

    count = 0
    for i, conv in enumerate(data):
        name = conv.get("name", f"conv-{i}")
        uuid = conv.get("uuid", "")
        created_at = conv.get("created_at", "")[:19]
        messages = conv.get("chat_messages", [])

        for msg in messages:
            sender = msg.get("sender", "")
            text = msg.get("text", "").strip()
            if not text:
                continue
            role = "human" if sender == "human" else "assistant"
            insert_message(
                conn, role, text, "claude_export",
                source_key=f"{uuid}:{name[:60]}", timestamp=created_at,
            )
            count += 1

    print(f"  Inserted {count} messages from {len(data)} conversations")
    return count


def convert_cis_docs(conn, docs_dir):
    """Convert CIS markdown docs to knowledge_messages."""
    print(f"Converting CIS docs: {docs_dir}")
    count = 0
    for root, dirs, files in os.walk(docs_dir):
        # Skip some directories
        dirs[:] = [d for d in dirs if d not in ("diagrams", "audits", ".git")]
        for fname in files:
            if not fname.endswith((".md", ".txt")):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath) as f:
                    content = f.read()
            except Exception:
                continue
            if not content.strip():
                continue

            relpath = os.path.relpath(fpath, docs_dir)
            # Split long docs into paragraphs
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            if len(paragraphs) > 20:
                # Large doc: insert as sections
                for pi, para in enumerate(paragraphs):
                    insert_message(
                        conn, "document", para, "cis_docs",
                        source_key=f"{relpath}:{pi}",
                    )
                    count += 1
            else:
                # Small doc: one message
                insert_message(
                    conn, "document", content, "cis_docs",
                    source_key=relpath,
                )
                count += 1

    print(f"  Inserted {count} messages from CIS docs")
    return count


def convert_archive_text(conn, archive_dir):
    """Convert archive text files to knowledge_messages."""
    print(f"Converting archive text: {archive_dir}")
    count = 0
    text_extensions = {".txt", ".md", ".json", ".csv", ".html", ".log", ".py", ".js", ".jsx", ".css", ".yaml", ".yml", ".toml", ".sh", ".xml"}

    for root, dirs, files in os.walk(archive_dir):
        # Skip large binary directories
        dirs[:] = [d for d in dirs if d not in ("lost+found", ".Trash-0", "models_temp", "cis_hcp_upload_backups", "cis_profile_backups", "cis_stale_context_packs_20260607")]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in text_extensions:
                continue
            fpath = os.path.join(root, fname)
            # Skip files > 1MB (likely data dumps)
            try:
                size = os.path.getsize(fpath)
                if size > 1_000_000:
                    continue
            except Exception:
                continue
            try:
                with open(fpath, errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
            if not content.strip():
                continue

            relpath = os.path.relpath(fpath, archive_dir)
            insert_message(
                conn, "document", content[:50000], "archive",
                source_key=relpath,
            )
            count += 1

    print(f"  Inserted {count} messages from archive")
    return count


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    total = 0

    # Claude export
    claude_path = "/mnt/archive/anthropic_exports/Anthropic_Data_Export_260625/conversations.json"
    if os.path.exists(claude_path):
        n = convert_claude_export(conn, claude_path)
        total += n
        conn.commit()

    # CIS docs
    docs_dir = "/mnt/projects/cis/docs"
    if os.path.exists(docs_dir):
        n = convert_cis_docs(conn, docs_dir)
        total += n
        conn.commit()

    # Archive text
    archive_dir = "/mnt/archive"
    if os.path.exists(archive_dir):
        n = convert_archive_text(conn, archive_dir)
        total += n
        conn.commit()

    # Verify
    row_count = conn.execute("SELECT COUNT(*) FROM knowledge_messages").fetchone()[0]
    fts_count = conn.execute("SELECT COUNT(*) FROM knowledge_messages_fts").fetchone()[0]
    sources = conn.execute(
        "SELECT source, COUNT(*) FROM knowledge_messages GROUP BY source"
    ).fetchall()

    print(f"\n═══ CONVERSION COMPLETE ═══")
    print(f"Total messages: {row_count}")
    print(f"FTS5 indexed: {fts_count}")
    for src, cnt in sources:
        print(f"  {src}: {cnt}")

    conn.close()


if __name__ == "__main__":
    main()
