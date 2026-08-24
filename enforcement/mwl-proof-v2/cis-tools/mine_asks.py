#!/usr/bin/env python3
"""mine_asks.py — deterministically extract Eric's candidate 'direct asks' from the spine.

No LLM involved. Reads knowledge_messages (role=human), filters terminal-paste noise,
writes JSONL candidates for the card generator.

Usage:
  python3 tools/mine_asks.py --db data/cis_memory.db --project swa --out cards/asks_swa.jsonl
"""
import argparse
import json
import re
import sqlite3

KEYWORDS = {
    "swa": ['SWA', '"social work"', '"case management"', 'DAP', 'CCS',
            '"secure note"', '"recovery plan"', '"progress note"', 'intake', 'CSSRS'],
    "wiasw": ['WIASW', 'WIAS', '"creative production"', '"project management"',
              'storyboard', '"asset management"', 'workbook'],
    "cis": ['CIS', 'pipeline', 'portal', '"control plane"', 'spine'],
}

# Lines that mark pasted terminal output rather than Eric's own sentences.
NOISE = re.compile(
    r'(PS C:\\|Traceback \(|INFO: {2,}|npm error|Requirement already satisfied|'
    r'^\s*\$ |sudo |docker (exec|build|run)|^eric@|Get-ChildItem|=== T\d)', re.M)


def looks_prose(text):
    """True if the message contains at least one plain sentence of 8+ words."""
    for sent in re.split(r'[.!?\n]', text):
        words = sent.split()
        if len(words) >= 8 and not re.search(r'[\\/{}<>=]|--', sent):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--project', required=True, choices=sorted(KEYWORDS))
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int, default=400)
    a = ap.parse_args()

    query = ' OR '.join(KEYWORDS[a.project])
    con = sqlite3.connect(a.db)
    rows = con.execute(
        "SELECT m.id, m.timestamp, m.content FROM knowledge_messages m "
        "WHERE m.role='human' AND m.id IN "
        "(SELECT rowid FROM knowledge_messages_fts WHERE knowledge_messages_fts MATCH ?) "
        "ORDER BY m.timestamp LIMIT ?", (query, a.limit)).fetchall()

    kept = 0
    with open(a.out, 'w') as f:
        for mid, ts, content in rows:
            noisy = bool(NOISE.search(content))
            if noisy and not looks_prose(content):
                continue  # pure terminal paste, no Eric sentences in it
            f.write(json.dumps({
                'id': mid,
                'date': (ts or '')[:10],
                'project': a.project,
                'noisy': noisy,
                'text': content[:1500],
            }) + '\n')
            kept += 1
    print(f'{kept} candidate asks -> {a.out} (from {len(rows)} FTS matches)')


if __name__ == '__main__':
    main()
