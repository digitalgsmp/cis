"""tests/test_mcp_dispatch.py — FD.1 MCP Dispatch Tools tests.

All tests are mocked per FD.1 §4.3 (M5). No test invokes a real subprocess,
writes to the spine, or launches a live pipeline run.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path for imports
sys.path.insert(0, "/mnt/projects/cis")

# Import the tools module (TOOLS list + handlers)
from runtime.mcp_bridge import tools as mcp_tools
from runtime.mcp_bridge import spine as mcp_spine


class TestDispatchToolRegistration(unittest.TestCase):
    """A1–A3: Verify dispatch tools are registered in TOOLS list."""

    def test_a1_three_dispatch_tools_present(self):
        """A1: 3 dispatch tools registered in TOOLS list."""
        dispatch_names = [
            t["name"] for t in mcp_tools.TOOLS
            if t["name"].startswith("cis_dispatch_")
        ]
        self.assertEqual(len(dispatch_names), 3,
                         "Expected 3 dispatch tools in TOOLS list")
        self.assertIn("cis_dispatch_drafter", dispatch_names)
        self.assertIn("cis_dispatch_reviewer", dispatch_names)
        self.assertIn("cis_dispatch_implementer", dispatch_names)

    def test_a2_no_name_collisions(self):
        """A2: 14 unique cis_* names, no duplicates."""
        all_names = [t["name"] for t in mcp_tools.TOOLS]
        self.assertEqual(len(all_names), len(set(all_names)),
                         "Tool names must be unique — collision detected")

    def test_a3_final_count_is_14(self):
        """A3: Final tool count = 14 (11 existing + 3 new)."""
        cis_tools = [t for t in mcp_tools.TOOLS
                     if t["name"].startswith("cis_")]
        self.assertEqual(len(cis_tools), 14,
                         "Expected 14 cis_* tools total")


class TestDispatchHandlers(unittest.TestCase):
    """A4–A6: Verify dispatch handler functions exist (all subprocess mocked)."""

    @patch("subprocess.run")
    def test_a4_drafter_handler_exists(self, mock_run):
        """A4: cis_dispatch_drafter handler returns correct keys.

        subprocess.run is mocked — dispatch path NOT actually called.
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="run-abc123\n",
            stderr="",
        )
        result = mcp_tools.handle_dispatch_drafter({
            "topic": "test topic",
            "intent": "test intent",
        })
        self.assertIn("workflow_run_id", result)
        self.assertEqual(result.get("status"), "DISPATCHED")
        self.assertNotIn("error", result)

    @patch("subprocess.run")
    def test_a5_reviewer_handler_exists(self, mock_run):
        """A5: cis_dispatch_reviewer handler returns correct keys.

        subprocess.run is mocked — dispatch path NOT actually called.
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="CONSENSUS_REACHED\n",
            stderr="",
        )
        result = mcp_tools.handle_dispatch_reviewer({
            "run_id": "run-test-123",
        })
        self.assertIn("run_id", result)
        self.assertIn("status", result)
        self.assertNotIn("error", result)

    @patch.object(mcp_spine, "check_eric_gate_approval", return_value=True)
    def test_a6_implementer_handler_exists(self, mock_gate):
        """A6: cis_dispatch_implementer handler returns correct keys.

        spine.check_eric_gate_approval is mocked to return True (approved).
        No subprocess dispatch — implementer handler is gate-check only.
        """
        result = mcp_tools.handle_dispatch_implementer({
            "run_id": "run-test-123",
        })
        self.assertEqual(result.get("status"), "DISPATCHED")
        self.assertEqual(result.get("gate_status"), "APPROVED")
        self.assertNotIn("error", result)


class TestSymlink(unittest.TestCase):
    """A7–A8: Verify runtime/mcp/ symlink."""

    def test_a7_symlink_resolves(self):
        """A7: runtime/mcp/tools.py is accessible."""
        symlink_path = "/mnt/projects/cis/runtime/mcp/tools.py"
        self.assertTrue(os.path.isfile(symlink_path),
                        f"Symlink target not accessible: {symlink_path}")

    def test_a8_symlink_is_relative(self):
        """A8: readlink returns 'mcp_bridge' not an absolute path."""
        symlink = "/mnt/projects/cis/runtime/mcp"
        target = os.readlink(symlink)
        self.assertEqual(target, "mcp_bridge",
                         f"Expected relative symlink 'mcp_bridge', got '{target}'")
        self.assertNotIn("/", target,
                         "Symlink target must be relative, not absolute")


class TestInputValidation(unittest.TestCase):
    """A9–A10: Verify required-field validation returns error dicts."""

    def test_a9_missing_required_field_drafter(self):
        """A9: cis_dispatch_drafter with empty topic returns error."""
        result = mcp_tools.handle_dispatch_drafter({
            "topic": "",
            "intent": "some intent",
        })
        self.assertIn("error", result)

    def test_a10_missing_required_field_reviewer(self):
        """A10: cis_dispatch_reviewer with no run_id returns error."""
        result = mcp_tools.handle_dispatch_reviewer({})
        self.assertIn("error", result)


class TestEricGateEnforcement(unittest.TestCase):
    """A11: Implementer must refuse unapproved run_ids.
    §4.3: assert_not_called() on dispatch path."""

    @patch.object(mcp_spine, "check_eric_gate_approval", return_value=False)
    def test_a11_implementer_refuses_unapproved(self, mock_gate):
        """A11: Unapproved run_id → error, gate_status=UNAPPROVED.

        §4.3 (M5): subprocess.run.assert_not_called() proves dispatch
        path was not invoked. Returning error key alone is insufficient.
        """
        with patch("subprocess.run") as mock_run:
            result = mcp_tools.handle_dispatch_implementer({
                "run_id": "run-unapproved-999",
            })
            self.assertIn("error", result)
            self.assertEqual(result.get("gate_status"), "UNAPPROVED")
            # §4.3: assert dispatch path was never called
            mock_run.assert_not_called()


class TestEricGateHelper(unittest.TestCase):
    """A12: check_eric_gate_approval — four cases.

    Tests the spine helper directly with controlled DB state.
    Cases: (a) approved, (b) NULL, (c) empty-string, (d) missing.
    """

    def _make_row(self, eric_approved_at):
        """Return a mock row with the given eric_approved_at value."""
        class MockRow:
            def __init__(self, val):
                self._val = val
            def __getitem__(self, key):
                if key == "approved":
                    return (self._val is not None and self._val != "")
                raise KeyError(key)
        return MockRow(eric_approved_at)

    def test_a12a_approved_timestamp_returns_true(self):
        """Case (a): non-empty eric_approved_at → True."""
        with patch.object(mcp_spine, "_connect_readonly") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = self._make_row("2026-06-20T00:00:00Z")
            mock_conn.return_value.execute.return_value = mock_cursor
            result = mcp_spine.check_eric_gate_approval("run-approved-1")
            self.assertTrue(result, "Approved run should return True")

    def test_a12b_null_approval_returns_false(self):
        """Case (b): eric_approved_at IS NULL → False."""
        with patch.object(mcp_spine, "_connect_readonly") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = self._make_row(None)
            mock_conn.return_value.execute.return_value = mock_cursor
            result = mcp_spine.check_eric_gate_approval("run-null-1")
            self.assertFalse(result, "NULL eric_approved_at should return False")

    def test_a12c_empty_string_approval_returns_false(self):
        """Case (c): eric_approved_at = '' → False."""
        with patch.object(mcp_spine, "_connect_readonly") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = self._make_row("")
            mock_conn.return_value.execute.return_value = mock_cursor
            result = mcp_spine.check_eric_gate_approval("run-empty-1")
            self.assertFalse(result, "Empty-string eric_approved_at should return False")

    def test_a12d_missing_run_id_returns_false(self):
        """Case (d): run_id not found → False."""
        with patch.object(mcp_spine, "_connect_readonly") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None  # no row
            mock_conn.return_value.execute.return_value = mock_cursor
            result = mcp_spine.check_eric_gate_approval("run-nonexistent")
            self.assertFalse(result, "Missing run_id should return False")


if __name__ == "__main__":
    unittest.main()
