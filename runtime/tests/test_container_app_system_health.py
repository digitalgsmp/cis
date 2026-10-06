"""
test_container_app_system_health.py — Flask endpoint test for
/api/relay/system/health (card container-kb-health-20260917).

Exercises the real endpoint through Flask's test client with the
unrelated gateway/llama-server subprocess calls and the SQLite spine
path mocked/pointed at fixtures, while the Chroma check runs for real
against temporary embedded-store fixtures set via CIS_CHROMA_PATH —
so the storage failure/success cases are not made vacuous by mocking.

Run: python3 runtime/tests/test_container_app_system_health.py
"""
import os
import sqlite3
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault("CIS_PIPELINE_API_KEY", "")

import container_app  # noqa: E402
from container_app import app  # noqa: E402


class FakeCompletedProcess:
    def __init__(self, returncode=1, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


def fake_subproc_run(*args, **kwargs):
    # Unrelated gateway / llama-server checks: deterministically "down",
    # isolated from whatever is or isn't actually running on this host.
    return FakeCompletedProcess(returncode=1, stdout="")


def make_fixture_db(path, with_collection=True):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT)")
    if with_collection:
        conn.execute(
            "INSERT INTO collections (id, name) VALUES (?, ?)",
            ("fixture-id", "knowledge_messages"),
        )
    conn.commit()
    conn.close()


def make_fixture_spine(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE placeholder (id INTEGER)")
    conn.commit()
    conn.close()


def run():
    results = []
    tmp_root = tempfile.mkdtemp(prefix="container_app_health_test_")
    client = app.test_client()

    orig_subproc_run = container_app._subproc.run
    orig_chroma_env = os.environ.get("CIS_CHROMA_PATH")
    orig_db_env = os.environ.get("CIS_DB_PATH")
    orig_repo_root_env = os.environ.get("CIS_REPO_ROOT")

    try:
        container_app._subproc.run = fake_subproc_run

        spine_db = os.path.join(tmp_root, "spine.db")
        make_fixture_spine(spine_db)
        os.environ["CIS_DB_PATH"] = spine_db

        # ── Case A: real embedded fixture -> endpoint reports healthy=True ──
        good_dir = os.path.join(tmp_root, "good_chroma")
        os.makedirs(good_dir)
        make_fixture_db(os.path.join(good_dir, "chroma.sqlite3"), with_collection=True)
        os.environ["CIS_CHROMA_PATH"] = good_dir

        resp = client.get("/api/relay/system/health")
        body = resp.get_json()

        if resp.status_code == 200:
            results.append("A1. endpoint returns 200: PASS")
        else:
            results.append(f"A1. endpoint returns 200: FAIL — {resp.status_code}")

        for key in ("containers", "gateways", "services"):
            if key in body:
                results.append(f"A2. response contains '{key}' key: PASS")
            else:
                results.append(f"A2. response contains '{key}' key: FAIL — body={body}")

        if len(body.get("gateways", [])) == 6 and all(g["healthy"] is False for g in body["gateways"]):
            results.append("A3. gateway checks isolated via mock, all down: PASS")
        else:
            results.append(f"A3. gateway checks isolated via mock, all down: FAIL — {body.get('gateways')}")

        chroma_service = next((s for s in body.get("services", []) if "Chroma" in s["name"]), None)
        if chroma_service is None:
            results.append("A4. a Chroma service entry is present: FAIL — none found")
        else:
            results.append("A4. a Chroma service entry is present: PASS")
            if chroma_service["healthy"] is True:
                results.append("A5. real good fixture -> healthy=True through the live endpoint: PASS")
            else:
                results.append(f"A5. real good fixture -> healthy=True through the live endpoint: FAIL — {chroma_service}")
            detail = chroma_service.get("detail", "")
            if "embedded" in detail.lower() and "readable" in detail.lower():
                results.append("A6. service detail says embedded/readable (not provider/pipeline claim): PASS")
            else:
                results.append(f"A6. service detail says embedded/readable: FAIL — {detail}")
            if "8000" not in detail and "heartbeat" not in detail.lower():
                results.append("A7. detail does not reference the old HTTP port/heartbeat probe: PASS")
            else:
                results.append(f"A7. detail does not reference the old HTTP probe: FAIL — {detail}")

        # SQLite spine check still present and using the fixture, proving we
        # did not touch that unrelated check's behavior/contract.
        sqlite_service = next((s for s in body.get("services", []) if s["name"] == "SQLite Spine"), None)
        if sqlite_service is not None and sqlite_service["healthy"] is True:
            results.append("A8. unrelated SQLite Spine check untouched and passes on its own fixture: PASS")
        else:
            results.append(f"A8. unrelated SQLite Spine check untouched: FAIL — {sqlite_service}")

        # ── Case B: missing chroma dir -> endpoint reports healthy=False ──
        missing_dir = os.path.join(tmp_root, "does_not_exist_chroma")
        os.environ["CIS_CHROMA_PATH"] = missing_dir

        resp = client.get("/api/relay/system/health")
        body = resp.get_json()
        chroma_service = next((s for s in body.get("services", []) if "Chroma" in s["name"]), None)
        if chroma_service is not None and chroma_service["healthy"] is False:
            results.append("B1. missing chroma dir -> healthy=False through the live endpoint: PASS")
        else:
            results.append(f"B1. missing chroma dir -> healthy=False through the live endpoint: FAIL — {chroma_service}")
        if chroma_service is not None and "not found" in chroma_service.get("detail", "").lower():
            results.append("B2. detail explains the missing path: PASS")
        else:
            results.append(f"B2. detail explains the missing path: FAIL — {chroma_service}")
        if not os.path.exists(missing_dir):
            results.append("B3. missing directory still absent after polling (no accidental creation): PASS")
        else:
            results.append("B3. missing directory still absent after polling: FAIL — directory now exists")

        # ── Case C: fixture missing knowledge_messages -> healthy=False ──
        nocol_dir = os.path.join(tmp_root, "nocollection_chroma")
        os.makedirs(nocol_dir)
        make_fixture_db(os.path.join(nocol_dir, "chroma.sqlite3"), with_collection=False)
        os.environ["CIS_CHROMA_PATH"] = nocol_dir

        resp = client.get("/api/relay/system/health")
        body = resp.get_json()
        chroma_service = next((s for s in body.get("services", []) if "Chroma" in s["name"]), None)
        if chroma_service is not None and chroma_service["healthy"] is False and "knowledge_messages" in chroma_service.get("detail", ""):
            results.append("C1. fixture without knowledge_messages -> healthy=False with useful detail: PASS")
        else:
            results.append(f"C1. fixture without knowledge_messages -> healthy=False: FAIL — {chroma_service}")

        # ── Case D: REGRESSION — empty explicit CIS_CHROMA_PATH must fail
        #      clearly through the live endpoint, not silently fall back ──
        os.environ["CIS_CHROMA_PATH"] = ""
        os.environ["CIS_REPO_ROOT"] = os.path.dirname(good_dir)  # would resolve to a working dir if wrongly used

        resp = client.get("/api/relay/system/health")
        body = resp.get_json()
        chroma_service = next((s for s in body.get("services", []) if "Chroma" in s["name"]), None)
        if chroma_service is not None and chroma_service["healthy"] is False and "empty" in chroma_service.get("detail", "").lower():
            results.append("D1. empty explicit CIS_CHROMA_PATH fails clearly through the live endpoint: PASS")
        else:
            results.append(f"D1. empty explicit CIS_CHROMA_PATH fails clearly: FAIL — {chroma_service}")
        os.environ.pop("CIS_REPO_ROOT", None)

        # ── Case E: REGRESSION — an unexpected (non-sqlite3.Error) exception
        #      from the health check must not leak its raw message in HTTP ──
        import chroma_health as _ch

        def _boom(*a, **kw):
            raise RuntimeError("super secret internal path /etc/shadow leaked here")

        orig_check = _ch.check_embedded_chroma_health
        _ch.check_embedded_chroma_health = _boom
        try:
            resp = client.get("/api/relay/system/health")
            body = resp.get_json()
            chroma_service = next((s for s in body.get("services", []) if "Chroma" in s["name"]), None)
            if chroma_service is not None and chroma_service["healthy"] is False:
                results.append("E1. unexpected exception -> healthy=False, endpoint does not crash: PASS")
            else:
                results.append(f"E1. unexpected exception -> healthy=False: FAIL — {chroma_service}")
            detail = chroma_service.get("detail", "") if chroma_service else ""
            if "secret" not in detail and "/etc/shadow" not in detail:
                results.append("E2. raw exception message is not echoed into HTTP output: PASS")
            else:
                results.append(f"E2. raw exception message is not echoed into HTTP output: FAIL — {detail}")
            if "RuntimeError" in detail:
                results.append("E3. detail names the exception type for diagnosis: PASS")
            else:
                results.append(f"E3. detail names the exception type for diagnosis: FAIL — {detail}")
        finally:
            _ch.check_embedded_chroma_health = orig_check

    finally:
        container_app._subproc.run = orig_subproc_run
        if orig_chroma_env is None:
            os.environ.pop("CIS_CHROMA_PATH", None)
        else:
            os.environ["CIS_CHROMA_PATH"] = orig_chroma_env
        if orig_db_env is None:
            os.environ.pop("CIS_DB_PATH", None)
        else:
            os.environ["CIS_DB_PATH"] = orig_db_env
        if orig_repo_root_env is None:
            os.environ.pop("CIS_REPO_ROOT", None)
        else:
            os.environ["CIS_REPO_ROOT"] = orig_repo_root_env
        shutil.rmtree(tmp_root, ignore_errors=True)

    for r in results:
        print(r)
    failed = [r for r in results if "FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
