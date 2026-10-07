#!/usr/bin/env python3.12
"""ingest_files.py — incremental, idempotent ingest of the file-based KB families.

Deterministic. Nothing is summarised and no model runs: this copies document text
into the two stores the rest of the system already reads, and records a sha256 per
file so the coverage gate can tell "never ingested" from "ingested then edited".

Why this exists next to tools/catalog/convert_to_knowledge.py: that loader is a
one-shot bulk importer. It has no dedup, no change detection and no provenance, so
running it a second time duplicates every row it already wrote — which is why
docs/ sat at 56% coverage for six weeks with no safe way to top it up. This does
the same job for the same source names, incrementally, keyed the same way.

Writes to BOTH stores, because they are read by different things:
  - knowledge_messages (SQLite + FTS5) — what the pipeline's KB_CONTEXT queries
  - the "knowledge_messages" Chroma collection — what tools/ask_history.py queries
Secrets are dropped at index time by filter_for_index() and masked on every read
path by redact_secrets(), exactly as for every other source.

  python3.12 tools/kb/ingest_files.py --family repository_docs --dry-run
  python3.12 tools/kb/ingest_files.py --family repository_docs
  python3.12 tools/kb/ingest_files.py --all          # every measurable, required family
  python3.12 tools/kb/ingest_files.py --all --no-embed
"""
import argparse
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb import source_policy as sp  # noqa: E402

# The embedding model (all-MiniLM-L6-v2) truncates past ~256 tokens, about 1,000
# characters. Chunk to fit the model: a 4,000-char chunk is three-quarters
# invisible to semantic search. Same bound ingest_claude_code_sessions.py uses.
MAX_CHARS = 900
MIN_CHARS = 30


def chunk(text):
    """Split on paragraph boundaries, then sentences, never mid-word.

    Each chunk is retrieved on its own, so it has to stand on its own. Headings
    shorter than MIN_CHARS are folded forward into the next paragraph rather than
    stored alone — a bare "### Retrieval" is a label, not an answer, and
    ask_history already drops anything under 200 chars at read time.
    """
    import re
    out, buf = [], ""
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        pieces = [para]
        if len(para) > MAX_CHARS:
            pieces, cur = [], ""
            for sent in re.split(r"(?<=[.!?])\s+", para):
                if cur and len(cur) + len(sent) + 1 > MAX_CHARS:
                    pieces.append(cur)
                    cur = sent
                else:
                    cur = f"{cur} {sent}" if cur else sent
            if cur:
                pieces.append(cur)
        for piece in pieces:
            if buf and len(buf) + len(piece) + 2 > MAX_CHARS:
                out.append(buf)
                buf = piece
            else:
                buf = f"{buf}\n\n{piece}" if buf else piece
    if buf:
        out.append(buf)
    return [c for c in out if len(c) >= MIN_CHARS]


def key_for(fam, rel, idx):
    """The source_key, in the convention the family already uses.

    Changing a convention would orphan everything ingested under the old one, so
    these match what is on disk in the spine today: docs use 'relpath:N',
    cis_kernel uses 'root/relpath#rN'.
    """
    style = fam.get("key_style", "path_colon_index")
    if style == "path_hash_index":
        root = fam.get("root", "").rstrip("/")
        return f"{root}/{rel}#r{idx}"
    return f"{rel}:{idx}"


def plan(name, fam, conn, manifest, backfill_provenance=False):
    """What this family needs: files never ingested, plus files whose bytes moved.

    A file ingested before the manifest existed has no recorded hash, so there is
    no honest way to say whether the KB copy still matches disk — and for sixteen
    docs/ files it demonstrably did not. backfill_provenance treats those as
    changed: re-read from disk, supersede the old chunks, record the hash. The
    file on disk is the source, so nothing is lost that cannot be re-derived.
    """
    root = sp.family_root(fam)
    eligible = sp.discover(fam)
    have = sp.ingested_identities(conn, fam)
    fmani = (manifest.get("families", {}).get(name) or {}).get("files", {})

    new, changed = [], []
    for rel in eligible:
        if sp.path_identity(fam, rel) not in have:
            new.append(rel)
            continue
        entry = fmani.get(rel)
        if not entry:
            if backfill_provenance:
                changed.append(rel)
            continue
        if entry.get("sha256") != sp.sha256_file(os.path.join(root, rel)):
            changed.append(rel)
    return root, new, changed


def ingest(name, fam, conn, manifest, embed=True, dry_run=False, limit=None,
           backfill_provenance=False, manifest_path=None):
    source = fam["kb_source"]
    root, new, changed = plan(name, fam, conn, manifest, backfill_provenance)
    todo = new + changed
    if limit:
        todo = todo[:limit]
    print(f"[{name}] {len(new)} never ingested, {len(changed)} changed since ingest")
    if not todo:
        return 0

    # A changed file's old rows are replaced, not stacked on top of. Supersession
    # by deletion is the only honest option here: two versions of the same
    # source_key in one corpus is the "stale conversation outranks current truth"
    # failure with a document wearing the costume.
    rows, receipts, superseded = [], {}, 0
    for rel in todo:
        path = os.path.join(root, rel)
        try:
            with open(path, errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"  SKIP {rel}: {exc}")
            continue
        chunks = chunk(text)
        if not chunks:
            continue
        for i, body in enumerate(chunks):
            rows.append((body, source, "document", key_for(fam, rel, i)))
        receipts[rel] = {
            "sha256": sp.sha256_file(path),
            "bytes": os.path.getsize(path),
            "chunks": len(chunks),
            "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    print(f"  {len(rows)} chunk(s), {sum(len(r[0]) for r in rows):,} chars")
    if dry_run:
        print("  --dry-run: nothing written. First chunk:")
        print("  " + (rows[0][0][:400].replace("\n", "\n  ") if rows else "(none)"))
        return 0

    # Identity comparison in Python, not SQL LIKE: a relative path may contain
    # '_' or '%', both of which are LIKE wildcards, and over-matching here would
    # delete a neighbouring document's chunks.
    old_ids = []
    replacing = {rel for rel in changed if rel in receipts}
    if replacing:
        style = fam.get("key_style", "path_colon_index")
        for row_id, key in conn.execute(
                "SELECT id, source_key FROM knowledge_messages "
                "WHERE source = ? AND source_key IS NOT NULL", (source,)):
            if sp.identity_of(key, style, fam) in replacing:
                old_ids.append(row_id)
    if old_ids:
        conn.executemany("DELETE FROM knowledge_messages WHERE id = ?",
                         [(i,) for i in old_ids])
        superseded = len(old_ids)
        print(f"  superseded {superseded} stale chunk(s) from changed files")

    row_ids = []
    for r in rows:
        # Chroma ids MUST be km_<rowid> — that is how the two stores are
        # reconciled and what tools/sync_missing_embeddings.py keys on.
        cur = conn.execute(
            "INSERT INTO knowledge_messages (content, source, role, source_key) "
            "VALUES (?, ?, ?, ?)", r)
        row_ids.append(cur.lastrowid)
    conn.commit()
    print(f"  knowledge_messages: +{len(rows)}")

    manifest.setdefault("families", {}).setdefault(name, {}).setdefault("files", {})
    manifest["families"][name]["files"].update(receipts)
    manifest["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    # Explicit path, never the module default: a test that wrote the production
    # manifest once already replaced three families' receipts with one temp file.
    sp.save_manifest(manifest, manifest_path)

    if not embed:
        print("  --no-embed: skipped Chroma. ask_history will NOT find these yet.")
        return len(rows)

    sys.path.insert(0, os.path.join(sp.REPO, "runtime"))
    from mcp_bridge.chroma_index import ChromaClient, filter_for_index
    from mcp_bridge.chroma_lock import chroma_write

    client = ChromaClient()
    with chroma_write(what=f"kb_ingest_files:{name}"):
        coll = client._client.get_collection("knowledge_messages")
        if old_ids:
            coll.delete(ids=[f"km_{i}" for i in old_ids])
        done = 0
        for i in range(0, len(rows), 1000):          # Chroma rejects >5,461 per add
            batch, ids = rows[i:i + 1000], row_ids[i:i + 1000]
            _ids, texts, _metas, _dropped = filter_for_index(
                [f"km_{r}" for r in ids], [b[0] for b in batch],
                [{"source": source, "role": b[2], "source_key": b[3]} for b in batch])
            if _ids:
                coll.add(ids=_ids, documents=texts,
                         embeddings=client._embedding.embed(texts), metadatas=_metas)
            done += len(batch)
            print(f"  embedded {done}/{len(rows)}")
    print(f"[{name}] done")
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", action="append", default=[])
    ap.add_argument("--all", action="store_true",
                    help="every required family that has a filesystem root")
    ap.add_argument("--db", default=None)
    ap.add_argument("--policy", default=None)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-embed", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--backfill-provenance", action="store_true",
                    help="re-ingest files that carry no recorded hash, superseding "
                         "their existing chunks, so provenance becomes real "
                         "rather than assumed")
    args = ap.parse_args()

    policy = sp.load_policy(args.policy)
    manifest_path = args.manifest or sp.MANIFEST_PATH
    manifest = sp.load_manifest(manifest_path)

    names = args.family
    if args.all:
        names = [n for n, f in policy["families"].items()
                 if (f or {}).get("required") and (f or {}).get("measurable", True)
                 and (f or {}).get("root") and (f or {}).get("kb_source")
                 and not (f or {}).get("ingest")]   # families with their own tool
    if not names:
        ap.error("pass --family NAME or --all")

    conn = sqlite3.connect(args.db or sp.DB_PATH)
    total = 0
    for name in names:
        fam = policy["families"].get(name)
        if not fam:
            print(f"[{name}] no such family in policy", file=sys.stderr)
            return 2
        if not fam.get("kb_source") or not fam.get("root"):
            print(f"[{name}] no filesystem root or kb_source — nothing to do")
            continue
        total += ingest(name, fam, conn, manifest,
                        embed=not args.no_embed, dry_run=args.dry_run,
                        limit=args.limit,
                        backfill_provenance=args.backfill_provenance,
                        manifest_path=manifest_path)
    conn.close()
    print(f"\ntotal {total} chunk(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
