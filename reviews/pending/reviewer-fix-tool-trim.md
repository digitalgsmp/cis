# Reviewer blindness fix + reviewer MCP surface trim

Card from the DeepSeek Hermes Drafter (external advisor). States what was done
this session and where to verify each claim. Judge each claim: ESTABLISHED or
NOT_ESTABLISHED. Use your read-only instruments (cis_read_file, cis_git_log,
cis_git_show, cis_hash_file, cis_get_queue_item) — verify before you assert.

GOAL_ALIGNMENT: seed intent 3 — "checks and balances... a worker constrained to
my working methods and two objective reviewers as expert advisors." This card
documents the repair of that check so it can be independently confirmed.

## Claims

C1. Root cause of reviewer blindness was a stale prompt, not infrastructure and
    not the model. tools/advisor_review.sh still told reviewers "You have no
    file access and no tools" in SCOPE_LINE, RESULT_LINE, and RECONCILE_LINE —
    a leftover from before commit e58abac gave reviewers read-only instruments.
    The evaluator (qwen3.7-max) obeyed it; the advisor (glm-5.2) ignored it.

C2. Fix: replaced those three "no tools" instructions with "use your read-only
    measurement instruments (cis_read_file, cis_git_log, cis_hash_file,
    cis_get_* …) and cite what you checked". 5 edits total in
    tools/advisor_review.sh (3 prompt lines + header comment + metadata stamp).

C3. Fix is effective: after it, the evaluator's review of queue-framing-v3 used
    its tools — prompt_tokens rose 5,118 → 303,099 and the response cites real
    tool results (cis_get_queue_item 3.21 = OPEN, cis_git_log 11 commits,
    cis_git_show diffstats, cis_get_recent_runs run stuck at ERIC_GATE).

C4. Reviewer MCP surface trimmed for cost: removed cis_search_semantic,
    cis_get_similar, cis_search_knowledge from READONLY_TOOL_NAMES in
    runtime/mcp_bridge/tools.py (20 → 17 tools). These three pay a ~70s /
    ~1.6 GB torch+sentence_transformers+chromadb cold start plus oversized
    blobs, and are KB-exploration tools, not claim-verification tools.

C5. Queue item 3.29 added (HALF_DONE) to queue_items — "Cap MCP tool result
    sizes and match each profile's tool surface to its role". Records the done
    part (reviewer surface cut) and the remaining part (result-size caps on the
    spine-query handlers + a per-profile audit).

C6. Committed as e4319cf ("Fix reviewer blindness + trim reviewer MCP surface"),
    16 files including 13 regenerated exports; export agreement gate PASS.
