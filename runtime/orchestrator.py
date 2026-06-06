#!/usr/bin/env python3
"""
orchestrator.py — Tier 0 Deliberation Engine
CIS Dependency Graph Build Plan v2.0 — Artifact 0.1

Deliberation loop:
  DRAFT(v4pro) → REVIEW(r1) → CONSENSUS_REACHED or OBJECTIONS → repeat
  Max rounds enforced. Eric gate NOT bypassed.

Usage:
  python3 orchestrator.py "Your topic here"
  python3 orchestrator.py --config /path/to/config.yaml "Your topic here"
  echo "Your topic here" | python3 orchestrator.py
"""

import sys
import json
import os
import time
import uuid
import argparse

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


# ── Main deliberation loop ────────────────────────────────────────────

def run_deliberation(topic, config):
    """Run the Drafter→Reviewer deliberation loop. Returns final output dict."""
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    thread_id = f"orch-{run_id}"

    print(f"═══ CIS Deliberation Engine ═══")
    print(f"Run ID: {run_id}")
    print(f"Topic: {topic}")
    print(f"Max rounds: {config['max_rounds']}")
    if config.get("test_mode"):
        print(f"Test mode: ON (truncated responses)")
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
            drafter_prompt = test_prefix + topic
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
            )

        try:
            drafter_resp = call_agent(
                config["drafter_agent"], drafter_prompt, thread_id, config
            )
        except Exception as e:
            print(f"  ROUND {round_num} DRAFT FAILED: {e}", flush=True)
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
        if detect_consensus(reviewer_output, config):
            print(f"\n  >>> consensus detected: CONSENSUS_REACHED in Round {round_num} <<<")
            print()
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

        # ── Detect objections ──────────────────────────────────────
        objections = detect_objections(reviewer_output, config)
        if objections:
            print(f"  objections detected: {len(objections)} objection(s) in Round {round_num}")
            for obj in objections:
                print(f"    - {obj}")
        else:
            # Reviewer didn't signal CONSENSUS_REACHED but also no clear OBJECTIONS
            # Treat the entire reviewer output as potential objections
            print(f"  no structured signals detected in Reviewer output for Round {round_num}")
            # Extract anything that looks like an objection
            objections = [reviewer_output[:500] + ("..." if len(reviewer_output) > 500 else "")]

        rounds_completed = round_num
        print()

    # ── Max rounds reached without consensus ──────────────────────────
    print(f"═══ escalating: max rounds ({config['max_rounds']}) reached without CONSENSUS_REACHED ═══")
    print()

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
    args = parser.parse_args()

    # Get topic
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

    # Load config
    config = load_config(args.config)

    # CLI flag overrides
    if args.test:
        config["test_mode"] = True

    # Run deliberation
    result = run_deliberation(topic, config)

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

    sys.exit(0)


if __name__ == "__main__":
    main()
