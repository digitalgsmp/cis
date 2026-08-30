#!/usr/bin/env python3.12
"""build_issue_list.py — distil mined statements into a working issue list.

The mining tools produce STATEMENTS: individual sentences from the corpus that
recognise a problem. That is raw material, not a work list. Eight different
sentences saying "there is no validation" are one issue, not eight.

This clusters statements by meaning, so each cluster is one candidate ISSUE. For
each it reports:
  - a representative statement, verbatim
  - how many statements support it (how often it was recognised)
  - how many distinct documents it appears in (independent recognition)
  - the documents themselves, so provenance is traceable
  - whether it matches anything already on the working queue

Clustering is by embedding similarity, not keywords, so "no validation layer
exists" and "outputs that fail are never flagged for review" land together.

Usage:
  python3.12 tools/build_issue_list.py --out docs/ISSUE_LIST.md
  python3.12 tools/build_issue_list.py --threshold 0.72 --out ...
"""
import argparse
import re
import sys

import numpy as np


def load_statements(paths):
    """(text, source, document) for every mined statement."""
    out = []
    for p in paths:
        src = doc = "?"
        for line in open(p):
            if line.startswith("- "):
                s = re.sub(r"\s*\(x(\d+)\)\s*$", "", line[2:].strip())
                s = s.replace("**NEW**", "").strip()
                if len(s) > 45:
                    out.append([s, None, None])
            elif line.strip().startswith("`[") and out:
                m = re.match(r"`\[([^\]]+)\]\s*(.*?)`", line.strip())
                if m and out[-1][1] is None:
                    out[-1][1], out[-1][2] = m.group(1), m.group(2)
    return [(t, s or "?", d or "?") for t, s, d in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="*",
                    default=["docs/SECONDARY_QUEUE.md",
                             "docs/SECONDARY_QUEUE_SEMANTIC.md"])
    ap.add_argument("--threshold", type=float, default=0.75,
                    help="cosine similarity for 'same issue'")
    ap.add_argument("--queue", default="docs/NEXT_SESSION.md")
    ap.add_argument("--min-support", type=int, default=2,
                    help="clusters with fewer statements are listed separately")
    ap.add_argument("--out")
    args = ap.parse_args()

    stmts = load_statements(args.files)
    print(f"statements: {len(stmts):,}")

    sys.path.insert(0, "/mnt/projects/cis/runtime")
    from mcp_bridge.chroma_index import ChromaClient
    client = ChromaClient()

    texts = [t for t, _, _ in stmts]
    emb = []
    for i in range(0, len(texts), 2000):
        emb.extend(client._embedding.embed(texts[i:i + 2000]))
        print(f"  embedded {min(i+2000, len(texts)):,}/{len(texts):,}", flush=True)
    E = np.array(emb, dtype=np.float32)
    E /= np.linalg.norm(E, axis=1, keepdims=True)

    # Greedy clustering: longest statement first becomes the representative,
    # everything close enough joins it. Deterministic given the same input.
    order = sorted(range(len(texts)), key=lambda i: -len(texts[i]))
    assigned = np.full(len(texts), -1)
    reps = []
    print("clustering...", flush=True)
    for i in order:
        if assigned[i] != -1:
            continue
        rid = len(reps)
        reps.append(i)
        sims = E @ E[i]
        members = np.where((sims >= args.threshold) & (assigned == -1))[0]
        assigned[members] = rid
        assigned[i] = rid
    print(f"clusters: {len(reps):,}")

    clusters = {}
    for idx, rid in enumerate(assigned):
        clusters.setdefault(rid, []).append(idx)

    # Match each cluster against the working queue
    qitems = []
    for line in open(args.queue):
        m = re.match(r"^(\d+)\. (.+)$", line)
        if m:
            qitems.append((int(m.group(1)), m.group(2).strip()))
    QE = np.array(client._embedding.embed([t for _, t in qitems]), dtype=np.float32)
    QE /= np.linalg.norm(QE, axis=1, keepdims=True)

    rows = []
    for rid, members in clusters.items():
        rep = reps[rid]
        docs = sorted({stmts[m][2] for m in members})
        # Match the queue against the BEST-matching member, not the longest one.
        # The representative is chosen for length so the entry reads well; the
        # statement that actually resembles a queue item is often a shorter one,
        # and scoring only the representative reported 0 matches where 6 existed.
        member_sims = QE @ E[members].T          # queue x members
        j = int(np.unravel_index(np.argmax(member_sims), member_sims.shape)[0])
        sims = member_sims.max(axis=1)
        rows.append({
            "text": texts[rep],
            "n": len(members),
            "docs": docs,
            "source": stmts[rep][1],
            "q_num": qitems[j][0] if qitems else None,
            "q_text": qitems[j][1] if qitems else "",
            "q_sim": float(sims[j]) if qitems else 0.0,
        })

    rows.sort(key=lambda r: (-len(r["docs"]), -r["n"]))

    strong = [r for r in rows if r["n"] >= args.min_support]
    singles = [r for r in rows if r["n"] < args.min_support]
    on_queue = [r for r in strong if r["q_sim"] >= 0.60]
    new = [r for r in strong if r["q_sim"] < 0.60]

    out = ["# ISSUE LIST — distilled from the mined record\n",
           "Built by tools/build_issue_list.py from docs/SECONDARY_QUEUE.md and",
           "docs/SECONDARY_QUEUE_SEMANTIC.md. Statements that mean the same thing",
           "are clustered into ONE issue. This is the working list; those two",
           "files are the raw material behind it.\n",
           "PROVENANCE for every entry: `support` is how many separate statements",
           "in the corpus say this; `docs` is how many distinct documents said it.",
           "High docs count = independently recognised in different places, which",
           "is stronger evidence than the same sentence repeated in one file.\n",
           "An entry proves a recognition was WRITTEN DOWN. It does NOT prove the",
           "issue is still open. Verify before acting — several checked on",
           "2026-08-29 turned out to be implemented by other means.\n",
           f"- clusters: {len(rows):,}",
           f"- with 2+ supporting statements: {len(strong):,}",
           f"- of those, already on the working queue: {len(on_queue):,}",
           f"- of those, NOT on the working queue: {len(new):,}",
           f"- single-statement clusters (listed last): {len(singles):,}\n"]

    def emit(title, items, limit=None):
        out.append(f"\n## {title}  ({len(items)})\n")
        for r in (items[:limit] if limit else items):
            out.append(f"### {r['text'][:300]}")
            out.append(f"- support: {r['n']} statements across {len(r['docs'])} document(s)")
            if r["q_sim"] >= 0.60:
                out.append(f"- MATCHES queue item {r['q_num']} (sim {r['q_sim']:.2f}): {r['q_text'][:90]}")
            else:
                out.append(f"- nearest queue item {r['q_num']} is only sim {r['q_sim']:.2f} — treat as NEW")
            for d in r["docs"][:6]:
                out.append(f"  - `{d[:96]}`")
            out.append("")

    emit("NOT on the working queue — candidates to merge", new)
    emit("Already represented on the working queue", on_queue)
    emit("Single-statement recognitions — weakest evidence", singles, limit=400)

    text = "\n".join(out)
    if args.out:
        open(args.out, "w").write(text + "\n")
        print(f"\nwrote {args.out}")
        print(f"  clusters {len(rows):,} | strong {len(strong):,} | "
              f"new {len(new):,} | already queued {len(on_queue):,}")
    else:
        print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
