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
   expected outcome — today 56 of 119 items — and it does NOT fail the run.
5. UNPARSED means something narrower: status prose is PRESENT but its value is
   not in the known vocabulary. The literal text is kept in need_raw.
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
import re
import sqlite3
import sys

DB = "/mnt/projects/cis/data/cis_memory.db"
SRC = "/mnt/projects/cis/docs/UNIFIED_BUILD_LIST.md"

HEADING_RE = re.compile(r"^### ([0-9]+\.[0-9]+)\s*(.*)$")
BULLET_RE = re.compile(r"^- \*\*([0-9]+\.[0-9]+)\*\*\s*(.*)$")
TIER_RE = re.compile(r"^# TIER\b")

KNOWN = {"OPEN", "UNASSESSED", "DONE", "HALF_DONE"}


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


def classify_status(body):
    """Return (need_status, need_raw). See rules 3-5 in the module docstring."""
    m = re.search(r"\*\*Need:\*\*\s*([A-Za-z_ ]+)", body)
    if m:
        raw = m.group(1).strip()
        value = raw.split("—")[0].strip().upper().replace(" ", "_")
        for token in ("HALF_DONE", "UNASSESSED", "OPEN", "DONE"):
            if value.startswith(token):
                return token, raw
        return "UNPARSED", raw

    m = re.search(r"\*\*Need:\s*(HALF DONE|DONE|OPEN|UNASSESSED)\b", body)
    if m:
        return m.group(1).replace(" ", "_"), m.group(0)

    m = re.search(r"\*\*(DONE|HALF DONE|RESOLVED)\b[^*]*\*\*", body)
    if m:
        token = m.group(1).replace(" ", "_")
        return ("DONE" if token == "RESOLVED" else token), m.group(0)[:200]

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
        print("\nAdd the spelling to classify_status(), then re-run.")
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
