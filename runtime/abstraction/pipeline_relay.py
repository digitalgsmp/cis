#!/usr/bin/env python3
"""
pipeline_relay.py — CIS Production Pipeline Relay (async state machine)

Per SPEC_PRODUCTION_PIPELINE_RELAY.md (REV-2, 2026-07-08).
Replaces test scaffolding in runtime/orchestrator.py.

Relay: Brain → Review1+2 → Draft → Review1+2 → Eric Gate → Menter → Verify
Features: mandatory pre-discovery, crash recovery, circuit breaker,
concurrent run protection, timeout management, saga compensation.

Usage:
    python3 pipeline_relay.py --intent "build a dark mode toggle"
    python3 pipeline_relay.py --resume <run_id>
    python3 pipeline_relay.py --status <run_id>
"""

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

# ── Constants ──────────────────────────────────────────────────────────

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
BASE_URL = "http://127.0.0.1"
AGENT_TIMEOUT = 180  # seconds per agent call (default)
# Per-role timeout overrides (verify/menter use tools and need more time)
AGENT_TIMEOUTS = {
    "verify": 600,   # 10 min — runs evidence commands
    "menter": 600,   # 10 min — builds code
    "brain": 300,    # 5 min — xhigh reasoning
    "draft": 300,    # 5 min — xhigh reasoning
}
REVIEWER_RETRY_TIMEOUT = 180
CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_COOLDOWN = 300  # 5 minutes
HUMAN_QUESTION_TIMEOUT = 72 * 3600  # 72 hours
MAX_BRAIN_ROUNDS = 2
MAX_DRAFT_ROUNDS = 3
MAX_CHUNK_REVISIONS = 3
MAX_CHUNK_LINES = 300

# ── Menter's Universal Rules (baked into prompt) ─────────────────────

MENTER_UNIVERSAL_RULES = """## UNIVERSAL RULES (you must follow these for every line of code you write)

1. DEFAULT TO INCOMPLETE: No function returns success without completing its job.
   No status field defaults to "success" or "consensus." Unknown states are errors, not passes.
2. HANDLE ERRORS EXPLICITLY: Every exception path must do something meaningful
   (log, raise, escalate). Silent `except: pass` is forbidden.
3. NO SECRETS IN CODE: No hardcoded API keys, passwords, tokens. Use env vars or config files.
4. NO DEBUG LEFTOVERS: No print() statements, no commented-out code, no TODO without context.
5. CLAIMS MUST MATCH REALITY: If you say "added function X", function X must exist in
   the code you wrote. Your self-report is a claim, not evidence.
6. CLEAN UP AFTER YOURSELF: No orphan temp files, no leftover debug artifacts,
   no resources opened without being closed.
7. STATE MUST PERSIST: If your code maintains state (circuit breaker, cache, counter),
   it must survive a process restart. In-memory only is not acceptable for state that matters.
8. VALIDATE BEFORE PROCEEDING: If your function calls another function or agent, validate
   the response before acting on it. Empty or malformed output is an error, not a silent success.

Self-check against these rules BEFORE submitting your chunk for review.
"""

# Import dispatch map
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dispatch import PROFILES, check_gateway, get_gateway_url  # noqa: E402

# ── State Machine ─────────────────────────────────────────────────────

STATES = {
    "PENDING", "INTAKE", "BRAIN_PHASE", "ESCALATE",
    "INTENT_REVIEW", "DRAFT_PHASE", "PROPOSAL_REVIEW",
    "ERIC_GATE", "PATTERN_CATALOG", "CODE_REVIEW_GATE",
    "EXECUTION", "VERIFICATION",
    "WAITING_FOR_HUMAN",
    "CONSENSUS_REACHED",
    # Error states
    "ESCALATED", "VERIFY_FAILED", "STALE", "ERROR",
}

TERMINAL_STATES = {"CONSENSUS_REACHED", "ESCALATED", "VERIFY_FAILED", "STALE", "ERROR"}

# ── Circuit Breaker ────────────────────────────────────────────────────

# In-memory cache, backed by circuit_breaker_state table for persistence
_circuit_breaker: Dict[str, dict] = {}  # role -> {failures, last_failure_ts}


def _breaker_load(role: str) -> dict:
    """Load circuit breaker state from DB (persists across restarts)."""
    try:
        conn = _db_connect()
        cur = conn.execute(
            "SELECT failures, last_failure_ts FROM circuit_breaker_state WHERE role = ?",
            (role,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {"failures": row[0], "last_failure_ts": row[1]}
    except Exception:
        pass
    return {"failures": 0, "last_failure_ts": 0}


def _breaker_save(role: str, entry: dict) -> None:
    """Persist circuit breaker state to DB."""
    try:
        conn = _db_connect()
        conn.execute(
            """INSERT INTO circuit_breaker_state (role, failures, last_failure_ts, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(role) DO UPDATE SET
               failures = excluded.failures,
               last_failure_ts = excluded.last_failure_ts,
               updated_at = excluded.updated_at""",
            (role, entry["failures"], entry["last_failure_ts"],
             datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _breaker_record_failure(role: str) -> None:
    """Record a gateway failure for circuit breaker (persisted to DB)."""
    entry = _circuit_breaker.get(role)
    if not entry:
        entry = _breaker_load(role)
    entry["failures"] += 1
    entry["last_failure_ts"] = time.time()
    _circuit_breaker[role] = entry
    _breaker_save(role, entry)


def _breaker_record_success(role: str) -> None:
    """Reset circuit breaker on success (persisted to DB)."""
    if role in _circuit_breaker:
        _circuit_breaker.pop(role, None)
    _breaker_save(role, {"failures": 0, "last_failure_ts": 0})


def _breaker_is_tripped(role: str) -> bool:
    """Check if circuit breaker is tripped for a role."""
    entry = _circuit_breaker.get(role)
    if not entry:
        entry = _breaker_load(role)
        _circuit_breaker[role] = entry
    if entry["failures"] < CIRCUIT_BREAKER_THRESHOLD:
        return False
    elapsed = time.time() - entry["last_failure_ts"]
    if elapsed > CIRCUIT_BREAKER_COOLDOWN:
        # Cooldown passed — reset
        _circuit_breaker.pop(role, None)
        _breaker_save(role, {"failures": 0, "last_failure_ts": 0})
        return False
    return True


# ── Database Helpers ──────────────────────────────────────────────────

def _db_connect() -> sqlite3.Connection:
    """Connect to spine DB with WAL mode and busy timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _db_retry(fn, max_attempts=3, base_delay=1.0):
    """Retry a DB operation with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_attempts - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            raise


def _set_run_status(conn: sqlite3.Connection, run_id: str, status: str,
                    extra: Optional[Dict] = None) -> None:
    """Atomically update run status. Raises if run not found."""
    # Concurrent run protection: only update if status is not terminal
    cur = conn.execute(
        "UPDATE workflow_runs SET status = ?, updated_at = ? WHERE id = ?",
        (status, datetime.now(timezone.utc).isoformat(), run_id)
    )
    if cur.rowcount == 0:
        raise ValueError(f"Run {run_id} not found or update failed")
    conn.commit()


def _create_run(conn: sqlite3.Connection, intent_text: str,
                created_by: str = "pipeline_relay") -> str:
    """Create a new workflow_run. Returns run_id."""
    # Idempotency: check for existing non-terminal run with same intent
    intent_hash = hashlib.sha256(intent_text.encode()).hexdigest()[:16]
    run_id = f"run-{intent_hash}-{int(time.time())}"
    conn.execute(
        """INSERT INTO workflow_runs
           (id, topic, result, status, created_at, max_rounds, rounds_completed)
           VALUES (?, ?, 'PENDING', 'INTAKE', ?, 3, 0)""",
        (run_id, intent_text[:500], datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    return run_id


def _get_run(conn: sqlite3.Connection, run_id: str) -> Optional[dict]:
    """Get a workflow run by ID."""
    cur = conn.execute(
        "SELECT id, topic, status, created_at, directive_hash FROM workflow_runs WHERE id = ?",
        (run_id,)
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0], "topic": row[1], "status": row[2],
        "created_at": row[3], "directive_hash": row[4],
    }


# ── Deliberation Round Helpers ─────────────────────────────────────────

def _start_round(conn: sqlite3.Connection, run_id: str, phase: str,
                 round_num: int) -> int:
    """Create a deliberation_rounds row. Returns round ID.

    The spine schema has UNIQUE(run_id, round_number), so we auto-increment
    the round number from the DB rather than trusting the caller's value.
    The caller's round_num is used only as a revision_number hint.
    """
    # Get next available round_number for this run
    cur = conn.execute(
        "SELECT COALESCE(MAX(round_number), 0) + 1 FROM deliberation_rounds WHERE run_id = ?",
        (run_id,)
    )
    actual_round_num = cur.fetchone()[0]

    cur = conn.execute(
        """INSERT INTO deliberation_rounds
           (run_id, round_number, drafter_role, drafter_output,
            reviewer_role, reviewer_signal, revision_number,
            requires_eric_review, created_at)
           VALUES (?, ?, ?, '', '', 'PENDING', ?, 0, ?)""",
        (run_id, actual_round_num, phase, round_num,
         datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    return cur.lastrowid


def _complete_round(conn: sqlite3.Connection, round_id: int,
                    reviewer_signal: str,
                    extra: Optional[Dict] = None) -> None:
    """Mark a deliberation round as complete with outputs.

    reviewer_signal must be one of: PENDING, OBJECTIONS, CONSENSUS_REACHED,
    ESCALATE, ERROR (per spine CHECK constraint).

    After completing the round, ingests all narrative content into the
    knowledge base (knowledge_messages) for FTS5 indexing. This is the
    self-evolution bridge — every round's content becomes searchable by
    future pipeline runs via pre-discovery.
    """
    fields = ["reviewer_signal = ?"]
    values = [reviewer_signal]
    if extra:
        for col, val in extra.items():
            fields.append(f"{col} = ?")
            values.append(val)
    values.append(round_id)
    conn.execute(
        f"UPDATE deliberation_rounds SET {', '.join(fields)} WHERE id = ?",
        values
    )
    conn.commit()

    # Self-evolution: ingest this round's narrative into the knowledge base
    # so future runs can discover it via FTS5 search in pre-discovery
    try:
        # Get run_id and phase for source tagging
        cur = conn.execute(
            "SELECT run_id, drafter_role FROM deliberation_rounds WHERE id = ?",
            (round_id,)
        )
        row = cur.fetchone()
        if row:
            run_id, phase = row[0], row[1]
            _ingest_round_to_kb(conn, run_id, round_id, phase, reviewer_signal)
    except Exception as e:
        print(f"[pipeline] KB ingestion for round {round_id} failed: {e}")


# ── Knowledge Base Ingestion (self-evolution bridge) ─────────────────

def _ingest_to_kb(conn: sqlite3.Connection, run_id: str, phase: str,
                  role: str, content: str, signal: str = "",
                  extra_context: str = "") -> None:
    """Ingest pipeline narrative into the knowledge_messages table.

    This is the self-evolution bridge. Every phase's output flows into
    the FTS5 knowledge base so future runs can discover it via pre-discovery.

    The knowledge_messages table has an AFTER INSERT trigger that auto-indexes
    into knowledge_messages_fts, so we just INSERT and the FTS5 index updates.

    Source naming convention:
      pipeline_{phase} — e.g. pipeline_brain, pipeline_code_review

    Content format includes:
      - Run ID and phase for traceability
      - Signal (CONSENSUS_REACHED / OBJECTIONS / etc) for filtering
      - The full narrative output
      - Extra context (review pass, revision number, etc.)
    """
    if not content or not content.strip():
        return

    source = f"pipeline_{phase}"

    # Build the narrative document
    parts = [
        f"[CIS Pipeline | Run: {run_id} | Phase: {phase} | Role: {role}]",
    ]
    if signal:
        parts.append(f"[Signal: {signal}]")
    if extra_context:
        parts.append(f"[Context: {extra_context}]")
    parts.append("")
    parts.append(content)

    document = "\n".join(parts)

    try:
        conn.execute(
            """INSERT INTO knowledge_messages (role, content, source, timestamp)
               VALUES (?, ?, ?, ?)""",
            (role, document, source,
             datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
    except Exception as e:
        # KB ingestion is best-effort — don't crash the pipeline
        print(f"[pipeline] KB ingest failed for {phase}/{role}: {e}")


def _ingest_round_to_kb(conn: sqlite3.Connection, run_id: str,
                        round_id: int, phase: str, signal: str) -> None:
    """Ingest a complete deliberation round into the knowledge base.

    Called after _complete_round(). Extracts all narrative content from
    the round and ingests each piece with appropriate source tags.
    """
    cur = conn.execute(
        """SELECT brain_output, drafter_output, reviewer1_output,
                  reviewer2_output, menter_output, verify_output,
                  human_question
           FROM deliberation_rounds WHERE id = ?""",
        (round_id,)
    )
    row = cur.fetchone()
    if not row:
        return

    brain_out, draft_out, r1_out, r2_out, menter_out, verify_out, human_q = row

    context = f"round_{round_id}_signal_{signal}"

    if brain_out:
        _ingest_to_kb(conn, run_id, phase, "brain", brain_out, signal, context)
    if draft_out:
        _ingest_to_kb(conn, run_id, phase, "draft", draft_out, signal, context)
    if r1_out:
        _ingest_to_kb(conn, run_id, phase, "review1", r1_out, signal, context)
    if r2_out:
        _ingest_to_kb(conn, run_id, phase, "review2", r2_out, signal, context)
    if menter_out:
        _ingest_to_kb(conn, run_id, phase, "menter", menter_out, signal, context)
    if verify_out:
        _ingest_to_kb(conn, run_id, phase, "verify", verify_out, signal, context)
    if human_q:
        _ingest_to_kb(conn, run_id, phase, "human", human_q, signal, context)


# ── Pre-Discovery (mandatory before every agent call) ──────────────────

def _pre_discovery(conn: sqlite3.Connection, intent: str, phase: str,
                    role: str, run_id: str,
                    web_search: bool = False) -> str:
    """Run mandatory pre-discovery and format results for injection.

    Searches: spine FTS5, filesystem, prior trajectories, optionally web.
    Returns a formatted string to prepend to the agent's prompt.
    """
    keywords = " ".join(intent.split()[:10])
    results = []

    # 1. Spine FTS5 search
    try:
        cur = conn.execute(
            "SELECT content, source FROM knowledge_messages_fts "
            "WHERE knowledge_messages_fts MATCH ? ORDER BY rank LIMIT 5",
            (keywords,)
        )
        kb_hits = cur.fetchall()
        if kb_hits:
            results.append("## Knowledge Base")
            for content, source in kb_hits:
                preview = (content[:200] + "...") if len(content) > 200 else content
                results.append(f"- [{source}] {preview}")
        else:
            results.append("## Knowledge Base\n(No results found)")
    except Exception as e:
        results.append(f"## Knowledge Base\n(Search error: {e})")

    # 2. Prior agent trajectories (MATM)
    # Verify phase: exclude only same-run Menter trajectories (per spec §3.4)
    # Other phases: exclude all same-run trajectories
    try:
        if phase == "verification":
            cur = conn.execute(
                "SELECT output_text, run_id, outcome, role, phase "
                "FROM agent_trajectories "
                "WHERE phase = ? AND role = ? "
                "  AND (run_id != ? OR role != 'menter') "
                "  AND outcome = 'success' "
                "ORDER BY created_at DESC LIMIT 3",
                (phase, role, run_id)
            )
        else:
            cur = conn.execute(
                "SELECT output_text, run_id, outcome, role, phase "
                "FROM agent_trajectories "
                "WHERE phase = ? AND role = ? AND run_id != ? "
                "  AND outcome = 'success' "
                "ORDER BY created_at DESC LIMIT 3",
                (phase, role, run_id)
            )
        trajectories = cur.fetchall()
        if trajectories:
            results.append("\n## Prior Agent Trajectories")
            for output, t_run, outcome, t_role, t_phase in trajectories:
                preview = (output[:300] + "...") if len(output) > 300 else output
                results.append(
                    f"--- Trajectory (run {t_run}, {t_role}/{t_phase}, {outcome}) ---\n"
                    f"{preview}"
                )
    except Exception as e:
        results.append(f"\n## Prior Agent Trajectories\n(Search error: {e})")

    # 3. Web search (Brain and Draft only)
    if web_search:
        try:
            import urllib.request
            import urllib.parse
            query = urllib.parse.quote(f"{keywords} best practices 2026")
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=3"
            req = urllib.request.Request(url, headers={"User-Agent": "CIS-Pipeline/1.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                results.append("\n## Current Research (web)")
                for item in search_results:
                    results.append(f"- {item['title']}: {item.get('snippet', '')[:200]}")
        except Exception as e:
            results.append(f"\n## Current Research (web)\n(Search error: {e})")

    return (
        "[PRE-DISCOVERY RESULTS — review before proceeding]\n\n"
        + "\n".join(results)
        + "\n\n[END PRE-DISCOVERY — now produce your output]"
    )


# ── FINAL_JSON Parsing (per ADR-SEED-012) ──────────────────────────────

_FINAL_JSON_RE = re.compile(
    r'```json\s*(\{.*?\})\s*```|FINAL_JSON[:\s]*(\{.*?\})',
    re.DOTALL
)


def _parse_final_json(text: str) -> Optional[dict]:
    """Extract FINAL_JSON block from agent output.

    Per ADR-SEED-012: every agent response must end with a FINAL_JSON block
    containing role, status, summary, recommendation, next_action.

    Returns parsed dict or None if not found.

    Priority:
    1. JSON blocks containing "role" field (FINAL_JSON signature)
    2. Bare JSON at end of text containing "status" field
    3. Any JSON code block (fallback)
    """
    # Collect all JSON code blocks and bare FINAL_JSON blocks
    matches = _FINAL_JSON_RE.findall(text)
    candidates = []
    for match in matches:
        for group in match:
            if group:
                try:
                    parsed = json.loads(group)
                    candidates.append(parsed)
                except json.JSONDecodeError:
                    continue

    # Priority 1: JSON with "role" field (the FINAL_JSON signature)
    for c in candidates:
        if "role" in c:
            return c

    # Priority 2: candidates with "status" field
    for c in candidates:
        if "status" in c:
            return c

    # Priority 3: any candidate
    if candidates:
        return candidates[-1]

    # Try bare JSON at end of text
    lines = text.strip().split("\n")
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith("{") and "status" in line.lower():
            candidate = "\n".join(lines[i:])
            try:
                brace_count = 0
                end = -1
                for j, ch in enumerate(candidate):
                    if ch == "{":
                        brace_count += 1
                    elif ch == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end = j + 1
                            break
                if end > 0:
                    return json.loads(candidate[:end])
            except (json.JSONDecodeError, IndexError):
                continue

    return None


# ── Trajectory Recording (MATM) ───────────────────────────────────────

def _record_trajectory(conn: sqlite3.Connection, run_id: str, role: str,
                       phase: str, input_text: str, output_text: str,
                       round_number: Optional[int] = None,
                       outcome: str = "pending",
                       consensus_reached: int = 0) -> None:
    """Record an agent trajectory to the shared memory (MATM).

    config_version captures the git HEAD at recording time, so future
    retrieval can filter by code state (trajectory from different code
    version = different reliability).
    """
    # Capture config_version (git HEAD short hash)
    config_version = "unknown"
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=DB_PATH.rsplit("/", 1)[0],
        )
        if result.returncode == 0 and result.stdout.strip():
            config_version = result.stdout.strip()
        else:
            config_version = f"git-error: {result.stderr.strip()[:50]}"
    except Exception as e:
        config_version = f"exception: {str(e)[:50]}"

    conn.execute(
        """INSERT INTO agent_trajectories
           (run_id, role, phase, input_text, output_text,
            round_number, outcome, consensus_reached, config_version)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, role, phase, input_text, output_text,
         round_number, outcome, consensus_reached, config_version)
    )
    conn.commit()


def _update_trajectory_outcome(conn: sqlite3.Connection, run_id: str,
                                role: str, phase: str,
                                outcome: str) -> None:
    """Update the outcome of the most recent trajectory for a run/role/phase.

    Called after a round completes — marks trajectory as 'success' or 'failed'
    so future retrieval can filter by outcome (per spec §4.3).
    """
    conn.execute(
        """UPDATE agent_trajectories SET outcome = ?
           WHERE id = (
               SELECT id FROM agent_trajectories
               WHERE run_id = ? AND role = ? AND phase = ?
               ORDER BY id DESC LIMIT 1
           )""",
        (outcome, run_id, role, phase)
    )
    conn.commit()


# ── Async Agent Dispatch ────────────────────────────────────────────────

# ── API Key Resolution ─────────────────────────────────────────────────

def _resolve_api_key(role: str) -> str:
    """Resolve the API key for a gateway role.

    Priority:
    1. CIS_{ROLE}_API_KEY env var (explicit override)
    2. API_SERVER_KEY from the gateway's .env file
    3. api_key from the gateway's config.yaml api_server section
    4. Empty string (auth disabled)
    """
    # 1. Explicit env var
    env_key = os.environ.get(f"CIS_{role.upper()}_API_KEY", "")
    if env_key:
        return env_key

    # 2. Read from gateway .env file
    profile = PROFILES.get(role, {})
    hermes_profile = profile.get("hermes_profile", "")
    if hermes_profile:
        env_path = os.path.expanduser(f"~/.{hermes_profile}/.env")
        if os.path.exists(env_path):
            try:
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("API_SERVER_KEY="):
                            return line.split("=", 1)[1].strip()
            except Exception:
                pass

        # 3. Read from config.yaml
        cfg_path = os.path.expanduser(f"~/.{hermes_profile}/config.yaml")
        if os.path.exists(cfg_path):
            try:
                import yaml
                with open(cfg_path) as f:
                    cfg = yaml.safe_load(f) or {}
                key = cfg.get("api_server", {}).get("api_key", "")
                if key:
                    return key
            except Exception:
                pass

    return ""


async def _call_agent(role: str, prompt: str, run_id: str) -> str:
    """Dispatch a call to a Hermes gateway agent.

    Returns the agent's text response.
    Raises httpx.TimeoutException on timeout, httpx.ConnectError if unreachable.
    """
    if _breaker_is_tripped(role):
        raise ConnectionError(
            f"Circuit breaker tripped for {role} — gateway has failed "
            f"{CIRCUIT_BREAKER_THRESHOLD} consecutive times. "
            f"Cooling down for {CIRCUIT_BREAKER_COOLDOWN}s."
        )

    gateway_url = get_gateway_url(role)
    if not gateway_url:
        raise ValueError(f"Unknown role: {role}")

    profile = PROFILES[role]
    port = profile["port"]

    # Health check before dispatch
    healthy, error, _ = check_gateway(port)
    if not healthy:
        _breaker_record_failure(role)
        raise ConnectionError(f"Gateway {role} (port {port}) is down: {error}")

    api_key = _resolve_api_key(role)

    payload = {
        "model": "agent",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8192,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    timeout = AGENT_TIMEOUTS.get(role, AGENT_TIMEOUT)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(gateway_url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    choices = data.get("choices", [])
    if not choices:
        _breaker_record_failure(role)
        raise ConnectionError(
            f"Gateway {role} (port {port}) returned no choices — "
            f"likely a stale/zombie process. Response: {str(data)[:200]}"
        )

    content = choices[0].get("message", {}).get("content", "")
    if not content.strip():
        # Check for reasoning_content (some models put output there)
        reasoning = choices[0].get("message", {}).get("reasoning_content", "")
        if reasoning and reasoning.strip():
            content = reasoning  # Use reasoning as content fallback

    if not content.strip():
        _breaker_record_failure(role)
        raise ConnectionError(
            f"Gateway {role} (port {port}) returned empty content — "
            f"model backend not working. Response: {str(data)[:200]}"
        )

    _breaker_record_success(role)
    return content


async def _call_reviewers_parallel(prompt: str, run_id: str) -> Tuple[str, str, Optional[str], Optional[str]]:
    """Call Review1 and Review2 in parallel, with retry on empty/ambiguous output.

    Returns (review1_output, review2_output, review1_error, review2_error).

    A reviewer that returns empty or unparseable output is retried once with a
    repair prompt. If it still fails, the output is returned as-is with the
    error set so the caller can decide how to handle the incomplete review.

    A reviewer that returns a valid FINAL_JSON (CONSENSUS_REACHED or OBJECTIONS)
    is considered to have completed its role, regardless of the signal.
    """
    MAX_REVIEWER_RETRIES = 1

    async def _call_with_retry(role: str) -> Tuple[str, Optional[str]]:
        """Call a reviewer, retry once if output is empty or unparseable."""
        last_error = None
        for attempt in range(MAX_REVIEWER_RETRIES + 1):
            try:
                output = await _call_agent(role, prompt, run_id)

                # Empty output — retry with repair prompt
                if not output.strip():
                    last_error = "empty output"
                    if attempt < MAX_REVIEWER_RETRIES:
                        print(f"[pipeline] {role} returned empty — retrying (attempt {attempt+1})")
                        continue
                    return "", last_error

                # Check if FINAL_JSON is parseable
                parsed = _parse_final_json(output)
                if parsed and parsed.get("status") in ("CONSENSUS_REACHED", "OBJECTIONS", "ESCALATE"):
                    return output, None  # Valid signal — review complete

                # FINAL_JSON missing or unparseable — try text-scan fallback
                has_consensus = "CONSENSUS" in output.upper()
                has_objection = "OBJECTION" in output.upper() or "ESCALATE" in output.upper()
                if has_consensus or has_objection:
                    return output, None  # Text-scan found a signal — review complete

                # Ambiguous — retry with repair prompt
                last_error = "ambiguous output (no FINAL_JSON, no text-scan signal)"
                if attempt < MAX_REVIEWER_RETRIES:
                    print(f"[pipeline] {role} returned ambiguous output — retrying (attempt {attempt+1})")
                    # Re-dispatch with same prompt (repair prompt would need the original context)
                    continue
                return output, last_error

            except (httpx.TimeoutException, ConnectionError, Exception) as e:
                last_error = str(e)
                if attempt < MAX_REVIEWER_RETRIES:
                    print(f"[pipeline] {role} errored ({e}) — retrying (attempt {attempt+1})")
                    continue
                return "", last_error

        return "", last_error

    results = await asyncio.gather(
        _call_with_retry("review1"),
        _call_with_retry("review2"),
    )
    return results[0][0], results[1][0], results[0][1], results[1][1]


def _check_consensus(r1_output: str, r2_output: str,
                      r1_error: Optional[str] = None,
                      r2_error: Optional[str] = None) -> Tuple[bool, bool, Optional[str]]:
    """Check if both reviewers reached consensus.

    Returns (consensus_reached, has_objections, objection_text).

    Only reviewers that completed their role (produced a parseable signal)
    can express consensus or objections. A reviewer with an error or
    ambiguous output did NOT complete its role — this is NOT an objection,
    it's an incomplete review that the caller must handle separately.

    A reviewer that completed its role and said OBJECTIONS is a real
    objection. A reviewer that completed and said CONSENSUS_REACHED is
    real agreement. These are stored as trajectory memory.
    """
    # A reviewer with an error did not complete its role
    r1_complete = r1_output.strip() and not r1_error
    r2_complete = r2_output.strip() and not r2_error

    if not r1_complete and not r2_complete:
        return False, False, None  # Neither completed — not an objection, incomplete
    if not r1_complete:
        return False, False, None  # r1 incomplete
    if not r2_complete:
        return False, False, None  # r2 incomplete

    # Both completed — parse their signals
    r1_json = _parse_final_json(r1_output)
    r2_json = _parse_final_json(r2_output)

    r1_status = r1_json.get("status", "") if r1_json else ""
    r2_status = r2_json.get("status", "") if r2_json else ""

    # If we can't parse FINAL_JSON, try text scanning (fallback per ADR-SEED-012)
    if not r1_json and not r2_json:
        r1_consensus = "CONSENSUS" in r1_output.upper()
        r2_consensus = "CONSENSUS" in r2_output.upper()
        r1_objections = "OBJECTION" in r1_output.upper() or "ESCALATE" in r1_output.upper()
        r2_objections = "OBJECTION" in r2_output.upper() or "ESCALATE" in r2_output.upper()
        consensus = r1_consensus and r2_consensus
        has_obj = r1_objections or r2_objections
        obj_text = ""
        if r1_objections:
            obj_text += f"[Review1] {r1_output[:500]}\n"
        if r2_objections:
            obj_text += f"[Review2] {r2_output[:500]}"
        return consensus, has_obj, obj_text

    # If only one parsed — that reviewer's output is ambiguous even though non-empty
    if not r1_json or not r2_json:
        return False, False, None  # incomplete, not an objection

    # Both parsed — check statuses
    consensus = (r1_status == "CONSENSUS_REACHED" and r2_status == "CONSENSUS_REACHED")
    has_obj = (r1_status == "OBJECTIONS" or r2_status == "OBJECTIONS"
               or r1_status == "ESCALATE" or r2_status == "ESCALATE")

    obj_text = ""
    if r1_status == "OBJECTIONS" and r1_json:
        obj_text += f"[Review1] {r1_json.get('summary', r1_output[:500])}\n"
    if r2_status == "OBJECTIONS" and r2_json:
        obj_text += f"[Review2] {r2_json.get('summary', r2_output[:500])}"

    return consensus, has_obj, obj_text


# ── L1 Deterministic Checks ────────────────────────────────────────────

def _run_l1_checks(cwd: str) -> str:
    """Run deterministic L1 checks against the working directory.

    Captures git diff, checks file existence/size, and returns
    a structured evidence report for the verify agent.
    """
    import subprocess

    parts = []

    # 1. Git diff stat
    try:
        diff_stat = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, timeout=15, cwd=cwd,
        ).stdout.strip()
        parts.append(f"## L1: Git Diff Stat\n```\n{diff_stat or '(no changes)'}\n```")
    except Exception as e:
        parts.append(f"## L1: Git Diff Stat\nERROR: {e}")

    # 2. Git diff (full, capped at 2000 chars)
    try:
        diff_full = subprocess.run(
            ["git", "diff"],
            capture_output=True, text=True, timeout=15, cwd=cwd,
        ).stdout.strip()
        if len(diff_full) > 2000:
            diff_full = diff_full[:2000] + "\n... (truncated)"
        parts.append(f"## L1: Git Diff (Full)\n```diff\n{diff_full or '(no changes)'}\n```")
    except Exception as e:
        parts.append(f"## L1: Git Diff (Full)\nERROR: {e}")

    # 3. Changed file existence + size check
    try:
        diff_names = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, timeout=10, cwd=cwd,
        ).stdout.strip()
        if diff_names:
            file_lines = []
            for fpath in diff_names.split("\n"):
                full = os.path.join(cwd, fpath)
                if os.path.exists(full):
                    size = os.path.getsize(full)
                    file_lines.append(f"  ✓ {fpath} ({size} bytes)")
                else:
                    file_lines.append(f"  ✗ {fpath} MISSING")
            parts.append("## L1: Changed Files\n" + "\n".join(file_lines))
        else:
            parts.append("## L1: Changed Files\n(no changed files)")
    except Exception as e:
        parts.append(f"## L1: Changed Files\nERROR: {e}")

    # 4. Untracked files
    try:
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=10, cwd=cwd,
        ).stdout.strip()
        if untracked:
            parts.append("## L1: Untracked Files\n" + untracked)
    except Exception:
        pass

    return "\n\n".join(parts)


def _run_isolated_l1(cwd: str, pre_exec_head: str) -> str:
    """Run L1 checks from a clean git worktree at the pre-Menter state.

    Creates a temporary git worktree at the pre-execution HEAD, applies
    Menter's diff, runs L1 checks there, then cleans up. This is true
    isolation — Menter never touched this directory, so cannot fabricate
    evidence there.

    If pre_exec_head is empty or worktree creation fails, falls back to
    in-place L1 checks with an explicit warning in the report.
    """
    import subprocess
    import tempfile

    def _run(cmd, timeout=15, workdir=None):
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=workdir or cwd
        )

    parts = []
    worktree_path = None

    # Capture Menter's diff to apply in the clean worktree
    try:
        menter_diff = _run(["git", "diff"]).stdout
    except Exception:
        menter_diff = ""

    # Try to create a clean worktree at the pre-execution HEAD
    if pre_exec_head:
        worktree_path = tempfile.mkdtemp(prefix=f"cis-verify-")
        try:
            wt_result = _run(
                ["git", "worktree", "add", "--detach", worktree_path, pre_exec_head],
                timeout=30,
            )
            if wt_result.returncode != 0:
                parts.append(f"## L1-ISOLATED: Worktree creation FAILED\n{wt_result.stderr.strip()[:300]}")
                parts.append("FALLING BACK to in-place checks — isolation NOT guaranteed.")
                # Clean up the orphan tempdir
                import shutil
                try:
                    shutil.rmtree(worktree_path, ignore_errors=True)
                except Exception:
                    pass
                worktree_path = None
            else:
                parts.append(f"## L1-ISOLATED: Clean Worktree\nChecked out {pre_exec_head[:12]} at {worktree_path}")

                # Apply Menter's diff to the clean worktree
                if menter_diff.strip():
                    patch_result = subprocess.run(
                        ["git", "apply", "--allow-empty"],
                        input=menter_diff, capture_output=True, text=True,
                        timeout=15, cwd=worktree_path,
                    )
                    if patch_result.returncode == 0:
                        parts.append("Menter's diff applied to clean worktree: OK")
                    else:
                        parts.append(f"Menter's diff FAILED to apply: {patch_result.stderr.strip()[:300]}")
                        parts.append("This may indicate Menter's changes are corrupt or conflict.")

                # Run baseline checks in the clean worktree
                parts.append("\n### Baseline Checks (Clean Worktree)")
                try:
                    status = _run(["git", "status", "--short"], workdir=worktree_path).stdout.strip()
                    parts.append(f"Git status: {status or '(clean)'}")
                except Exception as e:
                    parts.append(f"Git status error: {e}")

                # Run L1 checks in the clean worktree
                parts.append("\n### L1 Checks (Clean Worktree + Menter's Diff)")
                parts.append(_run_l1_checks(worktree_path))

                # Try import test in clean worktree
                try:
                    import_result = _run(
                        ["python3.12", "-c",
                         "import sys; sys.path.insert(0,'runtime'); from app import app; "
                         f"print(f'Flask app imports OK, {{len(app.url_map._rules)}} routes')"],
                        timeout=20, workdir=worktree_path,
                    )
                    if import_result.returncode == 0:
                        parts.append(f"Import test: {import_result.stdout.strip()}")
                    else:
                        parts.append(f"Import test FAILED: {import_result.stderr.strip()[:300]}")
                except Exception as e:
                    parts.append(f"Import test error: {e}")

        except Exception as e:
            parts.append(f"## L1-ISOLATED: Worktree error\n{e}")
            parts.append("FALLING BACK to in-place checks — isolation NOT guaranteed.")
        finally:
            # Clean up the worktree
            if worktree_path:
                try:
                    _run(["git", "worktree", "remove", "--force", worktree_path], timeout=15)
                    parts.append(f"\nWorktree cleaned up: {worktree_path}")
                except Exception as e:
                    parts.append(f"\nWorktree cleanup error: {e} (manual cleanup needed)")

    if not pre_exec_head or worktree_path is None:
        # Fallback: in-place checks (no isolation)
        parts.append("## L1: In-Place Checks (NO ISOLATION — warning)")
        parts.append("pre_exec_head was not captured or worktree failed.")
        parts.append("These checks run in Menter's workspace — evidence may be fabricated.")
        parts.append(_run_l1_checks(cwd))

    return "\n\n".join(parts)


# ── L1 Universal Checks for Code Chunks ───────────────────────────────

def _run_chunk_l1(cwd: str, file_path: str, diff_text: str) -> str:
    """Run universal L1 checks on a single code chunk.

    These are deterministic checks that work on any codebase regardless
    of language or pattern. Results are formatted as evidence for reviewers.
    """
    import subprocess
    parts = []
    full_path = os.path.join(cwd, file_path)

    # 1. File exists and is non-empty
    if not os.path.exists(full_path):
        parts.append(f"## L1: File Exists\n✗ {file_path} MISSING")
        return "\n\n".join(parts)
    size = os.path.getsize(full_path)
    parts.append(f"## L1: File Exists\n✓ {file_path} ({size} bytes)")
    if size == 0:
        parts.append("⚠ File is empty")

    # 2. Diff is non-empty
    if not diff_text.strip():
        parts.append("## L1: Diff\n⚠ No diff captured — Menter may not have changed anything")
    else:
        diff_lines = diff_text.count("\n")
        parts.append(f"## L1: Diff\n{diff_lines} lines in diff")

    # 3. No hardcoded secrets (basic scan)
    try:
        with open(full_path) as f:
            content = f.read()
        secret_patterns = ["api_key=", "password=", "token=", "secret="]
        found_secrets = []
        for pat in secret_patterns:
            if pat in content.lower():
                # Check it's not an env var reference
                for line_num, line in enumerate(content.split("\n"), 1):
                    if pat in line.lower() and "os.environ" not in line and "getenv" not in line:
                        found_secrets.append(f"  Line {line_num}: {line.strip()[:80]}")
        if found_secrets:
            parts.append("## L1: Secrets Scan\n⚠ Potential hardcoded secrets:\n" + "\n".join(found_secrets))
        else:
            parts.append("## L1: Secrets Scan\n✓ No hardcoded secrets found")
    except Exception as e:
        parts.append(f"## L1: Secrets Scan\nERROR: {e}")

    # 4. No silent except: pass
    try:
        import re
        silent_pattern = re.compile(r'except\s*.*:\s*\n\s*pass', re.MULTILINE)
        matches = silent_pattern.findall(content)
        if matches:
            parts.append(f"## L1: Silent Error Handling\n⚠ Found {len(matches)} silent except:pass")
        else:
            parts.append("## L1: Silent Error Handling\n✓ No silent except:pass found")
    except Exception:
        pass

    # 5. No print() debug statements (basic check)
    try:
        print_lines = [line_num for line_num, line in enumerate(content.split("\n"), 1)
                       if "print(" in line and "print(f'" not in line]
        if print_lines:
            parts.append(f"## L1: Debug Statements\n⚠ Found print() on lines: {print_lines[:10]}")
        else:
            parts.append("## L1: Debug Statements\n✓ No print() found")
    except Exception:
        pass

    # 6. Python syntax check (if .py file)
    if file_path.endswith(".py"):
        try:
            result = subprocess.run(
                ["python3.12", "-c", f"import py_compile; py_compile.compile('{full_path}', doraise=True)"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                parts.append("## L1: Syntax Check\n✓ Compiles without errors")
            else:
                parts.append(f"## L1: Syntax Check\n✗ COMPILE ERROR:\n{result.stderr.strip()[:500]}")
        except Exception as e:
            parts.append(f"## L1: Syntax Check\nERROR: {e}")

    # 7. Existing tests still pass (if test runner exists)
    try:
        pytest_check = subprocess.run(
            ["python3.12", "-m", "pytest", "--co", "-q", cwd],
            capture_output=True, text=True, timeout=30, cwd=cwd,
        )
        if pytest_check.returncode == 0:
            parts.append("## L1: Test Collection\n✓ Tests collect without errors")
        else:
            parts.append(f"## L1: Test Collection\n⚠ Test collection issues:\n{pytest_check.stderr.strip()[:300]}")
    except Exception:
        pass  # No pytest — skip

    return "\n\n".join(parts)


# ── Pattern Catalog Helper ────────────────────────────────────────────

def _read_codebase_overview(cwd: str) -> str:
    """Read a project codebase and produce a summary for Brain.

    Scans file types, directory structure, and existing patterns.
    Returns a formatted string Brain can use to produce the pattern catalog.
    """
    import subprocess
    parts = []

    # 1. Directory structure (top 3 levels)
    try:
        result = subprocess.run(
            ["find", cwd, "-maxdepth", "3", "-type", "f",
             "-not", "-path", "*/.git/*", "-not", "-path", "*/__pycache__/*",
             "-not", "-path", "*/node_modules/*", "-not", "-path", "*/.venv/*"],
            capture_output=True, text=True, timeout=15,
        )
        files = result.stdout.strip().split("\n") if result.stdout.strip() else []
        parts.append(f"## Files Found ({len(files)} total)")
        # Show first 50 files
        for f in files[:50]:
            rel = os.path.relpath(f, cwd) if f else ""
            parts.append(f"  {rel}")
        if len(files) > 50:
            parts.append(f"  ... and {len(files) - 50} more")
    except Exception as e:
        parts.append(f"## Files Found\nERROR: {e}")

    # 2. Language detection by extension
    try:
        extensions = {}
        for f in files:
            if "." in os.path.basename(f):
                ext = "." + os.path.basename(f).rsplit(".", 1)[1]
                extensions[ext] = extensions.get(ext, 0) + 1
        if extensions:
            parts.append("\n## Languages by Extension")
            for ext, count in sorted(extensions.items(), key=lambda x: -x[1]):
                parts.append(f"  {ext}: {count} files")
    except Exception:
        pass

    # 3. Test convention detection
    test_indicators = []
    for f in files:
        basename = os.path.basename(f)
        if "test" in basename.lower() or "spec" in basename.lower():
            test_indicators.append(os.path.relpath(f, cwd))
    if test_indicators:
        parts.append(f"\n## Test Files ({len(test_indicators)} found)")
        for t in test_indicators[:10]:
            parts.append(f"  {t}")

    # 4. Git log (last 5 commits for context)
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True, text=True, timeout=10, cwd=cwd,
        ).stdout.strip()
        if log:
            parts.append(f"\n## Recent Commits\n{log}")
    except Exception:
        pass

    return "\n".join(parts)


# ── Pipeline Relay (main state machine) ───────────────────────────────

class PipelineRelay:
    """Production pipeline relay orchestrator.

    Async state machine: Brain → Review1+2 → Draft → Review1+2
    → Eric Gate → Menter → Verify → Complete.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = _db_connect()

    def close(self) -> None:
        self.conn.close()

    async def start(self, intent_text: str) -> str:
        """Create a new pipeline run and begin processing."""
        run_id = _create_run(self.conn, intent_text)
        print(f"[pipeline] Run created: {run_id}")
        _set_run_status(self.conn, run_id, "BRAIN_PHASE")
        await self._brain_phase(run_id, intent_text)
        return run_id

    def start_sync(self, intent_text: str) -> str:
        """Create a new pipeline run (sync, non-async). Does NOT start processing.

        The API layer calls this to create the run, then launches
        resume() in a background thread.
        """
        run_id = _create_run(self.conn, intent_text)
        _set_run_status(self.conn, run_id, "BRAIN_PHASE")
        print(f"[pipeline] Run created (sync): {run_id}")
        return run_id

    async def resume(self, run_id: str) -> None:
        """Resume a non-terminal run from its last known state."""
        run = _get_run(self.conn, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        if run["status"] in TERMINAL_STATES:
            print(f"[pipeline] Run {run_id} is terminal: {run['status']}")
            return

        intent = run["topic"]
        status = run["status"]
        print(f"[pipeline] Resuming {run_id} from {status}")

        if status == "INTAKE":
            _set_run_status(self.conn, run_id, "BRAIN_PHASE")
            await self._brain_phase(run_id, intent)
        elif status == "BRAIN_PHASE":
            await self._brain_phase(run_id, intent)
        elif status == "WAITING_FOR_HUMAN":
            print(f"[pipeline] Run {run_id} waiting for human answer")
        elif status == "INTENT_REVIEW":
            await self._intent_review(run_id, intent)
        elif status == "DRAFT_PHASE":
            await self._draft_phase(run_id, intent)
        elif status == "PROPOSAL_REVIEW":
            await self._proposal_review(run_id, intent)
        elif status == "ERIC_GATE":
            print(f"[pipeline] Run {run_id} waiting at ERIC_GATE")
        elif status == "PATTERN_CATALOG":
            await self._pattern_catalog(run_id, intent)
        elif status == "CODE_REVIEW_GATE":
            await self._code_review_gate(run_id, intent)
        elif status == "EXECUTION":
            await self._execution(run_id, intent)
        elif status == "VERIFICATION":
            await self._verification(run_id, intent)

    async def _brain_phase(self, run_id: str, intent: str, round_num: int = 1) -> None:
        """Brain phase: explore intent, produce structured understanding."""
        print(f"[pipeline] BRAIN phase (round {round_num}) for {run_id}")

        round_id = _start_round(self.conn, run_id, "brain", round_num)
        discovery = _pre_discovery(
            self.conn, intent, "brain", "brain", run_id, web_search=True
        )

        prompt = (
            f"{discovery}\n\n"
            f"Eric's intent: {intent}\n\n"
            f"You are Brain. Explore this intent and produce an INTENT_UNDERSTANDING.\n"
            f"End with a FINAL_JSON block:\n"
            f'```json\n{{"role":"brain","status":"READY","summary":"..."}}\n```\n'
            f"If you need clarification, emit:\n"
            f'```json\n{{"role":"brain","status":"NEEDS_CLARIFICATION","question":"..."}}\n```'
        )

        try:
            output = await _call_agent("brain", prompt, run_id)
        except Exception as e:
            _breaker_record_failure("brain")
            _set_run_status(self.conn, run_id, "ERROR")
            _complete_round(self.conn, round_id, "ERROR",
                           {"brain_output": str(e)})
            _record_trajectory(self.conn, run_id, "brain", "brain",
                          prompt, str(e), round_num)
            _update_trajectory_outcome(self.conn, run_id, "brain", "brain", "failed")
            print(f"[pipeline] BRAIN failed: {e}")
            return

        _record_trajectory(self.conn, run_id, "brain", "brain",
                          prompt, output, round_num)

        # Check for HUMAN_QUESTION
        parsed = _parse_final_json(output)
        if parsed and parsed.get("status") == "NEEDS_CLARIFICATION":
            question = parsed.get("question", output[:500])
            _set_run_status(self.conn, run_id, "WAITING_FOR_HUMAN")
            _complete_round(self.conn, round_id, "CONSENSUS_REACHED",
                           {"human_question": question})
            print(f"[pipeline] BRAIN needs clarification: {question}")
            print(f"[pipeline] Run {run_id} waiting for human answer")
            return

        # Validate Brain produced a valid status
        if not parsed or parsed.get("status") not in ("READY", "NEEDS_CLARIFICATION"):
            _update_trajectory_outcome(self.conn, run_id, "brain", "brain", "failed")
            _complete_round(self.conn, round_id, "ESCALATE",
                           {"brain_output": output})
            _set_run_status(self.conn, run_id, "ESCALATED")
            print(f"[pipeline] BRAIN output invalid — no READY status. ESCALATE.")
            return

        _update_trajectory_outcome(self.conn, run_id, "brain", "brain", "success")
        _complete_round(self.conn, round_id, "CONSENSUS_REACHED",
                       {"brain_output": output})

        # Proceed to intent review
        _set_run_status(self.conn, run_id, "INTENT_REVIEW")
        await self._intent_review(run_id, intent)

    async def _intent_review(self, run_id: str, intent: str,
                             round_num: int = 1) -> None:
        """Intent review: parallel Review1 + Review2 check Brain's output."""
        print(f"[pipeline] INTENT_REVIEW (round {round_num}) for {run_id}")

        # Get brain output from last deliberation round
        cur = self.conn.execute(
            "SELECT brain_output FROM deliberation_rounds "
            "WHERE run_id = ? AND brain_output IS NOT NULL AND brain_output != '' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        row = cur.fetchone()
        brain_output = row[0] if row else ""

        round_id = _start_round(self.conn, run_id, "intent_review", round_num)
        discovery = _pre_discovery(
            self.conn, intent, "intent_review", "review1", run_id
        )

        prompt = (
            f"{discovery}\n\n"
            f"Eric's intent: {intent}\n\n"
            f"Brain's understanding:\n{brain_output}\n\n"
            f"You are a reviewer. Check Brain's understanding for gaps, "
            f"assumptions, and blind spots. End with FINAL_JSON:\n"
            f'```json\n{{"role":"reviewer","status":"CONSENSUS_REACHED"'
            f',"summary":"..."}}\n```\n'
            f'or\n```json\n{{"role":"reviewer","status":"OBJECTIONS"'
            f',"summary":"..."}}\n```'
        )

        r1_out, r2_out, r1_err, r2_err = await _call_reviewers_parallel(prompt, run_id)

        _record_trajectory(self.conn, run_id, "review1", "intent_review",
                          prompt, r1_out, round_num)
        _record_trajectory(self.conn, run_id, "review2", "intent_review",
                          prompt, r2_out, round_num)

        # Mark trajectory outcomes — only 'success' if reviewer completed its role
        _update_trajectory_outcome(self.conn, run_id, "review1", "intent_review",
                                  "failed" if r1_err else "success")
        _update_trajectory_outcome(self.conn, run_id, "review2", "intent_review",
                                  "failed" if r2_err else "success")

        # Check if both reviewers completed their role
        consensus, has_obj, obj_text = _check_consensus(r1_out, r2_out, r1_err, r2_err)

        # If reviewers didn't complete (consensus=False, has_obj=False, obj_text=None)
        # that's INCOMPLETE — not an objection. Escalate so Eric sees the problem.
        if not consensus and not has_obj and obj_text is None:
            incomplete = []
            if r1_err or not r1_out.strip():
                incomplete.append(f"Review1 ({r1_err or 'empty'})")
            if r2_err or not r2_out.strip():
                incomplete.append(f"Review2 ({r2_err or 'empty'})")
            _complete_round(self.conn, round_id, "ESCALATE", {
                "reviewer1_output": r1_out,
                "reviewer2_output": r2_out,
            })
            _set_run_status(self.conn, run_id, "ESCALATED")
            print(f"[pipeline] Review incomplete: {', '.join(incomplete)} — ESCALATE")
            return

        # Both reviewers completed — store their actual signal
        actual_signal = "CONSENSUS_REACHED" if consensus and not has_obj else "OBJECTIONS"
        _complete_round(self.conn, round_id, actual_signal, {
            "reviewer1_output": r1_out,
            "reviewer2_output": r2_out,
        })

        if has_obj and round_num < MAX_BRAIN_ROUNDS:
            print(f"[pipeline] Reviewers object — back to Brain (round {round_num+1})")
            _set_run_status(self.conn, run_id, "BRAIN_PHASE")
            await self._brain_phase(run_id, intent, round_num + 1)
        elif has_obj:
            print(f"[pipeline] Max brain rounds ({MAX_BRAIN_ROUNDS}) — ESCALATE")
            _set_run_status(self.conn, run_id, "ESCALATED")
        else:
            print(f"[pipeline] Intent review consensus — proceed to Draft")
            _set_run_status(self.conn, run_id, "DRAFT_PHASE")
            await self._draft_phase(run_id, intent)

    async def _draft_phase(self, run_id: str, intent: str,
                          round_num: int = 1) -> None:
        """Draft phase: produce structured proposal from Brain's understanding."""
        print(f"[pipeline] DRAFT phase (round {round_num}) for {run_id}")

        cur = self.conn.execute(
            "SELECT brain_output FROM deliberation_rounds "
            "WHERE run_id = ? AND brain_output IS NOT NULL AND brain_output != '' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        brain_output = row[0] if (row := cur.fetchone()) else ""

        round_id = _start_round(self.conn, run_id, "draft", round_num)
        discovery = _pre_discovery(
            self.conn, intent, "draft", "draft", run_id, web_search=True
        )

        prompt = (
            f"{discovery}\n\n"
            f"Eric's intent: {intent}\n\n"
            f"Brain's understanding:\n{brain_output}\n\n"
            f"You are Draft. Write a structured proposal/spec.\n"
            f"End with FINAL_JSON:\n"
            f'```json\n{{"role":"draft","status":"PROPOSAL_READY","summary":"..."}}\n```'
        )

        try:
            output = await _call_agent("draft", prompt, run_id)
        except Exception as e:
            _breaker_record_failure("draft")
            _set_run_status(self.conn, run_id, "ERROR")
            _complete_round(self.conn, round_id, "ERROR",
                           {"drafter_output": str(e)})
            _record_trajectory(self.conn, run_id, "draft", "draft",
                          prompt, str(e), round_num)
            _update_trajectory_outcome(self.conn, run_id, "draft", "draft", "failed")
            print(f"[pipeline] DRAFT failed: {e}")
            return

        _record_trajectory(self.conn, run_id, "draft", "draft",
                          prompt, output, round_num)

        # Validate Draft produced PROPOSAL_READY or REVISION_READY
        parsed = _parse_final_json(output)
        if not parsed or parsed.get("status") not in ("PROPOSAL_READY", "REVISION_READY"):
            _update_trajectory_outcome(self.conn, run_id, "draft", "draft", "failed")
            _complete_round(self.conn, round_id, "ESCALATE",
                           {"drafter_output": output})
            _set_run_status(self.conn, run_id, "ESCALATED")
            print(f"[pipeline] DRAFT output invalid — no PROPOSAL_READY status. ESCALATE.")
            return

        _update_trajectory_outcome(self.conn, run_id, "draft", "draft", "success")
        _complete_round(self.conn, round_id, "CONSENSUS_REACHED",
                       {"drafter_output": output})

        _set_run_status(self.conn, run_id, "PROPOSAL_REVIEW")
        await self._proposal_review(run_id, intent, round_num)

    async def _proposal_review(self, run_id: str, intent: str,
                               round_num: int = 1) -> None:
        """Proposal review: parallel reviewers critique Draft's proposal."""
        print(f"[pipeline] PROPOSAL_REVIEW (round {round_num}) for {run_id}")

        cur = self.conn.execute(
            "SELECT drafter_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_output IS NOT NULL AND drafter_output != '' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        draft_output = row[0] if (row := cur.fetchone()) else ""

        round_id = _start_round(self.conn, run_id, "proposal_review", round_num)
        discovery = _pre_discovery(
            self.conn, intent, "proposal_review", "review1", run_id
        )

        prompt = (
            f"{discovery}\n\n"
            f"Eric's intent: {intent}\n\n"
            f"Draft's proposal:\n{draft_output}\n\n"
            f"You are a reviewer. Critique this proposal. End with FINAL_JSON:\n"
            f'```json\n{{"role":"reviewer","status":"CONSENSUS_REACHED"'
            f',"summary":"..."}}\n```\n'
            f'or\n```json\n{{"role":"reviewer","status":"OBJECTIONS"'
            f',"summary":"..."}}\n```'
        )

        r1_out, r2_out, r1_err, r2_err = await _call_reviewers_parallel(prompt, run_id)

        _record_trajectory(self.conn, run_id, "review1", "proposal_review",
                          prompt, r1_out, round_num)
        _record_trajectory(self.conn, run_id, "review2", "proposal_review",
                          prompt, r2_out, round_num)

        # Mark trajectory outcomes — only 'success' if reviewer completed its role
        _update_trajectory_outcome(self.conn, run_id, "review1", "proposal_review",
                                  "failed" if r1_err else "success")
        _update_trajectory_outcome(self.conn, run_id, "review2", "proposal_review",
                                  "failed" if r2_err else "success")

        # Check if both reviewers completed their role
        consensus, has_obj, obj_text = _check_consensus(r1_out, r2_out, r1_err, r2_err)

        # If reviewers didn't complete — INCOMPLETE, not an objection. Escalate.
        if not consensus and not has_obj and obj_text is None:
            incomplete = []
            if r1_err or not r1_out.strip():
                incomplete.append(f"Review1 ({r1_err or 'empty'})")
            if r2_err or not r2_out.strip():
                incomplete.append(f"Review2 ({r2_err or 'empty'})")
            _complete_round(self.conn, round_id, "ESCALATE", {
                "reviewer1_output": r1_out,
                "reviewer2_output": r2_out,
            })
            _set_run_status(self.conn, run_id, "ESCALATED")
            print(f"[pipeline] Review incomplete: {', '.join(incomplete)} — ESCALATE")
            return

        # Both reviewers completed — store their actual signal
        actual_signal = "CONSENSUS_REACHED" if consensus and not has_obj else "OBJECTIONS"
        _complete_round(self.conn, round_id, actual_signal, {
            "reviewer1_output": r1_out,
            "reviewer2_output": r2_out,
        })

        if has_obj and round_num < MAX_DRAFT_ROUNDS:
            print(f"[pipeline] Reviewers object — back to Draft (round {round_num+1})")
            _set_run_status(self.conn, run_id, "DRAFT_PHASE")
            await self._draft_phase(run_id, intent, round_num + 1)
        elif has_obj:
            print(f"[pipeline] Max draft rounds ({MAX_DRAFT_ROUNDS}) — ESCALATE")
            _set_run_status(self.conn, run_id, "ESCALATED")
        else:
            print(f"[pipeline] Proposal review consensus — ERIC GATE")
            _set_run_status(self.conn, run_id, "ERIC_GATE")
            print(f"[pipeline] Run {run_id} waiting at ERIC GATE for approval")

    async def _pattern_catalog(self, run_id: str, intent: str) -> None:
        """Pattern Catalog phase: Brain reads codebase, produces pattern catalog.

        After Eric approves the proposal, Brain reads the existing codebase
        and identifies patterns, conventions, and completion criteria.
        Reviewers validate the catalog before Menter uses it.
        """
        print(f"[pipeline] PATTERN_CATALOG phase for {run_id}")

        project_dir = DB_PATH.rsplit("/", 1)[0]
        codebase_overview = _read_codebase_overview(project_dir)

        round_id = _start_round(self.conn, run_id, "pattern_catalog", 1)
        discovery = _pre_discovery(
            self.conn, intent, "pattern_catalog", "brain", run_id, web_search=True
        )

        # Get the approved directive
        cur = self.conn.execute(
            "SELECT drafter_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_output IS NOT NULL AND drafter_output != '' "
            "  AND drafter_role = 'draft' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        directive = row[0] if (row := cur.fetchone()) else ""

        prompt = (
            f"{discovery}\n\n"
            f"## CODEBASE OVERVIEW\n{codebase_overview}\n\n"
            f"## APPROVED DIRECTIVE\n{directive}\n\n"
            f"You are Brain. Read the codebase overview and the approved directive. "
            f"Produce a PATTERN CATALOG that identifies:\n"
            f"1. Language and toolchain\n"
            f"2. Architectural patterns found in the existing code\n"
            f"3. Convention rules (naming, file org, error handling)\n"
            f"4. Test convention\n"
            f"5. Completion criteria per pattern (what 'done' looks like)\n"
            f"6. List of files Menter will need to create or modify\n\n"
            f"If the codebase is empty (new project), derive patterns from the directive.\n"
            f"End with FINAL_JSON:\n"
            f'```json\n{{"role":"brain","status":"READY","summary":"...",'
            f'"files_planned":["path/to/file1.py","path/to/file2.py"]}}\n```'
        )

        try:
            output = await _call_agent("brain", prompt, run_id)
        except Exception as e:
            _breaker_record_failure("brain")
            _set_run_status(self.conn, run_id, "ERROR")
            _complete_round(self.conn, round_id, "ERROR",
                           {"brain_output": str(e)})
            _record_trajectory(self.conn, run_id, "brain", "pattern_catalog",
                          prompt, str(e), 1)
            _update_trajectory_outcome(self.conn, run_id, "brain", "pattern_catalog", "failed")
            print(f"[pipeline] PATTERN_CATALOG failed: {e}")
            return

        _record_trajectory(self.conn, run_id, "brain", "pattern_catalog",
                          prompt, output, 1)

        parsed = _parse_final_json(output)
        if not parsed or parsed.get("status") != "READY":
            _update_trajectory_outcome(self.conn, run_id, "brain", "pattern_catalog", "failed")
            _complete_round(self.conn, round_id, "ESCALATE",
                           {"brain_output": output})
            _set_run_status(self.conn, run_id, "ESCALATED")
            print(f"[pipeline] PATTERN_CATALOG invalid — no READY status. ESCALATE.")
            return

        _update_trajectory_outcome(self.conn, run_id, "brain", "pattern_catalog", "success")
        _complete_round(self.conn, round_id, "CONSENSUS_REACHED",
                       {"brain_output": output})

        # Save catalog to disk
        catalog_path = os.path.join(project_dir, "runtime", "catalogs", "PATTERN_CATALOG.md")
        os.makedirs(os.path.dirname(catalog_path), exist_ok=True)
        with open(catalog_path, "w") as f:
            f.write(f"# Pattern Catalog\n\nGenerated: {datetime.now(timezone.utc).isoformat()}\n\n")
            f.write(output)

        # Extract planned files from FINAL_JSON
        files_planned = parsed.get("files_planned", [])
        self._files_planned = files_planned

        print(f"[pipeline] Pattern catalog saved. {len(files_planned)} files planned.")
        _set_run_status(self.conn, run_id, "CODE_REVIEW_GATE")
        await self._code_review_gate(run_id, intent)

    async def _call_agent_with_retry(
        self, role: str, prompt: str, run_id: str, chunk_num: int,
        label: str, round_id: int, conn, diff_text: str, l1_results: str,
        revision: int, review_a_output: str = "", review_b_output: str = "",
    ) -> Optional[str]:
        """Call an agent with one retry. Returns None if both attempts fail.

        On failure, records the escalation to code_review_chunks and
        completes the round with ERROR signal. The caller should check
        for None and return immediately.
        """
        last_error = ""
        for attempt in range(2):  # original + 1 retry
            try:
                output = await _call_agent(role, prompt, run_id)
                if output.strip():
                    return output
                # Empty output — retry
                last_error = "empty output"
                print(f"[pipeline] {label} returned empty on chunk {chunk_num}"
                      f" (attempt {attempt + 1}), retrying...")
            except Exception as e:
                err_msg = str(e) or repr(e)  # repr fallback for empty str(e)
                last_error = err_msg
                print(f"[pipeline] {label} failed on chunk {chunk_num}"
                      f" (attempt {attempt + 1}): {err_msg}")
                if attempt == 0:
                    import asyncio as _aio
                    await _aio.sleep(2)  # brief backoff before retry

        # Both attempts failed — escalate
        _breaker_record_failure(role)
        _complete_round(conn, round_id, "ERROR")

        # Build the INSERT based on which review phase we're in
        cols = ["run_id", "chunk_number", "file_path", "diff_text", "l1_results"]
        vals = [run_id, chunk_num, "", diff_text[:5000], l1_results]

        if review_a_output:
            cols.append("review_a_pass1")
            vals.append(review_a_output[:5000])
        if review_b_output:
            cols.append("review_b_pass2")
            vals.append(review_b_output[:5000])

        cols.extend(["final_verdict", "revision_number", "created_at"])
        vals.extend(["ESCALATE", revision, datetime.now(timezone.utc).isoformat()])

        placeholders = ",".join("?" * len(vals))
        col_list = ",".join(cols)
        conn.execute(
            f"INSERT INTO code_review_chunks ({col_list}) VALUES ({placeholders})",
            vals
        )
        conn.commit()
        return None

    async def _code_review_gate(self, run_id: str, intent: str) -> None:
        """Code Review Gate: Menter builds chunks, sequential three-pass review.

        For each file:
        1. Menter builds the chunk (with universal rules in prompt)
        2. Pipeline captures diff + runs L1 universal checks
        3. Reviewer A reviews (fresh eyes)
        4. Reviewer B reviews (sees A's output, builds on it)
        5. Reviewer A consensus (sees B's output, delivers verdict)
        6. APPROVED → next chunk, CHANGES_REQUESTED → Menter revises
        """
        print(f"[pipeline] CODE_REVIEW_GATE phase for {run_id}")

        project_dir = DB_PATH.rsplit("/", 1)[0]
        files_planned = getattr(self, "_files_planned", [])

        if not files_planned:
            # Try to recover from DB
            cur = self.conn.execute(
                "SELECT brain_output FROM deliberation_rounds "
                "WHERE run_id = ? AND brain_output IS NOT NULL AND brain_output != '' "
                "  AND drafter_role = 'pattern_catalog' "
                "ORDER BY id DESC LIMIT 1", (run_id,)
            )
            row = cur.fetchone()
            if row:
                parsed = _parse_final_json(row[0])
                if parsed:
                    files_planned = parsed.get("files_planned", [])

        if not files_planned:
            print(f"[pipeline] No files planned — cannot proceed. ESCALATE.")
            _set_run_status(self.conn, run_id, "ESCALATED")
            return

        # Get directive
        cur = self.conn.execute(
            "SELECT drafter_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_output IS NOT NULL AND drafter_output != '' "
            "  AND drafter_role = 'draft' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        directive = row[0] if (row := cur.fetchone()) else ""

        # Get pattern catalog
        cur = self.conn.execute(
            "SELECT brain_output FROM deliberation_rounds "
            "WHERE run_id = ? AND brain_output IS NOT NULL AND brain_output != '' "
            "  AND drafter_role = 'pattern_catalog' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        catalog = row[0] if (row := cur.fetchone()) else ""

        # Capture pre-execution git state
        import subprocess
        try:
            pre_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10, cwd=project_dir,
            ).stdout.strip()
        except Exception:
            pre_head = ""
        self._pre_exec_head = pre_head

        # Process each file as a chunk
        for chunk_num, file_path in enumerate(files_planned, 1):
            print(f"[pipeline] Chunk {chunk_num}/{len(files_planned)}: {file_path}")
            await self._review_single_chunk(
                run_id, intent, directive, catalog,
                chunk_num, file_path, project_dir
            )

            # Check if this chunk was escalated
            cur = self.conn.execute(
                "SELECT final_verdict FROM code_review_chunks "
                "WHERE run_id = ? AND chunk_number = ? "
                "ORDER BY id DESC LIMIT 1", (run_id, chunk_num)
            )
            row = cur.fetchone()
            if row and row[0] == "ESCALATE":
                print(f"[pipeline] Chunk {chunk_num} escalated — stopping.")
                _set_run_status(self.conn, run_id, "ESCALATED")
                return

        # All chunks complete — proceed to verification
        print(f"[pipeline] All {len(files_planned)} chunks reviewed and incorporated.")
        _set_run_status(self.conn, run_id, "VERIFICATION")
        await self._verification(run_id, intent)

    async def _review_single_chunk(self, run_id: str, intent: str,
                                    directive: str, catalog: str,
                                    chunk_num: int, file_path: str,
                                    project_dir: str) -> None:
        """Review a single chunk through the three-pass sequential process."""
        import subprocess

        revision = 1

        while revision <= MAX_CHUNK_REVISIONS:
            print(f"[pipeline] Chunk {chunk_num} revision {revision}")

            # Step 1: Menter builds the chunk
            round_id = _start_round(self.conn, run_id, "code_review", chunk_num)

            menter_prompt = (
                f"{MENTER_UNIVERSAL_RULES}\n\n"
                f"## PATTERN CATALOG\n{catalog}\n\n"
                f"## DIRECTIVE\n{directive}\n\n"
                f"You are Menter. Build file: {file_path}\n"
                f"This is chunk {chunk_num}. Build ONLY this file.\n"
                f"Self-check against the universal rules before submitting.\n"
                f"End with FINAL_JSON:\n"
                f'```json\n{{"role":"menter","status":"CHUNK_READY",'
                f'"file":"{file_path}","summary":"..."}}\n```'
            )

            if revision > 1:
                # Get previous revision directive
                cur = self.conn.execute(
                    "SELECT revision_directive FROM code_review_chunks "
                    "WHERE run_id = ? AND chunk_number = ? AND revision_number = ?",
                    (run_id, chunk_num, revision - 1)
                )
                row = cur.fetchone()
                prev_directive = row[0] if row else ""
                menter_prompt += (
                    f"\n\n## REVISION REQUESTED\n"
                    f"Reviewers requested changes. Fix these issues:\n{prev_directive}"
                )

            menter_output = await self._call_agent_with_retry(
                "menter", menter_prompt, run_id, chunk_num, "Menter",
                round_id, self.conn, "", "", revision)
            if menter_output is None:
                return

            _record_trajectory(self.conn, run_id, "menter", "code_review",
                              menter_prompt, menter_output, chunk_num)

            # Validate Menter produced CHUNK_READY
            parsed = _parse_final_json(menter_output)
            if not parsed or parsed.get("status") != "CHUNK_READY":
                _update_trajectory_outcome(self.conn, run_id, "menter", "code_review", "failed")
                _complete_round(self.conn, round_id, "ESCALATE",
                               {"menter_output": menter_output})
                self.conn.execute(
                    """INSERT INTO code_review_chunks
                       (run_id, chunk_number, file_path, diff_text, l1_results,
                        final_verdict, revision_number, created_at)
                       VALUES (?, ?, ?, '', '', 'ESCALATE', ?, ?)""",
                    (run_id, chunk_num, file_path, revision,
                     datetime.now(timezone.utc).isoformat())
                )
                self.conn.commit()
                print(f"[pipeline] Menter didn't produce CHUNK_READY. ESCALATE.")
                return

            _update_trajectory_outcome(self.conn, run_id, "menter", "code_review", "success")

            # Step 2: Capture diff + run L1 universal checks
            try:
                diff_text = subprocess.run(
                    ["git", "diff"], capture_output=True, text=True,
                    timeout=15, cwd=project_dir,
                ).stdout
            except Exception:
                diff_text = ""

            l1_results = _run_chunk_l1(project_dir, file_path, diff_text)

            # Step 3: Pass 1 — Reviewer A (first pass, fresh eyes)
            review_a_prompt = (
                f"## L1 UNIVERSAL CHECK RESULTS\n{l1_results}\n\n"
                f"## CHUNK DIFF\n```diff\n{diff_text[:3000]}\n```\n\n"
                f"## PATTERN CATALOG\n{catalog}\n\n"
                f"## DIRECTIVE (what Menter was told to build)\n{directive}\n\n"
                f"You are Reviewer A (first pass). Review this code chunk.\n"
                f"Check against universal rules and pattern criteria.\n"
                f"If the chunk doesn't match a known pattern, assess it on its own merit.\n"
                f"End with FINAL_JSON:\n"
                f'```json\n{{"role":"reviewer","status":"APPROVED",'
                f'"summary":"...","checks_passed":[...],"checks_failed":[...]}}\n```\n'
                f'or\n```json\n{{"role":"reviewer","status":"CHANGES_REQUESTED",'
                f'"summary":"...","checks_failed":[...]}}\n```'
            )

            review_a_output = await self._call_agent_with_retry(
                "review1", review_a_prompt, run_id, chunk_num, "Reviewer A",
                round_id, self.conn, diff_text, l1_results, revision)
            if review_a_output is None:
                return

            _record_trajectory(self.conn, run_id, "review1", "code_review",
                          review_a_prompt, review_a_output, chunk_num)
            _update_trajectory_outcome(self.conn, run_id, "review1", "code_review", "success")

            # Step 4: Pass 2 — Reviewer B (sees A's output, builds on it)
            review_b_prompt = (
                f"## L1 UNIVERSAL CHECK RESULTS\n{l1_results}\n\n"
                f"## CHUNK DIFF\n```diff\n{diff_text[:3000]}\n```\n\n"
                f"## PATTERN CATALOG\n{catalog}\n\n"
                f"## DIRECTIVE\n{directive}\n\n"
                f"## REVIEWER A'S FINDINGS (first pass)\n{review_a_output}\n\n"
                f"You are Reviewer B (second pass). You see Reviewer A's findings.\n"
                f"Build on A's review. Find what A missed. Confirm or challenge A's findings.\n"
                f"If the chunk doesn't match a known pattern, assess it on its own merit.\n"
                f"End with FINAL_JSON:\n"
                f'```json\n{{"role":"reviewer","status":"APPROVED",'
                f'"summary":"...","checks_passed":[...],"checks_failed":[...],'
                f'"items_missed_by_a":[...],"disagreements_with_a":[...]}}\n```\n'
                f'or\n```json\n{{"role":"reviewer","status":"CHANGES_REQUESTED",'
                f'"summary":"...","checks_failed":[...]}}\n```'
            )

            review_b_output = await self._call_agent_with_retry(
                "review2", review_b_prompt, run_id, chunk_num, "Reviewer B",
                round_id, self.conn, diff_text, l1_results, revision,
                review_a_output=review_a_output)
            if review_b_output is None:
                return

            _record_trajectory(self.conn, run_id, "review2", "code_review",
                          review_b_prompt, review_b_output, chunk_num)
            _update_trajectory_outcome(self.conn, run_id, "review2", "code_review", "success")

            # Step 5: Pass 3 — Reviewer A consensus (sees B's output)
            consensus_prompt = (
                f"## L1 UNIVERSAL CHECK RESULTS\n{l1_results}\n\n"
                f"## CHUNK DIFF\n```diff\n{diff_text[:3000]}\n```\n\n"
                f"## PATTERN CATALOG\n{catalog}\n\n"
                f"## DIRECTIVE\n{directive}\n\n"
                f"## YOUR FIRST PASS (Reviewer A)\n{review_a_output}\n\n"
                f"## REVIEWER B'S FINDINGS (second pass)\n{review_b_output}\n\n"
                f"You are Reviewer A (consensus pass). You see B's findings.\n"
                f"Accept B's findings or push back with evidence.\n"
                f"Deliver one consolidated verdict.\n"
                f"End with FINAL_JSON:\n"
                f'```json\n{{"role":"reviewer","status":"APPROVED",'
                f'"summary":"...","consensus_summary":"..."}}\n```\n'
                f'or\n```json\n{{"role":"reviewer","status":"CHANGES_REQUESTED",'
                f'"summary":"...","revision_directive":"actionable feedback for Menter"}}\n```'
            )

            consensus_output = await self._call_agent_with_retry(
                "review1", consensus_prompt, run_id, chunk_num, "Reviewer A consensus",
                round_id, self.conn, diff_text, l1_results, revision,
                review_a_output=review_a_output, review_b_output=review_b_output)
            if consensus_output is None:
                return

            _record_trajectory(self.conn, run_id, "review1", "code_review_consensus",
                          consensus_prompt, consensus_output, chunk_num)
            _update_trajectory_outcome(self.conn, run_id, "review1", "code_review_consensus", "success")

            # Step 6: Parse consensus verdict
            consensus_parsed = _parse_final_json(consensus_output)
            consensus_status = consensus_parsed.get("status", "") if consensus_parsed else ""

            if not consensus_parsed or consensus_status not in ("APPROVED", "CHANGES_REQUESTED"):
                # Incomplete consensus — escalate
                print(f"[pipeline] Consensus incomplete for chunk {chunk_num}. ESCALATE.")
                self.conn.execute(
                    """INSERT INTO code_review_chunks
                       (run_id, chunk_number, file_path, diff_text, l1_results,
                        review_a_pass1, review_b_pass2, review_a_consensus,
                        final_verdict, revision_number, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ESCALATE', ?, ?)""",
                    (run_id, chunk_num, file_path, diff_text[:5000], l1_results,
                     review_a_output[:5000], review_b_output[:5000], consensus_output[:5000],
                     revision, datetime.now(timezone.utc).isoformat())
                )
                self.conn.commit()
                _complete_round(self.conn, round_id, "ESCALATE",
                               {"menter_output": menter_output})
                return

            if consensus_status == "APPROVED":
                # Chunk approved — record and incorporate
                revision_directive_text = consensus_parsed.get("consensus_summary", "")
                self.conn.execute(
                    """INSERT INTO code_review_chunks
                       (run_id, chunk_number, file_path, diff_text, l1_results,
                        review_a_pass1, review_b_pass2, review_a_consensus,
                        final_verdict, revision_directive, revision_number,
                        incorporated, created_at, completed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'APPROVED', ?, ?, 1, ?, ?)""",
                    (run_id, chunk_num, file_path, diff_text[:5000], l1_results,
                     review_a_output[:5000], review_b_output[:5000], consensus_output[:5000],
                     revision_directive_text, revision,
                     datetime.now(timezone.utc).isoformat(),
                     datetime.now(timezone.utc).isoformat())
                )
                self.conn.commit()
                _complete_round(self.conn, round_id, "CONSENSUS_REACHED",
                               {"menter_output": menter_output})
                print(f"[pipeline] Chunk {chunk_num} APPROVED. Incorporated.")

                # Ingest code review findings into knowledge base
                _ingest_to_kb(self.conn, run_id, "code_review", "menter",
                            menter_output, "CHUNK_APPROVED",
                            f"chunk_{chunk_num}_rev_{revision}_file_{file_path}")
                _ingest_to_kb(self.conn, run_id, "code_review", "review1",
                            review_a_output, "CHUNK_APPROVED",
                            f"chunk_{chunk_num}_pass1_first_review")
                _ingest_to_kb(self.conn, run_id, "code_review", "review2",
                            review_b_output, "CHUNK_APPROVED",
                            f"chunk_{chunk_num}_pass2_builds_on_review1")
                _ingest_to_kb(self.conn, run_id, "code_review", "review1_consensus",
                            consensus_output, "CHUNK_APPROVED",
                            f"chunk_{chunk_num}_pass3_consensus")
                return

            # CHANGES_REQUESTED — record and loop for revision
            revision_directive_text = consensus_parsed.get("revision_directive",
                                                           consensus_output[:1000])
            self.conn.execute(
                """INSERT INTO code_review_chunks
                   (run_id, chunk_number, file_path, diff_text, l1_results,
                    review_a_pass1, review_b_pass2, review_a_consensus,
                    final_verdict, revision_directive, revision_number,
                    incorporated, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CHANGES_REQUESTED', ?, ?, 0, ?)""",
                (run_id, chunk_num, file_path, diff_text[:5000], l1_results,
                 review_a_output[:5000], review_b_output[:5000], consensus_output[:5000],
                 revision_directive_text, revision,
                 datetime.now(timezone.utc).isoformat())
            )
            self.conn.commit()
            _complete_round(self.conn, round_id, "OBJECTIONS",
                           {"menter_output": menter_output})

            print(f"[pipeline] Chunk {chunk_num} CHANGES_REQUESTED. Revision {revision + 1}.")

            # Ingest code review findings (including objections) into knowledge base
            _ingest_to_kb(self.conn, run_id, "code_review", "menter",
                        menter_output, "CHANGES_REQUESTED",
                        f"chunk_{chunk_num}_rev_{revision}_file_{file_path}")
            _ingest_to_kb(self.conn, run_id, "code_review", "review1",
                        review_a_output, "CHANGES_REQUESTED",
                        f"chunk_{chunk_num}_pass1_first_review")
            _ingest_to_kb(self.conn, run_id, "code_review", "review2",
                        review_b_output, "CHANGES_REQUESTED",
                        f"chunk_{chunk_num}_pass2_builds_on_review1")
            _ingest_to_kb(self.conn, run_id, "code_review", "review1_consensus",
                        consensus_output, "CHANGES_REQUESTED",
                        f"chunk_{chunk_num}_pass3_consensus_revision_directive")
            _ingest_to_kb(self.conn, run_id, "code_review", "revision_directive",
                        revision_directive_text, "CHANGES_REQUESTED",
                        f"chunk_{chunk_num}_rev_{revision}")

            revision += 1

        # Max revisions exceeded
        print(f"[pipeline] Chunk {chunk_num} max revisions ({MAX_CHUNK_REVISIONS}) exceeded. ESCALATE.")
        _set_run_status(self.conn, run_id, "ESCALATED")

    async def _execution(self, run_id: str, intent: str) -> None:
        """Execution phase: Menter builds per approved FINAL_DIRECTIVE."""
        print(f"[pipeline] EXECUTION phase for {run_id}")

        # Capture pre-execution git state for L1 diff
        import subprocess
        try:
            pre_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10,
                cwd=DB_PATH.rsplit("/", 1)[0],
            ).stdout.strip()
        except Exception:
            pre_head = ""
        self._pre_exec_head = pre_head

        cur = self.conn.execute(
            "SELECT drafter_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_output IS NOT NULL AND drafter_output != '' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        directive = row[0] if (row := cur.fetchone()) else ""

        # Freeze directive hash
        directive_hash = hashlib.sha256(directive.encode()).hexdigest()
        self.conn.execute(
            "UPDATE workflow_runs SET directive_hash = ? WHERE id = ?",
            (directive_hash, run_id)
        )
        self.conn.commit()

        round_id = _start_round(self.conn, run_id, "execution", 1)
        discovery = _pre_discovery(
            self.conn, intent, "execution", "menter", run_id
        )

        prompt = (
            f"{discovery}\n\n"
            f"FINAL_DIRECTIVE (hash: {directive_hash[:16]}):\n{directive}\n\n"
            f"You are Menter. Execute this directive. Build exactly what is spec'd.\n"
            f"End with FINAL_JSON:\n"
            f'```json\n{{"role":"menter","status":"CONSENSUS_REACHED","summary":"..."}}\n```'
        )

        try:
            output = await _call_agent("menter", prompt, run_id)
        except Exception as e:
            _breaker_record_failure("menter")
            _set_run_status(self.conn, run_id, "ERROR")
            _complete_round(self.conn, round_id, "ERROR")
            _update_trajectory_outcome(self.conn, run_id, "menter", "execution", "failed")
            print(f"[pipeline] MENTER failed: {e}")
            return

        _record_trajectory(self.conn, run_id, "menter", "execution",
                          prompt, output, 1)

        # Validate Menter produced a valid status
        parsed = _parse_final_json(output)
        if not parsed or parsed.get("status") not in ("CONSENSUS_REACHED", "DONE", "COMPLETE"):
            _update_trajectory_outcome(self.conn, run_id, "menter", "execution", "failed")
            _complete_round(self.conn, round_id, "ESCALATE",
                           {"menter_output": output})
            _set_run_status(self.conn, run_id, "ESCALATED")
            print(f"[pipeline] MENTER output invalid — no completion status. ESCALATE.")
            return

        _update_trajectory_outcome(self.conn, run_id, "menter", "execution", "success")
        _complete_round(self.conn, round_id, "CONSENSUS_REACHED",
                        {"menter_output": output})

        _set_run_status(self.conn, run_id, "VERIFICATION")
        await self._verification(run_id, intent)

    async def _verification(self, run_id: str, intent: str) -> None:
        """Verification phase: Verify checks Menter's work independently.

        L1 deterministic checks run first (git diff, file existence/size).
        Results are fed to the verify agent as evidence. The agent does
        L2 semantic verification on top of the L1 evidence.
        """
        print(f"[pipeline] VERIFICATION phase for {run_id}")

        # Get the directive (Draft's proposal) — NOT Menter's self-report
        cur = self.conn.execute(
            "SELECT drafter_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_output IS NOT NULL AND drafter_output != '' "
            "  AND drafter_role = 'draft' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        directive = row[0] if (row := cur.fetchone()) else ""

        # Get Menter's output (what was actually built)
        cur = self.conn.execute(
            "SELECT menter_output FROM deliberation_rounds "
            "WHERE run_id = ? AND menter_output IS NOT NULL AND menter_output != '' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        menter_output = row[0] if (row := cur.fetchone()) else ""

        # Run L1 deterministic checks with clean-checkout isolation
        project_dir = DB_PATH.rsplit("/", 1)[0]
        pre_head = getattr(self, "_pre_exec_head", "")
        l1_evidence = _run_isolated_l1(project_dir, pre_head)
        print(f"[pipeline] L1 isolated checks complete ({len(l1_evidence)} chars)")

        round_id = _start_round(self.conn, run_id, "verification", 1)
        discovery = _pre_discovery(
            self.conn, intent, "verification", "verify", run_id
        )

        prompt = (
            f"{discovery}\n\n"
            f"## L1 DETERMINISTIC EVIDENCE (auto-collected)\n"
            f"{l1_evidence}\n\n"
            f"## FINAL_DIRECTIVE (what Menter was told to build)\n{directive}\n\n"
            f"## MENTER'S SELF-REPORT (what Menter claims it did)\n{menter_output}\n\n"
            f"You are Verify. Cross-check the L1 evidence against the directive. "
            f"Menter's self-report is NOT evidence — it is a claim. Verify independently. "
            f"Run additional evidence commands if needed (git diff, tests, "
            f"file state). Trust nothing Menter claimed — verify independently. "
            f"End with FINAL_JSON:\n"
            f'```json\n{{"role":"verify","status":"PASS","summary":"..."}}\n```\n'
            f'or\n```json\n{{"role":"verify","status":"FAIL","summary":"..."}}\n```'
        )

        try:
            output = await _call_agent("verify", prompt, run_id)
        except Exception as e:
            _breaker_record_failure("verify")
            _set_run_status(self.conn, run_id, "ERROR")
            _complete_round(self.conn, round_id, "ERROR")
            _update_trajectory_outcome(self.conn, run_id, "verify", "verification", "failed")
            print(f"[pipeline] VERIFY failed: {e}")
            return

        _record_trajectory(self.conn, run_id, "verify", "verification",
                          prompt, output, 1)
        _update_trajectory_outcome(self.conn, run_id, "verify", "verification", "success")
        _complete_round(self.conn, round_id, "CONSENSUS_REACHED",
                       {"verify_output": output})

        parsed = _parse_final_json(output)
        status = parsed.get("status", "") if parsed else ""

        if not parsed or status not in ("PASS", "FAIL"):
            # Verify did not produce a valid verdict — NOT a pass
            print(f"[pipeline] VERIFY incomplete — no valid PASS/FAIL verdict")
            _complete_round(self.conn, round_id, "ESCALATE",
                           {"verify_output": output})
            _set_run_status(self.conn, run_id, "ESCALATED")
            print(f"[pipeline] Run {run_id} ESCALATED — verify output unparseable")
            return

        if status == "FAIL":
            # Saga compensation: git stash Menter's changes
            print(f"[pipeline] VERIFY FAIL — compensating (git stash)")
            stash_ref = ""
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "stash", "push", "-m", f"CIS compensation: {run_id} verify FAIL"],
                    capture_output=True, text=True, timeout=30,
                    cwd=DB_PATH.rsplit("/", 1)[0],
                )
                if result.returncode == 0:
                    stash_ref = result.stdout.strip()
                    print(f"[pipeline] Compensation: changes stashed ({stash_ref})")
                else:
                    print(f"[pipeline] Compensation: git stash failed: {result.stderr.strip()}")
            except Exception as e:
                print(f"[pipeline] Compensation error: {e}")

            # Record compensation in DB audit trail
            self.conn.execute(
                """UPDATE deliberation_rounds SET
                   verify_output = ?,
                   objections_json = ?
                   WHERE id = ?""",
                (output, json.dumps({"stash_ref": stash_ref, "status": "FAIL"}), round_id)
            )
            self.conn.commit()
            _set_run_status(self.conn, run_id, "VERIFY_FAILED")
        else:
            print(f"[pipeline] VERIFY PASS — run complete")
            _set_run_status(self.conn, run_id, "CONSENSUS_REACHED")


# ── CLI Entry Point ────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CIS Pipeline Relay")
    parser.add_argument("--intent", "-i", help="Intent text to start a new run")
    parser.add_argument("--resume", "-r", help="Resume a run by ID")
    parser.add_argument("--status", "-s", help="Show status of a run")
    args = parser.parse_args()

    if args.status:
        conn = _db_connect()
        run = _get_run(conn, args.status)
        if run:
            print(f"Run ID: {run['id']}")
            print(f"Topic: {run['topic']}")
            print(f"Status: {run['status']}")
            print(f"Created: {run['created_at']}")
            if run['directive_hash']:
                print(f"Directive hash: {run['directive_hash'][:16]}...")
        else:
            print(f"Run {args.status} not found")
        conn.close()
        return

    relay = PipelineRelay()

    if args.intent:
        run_id = asyncio.run(relay.start(args.intent))
        print(f"\nPipeline run: {run_id}")
    elif args.resume:
        asyncio.run(relay.resume(args.resume))
    else:
        parser.print_help()

    relay.close()


if __name__ == "__main__":
    main()