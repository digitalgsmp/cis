#!/usr/bin/env python3
"""Continuous concept dossier mining across all 5 databases."""
import sqlite3, json, subprocess, datetime, sys, os

QWEN_URL = "http://127.0.0.1:8002/v1/chat/completions"
OUTPUT_FILE = "/mnt/projects/cis/data/taxonomy_mine/mining_dossiers.jsonl"
PROGRESS_FILE = "/mnt/projects/cis/data/taxonomy_mine/mining_progress.json"
BATCH_SIZE = 50

SOURCES = {
    "cis_spine": ("/mnt/projects/cis/data/cis_memory.db", "knowledge_messages",
                  "WHERE role='human' AND content IS NOT NULL AND content != ''",
                  "content", "timestamp", "source_key"),
    "prime": ("/home/eric/.hermes-v4pro/state.db", "messages",
              "WHERE role='user' AND content IS NOT NULL AND content != '' AND active=1",
              "content", "timestamp", "session_id"),
    "r1": ("/home/eric/.hermes-r1/state.db", "messages",
           "WHERE role='user' AND content IS NOT NULL AND content != '' AND active=1",
           "content", "timestamp", "session_id"),
    "glm": ("/home/eric/.hermes-glm-verifier/state.db", "messages",
            "WHERE role='user' AND content IS NOT NULL AND content != '' AND active=1",
            "content", "timestamp", "session_id"),
    "qwen": ("/home/eric/.hermes-qwen/state.db", "messages",
             "WHERE role='user' AND content IS NOT NULL AND content != '' AND active=1",
             "content", "timestamp", "session_id"),
}

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"processed_ids": [], "total_concepts": 0, "batches": 0}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

def load_all_messages():
    """Load all human messages from all 5 DBs, ordered by timestamp."""
    processed = set(load_progress()["processed_ids"])
    all_msgs = []
    
    for source, (db_path, table, where, col, ts_col, session_col) in SOURCES.items():
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        query = f"SELECT ROWID as id, {col}, {ts_col}, {session_col} FROM {table} {where}"
        cur.execute(query)
        for row in cur.fetchall():
            msg_id = f"{source}:{row[0]}"
            if msg_id not in processed:
                content = row[1]
                if len(content) > 2000:
                    content = content[:2000]
                all_msgs.append({
                    "id": msg_id,
                    "source": source,
                    "content": content.replace('\n', ' ')[:2000],
                    "timestamp": str(row[2]),
                    "session": str(row[3]) if row[3] else "unknown"
                })
        conn.close()
    
    # Sort by timestamp, then source
    all_msgs.sort(key=lambda m: m["timestamp"])
    return all_msgs

def build_prompt(batch, batch_num):
    """Build a concise prompt for Qwen."""
    msg_lines = []
    for m in batch:
        msg_lines.append(f"[{m['id']}|{m['source']}|{m['timestamp'][:19]}] {m['content'][:1500]}")
    
    return f"""Concept miner. Return JSON array of dossiers. Each: concept_name, aliases, problem_or_function, verbatim_evidence(exact quotes), source, message_id, timestamp, attribution:'user', stance{{label,evidence_span,confidence}}, uncertainties[], related_but_distinct[].

MUST-NOT-MERGE: WIAS/WIASW≠SWA, CIS product≠enforcement, creative≠pipeline, Hermes CP≠portal, archive≠live KB.

BATCH {batch_num}: {len(batch)} messages.

{chr(10).join(msg_lines)}

Return only: [{{"concept_name":"...","aliases":[],...}}]"""

def process_batch(batch, batch_num):
    prompt = build_prompt(batch, batch_num)
    payload = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    })
    
    result = subprocess.run([
        "curl", "-s", "--max-time", "300",
        "-X", "POST", QWEN_URL,
        "-H", "Content-Type: application/json",
        "-d", payload
    ], capture_output=True, text=True, timeout=310)
    
    try:
        data = json.loads(result.stdout)
        content = data['choices'][0]['message']['content']
    except:
        print(f"  ERROR parsing response: {result.stdout[:200]}")
        return [], batch
    
    # Extract JSON array
    import re
    # Remove markdown wrapper
    content = re.sub(r'^```(?:json)?\s*\n', '', content)
    content = re.sub(r'\n```\s*$', '', content)
    
    try:
        dossiers = json.loads(content)
        if isinstance(dossiers, dict):
            dossiers = dossiers.get('output', dossiers).get('provisional_concept_dossiers', [])
        if not isinstance(dossiers, list):
            dossiers = [dossiers]
    except json.JSONDecodeError:
        print(f"  JSON parse error, trying recovery...")
        # Try to close truncated JSON
        open_b = content.count('{') - content.count('}')
        content += '}' * max(open_b, 0)
        try:
            dossiers = json.loads(content)
            if isinstance(dossiers, list):
                pass
            elif isinstance(dossiers, dict):
                dossiers = dossiers.get('output', dossiers).get('provisional_concept_dossiers', [dossiers])
        except:
            print(f"  Recovery failed, saving raw")
            with open(f"/mnt/projects/cis/data/taxonomy_mine/batch_{batch_num}_raw.txt", "w") as f:
                f.write(result.stdout)
            return [], batch
    
    return dossiers if isinstance(dossiers, list) else [], batch

def main():
    progress = load_progress()
    all_msgs = load_all_messages()
    total = len(all_msgs)
    
    if total == 0:
        print("All messages already processed!")
        return
    
    print(f"Total unprocessed: {total}")
    batches = [all_msgs[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    print(f"Batches: {len(batches)}")
    
    total_concepts = 0
    start_time = datetime.datetime.now()
    
    for i, batch in enumerate(batches):
        batch_num = progress["batches"] + i + 1
        print(f"\nBatch {batch_num}/{progress['batches'] + len(batches)}: {len(batch)} msgs...", end=" ", flush=True)
        
        dossiers, _ = process_batch(batch, batch_num)
        
        # Save dossiers
        with open(OUTPUT_FILE, "a") as f:
            for d in dossiers:
                d["_batch"] = batch_num
                f.write(json.dumps(d) + "\n")
        
        # Update progress
        for m in batch:
            progress["processed_ids"].append(m["id"])
        progress["total_concepts"] += len(dossiers)
        progress["batches"] = batch_num
        save_progress(progress)
        
        total_concepts += len(dossiers)
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        rate = (i + 1) / elapsed * len(batches) if elapsed > 0 else 0
        eta_min = (len(batches) - i - 1) / rate if rate > 0 else 0
        
        print(f"{len(dossiers)} concepts | {total_concepts} total | ~{eta_min:.0f}min remaining")
    
    elapsed = (datetime.datetime.now() - start_time).total_seconds()
    print(f"\nDONE: {total_concepts} concepts from {total} messages in {elapsed/60:.1f} minutes")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
