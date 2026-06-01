#!/usr/bin/env python3
"""
cis_ingest.py — CIS Batch Ingestion Engine

Walks source folders, classifies files, extracts content via OCR (handwriting on JPGs)
or direct text extraction (PDFs, DOCX, TXT), runs AI auto-tagging, and creates
draft Asset records in the CIS database.

Pipeline:
  1. SCAN — discover files, classify by type/extension
  2. EXTRACT — transcribe content (vision model for JPGs, text extraction for documents)
  3. ANALYZE — AI auto-tags: themes, mood, genre, key entities
  4. WRITE — create Asset records in "draft" status, store path + transcription + tags
  5. LAND — flag for human review queue

Usage:
  python3 cis_ingest.py                          # Full pipeline (default)
  python3 cis_ingest.py --dry-run                # Show what would be processed
  python3 cis_ingest.py --source /path/to/folder # Scan specific folder
  python3 cis_ingest.py --limit 50               # Max files to process
  python3 cis_ingest.py --review                 # Show pending review items
"""

import os, sys, time, json, re, hashlib, subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── Configuration ──────────────────────────────────────────────────────────
CIS_DB_PATH = Path("/mnt/projects/cis/memory/cis_app.db")

# Where our source material lives
SOURCE_FOLDERS = {
    "word_ideabank": Path("/mnt/archive/_2 Word/Idea Bank/_ideabank Sorted"),
    "word_caliber": Path("/mnt/archive/_2 Word/Caliber Library0"),
    "word_unsorted": Path("/mnt/archive/_2 Word/Idea Bank/_Ideabank Unsorted"),
    "image_tuts": Path("/mnt/archive/_3 Image/Creative 24"),
    "image_learnsquared": Path("/mnt/archive/_3 Image/Learn Squared – Production Concept Art (2018) with Jan Urschel"),
    "action_animation": Path("/mnt/archive/_4 Action/Animation"),
    "action_filmmaking": Path("/mnt/archive/_4 Action/Filmmaking"),
}

# Supported file types
FILE_CATEGORIES = {
    "poem": [".jpg", ".png", ".jpeg"],       # Handwritten poems (need OCR)
    "story": [".jpg", ".png", ".jpeg"],       # Handwritten stories (need OCR)
    "document": [".pdf"],                     # Reference PDFs
    "script": [".fdx"],                       # Final Draft scripts
    "text": [".txt", ".md", ".rtf"],         # Plain text
    "office": [".doc", ".docx"],             # Word docs
    "whiteboard": [".jpg", ".png", ".pdf"],   # Mind maps / whiteboard photos
}

# Exclude patterns
EXCLUDE_PATTERNS = [
    "desktop.ini",
    "Thumbs.db",
    "~$",           # Temp Office files
]

# Batch safety
MAX_FILES_PER_RUN = 200  # hard cap

# Qwen3-VL-30B Vision endpoint (llama.cpp server on port 8002)
# This is the production OCR model — NOT ollama/llava
VISION_API = "http://127.0.0.1:8002/v1/chat/completions"
VISION_MODEL = "qwen3-vl-30b-a3b-instruct-q4_k_m.gguf"

# ── Logger ─────────────────────────────────────────────────────────────────
LOG_FILE = Path("/mnt/projects/cis/runtime/ingestion_log.md")

def log(msg: str, level: str = "INFO"):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── Helpers ────────────────────────────────────────────────────────────────

def is_poem_title(name: str) -> bool:
    """Heuristic: detect if a filename looks like a creative work."""
    # Remove extension and count words
    stem = Path(name).stem
    # Clean up common suffixes like (2), _2
    stem = re.sub(r'[\(\[\{]?\s*[\d]+\s*[\)\]\}]?\s*$', '', stem).strip()
    if len(stem.split()) >= 2 and len(stem) > 5:
        return True
    return False

def classify_file(fpath: Path) -> dict:
    """Classify a file by extension, folder context, and naming."""
    ext = fpath.suffix.lower()
    name = fpath.name
    parent = fpath.parent.name
    grandparents = [p.name for p in fpath.parents]

    # Skip unwanted
    for pat in EXCLUDE_PATTERNS:
        if pat in name:
            return None

    # Determine general category
    if ext in (".jpg", ".jpeg", ".png"):
        # JPG in the Idea Bank letter folders = creative work
        if "ideabank" in str(fpath).lower() or any(g in ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'] for g in [fpath.parent.name]):
            if "whiteboard" in str(fpath).lower():
                return {"type": "whiteboard", "category": "planning", "needs_ocr": True}
            return {"type": "creative_work", "category": "poem_story", "needs_ocr": True}
        return {"type": "image", "category": "reference", "needs_ocr": False}

    elif ext == ".pdf":
        # Caliber Library or reference PDFs
        if "caliber" in str(fpath).lower() or "reference" in str(fpath).lower():
            return {"type": "reference", "category": "book", "needs_ocr": False}
        return {"type": "document", "category": "reference", "needs_ocr": False}

    elif ext == ".fdx":
        return {"type": "script", "category": "screenplay", "needs_ocr": False}

    elif ext == ".txt":
        return {"type": "text", "category": "note", "needs_ocr": False}

    elif ext in (".doc", ".docx"):
        return {"type": "document", "category": "writing", "needs_ocr": False}

    elif ext == ".rtf":
        return {"type": "document", "category": "writing", "needs_ocr": False}

    elif ext == ".md":
        return {"type": "text", "category": "note", "needs_ocr": False}

    elif ext in (".psd", ".tiff", ".bmp"):
        return {"type": "image", "category": "artwork", "needs_ocr": False}

    return None  # Skip — system files, archives, etc.


def extract_text_from_pdf(fpath: Path) -> Optional[str]:
    """Extract text from a PDF using pdftotext or pypdf."""
    # Try pypdf first (usually installed)
    try:
        import pypdf
        reader = pypdf.PdfReader(str(fpath))
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        if text.strip():
            return text[:5000]  # Cap at 5K chars
    except ImportError:
        pass
    # Fallback: pdftotext
    try:
        result = subprocess.run(
            ["pdftotext", str(fpath), "-", "-l", "5"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout[:5000]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def extract_text_from_docx(fpath: Path) -> Optional[str]:
    """Extract text from a .docx file."""
    try:
        import docx
        doc = docx.Document(str(fpath))
        text = "\n".join(p.text for p in doc.paragraphs)
        return text[:5000] if text.strip() else None
    except ImportError:
        pass
    try:
        result = subprocess.run(
            ["python3", "-c", f"""
import zipfile, xml.etree.ElementTree as ET
with zipfile.ZipFile('''{fpath}''') as z:
    xml = z.read('word/document.xml')
    root = ET.fromstring(xml)
    ns = {{'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}}
    texts = [t.text for t in root.iter('{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}t') if t.text]
    print(' '.join(texts)[:5000])
"""],
            capture_output=True, text=True, timeout=15
        )
        if result.stdout.strip():
            return result.stdout[:5000]
    except:
        pass
    return None


def ocr_image(fpath: Path) -> Optional[dict]:
    """
    OCR an image using Qwen3-VL-30B (llama.cpp server on port 8002).
    Returns dict: {text, confidence}
    """
    try:
        import base64, urllib.request

        with open(fpath, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = json.dumps({
            "model": VISION_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "Transcribe ALL visible handwritten and printed text from this image exactly as written. "
                            "Preserve line breaks. If it's a poem, maintain stanza breaks. "
                            "If it's a story or notes, transcribe verbatim. "
                            "If you cannot read some words, mark them as [illegible]. "
                            "Output ONLY the transcription, no commentary or description."
                        )
                    }
                ]
            }],
            "max_tokens": 2048,
            "temperature": 0.1
        })

        req = urllib.request.Request(
            VISION_API,
            data=payload.encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        if text:
            return {
                "text": text,
                "confidence": 0.85,
                "model": VISION_MODEL
            }
        return None
    except Exception as e:
        log(f"OCR failed for {fpath.name}: {e}", "WARN")
        return None


def auto_tag(text: str, fclass: dict) -> list:
    """
    Simple rule-based auto-tagging from extracted text.
    Tags: genre, mood, theme
    """
    if not text:
        return []

    tags = []
    text_lower = text.lower()

    # Genre detection
    genre_keywords = {
        "poetry": ["poem", "verse", "stanza", "rhyme", "sonnet", "haiku", "metaphor"],
        "fiction": ["story", "chapter", "once upon", "he said", "she said", "narrator"],
        "philosophy": ["truth", "meaning", "existence", "consciousness", "reality", "god"],
        "dream": ["dream", "i dreamt", "sleep", "nightmare", "asleep", "woke up"],
        "journal": ["today i", "i feel", "dear diary", "this morning", "i remember"],
        "fantasy": ["magic", "dragon", "sword", "kingdom", "spell", "shadow", "ancient"],
        "spiritual": ["prayer", "god", "soul", "spirit", "holy", "divine", "faith", "bless"],
        "nature": ["tree", "river", "sky", "ocean", "forest", "wind", "mountain", "rain"],
    }

    for genre, keywords in genre_keywords.items():
        if any(kw in text_lower for kw in keywords):
            # Check how many keywords matched
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches >= 2:
                tags.append(genre)
                break

    # Mood detection
    mood_keywords = {
        "melancholy": ["dark", "tears", "sorrow", "grief", "lonely", "death", "lost", "pain", "cry", "mourning", "shadow", "cold"],
        "joyful": ["joy", "light", "love", "beautiful", "warm", "hope", "smile", "laugh", "happy", "dance", "sunrise"],
        "reflective": ["remember", "time", "past", "age", "memory", "childhood", "old", "reflect", "thought"],
        "angst": ["anger", "rage", "hate", "frustration", "scream", "burn", "war", "fight", "break"],
        "yearning": ["desire", "want", "wish", "longing", "wait", "search", "reach", "thirst", "hunger"],
    }

    for mood, keywords in mood_keywords.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches >= 3:
            tags.append(mood)
            break

    # If no strong signal, add "uncategorized"
    if not tags:
        tags.append("uncategorized")

    return tags


def walk_source_folder(folder: Path, limit: int = 0) -> list:
    """Walk a source folder and return classified file records."""
    results = []
    if not folder.exists():
        log(f"Folder not found: {folder}", "WARN")
        return results

    for fpath in folder.rglob("*"):
        if not fpath.is_file():
            continue
        if len(results) >= (limit if limit > 0 else MAX_FILES_PER_RUN):
            break

        classification = classify_file(fpath)
        if classification is None:
            continue

        # Derive a clean display title from filename
        stem = fpath.stem
        title = re.sub(r'[\(\[\{]?\s*[\d]+\s*[\)\]\}]?\s*$', '', stem).strip()
        title = title.replace("_", " ").replace("-", " ").strip()
        title = " ".join(title.split())  # collapse whitespace

        # Determine broad tag from folder context
        source_tags = []
        parent = fpath.parent.name
        if parent in [chr(c) for c in range(ord('A'), ord('Z')+1)]:
            source_tags.append("idea_bank")
        if "whiteboard" in str(fpath).lower():
            source_tags.append("mind_map")
        if "song" in str(fpath).lower():
            source_tags.append("song_lyric")
        if "caliber" in str(fpath).lower():
            source_tags.append("reference_book")

        results.append({
            "path": str(fpath),
            "name": fpath.name,
            "title": title if is_poem_title(fpath.name) else stem,
            "ext": fpath.suffix.lower(),
            "size": fpath.stat().st_size,
            "classification": classification,
            "source_tags": source_tags,
        })

    return results


# ── Database Operations ────────────────────────────────────────────────────

def get_db():
    """Get a SQLite connection with WAL mode."""
    import sqlite3
    conn = sqlite3.connect(str(CIS_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def asset_exists(fpath: str) -> bool:
    """Check if a file path is already ingested."""
    conn = get_db()
    row = conn.execute("SELECT id FROM assets WHERE path = ?", (fpath,)).fetchone()
    conn.close()
    return row is not None


def insert_draft_asset(record: dict) -> Optional[str]:
    """
    Insert a new draft asset. record fields:
        name, path, type, category, notes (transcription),
        tags (list), source_tags (list)
    Returns asset ID or None on failure.
    """
    uid = "asset_" + datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    now = datetime.utcnow().isoformat()

    all_tags = list(set(record.get("tags", []) + record.get("source_tags", [])))

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO assets (id, name, type, path, category,
                                notes, tags, status, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            uid,
            record.get("title", record["name"]),
            record.get("classification", {}).get("type", "reference"),
            record["path"],
            record.get("classification", {}).get("category", ""),
            record.get("notes", ""),
            json.dumps(all_tags),
            "draft",  # Starts in draft — needs review
            now, now
        ))
        conn.commit()
        return uid
    except Exception as e:
        log(f"DB insert failed for {record['name']}: {e}", "ERROR")
        return None
    finally:
        conn.close()


def get_review_queue(limit: int = 50) -> list:
    """Get assets pending review (draft status, ordered by recency)."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT * FROM assets
            WHERE status = 'draft'
            ORDER BY created DESC
            LIMIT ?
        """, (limit,)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("tags"), str):
                try:
                    d["tags"] = json.loads(d["tags"])
                except:
                    d["tags"] = []
            results.append(d)
        return results
    finally:
        conn.close()


def approve_asset(asset_id: str) -> bool:
    """Approve a draft asset — moves to 'reviewed' status."""
    conn = get_db()
    try:
        now = datetime.utcnow().isoformat()
        conn.execute("UPDATE assets SET status = 'reviewed', updated = ? WHERE id = ?",
                     (now, asset_id))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def reject_asset(asset_id: str) -> bool:
    """Reject and delete a draft asset."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def update_asset_notes(asset_id: str, notes: str):
    """Update the transcription/notes on an asset."""
    conn = get_db()
    try:
        now = datetime.utcnow().isoformat()
        conn.execute("UPDATE assets SET notes = ?, updated = ? WHERE id = ?",
                     (notes, now, asset_id))
        conn.commit()
    finally:
        conn.close()


# ── Pipeline Steps ─────────────────────────────────────────────────────────

def step_scan(dry_run: bool = False, source: str = None, limit: int = 0) -> list:
    """Step 1: Scan folders and classify files."""
    log("=" * 60)
    log("STEP 1: SCANNING source folders")
    log("=" * 60)

    all_files = []

    if source:
        src_path = Path(source)
        if src_path.exists():
            log(f"Scanning: {src_path}")
            files = walk_source_folder(src_path, limit=limit)
            all_files.extend(files)
            log(f"  Found {len(files)} processable files")
    else:
        for label, folder in SOURCE_FOLDERS.items():
            if folder.exists():
                log(f"Scanning {label}: {folder}")
                files = walk_source_folder(folder, limit=limit)
                all_files.extend(files)
                log(f"  Found {len(files)} processable files")
                if limit > 0 and len(all_files) >= limit:
                    all_files = all_files[:limit]
                    log(f"  Hit limit={limit}, stopping scan")
                    break
            else:
                log(f"Skipping {label} (not found)", "WARN")

    # Filter already-ingested
    before = len(all_files)
    if not dry_run:
        all_files = [f for f in all_files if not asset_exists(f["path"])]
    log(f"  New files (not yet in DB): {len(all_files)} (filtered {before - len(all_files)} already ingested)")

    return all_files


def step_extract(files: list, dry_run: bool = False) -> list:
    """Step 2: Extract content from each file."""
    log("=" * 60)
    log("STEP 2: EXTRACTING content")
    log("=" * 60)

    for i, f in enumerate(files):
        log(f"  [{i+1}/{len(files)}] {f['name']} ({f['ext']})")

        if dry_run:
            f["notes"] = f"[DRY RUN] would extract: {f['classification']['type']}"
            f["tags"] = ["dry_run"]
            continue

        needs_ocr = f["classification"].get("needs_ocr", False)
        ftype = f["classification"]["type"]

        if needs_ocr and f["ext"] in (".jpg", ".jpeg", ".png"):
            # Vision OCR — this is the heavy operation
            log(f"    → OCR via llava vision model...")
            result = ocr_image(Path(f["path"]))
            if result:
                f["notes"] = result["text"]
                log(f"    → Extracted {len(result['text'])} chars")
            else:
                f["notes"] = "[OCR failed — image could not be transcribed]"
                log(f"    → OCR FAILED", "WARN")

        elif ftype == "reference" and f["ext"] == ".pdf":
            text = extract_text_from_pdf(Path(f["path"]))
            if text:
                f["notes"] = text
                log(f"    → Extracted {len(text)} chars from PDF")
            else:
                f["notes"] = "[PDF text extraction failed]"
                log(f"    → PDF extraction failed", "WARN")

        elif f["ext"] in (".doc", ".docx"):
            text = extract_text_from_docx(Path(f["path"]))
            if text:
                f["notes"] = text
                log(f"    → Extracted {len(text)} chars from DOCX")
            else:
                f["notes"] = "[DOCX extraction failed]"
                log(f"    → DOCX extraction failed", "WARN")

        elif f["ext"] == ".txt":
            try:
                with open(f["path"], "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read(5000)
                f["notes"] = text
            except:
                f["notes"] = "[TXT read failed]"

        else:
            # Script files, etc.
            if f["ext"] == ".fdx":
                try:
                    with open(f["path"], "r", encoding="utf-8", errors="replace") as fh:
                        text = fh.read(5000)
                    f["notes"] = text
                except:
                    f["notes"] = "[FDX read failed]"
            else:
                f["notes"] = "[Content extraction not yet supported for this type]"

        log(f"    → Notes length: {len(f.get('notes', ''))}")

    return files


def step_analyze(files: list, dry_run: bool = False) -> list:
    """Step 3: Auto-tag and classify."""
    log("=" * 60)
    log("STEP 3: ANALYZING content")
    log("=" * 60)

    for i, f in enumerate(files):
        if dry_run:
            f["tags"] = ["dry_run"]
            continue

        text = f.get("notes", "")
        tags = auto_tag(text, f["classification"])
        # Add source-context tags
        all_tags = list(set(tags + f.get("source_tags", [])))

        # Add file type tag
        if f["classification"]["type"]:
            all_tags.append(f["classification"]["type"])
        if f["classification"]["category"]:
            all_tags.append(f["classification"]["category"])

        # Add medium/handwriting tag for OCR'd work
        if f["classification"].get("needs_ocr"):
            all_tags.append("handwritten")
            all_tags.append("transcribed")

        f["tags"] = list(set(all_tags))
        log(f"  [{i+1}/{len(files)}] {f['name']} → tags: {f['tags']}")

    return files


def step_write(files: list, dry_run: bool = False) -> list:
    """Step 4: Write to database as draft assets."""
    log("=" * 60)
    log("STEP 4: WRITING to database")
    log("=" * 60)

    created = 0
    for i, f in enumerate(files):
        if dry_run:
            log(f"  [{i+1}/{len(files)}] [DRY RUN] Would create: {f['title']}")
            continue

        aid = insert_draft_asset(f)
        if aid:
            created += 1
            log(f"  [{i+1}/{len(files)}] ✓ Created asset {aid}: {f['title']}")
        else:
            log(f"  [{i+1}/{len(files)}] ✗ Failed: {f['name']}", "ERROR")

    log(f"\n  Total assets created: {created}")
    return files


# ── API endpoints (to be registered in app.py) ─────────────────────────────

def create_api_blueprint():
    """Create Flask blueprint for ingestion API."""
    from flask import Blueprint, jsonify, request

    ingest_bp = Blueprint('ingest_api', __name__, url_prefix='/api/ingest')

    @ingest_bp.route('/scan', methods=['POST'])
    def api_scan():
        """Trigger a scan. Returns summary of what would be processed."""
        data = request.json or {}
        source = data.get('source')
        dry_run = data.get('dry_run', True)  # Default dry-run for safety
        limit = data.get('limit', 50)

        files = step_scan(dry_run=True, source=source, limit=limit)
        return jsonify({
            'total': len(files),
            'files': [
                {'name': f['name'], 'title': f['title'], 'type': f['classification']['type'],
                 'category': f['classification']['category'], 'needs_ocr': f['classification'].get('needs_ocr', False)}
                for f in files[:100]  # Cap response size
            ],
            'dry_run': dry_run
        })

    @ingest_bp.route('/run', methods=['POST'])
    def api_run():
        """Execute full ingestion pipeline on a batch."""
        data = request.json or {}
        source = data.get('source')
        limit = data.get('limit', 20)

        files = step_scan(dry_run=False, source=source, limit=limit)
        if not files:
            return jsonify({'processed': 0, 'message': 'No new files found'})

        files = step_extract(files, dry_run=False)
        files = step_analyze(files, dry_run=False)
        files = step_write(files, dry_run=False)

        approved = sum(1 for f in files if f.get('tags'))

        return jsonify({
            'processed': len(files),
            'created': len(files),
            'message': f'Processed {len(files)} files, all in draft status for review'
        })

    @ingest_bp.route('/review', methods=['GET'])
    def api_review():
        """Get review queue."""
        items = get_review_queue(limit=request.args.get('limit', 50, type=int))
        return jsonify({'items': items, 'total': len(items)})

    @ingest_bp.route('/review/<asset_id>/approve', methods=['POST'])
    def api_approve(asset_id):
        success = approve_asset(asset_id)
        return jsonify({'success': success, 'status': 'reviewed' if success else 'failed'})

    @ingest_bp.route('/review/<asset_id>/reject', methods=['POST'])
    def api_reject(asset_id):
        success = reject_asset(asset_id)
        return jsonify({'success': success, 'deleted': success})

    @ingest_bp.route('/review/<asset_id>/edit', methods=['PATCH'])
    def api_edit_asset(asset_id):
        data = request.json or {}
        notes = data.get('notes')
        if notes is not None:
            update_asset_notes(asset_id, notes)
        return jsonify({'success': True})

    return ingest_bp


# ── CLI Entry Point ────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CIS Batch Ingestion Engine")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without doing it")
    parser.add_argument("--source", type=str, help="Specific folder to scan")
    parser.add_argument("--limit", type=int, default=0, help=f"Max files to process (default: {MAX_FILES_PER_RUN})")
    parser.add_argument("--review", action="store_true", help="Show pending review queue")

    args = parser.parse_args()

    if args.review:
        items = get_review_queue()
        print(f"\n📋 Review Queue: {len(items)} items pending\n")
        for item in items:
            tags = ", ".join(item.get("tags", [])) if isinstance(item.get("tags"), list) else item.get("tags", "")
            print(f"  [{item['id']}]")
            print(f"     Name:  {item['name']}")
            print(f"     Type:  {item['type']}")
            print(f"     Path:  {item['path']}")
            print(f"     Tags:  {tags}")
            notes_preview = (item.get("notes") or "")[:120].replace("\n", " ")
            print(f"     Text:  {notes_preview}...")
            print()
        return

    limit = args.limit if args.limit > 0 else MAX_FILES_PER_RUN

    log("🚀 CIS Batch Ingestion Pipeline Started")
    log(f"    Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")

    files = step_scan(dry_run=args.dry_run, source=args.source, limit=limit)
    if not files:
        log("No new files to process.")
        return

    files = step_extract(files, dry_run=args.dry_run)
    files = step_analyze(files, dry_run=args.dry_run)
    files = step_write(files, dry_run=args.dry_run)

    log("\n✅ Pipeline complete!")
    if not args.dry_run:
        log(f"   {len(files)} assets created in 'draft' status — use --review to see them")
        log(f"   Visit the Review Queue in the UI to approve/reject/edit each one")


if __name__ == "__main__":
    main()
