#!/usr/bin/env python3
"""test_project_context.py — behavioral tests for
tools/state/project_context.py, the secure resolver behind the Workbench
Portfolio screen.

Runs entirely against scratch SQLite databases built from the real
migration file 0022_projects_table.sql ONLY — never against production,
never against migration 0042 (removed from this revision; no schema
migration is part of this slice), and never with a project_id, repo_path
or spine_path the test itself did not put there.

make_scratch_db() derives the registry schema from 0022 and then adds one
more row, `swa`, by plain INSERT — not by a second migration — mirroring
the exact shape of the live `projects` table today (two active rows, `cis`
and `swa`; no `wiasw` row at all). This is "construct the exact current
projects schema" from the task's own wording: the schema comes from 0022,
the row shape comes from matching what the live registry already holds.

Exercises every rejection the resolver names in its own docstring: unknown
id (including the specifically-named WIASW, which has no row and must
never resolve by falling back to another project's data), path escape,
symlink escape, unsafe root, missing repo root, missing spine — plus the
"CIS and SWA are independent" guarantee: each resolves using only its own
row, and one project's fixture existing or not existing never affects the
other's resolution.

Run:
    python3 tools/state/tests/test_project_context.py
"""
import os
import shutil
import sqlite3
import sys
import tempfile

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "state"))
import project_context as pc  # noqa: E402

MIGRATIONS_DIR = os.path.join(REPO_ROOT, "runtime", "schema", "migrations")

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def _exec_migration(conn, filename):
    path = os.path.join(MIGRATIONS_DIR, filename)
    with open(path, encoding="utf-8") as f:
        conn.executescript(f.read())


def make_scratch_db():
    """A real file (not :memory:) so the resolver's own mode=ro connection
    can open it independently of this test's connection, exactly like the
    route handlers do against the live spine.

    Schema comes from 0022 only. 0022's own INSERT OR IGNORE seeds 'cis';
    this function additionally inserts 'swa' directly (status 'active',
    placeholder paths a test then overwrites), matching the live registry's
    actual second row. No 'wiasw' row is ever inserted — WIASW has no
    provisioned root or spine and is not part of this registry."""
    tmp = tempfile.mkdtemp(prefix="cis_project_context_test_")
    path = os.path.join(tmp, "scratch.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # 0022 ALTERs workflow_runs to add project_id — a minimal stand-in table
    # is enough for that statement to apply; workflow_runs' own shape is not
    # under test here.
    conn.execute("CREATE TABLE workflow_runs (id TEXT PRIMARY KEY)")
    _exec_migration(conn, "0022_projects_table.sql")
    conn.execute(
        "INSERT INTO projects (id, name, repo_path, spine_path, agents_md_path, status) "
        "VALUES ('swa', 'SWA', '/mnt/projects/swa', '/mnt/projects/swa/data/cis_memory.db', "
        "'/mnt/projects/swa/AGENTS.md', 'active')"
    )
    conn.commit()
    return tmp, path, conn


def _set_safe_root(root):
    orig = pc.SAFE_ROOT
    pc.SAFE_ROOT = root
    return orig


def _restore_safe_root(orig):
    pc.SAFE_ROOT = orig


def _make_reachable(tmp, conn, project_id, safe_root=None):
    """Point one project's row at a real repo+spine under a safe root, and
    return that safe root. Parameterized by project_id so cis and swa can
    each be made reachable independently, in the same or different safe
    roots, without the two ever sharing a fixture."""
    if safe_root is None:
        safe_root = os.path.join(tmp, "projects")
    repo_dir = os.path.join(safe_root, project_id)
    os.makedirs(os.path.join(repo_dir, "data"), exist_ok=True)
    spine_path = os.path.join(repo_dir, "data", "cis_memory.db")
    sqlite3.connect(spine_path).close()
    conn.execute(
        "UPDATE projects SET repo_path = ?, spine_path = ? WHERE id = ?",
        (repo_dir, spine_path, project_id),
    )
    conn.commit()
    return safe_root


# ── 1. unknown id, including WIASW by name ──────────────────────────────────

def test_unknown_id_raises():
    tmp, path, conn = make_scratch_db()
    try:
        raised = False
        try:
            pc.resolve_project_context("not-a-real-project", db_path=path)
        except pc.UnknownProjectError:
            raised = True
        check("1a. an id with no registry row raises UnknownProjectError", raised, "no exception raised")

        raised = False
        try:
            pc.resolve_project_context("", db_path=path)
        except pc.UnknownProjectError:
            raised = True
        check("1b. an empty project_id is rejected the same way", raised, "no exception raised")

        raised = False
        try:
            pc.resolve_project_context("wiasw", db_path=path)
        except pc.UnknownProjectError:
            raised = True
        check("1c. 'wiasw' has no registry row and raises UnknownProjectError, not a fallback",
              raised, "no exception raised")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


# ── 2. cis and swa each resolve reachable from their own fixture, independently ──

def test_cis_resolves_when_its_own_fixture_is_real_and_safe():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    orig_root = _set_safe_root(safe_root)
    try:
        _make_reachable(tmp, conn, "cis", safe_root)
        repo_dir = os.path.join(safe_root, "cis")
        spine_path = os.path.join(repo_dir, "data", "cis_memory.db")

        ctx = pc.resolve_project_context("cis", db_path=path)
        check("2a. cis resolves reachable when its own repo+spine exist",
              ctx["reachable"] is True and ctx["error"] is None, ctx)
        check("2b. the resolved repo_path/spine_path are the real, absolute paths",
              ctx["repo_path"] == os.path.realpath(repo_dir)
              and ctx["spine_path"] == os.path.realpath(spine_path),
              ctx)
        check("2c. unsafe is False for a safely-rooted reachable project",
              ctx["unsafe"] is False, ctx)

        # swa's row still points at the unprovisioned placeholder path from
        # make_scratch_db() and was never touched by this test — it must
        # report unreachable on its own terms, not inherit cis's reachability.
        swa_ctx = pc.resolve_project_context("swa", db_path=path)
        check("2d. swa is untouched by resolving cis and reports its own (unreachable) state",
              swa_ctx["id"] == "swa" and swa_ctx["reachable"] is False, swa_ctx)
    finally:
        _restore_safe_root(orig_root)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_swa_resolves_when_its_own_fixture_is_real_and_safe():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    orig_root = _set_safe_root(safe_root)
    try:
        _make_reachable(tmp, conn, "swa", safe_root)
        repo_dir = os.path.join(safe_root, "swa")
        spine_path = os.path.join(repo_dir, "data", "cis_memory.db")

        ctx = pc.resolve_project_context("swa", db_path=path)
        check("3a. swa resolves reachable when its own repo+spine exist",
              ctx["reachable"] is True and ctx["error"] is None, ctx)
        check("3b. the resolved repo_path/spine_path are swa's own real, absolute paths",
              ctx["repo_path"] == os.path.realpath(repo_dir)
              and ctx["spine_path"] == os.path.realpath(spine_path),
              ctx)

        # cis's row still points at the unprovisioned placeholder path seeded
        # by 0022 — swa becoming reachable must not make cis reachable too.
        cis_ctx = pc.resolve_project_context("cis", db_path=path)
        check("3c. cis is untouched by resolving swa and reports its own (unreachable) state",
              cis_ctx["id"] == "cis" and cis_ctx["reachable"] is False, cis_ctx)
    finally:
        _restore_safe_root(orig_root)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_cis_and_swa_are_both_independently_reachable_in_the_same_run():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    orig_root = _set_safe_root(safe_root)
    try:
        _make_reachable(tmp, conn, "cis", safe_root)
        _make_reachable(tmp, conn, "swa", safe_root)

        cis_ctx = pc.resolve_project_context("cis", db_path=path)
        swa_ctx = pc.resolve_project_context("swa", db_path=path)
        check("4a. cis and swa are both reachable in the same test run",
              cis_ctx["reachable"] is True and swa_ctx["reachable"] is True,
              (cis_ctx, swa_ctx))
        check("4b. each project's resolved paths name only its own id, never the other's",
              os.path.basename(cis_ctx["repo_path"]) == "cis"
              and os.path.basename(swa_ctx["repo_path"]) == "swa",
              (cis_ctx["repo_path"], swa_ctx["repo_path"]))
    finally:
        _restore_safe_root(orig_root)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


# ── 3. unsafe root ────────────────────────────────────────────────────────

def test_unsafe_root_rejected():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    os.makedirs(safe_root)
    try:
        conn.execute(
            "UPDATE projects SET repo_path = ?, spine_path = ? WHERE id = 'cis'",
            (safe_root, os.path.join(safe_root, "x.db")),
        )
        conn.commit()
        orig_root = _set_safe_root(safe_root)
        try:
            ctx = pc.resolve_project_context("cis", db_path=path)
            check("5a. a repo_path equal to the safe root itself is rejected unsafe",
                  ctx["unsafe"] is True and ctx["error"] == "unsafe_root", ctx)
            check("5b. an unsafe project is never reachable",
                  ctx["reachable"] is False, ctx)
            check("5c. the rejection detail never echoes the raw safe-root path",
                  safe_root not in ctx["detail"], ctx["detail"])
        finally:
            _restore_safe_root(orig_root)

        conn.execute("UPDATE projects SET repo_path = 'relative/path' WHERE id = 'cis'")
        conn.commit()
        orig_root = _set_safe_root(safe_root)
        try:
            ctx = pc.resolve_project_context("cis", db_path=path)
            check("5d. a non-absolute repo_path is rejected unsafe",
                  ctx["unsafe"] is True and ctx["error"] == "unsafe_root", ctx)
        finally:
            _restore_safe_root(orig_root)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


# ── 4. path escape (textual, no symlink involved) ────────────────────────

def test_path_escape_rejected():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    os.makedirs(safe_root)
    outside = os.path.join(tmp, "outside")
    os.makedirs(outside)
    escaping_repo = os.path.join(safe_root, "..", "outside")
    escaping_spine = os.path.join(outside, "spine.db")
    sqlite3.connect(escaping_spine).close()
    try:
        conn.execute(
            "UPDATE projects SET repo_path = ?, spine_path = ? WHERE id = 'cis'",
            (escaping_repo, escaping_spine),
        )
        conn.commit()
        orig_root = _set_safe_root(safe_root)
        try:
            ctx = pc.resolve_project_context("cis", db_path=path)
            check("6a. a stored path with a literal '..' escape is rejected path_escape",
                  ctx["unsafe"] is True and ctx["error"] == "path_escape", ctx)
            check("6b. an escaping project is never reachable",
                  ctx["reachable"] is False, ctx)
        finally:
            _restore_safe_root(orig_root)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


# ── 5. symlink escape (textually inside, resolves outside) ───────────────

def test_symlink_escape_rejected():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    os.makedirs(safe_root)
    outside = os.path.join(tmp, "outside_target")
    os.makedirs(outside)
    spine_path = os.path.join(outside, "spine.db")
    sqlite3.connect(spine_path).close()

    link_path = os.path.join(safe_root, "cis_link")
    os.symlink(outside, link_path)

    try:
        conn.execute(
            "UPDATE projects SET repo_path = ?, spine_path = ? WHERE id = 'cis'",
            (link_path, spine_path),
        )
        conn.commit()
        orig_root = _set_safe_root(safe_root)
        try:
            ctx = pc.resolve_project_context("cis", db_path=path)
            check("7a. a symlink that resolves outside the safe root is rejected symlink_escape",
                  ctx["unsafe"] is True and ctx["error"] == "symlink_escape", ctx)
            check("7b. a symlink-escaping project is never reachable",
                  ctx["reachable"] is False, ctx)
        finally:
            _restore_safe_root(orig_root)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


# ── 6. missing repo / missing spine ──────────────────────────────────────

def test_missing_spine_rejected():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    repo_dir = os.path.join(safe_root, "cis")
    os.makedirs(repo_dir)
    missing_spine = os.path.join(repo_dir, "does_not_exist.db")

    try:
        conn.execute(
            "UPDATE projects SET repo_path = ?, spine_path = ? WHERE id = 'cis'",
            (repo_dir, missing_spine),
        )
        conn.commit()
        orig_root = _set_safe_root(safe_root)
        try:
            ctx = pc.resolve_project_context("cis", db_path=path)
            check("8a. a row whose spine file does not exist is rejected missing_spine",
                  ctx["reachable"] is False and ctx["error"] == "missing_spine", ctx)
            check("8b. a missing spine is not reported as 'unsafe' (it is a different rejection)",
                  ctx["unsafe"] is False, ctx)
        finally:
            _restore_safe_root(orig_root)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_repo_root_rejected():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    os.makedirs(safe_root)
    missing_repo = os.path.join(safe_root, "cis")
    spine_path = os.path.join(safe_root, "cis_memory.db")
    sqlite3.connect(spine_path).close()

    try:
        conn.execute(
            "UPDATE projects SET repo_path = ?, spine_path = ? WHERE id = 'cis'",
            (missing_repo, spine_path),
        )
        conn.commit()
        orig_root = _set_safe_root(safe_root)
        try:
            ctx = pc.resolve_project_context("cis", db_path=path)
            check("9a. a row whose repo root does not exist is rejected missing_repo",
                  ctx["reachable"] is False and ctx["error"] == "missing_repo", ctx)
        finally:
            _restore_safe_root(orig_root)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


# ── 7. opens the spine strictly read-only, never writes ─────────────────

def test_resolver_never_writes_to_the_spine():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    repo_dir = os.path.join(safe_root, "cis")
    os.makedirs(os.path.join(repo_dir, "data"))
    spine_path = os.path.join(repo_dir, "data", "cis_memory.db")
    probe_conn = sqlite3.connect(spine_path)
    probe_conn.execute("CREATE TABLE sentinel (n INTEGER)")
    probe_conn.execute("INSERT INTO sentinel VALUES (1)")
    probe_conn.commit()
    probe_conn.close()

    conn.execute(
        "UPDATE projects SET repo_path = ?, spine_path = ? WHERE id = 'cis'",
        (repo_dir, spine_path),
    )
    conn.commit()
    orig_root = _set_safe_root(safe_root)
    try:
        pc.resolve_project_context("cis", db_path=path)
        check_conn = sqlite3.connect(spine_path)
        count = check_conn.execute("SELECT COUNT(*) FROM sentinel").fetchone()[0]
        check_conn.close()
        check("10a. resolving a project's context does not mutate its spine",
              count == 1, count)
    finally:
        _restore_safe_root(orig_root)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_spine_connection_is_strictly_read_only():
    """Enforces mode=ro at the SQLite layer itself, not just by convention:
    a connection opened the exact way the resolver opens one must refuse a
    write, proving the protection does not depend on this module remembering
    never to issue one."""
    tmp, path, conn = make_scratch_db()
    spine_path = os.path.join(tmp, "ro_check.db")
    setup = sqlite3.connect(spine_path)
    setup.execute("CREATE TABLE t (n INTEGER)")
    setup.commit()
    setup.close()
    try:
        ro_conn = sqlite3.connect(f"file:{spine_path}?mode=ro", uri=True)
        raised = False
        try:
            ro_conn.execute("INSERT INTO t VALUES (1)")
            ro_conn.commit()
        except sqlite3.OperationalError:
            raised = True
        finally:
            ro_conn.close()
        check("11a. a connection opened mode=ro refuses a write with OperationalError",
              raised, "write did not raise")
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


# ── 8. the registry itself is never mutated by any resolve call ─────────

def test_registry_not_mutated_by_resolving():
    tmp, path, conn = make_scratch_db()
    safe_root = os.path.join(tmp, "projects")
    orig_root = _set_safe_root(safe_root)
    try:
        _make_reachable(tmp, conn, "cis", safe_root)
        _make_reachable(tmp, conn, "swa", safe_root)
        before = conn.execute(
            "SELECT id, repo_path, spine_path, status FROM projects ORDER BY id"
        ).fetchall()

        pc.resolve_project_context("cis", db_path=path)
        pc.resolve_project_context("swa", db_path=path)
        try:
            pc.resolve_project_context("wiasw", db_path=path)
        except pc.UnknownProjectError:
            pass

        after = conn.execute(
            "SELECT id, repo_path, spine_path, status FROM projects ORDER BY id"
        ).fetchall()
        check("12a. no registry row changed after resolving cis, swa and an unknown id",
              [tuple(r) for r in before] == [tuple(r) for r in after],
              (before, after))
    finally:
        _restore_safe_root(orig_root)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def run():
    test_unknown_id_raises()
    test_cis_resolves_when_its_own_fixture_is_real_and_safe()
    test_swa_resolves_when_its_own_fixture_is_real_and_safe()
    test_cis_and_swa_are_both_independently_reachable_in_the_same_run()
    test_unsafe_root_rejected()
    test_path_escape_rejected()
    test_symlink_escape_rejected()
    test_missing_spine_rejected()
    test_missing_repo_root_rejected()
    test_resolver_never_writes_to_the_spine()
    test_spine_connection_is_strictly_read_only()
    test_registry_not_mutated_by_resolving()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
