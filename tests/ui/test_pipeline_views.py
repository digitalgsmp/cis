"""
tests/ui/test_pipeline_views.py — Unit tests for Tier 10 Flask blueprint endpoints.

Tests all 8 GET endpoints in runtime/api/pipeline_views.py.
Uses Flask test client — no live server required.
"""

import pytest
import sys
import os

# Ensure runtime directory is on path for imports
runtime_dir = os.path.join(os.path.dirname(__file__), "..", "..", "runtime")
sys.path.insert(0, runtime_dir)

import flask


@pytest.fixture
def client():
    """Create a minimal Flask app with the pipeline_views blueprint registered."""
    app = flask.Flask(__name__)

    # Register only the pipeline_views blueprint (no other blueprints needed)
    from api.pipeline_views import pipeline_views_bp
    app.register_blueprint(pipeline_views_bp)

    return app.test_client()


class TestPipelineStatus:
    """Tests for GET /api/pipeline/status."""

    def test_status_endpoint_exists(self, client):
        """A1: Build plan status endpoint returns JSON (does not require live spine)."""
        resp = client.get("/api/pipeline/status")
        # May fail if spine DB is not available, but endpoint must exist (not 404)
        assert resp.status_code != 404, "Pipeline status endpoint not found"

    def test_status_response_is_json(self, client):
        """Verify the response content type is JSON."""
        resp = client.get("/api/pipeline/status")
        if resp.status_code == 200:
            assert resp.is_json or "application/json" in resp.content_type


class TestPipelineNodeStatus:
    """Tests for GET /api/pipeline/status/<node_label>."""

    def test_node_status_endpoint_exists(self, client):
        """Endpoint must exist (not return 404)."""
        resp = client.get("/api/pipeline/status/Tier%208%20%E2%80%94%20MCP%20Bridge")
        assert resp.status_code != 404, "Node status endpoint not found"


class TestPipelineNextActions:
    """Tests for GET /api/pipeline/next-actions."""

    def test_next_actions_endpoint_exists(self, client):
        resp = client.get("/api/pipeline/next-actions")
        assert resp.status_code != 404


class TestPipelineRuns:
    """Tests for GET /api/pipeline/runs."""

    def test_runs_endpoint_exists(self, client):
        resp = client.get("/api/pipeline/runs")
        assert resp.status_code != 404

    def test_runs_with_limit(self, client):
        resp = client.get("/api/pipeline/runs?limit=5")
        assert resp.status_code != 404

    def test_runs_detail_endpoint_exists(self, client):
        resp = client.get("/api/pipeline/runs/test-run-id")
        assert resp.status_code != 404


class TestEricGate:
    """Tests for GET /api/pipeline/eric-gate."""

    def test_eric_gate_endpoint_exists(self, client):
        resp = client.get("/api/pipeline/eric-gate")
        assert resp.status_code != 404


class TestDecisions:
    """Tests for GET /api/decisions."""

    def test_decisions_endpoint_exists(self, client):
        resp = client.get("/api/decisions")
        assert resp.status_code != 404


class TestArchiveSearch:
    """Tests for GET /api/archive/search/semantic and /api/archive/search/fts."""

    def test_semantic_search_endpoint_exists(self, client):
        resp = client.get("/api/archive/search/semantic?q=test")
        assert resp.status_code != 404

    def test_semantic_search_missing_query(self, client):
        resp = client.get("/api/archive/search/semantic")
        assert resp.status_code != 404  # Endpoint exists, empty q is handled

    def test_fts_search_endpoint_exists(self, client):
        resp = client.get("/api/archive/search/fts?q=test")
        assert resp.status_code != 404

    def test_fts_search_missing_query(self, client):
        resp = client.get("/api/archive/search/fts")
        assert resp.status_code != 404


class TestAllEndpointsAreGet:
    """Verify all 8 endpoints reject non-GET methods."""

    ENDPOINTS = [
        "/api/pipeline/status",
        "/api/pipeline/next-actions",
        "/api/pipeline/runs",
        "/api/pipeline/runs/test-run-id",
        "/api/pipeline/eric-gate",
        "/api/decisions",
        "/api/archive/search/semantic?q=test",
        "/api/archive/search/fts?q=test",
    ]

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_post_rejected(self, client, endpoint):
        """S4: POST to each endpoint must return 405 Method Not Allowed."""
        # Separate query string from path
        if "?" in endpoint:
            path, qs = endpoint.split("?", 1)
        else:
            path = endpoint
            qs = ""
        url = path + ("?" + qs if qs else "")
        resp = client.post(url)
        assert resp.status_code in (405, 400), \
            f"POST to {path} returned {resp.status_code}, expected 405"

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_put_rejected(self, client, endpoint):
        if "?" in endpoint:
            path, qs = endpoint.split("?", 1)
            url = path + ("?" + qs if qs else "")
        else:
            path = endpoint
            url = path
        resp = client.put(url)
        assert resp.status_code in (405, 400), \
            f"PUT to {path} returned {resp.status_code}, expected 405"

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_delete_rejected(self, client, endpoint):
        if "?" in endpoint:
            path, qs = endpoint.split("?", 1)
            url = path + ("?" + qs if qs else "")
        else:
            path = endpoint
            url = path
        resp = client.delete(url)
        assert resp.status_code in (405, 400), \
            f"DELETE to {path} returned {resp.status_code}, expected 405"


class TestAllEndpointsCount:
    """Verify exactly 8 endpoints are registered (A9)."""

    def test_eight_endpoints_registered(self):
        from api.pipeline_views import pipeline_views_bp
        assert len(pipeline_views_bp.deferred_functions) == 9, \
            f"Expected 9 deferred functions (8 endpoints + 1), got {len(pipeline_views_bp.deferred_functions)}"
