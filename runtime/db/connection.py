"""
db/connection.py — SQLite connection factory and schema initialisation.
All modules that need the main CIS database import from here.
"""

import sqlite3
from config import DB_PATH


def db_connect():
    """Open and return a connection to the main CIS SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables(conn):
    """
    Create all required tables if they do not already exist.
    Safe to call on every request — uses CREATE TABLE IF NOT EXISTS.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS insights (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            category         TEXT NOT NULL,
            title            TEXT NOT NULL,
            observation      TEXT NOT NULL,
            source_record_id TEXT,
            project_id       TEXT,
            created_at       TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            description  TEXT,
            command      TEXT,
            phase        TEXT,
            project_id   TEXT,
            priority     INTEGER DEFAULT 5,
            status       TEXT DEFAULT 'open',
            created_at   TEXT NOT NULL,
            completed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            capture_type     TEXT NOT NULL,
            title            TEXT NOT NULL,
            observation      TEXT NOT NULL,
            source_record_id TEXT,
            project_id       TEXT,
            created_at       TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS extraction_runs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id        TEXT NOT NULL,
            record_id        TEXT,
            model_used       TEXT,
            extraction_type  TEXT,
            status           TEXT NOT NULL DEFAULT 'pending',
            duration_seconds REAL,
            error            TEXT,
            project_id       TEXT,
            created_at       TEXT NOT NULL,
            completed_at     TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date TEXT NOT NULL,
            focus        TEXT NOT NULL,
            completed    TEXT NOT NULL,
            next_steps   TEXT NOT NULL,
            notes        TEXT,
            created_at   TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_number TEXT NOT NULL,
            title           TEXT NOT NULL,
            description     TEXT NOT NULL,
            rationale       TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'locked',
            created_at      TEXT,
            updated_at      TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            runtime         TEXT NOT NULL,
            capability      TEXT NOT NULL,
            tier            TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'installed',
            size_params     TEXT,
            quantization    TEXT,
            context_window  INTEGER,
            vram_required   REAL,
            benchmark_score TEXT,
            notes           TEXT,
            source_url      TEXT,
            installed_at    TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    conn.commit()


def ensure_phase1_tables(conn):
    """
    Phase 1 schema tables.
    Schema authority:
      /mnt/projects/cis/runtime/schemas/knowledge_spine_v1.json
      /mnt/projects/cis/runtime/schemas/spine_node_v1.json
    ADR: ADR-031, ADR-032
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_spines (
            spine_id        TEXT PRIMARY KEY,
            domain          TEXT NOT NULL,
            sub_domain      TEXT NOT NULL,
            subject         TEXT NOT NULL,
            source_type     TEXT NOT NULL,
            file_path       TEXT,
            node_count      INTEGER DEFAULT 0,
            status          TEXT NOT NULL DEFAULT 'ingested',
            ingested_at     TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spine_nodes (
            node_id         TEXT PRIMARY KEY,
            spine_id        TEXT NOT NULL,
            parent_node_id  TEXT,
            title           TEXT NOT NULL,
            depth           INTEGER NOT NULL,
            path            TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'generated',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (spine_id) REFERENCES knowledge_spines(spine_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS segments (
            segment_id          TEXT PRIMARY KEY,
            source_unit_id      TEXT NOT NULL,
            project_id          TEXT NOT NULL,
            segment_index       INTEGER NOT NULL,
            start_time          REAL NOT NULL,
            end_time            REAL NOT NULL,
            segmentation_method TEXT NOT NULL DEFAULT 'scene_detection',
            scene_score         REAL,
            anchor_node_id      TEXT,
            file_path           TEXT NOT NULL,
            file_format         TEXT NOT NULL,
            status              TEXT NOT NULL DEFAULT 'pending',
            extraction_run_id   TEXT,
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL,
            FOREIGN KEY (anchor_node_id) REFERENCES spine_nodes(node_id)
        )
    """)
    conn.commit()


def ensure_drafts_tables(conn):
    """
    ADR-048 Phase 1 — Staged Draft Intake Layer.
    Governs the four-zone trust model buffer between AI-proposed content
    and canonical CIS records.
    ADR: ADR-048
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_type          TEXT NOT NULL CHECK(draft_type IN (
                                    'adr', 'knowledge_record', 'session_field',
                                    'conflict', 'manifest', 'primer_update', 'config_patch'
                                )),
            payload_format      TEXT NOT NULL DEFAULT 'json' CHECK(payload_format IN (
                                    'json', 'markdown', 'text', 'structured'
                                )),
            schema_version      TEXT NOT NULL DEFAULT '1.0',
            zone                TEXT NOT NULL DEFAULT 'inbox' CHECK(zone IN (
                                    'downloads', 'inbox', 'staging', 'canonical'
                                )),
            status              TEXT NOT NULL DEFAULT 'inbox' CHECK(status IN (
                                    'inbox', 'staged', 'pending_review',
                                    'approved', 'rejected', 'committed',
                                    'superseded', 'archived'
                                )),
            source_model        TEXT CHECK(source_model IN (
                                    'claude', 'chatgpt', 'gemini', 'local', 'human'
                                )),
            source_session      TEXT,
            filename            TEXT,
            imported_by         TEXT,
            checksum            TEXT UNIQUE,
            payload             TEXT NOT NULL,
            proposed_target     TEXT,
            supersedes_id       INTEGER REFERENCES drafts(id),
            superseded_by       INTEGER REFERENCES drafts(id),
            approved_by         TEXT,
            approved_at         TEXT,
            rejected_by         TEXT,
            rejected_at         TEXT,
            rejection_reason    TEXT,
            committed_by        TEXT,
            committed_at        TEXT,
            commit_result       TEXT,
            canonical_record_id TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
