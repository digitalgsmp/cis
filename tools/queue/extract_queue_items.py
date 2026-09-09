#!/usr/bin/env python3.12
"""Extract docs/UNIFIED_BUILD_LIST.md into queue_items.

BUILD LIST 3.21. The markdown stays authoritative; this table is a projection
regenerated from it, the same relationship AGENTS.md already has to its
generator. A projection rebuilt from its source cannot drift from it — it can
only be stale, which source_sha makes detectable.

THE CONTRACT, as reviewed across three packets:

1. Both item forms are items: '### N.M Title' and '- **N.M** text'.
2. tier comes from the item NUMBER, never the enclosing '# TIER' header. They
   already disagree once (2.38 sits under Tier 3) and the number is what every
   cross-reference in the file uses.
3. All four status spellings are recognised, including the two where the key
   sits inside the bold and the bare '**DONE ...**' markers with no key at all.
4. An item with NO status prose gets need_status=NULL. That is a normal,
   expected outcome for most items and it does NOT fail the run. No count is
   written here: it changes with every edit to the list.
5. UNPARSED means something narrower: a '**Need:' marker is PRESENT but its
   token is not in the known vocabulary. The literal text is kept in need_raw.
   As of 2026-09-09 this fires for EITHER '**Need:' shape, not just one.
6. The run fails ONLY on UNPARSED > 0, printing the item numbers, because that
   is the one condition where the extractor knows it is losing information.

An earlier version of this contract conflated 4 and 5 — it made "no status"
unclassifiable, and made any unclassifiable item fail the run. It would have
imported nothing, ever. Both lineages caught it.

KNOWN BLIND SPOT, named rather than hidden: an item stating its status in prose
this parser does not recognise AS status prose — Qwen's example, "Status:
BLOCKED on 2.13" — lands in the NULL bucket alongside items that genuinely have
no status, and nothing fires. Rule 6 catches unknown VALUES, not unknown SHAPES.
There is no check for it here.
"""
import hashlib
import os
import re
import sqlite3
import sys

# Overridable ONLY so the negative test can run against a scratch file and a
# scratch database. Production runs take the defaults.
DB = os.environ.get("CIS_QUEUE_DB", "/mnt/projects/cis/data/cis_memory.db")
SRC = os.environ.get("CIS_QUEUE_SRC",
                     "/mnt/projects/cis/docs/UNIFIED_BUILD_LIST.md")

HEADING_RE = re.compile(r"^### ([0-9]+\.[0-9]+)\s*(.*)$")
BULLET_RE = re.compile(r"^- \*\*([0-9]+\.[0-9]+)\*\*\s*(.*)$")
TIER_RE = re.compile(r"^# TIER\b")

# The recognised status vocabulary. A token after '**Need:' that is NOT in here
# stops the run -- see classify_status.
#
# BUILT IS RECOGNISED BUT STORED AS DONE. queue_items.need_status carries a CHECK
# constraint listing five values, and BUILT is not one of them; storing it
# literally needs a schema change, which is out of scope for the card that added
# it. This follows the RESOLVED -> DONE mapping already in shape 3 below: the
# vocabulary is what the parser can READ, the CHECK is what the column can HOLD,
# and need_raw preserves the literal prose either way.
KNOWN = {"OPEN", "UNASSESSED", "DONE", "HALF_DONE", "BUILT"}
STORE_AS = {"BUILT": "DONE", "RESOLVED": "DONE"}


def parse_items(text):
    """Partition the file into items. Boundaries are the next item start of
    either form, or the next '# TIER' header — whichever comes first."""
    lines = text.split("\n")
    marks = []
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            marks.append((i, m.group(1), "heading", m.group(2).strip()))
            continue
        m = BULLET_RE.match(line)
        if m:
            marks.append((i, m.group(1), "bullet", m.group(2).strip()))
            continue
        if TIER_RE.match(line):
            marks.append((i, None, "tier", None))

    items = []
    for k, (i, num, form, title) in enumerate(marks):
        if num is None:
            continue
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        items.append({
            "item_num": num,
            "form": form,
            "title": title,
            "body_md": "\n".join(lines[i:end]),
            "source_line": i + 1,
        })
    return items


def _normalise(raw):
    """'HALF DONE 2026-09-04.' -> HALF_DONE;  'BUILT 2026-09-09,' -> BUILT."""
    words = [w.strip(":.,;)—") for w in raw.split() if w.strip(":.,;)—")]
    if not words:
        return None
    two = "_".join(w.upper() for w in words[:2])
    if two in KNOWN:
        return two
    return words[0].upper()


def classify_status(body):
    """Return (need_status, need_raw).

    THE TWO CASES BELOW ARE ONE LINE APART AND MEAN OPPOSITE THINGS:

      * NO '**Need:' MARKER ANYWHERE  ->  (None, None).
        The item states no status. NORMAL and expected; most items are like
        this. Does NOT fail the run.

      * A '**Need:' MARKER WHOSE TOKEN IS NOT IN `KNOWN`  ->  ('UNPARSED', raw).
        The item states a status this parser cannot read. That is information
        being LOST, and it FAILS the run so the spelling can be added.

    DEMONSTRATED 2026-09-09, which is why this changed. Item 2.25 carried
    '**Need: BUILT 2026-09-09, ONE-WAY.**' and was recorded as "no status
    stated". Shape 2 below used to match only the four literal known tokens, so
    an unknown token fell through every branch to None. UNPARSED fired only on
    the '**Need:** VALUE' shape -- unknown VALUES were caught, unknown SHAPES
    were not. That is precisely the gap the r3 review named, and it was hit
    within hours by the person who recorded it.
    """
    # AMBIGUITY BEATS PRECEDENCE. Two status claims in one item is not a
    # question of which wins -- the item's status is UNKNOWN, and saying so is
    # the only honest answer. Before 2026-09-09 this function returned on the
    # FIRST marker and the second was invisible; that silent precedence rule is
    # what let a negative test pass while never exercising the path it tested.
    #
    # Anchored to line start (re.M) on purpose. Item 3.21 discusses '**Need:'
    # markers in its own prose nine times inside backticks; an unanchored count
    # reads those as nine extra markers and fails the run on a correct file.
    markers = re.findall(r"^\*\*Need:", body, re.M)
    if len(markers) > 1:
        return "UNPARSED", "%d '**Need:' markers in one item — status ambiguous" % len(markers)

    # Shape 1 -- '**Need:** VALUE'
    m = re.search(r"^\*\*Need:\*\*\s*([A-Za-z_ ]+)", body, re.M)
    if m:
        raw = m.group(1).strip()
        token = _normalise(raw.split("\u2014")[0])
        if token not in KNOWN:
            return "UNPARSED", raw
        return STORE_AS.get(token, token), raw

    # Shape 2 -- '**Need: VALUE ...**', the key inside the bold. Captures ANY
    # token and then validates. It used to match only the known four, which is
    # exactly how BUILT reached None instead of stopping the run.
    m = re.search(r"^\*\*Need:\s*([A-Za-z][A-Za-z_ ]{0,30})", body, re.M)
    if m:
        raw = m.group(1).strip()
        token = _normalise(raw)
        if token not in KNOWN:
            return "UNPARSED", raw
        return STORE_AS.get(token, token), raw

    # Shape 3 -- a bare '**DONE ...**' marker with no Need key at all.
    m = re.search(r"\*\*(DONE|HALF DONE|RESOLVED)\b[^*]*\*\*", body)
    if m:
        token = m.group(1).replace(" ", "_")
        return STORE_AS.get(token, token), m.group(0)[:200]

    # NO STATUS MARKER OF ANY KIND. The normal case. Does not fail the run.
    return None, None


def extract_scope(body):
    m = re.search(r"\*\*Scope:?\*\*[:\s]*([^\n]+)", body)
    if m:
        return m.group(1).strip()[:300]
    m = re.search(r"\*\*Scope[^*]*\*\*\s*([^\n]*)", body)
    return m.group(0).strip()[:300] if m else None


def main():
    text = open(SRC, encoding="utf-8").read()
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    items = parse_items(text)

    rows, unparsed = [], []
    for it in items:
        status, raw = classify_status(it["body_md"])
        if status == "UNPARSED":
            unparsed.append((it["item_num"], raw))
        if status is not None and status not in KNOWN and status != "UNPARSED":
            unparsed.append((it["item_num"], raw))
            status = "UNPARSED"
        rows.append((
            it["item_num"],
            int(it["item_num"].split(".")[0]),
            it["title"] or it["item_num"],
            it["body_md"],
            it["form"],
            extract_scope(it["body_md"]),
            status,
            raw,
            it["source_line"],
            sha,
        ))

    print("source            : %s" % SRC)
    print("source_sha        : %s" % sha)
    print("items parsed      : %d" % len(rows))
    print("UNPARSED          : %d" % len(unparsed))

    # RULE 6 — the only condition that fails the run.
    if unparsed:
        print("\nSTATUS PROSE PRESENT BUT UNRECOGNISED — nothing imported:")
        for num, raw in unparsed:
            print("  %-6s %r" % (num, raw))
        print("\nAn unknown TOKEN means adding the spelling to classify_status().")
        print("Two MARKERS in one item means the item states its status twice —")
        print("remove one. Either way nothing was imported; the table is unchanged.")
        return 1

    conn = sqlite3.connect(DB)
    try:
        conn.execute("DELETE FROM queue_items")
        conn.executemany(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "scope, need_status, need_raw, source_line, source_sha) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
    finally:
        conn.close()

    print("\nwrote %d rows to queue_items" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
