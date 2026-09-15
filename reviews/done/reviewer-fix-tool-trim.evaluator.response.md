# Advisor review — reviewer-fix-tool-trim

- packet: `reviews/pending/reviewer-fix-tool-trim.md`
- advisor: evaluator on port 8650
- run tag: reviewer-fix-tool-trim @ 2026-09-12T14:36:35-05:00
- at: 2026-09-12T14:43:46
- prompt_tokens: 194992
- completion_tokens: 5070
- total_tokens: 200062
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

C1: ESTABLISHED. The backup tools/advisor_review.sh.bak-20260910-145818 (cis_read_file line 5, 145) contains "The advisor has no tools" and "You have no file access and no tools." The current version (cis_read_file lines 5, 145, 147, 436) now says "read-only measurement instruments" and lists the specific cis_* tools. Commit e58abac (cis_git_log) gave reviewers instruments but the prompt wasn't updated until now.

C2: ESTABLISHED. The diffstat (cis_git_show e4319cf) shows "tools/advisor_review.sh | 12 +--" and I verified the header comment (line 5), SCOPE_LINE (line 145), RESULT_LINE (line 147), and RECONCILE_LINE (line 436) all contain the new instruction text. The "5 edits" claim matches: 3 prompt lines + header + commit metadata.

C3: NOT_ESTABLISHED. docs/UNIFIED_BUILD_LIST.md line 3221 (cis_search_files) records "evaluator 303,099 on queue-framing-v3" — so the post-fix number exists. But I cannot find the 5,118 baseline in the repo. The recent runs (cis_get_recent_runs, last 10) show no run with topic "queue-framing-v3", so I cannot inspect deliberation_rounds for before/after token counts. The tool-use claim is plausible given theThe tool-use claim is plausible given the 303,099 token count exists in the build list, but I cannot independently verify the 5,118 baseline or confirm the evaluator actually called cis_get_queue_item, cis_git_log, cis_git_show, and cis_get_recent_runs as claimed. The recent runs query shows no queue-framing-v3 run in the last 10, so I cannot inspect its deliberation_rounds for tool call evidence. The claim needs a run_id or deliberation_rounds artifact to verify.

C4: ESTABLISHED. READONLY_TOOL_NAMES in runtime/mcp_bridge/tools.py (cis_read_file lines 22-42) contains exactly 17 tools. The comment block explicitly states: "cis_search_semantic / cis_get_similar / cis_search_knowledge are deliberately EXCLUDED from the read-only reviewer surface." The count went from 20 to 17 by removing those three.

C5: ESTABLISHED. Queue item 3.29 (cis_get_queue_item) exists with need_status="HALF_DONE" and title "Cap MCP tool result sizes and match each profile's tool surface to its role". The scope names runtime/mcp_bridge/tools.py and spine.py handlers, matching the card's description of what was done and what remains.

C6: ESTABLISHED. Commit e4319cf (cis_git_show) shows "Fix reviewer blindness + trim reviewer MCP surface" with 16 files changed: tools/advisor_review.sh, runtime/mcp_bridge/tools.py, runtime/manifests/EXPORT_MANIFEST.json, and 13 PROJECT_CONTEXT_PACK_UPLOAD files. The export manifest exists and was modified in this commit.

---

**Summary:**

C1, C2, C4, C5, C6 are ESTABLISHED — verified against backup file, current file, diffstat, queue_items, and git log.

C3 is NOT_ESTABLISHED — the 303,099 token count exists in UNIFIED_BUILD_LIST.md:3221, but I cannot verify the 5,118 baseline or inspect the actual tool calls made during the queue-framing-v3 review. The recent runs (last 10) show no such run, so I cannot check deliberation_rounds for evidence. Need: a run_id or artifact path showing the before/after token counts and tool call records.
