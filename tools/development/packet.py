#!/usr/bin/env python3
"""packet.py — prepare a task packet and check it for staleness (WB.1C).

A packet binds: the authoritative queue_items row for a task, the task's
dev_continuity_events (this module's during-work record), cited KB evidence,
and (WB.1C-R1 remediation 4) source/evidence references already present in
the queue item's own body_md, followed automatically rather than requiring
the developer to rediscover and re-supply them as --query/--kb-id — all at
specific revisions/hashes, so a freshness check later can tell whether any
of those has moved since the packet was built.

prepare_packet() never calls a model. Concept queries are plain FTS keyword
strings supplied by the developer (bounded, explicit) — this is not semantic
mining and does not re-embed anything. Queue-referenced material is EVIDENCE,
not instruction: nothing extracted from it is ever executed.
"""
import hashlib
import json
import time
import uuid

from . import continuity_store as cs
from . import kb_read
from . import queue_refs


def _sha256(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _queue_fingerprint(conn, task):
    row = conn.execute(
        "SELECT item_num, title, body_md, need_status, status_changed_at, source_sha "
        "FROM queue_items WHERE item_num=?", (task,),
    ).fetchone()
    if row is None:
        return None, None
    max_event_id = conn.execute(
        "SELECT MAX(id) FROM queue_item_events WHERE item_num=?", (task,),
    ).fetchone()[0]
    fp = {
        "item_num": row["item_num"],
        "title": row["title"],
        "body_hash": _sha256(row["body_md"]),
        "need_status": row["need_status"],
        "status_changed_at": row["status_changed_at"],
        "source_sha": row["source_sha"],
        "max_queue_event_id": max_event_id,
    }
    snapshot = {
        "title": row["title"],
        "body_md": row["body_md"],
        "need_status": row["need_status"],
    }
    return fp, snapshot


def _follow_queue_references(conn, body_md, kb_evidence, kb_provenance):
    """Extract and resolve source/evidence references already present in
    body_md (WB.1C-R1 remediation 4). Mutates kb_evidence/kb_provenance in
    place for any kb_id reference that resolves, exactly like a
    developer-supplied --kb-id would be merged, but tagged with its origin
    so the packet never blends the two without saying so.

    Returns (detected, followed, unresolved, file_evidence) — the four
    lists the remediation requires the packet to expose separately.
    """
    detected_raw = queue_refs.extract_references(body_md)
    detected, followed, unresolved = [], [], []
    file_evidence = []

    # Batch-resolve every kb_id reference's ids in one query.
    all_kb_ids = sorted({i for r in detected_raw if r["type"] == "kb_id" for i in r["parsed_ids"]})
    kb_fetch = kb_read.fetch_by_ids(conn, all_kb_ids) if all_kb_ids else {"ok": True, "results": [], "missing": []}
    kb_by_id = {r["id"]: r for r in kb_fetch.get("results", [])} if kb_fetch.get("ok") else {}
    kb_fetch_ok = kb_fetch.get("ok", False) if all_kb_ids else True

    for ref in detected_raw:
        if ref["type"] == "kb_id":
            if ref["malformed"]:
                entry = {**ref, "resolution": "malformed"}
                detected.append(entry)
                unresolved.append(entry)
                continue
            id_results = []
            any_resolved = False
            for i in ref["parsed_ids"]:
                if not kb_fetch_ok:
                    id_results.append({"id": i, "resolution": "unavailable",
                                        "reason": kb_fetch.get("error")})
                    continue
                rec = kb_by_id.get(i)
                if rec is None:
                    id_results.append({"id": i, "resolution": "missing"})
                    continue
                id_results.append({"id": i, "resolution": "resolved",
                                    "source_key": rec["source_key"]})
                any_resolved = True
                kb_evidence[i] = rec
                kb_provenance.setdefault(i, set()).add("queue_reference")
            entry = {**ref, "ids": id_results}
            detected.append(entry)
            (followed if any_resolved else unresolved).append(entry)

        elif ref["type"] == "file_path":
            resolved = queue_refs.resolve_file_reference(ref["parsed_path"])
            entry = {**ref, **resolved}
            detected.append(entry)
            if resolved["resolution"] == "resolved":
                followed.append(entry)
                file_evidence.append({
                    "path": ref["parsed_path"],
                    "content": resolved["content"],
                    "content_hash": _sha256(resolved["content"]),
                    "origin": "queue_reference",
                })
            else:
                unresolved.append(entry)

        else:  # queue_item — recognized but out of this task's scope
            entry = {**ref, "resolution": "recognized_unsupported"}
            detected.append(entry)
            unresolved.append(entry)

    return detected, followed, unresolved, file_evidence


def prepare_packet(conn, *, task, actor, concept_queries=None, kb_ids=None,
                    kb_limit=8, dev_conn=None, follow_queue_references=True):
    """Build a packet for `task`.

    conn: connection to the DB holding queue_items/queue_item_events and
    knowledge_messages (production, read-only in normal use).
    dev_conn: connection for dev_continuity_events (defaults to `conn`; kept
    separate so tests can point queue reads at one fixture and continuity
    events at another, and so a not-yet-initialized dev schema is reported
    rather than silently mixed with the queue read).
    follow_queue_references: WB.1C-R1 remediation 4 — on by default. A
    caller can disable it (e.g. a narrow re-check) but prepare_packet's
    normal contract is to follow the queue's own references, not only what
    the developer explicitly supplied.
    """
    dev_conn = dev_conn or conn
    concept_queries = concept_queries or []
    kb_ids = kb_ids or []

    queue_fp, queue_snapshot = _queue_fingerprint(conn, task)
    if queue_fp is None:
        return {
            "ok": False,
            "error": f"unknown queue item {task!r} (not in queue_items)",
        }

    dev_initialized = cs.is_initialized(dev_conn)
    if dev_initialized:
        dev_latest_revision = cs.latest_revision(dev_conn, task)
        dev_events = cs.list_events(dev_conn, task)
    else:
        dev_latest_revision = None
        dev_events = []

    kb_evidence = {}
    kb_provenance = {}

    kb_searches = []
    for q in concept_queries:
        result = kb_read.search_knowledge(conn, q, limit=kb_limit)
        kb_searches.append(result)
        if result.get("ok"):
            for r in result["results"]:
                kb_evidence[r["id"]] = r
                kb_provenance.setdefault(r["id"], set()).add("concept_search")

    if kb_ids:
        direct = kb_read.fetch_by_ids(conn, kb_ids)
        for r in direct.get("results", []):
            kb_evidence[r["id"]] = r
            kb_provenance.setdefault(r["id"], set()).add("developer_kb_id")
    else:
        direct = {"ok": True, "results": [], "missing": []}

    if follow_queue_references:
        refs_detected, refs_followed, refs_unresolved, file_evidence = _follow_queue_references(
            conn, queue_snapshot["body_md"], kb_evidence, kb_provenance,
        )
    else:
        refs_detected = refs_followed = refs_unresolved = file_evidence = []

    kb_fingerprint = [
        {"id": rid, "source_key": r["source_key"], "content_hash": _sha256(r["content"])}
        for rid, r in sorted(kb_evidence.items())
    ]
    file_fingerprint = [
        {"path": f["path"], "content_hash": f["content_hash"]} for f in file_evidence
    ]

    evidence_with_provenance = [
        {**r, "_provenance": sorted(kb_provenance.get(rid, set()))}
        for rid, r in sorted(kb_evidence.items())
    ]

    packet = {
        "packet_id": str(uuid.uuid4()),
        "task": task,
        "actor": actor,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "queue_snapshot": queue_snapshot,
        "dev_events": dev_events,
        "dev_schema_initialized": dev_initialized,
        "kb_searches": kb_searches,
        "kb_direct_fetch": direct,
        "kb_evidence": evidence_with_provenance,
        "queue_references": {
            "detected": refs_detected,
            "followed": refs_followed,
            "unresolved": refs_unresolved,
        },
        "file_evidence": file_evidence,
        "fingerprint": {
            "queue": queue_fp,
            "dev_latest_revision": dev_latest_revision,
            "kb_evidence": kb_fingerprint,
            "file_evidence": file_fingerprint,
        },
        "ok": True,
    }
    return packet


def check_freshness(conn, packet, dev_conn=None):
    """Recompute every fingerprint the packet claims to bind and diff
    against the packet's own copy (WB.1C-R1 remediation 3: a field carried
    in the fingerprint but never compared here is a silent freshness gap,
    so every field written by _queue_fingerprint/prepare_packet must appear
    in this function too).

    Returns a dict with `stale: bool` and itemized reasons. A missing or
    re-fetch-failed KB/file row is reported as kb_missing/kb_changed/
    file evidence missing-or-changed (NOT folded into "unchanged") — a
    failed read is not a freshness pass.
    """
    if not packet.get("ok"):
        return {"stale": True, "reasons": ["packet itself was not ok at prepare time"]}

    dev_conn = dev_conn or conn
    task = packet["task"]
    reasons = []

    current_queue_fp, _ = _queue_fingerprint(conn, task)
    if current_queue_fp is None:
        reasons.append("queue_item no longer found")
    else:
        prior = packet["fingerprint"]["queue"]
        if current_queue_fp.get("title") != prior.get("title"):
            reasons.append(
                f"queue_item title changed "
                f"({prior.get('title')!r} -> {current_queue_fp.get('title')!r})"
            )
        if current_queue_fp["body_hash"] != prior["body_hash"]:
            reasons.append("queue_item body_md changed")
        if current_queue_fp["need_status"] != prior["need_status"]:
            reasons.append(
                f"queue_item need_status changed "
                f"({prior['need_status']!r} -> {current_queue_fp['need_status']!r})"
            )
        if current_queue_fp.get("status_changed_at") != prior.get("status_changed_at"):
            reasons.append(
                f"queue_item status_changed_at changed "
                f"({prior.get('status_changed_at')!r} -> {current_queue_fp.get('status_changed_at')!r})"
            )
        if current_queue_fp.get("source_sha") != prior.get("source_sha"):
            reasons.append(
                f"queue_item source_sha changed "
                f"({prior.get('source_sha')!r} -> {current_queue_fp.get('source_sha')!r})"
            )
        if current_queue_fp["max_queue_event_id"] != prior["max_queue_event_id"]:
            reasons.append("new queue_item_events recorded for this task")

    new_dev_events = []
    if cs.is_initialized(dev_conn):
        prior_rev = packet["fingerprint"]["dev_latest_revision"] or 0
        new_dev_events = cs.list_events(dev_conn, task, since_revision=prior_rev)
        if new_dev_events:
            reasons.append(
                f"{len(new_dev_events)} new dev_continuity_events since revision {prior_rev}"
            )
    elif packet["fingerprint"]["dev_latest_revision"] is not None:
        reasons.append("dev_continuity schema no longer initialized (was initialized at prepare)")

    kb_missing, kb_changed, kb_source_key_changed = [], [], []
    ids = [e["id"] for e in packet["fingerprint"]["kb_evidence"]]
    if ids:
        refetch = kb_read.fetch_by_ids(conn, ids)
        if not refetch.get("ok"):
            reasons.append(f"kb re-fetch failed: {refetch.get('error')}")
        else:
            by_id = {r["id"]: r for r in refetch["results"]}
            for entry in packet["fingerprint"]["kb_evidence"]:
                cur = by_id.get(entry["id"])
                if cur is None:
                    kb_missing.append(entry["id"])
                    continue
                if _sha256(cur["content"]) != entry["content_hash"]:
                    kb_changed.append(entry["id"])
                # WB.1C-R2.1: source_key is bound into the fingerprint (it
                # is the evidence's identity/provenance, not just its
                # text) but was never actually compared here — a row that
                # keeps the same id and content but gets re-tagged to a
                # different source_key must still invalidate the packet.
                if cur.get("source_key") != entry.get("source_key"):
                    kb_source_key_changed.append(entry["id"])
            if kb_missing:
                reasons.append(f"KB evidence missing on re-fetch: {kb_missing}")
            if kb_changed:
                reasons.append(f"KB evidence content changed: {kb_changed}")
            for kid in kb_source_key_changed:
                reasons.append(f"KB evidence {kid} source_key changed")

    # File evidence auto-followed from the queue (remediation 4) is
    # freshness-checked exactly like KB evidence — re-resolve, compare hash,
    # a deletion or a read failure is staleness, not silence.
    file_missing, file_changed, file_errors = [], [], []
    for entry in packet["fingerprint"].get("file_evidence", []):
        cur = queue_refs.resolve_file_reference(entry["path"])
        if cur["resolution"] == "missing":
            file_missing.append(entry["path"])
        elif cur["resolution"] != "resolved":
            file_errors.append(entry["path"])
        elif _sha256(cur["content"]) != entry["content_hash"]:
            file_changed.append(entry["path"])
    if file_missing:
        reasons.append(f"file evidence deleted: {file_missing}")
    if file_errors:
        reasons.append(f"file evidence read error: {file_errors}")
    if file_changed:
        reasons.append(f"file evidence content changed: {file_changed}")

    return {
        "stale": bool(reasons),
        "reasons": reasons,
        "new_dev_events": new_dev_events,
        "kb_missing": kb_missing,
        "kb_changed": kb_changed,
        "kb_source_key_changed": kb_source_key_changed,
        "file_missing": file_missing,
        "file_changed": file_changed,
        "file_errors": file_errors,
    }
