#!/usr/bin/env python3.12
"""ingest_hermes_sessions_v2.py — re-ingest Hermes agent sessions as exchanges.

Supersedes tools/catalog/ingest_sessions.py, which glued each whole session into
one blob and cut it every 4,000 characters wherever that landed. Measured
2026-08-29: only 14-28% of the resulting chunks carried the question they were
answering, and the 4,000-char size meant the embedding model (max ~1,000 chars)
saw about a quarter of each one.

This keeps the PAIR — an operator turn and the reply it drew — and repeats the
ask at the head of every continuation chunk, so no chunk is an orphaned answer.
Same logic as tools/ingest_claude_code_sessions.py; the two ingests now agree.

Also drops the 30-day window the old script used. The session files on disk go
back to 2026-05-30 and there is no reason to ingest only the recent ones.

Deterministic: no model, nothing summarised.

Safety: new rows are written FIRST and counted. Old rows are removed only with
--replace, and only after the new ingest has at least as many source sessions as
the old rows represent — so a thinned sessions directory cannot silently delete
history that is no longer on disk.

Usage:
  python3.12 tools/ingest_hermes_sessions_v2.py --dry-run
  python3.12 tools/ingest_hermes_sessions_v2.py --replace
"""
import argparse
import glob
import json
import os
import re
import sys

# Turns that are harness plumbing, not somebody asking for something. These are
# only ~1-2% of chunks but they dominated retrieval when first ingested: a
# compaction summary is dense with project vocabulary, so it matches almost any
# query, and repeating one as the "[asked]" header put it at the top of every
# continuation chunk in that session. Excluded entirely — the real turns around
# them are kept.
NOISE_TURN = re.compile(
    r"CONTEXT COMPACTION|treat it as background reference|"
    r"\[System note:|previous turn was interrupted|"
    r"^\s*\[?HANDOFF|REFERENCE ONLY\]",
    re.I,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ingest_claude_code_sessions import split_long, MIN_TEXT  # noqa: E402

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")

PROFILES = {
    "prime": "~/.hermes/sessions",
    "v4pro": "~/.hermes-v4pro/sessions",
    "v4impl": "~/.hermes-v4impl/sessions",
    "r1": "~/.hermes-r1/sessions",
    "glm-reviewer": "~/.hermes-glm-reviewer/sessions",
    "glm-verifier": "~/.hermes-glm-verifier/sessions",
    "brainstorm": "~/.hermes-brainstorm/sessions",
    "qwen": "~/.hermes-qwen/sessions",
}


def exchanges(path):
    """Yield exchanges — an operator turn plus the replies that followed it."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
    except Exception:
        return

    turns = []
    for m in data.get("messages", []):
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue
        content = m.get("content")
        if isinstance(content, list):
            content = " ".join(str(p) for p in content if isinstance(p, str))
        elif not isinstance(content, str):
            content = str(content or "")
        content = content.strip()
        if len(content) < MIN_TEXT:
            continue
        if NOISE_TURN.search(content[:400]):
            continue
        turns.append((role, content))

    current, idx = [], 0
    for role, text in turns:
        if role == "user" and current and current[-1][0] == "assistant":
            yield idx, current
            idx += 1
            current = []
        current.append((role, text))
    if current:
        yield idx, current


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--replace", action="store_true",
                    help="delete the old blind-chunked rows after ingesting")
    ap.add_argument("--no-embed", action="store_true")
    args = ap.parse_args()

    import sqlite3
    conn = sqlite3.connect(args.db)

    plan = {}
    for profile, d in PROFILES.items():
        files = sorted(glob.glob(os.path.join(os.path.expanduser(d),
                                              "session_*.json")))
        if not files:
            continue
        rows = []
        for path in files:
            stem = os.path.basename(path)[:-5]
            for idx, ex in exchanges(path):
                for part, chunk in enumerate(split_long(ex)):
                    rows.append((
                        chunk, f"hermes_{profile}", "exchange",
                        f"hermes_session/{profile}/{stem}/{idx}.{part}",
                    ))
        if rows:
            plan[profile] = (len(files), rows)

    print(f"{'profile':16} {'files':>6} {'new chunks':>11} {'old rows':>9}")
    total_new = 0
    for profile, (nfiles, rows) in sorted(plan.items()):
        old = conn.execute(
            "SELECT count(*) FROM knowledge_messages WHERE source = ?",
            (f"hermes_{profile}",),
        ).fetchone()[0]
        print(f"{profile:16} {nfiles:6} {len(rows):11,} {old:9,}")
        total_new += len(rows)
    print(f"\ntotal new chunks: {total_new:,}")

    if args.dry_run:
        sample = next(iter(plan.values()))[1]
        print("\n--dry-run: nothing written. Sample chunk:")
        print("-" * 60)
        print(sample[0][0][:500])
        return 0

    if not args.no_embed:
        sys.path.insert(0, "/mnt/projects/cis/runtime")
        from mcp_bridge.chroma_index import ChromaClient, filter_for_index
        client = ChromaClient()
        coll = client._client.get_collection("knowledge_messages")
    else:
        client = coll = None

    for profile, (nfiles, rows) in sorted(plan.items()):
        source = f"hermes_{profile}"
        old_ids = [r[0] for r in conn.execute(
            "SELECT id FROM knowledge_messages WHERE source = ?", (source,))]

        new_ids, docs, metas = [], [], []
        for content, src, role, skey in rows:
            cur = conn.execute(
                "INSERT INTO knowledge_messages (content, source, role, source_key) "
                "VALUES (?, ?, ?, ?)", (content, src, role, skey))
            new_ids.append(f"km_{cur.lastrowid}")
            docs.append(content)
            metas.append({"source": src, "role": role, "source_key": skey})
        conn.commit()

        if coll is not None:
            for i in range(0, len(new_ids), 200):
                # Secrets never enter the store. (UNIFIED BUILD LIST 0.2)
                _i, _d, _m, _dropped = filter_for_index(
                    new_ids[i:i + 200], docs[i:i + 200], metas[i:i + 200])
                if not _i:
                    continue
                # Batched encode — 7x faster than per-text embed_single.
                coll.add(ids=_i, documents=_d, metadatas=_m,
                         embeddings=client._embedding.embed(_d))

        removed = 0
        if args.replace and old_ids:
            conn.executemany("DELETE FROM knowledge_messages WHERE id = ?",
                             [(i,) for i in old_ids])
            conn.commit()
            removed = len(old_ids)
            if coll is not None:
                stale = [f"km_{i}" for i in old_ids]
                for i in range(0, len(stale), 200):
                    try:
                        coll.delete(ids=stale[i:i + 200])
                    except Exception:
                        pass
        print(f"  {source:22} +{len(rows):,} new, -{removed:,} old", flush=True)

    print("rebuilding FTS5 index...")
    conn.execute("INSERT INTO knowledge_messages_fts(knowledge_messages_fts) "
                 "VALUES('rebuild')")
    conn.commit()
    conn.close()
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
