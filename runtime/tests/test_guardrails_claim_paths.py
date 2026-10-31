"""Regression tests for file-claim extraction."""

from runtime.abstraction.guardrails import _extract_claimed_files


def test_versioned_absolute_filename_is_not_truncated_at_numeric_dot():
    path = "/workspace/output/queue-4.37-canary.txt"
    claims = _extract_claimed_files(f"File exists at {path}, regular file.")

    assert path in claims
    assert "/workspace/output/queue-4.37" not in claims

