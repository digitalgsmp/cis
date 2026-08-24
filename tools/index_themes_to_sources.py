#!/usr/bin/env python3
"""
Pass 3: KB Indexing — bidirectional link between synthesis themes and source material.

Reads synthesis.db evidence table and creates reverse indexes:
  - theme_index: for each theme, list all supporting sources
  - source_index: for each source, list which themes it supports
  - Also indexes synthesis_themes by domain and confidence
"""
import json, os, re, sqlite3, sys

SYNTH_DB = 'cards/synthesis.db'
INDEX_DB = 'cards/index.db'


def create_index_db():
    con = sqlite3.connect(INDEX_DB)
    con.executescript("""
        -- Theme → Sources mapping
        CREATE TABLE IF NOT EXISTS theme_sources (
            id INTEGER PRIMARY KEY,
            theme TEXT NOT NULL,
            description TEXT,
            confidence TEXT,
            source TEXT NOT NULL,        -- '[prime]', '[v4pro:session_id]', '[kb_human:source]', '[file:path]'
            quote TEXT,                   -- Eric's exact words
            pass_id INTEGER,
            domain TEXT,                  -- inferred from connections table
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_theme ON theme_sources(theme);
        CREATE INDEX IF NOT EXISTS idx_source ON theme_sources(source);

        -- Source → Themes mapping (reverse)
        CREATE TABLE IF NOT EXISTS source_themes (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            source_type TEXT,             -- 'session', 'kb_human', 'kb_chatgpt', 'cis_file', etc.
            themes TEXT,                   -- JSON array of theme names
            theme_count INTEGER,
            top_domain TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_source_themes ON source_themes(source);

        -- Domain summary
        CREATE TABLE IF NOT EXISTS domain_summary (
            id INTEGER PRIMARY KEY,
            domain TEXT UNIQUE,
            theme_count INTEGER,
            source_count INTEGER,
            top_themes TEXT,              -- JSON array
            accumulated_understanding TEXT
        );
    """)
    con.commit()
    return con


def index_from_synthesis():
    """Read synthesis.db and build the reverse indexes."""
    if not os.path.exists(SYNTH_DB):
        print(f"Synthesis DB not found: {SYNTH_DB}", flush=True)
        return

    syn_con = sqlite3.connect(SYNTH_DB)
    syn_con.row_factory = sqlite3.Row
    idx_con = create_index_db()

    # 1. Index themes from evidence
    evidence_rows = syn_con.execute(
        "SELECT theme, quote, source, pass_id FROM synthesis_evidence ORDER BY pass_id"
    ).fetchall()

    for row in evidence_rows:
        idx_con.execute(
            "INSERT INTO theme_sources(theme, quote, source, pass_id) VALUES(?,?,?,?)",
            (row['theme'], row['quote'], row['source'], row['pass_id'])
        )

    print(f"  Evidence rows: {len(evidence_rows)}", flush=True)

    # 2. Try to infer domain from connections table
    connections = syn_con.execute(
        "SELECT source_domain, target_domain, connection_type, description FROM synthesis_connections"
    ).fetchall()

    # Build domain → themes map from connections
    domain_themes = {}
    for c in connections:
        for d in [c['source_domain'], c['target_domain']]:
            if d:
                domain_themes[d] = domain_themes.get(d, 0) + 1

    for domain, count in domain_themes.items():
        idx_con.execute(
            "INSERT OR REPLACE INTO domain_summary(domain, theme_count) VALUES(?,?)",
            (domain, count)
        )

    print(f"  Domains: {len(domain_themes)}", flush=True)

    # 3. Build source → themes reverse index
    source_rows = syn_con.execute(
        "SELECT source, theme FROM synthesis_evidence ORDER BY source"
    ).fetchall()

    source_map = {}
    for row in source_rows:
        src = row['source']
        theme = row['theme']
        if src not in source_map:
            source_map[src] = {'themes': [], 'type': 'unknown'}
        source_map[src]['themes'].append(theme)
        # Infer type from source prefix
        if src.startswith('[prime') or src.startswith('[v4'):
            source_map[src]['type'] = 'session'
        elif src.startswith('[kb_human'):
            source_map[src]['type'] = 'kb_human'
        elif src.startswith('[kb_chatgpt'):
            source_map[src]['type'] = 'kb_chatgpt'
        elif src.startswith('[file:'):
            source_map[src]['type'] = 'cis_file'

    for src, data in source_map.items():
        unique_themes = list(set(data['themes']))
        idx_con.execute(
            "INSERT INTO source_themes(source, source_type, themes, theme_count) VALUES(?,?,?,?)",
            (src, data['type'], json.dumps(unique_themes), len(unique_themes))
        )

    print(f"  Source entries: {len(source_map)}", flush=True)

    # 4. Copy theme descriptions for searchability
    theme_rows = syn_con.execute(
        "SELECT theme, description, confidence FROM synthesis_themes"
    ).fetchall()

    for row in theme_rows:
        # Update theme_sources with descriptions where theme matches
        idx_con.execute(
            "UPDATE theme_sources SET description=?, confidence=? WHERE theme=?",
            (row['description'], row['confidence'], row['theme'])
        )

    print(f"  Theme descriptions: {len(theme_rows)}", flush=True)

    # 5. Latest accumulated understanding
    acc_row = syn_con.execute(
        "SELECT understanding, eric_is_building_toward FROM synthesis_accumulated ORDER BY pass_id DESC LIMIT 1"
    ).fetchone()

    idx_con.commit()

    # Print summary
    print("\n=== INDEX SUMMARY ===", flush=True)
    theme_count = idx_con.execute("SELECT COUNT(DISTINCT theme) FROM theme_sources").fetchone()[0]
    source_count = idx_con.execute("SELECT COUNT(*) FROM source_themes").fetchone()[0]
    print(f"Unique themes: {theme_count}", flush=True)
    print(f"Unique sources: {source_count}", flush=True)

    # Top themes by evidence count
    top = idx_con.execute(
        "SELECT theme, COUNT(*) as c FROM theme_sources GROUP BY theme ORDER BY c DESC LIMIT 10"
    ).fetchall()
    print("\nTop themes:", flush=True)
    for t, c in top:
        print(f"  {t}: {c} sources", flush=True)

    # Top domains
    top_domains = idx_con.execute(
        "SELECT domain, theme_count FROM domain_summary ORDER BY theme_count DESC LIMIT 5"
    ).fetchall()
    print("\nTop domains:", flush=True)
    for d, c in top_domains:
        print(f"  {d}: {c}", flush=True)

    idx_con.close()
    syn_con.close()

    print(f"\nIndex DB: {INDEX_DB}", flush=True)
    print("\nQuery examples:")
    print('  sqlite3 cards/index.db "SELECT quote FROM theme_sources WHERE theme LIKE \'%enforcement%\' LIMIT 5"')
    print('  sqlite3 cards/index.db "SELECT themes FROM source_themes WHERE source LIKE \'%session_id%\'"')
    print('  sqlite3 cards/index.db "SELECT theme, COUNT(*) as cnt FROM theme_sources GROUP BY theme ORDER BY cnt DESC"')
    print('  sqlite3 cards/index.db "SELECT * FROM domain_summary"')


if __name__ == '__main__':
    index_from_synthesis()
