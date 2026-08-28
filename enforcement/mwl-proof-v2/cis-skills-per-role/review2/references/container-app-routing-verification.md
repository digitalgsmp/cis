# Container App Routing — Verification Technique

## Problem

When adding a static Flask route under a path prefix that already has a dynamic catch-all (e.g. `/api/relay/<run_id>`), you need to verify that the static route will actually win the routing match. Visual inspection of the code isn't enough — Werkzeug's routing priority rules need empirical confirmation.

## Verification Procedure

### 1. Dump the live URL map

```python
import sys, os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "/workspace/cis/runtime")
sys.path.insert(0, "/workspace/cis/runtime/abstraction")
from container_app import app

rules = sorted(app.url_map.iter_rules(), key=lambda r: str(r))
for r in rules:
    print(f"  {r.rule}  endpoint={r.endpoint}  methods={sorted(r.methods)}")
```

Confirm the new route is NOT yet registered. Confirm the catch-all exists.

### 2. Test current (pre-change) routing

```python
adapter = app.url_map.bind("localhost")
endpoint, params = adapter.match("/api/relay/ping", method="GET")
# Before adding static route: endpoint='relay.relay_status', params={'run_id': 'ping'}
```

This proves the catch-all swallows the literal path.

### 3. Simulate the route addition and re-test

```python
@app.route("/api/relay/ping", methods=["GET"])
def _test_relay_ping():
    from flask import jsonify
    return jsonify({"status": "ok"})

# Re-test routing
adapter = app.url_map.bind("localhost")
endpoint, params = adapter.match("/api/relay/ping", method="GET")
# After: endpoint='_test_relay_ping', params={}

# Verify catch-all still works for real run_ids
endpoint, params = adapter.match("/api/relay/run-abc123", method="GET")
# Still: endpoint='relay.relay_status', params={'run_id': 'run-abc123'}
```

### 4. Test via Flask test client

```python
with app.test_client() as client:
    resp = client.get("/api/relay/ping")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
```

### 5. Verify no DB side effects

The catch-all `relay_status` calls `_db()` which executes `PRAGMA journal_mode=WAL` (a write operation). The new static route must NOT touch the DB. Check by confirming the route handler has no `_db()`, `sqlite3`, or `conn` calls.

## Key Insight

Werkzeug sorts static rules ahead of dynamic `<converter>` rules regardless of registration order. This is already relied on in the existing app: `/api/relay/health`, `/api/relay/runs`, `/api/relay/system/health` all coexist with `/api/relay/<run_id>` without conflict. No blueprint changes are needed — defining the route as `@app.route` in `container_app.py` is sufficient.

## Environment Note

In a test environment where the spine DB file is absent, hitting the catch-all with a bogus run_id returns 500 (`OperationalError: unable to open database file`), not 404. In production (DB present), it returns 404 "Run not found" after opening the DB with WAL. Either way, the misrouting into DB machinery is the problem the static route solves.
