"""
config.py — CIS path constants and shared configuration.
All other modules import from here. Change paths in one place only.
"""

from pathlib import Path

# ── Root paths ─────────────────────────────────────────────────────────────────
PROJECTS_ROOT = Path("/mnt/projects/cis")
RECORDS_ROOT  = PROJECTS_ROOT / "knowledge" / "records"
INGEST_ROOT   = PROJECTS_ROOT / "ingest" / "processing"
PROJECTS_DIR  = PROJECTS_ROOT / "projects"
DB_PATH       = PROJECTS_ROOT / "memory" / "cis_memory.db"
RUNTIME_DIR   = PROJECTS_ROOT / "runtime"
HARNESS_PATH  = PROJECTS_ROOT / "memory" / "cis_harness.py"
VAULT_DIR     = PROJECTS_ROOT / "docs" / "CIS_Creative_Intelligence_System_v1"
LIVE_PATH     = PROJECTS_ROOT / "CIS_LIVE.md"

# ── External commands ──────────────────────────────────────────────────────────
EXTRACT_CMD = (
    "PYTORCH_ALLOC_CONF=expandable_segments:True "
    "/home/eric/gpu-test/bin/python3 "
    "/mnt/projects/cis/runtime/cis_extract.py"
)

# ── Domain constants ───────────────────────────────────────────────────────────
WIAS_STAGES = ["word", "image", "action", "sound", "web"]
