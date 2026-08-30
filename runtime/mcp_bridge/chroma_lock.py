"""chroma_lock.py — arbitration between Chroma readers and writers.

Chroma is not safe for concurrent access. Reading the store from the container
while a host-side ingest wrote to it produced, on 2026-08-29:

    Error deserializing pickle file: trailing bytes found

The container now queries Chroma live during a run, so this is not a rare race —
any ingest, re-embed or rebuild started on the host while a run is in flight can
corrupt that run's retrieval. Nothing arbitrated it. (UNIFIED BUILD LIST 0.3)

WHY A LOCK AND NOT A MAINTENANCE WINDOW. A window is a rule someone has to
remember; this has to hold when nobody is watching, which is the same standard
the rest of the system is held to — "every rule becomes a check that runs, or it
does not exist". A lock is enforced by the kernel whether or not anyone recalls
the rule.

WHY THIS WORKS ACROSS THE CONTAINER BOUNDARY. The repo is bind-mounted
(-v /mnt/projects/cis:/workspace/cis) and host and container share one kernel,
so an flock on the mounted file is the same lock on both sides. Verified
2026-08-30 rather than assumed: with the host holding it exclusively, the
container's non-blocking attempt raised BlockingIOError.

The lock file sits beside the store and follows it — CIS_CHROMA_PATH is set to
/workspace/cis/data/chroma_data in the container and defaults to the
/mnt/projects/cis equivalent on the host, and both name the same file on disk.

ASYMMETRIC BY DESIGN:

  readers take a SHARED lock, briefly, and GIVE UP rather than wait. Many
    readers may hold it at once. A run must never hang because someone started
    an ingest, so a reader that cannot get in degrades — pipeline_relay falls
    back to keyword search, which covers 100% of the corpus — and says so.

  writers take an EXCLUSIVE lock and RAISE rather than proceed. An ingest that
    cannot get the lock must not write anyway: proceeding is what corrupts a
    live read. Failing loudly is the point, since a silent corrupt read is
    exactly the failure this closes.
"""

import contextlib
import fcntl
import os
import time

DEFAULT_STORE = "/mnt/projects/cis/data/chroma_data"

# A reader waits only long enough to ride out lock hand-off between other
# readers, then degrades. Long enough to be useful, far too short to stall a run
# behind an ingest that runs for minutes.
READ_TIMEOUT = 5.0

# A writer waits out readers, which hold the lock only for the length of a
# query. Five minutes means a genuinely stuck reader surfaces as an error
# instead of an ingest that hangs until someone notices.
WRITE_TIMEOUT = 300.0

_POLL = 0.1


class ChromaBusy(RuntimeError):
    """Raised when a writer cannot get exclusive access to the store."""


def lock_path():
    """The lock file, beside the store and named from the same env var."""
    store = os.environ.get("CIS_CHROMA_PATH", DEFAULT_STORE)
    return store.rstrip("/") + ".lock"


def _acquire(fd, flags, timeout):
    """Poll for the lock until timeout. True if taken, False if not."""
    deadline = time.time() + timeout
    while True:
        try:
            fcntl.flock(fd, flags | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            if time.time() >= deadline:
                return False
            time.sleep(_POLL)


@contextlib.contextmanager
def chroma_read(timeout=READ_TIMEOUT):
    """Shared access for a query. Yields True if held, False if a writer has it.

    Yields rather than raises so the caller can degrade. Never blocks a run for
    longer than `timeout`.
    """
    path = lock_path()
    try:
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o664)
    except OSError:
        # No lock file and none creatable — an unarbitrated read is still better
        # than no retrieval at all, and the keyword index is unaffected either
        # way. The caller is told nothing was held.
        yield True
        return
    held = False   # bound before the try: the finally reads it on any path
    try:
        held = _acquire(fd, fcntl.LOCK_SH, timeout)
        yield held
    finally:
        try:
            if held:
                fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            pass
        os.close(fd)


@contextlib.contextmanager
def chroma_write(timeout=WRITE_TIMEOUT, what="ingest"):
    """Exclusive access for a write. Raises ChromaBusy rather than proceed."""
    path = lock_path()
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o664)
    try:
        if not _acquire(fd, fcntl.LOCK_EX, timeout):
            raise ChromaBusy(
                f"{what}: the Chroma store is in use and did not free up within "
                f"{timeout:.0f}s. Something is reading it — most likely a "
                f"pipeline run in the container. Nothing was written. Retry "
                f"when the run finishes, or stop it first.\nLock: {path}"
            )
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            pass
        os.close(fd)
