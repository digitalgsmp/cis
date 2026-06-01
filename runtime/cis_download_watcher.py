#!/usr/bin/env python3
"""
cis_download_watcher.py — ADR-048 Phase 2: Downloads → Inbox Automation
Watches ~/Downloads for new files and stages them into the CIS draft intake
buffer via /api/drafts/stage. Eliminates manual operator transport step.

Authority: /mnt/projects/cis/runtime/cis_download_watcher.py
Config:    DOWNLOADS_WATCH_DIR, DRAFT_INBOX_DIR defined in config.py
API:       POST /api/drafts/stage
ADR:       ADR-048 Staged Draft Intake Layer — Phase 2

Usage:
    python3 cis_download_watcher.py [--once] [--dry-run]

Flags:
    --once      Process existing files in Downloads and exit (no watch loop)
    --dry-run   Log what would happen without moving files or calling API

Governance:
    - Files are moved to DRAFT_INBOX_DIR before API call
    - If API call fails, file remains in inbox with .cis_stage_failed marker
    - Operator retains full approval authority — watcher only stages to inbox
    - No file is promoted beyond inbox without human action in the dashboard
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ── Add runtime to path for config import ─────────────────────────────────────
RUNTIME_DIR = Path("/mnt/projects/cis/runtime")
sys.path.insert(0, str(RUNTIME_DIR))

try:
    from config import DOWNLOADS_WATCH_DIR, DRAFT_INBOX_DIR
except ImportError as e:
    print(f"FAIL — Could not import config: {e}")
    print("Ensure DOWNLOADS_WATCH_DIR and DRAFT_INBOX_DIR are defined in config.py")
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────
API_URL          = "http://127.0.0.1:5000/api/drafts/stage"
POLL_INTERVAL    = 5          # seconds between scans in watch mode
MARKER_SUFFIX    = ".cis_staged"
FAIL_SUFFIX      = ".cis_stage_failed"
SKIP_SUFFIX      = ".cis_skip"
LOG_PATH         = Path("/mnt/projects/cis/logs/cis_download_watcher.log")

# File extensions that are candidates for staging
WATCHED_EXTENSIONS = {
    ".md", ".txt", ".json", ".py", ".html", ".csv", ".yaml", ".yml"
}

# Filenames to always ignore regardless of extension
IGNORE_NAMES = {
    ".DS_Store", "desktop.ini", "Thumbs.db"
}

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHER] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_draft_type(path: Path):
    """
    Infer ADR-048 draft_type from filename and extension.
    Falls back to 'raw_file' for unrecognized patterns.
    """
    name = path.name.lower()
    if "adr" in name:
        return "adr"
    if "session" in name or "handoff" in name:
        return "session_field"
    if "conflict" in name:
        return "conflict"
    if "primer" in name or "_update_draft" in name:
        return "primer_update"
    if "contract" in name:
        return "contract"
    if "knowledge" in name or "record" in name:
        return "knowledge_record"
    log.info(f"Skipping unrecognized draft type: {path.name}")
    return None


def stage_via_api(path: Path, dry_run: bool = False) -> bool:
    """
    Read file, build payload, POST to /api/drafts/stage.
    Returns True on success, False on failure.
    """
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        log.error(f"Could not read {path.name}: {e}")
        return False

    draft_type = infer_draft_type(path)
    if draft_type is None:
        return False
    payload = {
        "draft_type":     draft_type,
        "payload_format": "markdown" if path.suffix == ".md" else "text",
        "schema_version": "1.0",
        "source_model":   "human",
        "source_session": None,
        "filename":       path.name,
        "payload":        content,
        "notes":          f"Auto-staged from Downloads by cis_download_watcher.py"
    }

    if dry_run:
        log.info(f"[DRY-RUN] Would stage: {path.name} as draft_type={draft_type}")
        return True

    try:
        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            API_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            draft_id = body.get("draft_id") or body.get("existing_draft_id")
            log.info(f"STAGED: {path.name} → draft_id={draft_id} type={draft_type}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        log.error(f"API HTTP {e.code} for {path.name}: {body}")
        return False
    except Exception as e:
        log.error(f"API call failed for {path.name}: {e}")
        return False


def process_file(src: Path, dry_run: bool = False) -> None:
    """
    Move file from Downloads to inbox, then stage via API.
    Marks file with .cis_staged or .cis_stage_failed in inbox.
    """
    # Skip hidden files, ignored names, already-marked files
    if src.name.startswith("."):
        return
    if src.name in IGNORE_NAMES:
        return
    if src.suffix in {MARKER_SUFFIX, FAIL_SUFFIX, SKIP_SUFFIX}:
        return
    if src.suffix not in WATCHED_EXTENSIONS:
        log.debug(f"Skipping unsupported extension: {src.name}")
        return

    # Skip if already processed (marker file exists in inbox)
    marker = DRAFT_INBOX_DIR / (src.name + MARKER_SUFFIX)
    fail_marker = DRAFT_INBOX_DIR / (src.name + FAIL_SUFFIX)
    if marker.exists() or fail_marker.exists():
        return

    dest = DRAFT_INBOX_DIR / src.name

    # Handle filename collision in inbox
    if dest.exists():
        checksum_src  = sha256_file(src)
        checksum_dest = sha256_file(dest)
        if checksum_src == checksum_dest:
            log.info(f"Identical file already in inbox, skipping: {src.name}")
            return
        # Different content — rename with timestamp
        ts   = int(time.time())
        dest = DRAFT_INBOX_DIR / f"{src.stem}_{ts}{src.suffix}"

    if dry_run:
        log.info(f"[DRY-RUN] Would move: {src.name} → {dest}")
        stage_via_api(src, dry_run=True)
        return

    try:
        shutil.move(str(src), str(dest))
        log.info(f"MOVED: {src.name} → inbox/{dest.name}")
    except Exception as e:
        log.error(f"Could not move {src.name}: {e}")
        return

    success = stage_via_api(dest, dry_run=False)

    # Write marker
    if success:
        marker.touch()
    else:
        fail_marker.touch()
        log.warning(f"Stage failed — file retained in inbox: {dest.name}")


def scan_downloads(dry_run: bool = False) -> int:
    """Scan Downloads directory and process eligible files. Returns count processed."""
    count = 0
    for item in sorted(DOWNLOADS_WATCH_DIR.iterdir()):
        if item.is_file():
            process_file(item, dry_run=dry_run)
            count += 1
    return count


def watch_loop(dry_run: bool = False) -> None:
    """Continuous watch loop. Scans every POLL_INTERVAL seconds."""
    log.info(f"Watch loop started — scanning {DOWNLOADS_WATCH_DIR} every {POLL_INTERVAL}s")
    log.info(f"Inbox: {DRAFT_INBOX_DIR}")
    log.info(f"API:   {API_URL}")
    if dry_run:
        log.info("[DRY-RUN MODE — no files moved, no API calls]")
    try:
        while True:
            scan_downloads(dry_run=dry_run)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log.info("Watcher stopped by operator.")


def main():
    parser = argparse.ArgumentParser(
        description="CIS Download Watcher — ADR-048 Phase 2"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process existing Downloads files and exit (no watch loop)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without moving files or calling API"
    )
    args = parser.parse_args()

    # Ensure inbox exists
    DRAFT_INBOX_DIR.mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info("CIS Download Watcher — ADR-048 Phase 2")
    log.info(f"Watch dir: {DOWNLOADS_WATCH_DIR}")
    log.info(f"Inbox:     {DRAFT_INBOX_DIR}")
    log.info("=" * 60)

    if args.once:
        count = scan_downloads(dry_run=args.dry_run)
        log.info(f"--once complete. Files scanned: {count}")
    else:
        watch_loop(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
