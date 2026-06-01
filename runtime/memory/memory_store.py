"""
memory_store.py — CIS Unified Memory Core.

Hybrid SQLite + ChromaDB for persistent agent recall.
- SQLite is the canonical store: memory_records, memory_sessions tables
- ChromaDB is the recall layer: vectors for semantic search
- Both point to the same data; SQLite is source of truth

Usage:
    from memory.memory_store import MemoryStore
    ms = MemoryStore()
    ms.ensure_tables()
    ms.store_record(category='decision', summary='...', detail='...')
    results = ms.query_relevant("what did we decide about OCR", limit=5)
"""

import sqlite3
import json
import os
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────
RUNTIME_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = RUNTIME_DIR.parent
MEMORY_DIR = PROJECT_DIR / "memory"
DB_PATH = MEMORY_DIR / "cis_memory.db"
CHROMA_DIR = MEMORY_DIR / "chromadb"

# ── SQLite schema ───────────────────────────────────────────────────────

SCHEMA_MEMORY_RECORDS = """
CREATE TABLE IF NOT EXISTS memory_records (
    record_id TEXT PRIMARY KEY,
    session_id TEXT,
    category TEXT NOT NULL,          -- decision, correction, preference, current_state, project_fact, archive_note
    domain TEXT,                     -- creative, technical, socialcare, personal, cis, swa
    tags TEXT,                       -- comma-separated
    summary TEXT NOT NULL,           -- short (1-2 sentence)
    detail TEXT,                     -- full context (optional)
    source_type TEXT,                -- session, extraction, manual, archive
    source_path TEXT,                -- file path or session reference
    importance INTEGER DEFAULT 1,    -- 1-5, for prioritization
    created_at TEXT,
    updated_at TEXT
)
"""

SCHEMA_MEMORY_SESSIONS = """
CREATE TABLE IF NOT EXISTS memory_sessions (
    session_id TEXT PRIMARY KEY,
    platform TEXT,
    started_at TEXT,
    last_active TEXT,
    message_count INTEGER,
    extracted_at TEXT,
    status TEXT DEFAULT 'pending',   -- pending, extracting, done, failed
    error TEXT
)
"""

SCHEMA_MEMORY_ARCHIVE = """
CREATE TABLE IF NOT EXISTS memory_archive_files (
    path TEXT PRIMARY KEY,
    filename TEXT,
    domain TEXT,
    category TEXT,
    checksum TEXT,
    size_bytes INTEGER,
    indexed_at TEXT,
    status TEXT DEFAULT 'pending'    -- pending, indexed, failed
)
"""

INDEX_RECORDS = [
    "CREATE INDEX IF NOT EXISTS idx_memory_records_category ON memory_records(category)",
    "CREATE INDEX IF NOT EXISTS idx_memory_records_domain ON memory_records(domain)",
    "CREATE INDEX IF NOT EXISTS idx_memory_records_source ON memory_records(source_type)",
    "CREATE INDEX IF NOT EXISTS idx_memory_records_created ON memory_records(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_memory_sessions_status ON memory_sessions(status)",
]


# ── Embedding ───────────────────────────────────────────────────────────

def _get_chroma_collection():
    """Lazy-load ChromaDB client and get/create the unified_memory collection."""
    import chromadb
    chroma_dir = str(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=chroma_dir)
    try:
        collection = client.get_collection("unified_memory")
    except Exception:
        collection = client.create_collection(
            name="unified_memory",
            metadata={
                "description": "CIS Unified Memory — all agent-accessible knowledge",
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 20,
                "hnsw:M": 8,
                "hnsw:search_ef": 40,
                "hnsw:num_threads": 1,
            }
        )
    return collection


# ── MemoryStore class ───────────────────────────────────────────────────

class MemoryStore:
    """Hybrid SQLite + ChromaDB memory store.
    
    SQLite: canonical storage, structured queries, audit trail.
    ChromaDB: semantic search, fuzzy recall.
    """

    def __init__(self, db_path=None):
        self._db_path = str(db_path or DB_PATH)
        self._conn = None
        self._chroma = None

    # ── Connection ──────────────────────────────────────────────────

    @property
    def conn(self):
        if self._conn is None:
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def ensure_tables(self):
        """Create tables if they don't exist."""
        cur = self.conn.cursor()
        cur.execute(SCHEMA_MEMORY_RECORDS)
        cur.execute(SCHEMA_MEMORY_SESSIONS)
        cur.execute(SCHEMA_MEMORY_ARCHIVE)
        for idx in INDEX_RECORDS:
            cur.execute(idx)
        self.conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Embeddings ──────────────────────────────────────────────────

    @property
    def chroma(self):
        if self._chroma is None:
            self._chroma = _get_chroma_collection()
        return self._chroma

    def _make_vector_id(self, record_id):
        """Deterministic UUID-based vector ID from record_id."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"cis-memory::{record_id}"))

    # ── Store records ───────────────────────────────────────────────

    def store_record(self, *, category, summary, detail="", domain="",
                     tags="", source_type="manual", source_path="",
                     session_id="", importance=1):
        """Store a memory record in SQLite and index into ChromaDB.
        
        Returns the record_id.
        """
        record_id = f"mem_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        # SQLite
        self.conn.execute("""
            INSERT OR REPLACE INTO memory_records
                (record_id, session_id, category, domain, tags, summary, detail,
                 source_type, source_path, importance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record_id, session_id, category, domain, tags, summary, detail,
              source_type, source_path, importance, now, now))
        self.conn.commit()

        # ChromaDB
        try:
            text_for_embedding = f"{category}: {summary}"
            if detail:
                text_for_embedding += f"\n{detail}"
            vid = self._make_vector_id(record_id)
            self.chroma.upsert(
                ids=[vid],
                metadatas=[{
                    "record_id": record_id,
                    "category": category,
                    "domain": domain,
                    "source_type": source_type,
                    "session_id": session_id,
                    "importance": importance,
                    "timestamp": now,
                }],
                documents=[text_for_embedding],
            )
        except Exception as e:
            # On disk I/O error, reset the chroma client and retry once
            err_str = str(e)
            if "disk I/O error" in err_str or "RustBindingsAPI" in err_str:
                try:
                    self._chroma = None  # Force re-init
                    self.chroma.upsert(
                        ids=[vid],
                        metadatas=[{
                            "record_id": record_id,
                            "category": category,
                            "domain": domain,
                            "source_type": source_type,
                            "session_id": session_id,
                            "importance": importance,
                            "timestamp": now,
                        }],
                        documents=[text_for_embedding],
                    )
                except Exception as e2:
                    print(f"[memory] ChromaDB index error (retry failed): {e2}")
            else:
                print(f"[memory] ChromaDB index warning: {e}")

        return record_id

    def store_extraction_as_record(self, spine_row, node_rows):
        """Convert an extraction spine + nodes into memory records.
        
        spine_row: dict from knowledge_spines table
        node_rows: list of dicts from spine_nodes table
        """
        spine_id = spine_row["spine_id"]
        subject = spine_row.get("subject", "")
        domain = spine_row.get("domain", "")
        sub_domain = spine_row.get("sub_domain", "")
        node_count = spine_row.get("node_count", 0)

        summary = f"Extraction: {subject} ({sub_domain}) — {node_count} discoveries"
        detail_parts = []
        for node in node_rows[:8]:  # cap at 8 for context window
            title = node.get("title", "")
            detail_parts.append(title)
        if node_rows and len(node_rows) > 8:
            detail_parts.append(f"... and {len(node_rows) - 8} more discoveries")

        detail = "\n".join(detail_parts)
        tags = f"extraction,{sub_domain}"
        if domain:
            tags += f",{domain}"

        return self.store_record(
            category="extraction",
            domain=domain.lower() if domain else "",
            tags=tags,
            summary=summary,
            detail=detail,
            source_type="extraction",
            source_path=spine_row.get("file_path", ""),
            session_id="",
            importance=2,
        )

    def store_session_record(self, session_data, extracted_nodes):
        """Store extracted session data as memory records.
        
        session_data: dict with session_id, platform, message_count, etc.
        extracted_nodes: list of dicts with category, summary, detail, etc.
        """
        sid = session_data.get("session_id", "unknown")
        platform = session_data.get("platform", "cli")

        # Mark session as processed
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute("""
            INSERT OR REPLACE INTO memory_sessions
                (session_id, platform, started_at, last_active, message_count,
                 extracted_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sid, platform,
              session_data.get("session_start", ""),
              session_data.get("last_updated", ""),
              session_data.get("message_count", 0),
              now, "done"))
        self.conn.commit()

        # Store each extracted node as a memory record
        count = 0
        for node in extracted_nodes:
            self.store_record(
                category=node.get("category", "current_state"),
                domain=node.get("domain", ""),
                tags=node.get("tags", ""),
                summary=node.get("summary", ""),
                detail=node.get("detail", ""),
                source_type="session",
                source_path=node.get("source_path", ""),
                session_id=sid,
                importance=node.get("importance", 1),
            )
            count += 1

        return count

    # ── Query ───────────────────────────────────────────────────────

    def query_relevant(self, query="", limit=8, category=None, domain=None,
                       min_importance=1):
        """Query ChromaDB for semantically relevant memory records.
        
        Returns list of dicts with record_id, summary, detail, category, etc.
        Falls back to SQLite if ChromaDB fails.
        """
        try:
            # Build filter if specified
            where_filter = {}
            if category:
                where_filter["category"] = category
            if domain:
                where_filter["domain"] = domain
            if min_importance > 1:
                # ChromaDB doesn't support numeric filters easily with this setup
                pass

            if query:
                results = self.chroma.query(
                    query_texts=[query],
                    n_results=min(limit * 2, 20),
                    where=where_filter or None,
                )
            else:
                # No query = return most recent via ChromaDB (get all)
                results = self.chroma.get(limit=limit)

            if not results or not results.get("ids") or not results["ids"][0]:
                return self._fallback_query(category=category, domain=domain, limit=limit)

            # Map vector results back to SQLite for full records
            metadatas = results["metadatas"][0] if isinstance(results["metadatas"][0], list) else results["metadatas"]
            record_ids = [m.get("record_id", "") for m in metadatas if isinstance(m, dict)]
            distances = results["distances"][0] if results.get("distances") else [0] * len(record_ids)

            records = self._get_records_by_ids(record_ids)
            
            # Attach relevance scores
            for i, rec in enumerate(records):
                if i < len(distances):
                    rec["_relevance"] = round(float(distances[i]), 4)
            
            return records

        except Exception as e:
            print(f"[memory] ChromaDB query error: {e}")
            return self._fallback_query(category=category, domain=domain, limit=limit)

    def query_recent(self, limit=10, category=None):
        """Get most recent memory records from SQLite (no vector query).
        Used for session-start context injection.
        """
        sql = "SELECT * FROM memory_records WHERE 1=1"
        params = []
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cur = self.conn.cursor()
        rows = cur.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def _fallback_query(self, category=None, domain=None, limit=8):
        """Fallback when ChromaDB is unavailable — just use SQLite."""
        sql = "SELECT * FROM memory_records WHERE 1=1"
        params = []
        if category:
            sql += " AND category = ?"
            params.append(category)
        if domain:
            sql += " AND domain = ?"
            params.append(domain)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cur = self.conn.cursor()
        rows = cur.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def _get_records_by_ids(self, record_ids):
        """Fetch full records from SQLite by record_id list."""
        if not record_ids:
            return []
        placeholders = ",".join("?" * len(record_ids))
        cur = self.conn.cursor()
        rows = cur.execute(
            f"SELECT * FROM memory_records WHERE record_id IN ({placeholders})",
            record_ids
        ).fetchall()
        # Preserve the order of record_ids
        id_map = {r["record_id"]: dict(r) for r in rows}
        return [id_map.get(rid) for rid in record_ids if rid in id_map]

    # ── Queue management ────────────────────────────────────────────

    def get_unprocessed_sessions(self):
        """Get session files not yet processed by the memory pipeline."""
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT session_id, platform FROM memory_sessions WHERE status IN ('pending', 'failed')"
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_session_failed(self, session_id, error):
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE memory_sessions SET status='failed', error=?, extracted_at=? WHERE session_id=?",
            (str(error)[:500], now, session_id)
        )
        self.conn.commit()

    def get_stats(self):
        """Get simple stats about the memory store."""
        cur = self.conn.cursor()
        records = cur.execute("SELECT COUNT(*) FROM memory_records").fetchone()[0]
        sessions = cur.execute("SELECT COUNT(*) FROM memory_sessions").fetchone()[0]
        pending = cur.execute(
            "SELECT COUNT(*) FROM memory_sessions WHERE status='pending'"
        ).fetchone()[0]
        chroma_count = 0
        try:
            chroma_count = self.chroma.count()
        except Exception:
            pass
        return {
            "memory_records": records,
            "memory_sessions": sessions,
            "pending_sessions": pending,
            "chroma_vectors": chroma_count,
        }

    def get_recent_activity(self, limit=15):
        """Get most recent memory records across all categories, for use as prefill context."""
        cur = self.conn.cursor()
        rows = cur.execute("""
            SELECT record_id, category, domain, summary, detail, source_type, importance, created_at
            FROM memory_records
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# ── Standalone usage ────────────────────────────────────────────────────

if __name__ == "__main__":
    ms = MemoryStore()
    ms.ensure_tables()
    stats = ms.get_stats()
    print(f"Memory store initialized.")
    print(f"  Records: {stats['memory_records']}")
    print(f"  Sessions: {stats['memory_sessions']}")
    print(f"  Pending: {stats['pending_sessions']}")
    print(f"  Chroma vectors: {stats['chroma_vectors']}")
