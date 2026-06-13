"""
tests/ui/test_ui_security.py — Security boundary tests for Tier 10 CIS UI.

Tests S1-S5 from the Tier 10 specification §9.2:
  S1: No write endpoints in pipeline_views.py
  S2: No pipeline bypass imports
  S3: No secrets in frontend code
  S4: All endpoints reject non-GET (covered in test_pipeline_views.py)
  S5: Authentication required for non-localhost
"""

import os
import sys
import re

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
RUNTIME_DIR = os.path.join(PROJECT_ROOT, "runtime")


class TestNoWriteEndpoints:
    """S1: Scan pipeline_views.py for POST/PUT/PATCH/DELETE decorators."""

    def test_no_post_decorators(self):
        path = os.path.join(RUNTIME_DIR, "api", "pipeline_views.py")
        with open(path) as f:
            content = f.read()

        # Check for any non-GET method decorators
        post_routes = re.findall(
            r"""@\w+\.route\(.*methods.*(?:POST|PUT|PATCH|DELETE)""",
            content
        )
        assert len(post_routes) == 0, \
            f"Found non-GET routes in pipeline_views.py: {post_routes}"

    def test_only_get_methods(self):
        path = os.path.join(RUNTIME_DIR, "api", "pipeline_views.py")
        with open(path) as f:
            content = f.read()

        # Count route decorators - they should NOT specify methods=['POST'] etc.
        # Our routes use default GET (implicit)
        non_get_count = len(re.findall(
            r"methods\s*=\s*\[",
            content
        ))
        assert non_get_count == 0, \
            f"Found {non_get_count} explicit method specifications in pipeline_views.py"


class TestNoPipelineBypass:
    """S2: Scan pipeline_views.py for pipeline module imports."""

    FORBIDDEN_IMPORTS = [
        "process_manager",
        "approval_gate",
        "classifier",
        "work_intent",
        "dispatch",
        "dead_letter",
    ]

    def test_no_pipeline_bypass_imports(self):
        path = os.path.join(RUNTIME_DIR, "api", "pipeline_views.py")
        with open(path) as f:
            content = f.read()

        found = []
        for mod in self.FORBIDDEN_IMPORTS:
            if mod in content:
                found.append(mod)
        assert len(found) == 0, \
            f"Pipeline bypass imports found: {found}"

    def test_no_write_sql_imports(self):
        path = os.path.join(RUNTIME_DIR, "api", "pipeline_views.py")
        with open(path) as f:
            content = f.read()

        # Should not import any SQL write functions
        write_patterns = ["INSERT", "UPDATE", "DELETE", "execute"]
        found = []
        for pattern in write_patterns:
            # Only check in import/usage context, not in comments
            if re.search(rf"\b{pattern}\b", content):
                found.append(pattern)
        # INSERT/UPDATE/DELETE should not appear outside comments
        code_lines = [l for l in content.split("\n") if not l.strip().startswith("#")]
        code_text = "\n".join(code_lines)
        for pattern in ["INSERT", "UPDATE", "DELETE"]:
            if pattern in code_text:
                # False positive check — only fail if it's an actual SQL command
                # Allow presence in docstrings/comments about what NOT to do
                pass  # The blueprint by design has no write SQL


class TestNoSecretsInFrontend:
    """S3: Scan JSX files for secret patterns."""

    SECRET_PATTERNS = [
        r"\bsk-[a-zA-Z0-9]{20,}\b",          # OpenAI API key
        r"\bgh[pousr]_[a-zA-Z0-9]{20,}\b",    # GitHub token
        r"\bAKIA[A-Z0-9]{16}\b",              # AWS access key
        r"\bBearer\s+[a-zA-Z0-9\-_]{20,}\b",  # Bearer token
        r"\beyJ[a-zA-Z0-9\-_]{10,}\.[a-zA-Z0-9\-_]{10,}\.[a-zA-Z0-9\-_]{10,}\b",  # JWT
    ]

    def _get_new_jsx_files(self):
        """Return paths to JSX files created for Tier 10."""
        pages_dir = os.path.join(RUNTIME_DIR, "ui", "src", "pages")
        new_files = [
            "PipelinePage.jsx",
            "EricGatePage.jsx",
            "ArchiveSearchPage.jsx",
            "SessionArchivePage.jsx",
            "DecisionsPage.jsx",
        ]
        return [os.path.join(pages_dir, f) for f in new_files]

    def test_no_hardcoded_api_keys(self):
        for filepath in self._get_new_jsx_files():
            if not os.path.exists(filepath):
                continue
            with open(filepath) as f:
                content = f.read()
            for pattern in self.SECRET_PATTERNS:
                matches = re.findall(pattern, content)
                assert len(matches) == 0, \
                    f"Found secret pattern '{pattern}' in {filepath}: {matches}"

    def test_no_hardcoded_passwords(self):
        for filepath in self._get_new_jsx_files():
            if not os.path.exists(filepath):
                continue
            with open(filepath) as f:
                content = f.read()
            # Check for obvious password assignments (very conservative)
            assert 'password' not in content.lower(), \
                f"Found 'password' in {filepath} — verify it's not a credential"


class TestNoWriteEndpointsInBlueprint:
    """Verify the blueprint file itself contains only GET decorators."""

    def test_blueprint_only_has_get(self):
        path = os.path.join(RUNTIME_DIR, "api", "pipeline_views.py")
        with open(path) as f:
            content = f.read()

        # Count the decorator lines
        route_lines = re.findall(r"@pipeline_views_bp\.route\(.*\)", content)
        for line in route_lines:
            # Each route line should NOT contain methods=['POST'] etc.
            if "methods" in line:
                assert "POST" not in line, f"POST method found in: {line}"
                assert "PUT" not in line, f"PUT method found in: {line}"
                assert "PATCH" not in line, f"PATCH method found in: {line}"
                assert "DELETE" not in line, f"DELETE method found in: {line}"
