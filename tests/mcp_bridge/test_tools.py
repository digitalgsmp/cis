"""
test_tools.py — Unit tests for CIS MCP Bridge tool handlers.

Tests handler structure, error paths, and basic shape.
Tool handlers that call spine directly are tested with a temp DB.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runtime"))

from mcp_bridge import tools


class TestToolDefinitions(unittest.TestCase):
    """Test tool schema definitions (no DB needed)."""

    def test_all_9_tools_defined(self):
        self.assertEqual(len(tools.TOOLS), 9)

    def test_all_9_handlers_registered(self):
        self.assertEqual(len(tools.HANDLERS), 9)
        for t in tools.TOOLS:
            self.assertIn(t["name"], tools.HANDLERS,
                          "No handler for {}".format(t["name"]))

    def test_all_tools_have_input_schema(self):
        for t in tools.TOOLS:
            self.assertIn("inputSchema", t)
            self.assertIn("type", t["inputSchema"])


class TestHandlerErrorPaths(unittest.TestCase):
    """Test error paths that don't need a DB."""

    def test_get_build_status_missing_label(self):
        result = tools.handle_get_build_status({})
        self.assertIn("error", result)

    def test_get_run_detail_missing_id(self):
        result = tools.handle_get_run_detail({})
        self.assertIn("error", result)

    def test_search_sessions_missing_query(self):
        result = tools.handle_search_sessions({})
        self.assertIn("error", result)


class TestHandlerShapesWithDB(unittest.TestCase):
    """Test handler output shapes using a temp seeded DB."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="cis_mcp_tools_test_")
        cls.db_path = os.path.join(cls.tmpdir, "test_spine.db")

        # Seed from test_spine module
        from tests.mcp_bridge import test_spine
        test_spine.seed_test_db(cls.db_path)
        os.environ["CIS_SPINE_PATH"] = cls.db_path

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_get_current_phase_shape(self):
        result = tools.handle_get_current_phase({})
        self.assertIsInstance(result, dict)
        self.assertIn("build_phase", result)

    def test_get_next_actions_shape(self):
        result = tools.handle_get_next_actions({})
        self.assertIsInstance(result, dict)
        self.assertIn("actions", result)

    def test_get_recent_runs_shape(self):
        result = tools.handle_get_recent_runs({"limit": 3})
        self.assertIsInstance(result, dict)
        self.assertIn("runs", result)

    def test_get_open_decisions_shape(self):
        result = tools.handle_get_open_decisions({})
        self.assertIsInstance(result, dict)
        self.assertIn("decisions", result)

    def test_get_open_questions_shape(self):
        result = tools.handle_get_open_questions({})
        self.assertIsInstance(result, dict)
        self.assertIn("questions", result)

    def test_get_eric_gate_status_shape(self):
        result = tools.handle_get_eric_gate_status({})
        self.assertIsInstance(result, dict)
        self.assertIn("approvals", result)


if __name__ == "__main__":
    unittest.main()
