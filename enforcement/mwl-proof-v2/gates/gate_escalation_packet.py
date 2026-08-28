#!/usr/bin/env python3
"""
gate_escalation_packet.py — Escalation Packet Completeness & Hash Gate
Component 2: Escalation Advisor Integration Protocol

Deterministic check that a built packet contains every mandatory section P0-P6
and that the stored hash matches recomputation over P1-P6.

Usage:
    gate_escalation_packet.py --packet-id ID [--db PATH]
        # Verify a stored packet
    gate_escalation_packet.py --packet-file FILE
        # Verify a packet from a file (hash computed over P1-P6 in the file)

Exit 0: PASS
Exit 1: FAIL
Exit 2: ERROR
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "runtime"))
from db.database import init_db, get_packet

DEFAULT_DB = os.environ.get("CIS_DB_PATH", "/mnt/projects/cis/data/cis_memory.db")

SECTION_HEADERS = ["P0 — Header", "P1 — Project position", "P2 — Spine state excerpt",
                   "P3 — Provenance and lifecycle records", "P4 — The exact question",
                   "P5 — Constraints and authority limits", "P6 — Evidence appendix"]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def error(msg):
    print(f"ERROR: {msg}")
    sys.exit(2)


def extract_sections(packet_text):
    """Extract P0-P6 sections from packet text."""
    sections = {}
    current = None
    buf = []
    for line in packet_text.split("\n"):
        matched = False
        for i, hdr in enumerate(SECTION_HEADERS):
            if line.strip() == hdr:
                if current:
                    sections[current] = "\n".join(buf)
                current = f"P{i}"
                buf = [line]
                matched = True
                break
        if not matched and current:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf)
    return sections


def compute_packet_hash(p1_p6_text):
    """SHA256 over the concatenated P1-P6 text blocks."""
    return hashlib.sha256(p1_p6_text.encode("utf-8")).hexdigest()


def check_completeness(sections):
    """Verify all mandatory sections P0-P6 are present."""
    missing = []
    for i in range(7):
        key = f"P{i}"
        if key not in sections:
            missing.append(key)
    if missing:
        fail(f"Missing mandatory sections: {', '.join(missing)}")
    return True


def check_hash(packet_text, stored_hash):
    """Recompute hash over P1-P6 and compare to stored hash.
    
    Finds the P1 section header in the raw text and takes everything from there
    to the end as the P1-P6 content. This avoids extraction/reassembly mismatches.
    """
    # Find P1 start boundary
    p1_marker = "P1 — Project position"
    p1_idx = packet_text.find(p1_marker)
    if p1_idx == -1:
        fail("P1 section not found in packet text")
    
    p1_p6_text = packet_text[p1_idx:]
    computed_hash = compute_packet_hash(p1_p6_text)
    if computed_hash != stored_hash:
        fail(f"Hash mismatch: stored={stored_hash[:16]}... computed={computed_hash[:16]}...")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify escalation packet completeness and hash integrity"
    )
    parser.add_argument("--packet-id", type=int, default=None,
                        help="Packet ID in the spine")
    parser.add_argument("--packet-file", default=None,
                        help="Packet file to verify")
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()

    if args.packet_id is None and args.packet_file is None:
        error("Must provide --packet-id or --packet-file")

    if args.packet_id is not None:
        db_path = args.db
        if not Path(db_path).exists():
            error(f"Database not found: {db_path}")
        conn = init_db(db_path)
        packet = get_packet(conn, args.packet_id)
        conn.close()
        if packet is None:
            error(f"Packet {args.packet_id} not found")
        packet_text = packet["packet_raw"]
        stored_hash = packet["packet_hash"]
        source = f"packet_id={args.packet_id}"
    else:
        packet_file = Path(args.packet_file)
        if not packet_file.exists():
            error(f"Packet file not found: {args.packet_file}")
        packet_text = packet_file.read_text()
        # Extract hash from P0 header
        stored_hash = None
        for line in packet_text.split("\n"):
            if line.startswith("packet_hash:"):
                stored_hash = line.split(":", 1)[1].strip()
                break
        if stored_hash is None:
            error("No packet_hash found in P0 header")
        source = f"file={args.packet_file}"

    sections = extract_sections(packet_text)
    check_completeness(sections)
    check_hash(packet_text, stored_hash)

    print(f"PASS: All mandatory sections present and hash matches for {source}")


if __name__ == "__main__":
    main()
