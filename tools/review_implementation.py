#!/usr/bin/env python3
"""
review_implementation.py — dispatch the coder's build evidence to the two
pipeline reviewers (review1 8643 + review2 8647) for an IMPLEMENTATION review.

This is the wiring that was missing: after Claude Code builds (sandboxed,
read-only repo, output to its out dir), its evidence is routed to the pipeline
reviewers — NOT the advisor reviewers (8649/8650), which review CARDS.

Review contract (ADR-SEED-012 FINAL_JSON + ADR-SEED-002 evidence rule):
the reviewers assess the BUILD against the card's DONE-WHEN using deterministic
evidence (file contents, diff, test output), never the implementer's self-report.

Run INSIDE the container (gateways are loopback-only there):
  docker exec cis-pipeline python3 /workspace/cis/tools/review_implementation.py \
      <card-id> <evidence-file>
"""

import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Reviewers are agentic (multi-turn tool-calling) Hermes agents. A single chat
# completion can take several minutes while they verify evidence against the
# filesystem. The gateways allow up to 1800s; 900s is enough for verification
# without waiting on a truly stuck request.
REVIEW_TIMEOUT = 900

REVIEWERS = {
    "review1": {
        "url": "http://127.0.0.1:8643/v1/chat/completions",
        "api_key": "cis-qwen-reviewer-gateway-key-2026",
        "label": "review1 (Qwen)",
    },
    "review2": {
        "url": "http://127.0.0.1:8647/v1/chat/completions",
        "api_key": "cis-glm-reviewer-gateway-key-2026",
        "label": "review2 (GLM)",
    },
}

REPO = "/workspace/cis"

REVIEW_SYSTEM = (
    "You are an adversarial reviewer evaluating an IMPLEMENTATION — the coder's "
    "completed build of a card — not the card itself. Your job:\n"
    "1. Check the build against the card's DONE-WHEN criteria using DETERMINISTIC "
    "evidence only (file contents, diff, test output, endpoint responses). The "
    "implementer's prose self-report is NOT evidence (ADR-SEED-002).\n"
    "2. Cite the specific evidence you rely on. If evidence is missing or "
    "self-reported, flag it as an objection.\n"
    "3. End your response with a FINAL_JSON block:\n"
    "```json\n"
    "{\"role\":\"reviewer\",\"status\":\"CONSENSUS_REACHED\"|\"OBJECTIONS\","
    "\"summary\":\"<1-2 sentences>\",\"objections\":[\"<specific>\"],"
    "\"evidence_cited\":\"<what you actually verified>\"}\n"
    "```\n"
    "Status values: CONSENSUS_REACHED (build meets DONE-WHEN) or OBJECTIONS "
    "(specific gaps). Be honest — do not pass a build without evidence."
)


def call_reviewer(name, prompt):
    r = REVIEWERS[name]
    payload = json.dumps({
        "model": "hermes-agent",
        "messages": [
            {"role": "system", "content": REVIEW_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.2,
    }).encode("utf-8")
    req = urllib.request.Request(
        r["url"], data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {r['api_key']}",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=REVIEW_TIMEOUT)
        body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"].get("content", "")
        usage = body.get("usage", {})
        return content, usage
    except Exception as e:
        return f"REVIEW_ERROR: {e}", None


def main():
    if len(sys.argv) != 3:
        print("usage: review_implementation.py <card-id> <evidence-file>")
        sys.exit(1)
    card_id, evidence_file = sys.argv[1], sys.argv[2]

    card_path = f"{REPO}/reviews/pending/{card_id}.md"
    with open(card_path) as f:
        card_text = f.read()
    with open(evidence_file) as f:
        evidence_text = f.read()

    prompt = (
        "IMPLEMENTATION REVIEW\n\n"
        f"=== CARD (DONE-WHEN is the review criteria) ===\n{card_text}\n\n"
        f"=== CODER'S BUILD EVIDENCE ===\n{evidence_text}\n\n"
        "Assess whether the build satisfies the card's DONE-WHEN, citing the "
        "specific evidence you verified. End with the FINAL_JSON block."
    )

    # Run the two reviewers in parallel — they are independent. Total wall-clock
    # is max(review1, review2), not the sum.
    def run_one(name):
        label = REVIEWERS[name]["label"]
        print(f"--- {label} ---", flush=True)
        content, usage = call_reviewer(name, prompt)
        usage_lines = ""
        if usage:
            usage_lines = (
                f"- prompt_tokens: {usage.get('prompt_tokens', '?')}\n"
                f"- completion_tokens: {usage.get('completion_tokens', '?')}\n"
                f"- total_tokens: {usage.get('total_tokens', '?')}\n"
            )
        out_path = f"{REPO}/reviews/done/{card_id}.{name}.impl.response.md"
        with open(out_path, "w") as f:
            f.write(
                f"# Implementation review — {card_id}\n"
                f"- reviewer: {label}\n"
                f"- at: {datetime.now(timezone.utc).isoformat()}\n"
                f"{usage_lines}\n---\n\n"
                f"{content}\n"
            )
        return name, label, out_path, content

    with ThreadPoolExecutor(max_workers=len(REVIEWERS)) as ex:
        futures = {ex.submit(run_one, n): n for n in REVIEWERS}
        for fut in as_completed(futures):
            name, label, out_path, content = fut.result()
            print(f"wrote {out_path}", flush=True)
            print(content[:500], flush=True)
            print("", flush=True)


if __name__ == "__main__":
    main()
