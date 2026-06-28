#!/usr/bin/env python3
"""
measure_intent.py — CLI tool for intent alignment measurement.

Usage:
  python3 tools/pipeline/measure_intent.py "proposal text" --top-k 10
  python3 tools/pipeline/measure_intent.py --topic "dashboard" --intent "Eric wants..."
  python3 tools/pipeline/measure_intent.py --file /path/to/proposal.md

Output: JSON with semantic + keyword matches from Eric's verbatim knowledge base.
Exit code 0 on success, 1 on failure.

Used by: pipeline dispatch scripts to pre-load intent context before
Drafter/Reviewer/Implementer sessions.
"""
import argparse
import json
import sys
import os

# Add runtime to path so we can import the intent module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../runtime"))

from api.intent import measure_intent


def main():
    parser = argparse.ArgumentParser(
        description="Measure a proposal against Eric's verbatim intentions"
    )
    parser.add_argument("proposal", nargs="?", help="Proposal text to measure")
    parser.add_argument("--topic", help="Topic to search for")
    parser.add_argument("--intent", help="Intent context (combines with --topic)")
    parser.add_argument("--file", help="Read proposal from file")

    parser.add_argument("--top-k", type=int, default=10, help="Max results per search type")
    parser.add_argument("--summary-only", action="store_true", help="Only print summary counts")
    args = parser.parse_args()

    # Build query text
    if args.file:
        with open(args.file) as f:
            query = f.read().strip()
    elif args.topic and args.intent:
        query = f"{args.topic}: {args.intent}"
    elif args.topic:
        query = args.topic
    elif args.proposal:
        query = args.proposal
    else:
        print(json.dumps({"error": "No query text provided"}))
        sys.exit(1)

    if not query:
        print(json.dumps({"error": "No query text provided"}))
        sys.exit(1)

    result = measure_intent(query, top_k=args.top_k)

    if args.summary_only:
        sources = set()
        for r in result.get("semantic", []):
            sources.add(r.get("source", "?"))
        for r in result.get("keyword", []):
            sources.add(r.get("source", "?"))
        print(json.dumps({
            "semantic_count": len(result.get("semantic", [])),
            "keyword_count": len(result.get("keyword", [])),
            "sources": sorted(sources),
        }))
    else:
        print(json.dumps(result, indent=2, default=str))

    total = result.get("total_matches", 0)
    if total == 0:
        # No matches isn't an error — just means nothing relevant found
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
