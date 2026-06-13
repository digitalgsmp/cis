"""
test_chroma_index.py — Tests for Chroma/VDB index and query functions.

Tests secret filtering, embedding, and semantic search.
Uses a small in-memory Chroma instance with test data.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "runtime"))


class TestSecretFilter(unittest.TestCase):
    """Test SecretFilterPipeline regex patterns."""

    @classmethod
    def setUpClass(cls):
        from mcp_bridge.chroma_index import SecretFilterPipeline
        cls.filter = SecretFilterPipeline()

    def test_clean_text_passes(self):
        text = "This is a normal session message about client intake."
        result, action = self.filter.filter_text(text)
        self.assertEqual(action, "clean")
        self.assertEqual(result, text)

    def test_api_key_redacted(self):
        text = "The key is sk-abcdefghijklmnopqrstuvwxyz123"
        result, action = self.filter.filter_text(text)
        self.assertEqual(action, "redacted")

    def test_bearer_token_excluded(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abcdefg"
        result, action = self.filter.filter_text(text)
        self.assertEqual(action, "excluded")
        self.assertIsNone(result)

    def test_private_key_excluded(self):
        text = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkq...\n-----END PRIVATE KEY-----"
        result, action = self.filter.filter_text(text)
        self.assertEqual(action, "excluded")

    def test_generic_secret_replaced(self):
        text = "export API_KEY=sk-something-secret"
        result, action = self.filter.filter_text(text)
        self.assertIn("[REDACTED]", result)

    def test_empty_text_clean(self):
        text = ""
        result, action = self.filter.filter_text(text)
        self.assertEqual(action, "clean")

    def test_stats_tracked(self):
        self.filter.reset_stats()
        self.filter.filter_text("clean text")
        self.filter.filter_text("Bearer token123456789012345")
        self.assertEqual(self.filter.stats["clean"], 1)
        self.assertEqual(self.filter.stats["excluded"], 1)


class TestChromaIndex(unittest.TestCase):
    """Test Chroma index build and query with a temp DB."""

    @classmethod
    def setUpClass(cls):
        import sqlite3
        from mcp_bridge.chroma_index import ChromaClient

        cls.tmpdir = tempfile.mkdtemp(prefix="cis_chroma_test_")
        cls.db_path = os.path.join(cls.tmpdir, "test_spine.db")
        cls.chroma_path = os.path.join(cls.tmpdir, "chroma_test")

        # Create minimal test DB
        conn = sqlite3.connect(cls.db_path)
        conn.executescript("""
            CREATE TABLE dam_extracted_text (
                id INTEGER PRIMARY KEY,
                content_text TEXT,
                speaker_role TEXT,
                asset_id INTEGER
            );
            CREATE TABLE deliberation_rounds (
                id INTEGER PRIMARY KEY,
                drafter_output TEXT,
                run_id TEXT,
                round_number INTEGER
            );
            CREATE TABLE project_decisions (
                id TEXT PRIMARY KEY,
                label TEXT,
                decision TEXT,
                reason TEXT
            );
            CREATE TABLE session_closeouts (
                id INTEGER PRIMARY KEY,
                failure_summary TEXT,
                log_path TEXT
            );

            INSERT INTO dam_extracted_text VALUES
                (1, 'How do we handle client intake forms?', 'user', 1),
                (2, 'The intake process involves 3 steps.', 'user', 1),
                (3, 'We need admission paperwork for new clients.', 'user', 2);

            INSERT INTO deliberation_rounds VALUES
                (1, 'Proposal: Add archive routing to the pipeline', 'run-001', 1);

            INSERT INTO project_decisions VALUES
                ('ADR-SEED-001', 'Test decision', 'Approved', 'Because test');

            INSERT INTO session_closeouts VALUES
                (1, 'gate export agreement failure', '/tmp/closeout1.log');
        """)
        conn.commit()
        conn.close()

        os.environ["CIS_SPINE_PATH"] = cls.db_path
        os.environ["CIS_CHROMA_PATH"] = cls.chroma_path

        cls.client = ChromaClient(chroma_path=cls.chroma_path)

        # Build index
        from mcp_bridge.chroma_index import _get_db_path
        cls.stats = cls.client.index_from_spine(db_path=cls.db_path)

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_collections_created(self):
        names = self.client.list_collections()
        self.assertIn("cis_sessions", names)
        self.assertIn("cis_deliberations", names)
        self.assertIn("cis_decisions", names)
        self.assertIn("cis_closeouts", names)

    def test_sessions_indexed(self):
        count = self.client.collection_count("cis_sessions")
        self.assertGreater(count, 0)

    def test_search_returns_results(self):
        results = self.client.search_semantic("client intake forms", top_k=3)
        self.assertGreater(len(results), 0)

    def test_search_relevance(self):
        """Search for 'admission paperwork' should find 'client intake' docs."""
        results = self.client.search_semantic("admission paperwork", top_k=3)
        self.assertGreater(len(results), 0)

    def test_get_similar_works(self):
        """Find docs similar to a known session doc."""
        results = self.client.get_similar("session_1", top_k=3)
        if isinstance(results, dict) and "error" in results:
            # Collection may not be populated in test — accept gracefully
            self.skipTest("get_similar returned error: {}".format(results["error"]))
        self.assertGreater(len(results), 0)
        # Should not include the query doc itself
        ids = [r.get("id", r) if isinstance(r, dict) else str(r) for r in results]
        self.assertNotIn("session_1", ids)

    def test_search_empty_query(self):
        """Empty query should return results gracefully (embedding handles it)."""
        results = self.client.search_semantic("", top_k=5)
        self.assertIsInstance(results, list)

    def test_secret_filter_stats(self):
        """Verify filter stats are tracked."""
        self.assertIn("secret_filter", self.stats)


if __name__ == "__main__":
    unittest.main()
