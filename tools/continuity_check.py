#!/usr/bin/env python3
"""Evaluate one CIS semantic transaction from a JSON envelope.

This is the process boundary for modules that cannot import the runtime
library directly. It prints one JSON authorization. Exit 0 means ALLOW or
ANNOTATE; exit 2 means HOLD; exit 1 means malformed input or local failure.

Examples:
  python3 tools/continuity_check.py --envelope transaction.json
  producer | python3 tools/continuity_check.py --envelope -

The optional ``--record`` flag appends the check to migration 0041's ledger
with status='EVALUATED' only -- this tool never writes 'COMMITTED', because it
does not perform the domain mutation itself. In-process callers that do
perform the mutation should call ``persist_check(..., status="COMMITTED")`` on
the same SQLite connection and inside the same transaction as that change.
"""

import argparse
import json
import os
import sqlite3
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "runtime"))

from continuity_interceptor import (  # noqa: E402
    SemanticTransaction, evaluate, make_openai_compatible_caller, persist_check,
)


def read_envelope(path: str) -> dict:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--envelope", required=True,
                        help="JSON file, or - for stdin")
    parser.add_argument("--db", default=os.environ.get(
        "CIS_SPINE_PATH", os.path.join(REPO, "data", "cis_memory.db")))
    parser.add_argument("--record", action="store_true",
                        help="append the check to continuity_transactions")
    parser.add_argument("--url", default=None,
                        help="override CIS_CONTINUITY_URL")
    args = parser.parse_args()

    try:
        payload = read_envelope(args.envelope)
        for name in ("input_refs", "parent_transaction_ids"):
            if name in payload:
                payload[name] = tuple(payload[name])
        transaction = SemanticTransaction(**payload)
    except Exception as exc:
        print(json.dumps({"error": f"invalid envelope: {type(exc).__name__}: {exc}"}))
        return 1

    conn = sqlite3.connect(args.db, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        authorization = evaluate(
            conn, transaction, make_openai_compatible_caller(url=args.url)
        )
        if args.record:
            persist_check(conn, transaction, authorization, status="EVALUATED")
            conn.commit()
        print(json.dumps(authorization.as_dict(), indent=2, ensure_ascii=False))
        return 2 if authorization.decision == "HOLD" else 0
    except Exception as exc:
        conn.rollback()
        print(json.dumps({"error": f"check failed: {type(exc).__name__}: {exc}"}))
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
