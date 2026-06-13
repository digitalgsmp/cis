"""
test_security.py — Security boundary tests for CIS MCP Bridge.

Tests per Tier 8 spec §7.2:
  S1: Read-only enforcement (SQLite mode=ro)
  S2: No network imports
  S3: No write SQL statements
  S4: No filesystem writes
  S5: No secret env var references
"""
import os
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runtime"))

from mcp_bridge import spine


class TestSecurityBoundaries(unittest.TestCase):
    """Security tests for the MCP bridge."""

    BRIDGE_DIR = Path(__file__).resolve().parents[2] / "runtime" / "mcp_bridge"

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="cis_mcp_sec_test_")
        cls.db_path = os.path.join(cls.tmpdir, "test_spine.db")

        from tests.mcp_bridge import test_spine
        test_spine.seed_test_db(cls.db_path)
        os.environ["CIS_SPINE_PATH"] = cls.db_path

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    # ── S1: Read-only enforcement ─────────────────────

    def test_s1_readonly_connection_rejects_insert(self):
        """INSERT must raise OperationalError on read-only connection."""
        conn = spine._connect_readonly()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute(
                    "INSERT INTO build_plan_nodes "
                    "(node_label, tier, sequence, status) "
                    "VALUES ('test', '99', 99, 'PENDING')"
                )
        finally:
            conn.close()

    def test_s1_readonly_connection_rejects_update(self):
        """UPDATE must raise OperationalError on read-only connection."""
        conn = spine._connect_readonly()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("UPDATE build_plan_nodes SET status = 'HACKED'")
        finally:
            conn.close()

    def test_s1_readonly_connection_rejects_delete(self):
        """DELETE must raise OperationalError on read-only connection."""
        conn = spine._connect_readonly()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("DELETE FROM build_plan_nodes")
        finally:
            conn.close()

    # ── S2: No network imports ────────────────────────

    def test_s2_no_network_imports(self):
        """Scan bridge source for network-related imports."""
        blocked = {"socket", "http", "urllib", "requests", "httpx", "aiohttp"}
        for py_file in self.BRIDGE_DIR.glob("*.py"):
            text = py_file.read_text()
            for word in blocked:
                pattern = r"\bimport\s+" + word + r"\b|\bfrom\s+" + word + r"\b"
                match = re.search(pattern, text)
                self.assertIsNone(
                    match,
                    "Network import '{}' found in {}".format(
                        word, py_file.name),
                )

    # ── S3: No write SQL statements ───────────────────

    def test_s3_no_write_sql_in_execute_calls(self):
        """Scan bridge source for conn.execute with INSERT/UPDATE/DELETE."""
        for py_file in self.BRIDGE_DIR.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            text = py_file.read_text()
            self.assertNotIn(
                'conn.execute("INSERT', text,
                "INSERT via conn.execute in {}".format(py_file.name),
            )
            self.assertNotIn(
                'conn.execute("UPDATE', text,
                "UPDATE via conn.execute in {}".format(py_file.name),
            )
            self.assertNotIn(
                'conn.execute("DELETE', text,
                "DELETE via conn.execute in {}".format(py_file.name),
            )

    # ── S4: No filesystem writes ──────────────────────

    def test_s4_no_filesystem_writes(self):
        """Scan bridge source for filesystem write operations."""
        blocked_patterns = [
            (r'\bopen\s*\([^)]*["\']w["\']', "open with 'w' mode"),
            (r'\bopen\s*\([^)]*["\']a["\']', "open with 'a' mode"),
            (r'\bos\.remove\b', "os.remove()"),
            (r'\bos\.unlink\b', "os.unlink()"),
            (r'\bos\.rename\b', "os.rename()"),
            (r'\bshutil\.(rmtree|move|copy|copytree)\b', "shutil operation"),
            (r'\.write_text\s*\(', "Path().write_text()"),
        ]
        for py_file in self.BRIDGE_DIR.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            text = py_file.read_text()
            for pattern, desc in blocked_patterns:
                match = re.search(pattern, text)
                self.assertIsNone(
                    match,
                    "Filesystem write '{}' found in {}".format(
                        desc, py_file.name),
                )

    # ── S5: No environment variable leakage ───────────

    def test_s5_no_secret_env_vars(self):
        """Bridge should not access secret environment variables."""
        for py_file in self.BRIDGE_DIR.glob("*.py"):
            text = py_file.read_text()
            # Skip chroma_index.py — it contains detection regex patterns,
            # not actual env var access
            if py_file.name == "chroma_index.py":
                continue
            for secret_var in [
                "API_KEY", "TOKEN", "SECRET", "PASSWORD",
                "GITHUB_TOKEN", "OPENAI_API_KEY",
            ]:
                self.assertNotIn(
                    secret_var, text,
                    "Secret env var '{}' referenced in {}".format(
                        secret_var, py_file.name),
                )


if __name__ == "__main__":
    unittest.main()
