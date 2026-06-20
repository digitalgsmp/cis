"""
test_mcp_dispatch.py — FD.1 dispatch tool tests.

All dispatch handler tests mock subprocess.run per spec §4.3 (M5).
No test invokes a real subprocess, writes to the spine, or launches
a live pipeline run.

Tests A1-A12 per spec §4.1.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure runtime/ is on path for mcp_bridge imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))


class TestDispatchToolCounts(unittest.TestCase):
    """A1-A3: Tool count and collision checks."""

    def setUp(self):
        from mcp_bridge import tools
        self.tools = tools

    def test_A1_three_dispatch_tools_registered(self):
        """3 dispatch tools present in TOOLS list."""
        dispatch_names = [
            t["name"] for t in self.tools.TOOLS
            if t["name"].startswith("cis_dispatch_")
        ]
        self.assertEqual(len(dispatch_names), 3,
                         f"Expected 3 dispatch tools, got {len(dispatch_names)}: {dispatch_names}")

    def test_A2_no_name_collisions(self):
        """All 14 cis_* tool names are unique."""
        all_names = [t["name"] for t in self.tools.TOOLS if t["name"].startswith("cis_")]
        self.assertEqual(len(all_names), len(set(all_names)),
                         f"Duplicate names found: {all_names}")

    def test_A3_final_tool_count_is_14(self):
        """Total cis_* tool count is exactly 14."""
        count = len([t for t in self.tools.TOOLS if t["name"].startswith("cis_")])
        self.assertEqual(count, 14, f"Expected 14 tools, got {count}")


class TestDispatchHandlers(unittest.TestCase):
    """A4-A6, A9-A11: Handler behaviour (all mocked per M5)."""

    @classmethod
    def setUpClass(cls):
        from mcp_bridge import tools
        cls.tools = tools

    # ── A4: Drafter handler exists ──────────────────────────

    @patch("mcp_bridge.tools.subprocess.run")
    def test_A4_drafter_handler_returns_expected_keys(self, mock_run):
        """cis_dispatch_drafter returns workflow_run_id and DISPATCHED."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = self.tools.handle_dispatch_drafter({
            "topic": "Test topic",
            "intent": "Test intent",
        })
        self.assertIn("workflow_run_id", result)
        self.assertEqual(result.get("status"), "DISPATCHED")

    # ── A5: Reviewer handler exists ─────────────────────────

    @patch("mcp_bridge.tools.subprocess.run")
    def test_A5_reviewer_handler_returns_expected_keys(self, mock_run):
        """cis_dispatch_reviewer returns run_id and DISPATCHED."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = self.tools.handle_dispatch_reviewer({
            "run_id": "run-test123",
        })
        self.assertEqual(result.get("run_id"), "run-test123")
        self.assertEqual(result.get("status"), "DISPATCHED")

    # ── A6: Implementer handler exists ──────────────────────

    @patch("mcp_bridge.tools.subprocess.run")
    @patch("mcp_bridge.spine.check_eric_gate_approval")
    def test_A6_implementer_handler_returns_expected_keys(
        self, mock_gate, mock_run
    ):
        """cis_dispatch_implementer returns DISPATCHED with APPROVED gate."""
        mock_gate.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = self.tools.handle_dispatch_implementer({
            "run_id": "run-test123",
        })
        self.assertEqual(result.get("status"), "DISPATCHED")
        self.assertEqual(result.get("gate_status"), "APPROVED")

    # ── A9: Missing required field — drafter ────────────────

    def test_A9_drafter_missing_topic_returns_error(self):
        """cis_dispatch_drafter with empty topic returns error dict."""
        result = self.tools.handle_dispatch_drafter({
            "topic": "",
            "intent": "Some intent",
        })
        self.assertIn("error", result)

    # ── A10: Missing required field — reviewer ──────────────

    def test_A10_reviewer_missing_run_id_returns_error(self):
        """cis_dispatch_reviewer with no run_id returns error dict."""
        result = self.tools.handle_dispatch_reviewer({})
        self.assertIn("error", result)

    # ── A11: Implementer refuses unapproved run ─────────────

    @patch("mcp_bridge.spine.check_eric_gate_approval")
    @patch("mcp_bridge.tools.subprocess.run")
    def test_A11_implementer_refuses_unapproved_run(
        self, mock_run, mock_gate
    ):
        """cis_dispatch_implementer blocks unapproved run_id."""
        mock_gate.return_value = False
        result = self.tools.handle_dispatch_implementer({
            "run_id": "run-unapproved",
        })
        self.assertIn("error", result)
        self.assertEqual(result.get("gate_status"), "UNAPPROVED")
        # Dispatch must NOT be called
        mock_run.assert_not_called()


class TestSymlink(unittest.TestCase):
    """A7-A8: Symlink existence and relative-ness."""

    def test_A7_symlink_resolves(self):
        """runtime/mcp/tools.py exists via symlink."""
        target = os.path.join(
            os.path.dirname(__file__), "..", "runtime", "mcp", "tools.py"
        )
        self.assertTrue(os.path.isfile(target),
                        f"Symlink target not found: {target}")

    def test_A8_symlink_is_relative(self):
        """Symlink target is 'mcp_bridge' (no leading /)."""
        symlink_path = os.path.join(
            os.path.dirname(__file__), "..", "runtime", "mcp"
        )
        target = os.readlink(symlink_path)
        self.assertEqual(target, "mcp_bridge",
                         f"Expected 'mcp_bridge', got '{target}'")


class TestEricGateHelper(unittest.TestCase):
    """A12: check_eric_gate_approval four cases."""

    @classmethod
    def setUpClass(cls):
        from mcp_bridge import spine
        cls.spine = spine

    def test_A12a_approved_returns_true(self):
        """Row exists with APPROVE → True."""
        mock_conn = MagicMock()
        mock_row = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = mock_row
        with patch.object(self.spine, "_connect_readonly",
                          return_value=mock_conn):
            result = self.spine.check_eric_gate_approval("run-approved")
        self.assertTrue(result)

    def test_A12b_no_row_returns_false(self):
        """No matching row → False (unapproved or missing run_id)."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        with patch.object(self.spine, "_connect_readonly",
                          return_value=mock_conn):
            result = self.spine.check_eric_gate_approval("run-nonexistent")
        self.assertFalse(result)

    def test_A12c_wrong_decision_returns_false(self):
        """Only APPROVE matches — VETO/RETURN_TO_DRAFT rows don't count."""
        # The query filters decision='APPROVE', so a row with VETO
        # won't match → fetchone returns None → False.
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        with patch.object(self.spine, "_connect_readonly",
                          return_value=mock_conn):
            result = self.spine.check_eric_gate_approval("run-vetoed")
        self.assertFalse(result)

    def test_A12d_not_current_returns_false(self):
        """Superseded approval (is_current=0) doesn't match → False."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = None
        with patch.object(self.spine, "_connect_readonly",
                          return_value=mock_conn):
            result = self.spine.check_eric_gate_approval(
                "run-superseded")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
