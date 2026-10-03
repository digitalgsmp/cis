#!/usr/bin/env python3
"""queue_set.py — the sole write path for the queue's classification.

BUILD LIST queue-authority-and-audit, step 3C. The database is the authority;
a classification change goes through this tool, never raw SQL, so every change
carries an append-only event row with the evidence that justified it. That is
the column that makes the phase-2 audit mean anything: no mark on a belief.

TWO CLASSIFICATION FIELDS, ONE WRITE PATH (OQ-TRIAGE-001 option 1, 2026-10-03).
ADR-PIPE-001 defines queue triage as classifying BOTH `scope` AND `need_status`
on the rows carrying neither. Until this card there was an audited write path
for need_status and NONE for scope, so triage could not be performed as defined
-- the gap that produced OQ-TRIAGE-001. `--scope` is added HERE, to the existing
tool, rather than in a second writer, because `queue_items` has exactly one
sanctioned mutation path and splitting it would create the second queue
authority ADR-PIPE-006 forbids.

Usage:
    python3 tools/queue/queue_set.py <item_num> --status <VALUE> \
        [--evidence "<command output>"] [--note "<why>"] [--by "<who>"]

    python3 tools/queue/queue_set.py <item_num> --scope "<TEXT>" \
        [--evidence "<command output>"] [--note "<why>"] [--by "<who>"]

    python3 tools/queue/queue_set.py <item_num> --status <VALUE> --scope "<TEXT>" \
        --evidence "<command output>"          # one atomic triage operation

At least one of --status / --scope is required. Passing both writes both in ONE
transaction with one event row per field, so a triage write cannot half-land:
either the item ends up with both fields or the row is untouched. That matters
because a row carrying need_status with scope still NULL is the shape that reads
as triaged without being triaged.

Refuses unknown items and unknown statuses. Evidence (command output) is
required for statuses that assert a code fact: DONE, OPEN, PARTLY,
PRESENT_UNPROVEN, UNCLEAR. NEEDS_ERIC and NO_CHECK_WRITTEN carry a note -- a
question or explanation -- instead, since those are decisions, not measurements.
A scope write requires evidence or a note for the same reason: it asserts where
in the system the work lives, which is a claim about code, not a preference.
"""
import argparse
import datetime
import importlib.util
import os
import re
import sqlite3
import sys

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")

KNOWN = {
    "OPEN", "UNASSESSED", "HALF_DONE", "DONE", "UNPARSED",
    "PARTLY", "UNCLEAR", "PRESENT_UNPROVEN", "NEEDS_ERIC", "NO_CHECK_WRITTEN",
}
EVIDENCE_REQUIRED = {"DONE", "OPEN", "PARTLY", "PRESENT_UNPROVEN", "UNCLEAR"}


def recovery_readable_statuses():
    """The statuses the documented recovery path can read back, taken from the
    recovery path ITSELF rather than copied.

    THE DIVERGENCE THIS EXISTS TO STOP, found 2026-10-03 while adding the scope
    write path. queue_items.need_status's CHECK constraint permits 10 values.
    extract_queue_items.py -- the `--force` recovery path -- carries its own
    KNOWN vocabulary of 5: BUILT, DONE, HALF_DONE, OPEN, UNASSESSED. The other
    five (PARTLY, UNCLEAR, PRESENT_UNPROVEN, NEEDS_ERIC, NO_CHECK_WRITTEN) parse
    to UNPARSED, and the extractor's rule 6 FAILS THE WHOLE RECOVERY RUN on
    UNPARSED > 0 and imports nothing. The extractor's own comment documents the
    split as deliberate -- "the vocabulary is what the parser can READ, the
    CHECK is what the column can HOLD" -- but it was written when the CHECK
    listed five values, and the CHECK has since grown to ten while KNOWN did
    not. Nothing detected that.

    It stayed harmless only because the projection never WROTE a status into an
    item that had no marker, so these values never reached the markdown. Marker
    insertion (OQ-TRIAGE-001 option 1) removes that accident, which is why the
    guard is needed now.

    Derived by import, never duplicated, so the two cannot drift apart again.
    Returns None if the extractor cannot be read, in which case the caller does
    not guess -- it declines to enforce rather than enforce a stale copy.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "extract_queue_items.py")
    try:
        spec = importlib.util.spec_from_file_location("_cis_queue_extractor", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        known = set(mod.KNOWN)
        store_as = dict(mod.STORE_AS)
    except Exception:
        return None
    # BUILT is readable but stored as DONE, so what the column can hold after a
    # round trip is the stored form.
    return {store_as.get(k, k) for k in known}

# `scope` IS FREE TEXT AND STAYS FREE TEXT. No CHECK constraint is added here
# and none should be: the column holds a scope token followed by its
# justification, and 4 of the 63 values already on the table are bare prose
# (file lists) that any enum would reject. Derived 2026-10-03 from every
# non-null value on the production table:
#
#   CONTAINER              28     UNDETERMINED            7
#   NOT_IN_CONTAINER_PATH  14     HOST                    1
#   REPO                    8     REPO/CONTAINER          1
#   (bare prose, no token)  4
#
# So the tokens below are a CONVENTION the tool reports departures from, not a
# vocabulary it enforces. An unrecognised leading token prints a note and is
# written anyway.
SCOPE_CONVENTION = (
    "CONTAINER", "REPO", "REPO/CONTAINER", "HOST",
    "NOT_IN_CONTAINER_PATH", "UNDETERMINED",
)

# The three hard limits are ROUND-TRIP limits, not taste. docs/UNIFIED_BUILD_LIST.md
# is a generated projection that the documented recovery path
# (extract_queue_items.py --force) reads back, and extract_scope() there is
# `\*\*Scope:?\*\*[:\s]*([^\n]+)` truncated to [:300]. A value with a newline or
# over 300 characters would therefore come back DIFFERENT from what was written
# -- silent classification loss on recovery. Rejecting at the write path is the
# only place that cannot be bypassed.
SCOPE_MAX_LEN = 300
_SCOPE_LEADING_TOKEN = re.compile(r"\s*([A-Z][A-Z_/]*)")


def validate_scope(raw):
    """Return (value, error, notes). `value` is the text to store.

    Rejects only what is either meaningless or unrecoverable; everything else
    is accepted with a note, because scope has no enum and must not grow one.
    """
    notes = []
    if raw is None:
        return None, "scope is None", notes
    value = raw.strip()
    if not value:
        return None, ("--scope is empty or whitespace-only. A scope states WHERE the "
                      "work lives; there is no blank answer to that."), notes
    if "\n" in value or "\r" in value:
        return None, ("--scope contains a newline. The build-list projection renders "
                      "scope as a single '**Scope:** ...' line and the recovery "
                      "extractor reads to end-of-line, so a multi-line value would not "
                      "survive a round trip. Put the detail in --note."), notes
    if len(value) > SCOPE_MAX_LEN:
        return None, ("--scope is %d characters; the limit is %d. extract_scope() in "
                      "the recovery path truncates at %d, so a longer value would come "
                      "back truncated and the classification would silently change."
                      % (len(value), SCOPE_MAX_LEN, SCOPE_MAX_LEN)), notes
    m = _SCOPE_LEADING_TOKEN.match(value)
    token = m.group(1) if m else None
    if token not in SCOPE_CONVENTION:
        notes.append(
            "note: %s does not open with a scope token from the existing convention "
            "(%s). Written as given -- scope is free text -- but check it is "
            "deliberate." % (repr(token) if token else "this value",
                             ", ".join(SCOPE_CONVENTION)))
    return value, None, notes


def main():
    ap = argparse.ArgumentParser(
        description="Write queue_items classification (need_status and/or scope) "
                    "through the one audited path.")
    ap.add_argument("item_num")
    ap.add_argument("--status", default=None)
    ap.add_argument("--scope", default=None)
    ap.add_argument("--evidence", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--by", default="")
    ap.add_argument(
        "--allow-unrecoverable-status", action="store_true",
        help="write a status the recovery extractor cannot read back. Requires "
             "an architect decision on the recovery contract; see OQ-TRIAGE-002.")
    a = ap.parse_args()

    if a.status is None and a.scope is None:
        print("nothing to write: pass --status, --scope, or both.")
        print("ADR-PIPE-001 defines triage as BOTH fields; passing both together")
        print("writes them atomically, which is the shape triage should use.")
        return 2

    status = None
    if a.status is not None:
        status = a.status.upper()
        if status not in KNOWN:
            print("unknown status: %r" % a.status)
            print("known: %s" % ", ".join(sorted(KNOWN)))
            return 2
        if status in EVIDENCE_REQUIRED and not a.evidence.strip():
            print("--evidence is required for %s." % status)
            print("The rule is: no mark without the command output that justified it.")
            return 2
        readable = recovery_readable_statuses()
        if (readable is not None and status not in readable
                and not a.allow_unrecoverable_status):
            print("%s cannot survive the documented recovery path." % status)
            print("")
            print("extract_queue_items.py --force reads status back out of the")
            print("generated build list, and its KNOWN vocabulary is: %s."
                  % ", ".join(sorted(readable)))
            print("%s parses to UNPARSED there, and the extractor's rule 6 fails" % status)
            print("the entire recovery run on UNPARSED > 0 — importing nothing.")
            print("")
            print("So writing it would produce a build list that cannot be recovered.")
            print("Refused rather than written, because the damage only shows up at")
            print("recovery time, when the table is already gone.")
            print("")
            print("This needs an architect decision on the recovery contract, not a")
            print("flag: see OQ-TRIAGE-002. --allow-unrecoverable-status exists so")
            print("that decision can be carried out once it is made.")
            return 2

    scope = None
    scope_notes = []
    if a.scope is not None:
        scope, err, scope_notes = validate_scope(a.scope)
        if err:
            print(err)
            return 2
        if not a.evidence.strip() and not a.note.strip():
            print("--evidence or --note is required with --scope.")
            print("A scope asserts where in the system the work lives. That is a claim")
            print("about code, so it carries the output or the reasoning behind it.")
            return 2

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    row = cur.execute(
        "SELECT need_status, scope FROM queue_items WHERE item_num=?", (a.item_num,)
    ).fetchone()
    if row is None:
        conn.close()
        print("unknown item: %r (not in queue_items)" % a.item_num)
        return 2
    old_status, old_scope = row

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    who = a.by or os.environ.get("USER", "")

    # ONE TRANSACTION FOR BOTH FIELDS. A two-field triage write either lands
    # whole or not at all -- no half-classified row, and no event row recording
    # a change that did not happen.
    try:
        conn.execute("BEGIN IMMEDIATE")
        if status is not None:
            cur.execute(
                "UPDATE queue_items SET need_status=?, status_changed_at=?, "
                "status_changed_by=? WHERE item_num=?",
                (status, now, who, a.item_num))
            cur.execute(
                "INSERT INTO queue_item_events "
                "(item_num, field, old_value, new_value, changed_at, changed_by, "
                "evidence, note) VALUES (?,?,?,?,?,?,?,?)",
                (a.item_num, "need_status", old_status, status, now, who,
                 a.evidence, a.note))
        if scope is not None:
            # status_changed_at/_by are the STATUS columns and are left alone by
            # a scope write; the event row is scope's own timestamp and author.
            cur.execute(
                "UPDATE queue_items SET scope=? WHERE item_num=?",
                (scope, a.item_num))
            cur.execute(
                "INSERT INTO queue_item_events "
                "(item_num, field, old_value, new_value, changed_at, changed_by, "
                "evidence, note) VALUES (?,?,?,?,?,?,?,?)",
                (a.item_num, "scope", old_scope, scope, now, who,
                 a.evidence, a.note))
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()

    if status is not None:
        print("item %s need_status: %r -> %r" % (a.item_num, old_status, status))
    if scope is not None:
        print("item %s scope: %r -> %r" % (a.item_num, old_scope, scope))
    for n in scope_notes:
        print(n)
    if a.evidence:
        print("evidence: %s" % a.evidence[:300])
    if a.note:
        print("note: %s" % a.note[:300])
    if status is not None and scope is not None:
        print("both triage fields written in one transaction.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
