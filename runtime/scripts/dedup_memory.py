#!/usr/bin/env python3
"""Deduplicate memory_records by (category, summary) keeping the oldest record."""
import sqlite3

conn = sqlite3.connect('/mnt/projects/cis/memory/cis_memory.db')
cur = conn.cursor()

# Find duplicates
cur.execute("""
    SELECT category, summary, COUNT(*) as cnt
    FROM memory_records
    GROUP BY category, summary
    HAVING cnt > 1
    ORDER BY cnt DESC
    LIMIT 10
""")
dups = cur.fetchall()
print(f"Top duplicate groups: {len(dups)}")
for cat, summary, cnt in dups:
    print(f"  [{cat}] x{cnt} \"{summary[:80]}\"")

# Remove exact duplicates keeping the oldest
cur.execute("""
    DELETE FROM memory_records WHERE record_id NOT IN (
        SELECT MIN(record_id) FROM memory_records GROUP BY category, summary
    )
""")
removed = cur.rowcount
conn.commit()

cur.execute('SELECT COUNT(*) FROM memory_records')
final = cur.fetchone()[0]
print(f"\nRemoved {removed} exact duplicates")
print(f"Records now: {final}")

conn.close()
