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
  python3 orchestrator.py --kanban-card-id <id> [--test]
"""

import sys
import json
import os
import time
import uuid
import argparse
import sqlite3
import subprocess

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
        "kanban_board": "cis-pipeline",
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

def _kanban_db_path(config):
    """Return path to the Kanban SQLite database."""
    return os.environ.get(
        "HERMES_KANBAN_DB",
        "/mnt/projects/cis/data/kanban.db",
    )


def read_kanban_card(card_id):
    """Return (title, body) from a Kanban card via `hermes kanban show --json`.
    Raises RuntimeError on failure."""
    try:
        result = subprocess.run(
            ["hermes", "kanban", "show", "--json", card_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"hermes kanban show failed (exit {result.returncode}): "
                f"{result.stderr.strip()[:500]}"
            )
        data = json.loads(result.stdout)
        task = data.get("task", data)
        title = task.get("title", "")
        body = task.get("body", "") or ""
        return title, body
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse kanban show JSON: {e}")
    except FileNotFoundError:
        raise RuntimeError("hermes CLI not found on PATH")
    except Exception as e:
        raise RuntimeError(f"Kanban card read failed: {e}")


def write_card_body(card_id, body, config):
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
    """Check that ### Summary and ### Recommendation exist with non-empty
    content in Drafter output.
    Returns (passed: bool, missing_headings: list[str])."""
    missing = []
    for heading in ["### Summary", "### Recommendation"]:
        found = False
        lines = drafter_output.split("\n")
        for i, line in enumerate(lines):
            if line.strip() == heading:
                # Check that there is non-empty content after this heading
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line.startswith("### ") or next_line.startswith("## "):
                        # Hit another heading — no content found
                        break
                    if next_line:
                        found = True
                        break
                break
        if not found:
            missing.append(heading)
    return len(missing) == 0, missing


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

def run_deliberation(topic, config, kanban_card_id=None):
    """Run the Drafter→Reviewer deliberation loop. Returns final output dict.

    If kanban_card_id is provided, reads card body as context, writes
    ## Proposal and ## Review sections back to the card after each stage,
    and manages card status transitions.
    """
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    thread_id = f"orch-{run_id}"

    print(f"═══ CIS Deliberation Engine ═══")
    print(f"Run ID: {run_id}")
    print(f"Topic: {topic[:200]}{'...' if len(topic) > 200 else ''}")
    print(f"Max rounds: {config['max_rounds']}")
    if config.get("test_mode"):
        print(f"Test mode: ON (truncated responses)")
    if kanban_card_id:
        print(f"Kanban card: {kanban_card_id}")
    print()

    # ── Tier 6.3: Kanban card claim ────────────────────────────────
    if kanban_card_id:
        try:
            update_card_status(kanban_card_id, "claim", config=config)
            print(f"  Kanban card claimed → running", flush=True)
        except Exception as e:
            print(f"  ERROR: Failed to claim Kanban card: {e}", flush=True)
            sys.exit(1)

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
            # When using Kanban card, skip test prefix for Drafter —
            # proposal structure validation requires full structured output
            prefix = "" if kanban_card_id else test_prefix
            drafter_prompt = prefix + topic + PROPOSAL_STRUCTURE_REQUIREMENT
        else:
            prefix = "" if kanban_card_id else test_prefix
            # Build revision prompt with objections from Reviewer
            objections_text = "\n".join(f"  - {o}" for o in objections)
            drafter_prompt = (
                f"{prefix}"
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
            if kanban_card_id:
                try:
                    update_card_status(kanban_card_id, "block",
                                       f"ERROR: DRAFT API failure in round {round_num}: {e}",
                                       config=config)
                except Exception:
                    pass
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

        # ── Tier 6.3: Validate proposal structure ──────────────────
        if kanban_card_id:
            passed, missing = validate_proposal_sections(drafter_output)
            if not passed:
                print(f"  ROUND {round_num} DRAFT VALIDATION FAILED: missing {missing}", flush=True)
                try:
                    update_card_status(
                        kanban_card_id, "block",
                        f"DRAFT validation failed in round {round_num}: missing {', '.join(missing)}",
                        config=config,
                    )
                except Exception:
                    pass
                return {
                    "result": "ERROR",
                    "phase": "DRAFT_VALIDATION",
                    "round": round_num,
                    "error": f"Missing required proposal sections: {', '.join(missing)}",
                    "run_id": run_id,
                }

            # ── Write ## Proposal to Kanban card ───────────────────
            try:
                current_body, _ = _read_card_body_only(kanban_card_id)
                cleaned = strip_orchestrator_sections(current_body, keep_section="review")
                new_body = cleaned + f"\n\n## Proposal\n\n{drafter_output}"
                if new_body.startswith("\n"):
                    new_body = new_body.lstrip("\n")
                write_card_body(kanban_card_id, new_body, config)
                print(f"  ROUND {round_num} proposal written to Kanban card", flush=True)
            except Exception as e:
                print(f"  ROUND {round_num} Kanban body write FAILED: {e}", flush=True)
                try:
                    update_card_status(kanban_card_id, "block",
                                       f"ERROR: Kanban body write failed in round {round_num}: {e}",
                                       config=config)
                except Exception:
                    pass
                return {
                    "result": "ERROR",
                    "phase": "KANBAN_WRITE",
                    "round": round_num,
                    "error": f"Kanban body write failed: {e}",
                    "run_id": run_id,
                }

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
            if kanban_card_id:
                try:
                    update_card_status(kanban_card_id, "block",
                                       f"ERROR: REVIEW API failure in round {round_num}: {e}",
                                       config=config)
                except Exception:
                    pass
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

        # ── Tier 6.3: Normalize and write ## Review to Kanban card ─
        if kanban_card_id:
            is_last = (round_num == config["max_rounds"])
            review_section = normalize_review_section(
                reviewer_output, detected_objections, is_consensus, is_last
            )
            try:
                current_body, _ = _read_card_body_only(kanban_card_id)
                cleaned = strip_orchestrator_sections(current_body, keep_section="proposal")
                new_body = cleaned + f"\n\n{review_section}"
                if new_body.startswith("\n"):
                    new_body = new_body.lstrip("\n")
                write_card_body(kanban_card_id, new_body, config)
                print(f"  ROUND {round_num} review written to Kanban card", flush=True)
            except Exception as e:
                print(f"  ROUND {round_num} Kanban review write FAILED: {e}", flush=True)
                try:
                    update_card_status(kanban_card_id, "block",
                                       f"ERROR: Kanban review write failed in round {round_num}: {e}",
                                       config=config)
                except Exception:
                    pass
                return {
                    "result": "ERROR",
                    "phase": "KANBAN_WRITE",
                    "round": round_num,
                    "error": f"Kanban review write failed: {e}",
                    "run_id": run_id,
                }

        # ── Act on consensus ───────────────────────────────────────
        if is_consensus:
            print(f"\n  >>> consensus detected: CONSENSUS_REACHED in Round {round_num} <<<")
            print()
            if kanban_card_id:
                try:
                    update_card_status(kanban_card_id, "complete", config=config)
                    print(f"  Kanban card → done", flush=True)
                except Exception as e:
                    print(f"  WARNING: Failed to complete Kanban card: {e}", flush=True)
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

    if kanban_card_id:
        try:
            update_card_status(kanban_card_id, "block",
                               f"ESCALATE: max rounds ({config['max_rounds']}) reached without consensus",
                               config=config)
            print(f"  Kanban card → blocked", flush=True)
        except Exception as e:
            print(f"  WARNING: Failed to block Kanban card: {e}", flush=True)

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
    parser.add_argument(
        "--kanban-card-id", default=None, metavar="ID",
        help="Read topic from Kanban card, write deliberation artifacts back to card"
    )
    args = parser.parse_args()

    # Load config early — needed for Kanban reads
    config = load_config(args.config)

    # CLI flag overrides
    if args.test:
        config["test_mode"] = True

    # ── Tier 6.3: Kanban card topic resolution ────────────────────
    if args.kanban_card_id:
        try:
            title, body = read_kanban_card(args.kanban_card_id)
            if not title:
                print(f"Error: Kanban card {args.kanban_card_id} has no title")
                sys.exit(1)
            # Use card title as topic, prepend body as context
            topic = title
            if body:
                topic = f"{title}\n\n## Context from Kanban Card\n\n{body}"
            print(f"Topic from Kanban card: {title[:200]}{'...' if len(title) > 200 else ''}")
        except Exception as e:
            print(f"Error: Failed to read Kanban card {args.kanban_card_id}: {e}")
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
    result = run_deliberation(topic, config, kanban_card_id=args.kanban_card_id)

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
