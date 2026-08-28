#!/usr/bin/env python3
"""Verification battery for a POST relay endpoint chunk (CIS runtime).

Proves completion criteria with raw evidence: Flask test_client + sqlite3 reads.
Matches the runtime/tests/ plain-script convention (results list, N/M passed, exit 1 on FAIL).

Usage:
    CIS_SPINE_PATH=/workspace/cis/data/cis_memory.db python3 verify_relay_endpoint.py

CAUTION: creates REAL workflow_runs rows and drives LIVE gateways (8644-8648)
with real tokens. Use a trivial smoke intent. Daemon threads die when this
process exits — mid-flight runs recover via relay.resume (same as /start).

Auth matrix (401/200) MUST run in a separate process because api.relay reads
CIS_PIPELINE_API_KEY at import time:
    CIS_PIPELINE_API_KEY=testkey python3 -c "
    import sys; sys.path.insert(0, '<runtime_dir>')
    from container_app import app
    c = app.test_client()
    print(c.post('/api/relay/run', json={'intent':'x'}).status_code)                 # 401
    print(c.post('/api/relay/run', json={'intent':'y'}, headers={'Authorization':'Bearer testkey'}).status_code)  # 200
    print(c.post('/api/relay/run', json={'intent':'z'}, headers={'Authorization':'Bearer wrong'}).status_code)     # 401
    "
"""
import os
import re
import sqlite3
import sys
import time

RUNTIME_DIR = os.environ.get("CIS_RUNTIME_DIR", "/workspace/cis/runtime")
sys.path.insert(0, RUNTIME_DIR)
DB_PATH = os.environ.get("CIS_SPINE_PATH", "/workspace/cis/data/cis_memory.db")

from container_app import app  # noqa: E402
import api.relay as api_relay  # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append((label, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {label}  {detail}")


c = app.test_client()

r = c.get("/api/health")
check("GET /api/health -> 200", r.status_code == 200, f"{r.status_code}")

r = c.get("/api/relay/run")
body = r.get_json() or {}
check(
    "GET /api/relay/run -> 404 Run not found (dynamic rule, not 405)",
    r.status_code == 404 and body.get("run_id") == "run",
    f"{r.status_code} {body}",
)

r = c.post("/api/relay/run", json={})
check(
    "missing intent -> 400",
    r.status_code == 400 and (r.get_json() or {}) == {"error": "intent required"},
    f"{r.status_code} {r.get_json()}",
)

r = c.post("/api/relay/run", data="garbage", content_type="application/json")
check(
    "non-JSON body -> 400",
    r.status_code == 400 and (r.get_json() or {}).get("error") == "intent required",
    f"{r.status_code} {r.get_json()}",
)

r = c.post("/api/relay/start", json={})
check(
    "POST /api/relay/start regression (400 on empty body, no run created)",
    r.status_code == 400,
    f"{r.status_code} {r.get_json()}",
)

intent = "smoke: reply with the single word OK and nothing else, use no tools"
r = c.post("/api/relay/run", json={"intent": intent})
data = r.get_json() or {}
run_id = data.get("run_id", "")
check(
    "happy path -> 200 + run_id regex + BRAIN_PHASE",
    r.status_code == 200
    and bool(re.fullmatch(r"run-[0-9a-f]{16}-[0-9]{10}", run_id))
    and data.get("status") == "BRAIN_PHASE",
    f"{r.status_code} run_id={run_id!r} status={data.get('status')!r}",
)
check(
    "response shape parity with /start",
    set(data.keys()) >= {"run_id", "status", "message"},
    f"keys={sorted(data.keys())}",
)

r = c.get(f"/api/relay/{run_id}")
d = r.get_json() or {}
check(
    "background.active true immediately after POST",
    r.status_code == 200 and d.get("background", {}).get("active") is True,
    f"active={d.get('background', {}).get('active')} status={d.get('status')}",
)
entry = api_relay._active_runs.get(run_id)
check(
    "daemon thread alive in _active_runs",
    bool(entry and entry.get("thread") and entry["thread"].is_alive()),
    f"entry_keys={list(entry or {})}",
)

# PRAGMA first — workflow_runs schema has drifted before (no created_by column).
conn = sqlite3.connect(DB_PATH)
cols = [c[1] for c in conn.execute("PRAGMA table_info(workflow_runs)").fetchall()]
sel = "id, status, result" + (", rounds_completed" if "rounds_completed" in cols else "")
row = conn.execute(f"SELECT {sel} FROM workflow_runs WHERE id = ?", (run_id,)).fetchone()
check("workflow_runs row exists", row is not None, f"row={row}")
if row:
    check("DB status not INTAKE (start_sync transitioned synchronously)", row[1] != "INTAKE", f"status={row[1]}")

advanced = False
final_state = "no advance within window"
for _ in range(15):
    time.sleep(5)
    d = (c.get(f"/api/relay/{run_id}").get_json()) or {}
    bg = d.get("background", {})
    status = d.get("status")
    if (not bg.get("active")) or (status and status != "BRAIN_PHASE") or d.get("rounds_completed", 0) > 0:
        advanced = True
        final_state = (
            f"status={status} rounds={d.get('rounds_completed')} "
            f"active={bg.get('active')} error={bg.get('error')}"
        )
        break
entry_now = api_relay._active_runs.get(run_id)
thread_ran = bool(entry_now and ("finished_at" in entry_now or not entry_now["thread"].is_alive()))
check("pipeline advanced or thread finished within 75s", advanced or thread_ran, final_state)
conn.close()

print()
fails = [l for l, ok, _ in results if not ok]
print(f"{len(results) - len(fails)}/{len(results)} passed.")
if fails:
    print("FAILED:", [l for l, ok2, _ in results if not ok2])
    sys.exit(1)
print("ALL PASS")
