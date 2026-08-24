#!/usr/bin/env python3
"""
synthesize_phased.py — 4-phase recursive synthesis with simple per-phase prompts.

Phase 1 (Discovery): "What themes emerge?" — extractive, fast, 1K batches
Phase 2 (Connection): "How do these themes connect across domains?"
Phase 3 (Refinement): "Merge, split, find gaps in accumulated themes"
Phase 4 (Synthesis): "Final synthesis organized by Eric's priorities"

All data stored in cards/synthesis.db relational tables.
"""

import json, os, re, sqlite3, sys, time, urllib.request

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
QWEN_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m"
CHARS_PER_BATCH = 1000
DB_PATH = 'cards/synthesis.db'


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        DROP TABLE IF EXISTS passes;
        DROP TABLE IF EXISTS themes;
        DROP TABLE IF EXISTS connections;
        DROP TABLE IF EXISTS evidence;
        DROP TABLE IF EXISTS accumulated;
        CREATE TABLE passes (id INTEGER PRIMARY KEY, phase INTEGER, pass_num INTEGER, started TEXT, completed TEXT, batch_chars INTEGER, raw TEXT);
        CREATE TABLE themes (id INTEGER PRIMARY KEY, pass_id INTEGER, theme TEXT, description TEXT, confidence TEXT);
        CREATE TABLE connections (id INTEGER PRIMARY KEY, pass_id INTEGER, source_domain TEXT, target_domain TEXT, ctype TEXT, description TEXT);
        CREATE TABLE evidence (id INTEGER PRIMARY KEY, pass_id INTEGER, theme TEXT, quote TEXT, source TEXT);
        CREATE TABLE accumulated (id INTEGER PRIMARY KEY, pass_id INTEGER UNIQUE, summary TEXT);
    """)
    con.commit()
    return con


def collect_entries():
    entries = []
    dbs = [('/home/eric/.hermes/state.db','prime'),('/home/eric/.hermes-v4pro/state.db','v4pro'),
           ('/home/eric/.hermes-v4impl/state.db','v4impl'),('/home/eric/.hermes-r1/state.db','r1'),
           ('/home/eric/.hermes-qwen/state.db','qwen'),('/home/eric/.hermes-glm-reviewer/state.db','glm'),
           ('/home/eric/.hermes-glm-verifier/state.db','glmv'),('/home/eric/.hermes-brainstorm/state.db','brain')]
    for db_path, label in dbs:
        if not os.path.exists(db_path): continue
        con = sqlite3.connect(db_path)
        rows = con.execute("SELECT m.content,s.title FROM messages m JOIN sessions s ON m.session_id=s.id WHERE m.role='user' AND m.content IS NOT NULL AND length(m.content)>40 ORDER BY m.timestamp").fetchall()
        for c,t in rows: entries.append(f"[{label}] {(t or '')[:40]} | {c[:200].replace(chr(10),' ')}")
        con.close()

    kb = '/mnt/projects/cis/data/cis_memory.db'
    if os.path.exists(kb):
        con = sqlite3.connect(kb)
        for s in [s[0] for s in con.execute("SELECT DISTINCT source FROM knowledge_messages WHERE role='human'").fetchall() if s[0]]:
            rows = con.execute("SELECT content FROM knowledge_messages WHERE role='human' AND source=? AND length(content)>50 LIMIT 200",(s,)).fetchall()
            for (c,) in rows: entries.append(f"[kb:{s}] {c[:200].replace(chr(10),' ')}")
        con.close()

    for f in ['/mnt/projects/cis/AGENTS.md','/mnt/projects/cis/PROJECT_CONTEXT_PACK_UPLOAD/HCP_01_INTENTIONS_AND_MISSION.md']:
        if os.path.exists(f):
            entries.append(f"[file:{os.path.basename(f)}] {open(f).read()[:800]}")

    seen = set(); unique = []
    for e in entries:
        k = e[:60]
        if k not in seen: seen.add(k); unique.append(e)

    batches = []; cur = []; chars = 0
    for e in unique:
        if chars + len(e) > CHARS_PER_BATCH and cur: batches.append('\n'.join(cur)); cur = []; chars = 0
        cur.append(e); chars += len(e)
    if cur: batches.append('\n'.join(cur))
    return batches


def ask_qwen(system, user, max_tok=1024):
    payload = json.dumps({'model':QWEN_MODEL,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'max_tokens':max_tok,'temperature':0.1})
    req = urllib.request.Request(QWEN_URL, data=payload.encode(), headers={'Content-Type':'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=90)
        return json.loads(resp.read())['choices'][0]['message']['content']
    except Exception as e:
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


def run_phase(con, phase, batches, system_prompt, summary_prefix):
    """Run one phase across all batches."""
    accumulated = ""
    for i, batch in enumerate(batches):
        pid = con.execute("SELECT COUNT(*)+1 FROM passes").fetchone()[0]
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        con.execute("INSERT INTO passes(phase,pass_num,started,batch_chars) VALUES(?,?,?,?)",(phase,i+1,now,len(batch)))
        con.commit()

        if accumulated:
            prompt = f"{summary_prefix}{accumulated}\n\nNew material:\n{batch}"
        else:
            prompt = f"Material:\n{batch}"

        raw = ask_qwen(system_prompt, prompt)
        result = parse_json(raw)

        if result:
            acc = result.get('summary','') or result.get('accumulated_understanding','')
            if acc: accumulated = acc
            con.execute("UPDATE passes SET completed=?,raw=? WHERE id=?",(time.strftime('%H:%M:%S'),raw or '',pid))
            for t in result.get('themes',[]): con.execute("INSERT INTO themes(pass_id,theme,description,confidence) VALUES(?,?,?,?)",(pid,t.get('theme',''),t.get('description',''),t.get('confidence','emerging')))
            for c in result.get('connections',[]): con.execute("INSERT INTO connections(pass_id,source_domain,target_domain,ctype,description) VALUES(?,?,?,?,?)",(pid,c.get('from',''),c.get('to',''),c.get('type',''),c.get('description','')))
            for e in result.get('evidence',[]): con.execute("INSERT INTO evidence(pass_id,theme,quote,source) VALUES(?,?,?,?)",(pid,e.get('supports_theme',''),e.get('quote',''),e.get('source','')))
            if accumulated: con.execute("INSERT OR REPLACE INTO accumulated(pass_id,summary) VALUES(?,?)",(pid,accumulated))
            con.commit()
            print(f"  OK: {len(result.get('themes',[]))} themes, {len(result.get('evidence',[]))} evidence", flush=True)
        else:
            print(f"  FAIL", flush=True)

        time.sleep(0.3)
    return accumulated


def main():
    print("COLLECTING...", flush=True)
    batches = collect_entries()
    print(f"Batches: {len(batches)}", flush=True)

    con = init_db()

    # PHASE 1: Discovery
    print("\n=== PHASE 1: DISCOVERY ===", flush=True)
    sp1 = "You analyze Eric, a non-coder building AI systems (CIS pipeline, SWA app, WIASW creative framework). Identify themes in what he is trying to accomplish. Output JSON: {\"summary\":\"<growing understanding>\",\"themes\":[{\"theme\":\"...\",\"description\":\"...\"}],\"evidence\":[{\"quote\":\"exact words\",\"supports_theme\":\"...\",\"source\":\"...\"}]}"
    acc = run_phase(con, 1, batches, sp1, "Previous understanding:\n")

    # PHASE 2: Connection
    print("\n=== PHASE 2: CONNECTION ===", flush=True)
    # Build compact context from DB
    themes_list = con.execute("SELECT theme, description FROM themes GROUP BY theme ORDER BY COUNT(*) DESC LIMIT 30").fetchall()
    ctx = "THEMES FOUND:\\n" + "\\n".join([f"- {t}: {d[:100]}" for t,d in themes_list])
    sp2 = f"You are connecting themes across Eric's projects. {ctx}\\n\\nIdentify connections between domains (cis, swa, wiasw, creative, infrastructure). How do themes relate? Output JSON: {{\"connections\":[{{\"from\":\"domain\",\"to\":\"domain\",\"type\":\"enables|shares_goal|depends_on\",\"description\":\"...\"}}],\"summary\":\"<connection insights>\"}}"
    acc = run_phase(con, 2, batches[:min(30,len(batches))], sp2, "Connection insights:\n")

    # PHASE 3: Refinement
    print("\n=== PHASE 3: REFINEMENT ===", flush=True)
    all_themes = con.execute("SELECT theme, COUNT(*) as cnt FROM themes GROUP BY theme ORDER BY cnt DESC").fetchall()
    tctx = "ALL THEMES:\\n" + "\\n".join([f"- {t} ({c} mentions)" for t,c in all_themes])
    sp3 = f"{tctx}\\n\\nMerge similar themes. Split overly broad ones. Identify gaps. Output JSON: {{\"merged_themes\":[],\"gaps\":[],\"summary\":\"<refined understanding>\"}}"
    acc = run_phase(con, 3, [tctx], sp3, "Refined understanding:\n")

    # PHASE 4: Synthesis
    print("\n=== PHASE 4: SYNTHESIS ===", flush=True)
    final_themes = con.execute("SELECT theme, description FROM themes GROUP BY theme ORDER BY COUNT(*) DESC LIMIT 20").fetchall()
    final_connections = con.execute("SELECT source_domain, target_domain, ctype, description FROM connections GROUP BY source_domain, target_domain").fetchall()
    fctx = "THEMES:\\n" + "\\n".join([f"- {t}: {d[:150]}" for t,d in final_themes])
    fctx += "\\n\\nCONNECTIONS:\\n" + "\\n".join([f"- {s} {ct} {t}: {d}" for s,t,ct,d in final_connections])
    sp4 = f"{fctx}\\n\\nSynthesize into final analysis organized by Eric's priorities: (1) pipeline + usable UI, (2) organized intention map, (3) SWA app. Output JSON with final_synthesis."
    acc = run_phase(con, 4, [fctx], sp4, "")

    con.close()
    print(f"\\nDONE. DB: {DB_PATH}", flush=True)
    themes = sqlite3.connect(DB_PATH).execute("SELECT COUNT(*) FROM themes").fetchone()[0]
    evidence = sqlite3.connect(DB_PATH).execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    print(f"Themes: {themes}, Evidence: {evidence}", flush=True)


if __name__ == '__main__':
    main()
