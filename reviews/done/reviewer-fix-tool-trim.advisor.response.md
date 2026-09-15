# Advisor review — reviewer-fix-tool-trim

- packet: `reviews/pending/reviewer-fix-tool-trim.md`
- advisor: advisor on port 8649
- run tag: reviewer-fix-tool-trim @ 2026-09-12T14:36:35-05:00
- at: 2026-09-12T14:39:50
- prompt_tokens: 525830
- completion_tokens: 6989
- total_tokens: 532819
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The project's seed intent is "checks and balances — a worker constrained to my working methods and two objective reviewers as expert advisors." If reviewers are told in their prompt that they have no tools and cannot verify, the check is structurally broken — the advisors become opinion-givers, not measurers. Fixing that prompt is exactly the right work, right now, for what this project is for.

Now the claim-by-claim verdict.

---

C1. ESTABLISHED

The current tools/advisor_review.sh (cis_read_file) shows SCOPE_LINE, RESULT_LINE, and RECONCILE_LINE all now contain the instruction "Use your read-only measurement instruments (cis_read_file, cis_search_files, cis_git_log, cis_git_show, cis_hash_file, cis_list_dir, and the cis_get_* spine queries) to verify any claim before you assert it." I searched the file for "no file access|no tools|You have no" (cis_search_files) and got zero matches ("git grep failed" = exit 1, no hits). Commit e58abac (cis_git_show) is titled "un-blind reviewers: read-only measurement instruments (CARD-01)" and added 288 lines to tools.py — confirming it was the commit that gave reviewers instruments. The claim that the "no tools" text was a leftover from before e58abac is consistent: e58abac added the tools but did not update the prompts that told reviewers they had none.

One nuance: the card names SCOPE_LINE, RESULT_LINE, and RECONCILE_LINE as the three stale lines. REPLY_LINE also now contains the "use your read-only measurement instruments" language. The card does not mention REPLY_LINE, so either it was already updated or it was changed as part of this same fix and the card undercounts. This does not undermine C1's root-cause claim.

C2. ESTABLISHED (with a minor discrepancy)

cis_git_show for e4319cf shows `tools/advisor_review.sh | 12 +--` — 12 lines changed, mostly deletions, consistent with replacing longer "no tools" text with the shorter instrument-citation language. The header comment now reads "The advisor has read-only measurement instruments (cis_* read tools); it may verify against the repo and spine, but not write." The three named prompt lines (SCOPE_LINE, RESULT_LINE, RECONCILE_LINE) all contain the new language. The claim of "5 edits total" (3 prompt lines + header comment + metadata stamp) is plausible given the diffstat, but I cannot independently confirm the exact edit count without the full diff. The substance — three prompt lines were changed from "no tools" to "use your instruments" — is verified.

C3. ESTABLISHED

I read reviews/done/queue-framing-v3.evaluator.response.md (cis_read_file). Its header records `prompt_tokens: 303099`. The response body cites real tool results throughout:
- "cis_get_queue_item for 3.21 returned need_status: 'OPEN'" — confirmed independently by my own cis_get_queue_item call
- "From cis_git_log (limit 20), I can confirm these commit hashes" — lists 11 commits matching my own cis_git_log result
- "cis_git_show" cited for commits 0869c97, 16a30bf, a3f7dea
- "cis_get_recent_runs" — confirmed the ERIC_GATE run
- "cis_get_open_decisions" — confirmed ADR-015/016 DECIDED
- "cis_get_dev_pivot_status" — confirmed DEV-PIVOT-02/17 PARTIALLY_INVALIDATED

The 303,099 figure is also recorded in docs/UNIFIED_BUILD_LIST.md line 3221 (cis_search_files): "evaluator 303,099 on queue-framing-v3." The "5,118 → 303,099" baseline figure is not independently verifiable from the repo — I would need a prior evaluator response showing 5,118 prompt_tokens, and I did not find one. But the key claim — that after the fix, the evaluator used its tools and the response cites real tool results — is fully established.

C4. ESTABLISHED

cis_read_file of runtime/mcp_bridge/tools.py shows READONLY_TOOL_NAMES containing exactly 17 entries. The three named tools (cis_search_semantic, cis_get_similar, cis_search_knowledge) are absent from the set. All three are still present in the TOOLS list with full definitions — they were removed from the read-only surface only, not deleted. The NOTE comment in the set explains the rationale verbatim: "deliberately EXCLUDED from the read-only reviewer surface... KB-exploration tools, not claim-verification tools... ~70s cold start (torch + sentence_transformers + chromadb, ~1.6 GB)." The prior count would have been 17 + 3 = 20, confirming "20 → 17." The git_show diffstat shows `runtime/mcp_bridge/tools.py | 12 ++-` — consistent with removing 3 entries and adding the NOTE block.

One discrepancy: the module docstring at the top of tools.py still says "Defines 14 tools (11 read-only + 3 dispatch)" and lists cis_search_semantic and cis_get_similar among the read-only set. This docstring was not updated as part of this fix. It is stale — the actual TOOLS list defines more than 14 tools (it also includes cis_get_queue_item, cis_get_dev_pivot_status, cis_search_knowledge, cis_read_file, cis_search_files, cis_git_log, cis_git_show, cis_hash_file, cis_list_dir), and the read-only surface is now 17, not 11. This does not undermine C4's claim (the set was correctly trimmed), but it is a documentation gap the card did not mention.

C5. ESTABLISHED

cis_get_queue_item for "3.29" returned: title "Cap MCP tool result sizes and match each profile's tool surface to its role," need_status "HALF_DONE," need_raw "HALF_DONE." The UNIFIED_BUILD_LIST.md (cis_search_files) has the entry at line 3219. Line 3221 records both the done part ("reviewer surface cut") and the remaining part ("result-size caps on the spine-query handlers + a per-profile audit"). The scope field names the right files: runtime/mcp_bridge/tools.py + spine.py handlers + per-profile YAMLs. ESTABLISHED.

C6. PARTIALLY ESTABLISHED

The commit and file count: ESTABLISHED. cis_git_show for e4319cf shows 16 files changed. Counting the regenerated exports: AGENTS.md + 11 HCP files (HCP_00 through HCP_09 + READ_FIRST_HERMES_CONTEXT) = 13 regenerated files. Plus 3 content files (docs/UNIFIED_BUILD_LIST.md, runtime/mcp_bridge/tools.py, tools/advisor_review.sh) = 16 total. Matches the claim exactly.

The export agreement gate PASS: NOT ESTABLISHED. I searched for "export_agreement|EXPORT_AGREE" (cis_search_files) and got zero matches. I cannot find a gate script or a recorded pass/fail result in the repo. The EXPORT_MANIFEST.json (cis_read_file) records git_head as "3f7359c" — the prior commit, not e4319cf. This is consistent with the export having been generated before the commit was made (generate exports, then commit), but it means I cannot confirm from the manifest alone that the exported file hashes match the committed file hashes. The claim may refer to a pre-commit hook or a manual check that is not searchable in the repo. I would need either the gate script's path or a recorded gate result to verify this claim. The file count and commit are confirmed; the gate pass is not.

---

Summary:

C1: ESTABLISHED
C2: ESTABLISHED
C3: ESTABLISHED
C4: ESTABLISHED
C5: ESTABLISHED
C6: PARTIALLY ESTABLISHED — commit and 16-file count confirmed; "export agreement gate PASS" not independently verifiable from the repo

Two issues the card did not mention:
1. The module docstring in tools.py is stale — it says "14 tools (11 read-only + 3 dispatch)" and lists cis_search_semantic/cis_get_similar among the read-only set. The actual read-only surface is 17, and those two plus cis_search_knowledge are excluded. This docstring should have been updated as part of C4.
2. REPLY_LINE in advisor_review.sh also contains the "use your read-only measurement instruments" language, but the card does not mention it as one of the edited lines. Either it was already correct (in which case the card's "3 prompt lines" is right) or it was also changed and the card undercounts.
