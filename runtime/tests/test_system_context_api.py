"""
test_system_context_api.py — Flask endpoint tests for the Workbench System
Context / Recovery UI backend (CARD_03_WORKBENCH_SYSTEM_CONTEXT_UI.md,
queue 4.30): GET /api/workbench/system-context and
GET /api/workbench/system-context/recovery-packet.

Exercises the real endpoints through Flask's test client, pointed at a
scratch database (never production for anything that could mutate),
reusing tools/state/tests/test_canonical_state.py's fixture builder so the
schema stays in one place. Compares route output directly against calling
canonical_state.py / recovery_packet.py in-process, since Card 03 requires
the UI/backend to consume Cards 01-02's canonical read model rather than
reconstructing another truth -- if the route ever drifted from those
modules' own output, that would be exactly the bug this file exists to
catch.

Run: python3 runtime/tests/test_system_context_api.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'state'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'state', 'tests'))

os.environ.setdefault("CIS_PIPELINE_API_KEY", "")

import canonical_state as cs  # noqa: E402
import recovery_packet as rp  # noqa: E402
from test_canonical_state import make_scratch_db, table_counts  # noqa: E402

import container_app  # noqa: E402
from container_app import app  # noqa: E402

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def _use_scratch_db(path):
    """canonical_state.DB is a module-level constant read at import time;
    recovery_packet.py imports the SAME module object (sys.modules caches
    it), so patching cs.DB here redirects both, exactly the way the route
    handlers themselves resolve the database with no caller-supplied path."""
    orig = cs.DB
    cs.DB = path
    return orig


def _restore_db(orig):
    cs.DB = orig


def test_system_context_matches_canonical_state():
    tmp, path, conn = make_scratch_db()
    orig = _use_scratch_db(path)
    client = app.test_client()
    try:
        resp = client.get("/api/workbench/system-context")
        check("GET /api/workbench/system-context returns 200", resp.status_code == 200, resp.status_code)
        body = resp.get_json()
        direct = cs.get_canonical_state()
        # revision/computed_at compare directly; computed_at has wall-clock
        # jitter across the two calls so only its presence is checked.
        check("route revision matches direct canonical_state.get_canonical_state() call",
              body["revision"] == direct["revision"], f"route={body['revision']} direct={direct['revision']}")
        check("route queue_focus matches direct call", body["queue_focus"] == direct["queue_focus"], "mismatch")
        check("route observed_runtime_health section present and separate from authority",
              "observed_runtime_health" in body and "queue_focus" in body, sorted(body.keys()))
    finally:
        _restore_db(orig)
        conn.close()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_full_recovery_packet_matches_generator():
    tmp, path, conn = make_scratch_db()
    orig = _use_scratch_db(path)
    client = app.test_client()
    try:
        resp = client.get("/api/workbench/system-context/recovery-packet")
        check("GET recovery-packet (full) returns 200", resp.status_code == 200, resp.status_code)
        body = resp.get_json()
        direct = rp.build_recovery_packet()
        check("full packet's state_revision matches direct generator call",
              body["state_revision"] == direct["state_revision"], "mismatch")
        check("full packet's authority_statement matches direct generator call",
              body["authority_statement"] == direct["authority_statement"], "mismatch")
        check("full packet's queue_focus matches direct generator call",
              body["queue_focus"] == direct["queue_focus"], "mismatch")
    finally:
        _restore_db(orig)
        conn.close()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_focused_recovery_packet_matches_generator():
    tmp, path, conn = make_scratch_db()
    orig = _use_scratch_db(path)
    client = app.test_client()
    try:
        for issue in sorted(rp.ISSUE_AREAS):
            resp = client.get(f"/api/workbench/system-context/recovery-packet?issue={issue}")
            check(f"GET recovery-packet?issue={issue} returns 200", resp.status_code == 200, resp.status_code)
            body = resp.get_json()
            direct = rp.build_recovery_packet(issue=issue)
            # generated_at / state_computed_at are wall-clock timestamps
            # taken independently by each call, so they legitimately
            # differ between the route's call and this test's direct call
            # a moment later.
            _skip = {"generated_at", "state_computed_at"}
            body_cmp = {k: v for k, v in body.items() if k not in _skip}
            direct_cmp = {k: v for k, v in direct.items() if k not in _skip}
            check(f"focused packet ({issue}) matches direct generator call",
                  body_cmp == direct_cmp, f"route keys={sorted(body.keys())} direct keys={sorted(direct.keys())}")
    finally:
        _restore_db(orig)
        conn.close()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_unknown_issue_area_rejected_with_400():
    client = app.test_client()
    resp = client.get("/api/workbench/system-context/recovery-packet?issue=not_a_real_area")
    check("unknown ?issue is rejected with 400, not a silent full packet",
          resp.status_code == 400, resp.status_code)
    body = resp.get_json()
    check("400 response names the known issue areas", "known_issue_areas" in body, body)


def test_canonical_state_failure_returns_503_not_500():
    """A failure inside canonical_state.py (spine unreachable, etc.) must
    surface as a clean error, not a 500 traceback and not a fabricated
    200 — the honesty requirement from Card 03's failure-behavior section."""
    client = app.test_client()
    orig = cs.get_canonical_state

    def _boom(*a, **kw):
        raise RuntimeError("simulated spine failure")

    cs.get_canonical_state = _boom
    try:
        resp = client.get("/api/workbench/system-context")
        check("canonical_state failure -> 503, not 500", resp.status_code == 503, resp.status_code)
        body = resp.get_json()
        check("503 body carries an error field naming the exception type",
              "error" in body and "RuntimeError" in body["error"], body)
    finally:
        cs.get_canonical_state = orig


def test_recovery_packet_failure_returns_503_not_500():
    client = app.test_client()
    orig = rp.build_recovery_packet

    def _boom(*a, **kw):
        raise RuntimeError("simulated packet failure")

    rp.build_recovery_packet = _boom
    try:
        resp = client.get("/api/workbench/system-context/recovery-packet")
        check("recovery_packet failure -> 503, not 500", resp.status_code == 503, resp.status_code)
        body = resp.get_json()
        check("503 body carries an error field naming the exception type",
              "error" in body and "RuntimeError" in body["error"], body)
    finally:
        rp.build_recovery_packet = orig


def test_no_caller_supplied_db_path_accepted():
    """The route must never let a client point the Workbench at an
    arbitrary file on disk — no db_path/db query param is read at all."""
    client = app.test_client()
    resp = client.get("/api/workbench/system-context?db=/etc/passwd")
    check("a 'db' query param is silently ignored, not honored as a path override",
          resp.status_code == 200, resp.status_code)


def test_no_mutation_from_repeated_reads():
    tmp, path, conn = make_scratch_db()
    conn.execute(
        "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
        "need_status, source_line, source_sha) VALUES "
        "('9.3', 9, 'mutation guard (route)', '### 9.3 x', 'heading', 'OPEN', 1, 'x')"
    )
    conn.commit()
    orig = _use_scratch_db(path)
    client = app.test_client()
    try:
        before_counts = table_counts(conn)
        before_rev = cs.compute_state_revision(conn)

        client.get("/api/workbench/system-context")
        client.get("/api/workbench/system-context/recovery-packet")
        client.get("/api/workbench/system-context/recovery-packet?issue=queue")

        after_counts = table_counts(conn)
        after_rev = cs.compute_state_revision(conn)
        check("no authority table row count changed after hitting every route",
              before_counts == after_counts, f"before={before_counts} after={after_counts}")
        check("state revision is unchanged by view/copy reads",
              before_rev == after_rev, f"before={before_rev} after={after_rev}")
    finally:
        _restore_db(orig)
        conn.close()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_works_with_no_gateways_or_pipeline_running():
    """No Braingate/Card Factory/Card Runner/gateway process is expected to
    be reachable in this test environment — exactly the condition Card 03
    requires the screen to tolerate. Must return 200 with plain bool
    health flags, never raise."""
    client = app.test_client()
    resp = client.get("/api/workbench/system-context")
    check("system-context succeeds with no pipeline/gateway processes running",
          resp.status_code == 200, resp.status_code)
    body = resp.get_json()
    gw = body.get("observed_runtime_health", {}).get("gateways", {})
    check("every gateway observation is a plain bool, not an error",
          all(isinstance(v.get("listening"), bool) for v in gw.values()), gw)


def run():
    test_system_context_matches_canonical_state()
    test_full_recovery_packet_matches_generator()
    test_focused_recovery_packet_matches_generator()
    test_unknown_issue_area_rejected_with_400()
    test_canonical_state_failure_returns_503_not_500()
    test_recovery_packet_failure_returns_503_not_500()
    test_no_caller_supplied_db_path_accepted()
    test_no_mutation_from_repeated_reads()
    test_works_with_no_gateways_or_pipeline_running()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
