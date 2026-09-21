#!/usr/bin/env python3
"""
generate_all.py — Tier 5.5
Orchestrates AGENTS.md, HCP, and DEV-PIVOT manifest generation with a shared run ID.
Produces a hash manifest at runtime/manifests/EXPORT_MANIFEST.json.

Usage: python3 tools/export/generate_all.py [--db PATH] [--skip-agents] [--skip-hcp]
"""

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "data" / "cis_memory.db"
MANIFEST_PATH = REPO_ROOT / "runtime" / "manifests" / "EXPORT_MANIFEST.json"

sys.path.insert(0, str(REPO_ROOT / "tools" / "state"))
import canonical_state  # noqa: E402

GENERATE_AGENTS = REPO_ROOT / "tools" / "export" / "generate_agents_md.py"
GENERATE_HCP = REPO_ROOT / "tools" / "export" / "generate_hcp.py"
GENERATE_DEV_PIVOT = REPO_ROOT / "tools" / "export" / "generate_dev_pivot_manifest.py"
AGENTS_CONFIG = REPO_ROOT / "config" / "agents_static.yaml"
HCP_CONFIG = REPO_ROOT / "config" / "hcp_static.yaml"

AGENTS_OUT = REPO_ROOT / "AGENTS.md"
HCP_OUT_DIR = REPO_ROOT / "PROJECT_CONTEXT_PACK_UPLOAD"
DEV_PIVOT_OUT = REPO_ROOT / "docs" / "DEV-PIVOT_STATUS.md"

HCP_FILES = [
    "READ_FIRST_HERMES_CONTEXT.md",
    "HCP_00_README_START_HERE.md",
    "HCP_01_CURRENT_STATE.md",
    "HCP_02_ACTIVE_ARCHITECTURE.md",
    "HCP_03_DECISIONS_LOG.md",
    "HCP_04_OPEN_QUESTIONS.md",
    "HCP_05_NEXT_ACTIONS.md",
    "HCP_06_MODEL_ROLES_AND_PROTOCOL.md",
    "HCP_07_RECENT_HANDOFF.md",
    "HCP_08_FILES_CHANGED_RECENTLY.md",
    "HCP_09_TERMS_AND_NAMING.md",
]


def generate_run_id():
    """Generate a unique pipeline run ID: run-<12 hex chars>"""
    return "run-" + uuid.uuid4().hex[:12]


def get_git_head(repo_root):
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=repo_root, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def sha256_file(path):
    """Return hex SHA256 digest of file content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def file_stats(path):
    """Return (size_bytes, char_count, line_count) for a text file."""
    content = Path(path).read_text()
    return len(content.encode("utf-8")), len(content), content.count("\n") + (1 if content and not content.endswith("\n") else 0)


def run_generator(command, label):
    """Run a generator subprocess. Return (success_bool, stdout_text)."""
    print(f"[generate_all] Running: {' '.join(command)}")
    try:
        r = subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=REPO_ROOT)
        stdout = r.stdout.strip()
        stderr = r.stderr.strip()
        if r.returncode != 0:
            print(f"[generate_all] ERROR: {label} exited with code {r.returncode}")
            if stderr:
                print(f"[generate_all] stderr: {stderr}")
            if stdout:
                print(f"[generate_all] stdout: {stdout}")
            return False, stdout
        if stderr:
            print(f"[generate_all] {label} stderr: {stderr}")
        print(f"[generate_all] {label}: {stdout.split(chr(10))[-1] if stdout else 'OK'}")
        return True, stdout
    except Exception as e:
        print(f"[generate_all] ERROR: {label} failed: {e}")
        return False, ""


def get_state_revision(db_path):
    """The canonical state revision (CARD_01_SINGLE_AUTHORITY_CONTRACT.md,
    queue 4.29) this run's artifacts were generated against. Lets a caller
    compare a stored manifest's state_revision to a freshly-computed one
    (canonical_state.compute_state_revision) to detect staleness relative
    to the DB, not just relative to this manifest's own git_head/run_id."""
    conn = sqlite3.connect(db_path)
    try:
        return canonical_state.compute_state_revision(conn)
    finally:
        conn.close()


def build_manifest(run_id, artifacts, git_head, db_path, state_revision):
    """Construct the export manifest dict."""
    return {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": git_head,
        "state_revision": state_revision,
        "generator": "tools/export/generate_all.py",
        "db_path": str(db_path),
        "source_configs": [
            "config/agents_static.yaml",
            "config/hcp_static.yaml",
        ],
        "commands": [
            f"python3 tools/export/generate_agents_md.py --run-id {run_id}",
            f"python3 tools/export/generate_hcp.py --run-id {run_id}",
            f"python3 tools/export/generate_dev_pivot_manifest.py --run-id {run_id}",
        ],
        "artifacts": artifacts,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate AGENTS.md + HCP + DEV-PIVOT files with manifest")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--skip-agents", action="store_true", help="Skip AGENTS.md generation")
    parser.add_argument("--skip-hcp", action="store_true", help="Skip HCP generation")
    args = parser.parse_args()

    db_path = args.db
    if not Path(db_path).exists():
        print(f"ERROR: DB not found: {db_path}", file=sys.stderr)
        sys.exit(2)

    run_id = generate_run_id()
    git_head = get_git_head(REPO_ROOT)
    print(f"[generate_all] Run ID: {run_id}")
    print(f"[generate_all] Git HEAD: {git_head}")
    print(f"[generate_all] DB: {db_path}")

    # ── Step 1: Generate AGENTS.md ──
    agents_ok = True
    if not args.skip_agents:
        cmd = [
            "python3", str(GENERATE_AGENTS),
            "--db", db_path,
            "--config", str(AGENTS_CONFIG),
            "--out", str(AGENTS_OUT),
            "--run-id", run_id,
        ]
        agents_ok, _ = run_generator(cmd, "generate_agents_md.py")
        if not agents_ok:
            print("[generate_all] ABORT: generate_agents_md.py failed. Not writing manifest.")
            sys.exit(1)
    else:
        print("[generate_all] Skipping AGENTS.md generation (--skip-agents)")

    # ── Step 2: Generate HCP files ──
    hcp_ok = True
    if not args.skip_hcp:
        cmd = [
            "python3", str(GENERATE_HCP),
            "--db", db_path,
            "--hcp-config", str(HCP_CONFIG),
            "--agents-config", str(AGENTS_CONFIG),
            "--out-dir", str(HCP_OUT_DIR),
            "--run-id", run_id,
        ]
        hcp_ok, _ = run_generator(cmd, "generate_hcp.py")
        if not hcp_ok:
            print("[generate_all] ABORT: generate_hcp.py failed. Not writing manifest.")
            sys.exit(1)
    else:
        print("[generate_all] Skipping HCP generation (--skip-hcp)")

    # ── Step 3: Generate DEV-PIVOT manifest ──
    cmd = [
        "python3", str(GENERATE_DEV_PIVOT),
        "--db", db_path,
        "--out", str(DEV_PIVOT_OUT),
        "--run-id", run_id,
    ]
    dev_pivot_ok, _ = run_generator(cmd, "generate_dev_pivot_manifest.py")
    if not dev_pivot_ok:
        print("[generate_all] WARNING: generate_dev_pivot_manifest.py failed. Continuing.")

    # ── Step 4: Build manifest ──
    artifacts = []

    # AGENTS.md
    if not args.skip_agents:
        size, chars, lines = file_stats(AGENTS_OUT)
        sha = sha256_file(AGENTS_OUT)
        artifacts.append({
            "path": "AGENTS.md",
            "type": "agents_context",
            "generator": "tools/export/generate_agents_md.py",
            "sha256": sha,
            "size_bytes": size,
            "char_count": chars,
            "line_count": lines,
        })

    # HCP files
    if not args.skip_hcp:
        for fname in HCP_FILES:
            fpath = HCP_OUT_DIR / fname
            if not fpath.exists():
                print(f"[generate_all] WARNING: Expected HCP file not found: {fpath}")
                continue
            size, chars, lines = file_stats(fpath)
            sha = sha256_file(fpath)
            artifacts.append({
                "path": f"PROJECT_CONTEXT_PACK_UPLOAD/{fname}",
                "type": "hcp_context",
                "generator": "tools/export/generate_hcp.py",
                "sha256": sha,
                "size_bytes": size,
                "char_count": chars,
                "line_count": lines,
            })

    # DEV-PIVOT manifest
    if DEV_PIVOT_OUT.exists():
        size, chars, lines = file_stats(DEV_PIVOT_OUT)
        sha = sha256_file(DEV_PIVOT_OUT)
        artifacts.append({
            "path": "docs/DEV-PIVOT_STATUS.md",
            "type": "dev_pivot_manifest",
            "generator": "tools/export/generate_dev_pivot_manifest.py",
            "sha256": sha,
            "size_bytes": size,
            "char_count": chars,
            "line_count": lines,
        })

    state_revision = get_state_revision(db_path)
    manifest = build_manifest(run_id, artifacts, git_head, db_path, state_revision)

    # ── Step 5: Write manifest ──
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"[generate_all] Manifest written: {MANIFEST_PATH}")
    print(f"[generate_all] Artifacts: {len(artifacts)}")
    print(f"[generate_all] PASS — Run {run_id} complete.")


if __name__ == "__main__":
    main()
