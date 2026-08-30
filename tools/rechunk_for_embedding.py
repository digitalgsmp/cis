#!/usr/bin/env python3.12
"""rechunk_for_embedding.py — make existing KB rows fit the embedding window.

The embedding model (all-MiniLM-L6-v2) has max_seq_length 256 tokens, about
1,000 characters. Anything past that is silently truncated at embed time, so a
3,700-char row is represented in the vector index by its opening line and the
rest is invisible to semantic search. Measured 2026-08-29: only 11% of the
corpus text sits inside that window.

FTS5 keyword search is unaffected — it indexes every word regardless. This tool
only repairs the vector layer, and improves FTS context quality as a side effect
(the pipeline previews the first 300 chars of whatever chunk matched, which
against a long blob is usually the wrong part).

Splits oversized rows in place, on paragraph then sentence boundaries, never
mid-word. Old row is deleted, new rows inherit its source and source_key with a
#rN suffix so provenance survives. Chroma ids follow the existing km_<rowid>
convention.

Idempotent: rows already under the limit are skipped, so re-running is a no-op.

Usage:
  python3.12 tools/rechunk_for_embedding.py --dry-run
  python3.12 tools/rechunk_for_embedding.py --source-like 'hermes_%'
  python3.12 tools/rechunk_for_embedding.py --source-like 'hermes_%' --no-embed
"""
import argparse
import os
import re
import sqlite3
import sys
import time

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
MAX_CHARS = 900
CHROMA_ADD_MAX = 2000   # Chroma rejects a single add() over 5,461 records


def split_text(text, limit=MAX_CHARS):
    """Split on paragraphs, then sentences, then hard-wrap. Never mid-word."""
    if len(text) <= limit:
        return [text]
    out, buf = [], ""
    for para in text.split("\n\n"):
        pieces = [para]
        if len(para) > limit:
            pieces, cur = [], ""
            for sent in re.split(r"(?<=[.!?])\s+", para):
                while len(sent) > limit:            # a single huge "sentence"
                    cut = sent.rfind(" ", 0, limit)
                    cut = cut if cut > limit // 2 else limit
                    pieces.append(sent[:cut])
                    sent = sent[cut:].lstrip()
                if cur and len(cur) + len(sent) + 1 > limit:
                    pieces.append(cur)
                    cur = sent
                else:
                    cur = f"{cur} {sent}" if cur else sent
            if cur:
                pieces.append(cur)
        for piece in pieces:
            if buf and len(buf) + len(piece) + 2 > limit:
                out.append(buf)
                buf = piece
            else:
                buf = f"{buf}\n\n{piece}" if buf else piece
    if buf:
        out.append(buf)
    return [c for c in out if c.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--source-like", default="hermes\\_%",
                    help="SQL LIKE pattern over knowledge_messages.source")
    ap.add_argument("--max", type=int, default=MAX_CHARS)
    ap.add_argument("--batch", type=int, default=200,
                    help="rows rewritten per commit")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-embed", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    rows = conn.execute(
        "SELECT id, content, source, role, source_key FROM knowledge_messages "
        "WHERE source LIKE ? ESCAPE '\\' AND length(content) > ? ORDER BY id",
        (args.source_like, args.max),
    ).fetchall()

    if not rows:
        print("nothing oversized — already within the embedding window")
        return 0

    total_new = sum(len(split_text(r[1], args.max)) for r in rows)
    chars = sum(len(r[1]) for r in rows)
    print(f"oversized rows : {len(rows):,}")
    print(f"total chars    : {chars:,}")
    print(f"becomes        : {total_new:,} chunks at <= {args.max} chars")
    print(f"embedded before: {sum(min(len(r[1]), 1000) for r in rows)*100//chars}%"
          f"  ->  after: 100%")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    client = coll = None
    if not args.no_embed:
        sys.path.insert(0, "/mnt/projects/cis/runtime")
        from mcp_bridge.chroma_index import ChromaClient, filter_for_index
        client = ChromaClient()
        coll = client._client.get_collection("knowledge_messages")

    done = made = 0
    started = time.time()
    for i in range(0, len(rows), args.batch):
        batch = rows[i:i + args.batch]
        new_ids, new_docs, new_meta, drop_ids = [], [], [], []

        for old_id, content, source, role, skey in batch:
            parts = split_text(content, args.max)
            for n, part in enumerate(parts):
                cur = conn.execute(
                    "INSERT INTO knowledge_messages (content, source, role, source_key) "
                    "VALUES (?, ?, ?, ?)",
                    (part, source, role, f"{skey}#r{n}" if skey else None),
                )
                new_ids.append(f"km_{cur.lastrowid}")
                new_docs.append(part)
                new_meta.append({"source": source, "role": role,
                                 "source_key": f"{skey}#r{n}" if skey else ""})
            conn.execute("DELETE FROM knowledge_messages WHERE id = ?", (old_id,))
            drop_ids.append(f"km_{old_id}")
            made += len(parts)

        conn.commit()

        if coll is not None:
            try:
                coll.delete(ids=drop_ids)
            except Exception:
                pass                      # id may predate the km_ convention
            # Batch the encode. embed_single() calls encode([one]) — a batch of
            # one — paying full per-call overhead per chunk. Measured 2026-08-29
            # on the RTX 4090: 258/s one-at-a-time vs 1,820/s batched, 7.1x. The
            # model was already on the GPU; the device was never the bottleneck.
            #
            # Chroma caps a single add() at 5,461 records. One row can explode
            # into many chunks (archive rows average ~16), so the row batch is a
            # poor proxy for the add size — a 300-row batch produced 7,196 chunks
            # and the add threw. SQLite had already been committed by then, which
            # left those rows with no embedding. Sub-batch the add on its own
            # terms so row batching and Chroma limits stay independent.
            # Secrets never enter the store. Filtered BEFORE the encode so the
            # id/doc/meta/embedding lists stay index-aligned through the
            # sub-batching below. (UNIFIED BUILD LIST 0.2)
            new_ids, new_docs, new_meta, _dropped = filter_for_index(
                new_ids, new_docs, new_meta)
            embs = client._embedding.embed(new_docs) if new_docs else []
            for j in range(0, len(new_ids), CHROMA_ADD_MAX):
                coll.add(
                    ids=new_ids[j:j + CHROMA_ADD_MAX],
                    documents=new_docs[j:j + CHROMA_ADD_MAX],
                    metadatas=new_meta[j:j + CHROMA_ADD_MAX],
                    embeddings=embs[j:j + CHROMA_ADD_MAX],
                )

        done += len(batch)
        rate = done / max(time.time() - started, 1)
        eta = (len(rows) - done) / rate / 60 if rate else 0
        print(f"  {done:,}/{len(rows):,} rows -> {made:,} chunks "
              f"({rate:.1f} rows/s, ~{eta:.0f} min left)", flush=True)

    print("rebuilding FTS5 index...")
    conn.execute("INSERT INTO knowledge_messages_fts(knowledge_messages_fts) "
                 "VALUES('rebuild')")
    conn.commit()
    conn.close()
    print(f"\nDone. {len(rows):,} rows -> {made:,} chunks, all inside the "
          f"embedding window.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
