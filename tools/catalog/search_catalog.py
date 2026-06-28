#!/usr/bin/env python3
"""
Search the Eric intention catalog.

Usage:
  python3 search_catalog.py "pipeline automation"                    # FTS5 search
  python3 search_catalog.py --domain cis --status confirmed          # Filter by domain + status
  python3 search_catalog.py --project CIS --speaker eric_verbatim    # Filter by project
  python3 search_catalog.py --id 1247                                # Get specific intention
  python3 search_catalog.py --stats                                  # Summary statistics
  python3 search_catalog.py --export confirmed.json                  # Export confirmed to JSON

Used by pipeline scripts to measure alignment:
  Drafter queries:  --domain cis --status confirmed
  Reviewer queries: --id <intention_id>  (verify spec matches intention)
"""

import json
import sqlite3
import sys
import os

CATALOG = "/mnt/cache/catalog/eric_catalog.db"

def search(query=None, domain=None, project=None, speaker=None, status=None, 
           item_id=None, limit=50, export_file=None):
    
    if not os.path.exists(CATALOG):
        print(f"ERROR: Catalog not found: {CATALOG}")
        sys.exit(1)
    
    conn = sqlite3.connect(CATALOG)
    
    if item_id:
        row = conn.execute(
            "SELECT id, source_file, project, speaker, domain, status, raw_text, revised_text, eric_comment, char_length FROM eric_catalog WHERE id = ?",
            (item_id,)
        ).fetchone()
        if row:
            print(f"=== Intention #{row[0]} ===")
            print(f"Source: {row[1]}")
            print(f"Project: {row[2]} | Speaker: {row[3]} | Domain: {row[4]} | Status: {row[5]}")
            print(f"---")
            print(row[7] or row[6])  # revised_text or raw_text
            if row[8]:
                print(f"--- Eric's comment ---")
                print(row[8])
        else:
            print(f"No intention found with id={item_id}")
        conn.close()
        return
    
    # Build query
    if query:
        # FTS5 search
        rows = conn.execute(
            """SELECT e.id, e.source_file, e.project, e.speaker, e.domain, e.status, 
                      e.raw_text, e.revised_text, e.eric_comment, e.char_length
               FROM eric_catalog e
               JOIN eric_catalog_fts f ON e.id = f.rowid
               WHERE eric_catalog_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit)
        ).fetchall()
    else:
        # Filtered query
        conditions = []
        params = []
        if domain:
            conditions.append("domain LIKE ?")
            params.append(f"%{domain}%")
        if project:
            conditions.append("project = ?")
            params.append(project)
        if speaker:
            conditions.append("speaker = ?")
            params.append(speaker)
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where = " AND ".join(conditions) if conditions else "1=1"
        rows = conn.execute(
            f"""SELECT id, source_file, project, speaker, domain, status,
                       raw_text, revised_text, eric_comment, char_length
                FROM eric_catalog
                WHERE {where}
                ORDER BY id
                LIMIT ?""",
            params + [limit]
        ).fetchall()
    
    if export_file:
        # Export to JSON for pipeline consumption
        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "source_file": r[1],
                "project": r[2],
                "speaker": r[3],
                "domain": r[4],
                "status": r[5],
                "text": r[7] or r[6],
                "comment": r[8]
            })
        with open(export_file, 'w') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"Exported {len(items)} intentions to {export_file}")
    else:
        for r in rows:
            text = (r[7] or r[6])[:200].replace('\n', ' ')
            print(f"[{r[0]}] [{r[5] or 'unevaluated'}] {r[4]} | {text}...")
        
        if len(rows) == limit:
            print(f"\n... showing first {limit} results. Use --limit N for more.")
    
    conn.close()

def stats():
    conn = sqlite3.connect(CATALOG)
    
    print("=== ERIC CATALOG STATISTICS ===\n")
    
    # Total
    total = conn.execute("SELECT COUNT(*) FROM eric_catalog").fetchone()[0]
    print(f"Total fragments: {total}")
    
    # By speaker
    print("\n--- By Speaker ---")
    for row in conn.execute("SELECT speaker, COUNT(*) FROM eric_catalog GROUP BY speaker ORDER BY COUNT(*) DESC"):
        print(f"  {row[0]}: {row[1]}")
    
    # By status (for Eric's fragments)
    print("\n--- Eric's Intentions by Status ---")
    for row in conn.execute("""SELECT COALESCE(status,'unevaluated'), COUNT(*) 
                                FROM eric_catalog 
                                WHERE speaker IN ('eric_verbatim','eric_framing') 
                                GROUP BY status"""):
        print(f"  {row[0]}: {row[1]}")
    
    # By domain
    print("\n--- Eric's Intentions by Domain ---")
    domains = {}
    for row in conn.execute("SELECT domain FROM eric_catalog WHERE speaker IN ('eric_verbatim','eric_framing')"):
        for d in row[0].split(','):
            d = d.strip()
            domains[d] = domains.get(d, 0) + 1
    for d, c in sorted(domains.items(), key=lambda x: -x[1]):
        print(f"  {d}: {c}")
    
    # By project
    print("\n--- Eric's Intentions by Project ---")
    for row in conn.execute("""SELECT project, COUNT(*) 
                                FROM eric_catalog 
                                WHERE speaker IN ('eric_verbatim','eric_framing') 
                                GROUP BY project ORDER BY COUNT(*) DESC"""):
        print(f"  {row[0]}: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Search Eric intention catalog")
    parser.add_argument("query", nargs="?", help="FTS5 search query")
    parser.add_argument("--domain", help="Filter by domain (cis, swa, wias, shared)")
    parser.add_argument("--project", help="Filter by project (CIS, SWA, WIAS, ARCHIVE, SESSIONS)")
    parser.add_argument("--speaker", help="Filter by speaker")
    parser.add_argument("--status", help="Filter by status (confirmed, rejected, revised, unevaluated)")
    parser.add_argument("--id", type=int, help="Get specific intention by ID")
    parser.add_argument("--limit", type=int, default=50, help="Max results")
    parser.add_argument("--export", help="Export results to JSON file")
    parser.add_argument("--stats", action="store_true", help="Show catalog statistics")
    parser.add_argument("--catalog", default=CATALOG, help="Catalog database path")
    
    args = parser.parse_args()
    CATALOG = args.catalog
    
    if args.stats:
        stats()
    elif not args.query and not args.domain and not args.project and not args.speaker and not args.status and not args.id:
        stats()
    else:
        search(
            query=args.query,
            domain=args.domain,
            project=args.project,
            speaker=args.speaker,
            status=args.status,
            item_id=args.id,
            limit=args.limit,
            export_file=args.export
        )
