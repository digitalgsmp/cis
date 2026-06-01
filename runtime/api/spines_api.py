#!/usr/bin/env python3
"""Flask blueprint: /api/spines — serve knowledge spines as React Flow-compatible nodes + edges."""

import sqlite3
import json
from pathlib import Path
from flask import Blueprint, jsonify, request

spines_bp = Blueprint("spines", __name__)

DB_PATH = Path("/mnt/projects/cis/memory/cis_memory.db")

# ── Color scheme for spine domains ─────────────────────────────────────────────

DOMAIN_COLORS = {
    "cis":       {"bg": "#0a0d1a", "border": "#4a9eff", "text": "#ffffff"},
    "swa":       {"bg": "#0a1a0e", "border": "#3dffa0", "text": "#ffffff"},
    "unknown":   {"bg": "#101218", "border": "#7a8299", "text": "#7a8299"},
}

STATUS_COLORS = {
    "ingested":  {"bg": "#101218", "border": "#7a8299", "text": "#7a8299"},
    "active":    {"bg": "#0a1a2e", "border": "#4a9eff", "text": "#ffffff"},
    "done":      {"bg": "#0a1a0e", "border": "#3dffa0", "text": "#ffffff"},
}

SUB_DOMAIN_COLORS = {
    "transcripts_claude": {"border": "#4a9eff"},
    "vision":             {"border": "#a855f7"},
    "vision_docs":        {"border": "#3dffa0"},
}


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@spines_bp.route("/api/spines")
def list_spines():
    """Return all knowledge spines as React Flow nodes + edges."""
    db = get_db()
    try:
        # ── Query spines ──────────────────────────────────────────────
        rows = db.execute("""
            SELECT spine_id, domain, sub_domain, subject, source_type, 
                   file_path, node_count, status, ingested_at
            FROM knowledge_spines
            ORDER BY domain, sub_domain, ingested_at DESC
        """).fetchall()

        nodes = []
        edges = []
        y_pos = 0
        prev_spine_id = None

        for row in rows:
            spine_id = row["spine_id"]
            domain = row["domain"]
            sub_domain = row["sub_domain"]
            status = row["status"]

            colors = DOMAIN_COLORS.get(domain, DOMAIN_COLORS["unknown"])
            sub_colors = SUB_DOMAIN_COLORS.get(sub_domain, {"border": "#ffffff"})

            # Truncate subject for node display
            label = row["subject"]
            if label.startswith("Extraction Analysis: "):
                label = label[21:]
            if len(label) > 45:
                label = label[:42] + "..."

            # Spine-level node
            spine_node = {
                "id": spine_id,
                "type": "default",
                "position": {"x": 250, "y": y_pos},
                "data": {
                    "label": label,
                    "narrative": f"Domain: {domain}/{sub_domain}\nStatus: {status}\nNodes: {row['node_count']}\nFile: {row['file_path']}\nIngested: {row['ingested_at']}",
                    "status": status,
                    "domain": domain,
                    "node_count": row["node_count"],
                    "spine_id": spine_id,
                },
                "style": {
                    "background": colors["bg"],
                    "border": f"2px solid {sub_colors['border']}",
                    "color": colors["text"],
                    "width": 240,
                    "fontSize": 10,
                    "fontWeight": 600,
                },
            }
            nodes.append(spine_node)

            # Edge to previous spine in same domain
            if prev_spine_id and _same_group(prev_spine_id, spine_id, db):
                edges.append({
                    "id": f"e-{prev_spine_id}-{spine_id}",
                    "source": prev_spine_id,
                    "target": spine_id,
                    "style": {"stroke": sub_colors["border"], "opacity": 0.3},
                    "markerEnd": {"type": "arrowclosed", "color": sub_colors["border"]},
                })

            prev_spine_id = spine_id
            y_pos += 70

        return jsonify({"nodes": nodes, "edges": edges})

    finally:
        db.close()


@spines_bp.route("/api/spines/<spine_id>/nodes")
def spine_nodes(spine_id):
    """Return the discovery nodes for a specific spine."""
    db = get_db()
    try:
        spine = db.execute("SELECT * FROM knowledge_spines WHERE spine_id = ?", (spine_id,)).fetchone()
        if not spine:
            return jsonify({"error": "Spine not found"}), 404

        rows = db.execute("""
            SELECT node_id, title, depth, path, created_at
            FROM spine_nodes
            WHERE spine_id = ?
            ORDER BY node_id
        """, (spine_id,)).fetchall()

        # Build a richer response with position data for React Flow
        nodes = []
        y_pos = 0
        for row in rows:
            nodes.append({
                "id": row["node_id"],
                "spine_id": spine_id,
                "title": row["title"],
                "depth": row["depth"],
                "path": row["path"],
                "position": {"x": 250, "y": y_pos},
            })
            y_pos += 60

        return jsonify({
            "spine": dict(spine),
            "nodes": nodes,
        })
    finally:
        db.close()


@spines_bp.route("/api/spines/by-sub-domain")
def spines_by_sub_domain():
    """Return spines for a specific sub_domain (lightweight, no discovery nodes)."""
    domain = request.args.get("domain", "").upper()
    sub_domain = request.args.get("sub_domain", "")
    if not domain or not sub_domain:
        return jsonify({"error": "domain and sub_domain required"}), 400

    db = get_db()
    try:
        rows = db.execute("""
            SELECT spine_id, domain, sub_domain, subject, node_count, status
            FROM knowledge_spines
            WHERE domain = ? AND sub_domain = ?
            ORDER BY subject
        """, (domain, sub_domain)).fetchall()

        return jsonify({
            "success": True,
            "spines": [dict(r) for r in rows],
        })
    finally:
        db.close()


@spines_bp.route("/api/spines/domains")
def spine_domains():
    """Return summary counts grouped by domain."""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT domain, sub_domain, COUNT(*) as spines, SUM(node_count) as total_nodes
            FROM knowledge_spines
            GROUP BY domain, sub_domain
            ORDER BY domain, sub_domain
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


def _same_group(id1, id2, db):
    """Check if two spines share the same domain+sub_domain."""
    r1 = db.execute("SELECT domain, sub_domain FROM knowledge_spines WHERE spine_id = ?", (id1,)).fetchone()
    r2 = db.execute("SELECT domain, sub_domain FROM knowledge_spines WHERE spine_id = ?", (id2,)).fetchone()
    if r1 and r2:
        return r1["domain"] == r2["domain"] and r1["sub_domain"] == r2["sub_domain"]
    return False
