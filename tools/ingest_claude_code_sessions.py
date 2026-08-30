#!/usr/bin/env python3.12
"""ingest_claude_code_sessions.py — put Claude Code session reasoning in the KB.

Deterministic. No model runs here and nothing is summarised: this copies the
actual exchange out of the transcripts Claude Code already writes to disk, so
there is no generated prose to distrust.

Why exchanges and not messages
------------------------------
The reasoning in a session lives in the PAIR — an objection and the revision it
caused. tools/mine_asks_claude_code.py keeps Eric's asks and drops everything a
model wrote, which preserves the challenge but loses what it changed. The April
extraction contract distilled sessions into prose, which preserves the outcome
but asks the reader to trust a model's account of how it was reached. Neither
keeps the link. This keeps both halves, verbatim, adjacent.

Writes to BOTH stores, because they are read by different things:
  - knowledge_messages (SQLite + FTS5) — what the pipeline's KB_CONTEXT queries
  - the "knowledge_messages" Chroma collection — what tools/ask_history.py queries
Writing only one leaves the material invisible to half the system.

Usage:
  python3.12 tools/ingest_claude_code_sessions.py            # ingest, both stores
  python3.12 tools/ingest_claude_code_sessions.py --dry-run  # report, write nothing
  python3.12 tools/ingest_claude_code_sessions.py --no-embed # SQLite only (fast)
"""
import argparse
import glob
import json
import os
import re
import sqlite3
import sys

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
DEFAULT_GLOB = os.path.expanduser("~/.claude/projects/*/*.jsonl")
SOURCE = "claude_code"
# The embedding model (all-MiniLM-L6-v2) has max_seq_length 256 tokens — about
# 1,000 characters. Anything past that is silently TRUNCATED at embed time, so a
# 4,000-char chunk is three-quarters invisible to search. Chunk to fit the model,
# not to a round number. (The rest of the KB does not: ingest_sessions.py uses
# 4,000 and the archive averages 9,710, so most of the corpus is embedded only by
# its opening line. See NEXT_SESSION.md.)
MAX_CHARS = 900
ASK_REPEAT = 220     # how much of the operator's turn to repeat on continuations
MIN_TEXT = 30

# Harness-injected wrappers. Not the operator, not the assistant reasoning.
HARNESS = re.compile(
    r"<system-reminder>|<command-name>|<command-message>|<command-args>|"
    r"<local-command-stdout>|<local-command-caveat>|^\[Request interrupted",
    re.M,
)


def clean(text):
    """Drop harness blocks and collapse runaway whitespace."""
    text = re.sub(r"<system-reminder>.*?</system-reminder>", " ", text, flags=re.S)
    text = re.sub(r"<local-command-stdout>.*?</local-command-stdout>", " ", text, flags=re.S)
    text = re.sub(r"<command-[a-z]+>.*?</command-[a-z]+>", " ", text, flags=re.S)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def blocks_to_text(content):
    """Turn a message's content into plain text, keeping only real prose.

    tool_use and tool_result blocks are machine chatter — the command and its
    output are already in the repo and the spine. What is NOT recorded anywhere
    else is what was said around them.
    """
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(p for p in parts if p)


def read_exchanges(path):
    """Yield (index, text) exchanges — each an operator turn plus the reply."""
    turns = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") not in ("user", "assistant"):
                continue
            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue
            text = clean(blocks_to_text(msg.get("content")))
            if not text or len(text) < MIN_TEXT:
                continue
            if HARNESS.search(text):
                continue
            turns.append((rec["type"], text))

    # Group into exchanges: one or more user turns followed by the replies.
    current, idx = [], 0
    for role, text in turns:
        if role == "user" and current and current[-1][0] == "assistant":
            yield idx, current
            idx += 1
            current = []
        current.append((role, text))
    if current:
        yield idx, current


def render(exchange):
    return "\n\n".join(f"[{role}] {text}" for role, text in exchange)


def split_long(exchange):
    """Chunk an oversized exchange, repeating the ASK at the top of each part.

    A long exchange is mostly assistant text. Split naively and every part after
    the first is an answer with no question attached — which is the failure this
    script exists to avoid, reintroduced by the chunker. So each continuation
    carries the operator turn that prompted it.
    """
    ask = next((t for role, t in exchange if role == "user"), "")
    text = render(exchange)
    if len(text) <= MAX_CHARS:
        return [text]

    short_ask = ask[:ASK_REPEAT] + ("..." if len(ask) > ASK_REPEAT else "")
    header = f"[asked] {short_ask}\n\n" if ask else ""
    budget = max(MAX_CHARS - len(header), 300)

    chunks, buf = [], ""
    for para in text.split("\n\n"):
        # Paragraphs can themselves exceed the budget; split those on sentences.
        pieces = [para]
        if len(para) > budget:
            pieces, cur = [], ""
            for sent in re.split(r"(?<=[.!?])\s+", para):
                if cur and len(cur) + len(sent) + 1 > budget:
                    pieces.append(cur)
                    cur = sent
                else:
                    cur = f"{cur} {sent}" if cur else sent
            if cur:
                pieces.append(cur)
        for piece in pieces:
            if buf and len(buf) + len(piece) + 2 > budget:
                chunks.append(buf)
                buf = piece
            else:
                buf = f"{buf}\n\n{piece}" if buf else piece
    if buf:
        chunks.append(buf)
    return [chunks[0]] + [header + c for c in chunks[1:]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", default=DEFAULT_GLOB)
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-embed", action="store_true",
                    help="skip Chroma; ask_history will not see the new rows")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.expanduser(args.sessions)))
    if not files:
        print(f"no transcripts matched {args.sessions}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    existing = {
        r[0] for r in conn.execute(
            "SELECT source_key FROM knowledge_messages WHERE source = ?", (SOURCE,)
        )
    }
    print(f"already ingested: {len(existing)} chunks")

    rows = []
    for path in files:
        project = os.path.basename(os.path.dirname(path))
        session = os.path.basename(path)[:-6]
        kept = 0
        for idx, exchange in read_exchanges(path):
            for part, chunk in enumerate(split_long(exchange)):
                key = f"{SOURCE}/{project}/{session}/{idx}.{part}"
                if key in existing:
                    continue
                rows.append((chunk, SOURCE, "exchange", key))
                kept += 1
        print(f"  {project}/{session[:8]}: {kept} new chunk(s)")

    if not rows:
        print("nothing new to ingest")
        return 0

    print(f"\n{len(rows)} new chunk(s), "
          f"{sum(len(r[0]) for r in rows):,} chars")

    if args.dry_run:
        print("\n--dry-run: nothing written. Sample:")
        print("-" * 60)
        print(rows[0][0][:600])
        return 0

    # Insert one at a time to capture rowids. Chroma ids MUST be km_<rowid> —
    # that is the convention every other source uses, and the id is how the two
    # stores are reconciled. This tool originally used source_key as the id,
    # which made its rows invisible to tools/sync_missing_embeddings.py and got
    # all 645 duplicated when that backfill ran (2026-08-29).
    row_ids = []
    for r in rows:
        cur = conn.execute(
            "INSERT INTO knowledge_messages (content, source, role, source_key) "
            "VALUES (?, ?, ?, ?)", r,
        )
        row_ids.append(cur.lastrowid)
    conn.commit()
    print(f"knowledge_messages: +{len(rows)}")

    print("rebuilding FTS5 index...")
    conn.execute("INSERT INTO knowledge_messages_fts(knowledge_messages_fts) "
                 "VALUES('rebuild')")
    conn.commit()

    if args.no_embed:
        print("\n--no-embed: skipped Chroma. ask_history will NOT find these yet.")
        conn.close()
        return 0

    # Chroma — the store ask_history actually queries.
    sys.path.insert(0, "/mnt/projects/cis/runtime")
    from mcp_bridge.chroma_index import ChromaClient, filter_for_index
    from mcp_bridge.chroma_lock import chroma_write

    print("embedding into Chroma (local model, no network)...")
    client = ChromaClient()
    added = 0
    # Exclusive for the whole embed phase. (UNIFIED BUILD LIST 0.3)
    with chroma_write(what="ingest_claude_code_sessions"):
        coll = client._client.get_collection("knowledge_messages")
        # Chroma rejects a single add() over 5,461 records; stay well under.
        for i in range(0, len(rows), 1000):
            batch = rows[i:i + 1000]
            ids = row_ids[i:i + 1000]
            texts = [r[0] for r in batch]
            # Secrets never enter the store. (UNIFIED BUILD LIST 0.2)
            _ids, texts, _metas, _dropped = filter_for_index(
                [f"km_{rid}" for rid in ids], texts,
                [{"source": SOURCE, "role": r[2], "source_key": r[3]} for r in batch])
            # Batched encode — 7x faster than embed_single per text (see
            # tools/rechunk_for_embedding.py for the measurement).
            if _ids:
                coll.add(
                    ids=_ids,
                    documents=texts,
                    embeddings=client._embedding.embed(texts),
                    metadatas=_metas,
                )
            added += len(batch)
            print(f"  {added}/{len(rows)}")

    print(f"\nDone. {added} chunk(s) now searchable by ask_history.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
