#!/usr/bin/env python3
"""Card runner. Dry-run by default: parses cards, runs
EVIDENCE checks, reports status. Never executes BUILD."""
import re, subprocess, sys, pathlib, argparse

FIELD = re.compile(r'^([A-Z][A-Z ]+):\s*(.*)$')

def parse(path):
    card = {"path": str(path), "EVIDENCE": [], "BUILD": ""}
    cur = None
    for line in path.read_text().splitlines():
        m = FIELD.match(line)
        if m:
            cur = m.group(1).strip()
            if m.group(2).strip():
                card[cur] = m.group(2).strip()
            continue
        if cur == "EVIDENCE" and line.strip().startswith("- "):
            card["EVIDENCE"].append(line.strip()[2:])
    return card

def check(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           timeout=30)
        return r.returncode == 0, r.returncode
    except Exception as e:
        return False, str(e)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards_dir")
    ap.add_argument("--halt", action="store_true")
    a = ap.parse_args()
    files = sorted(pathlib.Path(a.cards_dir).glob("*.md"))
    print(f"CARDS: {len(files)}")
    for f in files:
        c = parse(f)
        if not c["EVIDENCE"]:
            print(f"SKIP  {f.name}  (no EVIDENCE)")
            continue
        results = [check(e) for e in c["EVIDENCE"]]
        ok = all(r[0] for r in results)
        print(f"{'DONE ' if ok else 'TODO '} {f.name}  "
              f"({sum(r[0] for r in results)}/{len(results)})")
        if not ok and a.halt:
            print("HALT")
            sys.exit(1)

main()
