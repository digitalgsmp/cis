-- Migration 0016: Add menter_output column to deliberation_rounds
-- Menter's execution output was being stored as drafter_output, which caused
-- Verify to read Menter's self-report instead of Draft's directive.
-- This separates them so Verify can check the actual directive.

ALTER TABLE deliberation_rounds ADD COLUMN menter_output TEXT DEFAULT '';
