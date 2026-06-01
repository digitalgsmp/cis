#!/usr/bin/env python3
"""
CIS Phase 0 — Classify Command
Usage: python3 cis_classify.py <source_id>
Assigns processing profile and moves source to classified status.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone

CIS_ROOT = "/mnt/projects/cis"
PROCESSING = f"{CIS_ROOT}/ingest/processing"
LOG_PATH = f"{CIS_ROOT}/logs/classify.log"

PROCESSING_PROFILES = {
    "image": {
        "passes": ["vision"],
        "models": ["qwen2.5-vl-32b"],
        "ocr": False,
        "extract_pages": False,
        "sample_frames": False,
        "notes": "Single image — vision pass only"
    },
    "pdf": {
        "passes": ["ocr", "vision", "merge"],
        "models": ["tesseract", "qwen2.5-vl-32b"],
        "ocr": True,
        "extract_pages": True,
        "sample_frames": False,
        "notes": "PDF — extract pages, run OCR and vision, merge"
    },
    "video": {
        "passes": ["frame_sample", "vision", "transcript"],
        "models": ["qwen2.5-vl-32b", "whisper"],
        "ocr": False,
        "extract_pages": False,
        "sample_frames": True,
        "notes": "Video — sample frames and extract transcript"
    },
    "audio": {
        "passes": ["transcript"],
        "models": ["whisper"],
        "ocr": False,
        "extract_pages": False,
        "sample_frames": False,
        "notes": "Audio — transcript only"
    },
    "text": {
        "passes": ["text_extract"],
        "models": ["none"],
        "ocr": False,
        "extract_pages": False,
        "sample_frames": False,
        "notes": "Text file — direct extraction"
    },
    "unknown": {
        "passes": ["manual_review"],
        "models": ["none"],
        "ocr": False,
        "extract_pages": False,
        "sample_frames": False,
        "notes": "Unknown type — requires manual classification"
    }
}

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

def run_classify(source_id):
    manifest, manifest_path = load_manifest(source_id)

    # Validate current status
    if manifest["status"] != "arrived":
        log(f"ERROR: {source_id} is in status '{manifest['status']}' "
            f"— classify requires status 'arrived'")
        sys.exit(1)

    source_type = manifest["source_type"]
    profile = PROCESSING_PROFILES.get(source_type,
                                       PROCESSING_PROFILES["unknown"])

    log(f"CLASSIFY START: {source_id} | type={source_type}")

    # Update manifest
    now = get_now()
    manifest["status"] = "classified"
    manifest["processing_profile"] = source_type
    manifest["processing_plan"] = profile
    manifest["updated_at"] = now
    manifest["history"].append({
        "status": "classified",
        "timestamp": now,
        "note": f"profile assigned: {source_type} | "
                f"passes: {profile['passes']}"
    })

    save_manifest(manifest, manifest_path)

    log(f"CLASSIFY COMPLETE: {source_id} | status=classified | "
        f"passes={profile['passes']}")

    print(f"\nSource ID: {source_id}")
    print(f"Status:    classified")
    print(f"Profile:   {source_type}")
    print(f"Passes:    {profile['passes']}")
    print(f"Models:    {profile['models']}")
    print(f"Notes:     {profile['notes']}")
    print(f"Next step: python3 cis_preprocess.py {source_id}")

    return source_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIS Classify Command")
    parser.add_argument("source_id", help="Source ID from intake")
    args = parser.parse_args()
    run_classify(args.source_id)
