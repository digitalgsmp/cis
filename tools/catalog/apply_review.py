#!/usr/bin/env python3
"""
Apply Eric's review decisions from the batch review form to eric_catalog.db.

Usage:
  python3 apply_review.py cis_review_decisions.json [--catalog /path/to/eric_catalog.db]

The review form exports cis_review_decisions.json when Eric clicks "Save All Changes".
This script reads that file and updates the catalog database with:
  - status: confirmed / rejected / revised
  - revised_text: Eric's clarified text
  - eric_comment: Eric's notes
"""

import json
import sqlite3
import sys
import os
from datetime import datetime

def apply_review(decisions_file, catalog_path):
    if not os.path.exists(decisions_file):
        print(f"ERROR: Decisions file not found: {decisions_file}")
        sys.exit(1)
    
    if not os.path.exists(catalog_path):
        print(f"ERROR: Catalog database not found: {catalog_path}")
        sys.exit(1)
    
    with open(decisions_file, 'r') as f:
        decisions = json.load(f)
    
    conn = sqlite3.connect(catalog_path)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Ensure columns exist
    try:
        conn.execute("ALTER TABLE eric_catalog ADD COLUMN status TEXT DEFAULT 'unevaluated'")
    except sqlite3.OperationalError:
        pass  # column already exists
    
    try:
        conn.execute("ALTER TABLE eric_catalog ADD COLUMN eric_comment TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE eric_catalog ADD COLUMN revised_text TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    stats = {"confirmed": 0, "rejected": 0, "revised": 0, "commented": 0, "errors": 0}
    
    for id_str, decision in decisions.items():
        try:
            item_id = int(id_str)
        except ValueError:
            stats["errors"] += 1
            continue
        
        updates = []
        params = []
        
        if 'status' in decision and decision['status']:
            updates.append("status = ?")
            params.append(decision['status'])
            stats[decision['status']] = stats.get(decision['status'], 0) + 1
        
        if 'revised_text' in decision and decision['revised_text']:
            updates.append("revised_text = ?")
            params.append(decision['revised_text'])
        
        if 'eric_comment' in decision and decision['eric_comment']:
            updates.append("eric_comment = ?")
            params.append(decision['eric_comment'])
            stats["commented"] += 1
        
        if updates:
            params.append(item_id)
            conn.execute(
                f"UPDATE eric_catalog SET {', '.join(updates)} WHERE id = ?",
                params
            )
    
    conn.commit()
    
    # Summary
    print("=== REVIEW APPLIED ===")
    for k, v in stats.items():
        if v > 0:
            print(f"  {k}: {v}")
    
    # Status breakdown
    rows = conn.execute(
        "SELECT status, COUNT(*) FROM eric_catalog WHERE speaker IN ('eric_verbatim','eric_framing') GROUP BY status"
    ).fetchall()
    print("\n=== CURRENT CATALOG STATUS ===")
    for status, count in rows:
        print(f"  {status or 'unevaluated'}: {count}")
    
    conn.close()
    print(f"\nCatalog updated: {catalog_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 apply_review.py <decisions.json> [--catalog path]")
        sys.exit(1)
    
    catalog = "/mnt/cache/catalog/eric_catalog.db"
    args = sys.argv[1:]
    if "--catalog" in args:
        idx = args.index("--catalog")
        catalog = args[idx + 1]
        args.pop(idx)
        args.pop(idx)
    
    decisions_file = args[0]
    apply_review(decisions_file, catalog)
