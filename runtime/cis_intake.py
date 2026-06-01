#!/usr/bin/env python3
"""
CIS Phase 0 — Intake Command
Usage: python3 cis_intake.py <file_path> [--project PROJECT_ID]
Creates a source manifest and moves file to arrived state.
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
from datetime import datetime, timezone

CIS_ROOT = "/mnt/projects/cis"
INCOMING = f"{CIS_ROOT}/ingest/incoming"
PROCESSING = f"{CIS_ROOT}/ingest/processing"
COMPLETED = f"{CIS_ROOT}/ingest/completed"
LOG_PATH = f"{CIS_ROOT}/logs/intake.log"

def get_now():
    return datetime.now(timezone.utc).isoformat()

def log(message):
    timestamp = get_now()
    with open(LOG_PATH, "a") as f:
        f.write(f"{timestamp} | {message}\n")
    print(f"{timestamp} | {message}")

def get_file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def infer_source_type(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    mapping = {
        ".pdf": "pdf",
        ".jpg": "image", ".jpeg": "image",
        ".png": "image", ".webp": "image",
        ".mp4": "video", ".mov": "video", ".avi": "video",
        ".mp3": "audio", ".wav": "audio",
        ".txt": "text", ".md": "text",
    }
    return mapping.get(ext, "unknown")

def build_source_slug(filename):
    base = os.path.splitext(filename)[0]
    slug = base.lower()
    slug = slug.replace(" ", "_")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    return slug[:40]

def find_next_sequence(source_type, source_slug):
    pattern = f"{source_type}__{source_slug}__"
    existing = [
        d for d in os.listdir(PROCESSING)
        if d.startswith(pattern)
    ]
    return str(len(existing) + 1).zfill(3)

def run_intake(file_path, project_id=None):
    # Validate input
    if not os.path.exists(file_path):
        log(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    filename = os.path.basename(file_path)
    source_type = infer_source_type(file_path)
    source_slug = build_source_slug(filename)
    sequence = find_next_sequence(source_type, source_slug)
    source_id = f"{source_type}__{source_slug}__{sequence}"

    log(f"INTAKE START: {filename} → {source_id}")

    # Create processing folder
    processing_dir = os.path.join(PROCESSING, source_id)
    os.makedirs(processing_dir, exist_ok=True)
    os.makedirs(os.path.join(processing_dir, "source"), exist_ok=True)
    os.makedirs(os.path.join(processing_dir, "extracted"), exist_ok=True)
    os.makedirs(os.path.join(processing_dir, "records"), exist_ok=True)

    # Copy file to source folder
    dest_path = os.path.join(processing_dir, "source", filename)
    shutil.copy2(file_path, dest_path)
    log(f"FILE COPIED: {dest_path}")

    # Calculate hash
    file_hash = get_file_hash(dest_path)
    file_size = os.path.getsize(dest_path)

    # Create source manifest
    manifest = {
        "source_id": source_id,
        "source_type": source_type,
        "source_slug": source_slug,
        "sequence": sequence,
        "original_filename": filename,
        "source_path": dest_path,
        "file_size_bytes": file_size,
        "sha256": file_hash,
        "project_id": project_id,
        "status": "arrived",
        "processing_profile": source_type,
        "created_at": get_now(),
        "updated_at": get_now(),
        "history": [
            {
                "status": "arrived",
                "timestamp": get_now(),
                "note": "intake completed"
            }
        ]
    }

    manifest_path = os.path.join(processing_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    log(f"MANIFEST CREATED: {manifest_path}")
    log(f"INTAKE COMPLETE: {source_id} | status=arrived | "
        f"size={file_size} bytes | sha256={file_hash[:16]}...")

    print(f"\nSource ID: {source_id}")
    print(f"Status:    arrived")
    print(f"Location:  {processing_dir}")
    print(f"Next step: python3 cis_classify.py {source_id}")

    return source_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIS Intake Command")
    parser.add_argument("file_path", help="Path to file to ingest")
    parser.add_argument("--project", default=None,
                        help="Optional project ID to link")
    args = parser.parse_args()
    run_intake(args.file_path, args.project)
