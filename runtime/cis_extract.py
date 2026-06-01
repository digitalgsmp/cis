#!/usr/bin/env python3
"""
CIS Phase 0 — Extract Command
Usage: python3 cis_extract.py <source_id>
Runs vision extraction using Qwen2.5-VL-32B via transformers + bitsandbytes.
Requires gpu-test environment:
  source /home/eric/gpu-test/bin/activate
  python3 /mnt/projects/cis/runtime/cis_extract.py <source_id>
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone

CIS_ROOT = "/mnt/projects/cis"
PROCESSING = f"{CIS_ROOT}/ingest/processing"
LOG_PATH = f"{CIS_ROOT}/logs/extract.log"
MODEL_PATH = "/mnt/models/huggingface/hub/models--Qwen--Qwen2.5-VL-32B-Instruct/snapshots/7cfb30d71a1f4f49a57592323337a4a4727301da"

EXTRACTION_PROMPT = """Analyze this image carefully and objectively.

Respond with ONLY these labeled sections. Do not add narrative or invented context.

VISIBLE_TEXT:
List all text you can read directly from the image. Quote exactly. If none, write NONE.

SCENE_DESCRIPTION:
Describe what is physically visible. Characters, objects, setting, actions. Be concrete.

LAYOUT_DESCRIPTION:
Describe the composition, arrangement, and structure of visual elements.

MOOD_STYLE:
Describe the visual style, color palette, and mood. Observable only.

TAGS:
List 8-12 specific concrete tags. No abstract concepts. Comma separated.

UNCERTAINTY:
List anything you cannot read clearly or are unsure about. If nothing, write NONE.

SHORT_SUMMARY:
One sentence describing what this image is."""

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

def load_model():
    try:
        import torch
        from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
        from qwen_vl_utils import process_vision_info
    except ImportError as e:
        log(f"ERROR: Missing dependency: {e}")
        log("Activate gpu-test environment first:")
        log("  source /home/eric/gpu-test/bin/activate")
        sys.exit(1)

    log(f"Loading model from {MODEL_PATH}")
    log("This takes 2-3 minutes on first load...")

    from transformers import BitsAndBytesConfig
    bnb_config = BitsAndBytesConfig(load_in_4bit=True)
    processor = AutoProcessor.from_pretrained(MODEL_PATH)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto"
    )

    log("Model loaded successfully")
    return model, processor

def run_extraction(model, processor, image_path):
    import torch
    from qwen_vl_utils import process_vision_info

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": EXTRACTION_PROMPT}
            ]
        }
    ]

    text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt"
    )
    inputs = inputs.to("cuda")

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=0.1,
            do_sample=False
        )

    generated_ids_trimmed = [
        out_ids[len(in_ids):]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]

    output = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )

    return output[0]

def run_extract(source_id):
    manifest, manifest_path = load_manifest(source_id)

    if manifest["status"] != "preprocessed":
        log(f"ERROR: {source_id} is in status '{manifest['status']}' "
            f"— extract requires status 'preprocessed'")
        sys.exit(1)

    extracted_files = manifest.get("extracted_files", [])
    if not extracted_files:
        log(f"ERROR: No extracted files found in manifest for {source_id}")
        sys.exit(1)

    log(f"EXTRACT START: {source_id} | files={len(extracted_files)}")

    model, processor = load_model()

    raw_outputs = []
    records_dir = os.path.join(PROCESSING, source_id, "records")
    os.makedirs(records_dir, exist_ok=True)

    for i, file_path in enumerate(extracted_files):
        filename = os.path.basename(file_path)
        log(f"EXTRACTING: {filename}")

        raw_output = run_extraction(model, processor, file_path)

        raw_filename = f"raw_extraction_{str(i+1).zfill(3)}.txt"
        raw_path = os.path.join(records_dir, raw_filename)
        with open(raw_path, "w") as f:
            f.write(raw_output)

        raw_outputs.append({
            "source_file": file_path,
            "raw_output_path": raw_path,
            "unit": str(i+1).zfill(3)
        })
        log(f"RAW OUTPUT SAVED: {raw_path}")

    now = get_now()
    manifest["status"] = "extracted"
    manifest["updated_at"] = now
    manifest["raw_outputs"] = raw_outputs
    manifest["model_used"] = "Qwen2.5-VL-32B-Instruct-4bit"
    manifest["runtime"] = "transformers+bitsandbytes"
    manifest["history"].append({
        "status": "extracted",
        "timestamp": now,
        "note": f"extracted {len(raw_outputs)} unit(s) using "
                f"Qwen2.5-VL-32B 4-bit via transformers"
    })

    save_manifest(manifest, manifest_path)

    log(f"EXTRACT COMPLETE: {source_id} | "
        f"status=extracted | units={len(raw_outputs)}")

    print(f"\nSource ID:    {source_id}")
    print(f"Status:       extracted")
    print(f"Units:        {len(raw_outputs)}")
    print(f"Next step:    python3 cis_normalize.py {source_id}")

    return source_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIS Extract Command")
    parser.add_argument("source_id", help="Source ID from preprocess")
    args = parser.parse_args()
    run_extract(args.source_id)
