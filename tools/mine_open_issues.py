#!/usr/bin/env python3.12
"""mine_open_issues.py — acknowledged issues from the record, by category.

Purpose (Eric, 2026-08-29): specs were written as issues were uncovered, but
NOT every issue got a spec. Much of it is comments of recognition — someone
noticing a problem in passing. Those are clues, not noise, and they must not be
dropped because a marker looks weak or because the count is inconvenient.

So nothing is eliminated for being numerous. Reduction happens two ways only:
  1. DUPLICATION — the same recognition restated across chunks and documents.
  2. CATEGORY — statements are grouped by what they are ABOUT, so a category can
     be read as a whole instead of a flat list.

Deterministic. No model, no summarisation. Every line is a verbatim sentence
from the corpus with the document that said it.

An entry proves an issue was once WRITTEN DOWN. It does not prove the issue is
still open. Verify before acting.

Usage:
  python3.12 tools/mine_open_issues.py --out docs/SECONDARY_QUEUE.md
  python3.12 tools/mine_open_issues.py --include-sessions --out docs/SECONDARY_QUEUE.md
"""
import argparse
import os
import re
import sqlite3
from collections import defaultdict

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")

DOC_SOURCES = ("cis_docs", "cis_contracts", "cis_adrs", "cis_handoffs",
               "cis_kernel", "cis_drafts", "cis_ingest", "cis_v1_vault",
               "cis_legacy_archive", "pve_architecture")
SESSION_SOURCES = ("claude_code", "claude_export", "chatgpt_export",
                   "claude_transcripts", "hermes_prime", "hermes_v4pro",
                   "hermes_r1", "hermes_v4impl", "hermes_glm-reviewer",
                   "hermes_glm-verifier", "hermes_menter")

# Every marker is kept. Recognition-in-passing is the point of this tool.
MARKERS = [
    "not implemented", "not yet built", "needs implementation", "remaining gap",
    "not enforced", "known limitation", "blocked by", "open question",
    "open questions", "future work", "out of scope", "unresolved", "deferred",
    "gap", "missing", "does not exist", "never built", "still needed",
    "no implementation", "not wired", "placeholder", "stubbed", "incomplete",
    "not covered", "cannot enforce", "no validation", "silently",
]

# Third-party product documentation. Its "todo" is a TOOL NAME and its
# "blocked by policy" is a feature description — neither is a CIS issue.
VENDOR_DOC = re.compile(r"Hermes Agent Full Documentation|hermes-kanban-v1-spec",
                        re.I)
NOISE = re.compile(
    r"gap analysis|mind the gap|no gaps|gaps? (?:were |was )?closed|"
    r"SECONDARY QUEUE|mine_open_issues", re.I)

# Template scaffolding from handoff and status formats — the FORM asking about
# deferred work, not anyone recognising a problem. "Anything deferred that is
# not a next step" appeared 178 times as a section heading.
BOILERPLATE = re.compile(
    r"^anything deferred|^deferred\s*[:|]?\s*$|^\s*deferred\s*\|"
    r"|^(?:transitional|deferred|planned|pre-draft)\s*\|\s*various"
    r"|^list any|^note any|^record any|^\(if any\)|^n/?a\b"
    r"|^status\s*[:|]|^\|?\s*status\s*\|"
    # Bracketed status-taxonomy labels: "[DEFERRED] — Identified but not yet
    # built", "[TRANSITIONAL] — Exists but is temporary". These define the
    # vocabulary; they are not instances of anyone noticing a problem.
    r"|^\[?(?:deferred|transitional|planned|pre-?draft|locked|operational)\]?\s*"
    r"[-—:|]\s*(?:identified|exists|temporary|not yet)", re.I)

# Categories are the project's own domains. First match wins, so order matters:
# specific before general.
CATEGORIES = [
    # Put first: the project's central complaint. "Human operator still manually
    # bridges incomplete orchestration layers" was landing in Uncategorised,
    # which is how a third of the corpus hid the thing it is most about.
    ("Orchestration gap — the human is still the bridge",
     r"manual(?:ly)? (?:bridge|relay|paste|copy|transport|step|intervention)|"
     r"human (?:operator|relay|in the loop|bridge)|eric (?:manually|still has|"
     r"is the relay|must)|by hand|copy.?paste|orchestrat|automat|"
     r"reduce.{0,20}burden|execution bridge|missing layer|not triggered|"
     r"no trigger|still requires"),
    # "Execution Layer as Missing Foundational Layer", "the missing conceptual
    # structure", "this gap was never structurally closed" — recognitions that
    # something is absent from the ARCHITECTURE rather than from the code.
    ("Architecture & missing layers",
     r"architectur|conceptual structure|foundational|architecture map|"
     r"missing (?:piece|layer|foundation|relationship|structure|conceptual)|"
     r"layered|topology|structurally (?:closed|missing)|design gap|"
     r"missing the|whole picture"),
    ("Model behaviour, honesty & drift",
     r"hallucinat|described a capability|does not exist as described|"
     r"reassuring|sycophan|rubber.?stamp|self.?report|claimed .{0,20}without|"
     r"overstat|confabulat|guess(?:ed|ing)?\b|drift"),
    ("Security, auth & secrets",
     r"auth(?:entication|orisation|orization)?\b|secret|credential|token|"
     r"api key|permission|exposed|external access|security review"),
    ("Roadmap, phasing & scope",
     r"phase \d|tier \d|roadmap|milestone|next step|sequencing|prioriti|"
     r"backlog|out of phase"),
    ("Gates, guardrails & enforcement",
     r"\bgate|guardrail|enforce|hook|block(?:ing|ed)? (?:the )?(?:run|agent)|"
     r"non-bypass|bypass|policy|mwl|proof"),
    ("Eric Gate, approval & provenance",
     r"eric gate|approval|approve|briefing|provenance|decision trail|"
     r"goal_reference|rejection rationale"),
    ("KB, retrieval, embeddings & search",
     r"\bkb\b|knowledge|chroma|embed|vector|semantic|fts5?|retriev|index|"
     r"search|corpus"),
    ("Ingest, catalog & extraction",
     r"ingest|catalog|extract|scrap|mine|distil|chunk|import"),
    ("Pipeline, runs & deliberation",
     r"pipeline|deliberat|consensus|round|drafter|reviewer|relay|dispatch|"
     r"workflow_run|escalat|verifier|menter"),
    ("Agents, roles & prompts",
     r"\bagent|role|profile|persona|prompt|soul|overlay|skill|hermes profile"),
    ("Schema, spine & database",
     r"schema|sqlite|spine|table|column|migration|foreign key|\bdb\b|database"),
    ("Container, deployment & environment",
     r"container|docker|image|mount|lxc|proxmox|env var|venv|deploy"),
    ("UI, dashboard & API",
     r"dashboard|\bui\b|frontend|panel|endpoint|\bapi\b|route|http"),
    ("Storage, filesystem & backup",
     r"backup|storage|filesystem|drive|disk|archive|retention|/mnt/"),
    ("Sessions, handoff & context",
     r"session|handoff|context|closeout|memory|transcript|continuity"),
    ("Verification, evidence & claims",
     r"verif|evidence|claim|proof|audit|test|validate|check"),
    ("Governance docs & decisions",
     r"\badr\b|governance|contract|spec\b|proposal|decision|charter|tier"),
]


def sentences(text):
    for s in re.split(r"(?<=[.!?])\s+|\n+", text):
        s = " ".join(s.split())
        s = re.sub(r"^[-*|#>\s]+", "", s).strip(" |")
        if 35 <= len(s) <= 400:
            yield s


def doc_name(source_key):
    k = source_key or "(unknown)"
    k = re.sub(r"#r\d+$", "", k)
    k = re.sub(r":\d+$", "", k)
    k = re.sub(r"/\d+\.\d+$", "", k)
    return k


def normalise(s):
    """Aggressive normalisation for duplicate detection only."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\b\d+\b", "#", s)
    return " ".join(s.split())


def categorise(s):
    low = s.lower()
    for name, pat in CATEGORIES:
        if re.search(pat, low):
            return name
    return "Uncategorised"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--include-sessions", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--near-dup", type=float, default=0.82,
                    help="token-overlap threshold for near-duplicate merging")
    args = ap.parse_args()

    sources = DOC_SOURCES + (SESSION_SOURCES if args.include_sessions else ())
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    query = " OR ".join(f'"{m}"' for m in MARKERS)

    rows = conn.execute(
        "SELECT k.content, k.source, k.source_key "
        "FROM knowledge_messages_fts f "
        "JOIN knowledge_messages k ON k.rowid = f.rowid "
        "WHERE knowledge_messages_fts MATCH ? "
        f"AND k.source IN ({','.join('?' * len(sources))})",
        (query,) + sources,
    ).fetchall()

    # ── collect ──────────────────────────────────────────────────────
    raw = []
    for content, source, skey in rows:
        doc = doc_name(skey)
        if VENDOR_DOC.search(doc):
            continue
        for s in sentences(content or ""):
            if NOISE.search(s) or BOILERPLATE.search(s):
                continue
            if not any(re.search(r"\b" + re.escape(m) + r"\b", s, re.I)
                       for m in MARKERS):
                continue
            raw.append((s, source, doc))
    print(f"statements found            : {len(raw):,}")

    # ── exact duplicate removal ──────────────────────────────────────
    exact = {}
    for s, source, doc in raw:
        k = normalise(s)
        if not k:
            continue
        if k not in exact:
            exact[k] = [s, source, doc, 1]
        else:
            exact[k][3] += 1
    print(f"after exact de-duplication  : {len(exact):,}")

    # ── near-duplicate merge, within category, by token overlap ──────
    by_cat = defaultdict(list)
    for k, (s, source, doc, n) in exact.items():
        by_cat[categorise(s)].append((s, source, doc, n, set(k.split())))

    merged_total = 0
    final = defaultdict(list)
    for cat, items in by_cat.items():
        items.sort(key=lambda x: -len(x[4]))     # longest first: keep the fullest
        kept = []
        for s, source, doc, n, toks in items:
            dup_of = None
            for i, (ks, ksrc, kdoc, kn, ktoks) in enumerate(kept):
                inter = len(toks & ktoks)
                union = len(toks | ktoks) or 1
                if inter / union >= args.near_dup:
                    dup_of = i
                    break
            if dup_of is None:
                kept.append([s, source, doc, n, toks])
            else:
                kept[dup_of][3] += n
                merged_total += 1
        final[cat] = kept
    print(f"after near-duplicate merge  : "
          f"{sum(len(v) for v in final.values()):,} (merged {merged_total:,})")

    # ── write ────────────────────────────────────────────────────────
    out = ["# SECONDARY QUEUE — issues the record already acknowledges\n",
           "Generated by tools/mine_open_issues.py. Deterministic: verbatim",
           "sentences from the corpus, grouped by what they are ABOUT.",
           "Nothing is summarised, inferred, or dropped for being numerous.\n",
           "NOT every issue got a spec. Much of this is recognition in passing —",
           "someone noticing a problem while doing something else. Those are",
           "clues, and they are kept deliberately.\n",
           "An entry proves an issue was once WRITTEN DOWN. It does NOT prove the",
           "issue is still open — some are long fixed. Verify before acting.\n",
           "(xN) after a line means that recognition appears N times across the",
           "corpus. A high count means it was noticed repeatedly and, quite",
           "possibly, never dealt with.\n"]

    order = sorted(final.items(), key=lambda kv: -len(kv[1]))
    out.append("## Contents\n")
    for cat, items in order:
        out.append(f"- {cat} — {len(items)}")
    out.append("")

    for cat, items in order:
        out.append(f"\n## {cat}  ({len(items)})\n")
        items.sort(key=lambda x: (-x[3], x[0]))
        for s, source, doc, n, _ in items:
            tag = f" (x{n})" if n > 1 else ""
            short = doc if len(doc) <= 62 else "..." + doc[-59:]
            out.append(f"- {s}{tag}\n  `[{source}] {short}`")

    text = "\n".join(out)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text + "\n")
        print(f"\nwrote {args.out}")
        for cat, items in order:
            print(f"  {len(items):5}  {cat}")
    else:
        print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
