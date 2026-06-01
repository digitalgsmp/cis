#!/usr/bin/env python3
"""
cis_convert_export.py
Converts Anthropic data export JSON to clean .md files.

Usage:
    python3 cis_convert_export.py --input /path/to/conversations.json \
                                  --output /mnt/projects/cis/docs/claude_chat_transcripts/

One .md file is produced per conversation.
Files are named: YYYY-MM-DD_conversation-title.md
Verification is run after each file write — no silent failures.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ── Forbidden strings check (from ADR-033 verification contract) ──────────────
FORBIDDEN_STRINGS = ["TODO", "[placeholder]", "[coming soon]", "[to be completed]",
                     "[fill in]", "[insert]", "PLACEHOLDER", "TBD"]

# ── Sender labels ─────────────────────────────────────────────────────────────
SENDER_LABEL = {
    "human": "## Human",
    "assistant": "## Claude",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def safe_filename(name: str, date: str) -> str:
    """Produce a clean filename from conversation title and date."""
    clean = name.strip().replace("/", "-").replace("\\", "-")
    clean = "".join(c if c.isalnum() or c in " -_" else "" for c in clean)
    clean = clean[:60].strip()
    return f"{date}_{clean}.md"


def format_timestamp(ts: str) -> str:
    """Convert ISO timestamp to readable UTC string."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return ts


def extract_date(ts: str) -> str:
    """Extract YYYY-MM-DD from ISO timestamp."""
    try:
        return ts[:10]
    except Exception:
        return "0000-00-00"


def build_markdown(convo: dict) -> str:
    """Convert a single conversation dict to markdown string."""
    title = convo.get("name") or "Untitled Conversation"
    created = format_timestamp(convo.get("created_at", ""))
    updated = format_timestamp(convo.get("updated_at", ""))
    uuid = convo.get("uuid", "")

    lines = [
        f"# {title}",
        f"",
        f"- **Created:** {created}",
        f"- **Updated:** {updated}",
        f"- **UUID:** {uuid}",
        f"",
        "---",
        "",
    ]

    messages = convo.get("chat_messages", [])

    # Sort by created_at to ensure correct order
    try:
        messages = sorted(messages, key=lambda m: m.get("created_at", ""))
    except Exception:
        pass

    for msg in messages:
        sender = msg.get("sender", "unknown")
        label = SENDER_LABEL.get(sender, f"## {sender.title()}")
        msg_time = format_timestamp(msg.get("created_at", ""))
        text = msg.get("text", "").strip()

        # Skip empty messages
        if not text:
            continue

        # Note any file attachments
        files = msg.get("files", [])
        file_notes = ""
        if files:
            names = [f.get("file_name", "unknown") for f in files]
            file_notes = f"\n*Attachments: {', '.join(names)}*\n"

        lines.append(f"{label} — {msg_time}")
        if file_notes:
            lines.append(file_notes)
        lines.append("")
        lines.append(text)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def verify_file(path: Path, min_bytes: int = 100) -> list[str]:
    """
    Layer 1 verification — deterministic checks.
    Returns list of failure strings. Empty list = PASS.
    """
    failures = []

    if not path.exists():
        failures.append(f"FAIL  File does not exist: {path}")
        return failures

    size = path.stat().st_size
    if size == 0:
        failures.append(f"FAIL  File is empty: {path}")
        return failures

    if size < min_bytes:
        failures.append(f"FAIL  File too small ({size} bytes, expected >{min_bytes}): {path}")

    content = path.read_text(encoding="utf-8")

    if "## Human" not in content and "## Claude" not in content:
        failures.append(f"FAIL  No message content found in: {path}")

    for forbidden in FORBIDDEN_STRINGS:
        if forbidden in content:
            failures.append(f"FAIL  Forbidden string '{forbidden}' found in: {path}")

    return failures


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Convert Anthropic JSON export to .md files")
    parser.add_argument("--input", required=True,
                        help="Path to Anthropic export JSON file (conversations.json)")
    parser.add_argument("--output", required=True,
                        help="Output directory for .md files")
    parser.add_argument("--filter-after", default=None,
                        help="Only convert conversations created after this date (YYYY-MM-DD)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading: {input_path}")
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    # Handle both list and dict with 'conversations' key
    if isinstance(data, list):
        conversations = data
    elif isinstance(data, dict) and "conversations" in data:
        conversations = data["conversations"]
    else:
        # Single conversation
        conversations = [data]

    print(f"Found {len(conversations)} conversations")

    # Optional date filter
    filter_date = args.filter_after  # e.g. "2026-03-01"

    passed = 0
    failed = 0
    skipped = 0
    failures_summary = []

    for convo in conversations:
        created = convo.get("created_at", "")
        date_str = extract_date(created)

        # Apply date filter
        if filter_date and date_str < filter_date:
            skipped += 1
            continue

        title = convo.get("name") or "Untitled"
        filename = safe_filename(title, date_str)
        out_path = output_dir / filename

        # Build markdown
        md_content = build_markdown(convo)

        # Write file
        out_path.write_text(md_content, encoding="utf-8")

        # Verify immediately after write
        failures = verify_file(out_path)

        if failures:
            print(f"  FAIL  {filename}")
            for f in failures:
                print(f"        {f}")
            failures_summary.extend(failures)
            failed += 1
        else:
            print(f"  PASS  {filename}")
            passed += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("CONVERSION COMPLETE")
    print(f"  Converted:  {passed}")
    print(f"  Failed:     {failed}")
    print(f"  Skipped:    {skipped} (before filter date)")
    print(f"  Output dir: {output_dir}")
    print()

    if failures_summary:
        print("VERIFICATION FAILURES — resolve before proceeding:")
        for f in failures_summary:
            print(f"  {f}")
        print()
        print("Result: CHAIN FAIL — do not run batch extraction until resolved")
        sys.exit(1)
    else:
        print("Result: CHAIN PASS — all files verified")
        print()
        print("Next step: run cis_batch_extract.py against these .md files")


if __name__ == "__main__":
    main()
