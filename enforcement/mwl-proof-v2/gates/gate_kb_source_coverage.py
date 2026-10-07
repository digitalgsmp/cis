#!/usr/bin/env python3
"""gate_kb_source_coverage.py — fail closed when durable knowledge has a hole.

Deterministic. Reads config/kb_source_policy.yaml, discovers the sources on disk,
compares against knowledge_messages.source_key and the ingestion manifest, and
exits non-zero on any of:

  - an expected source absent from ingestion
  - coverage below the family's declared floor
  - a source changed since it was ingested (sha256 mismatch)
  - a required family whose ingested rows carry no provenance
  - a required family with no ingestion path at all
  - the policy, the spine or a declared root being unreadable (fails closed:
    coverage that cannot be established is not coverage)

It never asks anyone to count files or remember which sources belong in the KB.
Adding a document under a declared root is enough to make it eligible.

  python3 tools/gates/gate_kb_source_coverage.py            # human table
  python3 tools/gates/gate_kb_source_coverage.py --json     # machine-readable
  python3 tools/gates/gate_kb_source_coverage.py --family X # one family
  python3 tools/gates/gate_kb_source_coverage.py --closeout # stage-closeout mode

--closeout narrows the exit code to families that are required AND measurable.
A family that is required but carries `measurable: false` with
`ingestion_path: MISSING` is printed as POLICY UNDECIDED and does not fail,
because a gate that can never go green is a gate people learn to ignore. The
split is the one config/kb_source_policy.yaml already declares; this mode reads
it, it does not change it. The DEFAULT mode still fails on those families, so
the unresolved architecture decision stays visible.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb import source_policy as sp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--family", action="append", default=None)
    ap.add_argument("--policy", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--list-missing", action="store_true",
                    help="print every un-ingested source path")
    ap.add_argument("--closeout", action="store_true",
                    help="stage-closeout mode: fail only on required families "
                         "whose coverage is measurable; report required-but-"
                         "unmeasurable families as POLICY UNDECIDED")
    args = ap.parse_args()

    try:
        policy = sp.load_policy(args.policy)
        manifest = sp.load_manifest(args.manifest)
    except Exception as exc:                      # fail closed, loudly
        print(f"GATE FAIL: policy unreadable — {exc}", file=sys.stderr)
        return 2

    families = policy["families"]
    if args.family:
        families = {k: v for k, v in families.items() if k in args.family}
        missing_names = set(args.family) - set(families)
        if missing_names:
            print(f"GATE FAIL: no such family: {', '.join(sorted(missing_names))}",
                  file=sys.stderr)
            return 2

    import sqlite3
    db = args.db or sp.DB_PATH
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        conn.execute("SELECT 1 FROM knowledge_messages LIMIT 1").fetchone()
    except Exception as exc:
        print(f"GATE FAIL: spine unreadable at {db} — {exc}", file=sys.stderr)
        return 2

    rows = []
    for name, fam in families.items():
        try:
            rows.append(sp.measure_family(name, fam or {}, conn, manifest))
        except Exception as exc:
            rows.append({"family": name, "status": "VIOLATION", "coverage": None,
                         "expected": True, "violations": [f"measurement failed: {exc}"]})
    conn.close()

    violating = [r for r in rows if r.get("violations")]
    # In closeout mode a required-but-unmeasurable family is reported, not fatal.
    # Same rows, same violations — only the exit code narrows.
    undecided = [r for r in violating
                 if args.closeout and not r.get("measurable", True)]
    failed = [r for r in violating if r not in undecided]

    if args.json:
        print(json.dumps({"families": rows,
                          "violations": sum(len(r.get("violations", [])) for r in rows),
                          "mode": "closeout" if args.closeout else "full",
                          "policy_undecided": [r["family"] for r in undecided],
                          "pass": not failed}, indent=1))
    else:
        print(f"{'FAMILY':26s} {'REQ':4s} {'COV':>7s} {'ELIG':>6s} {'ING':>6s} "
              f"{'MISS':>6s} {'STATUS'}")
        print("-" * 88)
        for r in rows:
            cov = "-" if r.get("coverage") is None else f"{r['coverage']:.1%}"
            print(f"{r['family']:26s} {'yes' if r.get('expected') else 'no':4s} "
                  f"{cov:>7s} {r.get('total_eligible', '-'):>6} "
                  f"{r.get('ingested', '-'):>6} {r.get('missing', '-'):>6} "
                  f"{r.get('status', '?')}")
            marker = "?" if r in undecided else "!"
            for v in r.get("violations", []):
                print(f"{'':26s}   {marker} {v}")
            if r in undecided:
                print(f"{'':26s}   ? POLICY UNDECIDED — reported, not blocking "
                      f"closeout (see R3 / the family's note)")
            if args.list_missing:
                for f in r.get("missing_files", []):
                    print(f"{'':28s} missing: {f}")
                for f in r.get("changed_since_ingest", []):
                    print(f"{'':28s} changed: {f}")
        print()
        if undecided:
            print(f"POLICY UNDECIDED (not blocking in --closeout): "
                  f"{', '.join(r['family'] for r in undecided)}")
        print("GATE FAIL" if failed else "GATE PASS")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
