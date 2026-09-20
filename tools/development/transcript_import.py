#!/usr/bin/env python3
"""transcript_import.py — explicit import of a supplied external-developer
transcript into dev_continuity_transcripts (WB.1C).

SUPPORTED INPUT FORMAT (the only one this module parses):
  Claude Code's own on-disk session transcript — a JSONL file under
  ~/.claude/projects/<project>/<session>.jsonl, one JSON object per line,
  {"type": "user"|"assistant", "message": {"content": ...}, ...}. This is
  exactly tools/ingest_claude_code_sessions.py's input format, and this
  module reuses that script's parser (read_exchanges/clean/blocks_to_text)
  rather than re-implementing it, per the task's "reuse suitable parser
  logic without all-history scanning" instruction.

EXPLICIT, NOT A SCAN: the caller must name one session_file. This module
never globs ~/.claude/projects/*/*.jsonl itself — that bulk path belongs to
ingest_claude_code_sessions.py and is out of this task's scope. An optional
`select` list of exchange indices narrows further to specific supplied/
selected messages.

CODEX TRANSCRIPT FORMAT: not implemented. This session had no access to a
live Codex chat transcript file to inspect, so no parser exists for one here.
Calling import_transcript(source="codex", ...) raises UnsupportedFormatError
rather than guessing a format or fabricating turns. This is the documented
limitation the task asked to be reported honestly instead of worked around.

Writes to dev_continuity_transcripts (migration 0039, staged, not applied to
the production spine) — NOT to knowledge_messages. This keeps transcript
import separate from generated/production KB content, per task scope.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ingest_claude_code_sessions as _icc  # noqa: E402  (reused parser)

from . import continuity_store as cs  # noqa: E402


class UnsupportedFormatError(Exception):
    pass


SUPPORTED_SOURCES = {"claude_code"}


def import_transcript(conn, *, task, session_file, actor, source="claude_code",
                       select=None):
    """Import exchanges from one explicit session_file into dev_continuity_transcripts.

    select: optional list of exchange indices (as produced by
    ingest_claude_code_sessions.read_exchanges) to import only specific
    supplied/selected messages instead of the whole file.

    Returns {"inserted": [source_key,...], "skipped_existing": [source_key,...],
    "session_file":..., "task":..., "source":...}. Idempotent: re-running with
    the same file/select is a no-op on the second pass (unique source_key).
    """
    if source not in SUPPORTED_SOURCES:
        raise UnsupportedFormatError(
            f"no parser for source={source!r}. Supported: {sorted(SUPPORTED_SOURCES)}. "
            "Reporting this honestly rather than guessing a format or "
            "synthesizing a synopsis as if it were a full import."
        )
    if not os.path.isfile(session_file):
        raise FileNotFoundError(session_file)

    cs._require_initialized(conn)  # explicit: no silent no-op on an uninitialized db

    existing = {
        r[0] for r in conn.execute(
            "SELECT source_key FROM dev_continuity_transcripts WHERE task=?", (task,)
        )
    }

    session_base = os.path.basename(session_file)
    inserted, skipped = [], []
    for idx, exchange in _icc.read_exchanges(session_file):
        if select is not None and idx not in select:
            continue
        for part, chunk in enumerate(_icc.split_long(exchange)):
            key = f"{source}/{task}/{session_base}/{idx}.{part}"
            if key in existing:
                skipped.append(key)
                continue
            conn.execute(
                "INSERT INTO dev_continuity_transcripts "
                "(task, source, source_key, session_file, exchange_index, part, "
                " content, imported_by) VALUES (?,?,?,?,?,?,?,?)",
                (task, source, key, session_file, idx, part, chunk, actor),
            )
            inserted.append(key)
    conn.commit()

    return {
        "inserted": inserted,
        "skipped_existing": skipped,
        "session_file": session_file,
        "task": task,
        "source": source,
    }


def list_imported(conn, task):
    cs._require_initialized(conn)
    rows = conn.execute(
        "SELECT id, source, source_key, session_file, exchange_index, part, "
        "       content, imported_by, imported_at "
        "FROM dev_continuity_transcripts WHERE task=? ORDER BY exchange_index, part",
        (task,),
    ).fetchall()
    return [dict(r) for r in rows]
