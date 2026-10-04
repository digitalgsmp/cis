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
import json
import os
import re
import sqlite3
import sys
from pathlib import Path


# Portable by construction (Card 04 R1 correction): derive both defaults
# from this module's own location instead of a hardcoded host path. The
# host repo lives at /mnt/projects/cis; cis-pipeline bind-mounts the same
# repo at /workspace/cis -- a hardcoded host path made the container's
# --verify report the build list missing even at an identical DB revision
# (reproduced: only setting CIS_QUEUE_SRC=/workspace/cis/... by hand fixed
# it). Path(__file__).resolve() already reflects wherever this file
# actually is, so parents[2] is the right project root in either
# environment with no override needed. Explicit CIS_SPINE_PATH/
# CIS_QUEUE_SRC env overrides are still honored first, unchanged.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB = os.environ.get("CIS_SPINE_PATH", str(PROJECT_ROOT / "data" / "cis_memory.db"))
SRC = os.environ.get("CIS_QUEUE_SRC",
                     str(PROJECT_ROOT / "docs" / "UNIFIED_BUILD_LIST.md"))

sys.path.insert(0, str(PROJECT_ROOT / "tools" / "state"))
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


# A '---' rule is how this file separates items; markers belong with the item's
# prose, above it, not orphaned underneath.
_RULE_RE = re.compile(r"^-{3,}\s*$")

# The marker count classify_status() in extract_queue_items.py uses to decide
# the status is AMBIGUOUS. It is anchored, and it is the exact expression a
# marker insertion must not push from 1 to 2 -- two markers fail the recovery
# run outright.
_NEED_MARKER_COUNT_RE = re.compile(r"^\*\*Need:", re.M)

# The visible '**Scope:**' line. SINCE ADR-PIPE-009 THIS IS PROSE, NOT A
# RECOVERY CARRIER: the extractor no longer reads scope from it at all, so a
# line in this shape is for a human reading the document and the cis:scope
# marker is what survives a recovery cycle.
_SCOPE_LINE_RE = re.compile(r"^\*\*Scope:?\*\*.*$", re.M)


def _split_trailer(lines):
    """Split body lines into (content, trailer).

    trailer is the trailing blank lines plus an optional trailing '---' rule and
    the blanks above it. Inserting a marker between the two keeps it attached to
    the item it describes and leaves the item separator where it was, so the
    rendered file still reads as the same document.
    """
    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    if end > 0 and _RULE_RE.match(lines[end - 1]):
        end -= 1
        while end > 0 and not lines[end - 1].strip():
            end -= 1
    return lines[:end], lines[end:]


def _insert_marker(body_md, marker_line):
    """Append marker_line as its own paragraph, above any trailing rule."""
    content, trailer = _split_trailer(body_md.split("\n"))
    if content:
        content.append("")
    content.append(marker_line)
    return "\n".join(content + trailer)


def rewrite_status(body_md, need_status):
    """Put a canonical '**Need: <STATUS>.**' marker into body_md.

    Called for items whose status was EXPLICITLY changed via queue_set.py
    (status_changed_at not null). The three marker shapes mirror
    classify_status() in extract_queue_items.py; each is replaced wholesale —
    token, stale date, and trailing prose — because the date belongs to the OLD
    status. Unchanged items never reach here, which is what keeps the render
    byte-faithful at baseline.

    Canonical form chosen over minimal-token-replacement because a half-edit
    leaves artefacts like 'DONE-09-04.' (stale date glued to the new status).

    WHEN NO MARKER EXISTS THE MARKER IS INSERTED (OQ-TRIAGE-001 option 1).
    This function used to return body_md unchanged in that case, which meant a
    status written through queue_set.py was invisible in the projection and was
    reset to NULL by the documented recovery path. Measured 2026-10-03: 0 of the
    56 unclassified items carry a marker of any shape, so for triage the
    insertion branch is the ONLY branch that ever runs.
    """
    display = need_status.replace("_", " ")
    marker = "**Need: " + display + ".**"
    # Shape 1 -- '**Need:** VALUE' (value bare, outside the bold)
    m = re.search(r"\*\*Need:\*\*\s*[A-Za-z_ ]+", body_md)
    if m:
        return body_md[:m.start()] + marker + body_md[m.end():]
    # Shape 2 -- '**Need: VALUE ...**' (key inside the bold span)
    m = re.search(r"\*\*Need:\s*[A-Za-z][A-Za-z_ ]{0,30}[^*]*\*\*", body_md)
    if m:
        return body_md[:m.start()] + marker + body_md[m.end():]
    # Shape 3 -- bare '**DONE ...**' marker with no Need key
    m = re.search(r"\*\*(?:DONE|HALF DONE|RESOLVED)\b[^*]*\*\*", body_md)
    if m:
        return body_md[:m.start()] + marker + body_md[m.end():]
    # No marker of any recognised shape. Guard on the SAME anchored count the
    # extractor uses before inserting: a malformed '**Need: x' with no closing
    # bold matches none of the shapes above but still counts as a marker there,
    # and inserting beside it would take the count to 2 and fail recovery.
    if _NEED_MARKER_COUNT_RE.search(body_md):
        return body_md
    return _insert_marker(body_md, marker)


def rewrite_scope(body_md, scope):
    """Put a canonical '**Scope:** <scope>' line into body_md.

    HUMAN VISIBILITY ONLY SINCE ADR-PIPE-009. This used to be how scope reached
    the recovery path; it no longer is, because '**Scope:**' is overloaded in
    this document and prose may not carry a classification (clause 3). Recovery
    now reads the cis:scope marker, which apply_scope_marker() writes for EVERY
    non-NULL scope rather than only for the event-gated rows this function sees.
    What is left here is the courtesy of showing an audited scope write to a
    person reading the markdown.

    An existing prose scope ('**Scope — REPOINTED ...**', item 1.20) is still
    left alone rather than rewritten: rewriting someone's recorded prose is not
    this function's business, and nothing depends on it any more.
    """
    marker = "**Scope:** " + scope
    m = _SCOPE_LINE_RE.search(body_md)
    if m:
        return body_md[:m.start()] + marker + body_md[m.end():]
    return _insert_marker(body_md, marker)


# ── the machine-owned scope marker (ADR-PIPE-009 clauses 2-4) ───────────────
# THIS, not '**Scope:**', is what carries scope through a recovery cycle. The
# prose form stayed overloaded in this document -- both a classification marker
# and an ordinary paragraph label, with 12 legitimate scopes and 6 authoritative
# NULLs wearing structurally identical wrapped paragraphs -- so the
# classification moved to a marker this module owns and the extractor reads
# exactly, and historical prose is now preserved rather than interpreted.
#
# EMITTED FOR EVERY NON-NULL SCOPE, NOT ONLY AUDITED ONES (clause 4). The
# event-gated '**Scope:**' insertion below cannot bootstrap recovery identity:
# there are ZERO queue_item_events rows with field='scope' in production, so
# gating on them would have left all 63 stored scopes unrecoverable.
_SCOPE_MARKER_PROBE = re.compile(r"^<!--\s*cis:scope=")


def scope_marker(scope):
    """'<!-- cis:scope="VALUE" -->' with VALUE JSON-encoded.

    JSON because the marker must carry what the column already holds: item
    1.20's legacy value contains an embedded newline and another contains a
    double quote. '>' is escaped so no value can close the comment early with
    '-->'. Nothing is normalised -- clause 9 forbids cleaning a legacy value to
    make a proof pass.
    """
    return "<!-- cis:scope=" + json.dumps(scope, ensure_ascii=False).replace(
        ">", "\\u003e") + " -->"


def _strip_scope_markers(lines):
    """Drop any existing marker line AND the blank line _insert_marker put above
    it, so remove-then-insert is exactly inverse.

    Needed for idempotence across a recovery cycle: after a --force recovery the
    stored body_md CONTAINS the marker, and re-rendering must reproduce the same
    bytes rather than accumulate a blank line per render.
    """
    out = []
    for line in lines:
        if _SCOPE_MARKER_PROBE.match(line):
            if out and not out[-1].strip():
                out.pop()
            continue
        out.append(line)
    return out


def apply_scope_marker(body_md, scope):
    """Ensure body_md carries exactly one canonical marker, or none for NULL."""
    body = "\n".join(_strip_scope_markers(body_md.split("\n")))
    if scope is None:
        return body
    return _insert_marker(body, scope_marker(scope))


def explicitly_scoped(conn):
    """Item numbers whose scope was set through queue_set.py.

    queue_items has a status_changed_at column but no scope_changed_at, and
    adding one would be a migration this card does not need: queue_item_events
    is already the append-only authority on what was explicitly changed, and a
    `field='scope'` row there says exactly that. Items with no scope event are
    left byte-untouched, which is what keeps --verify meaningful at baseline.
    """
    try:
        return {r[0] for r in conn.execute(
            "SELECT DISTINCT item_num FROM queue_item_events WHERE field='scope'")}
    except sqlite3.Error:
        return set()


def render(conn):
    """Reconstruct the markdown by interleaving sections and items in PHYSICAL
    order (source_line), not numbered tier. Item 2.38 is numbered tier 2 but
    sits under '# TIER 3' in the file; sorting by tier would move it.

    Items whose status was changed through queue_set.py (status_changed_at set)
    get their marker rewritten to the new status, and items whose scope was set
    through it (a queue_item_events row with field='scope') get a '**Scope:**'
    line, so the rendered markdown never lags behind the database on either
    triage field. An item changed in neither way is emitted byte-for-byte."""
    sections = conn.execute(
        "SELECT kind, content, tier, source_line FROM queue_sections ORDER BY seq"
    ).fetchall()
    items = conn.execute(
        "SELECT item_num, body_md, source_line, need_status, scope, status_changed_at "
        "FROM queue_items ORDER BY source_line"
    ).fetchall()
    scoped = explicitly_scoped(conn)

    blocks = [banner(conn)]
    # preamble comes first, before the first tier header
    preamble = next((c for k, c, t, sl in sections if k == "preamble"), "")
    blocks.append(preamble)

    # then tier headers and items, interleaved by source_line
    segments = []
    for k, c, t, sl in sections:
        if k == "tier_header":
            segments.append((sl, c))
    for item_num, body_md, sl, need_status, scope, changed_at in items:
        if changed_at is not None and need_status is not None:
            body_md = rewrite_status(body_md, need_status)
        if item_num in scoped and scope:
            body_md = rewrite_scope(body_md, scope)
        # LAST, and for EVERY row rather than only audited ones: this is the
        # marker the recovery path actually reads (ADR-PIPE-009 clause 4). The
        # visible '**Scope:**' line above remains a human-readable courtesy for
        # an audited write; it is no longer the recovery mechanism.
        body_md = apply_scope_marker(body_md, scope)
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
