#!/usr/bin/env python3
"""Render docs/UNIFIED_BUILD_LIST.md FROM the queue_items table.

BUILD LIST queue-authority-and-audit, phase 1, step 3D. The spine is a binary
nobody can diff; the rendered markdown is the readable history committed on
every change — the same relationship AGENTS.md already has to its generator.

The table is the authority. This writes the markdown back out by interleaving
queue_sections (preamble + tier headers) with queue_items (body_md), so the
file reproduces byte-faithfully except for the DO NOT EDIT banner.

Usage:
    python3 tools/queue/render_build_list.py            # write the markdown
    python3 tools/queue/render_build_list.py --stdout   # print to stdout instead
    python3 tools/queue/render_build_list.py --verify   # exit 1 if stale
"""
import os
import re
import sqlite3
import sys
from pathlib import Path

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
SRC = os.environ.get("CIS_QUEUE_SRC",
                     "/mnt/projects/cis/docs/UNIFIED_BUILD_LIST.md")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "state"))
import canonical_state  # noqa: E402

BANNER_STATIC = (
    "<!-- DO NOT EDIT — generated from queue_items (the spine). -->\n"
    "<!-- Change a status with tools/queue/queue_set.py; this file "
    "regenerates on commit. -->"
)


def banner(conn):
    """This file is a projection of the spine (CARD_01_SINGLE_AUTHORITY_
    CONTRACT.md, queue 4.29): stamp the same canonical state_revision the
    other exports (EXPORT_MANIFEST.json) carry, so staleness relative to
    the DB -- not just relative to this file's own last render -- is
    checkable without needing to re-render first. Deterministic: unchanged
    whenever the DB content it's derived from is unchanged, so --verify's
    byte-exact comparison still holds at baseline."""
    rev = canonical_state.compute_state_revision(conn)
    return BANNER_STATIC + f"\n<!-- state_revision: {rev} -->"


def rewrite_status(body_md, need_status):
    """Replace the whole status marker in body_md with a canonical
    '**Need: <STATUS>.**' reflecting need_status.

    Only called for items whose status was EXPLICITLY changed via queue_set.py
    (status_changed_at not null). The three marker shapes mirror
    classify_status() in extract_queue_items.py; each is replaced wholesale —
    token, stale date, and trailing prose — because the date belongs to the OLD
    status. Unchanged items never reach here, which is what keeps the render
    byte-faithful at baseline.

    Canonical form chosen over minimal-token-replacement because a half-edit
    leaves artefacts like 'DONE-09-04.' (stale date glued to the new status).
    """
    display = need_status.replace("_", " ")
    # Shape 1 -- '**Need:** VALUE' (value bare, outside the bold)
    m = re.search(r"\*\*Need:\*\*\s*[A-Za-z_ ]+", body_md)
    if m:
        return body_md[:m.start()] + "**Need: " + display + ".**" + body_md[m.end():]
    # Shape 2 -- '**Need: VALUE ...**' (key inside the bold span)
    m = re.search(r"\*\*Need:\s*[A-Za-z][A-Za-z_ ]{0,30}[^*]*\*\*", body_md)
    if m:
        return body_md[:m.start()] + "**Need: " + display + ".**" + body_md[m.end():]
    # Shape 3 -- bare '**DONE ...**' marker with no Need key
    m = re.search(r"\*\*(?:DONE|HALF DONE|RESOLVED)\b[^*]*\*\*", body_md)
    if m:
        return body_md[:m.start()] + "**Need: " + display + ".**" + body_md[m.end():]
    return body_md


def render(conn):
    """Reconstruct the markdown by interleaving sections and items in PHYSICAL
    order (source_line), not numbered tier. Item 2.38 is numbered tier 2 but
    sits under '# TIER 3' in the file; sorting by tier would move it.

    Items whose status was changed through queue_set.py (status_changed_at set)
    get their marker rewritten to the new status, so the rendered markdown never
    lags behind the database."""
    sections = conn.execute(
        "SELECT kind, content, tier, source_line FROM queue_sections ORDER BY seq"
    ).fetchall()
    items = conn.execute(
        "SELECT body_md, source_line, need_status, status_changed_at "
        "FROM queue_items ORDER BY source_line"
    ).fetchall()

    blocks = [banner(conn)]
    # preamble comes first, before the first tier header
    preamble = next((c for k, c, t, sl in sections if k == "preamble"), "")
    blocks.append(preamble)

    # then tier headers and items, interleaved by source_line
    segments = []
    for k, c, t, sl in sections:
        if k == "tier_header":
            segments.append((sl, c))
    for body_md, sl, need_status, changed_at in items:
        if changed_at is not None and need_status is not None:
            body_md = rewrite_status(body_md, need_status)
        segments.append((sl, body_md))
    segments.sort(key=lambda x: x[0])
    blocks.extend(c for sl, c in segments)

    return "\n".join(blocks)


def main():
    conn = sqlite3.connect(DB)
    text = render(conn)
    conn.close()

    if "--stdout" in sys.argv:
        sys.stdout.write(text)
        return 0

    if "--verify" in sys.argv:
        try:
            current = open(SRC, encoding="utf-8").read()
        except OSError:
            print("STALE (file missing)")
            return 1
        if current == text:
            print("fresh")
            return 0
        print("STALE — run tools/queue/render_build_list.py")
        return 1

    with open(SRC, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s (%d chars)" % (SRC, len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
