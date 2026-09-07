#!/usr/bin/env python3
"""seed_build_plan.py — Seed CIS build graph. Component 3.5 Phase 2. Idempotent."""

import sys
sys.path.insert(0, '/mnt/projects/cis/runtime')
from db.database import init_db
from db.build_plan import create_node, create_dependency

NODES = [
    # (project_id, node_label, tier, sequence, status, blocked_reason, required_role, allowed_mode)
    ('cis', 'Tier 0 — Deliberation Engine', '0', 1, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 1 — Deterministic Verification Gates', '1', 2, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 2 — Kanban Coordination Layer', '2', 3, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 3 — Pipeline Smoke Test', '3', 4, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 4 — SQLite Spine', '4', 5, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 5 — Context Export Pipeline', '5', 6, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 6 — Pipeline Integration', '6', 7, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 7 — Full Durable Router Pipeline', '7', 8, 'DEFERRED',
     'Intentionally held pending Eric decision. Full reclassification must be spine-native; Kanban remains retired as pipeline transport per ADR-013. Partial work exists in 7.1/7.5a/7.5b.',
     'Drafter', 'specification'),
    ('cis', 'Tier 7.1 — Router Reclassification (archive route)', '7.1', 9, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 7.5a — Corpus Audit', '7.5a', 10, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 7.5b — Clean Subset Import + FTS5', '7.5b', 11, 'COMPLETE', None, 'Implementer', 'implementation'),
    ('cis', 'Tier 8 — MCP Bridge', '8', 12, 'BLOCKED',
     'Gated on Tier 7 Full Durable Router Pipeline per dependency graph.',
     None, 'specification'),
    ('cis', 'Tier 9 — Chroma/VDB', '9', 13, 'BLOCKED',
     'Gated on Tier 8 MCP Bridge per dependency graph.',
     None, None),
    ('cis', 'Tier 10 — CIS UI / Custom Display Views', '10', 14, 'BLOCKED',
     'Gated on Tier 9 Chroma/VDB per dependency graph.',
     None, None),
    ('cis', 'Component 3.5 — Build-Plan Spine Authority', '3.5', 15, 'IN_PROGRESS',
     None, 'Implementer', 'implementation'),
]

DEPENDENCIES = [
    ('Tier 1 — Deterministic Verification Gates', 'Tier 0 — Deliberation Engine', 'HARD'),
    ('Tier 2 — Kanban Coordination Layer', 'Tier 0 — Deliberation Engine', 'HARD'),
    ('Tier 3 — Pipeline Smoke Test', 'Tier 0 — Deliberation Engine', 'HARD'),
    ('Tier 3 — Pipeline Smoke Test', 'Tier 2 — Kanban Coordination Layer', 'HARD'),
    ('Tier 4 — SQLite Spine', 'Tier 3 — Pipeline Smoke Test', 'HARD'),
    ('Tier 5 — Context Export Pipeline', 'Tier 3 — Pipeline Smoke Test', 'HARD'),
    ('Tier 5 — Context Export Pipeline', 'Tier 4 — SQLite Spine', 'HARD'),
    ('Tier 6 — Pipeline Integration', 'Tier 5 — Context Export Pipeline', 'HARD'),
    ('Tier 7 — Full Durable Router Pipeline', 'Tier 6 — Pipeline Integration', 'HARD'),
    ('Tier 7.1 — Router Reclassification (archive route)', 'Tier 6 — Pipeline Integration', 'HARD'),
    ('Tier 7.5a — Corpus Audit', 'Tier 7.1 — Router Reclassification (archive route)', 'HARD'),
    ('Tier 7.5b — Clean Subset Import + FTS5', 'Tier 7.5a — Corpus Audit', 'HARD'),
    ('Tier 8 — MCP Bridge', 'Tier 7 — Full Durable Router Pipeline', 'HARD'),
    ('Tier 9 — Chroma/VDB', 'Tier 8 — MCP Bridge', 'HARD'),
    ('Tier 10 — CIS UI / Custom Display Views', 'Tier 9 — Chroma/VDB', 'HARD'),
]


def seed():
    conn = init_db()
    node_ids = {}
    inserted = 0
    skipped = 0
    for (pid, label, tier, seq, status, reason, role, mode) in NODES:
        nid, is_new = create_node(conn, pid, label, tier, seq,
                                  status=status, blocked_reason=reason,
                                  required_role=role, allowed_mode=mode)
        if nid:
            node_ids[label] = nid
            if is_new:
                inserted += 1
            else:
                skipped += 1
    print(f"Nodes: {inserted} inserted, {skipped} skipped (already exist)")

    dep_inserted = 0
    dep_skipped = 0
    for (node_label, depends_label, dtype) in DEPENDENCIES:
        nid = node_ids.get(node_label)
        did = node_ids.get(depends_label)
        if nid and did:
            if create_dependency(conn, nid, did, dtype):
                dep_inserted += 1
            else:
                dep_skipped += 1
    print(f"Dependencies: {dep_inserted} created, {dep_skipped} skipped")

    # NOTE: promote_unblocked() NOT called here. DEFERRED nodes are never auto-promoted.
    # Tested separately on a temp DB (see Step 6).
    conn.commit()
    conn.close()
    print("Seed complete.")


if __name__ == '__main__':
    seed()
