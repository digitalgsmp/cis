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

# ── Log paths ──────────────────────────────────────────────────────────────────
LOG_DIR       = PROJECTS_ROOT / "logs"

# ── Manifest class authorities ─────────────────────────────────────────────────
# Three distinct manifest concepts exist in CIS. Do not use the bare word
# "manifest" in new code. Reference the named constant for the correct class.
#
# VERIFICATION_MANIFEST_DIR
#   What:       Session L1/L2 verification run records
#   Written by: cis_verify.py, queue_worker.py
#   Lifecycle:  Retained per session for audit trail
#   Status:     ACTIVE — canonical drop location
VERIFICATION_MANIFEST_DIR = PROJECTS_ROOT / "logs" / "manifests"
#
# RUNTIME_MANIFEST_DIR
#   What:    Manifests folder inside /runtime — origin pre-ADR-033
#   Status:  GOVERNANCE QUESTION — do not write new files here
#   Blocked: ADR-047 Filesystem Governance and Canonicality
#            Must resolve: ownership, lifecycle, retention, deprecation
RUNTIME_MANIFEST_DIR = RUNTIME_DIR / "manifests"
#
# SOURCE_MANIFEST_NAME
#   What:       Per-source processing manifest filename
#   Path:       INGEST_ROOT / source_id / SOURCE_MANIFEST_NAME
#   Written by: pipeline.py
#   Status:     ACTIVE
SOURCE_MANIFEST_NAME = "manifest.json"

# ── External commands ──────────────────────────────────────────────────────────
EXTRACT_CMD = (
    "PYTORCH_ALLOC_CONF=expandable_segments:True "
    "/home/eric/gpu-test/bin/python3 "
    "/mnt/projects/cis/runtime/cis_extract.py"
)

# ── Domain constants ───────────────────────────────────────────────────────────
WIAS_STAGES = ["word", "image", "action", "sound", "web"]

# ── Draft Intake Layer (ADR-048) ───────────────────────────────────────────────
# Filesystem paths for the staged draft intake pipeline.
# Separate from INGEST_ROOT — that pipeline is for raw creative material.
# This pipeline is for AI-proposed structured drafts awaiting human approval.
#
# Trust zone map:
#   Downloads (untrusted) → DRAFT_INBOX_DIR (quarantine)
#   → DRAFT_STAGING_DIR (reviewed candidate, future Phase 3)
#   → canonical DB/files (approved truth, human-gated)
DOWNLOADS_WATCH_DIR = Path("/home/eric/Downloads/CIS_intake")
DRAFT_INBOX_DIR     = PROJECTS_ROOT / "drafts" / "inbox"
DRAFT_STAGING_DIR   = PROJECTS_ROOT / "drafts" / "staging"
