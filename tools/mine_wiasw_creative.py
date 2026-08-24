#!/usr/bin/env python3
"""Targeted creative/WIASW mining pass. Feeds all WIASW-adjacent content to Qwen."""
import json, os, sys, time, urllib.request

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"
INPUT = '/mnt/projects/cis/cards/synthesis_input.jsonl'
OUT = '/mnt/projects/cis/cards/wiasw_creative_analysis.json'

SYSTEM_PROMPT = """You are analyzing Eric's creative work and the WIASW framework. 

CONTEXT FROM ERIC:
- WIASW = "What I Am Seeing Within" — the last W is for "Web" (code + distribution)
- WIASW is NOT a separate project — its concepts are meant to be built INTO CIS
- CIS is the pipeline; WIASW is the creative methodology that CIS should enable
- Eric is a non-coder with creative background: music, art, writing, animation
- He has "hundreds of ideas for dozens of genre topics" — t-shirts, books, dreams→animations, songs
- Goal: use the card factory to identify ideas from his archive, generate cards, categorize by product type and creative domain

TASK: Find all references to creative work, WIASW, idea generation, music, art, writing, animation, design, and the card factory's role in processing creative material.

Output JSON:
{
  "creative_domains": [{"domain":"music|art|writing|animation|design|other","description":"...","evidence":["quote"]}],
  "wiasw_role": "<what WIASW actually is and how it relates to CIS>",
  "card_factory_creative_role": "<how the card factory should process creative ideas>",
  "creative_blocks": ["what prevents Eric from executing on creative ideas"],
  "cis_as_creative_enabler": "<how CIS enables creative production>"
}"""


def ask_qwen(msg, max_tok=2048):
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
        resp = urllib.request.urlopen(req, timeout=300)
        return json.loads(resp.read())['choices'][0]['message']['content']
    except Exception as e:
        print(f"  QWEN ERROR: {e}", flush=True)
        return None


# Collect creative/WIASW entries
entries = []
with open(INPUT) as f:
    for line in f:
        try:
            e = json.loads(line)
            content = json.dumps(e).lower()
            if any(kw in content for kw in ['wiasw', 'creative', 'music', 'song', 'art', 'animation',
                                              'writing', 'design', 't-shirt', 'book', 'dream',
                                              'what i am seeing', 'idea bank', 'archive drive',
                                              'card factory', 'taxonomy', 'genre']):
                entries.append(e)
        except:
            pass

print(f"Creative entries: {len(entries)}", flush=True)

# Build batches
batches = []
cur, chars = [], 0
for e in entries:
    text = json.dumps(e)[:2000]
    if chars + len(text) > 2500 and cur:
        batches.append('\n---\n'.join(cur))
        cur, chars = [], 0
    cur.append(text)
    chars += len(text)
if cur:
    batches.append('\n---\n'.join(cur))

print(f"Batches: {len(batches)}", flush=True)

# Process
import re
all_results = []
for i, batch in enumerate(batches[:10]):  # Max 10 batches to avoid long runs
    print(f"Batch {i+1}/{min(len(batches),10)}", flush=True)
    raw = ask_qwen(batch)
    if raw:
        # Try to parse JSON
        try:
            result = json.loads(raw)
        except:
            m = re.search(r'\{[\s\S]*\}', raw)
            if m:
                try:
                    result = json.loads(m.group(0))
                except:
                    result = {'raw': raw}
            else:
                result = {'raw': raw}
        all_results.append(result)
        # Print domains found
        if 'creative_domains' in result:
            print(f"  Domains: {[d.get('domain','') for d in result['creative_domains']]}", flush=True)
    time.sleep(1)

with open(OUT, 'w') as f:
    json.dump(all_results, f, indent=2)

print(f"\nResults: {OUT}", flush=True)

# Also seed into synthesis.db
synth_db = 'cards/synthesis.db'
if os.path.exists(synth_db):
    import sqlite3
    con = sqlite3.connect(synth_db)
    for r in all_results:
        if 'wiasw_role' in r:
            con.execute(
                "INSERT INTO synthesis_themes(pass_id,theme,description,confidence) VALUES(?,?,?,?)",
                (0, 'WIASW creative framework', r.get('wiasw_role','')[:500], 'confirmed')
            )
        if 'creative_domains' in r:
            for d in r['creative_domains']:
                con.execute(
                    "INSERT INTO synthesis_themes(pass_id,theme,description,confidence) VALUES(?,?,?,?)",
                    (0, f"creative:{d.get('domain','')}", d.get('description','')[:500], 'confirmed')
                )
    con.commit()
    con.close()
    print("Seeded WIASW/creative themes into synthesis.db", flush=True)
