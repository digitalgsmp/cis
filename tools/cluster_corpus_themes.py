#!/usr/bin/env python3.12
"""cluster_corpus_themes.py — reduce the extracted corpus to ranked themes.

synthesis.db holds ~27k blocker records and ~38k theme records, most of them the
same problem phrased many ways. This collapses them into ranked clusters so the
corpus can be acted on. Local compute only: no API calls, no model judgment here.

The output is a proposal, not a conclusion — cluster membership is decided by
string similarity, so a reviewer still has to read the labels and reject bad
merges before anything downstream trusts them.

Usage:
  python3.12 tools/cluster_corpus_themes.py --out cards/corpus_clusters.json
  python3.12 tools/cluster_corpus_themes.py --table synthesis_themes --column theme
"""
import argparse
import json
import re
import sqlite3
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

STOP = re.compile(r'\b(the|a|an|of|for|to|in|and|is|are|no|not|due|with|on)\b')


def normalise(s):
    s = s.lower().strip()
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = STOP.sub(' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='cards/synthesis.db')
    ap.add_argument('--table', default='synthesis_blockers')
    ap.add_argument('--column', default='blocker')
    ap.add_argument('--domain-column', default='affected_domain')
    ap.add_argument('--threshold', type=float, default=0.70)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    con = sqlite3.connect(a.db)
    try:
        rows = con.execute(
            f'SELECT {a.column}, {a.domain_column}, COUNT(*) '
            f'FROM {a.table} GROUP BY {a.column}, {a.domain_column}').fetchall()
    except sqlite3.OperationalError:
        rows = con.execute(
            f'SELECT {a.column}, NULL, COUNT(*) '
            f'FROM {a.table} GROUP BY {a.column}').fetchall()
    con.close()
    print(f'{len(rows)} distinct ({a.column}, domain) pairs')

    agg = {}
    for text, domain, n in rows:
        if not text:
            continue
        key = normalise(text)
        if not key:
            continue
        e = agg.setdefault(key, {'n': 0, 'variants': set(), 'domains': {}})
        e['n'] += n
        e['variants'].add(text)
        if domain:
            e['domains'][domain] = e['domains'].get(domain, 0) + n

    keys = sorted(agg, key=lambda k: -agg[k]['n'])
    print(f'{len(keys)} after normalisation')

    model = SentenceTransformer('all-MiniLM-L6-v2')
    emb = model.encode(keys, batch_size=256, show_progress_bar=False,
                       normalize_embeddings=True).astype(np.float32)
    print('embedded, clustering...')

    centroids, members = [], []
    for i in range(len(keys)):
        v = emb[i]
        if centroids:
            sims = np.dot(np.vstack(centroids), v)
            j = int(np.argmax(sims))
            if sims[j] >= a.threshold:
                members[j].append(i)
                k = len(members[j])
                c = (centroids[j] * (k - 1) + v) / k
                centroids[j] = c / np.linalg.norm(c)
                continue
        centroids.append(v.copy())
        members.append([i])

    clusters = []
    for m in members:
        variants, domains, total = set(), {}, 0
        for i in m:
            e = agg[keys[i]]
            total += e['n']
            variants |= e['variants']
            for d, dn in e['domains'].items():
                domains[d] = domains.get(d, 0) + dn
        head = max(m, key=lambda i: agg[keys[i]]['n'])
        clusters.append({
            'label': sorted(agg[keys[head]]['variants'], key=len)[0],
            'records': total,
            'phrasings': len(variants),
            'domains': sorted(domains, key=domains.get, reverse=True)[:4],
            'samples': sorted(variants, key=len)[:4],
            # full membership, so downstream can join these back to
            # synthesis_evidence and recover the quotes behind each cluster
            'members': sorted(variants),
        })
    clusters.sort(key=lambda c: -c['records'])

    with open(a.out, 'w') as f:
        json.dump(clusters, f, indent=1)

    total = sum(c['records'] for c in clusters)
    top = sum(c['records'] for c in clusters[:30])
    print(f'{len(clusters)} clusters -> {a.out}')
    print(f'top 30 cover {top}/{total} records ({100*top//max(total,1)}%)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
