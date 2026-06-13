#!/usr/bin/env python3
"""
gate_chroma_secret_filter.py — Verify SecretFilterPipeline detects secrets.

Tests the secret filtering regex patterns against known-clean and known-secret
test inputs per Tier 9 spec §2.4.

Exit 0: PASS — all patterns detect correctly
Exit 1: FAIL — pattern mismatch
Exit 2: ERROR — import failure
"""
import os
import sys
import tempfile

sys.path.insert(0, "/mnt/projects/cis/runtime")

try:
    from mcp_bridge.chroma_index import SecretFilterPipeline
except ImportError as exc:
    print("ERROR: Cannot import SecretFilterPipeline: {}".format(exc))
    sys.exit(2)


def main():
    f = SecretFilterPipeline()
    failures = []

    # Test 1: API key should be redacted
    text = "Use the key sk-abcdefghijklmnopqrstuvwxyz123 for auth"
    result, action = f.filter_text(text)
    if action != "redacted":
        failures.append("API key not redacted (got: {})".format(action))

    # Test 2: Bearer token should be excluded
    text = "Authorization: Bearer abcdefghijklmnopqrstuv1234567890"
    result, action = f.filter_text(text)
    if action != "excluded":
        failures.append("Bearer token not excluded (got: {})".format(action))

    # Test 3: Private key should be excluded
    text = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkq\n-----END PRIVATE KEY-----"
    result, action = f.filter_text(text)
    if action != "excluded":
        failures.append("Private key not excluded (got: {})".format(action))

    # Test 4: Generic secret should be replaced
    text = "export API_KEY=sk-proj-secret-value-12345"
    result, action = f.filter_text(text)
    if "[REDACTED]" not in result:
        failures.append("Generic secret not replaced")
    if action != "replaced":
        failures.append("Generic secret action wrong (got: {})".format(action))

    # Test 5: Clean text should pass
    text = "This is a normal message about client intake procedures."
    result, action = f.filter_text(text)
    if action != "clean":
        failures.append("Clean text flagged (got: {})".format(action))

    # Test 6: GitHub token should be redacted
    text = "My token is ghp_abcdefghijklmnopqrstuvwxyz1234567890"
    result, action = f.filter_text(text)
    if action != "redacted":
        failures.append("GitHub token not redacted (got: {})".format(action))

    # Test 7: JWT token should be redacted
    text = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    result, action = f.filter_text(text)
    if action != "redacted":
        failures.append("JWT token not redacted (got: {})".format(action))

    if failures:
        print("FAIL: {} secret filter pattern(s) failed:".format(len(failures)))
        for fail in failures:
            print("  - {}".format(fail))
        sys.exit(1)

    print("PASS: All 7 secret filter patterns detect correctly")
    sys.exit(0)


if __name__ == "__main__":
    main()
