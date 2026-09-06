#!/usr/bin/env python3
"""check_chroma_writers.py — every Chroma writer must take the lock and the filter.

BUILD LIST 0.2 and 0.3. Both are marked DONE and both had the same live hole:
`tools/catalog/append_embeddings.py` wrote to the Chroma store with no
`chroma_write` lock (0.3) and no `filter_for_index` secret filter (0.2). It was
found by accident during unrelated work on 2026-09-05, months after both items
closed. Nothing detected it, and `filter_for_index`'s own docstring enumerates
five tools as though that were the complete set.

THE RULE IS NOT AN ALLOWLIST. An allowlist of six names goes stale the moment
someone writes a seventh tool, which is exactly how this hole appeared. The rule
is a property each file must satisfy:

    a file that ADDS to a Chroma collection must import chroma_write
                                             and must import filter_for_index
    a file that OPENS a Chroma client must import chroma_write or chroma_read

A new writer therefore fails this check on the day it is written, without anyone
remembering to register it.

Usage:
  python3 tools/check_chroma_writers.py                 # scan tools/ and runtime/
  python3 tools/check_chroma_writers.py PATH [PATH...]  # scan specific files
Exit: 0 all clear | 1 violations found | 2 could not scan
"""
import os
import re
import sys

ROOTS = ["tools", "runtime"]

# Files that legitimately touch Chroma without the wrappers.
EXEMPT = {
    # the lock and the filter themselves — they define what everyone else imports
    "runtime/mcp_bridge/chroma_lock.py",
    "runtime/mcp_bridge/chroma_index.py",
    # this checker
    "tools/check_chroma_writers.py",
}
EXEMPT_DIRS = ("tests/", "/.venv/", "/venv/", "site-packages/", "__pycache__/",
               "runtime/rails/", "data/drive_imports/")

ADD = re.compile(r"\b(?:collection|coll|_coll|c)\.add\s*\(|\.add\s*\(\s*ids\s*=")
CLIENT = re.compile(r"chromadb\.(?:Persistent|Http)Client\s*\(|get_collection\s*\(")
LOCK_W = re.compile(r"\bchroma_write\b")
LOCK_R = re.compile(r"\bchroma_read\b")
FILTER = re.compile(r"\bfilter_for_index\b")


def scan(path):
    """Return a list of violation strings for one file."""
    rel = os.path.relpath(path, "/mnt/projects/cis")
    if rel in EXEMPT or any(d in "/" + rel for d in EXEMPT_DIRS):
        return []
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []

    writes = bool(ADD.search(src))
    opens = bool(CLIENT.search(src))
    if not (writes or opens):
        return []

    out = []
    if writes:
        if not LOCK_W.search(src):
            out.append(f"{rel}: ADDS to a collection with no chroma_write lock (0.3)")
        if not FILTER.search(src):
            out.append(f"{rel}: ADDS to a collection with no filter_for_index (0.2)")
    elif opens and not (LOCK_W.search(src) or LOCK_R.search(src)):
        out.append(f"{rel}: opens a Chroma client with no chroma_read/chroma_write (0.3)")
    return out


def main(argv):
    base = "/mnt/projects/cis"
    targets = []
    if len(argv) > 1:
        targets = [a if os.path.isabs(a) else os.path.join(base, a) for a in argv[1:]]
    else:
        for root in ROOTS:
            for dirpath, dirnames, names in os.walk(os.path.join(base, root)):
                dirnames[:] = [d for d in dirnames
                               if d not in ("__pycache__", ".venv", "venv", "rails")]
                targets += [os.path.join(dirpath, n) for n in names if n.endswith(".py")]

    files = []
    for t in targets:
        if os.path.isdir(t):
            for dp, _, ns in os.walk(t):
                files += [os.path.join(dp, n) for n in ns if n.endswith(".py")]
        elif os.path.isfile(t):
            files.append(t)

    if not files:
        print("CANNOT CHECK — no Python files found in the given paths")
        return 2

    violations = []
    for f in sorted(files):
        violations += scan(f)

    if violations:
        print("CHROMA WRITER GATE: FAIL")
        for v in violations:
            print("  " + v)
        print(f"\n{len(violations)} violation(s). Every Chroma writer must hold "
              f"chroma_write (0.3) and apply filter_for_index (0.2).")
        return 1

    print(f"CHROMA WRITER GATE: PASS — {len(files)} file(s) scanned, "
          f"every Chroma writer takes the lock and the filter.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
