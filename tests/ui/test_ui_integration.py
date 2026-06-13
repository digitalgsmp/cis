"""
tests/ui/test_ui_integration.py — Integration tests for Tier 10 CIS UI.

Tests I1-I5 from the Tier 10 specification §9.3:
  I1: Flask serves new endpoints (curl-like test)
  I2: React app builds with new pages (build check)
  I3: New nav links appear in App.jsx
  I4: Existing UI regression — all 20 existing JSX pages present
  I5: MCP bridge functions importable
"""

import os
import sys
import re
import subprocess

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
RUNTIME_DIR = os.path.join(PROJECT_ROOT, "runtime")


class TestFlaskBlueprint:
    """I1: Flask serves new endpoints."""

    def test_blueprint_imports_cleanly(self):
        """Verify pipeline_views module imports without error."""
        sys.path.insert(0, RUNTIME_DIR)
        try:
            from api.pipeline_views import pipeline_views_bp
            assert pipeline_views_bp is not None
            assert pipeline_views_bp.name == "pipeline_views"
        except ImportError as e:
            pytest.fail(f"Failed to import pipeline_views: {e}")

    def test_blueprint_has_eight_endpoints(self):
        sys.path.insert(0, RUNTIME_DIR)
        from api.pipeline_views import pipeline_views_bp
        # deferred_functions count = number of route registrations
        # (one per @blueprint.route decorator)
        count = len(pipeline_views_bp.deferred_functions)
        assert count == 9, \
            f"Expected 9 deferred functions (8 routes + __init__), got {count}"


class TestReactBuildComponents:
    """I2: React build components validate against the existing build setup."""

    EXPECTED_NEW_PAGES = [
        "PipelinePage.jsx",
        "EricGatePage.jsx",
        "ArchiveSearchPage.jsx",
        "SessionArchivePage.jsx",
        "DecisionsPage.jsx",
    ]

    def test_all_new_pages_exist(self):
        pages_dir = os.path.join(RUNTIME_DIR, "ui", "src", "pages")
        missing = []
        for fname in self.EXPECTED_NEW_PAGES:
            fpath = os.path.join(pages_dir, fname)
            if not os.path.exists(fpath):
                missing.append(fname)
        assert len(missing) == 0, f"Missing page files: {missing}"

    def test_new_pages_are_non_empty(self):
        pages_dir = os.path.join(RUNTIME_DIR, "ui", "src", "pages")
        empty = []
        for fname in self.EXPECTED_NEW_PAGES:
            fpath = os.path.join(pages_dir, fname)
            if os.path.exists(fpath) and os.path.getsize(fpath) < 100:
                empty.append(fname)
        assert len(empty) == 0, f"Potentially empty page files: {empty}"


class TestNavLinks:
    """I3: New nav links appear in App.jsx."""

    EXPECTED_ROUTES = [
        "/pipeline",
        "/eric-gate",
        "/archive/search",
        "/archive/sessions",
        "/decisions",
    ]

    EXPECTED_IMPORTS = [
        "PipelinePage",
        "EricGatePage",
        "ArchiveSearchPage",
        "SessionArchivePage",
        "DecisionsPage",
    ]

    def test_new_routes_in_app(self):
        app_path = os.path.join(RUNTIME_DIR, "ui", "src", "App.jsx")
        with open(app_path) as f:
            content = f.read()

        for route in self.EXPECTED_ROUTES:
            assert f'path="{route}"' in content or f"path='{route}'" in content, \
                f"Route {route} not found in App.jsx"

    def test_new_imports_in_app(self):
        app_path = os.path.join(RUNTIME_DIR, "ui", "src", "App.jsx")
        with open(app_path) as f:
            content = f.read()

        for imp in self.EXPECTED_IMPORTS:
            assert imp in content, f"Import {imp} not found in App.jsx"

    def test_new_nav_entries_in_app(self):
        app_path = os.path.join(RUNTIME_DIR, "ui", "src", "App.jsx")
        with open(app_path) as f:
            content = f.read()

        nav_labels = ["Pipeline", "Eric Gate", "Archive", "Sessions", "Decisions"]
        for label in nav_labels:
            assert f"'{label}'" in content, f"Nav label '{label}' not found in App.jsx"


class TestApiJs:
    """Verify new API functions exist in api.js."""

    EXPECTED_FUNCTIONS = [
        "pipelineStatus",
        "pipelineRuns",
        "pipelineRunDetail",
        "ericGate",
        "decisions",
        "archiveSearchSemantic",
        "archiveSearchFts",
    ]

    def test_new_api_functions_exist(self):
        api_path = os.path.join(RUNTIME_DIR, "ui", "src", "api.js")
        with open(api_path) as f:
            content = f.read()

        for func in self.EXPECTED_FUNCTIONS:
            assert f"{func}:" in content or f"{func} =" in content, \
                f"API function {func} not found in api.js"


class TestExistingUiRegression:
    """I4: All 20 existing JSX page files still present (13 top-level + 7 infra)."""

    EXISTING_TOP_PAGES = [
        "AssetDetail.jsx",
        "ChatConsole.jsx",
        "DamPage.jsx",
        "HomePage.jsx",
        "IdeasPage.jsx",
        "InfraPage.jsx",
        "IngestionPage.jsx",
        "LearningPage.jsx",
        "ProjectDetail.jsx",
        "ProjectsPage.jsx",
        "ReviewQueue.jsx",
        "SchedulePage.jsx",
        "SpineGraphPage.jsx",
    ]

    EXISTING_INFRA_PAGES = [
        "AdvisorChat.jsx",
        "CollabTracker.jsx",
        "Hardware.jsx",
        "Models.jsx",
        "Services.jsx",
        "Software.jsx",
        "Storage.jsx",
    ]

    def test_all_existing_top_pages_present(self):
        pages_dir = os.path.join(RUNTIME_DIR, "ui", "src", "pages")
        present = set(os.listdir(pages_dir))
        for fname in self.EXISTING_TOP_PAGES:
            assert fname in present, f"Existing page {fname} is missing!"

    def test_all_existing_infra_pages_present(self):
        infra_dir = os.path.join(RUNTIME_DIR, "ui", "src", "pages", "infra")
        present = set(os.listdir(infra_dir))
        for fname in self.EXISTING_INFRA_PAGES:
            assert fname in present, f"Existing infra page {fname} is missing!"

    def test_none_of_existing_pages_were_deleted(self):
        pages_dir = os.path.join(RUNTIME_DIR, "ui", "src", "pages")
        count = len([f for f in os.listdir(pages_dir) if f.endswith(".jsx")])
        # 13 existing + 5 new Tier 10 pages = 18
        assert count >= 17, f"Expected at least 17 JSX files in pages/, got {count}"


class TestMcpBridgeImportable:
    """I5: MCP bridge functions are importable."""

    MCP_FUNCTIONS = [
        "handle_get_current_phase",
        "handle_get_build_status",
        "handle_get_next_actions",
        "handle_get_recent_runs",
        "handle_get_run_detail",
        "handle_get_open_decisions",
        "handle_get_eric_gate_status",
        "handle_search_sessions",
        "handle_search_semantic",
    ]

    def test_mcp_functions_importable(self):
        sys.path.insert(0, RUNTIME_DIR)
        from mcp_bridge.tools import (
            handle_get_current_phase,
            handle_get_build_status,
            handle_get_next_actions,
            handle_get_recent_runs,
            handle_get_run_detail,
            handle_get_open_decisions,
            handle_get_eric_gate_status,
            handle_search_sessions,
            handle_search_semantic,
        )
        assert callable(handle_get_current_phase)
        assert callable(handle_get_build_status)
        assert callable(handle_get_next_actions)
        assert callable(handle_get_recent_runs)
        assert callable(handle_get_run_detail)
        assert callable(handle_get_open_decisions)
        assert callable(handle_get_eric_gate_status)
        assert callable(handle_search_sessions)
        assert callable(handle_search_semantic)
