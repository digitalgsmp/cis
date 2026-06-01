#!/usr/bin/env python3
"""
ingest_extractions.py — Parse extraction analysis files into knowledge_spines + spine_nodes.

Handles three sub-formats seen across 1,536 CIS + SWA extraction files:
  Format A — bullet-style discoveries with **Affected Layers:** etc. as inline bold
  Format B — heading-style discoveries with ### Discovery N + separate field headings
  Format C — ### Discovery N with inline bullet style (common in SWA)

Usage:
    python3 ingest_extractions.py                   # CIS only
    python3 ingest_extractions.py --all              # CIS + SWA
    python3 ingest_extractions.py --project swa      # SWA only
    python3 ingest_extractions.py --dry-run --all    # Preview without writing
"""

import re
import sys
import json
import os
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

DB_PATH = Path(os.environ.get("CIS_DB_PATH", "/mnt/projects/cis/memory/cis_memory.db"))

CIS_EXTRACTIONS = Path("/mnt/projects/cis/cis_kernel/extraction/functional_intents/")
SWA_EXTRACTIONS = Path("/mnt/projects/social_work_ai/swa_kernel/extraction/functional_intents/")

# ── Regex patterns ─────────────────────────────────────────────────────────────

RE_HEADER_META = re.compile(
    r'\*\*Source:\*\*\s*`([^`]+)`\s*\n'
    r'\*\*Group:\*\*\s*(\S+)',
    re.MULTILINE
)
RE_HEADER_EXTRACTED = re.compile(r'\*\*Extracted:\*\*\s*([\d-]+\s*[\d:]*)')
RE_HEADER_MODEL = re.compile(r'\*\*Model:\*\*\s*(\S+)')

# Discovery patterns
RE_DISCOVERY_HEADING = re.compile(r'#{1,6}\s+Discovery\s+(\d+)', re.IGNORECASE)

# Field extraction for bullet-style discoveries
RE_BULLET_FIELDS = {
    'architectural_significance': re.compile(r'\*\*Architectural Significance\*\*:?\s*(.+?)(?:\n\s*\*\*|\Z)', re.DOTALL),
    'affected_layers': re.compile(r'\*\*Affected Layers?\*\*:?\s*(.+?)(?:\n\s*\*\*|\Z)', re.DOTALL),
    'dependency_impact': re.compile(r'\*\*Dependency Impact\*\*:?\s*(.+?)(?:\n\s*\*\*|\Z)', re.DOTALL),
    'build_impact': re.compile(r'\*\*Build Impact\*\*:?\s*(.+?)(?:\n\s*\*\*|\Z)', re.DOTALL),
    'runtime_impact': re.compile(r'\*\*Runtime Impact\*\*:?\s*(.+?)(?:\n\s*\*\*|\Z)', re.DOTALL),
}

def slugify(text):
    """Create a URL-safe ID from text."""
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'\s+', '-', s)
    return s[:80]

def parse_extraction_file(filepath):
    """Parse a single extraction file, return dict of spine data."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    filename = filepath.name

    # ── Parse header metadata ─────────────────────────────────────────────
    meta = {'source_path': str(filepath), 'filename': filename}

    m = RE_HEADER_META.search(content)
    if m:
        meta['source'] = m.group(1)
        meta['group'] = m.group(2)

    m = RE_HEADER_EXTRACTED.search(content)
    if m:
        meta['extracted'] = m.group(1).strip()

    m = RE_HEADER_MODEL.search(content)
    if m:
        meta['model'] = m.group(1)

    # Determine project
    if 'cis' in str(filepath).lower():
        meta['project'] = 'cis'
    elif 'social_work_ai' in str(filepath).lower() or 'swa' in str(filepath).lower():
        meta['project'] = 'swa'
    else:
        meta['project'] = 'unknown'

    # Extract title from first # heading
    title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    meta['title'] = title_match.group(1).strip() if title_match else filename

    # ── Parse discoveries ────────────────────────────────────────────────
    discoveries = []
    current_discovery = None
    current_num = 0

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for discovery heading
        dm = RE_DISCOVERY_HEADING.search(line)
        if dm:
            if current_discovery:
                discoveries.append(current_discovery)
            current_num = int(dm.group(1))
            current_discovery = {
                'number': current_num,
                'title': '',
                'architectural_significance': '',
                'affected_layers': '',
                'dependency_impact': '',
                'build_impact': '',
                'runtime_impact': '',
                'raw_lines': []
            }
            # Extract inline title after "Discovery N:"
            title_part = re.sub(r'^#{1,6}\s+Discovery\s+\d+\s*[:–—-]\s*', '', line, flags=re.IGNORECASE)
            if title_part == line:
                title_part = re.sub(r'^#{1,6}\s+Discovery\s+\d+\s*', '', line, flags=re.IGNORECASE)
            current_discovery['title'] = title_part.strip()
            i += 1
            continue

        if current_discovery:
            # Collect raw text for field extraction
            current_discovery['raw_lines'].append(line)
        i += 1

    if current_discovery:
        discoveries.append(current_discovery)

    # If no discoveries found via headings, try bullet-style
    if not discoveries:
        discoveries = _parse_bullet_style(content)

    # For each discovery, extract fields from raw text
    for disc in discoveries:
        raw = '\n'.join(disc.get('raw_lines', []))
        for field, pattern in RE_BULLET_FIELDS.items():
            m = pattern.search(raw)
            if m:
                disc[field] = m.group(1).strip()

    return {
        'meta': meta,
        'discoveries': discoveries,
        'raw_content': content,
    }

def _parse_bullet_style(content):
    """Fallback: parse discoveries from bullet-style format (no ### headings)."""
    discoveries = []
    # Look for "## Discovery N:" or "### Discovery N:" patterns
    pattern = re.compile(r'#{1,6}\s*Discovery\s+(\d+)\s*[:–—-]?\s*(.*?)(?=\n\s*(?:#{1,6}\s*Discovery\s+\d+|#{1,6}\s*\d+\.\s*(?:CORE|FUNCTIONAL|ARCHITECTURAL)|$))', re.DOTALL | re.IGNORECASE)
    for m in pattern.finditer(content):
        num = int(m.group(1))
        title_line = m.group(2).strip()
        body = m.group(0)
        # Extract title (first sentence or line)
        title = title_line.split('\n')[0].strip().rstrip(':')
        if not title:
            title_match = re.search(r'\*\*([^*]+)\*\*', body)
            title = title_match.group(1) if title_match else f'Discovery {num}'
        disc = {
            'number': num,
            'title': title,
            'architectural_significance': '',
            'affected_layers': '',
            'dependency_impact': '',
            'build_impact': '',
            'runtime_impact': '',
            'raw_lines': body.split('\n'),
        }
        discoveries.append(disc)
    return discoveries

def generate_node_id(spine_id, disc_num):
    return f"{spine_id}--d{disc_num:04d}"

def insert_spine(db, spine_data):
    """Insert a knowledge_spine and its spine_nodes into the database."""
    meta = spine_data['meta']
    discoveries = spine_data['discoveries']

    spine_id = str(uuid.uuid4())[:12]
    domain = meta.get('project', 'unknown')
    sub_domain = meta.get('group', 'unknown')
    subject = meta.get('title', meta['filename'])
    source_type = 'extraction_analysis'
    file_path = meta.get('source_path', '')
    node_count = len(discoveries)

    db.execute("""
        INSERT OR IGNORE INTO knowledge_spines
            (spine_id, domain, sub_domain, subject, source_type, file_path, node_count, status, ingested_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'ingested', datetime('now'), datetime('now'))
    """, (spine_id, domain, sub_domain, subject, source_type, file_path, node_count))

    # Insert spine_nodes
    prev_node_id = None
    for i, disc in enumerate(discoveries):
        node_id = generate_node_id(spine_id, disc['number'])
        title = disc.get('title', f'Discovery {disc.get("number", i+1)}')
        depth = 1
        path = f"/{domain}/{sub_domain}/{spine_id}/{disc['number']}"

        # Build a richer node payload
        payload = json.dumps({
            'architectural_significance': disc.get('architectural_significance', ''),
            'affected_layers': disc.get('affected_layers', ''),
            'dependency_impact': disc.get('dependency_impact', ''),
            'build_impact': disc.get('build_impact', ''),
            'runtime_impact': disc.get('runtime_impact', ''),
            'source_file': meta.get('filename', ''),
            'source_path': meta.get('source_path', ''),
            'extraction_date': meta.get('extracted', ''),
        })

        db.execute("""
            INSERT OR IGNORE INTO spine_nodes
                (node_id, spine_id, parent_node_id, title, depth, path, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'generated', datetime('now'))
        """, (node_id, spine_id, prev_node_id, title, depth, path))

        prev_node_id = node_id

    return spine_id, len(discoveries)


def run_ingestion(project_dir, project_name, dry_run=False):
    """Ingest all extraction files from a project directory."""
    if not project_dir.exists():
        print(f"  [SKIP] Directory not found: {project_dir}")
        return 0, 0

    files = sorted(project_dir.glob("*_extraction_analysis.md"))
    print(f"\n{'='*60}")
    print(f"  {project_name.upper()} — {len(files)} extraction files")
    print(f"{'='*60}")

    total_spines = 0
    total_nodes = 0
    errors = []

    db = None if dry_run else sqlite3.connect(str(DB_PATH))

    for fpath in files:
        try:
            data = parse_extraction_file(fpath)
            if dry_run:
                disc_count = len(data['discoveries'])
                total_spines += 1
                total_nodes += disc_count
                title = data['meta'].get('title', fpath.name)
                print(f"  [DRY] {fpath.name} → {disc_count} discoveries")
                continue

            spine_id, node_count = insert_spine(db, data)
            total_spines += 1
            total_nodes += node_count
            print(f"  [OK]  {fpath.name} → {node_count} nodes (spine: {spine_id})")
        except Exception as e:
            errors.append((fpath.name, str(e)))
            print(f"  [ERR] {fpath.name}: {e}")

    if not dry_run and db:
        db.commit()
        db.close()

    print(f"\n  Results: {total_spines} spines, {total_nodes} nodes")
    if errors:
        print(f"  Errors: {len(errors)}")
        for name, err in errors[:5]:
            print(f"    - {name}: {err}")
        if len(errors) > 5:
            print(f"    ... and {len(errors)-5} more")

    return total_spines, total_nodes


if __name__ == "__main__":
    dry_run = '--dry-run' in sys.argv
    all_projects = '--all' in sys.argv
    single_project = None

    for arg in sys.argv[1:]:
        if arg.startswith('--project='):
            single_project = arg.split('=', 1)[1]
        elif arg == '--project' and len(sys.argv) > sys.argv.index(arg) + 1:
            idx = sys.argv.index(arg)
            single_project = sys.argv[idx + 1]

    print(f"Extraction Ingestion Pipeline")
    print(f"{'='*60}")
    print(f"DB:     {DB_PATH}")
    print(f"Mode:   {'DRY RUN' if dry_run else 'LIVE'}")

    total_s, total_n = 0, 0

    if all_projects or single_project is None or single_project == 'cis':
        s, n = run_ingestion(CIS_EXTRACTIONS, 'CIS', dry_run=dry_run)
        total_s += s
        total_n += n

    if all_projects or single_project == 'swa':
        s, n = run_ingestion(SWA_EXTRACTIONS, 'SWA', dry_run=dry_run)
        total_s += s
        total_n += n

    print(f"\n{'='*60}")
    print(f"  TOTAL: {total_s} spines, {total_n} nodes")
    if dry_run:
        print(f"  (dry run — no data written)")
    print(f"{'='*60}")
