-- Migration 0020: Expand deliberation_rounds.reviewer_signal CHECK to include PENDING
-- Rounds now start as PENDING (not CONSENSUS_REACHED) per bug fix #3.
-- Requires rebuilding the table to change the CHECK constraint.

-- Step 1: Rename old table
ALTER TABLE deliberation_rounds RENAME TO deliberation_rounds_old;

-- Step 2: Create new table with expanded CHECK
CREATE TABLE deliberation_rounds (
    id                  INTEGER PRIMARY KEY,
    run_id              TEXT NOT NULL,
    round_number        INTEGER NOT NULL,
    drafter_role        TEXT NOT NULL,
    drafter_output      TEXT NOT NULL DEFAULT '',
    reviewer_role       TEXT NOT NULL DEFAULT '',
    reviewer_signal     TEXT NOT NULL DEFAULT 'PENDING'
                        CHECK (reviewer_signal IN
                        ('PENDING', 'OBJECTIONS', 'CONSENSUS_REACHED', 'ESCALATE', 'ERROR')),
    objections_json     TEXT,
    revision_number     INTEGER NOT NULL DEFAULT 1,
    requires_eric_review INTEGER NOT NULL DEFAULT 1
                        CHECK (requires_eric_review IN (0, 1)),
    created_at          TEXT NOT NULL,
    reviewer1_output    TEXT DEFAULT '',
    reviewer2_output    TEXT DEFAULT '',
    brain_output        TEXT DEFAULT '',
    verify_output       TEXT DEFAULT '',
    human_question      TEXT DEFAULT '',
    human_answer        TEXT DEFAULT '',
    menter_output       TEXT DEFAULT '',
    UNIQUE(run_id, round_number)
);

-- Step 3: Copy data from old table
INSERT INTO deliberation_rounds
SELECT id, run_id, round_number, drafter_role, drafter_output,
       reviewer_role, reviewer_signal, objections_json, revision_number,
       requires_eric_review, created_at, reviewer1_output, reviewer2_output,
       brain_output, verify_output, human_question, human_answer, menter_output
FROM deliberation_rounds_old;

-- Step 4: Drop old table
DROP TABLE deliberation_rounds_old;
