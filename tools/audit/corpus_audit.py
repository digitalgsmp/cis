#!/usr/bin/env python3
"""
corpus_audit.py — Tier 7.5a Corpus Audit / Format Discovery
Read-only scan of Eric's archive directories.
Reports 15 findings to docs/audits/corpus_audit_YYYYMMDD.md.
No database changes. No import. No file modification.
"""

import json
import hashlib
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "docs" / "audits"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# Directories to scan
SCAN_DIRS = [
    Path.home() / ".hermes" / "sessions",
    Path.home() / ".hermes-v4impl" / "sessions",
    Path.home() / ".hermes-r1" / "sessions",
    Path.home() / ".hermes-v4pro" / "sessions",
    REPO_ROOT / "docs" / "claude_chat_transcripts",
]


def sha256_file(path):
    """SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_filename_date(name):
    """Try to extract a date from a filename like session_20260525_232304_b2d3b2.json."""
    stem = Path(name).stem
    parts = stem.split("_")
    for part in parts:
        if len(part) == 8 and part.isdigit():
            try:
                return f"{part[:4]}-{part[4:6]}-{part[6:8]}"
            except (ValueError, IndexError):
                pass
    return None


def audit_directory(scan_path):
    """Scan one directory and return findings dict."""
    findings = {
        "path": str(scan_path),
        "exists": scan_path.exists(),
        "file_count": 0,
        "extensions": defaultdict(int),
        "valid_json": 0,
        "invalid_json": 0,
        "json_structures": defaultdict(int),  # array, object, other
        "roles_distinguishable": 0,
        "roles_not_distinguishable": 0,
        "content_field": defaultdict(int),
        "has_per_message_timestamps": 0,
        "has_session_timestamp": 0,
        "has_filename_timestamp": 0,
        "has_no_timestamp": 0,
        "non_json_formats": defaultdict(int),
        "size_buckets": defaultdict(int),  # "0-10KB", "10-100KB", etc.
        "total_size_bytes": 0,
        "max_file_path": "",
        "max_file_size": 0,
        "date_range": {"earliest": None, "latest": None},
        "files_over_1mb": [],
        "importable": 0,
        "needs_conversion": 0,
        "deferred_reason": [],
    }

    if not scan_path.exists():
        return findings

    all_files = sorted(scan_path.iterdir())
    findings["file_count"] = len(all_files)

    # Sample first 100 files for detailed structure analysis
    sample = all_files[:100]
    checksums = {}

    for fpath in all_files:
        if not fpath.is_file():
            continue

        ext = fpath.suffix.lower() or "(no extension)"
        findings["extensions"][ext] += 1
        fsize = fpath.stat().st_size
        findings["total_size_bytes"] += fsize

        if fsize > findings["max_file_size"]:
            findings["max_file_size"] = fsize
            findings["max_file_path"] = str(fpath)

        # Size buckets
        if fsize < 10240:
            findings["size_buckets"]["0-10KB"] += 1
        elif fsize < 102400:
            findings["size_buckets"]["10-100KB"] += 1
        elif fsize < 1048576:
            findings["size_buckets"]["100KB-1MB"] += 1
        else:
            findings["size_buckets"]["1MB+"] += 1
            findings["files_over_1mb"].append({
                "path": str(fpath),
                "size": fsize,
                "ext": ext,
                "dir": str(scan_path),
            })

        # Date from filename
        fdate = parse_filename_date(fpath.name)
        if fdate:
            findings["has_filename_timestamp"] += 1
            if findings["date_range"]["earliest"] is None or fdate < findings["date_range"]["earliest"]:
                findings["date_range"]["earliest"] = fdate
            if findings["date_range"]["latest"] is None or fdate > findings["date_range"]["latest"]:
                findings["date_range"]["latest"] = fdate

        # JSON validation
        if ext == ".json":
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                findings["valid_json"] += 1

                # Structure
                if isinstance(data, list):
                    findings["json_structures"]["array"] += 1
                elif isinstance(data, dict):
                    findings["json_structures"]["object"] += 1
                else:
                    findings["json_structures"]["other"] += 1

                # Role detection (only on sample for performance)
                if fpath in sample:
                    messages = None
                    if isinstance(data, list):
                        messages = data
                    elif isinstance(data, dict) and "messages" in data:
                        messages = data["messages"]

                    if messages and isinstance(messages, list) and len(messages) > 0:
                        roles = set()
                        content_fields = set()
                        for msg in messages[:20]:
                            if isinstance(msg, dict):
                                roles.add(msg.get("role", ""))
                                for key in msg:
                                    if key.lower() in ("content", "text", "message", "body"):
                                        content_fields.add(key)
                        if "user" in roles or "assistant" in roles or "system" in roles:
                            findings["roles_distinguishable"] += 1
                        else:
                            findings["roles_not_distinguishable"] += 1
                        for cf in content_fields:
                            findings["content_field"][cf] += 1

                findings["importable"] += 1

            except (json.JSONDecodeError, UnicodeDecodeError):
                findings["invalid_json"] += 1
                findings["needs_conversion"] += 1
        else:
            findings["non_json_formats"][ext] += 1
            findings["needs_conversion"] += 1

        # Checksum dup check (first 100 only)
        if len(checksums) < 100:
            try:
                cs = sha256_file(fpath)
                if cs in checksums:
                    findings.setdefault("duplicates", []).append(
                        {"file1": checksums[cs], "file2": str(fpath)}
                    )
                else:
                    checksums[cs] = str(fpath)
            except (OSError, IOError):
                pass

    return findings


def sample_large_files(findings_all, max_sample_bytes=5_000_000):
    """For files >1MB, sample their structure by reading the full file."""
    large_samples = {}
    for dir_findings in findings_all:
        for lf in dir_findings.get("files_over_1mb", []):
            path = Path(lf["path"])
            try:
                size_mb = lf["size"] / 1048576
                # Read full file to properly validate JSON (up to 100KB of content)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read(max_sample_bytes)
                is_valid = False
                msg_count = 0
                has_roles = False
                try:
                    data = json.loads(content)
                    is_valid = True
                    if isinstance(data, dict) and "messages" in data:
                        msgs = data["messages"]
                        msg_count = len(msgs) if isinstance(msgs, list) else 0
                        if msgs and isinstance(msgs, list):
                            roles = {m.get("role") for m in msgs[:20] if isinstance(m, dict)}
                            has_roles = "user" in roles or "assistant" in roles
                except json.JSONDecodeError:
                    pass

                if is_valid and has_roles:
                    ftype = f"Hermes session ({msg_count} messages, roles distinguishable)"
                    rec = "INCLUDE — valid session with distinguishable roles"
                elif is_valid:
                    ftype = f"Valid JSON ({msg_count} messages, roles NOT confirmed)"
                    rec = "DEFER — roles not confirmed, review before import"
                else:
                    ftype = "JSON parse error (may be truncated read or non-standard format)"
                    rec = "DEFER — sample and split strategy needed"

                large_samples[str(path)] = {
                    "size_mb": round(size_mb, 2),
                    "ext": path.suffix,
                    "type_guess": ftype,
                    "recommendation": rec,
                }
            except (OSError, IOError, UnicodeDecodeError):
                large_samples[str(path)] = {"size_mb": lf["size"] / 1048576, "error": "unreadable"}
    return large_samples


def write_report(findings_all, large_samples):
    """Write the markdown audit report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = AUDIT_DIR / f"corpus_audit_{now}.md"

    total_files = sum(f["file_count"] for f in findings_all)
    total_importable = sum(f["importable"] for f in findings_all)
    total_needs_conversion = sum(f["needs_conversion"] for f in findings_all)
    total_over_1mb = sum(len(f["files_over_1mb"]) for f in findings_all)

    lines = [
        f"# Corpus Audit — {now}",
        "",
        f"**Tier:** 7.5a | **Tool:** `tools/audit/corpus_audit.py`",
        f"**Total files scanned:** {total_files}",
        "",
        "---",
        "",
    ]

    for findings in findings_all:
        if not findings["exists"]:
            lines.append(f"## Directory: {findings['path']}")
            lines.append("")
            lines.append("**NOT FOUND** — directory does not exist.")
            lines.append("")
            continue

        lines.append(f"## Directory: {findings['path']}")
        lines.append("")
        lines.append(f"- File count: {findings['file_count']}")
        lines.append(f"- Total size: {findings['total_size_bytes'] / 1048576:.1f} MB")
        lines.append(f"- Largest file: {findings['max_file_size'] / 1048576:.1f} MB ({findings['max_file_path']})")

        # Extensions
        lines.append(f"- Extensions: {', '.join(f'{ext} ({count})' for ext, count in sorted(findings['extensions'].items()))}")

        # JSON stats
        jtotal = findings["valid_json"] + findings["invalid_json"]
        if jtotal > 0:
            lines.append(f"- Valid JSON: {findings['valid_json']}/{jtotal} ({findings['valid_json'] * 100 // jtotal}%)")
            if findings["json_structures"]:
                structs = ", ".join(f"{k}: {v}" for k, v in sorted(findings["json_structures"].items()))
                lines.append(f"- JSON structures: {structs}")
        if findings["invalid_json"] > 0:
            lines.append(f"- Invalid JSON: {findings['invalid_json']}")

        # Roles
        rtotal = findings["roles_distinguishable"] + findings["roles_not_distinguishable"]
        if rtotal > 0:
            lines.append(f"- Roles distinguishable: {findings['roles_distinguishable']}/{rtotal} (sampled)")

        # Content fields
        if findings["content_field"]:
            cfs = ", ".join(f"'{k}': {v}" for k, v in sorted(findings["content_field"].items()))
            lines.append(f"- Content fields found: {cfs}")

        # Timestamps
        ts_parts = []
        if findings["has_filename_timestamp"]:
            ts_parts.append(f"filename: {findings['has_filename_timestamp']}")
        if findings["has_per_message_timestamps"]:
            ts_parts.append(f"per-message: {findings['has_per_message_timestamps']}")
        if findings["has_session_timestamp"]:
            ts_parts.append(f"session: {findings['has_session_timestamp']}")
        if findings["has_no_timestamp"]:
            ts_parts.append(f"none: {findings['has_no_timestamp']}")
        lines.append(f"- Timestamps: {', '.join(ts_parts) if ts_parts else 'none detected'}")

        # Date range
        if findings["date_range"]["earliest"]:
            lines.append(f"- Date range: {findings['date_range']['earliest']} to {findings['date_range']['latest']}")

        # Non-JSON
        if findings["non_json_formats"]:
            njs = ", ".join(f"{ext}: {count}" for ext, count in sorted(findings["non_json_formats"].items()))
            lines.append(f"- Non-JSON formats: {njs}")

        # Size buckets
        lines.append("- Size distribution:")
        for bucket in ["0-10KB", "10-100KB", "100KB-1MB", "1MB+"]:
            count = findings["size_buckets"].get(bucket, 0)
            lines.append(f"  - {bucket}: {count}")

        # Importability
        lines.append(f"- Immediately importable: {findings['importable']}")
        lines.append(f"- Needs conversion: {findings['needs_conversion']}")

        # Duplicates
        if findings.get("duplicates"):
            lines.append(f"- Likely duplicates: {len(findings['duplicates'])}")

        # Recommendation
        if findings["importable"] > 0 and findings["needs_conversion"] == 0:
            lines.append("- **Recommendation: INCLUDE in first import subset**")
        elif findings["importable"] > 0:
            lines.append(f"- **Recommendation: INCLUDE importable files ({findings['importable']}); DEFER conversion-needed ({findings['needs_conversion']})**")
        else:
            lines.append("- **Recommendation: DEFER — no importable files**")

        lines.append("")

    # Large files section
    if total_over_1mb > 0:
        lines.append("## Files Larger Than 1MB")
        lines.append("")
        lines.append(f"Total files over 1MB: {total_over_1mb}")
        lines.append("")
        for path, info in sorted(large_samples.items()):
            lines.append(f"- `{path}` — {info.get('size_mb', '?')} MB — {info.get('type_guess', 'unknown')}")
            lines.append(f"  - Recommendation: {info.get('recommendation', 'DEFER')}")
            if "error" in info:
                lines.append(f"  - Error: {info['error']}")
        lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total files scanned: {total_files}")
    lines.append(f"- Immediately importable: {total_importable} ({total_importable * 100 // max(total_files, 1)}%)")
    lines.append(f"- Requires conversion: {total_needs_conversion} ({total_needs_conversion * 100 // max(total_files, 1)}%)")
    lines.append(f"- Files over 1MB: {total_over_1mb}")
    pct_over_1mb = total_over_1mb * 100 // max(total_files, 1)
    lines.append(f"- Large file recommendation: {'INVESTIGATE before import — ' if total_over_1mb > 0 else 'None'}see large files section above")

    lines.append("")
    lines.append("### First import subset recommendation")
    importable_count = 0
    conversion_count = 0
    for f in findings_all:
        if f["exists"]:
            importable_count += f["importable"]
            conversion_count += f["needs_conversion"]
    lines.append(f"- **Importable files across all directories: {importable_count}**")
    lines.append(f"- **Conversion-needed files across all directories: {conversion_count}**")
    lines.append("- **All directories with valid Hermes session JSON should be included.**")
    lines.append("- **Deferred formats:** .jsonl, .tmp, .md, .docx, .txt (Claude/ChatGPT transcripts)")
    if importable_count > 0:
        included_dirs = [f["path"] for f in findings_all if f["exists"] and f["importable"] > 0]
        lines.append(f"- **Include directories:** {', '.join(included_dirs)}")
    non_hermes = [f["path"] for f in findings_all if f["exists"] and "_chat_transcripts" in f["path"]]
    if non_hermes:
        lines.append(f"- **Defer directories (mixed/non-Hermes formats):** {', '.join(non_hermes)}")

    lines.append("")
    lines.append("### Tier 7.5b readiness")
    if total_importable > 0:
        lines.append("- **Tier 7.5b can proceed** with the importable subset.")
        if total_over_1mb > 0:
            lines.append("- **Caution:** Large files >1MB should be sampled before import.")
    else:
        lines.append("- **Tier 7.5b BLOCKED** — no importable files found.")

    lines.append("")
    lines.append("### User/model message separation")
    # Check if roles are distinguishable in the sampled files
    all_samples_with_roles = 0
    all_samples_checked = 0
    for f in findings_all:
        if f["exists"]:
            checked = f.get("roles_distinguishable", 0) + f.get("roles_not_distinguishable", 0)
            all_samples_checked += checked
            all_samples_with_roles += f.get("roles_distinguishable", 0)
    if all_samples_checked > 0 and all_samples_with_roles > 0:
        lines.append(f"- **User messages CAN be separated from model messages.** ({all_samples_with_roles}/{all_samples_checked} sampled files have distinguishable roles)")
    elif all_samples_checked > 0:
        lines.append("- **WARNING:** Role detection did not find user/assistant roles in sampled files. Check message structure.")
    else:
        lines.append("- **WARNING:** No files were sampled for role detection. Check audit logic.")

    report_text = "\n".join(lines) + "\n"
    report_path.write_text(report_text)
    return report_path


def main():
    findings_all = []
    for scan_path in SCAN_DIRS:
        print(f"Scanning: {scan_path}")
        findings = audit_directory(scan_path)
        findings_all.append(findings)
        if findings["exists"]:
            print(f"  {findings['file_count']} files, {findings['importable']} importable, {findings['needs_conversion']} need conversion")
        else:
            print(f"  (not found)")

    large_samples = sample_large_files(findings_all)
    report_path = write_report(findings_all, large_samples)
    print(f"\nReport: {report_path}")
    return report_path


if __name__ == "__main__":
    main()
