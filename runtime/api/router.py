import json
import sqlite3
from typing import Dict, List, Optional

# Constants
RESEARCH_SIGNALS = [
    "current", "latest", "recent", "today", "find", "search", "verify",
    "evidence", "source", "fact", "news", "check if", "is there", "who is",
    "what happened", "confirm", "look up", "real-time", "still"
]
DRAFTER_SIGNALS = [
    "design", "plan", "propose", "implement", "build", "architecture",
    "draft", "directive", "how should", "create", "structure", "approach",
    "strategy", "schema", "spec", "define", "write a", "outline", "pipeline"
]
REVIEWER_SIGNALS = [
    "critique", "review", "risk", "flaw", "adversarial", "validate",
    "challenge", "what's wrong", "missing", "weak", "counterargument",
    "devil's advocate", "push back", "check this", "tear apart", "poke holes"
]
QWEN_PREFIXES = ("FINAL_DIRECTIVE", "JUDGE_REQUEST")
ROUTER_AGENT_MAP = {
    "fast":        {"agent": "hermes-prime",  "port": 8800},
    "v4_drafter":  {"agent": "hermes-v4pro",  "port": 8645},
    "v4_reviewer": {"agent": "hermes-r1",     "port": 8643},
    "qwen":        {"agent": "hermes-qwen",   "port": 8644},
}
ROUTER_NEXT_ACTION = {
    "fast":        "Evidence returned — continue to V4 Drafter",
    "v4_drafter":  "Send to V4 Reviewer for adversarial critique",
    "v4_reviewer": "Incorporate critique, then generate FINAL_DIRECTIVE for Qwen",
    "qwen":        "Review VERDICT / ACTION / EVIDENCE output",
    "blocked":     "Use V4 Drafter to generate a properly formatted directive first",
    "multihop":    "Research preflight complete — auto-forwarding to V4 Drafter",
}

# Helper
def _score_signals(text: str, signals: List[str]) -> List[str]:
    t = text.lower()
    return [s for s in signals if s in t]

# Main classification function
def classify_route(message: str, override: Optional[str] = None) -> Dict[str, any]:
    # Initialize result
    result = {
        "message_id": "",  # Will be set later
        "route": "",      # Will be set below
        "agent": "",      # Will be set below
        "port": 0,        # Will be set below
        "confidence": "", # Will be set below
        "signals_matched": [],
        "reason": "",
        "multihop": False,
        "qwen_blocked": False,
        "next_suggested_action": "",
    }

    # 1. Qwen gate: FINAL_DIRECTIVE or JUDGE_REQUEST
    if message.strip().startswith(QWEN_PREFIXES):
        result["route"] = "qwen"
        result["confidence"] = "deterministic"
        result["reason"] = "Qwen gate: FINAL_DIRECTIVE or JUDGE_REQUEST detected"
        return result

    # 2. Qwen gate: override not allowed unless format is correct
    if override == "qwen" and not message.strip().startswith(QWEN_PREFIXES):
        result["route"] = "blocked"
        result["confidence"] = "deterministic"
        result["qwen_blocked"] = True
        result["qwen_block_reason"] = "Must start with FINAL_DIRECTIVE or JUDGE_REQUEST"
        result["reason"] = "Qwen gate: override rejected — input must start with FINAL_DIRECTIVE or JUDGE_REQUEST"
        return result

    # 3. Manual override
    if override is not None and override in ROUTER_AGENT_MAP:
        result["route"] = override
        result["confidence"] = "override"
        result["reason"] = f"Manual override to {override}"
        result["agent"] = ROUTER_AGENT_MAP[override]["agent"]
        result["port"] = ROUTER_AGENT_MAP[override]["port"]
        return result

    # 4. Adversarial/critique intent
    reviewer_signals = _score_signals(message, REVIEWER_SIGNALS)
    if reviewer_signals:
        result["route"] = "v4_reviewer"
        result["confidence"] = "high" if len(reviewer_signals) >= 2 else "medium"
        result["reason"] = f"Adversarial/critique intent detected — signals: {reviewer_signals}"
        result["agent"] = ROUTER_AGENT_MAP["v4_reviewer"]["agent"]
        result["port"] = ROUTER_AGENT_MAP["v4_reviewer"]["port"]
        return result

    # 5. Current facts / evidence gathering
    research_signals = _score_signals(message, RESEARCH_SIGNALS)
    drafter_signals = _score_signals(message, DRAFTER_SIGNALS)
    if research_signals and not drafter_signals:
        result["route"] = "fast"
        result["confidence"] = "high" if len(research_signals) >= 2 else "medium"
        result["reason"] = f"Current facts / evidence gathering detected — signals: {research_signals}"
        result["agent"] = ROUTER_AGENT_MAP["fast"]["agent"]
        result["port"] = ROUTER_AGENT_MAP["fast"]["port"]
        return result

    # 6. Research preflight before drafting
    if research_signals and drafter_signals:
        result["route"] = "fast"
        result["multihop"] = True
        result["confidence"] = "high"
        result["reason"] = "Research preflight before drafting — evidence will be injected into V4 Drafter"
        result["agent"] = ROUTER_AGENT_MAP["fast"]["agent"]
        result["port"] = ROUTER_AGENT_MAP["fast"]["port"]
        return result

    # 7. Architecture/proposal intent
    if drafter_signals:
        result["route"] = "v4_drafter"
        result["confidence"] = "high" if len(drafter_signals) >= 2 else "medium"
        result["reason"] = f"Architecture/proposal intent detected — signals: {drafter_signals}"
        result["agent"] = ROUTER_AGENT_MAP["v4_drafter"]["agent"]
        result["port"] = ROUTER_AGENT_MAP["v4_drafter"]["port"]
        return result

    # 8. Fallback
    result["route"] = "v4_drafter"
    result["confidence"] = "low"
    result["reason"] = "No clear signal — defaulted to V4 Drafter"
    result["agent"] = ROUTER_AGENT_MAP["v4_drafter"]["agent"]
    result["port"] = ROUTER_AGENT_MAP["v4_drafter"]["port"]
    return result

# SQL DDL for routing decisions table
ROUTING_DDL = [
    """CREATE TABLE IF NOT EXISTS routing_decisions ("
    "id                        INTEGER PRIMARY KEY AUTOINCREMENT,"
    "message_id                TEXT NOT NULL,"
    "thread_id                 TEXT,"
    "original_message          TEXT NOT NULL,"
    "selected_route            TEXT NOT NULL,"
    "selected_agent            TEXT,"
    "matched_signals           TEXT,"
    "confidence                TEXT NOT NULL,"
    "override_used             TEXT,"
    "multihop                  INTEGER DEFAULT 0,"
    "qwen_blocked              INTEGER DEFAULT 0,"
    "agent_response_message_id TEXT,"
    "preflight_response        TEXT,"
    "created_at                DATETIME DEFAULT CURRENT_TIMESTAMP"
    ")""","
    "CREATE INDEX IF NOT EXISTS idx_rd_thread  ON routing_decisions(thread_id)","
    "CREATE INDEX IF NOT EXISTS idx_rd_route   ON routing_decisions(selected_route)","
    "CREATE INDEX IF NOT EXISTS idx_rd_created ON routing_decisions(created_at)"
]

# Ensure routing table exists
def _ensure_routing_table(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        for ddl in ROUTING_DDL:
            cursor.execute(ddl)
        conn.commit()
    finally:
        conn.close()

# Persist routing decision to database
def _persist_routing(db_path: str, routing: Dict[str, any], original_message: str, thread_id: Optional[str], override: Optional[str] = None, agent_response_message_id: Optional[str] = None, preflight_response: Optional[str] = None) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO routing_decisions ("
            "message_id, thread_id, original_message, selected_route, selected_agent, matched_signals, confidence, override_used, multihop, qwen_blocked, agent_response_message_id, preflight_response, created_at)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (
                routing["message_id"],
                thread_id,
                original_message,
                routing["selected_route"],
                routing["selected_agent"],
                json.dumps(routing.get("signals_matched", [])),
                routing["confidence"],
                override,
                1 if routing.get("multihop") else 0,
                1 if routing.get("qwen_blocked") else 0,
                agent_response_message_id,
                preflight_response,
            )
        )
        conn.commit()
    finally:
        conn.close()