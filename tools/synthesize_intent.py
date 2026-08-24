#!/usr/bin/env python3
"""
synthesize_intent.py — Recursive multi-pass intent synthesis from session asks.

Feeds the 228 extracted asks (condensed session context) to Qwen in recursive
passes. Each pass builds understanding from previous passes. The question is NOT
"what did Eric ask for" — it's "what is Eric trying to accomplish across the
totality of his engagement with AI models?"

Input: cards/asks_all_profiles.jsonl (from mine_asks_sessions.py)
Output: cards/synthesis_output.json
"""

import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"
ASKS_PER_BATCH = 30  # ~12K chars per batch, leaves room for accumulated understanding

SYNTHESIS_SYSTEM = """You are analyzing the complete body of Eric's engagement with AI models over several months (May-August 2026). Eric is a non-coder with creative ideas who uses AI models to help him think, plan, and build systems.

CRITICAL: Do NOT extract tasks, requests, or action items. Instead, read across ALL the material and infer what Eric is fundamentally trying to accomplish. His goals are implicit in the totality of his engagement — the patterns across sessions, domains, projects, and time.

ERIC'S PROJECTS:
- CIS: A multi-agent pipeline where models review each other's work with containerized enforcement, a control plane portal, and a knowledge base. The goal is verified, aligned AI collaboration — not co-pilot assistance.
- SWA: A Social Work App for field workers — scheduling, progress notes, client intake, service provider management.
- WIASW: A creative production framework (Word/Image/Action/Sound/Web) for managing creative projects from idea through distribution.
- Card Factory: Extracting Eric's intentions from his knowledge base into structured briefing cards for frontier models.

WHAT TO LOOK FOR:
- Recurring frustrations that reveal what Eric keeps trying to do but can't
- Patterns across different sessions that point to the same underlying goal
- Ideas expressed in one domain that connect to needs in another
- What Eric returns to repeatedly across weeks and months
- The difference between surface-level requests and the deeper goal they serve

OUTPUT FORMAT (each pass):
{
  "pass": N,
  "new_insights": "<what this batch revealed that previous batches didn't>",
  "accumulated_understanding": "<compact synthesis of everything understood so far>",
  "key_themes": ["<recurring theme>", ...],
  "cross_domain_connections": "<how projects/domains connect to each other>",
  "eric_is_trying_to": "<one sentence: what is Eric fundamentally trying to accomplish?>",
  "unresolved": ["<what still needs more context?>", ...]
}

FINAL PASS: Add "final_synthesis" field with complete analysis."""


def query_qwen(system_prompt, user_msg, temperature=0.3, max_tokens=4096):
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        QWEN_URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    for attempt in range(3):
        try:
            resp = urllib.request.urlopen(req, timeout=180)
            return json.loads(resp.read())['choices'][0]['message']['content']
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                print(f"  Qwen error: {e}", file=sys.stderr, flush=True)
                return None


def parse_json(raw):
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def format_ask(ask):
    """Format one ask as a concise context entry."""
    return (
        f"[{ask.get('category','?')}] {ask.get('interpretation','')}\n"
        f"  Quotes: {'; '.join(ask.get('verbatim_quotes',[])[:2])}\n"
    )


def main():
    asks_file = 'cards/asks_all_profiles.jsonl'
    if not os.path.exists(asks_file):
        print(f"ERROR: {asks_file} not found. Run mine_asks_sessions.py first.")
        sys.exit(1)

    asks = []
    with open(asks_file) as f:
        for line in f:
            line = line.strip()
            if line:
                asks.append(json.loads(line))

    print(f"Loaded {len(asks)} asks from all profiles", flush=True)

    # Sort by DB + category for thematic grouping
    asks.sort(key=lambda a: (a.get('_source_db', ''), a.get('category', '')))

    # Batch
    batches = []
    for i in range(0, len(asks), ASKS_PER_BATCH):
        batch_asks = asks[i:i + ASKS_PER_BATCH]
        text = f"BATCH {len(batches)+1}: Sessions involving:\n\n"
        text += ''.join(format_ask(a) for a in batch_asks)
        batches.append(text)

    print(f"Split into {len(batches)} batches (~{ASKS_PER_BATCH} asks each)", flush=True)
    print(f"Estimated time: ~{len(batches) * 2} minutes\n", flush=True)

    all_results = []
    accumulated = ""

    for i, batch in enumerate(batches):
        print(f"{'='*60}", flush=True)
        print(f"PASS {i+1}/{len(batches)} ({len(batch)} chars)", flush=True)

        if i == 0:
            prompt = f"FIRST PASS. Read this material carefully:\n\n{batch}"
        elif i == len(batches) - 1:
            prompt = (
                f"FINAL PASS. Your accumulated understanding:\n\n{accumulated}\n\n"
                f"Final material:\n\n{batch}\n\n"
                f"Produce the complete final_synthesis."
            )
        else:
            prompt = (
                f"Your accumulated understanding so far:\n\n{accumulated}\n\n"
                f"NEW material to incorporate:\n\n{batch}"
            )

        raw = query_qwen(SYNTHESIS_SYSTEM, prompt, max_tokens=4096)
        result = parse_json(raw)

        if result:
            all_results.append(result)
            accumulated = result.get('accumulated_understanding', '')
            print(f"  Themes: {result.get('key_themes', [])}", flush=True)
            print(f"  Eric is trying to: {result.get('eric_is_trying_to', '')[:150]}", flush=True)

            os.makedirs('cards', exist_ok=True)
            with open('cards/synthesis_output.json', 'w') as f:
                json.dump({
                    'passes': all_results,
                    'final': result if i == len(batches) - 1 else None,
                    'total_asks': len(asks),
                    'total_passes': len(batches),
                }, f, indent=2)
        else:
            print(f"  FAILED to get response", flush=True)

        if i < len(batches) - 1:
            time.sleep(1)

    print(f"\n{'='*60}", flush=True)
    print("DONE", flush=True)
    if all_results:
        final = all_results[-1]
        print(f"\nEric is trying to: {final.get('eric_is_trying_to', '')}", flush=True)
        fs = final.get('final_synthesis', {})
        if fs:
            print(f"Core mission: {fs.get('core_mission', '')[:200]}", flush=True)
            print(f"Blockers: {fs.get('blockers', [])}", flush=True)
    print(f"\nOutput: cards/synthesis_output.json", flush=True)


if __name__ == '__main__':
    main()
