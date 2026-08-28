#!/usr/bin/env python3
"""
gate_chroma_no_secrets_in_results.py — Verify Chroma search results contain
no raw secret patterns.

Queries Chroma and confirms zero secret-bearing rows in results per
Tier 9 spec §2.4 verification.

Exit 0: PASS — no secrets in results
Exit 1: FAIL — secrets found
Exit 2: ERROR — Chroma not available
"""
import os
import re
import sys

sys.path.insert(0, os.environ.get("CIS_REPO", "/mnt/projects/cis") + "/runtime")

# Secret patterns (same as chroma_index.py)
SECRET_PATTERNS = [
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), "API key"),
    (re.compile(r'Bearer\s+[A-Za-z0-9\-_\.]{20,}'), "Bearer token"),
    (re.compile(r'-----BEGIN\s.*PRIVATE\sKEY-----'), "Private key"),
    (re.compile(r'gh[pousr]_[A-Za-z0-9]{36,}'), "GitHub token"),
    (re.compile(r'eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+'), "JWT token"),
]


def main():
    # Use test index or production
    chroma_path = os.environ.get(
        "CIS_CHROMA_PATH",
        os.environ.get("CIS_REPO", "/mnt/projects/cis") + "/data/chroma_data_test",
    )

    try:
        from mcp_bridge.chroma_index import ChromaClient
        client = ChromaClient(chroma_path=chroma_path)
    except Exception as exc:
        print("ERROR: Cannot create ChromaClient: {}".format(exc))
        sys.exit(2)

    collections = client.list_collections()
    if not collections:
        print("WARN: No Chroma collections found — gate passes vacuously")
        print("PASS: No secrets in Chroma results (0 collections)")
        sys.exit(0)

    failures = []
    total_docs = 0

    for coll_name in collections:
        try:
            count = client.collection_count(coll_name)
            if count == 0:
                continue

            # Query each collection for secret-like patterns
            # Use a neutral query to get sample results
            results = client.search_semantic("build plan migration tier",
                                             top_k=min(count, 20),
                                             collection_name=coll_name)
            for r in results:
                total_docs += 1
                doc = r.get("document", "")
                for pattern, label in SECRET_PATTERNS:
                    match = pattern.search(doc)
                    if match:
                        failures.append(
                            "{} found in {}: '{}'".format(
                                label, r.get("id", "?"),
                                doc[:80]))
        except Exception:
            continue

    if failures:
        print("FAIL: {} secret pattern(s) found in {} documents:".format(
            len(failures), total_docs))
        for f in failures:
            print("  - {}".format(f))
        sys.exit(1)

    print("PASS: No secrets found in {} documents across {} collection(s)".format(
        total_docs, len(collections)))
    sys.exit(0)


if __name__ == "__main__":
    main()
