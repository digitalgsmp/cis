#!/usr/bin/env python3
"""
ingest_extractions.py — Parse extraction analysis files into knowledge_spines + spine_nodes.

Scans both CIS and SWA extraction directories, parses each file's metadata header
and numbered architectural discoveries, then inserts into the CIS database.

Usage:
    python3 ingest_extractions.py                         # ingest everything
    python3 ingest_extractions.py --project cis           # CIS only
    python3 ingest_extractions.py --project swa           # SWA only
    python3 ingest_extractions.py --dry-run               # show what would be inserted
    python3 ingest_extractions.py --sample 5              # test with N files per project
"""

import os
import re
import sys
import sqlite3
import argparse
import uuid
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECTS_DIR = Path("/mnt/projects")
CIS_EXT_DIR = PROJECTS_DIR / "cis" / "cis_kernel" / "extraction" / "functional_intents"
SWA_EXT_DIR = PROJECTS_DIR / "social_work_ai" / "swa_kernel" / "extraction" / "functional_intents"
DB_PATH = PROJECTS_DIR / "cis" / "memory" / "cis_memory.db"

# ── Section name mapping ───────────────────────────────────────────────────
# Order matters — section 1 = CORE ARCHITECTURAL DISCOVERIES, etc.
SECTION_NAMES = {
    1: "CORE_ARCHITECTURAL_DISCOVERIES",
    2: "TOPOLOGY_MUTATIONS",
    3: "DEPENDENCY_DISCOVERIES",
    4: "EXECUTION_LAYER_IMPLICATIONS",
    5: "GOVERNANCE_VALIDATION_IMPLICATIONS",
    6: "KNOWLEDGE_LAYER_IMPLICATIONS",
    7: "APPLICATION_LAYER_IMPLICATIONS",
    8: "FEEDBACK_LOOP_DISCOVERIES",
    9: "UNRESOLVED_GAPS_MISSING_LAYERS",
    10: "BUILD_PLAN_IMPLICATIONS",
    11: "EXTRACTED_CANONICAL_OBJECTS",
    12: "ARCHITECTURAL_DELTA_SUMMARY",
}

SECTION_PATTERN = re.compile(
    r'^#{1,2}\s+(\d+)\.\s+(CORE ARCHITECTURAL|TOPOLOGY|DEPENDENCY|'
    r'EXECUTION-LAYER|GOVERNANCE|KNOWLEDGE-LAYER|APPLICATION-LAYER|'
    r'FEEDBACK|UNRESOLVED|BUILD-PLAN|EXTRACTED|ARCHITECTURAL)',
    re.IGNORECASE | re.MULTILINE
)

DISCOVERY_PATTERN = re.compile(
    r'^#{2,3}\s+Discovery\s+(\d+):\s*(.+?)$',
    re.IGNORECASE | re.MULTILINE
)

# ── Metadata regex ─────────────────────────────────────────────────────────
# Handles both **Key:** value and **Key**: value
META_PATTERN = re.compile(r'^\*\*(.+?)\*\*:?\s*(.+)$', re.MULTILINE)

# ── Discovery field regex ─────────────────────────────────────────────────
FIELD_PATTERN = re.compile(
    r'^\-\s+\*\*([^*]+)\*\*:?\s*(.+)$',
    re.MULTILINE
)


def get_project_from_path(filepath):
    """Determine which project an extraction file belongs to."""
    path = str(filepath)
    if "/cis/" in path:
        return "cis"
    elif "/social_work_ai/" in path:
        return "swa"
    return "unknown"


def parse_extraction(filepath):
    """
    Parse a single extraction analysis file.
    
    Returns dict with:
      - metadata: dict of header fields
      - discoveries: list of {number, title, fields}
      - sections: list of {number, name, content}
      - source_filename: original filename from metadata
      - project: cis or swa
    """
    text = filepath.read_text(encoding="utf-8", errors="replace")
    result = {
        "filepath": str(filepath),
        "filename": filepath.name,
        "project": get_project_from_path(filepath),
        "metadata": {},
        "discoveries": [],
        "sections": [],
    }

    # ── Parse metadata header ──────────────────────────────────────────────
    # The metadata header is bounded by the first `---\n` separator
    # We look at lines before the first or second ---
    dash_positions = []
    idx = 0
    while True:
        dash_pos = text.find("\n---\n", idx)
        if dash_pos == -1:
            break
        dash_positions.append(dash_pos)
        idx = dash_pos + 5
        if len(dash_positions) >= 2:
            break

    if dash_positions:
        header_area = text[:dash_positions[0]]
    else:
        header_area = text[:min(len(text), 3000)]

    for match in META_PATTERN.finditer(header_area):
        key = match.group(1).strip().lower().replace(" ", "_").rstrip(":")
        val = match.group(2).strip().strip('`').strip()
        result["metadata"][key] = val

    # Also check between first and second dashes if first one was minimal
    if len(dash_positions) >= 2:
        second_header = text[dash_positions[0]:dash_positions[1]]
        for match in META_PATTERN.finditer(second_header):
            key = match.group(1).strip().lower().replace(" ", "_").rstrip(":")
            val = match.group(2).strip().strip('`').strip()
            if key not in result["metadata"]:
                result["metadata"][key] = val

    # ── Find section boundaries ────────────────────────────────────────────
    # First, identify fenced code block ranges (```) to exclude from section detection
    lines = text.split("\n")
    code_block_ranges = []
    code_open = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            if code_open is None:
                code_open = i
            else:
                code_block_ranges.append((code_open, i))
                code_open = None
    # Handle unclosed code blocks (file ends inside a fenced block)
    if code_open is not None:
        code_block_ranges.append((code_open, len(lines) - 1))

    def in_code_block(lineno):
        for start, end in code_block_ranges:
            if start <= lineno <= end:
                return True
        return False

    section_markers = []
    for i, line in enumerate(lines):
        if in_code_block(i):
            continue
        m = SECTION_PATTERN.match(line)
        if m:
            section_num = int(m.group(1))
            heading_text = line.strip().lstrip("#").strip()
            section_markers.append((i, section_num, heading_text))

    # ── Extract section content ────────────────────────────────────────────
    for idx, (start_line, sec_num, heading) in enumerate(section_markers):
        end_line = len(lines)
        if idx + 1 < len(section_markers):
            end_line = section_markers[idx + 1][0]

        section_content = "\n".join(lines[start_line:end_line]).strip()
        result["sections"].append({
            "number": sec_num,
            "name": SECTION_NAMES.get(sec_num, f"SECTION_{sec_num}"),
            "heading": heading,
            "content": section_content,
        })

    # ── Extract discoveries ────────────────────────────────────────────────
    # Process sections 1-9 only (skip 10=Build Plan, 11=Canonical Objects,
    # 12=Delta Summary which often contains downloadable artifact) to avoid
    # duplicates from embedded code-block copies.
    for section in result["sections"]:
        if section["number"] > 9:
            continue
        section_body = section["content"]

        # Strip fenced code blocks from section content before discovery parsing
        cleaned_body = re.sub(
            r'^```[\w\-]*\n.*?^```',
            '',
            section_body,
            count=0,
            flags=re.DOTALL | re.MULTILINE
        )

        seen_discoveries = set()
        for m in DISCOVERY_PATTERN.finditer(cleaned_body):
            disc_num = int(m.group(1))
            disc_title = m.group(2).strip()

            # Deduplicate: same number + same title = skip
            dedup_key = (disc_num, disc_title)
            if dedup_key in seen_discoveries:
                continue
            seen_discoveries.add(dedup_key)

            # Find this discovery's content (until next discovery or end)
            disc_start = m.end()
            next_disc = DISCOVERY_PATTERN.search(cleaned_body, disc_start)
            if next_disc:
                disc_body = cleaned_body[m.start():next_disc.start()]
            else:
                disc_body = cleaned_body[m.start():]

            # Also strip inline code blocks from discovery body
            disc_body = re.sub(
                r'^```[\w\-]*\n.*?^```',
                '',
                disc_body,
                count=0,
                flags=re.DOTALL | re.MULTILINE
            )

            fields = {}
            for fm in FIELD_PATTERN.finditer(disc_body):
                fkey = fm.group(1).strip().lower().replace(" ", "_")
                fval = fm.group(2).strip()
                fields[fkey] = fval

            result["discoveries"].append({
                "number": disc_num,
                "title": disc_title,
                "fields": fields,
                "section": section["name"],
                "full_text": disc_body.strip(),
            })

    return result


def generate_spine_id(project, filename):
    """Generate a deterministic spine_id from project and filename."""
    raw = f"{project}::{filename}"
    return "spine-" + uuid.uuid5(uuid.NAMESPACE_DNS, raw).hex[:20]


def generate_node_id(spine_id, discovery_num):
    """Generate a deterministic node_id from spine and discovery number."""
    return f"{spine_id}-d{discovery_num:03d}"


def insert_into_db(parsed, dry_run=False):
    """Insert parsed extraction into knowledge_spines + spine_nodes tables."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    project = parsed["project"]
    filename = parsed["filename"]
    meta = parsed["metadata"]
    spine_id = generate_spine_id(project, filename)

    # Source group from metadata (vision_docs, transcripts_claude, governance, etc.)
    source_group = meta.get("group", "unknown")
    extraction_date = meta.get("extracted", "")

    # Build a subject from the source filename
    source_filename = meta.get("source", filename)
    # Clean up the source path to just the filename
    if "/" in source_filename:
        source_filename = source_filename.rsplit("/", 1)[-1]
    if source_filename.endswith(".md"):
        source_filename = source_filename[:-3]

    subject = source_filename

    if dry_run:
        print(f"  [DRY-RUN] Would insert spine: {spine_id}")
        print(f"    Project={project}, Subject={subject}, Source={source_group}")
        print(f"    Discoveries: {len(parsed['discoveries'])}")
        for d in parsed["discoveries"]:
            print(f"      - D{d['number']}: {d['title'][:60]}")
        return {"spine_id": spine_id, "node_count": len(parsed["discoveries"])}

    # ── Insert knowledge spine ─────────────────────────────────────────────
    now = datetime.utcnow().isoformat()
    domain = project.upper()
    sub_domain = source_group

    cursor.execute("""
        INSERT OR REPLACE INTO knowledge_spines
            (spine_id, domain, sub_domain, subject, source_type, file_path,
             node_count, status, ingested_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        spine_id,
        domain,
        sub_domain,
        subject,
        "extraction_analysis",
        str(parsed["filepath"]),
        len(parsed["discoveries"]),
        "ingested",
        now,
        now,
    ))

    # ── Insert spine nodes (discoveries) ───────────────────────────────────
    for disc in parsed["discoveries"]:
        node_id = generate_node_id(spine_id, disc["number"])
        # Build a path like "cis/transcripts_claude/00_START_HERE/Discovery-1"
        path = f"{project}/{source_group}/{subject}/Discovery-{disc['number']}"

        # The node title includes the discovery title plus key fields as narrative
        fields = disc["fields"]
        narrative_parts = []
        for fkey in ["architectural_significance", "dependency_impact", "build_impact", "runtime_impact"]:
            if fkey in fields and fields[fkey]:
                # Clean up the key name for display
                display_key = fkey.replace("_", " ").title()
                narrative_parts.append(f"**{display_key}:** {fields[fkey]}")

        narrative = "\n\n".join(narrative_parts) if narrative_parts else disc["full_text"][:500]

        # Title with discovery number
        title = f"D{disc['number']}: {disc['title']}"

        # Affected layers become tags
        affected_layers = fields.get("affected_layers", "")

        # Parent node: use the spine's first node if discovery 1, otherwise link to previous
        parent_node_id = None
        if disc["number"] > 1:
            parent_node_id = generate_node_id(spine_id, disc["number"] - 1)

        cursor.execute("""
            INSERT OR REPLACE INTO spine_nodes
                (node_id, spine_id, parent_node_id, title, depth, path,
                 status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            spine_id,
            parent_node_id,
            title,
            1,
            path,
            "ingested",
            now,
        ))

    conn.commit()
    conn.close()

    # ── Index into unified memory store ────────────────────────────────────
    if not dry_run:
        _index_into_memory(parsed, spine_id, project, subject, source_group)

    return {"spine_id": spine_id, "node_count": len(parsed["discoveries"])}


# ── Memory indexing ────────────────────────────────────────────────────────

# Lazy import for memory store to avoid circular deps at module level
_memory_store = None

def _get_memory():
    global _memory_store
    if _memory_store is None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from memory.memory_store import MemoryStore
        _memory_store = MemoryStore()
        _memory_store.ensure_tables()
    return _memory_store


def _index_into_memory(parsed, spine_id, project, subject, source_group):
    """Create memory_records + vectors from a parsed extraction."""
    try:
        ms = _get_memory()
    except Exception as e:
        print(f"    [memory] Store unavailable: {e}")
        return

    domain = project.lower()
    discoveries = parsed.get("discoveries", [])
    filepath = parsed.get("filepath", "")
    subject_clean = subject.replace("_", " ").replace("-", " ")

    # ── Spine-level record ──────────────────────────────────────────────
    spine_summary = f"Extraction: {subject_clean} ({source_group}) — {len(discoveries)} discoveries about {domain} architecture"
    spine_detail_parts = []
    for d in discoveries[:5]:
        fields = d.get("fields", {})
        sig = fields.get("architectural_significance", "")
        spine_detail_parts.append(f"Discovery {d['number']}: {d['title']}")
        if sig:
            spine_detail_parts.append(f"  → {sig[:200]}")
    if len(discoveries) > 5:
        spine_detail_parts.append(f"  ... and {len(discoveries) - 5} more discoveries")
    
    ms.store_record(
        category="extraction",
        domain=domain,
        tags=f"extraction,{source_group},{domain}",
        summary=spine_summary,
        detail="\n".join(spine_detail_parts),
        source_type="extraction",
        source_path=str(filepath),
        session_id="",
        importance=2,
    )

    # ── Per-discovery records for deeper signal ─────────────────────────
    for d in discoveries[:12]:  # cap at 12 per file
        fields = d.get("fields", {})
        sig = fields.get("architectural_significance", "")
        affected = fields.get("affected_layers", "")
        dep_impact = fields.get("dependency_impact", "")
        build_impact = fields.get("build_impact", "")
        runtime_impact = fields.get("runtime_impact", "")

        if not sig and not build_impact:
            continue  # skip if no substantive content

        detail_parts = []
        if affected:
            detail_parts.append(f"Affected Layers: {affected}")
        if dep_impact:
            detail_parts.append(f"Dependency Impact: {dep_impact}")
        if build_impact:
            detail_parts.append(f"Build Impact: {build_impact}")
        if runtime_impact:
            detail_parts.append(f"Runtime Impact: {runtime_impact}")

        ms.store_record(
            category="discovery",
            domain=domain,
            tags=f"discovery,{source_group},{domain},{source_group}",
            summary=f"D{d['number']}: {d['title']}",
            detail=f"{sig}\n" + "\n".join(detail_parts) if detail_parts else sig,
            source_type="extraction",
            source_path=f"{filepath}#D{d['number']}",
            session_id="",
            importance=1,
        )

    # ── Section-level records for non-discovery sections ────────────────
    for section in parsed.get("sections", []):
        sec_num = section.get("number", 0)
        if 1 <= sec_num <= 9:
            continue  # discoveries already handled above
        sec_name = section.get("name", f"section_{sec_num}")
        content = section.get("content", "")
        if len(content) < 50:
            continue

        ms.store_record(
            category="extraction_section",
            domain=domain,
            tags=f"extraction,{source_group},{domain},{sec_name}",
            summary=f"Section {sec_num}: {sec_name.replace('_', ' ').title()} ({subject_clean})",
            detail=content[:1000],
            source_type="extraction",
            source_path=f"{filepath}#section{sec_num}",
            session_id="",
            importance=1,
        )


def main():
    parser = argparse.ArgumentParser(description="Ingest extraction files into CIS knowledge spines")
    parser.add_argument("--project", choices=["cis", "swa"], help="Ingest only one project")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be inserted without writing")
    parser.add_argument("--sample", type=int, default=0, help="Process only N files per project for testing")
    args = parser.parse_args()

    # Collect files
    files = []
    if args.project in (None, "cis"):
        if CIS_EXT_DIR.exists():
            for f in sorted(CIS_EXT_DIR.iterdir()):
                if f.suffix == ".md":
                    files.append(f)
    if args.project in (None, "swa"):
        if SWA_EXT_DIR.exists():
            for f in sorted(SWA_EXT_DIR.iterdir()):
                if f.suffix == ".md":
                    files.append(f)

    print(f"Found {len(files)} extraction files")
    if args.sample:
        # Take a balanced sample
        cis_files = [f for f in files if "/cis/" in str(f)]
        swa_files = [f for f in files if "/social_work_ai/" in str(f)]
        files = cis_files[:args.sample] + swa_files[:args.sample]
        print(f"Sampling: {len(files)} files ({len(cis_files[:args.sample])} CIS, {len(swa_files[:args.sample])} SWA)")

    total_spines = 0
    total_nodes = 0
    parse_errors = 0
    problematic_files = []

    for i, filepath in enumerate(files):
        label = filepath.name[:50]
        print(f"[{i+1}/{len(files)}] {filepath.name[:60]}...", end=" ", flush=True)

        try:
            parsed = parse_extraction(filepath)
            result = insert_into_db(parsed, dry_run=args.dry_run)
            total_spines += 1
            total_nodes += result["node_count"]

            if not parsed["discoveries"]:
                # Check if this is a problem or just a single-section file
                sections_found = len(parsed["sections"])
                if sections_found == 0:
                    print(f"⚠ NO SECTIONS FOUND")
                    problematic_files.append(filepath.name)
                else:
                    print(f"✓ {result['node_count']} nodes, {sections_found} sections (no discovery pattern)")
            else:
                print(f"✓ {result['node_count']} discoveries")

        except Exception as e:
            parse_errors += 1
            print(f"✗ ERROR: {e}")
            problematic_files.append(filepath.name)

    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Files processed:  {len(files)}")
    print(f"  Spines created:  {total_spines}")
    print(f"  Total nodes:     {total_nodes}")
    print(f"  Parse errors:    {parse_errors}")
    if problematic_files:
        print(f"  Problematic:     {len(problematic_files)} files")
        for pf in problematic_files[:10]:
            print(f"    - {pf}")
        if len(problematic_files) > 10:
            print(f"    ... and {len(problematic_files) - 10} more")
    print("=" * 60)


if __name__ == "__main__":
    main()
