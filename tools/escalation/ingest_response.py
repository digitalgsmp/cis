#!/usr/bin/env python3
"""
ingest_response.py — Deterministic Advisor Response Ingestion
Component 2: Escalation Advisor Integration Protocol

Writes verbatim advisor response to the spine. Computes hash_match_status
against the referenced packet version. May attach a PROPOSED classification
via simple deterministic keyword/structure detection only. Never sets CONFIRMED.

Usage:
    ingest_response.py --response-id ID --response-file FILE [--db PATH]
    # Updates an existing EXPECTED response row with the ingested response.
    ingest_response.py --escalation-id ID --packet-id ID --advisor CLAUDE|CHATGPT \
        --response-file FILE [--transmission-mode MANUAL_PASTE|API] [--db PATH]
    # Creates a new response row and ingests.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "runtime"))
from db.database import (
    init_db, get_packet, update_response_status, insert_advisor_response,
    get_response, get_escalation,
    ALLOWED_ADVISORS,
)

DEFAULT_DB = "/mnt/projects/cis/data/cis_memory.db"


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def detect_primary_type(response_text):
    """Deterministic keyword/structure detection for PROPOSED classification only."""
    text_upper = response_text.upper()
    # Strong signals (must appear early and prominently)
    if "PASS WITH REQUIRED REVISIONS" in text_upper:
        return "AUDIT_OBJECTION"
    if "AUDIT_PASS" in text_upper and "OBJECTION" not in text_upper[:500]:
        return "AUDIT_PASS"
    if "AUDIT_OBJECTION" in text_upper or "OBJECTION" in text_upper[:200]:
        return "AUDIT_OBJECTION"
    if "PROPOSAL" in text_upper[:200]:
        return "PROPOSAL"
    if "CLARIFICATION" in text_upper[:200] and "REQUEST" in text_upper[:500]:
        return "CLARIFICATION_REQUEST"
    if "RISK" in text_upper[:200] and ("FLAG" in text_upper[:500] or "IDENTIF" in text_upper[:500]):
        return "RISK_FLAG"
    if "RECOMMEND" in text_upper[:200]:
        return "RECOMMENDATION"
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Ingest an advisor response verbatim into the spine"
    )
    parser.add_argument("--response-id", type=int, default=None,
                        help="Update an existing response row by ID")
    parser.add_argument("--escalation-id", type=int, default=None,
                        help="Escalation ID (for new response)")
    parser.add_argument("--packet-id", type=int, default=None,
                        help="Packet ID (for new response)")
    parser.add_argument("--advisor", choices=sorted(ALLOWED_ADVISORS), default=None)
    parser.add_argument("--response-file", required=True,
                        help="File containing the verbatim advisor response")
    parser.add_argument("--transmission-mode", default="MANUAL_PASTE",
                        choices=["MANUAL_PASTE", "API"])
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()

    if args.response_id is None and (args.escalation_id is None or args.packet_id is None):
        fail("Must provide either --response-id OR (--escalation-id + --packet-id + --advisor)")

    db_path = args.db
    if not Path(db_path).exists():
        fail(f"Database not found: {db_path}")

    # Read response
    response_file = Path(args.response_file)
    if not response_file.exists():
        fail(f"Response file not found: {args.response_file}")
    response_raw = response_file.read_text()

    conn = init_db(db_path)

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    if args.response_id is not None:
        # Update existing response row
        resp = get_response(conn, args.response_id)
        if resp is None:
            conn.close()
            fail(f"Response {args.response_id} not found")

        packet = get_packet(conn, resp["packet_id"])
        if packet is None:
            conn.close()
            fail(f"Packet {resp['packet_id']} not found for response {args.response_id}")

        # Compute hash match
        hash_match = "MATCH"
        # The responded_packet_hash should be the hash the advisor was responding to
        # For ingestion, we compare against the actual stored packet hash
        if resp.get("responded_packet_hash") and resp["responded_packet_hash"] != packet["packet_hash"]:
            hash_match = "MISMATCH"

        # Deterministic classification
        primary_type = detect_primary_type(response_raw)

        update_response_status(conn, args.response_id, "INGESTED", extra_fields={
            "response_raw": response_raw,
            "hash_match_status": hash_match,
            "primary_type": primary_type,
            "classification_source": "TOOL" if primary_type else None,
            "classification_status": "PROPOSED" if primary_type else None,
            "received_at": now,
            "ingested_at": now,
        })
        response_id = args.response_id
    else:
        # Create new response row
        packet = get_packet(conn, args.packet_id)
        if packet is None:
            conn.close()
            fail(f"Packet {args.packet_id} not found")

        responded_hash = packet["packet_hash"]
        hash_match = "MATCH"

        primary_type = detect_primary_type(response_raw)

        response_id = insert_advisor_response(
            conn,
            escalation_id=args.escalation_id,
            packet_id=packet["id"],
            advisor=args.advisor,
            response_raw=response_raw,
            responded_packet_hash=responded_hash,
            hash_match_status=hash_match,
            primary_type=primary_type,
            classification_source="TOOL" if primary_type else None,
            classification_status="PROPOSED" if primary_type else None,
            response_status="INGESTED",
            transmission_mode=args.transmission_mode,
            received_at=now,
            ingested_at=now,
        )

    conn.commit()
    conn.close()

    classification_info = ""
    pt = detect_primary_type(response_raw)
    if pt:
        classification_info = f" (PROPOSED classification: {pt}, source: TOOL)"

    print(f"Ingested response_id={response_id} hash_match={hash_match}{classification_info}")
    print("NOTE: Classification is PROPOSED only. Eric must confirm or correct.")


if __name__ == "__main__":
    main()
