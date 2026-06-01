#!/usr/bin/env python3
"""
session_extract.py — Deep topological extraction from Hermes session JSON files.

Reads a session JSON from ~/.hermes/sessions/, parses the conversation,
extracts decisions, corrections, preferences, current_state, and project_facts
as structured memory records, and indexes them into SQLite + ChromaDB.

Usage:
    python3 session_extract.py <session_file.json>
    python3 session_extract.py --sweep           # process all unprocessed sessions
    python3 session_extract.py --session <id>    # process a specific session by ID
    python3 session_extract.py --dry-run <file>  # show what would be extracted

Output:
    - memory_sessions row (status=done)
    - 1+ memory_records per extracted signal
    - Vectors in ChromaDB unified_memory collection
"""

import json
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────
RUNTIME_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = Path.home() / ".hermes" / "sessions"

sys.path.insert(0, str(RUNTIME_DIR))


# ── Signal extraction patterns ──────────────────────────────────────────
# These are heuristics — they detect patterns common in Hermes conversations
# where the user gives a correction, makes a decision, or states a preference.
# IMPORTANT: patterns must not match system-generated text that happens to
# appear in user messages (system prompts, Hermes framework instructions).

SIGNAL_PATTERNS = {
    "correction": [
        r"\b(?:no[.,!]|wrong|that'?s?\s+not\s+(?:what|right|correct)|actually[.,])\s.*",
        r"\b(?:i\s+said\s+|i\s+meant\s+).*",
        r"\b(?:stop\s+doing|don'?t\s+(?:do|format|explain|give))\b.*",
        r"\b(?:option\s+[ab]|choose\s+[ab]|pick\s+[ab])\s+.*",
    ],
    "decision": [
        r"\b(?:we\s+should|let'?s\s+(?:go|use|build|start|try|do))\b.*",
        r"\b(?:decided|approved|confirmed)\b.*",
        r"\b(?:option\s+b|go\s+with|use\s+option)\b.*",
    ],
    "preference": [
        r"\b(?:i\s+(?:like|want|need|prefer|hate|don'?t\s+like))\s+.*",
        r"\b(?:visually|aesthetic|thumbnail|grid|list|visual|text[- ]first|dark|light)\b.*",
    ],
    "current_state": [
        r"\b(?:currently\s+|right\s+now\s+we'?re|so\s+far\s+|status\s+update)\b.*",
        r"\b(?:working\s+on\s+|building\s+|debugging\s+|implementing\s+)\b.*",
        r"\b(?:stuck\s+on|blocked\s+by|waiting\s+for|next\s+step)\b.*",
    ],
}

# Compile patterns
CATEGORY_PATTERNS = {}
for cat, patterns in SIGNAL_PATTERNS.items():
    CATEGORY_PATTERNS[cat] = [re.compile(p, re.IGNORECASE) for p in patterns]


_NOISE_SKIP_PREFIXES = (
    "[System note",
    "• User corrected",
    "• ",
    "[System",
    "Review the conversation above",
    "[IMPORTANT: You are running as a scheduled cron job",
    "[IMPORTANT: You are running as a scheduled cron",
)


def detect_signals(text):
    """Scan text for signal patterns, return list of (category, matched_text) tuples."""
    signals = []
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            m = pattern.search(text)
            if m:
                signals.append((category, m.group(0)[:200]))
    return signals


def extract_session(path):
    """Extract structured memory records from a session JSON file.
    
    Returns dict with:
      - session_id: str
      - session_data: dict (metadata)
      - extracted_nodes: list of dicts (memory records to create)
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    session_id = data.get("session_id", path.stem)
    platform = data.get("platform", "unknown")
    model = data.get("model", "unknown")
    started_at = data.get("session_start", "")
    last_active = data.get("last_updated", "")
    messages = data.get("messages", [])
    message_count = len(messages)

    session_data = {
        "session_id": session_id,
        "platform": platform,
        "session_start": started_at,
        "last_updated": last_active,
        "message_count": message_count,
        "model": model,
    }

    extracted_nodes = []

    # Track what we've already seen to avoid duplicates within one session
    seen_signals = set()

    # ── Phase 1: Extract from user messages (corrections, decisions, preferences) ──
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = str(msg.get("content", ""))
        if not content or len(content) < 20:
            continue

        # Skip system-level and tool messages
        if content.startswith(_NOISE_SKIP_PREFIXES):
            continue

        # Skip known Hermes system prompt templates — these appear in user
        # message slots when a cron or system-injected instruction is echoed
        # back into the session. They produce false signals.
        HERMES_SYSTEM_SIGNATURES = [
            "Review the conversation above and update the skill library",
            "[IMPORTANT: You are running as a scheduled cron job",
            "DELIVERY: Your final response will be automatically delivered",
            "SILENT: If there is genuinely nothing new to report",
            "Target shape of the library: CLASS-LEVEL skills",
            "Signals to look for (any one of these warrants action)",
            "prefer the earliest action that fits",
            "first-class skill signals, not just memory signals",
        ]
        if any(sig in content for sig in HERMES_SYSTEM_SIGNATURES):
            continue

        signals = detect_signals(content)
        if not signals:
            continue

        # Group signals by category, keep the strongest one
        grouped = {}
        for cat, matched in signals:
            if cat not in grouped:
                grouped[cat] = matched

        for category, matched in grouped.items():
            # Deduplicate: same category + similar content
            dedup_key = f"{category}:{matched[:80]}"
            if dedup_key in seen_signals:
                continue
            seen_signals.add(dedup_key)

            # Build a summary and detail for this signal
            summary = _extract_summary(content, category, matched)
            detail = _extract_detail(content, messages, session_id)
            tags = _extract_tags(content, category, platform)
            domain = _detect_domain(content)

            # Higher importance for corrections and decisions
            imp = 3 if category == "correction" else (2 if category == "decision" else 1)

            extracted_nodes.append({
                "category": category,
                "domain": domain,
                "tags": tags,
                "summary": summary,
                "detail": detail,
                "source_type": "session",
                "source_path": f"session://{session_id}",
                "importance": imp,
            })

    # ── Phase 2: Session-level summary record (no more project_fact noise) ──
    user_messages = [m for m in messages if m.get("role") == "user" and not str(m.get("content","")).startswith("[System")]
    topic_hints = []
    for m in user_messages[:3]:
        c = str(m.get("content", ""))[:100]
        topic_hints.append(c.strip())

    extracted_nodes.append({
        "category": "current_state",
        "domain": "technical" if platform == "cli" else "general",
        "tags": f"session,session_{platform}",
        "summary": f"Session {session_id[:20]}... ({platform}, {model}) — {message_count} messages",
        "detail": "Topics: " + " | ".join(topic_hints),
        "source_type": "session",
        "source_path": f"session://{session_id}",
        "importance": 1,
    })

    return {
        "session_id": session_id,
        "session_data": session_data,
        "extracted_nodes": extracted_nodes,
    }


def _extract_summary(content, category, matched):
    """Build a concise summary from user content."""
    # Try to get a clean sentence after the signal
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    for line in lines:
        if any(kw in line.lower() for kw in ["correction", "actually", "i meant", "no,", "wrong", "should", "prefer", "want", "need"]):
            return line[:200]
    return matched[:200]


def _extract_detail(content, all_messages, session_id):
    """Build detail — include context from surrounding messages."""
    parts = [content[:1000]]
    # Try to find the assistant's response to provide context
    for i, m in enumerate(all_messages):
        if m.get("role") == "user" and session_id in str(m.get("content", "")):
            # Look at next assistant message
            if i + 1 < len(all_messages) and all_messages[i + 1].get("role") == "assistant":
                resp = str(all_messages[i + 1].get("content", ""))[:300]
                parts.append(f"[Response: {resp}]")
            break
    return "\n".join(parts)


def _extract_tags(content, category, platform):
    """Extract relevant tags from content."""
    tags = [category, f"session_{platform}"]
    # Domain keywords
    if any(kw in content.lower() for kw in ["creative", "art", "poem", "story", "comic", "blender"]):
        tags.append("creative")
    if any(kw in content.lower() for kw in ["technical", "api", "database", "config", "code"]):
        tags.append("technical")
    if any(kw in content.lower() for kw in ["lms", "learn", "course", "tutorial"]):
        tags.append("learning")
    if any(kw in content.lower() for kw in ["social", "care", "client", "swa"]):
        tags.append("socialcare")
    return ",".join(set(tags))


def _detect_domain(content):
    """Detect which CIS domain the content belongs to."""
    cl = content.lower()
    if any(kw in cl for kw in ["social care", "social_work_ai", "client", "case file", "swa"]):
        return "socialcare"
    if any(kw in cl for kw in ["creative", "poem", "story", "art", "comic", "blender", "nuke", "resolve"]):
        return "creative"
    if any(kw in cl for kw in ["lms", "course", "tutorial", "learn", "study"]):
        return "learning"
    if any(kw in cl for kw in ["personal", "home", "family", "health"]):
        return "personal"
    return "technical"


def process_session_file(path, dry_run=False):
    """Process a single session file: extract + store.
    
    Cron sessions are tracked but produce no memory records — they're
    heartbeat logs with no conversational content worth storing.
    """
    print(f"  Extracting: {path.name}...", end=" ", flush=True)
    try:
        # Detect cron sessions early — skip extraction entirely
        if "cron_" in path.stem or "cron_" in str(path):
            print(f"cron session — skipping (no memory records)", end="")
            if dry_run:
                print()
                return {"session_id": str(path), "nodes": 0, "skipped": True}
            # Still mark as done so we don't re-process
            from memory.memory_store import MemoryStore
            ms = MemoryStore()
            ms.ensure_tables()
            sid = _get_session_id_for_cron(path)
            if sid:
                now = datetime.now(timezone.utc).isoformat()
                ms.conn.execute("""
                    INSERT OR REPLACE INTO memory_sessions
                        (session_id, platform, started_at, last_active, message_count,
                         extracted_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sid, "cron", "", "", 0, now, "done"))
                ms.conn.commit()
            print(f" → 0 records stored (cron)")
            return {"session_id": sid or str(path), "nodes": 0, "skipped": True}

        result = extract_session(path)
        nodes = result["extracted_nodes"]
        print(f"{len(nodes)} signals found", end="")

        if dry_run:
            for n in nodes[:5]:
                print(f"\n    [{n['category']}] {n['summary'][:80]}")
            print()
            return {"session_id": result["session_id"], "nodes": len(nodes)}

        # Store via memory_store
        from memory.memory_store import MemoryStore
        ms = MemoryStore()
        ms.ensure_tables()
        count = ms.store_session_record(result["session_data"], nodes)
        print(f" → {count} records stored", end="")
        return {"session_id": result["session_id"], "nodes": count}

    except Exception as e:
        print(f"✗ ERROR: {e}")
        # Try to mark as failed
        try:
            from memory.memory_store import MemoryStore
            ms = MemoryStore()
            ms.ensure_tables()
            sid = path.stem.replace("session_", "").replace(".json", "")
            ms.mark_session_failed(sid, str(e))
        except Exception:
            pass
        return {"session_id": str(path), "error": str(e)}


def _get_session_id_for_cron(path):
    """Extract session_id from a cron session JSON file."""
    try:
        import json as _json
        with open(path) as _f:
            return _json.load(_f).get("session_id", "")
    except Exception:
        return ""


def sweep():
    """Process all unprocessed session files from Hermes sessions dir."""
    from memory.memory_store import MemoryStore
    ms = MemoryStore()
    ms.ensure_tables()

    # Get all session JSON files
    if not SESSIONS_DIR.exists():
        print(f"Session directory not found: {SESSIONS_DIR}")
        return

    session_files = sorted(SESSIONS_DIR.glob("session_*.json"), key=lambda p: p.stat().st_mtime)

    # Check which ones are already processed
    already_done = set()
    try:
        cur = ms.conn.cursor()
        rows = cur.execute("SELECT session_id FROM memory_sessions WHERE status='done'").fetchall()
        already_done = {r[0] for r in rows}
    except Exception:
        pass

    results = {"total": 0, "done": 0, "skipped": 0, "failed": 0}
    for path in session_files:
        # Extract session_id from filename: session_20260513_120058_04e66a4f.json
        # Filenames sometimes mismatch the JSON session_id, so check both
        file_key = path.stem
        file_key = file_key.replace("session_", "", 1) if file_key.startswith("session_") else file_key
        # Also peek at the JSON for its internal session_id
        try:
            import json as _json
            with open(path) as _f:
                _data = _json.load(_f)
            json_sid = _data.get("session_id", "")
        except Exception:
            json_sid = ""
        if file_key in already_done or json_sid in already_done:
            results["skipped"] += 1
            continue

        results["total"] += 1
        outcome = process_session_file(path)
        if outcome.get("error"):
            results["failed"] += 1
        else:
            results["done"] += 1

    print(f"\nSweep complete: {results['done']} processed, {results['skipped']} already done, {results['failed']} failed")
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract signals from Hermes session files")
    parser.add_argument("files", nargs="*", help="Session JSON file(s) to extract")
    parser.add_argument("--sweep", action="store_true", help="Process all unprocessed sessions")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be extracted without storing")
    parser.add_argument("--session", help="Process a specific session by ID (partial match)")
    args = parser.parse_args()

    if args.sweep:
        sweep()
    elif args.files:
        for f in args.files:
            fp = Path(f)
            if fp.exists():
                process_session_file(fp, dry_run=args.dry_run)
            else:
                print(f"File not found: {f}")
    elif args.session:
        # Find session file by partial ID match
        if not SESSIONS_DIR.exists():
            print(f"Session directory not found: {SESSIONS_DIR}")
            return
        for path in sorted(SESSIONS_DIR.glob("*.json")):
            if args.session in path.stem or args.session in open(path).read(500):
                print(f"Found: {path.name}")
                process_session_file(path, dry_run=args.dry_run)
                break
        else:
            print(f"No session found matching: {args.session}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
