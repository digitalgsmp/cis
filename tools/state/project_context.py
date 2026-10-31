#!/usr/bin/env python3
"""project_context.py — secure, server-owned project-context resolver for
the Workbench Portfolio screen.

WHAT THIS IS. dev_continuity_events revision 180 (task WB.1, status
approved) is the reconciliation authority for this slice: the Workbench is
an application-level portfolio hub, and CIS, WIASW and SWA are peer
projects with separate repositories, spines, roadmaps, gates and
development histories. ADR-SEED-010 ("Project isolation model:
--project-root") decided, and continues to decide, that each CIS-managed
project has its own git repo/project root and its own spine database —
revision 180 does not override that isolation, it is the authority that
reconciles an application-level portfolio VIEW with it. This module never
shares a runtime spine across projects and never imports one project's
generated context or state into another's; it only resolves a `project_id`
(the only thing a browser is ever allowed to send) against the
server-owned `projects` registry table (migration 0022) and reports,
honestly, whether that project's repository and spine are safe to use and
currently reachable.

THE REGISTRY, AS IT STANDS. `projects` (migration 0022) is the provisioned-
project registry, not a planning list — every column but `agents_md_path`
and `status` is NOT NULL, and it currently carries exactly two active rows,
`cis` and `swa`. WIASW has no row: it has no provisioned repo root or spine,
and is not part of this resolver until an approved structured planning
projection exists for it. This module does not seed, fabricate or special-
case a WIASW row, and does not alter the `projects` table in any way — no
migration, no INSERT, no ALTER. An id with no row is UnknownProjectError,
full stop; it is never treated as "not yet provisioned" or satisfied by
another project's data.

WHAT THE BROWSER MAY SEND. A stable `project_id` string. Nothing else. This
module never accepts a repo_path, spine_path or db_path from a caller — the
registry row is the only source either path comes from, and every path that
row supplies is re-validated here before it is trusted.

REJECTIONS, NAMED:
  unknown id        no row in `projects` carries this id -> UnknownProjectError
                    (the only case this module raises; everything else is
                    reported in the returned dict, never as a Python
                    exception, so one unsafe/unreachable project can never
                    take down a caller that is listing many).
  path escape       the registry's stored path, BEFORE any symlink is
                    followed, already normalizes to something outside the
                    configured safe root (e.g. a stray '..' segment).
  symlink escape    the stored path is textually inside the safe root, but
                    following its symlinks (os.path.realpath) lands outside
                    it.
  unsafe root       the stored path is not absolute, or normalizes to the
                    filesystem root or to the safe root itself (too broad to
                    ever be one project's repo or spine).
  missing repo      the row's repo_path does not exist as a directory on disk.
  missing spine     the row's spine_path does not exist as a file on disk.
  spine unreachable the spine file exists but will not open under sqlite3's
                    mode=ro URI.

NEVER FALLS BACK. There is no code path in resolve_project_context() that
reads one project_id's row and returns data belonging to a different one.
An id with no registry row is UnknownProjectError; it is never satisfied by
substituting another project's repository or spine.

OPENS SPINES READ-ONLY. The one liveness probe this module performs against
a resolved spine uses sqlite3's mode=ro URI, the same convention used
throughout tools/state/ (see canonical_state.py, project_intelligence.py).
Nothing here issues a write of any kind, and SQLite itself enforces that:
a mode=ro connection raises on any write attempt.
"""
import os
import sqlite3
import sys
from pathlib import Path

_STATE_DIR = Path(__file__).resolve().parent
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import canonical_state as cs  # noqa: E402  (shared DB default: the CIS spine)

# The one allowed container directory for every project's repo_path and
# spine_path. Every provisioned project under ADR-SEED-010 — CIS and SWA
# included — lives at <SAFE_ROOT>/<project>, matching the convention already
# used in runtime/extractor.py and the 'cis' row itself (/mnt/projects/cis).
# A registry row whose path does not resolve inside this root, even after
# following symlinks, is rejected rather than trusted.
#
# Read once at import time (the same pattern cs.DB uses), so tests can
# override it the same way existing tests override cs.DB: reassign the
# module attribute directly (`project_context.SAFE_ROOT = tmp_root`).
DEFAULT_SAFE_ROOT = "/mnt/projects"
SAFE_ROOT = os.environ.get("CIS_PORTFOLIO_SAFE_ROOT", DEFAULT_SAFE_ROOT)


class ProjectContextError(Exception):
    """Base class for resolver-level problems."""


class UnknownProjectError(ProjectContextError):
    """No row in the `projects` registry carries this id (404 at the API layer)."""


class _UnsafePathError(ProjectContextError):
    """Internal base for the three path-safety rejections below. Never
    raised across resolve_project_context()'s own boundary — caught there
    and folded into the returned dict's `error` field, never a raw
    Python exception a caller has to know the type of."""


class UnsafeRootError(_UnsafePathError):
    """The stored path is not absolute, or names the filesystem root or the
    safe root itself."""


class PathEscapeError(_UnsafePathError):
    """The stored path, before any symlink is followed, is already outside
    the configured safe root."""


class SymlinkEscapeError(_UnsafePathError):
    """The stored path is textually inside the safe root, but resolving its
    symlinks lands outside it."""


def _connect(db_path=None):
    """Open the registry database read-only. The registry lives in the CIS
    spine (the same database migration 0022 targets), so the default is the
    same one every other tools/state/ module resolves to."""
    conn = sqlite3.connect(f"file:{db_path or cs.DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_resolve(label, raw_path, project_id):
    """Validate one server-owned path from the registry. Returns its
    resolved real path on success, or raises one of the three
    _UnsafePathError subclasses above. `label` is 'repo_path' or
    'spine_path', used only to make the rejection's detail readable — never
    to change which checks run."""
    if not os.path.isabs(raw_path):
        raise UnsafeRootError(
            f"{label} for project {project_id!r} is not an absolute path")

    normalized = os.path.normpath(raw_path)
    safe_root = os.path.normpath(SAFE_ROOT)

    if normalized in (os.path.sep, safe_root):
        raise UnsafeRootError(
            f"{label} for project {project_id!r} resolves to an unsafe root")

    # Textual containment, BEFORE any symlink is followed. Catches a stored
    # path that already escapes the safe root (e.g. a '..' segment),
    # independent of whether a symlink is involved at all.
    try:
        textually_inside = os.path.commonpath([normalized, safe_root]) == safe_root
    except ValueError:
        # Raised by commonpath for mixed absolute/relative paths or, on
        # Windows, different drives. Neither is reachable given the isabs()
        # check above on this platform, but treat it as an escape, never a
        # crash.
        textually_inside = False
    if not textually_inside:
        raise PathEscapeError(
            f"{label} for project {project_id!r} escapes the configured safe root")

    real = os.path.realpath(normalized)
    safe_root_real = os.path.realpath(safe_root)
    try:
        really_inside = os.path.commonpath([real, safe_root_real]) == safe_root_real
    except ValueError:
        really_inside = False
    if not really_inside:
        raise SymlinkEscapeError(
            f"{label} for project {project_id!r} resolves outside the configured "
            "safe root once symlinks are followed")

    return real


def _row_for(conn, project_id):
    return conn.execute(
        "SELECT id, name, repo_path, spine_path, agents_md_path, status "
        "FROM projects WHERE id = ?",
        (project_id,),
    ).fetchone()


def resolve_project_context(project_id, db_path=None):
    """Resolve one project_id against the registry. Raises
    UnknownProjectError if the id does not exist; otherwise always returns a
    dict (never raises for an unsafe or unreachable project — those are
    reported, not thrown).

    Returned dict (every key always present):
        id, name, status      — the registry row, verbatim
        reachable              — True only once both paths have passed every
                                  safety check AND the spine opened read-only
        unsafe                 — True when a stored path failed a safety check
        error                  — None, or one of: 'unsafe_root', 'path_escape',
                                  'symlink_escape', 'missing_repo',
                                  'missing_spine', 'spine_unreachable'
        detail                 — a human-readable explanation; never contains
                                  a raw filesystem path
        repo_path, spine_path  — the resolved, validated real paths, present
                                  ONLY when reachable is True; None otherwise.
                                  Callers that expose this dict over HTTP must
                                  drop these two keys — see
                                  tools/state/portfolio.py's _public_view().
    """
    if not isinstance(project_id, str) or not project_id.strip():
        raise UnknownProjectError("project_id must be a non-empty string")

    conn = _connect(db_path)
    try:
        row = _row_for(conn, project_id)
    finally:
        conn.close()

    if row is None:
        raise UnknownProjectError(f"no such project: {project_id!r}")

    result = {
        "id": row["id"],
        "name": row["name"],
        "status": row["status"],
        "reachable": False,
        "unsafe": False,
        "error": None,
        "detail": None,
        "repo_path": None,
        "spine_path": None,
    }

    try:
        repo_real = _safe_resolve("repo_path", row["repo_path"], project_id)
        spine_real = _safe_resolve("spine_path", row["spine_path"], project_id)
    except UnsafeRootError as e:
        result["unsafe"] = True
        result["error"] = "unsafe_root"
        result["detail"] = str(e)
        return result
    except PathEscapeError as e:
        result["unsafe"] = True
        result["error"] = "path_escape"
        result["detail"] = str(e)
        return result
    except SymlinkEscapeError as e:
        result["unsafe"] = True
        result["error"] = "symlink_escape"
        result["detail"] = str(e)
        return result

    if not os.path.isdir(repo_real):
        result["error"] = "missing_repo"
        result["detail"] = f"{row['id']}'s registered repository root does not exist on disk"
        return result

    if not os.path.isfile(spine_real):
        result["error"] = "missing_spine"
        result["detail"] = f"{row['id']}'s registered spine database does not exist on disk"
        return result

    try:
        probe = sqlite3.connect(f"file:{spine_real}?mode=ro", uri=True)
        try:
            probe.execute("SELECT 1")
        finally:
            probe.close()
    except sqlite3.Error as e:
        result["error"] = "spine_unreachable"
        result["detail"] = (
            f"{row['id']}'s spine could not be opened read-only: {type(e).__name__}")
        return result

    result["repo_path"] = repo_real
    result["spine_path"] = spine_real
    result["reachable"] = True
    return result


if __name__ == "__main__":
    import json

    if len(sys.argv) != 2:
        print("usage: python3 project_context.py <project_id>", file=sys.stderr)
        sys.exit(2)
    try:
        print(json.dumps(resolve_project_context(sys.argv[1]), indent=2))
    except UnknownProjectError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
