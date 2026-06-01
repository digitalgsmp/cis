#!/usr/bin/env python3
"""
cis_test_queue.py
ADR-045 Step 2 — Test all four queue API routes

Replaces manual curl commands or browser testing of queue routes.
Requires Flask to be running on 127.0.0.1:5000.

Tests:
  1. POST /api/queue/enqueue       — enqueue a verify_contract job
  2. GET  /api/queue/status        — list all jobs
  3. GET  /api/queue/status?status=queued — filter by status
  4. GET  /api/queue/job/<id>      — get job detail
  5. POST /api/queue/cancel/<id>   — cancel the queued job
  6. GET  /api/queue/job/<id>      — confirm status is cancelled
  7. Enqueue invalid job_type      — confirm rejection
  8. Cancel non-queued job         — confirm rejection

Usage:
    python3 /mnt/projects/cis/runtime/cis_test_queue.py

Writes results to:
    /mnt/projects/cis/logs/queue_test_log.md
"""

import json
import sys
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE     = "http://127.0.0.1:5000"
LOG_PATH = "/mnt/projects/cis/logs/queue_test_log.md"
passed   = 0
failed   = 0
results  = []


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def post(path, body):
    data = json.dumps(body).encode()
    req  = Request(f"{BASE}{path}", data=data,
                   headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except HTTPError as e:
        try:
            return json.loads(e.read()), e.code
        except Exception:
            return {"error": str(e)}, e.code
    except Exception as e:
        return {"error": str(e)}, 0


def get(path):
    req = Request(f"{BASE}{path}", method="GET")
    try:
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except Exception as e:
        return {"error": str(e)}, 0


def check(label, ok, detail=""):
    global passed, failed
    status = "PASS" if ok else "FAIL"
    line   = f"{status}  {label}" + (f" — {detail}" if detail else "")
    results.append(line)
    print(line)
    if ok:
        passed += 1
    else:
        failed += 1


print(f"\nQUEUE ROUTE TEST")
print(f"Run time: {now()}")
print(f"Base URL: {BASE}")
print("-" * 60)

# ── Check Flask is up ──────────────────────────────────────────────────────────
try:
    data, code = get("/api/queue/status")
    check("Flask is reachable", code == 200, f"HTTP {code}")
except Exception as e:
    check("Flask is reachable", False, str(e))
    print("\nFATAL: Flask not running. Start Flask and retry.")
    sys.exit(1)

# ── Test 1: Enqueue a valid job ────────────────────────────────────────────────
data, code = post("/api/queue/enqueue", {
    "job_type": "verify_contract",
    "source":   "cis_test_queue.py",
    "payload":  json.dumps({"contract": "test_contract.md"})
})
check("Enqueue verify_contract job", code == 200 and data.get("success"), f"job_id={data.get('job_id')}")
job_id = data.get("job_id")

# ── Test 2: List all jobs ──────────────────────────────────────────────────────
data, code = get("/api/queue/status")
check("GET /api/queue/status returns jobs", code == 200 and "jobs" in data, f"count={data.get('count')}")

# ── Test 3: Filter by status ───────────────────────────────────────────────────
data, code = get("/api/queue/status?status=queued")
has_our_job = any(j.get("id") == job_id for j in data.get("jobs", []))
check("Filter by status=queued includes our job", code == 200 and has_our_job, f"count={data.get('count')}")

# ── Test 4: Job detail ─────────────────────────────────────────────────────────
if job_id:
    data, code = get(f"/api/queue/job/{job_id}")
    check("GET /api/queue/job/<id> returns job", code == 200 and data.get("found"),
          f"status={data.get('job', {}).get('status')}")
else:
    check("GET /api/queue/job/<id>", False, "no job_id from enqueue")

# ── Test 5: Cancel the job ─────────────────────────────────────────────────────
if job_id:
    data, code = post(f"/api/queue/cancel/{job_id}", {})
    check("Cancel queued job", code == 200 and data.get("success"),
          f"status={data.get('status')}")

# ── Test 6: Confirm cancelled ──────────────────────────────────────────────────
if job_id:
    data, code = get(f"/api/queue/job/{job_id}")
    check("Cancelled job status confirmed", data.get("job", {}).get("status") == "cancelled")

# ── Test 7: Reject invalid job_type ───────────────────────────────────────────
data, code = post("/api/queue/enqueue", {
    "job_type": "invalid_type",
    "source":   "cis_test_queue.py"
})
check("Invalid job_type rejected", code == 400 and not data.get("success"),
      data.get("error", "")[:60])

# ── Test 8: Cancel non-queued job ─────────────────────────────────────────────
if job_id:
    data, code = post(f"/api/queue/cancel/{job_id}", {})
    check("Cancel non-queued job rejected", code == 409 and not data.get("success"),
          data.get("error", "")[:60])

# ── Summary ────────────────────────────────────────────────────────────────────
print("-" * 60)
overall  = "PASS" if failed == 0 else "FAIL"
summary  = f"Result: {overall} — {passed} passed, {failed} failed"
blocking = "NO" if failed == 0 else "YES — do not advance to Step 3 until resolved"
print(summary)
print(f"Blocking: {blocking}")

results += [summary, f"Blocking: {blocking}"]

# ── Write log ──────────────────────────────────────────────────────────────────
try:
    entry = f"\n## {now()} — ADR-045 Step 2 Queue Route Test\n" + "\n".join(results) + "\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"\nLog written: {LOG_PATH}")
except Exception as e:
    print(f"WARNING: Could not write log: {e}")

sys.exit(0 if failed == 0 else 1)
