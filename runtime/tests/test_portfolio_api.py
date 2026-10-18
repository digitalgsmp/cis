"""
test_portfolio_api.py — Flask endpoint tests for the Workbench Portfolio
backend: GET /api/workbench/portfolio and
GET /api/workbench/portfolio/projects/<project_id>.

Exercises the real endpoints through Flask's test client, pointed at a
scratch database built from the real migration file 0022_projects_table.sql
ONLY — never against production, and never against migration 0042 (removed
from this revision; no schema migration is part of this slice). Reuses
tools/state/tests/test_project_context.py's fixture builder so the schema
stays in one place, the same way test_system_context_api.py reuses
test_canonical_state.py's.

Compares route output directly against calling tools/state/portfolio.py
in-process, so the route can never drift from what the read model itself
returns, and asserts what this screen exists to guarantee: the browser is
never handed a raw server filesystem path, an unknown project_id (including
WIASW, which has no registry row) is a clean 404 and never a fallback to
another project's data, and CIS and SWA each resolve independently when
their own fixture exists.

Run: python3 runtime/tests/test_portfolio_api.py
"""
import os
import shutil
import sqlite3
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_HERE, ".."))                               # runtime/
sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "state"))              # read models
sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "state", "tests"))     # fixture builder

import canonical_state as cs  # noqa: E402
import portfolio as pf  # noqa: E402
import project_context as pc  # noqa: E402
from test_project_context import make_scratch_db, _make_reachable  # noqa: E402

import container_app  # noqa: E402
from container_app import app  # noqa: E402

# These two routes sit behind workbench_auth.check_auth() like every other
# Workbench read model. This file tests the READ MODEL exposed through the
# route, not the authorization contract — that has its own file,
# test_revision_127_containment.py — so it configures a credential once and
# presents it on every request, exactly as test_system_context_api.py and
# test_project_intelligence_api.py already do.
import authed_test_client  # noqa: E402

authed_test_client.install(app)

results = []

LIST_ROUTE = "/api/workbench/portfolio"


def detail_route(project_id):
    return f"/api/workbench/portfolio/projects/{project_id}"


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def _use_scratch_db(path):
    """canonical_state.DB is a module-level constant read at import time;
    portfolio.py and project_context.py both import the SAME module object
    (sys.modules caches it), so patching cs.DB here redirects every default
    lookup, exactly the way the route handlers themselves resolve the
    registry database with no caller-supplied path."""
    orig = cs.DB
    cs.DB = path
    return orig


def _restore_db(orig):
    cs.DB = orig


def _use_safe_root(root):
    orig = pc.SAFE_ROOT
    pc.SAFE_ROOT = root
    return orig


def _restore_safe_root(orig):
    pc.SAFE_ROOT = orig


def test_portfolio_list_matches_read_model():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    safe_root = os.path.join(tmp, "projects")
    orig_root = _use_safe_root(safe_root)
    _make_reachable(tmp, conn, "cis", safe_root)
    _make_reachable(tmp, conn, "swa", safe_root)
    client = app.test_client()
    try:
        resp = client.get(LIST_ROUTE)
        check("1a. GET /api/workbench/portfolio returns 200", resp.status_code == 200, resp.status_code)
        body = resp.get_json()
        direct = pf.list_projects(db_path=path)
        check("1b. the route's body matches a direct list_projects() call",
              body == direct, (body, direct))
        check("1c. exactly the registry's two current rows are present, no wiasw",
              {p["id"] for p in body["projects"]} == {"cis", "swa"},
              [p["id"] for p in body["projects"]])
        check("1d. exactly one portfolio list route is registered, and it is GET-only",
              [sorted(r.methods - {"HEAD", "OPTIONS"}) for r in app.url_map.iter_rules()
               if str(r.rule) == LIST_ROUTE] == [["GET"]],
              [str(r.rule) for r in app.url_map.iter_rules() if "portfolio" in str(r.rule)])
    finally:
        _restore_safe_root(orig_root)
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_portfolio_list_never_leaks_filesystem_paths():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    safe_root = os.path.join(tmp, "projects")
    orig_root = _use_safe_root(safe_root)
    _make_reachable(tmp, conn, "cis", safe_root)
    _make_reachable(tmp, conn, "swa", safe_root)
    client = app.test_client()
    try:
        resp = client.get(LIST_ROUTE)
        body = resp.get_json()
        check("2a. no project in the list response carries a repo_path or spine_path key",
              all("repo_path" not in p and "spine_path" not in p for p in body["projects"]),
              body["projects"])
        check("2b. the reachable cis entry is reported reachable without its path",
              next(p for p in body["projects"] if p["id"] == "cis")["reachable"] is True,
              body["projects"])
        check("2c. the reachable swa entry is reported reachable without its path",
              next(p for p in body["projects"] if p["id"] == "swa")["reachable"] is True,
              body["projects"])
    finally:
        _restore_safe_root(orig_root)
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_unknown_project_detail_is_404():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    client = app.test_client()
    try:
        resp = client.get(detail_route("not-a-real-project"))
        check("3a. an unknown project_id answers 404", resp.status_code == 404, resp.status_code)
        body = resp.get_json()
        check("3b. the 404 body names the unknown id", "not-a-real-project" in body.get("error", ""), body)

        resp = client.get(detail_route("wiasw"))
        check("3c. WIASW (no registry row) is also a clean 404, not a fallback",
              resp.status_code == 404, resp.status_code)
        wiasw_body = resp.get_json()
        check("3d. the WIASW 404 body names wiasw and carries no cis/swa data",
              "wiasw" in wiasw_body.get("error", "")
              and "repo_path" not in wiasw_body and "spine_path" not in wiasw_body,
              wiasw_body)
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_cis_and_swa_detail_are_independently_reachable():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    safe_root = os.path.join(tmp, "projects")
    orig_root = _use_safe_root(safe_root)
    _make_reachable(tmp, conn, "cis", safe_root)
    _make_reachable(tmp, conn, "swa", safe_root)
    client = app.test_client()
    try:
        cis_resp = client.get(detail_route("cis"))
        swa_resp = client.get(detail_route("swa"))
        check("4a. GET cis's detail returns 200", cis_resp.status_code == 200, cis_resp.status_code)
        check("4b. GET swa's detail returns 200", swa_resp.status_code == 200, swa_resp.status_code)
        cis_body = cis_resp.get_json()
        swa_body = swa_resp.get_json()
        check("4c. cis's own detail is reachable and carries no filesystem path",
              cis_body["reachable"] is True
              and "repo_path" not in cis_body and "spine_path" not in cis_body,
              cis_body)
        check("4d. swa's own detail is reachable and carries no filesystem path",
              swa_body["reachable"] is True
              and "repo_path" not in swa_body and "spine_path" not in swa_body,
              swa_body)
        check("4e. cis's detail never names swa and swa's detail never names cis",
              "swa" not in str(cis_body.get("detail") or "").lower()
              and "cis" not in str(swa_body.get("detail") or "").lower(),
              (cis_body, swa_body))
    finally:
        _restore_safe_root(orig_root)
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_unsafe_project_detail_is_200_with_honest_body():
    """An unsafe or unreachable project is reported, not hidden behind a
    503 — the same "composed area degrades, the screen does not" rule
    api/project_intelligence.py documents for its own composed areas."""
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    safe_root = os.path.join(tmp, "projects")
    os.makedirs(safe_root)
    conn.execute(
        "UPDATE projects SET repo_path = ?, spine_path = ? WHERE id = 'cis'",
        (safe_root, os.path.join(safe_root, "x.db")),
    )
    conn.commit()
    orig_root = _use_safe_root(safe_root)
    client = app.test_client()
    try:
        resp = client.get(detail_route("cis"))
        check("5a. an unsafe-root project is still a 200, with the rejection in the body",
              resp.status_code == 200, resp.status_code)
        body = resp.get_json()
        check("5b. the body reports unsafe with the unsafe_root error code",
              body["unsafe"] is True and body["error"] == "unsafe_root", body)
    finally:
        _restore_safe_root(orig_root)
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_write_methods_on_either_route():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    client = app.test_client()
    try:
        for method in ("POST", "PATCH", "PUT", "DELETE"):
            resp = client.open(LIST_ROUTE, method=method)
            check(f"6a. {method} on the list route is refused (405)", resp.status_code == 405, resp.status_code)
            resp = client.open(detail_route("cis"), method=method)
            check(f"6b. {method} on the detail route is refused (405)", resp.status_code == 405, resp.status_code)
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_caller_supplied_db_path_or_repo_path():
    """The only input either route accepts is the project_id path segment.
    A query string cannot smuggle a repo_path, spine_path or db_path."""
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    client = app.test_client()
    try:
        resp = client.get(f"{LIST_ROUTE}?db=/etc/passwd&repo_path=/etc")
        check("7a. a caller-supplied db/repo_path query param is ignored, not honored",
              resp.status_code == 200 and resp.get_json()["read_model"] == "cis_portfolio",
              resp.status_code)

        resp = client.get(f"{detail_route('cis')}?spine_path=/etc/passwd")
        check("7b. a caller-supplied spine_path query param on the detail route is ignored",
              resp.status_code == 200, resp.status_code)
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_list_read_model_failure_returns_503_not_500():
    import api.portfolio as api_pf
    original = api_pf.pf.list_projects
    try:
        def boom():
            raise sqlite3.OperationalError("unable to open database file")
        api_pf.pf.list_projects = boom
        resp = app.test_client().get(LIST_ROUTE)
        body = resp.get_json()
        check("8a. a list read-model failure is a 503, never a 500 traceback",
              resp.status_code == 503, resp.status_code)
        check("8b. the error names the exception type and fabricates no project list",
              "OperationalError" in body.get("error", "") and "projects" not in body, body)
    finally:
        api_pf.pf.list_projects = original


def test_detail_read_model_failure_returns_503_not_500():
    import api.portfolio as api_pf
    original = api_pf.pf.get_project
    try:
        def boom(project_id):
            raise RuntimeError("registry spine unreachable")
        api_pf.pf.get_project = boom
        resp = app.test_client().get(detail_route("cis"))
        body = resp.get_json()
        check("9a. a detail read-model failure is a 503, never a 500 traceback",
              resp.status_code == 503, resp.status_code)
        check("9b. the error names the exception type", "RuntimeError" in body.get("error", ""), body)
    finally:
        api_pf.pf.get_project = original


def test_detail_unknown_project_is_404_not_503():
    """UnknownProjectError must still reach the route as a 404 even though
    the generic except clause below it catches everything else as 503 —
    proves the specific except for pc.UnknownProjectError is actually
    ordered before the broad one, not shadowed by it."""
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    try:
        resp = app.test_client().get(detail_route("genuinely-unknown"))
        check("10a. an unknown id still answers 404 (not swallowed into a 503)",
              resp.status_code == 404, resp.status_code)
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_reads_do_not_mutate_the_registry():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    safe_root = os.path.join(tmp, "projects")
    orig_root = _use_safe_root(safe_root)
    _make_reachable(tmp, conn, "cis", safe_root)
    _make_reachable(tmp, conn, "swa", safe_root)
    client = app.test_client()
    try:
        before = conn.execute("SELECT id, repo_path, spine_path, status FROM projects ORDER BY id").fetchall()

        client.get(LIST_ROUTE)
        client.get(detail_route("cis"))
        client.get(detail_route("swa"))
        client.get(detail_route("wiasw"))

        after = conn.execute("SELECT id, repo_path, spine_path, status FROM projects ORDER BY id").fetchall()
        check("11a. no registry row changed after hitting every route",
              [tuple(r) for r in before] == [tuple(r) for r in after],
              (before, after))
    finally:
        _restore_safe_root(orig_root)
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_portfolio_routes_do_not_collide_with_workbench_projects():
    """Only two GET routes are registered under /api/workbench/portfolio*,
    and they are distinct from braingate_conversation_bp's pre-existing
    /api/workbench/projects* surface (workbench_projects conversation
    workspaces) — the two tables and the two route families are never
    merged."""
    portfolio_rules = {
        str(r.rule): sorted(r.methods - {"HEAD", "OPTIONS"})
        for r in app.url_map.iter_rules() if "portfolio" in str(r.rule)
    }
    check("12a. exactly two portfolio routes are registered",
          set(portfolio_rules.keys()) == {LIST_ROUTE, "/api/workbench/portfolio/projects/<project_id>"},
          portfolio_rules)
    check("12b. both portfolio routes are GET-only",
          all(methods == ["GET"] for methods in portfolio_rules.values()),
          portfolio_rules)

    workbench_projects_rules = {
        str(r.rule) for r in app.url_map.iter_rules()
        if str(r.rule).startswith("/api/workbench/projects")
    }
    check("12c. the pre-existing /api/workbench/projects* surface is untouched and distinct",
          len(workbench_projects_rules) > 0
          and not any(rule.startswith("/api/workbench/portfolio") for rule in workbench_projects_rules),
          workbench_projects_rules)


def run():
    test_portfolio_list_matches_read_model()
    test_portfolio_list_never_leaks_filesystem_paths()
    test_unknown_project_detail_is_404()
    test_cis_and_swa_detail_are_independently_reachable()
    test_unsafe_project_detail_is_200_with_honest_body()
    test_no_write_methods_on_either_route()
    test_no_caller_supplied_db_path_or_repo_path()
    test_list_read_model_failure_returns_503_not_500()
    test_detail_read_model_failure_returns_503_not_500()
    test_detail_unknown_project_is_404_not_503()
    test_reads_do_not_mutate_the_registry()
    test_portfolio_routes_do_not_collide_with_workbench_projects()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
