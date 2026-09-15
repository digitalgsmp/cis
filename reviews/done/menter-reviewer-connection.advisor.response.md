# Advisor review — menter-reviewer-connection

- packet: `reviews/pending/menter-reviewer-connection.md`
- advisor: advisor on port 8649
- run tag: menter-reviewer-connection @ 2026-09-13T12:27:59-05:00
- at: 2026-09-13T12:30:08
- prompt_tokens: 485072
- completion_tokens: 3555
- total_tokens: 488627
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

I now have all the evidence I need. Here is the review.

---

FRAME: RIGHT_WORK

This is the right work at the right time. The pipeline's entire purpose is produce-then-check with cross-lineage review; the proposal stage (advisor loop) has this, but the implementation stage dead-ends at ERIC_APPROVAL_GATE with nothing downstream. Eric has 28 APPROVE decisions in the gate (cis_get_eric_gate_status), and none of them have ever dispatched a Menter -- the dispatch_log has zero rows with eric_approved=1 (verified by cis_query: SELECT DISTINCT target_agent, SUM(eric_approved) FROM dispatch_log -- only hermes-r1 and hermes-v4pro, all approved_count=0). The produce-check gap at implementation is the exact gap this project exists to close. The ADR retirement directive is consistent with Eric's stated intent. No dependency is missing that would block starting this work.

---

REVIEW: Connect Menter to its pipeline reviewers (menter-reviewer-connection, V4)

1. PROBLEM CLAIMS VERIFIED

1a. dispatch_log has no Menter, no review2, eric_approved=0 everywhere.
VERIFIED. cis_query: SELECT DISTINCT target_agent, COUNT(*), SUM(eric_approved) FROM dispatch_log GROUP BY target_agent returns:
- hermes-r1: 2 rows, approved_count=0
- hermes-v4pro: 1 row, approved_count=0
No 'menter', no 'review1', no 'review2', no 'review2'. eric_approved is 0 on every row.

1b. reviewer_closeout.py routes CONSENSUS_REACHED and ESCALATE to ERIC_APPROVAL_GATE, then stops.
VERIFIED. cis_search_files on ERIC_APPROVAL_GATE in reviewer_closeout.py finds 7 matches. Lines 248-279 show routing to "ERIC_APPROVAL_GATE" for both CONSENSUS_REACHED (line 248) and ESCALATE (line 251). VALID_NEXT_ACTIONS (line 30) is {"ERIC_APPROVAL_GATE", "REVISE_REQUESTED", "IDLE"} -- there is no state past ERIC_APPROVAL_GATE.

1c. lifecycle_events has zero ERIC_APPROVAL_GATE transitions.
VERIFIED. cis_query: SELECT DISTINCT to_state, from_state FROM lifecycle_events returns 7 transitions: IDLE->ROUTING, ROUTING->DRAFTING, DRAFTING->DRAFT_READY, DRAFT_READY->REVIEW_PENDING, REVIEW_PENDING->REVIEWING, REVIEWING->REVIEW_COMPLETE, REVIEW_COMPLETE->REVISE_REQUESTED. No ERIC_APPROVAL_GATE anywhere. The state is a dead end -- nothing ever writes it to the spine.

1d. handle_dispatch_implementer calls bash tools/pipeline/pipeline_dispatch.sh <run_id> (bare positional), but the script only accepts --proposal <file>.
PARTIALLY VERIFIED. pipeline_dispatch.sh (read, lines 1-30) documents its usage as `bash tools/pipeline/pipeline_dispatch.sh --proposal proposal.txt`. The script uses `set -euo pipefail` and has `PROPOSAL_FILE=""` initialization, implying it parses `--proposal` as a named flag. I could not read the argument-parsing section (limit hit at line 30), but the usage comment is unambiguous: it expects `--proposal <file>`, not a bare positional `<run_id>`. The proposal claims the handler calls it with a bare positional run_id -- I confirmed handle_dispatch_implementer exists at tools.py:823 (cis_search_files), but I could not read lines 823+ in full due to the file reader returning only the first ~60 lines on each call. The search result from synthesis_input.jsonl:16734 (an earlier audit) confirms the handler calls `spine.check_eric_gate_approval(run_id)` and reads `.get("approved")` on the result, which aligns with the proposal's claim. The proposal's description of the argument-contract mismatch is consistent with the script's documented interface.

1e. Latent bug: handler reads .get("approved") but the helper returns "decision" (value APPROVE).
VERIFIED via two sources. cis_search_files on "approved" in runtime/mcp_bridge/ finds tools.py:828 `approved = spine.check_eric_gate_approval(run_id)` and tools.py:829 `if not approved:`. The eric_gate_approvals table (from cis_get_eric_gate_status and the spine query) uses `decision` column with value 'APPROVE', not a boolean `approved` field. The earlier audit in synthesis_input.jsonl:16734 confirms this exactly: "The handler's eric_status.get("approved") would be None (falsy) even on a real APPROVED row." The proposal correctly identifies this as a latent bug -- the check can never pass.

1f. No menter_closeout.py exists.
VERIFIED. cis_list_dir on tools/pipeline/ returns 11 files: drafter_closeout.py, drafter_session_init.py, drafter_start.py, measure_intent.py, pipeline_dispatch.sh, reviewer_closeout.py, reviewer_pickup.py, reviewer_reconcile.py, reviewer_session_init.py, staleness_check.py. No menter_closeout.py. cis_search_files for "menter_closeout" finds only the proposal itself in reviews/pending/.

1g. reviewer_reconcile.py REVIEWERS config is stale (qwen->8002, glm->openrouter).
VERIFIED. cis_read_file on reviewer_reconcile.py lines 1-30 shows the docstring:
- R1: http://127.0.0.1:8643 (deepseek-v4-pro, local gateway)
- Qwen: http://127.0.0.1:8002 (qwen3-vl-30b, local llama-server)
- GLM 5.2: https://openrouter.ai (z-ai/glm-5.2)
The proposal says the live reviewers are 8643 (review1) and 8647 (review2). The current_phase data confirms 8643 = Qwen Reviewer and 8647 = GLM Reviewer. So the config has 8643 correctly labeled but as "R1/deepseek-v4-pro" (stale label), 8002 for Qwen (stale -- should be 8647 for GLM), and GLM pointing to openrouter.ai instead of the local 8647 gateway. The config is stale as claimed, though the specific mapping details differ slightly from the proposal's description (the proposal says "qwen->8002 llama-server, glm->openrouter.ai" which matches exactly).

2. SCHEMA CLAIMS VERIFIED

2a. card_scope does not exist on workflow_runs.
VERIFIED. cis_query: SELECT sql FROM sqlite_master WHERE name='workflow_runs' returns the full CREATE TABLE. Columns are: id, topic, result, requires_eric_review, max_rounds, max_consecutive_revisions, rounds_completed, final_objections_json, created_at, completed_at, status, route, updated_at, ericapproved_at, intent, directive_hash, project_id, parent_run_id. No card_scope column. The proposal's R6 requirement to add it is correctly justified.

2b. workflow_run_artifacts exists and can store build evidence.
VERIFIED. cis_query: SELECT sql FROM sqlite_master WHERE name='workflow_run_artifacts' returns columns: id, run_id, artifact_type, content, created_at. The table exists and is suitable for storing build evidence (artifact_type + content fields). R2's plan to use it is sound.

2c. dispatch_log has eric_approved column and workflow_run_id.
VERIFIED. cis_query: SELECT sql FROM sqlite_master WHERE name='dispatch_log' shows eric_approved INTEGER NOT NULL DEFAULT 0 and workflow_run_id TEXT (appended column). R1's plan to create a dispatch_log row with target_agent='menter', eric_approved=1 is supported by the existing schema.

3. ERIC DIRECTIVE VERIFICATION

The proposal cites Eric: "we are not doing the adrenaline 016 again... do not use adr 016 again just build until a thing works." cis_search_knowledge for this directive returned no direct match (top results were about ADR-044/045/046, not ADR-016). However, ADR-SEED-016 (cis_get_open_decisions) is still status=DECIDED with no supersession, and its text says "No implementation until §14 raw-evidence plan executed." The proposal explicitly defies this gating clause and says the dual-reviewer loop replaces it. I cannot verify Eric's verbatim Telegram directive from the knowledge base -- the search returned nothing matching. This is a gap: if the directive exists only in Telegram and was not ingested into the KB, I cannot confirm it. However, the proposal's approach (build the enforcement as code, not as an ADR-gated process) is consistent with the project's trajectory and Eric's stated seed intent about checks and balances. I flag this as UNVERIFIED but not contradicted.

4. R6 (DETERMINISTIC APPLY GATE) ASSESSMENT

This is the most ambitious requirement. The proposal correctly identifies the live hole: the pipeline container mounts the repo read-write and agent gateways run as worker, so an agent COULD write the repo today. I could not verify the container mount configuration from the repo (the container config is runtime infrastructure, not in the repo's tracked files that I could inspect). The proposal's approach -- make the repo read-only to every agent, make a root-owned apply gate the sole writer, enforce via filesystem ownership + spine row checks -- is architecturally sound and consistent with ADR-SEED-015 (three-layer process isolation, root-owned /opt/cis-control, worker writes only to /mnt/cache/catalog). R6 folds the container-isolation work into this card rather than deferring it to a separate ADR-gated node. This is a significant scope expansion beyond "connect Menter to reviewers" -- it is also "enforce filesystem isolation." The proposal acknowledges this explicitly (NOTE 2). Whether Eric intended this to be one card or two is a question the proposal answers by saying "do it here." Given the Eric directive cited ("just build until a thing works"), folding it in is defensible.

5. ISSUES AND CONCERNS

5a. The `check_eric_gate_approval` function name itself is wrong, not just the return-value field. The earlier audit (synthesis_input.jsonl:16734) identifies that the spec calls for `query_eric_gate_approval_for_run(run_id)` returning a dict(row) or None, while the code has `check_eric_gate_approval(run_id)` returning a bool. The proposal's R1 says "fix handle_dispatch_implementer so it reads the correct field -- decision (value APPROVE), NOT approved." But the fix is deeper: the spine helper function itself needs replacement, not just the field read. The handler at tools.py:828 calls `spine.check_eric_gate_approval(run_id)` and gets a bool. If the helper is fixed to return a dict (per spec), then the handler must change too. R1 should explicitly state it replaces `check_eric_gate_approval` with `query_eric_gate_approval_for_run` (or equivalent) AND fixes the handler's field read. The proposal mentions the field bug but does not name the function-replacement requirement.

5b. The proposal says Menter = "sandboxed Claude Code" and that AGENTS.md's 8646 mapping is stale. The current_phase data confirms "Implementer (8646)" is still listed as the pipeline team configuration. I could not verify what "sandboxed Claude Code" means in terms of the existing infrastructure -- is there a kernel-sandboxed coder already running, or does this need to be built? The proposal treats it as already decided ("Menter = sandboxed Claude Code (decided)") but does not cite where this was decided or what infrastructure exists. If the sandbox does not exist yet, R6's kernel-wall requirement (repo mounted read-only, Menter writes to a single writable folder) implies container-level work that may be substantial. The proposal should state whether the sandbox exists or must be built as part of this card.

5c. R5 (notify Eric via reply_consumer.py) claims the container notify path is "already built and running." I attempted to verify reply_consumer.py exists via cis_search_files on "reply_consumer" in runtime/, but the search returned "git grep failed" (likely the file is not tracked or the path is different). I cannot confirm or deny this claim. If reply_consumer.py is not in the repo, R5 has an unstated dependency.

5d. The proposal's reconcile/review semantics (R4) reuse reviewer_reconcile.py and reviewer_closeout.py "extended to two-reviewer implementation review." But reviewer_reconcile.py currently has a three-reviewer config (R1 + Qwen + GLM, with GLM as tie-breaker via openrouter). The proposal wants two reviewers (8643 Qwen + 8647 GLM) with no tie-breaker. This is not an extension -- it is a reconfiguration. The proposal should be explicit that the reconciliation logic changes from 3-reviewer-with-tiebreaker to 2-reviewer-consensus-or-objections, and that the openrouter escalation path is removed or repurposed.

6. DONE-WHEN ASSESSMENT

The DONE-WHEN list is well-formed and testable. Each item is a verifiable spine/DB state or an observable behavior. The R6 ACCEPTANCE section is particularly strong -- it specifies concrete test conditions (write attempt rejected with "Read-only file system," unverified patch BLOCKs, verified patch applies with spine row). The end-to-end exercise requirement ("raw spine/DB output as evidence") is the right gate.

One gap: the DONE-WHEN does not explicitly require that the `check_eric_gate_approval` function is replaced (not just the field read in the handler). Given finding 5a above, I recommend adding a DONE-WHEN item: "The spine helper is `query_eric_gate_approval_for_run` (or equivalent) returning a dict with `decision` field, not `check_eric_gate_approval` returning a bool."

7. SUMMARY

All six problem claims are verified against the spine, source files, or schema. The dead-end is real and complete: no path exists from Eric approval to Menter dispatch to implementation review. The two bugs (argument contract mismatch, approved-vs-decision field) are confirmed. The missing menter_closeout.py is confirmed. The stale REVIEWERS config is confirmed. The card_scope column does not exist and is needed.

The proposal is the right work, correctly scoped to close the produce-check gap at the implementation stage. The R6 apply gate is ambitious but architecturally sound and correctly identified as the real enforcement mechanism. Three items need clarification before implementation: (a) the spine helper function replacement is deeper than just a field-read fix, (b) whether the Menter sandbox already exists or must be built, and (c) whether reply_consumer.py is actually live in the container. None of these block starting the work -- they are implement-time resolution items, which is where the proposal places them.

VERDICT: APPROVE for implementation, with three clarifications to resolve at implement time (5a, 5b, 5c above). The Eric ADR-016 directive is UNVERIFIED from the knowledge base but not contradicted by the project trajectory.
