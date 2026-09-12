-- Migration 0032: queue authority — the database becomes the queue's source of truth
--
-- BUILD LIST queue-authority-and-audit, phase 1. Three parts:
--   1. queue_items gains status_changed_at / status_changed_by, so a status
--      carries who changed it and when.
--   2. queue_item_events — append-only change history. `evidence` holds the
--      command output that justified the change, not a claim that one exists.
--      This is the column that makes the phase-2 audit mean anything.
--   3. queue_sections — the non-item file structure (preamble + tier headers)
--      so the markdown renders back byte-faithfully from the table. The
--      extractor (extract_queue_items.py) previously dropped these 57 lines —
--      the "TWO PLANES" frame and the five "# TIER N" headers — which made the
--      card's own "render reproduces the file" check impossible. Caught
--      2026-09-11 by reconstruction+diff, not by the (blind) reviewers.
--
-- Idempotent where SQLite allows (CREATE IF NOT EXISTS). The ALTER TABLE
-- ADD COLUMN statements are NOT idempotent in SQLite; apply once, or apply via
-- the Python guard in tools/queue/apply_migration_0032.py which checks column
-- existence first.

-- 1. queue_items: who/when changed the status
ALTER TABLE queue_items ADD COLUMN status_changed_at TEXT;
ALTER TABLE queue_items ADD COLUMN status_changed_by TEXT;

-- 2. append-only change history. evidence is the command output that justified
--    the change; note is free text for the JUDGMENT / NO_CHECK cases.
CREATE TABLE IF NOT EXISTS queue_item_events (
    id          INTEGER PRIMARY KEY,
    item_num    TEXT NOT NULL,
    field       TEXT NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    changed_at  TEXT NOT NULL DEFAULT (datetime('now')),
    changed_by  TEXT,
    evidence    TEXT,
    note        TEXT
);
CREATE INDEX IF NOT EXISTS idx_queue_item_events_item ON queue_item_events(item_num);

-- 3. non-item file structure, in sequence order. kind is either the preamble
--    (the intro prose before the first "# TIER") or a tier_header. tier carries
--    the tier number for tier_header rows so the render can interleave items.
CREATE TABLE IF NOT EXISTS queue_sections (
    seq         INTEGER PRIMARY KEY,
    kind        TEXT NOT NULL CHECK (kind IN ('preamble','tier_header')),
    content     TEXT NOT NULL,
    tier        INTEGER,
    source_line INTEGER,
    source_sha  TEXT NOT NULL
);
