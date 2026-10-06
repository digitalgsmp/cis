"""
test_chroma_health.py — focused tests for runtime/chroma_health.py
(card container-kb-health-20260917, including the revision-required fixes
from codex-first-review.json: URI escaping, CIS_REPO_ROOT precedence, and
WAL sidecar side effects).

Run: python3 runtime/tests/test_chroma_health.py
"""
import os
import shutil
import sqlite3
import sys
import tempfile
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import chroma_health
from chroma_health import check_embedded_chroma_health, resolve_chroma_path


def make_fixture_db(path, with_collection=True, table_only=False):
    conn = sqlite3.connect(path)
    if not table_only:
        conn.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT)")
        if with_collection:
            conn.execute(
                "INSERT INTO collections (id, name) VALUES (?, ?)",
                ("fixture-id-1", "knowledge_messages"),
            )
        else:
            conn.execute(
                "INSERT INTO collections (id, name) VALUES (?, ?)",
                ("fixture-id-2", "some_other_collection"),
            )
    else:
        conn.execute("CREATE TABLE unrelated (id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()


def make_wal_fixture_db(path, checkpoint_and_close_sidecars=True):
    """Create a WAL-journal-mode fixture. If checkpoint_and_close_sidecars,
    fully checkpoint so no -wal/-shm remain on disk (the "cleanly closed"
    case from the review)."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT)")
    conn.execute(
        "INSERT INTO collections (id, name) VALUES (?, ?)",
        ("fixture-id", "knowledge_messages"),
    )
    conn.commit()
    if checkpoint_and_close_sidecars:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()


def file_hash(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def run():
    results = []
    tmp_root = tempfile.mkdtemp(prefix="chroma_health_test_")

    try:
        # ── 1. Real embedded fixture with knowledge_messages -> healthy ──
        good_dir = os.path.join(tmp_root, "good")
        os.makedirs(good_dir)
        db_file = os.path.join(good_dir, "chroma.sqlite3")
        make_fixture_db(db_file, with_collection=True)
        before_hash = file_hash(db_file)
        before_listing = sorted(os.listdir(good_dir))

        result = check_embedded_chroma_health(chroma_path=good_dir, explicit=True)
        if result["healthy"] is True:
            results.append("1a. healthy fixture -> healthy=True: PASS")
        else:
            results.append(f"1a. healthy fixture -> healthy=True: FAIL — {result}")

        detail_lower = result["detail"].lower()
        if "embedded" in detail_lower and "readable" in detail_lower:
            results.append("1b. detail mentions embedded/readable: PASS")
        else:
            results.append(f"1b. detail mentions embedded/readable: FAIL — {result['detail']}")

        if "8000" not in detail_lower and "heartbeat" not in detail_lower:
            results.append("1c. detail does not reference port 8000/heartbeat: PASS")
        else:
            results.append(f"1c. detail does not reference port 8000/heartbeat: FAIL — {result['detail']}")

        for _ in range(3):
            check_embedded_chroma_health(chroma_path=good_dir, explicit=True)
        after_hash = file_hash(db_file)
        after_listing = sorted(os.listdir(good_dir))
        if after_hash == before_hash:
            results.append("1d. repeated polling leaves chroma.sqlite3 bytes unchanged: PASS")
        else:
            results.append("1d. repeated polling leaves chroma.sqlite3 bytes unchanged: FAIL")
        if after_listing == before_listing:
            results.append("1e. repeated polling creates no new files (-wal/-shm/journal): PASS")
        else:
            results.append(
                f"1e. repeated polling creates no new files: FAIL — before={before_listing} after={after_listing}"
            )

        # ── 2. Missing directory -> healthy False, path stays absent ──
        missing_dir = os.path.join(tmp_root, "does_not_exist")
        result = check_embedded_chroma_health(chroma_path=missing_dir, explicit=True)
        if result["healthy"] is False and "not found" in result["detail"].lower():
            results.append("2a. missing directory -> healthy=False with detail: PASS")
        else:
            results.append(f"2a. missing directory -> healthy=False with detail: FAIL — {result}")
        if not os.path.exists(missing_dir):
            results.append("2b. missing directory remains absent after check: PASS")
        else:
            results.append("2b. missing directory remains absent after check: FAIL — directory was created")

        # ── 3. Directory exists, no chroma.sqlite3 -> healthy False ──
        empty_dir = os.path.join(tmp_root, "empty")
        os.makedirs(empty_dir)
        result = check_embedded_chroma_health(chroma_path=empty_dir, explicit=True)
        if result["healthy"] is False and "chroma.sqlite3" in result["detail"]:
            results.append("3a. missing database file -> healthy=False: PASS")
        else:
            results.append(f"3a. missing database file -> healthy=False: FAIL — {result}")
        if sorted(os.listdir(empty_dir)) == []:
            results.append("3b. empty directory stays empty (no db created): PASS")
        else:
            results.append(f"3b. empty directory stays empty: FAIL — {os.listdir(empty_dir)}")

        # ── 4. Corrupt database -> healthy False, no crash, no traceback ──
        corrupt_dir = os.path.join(tmp_root, "corrupt")
        os.makedirs(corrupt_dir)
        corrupt_db = os.path.join(corrupt_dir, "chroma.sqlite3")
        with open(corrupt_db, "wb") as f:
            f.write(b"this is not a sqlite database, just garbage bytes")
        result = check_embedded_chroma_health(chroma_path=corrupt_dir, explicit=True)
        if result["healthy"] is False and result["detail"]:
            results.append("4a. corrupt database -> healthy=False with useful detail: PASS")
        else:
            results.append(f"4a. corrupt database -> healthy=False with useful detail: FAIL — {result}")
        if "Traceback" not in result["detail"] and "File \"" not in result["detail"]:
            results.append("4b. corrupt database detail contains no traceback: PASS")
        else:
            results.append(f"4b. corrupt database detail contains no traceback: FAIL — {result['detail']}")

        # ── 5. Missing knowledge_messages collection -> healthy False, and
        #        the detail does not enumerate every other collection name ──
        nocol_dir = os.path.join(tmp_root, "nocollection")
        os.makedirs(nocol_dir)
        nocol_db = os.path.join(nocol_dir, "chroma.sqlite3")
        make_fixture_db(nocol_db, with_collection=False)
        result = check_embedded_chroma_health(chroma_path=nocol_dir, explicit=True)
        if result["healthy"] is False and "knowledge_messages" in result["detail"]:
            results.append("5a. missing knowledge_messages collection -> healthy=False: PASS")
        else:
            results.append(f"5a. missing knowledge_messages collection -> healthy=False: FAIL — {result}")
        if "some_other_collection" not in result["detail"]:
            results.append("5b. detail does not leak unrelated collection names: PASS")
        else:
            results.append(f"5b. detail does not leak unrelated collection names: FAIL — {result['detail']}")

        # ── 6. Path resolution: explicit CIS_CHROMA_PATH wins, invalid -> no fallback ──
        old_env = dict(os.environ)
        try:
            os.environ["CIS_CHROMA_PATH"] = missing_dir
            os.environ["CIS_REPO_ROOT"] = os.path.join(tmp_root, "should_not_be_used")
            path, explicit = resolve_chroma_path()
            if path == missing_dir and explicit is True:
                results.append("6a. explicit CIS_CHROMA_PATH wins over CIS_REPO_ROOT: PASS")
            else:
                results.append(f"6a. explicit CIS_CHROMA_PATH wins over CIS_REPO_ROOT: FAIL — {path}, explicit={explicit}")

            result = check_embedded_chroma_health()
            if result["healthy"] is False and "explicitly configured" in result["detail"]:
                results.append("6b. invalid explicit path reported, not silently swapped: PASS")
            else:
                results.append(f"6b. invalid explicit path reported, not silently swapped: FAIL — {result}")
        finally:
            os.environ.clear()
            os.environ.update(old_env)

        # ── 6c. REGRESSION: CIS_CHROMA_PATH explicitly set to "" must fail
        #         clearly, not silently fall back to CIS_REPO_ROOT/default ──
        old_env = dict(os.environ)
        try:
            os.environ["CIS_CHROMA_PATH"] = ""
            os.environ["CIS_REPO_ROOT"] = good_dir  # a directory that WOULD succeed
            path, explicit = resolve_chroma_path()
            result = check_embedded_chroma_health()
            if explicit is True and path == "" and result["healthy"] is False and "empty" in result["detail"].lower():
                results.append("6c. empty explicit CIS_CHROMA_PATH fails clearly, no silent fallback: PASS")
            else:
                results.append(f"6c. empty explicit CIS_CHROMA_PATH fails clearly: FAIL — path={path!r} explicit={explicit} result={result}")
        finally:
            os.environ.clear()
            os.environ.update(old_env)

        # ── 7. REGRESSION: CIS_REPO_ROOT honored (storage-client convention),
        #        used verbatim rather than existence-probing between roots ──
        old_env = dict(os.environ)
        try:
            os.environ.pop("CIS_CHROMA_PATH", None)
            custom_root = os.path.join(tmp_root, "custom_repo_root")
            os.environ["CIS_REPO_ROOT"] = custom_root
            path, explicit = resolve_chroma_path()
            expected = os.path.join(custom_root, "data", "chroma_data")
            if path == expected and explicit is False:
                results.append("7a. CIS_REPO_ROOT honored per storage-client convention: PASS")
            else:
                results.append(f"7a. CIS_REPO_ROOT honored: FAIL — {path}, explicit={explicit}")
        finally:
            os.environ.clear()
            os.environ.update(old_env)

        # ── 7b. No env vars at all -> portable module-derived repo root ──
        old_env = dict(os.environ)
        try:
            os.environ.pop("CIS_CHROMA_PATH", None)
            os.environ.pop("CIS_REPO_ROOT", None)
            path, explicit = resolve_chroma_path()
            expected = os.path.join(chroma_health._module_derived_repo_root(), "data", "chroma_data")
            if path == expected and explicit is False:
                results.append("7b. no env vars -> portable module-derived repo root: PASS")
            else:
                results.append(f"7b. no env vars -> portable module-derived repo root: FAIL — {path}")
        finally:
            os.environ.clear()
            os.environ.update(old_env)

        # ── 8. No chromadb import anywhere in the module ──
        with open(os.path.join(os.path.dirname(__file__), "..", "chroma_health.py")) as f:
            src = f.read()
        if "import chromadb" not in src and "PersistentClient(" not in src:
            results.append("8a. chroma_health.py never imports/instantiates chromadb: PASS")
        else:
            results.append("8a. chroma_health.py never imports/instantiates chromadb: FAIL")
        if "chromadb" not in sys.modules:
            results.append("8b. chromadb module never loaded into sys.modules by these checks: PASS")
        else:
            results.append("8b. chromadb module never loaded into sys.modules by these checks: FAIL")

        # ── 9. REGRESSION: URI punctuation in the path must not break/redirect ──
        special_dir = os.path.join(tmp_root, "special?#name")
        os.makedirs(special_dir)
        special_db = os.path.join(special_dir, "chroma.sqlite3")
        make_fixture_db(special_db, with_collection=True)
        result = check_embedded_chroma_health(chroma_path=special_dir, explicit=True)
        if result["healthy"] is True:
            results.append("9a. path containing '?#' resolves and reads correctly: PASS")
        else:
            results.append(f"9a. path containing '?#' resolves and reads correctly: FAIL — {result}")
        # Prove no stray file was created next to the intended one due to
        # URI misparsing (e.g. a file literally named "name" from a
        # mis-split query string).
        if sorted(os.listdir(special_dir)) == ["chroma.sqlite3"]:
            results.append("9b. no stray files created from URI misparsing: PASS")
        else:
            results.append(f"9b. no stray files created from URI misparsing: FAIL — {os.listdir(special_dir)}")

        # ── 10. REGRESSION: WAL sidecars — three states ──

        # 10a. Cleanly closed WAL db (no -wal/-shm on disk) must stay that
        #      way after a read, and still read correctly (immutable path).
        wal_clean_dir = os.path.join(tmp_root, "wal_clean")
        os.makedirs(wal_clean_dir)
        wal_clean_db = os.path.join(wal_clean_dir, "chroma.sqlite3")
        make_wal_fixture_db(wal_clean_db, checkpoint_and_close_sidecars=True)
        before_listing = sorted(os.listdir(wal_clean_dir))
        if before_listing == ["chroma.sqlite3"]:
            results.append("10a-setup. WAL fixture cleanly closed with no sidecars: PASS")
        else:
            results.append(f"10a-setup. WAL fixture cleanly closed with no sidecars: FAIL — {before_listing}")
        result = check_embedded_chroma_health(chroma_path=wal_clean_dir, explicit=True)
        after_listing = sorted(os.listdir(wal_clean_dir))
        if result["healthy"] is True:
            results.append("10a. cleanly-closed WAL fixture reads healthy=True: PASS")
        else:
            results.append(f"10a. cleanly-closed WAL fixture reads healthy=True: FAIL — {result}")
        if after_listing == before_listing:
            results.append("10b. reading a cleanly-closed WAL fixture creates NO -wal/-shm sidecars: PASS")
        else:
            results.append(
                f"10b. reading a cleanly-closed WAL fixture creates NO sidecars: FAIL — before={before_listing} after={after_listing}"
            )

        # 10c. Live WAL with both sidecars already present: must read
        #      correctly (including WAL content) and create nothing new.
        wal_live_dir = os.path.join(tmp_root, "wal_live")
        os.makedirs(wal_live_dir)
        wal_live_db = os.path.join(wal_live_dir, "chroma.sqlite3")
        writer = sqlite3.connect(wal_live_db)
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT)")
        writer.execute(
            "INSERT INTO collections (id, name) VALUES (?, ?)",
            ("fixture-id", "knowledge_messages"),
        )
        writer.commit()
        # keep writer connection open so -wal/-shm persist and stay "live"
        live_listing = sorted(os.listdir(wal_live_dir))
        if "chroma.sqlite3-wal" in live_listing and "chroma.sqlite3-shm" in live_listing:
            results.append("10c-setup. live WAL fixture has both sidecars present: PASS")
        else:
            results.append(f"10c-setup. live WAL fixture has both sidecars present: FAIL — {live_listing}")
        result = check_embedded_chroma_health(chroma_path=wal_live_dir, explicit=True)
        after_live_listing = sorted(os.listdir(wal_live_dir))
        if result["healthy"] is True:
            results.append("10c. live WAL (sidecars present) reads healthy=True without immutable: PASS")
        else:
            results.append(f"10c. live WAL (sidecars present) reads healthy=True: FAIL — {result}")
        if after_live_listing == live_listing:
            results.append("10d. reading a live WAL fixture creates no additional sidecar files: PASS")
        else:
            results.append(
                f"10d. reading a live WAL fixture creates no additional files: FAIL — before={live_listing} after={after_live_listing}"
            )
        writer.close()

        # 10e. Partial/inconsistent WAL state (only one sidecar present):
        #      fail closed rather than create the missing file or guess.
        wal_partial_dir = os.path.join(tmp_root, "wal_partial")
        os.makedirs(wal_partial_dir)
        wal_partial_db = os.path.join(wal_partial_dir, "chroma.sqlite3")
        make_wal_fixture_db(wal_partial_db, checkpoint_and_close_sidecars=True)
        # Manually fabricate an orphaned -shm file with no matching -wal,
        # simulating an inconsistent on-disk state.
        with open(wal_partial_db + "-shm", "wb") as f:
            f.write(b"\x00" * 32768)
        before_partial_listing = sorted(os.listdir(wal_partial_dir))
        result = check_embedded_chroma_health(chroma_path=wal_partial_dir, explicit=True)
        after_partial_listing = sorted(os.listdir(wal_partial_dir))
        if result["healthy"] is False and "inconsistent" in result["detail"].lower():
            results.append("10e. partial WAL sidecar state fails closed with clear detail: PASS")
        else:
            results.append(f"10e. partial WAL sidecar state fails closed: FAIL — {result}")
        if after_partial_listing == before_partial_listing:
            results.append("10f. partial WAL sidecar state creates no further files: PASS")
        else:
            results.append(
                f"10f. partial WAL sidecar state creates no further files: FAIL — before={before_partial_listing} after={after_partial_listing}"
            )

        # ── 10g. REGRESSION (codex-wal-race.json): a writer that commits
        #         in the gap between the sidecar check and the connect must
        #         not produce a stale healthy=True. Reproduces exactly the
        #         "writer commits after sidecar check before connection"
        #         case from codex-wal-race.json using the _after_sidecar_check
        #         test seam to land the write deterministically in that gap.
        race_dir = os.path.join(tmp_root, "wal_race")
        os.makedirs(race_dir)
        race_db = os.path.join(race_dir, "chroma.sqlite3")
        make_wal_fixture_db(race_db, checkpoint_and_close_sidecars=True)
        # fixture starts clean: no -wal/-shm, knowledge_messages present

        def writer_commits_during_gap():
            w = sqlite3.connect(race_db)
            w.execute("DELETE FROM collections")  # simulate a real state change
            w.commit()
            # deliberately leave the writer connection open so -wal/-shm
            # persist past our own read, exactly like the reviewer's fixture
            race_state["writer"] = w

        race_state = {}
        result = check_embedded_chroma_health(
            chroma_path=race_dir, explicit=True,
            _after_sidecar_check=writer_commits_during_gap,
        )
        if "writer" in race_state:
            race_state["writer"].close()

        if result["healthy"] is False and "write began" in result["detail"].lower():
            results.append("10g. writer racing the sidecar-check-to-connect gap is caught, fails closed: PASS")
        else:
            results.append(f"10g. writer racing the sidecar-check-to-connect gap is caught: FAIL — {result}")

        # ── 11. REGRESSION: bounded detail length ──
        long_dir = "x" * 1000
        result = check_embedded_chroma_health(chroma_path=long_dir, explicit=True)
        if len(result["detail"]) <= 350:
            results.append("11a. detail length is bounded even for pathological input: PASS")
        else:
            results.append(f"11a. detail length is bounded: FAIL — length={len(result['detail'])}")

    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    for r in results:
        print(r)
    failed = [r for r in results if "FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
