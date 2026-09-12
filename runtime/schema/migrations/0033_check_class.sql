-- Migration 0033: queue_items.check_class — deterministic item classification
-- feeding item selection. RUNNABLE = an agent can advance it by running its
-- check (no Eric); JUDGMENT = only Eric can decide it; NO_CHECK = blocked until
-- someone writes a check. Applied idempotently by tools/queue/classify_check.py
-- (the ALTER is guarded by a column-existence check), so this file is the
-- committed schema history, not the applier.
ALTER TABLE queue_items ADD COLUMN check_class TEXT
    CHECK (check_class IN ('RUNNABLE','JUDGMENT','NO_CHECK'));
