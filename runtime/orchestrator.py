#!/usr/bin/env python3
"""
orchestrator.py — Tier 0 Deliberation Engine
CIS Dependency Graph Build Plan v2.0 — Artifact 0.1
Tier 6.3 — Kanban/blackboard integration

Deliberation loop:
  DRAFT(v4pro) → REVIEW(r1) → CONSENSUS_REACHED or OBJECTIONS → repeat
  Max rounds enforced. Eric gate NOT bypassed.

Usage:
  python3 orchestrator.py "Your topic here"
  python3 orchestrator.py --config /path/to/config.yaml "Your topic here"
  echo "Your topic here" | python3 orchestrator.py
  python3 orchestrator.py --run-id <id> [--test]
"""

import sys
import json
import os
import time
import uuid
import argparse
import sqlite3
import subprocess
from datetime import datetime, timezone

import yaml
import requests


# ── Config loading ────────────────────────────────────────────────────

def load_config(config_path=None):
    """Load orchestrator config from YAML file. Falls back to env and defaults."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "orchestrator_config.yaml")

    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    # Apply defaults for any missing keys
    defaults = {
        "max_rounds": 3,
        "drafter_agent": "hermes-v4pro",
        "reviewer_agent": "hermes-r1",
        "consensus_signal": "CONSENSUS_REACHED",
        "escalation_signal": "ESCALATE",
        "require_structured_reviewer_signal": True,
        "objections_header": "OBJECTIONS",
        "api_base_url": "http://127.0.0.1:5000",
        "chat_endpoint": "/api/advisor/chat",
        "api_key": "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd",
        "request_timeout": 300,
        "drafter_timeout": None,
        "reviewer_timeout": None,
        "max_input_chars": None,
        "max_reviewer_input_chars": 4000,
        "test_mode": False,
    }
    for key, default in defaults.items():
        if key not in config:
            config[key] = default

    # Env overrides
    if os.environ.get("ORCHESTRATOR_API_KEY"):
        config["api_key"] = os.environ["ORCHESTRATOR_API_KEY"]

    return config


# ── Agent communication ───────────────────────────────────────────────

def call_agent(agent_name, content, thread_id, config):
    """Call a named agent via /api/advisor/chat. Returns response JSON or raises."""
    url = f"{config['api_base_url']}{config['chat_endpoint']}"
    headers = {
        "Content-Type": "application/json",
        "X-CIS-API-Key": config["api_key"],
    }
    payload = {
        "agent": agent_name,
        "thread_id": thread_id,
        "content": content,
    }

    # Per-agent timeout: drafter_timeout / reviewer_timeout, fall back to request_timeout
    timeout = config.get("request_timeout", 300)
    if agent_name == config.get("drafter_agent") and config.get("drafter_timeout") is not None:
        timeout = config["drafter_timeout"]
    elif agent_name == config.get("reviewer_agent") and config.get("reviewer_timeout") is not None:
        timeout = config["reviewer_timeout"]

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


# ── Signal detection ──────────────────────────────────────────────────

def detect_consensus(reviewer_response_text, config):
    """
    Detect CONSENSUS_REACHED in Reviewer output.

    With require_structured_reviewer_signal=true:
      Must contain 'CONSENSUS_REACHED' on its own line or as a clear header,
      with 'remaining_objections:' indicating none.
      Pattern:
        CONSENSUS_REACHED
        remaining_objections: none
        requires_eric_review: true

    Without structured requirement:
      Any text containing 'CONSENSUS_REACHED' counts.
    """
    text = reviewer_response_text or ""

    if config["require_structured_reviewer_signal"]:
        # Look for CONSENSUS_REACHED with structured format
        lines = text.split("\n")
        found_consensus = False
        found_no_objections = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "CONSENSUS_REACHED" or stripped.startswith("CONSENSUS_REACHED"):
                found_consensus = True
                # Check next 5 lines for remaining_objections: none
                for j in range(i + 1, min(i + 6, len(lines))):
                    next_line = lines[j].strip().lower()
                    if "remaining_objections" in next_line and (
                        "none" in next_line or "0" in next_line or "[]" in next_line
                    ):
                        found_no_objections = True
                        break
                break

        return found_consensus and found_no_objections
    else:
        return "CONSENSUS_REACHED" in text.upper()


def detect_objections(reviewer_response_text, config):
    """
    Detect OBJECTIONS header in Reviewer output.
    Returns list of objection strings, or empty list if none.
    """
    text = reviewer_response_text or ""
    lines = text.split("\n")
    objections = []

    in_objections = False
    for line in lines:
        stripped = line.strip()
        if stripped.upper() == config["objections_header"].upper():
            in_objections = True
            continue
        if in_objections:
            if stripped.startswith("- "):
                objections.append(stripped[2:])
            elif stripped == "":
                continue  # blank line in objections section
            elif stripped and not stripped.startswith("- "):
                # Non-blank, non-list line after objections — might be a new section
                if not objections:
                    # No objections captured yet, continue
                    continue
                else:
                    # We have objections and hit a new section header
                    break

    return objections


# ── Tier 6.3: Kanban integration helpers ──────────────────────────────

# RETIRED — _kanban_db_path retired per ADR-013

def _spine_db_path():
    """Return path to the CIS spine database."""
    return os.environ.get(
        "CIS_DB_PATH",
        "/mnt/projects/cis/data/cis_memory.db",
    )


def read_workflow_run(run_id):
    """Return (topic, status, max_rounds) from workflow_runs by id.
    Raises RuntimeError if not found."""
    db_path = _spine_db_path()
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT topic, status, max_rounds, rounds_completed FROM workflow_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        conn.close()
        if row is None:
            raise RuntimeError(f"Workflow run not found: {run_id}")
        return row[0], row[1], row[2], row[3]
    except sqlite3.Error as e:
        raise RuntimeError(f"Spine read failed: {e}")


def update_workflow_status(run_id, status, result=None, round_num=None):
    """Update workflow_runs status, optionally result and rounds_completed."""
    db_path = _spine_db_path()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn = sqlite3.connect(db_path)
        if round_num is not None:
            conn.execute(
                "UPDATE workflow_runs SET status=?, updated_at=?, rounds_completed=? WHERE id=?",
                (status, now, round_num, run_id),
            )
        else:
            conn.execute(
                "UPDATE workflow_runs SET status=?, updated_at=? WHERE id=?",
                (status, now, run_id),
            )
        if result is not None:
            conn.execute(
                "UPDATE workflow_runs SET result=?, completed_at=? WHERE id=?",
                (result, now, run_id),
            )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Spine status update failed: {e}")


def insert_deliberation_round(run_id, round_number, drafter_output, reviewer_output,
                               reviewer_signal, objections_json=None):
    """Insert one deliberation_rounds row. Matches the inspected schema exactly."""
    db_path = _spine_db_path()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO deliberation_rounds
                (run_id, round_number, drafter_role, drafter_output,
                 reviewer_role, reviewer_signal, objections_json,
                 revision_number, requires_eric_review, created_at)
            VALUES (?, ?, 'hermes-v4pro', ?, 'hermes-r1', ?, ?,
                    1, 1, ?)
        """, (run_id, round_number, drafter_output, reviewer_signal,
              objections_json, now))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Deliberation round insert failed: {e}")


# ── DEPRECATED: Kanban functions (commented out — spine-native path now used) ─
# See session_handoffs/PROPOSAL_RETIRE_KANBAN_SPINE_API.md
#
# def read_kanban_card(card_id): ... (commented out)
# def write_card_body(card_id, body, config): ... (commented out)
# def update_card_status(card_id, action, reason=None, config=None): ... (commented out)
# def _read_card_body_only(card_id): ... (commented out)
# def strip_orchestrator_sections(body, keep_section=None): ... (commented out)
#
# The original function bodies are preserved below for reference.
# --- ORPHANED read_kanban_card body (def removed) ---
#     """Return (title, body) from a Kanban card via `hermes kanban show --json`.
#     Raises RuntimeError on failure."""
#     try:
#         result = subprocess.run(
#             ["hermes", "kanban", "show", "--json", card_id],
#             ... (commented out — spine-native path now used)


# DEPRECATED — write_card_body: Kanban card body writer (commented out)
# Stub retained so old Kanban code paths compile but are never executed in spine-native mode.
def write_card_body(card_id, body, config):
    """DEPRECATED. Use insert_deliberation_round() for spine-native path."""
    raise RuntimeError("write_card_body is deprecated — use spine-native path")
    """Write body to Kanban card via direct SQLite UPDATE.
    Uses short-lived connection. Confirms exactly one row updated.
    Raises RuntimeError on failure."""
    db_path = _kanban_db_path(config)
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "UPDATE tasks SET body = ? WHERE id = ?",
            (body, card_id),
        )
        if cursor.rowcount != 1:
            raise RuntimeError(
                f"Body update affected {cursor.rowcount} rows (expected 1). "
                f"Card ID may not exist: {card_id}"
            )
        conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"SQLite body write failed: {e}")
    finally:
        if conn:
            conn.close()


# DEPRECATED — read_kanban_card stub (spine-native path replaces Kanban)
def read_kanban_card(card_id):
    """DEPRECATED. Use read_workflow_run() for spine-native path."""
    raise RuntimeError("read_kanban_card is deprecated — use spine-native path")


def update_card_status(card_id, action, reason=None, config=None):
    """Update card status via `hermes kanban` CLI.
    action: 'claim', 'complete', or 'block'.
    Raises RuntimeError on failure."""
    if action == "claim":
        cmd = ["hermes", "kanban", "claim", card_id]
    elif action == "complete":
        cmd = ["hermes", "kanban", "complete", card_id]
    elif action == "block":
        cmd = ["hermes", "kanban", "block", card_id]
        if reason:
            cmd.append(reason)
    else:
        raise ValueError(f"Unknown status action: {action}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"hermes kanban {action} failed (exit {result.returncode}): "
                f"{result.stderr.strip()[:500]}"
            )
    except FileNotFoundError:
        raise RuntimeError("hermes CLI not found on PATH")
    except Exception as e:
        raise RuntimeError(f"Kanban status update failed: {e}")


def strip_orchestrator_sections(body, keep_section=None):
    """Remove ## Proposal and ## Review sections from body.
    If keep_section is 'proposal', preserves ## Proposal while removing ## Review.
    If keep_section is 'review', preserves ## Review while removing ## Proposal.
    If keep_section is None (default), removes both.
    Preserves all other sections including ## Context, ## Eric Gate,
    ## Implementation, ## Research Artifact, ## Verification Failure, etc."""
    if not body:
        return ""

    lines = body.split("\n")
    result = []
    skip_proposal = (keep_section != "proposal")
    skip_review = (keep_section != "review")
    skip = False
    current_section = None

    for line in lines:
        stripped = line.strip()
        # Detect section headings
        if stripped == "## Proposal":
            if skip_proposal:
                skip = True
                current_section = "proposal"
                continue
            else:
                skip = False
                current_section = None
        elif stripped == "## Review":
            if skip_review:
                skip = True
                current_section = "review"
                continue
            else:
                skip = False
                current_section = None
        elif skip and stripped.startswith("## "):
            # New top-level section — stop skipping
            skip = False
            current_section = None

        if not skip:
            result.append(line)

    return "\n".join(result).strip()


def validate_proposal_sections(drafter_output):
    """Check that Drafter output is non-empty and contains substantive content.
    Does NOT require specific markdown headings — the Reviewer is the real
    quality gate.  Only blocks truly empty or whitespace-only responses.
    Returns (passed: bool, missing_headings: list[str])."""
    stripped = drafter_output.strip()
    if len(stripped) < 50:
        return False, ["Drafter output too short (< 50 chars)"]
    return True, []


def normalize_review_section(reviewer_output, objections, is_consensus, is_last_round):
    """Construct a deterministic ## Review section with exactly one valid signal.

    Returns normalized markdown string for the ## Review section.

    Signal priority (first match wins):
      1. If is_consensus → CONSENSUS_REACHED
      2. If objections list is non-empty → OBJECTIONS
      3. Otherwise → ESCALATE (fallback)
    """
    if is_consensus:
        signal_block = (
            "CONSENSUS_REACHED\n"
            "remaining_objections: none\n"
            "requires_eric_review: true\n"
        )
    elif objections and len(objections) > 0:
        objection_lines = "\n".join(f"- {o}" for o in objections)
        signal_block = f"OBJECTIONS\n{objection_lines}\n"
    else:
        signal_block = (
            "ESCALATE\n"
            "Reviewer output did not contain a valid consensus or objections signal.\n"
        )

    return f"## Review\n\n{signal_block}\n{reviewer_output}"


# ── Main deliberation loop ────────────────────────────────────────────

def run_deliberation(topic, config, run_id=None):
    """Run the Drafter->Reviewer deliberation loop. Returns final output dict.

    If run_id is provided (spine-native), writes state to workflow_runs and
    deliberation_rounds via SQLite. If None, raw topic mode (no persistence)."""
    # RETIRED — Kanban retired per ADR-013. All kanban_card_id paths removed.
    run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
    thread_id = f"orch-{run_id}"

    print(f"═══ CIS Deliberation Engine ═══")
    print(f"Run ID: {run_id}")
    print(f"Topic: {topic[:200]}{'...' if len(topic) > 200 else ''}")
    print(f"Max rounds: {config['max_rounds']}")
    if config.get("test_mode"):
        print(f"Test mode: ON (truncated responses)")
    if run_id:
        print(f"Spine-native mode: run_id={run_id}")
    print()

    # Apply max_input_chars if configured
    max_in = config.get("max_input_chars")
    if max_in and len(topic) > max_in:
        topic = topic[:max_in]
        print(f"Input truncated to {max_in} chars")

    # Test mode prefix
    test_prefix = ""
    if config.get("test_mode"):
        test_prefix = "[TEST MODE] Respond in 3 sentences or fewer. Be direct.\n\n"

    # ── Tier 6.3: Proposal structure requirement ───────────────────
    PROPOSAL_STRUCTURE_REQUIREMENT = (
        "\n\nIMPORTANT — Your response MUST include the following sections with "
        "markdown headings. This requirement overrides any length or brevity "
        "constraints:\n\n"
        "### Summary\n"
        "<concise summary of your proposal>\n\n"
        "### Recommendation\n"
        "<your recommendation and reasoning>\n\n"
        "You may include additional sections (### Analysis, ### Risks, etc.) "
        "but ### Summary and ### Recommendation are REQUIRED."
    )

    drafter_output = None
    reviewer_output = None
    drafter_reasoning = None
    reviewer_reasoning = None
    objections = []
    rounds_completed = 0

    for round_num in range(1, config["max_rounds"] + 1):
        print(f"─── Round {round_num}/{config['max_rounds']} ───")

        # ── DRAFT phase ────────────────────────────────────────────
        print(f"  ROUND {round_num} DRAFT started ({config['drafter_agent']})", flush=True)
        t0 = time.time()

        if round_num == 1:
            drafter_prompt = test_prefix + topic + PROPOSAL_STRUCTURE_REQUIREMENT
        else:
            # Build revision prompt with objections from Reviewer
            objections_text = "\n".join(f"  - {o}" for o in objections)
            drafter_prompt = (
                f"{test_prefix}"
                f"REVISION REQUEST — Round {round_num}\n\n"
                f"Original topic: {topic}\n\n"
                f"The Reviewer raised the following objections to your previous proposal:\n"
                f"{objections_text}\n\n"
                f"Revise your proposal to address each objection. "
                f"Do NOT claim execution or completion. "
                f"Output a revised proposal only."
                f"{PROPOSAL_STRUCTURE_REQUIREMENT}"
            )

        try:
            drafter_resp = call_agent(
                config["drafter_agent"], drafter_prompt, thread_id, config
            )
        except Exception as e:
            print(f"  ROUND {round_num} DRAFT FAILED: {e}", flush=True)
            # RETIRED — Kanban retired per ADR-013
            return {
                "result": "ERROR",
                "phase": "DRAFT",
                "round": round_num,
                "error": str(e),
                "run_id": run_id,
            }

        drafter_output = drafter_resp.get("content", "")
        drafter_reasoning = drafter_resp.get("reasoning_content", "")
        drafter_elapsed = time.time() - t0
        print(f"  ROUND {round_num} DRAFT complete ({drafter_elapsed:.1f}s, {len(drafter_output)} chars)", flush=True)

        # RETIRED — Kanban proposal validation and card writes retired per ADR-013
        # ── REVIEW phase ───────────────────────────────────────────
        print(f"  ROUND {round_num} REVIEW started ({config['reviewer_agent']})", flush=True)
        t0 = time.time()

        # Truncate Drafter output for Reviewer if configured
        reviewer_input = drafter_output
        max_rev_in = config.get("max_reviewer_input_chars")
        if max_rev_in and len(reviewer_input) > max_rev_in:
            reviewer_input = reviewer_input[:max_rev_in]
            print(f"  reviewer input truncated: {len(drafter_output)} → {max_rev_in} chars", flush=True)

        reviewer_prompt = (
            f"{test_prefix}"
            f"Review this proposal critically. Identify objections, missing evidence, "
            f"and risks. If the proposal is acceptable, respond with the structured signal:\n\n"
            f"CONSENSUS_REACHED\n"
            f"remaining_objections: none\n"
            f"requires_eric_review: true\n\n"
            f"If you have objections, respond with:\n\n"
            f"OBJECTIONS\n"
            f"- objection 1\n"
            f"- objection 2\n\n"
            f"Proposal to review:\n\n"
            f"{reviewer_input}"
        )

        try:
            reviewer_resp = call_agent(
                config["reviewer_agent"], reviewer_prompt, thread_id, config
            )
        except Exception as e:
            print(f"  ROUND {round_num} REVIEW FAILED: {e}", flush=True)
            # RETIRED — Kanban retired per ADR-013
            return {
                "result": "ERROR",
                "phase": "REVIEW",
                "round": round_num,
                "error": str(e),
                "run_id": run_id,
            }

        reviewer_output = reviewer_resp.get("content", "")
        reviewer_reasoning = reviewer_resp.get("reasoning_content", "")
        reviewer_elapsed = time.time() - t0
        print(f"  ROUND {round_num} REVIEW complete ({reviewer_elapsed:.1f}s, {len(reviewer_output)} chars)", flush=True)

        # ── Detect consensus ───────────────────────────────────────
        is_consensus = detect_consensus(reviewer_output, config)

        # ── Detect objections ──────────────────────────────────────
        detected_objections = detect_objections(reviewer_output, config)
        if not detected_objections and not is_consensus:
            # No structured signals — treat as unclear
            print(f"  no structured signals detected in Reviewer output for Round {round_num}")
            detected_objections = [reviewer_output[:500] + ("..." if len(reviewer_output) > 500 else "")]

        # RETIRED — Kanban review write to card retired per ADR-013

        # ── Spine-native: persist round to deliberation_rounds ────
        if run_id:
            try:
                signal = 'CONSENSUS_REACHED' if is_consensus else (
                    'OBJECTIONS' if detected_objections and detected_objections != [reviewer_output[:500]] else 'ESCALATE')
                obj_json = json.dumps(detected_objections) if detected_objections else None
                insert_deliberation_round(run_id, round_num, drafter_output,
                                         reviewer_output, signal, obj_json)
                print(f"  Spine: deliberation_rounds round={round_num} written", flush=True)
            except Exception as e:
                print(f"  WARNING: deliberation_rounds write failed: {e}", flush=True)

        # ── Act on consensus ───────────────────────────────────────
        if is_consensus:
            print(f"\n  >>> consensus detected: CONSENSUS_REACHED in Round {round_num} <<<")
            print()
            # RETIRED — Kanban retired per ADR-013
            if run_id:
                try:
                    update_workflow_status(run_id, 'CONSENSUS_REACHED',
                                          result='CONSENSUS_REACHED', round_num=round_num)
                    print(f"  Spine: workflow_runs status=CONSENSUS_REACHED", flush=True)
                except Exception as e:
                    print(f"  WARNING: Spine status update failed: {e}", flush=True)
            return {
                "result": "CONSENSUS_REACHED",
                "round": round_num,
                "run_id": run_id,
                "thread_id": thread_id,
                "topic": topic,
                "drafter_output": drafter_output,
                "drafter_reasoning": drafter_reasoning,
                "reviewer_output": reviewer_output,
                "reviewer_reasoning": reviewer_reasoning,
                "total_rounds": round_num,
                "max_rounds": config["max_rounds"],
                "requires_eric_review": True,
            }

        # ── Store objections for next round ────────────────────────
        objections = detected_objections
        if objections and objections != [reviewer_output[:500] + ("..." if len(reviewer_output) > 500 else "")]:
            print(f"  objections detected: {len(objections)} objection(s) in Round {round_num}")
            for obj in objections:
                print(f"    - {obj}")
        rounds_completed = round_num
        print()

    # ── Max rounds reached without consensus ──────────────────────────
    print(f"═══ escalating: max rounds ({config['max_rounds']}) reached without CONSENSUS_REACHED ═══")
    print()

    # RETIRED — Kanban retired per ADR-013

    if run_id:
        try:
            update_workflow_status(run_id, 'ESCALATE', result='ESCALATE',
                                  round_num=rounds_completed)
            print(f"  Spine: workflow_runs status=ESCALATE", flush=True)
        except Exception as e:
            print(f"  WARNING: Spine status update failed: {e}", flush=True)

    # Collect unresolved objections from last round
    unresolved = "\n".join(f"  - {o}" for o in objections) if objections else "No structured objections extracted"

    return {
        "result": config["escalation_signal"],
        "round": rounds_completed,
        "run_id": run_id,
        "thread_id": thread_id,
        "topic": topic,
        "drafter_output": drafter_output,
        "drafter_reasoning": drafter_reasoning,
        "reviewer_output": reviewer_output,
        "reviewer_reasoning": reviewer_reasoning,
        "unresolved_objections": objections,
        "total_rounds": rounds_completed,
        "max_rounds": config["max_rounds"],
        "requires_eric_review": True,
    }


def _read_card_body_only(card_id):
    """Read only the card body from Kanban (used internally for
    incremental writes). Returns (body, full_data)."""
    try:
        result = subprocess.run(
            ["hermes", "kanban", "show", "--json", card_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"hermes kanban show failed: {result.stderr.strip()[:200]}")
        data = json.loads(result.stdout)
        task = data.get("task", data)
        return task.get("body", "") or "", task
    except Exception:
        # On failure, return empty body — will be overwritten
        return "", {}


# ── CLI ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CIS Tier 0 Deliberation Engine — Drafter→Reviewer loop"
    )
    parser.add_argument(
        "topic", nargs="?", default=None,
        help="Topic to deliberate on (reads from stdin if omitted)"
    )
    parser.add_argument(
        "--config", "-c", default=None, metavar="PATH",
        help="Path to orchestrator_config.yaml"
    )
    parser.add_argument(
        "--test", "-t", action="store_true",
        help="Short test mode: prepends test prefix and enables truncated output"
    )
    parser.add_argument(
        "--output", "-o", default=None, metavar="PATH",
        help="Write full result JSON to file"
    )
    # RETIRED — --kanban-card-id retired per ADR-013
    parser.add_argument(
        "--run-id", default=None, metavar="ID",
        help="Read topic from workflow_runs table and write state back (spine-native)"
    )
    args = parser.parse_args()

    # Load config early — needed for Kanban reads
    config = load_config(args.config)

    # CLI flag overrides
    if args.test:
        config["test_mode"] = True

    # ── Spine-native: workflow_runs topic resolution ───────────────
    if args.run_id:
        try:
            topic, status, max_rounds, rounds_done = read_workflow_run(args.run_id)
            if not topic:
                print(f"Error: Workflow run {args.run_id} has no topic")
                sys.exit(1)
            print(f"Topic from spine: {topic[:200]}{'...' if len(topic) > 200 else ''}")
            print(f"Status: {status}, Rounds completed: {rounds_done}")
        except Exception as e:
            print(f"Error: Failed to read workflow run {args.run_id}: {e}")
            sys.exit(1)
    else:
        # Get topic from CLI arg or stdin (raw topic mode — unchanged)
        if args.topic:
            topic = args.topic
        elif not sys.stdin.isatty():
            topic = sys.stdin.read().strip()
        else:
            print("Error: No topic provided. Usage: orchestrator.py <topic>")
            sys.exit(1)

        if not topic:
            print("Error: Empty topic")
            sys.exit(1)

    # Run deliberation
    # RETIRED — kanban_card_id retired per ADR-013
    result = run_deliberation(topic, config, run_id=args.run_id)

    # Output
    print("═══ Final Result ═══")
    print(f"Result: {result['result']}")
    if result["result"] == "CONSENSUS_REACHED":
        print(f"Round: {result['round']}/{result['max_rounds']}")
        print()
        print("─── Final Proposal (Drafter output) ───")
        print(result["drafter_output"])
        print()
        print("─── Reviewer Confirmation ───")
        print(result["reviewer_output"])
    elif result["result"] == "ESCALATE":
        print(f"Rounds completed: {result['round']}/{result['max_rounds']}")
        print()
        print("─── Unresolved Objections ───")
        for obj in result.get("unresolved_objections", []):
            print(f"  - {obj}")
        print()
        print("─── Last Drafter Output ───")
        drafter_out = result.get("drafter_output", "")
        print(drafter_out[:2000] + ("..." if len(drafter_out) > 2000 else ""))
        print()
        print("─── Last Reviewer Output ───")
        reviewer_out = result.get("reviewer_output", "")
        print(reviewer_out[:2000] + ("..." if len(reviewer_out) > 2000 else ""))
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    # Write full JSON output if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull result written to {args.output}")

    # Tier 6.3: Exit code 5 for ESCALATE
    if result["result"] == "ESCALATE":
        sys.exit(5)

    sys.exit(0)


if __name__ == "__main__":
    main()
