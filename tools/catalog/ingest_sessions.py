#!/usr/bin/env python3
"""
Ingest recent Hermes sessions (last 30 days) into knowledge_messages.
Reads session_*.json from all profile session dirs, chunks user+assistant
messages, deduplicates by source_key, rebuilds FTS5 index.
"""
import sqlite3, os, json, glob, time, hashlib
from datetime import datetime, timedelta

DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
CHUNK_SIZE = 4000
BATCH_SIZE = 500
DAYS_BACK = 30

PROFILES = {
    "prime": os.path.expanduser("~/.hermes/sessions"),
    "v4pro": os.path.expanduser("~/.hermes-v4pro/sessions"),
    "v4impl": os.path.expanduser("~/.hermes-v4impl/sessions"),
    "r1": os.path.expanduser("~/.hermes-r1/sessions"),
    "glm-reviewer": os.path.expanduser("~/.hermes-glm-reviewer/sessions"),
    "brainstorm": os.path.expanduser("~/.hermes-brainstorm/sessions"),
    "qwen": os.path.expanduser("~/.hermes-qwen/sessions"),
    "glm-verifier": os.path.expanduser("~/.hermes-glm-verifier/sessions"),
}

def chunk_text(text, max_len=CHUNK_SIZE):
    if len(text) <= max_len:
        return [text]
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind('\n', 0, max_len)
        if split_at == -1 or split_at < max_len // 2:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip('\n')
    if text:
        chunks.append(text)
    return chunks

def extract_messages(session_data):
    """Extract user+assistant messages from a session JSON."""
    msgs = []
    for m in session_data.get("messages", []):
        role = m.get("role", "")
        if role not in ("user", "assistant"):
            continue
        content = m.get("content", "")
        if isinstance(content, list):
            # content may be list of parts
            content = " ".join(str(p) for p in content if isinstance(p, str))
        elif not isinstance(content, str):
            content = str(content)
        content = content.strip()
        if content and len(content) > 10:
            msgs.append((role, content))
    return msgs

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    cutoff = time.time() - (DAYS_BACK * 86400)

    # Get existing source_keys for dedup
    existing = {r[0] for r in conn.execute("SELECT DISTINCT source_key FROM knowledge_messages").fetchall()}
    print(f"Existing source_keys: {len(existing)}")

    total_inserted = 0
    total_sessions = 0
    total_skipped = 0

    for profile_name, sessions_dir in PROFILES.items():
        if not os.path.isdir(sessions_dir):
            continue
        files = [f for f in glob.glob(os.path.join(sessions_dir, "session_*.json")) if os.path.getmtime(f) > cutoff]
        print(f"\n[{profile_name}] {len(files)} sessions (last {DAYS_BACK}d)")

        batch = []
        profile_inserted = 0

        for fpath in sorted(files):
            session_file = os.path.basename(fpath)
            source_key_base = f"hermes_session/{profile_name}/{session_file.replace('.json','')}"

            # Dedup check - skip if first chunk already exists
            if source_key_base + "/0" in existing:
                total_skipped += 1
                continue

            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                    data = json.load(fh)
            except Exception:
                continue

            msgs = extract_messages(data)
            if not msgs:
                continue

            # Build full text from user+assistant messages
            full_text_parts = []
            for role, content in msgs:
                full_text_parts.append(f"[{role}] {content}")
            full_text = "\n\n".join(full_text_parts)

            chunks = chunk_text(full_text)
            for i, chunk in enumerate(chunks):
                source_key = f"{source_key_base}/{i}"
                if source_key in existing:
                    continue
                batch.append((chunk, f"hermes_{profile_name}", "session", source_key))

            total_sessions += 1

            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT INTO knowledge_messages (content, source, role, source_key) VALUES (?, ?, ?, ?)",
                    batch
                )
                profile_inserted += len(batch)
                total_inserted += len(batch)
                batch = []
                print(f"  {profile_inserted} inserted...")

        # Flush remaining
        if batch:
            conn.executemany(
                "INSERT INTO knowledge_messages (content, source, role, source_key) VALUES (?, ?, ?, ?)",
                batch
            )
            profile_inserted += len(batch)
            total_inserted += len(batch)

        print(f"  [{profile_name}] done: {profile_inserted} messages")

    conn.commit()

    # Rebuild FTS5
    print("\nRebuilding FTS5 index...")
    conn.execute("INSERT INTO knowledge_messages_fts(knowledge_messages_fts) VALUES('rebuild')")
    conn.commit()

    print(f"\n=== INGESTION COMPLETE ===")
    print(f"Sessions processed: {total_sessions}")
    print(f"Sessions skipped (already ingested): {total_skipped}")
    print(f"Messages inserted: {total_inserted}")
    print(f"Total in knowledge_messages: {conn.execute('SELECT count(*) FROM knowledge_messages').fetchone()[0]}")

    conn.close()

if __name__ == "__main__":
    main()
