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

A STATUS WRITE ALSO CHECKS THE RECOVERY CONTRACT, FAIL CLOSED (OQ-TRIAGE-002,
2026-10-03). The value has to be one the documented recovery path
(extract_queue_items.py --force) can read back out of the generated build list,
and that vocabulary is derived by importing the extractor rather than copied here
-- a copy is what drifted in the first place. If the vocabulary cannot be
determined at all, the status write is REFUSED; it used to be allowed, which
disabled the guard in the one case where it mattered. A scope-only write does not
consult the extractor and is unaffected.

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
    recovery path ITSELF rather than copied. Returns (statuses, error): on any
    failure `statuses` is None and `error` says why, and the caller REFUSES the
    status write. See the fail-closed note below.

    THE DIVERGENCE THIS EXISTS TO STOP, found 2026-10-03 while adding the scope
    write path. queue_items.need_status's CHECK constraint permits 10 values.
    extract_queue_items.py -- the `--force` recovery path -- carried its own
    KNOWN vocabulary of 5: BUILT, DONE, HALF_DONE, OPEN, UNASSESSED. The other
    five (PARTLY, UNCLEAR, PRESENT_UNPROVEN, NEEDS_ERIC, NO_CHECK_WRITTEN) parsed
    to UNPARSED, and the extractor's rule 6 FAILS THE WHOLE RECOVERY RUN on
    UNPARSED > 0 and imports nothing. The extractor's own comment documented the
    split as deliberate -- "the vocabulary is what the parser can READ, the
    CHECK is what the column can HOLD" -- but it was written when the CHECK
    listed five values, and the CHECK had since grown to ten while KNOWN did
    not. Nothing detected that.

    It stayed harmless only because the projection never WROTE a status into an
    item that had no marker, so these values never reached the markdown. Marker
    insertion (OQ-TRIAGE-001 option 1) removes that accident, which is why the
    guard was needed.

    OQ-TRIAGE-002 (2026-10-03) then repaired the extractor rather than leaving
    the guard to refuse legitimate statuses forever: all nine stored statuses now
    round-trip, and the only CHECK value this returns without is UNPARSED, the
    extractor's own "marker present but unreadable" sentinel. So in normal
    operation this guard refuses nothing a triage pass needs.

    Derived by import, never duplicated, so the two cannot drift apart again.

    FAIL CLOSED (OQ-TRIAGE-002 review finding). This used to return None on
    failure and the caller then DECLINED TO ENFORCE -- so the one condition under
    which the guard mattered most, an unreadable or broken recovery path, was the
    condition under which it stopped guarding. An unverifiable recovery contract
    is not a verified one.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "extract_queue_items.py")
    if not os.path.exists(path):
        return None, "%s does not exist" % path
    try:
        spec = importlib.util.spec_from_file_location("_cis_queue_extractor", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        known = set(mod.KNOWN)
        store_as = dict(mod.STORE_AS)
    except Exception as e:
        return None, "%s could not be imported: %s: %s" % (path, type(e).__name__, e)
    if not known:
        return None, "%s defines an EMPTY KNOWN vocabulary" % path
    # BUILT is readable but stored as DONE, so what the column can hold after a
    # round trip is the stored form.
    return {store_as.get(k, k) for k in known}, None

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

# The three hard limits are the CANONICAL SINGLE-LINE WRITE CONTRACT, not taste.
# They began as round-trip limits: the old recovery reader was
# `\*\*Scope:?\*\*[:\s]*([^\n]+)` truncated to [:300], so a newline or a longer
# value came back DIFFERENT from what was written. ADR-PIPE-009 removed that
# particular failure -- the cis:scope marker JSON-encodes the value, so a newline
# would now survive -- and the limits are KEPT anyway, deliberately: a scope is a
# short statement of where work lives, the one legacy value that broke this
# contract (item 1.20, an embedded newline inside a 300-character truncation
# artefact of the old parser) is recorded as integrity debt rather than a
# precedent, and clause 9 forbids cleaning it. Rejecting at the write path is
# still the only place that cannot be bypassed.
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
        return None, ("--scope contains a newline. A scope is a single-line "
                      "statement of where the work lives; the one stored value that "
                      "breaks that (item 1.20) is recorded as legacy integrity debt "
                      "under ADR-PIPE-009 clause 9, not a precedent. Put the detail "
                      "in --note."), notes
    if len(value) > SCOPE_MAX_LEN:
        return None, ("--scope is %d characters; the limit is %d. A scope states "
                      "WHERE the work lives and stays short enough to read in the "
                      "projection; the detail belongs in --note or the item body."
                      % (len(value), SCOPE_MAX_LEN)), notes
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
    # KEPT, WITH ONE REMAINING PURPOSE (OQ-TRIAGE-002 requirement 12). After the
    # vocabulary repair the only CHECK value the recovery path cannot read is
    # UNPARSED -- the extractor's own sentinel for "a marker was present and
    # unreadable", deliberately excluded so a recorded parse failure cannot
    # round-trip back in as a successful status. Writing UNPARSED through this
    # tool is therefore the one legitimate unrecoverable write: it records that an
    # item's stated status could not be read, which is a true fact about the item
    # that the projection then cannot carry back. It is not removed, because the
    # guard it overrides is derived by import and will refuse any FUTURE drift
    # between the CHECK and the extractor too -- and when that happens the
    # architect needs a way to write the already-legitimate value while the
    # extractor is repaired, which is precisely how this flag was used before.
    # It does NOT override the fail-closed branch above: see there.
    ap.add_argument(
        "--allow-unrecoverable-status", action="store_true",
        help="write a status the recovery extractor cannot read back. Since "
             "OQ-TRIAGE-002 that means UNPARSED and nothing else; any other "
             "status reaching this flag means the CHECK and the extractor have "
             "drifted apart again, which is a bug to fix, not to flag past.")
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
        # FAIL CLOSED. If the recovery-readable vocabulary cannot be determined,
        # no status is written -- and the override does NOT reach this branch.
        # --allow-unrecoverable-status is a deliberate decision about ONE status
        # known to be unreadable; it is not a way past a recovery path that
        # cannot be inspected at all, because then nobody knows what is being
        # overridden. The fix is to repair the extractor, not to flag past it.
        readable, readable_err = recovery_readable_statuses()
        if readable is None:
            print("REFUSED — cannot determine what the recovery path can read back.")
            print("")
            print("  %s" % readable_err)
            print("")
            print("queue_items.need_status is only safe to write if the documented")
            print("recovery path (extract_queue_items.py --force) can read the value")
            print("back out of the generated build list. That vocabulary is derived")
            print("from the extractor by import, and the import did not succeed, so")
            print("the guarantee cannot be checked.")
            print("")
            print("This refuses rather than assuming, because the assumption that")
            print("used to be made here was the permissive one: an unreadable")
            print("extractor disabled the guard exactly when it mattered most.")
            print("")
            print("Repair tools/queue/extract_queue_items.py and retry. A scope-only")
            print("write (--scope with no --status) does not consult this and still")
            print("works.")
            return 2
        if status not in readable and not a.allow_unrecoverable_status:
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
            print("OQ-TRIAGE-002 widened the recovery vocabulary to cover every")
            print("status the column can hold except UNPARSED, so a triage pass no")
            print("longer meets this refusal. If you are reading it for anything")
            print("other than UNPARSED, the extractor and the CHECK have drifted")
            print("again and THAT is the bug — not this guard.")
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
