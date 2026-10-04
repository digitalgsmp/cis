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
7. The known vocabulary COVERS EVERY need_status the column can hold except
   UNPARSED itself (OQ-TRIAGE-002, 2026-10-03), and the normalisation that
   reaches it is derived FROM that vocabulary rather than fixed at two words.
   Before this, five legitimate stored statuses were unreadable here and any one
   of them in the projection failed the entire recovery run. See KNOWN below.

An earlier version of this contract conflated 4 and 5 — it made "no status"
unclassifiable, and made any unclassifiable item fail the run. It would have
imported nothing, ever. Both lineages caught it.

8. IDENTITY IS PART OF THE CONTRACT TOO (ADR-PIPE-009, OQ-TRIAGE-003,
   2026-10-04). The item IDENTIFIER grammar is derived from the authoritative
   queue rather than guessed, an item-shaped line this parser cannot read FAILS
   the run instead of vanishing from it, and a duplicate identity fails rather
   than collapsing two projected items into one row. Before this, two items were
   lost SILENTLY with the run exiting 0: WB.1, whose alphabetic prefix no regex
   here accepted, and 4.10, whose bullet carries its title INSIDE the bold span.
9. `scope` IS READ ONLY FROM A MACHINE-OWNED MARKER (ADR-PIPE-009 clauses 2-4).
   See extract_scope below. Prose can no longer create a classification.

KNOWN BLIND SPOT, named rather than hidden: an item stating its status in prose
this parser does not recognise AS status prose — Qwen's example, "Status:
BLOCKED on 2.13" — lands in the NULL bucket alongside items that genuinely have
no status, and nothing fires. Rule 6 catches unknown VALUES, not unknown SHAPES.
There is no check for it here.
"""
import hashlib
import json
import os
import re
import sqlite3
import sys

# Overridable ONLY so the negative test can run against a scratch file and a
# scratch database. Production runs take the defaults.
DB = os.environ.get("CIS_QUEUE_DB", "/mnt/projects/cis/data/cis_memory.db")
SRC = os.environ.get("CIS_QUEUE_SRC",
                     "/mnt/projects/cis/docs/UNIFIED_BUILD_LIST.md")

# ── item identifiers (ADR-PIPE-009 clause 5) ────────────────────────────────
# DERIVED FROM THE AUTHORITATIVE QUEUE, NOT GUESSED. Measured 2026-10-04 across
# all 132 authoritative rows: 131 numeric dotted ids and exactly one alphabetic-
# prefixed id, WB.1. So the grammar is an OPTIONAL uppercase alphabetic prefix
# plus a dot-separated numeric part.
#
# AT LEAST ONE DOT IS REQUIRED, and that is load-bearing rather than cosmetic:
# without it this matches '- **445** broad `except` blocks' and '- **62** of
# them are...', two of the 27 ordinary bullets in the file whose bold span opens
# with a bare integer. A date like '2026-06-19' is excluded for the same reason
# (no dot), as is '## 3.                 at char  1453' (nothing after the dot).
ITEM_ID = r"(?:[A-Z][A-Z0-9]*\.[0-9]+|[0-9]+\.[0-9]+)(?:\.[0-9]+)*"

HEADING_RE = re.compile(r"^### (" + ITEM_ID + r")(?=\s|$)\s*(.*)$")
# TWO BULLET FORMS, BOTH DEMONSTRATED IN THE FILE:
#   '- **4.20** text'              the identifier alone in the bold span
#   '- **4.10 TITLE — date.**'     the identifier AND title inside the bold span
# The second is why item 4.10 was never extracted at all. It is accepted here
# because the document demonstrably uses it, and the title is then the bold
# span's own text rather than whatever follows the span.
BULLET_RE = re.compile(r"^- \*\*(" + ITEM_ID + r")\*\*\s*(.*)$")
BULLET_TITLED_RE = re.compile(r"^- \*\*(" + ITEM_ID + r")\s+([^*]*?)\s*\*\*\s*(.*)$")
TIER_RE = re.compile(r"^# TIER\b")

# APPARENT ITEM STARTS — the integrity probe, NOT the grammar (clause 6).
# A line that opens with an identifier-shaped token after a real item prefix is
# an apparent queue item. If the grammar above cannot parse it, the run FAILS
# and names the line, because that is exactly how WB.1 and 4.10 disappeared
# while the run exited 0.
#
# ANCHORED TO ACTUAL ITEM PREFIXES ON PURPOSE. A line-leading bold item
# reference is NOT probed: three ordinary prose sentences in this file open that
# way -- '**0.3 arbitrates by ORDER OF ARRIVAL.** It has no notion of who is
# waiting', '**2.12** (divergence between two copies) are the same defect' and
# "**2.25's `BUILT` spelling is left unnormalised on purpose.** Rewriting it to"
# -- and probing that shape would fail the run on a correct file. A bare
# '- 1.5 ...' bullet is not probed either: the convention does not exist in this
# document (0 occurrences) and '- 2.5 GB of data' is ordinary prose.
APPARENT_HEADING_RE = re.compile(r"^#{2,6}\s+(" + ITEM_ID + r")(?=\s|$)")
APPARENT_BULLET_RE = re.compile(r"^- \*\*(" + ITEM_ID + r")(?=[\s*])")

# The separator a titled heading uses between identifier and title. Measured:
# of the 112 '### ' headings only WB.1 writes one ('### WB.1 — CURRENT
# PRIORITY: ...' against a stored title of 'CURRENT PRIORITY: ...'), so
# stripping it changes no other item's title and makes WB.1's round-trip exact.
_TITLE_SEP_RE = re.compile(r"^[—–-]\s+")

# The recognised status vocabulary. A token after '**Need:' that is NOT in here
# stops the run -- see classify_status.
#
# IT MUST COVER EVERY need_status THE COLUMN CAN HOLD (OQ-TRIAGE-002, resolved
# 2026-10-03). The earlier comment here recorded the split as deliberate -- "the
# vocabulary is what the parser can READ, the CHECK is what the column can HOLD"
# -- and that was true when the CHECK listed five values and the projection never
# WROTE a status into an item that had no marker, so the other values could not
# reach the markdown. Both halves of that have changed: the CHECK grew to ten,
# and marker insertion (OQ-TRIAGE-001 option 1) now puts whatever the table holds
# into the projection. A stored status the parser cannot read back is therefore no
# longer a harmless asymmetry -- it is a status that fails the whole recovery run
# (rule 6) and takes the other 131 items down with it. Nothing detected that
# drift, which is why queue_set.py now DERIVES its guard from this set by import.
#
# BUILT IS RECOGNISED BUT STORED AS DONE. It is not one of the CHECK's values;
# storing it literally would need a schema change. It stays readable for
# compatibility with markdown written before the table existed, following the
# RESOLVED -> DONE mapping already in shape 3 below. need_raw preserves the
# literal prose either way.
#
# UNPARSED IS DELIBERATELY ABSENT, and it is the one CHECK value this set does
# not cover. UNPARSED is this parser's own sentinel for "a marker was present and
# unreadable". A rendered '**Need: UNPARSED.**' must keep failing the run rather
# than round-tripping, because reading a recorded parse FAILURE back as a
# successful status is how an unknown status would launder itself into the table.
KNOWN = {
    "OPEN", "UNASSESSED", "DONE", "HALF_DONE",
    "PARTLY", "UNCLEAR", "PRESENT_UNPROVEN", "NEEDS_ERIC", "NO_CHECK_WRITTEN",
    "BUILT",
}
STORE_AS = {"BUILT": "DONE", "RESOLVED": "DONE"}


def _tier_for(item_num, enclosing_tier):
    """tier from the item NUMBER where the number has one (contract rule 2),
    else from document position (ADR-PIPE-009 clause 7).

    'WB.1' has no numeric tier prefix and int('WB') is not a tier. It sits
    BEFORE '# TIER 0' in the file, so there is no enclosing header either and it
    takes 0 — which is what the authority holds. A future prefixed item placed
    under a tier header takes that tier.
    """
    head = item_num.split(".")[0]
    if head.isdigit():
        return int(head)
    return 0 if enclosing_tier is None else enclosing_tier


def parse_items(text):
    """Partition the file into items. Boundaries are the next item start of any
    accepted form, or the next '# TIER' header — whichever comes first."""
    lines = text.split("\n")
    marks = []
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            title = _TITLE_SEP_RE.sub("", m.group(2).strip()).strip()
            marks.append((i, m.group(1), "heading", title))
            continue
        m = BULLET_RE.match(line)
        if m:
            marks.append((i, m.group(1), "bullet", m.group(2).strip()))
            continue
        m = BULLET_TITLED_RE.match(line)
        if m:
            marks.append((i, m.group(1), "bullet", m.group(2).strip()))
            continue
        if TIER_RE.match(line):
            t = TIER_NUM_RE.match(line)
            marks.append((i, None, "tier", int(t.group(1)) if t else None))

    items = []
    enclosing_tier = None
    for k, (i, num, form, title) in enumerate(marks):
        if num is None:
            enclosing_tier = title  # the tier header's own number
            continue
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        items.append({
            "item_num": num,
            "tier": _tier_for(num, enclosing_tier),
            "form": form,
            "title": title,
            "body_md": "\n".join(lines[i:end]),
            "source_line": i + 1,
        })
    return items


def apparent_unparsed_items(text, parsed_lines):
    """Lines that LOOK like a queue item start but no accepted form parsed.

    Returns [(line_number, line)]. ADR-PIPE-009 clause 6: these fail the run.
    parsed_lines is the set of 0-based indices parse_items() already claimed, so
    a line that parsed correctly is never reported.
    """
    found = []
    for i, line in enumerate(text.split("\n")):
        if i in parsed_lines:
            continue
        if APPARENT_HEADING_RE.match(line) or APPARENT_BULLET_RE.match(line):
            found.append((i + 1, line))
    return found


TIER_NUM_RE = re.compile(r"^# TIER\s+([0-9]+)")


def parse_sections(text):
    """Return (preamble, tier_headers) — the non-item content the item parser
    drops. preamble is everything before the first '# TIER' header (the intro
    frame). tier_headers is [(tier_num, content)] where content is the raw
    '# TIER N — ...' header plus whatever precedes the first item of that tier
    (normally one blank line). Same line-slice convention as body_md, so the
    render can concatenate preamble + tier_header + items to reproduce the file.
    """
    lines = text.split("\n")
    marks = []  # (line_idx, kind, tier_or_None)
    for i, line in enumerate(lines):
        # The SAME forms parse_items() accepts, including the titled bullet.
        # If these two disagree about where an item starts, the preamble and
        # tier-header slices silently swallow the item's text -- which is
        # exactly what happened to WB.1: it was not a mark here either, so its
        # whole 21KB body was absorbed into the preamble row and the loss was
        # invisible in the re-rendered markdown.
        if (HEADING_RE.match(line) or BULLET_RE.match(line)
                or BULLET_TITLED_RE.match(line)):
            marks.append((i, "item", None))
        elif TIER_RE.match(line):
            m = TIER_NUM_RE.match(line)
            marks.append((i, "tier", int(m.group(1)) if m else None))

    if not marks:
        return text, []

    first_mark = marks[0][0]
    preamble = "\n".join(lines[:first_mark])

    tier_headers = []
    for k, (i, kind, tier) in enumerate(marks):
        if kind != "tier":
            continue
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        tier_headers.append((tier, "\n".join(lines[i:end]), i + 1))
    return preamble, tier_headers


# The vocabulary indexed BY ITS RENDERED SPELLING, which is what this parser
# actually receives. render_build_list.py writes '**Need: <status>.**' with
# underscores canonicalised to spaces, so NO_CHECK_WRITTEN arrives as three
# words, PRESENT_UNPROVEN as two, and DONE as one.
#
# THIS IS WHY OQ-TRIAGE-002 COULD NOT BE FIXED BY ADDING STRINGS TO `KNOWN`.
# _normalise() used to join at most the first TWO words, so 'NO CHECK WRITTEN'
# normalised to 'NO' no matter what `KNOWN` contained -- the three-word status was
# unreachable by construction. The word count is now derived from the vocabulary
# instead of hardcoded, so a status of any length survives the round trip and
# adding one later needs no change here.
#
# Keyed on the space form with both spellings folded into it, so a hand-written
# underscore form ('**Need: NO_CHECK_WRITTEN.**') reads identically to the
# generated one -- recovery runs against files humans have edited.
_RENDERED = {tok.replace("_", " "): tok for tok in set(KNOWN) | set(STORE_AS)}
_MAX_STATUS_WORDS = max(len(k.split()) for k in _RENDERED)


def _normalise(raw):
    """'HALF DONE 2026-09-04.' -> HALF_DONE;  'NO CHECK WRITTEN.' ->
    NO_CHECK_WRITTEN;  'BUILT 2026-09-09,' -> BUILT.

    LONGEST VOCABULARY MATCH FIRST, then fall back to the first word. The
    fallback is what preserves unknown-token detection: 'TOTALLY UNKNOWN STATUS'
    matches no entry at any length, so it returns 'TOTALLY', which is not in
    KNOWN, and classify_status() calls it UNPARSED. Widening the vocabulary
    cannot widen what this accepts -- only an entry in `KNOWN` can.
    """
    words = [w.strip(":.,;)—") for w in raw.split() if w.strip(":.,;)—")]
    if not words:
        return None
    upper = [w.upper() for w in words]
    for n in range(min(_MAX_STATUS_WORDS, len(upper)), 0, -1):
        candidate = " ".join(upper[:n]).replace("_", " ")
        if candidate in _RENDERED:
            return _RENDERED[candidate]
    return upper[0]


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


# ── scope (ADR-PIPE-009 clauses 2-4) ────────────────────────────────────────
# THE MACHINE-OWNED MARKER. render_build_list.py writes exactly one of these per
# item with a non-NULL scope and this is the ONLY thing that creates
# queue_items.scope. Exact, anchored, case-sensitive.
#
# WHY PROSE WAS DISQUALIFIED ENTIRELY RATHER THAN PARSED MORE CAREFULLY. The old
# reader was `\*\*Scope:?\*\*[:\s]*([^\n]+)` with a `\*\*Scope[^*]*\*\*` fallback,
# and on 2026-10-04 it returned a WRONG scope for 9 of 132 production rows. Six
# of those rows hold authoritative NULL and got a FABRICATED value, because
# '**Scope:**' in this document is also an ordinary prose paragraph label and the
# end-of-line capture turned an arbitrary line-wrap boundary into a
# classification: 4.29 through 4.32 recovered as 'Full spec:', 4.28 as 'An
# independent reviewer (Codex, matching the WB.1B-2A/2B/3', 4.20 as 'CONTAINED
# PIPELINE — everything below is about the in-container'. Since the read models
# compute partially_classified and fully_classified from `scope IS NOT NULL`,
# that manufactures false triage completion on honestly-unclassified rows.
#
# AND IT COULD NOT BE FIXED BY TIGHTENING THE HEURISTIC. 12 items hold a
# LEGITIMATE non-NULL scope in a '**Scope:**' paragraph that wraps across lines,
# structurally identical to the 6 that must stay NULL. There is no syntactic
# property separating them -- only the human judgement already recorded in the
# scope column. So the classification moved to a marker the generator owns and
# prose became prose, exactly as '**Need:' already works for need_status.
#
# JSON IS THE ENCODING because it has to carry what the column can already hold:
# one legacy value (item 1.20) contains an embedded NEWLINE and one contains a
# double quote. The renderer additionally escapes '>' as > so a value can
# never close the comment early with '-->'. Neither value is normalised --
# ADR-PIPE-009 clause 9 forbids cleaning legacy scope to obtain a passing proof.
SCOPE_MARKER_PROBE = re.compile(r"^<!--\s*cis:scope=", re.M)
SCOPE_MARKER_RE = re.compile(r'^<!-- cis:scope=("(?:[^"\\]|\\.)*") -->$', re.M)


def extract_scope(body):
    """Return (scope, error). error is a string when the marker is PRESENT but
    unreadable, which fails the whole run before any mutation.

    NO MARKER -> (None, None). The item states no scope. Normal and expected --
    63 of 132 production rows are like this -- and it does NOT fail the run.
    This is the same absence-is-allowed rule classify_status() applies.
    """
    present = SCOPE_MARKER_PROBE.findall(body)
    if not present:
        return None, None
    if len(present) > 1:
        return None, ("%d cis:scope markers in one item — scope ambiguous"
                      % len(present))
    m = SCOPE_MARKER_RE.search(body)
    if not m:
        line = next((l for l in body.split("\n")
                     if SCOPE_MARKER_PROBE.match(l)), "")
        return None, "malformed cis:scope marker: %r" % line[:200]
    try:
        value = json.loads(m.group(1))
    except ValueError as e:
        return None, "cis:scope value is not valid JSON (%s): %r" % (e, m.group(1)[:160])
    if not isinstance(value, str):
        return None, ("cis:scope decoded to %s, not a string: %r"
                      % (type(value).__name__, m.group(1)[:160]))
    if not value.strip():
        return None, "cis:scope decoded to an empty value: %r" % m.group(1)[:160]
    return value, None


def main():
    # STEP 3A — the extractor is locked. After the flip the table is the
    # authority and the markdown is generated FROM it; re-extracting would
    # overwrite authority (status_changed_at + queue_item_events) with a copy.
    if "--force" not in sys.argv:
        print("LOCKED — the queue is no longer extracted from the markdown.")
        print("")
        print("queue_items (the spine) is the authority. The markdown")
        print("docs/UNIFIED_BUILD_LIST.md is GENERATED from the table by")
        print("tools/queue/render_build_list.py. Re-extracting here would")
        print("overwrite the authority — and any status_changed_at /")
        print("queue_item_events history — with a copy of the generated file.")
        print("")
        print("Run with --force only to rebuild the table from a hand-edited")
        print("markdown during recovery, then re-render the markdown.")
        return 1

    text = open(SRC, encoding="utf-8").read()
    # Strip leading DO-NOT-EDIT banner comment lines. A --force recovery from a
    # file the render already wrote would otherwise ingest the banner into the
    # preamble (and then the render would add it a second time on top).
    while text.startswith("<!--"):
        nl = text.find("\n")
        text = text[nl + 1:] if nl != -1 else ""
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    items = parse_items(text)
    preamble, tier_headers = parse_sections(text)

    rows, unparsed, scope_errors = [], [], []
    for it in items:
        status, raw = classify_status(it["body_md"])
        if status == "UNPARSED":
            unparsed.append((it["item_num"], raw))
        if status is not None and status not in KNOWN and status != "UNPARSED":
            unparsed.append((it["item_num"], raw))
            status = "UNPARSED"
        scope, scope_err = extract_scope(it["body_md"])
        if scope_err:
            scope_errors.append((it["item_num"], it["source_line"], scope_err))
        rows.append((
            it["item_num"],
            it["tier"],
            it["title"] or it["item_num"],
            it["body_md"],
            it["form"],
            scope,
            status,
            raw,
            it["source_line"],
            sha,
        ))

    # ── structural integrity, ADR-PIPE-009 clause 6 ──────────────────────────
    apparent = apparent_unparsed_items(text, {it["source_line"] - 1 for it in items})
    seen, duplicates = {}, []
    for it in items:
        if it["item_num"] in seen:
            duplicates.append((it["item_num"], seen[it["item_num"]], it["source_line"]))
        else:
            seen[it["item_num"]] = it["source_line"]

    print("source            : %s" % SRC)
    print("source_sha        : %s" % sha)
    print("items parsed      : %d" % len(rows))
    print("tier headers      : %d" % len(tier_headers))
    print("UNPARSED          : %d" % len(unparsed))
    print("scope markers     : %d" % sum(1 for r in rows if r[5] is not None))
    print("apparent unparsed : %d" % len(apparent))
    print("duplicate ids     : %d" % len(duplicates))
    print("scope errors      : %d" % len(scope_errors))

    # EVERY FAILURE BELOW IS CHECKED BEFORE sqlite3.connect(). A failed recovery
    # must mutate ZERO rows in the target, so the gate cannot sit after the
    # DELETE -- see the test that runs each of these against a target database
    # that ALREADY contains rows and asserts it comes back byte-identical.
    failed = False

    # RULE 6 — unknown or ambiguous status.
    if unparsed:
        failed = True
        print("\nSTATUS PROSE PRESENT BUT UNRECOGNISED — nothing imported:")
        for num, raw in unparsed:
            print("  %-6s %r" % (num, raw))
        print("\nAn unknown TOKEN means adding the spelling to classify_status().")
        print("Two MARKERS in one item means the item states its status twice —")
        print("remove one.")

    # CLAUSE 6 — an item-shaped line no accepted form could parse. This is the
    # check whose absence lost WB.1 and 4.10 while the run exited 0.
    if apparent:
        failed = True
        print("\nAPPARENT QUEUE ITEM THE PARSER CANNOT READ — nothing imported:")
        for ln, line in apparent:
            print("  line %-6d %r" % (ln, line[:160]))
        print("\nThis line opens with an item identifier after a real item prefix")
        print("but matches no accepted form. Either it IS an item and the form")
        print("belongs in the grammar, or the identifier is wrong. It is NOT")
        print("skipped: an item that disappears quietly is the defect ADR-PIPE-009")
        print("exists to prevent.")

    # CLAUSE 6 — two projected items with one identity. item_num is the primary
    # key, so importing these would collapse them into a single row (or abort
    # mid-transaction); neither is an honest outcome.
    if duplicates:
        failed = True
        print("\nDUPLICATE ITEM IDENTITY — nothing imported:")
        for num, first, second in duplicates:
            print("  %-8s first at line %d, again at line %d" % (num, first, second))
        print("\nTwo items cannot share one identifier: the table would keep one")
        print("and lose the other. Renumber one of them.")

    # CLAUSES 2 AND 5 — scope marker present but unreadable. Absence is fine;
    # this is the other half of the rule.
    if scope_errors:
        failed = True
        print("\nSCOPE CLASSIFICATION PRESENT BUT UNREADABLE — nothing imported:")
        for num, ln, err in scope_errors:
            print("  %-8s line %-6d %s" % (num, ln, err))
        print("\nA cis:scope marker states a classification. An unreadable one is")
        print("not the same as no marker at all, so it fails here instead of")
        print("silently recovering as NULL and losing the classification.")

    if failed:
        print("\nNOTHING WAS IMPORTED; the target table is unchanged.")
        return 1

    conn = sqlite3.connect(DB)
    try:
        conn.execute("DELETE FROM queue_items")
        conn.executemany(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
            "scope, need_status, need_raw, source_line, source_sha) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        # non-item structure: preamble (seq 0) + tier headers (seq tier+1)
        conn.execute("DELETE FROM queue_sections")
        section_rows = [(0, "preamble", preamble, None, 1, sha)]
        section_rows += [(tier + 1, "tier_header", content, tier, src_line, sha)
                         for tier, content, src_line in tier_headers]
        conn.executemany(
            "INSERT INTO queue_sections (seq, kind, content, tier, source_line, source_sha) "
            "VALUES (?,?,?,?,?,?)", section_rows)
        conn.commit()
    finally:
        conn.close()

    print("\nwrote %d rows to queue_items, %d sections" % (len(rows), len(section_rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
