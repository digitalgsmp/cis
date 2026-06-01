#!/usr/bin/env python3
"""
CIS Phase 0 — Preprocess Command
Usage: python3 cis_preprocess.py <source_id>
Prepares source material for extraction.
- Images: copied directly to extracted folder
- PDFs: pages extracted as images
- Videos: frames sampled
- Text: copied directly
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime, timezone

CIS_ROOT = "/mnt/projects/cis"
PROCESSING = f"{CIS_ROOT}/ingest/processing"
LOG_PATH = f"{CIS_ROOT}/logs/preprocess.log"

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

def preprocess_image(source_path, extracted_dir):
    filename = os.path.basename(source_path)
    dest = os.path.join(extracted_dir, filename)
    shutil.copy2(source_path, dest)
    return [dest]

def preprocess_pdf(source_path, extracted_dir):
    try:
        from pdf2image import convert_from_path
    except ImportError:
        log("ERROR: pdf2image not installed. Run: pip install pdf2image")
        sys.exit(1)
    pages = convert_from_path(source_path, dpi=150)
    output_files = []
    for i, page in enumerate(pages):
        page_filename = f"page_{str(i+1).zfill(3)}.png"
        page_path = os.path.join(extracted_dir, page_filename)
        page.save(page_path, "PNG")
        output_files.append(page_path)
        log(f"PAGE EXTRACTED: {page_filename}")
    return output_files

def preprocess_text(source_path, extracted_dir):
    filename = os.path.basename(source_path)
    dest = os.path.join(extracted_dir, filename)
    shutil.copy2(source_path, dest)
    return [dest]

def run_preprocess(source_id):
    manifest, manifest_path = load_manifest(source_id)

    if manifest["status"] != "classified":
        log(f"ERROR: {source_id} is in status '{manifest['status']}' "
            f"— preprocess requires status 'classified'")
        sys.exit(1)

    source_type = manifest["source_type"]
    source_path = manifest["source_path"]
    extracted_dir = os.path.join(PROCESSING, source_id, "extracted")
    os.makedirs(extracted_dir, exist_ok=True)

    log(f"PREPROCESS START: {source_id} | type={source_type}")

    if source_type == "image":
        output_files = preprocess_image(source_path, extracted_dir)
    elif source_type == "pdf":
        output_files = preprocess_pdf(source_path, extracted_dir)
    elif source_type == "text":
        output_files = preprocess_text(source_path, extracted_dir)
    else:
        log(f"WARNING: No preprocessor for type '{source_type}'. "
            f"Copying source directly.")
        output_files = preprocess_image(source_path, extracted_dir)

    now = get_now()
    manifest["status"] = "preprocessed"
    manifest["updated_at"] = now
    manifest["extracted_files"] = output_files
    manifest["extracted_count"] = len(output_files)
    manifest["history"].append({
        "status": "preprocessed",
        "timestamp": now,
        "note": f"extracted {len(output_files)} file(s) to extracted/"
    })

    save_manifest(manifest, manifest_path)

    log(f"PREPROCESS COMPLETE: {source_id} | "
        f"status=preprocessed | files={len(output_files)}")

    print(f"\nSource ID:       {source_id}")
    print(f"Status:          preprocessed")
    print(f"Extracted files: {len(output_files)}")
    for f in output_files:
        print(f"  {f}")
    print(f"Next step: python3 cis_extract.py {source_id}")

    return source_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIS Preprocess Command")
    parser.add_argument("source_id", help="Source ID from classify")
    args = parser.parse_args()
    run_preprocess(args.source_id)
