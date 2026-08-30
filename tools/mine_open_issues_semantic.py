#!/usr/bin/env python3.12
"""mine_open_issues_semantic.py — find acknowledged issues by MEANING.

Companion to tools/mine_open_issues.py, which is purely lexical: it FTS5-matches
a list of marker strings and buckets the hits with regexes. That finds what
someone thought to name. It cannot find a recognition phrased in words that are
not on the list, and it cannot tell a complaint from a coincidence — it matched
a Blender document saying "separated by a small gap".

This one queries the vector index with PROBE STATEMENTS: sentences that express
the CONCEPT of an unresolved problem, in many phrasings. Nearest neighbours to a
probe are statements that mean something similar, whatever words they used.

Neither tool is sufficient alone. Eric, 2026-08-29: "the point of having these
different types of db is to run both for thoroughness." Use --merge to union
this with the lexical results and see what each found that the other missed.

Deterministic in the sense that matters: nothing is summarised or rewritten.
Output is verbatim corpus text with its source.

Usage:
  python3.12 tools/mine_open_issues_semantic.py --out docs/SECONDARY_QUEUE_SEMANTIC.md
  python3.12 tools/mine_open_issues_semantic.py --merge docs/SECONDARY_QUEUE.md --out ...
"""
import argparse
import os
import re
import sys
from collections import defaultdict

# Probes are grouped by the KIND of recognition, so results arrive already
# separated by what sort of problem they are. Each probe is a full sentence
# because the embedding model was trained on sentences, not keywords.
PROBES = {
    "Specified but never built": [
        "This was specified in a design document but the implementation was never written.",
        "The spec exists but there is no code implementing it.",
        "We designed this component and then never built it.",
        "The architecture describes a layer that does not exist in the codebase.",
        "This was planned as the next build target and was never started.",
    ],
    "Built but never connected": [
        "This function was written but nothing ever calls it.",
        "The code exists but was never wired into the application.",
        "The column was added to the schema but nothing ever populates it.",
        "This component has no integration point with the rest of the system.",
        "The feature is present but unreachable from the user's path.",
    ],
    "Recognised in passing, never actioned": [
        "I noticed this problem while doing something else and did not fix it.",
        "This is a known issue that we have not addressed.",
        "We keep running into this and it never gets resolved.",
        "This came up again, the same problem as before.",
        "Noting this here so it is not forgotten, though nothing was done about it.",
    ],
    "Deferred deliberately, may now be due": [
        "We decided to defer this until a later phase.",
        "This was postponed because something else had to come first.",
        "Out of scope for now, revisit when the prerequisite is done.",
        "Blocked until the dependency is resolved.",
    ],
    "Manual work that should be automated": [
        "Eric has to do this step by hand every time.",
        "This requires manual copy and paste between systems.",
        "The human is still the relay between these components.",
        "There is no trigger for this, someone has to remember to run it.",
        "This should happen automatically but currently does not.",
    ],
    "Silent failure — breaks without reporting": [
        "This fails silently and nothing reports the error.",
        "The failure is swallowed and the caller sees a normal result.",
        "There is no validation, so bad input passes through unnoticed.",
        "Nothing checks whether this actually worked.",
        "The error is caught and discarded without logging.",
    ],
    "Claims made without evidence": [
        "The model claimed something that turned out not to be true.",
        "This described a capability that does not exist as described.",
        "The status says complete but the functionality does not work.",
        "It reported success without verifying the result.",
    ],
    "Enforcement that does not enforce": [
        "This rule is written down but nothing prevents violating it.",
        "The guardrail is advisory and does not actually block anything.",
        "The gate can be bypassed because it is only a convention.",
        "Governance exists in documentation but not in the application.",
    ],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-probe", type=int, default=40,
                    help="nearest neighbours to pull per probe sentence")
    ap.add_argument("--min-chars", type=int, default=60)
    ap.add_argument("--out")
    ap.add_argument("--merge", help="lexical SECONDARY_QUEUE.md to compare against")
    args = ap.parse_args()

    sys.path.insert(0, "/mnt/projects/cis/runtime")
    from mcp_bridge.chroma_index import ChromaClient
    client = ChromaClient()
    coll = client._client.get_collection("knowledge_messages")
    print(f"collection: {coll.count():,} vectors", flush=True)

    found = defaultdict(dict)          # kind -> {normalised: (text, source, key)}
    for kind, probes in PROBES.items():
        embs = client._embedding.embed(probes)
        for probe, e in zip(probes, embs):
            r = coll.query(query_embeddings=[e], n_results=args.per_probe,
                           include=["documents", "metadatas"])
            for d, m in zip(r["documents"][0], r["metadatas"][0]):
                if not d or len(d) < args.min_chars:
                    continue
                text = " ".join(d.split())
                key = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
                key = " ".join(key.split())[:160]
                if key not in found[kind]:
                    found[kind][key] = (text, (m or {}).get("source", "?"),
                                        (m or {}).get("source_key", ""))
        print(f"  {kind}: {len(found[kind])}", flush=True)

    # Cross-kind dedupe: keep a statement in the kind that found it first.
    seen = set()
    for kind in PROBES:
        for k in list(found[kind]):
            if k in seen:
                del found[kind][k]
            else:
                seen.add(k)

    lex = set()
    if args.merge and os.path.exists(args.merge):
        for line in open(args.merge):
            if line.startswith("- "):
                s = re.sub(r"\s*\(x\d+\)$", "", line[2:].strip())
                s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
                lex.add(" ".join(s.split())[:160])
        print(f"\nlexical statements loaded for comparison: {len(lex):,}")

    out = ["# SECONDARY QUEUE (SEMANTIC) — issues found by meaning\n",
           "Generated by tools/mine_open_issues_semantic.py.",
           "Found by embedding probe sentences that EXPRESS the concept of an",
           "unresolved problem and pulling their nearest neighbours from the",
           "vector index. This finds recognitions phrased in words no keyword",
           "list would have contained.\n",
           "Run alongside the lexical pass (tools/mine_open_issues.py). Neither",
           "is sufficient alone: keyword finds what someone thought to name,",
           "semantic finds what they did not. NEW means the lexical pass missed",
           "it entirely.\n",
           "An entry proves a recognition was WRITTEN DOWN, not that it is still",
           "open. Verify before acting.\n"]

    total = new_total = 0
    for kind in PROBES:
        items = list(found[kind].values())
        if not items:
            continue
        total += len(items)
        news = [i for k, i in found[kind].items() if k not in lex]
        new_total += len(news)
        out.append(f"\n## {kind}  ({len(items)}, {len(news)} not found lexically)\n")
        for text, source, skey in items:
            k = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
            k = " ".join(k.split())[:160]
            tag = " **NEW**" if lex and k not in lex else ""
            short = skey if len(skey) <= 58 else "..." + skey[-55:]
            out.append(f"- {text[:400]}{tag}\n  `[{source}] {short}`")

    text = "\n".join(out)
    if args.out:
        open(args.out, "w").write(text + "\n")
        print(f"\nwrote {args.out}")
        print(f"  statements: {total}")
        if lex:
            print(f"  not found by the lexical pass: {new_total}")
    else:
        print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
