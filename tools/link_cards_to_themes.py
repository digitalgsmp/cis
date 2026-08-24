#!/usr/bin/env python3
"""Card-Theme Linker: Qwen connects every card to synthesis themes."""
import json, os, sys, time, urllib.request, sqlite3, re, glob

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"
CARD_DIR = '/mnt/projects/cis/cards/inbox'
SYNTH_DB = '/mnt/projects/cis/cards/synthesis.db'
LINK_DB = '/mnt/projects/cis/cards/card_theme_links.db'

SYSTEM_PROMPT = """You are connecting BUILD CARDS to SYNTHESIS THEMES. You must be precise and only link when the card's intent genuinely relates to the theme. Do NOT force connections.

For each card, output JSON:
{
  "card_id": "<filename>",
  "linked_themes": [
    {"theme": "<exact theme name>", "relevance": "direct|partial|none", "reason": "one sentence"}
  ]
}

Only include themes where relevance is "direct" or "partial". Do not include "none".
"""

def ask_qwen(msg, max_tok=1024):
    payload = json.dumps({
        'model': QWEN_MODEL,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': msg}
        ],
        'max_tokens': max_tok,
        'temperature': 0.1
    })
    req = urllib.request.Request(QWEN_URL, data=payload.encode(),
                                 headers={'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read())['choices'][0]['message']['content']
    except Exception as e:
        print(f"  QWEN ERROR: {e}", flush=True)
        return None

# Get top themes
con = sqlite3.connect(SYNTH_DB)
themes = con.execute(
    "SELECT theme, description FROM synthesis_themes GROUP BY LOWER(TRIM(theme)) ORDER BY COUNT(*) DESC LIMIT 100"
).fetchall()
con.close()

theme_list = "\n".join([f"- {t[0]}: {t[1][:100]}" for t in themes])

# Get cards
cards = glob.glob(f"{CARD_DIR}/*.md")
print(f"Themes: {len(themes)}, Cards: {len(cards)}", flush=True)

# Setup link DB
lcon = sqlite3.connect(LINK_DB)
lcon.executescript("""
    CREATE TABLE IF NOT EXISTS card_theme_links (
        id INTEGER PRIMARY KEY,
        card_id TEXT,
        theme TEXT,
        relevance TEXT,
        reason TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_card ON card_theme_links(card_id);
    CREATE INDEX IF NOT EXISTS idx_theme ON card_theme_links(theme);
""")
lcon.commit()

# Process each card
total_linked = 0
for i, card_path in enumerate(cards):
    card_id = os.path.basename(card_path)
    with open(card_path) as f:
        card_content = f.read()[:2000]

    prompt = f"""THEMES:
{theme_list}

CARD: {card_id}
CONTENT:
{card_content}

Link this card to the themes it genuinely relates to. Be strict — only link when there's clear relevance."""

    print(f"  Card {i+1}/{len(cards)}: {card_id[:50]}...", flush=True)
    raw = ask_qwen(prompt)

    if raw:
        try:
            result = json.loads(raw)
        except:
            m = re.search(r'\{[\s\S]*\}', raw)
            if m:
                try:
                    result = json.loads(m.group(0))
                except:
                    result = None
            else:
                result = None

        if result and 'linked_themes' in result:
            for link in result['linked_themes']:
                lcon.execute(
                    "INSERT INTO card_theme_links(card_id, theme, relevance, reason) VALUES(?,?,?,?)",
                    (card_id, link['theme'], link.get('relevance','partial'), link.get('reason',''))
                )
                total_linked += 1

    time.sleep(0.5)

lcon.commit()

# Summary
linked_cards = lcon.execute("SELECT COUNT(DISTINCT card_id) FROM card_theme_links").fetchone()[0]
print(f"\nLinked: {total_linked} connections across {linked_cards}/{len(cards)} cards", flush=True)

# Show top card-theme pairs
print("\nTop card-theme links:", flush=True)
for row in lcon.execute(
    "SELECT card_id, theme, relevance FROM card_theme_links ORDER BY card_id LIMIT 15"
).fetchall():
    print(f"  {row[0][:40]} → {row[1][:40]} ({row[2]})", flush=True)

lcon.close()
print(f"\nLink DB: {LINK_DB}", flush=True)
print("Query: sqlite3 cards/card_theme_links.db \"SELECT * FROM card_theme_links WHERE theme LIKE '%enforcement%'\"")
