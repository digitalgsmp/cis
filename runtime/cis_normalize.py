#!/usr/bin/env python3
"""
CIS Phase 0 — Normalize Command
Usage: python3 cis_normalize.py <source_id>
Converts raw extraction output into canonical knowledge_record JSON + markdown.
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime, timezone

CIS_ROOT = "/mnt/projects/cis"
PROCESSING = f"{CIS_ROOT}/ingest/processing"
KNOWLEDGE = f"{CIS_ROOT}/knowledge/records"
LOG_PATH = f"{CIS_ROOT}/logs/normalize.log"


def get_now():
    return datetime.now(timezone.utc).isoformat()


def log(message):
    timestamp = get_now()
    with open(LOG_PATH, "a") as f:
        f.write(f"{timestamp} | {message}\n")
    print(f"{timestamp} | {message}")


def load_manifest(source_id):
    manifest_path = os.path.join(PROCESSING, source_id, "manifest.json")
    if not os.path.exists(manifest_path):
        log(f"ERROR: Manifest not found for {source_id}")
        sys.exit(1)
    with open(manifest_path) as f:
        return json.load(f), manifest_path


def save_manifest(manifest, manifest_path):
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def parse_raw_extraction(raw_text):
    fields = {
        "visible_text": "",
        "scene_description": "",
        "layout_description": "",
        "mood_style": "",
        "tags": [],
        "uncertainty": "",
        "short_summary": ""
    }

    section_map = {
        "VISIBLE_TEXT": "visible_text",
        "SCENE_DESCRIPTION": "scene_description",
        "LAYOUT_DESCRIPTION": "layout_description",
        "MOOD_STYLE": "mood_style",
        "TAGS": "tags",
        "UNCERTAINTY": "uncertainty",
        "SHORT_SUMMARY": "short_summary"
    }

    current_section = None
    current_lines = []

    for line in raw_text.split("\n"):
        stripped = line.strip()
        matched = False
        for header, field in section_map.items():
            if (stripped.startswith(f"### {header}") or
                    stripped.startswith(f"## {header}") or
                    stripped == header + ":"):
                if current_section and current_lines:
                    fields[current_section] = "\n".join(current_lines).strip()
                current_section = field
                current_lines = []
                matched = True
                break
        if not matched and current_section:
            current_lines.append(line)

    if current_section and current_lines:
        fields[current_section] = "\n".join(current_lines).strip()

    if fields["tags"] and isinstance(fields["tags"], str):
        tag_text = fields["tags"].strip()
        tag_text = re.sub(r"^[-*]\s*", "", tag_text)
        tags = [t.strip().strip('"').strip("'")
                for t in tag_text.split(",") if t.strip()]
        fields["tags"] = tags

    return fields


def build_record_id(source_id, unit="001"):
    parts = source_id.upper().split("__")
    if len(parts) >= 3:
        return f"KNOWLEDGE__{parts[0]}__{parts[1]}__{unit}__{parts[2]}"
    return f"KNOWLEDGE__{source_id.upper()}__{unit}"


def infer_knowledge_category(source_type, tags):
    tag_lower = [t.lower() for t in tags]
    if any(t in tag_lower for t in ["tutorial", "guide", "how-to",
                                     "walkthrough", "lesson"]):
        return "learning"
    if any(t in tag_lower for t in ["comic", "illustration", "reference",
                                     "cover", "art", "design"]):
        return "reference"
    if source_type == "video":
        return "learning"
    return "reference"


def build_knowledge_record(manifest, parsed_fields, unit="001"):
    source_id = manifest["source_id"]
    source_type = manifest["source_type"]
    original_filename = manifest["original_filename"]
    source_path = manifest["source_path"]
    tags = parsed_fields.get("tags", [])

    record_id = build_record_id(source_id, unit)
    knowledge_category = infer_knowledge_category(source_type, tags)

    retrieval_parts = []
    if parsed_fields.get("short_summary"):
        retrieval_parts.append(parsed_fields["short_summary"])
    if parsed_fields.get("scene_description"):
        scene = parsed_fields["scene_description"]
        retrieval_parts.append(scene[:300] if len(scene) > 300 else scene)
    if parsed_fields.get("visible_text"):
        vt = parsed_fields["visible_text"]
        retrieval_parts.append(f"Visible text: {vt[:200]}")
    retrieval_text = " | ".join(retrieval_parts)

    return {
        "record_id": record_id,
        "record_type": "knowledge_record",
        "title": parsed_fields.get("short_summary", original_filename),
        "source_type": source_type,
        "source_name": original_filename,
        "source_path": source_path,
        "source_unit": unit,
        "knowledge_category": knowledge_category,
        "subject": "comics" if "comic" in str(tags).lower() else "general",
        "tags": tags,
        "summary": parsed_fields.get("short_summary", ""),
        "visible_text": parsed_fields.get("visible_text", ""),
        "scene_description": parsed_fields.get("scene_description", ""),
        "layout_description": parsed_fields.get("layout_description", ""),
        "mood_style": parsed_fields.get("mood_style", ""),
        "uncertainty": parsed_fields.get("uncertainty", ""),
        "retrieval_text": retrieval_text,
        "project_id": manifest.get("project_id"),
        "project_title": None,
        "active_stages": ["image"],
        "source_origin": "local",
        "model_used": manifest.get("model_used",
                                   "Qwen2.5-VL-32B-Instruct-4bit"),
        "created_at": get_now(),
        "updated_at": get_now(),
        "status": "draft",
        "version": "v1",
        "is_current": True
    }


def build_markdown_mirror(record):
    lines = [
        f"# {record['title']}",
        "",
        f"**Record ID:** {record['record_id']}",
        f"**Status:** {record['status']}",
        f"**Category:** {record['knowledge_category']}",
        f"**Subject:** {record['subject']}",
        f"**Source:** {record['source_name']}",
        f"**Model:** {record['model_used']}",
        f"**Created:** {record['created_at'][:10]}",
        "",
        "## Summary",
        record['summary'],
        "",
        "## Visible Text",
        record['visible_text'],
        "",
        "## Scene Description",
        record['scene_description'],
        "",
        "## Layout",
        record['layout_description'],
        "",
        "## Mood and Style",
        record['mood_style'],
        "",
        "## Uncertainty",
        record['uncertainty'],
        "",
        "## Tags",
        ", ".join(record['tags']),
        "",
        "## Retrieval Text",
        record['retrieval_text'],
    ]
    return "\n".join(lines)


def run_normalize(source_id):
    manifest, manifest_path = load_manifest(source_id)

    if manifest["status"] != "extracted":
        log(f"ERROR: {source_id} status is '{manifest['status']}' "
            f"— normalize requires status 'extracted'")
        sys.exit(1)

    raw_outputs = manifest.get("raw_outputs", [])
    if not raw_outputs:
        log(f"ERROR: No raw outputs found in manifest for {source_id}")
        sys.exit(1)

    log(f"NORMALIZE START: {source_id} | units={len(raw_outputs)}")

    record_family = source_id.upper()
    record_dir = os.path.join(KNOWLEDGE, record_family)
    os.makedirs(record_dir, exist_ok=True)
    os.makedirs(os.path.join(record_dir, "source"), exist_ok=True)

    records_created = []

    for output_info in raw_outputs:
        unit = output_info["unit"]
        raw_path = output_info["raw_output_path"]

        with open(raw_path) as f:
            raw_text = f.read()

        parsed = parse_raw_extraction(raw_text)
        record = build_knowledge_record(manifest, parsed, unit)

        json_path = os.path.join(record_dir, f"record_{unit}.json")
        with open(json_path, "w") as f:
            json.dump(record, f, indent=2)

        md_path = os.path.join(record_dir, f"record_{unit}.md")
        with open(md_path, "w") as f:
            f.write(build_markdown_mirror(record))

        records_created.append({
            "record_id": record["record_id"],
            "json_path": json_path,
            "md_path": md_path,
            "status": "draft"
        })

        log(f"RECORD CREATED: {record['record_id']}")

    now = get_now()
    manifest["status"] = "draft"
    manifest["updated_at"] = now
    manifest["knowledge_records"] = records_created
    manifest["history"].append({
        "status": "draft",
        "timestamp": now,
        "note": f"normalized {len(records_created)} record(s) to knowledge/records/"
    })

    save_manifest(manifest, manifest_path)

    log(f"NORMALIZE COMPLETE: {source_id} | "
        f"status=draft | records={len(records_created)}")

    print(f"\nSource ID: {source_id}")
    print(f"Status:    draft")
    print(f"Records:   {len(records_created)}")
    for r in records_created:
        print(f"  {r['record_id']}")
        print(f"    JSON: {r['json_path']}")
        print(f"    MD:   {r['md_path']}")
    print(f"Next step: python3 cis_review.py {source_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIS Normalize Command")
    parser.add_argument("source_id", help="Source ID from extract")
    args = parser.parse_args()
    run_normalize(args.source_id)
