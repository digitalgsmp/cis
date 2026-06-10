-- Migration 0007: Add push_status to session_closeouts.
-- Records whether git push to GitHub succeeded at closeout.
-- Allows router to surface push failures at next session start.

ALTER TABLE session_closeouts ADD COLUMN push_status TEXT;
