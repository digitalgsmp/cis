#!/usr/bin/env python3
"""
mine_asks_sessions.py v2 — Extract Eric's direct asks from full session transcripts.

Unlike v1 (keyword-based, spine-only) or the failed taxonomy mine (entity extraction),
this pulls COMPLETE session transcripts (user + assistant + tool) so Qwen sees
the full dialogue where Eric's intent was developed and clarified.

Process:
1. Pull all sessions + messages from all agent state DBs
2. Quick filter: skip sessions with no intent-language in user messages
3. For intent-candidate sessions, pull full transcript (truncated to ~3K tokens)
4. Feed to local Qwen 30B with reasoning prompt
5. Qwen identifies Eric's asks WITH the agent-response context
6. Output: asks_sessions.jsonl ready for card generation

Usage:
  python3 tools/mine_asks_sessions.py --out cards/asks_sessions.jsonl
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime

# Unbuffered output for progress visibility
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"
MAX_TRANSCRIPT_CHARS = 8000  # ~2000 tokens, leaves room for prompt + output
MAX_MSG_CHARS = 800  # per-message truncation in transcript

INTENT_PATTERNS = re.compile(
    r'\b(I want|I need|I am trying|my goal|what I want|I\'m trying|'
    r'can you (build|create|make|add|fix|set up|configure|write|implement|design)|'
    r'I want (to|the)|make it|build (me|a|the)|create (a|the)|'
    r'the app should|I need you to|can\'t you)\b', re.I)

SYSTEM_PROMPT = """You are an intent extractor for Eric, a non-coder building a system called CIS (Control and Integration System) with AI agent help.
Read this full conversation transcript between Eric and an AI agent. 

ERIC'S PROJECTS:
- CIS: A multi-agent pipeline system with containerized enforcement, control plane, knowledge base, and portal UI. Uses Hermes agents (DeepSeek V4 Pro, R1, Qwen, GLM) as workers, dual reviewers for code verification, Telegram for mobile access.
- SWA: A Social Work App for field workers — scheduling, DAP progress notes, client intake.
- WIASW: A creative production framework (Word/Image/Action/Sound/Web) for managing creative projects.
- Card Factory: A system to extract Eric's asks from the knowledge base and convert them into buildable cards.

YOUR JOB: Identify whether Eric, in this conversation, stated something he wants BUILT, CREATED, CHANGED, FIXED, or ACCOMPLISHED. This is his INTENT.

What IS intent:
- "Build me a dashboard that shows pipeline health" → intent to create a dashboard
- "I want the container to restart when it crashes" → intent to add auto-restart
- "Make it so each agent can see what the others are doing" → intent for cross-agent visibility
- "I need a way to track which tasks are deferred" → intent for deferred task tracking
- "The reviewers should check intent alignment before approving" → intent for reviewer workflow
- Even implied asks: "I can't see what's happening in the pipeline" → intent to add visibility

What is NOT intent:
- Testing: "are you there?", "test message", "reply with your model name"
- Status checks: "what port is it on?", "is the gateway running?", "show me the logs"
- General conversation, brainstorming without a decision, asking how something works
- Short confirmations: "yes", "ok", "go ahead", "proceed"

Look at the FULL DIALOGUE. Sometimes Eric states an intent, the agent responds with questions or clarifications, and Eric elaborates. The intent may be refined across multiple exchanges. Use the agent's responses to understand what Eric was truly asking for.

For EACH distinct intent found in this transcript, output a JSON object:
{
  "session_id": "<session_id from transcript>",
  "date": "<date from transcript>",
  "session_title": "<title or summary>",  
  "verbatim_quotes": ["<exact sentence from Eric stating what he wants>", ...],
  "interpretation": "<one sentence: what Eric wants built, created, or changed>",
  "agent_context": "<brief: how the agent responded, which clarifies or confirms Eric's intent>",
  "category": "<cis|swa|wiasw|creative|infrastructure|governance|knowledge-base|portal|container|other>"
}

Return ONLY a JSON array. If this session is purely testing/debugging/status-checking with no intent, return [].

IMPORTANT: Do NOT extract intents from agent messages — only Eric's words. 
Do NOT invent intents that aren't supported by what Eric actually said.
If Eric asks the agent to DO something (write code, run a command, explain something), that is a REQUEST not an intent — only extract it as intent if he's asking for something to be permanently built or changed in his system."""


def pull_sessions(db_path, db_label):
    """Pull all sessions with their messages from a state DB."""
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    sessions = con.execute("""
        SELECT id, title, started_at, ended_at, message_count, source, model
        FROM sessions
        ORDER BY started_at
    """).fetchall()

    results = []
    for srow in sessions:
        sid = srow['id']

        # Pull full transcript — no keyword pre-filter
        msgs = con.execute("""
            SELECT role, content, timestamp
            FROM messages
            WHERE session_id = ? AND content IS NOT NULL
            ORDER BY timestamp
        """, (sid,)).fetchall()

        if not msgs:
            continue  # skip truly empty sessions

        transcript = format_transcript(msgs)
        date_str = datetime.fromtimestamp(srow['started_at']).strftime('%Y-%m-%d %H:%M') if srow['started_at'] else ''

        results.append({
            'session_id': f"{db_label}:{sid}",
            'title': srow['title'] or f"Session {sid[:12]}",
            'date': date_str,
            'timestamp': srow['started_at'] or 0,
            'db': db_label,
            'msg_count': len(msgs),
            'user_msg_count': sum(1 for r, _, _ in msgs if r == 'user'),
            'transcript': transcript,
            'model': srow['model'] or 'unknown',
        })

    con.close()
    return results


def format_transcript(msgs):
    """Format messages into a readable transcript, truncated per message."""
    lines = []
    total_chars = 0
    for role, content, ts in msgs:
        if not content:
            continue
        label = "ERIC" if role == 'user' else "AGENT"
        if role == 'tool':
            # Truncate tool output heavily
            text = (content or '')[:200].replace('\n', ' ')
            if len(content or '') > 200:
                text += ' [truncated]'
        else:
            text = content[:MAX_MSG_CHARS]
            if len(content) > MAX_MSG_CHARS:
                text += ' [truncated]'

        lines.append(f"[{label}] {text}")
        total_chars += len(lines[-1])
        if total_chars > MAX_TRANSCRIPT_CHARS:
            lines.append("[TRANSCRIPT TRUNCATED - too long]")
            break

    return '\n'.join(lines)


def query_qwen(session_data):
    """Send a session transcript to Qwen for intent reasoning."""
    user_msg = f"""Session: {session_data['session_id']}
Date: {session_data['date']}
Title: {session_data['title']}

Transcript:
{session_data['transcript']}"""

    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 2048,
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
        content = body['choices'][0]['message']['content']
        return content
    except Exception as e:
        print(f"  Qwen error: {e}", file=sys.stderr, flush=True)
        return None


def parse_output(raw):
    """Parse Qwen output into asks list."""
    if raw is None:
        return []
    try:
        results = json.loads(raw)
        if isinstance(results, list):
            return results
        return []
    except json.JSONDecodeError:
        pass
    # Try extracting JSON array
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='cards/asks_sessions.jsonl')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()

    # Check Qwen
    if not a.dry_run:
        try:
            urllib.request.urlopen("http://127.0.0.1:8002/health", timeout=5)
        except Exception:
            print("ERROR: Qwen not reachable at http://127.0.0.1:8002", file=sys.stderr)
            sys.exit(1)

    # Pull sessions from ALL agent DBs (8 profiles)
    dbs = [
        ('/home/eric/.hermes/state.db', 'prime'),
        ('/home/eric/.hermes-v4pro/state.db', 'v4pro'),
        ('/home/eric/.hermes-v4impl/state.db', 'v4impl'),
        ('/home/eric/.hermes-r1/state.db', 'r1'),
    ]
    for extra in ['qwen', 'glm-reviewer', 'glm-verifier', 'brainstorm']:
        path = f'/home/eric/.hermes-{extra}/state.db'
        if os.path.exists(path):
            dbs.append((path, extra))

    all_sessions = []
    for db_path, label in dbs:
        if os.path.exists(db_path):
            sessions = pull_sessions(db_path, label)
            print(f"{label}: {len(sessions)} intent-candidate sessions", flush=True)
            all_sessions.extend(sessions)
        else:
            print(f"{label}: DB not found", flush=True)

    all_sessions.sort(key=lambda s: s['timestamp'])
    if a.limit:
        all_sessions = all_sessions[:a.limit]

    print(f"\nTotal sessions to process: {len(all_sessions)}", flush=True)
    print(f"Estimated time: ~{len(all_sessions) * 3}s ({len(all_sessions) * 3 // 60}m)", flush=True)

    if a.dry_run:
        print("\n--- SAMPLE SESSIONS (first 5) ---", flush=True)
        for s in all_sessions[:5]:
            print(f"\n[{s['session_id']}] {s['date']} | {s['title'][:60]}", flush=True)
            print(f"  Messages: {s['msg_count']} ({s['user_msg_count']} user)", flush=True)
            print(f"  Transcript: {len(s['transcript'])} chars", flush=True)
            print(f"  First 200: {s['transcript'][:200]}...", flush=True)
        return

    # Process each session
    all_asks = []
    for i, sess in enumerate(all_sessions):
        print(f"\nSession {i+1}/{len(all_sessions)}: {sess['session_id']} ({sess['title'][:40]})", end='', flush=True)
        raw = query_qwen(sess)
        asks = parse_output(raw)
        print(f" → {len(asks)} asks", flush=True)

        for ask in asks:
            ask['_source_db'] = sess['db']
            ask['_session_title'] = sess['title']
            all_asks.append(ask)

        if i < len(all_sessions) - 1:
            time.sleep(0.3)

    # Write output
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    with open(a.out, 'w') as f:
        for ask in all_asks:
            f.write(json.dumps(ask) + '\n')

    print(f"\n{'='*60}", flush=True)
    print(f"DONE: {len(all_asks)} asks from {len(all_sessions)} sessions", flush=True)
    print(f"Output: {a.out}", flush=True)

    # Summary by category
    cats = {}
    for ask in all_asks:
        cat = ask.get('category', 'other')
        cats[cat] = cats.get(cat, 0) + 1
    print(f"\nBy category:", flush=True)
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}", flush=True)


if __name__ == '__main__':
    main()
