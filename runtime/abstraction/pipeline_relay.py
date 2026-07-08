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

# Import dispatch map
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dispatch import PROFILES, check_gateway, get_gateway_url  # noqa: E402

# ── State Machine ─────────────────────────────────────────────────────

STATES = {
    "PENDING", "INTAKE", "BRAIN_PHASE", "ESCALATE",
    "INTENT_REVIEW", "DRAFT_PHASE", "PROPOSAL_REVIEW",
    "ERIC_GATE", "EXECUTION", "VERIFICATION",
    "WAITING_FOR_HUMAN",
    "CONSENSUS_REACHED",
    # Error states
    "ESCALATED", "VERIFY_FAILED", "STALE", "ERROR",
}

TERMINAL_STATES = {"CONSENSUS_REACHED", "ESCALATED", "VERIFY_FAILED", "STALE", "ERROR"}

# ── Circuit Breaker ────────────────────────────────────────────────────

_circuit_breaker: Dict[str, dict] = {}  # role -> {failures, last_failure_ts}


def _breaker_record_failure(role: str) -> None:
    """Record a gateway failure for circuit breaker."""
    entry = _circuit_breaker.get(role, {"failures": 0, "last_failure_ts": 0})
    entry["failures"] += 1
    entry["last_failure_ts"] = time.time()
    _circuit_breaker[role] = entry


def _breaker_record_success(role: str) -> None:
    """Reset circuit breaker on success."""
    _circuit_breaker.pop(role, None)


def _breaker_is_tripped(role: str) -> bool:
    """Check if circuit breaker is tripped for a role."""
    entry = _circuit_breaker.get(role)
    if not entry:
        return False
    if entry["failures"] < CIRCUIT_BREAKER_THRESHOLD:
        return False
    elapsed = time.time() - entry["last_failure_ts"]
    if elapsed > CIRCUIT_BREAKER_COOLDOWN:
        # Cooldown passed — reset
        _circuit_breaker.pop(role, None)
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
           VALUES (?, ?, 'CONSENSUS_REACHED', 'INTAKE', ?, 3, 0)""",
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
           VALUES (?, ?, ?, '', '', 'CONSENSUS_REACHED', ?, 0, ?)""",
        (run_id, actual_round_num, phase, round_num,
         datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    return cur.lastrowid


def _complete_round(conn: sqlite3.Connection, round_id: int,
                    reviewer_signal: str,
                    extra: Optional[Dict] = None) -> None:
    """Mark a deliberation round as complete with outputs.

    reviewer_signal must be one of: OBJECTIONS, CONSENSUS_REACHED, ESCALATE, ERROR
    (per spine CHECK constraint).
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
    except Exception:
        pass  # Table may be empty — fine

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
        except Exception:
            pass  # Web search is best-effort

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
    """
    # Try code-block JSON first
    matches = _FINAL_JSON_RE.findall(text)
    for match in matches:
        for group in match:
            if group:
                try:
                    return json.loads(group)
                except json.JSONDecodeError:
                    continue

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
    config_version = ""
    try:
        import subprocess
        config_version = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=DB_PATH.rsplit("/", 1)[0],
        ).stdout.strip()
    except Exception:
        pass

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
        _update_trajectory_outcome(self.conn, run_id, "brain", "brain", "success")
        _complete_round(self.conn, round_id, "CONSENSUS_REACHED",
                       {"brain_output": output})

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
        _update_trajectory_outcome(self.conn, run_id, "menter", "execution", "success")
        _complete_round(self.conn, round_id, "CONSENSUS_REACHED",
                        {"drafter_output": output})

        _set_run_status(self.conn, run_id, "VERIFICATION")
        await self._verification(run_id, intent)

    async def _verification(self, run_id: str, intent: str) -> None:
        """Verification phase: Verify checks Menter's work independently.

        L1 deterministic checks run first (git diff, file existence/size).
        Results are fed to the verify agent as evidence. The agent does
        L2 semantic verification on top of the L1 evidence.
        """
        print(f"[pipeline] VERIFICATION phase for {run_id}")

        cur = self.conn.execute(
            "SELECT drafter_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_output IS NOT NULL AND drafter_output != '' "
            "ORDER BY id DESC LIMIT 1", (run_id,)
        )
        directive = row[0] if (row := cur.fetchone()) else ""

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
            f"## FINAL_DIRECTIVE (Menter's task)\n{directive}\n\n"
            f"You are Verify. Cross-check the L1 evidence against the directive. "
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

        if status == "FAIL":
            # Saga compensation: git stash Menter's changes
            print(f"[pipeline] VERIFY FAIL — compensating (git stash)")
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "stash", "push", "-m", f"CIS compensation: {run_id} verify FAIL"],
                    capture_output=True, text=True, timeout=30,
                    cwd=DB_PATH.rsplit("/", 1)[0],
                )
                if result.returncode == 0:
                    print(f"[pipeline] Compensation: changes stashed ({result.stdout.strip()})")
                else:
                    print(f"[pipeline] Compensation: git stash failed: {result.stderr.strip()}")
            except Exception as e:
                print(f"[pipeline] Compensation error: {e}")
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