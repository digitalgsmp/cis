"""
chroma_index.py — Chroma/VDB embedding pipeline and query functions.

Tier 9 Chroma/VDB per docs/CIS_TIER_9_CHROMA_VDB_SPECIFICATION.md.

Three layers:
  1. SecretFilterPipeline — pre-indexing regex-based secret detection/redaction
  2. EmbeddingPipeline — local sentence-transformers model, batch embedding
  3. ChromaClient — collection management, index-from-spine, query functions

All embedding is local (no network calls). Chroma runs embedded (no server).
The spine is read-only (queries via runtime/mcp_bridge/spine.py).
"""
import logging
import os
import re
import sqlite3

logger = logging.getLogger(__name__)


# ── 1. SecretFilterPipeline (§2.4) ────────────────────────────────

# Patterns from the approved spec §2.4
SECRET_PATTERNS = [
    # (regex, action, label)
    # Exclude entire row
    (re.compile(r'-----BEGIN\s.*PRIVATE\sKEY-----'), "exclude", "private_key"),
    (re.compile(r'Bearer\s+[A-Za-z0-9\-_\.]{20,}'), "exclude", "bearer_token"),
    # Specific token patterns (check before generic)
    (re.compile(r'eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+'), "redact", "jwt_token"),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), "redact", "api_key"),
    (re.compile(r'AKIA[0-9A-Z]{16}'), "redact", "aws_key"),
    (re.compile(r'gh[pousr]_[A-Za-z0-9]{36,}'), "redact", "github_token"),
    # Generic patterns (check last — may be too broad)
    (re.compile(
        r'(API_KEY|TOKEN|SECRET|PASSWORD)\s*[=:]\s*\S+',
        re.IGNORECASE,
    ), "replace", "generic_secret"),
]


# A PEM header is only the first LINE of the secret; the key itself is the body
# below it. Index-time filtering drops the whole row so that never mattered, but
# a read-time span replacement on the header alone leaves the key material in
# place — caught by testing the redaction on 2026-08-30 rather than trusting it.
# Matches to the END marker where there is one, otherwise across the base64 body.
# The no-END branch consumes whole LINES made only of base64 characters. A first
# attempt required 16+ chars per line and leaked the tail of a key whose last
# line was 12 — chunking splits keys mid-block, so the truncated case is the
# common one, not the exotic one. Requiring the line to END after the base64 run
# is what keeps prose out: a sentence contains spaces and cannot match.
_PEM_BLOCK = re.compile(
    r'-----BEGIN[^-\n]*-----'
    r'(?:.*?-----END[^-\n]*-----'
    r'|(?:[ \t]*\r?\n[A-Za-z0-9+/=]+(?=\r?\n|$))+)',
    re.DOTALL,
)


class SecretFilterPipeline:
    """Pre-indexing secret detection and redaction."""

    def __init__(self, patterns=None):
        self.patterns = patterns or SECRET_PATTERNS
        self.stats = {"excluded": 0, "redacted": 0, "replaced": 0, "clean": 0}
        self.display_stats = {"redacted": 0}

    def filter_text(self, text):
        """
        Apply secret filtering to a single text string.

        Returns (filtered_text, action_taken) where action_taken is one of:
          "excluded" — entire row should be skipped
          "redacted" — values replaced with [REDACTED], text still embeddable
          "replaced" — generic secrets replaced, text still embeddable
          "clean" — no secrets detected
        """
        if not text:
            self.stats["clean"] += 1
            return text, "clean"

        action = "clean"

        for pattern, pat_action, label in self.patterns:
            match = pattern.search(text)
            if not match:
                continue

            if pat_action == "exclude":
                self.stats["excluded"] += 1
                return None, "excluded"
            elif pat_action == "redact":
                text = pattern.sub("[REDACTED]", text)
                self.stats["redacted"] += 1
                action = "redacted"
            elif pat_action == "replace":
                text = pattern.sub(r"\1=[REDACTED]", text)
                self.stats["replaced"] += 1
                if action != "redacted":
                    action = "replaced"

        if action == "redacted" or action == "replaced":
            return text, action

        self.stats["clean"] += 1
        return text, "clean"

    def redact_for_display(self, text):
        """Mask secrets in text that is about to be SHOWN, never stored.

        filter_text() is the index-time filter: its "exclude" patterns drop the
        whole row so a secret never enters the store. That is right for a write
        and wrong for a read. At query time the row is already stored — refusing
        to display it protects nothing that masking would not, and it costs the
        reader the surrounding material.

        Measured 2026-08-30: 112 rows in the KB carry a PRIVATE KEY header and
        111 of them are agents DISCUSSING key handling, with no key body. Under
        the exclude rule those 112 vanish from every search result, so asking
        the pipeline how to handle secrets safely would return nothing.

        So: every pattern redacts here, none excludes. Always returns a string.
        Stats are kept separately so index-time counters stay meaningful.
        """
        if not text:
            return text
        # Whole-block secrets first: a span replacement on the header alone
        # would leave the key body sitting in the text underneath it.
        if _PEM_BLOCK.search(text):
            text = _PEM_BLOCK.sub("[REDACTED KEY BLOCK]", text)
            self.display_stats["redacted"] += 1
        for pattern, _action, _label in self.patterns:
            if pattern.search(text):
                # \1 is the key name in the generic KEY=VALUE pattern; the other
                # patterns have no groups, so a plain marker is used for them.
                repl = r"\1=[REDACTED]" if pattern.groups else "[REDACTED]"
                text = pattern.sub(repl, text)
                self.display_stats["redacted"] += 1
        return text

    def filter_batch(self, texts):
        """
        Filter a batch of text strings. Returns list of (index, filtered_text,
        action) tuples. Index is from the original batch.
        """
        results = []
        for i, text in enumerate(texts):
            filtered, action = self.filter_text(text)
            results.append((i, filtered, action))
        return results

    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {"excluded": 0, "redacted": 0, "replaced": 0, "clean": 0}


# Shared instance for read paths. Deliberately at module level and dependency-
# free: everything above this line uses only the standard library, and chromadb
# is imported lazily inside ChromaClient, so a caller with no chromadb (the
# container, until the image ships it) can still import and use this.
_DISPLAY_FILTER = SecretFilterPipeline()


def filter_for_index(ids, documents, metadatas=None):
    """Apply the index-time filter to a batch about to be embedded and stored.

    The write-side counterpart to redact_secrets(). Excluded rows are DROPPED
    here rather than masked — at index time the choice is whether to store the
    material at all, and a private key has no business in the store in any form.
    Redact/replace rows are kept with the secret masked.

    Every ingest tool must call this before coll.add(). index_from_spine() has
    filtered since Tier 9, but the tools that wrote the corpus never went
    through it: rebuild_vector_index, ingest_claude_code_sessions,
    ingest_hermes_sessions_v2, rechunk_for_embedding and sync_missing_embeddings
    all embed directly, and the 451,167 chunks indexed on 2026-08-29 went in
    unfiltered. (UNIFIED BUILD LIST 0.2)

    Returns (ids, documents, metadatas, dropped_count) with the three lists
    still index-aligned, so embeddings computed from the returned documents
    still line up.
    """
    keep_ids, keep_docs, keep_metas = [], [], []
    dropped = 0
    for i, doc in enumerate(documents):
        filtered, action = _DISPLAY_FILTER.filter_text(doc)
        if action == "excluded":
            dropped += 1
            continue
        keep_ids.append(ids[i])
        keep_docs.append(filtered)
        if metadatas is not None:
            keep_metas.append(metadatas[i])
    return keep_ids, keep_docs, (keep_metas if metadatas is not None else None), dropped


def redact_secrets(text):
    """Mask secret-shaped strings in text about to be shown to an agent or Eric.

    The one call every read path uses. Until 2026-08-30 the filter existed but
    ran only at index time, so nothing stood between a stored secret and an
    agent prompt: 11 of 100 live keyword results carried secret-shaped strings
    and the two gates written to catch it had never fired.
    """
    return _DISPLAY_FILTER.redact_for_display(text)


# ── 2. EmbeddingPipeline ──────────────────────────────────────────

class EmbeddingPipeline:
    """Local sentence-transformers embedding model."""

    def __init__(self, model_name=None):
        from sentence_transformers import SentenceTransformer
        # CIS_EMBED_MODEL lets the container name the model by ABSOLUTE PATH
        # instead of by repo id. Resolving a repo id means going through the
        # HuggingFace cache lookup, which failed inside the container even with
        # the cache mounted, HF_HOME set and the files provably readable —
        # sentence-transformers passes its own cache_dir and the layers disagree
        # about which directory is the cache root. A path removes the guesswork:
        # the exact weights are named, nothing is resolved, nothing can download
        # a different revision later. The host still uses the repo id.
        model_name = model_name or os.environ.get(
            "CIS_EMBED_MODEL", "all-MiniLM-L6-v2")
        logger.info("Loading embedding model: %s", model_name)
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def embed(self, texts):
        """Embed a list of text strings. Returns list of embedding vectors."""
        if not texts:
            return []
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_single(self, text):
        """Embed a single text string. Returns embedding vector."""
        result = self.embed([text])
        return result[0] if result else []


# ── 3. ChromaClient ────────────────────────────────────────────────

COLLECTION_SCHEMAS = {
    "cis_sessions": {
        "source_table": "dam_extracted_text",
        "content_column": "content_text",
        "metadata_columns": {
            "source_table": "dam_extracted_text",
            "source_id": None,  # filled at query time
            "speaker_role": None,
            "asset_id": None,
        },
    },
    "cis_deliberations": {
        "source_table": "deliberation_rounds",
        "content_column": "drafter_output",
        "metadata_columns": {
            "source_table": "deliberation_rounds",
            "source_id": None,
            "run_id": None,
            "round_number": None,
        },
    },
    "cis_decisions": {
        "source_table": "project_decisions",
        "content_column": "decision",
        "metadata_columns": {
            "source_table": "project_decisions",
            "source_id": None,
            "decision_id": None,
        },
    },
    "cis_closeouts": {
        "source_table": "session_closeouts",
        "content_column": "failure_summary",
        "metadata_columns": {
            "source_table": "session_closeouts",
            "source_id": None,
            "log_path": None,
        },
    },
}


def _get_chroma_path():
    """Return Chroma storage path from env or default."""
    return os.environ.get(
        "CIS_CHROMA_PATH",
        "/mnt/projects/cis/data/chroma_data",
    )


def _get_db_path():
    """Return spine path from env or default."""
    return os.environ.get(
        "CIS_SPINE_PATH",
        "/mnt/projects/cis/data/cis_memory.db",
    )


class ChromaClient:
    """Chroma vector database client — manages collections and queries."""

    def __init__(self, chroma_path=None, embedding_pipeline=None):
        import chromadb
        self.chroma_path = chroma_path or _get_chroma_path()
        self._client = chromadb.PersistentClient(path=self.chroma_path)
        self._embedding = embedding_pipeline or EmbeddingPipeline()
        self._filter = SecretFilterPipeline()

    # ── Collection management ────────────────────────

    def get_or_create_collection(self, name):
        """Get existing collection or create with default embedding function."""
        try:
            return self._client.get_collection(name)
        except Exception:
            return self._client.create_collection(name)

    def list_collections(self):
        """List all collection names."""
        return [c.name for c in self._client.list_collections()]

    def collection_count(self, name):
        """Return document count for a collection."""
        try:
            coll = self._client.get_collection(name)
            return coll.count()
        except Exception:
            return 0

    # ── Index building ──────────────────────────────

    def index_from_spine(self, db_path=None):
        """
        Build/update Chroma index from the SQLite spine.

        Reads from dam_extracted_text, deliberation_rounds,
        project_decisions, and session_closeouts. Applies secret
        filtering before embedding. Tracks indexed source_ids to
        support incremental updates.

        Returns dict with stats per collection.
        """
        db_path = db_path or _get_db_path()
        conn = sqlite3.connect(
            "file:{}?mode=ro".format(db_path), uri=True
        )
        conn.row_factory = sqlite3.Row

        stats = {}
        self._filter.reset_stats()

        # cis_sessions — from dam_extracted_text
        stats["cis_sessions"] = self._index_sessions(conn)

        # cis_deliberations — from deliberation_rounds
        stats["cis_deliberations"] = self._index_deliberations(conn)

        # cis_decisions — from project_decisions
        stats["cis_decisions"] = self._index_decisions(conn)

        # cis_closeouts — from session_closeouts
        stats["cis_closeouts"] = self._index_closeouts(conn)

        conn.close()

        stats["secret_filter"] = dict(self._filter.stats)
        return stats

    def _index_sessions(self, conn):
        """Index dam_extracted_text rows."""
        coll = self.get_or_create_collection("cis_sessions")
        batch_size = 1000
        offset = 0
        total_indexed = 0
        total_excluded = 0

        while True:
            rows = conn.execute(
                """SELECT id, content_text, speaker_role, asset_id
                   FROM dam_extracted_text
                   WHERE content_text IS NOT NULL
                     AND content_text != ''
                   ORDER BY id
                   LIMIT ? OFFSET ?""",
                (batch_size, offset),
            ).fetchall()

            if not rows:
                break

            texts = []
            metadatas = []
            ids = []

            for row in rows:
                filtered_text, action = self._filter.filter_text(
                    row["content_text"] or ""
                )
                if action == "excluded":
                    total_excluded += 1
                    continue

                texts.append(filtered_text)
                metadatas.append({
                    "source_table": "dam_extracted_text",
                    "source_id": str(row["id"]),
                    "speaker_role": row["speaker_role"] or "",
                    "asset_id": str(row["asset_id"]) if row["asset_id"] else "",
                })
                ids.append("session_{}".format(row["id"]))
                total_indexed += 1

            if texts:
                embeddings = self._embedding.embed(texts)
                coll.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=texts,
                )

            offset += batch_size

        return {
            "indexed": total_indexed,
            "excluded": total_excluded,
            "total_in_collection": coll.count(),
        }

    def _index_deliberations(self, conn):
        """Index deliberation_rounds drafter_output."""
        coll = self.get_or_create_collection("cis_deliberations")
        rows = conn.execute(
            """SELECT id, drafter_output, run_id, round_number
               FROM deliberation_rounds
               WHERE drafter_output IS NOT NULL
                 AND drafter_output != ''
               ORDER BY id"""
        ).fetchall()

        texts, metadatas, ids = [], [], []
        excluded = 0

        for row in rows:
            filtered_text, action = self._filter.filter_text(
                row["drafter_output"] or ""
            )
            if action == "excluded":
                excluded += 1
                continue
            texts.append(filtered_text)
            metadatas.append({
                "source_table": "deliberation_rounds",
                "source_id": str(row["id"]),
                "run_id": row["run_id"] or "",
                "round_number": str(row["round_number"]) if row["round_number"] else "0",
            })
            ids.append("delib_{}".format(row["id"]))

        if texts:
            embeddings = self._embedding.embed(texts)
            coll.add(ids=ids, embeddings=embeddings, metadatas=metadatas,
                     documents=texts)

        return {
            "indexed": len(texts),
            "excluded": excluded,
            "total_in_collection": coll.count(),
        }

    def _index_decisions(self, conn):
        """Index project_decisions text."""
        coll = self.get_or_create_collection("cis_decisions")
        rows = conn.execute(
            """SELECT id, label, decision, reason
               FROM project_decisions
               WHERE decision IS NOT NULL AND decision != ''
               ORDER BY id"""
        ).fetchall()

        texts, metadatas, ids = [], [], []
        excluded = 0

        for row in rows:
            content = "{}: {}".format(row["label"] or "", row["decision"] or "")
            if row["reason"]:
                content += " — {}".format(row["reason"])
            filtered_text, action = self._filter.filter_text(content)
            if action == "excluded":
                excluded += 1
                continue
            texts.append(filtered_text)
            metadatas.append({
                "source_table": "project_decisions",
                "source_id": str(row["id"]),
                "decision_id": row["id"] or "",
            })
            ids.append("decision_{}".format(row["id"]))

        if texts:
            embeddings = self._embedding.embed(texts)
            coll.add(ids=ids, embeddings=embeddings, metadatas=metadatas,
                     documents=texts)

        return {
            "indexed": len(texts),
            "excluded": excluded,
            "total_in_collection": coll.count(),
        }

    def _index_closeouts(self, conn):
        """Index session_closeouts summaries."""
        coll = self.get_or_create_collection("cis_closeouts")
        rows = conn.execute(
            """SELECT id, failure_summary, log_path
               FROM session_closeouts
               WHERE failure_summary IS NOT NULL
                 AND failure_summary != ''
               ORDER BY id"""
        ).fetchall()

        texts, metadatas, ids = [], [], []
        excluded = 0

        for row in rows:
            filtered_text, action = self._filter.filter_text(
                row["failure_summary"] or ""
            )
            if action == "excluded":
                excluded += 1
                continue
            texts.append(filtered_text)
            metadatas.append({
                "source_table": "session_closeouts",
                "source_id": str(row["id"]),
                "log_path": row["log_path"] or "",
            })
            ids.append("closeout_{}".format(row["id"]))

        if texts:
            embeddings = self._embedding.embed(texts)
            coll.add(ids=ids, embeddings=embeddings, metadatas=metadatas,
                     documents=texts)

        return {
            "indexed": len(texts),
            "excluded": excluded,
            "total_in_collection": coll.count(),
        }

    # ── Query functions ──────────────────────────────

    def search_semantic(self, query_text, top_k=10, collection_name=None):
        """
        Semantic search across Chroma collections.

        If collection_name is specified, search only that collection.
        Otherwise search all collections and merge results.
        """
        query_embedding = self._embedding.embed_single(query_text)

        if collection_name:
            coll = self._client.get_collection(collection_name)
            results = coll.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, coll.count()),
                include=["documents", "metadatas", "distances"],
            )
            return self._format_results(results)

        # Search all collections
        all_results = []
        for name in self.list_collections():
            try:
                coll = self._client.get_collection(name)
                if coll.count() == 0:
                    continue
                results = coll.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, coll.count()),
                    include=["documents", "metadatas", "distances"],
                )
                formatted = self._format_results(results, collection=name)
                all_results.extend(formatted)
            except Exception:
                continue

        # Sort by distance (ascending = more relevant) and take top_k
        all_results.sort(key=lambda x: x.get("distance", 999.0))
        return all_results[:top_k]

    def get_similar(self, document_id, top_k=10):
        """
        Get documents similar to a given document by ID.

        Searches within the collection inferred from the document_id prefix.
        """
        prefix = document_id.split("_")[0] if "_" in document_id else ""
        collection_map = {
            "session": "cis_sessions",
            "delib": "cis_deliberations",
            "decision": "cis_decisions",
            "closeout": "cis_closeouts",
        }
        coll_name = collection_map.get(prefix)
        if not coll_name:
            return {"error": "Unknown collection for document ID: {}".format(
                document_id)}

        try:
            coll = self._client.get_collection(coll_name)
            # Get the embedding of the source document
            source = coll.get(
                ids=[document_id],
                include=["embeddings", "documents", "metadatas"],
            )
            if not source or not source["embeddings"]:
                return {"error": "Document not found: {}".format(document_id)}

            query_embedding = source["embeddings"][0]
            results = coll.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k + 1, coll.count()),  # +1 to skip self
                include=["documents", "metadatas", "distances"],
            )
            formatted = self._format_results(results, collection=coll_name)

            # Filter out the query document itself
            formatted = [
                r for r in formatted
                if r.get("id") != document_id
            ][:top_k]

            return formatted
        except Exception as exc:
            return {"error": str(exc)}

    def _format_results(self, chroma_results, collection=None):
        """Convert Chroma query results to a list of dicts."""
        output = []
        if not chroma_results or "ids" not in chroma_results:
            return output

        ids_list = chroma_results.get("ids", [[]])[0]
        docs_list = chroma_results.get("documents", [[]])[0] if chroma_results.get("documents") else [""] * len(ids_list)
        meta_list = chroma_results.get("metadatas", [[]])[0] if chroma_results.get("metadatas") else [{}] * len(ids_list)
        dist_list = chroma_results.get("distances", [[]])[0] if chroma_results.get("distances") else [0.0] * len(ids_list)

        for i in range(len(ids_list)):
            item = {
                "id": ids_list[i],
                "document": docs_list[i][:500] if docs_list[i] else "",  # truncated
                "distance": round(dist_list[i], 4) if i < len(dist_list) else None,
                "metadata": meta_list[i] if i < len(meta_list) else {},
            }
            if collection:
                item["collection"] = collection
            output.append(item)

        return output


# ── Module-level singleton (lazily initialized) ────────────────────

_client = None


def get_client():
    """Get or create the ChromaClient singleton."""
    global _client
    if _client is None:
        _client = ChromaClient()
    return _client
