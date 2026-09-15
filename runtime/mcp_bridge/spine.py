"""
spine.py — Read-only SQLite queries for the CIS MCP Bridge.

All queries are SELECT only. The database is opened in read-only mode
(uri=True, mode=ro) to OS-enforce the no-write constraint.

Tables read:
  build_plan_nodes, workflow_runs, deliberation_rounds,
  workflow_run_artifacts, eric_gate_approvals, session_closeouts,
  session_closeouts_fts, project_decisions, open_questions
"""
import os
import sqlite3
import threading


def _get_db_path():
    """Return the CIS spine path from CIS_SPINE_PATH env var."""
    path = os.environ.get("CIS_SPINE_PATH", "")
    if not path:
        raise RuntimeError("CIS_SPINE_PATH environment variable is not set")
    return path


def _connect_readonly(db_path=None):
    """Open the spine database in read-only mode (OS-enforced)."""
    if db_path is None:
        db_path = _get_db_path()
    # Use URI mode with mode=ro for read-only enforcement
    # Encode the path for URI usage (handle spaces and special chars)
    encoded = db_path.replace("%", "%25").replace("#", "%23")
    uri = "file:{}?mode=ro".format(encoded)
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row):
    """Convert sqlite3.Row to dict."""
    if row is None:
        return None
    return dict(row)


def _rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows] if rows else []


# ── Query Functions (one per MCP tool) ───────────────────────────────


def query_current_phase(db_path=None):
    """
    Current build tier, status, and next actions from build_plan_nodes.

    Returns dict with keys:
      build_phase: str (from project_state)
      in_progress: list of nodes with status IN_PROGRESS
      pending: list of nodes with status PENDING
      next_tier: str (from project_state)
      next_action: str (from project_state)
    """
    conn = _connect_readonly(db_path)
    try:
        # Build phase from project_state (latest non-superseded)
        phase_row = conn.execute(
            """SELECT value FROM project_state
               WHERE key = 'build_phase' AND superseded_at IS NULL
               ORDER BY id DESC LIMIT 1"""
        ).fetchone()

        next_tier_row = conn.execute(
            """SELECT value FROM project_state
               WHERE key = 'next_tier' AND superseded_at IS NULL
               ORDER BY id DESC LIMIT 1"""
        ).fetchone()

        next_action_row = conn.execute(
            """SELECT value FROM project_state
               WHERE key = 'next_action' AND superseded_at IS NULL
               ORDER BY id DESC LIMIT 1"""
        ).fetchone()

        in_progress = _rows_to_list(conn.execute(
            """SELECT node_label, status, tier, blocked_reason
               FROM build_plan_nodes
               WHERE project_id = 'cis' AND status = 'IN_PROGRESS'
               ORDER BY sequence"""
        ).fetchall())

        pending = _rows_to_list(conn.execute(
            """SELECT node_label, status, tier, blocked_reason
               FROM build_plan_nodes
               WHERE project_id = 'cis' AND status = 'PENDING'
               ORDER BY sequence"""
        ).fetchall())

        return {
            "build_phase": phase_row["value"] if phase_row else None,
            "next_tier": next_tier_row["value"] if next_tier_row else None,
            "next_action": next_action_row["value"] if next_action_row else None,
            "in_progress": in_progress,
            "pending": pending,
        }
    finally:
        conn.close()


def query_build_status(node_label, db_path=None):
    """
    Single build_plan_node by label.

    Returns dict with keys: node_label, status, tier, blocked_reason,
    evidence_path, commit_hash, completed_at, approved_at, created_at, updated_at.
    Returns None if no matching node.
    """
    conn = _connect_readonly(db_path)
    try:
        row = conn.execute(
            """SELECT node_label, status, tier, blocked_reason,
                      evidence_path, commit_hash, completed_at,
                      approved_at, created_at, updated_at
               FROM build_plan_nodes
               WHERE node_label = ?""",
            (node_label,),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def query_next_actions(db_path=None):
    """
    Nodes with status PENDING where dependencies are satisfied.

    Returns list of dicts with all build_plan_nodes columns for eligible nodes.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT node_label, status, tier, blocked_reason,
                      evidence_path, commit_hash, completed_at,
                      approved_at, created_at, updated_at
               FROM build_plan_nodes
               WHERE project_id = 'cis' AND status = 'PENDING'
               ORDER BY sequence"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_recent_runs(limit=5, db_path=None):
    """
    Last N workflow_runs.

    Returns list of dicts with keys: id, topic, result, rounds_completed,
    created_at, completed_at, status.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT id, topic, result, rounds_completed,
                      created_at, completed_at, status
               FROM workflow_runs
               ORDER BY created_at DESC
               LIMIT ?""",
            (int(limit),),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_run_detail(run_id, db_path=None):
    """
    Single workflow_run + its deliberation_rounds + artifacts.

    Returns dict with keys:
      run: dict (workflow_runs row)
      rounds: list of dicts (deliberation_rounds rows)
      artifacts: list of dicts (workflow_run_artifacts rows)
    Returns None if run_id not found.
    """
    conn = _connect_readonly(db_path)
    try:
        run_row = conn.execute(
            """SELECT * FROM workflow_runs WHERE id = ?""",
            (run_id,),
        ).fetchone()
        if run_row is None:
            return None

        rounds = _rows_to_list(conn.execute(
            """SELECT * FROM deliberation_rounds
               WHERE run_id = ?
               ORDER BY round_number""",
            (run_id,),
        ).fetchall())

        artifacts = _rows_to_list(conn.execute(
            """SELECT * FROM workflow_run_artifacts
               WHERE run_id = ?
               ORDER BY created_at""",
            (run_id,),
        ).fetchall())

        return {
            "run": dict(run_row),
            "rounds": rounds,
            "artifacts": artifacts,
        }
    finally:
        conn.close()


def query_open_decisions(db_path=None):
    """
    Active non-superseded decisions from project_decisions.

    Returns list of dicts.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT * FROM project_decisions
               WHERE status = 'DECIDED' AND superseded_by IS NULL
               ORDER BY decided_at DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_open_questions(db_path=None):
    """
    All open questions from open_questions.

    Returns list of dicts.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT * FROM open_questions
               WHERE status = 'OPEN'
               ORDER BY opened_at DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_eric_gate_status(db_path=None):
    """
    Pending Eric Gate approvals.

    Returns list of dicts from eric_gate_approvals where is_current=1,
    joined with goal_references for goal_label.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT ega.decision, ega.decided_at,
                      ega.workflow_run_id, ega.rationale,
                      ega.created_at, gr.goal_label
               FROM eric_gate_approvals ega
               LEFT JOIN goal_references gr
                 ON ega.goal_reference_id = gr.id
               WHERE ega.is_current = 1
               ORDER BY ega.decided_at DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_eric_gate_approval_for_run(run_id, db_path=None):
    """Return the current Eric Gate decision row for a workflow_run, or None.

    Replaces the old bool-only check_eric_gate_approval(). Returns dict(row)
    with every eric_gate_approvals column for the current (is_current=1) row —
    including `decision` (APPROVE/VETO/RETURN_TO_DRAFT), decided_at,
    decided_by, rationale, etc. Returns None when no current decision exists.

    Callers MUST check row["decision"] == "APPROVE" explicitly; a non-None
    return is not itself approval.
    """
    conn = _connect_readonly(db_path)
    try:
        row = conn.execute(
            """SELECT * FROM eric_gate_approvals
               WHERE workflow_run_id = ?
                 AND is_current = 1
               ORDER BY decided_at DESC LIMIT 1""",
            (run_id,),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def check_eric_gate_approval(run_id, db_path=None):
    """DEPRECATED bool wrapper — prefer query_eric_gate_approval_for_run().

    Kept only for backward compatibility with tests/test_mcp_dispatch.py.
    Returns True iff the current decision row is APPROVE.
    """
    row = query_eric_gate_approval_for_run(run_id, db_path)
    return bool(row and row.get("decision") == "APPROVE")


def query_search_sessions(query_text, limit=10, db_path=None):
    """
    FTS5 search across session_closeouts.

    Searches the session_closeouts_fts virtual table for matching text
    in failure_summary, failure_step, log_path, and created_by columns.
    Returns matching rows from the base session_closeouts table.

    Returns list of dicts with session_closeouts columns.
    """
    conn = _connect_readonly(db_path)
    try:
        # Use FTS5 MATCH to find matching rowids, then join back to base table
        rows = conn.execute(
            """SELECT sc.*
               FROM session_closeouts sc
               JOIN session_closeouts_fts fts ON sc.id = fts.rowid
               WHERE session_closeouts_fts MATCH ?
               ORDER BY sc.created_at DESC
               LIMIT ?""",
            (query_text, int(limit)),
        ).fetchall()

        # Also try a LIKE fallback for simple term matching
        if not rows:
            like_pattern = "%{}%".format(query_text)
            rows = conn.execute(
                """SELECT * FROM session_closeouts
                   WHERE failure_summary LIKE ?
                      OR failure_step LIKE ?
                      OR log_path LIKE ?
                      OR created_by LIKE ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (like_pattern, like_pattern, like_pattern,
                 like_pattern, int(limit)),
            ).fetchall()

        return _rows_to_list(rows)
    finally:
        conn.close()


def search_knowledge_fts(query_text, limit=10, db_path=None):
    """FTS5 search across knowledge_messages, with LIKE fallback.

    The knowledge_messages_fts index is built and populated (verified
    2026-09-10: 2,650,075 rows, matching the base table; MATCH returns results
    instantly). The LIKE fallback is retained as a safety net for the case
    where the index is dropped or a MATCH query errors out (e.g. a stray
    column-filter token from a query containing ':'). The FTS path is guarded:
    when the index is absent or any FTS error occurs, it falls back to a LIKE
    scan instead of erroring out.
    """
    conn = _connect_readonly(db_path)
    try:
        safe_query = query_text.replace('"', '').replace("'", "")
        rows = None
        try:
            rows = conn.execute(
                """SELECT km.id, km.content, km.source, km.role, km.source_key
                   FROM knowledge_messages km
                   JOIN knowledge_messages_fts fts ON km.id = fts.rowid
                   WHERE knowledge_messages_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (safe_query, int(limit)),
            ).fetchall()
        except Exception:
            rows = None
        if not rows:
            like = f"%{safe_query}%"
            rows = conn.execute(
                """SELECT id, content, source, role, source_key
                   FROM knowledge_messages
                   WHERE content LIKE ?
                   ORDER BY id DESC
                   LIMIT ?""",
                (like, int(limit)),
            ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


# --- Semantic search singleton cache ---------------------------------------
# The knowledge_messages collection holds 2.65M precomputed embeddings backed
# by a 4.4 GB HNSW index + a 19 GB metadata sqlite. Building the client,
# collection and embedding model fresh on every call re-pays a ~70s cold start
# (torch import + HNSW index unpickle) per query, which blows the MCP tool
# timeout. The MCP server is a long-lived stdio process, so we cache the
# components once and reuse them: the first query pays the cold start, every
# later query is sub-second.
_chroma_client = None
_chroma_collection = None
_embed_model = None


_semantic_lock = threading.Lock()


def _semantic_components():
    """Load (once) and return the cached (collection, model) pair.

    Thread-safe: the pre-warm thread (started at server boot) and the first
    query thread can race to load. The lock serializes them so the heavy
    torch/model load happens exactly once and both callers get the cached pair.
    """
    global _chroma_client, _chroma_collection, _embed_model
    if _chroma_collection is not None and _embed_model is not None:
        return _chroma_collection, _embed_model

    with _semantic_lock:
        if _chroma_collection is not None and _embed_model is not None:
            return _chroma_collection, _embed_model
        import chromadb
        from sentence_transformers import SentenceTransformer

        if _chroma_client is None:
            repo = os.environ.get("CIS_REPO_ROOT", "/workspace/cis")
            _chroma_client = chromadb.PersistentClient(
                path=os.path.join(repo, "data", "chroma_data")
            )
            _chroma_collection = _chroma_client.get_collection("knowledge_messages")

        if _embed_model is None:
            model_src = os.environ.get("CIS_EMBED_MODEL", "all-MiniLM-L6-v2")
            _embed_model = SentenceTransformer(model_src)

    return _chroma_collection, _embed_model


def prewarm_semantic():
    """Load the embedding model + Chroma in a background thread at MCP server
    startup, so the first semantic-search call does not pay the ~70s cold start.

    Called from server.run() before the stdio loop. The thread is a daemon so it
    never blocks shutdown; on failure semantic search still falls back to the
    FTS/LIKE path in its caller (search_knowledge_semantic returns []).
    """
    def _load():
        try:
            _semantic_components()
        except Exception:
            pass

    threading.Thread(target=_load, daemon=True, name="semantic-prewarm").start()


def search_knowledge_semantic(query_text, top_k=10, db_path=None):
    """Semantic search across knowledge_messages via ChromaDB.

    The knowledge_messages collection stores PRE-COMPUTED embeddings (dim 384,
    all-MiniLM-L6-v2) with NO embedding function configured on the collection
    (config_json_str={}). Querying by raw text (query_texts) therefore fails —
    the query must be embedded locally and sent as query_embeddings. The client,
    collection and model are cached at module scope (the MCP server is a
    long-lived stdio process), so the ~70s cold start is paid once and
    subsequent queries are sub-second. Returns [] (not an error) when chromadb
    or the embedding model is unavailable, so the FTS/LIKE path in the caller
    still stands alone rather than erroring out.
    """
    try:
        collection, model = _semantic_components()
    except Exception:
        return []
    try:
        embedding = model.encode([query_text], show_progress_bar=False).tolist()[0]
    except Exception:
        return []
    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, 50),
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return []

    hits = []
    if results.get("ids") and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            hits.append({
                "id": doc_id,
                "content": (results["documents"][0][i] or "")[:500]
                if results.get("documents") else "",
                "source": results["metadatas"][0][i].get("source", "")
                if results.get("metadatas") else "",
                "role": results["metadatas"][0][i].get("role", "")
                if results.get("metadatas") else "",
                "score": 1.0 - float(results["distances"][0][i])
                if results.get("distances") else 0,
            })

    return hits


def query_dev_pivot_status(status_filter=None, category_filter=None, db_path=None):
    """Query dev_pivot_status table with optional filters."""
    db = db_path or _get_db_path()
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM dev_pivot_status WHERE 1=1"
    params = []

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY doc_id"

    try:
        rows = conn.execute(query, params).fetchall()
        return _rows_to_list(rows)
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def query_queue_item(item_num, db_path=None):
    """Single unified-build-list item by its number, e.g. '3.21'.

    BUILD LIST 3.21. This is the first reader of queue_items and the reason the
    table is not sediment (item 2.37).

    DEPENDENCY EDGES ARE DELIBERATELY NOT RETURNED. queue_edges holds 45 rows
    hand-extracted on 2026-09-05 that nothing regenerates; six items added since
    have dependency prose and zero edges. Both advisor lineages independently
    said to omit rather than serve them: returning nothing forces the caller to
    say "I don't know", returning a stale snapshot lets it say "I know" when it
    does not. The dependency half arrives with the queue_edges regeneration
    card, not before.

    Returns dict with item_num, tier, title, form, scope, need_status, need_raw,
    source_line, source_sha, extracted_at, plus answers_2_30 describing what this
    row can and cannot tell the caller. Returns None if no matching item.
    """
    conn = _connect_readonly(db_path)
    try:
        row = conn.execute(
            """SELECT item_num, tier, title, form, scope, need_status,
                      need_raw, source_line, source_sha, extracted_at
                 FROM queue_items
                WHERE item_num = ?""",
            (item_num,),
        ).fetchone()
        result = _row_to_dict(row)
        if result is not None:
            # The current item, re-checked on every call. A pointer left on
            # finished work is the DEFAULT failure here, not an edge case --
            # nothing advances it when the markdown marks an item done. So the
            # reader refuses to report a DONE item as current and says STALE
            # instead: an honest admission beats a false assertion, which is
            # the same standard the unset case already met.
            cur = "NOT AVAILABLE - nothing designates one"
            try:
                ptr = conn.execute(
                    "SELECT value FROM project_state "
                    "WHERE key='current_queue_item' AND superseded_at IS NULL"
                ).fetchone()
                if ptr:
                    st = conn.execute(
                        "SELECT need_status FROM queue_items WHERE item_num=?",
                        (ptr[0],)).fetchone()
                    if st is None:
                        cur = "STALE - pointer names %s, which is not an item" % ptr[0]
                    elif st[0] == "DONE":
                        cur = "STALE - pointer names %s, which is DONE" % ptr[0]
                    else:
                        cur = ptr[0]
            except sqlite3.OperationalError:
                pass

            result["answers_2_30"] = {
                "what_was_just_done": "need_status on this row",
                "what_is_the_current_item": cur,
                "what_does_it_depend_on": "NOT AVAILABLE - queue_edges is not regenerated",
                "did_it_succeed": "ABSENT BY DECISION - see ADR-3.21-001",
            }
        return result
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()
