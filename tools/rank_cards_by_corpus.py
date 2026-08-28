#!/usr/bin/env python3.12
"""rank_cards_by_corpus.py — order existing cards by how persistently the corpus
raises the theme behind them.

The corpus cannot produce asks (its evidence quotes are descriptions, not
requests — proven by feeding them to the generator, which returned NO_CARD on
every one). What it can do is say which concerns recur most across 700 sessions.

So: match each existing card to its nearest theme cluster and inherit that
cluster's record count as priority. The ordering comes from counting, not from
any model's opinion about what matters.

Usage:
  python3.12 tools/rank_cards_by_corpus.py --cards cards/inbox --out cards/card_ranking.md
"""
import argparse
import glob
import json
import os
import re
import sys

import numpy as np
from sentence_transformers import SentenceTransformer


def card_text(path):
    """INTENT + BUILD carry the substance; the rest is scaffolding."""
    txt = open(path, errors='ignore').read()
    keep = []
    for name in ('INTENT', 'BUILD'):
        m = re.search(rf'^{name}.*?(?=^(?:BUILD|DONE WHEN|EVIDENCE|NOT IN)\b)',
                      txt, re.S | re.M)
        if m:
            keep.append(m.group(0))
    return ' '.join(keep)[:1200] or txt[:600]


def rank_asks(a, clusters, labels):
    """Reorder an asks JSONL so the generator builds the heaviest themes first."""
    rows = [json.loads(l) for l in open(a.asks) if l.strip()]
    if not rows:
        print(f'no asks in {a.asks}', file=sys.stderr)
        return 1
    model = SentenceTransformer('all-MiniLM-L6-v2')
    lab = model.encode(labels, batch_size=256, normalize_embeddings=True,
                       show_progress_bar=False).astype(np.float32)
    def ask_text(r):
        """Miners disagree on field names: mine_asks.py writes 'text',
        mine_asks_sessions.py writes verbatim_quotes + interpretation."""
        for k in ('text', 'verbatim_quotes'):
            if r.get(k):
                v = r[k]
                extra = r.get('interpretation') or r.get('session_title') or ''
                return f'{v} {extra}'[:1000]
        return (r.get('session_title') or '')[:1000]

    txt = model.encode([ask_text(r) for r in rows], batch_size=64,
                       normalize_embeddings=True,
                       show_progress_bar=False).astype(np.float32)
    sims = np.dot(txt, lab.T)
    for i, r in enumerate(rows):
        j = int(np.argmax(sims[i]))
        r['corpus_theme'] = clusters[j]['label']
        r['corpus_records'] = clusters[j]['records']
        r['corpus_match'] = round(float(sims[i][j]), 3)
    rows.sort(key=lambda r: (-r['corpus_records'], -r['corpus_match']))
    with open(a.out, 'w') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')
    print(f'{len(rows)} asks reordered -> {a.out}')
    for r in rows[:8]:
        print(f'  {r["corpus_records"]:5}  {r["corpus_match"]:.2f}  '
              f"{ask_text(r)[:62]}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cards', default='cards/inbox')
    ap.add_argument('--asks', help='rank an asks JSONL instead of card files; '
                                   'writes a reordered JSONL for the generator')
    ap.add_argument('--clusters', default='cards/theme_clusters.json')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    clusters = json.load(open(a.clusters))
    labels = [c['label'] for c in clusters]

    if a.asks:
        return rank_asks(a, clusters, labels)

    paths = sorted(glob.glob(os.path.join(a.cards, '*.md')))
    if not paths:
        print(f'no cards under {a.cards}', file=sys.stderr)
        return 1

    model = SentenceTransformer('all-MiniLM-L6-v2')
    lab_emb = model.encode(labels, batch_size=256, normalize_embeddings=True,
                           show_progress_bar=False).astype(np.float32)
    texts = [card_text(p) for p in paths]
    card_emb = model.encode(texts, batch_size=64, normalize_embeddings=True,
                            show_progress_bar=False).astype(np.float32)

    scored = []
    sims_all = np.dot(card_emb, lab_emb.T)
    for i, p in enumerate(paths):
        j = int(np.argmax(sims_all[i]))
        scored.append({
            'card': os.path.basename(p),
            'theme': clusters[j]['label'],
            'records': clusters[j]['records'],
            'match': float(sims_all[i][j]),
        })
    scored.sort(key=lambda s: (-s['records'], -s['match']))

    with open(a.out, 'w') as f:
        f.write('# Card ranking by corpus weight\n\n')
        f.write('Each card matched to its nearest theme cluster; the count is '
                'how many records back that theme across the corpus.\n')
        f.write('Ordering is by count, not by judgment. A weak match score '
                'means the card has no strong theme behind it.\n\n')
        f.write('| records | match | card | nearest theme |\n')
        f.write('|--------:|------:|------|---------------|\n')
        for s in scored:
            f.write(f'| {s["records"]} | {s["match"]:.2f} | {s["card"][:52]} '
                    f'| {s["theme"][:46]} |\n')

    print(f'{len(scored)} cards ranked -> {a.out}')
    for s in scored[:10]:
        print(f'  {s["records"]:5}  {s["match"]:.2f}  {s["card"][:46]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
