#!/usr/bin/env python3
"""
tools/manifest/generate_dam_manifest.py — Tier 7.5b Frozen Manifest Generator
Scans approved Hermes session directories and writes a frozen manifest
of .json files with mtime <= --cutoff.

Usage:
    python3 tools/manifest/generate_dam_manifest.py --cutoff "2026-06-08T23:28:00Z" --out runtime/manifests/dam_frozen_manifest.txt
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

APPROVED_DIRS = [
    "/home/eric/.hermes/sessions",
    "/home/eric/.hermes-v4impl/sessions",
    "/home/eric/.hermes-r1/sessions",
    "/home/eric/.hermes-v4pro/sessions",
]


def parse_cutoff(iso_str):
    """Parse an ISO 8601 timestamp string (with or without Z/timezone)."""
    iso_str = iso_str.replace("Z", "+00:00")
    return datetime.fromisoformat(iso_str).astimezone(timezone.utc)


def scan_directory(directory, cutoff_dt):
    """Return sorted list of .json file paths with mtime <= cutoff."""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"  SKIP: directory not found: {directory}", file=sys.stderr)
        return []
    files = []
    for fp in sorted(dir_path.glob("*.json")):
        mtime = datetime.fromtimestamp(fp.stat().st_mtime, tz=timezone.utc)
        if mtime <= cutoff_dt:
            files.append(str(fp))
    return files


def main():
    parser = argparse.ArgumentParser(description="Generate frozen DAM manifest")
    parser.add_argument("--cutoff", type=str, required=True,
                        help="ISO 8601 cutoff timestamp (e.g., '2026-06-08T23:28:00Z')")
    parser.add_argument("--out", type=str, required=True,
                        help="Output manifest file path")
    args = parser.parse_args()

    cutoff_dt = parse_cutoff(args.cutoff)
    print(f"Cutoff: {cutoff_dt.isoformat()}")
    print(f"Scanning directories...")

    all_files = []
    per_dir = {}
    for directory in APPROVED_DIRS:
        files = scan_directory(directory, cutoff_dt)
        profile = os.path.basename(os.path.dirname(directory))
        if "hermes-v4impl" in directory:
            profile = "v4impl"
        elif "hermes-v4pro" in directory:
            profile = "v4pro"
        elif "hermes-r1" in directory:
            profile = "r1"
        else:
            profile = "prime"
        per_dir[profile] = len(files)
        all_files.extend(files)
        print(f"  {profile}: {len(files)} files")

    total = len(all_files)
    print(f"\nTotal: {total} files")

    # Verify against audit expectations
    expected = {"prime": 2731, "v4impl": 173, "r1": 97, "v4pro": 70}
    ok = True
    for profile, count in expected.items():
        actual = per_dir.get(profile, 0)
        status = "OK" if actual == count else f"MISMATCH (expected {count})"
        if actual != count:
            ok = False
        print(f"  verify {profile}: {actual} vs expected {count} — {status}")

    if not ok:
        print("\nWARNING: Manifest counts don't match Tier 7.5a audit expectations.")
        print("The cutoff may need adjustment or the directories have changed.")

    # Write manifest
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(all_files) + "\n")
    print(f"\nManifest written: {out_path} ({total} lines)")
    print(f"File size: {out_path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
