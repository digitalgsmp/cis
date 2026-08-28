#!/usr/bin/env python3
"""corpus_to_asks.py — turn ranked theme clusters into card-generator asks.

The corpus says what has weighed on this project most; it does not say it in
Eric's words, and a card must quote Eric. Each theme in synthesis_evidence
carries the verbatim quote that produced it, so this walks:

    theme cluster -> member themes -> evidence quotes -> authorship filter

Only quotes that appear in the spine under a role Eric authored survive. That is
the same test card_gate applies, so anything emitted here can pass the gate.

Ranking is by how many records back the cluster — a count, not a judgment.

Usage:
  python3 tools/corpus_to_asks.py --clusters cards/theme_clusters.json \
      --top 40 --out cards/asks_corpus.jsonl
"""
import argparse
import json
import re
import sqlite3
import sys

MODEL_ROLES = {'assistant', 'brain', 'draft', 'review1', 'review2', 'menter',
               'verify', 'review1_consensus', 'revision_directive'}

# Authorship proves Eric typed it; it does not prove he was asking for something.
# Evidence quotes are frequently terminal output and logs he pasted, which are
# his rows in the spine but carry no intent. Same filters mine_asks.py applies.
NOISE = re.compile(
    r'(PS C:\\|Traceback \(|INFO: {2,}|npm error|Requirement already satisfied|'
    r'^\s*\$ |sudo |docker (exec|build|run)|^eric@|Get-ChildItem|=== T\d|'
    r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d|HTTP/1\.[01]"? \d{3}|'
    r'\d+\.\d+\.\d+\.\d+:\d+|checks passed)', re.M)


def looks_prose(text):
    """True if the text contains at least one plain sentence of 8+ words."""
    for sent in re.split(r'[.!?\n]', text):
        words = sent.split()
        if len(words) >= 8 and not re.search(r'[\\/{}<>=]|--', sent):
            return True
    return False


def authored_by_eric(con, quote, cache):
    """True if this phrase exists in the spine outside model-authored rows."""
    toks = re.findall(r"[A-Za-z0-9']+", quote.lower())
    if len(toks) < 5:
        return False
    phrase = ' '.join(t.replace("'", '') for t in toks[:8])
    if phrase in cache:
        return cache[phrase]
    try:
        rows = con.execute(
            "SELECT m.role FROM knowledge_messages_fts f "
            "JOIN knowledge_messages m ON m.id = f.rowid "
            "WHERE knowledge_messages_fts MATCH ? LIMIT 40",
            (f'"{phrase}"',)).fetchall()
        ok = any(r[0] not in MODEL_ROLES for r in rows)
    except sqlite3.OperationalError:
        ok = False
    cache[phrase] = ok
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clusters', default='cards/theme_clusters.json')
    ap.add_argument('--synth', default='cards/synthesis.db')
    ap.add_argument('--db', default='data/cis_memory.db')
    ap.add_argument('--top', type=int, default=40)
    ap.add_argument('--per-cluster', type=int, default=3)
    ap.add_argument('--project', default='cis')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    clusters = json.load(open(a.clusters))[:a.top]
    synth = sqlite3.connect(a.synth)
    spine = sqlite3.connect(a.db)
    cache = {}

    written = skipped = noise = 0
    with open(a.out, 'w') as out:
        for rank, cl in enumerate(clusters, 1):
            members = cl.get('members') or cl.get('samples') or []
            if not members:
                continue
            marks = ','.join('?' * len(members))
            rows = synth.execute(
                f"SELECT quote, source, date FROM synthesis_evidence "
                f"WHERE theme IN ({marks}) AND quote IS NOT NULL "
                f"AND length(quote) > 40 GROUP BY quote", members).fetchall()

            kept = 0
            for quote, source, date in rows:
                if kept >= a.per_cluster:
                    break
                q = quote.strip()
                if NOISE.search(q) or not looks_prose(q):
                    noise += 1
                    continue
                if not authored_by_eric(spine, q, cache):
                    skipped += 1
                    continue
                out.write(json.dumps({
                    'id': f'corpus-r{rank:03d}-{kept}',
                    'date': (date or '')[:10],
                    'project': a.project,
                    'noisy': False,
                    'theme': cl['label'],
                    'theme_records': cl['records'],
                    'rank': rank,
                    'source': source,
                    'text': q[:1500],
                }) + '\n')
                kept += 1
                written += 1

            print(f'  [{rank:3}] {cl["records"]:5} records  {kept} ask(s)  '
                  f'{cl["label"][:56]}')

    print(f'\n{written} asks -> {a.out}')
    print(f'  rejected: {noise} as log/terminal output, '
          f'{skipped} as not Eric-authored')
    return 0


if __name__ == '__main__':
    sys.exit(main())
