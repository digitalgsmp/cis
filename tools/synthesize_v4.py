#!/usr/bin/env python3
"""
synthesize_v4.py — Qwen synthesis with DeepSeek review loop.

PHASES:
  pilot (--pilot N): Process N batches, output for review, exit.
  full (default): Process all batches with checkpointing.
  
Review loop: After pilot, DeepSeek reviews output → prompt refined → re-run pilot → repeat.
Once prompt is dialed in, run full synthesis.
"""
import json, os, re, sqlite3, sys, time, urllib.request

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"
INPUT_FILE = 'cards/synthesis_input.jsonl'
DB_PATH = 'cards/synthesis.db'
PROGRESS_FILE = 'cards/.synth_v4_progress.json'
CHARS_PER_BATCH = 2400
TIMEOUT = 300

SYSTEM_PROMPT = """You are mining Eric's AI engagement to discover what he is trying to build. Eric is a non-coder with creative ideas. He directs at the vision level and uses AI models as thinking partners and workers.

ERIC'S OWN WORDS (seed intent):
"I don't want summaries, I am trying to build a system that works from the raw files."
"the LLMs are the tools, I am trying to get LLMs to help me think by contributing factual information and expertise."
"when I sit down and interact with the LLMs they don't remember anything and the overall vision is not apparent"
"I need checks and balance, I am not a coder and if I don't trust something one of you says I have to be able to paste it for another model to evaluate"
"I need a worker who is constrained to my working methods and two objective reviewers as expert advisors."
"I am the conductor, not a gate."

ERIC'S PROFILE:
- Non-coder, creative design background. Directs at idea level.
- Cost-conscious. Prefers local/free models (Qwen, GLM) over paid APIs.
- Manually routes between models — DeepSeek for specs, GLM for code, Claude/ChatGPT for external review.
- Dual-reviewer requirement is non-negotiable: different training data = different blind spots.
- "Fix the spine first — don't debate in chat."

CIS PIPELINE (what he's building):
- Brain (port 8644) → Drafter (8645) → Review1/Qwen (8643) → Review2/GLM (8647) → Implementer (8646) → Verifier (8648)
- Enforcement primitive: container isolation with read-only /opt/cis-control
- Build order enforced by CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md
- Raw evidence required, never trust self-reports
- READ_ONLY_STANDING_BY protocol on startup

DOMAINS:
- cis: multi-agent pipeline, enforcement, gateways, SQLite spine, AGENTS.md
- swa: social work app (field scheduling, DAP notes, client intake, unified comms)
- wiasw: creative framework
- infrastructure: Proxmox (wander:192.168.1.200), VM (creative-vm:192.168.1.15), 4090 GPU, 10TB archive
- creative: music/audio, art, writing
- knowledge_management: KB indexing, card factory, session mining, search

CRITICAL RULES:
1. BE SPECIFIC, NOT ABSTRACT. "Persistent multi-agent system" is too vague. Say "CIS pipeline with port-isolated gateways and container enforcement."
2. QUOTE ERIC ONLY. Evidence must be Eric's words (role='user'). NEVER quote agent responses or tool output as evidence.
3. TRACK EVOLUTION OVER TIME. Early sessions (May-June 2025) = learning Hermes. July-2025 = building CIS. August 2025 = enforcement and KB indexing. Note WHEN goals emerged or shifted.
4. FIND WHAT ONLY APPEARS ACROSS SESSIONS. Single sessions show tasks. Patterns across sessions reveal goals.
5. DISTINGUISH ERIC'S ASK FROM AGENT'S DOING. Eric says "I want X." The agent may spend 20 messages implementing Y instead. Track the GAP.

Output JSON:
{
  "pass": N,
  "accumulated_understanding": "<GROWING paragraph — connect specifics from this batch to what was learned before>",
  "themes": [{"theme":"specific,concrete label","description":"what Eric is actually trying to accomplish, with specifics","confidence":"emerging|confirmed|refined"}],
  "connections": [{"from":"domain","to":"domain","type":"enables|shares_goal|depends_on|blocks","description":"specific link"}],
  "evidence": [{"quote":"ERIC'S words only","supports_theme":"...","source":"..."}],
  "blockers": [{"blocker":"specific obstacle","affected":"domain"}],
  "pattern_shifts": [{"from":"old focus","to":"new focus","when":"approx date"}],
  "eric_is_building_toward": "<one sentence — as specific as possible>"
}"""


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS synthesis_passes (
            id INTEGER PRIMARY KEY, pass_number INTEGER, phase TEXT,
            started_at TEXT, completed_at TEXT, batch_chars INTEGER, raw_output TEXT
        );
        CREATE TABLE IF NOT EXISTS synthesis_themes (
            id INTEGER PRIMARY KEY, pass_id INTEGER, theme TEXT,
            description TEXT, confidence TEXT
        );
        CREATE TABLE IF NOT EXISTS synthesis_connections (
            id INTEGER PRIMARY KEY, pass_id INTEGER, source_domain TEXT,
            target_domain TEXT, connection_type TEXT, description TEXT
        );
        CREATE TABLE IF NOT EXISTS synthesis_evidence (
            id INTEGER PRIMARY KEY, pass_id INTEGER, theme TEXT,
            quote TEXT, source TEXT, date TEXT
        );
        CREATE TABLE IF NOT EXISTS synthesis_blockers (
            id INTEGER PRIMARY KEY, pass_id INTEGER, blocker TEXT,
            affected_domain TEXT, first_seen_pass INTEGER, still_active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS synthesis_accumulated (
            id INTEGER PRIMARY KEY, pass_id INTEGER UNIQUE,
            understanding TEXT, eric_is_building_toward TEXT
        );
    """)
    con.commit()
    return con


def load_entries():
    entries = []
    with open(INPUT_FILE) as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except:
                pass
    return entries


def format_entry(entry):
    """Format an entry for Qwen context."""
    src = entry.get('source', 'unknown')
    if src == 'session':
        return (
            f"[SESSION:{entry.get('profile','')}:{entry.get('date','')}] "
            f"{entry.get('session_title','')}\n{entry.get('content','')}"
        )
    elif src.startswith('kb_'):
        return f"[{src}:{entry.get('kb_source','')}] {entry.get('content','')}"
    elif src == 'cis_file':
        return f"[FILE:{entry.get('file','')}] {entry.get('content','')}"
    elif src == 'drive_cluster':
        return f"[DRIVE:{entry.get('content','')}]"
    else:
        return str(entry.get('content', ''))


def batch_entries(entries, chars_per_batch=CHARS_PER_BATCH):
    """Batch entries with progress output, keeping whole entries together."""
    batches = []
    cur = []
    chars = 0
    total = len(entries)
    for i, entry in enumerate(entries):
        text = format_entry(entry)
        if chars + len(text) > chars_per_batch and cur:
            batches.append('\n---\n'.join(cur))
            cur = []
            chars = 0
        if len(text) > chars_per_batch:
            text = text[:chars_per_batch-100] + '...[truncated]'
        cur.append(text)
        chars += len(text)
        if (i + 1) % 1000 == 0:
            print(f"  Batching: {i+1}/{total} entries → {len(batches)} batches so far", flush=True)
    if cur:
        batches.append('\n---\n'.join(cur))
    return batches


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
    req = urllib.request.Request(
        QWEN_URL, data=payload.encode(),
        headers={'Content-Type': 'application/json'}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        return json.loads(resp.read())['choices'][0]['message']['content']
    except Exception as e:
        print(f"  QWEN ERROR: {e}", flush=True)
        return None


def parse_json(raw):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except:
        pass
    # Extract JSON from markdown blocks or raw text
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if m:
        try:
            return json.loads(m.group(1))
        except:
            pass
    m = re.search(r'\{[\s\S]*\}', raw)
    if m:
        try:
            return json.loads(m.group(0))
        except:
            pass
    return None


def store_pass(con, pid, phase, result, raw):
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    con.execute(
        "UPDATE synthesis_passes SET completed_at=?, raw_output=? WHERE pass_number=? AND phase=?",
        (now, raw or '', pid, phase)
    )
    for t in result.get('themes', []):
        con.execute(
            "INSERT INTO synthesis_themes(pass_id,theme,description,confidence) VALUES(?,?,?,?)",
            (pid, t.get('theme', ''), t.get('description', ''), t.get('confidence', 'emerging'))
        )
    for c in result.get('connections', []):
        con.execute(
            "INSERT INTO synthesis_connections(pass_id,source_domain,target_domain,connection_type,description) VALUES(?,?,?,?,?)",
            (pid, c.get('from', ''), c.get('to', ''), c.get('type', ''), c.get('description', ''))
        )
    for e in result.get('evidence', []):
        con.execute(
            "INSERT INTO synthesis_evidence(pass_id,theme,quote,source,date) VALUES(?,?,?,?,?)",
            (pid, e.get('supports_theme', ''), e.get('quote', ''), e.get('source', ''), e.get('date', ''))
        )
    for b in result.get('blockers', []):
        con.execute(
            "INSERT INTO synthesis_blockers(pass_id,blocker,affected_domain,first_seen_pass) VALUES(?,?,?,?)",
            (pid, b.get('blocker', ''), b.get('affected', ''), pid)
        )
    con.execute(
        "INSERT OR REPLACE INTO synthesis_accumulated(pass_id,understanding,eric_is_building_toward) VALUES(?,?,?)",
        (pid, result.get('accumulated_understanding', ''), result.get('eric_is_building_toward', ''))
    )
    con.commit()


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {'processed': 0, 'accumulated': '', 'phase': ''}


def save_progress(data):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f)


def run_pilot(n_batches=5):
    """Run N pilot batches and save raw output for review."""
    print(f"=== PILOT MODE: {n_batches} batches ===", flush=True)
    entries = load_entries()
    batches = batch_entries(entries)
    batches = batches[:n_batches]

    pilot_output = []
    accumulated = ''
    for i, batch in enumerate(batches):
        print(f"\nBatch {i+1}/{len(batches)} ({len(batch)} chars)", flush=True)

        if i == 0:
            prompt = f"FIRST BATCH — no prior context:\n\n{batch}"
        else:
            prompt = f"Previous understanding:\n{accumulated[-1500:] if accumulated else 'none'}\n\nNew material:\n{batch}"

        raw = ask_qwen(prompt)
        result = parse_json(raw)
        accumulated = ''

        pilot_output.append({
            'batch': i + 1,
            'batch_chars': len(batch),
            'prompt_chars': len(prompt),
            'raw': raw,
            'parsed': result is not None,
            'themes': [t.get('theme', '') for t in (result or {}).get('themes', [])],
            'building_toward': (result or {}).get('eric_is_building_toward', ''),
            'accumulated': (result or {}).get('accumulated_understanding', '')[:500],
            'evidence': [(result or {}).get('evidence', [])[:3]]
        })

        if result:
            accumulated = result.get('accumulated_understanding', '')
            print(f"  Themes: {[t.get('theme','') for t in result.get('themes',[])]}", flush=True)
            print(f"  Toward: {(result.get('eric_is_building_toward','') or '')[:150]}", flush=True)
        else:
            print(f"  FAILED", flush=True)

        time.sleep(1)

    # Save pilot output for review
    with open('cards/pilot_review.json', 'w') as f:
        json.dump(pilot_output, f, indent=2, ensure_ascii=False)

    print(f"\nPilot complete. Review file: cards/pilot_review.json", flush=True)
    for i, p in enumerate(pilot_output):
        print(f"  Batch {i+1}: {'parsed' if p['parsed'] else 'FAILED'}, themes={p['themes']}", flush=True)


def run_full():
    """Run full synthesis with checkpointing. Requires pilot-reviewed prompt."""
    print("=== FULL SYNTHESIS ===", flush=True)
    entries = load_entries()
    batches = batch_entries(entries)
    total = len(batches)

    con = init_db()
    progress = load_progress()

    # Load accumulated from DB
    row = con.execute(
        "SELECT understanding FROM synthesis_accumulated ORDER BY pass_id DESC LIMIT 1"
    ).fetchone()
    accumulated = row[0] if row else ''

    start = progress.get('processed', 0)
    pass_num = start + 1
    results = 0

    for i in range(start, total):
        batch = batches[i]
        print(f"\nBatch {i+1}/{total} ({len(batch)} chars)", flush=True)

        now = time.strftime('%Y-%m-%d %H:%M:%S')
        con.execute(
            "INSERT INTO synthesis_passes(pass_number,phase,started_at,batch_chars) VALUES(?,?,?,?)",
            (pass_num, 'full', now, len(batch))
        )
        con.commit()

        if i == 0 and not accumulated:
            prompt = f"FIRST BATCH:\n\n{batch}"
        else:
            prompt = f"Previous understanding:\n{accumulated[-2000:]}\n\nNew material:\n{batch}"

        raw = ask_qwen(prompt)
        result = parse_json(raw)

        if result:
            store_pass(con, pass_num, 'full', result, raw or '')
            accumulated = result.get('accumulated_understanding', accumulated)
            results += 1
            themes = [t.get('theme','') for t in result.get('themes',[])]
            print(f"  Themes: {themes}", flush=True)
            print(f"  Toward: {(result.get('eric_is_building_toward','') or '')[:150]}", flush=True)
        else:
            print(f"  FAILED", flush=True)

        progress['processed'] = i + 1
        progress['accumulated'] = accumulated
        save_progress(progress)

        pass_num += 1
        time.sleep(1)

    con.close()
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    print(f"\nDONE: {results}/{total} batches produced results", flush=True)
    print(f"DB: {DB_PATH}", flush=True)


if __name__ == '__main__':
    if '--pilot' in sys.argv:
        n = int(sys.argv[sys.argv.index('--pilot') + 1]) if len(sys.argv) > sys.argv.index('--pilot') + 1 else 5
        run_pilot(n)
    else:
        run_full()
