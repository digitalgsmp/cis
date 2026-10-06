"""
chroma_health.py — read-only health probe for the embedded Chroma store.

Chroma in this system runs embedded (chromadb.PersistentClient), not as an
HTTP server. This module answers exactly one question cheaply and without
side effects: is the on-disk Chroma metadata SQLite database present and
does it contain the knowledge_messages collection? It never imports
chromadb, never creates a store, and never mutates one.

A "healthy" result here means the embedded store file and its
knowledge_messages collection row are readable. It says nothing about
model-provider availability, semantic retrieval quality, or whether any
pipeline run has completed.
"""

import os
import sqlite3
import urllib.parse

REQUIRED_COLLECTION = "knowledge_messages"
_DETAIL_LIMIT = 300


def _bounded(message):
    """Cap detail strings so a pathological error can't blow up the response."""
    text = str(message)
    return text if len(text) <= _DETAIL_LIMIT else text[:_DETAIL_LIMIT] + "...(truncated)"


def _module_derived_repo_root():
    """Repo root derived from this file's own location, not a hardcoded string.

    This file lives at <repo_root>/runtime/chroma_health.py, so two
    directories up is the repo root — correct whether the checkout is at
    /workspace/cis (container) or /mnt/projects/cis (host dev checkout),
    with no need to guess between the two.
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_chroma_path():
    """Resolve the Chroma storage directory.

    Precedence matches the existing storage-client convention in
    runtime/mcp_bridge/chroma_index.py (_get_chroma_path): CIS_CHROMA_PATH
    wins outright when the variable is present in the environment at all —
    including an explicitly set empty string, which is reported as an
    error by the caller rather than silently falling through. Otherwise
    CIS_REPO_ROOT is honored if set, then a portable module-derived repo
    root as the final default.
    """
    if "CIS_CHROMA_PATH" in os.environ:
        return os.environ["CIS_CHROMA_PATH"], True

    repo_root = os.environ.get("CIS_REPO_ROOT") or _module_derived_repo_root()
    return os.path.join(repo_root, "data", "chroma_data"), False


def _read_journal_mode_flags(db_file):
    """Return the (write_version, read_version) header bytes, or None if
    the file is too short/unreadable to have a valid SQLite header. A value
    of 2 in both slots means the database is in WAL journal mode."""
    try:
        with open(db_file, "rb") as f:
            header = f.read(20)
    except OSError:
        return None
    if len(header) < 20:
        return None
    return header[18], header[19]


def _sqlite_ro_uri(db_file, extra_params=""):
    """Build a percent-encoded file: URI for a read-only SQLite connection.

    The path is percent-encoded (except '/') so that characters which are
    URI delimiters — '?' and '#' in particular — can't be misread as the
    start of a query string or fragment and silently redirect us at a
    different file than the one we intended to open.
    """
    quoted = urllib.parse.quote(os.path.abspath(db_file), safe="/")
    return f"file:{quoted}?mode=ro{extra_params}"


def check_embedded_chroma_health(chroma_path=None, explicit=None, timeout=2.0, _after_sidecar_check=None):
    """Read-only check of the embedded Chroma metadata store.

    Returns {"healthy": bool, "detail": str}. Never raises. Never writes to
    the fixture/store beyond what SQLite's WAL protocol requires it to.

    WAL handling: a WAL-mode SQLite database normally requires creating
    -wal/-shm sidecar files just to determine whether it has pending data,
    even when opened read-only. To avoid that here while still refusing to
    return a stale read from an actively-written database:
      - non-WAL databases are opened plain read-only (no WAL machinery
        involved, nothing to create);
      - WAL databases whose -wal and -shm sidecars already exist are opened
        plain read-only too — no new files are created, and any pending WAL
        content is correctly included;
      - WAL databases with neither sidecar present have, by construction,
        no pending WAL data (SQLite always creates -wal before any write
        transaction begins), so they are opened with immutable=1, which
        skips the WAL/shared-memory subsystem entirely and creates nothing;
      - WAL databases with exactly one sidecar present are an inconsistent
        state this probe refuses to touch — it fails closed rather than
        risk creating a file or misreading a partial write.
    There is an inherent gap between checking sidecar presence and opening
    the connection: a writer could begin its first transaction in that gap,
    which would make an immutable=1 read stale (it would not see the new
    WAL data). This is closed, not just documented: after the read
    completes, sidecar presence is checked again, and if a sidecar now
    exists that did not exist before the connect (i.e. a write started
    during our window), the result is discarded and reported unhealthy
    rather than trusted. See _after_sidecar_check in tests for how this is
    exercised deterministically.
    """
    if chroma_path is None:
        chroma_path, explicit = resolve_chroma_path()

    prefix = "explicitly configured CIS_CHROMA_PATH" if explicit else "chroma path"

    if explicit and not chroma_path:
        return {
            "healthy": False,
            "detail": "CIS_CHROMA_PATH is explicitly set but empty",
        }

    if not os.path.isdir(chroma_path):
        return {
            "healthy": False,
            "detail": _bounded(f"{prefix} not found: {chroma_path}"),
        }

    db_file = os.path.join(chroma_path, "chroma.sqlite3")
    if not os.path.isfile(db_file):
        return {
            "healthy": False,
            "detail": _bounded(f"chroma.sqlite3 not found at {chroma_path}"),
        }

    extra_params = ""
    used_immutable = False
    flags = _read_journal_mode_flags(db_file)
    is_wal = flags is not None and flags[0] == 2 and flags[1] == 2
    if is_wal:
        wal_exists = os.path.isfile(db_file + "-wal")
        shm_exists = os.path.isfile(db_file + "-shm")
        if wal_exists and shm_exists:
            extra_params = ""  # sidecars already live; reuse them, create nothing
        elif not wal_exists and not shm_exists:
            extra_params = "&immutable=1"  # provably no pending WAL data to miss
            used_immutable = True
        else:
            return {
                "healthy": False,
                "detail": _bounded(
                    f"embedded store at {chroma_path} is in an inconsistent WAL "
                    "state (only one of -wal/-shm present); refusing to read "
                    "without risking file creation or a stale result"
                ),
            }

    if _after_sidecar_check is not None:
        # Test-only seam: lets tests deterministically inject a writer
        # commit in the gap between the sidecar check above and the
        # connect below, to exercise the staleness guard after the read.
        _after_sidecar_check()

    uri = _sqlite_ro_uri(db_file, extra_params)
    conn = None
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=timeout)
        cur = conn.execute(
            "SELECT 1 FROM collections WHERE name = ? LIMIT 1",
            (REQUIRED_COLLECTION,),
        )
        found = cur.fetchone() is not None
    except sqlite3.Error as e:
        return {
            "healthy": False,
            "detail": _bounded(f"embedded store unreadable at {chroma_path}: {e}"),
        }
    except Exception as e:
        # Not a SQLite-level error (e.g. a bug in our own path handling) —
        # bounded, no raw message, so nothing unexpected reaches HTTP output.
        return {
            "healthy": False,
            "detail": f"embedded store check failed unexpectedly ({type(e).__name__}) at {chroma_path}",
        }
    finally:
        if conn is not None:
            conn.close()

    if used_immutable and (os.path.isfile(db_file + "-wal") or os.path.isfile(db_file + "-shm")):
        # A write began during our check-then-open window: our immutable
        # read was taken on the assumption that no WAL data existed, and
        # that assumption is now known to be false. Discard the read rather
        # than report a result that may be stale.
        return {
            "healthy": False,
            "detail": _bounded(
                f"a write began at {chroma_path} during the read-only check; "
                "discarding a possibly-stale result"
            ),
        }

    if not found:
        return {
            "healthy": False,
            "detail": _bounded(
                f"'{REQUIRED_COLLECTION}' collection not found in embedded "
                f"store metadata at {chroma_path}"
            ),
        }

    return {
        "healthy": True,
        "detail": _bounded(
            f"embedded '{REQUIRED_COLLECTION}' collection readable at {chroma_path} "
            "(read-only metadata check; not a measure of retrieval quality "
            "or model-provider availability)"
        ),
    }
