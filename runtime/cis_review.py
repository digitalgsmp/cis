#!/usr/bin/env python3
"""
cis_review.py — CIS Human Review Interface
Phase 1 tool: reviews draft knowledge records, applies logged corrections,
promotes status from draft → checked.

Usage:
    python3 /mnt/projects/cis/runtime/cis_review.py <source_id>

Example:
    python3 /mnt/projects/cis/runtime/cis_review.py IMAGE__WEIRD_WAR_TALES_COVER__001

Contract:
    Input:   source_id (e.g. IMAGE__WEIRD_WAR_TALES_COVER__001)
    Output:  updated record JSON + updated manifest
    DB:      reads corrections table, writes to session_log
    Status:  record draft → checked, manifest draft → checked
"""

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECTS_ROOT = Path("/mnt/projects/cis")
RECORDS_ROOT  = PROJECTS_ROOT / "knowledge" / "records"
INGEST_ROOT   = PROJECTS_ROOT / "ingest" / "processing"
DB_PATH       = PROJECTS_ROOT / "memory" / "cis_memory.db"

# ── Helpers ────────────────────────────────────────────────────────────────────

def ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def separator(char="─", width=68):
    print(char * width)

def header(text: str):
    separator("═")
    print(f"  {text}")
    separator("═")

def section(text: str):
    separator()
    print(f"  {text}")
    separator()

def find_record_dir(source_id: str) -> Path:
    """
    Locate the record family folder for a source_id.
    Tries exact match first, then case-insensitive.
    """
    record_dir = RECORDS_ROOT / source_id
    if record_dir.exists():
        return record_dir
    for d in RECORDS_ROOT.iterdir():
        if d.name.upper() == source_id.upper():
            return d
    raise FileNotFoundError(
        f"No record folder found for source_id: {source_id}\n"
        f"Looked in: {RECORDS_ROOT}\n"
        f"Available: {[d.name for d in RECORDS_ROOT.iterdir() if d.is_dir()]}"
    )

def find_manifest(source_id: str) -> Path:
    """
    Locate the source manifest for a source_id.
    Manifest lives at: ingest/processing/<lowercase_source_id>/manifest.json
    """
    # Try lowercase first (actual convention on disk)
    for candidate_name in [source_id.lower(), source_id]:
        candidate = INGEST_ROOT / candidate_name / "manifest.json"
        if candidate.exists():
            return candidate
    # Case-insensitive search
    for d in INGEST_ROOT.iterdir():
        if d.name.lower() == source_id.lower():
            candidate = d / "manifest.json"
            if candidate.exists():
                return candidate
    raise FileNotFoundError(
        f"No manifest found for source_id: {source_id}\n"
        f"Looked in: {INGEST_ROOT}\n"
        f"Available: {[d.name for d in INGEST_ROOT.iterdir() if d.is_dir()]}"
    )

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def find_draft_records(record_dir: Path) -> list:
    """Return all record JSON files with status=draft."""
    drafts = []
    for p in sorted(record_dir.glob("*.json")):
        try:
            data = load_json(p)
            if data.get("status") == "draft":
                drafts.append(p)
        except Exception:
            pass
    return drafts

def get_corrections(db_path: Path, record_id: str) -> list:
    """Fetch all corrections logged for a record_id."""
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT field_name, original_value, corrected_value, correction_type, created_at
            FROM corrections
            WHERE record_id = ?
            ORDER BY created_at ASC
            """,
            (record_id,)
        )
        rows = [dict(r) for r in cur.fetchall()]
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return rows

def log_session(db_path: Path, source_id: str, record_id: str,
                corrections_applied: int, status: str):
    """Write a session_log entry for this review."""
    if not db_path.exists():
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO session_log (session_date, focus, completed, next_steps, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ts()[:10],
                f"review: {source_id}",
                f"Record {record_id} reviewed. {corrections_applied} correction(s) applied. Status → {status}.",
                "Run cis_review.py on next draft record or promote to approved.",
                f"Reviewed via cis_review.py at {ts()}",
                ts()
            )
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"  [warn] Could not write session_log: {e}")
    conn.close()

def update_markdown_mirror(record_dir: Path, record: dict):
    """Regenerate the markdown mirror from the updated record JSON."""
    record_id = record.get("record_id", "unknown")
    md_path = record_dir / f"{record_id}.md"

    lines = [
        f"# {record.get('title', record_id)}",
        "",
        f"**Record ID:** {record_id}",
        f"**Status:** {record.get('status', '')}",
        f"**Updated:** {record.get('updated_at', '')}",
        "",
        "## Summary",
        "",
        record.get("summary", "_No summary._"),
        "",
    ]

    if record.get("visible_text"):
        lines += ["## Visible Text", "", record["visible_text"], ""]
    if record.get("scene_description"):
        lines += ["## Scene Description", "", record["scene_description"], ""]
    if record.get("mood_style"):
        lines += ["## Style / Mood", "", record["mood_style"], ""]
    if record.get("tags"):
        tags = record["tags"]
        if isinstance(tags, list):
            tags = ", ".join(tags)
        lines += ["## Tags", "", tags, ""]
    if record.get("confidence_notes"):
        lines += ["## Confidence Notes", "", record["confidence_notes"], ""]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  ✓ Markdown mirror updated: {md_path.name}")

# ── Display ────────────────────────────────────────────────────────────────────

def display_record_summary(record: dict):
    """Print the key reviewable fields of a record."""
    fields = [
        ("title",             "Title"),
        ("summary",           "Summary"),
        ("visible_text",      "Visible Text"),
        ("scene_description", "Scene Description"),
        ("layout_description","Layout Description"),
        ("style_mood_tags",   "Style/Mood Tags"),
        ("functional_tags",   "Functional Tags"),
        ("confidence_notes",  "Confidence Notes"),
        ("knowledge_category","Category"),
        ("topics",            "Topics"),
    ]
    for key, label in fields:
        val = record.get(key)
        if val:
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            print(f"\n  [{label}]")
            for line in str(val).splitlines():
                print(f"    {line}")

def display_corrections(corrections: list):
    """Print all logged corrections for the record."""
    if not corrections:
        print("\n  No corrections logged for this record.")
        return
    print(f"\n  {len(corrections)} correction(s) logged:\n")
    for i, c in enumerate(corrections, 1):
        print(f"  [{i}] Field:     {c['field_name']}")
        print(f"       Type:      {c['correction_type']}")
        print(f"       Original:  {c['original_value']}")
        print(f"       Corrected: {c['corrected_value']}")
        print(f"       Logged:    {c['created_at']}")
        print()

# ── Review loop ────────────────────────────────────────────────────────────────

def review_corrections(record: dict, corrections: list) -> tuple:
    """
    Walk the human through each correction.
    Returns (updated_record, corrections_applied_count).
    """
    applied = 0
    section(f"CORRECTIONS — {len(corrections)} to review")

    for i, c in enumerate(corrections, 1):
        field     = c["field_name"]
        original  = c["original_value"]
        corrected = c["corrected_value"]
        ctype     = c["correction_type"]

        print(f"\n  Correction {i} of {len(corrections)}")
        print(f"  Field:     {field}")
        print(f"  Type:      {ctype}")
        print(f"  Original:  {original}")
        print(f"  Corrected: {corrected}")
        print()

        while True:
            choice = input("  Apply this correction? [y]es / [n]o / [e]dit value: ").strip().lower()
            if choice in ("y", "yes"):
                record[field] = corrected
                record["updated_at"] = ts()
                applied += 1
                print("  ✓ Applied.")
                break
            elif choice in ("n", "no"):
                print("  ✗ Skipped.")
                break
            elif choice in ("e", "edit"):
                new_val = input(f"  Enter new value for [{field}]: ").strip()
                if new_val:
                    record[field] = new_val
                    record["updated_at"] = ts()
                    applied += 1
                    print("  ✓ Applied with edited value.")
                else:
                    print("  No value entered. Skipped.")
                break
            else:
                print("  Enter y, n, or e.")

    return record, applied

def freeform_edit(record: dict) -> dict:
    """Allow the reviewer to directly edit any field by name."""
    section("FREEFORM EDIT (optional)")
    print("  Edit any field directly. Enter field name or press Enter to skip.\n")

    while True:
        field = input("  Field name (or Enter to finish): ").strip()
        if not field:
            break
        if field not in record:
            print(f"  Field '{field}' not in record. Available fields:")
            print("  " + ", ".join(record.keys()))
            continue
        current = record[field]
        print(f"  Current value: {current}")
        new_val = input("  New value (Enter to keep): ").strip()
        if new_val:
            record[field] = new_val
            record["updated_at"] = ts()
            print("  ✓ Updated.")

    return record

def final_decision(record: dict) -> str:
    """Ask reviewer to approve or reject the record. Returns 'checked' or 'rejected'."""
    section("FINAL DECISION")
    print(f"  Record: {record.get('record_id')}")
    print(f"  Title:  {record.get('title')}")
    print()
    while True:
        choice = input("  Decision — [a]pprove (→ checked) / [r]eject (→ rejected): ").strip().lower()
        if choice in ("a", "approve"):
            return "checked"
        elif choice in ("r", "reject"):
            return "rejected"
        else:
            print("  Enter a or r.")

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cis_review.py <source_id>")
        print("Example: python3 cis_review.py IMAGE__WEIRD_WAR_TALES_COVER__001")
        sys.exit(1)

    source_id = sys.argv[1].strip()

    header(f"CIS REVIEW — {source_id}")
    print(f"  Started: {ts()}\n")

    # ── Locate files ──────────────────────────────────────────────────────────
    try:
        record_dir    = find_record_dir(source_id)
        manifest_path = find_manifest(source_id)
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)

    print(f"  Record dir:  {record_dir}")
    print(f"  Manifest:    {manifest_path}\n")

    draft_records = find_draft_records(record_dir)
    if not draft_records:
        print(f"  No draft records found in {record_dir}")
        print("  Nothing to review.")
        sys.exit(0)

    print(f"  Found {len(draft_records)} draft record(s) to review.\n")

    total_corrections_applied = 0

    for record_path in draft_records:
        record    = load_json(record_path)
        record_id = record.get("record_id", record_path.stem)

        section(f"RECORD — {record_id}")
        print(f"  File: {record_path}\n")

        # Display record fields
        display_record_summary(record)

        # Load and display corrections
        corrections = get_corrections(DB_PATH, record_id)
        section("LOGGED CORRECTIONS")
        display_corrections(corrections)

        # Review corrections
        if corrections:
            record, n_applied = review_corrections(record, corrections)
            total_corrections_applied += n_applied
        else:
            n_applied = 0

        # Freeform edits
        do_edit = input("\n  Open freeform edit? [y/N]: ").strip().lower()
        if do_edit in ("y", "yes"):
            record = freeform_edit(record)

        # Final decision
        new_status = final_decision(record)
        record["status"] = new_status
        record["updated_at"] = ts()

        # Save record
        save_json(record_path, record)
        print(f"\n  ✓ Record saved: {record_path.name}")

        # Update markdown mirror
        update_markdown_mirror(record_dir, record)

        # Update manifest
        manifest = load_json(manifest_path)
        manifest["status"] = new_status
        manifest.setdefault("history", []).append({
            "timestamp":           ts(),
            "event":               "review_complete",
            "status":              new_status,
            "corrections_applied": n_applied,
            "reviewed_by":         "human"
        })
        save_json(manifest_path, manifest)
        print(f"  ✓ Manifest updated: status → {new_status}")

        # Log session
        log_session(DB_PATH, source_id, record_id, n_applied, new_status)
        print(f"  ✓ Session logged to database.\n")

    # ── Summary ───────────────────────────────────────────────────────────────
    header("REVIEW COMPLETE")
    print(f"  Source:              {source_id}")
    print(f"  Records reviewed:    {len(draft_records)}")
    print(f"  Corrections applied: {total_corrections_applied}")
    print(f"  Finished:            {ts()}")
    separator("═")
    print()

if __name__ == "__main__":
    main()
