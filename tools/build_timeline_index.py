#!/usr/bin/env python3
"""Build deterministic timeline index from all 7 Hermes profile DBs + assessment classifications."""
import sqlite3, os, json
from datetime import datetime

DB = "/mnt/projects/cis/cards/timeline_index.db"
if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")

conn.executescript("""
    CREATE TABLE messages (
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        orig_id INTEGER, profile TEXT NOT NULL, session_id TEXT NOT NULL,
        role TEXT NOT NULL, content TEXT NOT NULL, content_hash TEXT,
        timestamp REAL, date TEXT, week TEXT, content_type TEXT
    );
    CREATE TABLE sessions (
        session_id TEXT NOT NULL, profile TEXT NOT NULL,
        model TEXT, source TEXT, started_at REAL, ended_at REAL,
        title TEXT, message_count INTEGER,
        PRIMARY KEY (session_id, profile)
    );
    CREATE TABLE exchanges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile TEXT NOT NULL, session_id TEXT NOT NULL,
        user_msg_id INTEGER, asst_msg_id INTEGER,
        classification TEXT, was_productive INTEGER, failure_reason TEXT
    );
    CREATE INDEX idx_msg_date ON messages(date);
    CREATE INDEX idx_msg_week ON messages(week);
    CREATE INDEX idx_msg_session ON messages(session_id);
    CREATE INDEX idx_exch_session ON exchanges(session_id);
""")

PROFILES = {
    'v4pro':      '/home/eric/.hermes-v4pro/state.db',
    'r1':         '/home/eric/.hermes-r1/state.db',
    'qwen':       '/home/eric/.hermes-qwen/state.db',
    'v4impl':     '/home/eric/.hermes-v4impl/state.db',
    'glm-review': '/home/eric/.hermes-glm-reviewer/state.db',
    'glm-verify': '/home/eric/.hermes-glm-verifier/state.db',
    'brainstorm': '/home/eric/.hermes-brainstorm/state.db',
}

CODE_PREFIXES = ('```','#!/','import ','def ','class ','curl ','git ','cd ','ls ',
                 'python3','SELECT','INSERT','npm','pip','docker','systemctl','sudo',
                 'echo','export','source ','./','cp ','mv ','rm ','mkdir','chmod')

total_msgs = 0
total_exchanges = 0

for profile, db_path in PROFILES.items():
    if not os.path.exists(db_path):
        print(f"  SKIP {profile}: no DB")
        continue
    
    pconn = sqlite3.connect("file:" + db_path + "?mode=ro", uri=True)
    
    # Sessions
    for sid, model, source, start, end, mc, title in pconn.execute(
        "SELECT id, model, source, started_at, ended_at, message_count, title FROM sessions"
    ).fetchall():
        conn.execute(
            "INSERT OR IGNORE INTO sessions VALUES(?,?,?,?,?,?,?,?)",
            (str(sid), profile, model or '', source or '', start or 0, end or 0, title or '', mc or 0)
        )
    
    # Messages
    msgs = pconn.execute("""
        SELECT m.id, m.session_id, m.role, m.content, m.timestamp
        FROM messages m WHERE m.content IS NOT NULL AND length(m.content) > 0
        ORDER BY m.session_id, m.timestamp, m.id
    """).fetchall()
    
    pending_user = {}
    
    for mid, sid, role, content, ts in msgs:
        content = str(content)[:2000]
        dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts and ts > 0 else ''
        wk = datetime.fromtimestamp(ts).strftime('%Y-W%W') if ts and ts > 0 else ''
        ch = str(hash(content))[:16]
        
        # Content type
        fl = content.strip().split('\n')[0][:80] if content.strip() else ''
        ctype = 'code' if any(fl.startswith(p) for p in CODE_PREFIXES) else 'text'
        
        cursor = conn.execute(
            "INSERT INTO messages(orig_id,profile,session_id,role,content,content_hash,timestamp,date,week,content_type) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (mid, profile, str(sid), role, content, ch, ts or 0, dt, wk, ctype)
        )
        new_id = cursor.lastrowid
        total_msgs += 1
        
        skey = profile + ":" + str(sid)
        if role == 'user':
            pending_user[skey] = new_id
        elif role == 'assistant' and skey in pending_user:
            uid = pending_user.pop(skey)
            conn.execute(
                "INSERT INTO exchanges(profile,session_id,user_msg_id,asst_msg_id) VALUES(?,?,?,?)",
                (profile, str(sid), uid, new_id)
            )
            total_exchanges += 1
    
    pconn.close()
    print("  {}: {} messages so far".format(profile, total_msgs))

# Join classifications from assessment.db
assess = sqlite3.connect("file:/mnt/projects/cis/cards/assessment.db?mode=ro", uri=True)
class_rows = assess.execute("""
    SELECT session_id, profile, model_response_type, was_productive, failure_reason
    FROM exchange_classifications WHERE session_id IS NOT NULL AND session_id != ''
""").fetchall()
assess.close()

classified = 0
# Match classifications to exchanges by session/profile
class_map = {}
for sess_id, prof, rtype, productive, reason in class_rows:
    key = (sess_id, prof)
    if key not in class_map:
        class_map[key] = []
    class_map[key].append((rtype, productive, reason))

for (sess_id, prof), items in class_map.items():
    # Get unclassified exchanges for this session
    exch_rows = conn.execute(
        "SELECT id FROM exchanges WHERE session_id=? AND classification IS NULL ORDER BY id",
        (sess_id,)
    ).fetchall()
    for i, (rtype, productive, reason) in enumerate(items):
        if i < len(exch_rows):
            conn.execute(
                "UPDATE exchanges SET classification=?, was_productive=?, failure_reason=? WHERE id=?",
                (rtype, productive, reason, exch_rows[i][0])
            )
            classified += 1

# Views
conn.executescript("""
    CREATE VIEW v_timeline AS
    SELECT date, week, profile, session_id, role, content_type,
           substr(content,1,300) as preview, content_hash
    FROM messages WHERE role='user' ORDER BY timestamp;
    
    CREATE VIEW v_weekly_summary AS
    SELECT week, profile,
           COUNT(*) as msg_count,
           COUNT(DISTINCT session_id) as session_count
    FROM messages WHERE role='user'
    GROUP BY week, profile ORDER BY week;
    
    CREATE VIEW v_struggle_evidence AS
    SELECT m.date, e.profile, e.session_id,
           substr(m.content,1,200) as user_msg,
           e.classification, e.was_productive, e.failure_reason
    FROM exchanges e
    JOIN messages m ON e.user_msg_id = m.rowid
    WHERE e.classification IS NOT NULL AND e.was_productive = 0
    ORDER BY m.date;
""")

conn.commit()

# Report
user_count = conn.execute("SELECT COUNT(*) FROM messages WHERE role='user'").fetchone()[0]
sess_count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
dr = conn.execute("SELECT MIN(date), MAX(date) FROM messages WHERE role='user' AND date!=''").fetchone()
sc = conn.execute("SELECT COUNT(*) FROM v_struggle_evidence").fetchone()[0]

print("\n=== timeline_index.db ===")
print("  messages: {}".format(total_msgs))
print("  user messages: {}".format(user_count))
print("  sessions: {}".format(sess_count))
print("  exchanges: {}".format(total_exchanges))
print("  classified exchanges: {}".format(classified))
print("  date range: {} to {}".format(dr[0], dr[1]))
print("  struggle evidence: {} unproductive exchanges".format(sc))

# Sample
print("\n=== TIMELINE SAMPLE ===")
for r in conn.execute("SELECT date, profile, substr(preview,1,100) FROM v_timeline LIMIT 3").fetchall():
    print("  {} [{}] {}...".format(r[0], r[1], r[2]))

print("\n=== STRUGGLE SAMPLE ===")
for r in conn.execute("SELECT date, profile, classification, substr(user_msg,1,100) FROM v_struggle_evidence LIMIT 5").fetchall():
    print("  {} [{}] {}: {}...".format(r[0], r[1], r[2], r[3]))

conn.close()
print("\nSIZE: {} bytes".format(os.path.getsize(DB)))
print("DONE")
