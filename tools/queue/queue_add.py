#!/usr/bin/env python3
"""queue_add.py — the sole sanctioned CREATE path for queue_items (CARD 5).

BUILD LIST queue-authority-and-audit. queue_set.py is the sole write path
for an EXISTING item's status; this is the sole write path for a NEW
item's existence. Both share the same principle: a write goes through a
tool, never raw SQL, so every change carries an audit trail
(queue_item_events) — no mark on a belief.

item_num is caller-supplied, not auto-generated: this repo's numbering
(tier.subitem) carries meaning only a human/reviewing model should assign,
matching queue_set.py's own precedent of taking its target explicitly
rather than inferring one.

CREATE-only, never UPDATE: an item_num that already exists is refused
outright (exit 2, nothing written) — changing an existing item's status
goes through queue_set.py, changing its body goes through whatever
mechanism the current WB.1 body edit used (documented, ad hoc, and exactly
the gap this tool exists to eventually replace for creation; this tool
does not attempt to also become the body-edit path, which is a separate,
narrower problem).

Placement: render_build_list.py orders the rendered markdown purely by
source_line. A new item's source_line is chosen as
max(existing item/section source_line) + 10, so it sorts after everything
currently in the table. Disclosed, pre-existing rendering quirk (not
introduced or fixed by this tool): the file's own trailing
"REFERENCE DOCUMENTS"/"Recorded, not queued"/"HOW TO WORK THIS LIST"/
"COVERAGE" sections never matched the original extractor's
HEADING_RE/BULLET_RE/TIER_RE patterns, so they became physically glued
onto the LAST item's (4.19's) own body_md at extraction time. Any new item
necessarily renders textually AFTER that entire glued blob — a markdown
rendering-order cosmetic, not a defect in the table (the actual
authority), and not something this card's scope calls for fixing.

Usage:
    python3 tools/queue/queue_add.py <item_num> --tier N --title T \
        --body-file PATH --form {heading|bullet} [--need-status S] \
        --actor A --evidence "why this is being created" [--dry-run]

Env: CIS_SPINE_PATH overrides the default production path (same convention
as queue_set.py/render_build_list.py — no separate --db flag, so tests use
CIS_SPINE_PATH pointed at a scratch database, never a CLI flag that could
be forgotten).
"""
import argparse
import datetime
import os
import sqlite3
import sys

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")

VALID_FORMS = {"heading", "bullet"}
VALID_NEED_STATUS = {
    "OPEN", "UNASSESSED", "HALF_DONE", "DONE", "UNPARSED",
    "PARTLY", "UNCLEAR", "PRESENT_UNPROVEN", "NEEDS_ERIC", "NO_CHECK_WRITTEN",
}
SOURCE_SHA_SENTINEL = "queue_add-created"  # NOT a real file hash — labeled so
# nobody mistakes it for a genuine markdown-extraction sha256; this item did
# not originate from re-extracting the file (extraction is locked, see
# extract_queue_items.py), it was created directly through this tool.


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("item_num")
    ap.add_argument("--tier", required=True, type=int)
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", required=True,
                     help="file containing the item's full body_md, starting with its own "
                          "'### N.M Title' or '- **N.M** ...' line")
    ap.add_argument("--form", required=True, choices=sorted(VALID_FORMS))
    ap.add_argument("--need-status", default=None, choices=sorted(VALID_NEED_STATUS))
    ap.add_argument("--actor", required=True)
    ap.add_argument("--evidence", required=True,
                     help="why this item is being created — required, becomes the "
                          "creation event's audit evidence")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    if not a.evidence.strip():
        print("refusing: --evidence must not be empty — no creation without the "
              "reasoning that justified it")
        return 2
    if not a.title.strip():
        print("refusing: --title must not be empty")
        return 2
    if not a.item_num.strip():
        print("refusing: item_num must not be empty")
        return 2
    if not os.path.isfile(a.body_file):
        print(f"refusing: --body-file {a.body_file!r} not found")
        return 2
    body_md = open(a.body_file, encoding="utf-8").read()
    if not body_md.strip():
        print("refusing: body is empty")
        return 2

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    existing = conn.execute(
        "SELECT item_num FROM queue_items WHERE item_num=?", (a.item_num,)
    ).fetchone()
    if existing is not None:
        print(f"refusing: item_num {a.item_num!r} already exists — queue_add.py never "
              f"overwrites; use queue_set.py to change an existing item's status")
        conn.close()
        return 2

    max_item_line = conn.execute(
        "SELECT COALESCE(MAX(source_line), 0) FROM queue_items"
    ).fetchone()[0]
    max_section_line = conn.execute(
        "SELECT COALESCE(MAX(source_line), 0) FROM queue_sections"
    ).fetchone()[0]
    source_line = max(max_item_line, max_section_line) + 10

    if a.dry_run:
        print(f"DRY RUN — would create item_num={a.item_num!r} tier={a.tier} "
              f"form={a.form!r} need_status={a.need_status!r} source_line={source_line}")
        print(f"DRY RUN — would record queue_item_events(item_num={a.item_num!r}, "
              f"field='created', changed_by={a.actor!r}, evidence={a.evidence!r})")
        print("DRY RUN — nothing written")
        conn.close()
        return 0

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "INSERT INTO queue_items (item_num, tier, title, body_md, form, need_status, "
            "source_line, source_sha, extracted_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (a.item_num, a.tier, a.title, body_md, a.form, a.need_status,
             source_line, SOURCE_SHA_SENTINEL, now),
        )
        conn.execute(
            "INSERT INTO queue_item_events (item_num, field, old_value, new_value, "
            "changed_at, changed_by, evidence, note) VALUES (?,?,?,?,?,?,?,?)",
            (a.item_num, "created", None, a.item_num, now, a.actor, a.evidence,
             f"created via queue_add.py, tier={a.tier}, form={a.form}"),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"refusing: {e}")
        conn.close()
        return 2
    except Exception:
        conn.rollback()
        conn.close()
        raise

    conn.close()
    print(f"created {a.item_num!r} at source_line={source_line} "
          f"(run tools/queue/render_build_list.py to regenerate the markdown)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
