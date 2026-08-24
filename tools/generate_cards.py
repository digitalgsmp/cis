#!/usr/bin/env python3
"""
generate_cards.py — Convert extracted asks into BUILD CARDS using GENERATOR_PROMPT.txt.

Reads asks JSONL (from mine_asks_sessions.py), feeds each ask to Qwen with the
card generation prompt, writes output to cards/inbox/, then validates with card_gate.py.

Usage:
  python3 tools/generate_cards.py --asks cards/asks_sessions.jsonl --out-dir cards/inbox/
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"

# Load generator prompt
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
GEN_PROMPT = open(os.path.join(PROJECT_DIR, 'cards', 'GENERATOR_PROMPT.txt')).read()


def slugify(text):
    """Create a short slug from text."""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:40]


def generate_card(ask, card_num):
    """Feed an ask through Qwen with the card generator prompt."""
    # Build input in the format the generator expects
    # The generator expects: id, date, project, text
    quotes = ask.get('verbatim_quotes', [])
    interpretation = ask.get('interpretation', '')
    category = ask.get('category', 'cis')
    session_id = ask.get('session_id', 'unknown')
    date = ask.get('date', '')
    agent_context = ask.get('agent_context', '')

    # Construct a message that captures Eric's ask with context
    text = f"Eric's ask (from session {session_id}):\n"
    for q in quotes:
        text += f'"{q}"\n'
    if interpretation:
        text += f"\nInterpretation: {interpretation}"
    if agent_context:
        text += f"\nAgent context: {agent_context}"

    ask_input = json.dumps({
        "id": session_id,
        "date": date,
        "project": category,
        "text": text,
    })

    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": GEN_PROMPT},
            {"role": "user", "content": ask_input},
        ],
        "max_tokens": 1024,
        "temperature": 0.1,
    }

    req = urllib.request.Request(
        QWEN_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        body = json.loads(resp.read())
        return body['choices'][0]['message']['content']
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr, flush=True)
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--asks', required=True, help='JSONL file of extracted asks')
    ap.add_argument('--out-dir', default='cards/inbox')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()

    # Load asks
    asks = []
    with open(a.asks) as f:
        for line in f:
            line = line.strip()
            if line:
                asks.append(json.loads(line))

    print(f"Loaded {len(asks)} asks from {a.asks}", flush=True)
    if not asks:
        print("No asks to process.")
        return

    if a.limit:
        asks = asks[:a.limit]

    if a.dry_run:
        print(f"\nWould generate {len(asks)} cards to {a.out_dir}/", flush=True)
        print("\n--- SAMPLE ASKS ---", flush=True)
        for i, ask in enumerate(asks[:5]):
            print(f"\nAsk {i+1}: [{ask.get('category', '?')}] {ask.get('interpretation', '')[:100]}", flush=True)
            for q in ask.get('verbatim_quotes', []):
                print(f'  "{q[:120]}..."' if len(q) > 120 else f'  "{q}"', flush=True)
        return

    os.makedirs(a.out_dir, exist_ok=True)

    generated = 0
    skipped = 0
    errors = 0

    for i, ask in enumerate(asks):
        slug = slugify(ask.get('interpretation', ''))
        card_name = f"ask-{i+1:03d}-{slug}.md" if slug else f"ask-{i+1:03d}.md"
        card_path = os.path.join(a.out_dir, card_name)

        print(f"\nCard {i+1}/{len(asks)}: {ask.get('category', '?')} — {ask.get('interpretation', '')[:60]}", flush=True)

        raw = generate_card(ask, i + 1)

        if raw is None:
            errors += 1
            continue

        if raw.strip() == 'NO_CARD':
            print(f"  → NO_CARD (no direct ask)", flush=True)
            skipped += 1
            continue

        # Write card
        with open(card_path, 'w') as f:
            f.write(raw + '\n')
        generated += 1
        print(f"  → {card_name}", flush=True)

        # Validate
        result = subprocess.run(
            ['python3', os.path.join(PROJECT_DIR, 'tools', 'card_gate.py'),
             '--db', os.path.join(PROJECT_DIR, 'data', 'cis_memory.db'),
             card_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            print(f"  ✓ PASS", flush=True)
        else:
            print(f"  ✗ FAIL: {result.stdout.strip()[:100]} {result.stderr.strip()[:100]}", flush=True)

        if i < len(asks) - 1:
            time.sleep(0.3)

    print(f"\n{'='*60}", flush=True)
    print(f"DONE: {generated} cards generated, {skipped} skipped, {errors} errors", flush=True)
    print(f"Output: {a.out_dir}/", flush=True)


if __name__ == '__main__':
    main()
