#!/usr/bin/env python3
"""portfolio.py — server-owned Portfolio read model.

Composes over the `projects` registry table (migration 0022) and
tools/state/project_context.py's resolver — it holds no path, no safety
rule and no project list of its own; it lists the ids the registry
currently carries (today: `cis` and `swa`) and resolves each one through
the SAME resolver the detail route uses, so the portfolio overview and a
single project's detail page can never disagree about whether that
project is safe or reachable.

dev_continuity_events revision 180 (task WB.1, approved) is the
reconciliation authority for this slice: the Workbench is an
application-level portfolio hub over CIS, WIASW and SWA as peer projects.
ADR-SEED-010's repository/spine isolation is unchanged by that
reconciliation — this module never shares a runtime spine across
projects. WIASW carries no registry row and is not represented by this
read model; it is not seeded or inferred here.

WHAT THIS DOES NOT DO. It accepts no repo_path, spine_path or db_path from
a caller; the only input either public function takes beyond an optional
internal `db_path` override (used by tests the same way every other
tools/state/ module's db_path override is used) is a project_id string. It
issues no write of any kind — every connection it opens, directly or via
project_context.py, is mode=ro.

PUBLIC-FACING PROJECTION. resolve_project_context() returns resolved,
validated absolute filesystem paths for internal callers. This module's two
public functions strip those paths (_public_view()) before returning — the
HTTP layer (runtime/api/portfolio.py) serializes exactly this projection, so
a project's real server-side filesystem layout is never sent to a browser,
only its validated status.
"""
import sys
from pathlib import Path

_STATE_DIR = Path(__file__).resolve().parent
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import canonical_state as cs  # noqa: E402  (shared DB default: the CIS spine)
import project_context as pc  # noqa: E402

READ_MODEL_KIND = "cis_portfolio"

# Keys resolve_project_context() returns for internal use that must never
# reach the HTTP response — see module docstring.
_INTERNAL_ONLY_KEYS = ("repo_path", "spine_path")


def _connect(db_path=None):
    import sqlite3
    conn = sqlite3.connect(f"file:{db_path or cs.DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _public_view(context):
    return {k: v for k, v in context.items() if k not in _INTERNAL_ONLY_KEYS}


def list_projects(db_path=None):
    """Every project the registry currently carries, each resolved through
    project_context.resolve_project_context(). One unsafe or unreachable
    project never removes another from this list, and never raises —
    the ids themselves come straight from the same table each is resolved
    against, so an id this function just read can only fail to resolve if
    the row was deleted between the two queries."""
    conn = _connect(db_path)
    try:
        ids = [r["id"] for r in conn.execute("SELECT id FROM projects ORDER BY id").fetchall()]
    finally:
        conn.close()

    projects = [_public_view(pc.resolve_project_context(pid, db_path=db_path)) for pid in ids]
    return {
        "read_model": READ_MODEL_KIND,
        "count": len(projects),
        "projects": projects,
    }


def get_project(project_id, db_path=None):
    """One project's resolved, public-facing context. Raises
    project_context.UnknownProjectError if project_id names no registry row
    — the only case the API layer maps to 404."""
    return _public_view(pc.resolve_project_context(project_id, db_path=db_path))


if __name__ == "__main__":
    import json

    if len(sys.argv) == 1:
        print(json.dumps(list_projects(), indent=2))
    else:
        try:
            print(json.dumps(get_project(sys.argv[1]), indent=2))
        except pc.UnknownProjectError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)
