"""
test_spine.py — Unit tests for CIS MCP Bridge spine query layer.

Tests read-only SQLite queries against a temporary database
seeded with known test data. No production spine is used.
"""
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# Add runtime dir to path for cis_mcp_bridge imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runtime"))

from mcp_bridge import spine


def seed_test_db(db_path):
    """Create test tables + seed data for spine query tests."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    # Build plan nodes
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS build_plan_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL DEFAULT 'CIS',
            node_label TEXT NOT NULL,
            tier TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            blocked_reason TEXT,
            required_role TEXT,
            allowed_mode TEXT,
            workflow_run_id TEXT,
            evidence_path TEXT,
            commit_hash TEXT,
            completed_at TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(project_id, node_label)
        );

        CREATE TABLE IF NOT EXISTS project_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'manual',
            evidence_hash TEXT,
            evidence_run_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            superseded_at TEXT,
            superseded_by INTEGER
        );

        CREATE TABLE IF NOT EXISTS workflow_runs (
            id TEXT PRIMARY KEY,
            topic TEXT,
            result TEXT,
            rounds_completed INTEGER DEFAULT 0,
            created_at TEXT,
            completed_at TEXT,
            status TEXT DEFAULT 'created'
        );

        CREATE TABLE IF NOT EXISTS deliberation_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            round_number INTEGER NOT NULL,
            drafter_output TEXT,
            reviewer_signal TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS workflow_run_artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id TEXT NOT NULL,
            artifact_type TEXT,
            artifact_path TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS project_decisions (
            id TEXT PRIMARY KEY,
            label TEXT,
            decision TEXT,
            reason TEXT,
            status TEXT DEFAULT 'DECIDED',
            decided_at TEXT,
            superseded_by TEXT
        );

        CREATE TABLE IF NOT EXISTS open_questions (
            id TEXT PRIMARY KEY,
            question TEXT,
            status TEXT DEFAULT 'OPEN',
            opened_at TEXT
        );

        CREATE TABLE IF NOT EXISTS eric_gate_approvals (
            id TEXT PRIMARY KEY,
            workflow_run_id TEXT,
            decision TEXT,
            decided_at TEXT,
            decided_by TEXT DEFAULT 'Eric',
            goal_reference_id INTEGER,
            briefing_hash TEXT,
            briefing_json TEXT,
            drift_snapshot_json TEXT,
            decision_trail_snapshot_json TEXT,
            is_current INTEGER DEFAULT 1,
            supersedes_approval_id TEXT,
            rationale TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS goal_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id TEXT,
            goal_label TEXT,
            dependency_node TEXT,
            tier_advanced TEXT,
            advancement_type TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS session_closeouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            failure_summary TEXT,
            failure_step TEXT,
            log_path TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS session_closeouts_fts USING fts5(
            failure_summary, failure_step, log_path, created_by,
            content='session_closeouts', content_rowid='id'
        );
    """)

    # Seed data
    conn.executescript("""
        INSERT INTO build_plan_nodes (node_label, tier, sequence, status) VALUES
            ('Tier 7R.4 — Process Manager', '7R.4', 1, 'COMPLETE'),
            ('Tier 8 — MCP Bridge', '8', 2, 'PENDING'),
            ('Tier 9 — Chroma/VDB', '9', 3, 'BLOCKED');

        INSERT INTO project_state (key, value) VALUES
            ('build_phase', 'Tier 7R COMPLETE. Tier 8 PENDING.'),
            ('next_tier', '8'),
            ('next_action', 'Implement Tier 8 MCP Bridge.');

        INSERT INTO workflow_runs (id, topic, result, rounds_completed, created_at, status) VALUES
            ('run-test-001', 'Test topic 1', 'CONSENSUS_REACHED', 2, '2026-06-13T00:00:00Z', 'completed'),
            ('run-test-002', 'Test topic 2', 'ERROR', 0, '2026-06-13T01:00:00Z', 'error');

        INSERT INTO deliberation_rounds (run_id, round_number, drafter_output, reviewer_signal, created_at) VALUES
            ('run-test-001', 1, 'Draft proposal', 'OBJECTIONS', '2026-06-13T00:01:00Z'),
            ('run-test-001', 2, 'Revised proposal', 'CONSENSUS_REACHED', '2026-06-13T00:02:00Z');

        INSERT INTO workflow_run_artifacts (workflow_run_id, artifact_type, artifact_path, created_at) VALUES
            ('run-test-001', 'proposal', '/tmp/proposal.md', '2026-06-13T00:01:00Z');

        INSERT INTO project_decisions (id, label, decision, status, decided_at) VALUES
            ('ADR-SEED-001', 'Test decision', 'Approved', 'DECIDED', '2026-06-12T00:00:00Z');

        INSERT INTO open_questions (id, question, status, opened_at) VALUES
            ('OQ-SEED-001', 'Test question?', 'OPEN', '2026-06-12T00:00:00Z');

        INSERT INTO session_closeouts (failure_summary, failure_step, log_path, created_by) VALUES
            ('gate failure test', 'gate_build_state_coherence', '/tmp/closeout1.log', 'hermes-v4impl'),
            ('export mismatch', 'gate_export_agreement', '/tmp/closeout2.log', 'hermes-v4impl');
    """)

    # Rebuild FTS index for existing session_closeouts
    conn.execute(
        "INSERT INTO session_closeouts_fts(rowid, failure_summary, failure_step, log_path, created_by) "
        "SELECT id, failure_summary, failure_step, log_path, created_by FROM session_closeouts"
    )

    conn.commit()
    conn.close()


class TestSpineQueries(unittest.TestCase):
    """Test all spine query functions against a seeded temp DB."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="cis_mcp_test_")
        cls.db_path = os.path.join(cls.tmpdir, "test_spine.db")
        seed_test_db(cls.db_path)
        # Override env for the duration of tests
        os.environ["CIS_SPINE_PATH"] = cls.db_path

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    # ── A1: Current phase ─────────────────────────────

    def test_current_phase_returns_dict(self):
        result = spine.query_current_phase()
        self.assertIsInstance(result, dict)
        self.assertIn("build_phase", result)
        self.assertIn("pending", result)
        self.assertEqual(result["build_phase"], "Tier 7R COMPLETE. Tier 8 PENDING.")

    def test_current_phase_has_pending_nodes(self):
        result = spine.query_current_phase()
        pending = result.get("pending", [])
        labels = [n["node_label"] for n in pending]
        self.assertIn("Tier 8 — MCP Bridge", labels)

    # ── A2: Build status ──────────────────────────────

    def test_build_status_known_node(self):
        result = spine.query_build_status("Tier 7R.4 — Process Manager")
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "COMPLETE")

    def test_build_status_unknown_node(self):
        result = spine.query_build_status("Nonexistent Node")
        self.assertIsNone(result)

    # ── A3: Next actions ──────────────────────────────

    def test_next_actions_returns_pending(self):
        results = spine.query_next_actions()
        self.assertGreater(len(results), 0)
        statuses = {r["status"] for r in results}
        self.assertEqual(statuses, {"PENDING"})

    # ── A4: Recent runs ───────────────────────────────

    def test_recent_runs_returns_list(self):
        results = spine.query_recent_runs(limit=5)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_recent_runs_ordered_desc(self):
        results = spine.query_recent_runs(limit=5)
        if len(results) >= 2:
            self.assertGreaterEqual(results[0]["created_at"],
                                     results[1]["created_at"])

    # ── A5: Run detail ────────────────────────────────

    def test_run_detail_known_run(self):
        result = spine.query_run_detail("run-test-001")
        self.assertIsNotNone(result)
        self.assertIn("run", result)
        self.assertIn("rounds", result)
        self.assertEqual(len(result["rounds"]), 2)
        self.assertEqual(len(result["artifacts"]), 1)

    def test_run_detail_unknown_run(self):
        result = spine.query_run_detail("nonexistent-run")
        self.assertIsNone(result)

    # ── A6: Eric Gate status ──────────────────────────

    def test_eric_gate_status_returns_list(self):
        results = spine.query_eric_gate_status()
        self.assertIsInstance(results, list)

    # ── A7: Session search ────────────────────────────

    def test_search_sessions_finds_match(self):
        results = spine.query_search_sessions("gate failure")
        self.assertGreater(len(results), 0)
        summaries = [r["failure_summary"] for r in results]
        self.assertTrue(any("gate failure" in s for s in summaries))

    def test_search_sessions_no_match(self):
        results = spine.query_search_sessions("zzzznonexistent")
        self.assertEqual(len(results), 0)

    # ── A8: Open decisions ────────────────────────────

    def test_open_decisions_returns_decided(self):
        results = spine.query_open_decisions()
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["id"], "ADR-SEED-001")

    # ── A9: Open questions ────────────────────────────

    def test_open_questions_returns_open(self):
        results = spine.query_open_questions()
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["id"], "OQ-SEED-001")

    # ── Security: Read-only enforcement ───────────────

    def test_readonly_connection_rejects_write(self):
        """Verify that the read-only connection cannot execute writes."""
        conn = spine._connect_readonly()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("CREATE TABLE should_fail (x INTEGER)")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
