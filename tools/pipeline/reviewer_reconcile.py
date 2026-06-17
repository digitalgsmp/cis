#!/usr/bin/env python3
"""
reconciler.py — Multi-Reviewer Reconciliation Engine with External Escalation

Primary reviewers (R1 + Qwen) deliberate on a proposal.
If they deadlock, external advisors (ChatGPT + Claude) weigh in with
independent advisory opinions. Eric always makes the final call.

Reviewers:
  R1:    http://127.0.0.1:8643  (deepseek-v4-pro, local gateway)
  Qwen:  http://127.0.0.1:8644  (qwen3-vl-30b, local gateway)

Escalation advisors (called on deadlock only):
  ChatGPT: api.openai.com       (requires OPENAI_API_KEY env var)
  Claude:  api.anthropic.com    (requires ANTHROPIC_API_KEY env var)

Usage:
  python3 tools/pipeline/reviewer_reconcile.py --proposal-file proposal.txt
  python3 tools/pipeline/reviewer_reconcile.py --proposal-file proposal.txt --max-rounds 2 --escalate
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone


# ── Config ──────────────────────────────────────────────────────────────

REVIEWERS = {
    "r1": {
        "name": "R1 Reviewer (deepseek-v4-pro)",
        "url": "http://127.0.0.1:8643/v1/chat/completions",
        "api_key": "f0a78f4dffa94705dd8a714bf60155e5fa8209f8b3828860",
        "model": "hermes-agent",
        "max_input_chars": 15000,  # R1 reasoning chokes on large prompts
    },
    "qwen": {
        "name": "Qwen Reviewer (qwen3-vl-30b)",
        "url": "http://127.0.0.1:8002/v1/chat/completions",  # Direct llama-server — bypasses Hermes agent loop (avoids tool-approval hangs)
        "api_key": "not-needed",  # llama-server doesn't require auth
        "model": "qwen3-vl-30b-a3b-instruct-q4_k_m",  # Use the actual model name, not "hermes-agent" which triggers the full agent loop
        "max_input_chars": 20000,
    },
}

# External escalation advisors — only called on deadlock.
# Set env vars to enable; skipped gracefully if missing.
ESCALATION = {
    "chatgpt": {
        "name": "ChatGPT (GPT-4o)",
        "url": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4o",
    },
    "claude": {
        "name": "Claude (Sonnet)",
        "url": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "model": "claude-sonnet-4-20250514",
    },
}


# ── Helpers ─────────────────────────────────────────────────────────────

def call_reviewer(reviewer: dict, system_prompt: str, user_prompt: str,
                  timeout: int = 300) -> dict:
    """POST to a local reviewer's API server and return parsed response."""
    payload = {
        "model": reviewer.get("model", "hermes-agent"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 8192,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        reviewer["url"], data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {reviewer['api_key']}",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return {"ok": True, "content": content, "usage": body.get("usage", {})}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return {"ok": False, "error": f"HTTP {e.code}", "body": err_body[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def call_openai(system_prompt: str, user_prompt: str, timeout: int = 120) -> dict:
    """Call OpenAI ChatGPT API directly."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {"ok": False, "error": "OPENAI_API_KEY not set"}

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return {"ok": True, "content": content, "usage": body.get("usage", {})}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return {"ok": False, "error": f"HTTP {e.code}", "body": err_body[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def call_anthropic(system_prompt: str, user_prompt: str, timeout: int = 120) -> dict:
    """Call Anthropic Claude API directly."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return {"ok": False, "error": "ANTHROPIC_API_KEY not set"}

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "temperature": 0.3,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = json.loads(resp.read().decode("utf-8"))
        content = body["content"][0]["text"]
        return {"ok": True, "content": content, "usage": body.get("usage", {})}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return {"ok": False, "error": f"HTTP {e.code}", "body": err_body[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def extract_final_json(text: str) -> dict | None:
    """Extract and parse a FINAL_JSON block from reviewer output."""
    fence_pattern = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)
    matches = fence_pattern.findall(text)
    for candidate in reversed(matches):
        try:
            parsed = json.loads(candidate.strip())
            if "role" in parsed and "status" in parsed:
                return parsed
        except (json.JSONDecodeError, ValueError):
            continue

    lines = text.strip().split("\n")
    for i in range(len(lines) - 1, -1, -1):
        candidate = "\n".join(lines[i:]).strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            try:
                parsed = json.loads(candidate)
                if "role" in parsed and "status" in parsed:
                    return parsed
            except (json.JSONDecodeError, ValueError):
                continue

    return None


REVIEW_SYSTEM = """You are an adversarial reviewer evaluating a proposal. Your job:
1. Identify factual errors, logical gaps, security issues, and missing edge cases.
2. Be precise — cite specific problems, not general opinions.
3. Your output MUST end with a FINAL_JSON block:

```json
{
  "role": "reviewer",
  "status": "CONSENSUS_REACHED",
  "summary": "<1-3 sentence summary of your verdict>",
  "objections": ["<specific objection 1>", "<specific objection 2>"]  OR  [],
  "recommendation": "<what should happen next>"
}
```

Valid status values:
- CONSENSUS_REACHED — you agree the proposal is acceptable
- OBJECTIONS — you have specific concerns that must be addressed

If you receive the OTHER reviewer's objections in the prompt, you must address each one:
- If you agree with their objection, say so and recommend the fix.
- If you disagree, explain why and maintain your position.
- Then re-evaluate whether consensus is now possible.

BE HONEST. Do not agree just to close the loop. If you genuinely disagree, maintain OBJECTIONS."""


ESCALATION_SYSTEM = """You are an independent advisory reviewer for the CIS (Creative Intelligence System) project.
Two local reviewers (R1/deepseek-v4-pro and Qwen/qwen3-vl-30b) have deadlocked on a proposal.
You are NOT voting. Your job is to provide a clear advisory opinion:

1. Read both reviewers' positions below.
2. Identify which reviewer has the stronger argument on each point of disagreement.
3. Recommend whether the proposal should proceed, be revised, or be blocked.
4. Be decisive — Eric needs a clear recommendation, not more ambiguity.
5. End your response with this JSON block:

```json
{"role":"advisor","recommendation":"APPROVE"|"REVISE"|"BLOCK","rationale":"<1-2 sentences>"}
```"""


# ── Chunking ────────────────────────────────────────────────────────────

def chunk_proposal(text: str, max_chars: int, overlap: int = 200) -> list[str]:
    """Split proposal into chunks that fit within max_chars.

    Tries to split on paragraph/section boundaries. Each chunk includes
    a header noting its position (e.g., '[Chunk 1/5 of proposal]').
    Overlap preserves context across chunk boundaries.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    remaining = text
    chunk_num = 0
    total_chunks = (len(text) // max_chars) + 1

    while remaining:
        chunk_num += 1
        header = f"[Chunk {chunk_num}/{total_chunks} — CIS Oversight Review]\n\n"

        if len(remaining) <= max_chars:
            chunks.append(header + remaining)
            break

        # Try to split on a paragraph boundary near max_chars
        chunk_text = remaining[:max_chars]
        # Find last paragraph break (double newline) in the chunk
        last_break = chunk_text.rfind('\n\n')
        if last_break > max_chars // 2:
            chunk_text = remaining[:last_break]
        else:
            # Fall back to sentence boundary
            for punct in ['. ', '! ', '? ', ':\n', '\n']:
                last_sentence = chunk_text.rfind(punct)
                if last_sentence > max_chars // 2:
                    chunk_text = remaining[:last_sentence + 1]
                    break

        chunks.append(header + chunk_text)

        # Advance with overlap
        advance = len(chunk_text) - overlap
        if advance <= 0:
            advance = len(chunk_text)
        remaining = remaining[advance:]

    # Update total after actual split
    for i, chunk in enumerate(chunks):
        chunks[i] = chunk.replace(f"/{total_chunks}", f"/{len(chunks)}", 1)

    return chunks


def chunked_reconcile(run_id: str, proposal: str, max_rounds: int,
                      do_escalate: bool, verbose: bool,
                      chunk_size: int) -> dict:
    """Run reconciliation on chunked proposal for large documents.

    Each chunk is reviewed independently. Results are aggregated into
    a single combined verdict.
    """
    chunks = chunk_proposal(proposal, chunk_size)

    print(f"═══ Chunked Reconciliation ═══")
    print(f"Proposal: {len(proposal)} chars → {len(chunks)} chunks of ~{chunk_size} chars")
    print()

    all_results = []
    all_objections = []
    consensus_count = 0

    for i, chunk in enumerate(chunks, 1):
        print(f"─── Chunk {i}/{len(chunks)} ({len(chunk)} chars) ───")
        result = reconcile(
            run_id=f"{run_id or 'chunked'}-c{i}",
            proposal=chunk,
            max_rounds=1,  # Single round per chunk (speed)
            do_escalate=False,  # No external escalation per chunk
            verbose=verbose,
        )
        all_results.append(result)

        if result.get("status") == "CONSENSUS_REACHED":
            consensus_count += 1
        elif result.get("r1_objections"):
            all_objections.extend(result.get("r1_objections", []))
        if result.get("qwen_objections"):
            all_objections.extend(result.get("qwen_objections", []))

    # Aggregate verdict
    if consensus_count == len(chunks):
        overall = "CONSENSUS_REACHED"
    elif consensus_count > len(chunks) * 0.7:
        overall = "PARTIAL_CONSENSUS"
    else:
        overall = "OBJECTIONS"

    return {
        "status": overall,
        "round": 0,  # chunked doesn't use rounds
        "chunks_total": len(chunks),
        "chunks_consensus": consensus_count,
        "aggregated_objections": all_objections[:20],  # top 20
        "per_chunk_results": all_results,
    }

def escalate_to_external(proposal: str, r1_status: str, qwen_status: str,
                         r1_objs: list, qwen_objs: list,
                         history: list) -> dict:
    """Call external advisors when local reviewers deadlock."""

    print(f"\n═══ EXTERNAL ESCALATION ═══")
    print(f"Local deadlock: R1={r1_status}, Qwen={qwen_status}")

    # Build escalation prompt with full context
    r1_pos = f"R1 position ({r1_status}):\n" + "\n".join(f"• {o}" for o in r1_objs) if r1_objs else f"R1 position ({r1_status}): No objections — proposal acceptable."
    qwen_pos = f"Qwen position ({qwen_status}):\n" + "\n".join(f"• {o}" for o in qwen_objs) if qwen_objs else f"Qwen position ({qwen_status}): No objections — proposal acceptable."

    escalation_prompt = f"""PROPOSAL UNDER REVIEW:
{proposal[:5000]}

DELIBERATION HISTORY:
{json.dumps(history, indent=2)[:3000]}

CURRENT DEADLOCK:
{r1_pos}

{qwen_pos}

Provide your independent advisory opinion. Who is right on each point? What should happen?"""

    results = {}

    # Try ChatGPT
    print("  → Querying ChatGPT (GPT-4o)...")
    t0 = time.time()
    gpt_resp = call_openai(ESCALATION_SYSTEM, escalation_prompt)
    t1 = time.time()
    if gpt_resp.get("ok"):
        gpt_json = extract_final_json(gpt_resp["content"])
        print(f"    ChatGPT responded in {t1 - t0:.1f}s: "
              f"{gpt_json.get('recommendation', '?') if gpt_json else 'no JSON'}")
        results["chatgpt"] = {
            "ok": True,
            "content": gpt_resp["content"][:2000],
            "verdict": gpt_json,
        }
    else:
        print(f"    ChatGPT: {gpt_resp.get('error')}")

    # Try Claude
    print("  → Querying Claude (Sonnet)...")
    claude_resp = call_anthropic(ESCALATION_SYSTEM, escalation_prompt)
    t2 = time.time()
    if claude_resp.get("ok"):
        claude_json = extract_final_json(claude_resp["content"])
        print(f"    Claude responded in {t2 - t1:.1f}s: "
              f"{claude_json.get('recommendation', '?') if claude_json else 'no JSON'}")
        results["claude"] = {
            "ok": True,
            "content": claude_resp["content"][:2000],
            "verdict": claude_json,
        }
    else:
        print(f"    Claude: {claude_resp.get('error')}")

    if not results:
        print("  ⚠ No external advisors available — API keys not configured.")

    return results


def reconcile(run_id: str, proposal: str, max_rounds: int = 3,
              do_escalate: bool = True, verbose: bool = False):
    """Run multi-reviewer reconciliation loop with escalation."""

    print(f"═══ CIS Reviewer Reconciliation ═══")
    print(f"Run: {run_id or 'direct'}")
    print(f"Proposal length: {len(proposal)} chars")
    print(f"Max rounds: {max_rounds}")
    print(f"Escalation: {'enabled' if do_escalate else 'disabled'}")
    print()

    history = {"r1": [], "qwen": [], "rounds": []}

    for round_num in range(1, max_rounds + 1):
        print(f"─── Round {round_num}/{max_rounds} ───")

        r1_prompt = proposal
        qwen_prompt = proposal

        # Truncate per-reviewer max_input_chars if configured
        for key, reviewer in REVIEWERS.items():
            limit = reviewer.get("max_input_chars")
            if limit and len(proposal) > limit:
                truncated = proposal[:limit] + f"\n\n[... {len(proposal) - limit} more chars truncated for {reviewer['name']}]"
                if key == "r1":
                    r1_prompt = truncated
                elif key == "qwen":
                    qwen_prompt = truncated

        if round_num > 1 and history["rounds"]:
            prev = history["rounds"][-1]
            if prev.get("qwen_objections"):
                obj_text = "\n".join(f"• {o}" for o in prev["qwen_objections"])
                # Compact: don't repeat full proposal (already seen in round 1)
                r1_prompt = (
                    f"ROUND {round_num} CROSS-REVIEW\n"
                    f"Qwen objections from round {round_num-1}:\n{obj_text}\n\n"
                    f"Address each objection. Re-evaluate. Return FINAL_JSON.\n"
                    f"Proposal (same as round 1): {proposal[:500] if len(proposal) > 500 else proposal}"
                )
            if prev.get("r1_objections"):
                obj_text = "\n".join(f"• {o}" for o in prev["r1_objections"])
                # Compact cross-feed: only first 2000 chars of proposal (already seen)
                prop_snip = proposal[:2000] if len(proposal) > 2000 else proposal
                qwen_prompt = (
                    f"ROUND {round_num} CROSS-REVIEW\n"
                    f"R1 objections from round {round_num-1}:\n{obj_text}\n\n"
                    f"Address each objection. Re-evaluate. Return FINAL_JSON.\n"
                    f"Proposal (same as round 1, truncated): {prop_snip}"
                )

        print("  → Querying R1 (8643)...")
        t0 = time.time()
        r1_resp = call_reviewer(REVIEWERS["r1"], REVIEW_SYSTEM, r1_prompt)
        t1 = time.time()
        print(f"    R1 responded in {t1 - t0:.1f}s")
        history["r1"].append(r1_resp)

        print("  → Querying Qwen (8644)...")
        qwen_resp = call_reviewer(REVIEWERS["qwen"], REVIEW_SYSTEM, qwen_prompt)
        t2 = time.time()
        print(f"    Qwen responded in {t2 - t1:.1f}s")
        history["qwen"].append(qwen_resp)

        r1_json = None
        qwen_json = None

        if r1_resp.get("ok"):
            r1_json = extract_final_json(r1_resp["content"])
            if r1_json:
                print(f"    R1 verdict: {r1_json.get('status')}")
            else:
                print(f"    R1: NO VALID FINAL_JSON FOUND")
        else:
            print(f"    R1 ERROR: {r1_resp.get('error')}")

        if qwen_resp.get("ok"):
            qwen_json = extract_final_json(qwen_resp["content"])
            if qwen_json:
                print(f"    Qwen verdict: {qwen_json.get('status')}")
            else:
                print(f"    Qwen: NO VALID FINAL_JSON FOUND")
        else:
            print(f"    Qwen ERROR: {qwen_resp.get('error')}")

        # Repair missing FINAL_JSON
        missing = []
        if r1_json is None and r1_resp.get("ok"):
            missing.append(("r1", r1_resp))
        if qwen_json is None and qwen_resp.get("ok"):
            missing.append(("qwen", qwen_resp))

        for reviewer_key, resp in missing:
            reviewer = REVIEWERS[reviewer_key]
            print(f"\n  ⚠ {reviewer_key.upper()} missing FINAL_JSON — requesting repair...")
            repair_prompt = (
                "Your response above is missing the required FINAL_JSON block. "
                "Append EXACTLY this JSON block:\n\n"
                '```json\n{"role":"reviewer","status":"CONSENSUS_REACHED","objections":[],'
                '"summary":"<your verdict in 1 sentence>"}\n```'
            )
            repair_resp = call_reviewer(reviewer, repair_prompt, resp["content"][-2000:])
            if repair_resp.get("ok"):
                repaired_json = extract_final_json(repair_resp["content"])
                if repaired_json:
                    print(f"    Repair successful: {repaired_json.get('status')}")
                    if reviewer_key == "r1":
                        r1_json = repaired_json
                    else:
                        qwen_json = repaired_json
                else:
                    print(f"    Repair FAILED")
            else:
                print(f"    Repair FAILED")

        if r1_json is None or qwen_json is None:
            print(f"\n  ⚠ Missing FINAL_JSON after repair.")
            if do_escalate:
                ext = escalate_to_external(proposal,
                    r1_json.get("status","UNKNOWN") if r1_json else "NO_RESPONSE",
                    qwen_json.get("status","UNKNOWN") if qwen_json else "NO_RESPONSE",
                    r1_json.get("objections",[]) if r1_json else [],
                    qwen_json.get("objections",[]) if qwen_json else [],
                    history["rounds"])
                return {"status": "ESCALATE", "round": round_num,
                        "external": ext, "reason": "Missing FINAL_JSON"}
            return {"status": "ERROR", "round": round_num}

        r1_status = r1_json.get("status", "UNKNOWN")
        qwen_status = qwen_json.get("status", "UNKNOWN")
        r1_objs = r1_json.get("objections", []) or []
        qwen_objs = qwen_json.get("objections", []) or []

        round_record = {
            "round": round_num,
            "r1_status": r1_status,
            "qwen_status": qwen_status,
            "r1_objections": r1_objs,
            "qwen_objections": qwen_objs,
        }
        history["rounds"].append(round_record)

        # ── Consensus ──
        if r1_status == "CONSENSUS_REACHED" and qwen_status == "CONSENSUS_REACHED":
            print(f"\n  ✅ JOINT CONSENSUS REACHED (round {round_num})")
            return {
                "status": "CONSENSUS_REACHED",
                "round": round_num,
                "r1_summary": r1_json.get("summary", ""),
                "qwen_summary": qwen_json.get("summary", ""),
                "history": history["rounds"],
            }

        # ── Deadlock → Escalate ──
        if round_num >= max_rounds:
            print(f"\n  ⚠ MAX ROUNDS — deadlock: R1={r1_status}, Qwen={qwen_status}")
            if do_escalate:
                ext = escalate_to_external(proposal, r1_status, qwen_status,
                                           r1_objs, qwen_objs, history["rounds"])
                return {
                    "status": "ESCALATE",
                    "round": round_num,
                    "r1_status": r1_status,
                    "qwen_status": qwen_status,
                    "r1_objections": r1_objs,
                    "qwen_objections": qwen_objs,
                    "external": ext,
                    "history": history["rounds"],
                }
            return {
                "status": "ESCALATE",
                "round": round_num,
                "r1_status": r1_status,
                "qwen_status": qwen_status,
                "r1_objections": r1_objs,
                "qwen_objections": qwen_objs,
                "history": history["rounds"],
            }

        print(f"  ↻ Round {round_num}: R1={r1_status}, Qwen={qwen_status} — continuing\n")

    return {"status": "ERROR", "round": max_rounds}


# ── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CIS Multi-Reviewer Reconciliation Engine"
    )
    parser.add_argument("--proposal-file", required=True)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--escalate", action="store_true", default=True,
                        help="Enable external escalation on deadlock (default: on)")
    parser.add_argument("--no-escalate", dest="escalate", action="store_false",
                        help="Disable external escalation")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what each reviewer would receive without calling APIs")
    parser.add_argument("--chunk-size", type=int, default=None,
                        help="Split proposals larger than this many chars into chunks. "
                             "Each chunk is reviewed independently. Default: no chunking.")

    args = parser.parse_args()

    with open(args.proposal_file) as f:
        proposal = f.read()

    if not proposal.strip():
        print("ERROR: Empty proposal file.", file=sys.stderr)
        sys.exit(1)

    # ── Dry-run mode ──────────────────────────────────────────────────
    if args.dry_run:
        print("═══ DRY RUN — No API calls ═══")
        print(f"Proposal: {args.proposal_file}")
        print(f"Proposal length: {len(proposal)} chars")
        print()

        for key, reviewer in REVIEWERS.items():
            limit = reviewer.get("max_input_chars")
            effective = proposal
            truncated = False
            if limit and len(proposal) > limit:
                effective = proposal[:limit]
                truncated = True

            # Rough token estimate (avg 4 chars per token)
            system_tokens = len(REVIEW_SYSTEM) // 4
            prompt_tokens = len(effective) // 4
            total_tokens = system_tokens + prompt_tokens

            print(f"─── {reviewer['name']} ───")
            print(f"  Model: {reviewer['model']}")
            print(f"  Max input chars: {limit or 'unlimited'}")
            print(f"  Effective prompt: {len(effective)} chars")
            print(f"  System prompt: {len(REVIEW_SYSTEM)} chars")
            print(f"  Estimated tokens: ~{system_tokens} (system) + ~{prompt_tokens} (prompt) = ~{total_tokens}")
            if truncated:
                cut = (limit or 0)
                print(f"  ⚠ TRUNCATED: {len(proposal) - cut} chars cut")
            print(f"  Headroom: {'✅ OK' if total_tokens < 28000 else '⚠️ TIGHT' if total_tokens < 32000 else '🔴 OVERFLOW LIKELY'}")
            print(f"  First 200 chars: {effective[:200]}…")
            print()

        print("Dry run complete. Remove --dry-run to execute.")
        sys.exit(0)

    # ── Chunked mode ──────────────────────────────────────────────────
    if args.chunk_size and len(proposal) > args.chunk_size:
        print(f"Proposal ({len(proposal)} chars) exceeds chunk size ({args.chunk_size}).")
        print(f"Running chunked reconciliation...")
        print()
        result = chunked_reconcile(
            run_id=args.run_id or "",
            proposal=proposal,
            max_rounds=args.max_rounds,
            do_escalate=args.escalate,
            verbose=args.verbose,
            chunk_size=args.chunk_size,
        )
    else:
        result = reconcile(
            run_id=args.run_id or "",
            proposal=proposal,
            max_rounds=args.max_rounds,
            do_escalate=args.escalate,
            verbose=args.verbose,
        )

    print("\n═══ FINAL RESULT ═══")
    output = {
        "status": result["status"],
        "rounds_taken": result.get("round", 0),
        "r1_verdict": result.get("r1_status", result.get("r1_summary", "")),
        "qwen_verdict": result.get("qwen_status", result.get("qwen_summary", "")),
    }
    if result.get("chunks_total"):
        output["chunks"] = {
            "total": result["chunks_total"],
            "consensus": result["chunks_consensus"],
            "objections_count": len(result.get("aggregated_objections", [])),
        }
    if result.get("external"):
        ext = result["external"]
        output["external_advisors"] = {
            k: v.get("verdict", {}).get("recommendation", "?")
            for k, v in ext.items() if v.get("ok")
        } if ext else "none available"
    print(json.dumps(output, indent=2))

    sys.exit(0 if result["status"] == "CONSENSUS_REACHED" else 1)


if __name__ == "__main__":
    main()
