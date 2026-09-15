# Advisor review — container-working-state-blocks

- packet: `reviews/pending/container-working-state-blocks.md`
- advisor: advisor on port 8649
- run tag: container-working-state-blocks @ 2026-09-13T11:09:02-05:00
- at: 2026-09-13T11:12:23
- prompt_tokens: 568276
- completion_tokens: 2983
- total_tokens: 571259
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The container working-state block assessment is the right work at the right time. The project exists to run a multi-agent deliberation pipeline that produces verified work artifacts with Eric's approval, and the pipeline dead-ends at proposal approval -- Eric has approved runs, but nothing after that gate dispatches a builder, reviews the build, or verifies the result. The container has the gateways, the advisor review loop, and the Eric Gate mechanism working. What is missing is everything downstream of Eric's approval. The TG2 two-way phone notification (queue 3.31) is the current item per cis_get_current_phase, and both advisor lineages returned FRAME: RIGHT_WORK for it (reviews/done/tg2-two-way-report.advisor.response.md, reviews/done/tg2-two-way-report.evaluator.response.md). The block assessment is the right work because it surfaces what is actually broken before more pieces are built on top of gaps.

Now the ordered block list. Each block is backed by evidence I checked with read-only instruments.

BLOCK 1 — The pipeline dead-ends at ERIC_GATE: no Menter dispatch, no implementation review, no verify

What it is: After Eric approves a proposal (eric_gate_approvals decision=APPROVE), nothing dispatches Menter to build. The relay state machine (runtime/abstraction/pipeline_relay.py, 4018 lines) defines states EXECUTION, VERIFICATION, CODE_REVIEW_GATE, but no code path wires ERIC_GATE to Menter dispatch. The dispatch_log table has only two target_agent values ever: hermes-r1 (2 rows) and hermes-v4pro (1 row) -- zero dispatches to menter, review2, or verify (verified via cis_query: SELECT target_agent, COUNT(*) FROM dispatch_log GROUP BY target_agent). The tools/pipeline/ directory (verified via cis_list_dir) contains drafter_*, reviewer_*, pipeline_dispatch.sh, staleness_check.py, measure_intent.py -- but NO menter_closeout.py, NO verify_closeout.py, NO menter_start.py, NO implementation-review dispatch script. The menter-reviewer-connection.md card (reviews/pending/) documents this with specific evidence: reviewer_closeout.py routes CONSENSUS_REACHED to ERIC_APPROVAL_GATE then stops with no successor state; runtime/mcp_bridge/tools.py:handle_dispatch_implementer calls pipeline_dispatch.sh with a bare positional arg, but pipeline_dispatch.sh expects --proposal <file> and rejects it ("Unknown arg").

Why it blocks: This is the single largest gap. Without it, the full loop (Author -> advisor review -> Claude sandboxed build -> pipeline review -> verification -> evidence to Eric) cannot run past the Eric Gate. Every downstream block is moot until the pipeline can dispatch a builder and route its output to reviewers and a verifier. This is the produce->check gap at the IMPLEMENTATION stage.

Next action: Implement the menter-reviewer-connection card (R1-R6 as specified in reviews/pending/menter-reviewer-connection.md). R1: fix the dispatch contract and create a menter dispatch on ERIC_APPROVAL_GATE approval. R2: menter_closeout.py to capture build evidence. R3: implementation review dispatch to review1+review2 with the build-evidence handle. R4: reconcile/closeout on build evidence. R5: verify_closeout.py. R6: notify Eric via the container TG2 path.

BLOCK 2 — Claude Code sandbox is not integrated into the pipeline relay

What it is: tools/run_claude_sandbox.sh (64 lines, verified) exists and works as a standalone kernel-sandboxed Docker container: repo mounted read-only (-v "$REPO":/workspace/cis:ro), single writable output dir (-v "$OUTDIR":/workspace/output:rw), Claude runs headless (claude -p) with --allowedTools. The §14 evidence (enforcement/mwl-proof-v2/RESULTS/s14_evidence_20260912.md, commit 60703c8) demonstrates a read-only mount rejects every write. But this script runs as a SEPARATE docker container with --entrypoint sh, overriding the image CMD. It is NOT invoked from inside the cis-pipeline container by the relay or any pipeline tool. No code in pipeline_relay.py or tools/pipeline/ calls run_claude_sandbox.sh. The sandbox-claude-code.md card (reviews/pending/) is PENDING -- it has not been reviewed or approved.

Why it blocks: The sandbox exists as a proven mechanism, but the pipeline cannot use it. When Menter is dispatched (Block 1), it needs to invoke Claude Code in the sandbox. Without integration, Menter has no constrained coder to call. The sandbox is the prerequisite Eric named: "sandbox Claude before wiring any implementation review" (sandbox-claude-code.md, GOAL_ALIGNMENT).

Next action: Review and approve the sandbox-claude-code.md card. Then wire the Menter dispatch (from Block 1's R1) to invoke run_claude_sandbox.sh with the approved card's directive as the prompt, capturing the output dir as the build-evidence handle.

BLOCK 3 — The loop driver is host-resident, not in the container

What it is: advisor_review.sh (1087 lines, verified) runs from the HOST and docker-execs into the container: CONTAINER="${CIS_CONTAINER:-cis-pipeline}" and the gateway call uses docker exec -i -u worker "$CONTAINER" (line ~80). The script sets REPO_ROOT from BASH_SOURCE, not from /workspace/cis. This means the advisor review loop -- which builds packets, hashes them, records deliberation_rounds, writes artifacts, and manages pauses -- is driven from outside the container. The container has gateways and a pipeline API (port 5000) but does not have the loop driver. The entrypoint.sh (226 lines, verified) starts 8 gateways + the Flask API and ends with wait $PIPELINE_PID -- it does not start any loop driver or reply consumer.

Why it blocks: For the container to be self-sufficient (the stated goal of the container transition), the loop driver must run inside it. The TG2 two-way reply consumer (tools/reply_consumer.py) can release a pause row from inside the container, but it cannot advance the loop because the loop driver (advisor_review.sh) is on the host. The advisor review identified this as the design's largest unresolved question: "the release is specified, but the advance is hand-waved" (reviews/done/tg2-two-way-report.advisor.response.md, concern A).

Next action: Either (a) move advisor_review.sh into the container and invoke it from there, or (b) build a container-side loop driver that replicates the packet-build/hash/record/artifact logic. The advisor review's recommendation: specify a concrete contract for what "advance" means before implementation.

BLOCK 4 — TG2 reply consumer's advance mechanism is underspecified

What it is: tools/reply_consumer.py exists (per context summary) and can poll Telegram for replies from Eric and flip a PENDING pause row to CONSENSUS_REACHED. But what happens after the release is not concrete. The advisor review (reviews/done/tg2-two-way-report.advisor.response.md, concern A) found: "the proposal does not specify what 'calls the gateways for the next round' means concretely. The existing --continue path in advisor_review.sh does ONLY the release -- it calls pause_state release and exits. The actual next-round invocation is a separate advisor_review.sh <id> call made by whatever external loop driver exists." The consumer would need to either invoke advisor_review.sh (host-resident, docker-execs in -- Block 3) or replicate its logic.

Why it blocks: Eric can release a pause from his phone, but the loop does not advance. This is the difference between "Eric can reply from his phone" and "Eric canreply from his phone and the loop actually continues." Without the advance, a phone release just sits there -- someone has to manually run the next round from a terminal. That defeats the purpose of the two-way mechanism.

Next action: Define the advance contract. The consumer must either (a) invoke advisor_review.sh from inside the container (requires Block 3 resolved), or (b) call the gateway HTTP endpoints directly and replicate the packet-build/hash/record logic in Python. Option (b) is more work but removes the host dependency entirely. This should be resolved as part of the TG2 card's implementation, before the consumer is trusted as the primary release path.

BLOCK 5 — /tmp ack-state file does not survive container removal

What it is: The reply consumer's "hold" ack-state lives at /tmp/cis-logs/reply_consumer.ack. The advisor review (reviews/done/tg2-two-way-report.advisor.response.md, concern B) found that run_container.sh does `docker rm -f` before each start, so /tmp is wiped. A "hold" ack would be lost on restart, and Eric would be re-notified for a pause he already held.

Why it blocks: Not a hard block on the loop running, but a UX regression that undermines trust in the two-way mechanism. Eric says "hold" and gets re-notified anyway. If this happens during real work, it creates confusion about whether his instruction was received.

Next action: Persist the ack set under /workspace/cis (the persistent mount) or as a spine row, not in /tmp. The advisor review recommended either acknowledging this as acceptable for MVP or moving it to a persistent location.

BLOCK 6 — Double-notification during coexistence

What it is: advisor_review.sh's notify_stop() calls python3 "$REPO_ROOT/tools/pause_notify.py" (verified in the advisor response, concern C). The container-side reply consumer also pushes via TG2. During coexistence (the default per D2 of the TG2 proposal), both fire, and Eric gets two notifications for one pause.

Why it blocks: Not a hard block, but it creates ambiguity. Eric sees two messages for the same event and does not know which path is authoritative. If he replies to one but not the other, the system's state is unclear.

Next action: Guard the host notify_stop() to check whether the container consumer is running before firing, or designate only one push path as active at a time. Resolve before the TG2 mechanism is trusted as primary.

BLOCK 7 — No backoff on repeated release failure

What it is: If the reply consumer receives Eric's "go" but the release fails (e.g., DB locked), it replies "release failed -- run --continue from the terminal" and advances Telegram's update_id offset only after success (advisor response, concern F). But if the release keeps failing, Eric gets this failure message every 30 seconds on every poll cycle.

Why it blocks: Not a hard block, but a noise problem that would make the phone channel unusable during a failure condition. Eric's phone would spam with failure messages.

Next action: Add a backoff or max-retry before falling back to "run --continue." Three retries with exponential backoff, then a single "release failed, manual intervention required" message and stop polling.

BLOCK 8 — No handling for multiple PENDING pause rows

What it is: The reply consumer resolves the card id from "the single PENDING pause row" (advisor response, concern H). The system's invariant is one-card-at-a-time, so this should not happen. But if it does, the consumer's behavior is undefined.

Why it blocks: Edge case, not a current block. The invariant holds today (0 pending pause rows, verified via cis_query: SELECT * FROM deliberation_rounds WHERE reviewer_role='pause' AND reviewer_signal='PENDING' returned 0 rows). But the consumer should be defensive.

Next action: Add a check: if more than one PENDING pause row exists, reply "multiple cards paused, specify which" and refuse to act. Low priority.

SUMMARY OF PRIORITY ORDER

1. Block 1 (pipeline dead-ends at ERIC_GATE) -- the foundational gap. Without this, no full loop is possible.
2. Block 2 (Claude sandbox not integrated) -- prerequisite to Block 1's Menter dispatch actually building anything.
3. Block 3 (loop driver is host-resident) -- the container cannot be self-sufficient until this moves inside.
4. Block 4 (TG2 advance underspecified) -- depends on Block 3; the phone release works but the loop does not advance.
5. Block 5 (/tmp ack persistence) -- UX regression, not a hard block.
6. Block 6 (double-notification) -- coexistence noise, resolve before TG2 is primary.
7. Block 7 (no backoff on release failure) -- noise during failure, low priority.
8. Block 8 (multiple PENDING rows) -- edge case, invariant holds today.

Evidence sources cited:
- cis_query: dispatch_log GROUP BY target_agent (2 agents, 0 menter/verify)
- cis_query: deliberation_rounds WHERE reviewer_role='pause' AND reviewer_signal='PENDING' (0 rows)
- cis_query: eric_gate_approvals is_current=1 (5 rows, 1 APPROVE active)
- cis_list_dir: tools/pipeline/ (no menter_closeout.py, no verify_closeout.py)
- cis_read_file: reviews/pending/menter-reviewer-connection.md (120 lines, documents the dead-end)
- cis_read_file: reviews/pending/sandbox-claude-code.md (95 lines, sandbox prerequisite)
- cis_read_file: reviews/done/tg2-two-way-report.advisor.response.md (80 lines, concerns A-H)
- cis_read_file: reviews/done/tg2-two-way-report.evaluator.response.md (22 lines, FRAME: RIGHT_WORK)
- cis_read_file: enforcement/mwl-proof-v2/run_container.sh (192 lines, sources secrets.env, docker rm -f)
- cis_read_file: enforcement/mwl-proof-v2/entrypoint.sh (226 lines, 8 gateways + Flask API, wait $PIPELINE_PID)
- cis_read_file: tools/advisor_review.sh (1087 lines, host-resident, docker exec, pause_state release)
- cis_read_file: tools/run_claude_sandbox.sh (64 lines, kernel RO mount, proven mechanism)
- cis_read_file: runtime/abstraction/pipeline_relay.py (4018 lines, state machine, ERIC_GATE state exists but no Menter dispatch path)
- cis_git_show: commit 60703c8 (sandbox Claude Code launcher + s14 evidence + 4 pending review cards)
- cis_search_knowledge: "container working state blocks" (advisor deliberation: FRAME: RIGHT_WORK from evaluator, FRAME: WRONG_WORK from advisor -- the WRONG_WORK was from round 1 advisor, the evaluator overruled with RIGHT_WORK)
