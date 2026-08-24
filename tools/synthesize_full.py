#!/usr/bin/env python3
"""
synthesize_full.py v2 — Recursive synthesis with SQLite accumulation.
Uses same Qwen parameters as mine_asks_sessions.py (proven working).
Batches at 3500 chars for reliability.
"""

import json, os, re, sqlite3, sys, time, urllib.request

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"
CHARS_PER_BATCH = 2500
DB_PATH = 'cards/synthesis.db'

SYSTEM_PROMPT = """You are analyzing Eric's engagement with AI models over several months. Eric is a non-coder with creative ideas. Read the material and produce structured JSON.

PROJECTS: cis (multi-agent pipeline), swa (social work app), wiasw (creative framework), creative (art/music/etc).

Output JSON per pass:
{
  "pass": N,
  "accumulated_understanding": "<GROWING synthesis of what Eric is trying to accomplish>",
  "themes": [{"theme":"...","description":"...","confidence":"emerging|confirmed"}],
  "connections": [{"from":"domain","to":"domain","type":"enables|shares_goal|depends_on","description":"..."}],
  "evidence": [{"quote":"Eric's exact words","supports_theme":"...","source":"..."}],
  "blockers": [{"blocker":"...","affected":"domain","first_seen_pass":N}],
  "eric_is_building_toward": "<one sentence>"
}"""


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        DROP TABLE IF EXISTS synthesis_passes;
        DROP TABLE IF EXISTS synthesis_themes;
        DROP TABLE IF EXISTS synthesis_connections;
        DROP TABLE IF EXISTS synthesis_evidence;
        DROP TABLE IF EXISTS synthesis_blockers;
        DROP TABLE IF EXISTS synthesis_accumulated;
        CREATE TABLE synthesis_passes (id INTEGER PRIMARY KEY, pass_number INTEGER, started_at TEXT, completed_at TEXT, batch_chars INTEGER, raw_output TEXT);
        CREATE TABLE synthesis_themes (id INTEGER PRIMARY KEY, pass_id INTEGER, theme TEXT, description TEXT, confidence TEXT);
        CREATE TABLE synthesis_connections (id INTEGER PRIMARY KEY, pass_id INTEGER, source_domain TEXT, target_domain TEXT, connection_type TEXT, description TEXT);
        CREATE TABLE synthesis_evidence (id INTEGER PRIMARY KEY, pass_id INTEGER, theme TEXT, quote TEXT, source TEXT, date TEXT);
        CREATE TABLE synthesis_blockers (id INTEGER PRIMARY KEY, pass_id INTEGER, blocker TEXT, affected_domain TEXT, first_seen_pass INTEGER, still_active INTEGER DEFAULT 1);
        CREATE TABLE synthesis_accumulated (id INTEGER PRIMARY KEY, pass_id INTEGER UNIQUE, understanding TEXT, eric_is_building_toward TEXT);
    """)
    con.commit()
    return con


def collect_all():
    entries = []
    dbs = [
        ('/home/eric/.hermes/state.db','prime'),('/home/eric/.hermes-v4pro/state.db','v4pro'),
        ('/home/eric/.hermes-v4impl/state.db','v4impl'),('/home/eric/.hermes-r1/state.db','r1'),
        ('/home/eric/.hermes-qwen/state.db','qwen'),('/home/eric/.hermes-glm-reviewer/state.db','glm-reviewer'),
        ('/home/eric/.hermes-glm-verifier/state.db','glm-verifier'),('/home/eric/.hermes-brainstorm/state.db','brainstorm'),
    ]
    for db_path, label in dbs:
        if not os.path.exists(db_path): continue
        try:
            con = sqlite3.connect(db_path)
            rows = con.execute("SELECT m.content, s.title FROM messages m JOIN sessions s ON m.session_id=s.id WHERE m.role='user' AND m.content IS NOT NULL AND length(m.content)>40 ORDER BY m.timestamp").fetchall()
            for c,t in rows: entries.append(f"[{label}] {(t or '')[:40]} | {c[:250].replace(chr(10),' ')}")
            con.close()
        except: pass

    kb = '/mnt/projects/cis/data/cis_memory.db'
    if os.path.exists(kb):
        try:
            con = sqlite3.connect(kb)
            for s in [s[0] for s in con.execute("SELECT DISTINCT source FROM knowledge_messages WHERE role='human'").fetchall() if s[0]]:
                rows = con.execute("SELECT content FROM knowledge_messages WHERE role='human' AND source=? AND content IS NOT NULL AND length(content)>50 LIMIT 200",(s,)).fetchall()
                for (c,) in rows: entries.append(f"[kb:{s}] {c[:250].replace(chr(10),' ')}")
            con.close()
        except: pass

    files = ['/mnt/projects/cis/AGENTS.md','/mnt/projects/cis/docs/SPEC_CONTROL_PLANE_OBSERVATION.md',
             '/mnt/projects/cis/PROJECT_CONTEXT_PACK_UPLOAD/HCP_01_INTENTIONS_AND_MISSION.md']
    for f in files:
        if os.path.exists(f):
            try: entries.append(f"[file:{os.path.basename(f)}] {open(f).read()[:1200]}")
            except: pass

    seen = set(); unique = []
    for e in entries:
        k = e[:80]
        if k not in seen: seen.add(k); unique.append(e)

    batches = []; cur = []; chars = 0
    for e in unique:
        if chars + len(e) > CHARS_PER_BATCH and cur: batches.append('\n'.join(cur)); cur = []; chars = 0
        cur.append(e); chars += len(e)
    if cur: batches.append('\n'.join(cur))
    return batches


def ask_qwen(msg, max_tok=2048):
    payload = json.dumps({'model':QWEN_MODEL,'messages':[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':msg}],'max_tokens':max_tok,'temperature':0.1})
    req = urllib.request.Request(QWEN_URL, data=payload.encode(), headers={'Content-Type':'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read())['choices'][0]['message']['content']
    except Exception as e:
        print(f"  QWEN ERROR: {e}", flush=True)
        return None


def parse_json(raw):
    if not raw: return None
    try: return json.loads(raw)
    except: pass
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    return None


def store_pass(con, pid, result, raw):
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    con.execute("UPDATE synthesis_passes SET completed_at=?, raw_output=? WHERE pass_number=?", (now, raw or '', result.get('pass',pid)))
    for t in result.get('themes',[]): con.execute("INSERT INTO synthesis_themes(pass_id,theme,description,confidence) VALUES(?,?,?,?)",(pid,t.get('theme',''),t.get('description',''),t.get('confidence','emerging')))
    for c in result.get('connections',[]): con.execute("INSERT INTO synthesis_connections(pass_id,source_domain,target_domain,connection_type,description) VALUES(?,?,?,?,?)",(pid,c.get('from',''),c.get('to',''),c.get('type',''),c.get('description','')))
    for e in result.get('evidence',[]): con.execute("INSERT INTO synthesis_evidence(pass_id,theme,quote,source,date) VALUES(?,?,?,?,?)",(pid,e.get('supports_theme',''),e.get('quote',''),e.get('source',''),e.get('date','')))
    for b in result.get('blockers',[]): con.execute("INSERT INTO synthesis_blockers(pass_id,blocker,affected_domain,first_seen_pass) VALUES(?,?,?,?)",(pid,b.get('blocker',''),b.get('affected',''),b.get('first_seen_pass',pid)))
    con.execute("INSERT OR REPLACE INTO synthesis_accumulated(pass_id,understanding,eric_is_building_toward) VALUES(?,?,?)",(pid,result.get('accumulated_understanding',''),result.get('eric_is_building_toward','')))
    con.commit()


def main():
    print("COLLECTING...", flush=True)
    batches = collect_all()
    print(f"Batches: {len(batches)} (~{len(batches)*90//60} min)", flush=True)

    con = init_db()
    accumulated = ""

    for i, batch in enumerate(batches):
        print(f"\nPASS {i+1}/{len(batches)} ({len(batch)} chars)", flush=True)
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        con.execute("INSERT INTO synthesis_passes(pass_number,started_at,batch_chars) VALUES(?,?,?)",(i+1,now,len(batch)))
        con.commit()

        if i == 0: prompt = f"FIRST BATCH:\n\n{batch}"
        elif i == len(batches)-1: prompt = f"FINAL BATCH. Previous understanding:\n{accumulated}\n\nFinal material:\n{batch}"
        else: prompt = f"Previous understanding:\n{accumulated}\n\nNEW material:\n{batch}"

        raw = ask_qwen(prompt)
        result = parse_json(raw)

        if result:
            store_pass(con, i+1, result, raw or '')
            accumulated = result.get('accumulated_understanding','')
            print(f"  Themes: {[t.get('theme','') for t in result.get('themes',[])]}", flush=True)
            print(f"  Building toward: {(result.get('eric_is_building_toward','') or '')[:150]}", flush=True)
        else:
            print(f"  FAILED - no valid response", flush=True)

        time.sleep(0.5)

    con.close()
    print(f"\nDONE. DB: {DB_PATH}", flush=True)


if __name__ == '__main__':
    main()
