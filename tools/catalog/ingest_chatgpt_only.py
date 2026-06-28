#!/usr/bin/env python3
"""Re-run ONLY the ChatGPT export ingestion with fixed mapping parser."""
import sqlite3, json, zipfile, sys
sys.path.insert(0, '/mnt/projects/cis/tools/catalog')
from ingest_legacy import chunk_text, get_existing_source_keys, rebuild_fts

DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
ZIP_PATH = "/mnt/backup-win/chatgtp_data.zip"
BATCH_SIZE = 500

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")

existing = get_existing_source_keys(conn)
print(f"Existing keys: {len(existing)}")

inserted = 0
with zipfile.ZipFile(ZIP_PATH) as zf:
    for fname in sorted(zf.namelist()):
        if not fname.startswith('conversations-') or not fname.endswith('.json'):
            continue
        print(f"Processing {fname}...")
        with zf.open(fname) as f:
            data = json.load(f)
        print(f"  {len(data)} conversations")

        batch = []
        for conv in data:
            title = conv.get('title', 'Untitled')[:200]
            conv_id = conv.get('conversation_id', conv.get('id', 'unknown'))
            source_key = f"chatgpt_export/{conv_id}"

            if source_key in existing:
                continue

            mapping = conv.get('mapping', {})
            full_text_parts = []
            # Filter to only dict entries, then sort by create_time
            valid_msgs = [(k, v) for k, v in mapping.items() if isinstance(v, dict) and v.get('message')]
            sorted_msgs = sorted(
                valid_msgs,
                key=lambda x: (x[1].get('message', {}).get('create_time') or 0)
            )
            for msg_id, msg_node in sorted_msgs:
                msg = msg_node.get('message')
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
            chunks = chunk_text(full_text)
            for chunk in chunks:
                batch.append((chunk, 'chatgpt_export', 'chatgpt_conversation', source_key))

            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT INTO knowledge_messages (content, source, role, source_key) VALUES (?, ?, ?, ?)",
                    batch,
                )
                inserted += len(batch)
                batch = []
                print(f"  {inserted} messages...")

        if batch:
            conn.executemany(
                "INSERT INTO knowledge_messages (content, source, role, source_key) VALUES (?, ?, ?, ?)",
                batch,
            )
            inserted += len(batch)

rebuild_fts(conn)
conn.close()
print(f"DONE: {inserted} ChatGPT messages ingested")
