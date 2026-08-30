#!/usr/bin/env python3.12
"""find_specs_by_content.py — find specifications by what they SAY, not their name.

Eric, 2026-08-29: "It looks like you are targeting files with words like spec and
contract. If you actually read the files for the context you will find
descriptions of functionality or capability."

Filename matching found 181 documents in one directory and missed everything
called something else. A specification is identified by its CONTENT: normative
language, defined inputs and outputs, state machines, field tables, failure
modes, interfaces.

This reads every document and scores it on those signals. Deterministic — no
model, no embeddings. Scores are transparent and every hit lists which signals
fired, so a judgement can be checked.

Usage:
  python3.12 tools/find_specs_by_content.py --min-score 6
  python3.12 tools/find_specs_by_content.py --out docs/SPEC_INVENTORY_BY_CONTENT.md
"""
import argparse
import os
import re

ROOT = "/mnt/projects/cis"
SKIP_DIRS = {".git", "node_modules", "site-packages", ".venv", "venv",
             "__pycache__", ".pytest_cache", "dist-info"}

# Each signal is (name, regex, weight). Weights reflect how strongly the signal
# indicates a SPECIFICATION rather than a narrative, transcript, or log.
SIGNALS = [
    # Normative language — the strongest single marker of a spec.
    ("normative MUST/SHALL", re.compile(
        r"\b(MUST NOT|MUST|SHALL NOT|SHALL|MAY NOT|is required to|is prohibited)\b"), 3),
    ("rule statements", re.compile(
        r"^\s*(#+\s*)?(Rule|Core Rule|Constraint|Invariant|Requirement)s?\b[:\s]", re.M | re.I), 3),
    # Structure that only specs have
    ("state machine", re.compile(
        r"\b(state machine|allowed transitions?|state transitions?|terminal states?|"
        r"active states?)\b", re.I), 3),
    ("defined states list", re.compile(
        r"`?[a-z_]+`?\s*(?:->|→)\s*`?[a-z_]+`?", ), 1),
    ("field/schema table", re.compile(
        r"^\|.*\|(?:\s*-+\s*\|)+", re.M), 2),
    ("schema block", re.compile(
        r"\b(schema|canonical fields?|required fields?|field definitions?)\b[:\s]", re.I), 2),
    ("inputs and outputs", re.compile(
        r"\b(input[s]?\s*[:|]|output[s]?\s*[:|]|returns?\s*[:|]|parameters?\s*[:|])", re.I), 1),
    ("failure modes", re.compile(
        r"\b(failure mode|fail(?:ure)? condition|error handling|on failure|"
        r"exit code|FAIL\s*[:|]|rejection)\b", re.I), 2),
    ("validation rules", re.compile(
        r"\b(validation rule|validates? that|must validate|verification requirement)\b", re.I), 2),
    ("interface/API definition", re.compile(
        r"\b(GET|POST|PUT|DELETE)\s+/[a-z]|endpoint[s]?\s*[:|]|interface\s*[:|]", re.I), 2),
    ("purpose section", re.compile(
        r"^\s*#+\s*(Purpose|Scope|Overview)\b", re.M | re.I), 2),
    ("status/authority header", re.compile(
        r"^\s*#?\s*(Status|Contract Authority|ADR reference|Parent contracts?)\s*[:|]", re.M | re.I), 3),
    ("numbered sections", re.compile(r"^#+\s*\d+\.\s+\w", re.M), 2),
    ("capability description", re.compile(
        r"\b(capabilit(?:y|ies)|behaviou?r\s+(?:is|must|shall)|responsib(?:le|ility) for|"
        r"the system (?:must|shall|will|provides?))\b", re.I), 2),
]

# Documents that describe functionality but are NOT specs: transcripts, logs,
# session narratives, and the derived extraction analyses.
NEGATIVE = [
    ("chat transcript", re.compile(
        r"^\s*(You said:|ChatGPT said:|\[user\]|\[assistant\]|Claude responded|"
        r"Thought for |Edit\s*$|Retry\s*$)", re.M), -14),
    ("extraction analysis", re.compile(
        r"^#\s*Extraction Analysis:", re.M), -20),
    ("session narrative", re.compile(
        r"^#+\s*(What (?:this session|failed|changed)|Session (?:Focus|Insight))", re.M | re.I), -8),
    ("log output", re.compile(r"^\s*\d{4}-\d\d-\d\d[T ]\d\d:\d\d", re.M), -3),
    # Conversational second person is the clearest transcript tell. A spec does
    # not say "you should" or "let me" or "here's what I found".
    ("conversational voice", re.compile(
        r"\b(let me |here'?s what|I'?ll |you'?ll want|do you want|"
        r"good question|you'?re right|I can help|shall I )\b", re.I), -10),
    ("dated chat filename body", re.compile(
        r"^\s*#\s*\d{4}-\d\d-\d\d[_ ]", re.M), -6),
]

# Files whose PATH marks them as derived, staged, or a duplicate import rather
# than an authored specification. These are not deleted from the results, they
# are flagged, because a spec that only survives in an import is still a spec.
DERIVED_PATH = re.compile(
    r"/tagging_input/|/tagging_results/|/extraction/functional_intents/|"
    r"_extraction_analysis|/cis_kernel/source/transcripts|/_archive/|"
    r"/claude_chat_transcripts/", re.I)


def walk():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.lower().endswith((".md", ".txt")):
                yield os.path.join(dirpath, fn)


def score(text):
    hits, total = [], 0
    for name, rx, w in SIGNALS:
        n = len(rx.findall(text))
        if n:
            # cap each signal's contribution so one repeated pattern cannot
            # carry a document on its own
            contrib = w * min(n, 3)
            total += contrib
            hits.append(f"{name}x{n}")
    for name, rx, w in NEGATIVE:
        if rx.search(text):
            total += w
            hits.append(f"NEG:{name}")
    return total, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-score", type=int, default=14)
    ap.add_argument("--min-chars", type=int, default=800)
    ap.add_argument("--out")
    args = ap.parse_args()

    import hashlib
    results, scanned, skipped = [], 0, 0
    seen_hash = {}
    dup_count = 0
    for path in walk():
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read(120000)
        except Exception:
            continue
        scanned += 1
        if len(text) < args.min_chars:
            skipped += 1
            continue
        s, hits = score(text)
        if s < args.min_score:
            continue
        # De-duplicate by content. The same document exists in up to five
        # places (docs/, data/drive_imports/, cis_kernel/source/,
        # tagging_input/, _archive/). Keep the copy in the least-derived path.
        h = hashlib.sha256(re.sub(r"\s+", " ", text[:20000]).encode()).hexdigest()
        derived = bool(DERIVED_PATH.search(path))
        if h in seen_hash:
            dup_count += 1
            prev = seen_hash[h]
            if prev["derived"] and not derived:
                prev["path"], prev["derived"] = path, derived
            prev["copies"] += 1
            continue
        seen_hash[h] = {"score": s, "path": path, "hits": hits,
                        "len": len(text), "derived": derived, "copies": 1}

    results = [(v["score"], v["path"], v["hits"], v["len"], v["copies"],
                v["derived"]) for v in seen_hash.values()]
    results.sort(key=lambda r: -r[0])
    print(f"duplicate copies collapsed: {dup_count:,}")
    print(f"documents scanned : {scanned:,}")
    print(f"too short to judge: {skipped:,}")
    print(f"score >= {args.min_score}      : {len(results):,}")

    # how many would a filename search have found?
    fn_pat = re.compile(r"spec|contract|design|proposal|architecture|adr|blueprint|schema", re.I)
    by_name = sum(1 for r in results if fn_pat.search(os.path.basename(r[1])))
    print(f"  of those, findable by filename: {by_name:,}")
    print(f"  MISSED by filename search     : {len(results)-by_name:,}")

    if args.out:
        lines = ["# SPEC INVENTORY BY CONTENT\n",
                 "Documents identified as specifications by WHAT THEY SAY, not by",
                 "filename. Built by tools/find_specs_by_content.py — deterministic,",
                 "no model. Each entry lists the signals that fired so the judgement",
                 "can be checked.\n",
                 f"- scanned: {scanned:,} documents",
                 f"- scoring >= {args.min_score}: {len(results):,}",
                 f"- **findable by filename: {by_name:,}**",
                 f"- **missed by any filename search: {len(results)-by_name:,}**\n"]
        for s, p, hits, ln, copies, derived in results:
            rel = p.replace(ROOT + "/", "")
            flag = "" if fn_pat.search(os.path.basename(p)) else "  NAME-BLIND"
            d = "  (derived/import path)" if derived else ""
            c = f", {copies} copies" if copies > 1 else ""
            lines.append(f"\n### [{s}] {rel}{flag}{d}")
            lines.append(f"- {ln:,} chars{c} — signals: {', '.join(hits[:9])}")
        open(args.out, "w").write("\n".join(lines) + "\n")
        print(f"\nwrote {args.out}")
    else:
        for r in results[:40]:
            print(f"  {r[0]:4}  {r[1].replace(ROOT+'/','')[:88]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
