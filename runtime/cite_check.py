#!/usr/bin/env python3
"""Extract file paths from a review, verify each exists.
Usage: cite_check.py <review.md> [repo_root]"""
import re, sys, pathlib

def main():
    text = pathlib.Path(sys.argv[1]).read_text()
    root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2
                        else "/workspace/cis")
    pat = re.compile(r"[A-Za-z0-9_./-]+\.(?:py|md|yaml|yml|json|sh)")
    seen = []
    for m in pat.findall(text):
        if m in seen:
            continue
        seen.append(m)
        p = pathlib.Path(m)
        hit = p.exists() or (root / m).exists() or \
              any(root.rglob(p.name))
        print(("REAL  " if hit else "FAKE  ") + m)
    print("TOTAL", len(seen))

main()
