#!/usr/bin/env python3
"""
generate_intention_cards.py — Convert extracted session asks into INTENTION CARDS.

Unlike generate_cards.py (which only captures literal "build this" tasks),
this generates cards that capture the FULL INTENTION behind each exchange:
what Eric was trying to accomplish, how it connects to the CIS mission,
and what frontier models (Claude, ChatGPT) need to know.

Each card answers: "What was Eric's intention in this exchange, and why does it matter?"

Usage:
  python3 tools/generate_intention_cards.py --asks cards/asks_sessions.jsonl --out-dir cards/intentions/
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"

SYSTEM_PROMPT = """You are an INTENTION ANALYST for Eric, a non-coder building a system called CIS (Control and Integration System).

CIS MISSION: Build a multi-agent pipeline system where AI models review each other's work, validate against Eric's documented intentions, and produce verified builds. The system uses containerized enforcement, a control plane portal, a knowledge base of all past interactions, and dual reviewers (different training data, different blind spots). Eric is the conductor — he routes between models manually, making decisions after seeing independent analysis.

YOUR JOB: Read a session exchange where Eric interacted with an AI agent. Determine Eric's INTENTION — what was he trying to accomplish, and how does it connect to the broader CIS project?

An intention is NOT just a build request. It can be:
- Trying to understand something to make a decision
- Validating an approach before committing to it
- Correcting the system's direction when it drifts
- Designing a component as part of a larger goal
- Diagnosing a blocker that prevents progress
- Establishing a process or workflow
- Rejecting an approach that doesn't align with the mission
- Expressing frustration about a recurring problem that needs systemic solution
- Testing whether something works as part of a larger validation chain

The KEY QUESTION: If a frontier model (Claude, ChatGPT) needs to understand what Eric is building and why, what does THIS exchange reveal about his intent, priorities, and direction?

Output a JSON object for each distinct intention found:
{
  "intention": "<one clear sentence: what was Eric trying to accomplish in this exchange?>",
  "mission_connection": "<how does this connect to the broader CIS project mission?>",
  "what_was_learned": "<what decision, understanding, or outcome came from this exchange?>",
  "relevance_to_frontier_model": "<why would Claude/ChatGPT need to know this when working on CIS?>",
  "category": "<cis|portal|container|knowledge-base|governance|infrastructure|swa|creative>",
  "verbatim_quotes": ["<Eric's exact words that reveal his intent>"],
  "session_id": "<session id>",
  "date": "<date>"
}

Return ONLY a JSON array. One object per distinct intention in this session.

CRITICAL: Do NOT reduce Eric's intent to "build X." Capture WHY he wanted it, what problem it solves, how it fits into the bigger picture. If he was frustrated, capture what the frustration reveals about his priorities. If he was validating, capture what he was validating against. If he was course-correcting, capture what direction he was correcting toward.

Every exchange is a piece of the mission. Your job is to show how this piece connects to the whole."""


def slugify(text):
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:50]


def query_qwen(ask):
    """Send an ask to Qwen for intention analysis."""
    # Format the ask for Qwen
    quotes = ask.get('verbatim_quotes', [])
    interpretation = ask.get('interpretation', '')
    agent_context = ask.get('agent_context', '')
    session_id = ask.get('session_id', '')
    date = ask.get('date', '')
    session_title = ask.get('_session_title', '')

    user_msg = f"""Session: {session_id}
Date: {date}
Title: {session_title}

Eric's words (verbatim):
{chr(10).join(f'- "{q}"' for q in quotes)}

Qwen's initial interpretation: {interpretation}
Agent context: {agent_context}

Analyze Eric's INTENTION in this exchange. What was he trying to accomplish, and how does it connect to the broader CIS mission?"""

    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 1536,
        "temperature": 0.2,
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


def parse_output(raw):
    """Parse Qwen output."""
    if raw is None:
        return []
    try:
        results = json.loads(raw)
        if isinstance(results, list):
            return results
        if isinstance(results, dict):
            return [results]
        return []
    except json.JSONDecodeError:
        pass
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return [json.loads(match.group(0))]
        except json.JSONDecodeError:
            pass
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--asks', required=True)
    ap.add_argument('--out-dir', default='cards/intentions')
    ap.add_argument('--out-jsonl', default='cards/intentions.jsonl')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()

    asks = []
    with open(a.asks) as f:
        for line in f:
            line = line.strip()
            if line:
                asks.append(json.loads(line))

    print(f"Loaded {len(asks)} asks", flush=True)
    if a.limit:
        asks = asks[:a.limit]

    if a.dry_run:
        print(f"\nWould generate {len(asks)} intention cards", flush=True)
        for i, ask in enumerate(asks[:3]):
            print(f"\nAsk {i+1}: {ask.get('interpretation', '')[:100]}", flush=True)
            for q in ask.get('verbatim_quotes', [])[:2]:
                print(f'  "{q[:100]}..."' if len(q) > 100 else f'  "{q}"', flush=True)
        return

    os.makedirs(a.out_dir, exist_ok=True)

    all_cards = []
    for i, ask in enumerate(asks):
        print(f"Card {i+1}/{len(asks)}: {ask.get('interpretation', '')[:60]}", end='', flush=True)
        raw = query_qwen(ask)
        cards = parse_output(raw)

        if not cards:
            print(" → no output", flush=True)
            continue

        print(f" → {len(cards)} intention(s)", flush=True)

        for card in cards:
            card['_session_id'] = ask.get('session_id', '')
            card['_date'] = ask.get('date', '')
            card['_source_db'] = ask.get('_source_db', '')
            all_cards.append(card)

            # Write individual card file
            slug = slugify(card.get('intention', ''))
            card_path = os.path.join(a.out_dir, f"intent-{i+1:03d}-{slug}.md")
            with open(card_path, 'w') as f:
                f.write(f"# Intention Card\n\n")
                f.write(f"**Intention:** {card.get('intention', '')}\n\n")
                f.write(f"**Mission Connection:** {card.get('mission_connection', '')}\n\n")
                f.write(f"**What Was Learned:** {card.get('what_was_learned', '')}\n\n")
                f.write(f"**Relevance to Frontier Model:** {card.get('relevance_to_frontier_model', '')}\n\n")
                f.write(f"**Category:** {card.get('category', '')}\n\n")
                f.write(f"**Session:** {ask.get('session_id', '')}\n")
                f.write(f"**Date:** {ask.get('date', '')}\n\n")
                f.write(f"**Verbatim Quotes:**\n")
                for q in card.get('verbatim_quotes', []):
                    f.write(f"- \"{q}\"\n")

        if i < len(asks) - 1:
            time.sleep(0.3)

    # Write combined JSONL
    with open(a.out_jsonl, 'w') as f:
        for card in all_cards:
            f.write(json.dumps(card) + '\n')

    print(f"\n{'='*60}", flush=True)
    print(f"DONE: {len(all_cards)} intention cards from {len(asks)} asks", flush=True)
    print(f"Output: {a.out_dir}/ and {a.out_jsonl}", flush=True)

    # Category summary
    cats = {}
    for card in all_cards:
        cat = card.get('category', 'other')
        cats[cat] = cats.get(cat, 0) + 1
    print(f"\nBy category:", flush=True)
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}", flush=True)


if __name__ == '__main__':
    main()
