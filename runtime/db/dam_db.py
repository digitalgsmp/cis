"""
dam_db.py — DAM Database Layer (Tier 7.5b)
Schema application, asset existence checks, text insert, and FTS5 search.
"""

import sqlite3
import os
from pathlib import Path

# Database path — same spine as the rest of CIS
DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
MIGRATION_PATH = "/mnt/projects/cis/runtime/schema/migrations/0003_dam.sql"


def ensure_dam_schema(conn):
    """Idempotent: apply 0003_dam.sql if dam_assets table doesn't exist."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='dam_assets'"
    )
    if cursor.fetchone() is None:
        migration_sql = Path(MIGRATION_PATH).read_text()
        conn.executescript(migration_sql)
        conn.commit()


def asset_exists_by_hash(conn, file_hash):
    """Return True if an asset with this file_hash already exists (dedup check)."""
    row = conn.execute(
        "SELECT 1 FROM dam_assets WHERE file_hash = ? LIMIT 1", (file_hash,)
    ).fetchone()
    return row is not None


def insert_asset(conn, file_path, file_hash, file_size, source_profile,
                 session_id, session_start, message_count, imported_at):
    """Insert one asset row. Returns the new asset_id."""
    cursor = conn.execute(
        """INSERT INTO dam_assets
           (file_path, file_hash, file_size, source_profile, session_id,
            session_start, message_count, imported_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (file_path, file_hash, file_size, source_profile, session_id,
         session_start, message_count, imported_at)
    )
    return cursor.lastrowid


def insert_extracted_text_batch(conn, rows):
    """Insert multiple extracted_text rows efficiently.
    rows: list of (asset_id, segment_index, speaker_role, content_text, created_at)
    Returns count inserted.
    """
    conn.executemany(
        """INSERT INTO dam_extracted_text
           (asset_id, segment_index, speaker_role, content_text, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        rows
    )
    return len(rows)


def search_fts(conn, query, speaker_filter=None, limit=20, offset=0):
    """Run FTS5 search over dam_extracted_text_fts.
    Returns list of dicts with source references.
    """
    if speaker_filter:
        sql = """
            SELECT
                t.id AS text_id,
                t.asset_id,
                t.segment_index,
                t.speaker_role,
                snippet(dam_extracted_text_fts, 0, '<mark>', '</mark>', '…', 40) AS snippet,
                t.content_text,
                a.file_path,
                a.source_profile,
                a.session_id,
                a.session_start
            FROM dam_extracted_text_fts f
            JOIN dam_extracted_text t ON f.rowid = t.id
            JOIN dam_assets a ON t.asset_id = a.id
            WHERE dam_extracted_text_fts MATCH ?
              AND t.speaker_role = ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        params = (query, speaker_filter, limit, offset)
    else:
        sql = """
            SELECT
                t.id AS text_id,
                t.asset_id,
                t.segment_index,
                t.speaker_role,
                snippet(dam_extracted_text_fts, 0, '<mark>', '</mark>', '…', 40) AS snippet,
                t.content_text,
                a.file_path,
                a.source_profile,
                a.session_id,
                a.session_start
            FROM dam_extracted_text_fts f
            JOIN dam_extracted_text t ON f.rowid = t.id
            JOIN dam_assets a ON t.asset_id = a.id
            WHERE dam_extracted_text_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        params = (query, limit, offset)

    rows = conn.execute(sql, params).fetchall()
    results = []
    for row in rows:
        results.append({
            "text_id": row[0],
            "asset_id": row[1],
            "segment_index": row[2],
            "speaker_role": row[3],
            "snippet": row[4],
            "content_text": row[5][:500],  # Truncate for API response
            "source_file": row[6],
            "source_profile": row[7],
            "session_id": row[8],
            "inferred_date": row[9][:10] if row[9] else None,  # YYYY-MM-DD
        })
    return results


def count_fts(conn, query, speaker_filter=None):
    """Return total match count for an FTS5 query."""
    if speaker_filter:
        sql = """
            SELECT COUNT(*)
            FROM dam_extracted_text_fts f
            JOIN dam_extracted_text t ON f.rowid = t.id
            WHERE dam_extracted_text_fts MATCH ?
              AND t.speaker_role = ?
        """
        row = conn.execute(sql, (query, speaker_filter)).fetchone()
    else:
        sql = """
            SELECT COUNT(*)
            FROM dam_extracted_text_fts f
            WHERE dam_extracted_text_fts MATCH ?
        """
        row = conn.execute(sql, (query,)).fetchone()
    return row[0] if row else 0


def dam_stats(conn):
    """Return aggregate stats for reporting."""
    assets = conn.execute("SELECT COUNT(*) FROM dam_assets").fetchone()[0]
    texts = conn.execute("SELECT COUNT(*) FROM dam_extracted_text").fetchone()[0]
    fts_count = conn.execute("SELECT COUNT(*) FROM dam_extracted_text_fts").fetchone()[0]
    profiles = conn.execute(
        "SELECT source_profile, COUNT(*) FROM dam_assets GROUP BY source_profile"
    ).fetchall()
    return {
        "assets": assets,
        "extracted_text_rows": texts,
        "fts_rows": fts_count,
        "by_profile": dict(profiles),
    }
