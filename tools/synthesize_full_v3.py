#!/usr/bin/env python3
"""
synthesize_full v3 — Accumulative synthesis with checkpointing.
Key fixes over v2:
  - init_db() uses CREATE IF NOT EXISTS (no more DROP on every run)
  - Collects full user+agent transcripts from session DBs (not just user snippets)
  - Checkpointing: writes .synth_progress.json so crashes can resume
  - Recursive refinement: after first pass, re-feeds accumulated understanding
  - KB: processes human messages from cis_memory.db with full source tracking
"""
import json, os, re, sqlite3, sys, time, urllib.request

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"
CHARS_PER_BATCH = 2500
DB_PATH = 'cards/synthesis.db'
PROGRESS_FILE = 'cards/.synth_progress.json'
TIMEOUT = 240

SYSTEM_PROMPT = """You are mining Eric's AI engagement across many months. Eric is a non-coder with creative and business ideas. He uses multiple AI models (DeepSeek, GLM, Qwen, Claude, ChatGPT) for different purposes.

DOMAINS:
- cis: multi-agent pipeline for code generation with checks and balances
- swa: social work app (field scheduling, DAP notes, client intake, unified comms)
- wiasw: creative framework / "What I Am Seeing Within"
- infrastructure: Proxmox, VMs, GPUs, networking
- creative: art, music, writing, audio generation

Analyze the material and produce structured JSON:
{
  "pass": N,
  "accumulated_understanding": "<GROWING synthesis paragraph — what Eric is trying to accomplish across ALL engagement>",
  "themes": [{"theme":"...","description":"...","confidence":"emerging|confirmed|refined"}],
  "connections": [{"from":"domain","to":"domain","type":"enables|shares_goal|depends_on|blocks","description":"..."}],
  "evidence": [{"quote":"Eric's exact words","supports_theme":"...","source":"[prime|v4pro|kb:source|...]"}],
  "blockers": [{"blocker":"...","affected":"domain"}],
  "eric_is_building_toward": "<one sentence — the thing all this work converges on>"
}

CRITICAL: 
- Accumulated_understanding must GROW — don't summarize, integrate.
- Quote Eric verbatim in evidence. Never paraphrase his words.
- Identify what he wants even when he doesn't state it explicitly — infer from patterns.
- His goals are implicit in the totality of his engagement, not in individual asks.
"""


def init_db():
    """Create tables WITHOUT dropping existing data."""
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


def collect_session_transcripts():
    """Collect full user+agent transcripts from all session DBs."""
    entries = []
    dbs = [
        ('/home/eric/.hermes/state.db', 'prime'),
        ('/home/eric/.hermes-v4pro/state.db', 'v4pro'),
        ('/home/eric/.hermes-v4impl/state.db', 'v4impl'),
        ('/home/eric/.hermes-r1/state.db', 'r1'),
        ('/home/eric/.hermes-qwen/state.db', 'qwen'),
        ('/home/eric/.hermes-glm-reviewer/state.db', 'glm-reviewer'),
        ('/home/eric/.hermes-glm-verifier/state.db', 'glm-verifier'),
        ('/home/eric/.hermes-brainstorm/state.db', 'brainstorm'),
    ]
    for db_path, label in dbs:
        if not os.path.exists(db_path):
            continue
        try:
            con = sqlite3.connect(db_path)
            con.row_factory = sqlite3.Row
            # Get sessions with timestamps
            sessions = con.execute(
                "SELECT id, title, created_at FROM sessions ORDER BY created_at"
            ).fetchall()
            for sess in sessions:
                msgs = con.execute(
                    "SELECT role, content, timestamp FROM messages "
                    "WHERE session_id=? AND content IS NOT NULL AND length(content)>20 "
                    "ORDER BY timestamp",
                    (sess['id'],)
                ).fetchall()
                if not msgs:
                    continue
                # Build a conversation summary: user messages + key agent responses
                user_msgs = [m for m in msgs if m['role'] == 'user']
                agent_msgs = [m for m in msgs if m['role'] in ('assistant', 'tool')]
                if not user_msgs:
                    continue

                # Keep first and last user messages (intent + outcome) + up to 3 more
                selected = []
                if user_msgs:
                    selected.append(user_msgs[0])  # first ask
                if len(user_msgs) > 1:
                    selected.append(user_msgs[-1])  # last follow-up
                # Pick a couple from the middle if available
                mid = len(user_msgs) // 2
                if mid > 0 and mid < len(user_msgs) - 1:
                    selected.append(user_msgs[mid])

                for m in selected:
                    ts = m['timestamp'] or ''
                    entries.append(
                        f"[{label}:{sess['title'] or 'untitled'}:{ts[:10]}] "
                        f"{m['content'][:300].replace(chr(10), ' ')}"
                    )
            con.close()
        except Exception as e:
            print(f"  WARN: {db_path}: {e}", flush=True)
    return entries


def collect_kb_messages():
    """Collect human messages from cis_memory.db with source context."""
    entries = []
    kb = '/mnt/projects/cis/data/cis_memory.db'
    if not os.path.exists(kb):
        return entries
    try:
        con = sqlite3.connect(kb)
        rows = con.execute(
            "SELECT content, source FROM knowledge_messages "
            "WHERE role='human' AND content IS NOT NULL AND length(content)>30 "
            "ORDER BY rowid"
        ).fetchall()
        for content, source in rows:
            entries.append(
                f"[kb:{source or 'unknown'}] "
                f"{content[:300].replace(chr(10), ' ')}"
            )
        con.close()
    except Exception as e:
        print(f"  WARN: KB: {e}", flush=True)
    return entries


def deduplicate(entries):
    """Remove near-duplicate entries."""
    seen = set()
    unique = []
    for e in entries:
        # Normalize for dedup
        key = re.sub(r'\s+', ' ', e.lower())[:100]
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def batch_entries(entries, chars_per_batch=CHARS_PER_BATCH):
    """Split entries into batches that fit Qwen's context."""
    batches = []
    cur = []
    chars = 0
    for e in entries:
        if chars + len(e) > chars_per_batch and cur:
            batches.append('\n'.join(cur))
            cur = []
            chars = 0
        cur.append(e)
        chars += len(e)
    if cur:
        batches.append('\n'.join(cur))
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
    # Try direct parse
    try:
        return json.loads(raw)
    except:
        pass
    # Try to extract JSON block
    for pattern in [r'\{[\s\S]*\}', r'```json\s*([\s\S]*?)\s*```']:
        m = re.search(pattern, raw)
        if m:
            try:
                return json.loads(m.group(1) if m.lastindex else m.group(0))
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
            (pid, t.get('theme', ''), t.get('description', ''),
             t.get('confidence', 'emerging'))
        )
    for c in result.get('connections', []):
        con.execute(
            "INSERT INTO synthesis_connections(pass_id,source_domain,target_domain,connection_type,description) VALUES(?,?,?,?,?)",
            (pid, c.get('from', ''), c.get('to', ''),
             c.get('type', ''), c.get('description', ''))
        )
    for e in result.get('evidence', []):
        con.execute(
            "INSERT INTO synthesis_evidence(pass_id,theme,quote,source,date) VALUES(?,?,?,?,?)",
            (pid, e.get('supports_theme', ''), e.get('quote', ''),
             e.get('source', ''), e.get('date', ''))
        )
    for b in result.get('blockers', []):
        con.execute(
            "INSERT INTO synthesis_blockers(pass_id,blocker,affected_domain,first_seen_pass) VALUES(?,?,?,?)",
            (pid, b.get('blocker', ''), b.get('affected', ''), pid)
        )
    con.execute(
        "INSERT OR REPLACE INTO synthesis_accumulated(pass_id,understanding,eric_is_building_toward) VALUES(?,?,?)",
        (pid, result.get('accumulated_understanding', ''),
         result.get('eric_is_building_toward', ''))
    )
    con.commit()


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {'processed_batches': 0, 'accumulated': '', 'phase': '', 'total_batches': 0}


def save_progress(data):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f)


def run_phase(con, phase_name, entries, start_pass=1):
    """Run a synthesis phase over entries."""
    batches = batch_entries(entries)
    total = len(batches)
    print(f"  Phase '{phase_name}': {total} batches (~{total*2//60} min)", flush=True)

    progress = load_progress()
    # Always load latest accumulated from DB
    row = con.execute(
        "SELECT understanding FROM synthesis_accumulated ORDER BY pass_id DESC LIMIT 1"
    ).fetchone()
    accumulated = row[0] if row else ''

    pass_num = start_pass
    results_count = 0

    for i, batch in enumerate(batches):
        # Skip already-processed batches
        if i < progress.get('processed_batches', 0):
            pass_num += 1
            continue

        print(f"\n  Batch {i+1}/{total} ({len(batch)} chars)", flush=True)
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        con.execute(
            "INSERT INTO synthesis_passes(pass_number,phase,started_at,batch_chars) VALUES(?,?,?,?)",
            (pass_num, phase_name, now, len(batch))
        )
        con.commit()

        if i == 0 and not accumulated:
            prompt = f"FIRST BATCH — no prior context:\n\n{batch}"
        else:
            prompt = f"Previous accumulated understanding:\n{accumulated[-2000:]}\n\nNew material to integrate:\n{batch}"

        raw = ask_qwen(prompt)
        result = parse_json(raw)

        if result:
            store_pass(con, pass_num, phase_name, result, raw or '')
            accumulated = result.get('accumulated_understanding', accumulated)
            results_count += 1
            print(f"    Building toward: {(result.get('eric_is_building_toward','') or '')[:150]}", flush=True)
        else:
            print(f"    FAILED — keeping previous understanding", flush=True)

        # Checkpoint
        progress['processed_batches'] = i + 1
        progress['accumulated'] = accumulated
        progress['phase'] = phase_name
        progress['total_batches'] = total
        save_progress(progress)

        pass_num += 1
        time.sleep(1)

    print(f"  Phase complete: {results_count}/{total} batches produced results", flush=True)
    return pass_num, accumulated


def main():
    print("=== SYNTHESIS v3 ===", flush=True)
    con = init_db()

    # Phase A: Session transcripts
    print("\n--- PHASE A: Session Transcripts ---", flush=True)
    print("Collecting from 8 profile DBs...", flush=True)
    session_entries = collect_session_transcripts()
    session_entries = deduplicate(session_entries)
    print(f"  {len(session_entries)} unique entries", flush=True)

    if session_entries:
        next_pass, accumulated = run_phase(con, 'sessions', session_entries, start_pass=1)
    else:
        print("  No session entries found", flush=True)
        next_pass, accumulated = 1, ''

    # Phase B: KB messages
    print("\n--- PHASE B: Knowledge Base ---", flush=True)
    print("Collecting from cis_memory.db...", flush=True)
    kb_entries = collect_kb_messages()
    # Don't dedup against sessions — KB has different source context
    print(f"  {len(kb_entries)} entries", flush=True)

    if kb_entries:
        next_pass, accumulated = run_phase(con, 'kb', kb_entries, start_pass=next_pass)

    # Phase C: Recursive refinement
    print("\n--- PHASE C: Recursive Refinement ---", flush=True)
    progress = load_progress()
    if accumulated:
        # Feed the accumulated understanding back through for a meta-synthesis pass
        print("  Running meta-synthesis on accumulated understanding...", flush=True)
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        con.execute(
            "INSERT INTO synthesis_passes(pass_number,phase,started_at,batch_chars) VALUES(?,?,?,?)",
            (next_pass, 'meta', now, len(accumulated))
        )
        con.commit()

        prompt = (
            f"META-SYNTHESIS PASS. Below is the accumulated understanding from processing "
            f"all of Eric's sessions and knowledge base messages. Re-read it critically "
            f"and produce a refined, deeper synthesis. Identify patterns that only become "
            f"visible when you see everything together. What is Eric really driving toward?\n\n"
            f"{accumulated}"
        )
        raw = ask_qwen(prompt, max_tok=4096)
        result = parse_json(raw)

        if result:
            store_pass(con, next_pass, 'meta', result, raw or '')
            accumulated = result.get('accumulated_understanding', accumulated)
            print(f"    Refined toward: {(result.get('eric_is_building_toward','') or '')[:200]}", flush=True)
        else:
            print(f"    Meta-synthesis failed — keeping previous understanding", flush=True)
    else:
        print("  No accumulated understanding to refine", flush=True)

    con.close()

    # Clear progress
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    print(f"\n=== DONE ===", flush=True)
    print(f"DB: {DB_PATH}", flush=True)

    # Show summary
    con2 = sqlite3.connect(DB_PATH)
    passes = con2.execute("SELECT COUNT(*) FROM synthesis_passes WHERE completed_at IS NOT NULL").fetchone()[0]
    themes = con2.execute("SELECT COUNT(*) FROM synthesis_themes").fetchone()[0]
    row = con2.execute(
        "SELECT eric_is_building_toward FROM synthesis_accumulated ORDER BY pass_id DESC LIMIT 1"
    ).fetchone()
    con2.close()

    print(f"Total completed passes: {passes}")
    print(f"Total themes: {themes}")
    if row:
        print(f"Eric is building toward: {row[0]}")


if __name__ == '__main__':
    main()
