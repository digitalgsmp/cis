#!/usr/bin/env python3
"""Seed pipeline_cards.db from inbox cards + assessment engine findings."""
import sqlite3, os, re, glob, json

DB = "/mnt/projects/cis/cards/pipeline_cards.db"
INBOX = "/mnt/projects/cis/cards/inbox"
ASSESS = "/mnt/projects/cis/cards/assessment.db"

if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)
conn.executescript("""
    CREATE TABLE goals (id TEXT PRIMARY KEY, goal TEXT NOT NULL, verbatim_quote TEXT NOT NULL, source_session TEXT NOT NULL);
    CREATE TABLE cards (id TEXT PRIMARY KEY, title TEXT, intent TEXT, source_session TEXT, source_profile TEXT, source_date TEXT, priority INTEGER DEFAULT 3, status TEXT DEFAULT 'unbuilt', times_requested INTEGER DEFAULT 1, done_when TEXT, not_in_card TEXT);
    CREATE TABLE card_goals (card_id TEXT, goal_id TEXT, relevance TEXT, PRIMARY KEY(card_id, goal_id));
    CREATE TABLE card_obstacles (card_id TEXT, obstacle_type TEXT, description TEXT, source_pass TEXT);
    CREATE TABLE fabrications (card_id TEXT, claimed_capability TEXT, actual_evidence TEXT, honesty_class TEXT, consequence TEXT, source_session TEXT);
    CREATE TABLE source_sessions (session_id TEXT PRIMARY KEY, profile TEXT, date TEXT, retrieval_path TEXT);
""")

# --- GOALS ---
goals = [
    ("G1", "Raw-file system", "I don't want summaries, I am trying to build a system that works from the raw files.", "session_20260520_215551_16187f"),
    ("G2", "LLMs as knowledge contributors", "The LLMs are the tools, I am trying to get LLMs to help me think by contributing factual information and expertise.", "session_20260525_232304_b2d3b2"),
    ("G3", "Constrained worker + dual reviewers", "I need a worker who is constrained to my working methods and two objective reviewers as expert advisors.", "session_20260518_203801_265262"),
]
conn.executemany("INSERT INTO goals VALUES(?,?,?,?)", goals)

# --- CARDS ---
dupes = {
    'ask-159':6,'ask-160':6,'ask-161':6,'ask-162':6,'ask-163':6,'ask-165':6,
    'ask-154':3,'ask-155':3,'ask-157':3,
    'ask-106':2,'ask-107':2,'ask-150':2,'ask-152':2,
}

cards_inserted = []
for fp in sorted(glob.glob(f"{INBOX}/*.md")):
    with open(fp) as f:
        content = f.read()
    cid = os.path.basename(fp).replace('.md', '')
    
    title_m = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else cid
    
    src_m = re.search(r'SOURCE:\s*(.+)', content)
    src = src_m.group(1).strip() if src_m else ''
    
    intent_m = re.search(r'INTENT[^:]*:\s*"([^"]+)"', content)
    intent = intent_m.group(1).strip() if intent_m else ''
    
    build_m = re.search(r'BUILD:\s*(.+?)(?:\n[A-Z]|\n\n|\Z)', content, re.DOTALL)
    build = build_m.group(1).strip() if build_m else ''
    
    done_m = re.search(r'DONE WHEN:(.+?)(?:\n\n[A-Z]|\n\Z|\Z)', content, re.DOTALL)
    done = done_m.group(1).strip() if done_m else ''
    
    not_m = re.search(r'NOT IN THIS CARD:(.+?)(?:\Z)', content, re.DOTALL)
    notin = not_m.group(1).strip() if not_m else ''
    
    sess_m = re.search(r'message\s+(\w+):(\S+)', src)
    session = f"{sess_m.group(1)}:{sess_m.group(2)}" if sess_m else ''
    profile = sess_m.group(1) if sess_m else ''
    date_m = re.search(r'(\d{4}-\d{2}-\d{2})', src)
    date = date_m.group(1) if date_m else ''
    
    nl = cid.lower()
    if 'swa-' in nl: pri = 1
    elif any(k in nl for k in ['dark-mode','health-check','health_check','todo-comment','health-badge','orchestrat']): pri = 2
    else: pri = 3
    
    conn.execute("INSERT INTO cards VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (cid, title, intent or build, session, profile, date, pri, 'unbuilt', dupes.get(cid,1), done, notin))
    cards_inserted.append(cid)
    
    # Goal alignment
    combined = (title + ' ' + intent + ' ' + build).lower()
    gset = set()
    if any(k in combined for k in ['evidence','endpoint','verify','test','check','raw file','curl','health']):
        gset.add(('G1','direct'))
    if any(k in combined for k in ['knowledge','search','index','tool','retriev','kb','data']):
        gset.add(('G2','direct'))
    if any(k in combined for k in ['worker','review','pipeline','orchestrat','container','enforce','gateway','isolation']):
        gset.add(('G3','direct'))
    if any(k in combined for k in ['hermes','config','runtime','portal','ui','dashboard','telegram','chat','dark','badge','toggle']):
        gset.add(('G3','enables'))
    if not gset:
        gset.add(('G2','supports'))
    for gid, rel in gset:
        conn.execute("INSERT OR IGNORE INTO card_goals VALUES(?,?,?)", (cid, gid, rel))

# --- OBSTACLES from assessment.db ---
obs_map = {
    'communication_breakdown': ['ask-001','ask-008','ask-014','ask-016','ask-018'],
    'model_bias': ['ask-159','ask-160','ask-161','ask-162','ask-163','ask-165'],
    'specification_gap': ['ask-106','ask-107','ask-150','ask-152'],
    'execution_failure': ['ask-154','ask-155','ask-157'],
    'context_loss': ['ask-045','ask-046','ask-176'],
}

a = sqlite3.connect(f"file:{ASSESS}?mode=ro", uri=True)
obs_rows = a.execute("SELECT category, finding, evidence_from_passes, proposed_defense FROM meta_synthesis").fetchall()
for cat, finding, evidence, defense in obs_rows:
    for cid in obs_map.get(cat, []):
        if cid in cards_inserted:
            conn.execute("INSERT INTO card_obstacles VALUES(?,?,?,?)",
                (cid, cat, f"{finding} | Defense: {defense}", f"pass 6 ({evidence})"))

# --- FABRICATIONS ---
fab_map = {
    'plan written': 'ask-030', 'untracked files': 'ask-154',
    'created cis_pre_tool_gate': 'ask-014', 'restarted flask': 'ask-159',
    'identified trust root': 'ask-016', 'built a roadmap': 'ask-090',
    'reset credentials': 'ask-045', 'created the contracts': 'ask-018',
    'created a file': 'ask-154', 'created a structured memory': 'ask-001',
    'generated a structured extraction': 'ask-008',
}

fabs = a.execute("SELECT claimed_capability, actual_evidence, honesty_class, consequence, session_id FROM capability_boundaries").fetchall()
a.close()

for claimed, evidence, honesty, consequence, session_id in fabs:
    matched = False
    for keyword, cid in fab_map.items():
        if keyword in claimed.lower():
            if cid in cards_inserted:
                conn.execute("INSERT INTO fabrications VALUES(?,?,?,?,?,?)",
                    (cid, claimed, evidence, honesty, consequence, session_id))
            matched = True
            break
    if not matched:
        conn.execute("INSERT INTO fabrications VALUES(?,?,?,?,?,?)",
            (None, claimed, evidence, honesty, consequence, session_id))

# --- SOURCE SESSIONS ---
conn.execute("""
    INSERT OR IGNORE INTO source_sessions(session_id, profile, date, retrieval_path)
    SELECT DISTINCT source_session, source_profile, source_date, '~/.hermes-' || source_profile || '/state.db'
    FROM cards WHERE source_session != ''
""")

# --- VIEWS ---
conn.executescript("""
    CREATE VIEW v_card_goal_map AS SELECT c.id, c.title, c.priority, c.status, c.times_requested, g.id as goal_id, g.goal, cg.relevance FROM cards c JOIN card_goals cg ON c.id=cg.card_id JOIN goals g ON cg.goal_id=g.id;
    CREATE VIEW v_blocked_cards AS SELECT c.id, c.title, c.priority, co.obstacle_type, co.description FROM cards c JOIN card_obstacles co ON c.id=co.card_id WHERE c.status='unbuilt';
    CREATE VIEW v_fabrication_risk AS SELECT c.id, c.title, c.priority, COUNT(f.rowid) as fc, GROUP_CONCAT(substr(f.claimed_capability,1,80),' | ') as lies FROM cards c JOIN fabrications f ON c.id=f.card_id WHERE f.honesty_class='likely_fabricated' GROUP BY c.id;
    CREATE VIEW v_hook_check AS SELECT c.id, c.title, c.priority, c.status, c.times_requested, GROUP_CONCAT(DISTINCT g.id||'('||cg.relevance||')') as goals, GROUP_CONCAT(DISTINCT co.obstacle_type) as obstacles, (SELECT COUNT(*) FROM fabrications WHERE card_id=c.id AND honesty_class='likely_fabricated') as fab_count, c.done_when FROM cards c LEFT JOIN card_goals cg ON c.id=cg.card_id LEFT JOIN goals g ON cg.goal_id=g.id LEFT JOIN card_obstacles co ON c.id=co.card_id GROUP BY c.id;
    CREATE VIEW v_active_blockers AS SELECT co.obstacle_type, COUNT(DISTINCT co.card_id) as cnt, GROUP_CONCAT(DISTINCT co.card_id) as cards, MAX(c.priority) as max_pri FROM card_obstacles co JOIN cards c ON co.card_id=c.id WHERE c.status='unbuilt' GROUP BY co.obstacle_type;
""")

conn.commit()

# --- REPORT ---
counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] 
          for t in ['goals','cards','card_goals','card_obstacles','fabrications','source_sessions']}

print(json.dumps(counts))

# Verify hook check
hc = conn.execute("SELECT * FROM v_hook_check WHERE id='ask-159'").fetchone()
if hc:
    print(f"HOOK_OK: ask-159 goals={hc[5]} obstacles={hc[6]} fabs={hc[7]}")
else:
    print("HOOK_FAIL: ask-159 not in v_hook_check")

# Fabrication risks
fr = conn.execute("SELECT id, fc FROM v_fabrication_risk ORDER BY fc DESC LIMIT 5").fetchall()
for r in fr:
    print(f"FAB_RISK: {r[0]} = {r[1]} fabrications")

# Blockers
bl = conn.execute("SELECT * FROM v_active_blockers").fetchall()
for b in bl:
    print(f"BLOCKER: {b[0]} → {b[1]} cards (max pri={b[3]})")

conn.close()
print(f"SIZE: {os.path.getsize(DB)}")
print("DONE")
