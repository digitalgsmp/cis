#!/usr/bin/env python3
"""
minutes_agent.py — Session dictation agent.
Watches the engineering log and produces structured session records.
Runs as a background process during development conversations.

Usage:
    python3 minutes_agent.py &
    
Output:
    Writes structured session records to /mnt/projects/cis/logs/session_records/
    Appends to the running engineering log with timestamps.
"""

import time
import os
import json
from datetime import datetime, timezone

LOG_PATH = "/mnt/projects/cis/logs/session_2026-05-12_engineering_log.md"
RECORDS_DIR = "/mnt/projects/cis/logs/session_records"
os.makedirs(RECORDS_DIR, exist_ok=True)

def get_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def get_log_size():
    try:
        return os.path.getsize(LOG_PATH)
    except:
        return 0

def produce_minutes():
    """Read the current log and produce a structured summary."""
    try:
        with open(LOG_PATH) as f:
            content = f.read()
    except:
        return None
    
    entries = []
    current = None
    for line in content.split("\n"):
        if line.startswith("### Entry"):
            if current:
                entries.append(current)
            current = {"title": line.strip(), "body": ""}
        elif current and line.strip():
            current["body"] += line + "\n"
    if current:
        entries.append(current)
    
    if not entries:
        return None
    
    record = {
        "timestamp": get_timestamp(),
        "session": "2026-05-12",
        "project": "CIS Kernel v1",
        "entries": len(entries),
        "summary": {
            "last_entry": entries[-1]["title"] if entries else None,
            "last_insight": entries[-1]["body"][:200] if entries else None
        }
    }
    
    # Write structured record
    record_path = os.path.join(RECORDS_DIR, f"minutes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(record_path, "w") as f:
        json.dump(record, f, indent=2)
    
    return record

if __name__ == "__main__":
    print(f"[Minutes Agent] Started at {get_timestamp()}")
    print(f"[Minutes Agent] Watching: {LOG_PATH}")
    print(f"[Minutes Agent] Records dir: {RECORDS_DIR}")
    
    last_size = get_log_size()
    
    try:
        while True:
            time.sleep(30)
            current_size = get_log_size()
            if current_size != last_size:
                record = produce_minutes()
                if record:
                    print(f"[Minutes Agent] Log changed — produced minutes: {record['entries']} entries")
                last_size = current_size
    except KeyboardInterrupt:
        print(f"\n[Minutes Agent] Stopped at {get_timestamp()}")
