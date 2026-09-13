# Advisor review — sandbox-claude-code

- packet: `reviews/pending/sandbox-claude-code.md`
- advisor: evaluator on port 8650
- run tag: sandbox-claude-code @ 2026-09-12T20:09:08-05:00
- at: 2026-09-12T20:12:02
- prompt_tokens: 122470
- completion_tokens: 1994
- total_tokens: 124464
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: WRONG_WORK

Eric has explicitly directed work on queue item 3.31 (TG2 two-way report for container transition), not enforcement. The `cis_get_current_phase` query shows current priority is container transition work, while "Enforcement — Container Isolation (ADR-015/016)" sits PENDING in the build plan. More critically, ADR-SEED-016 states "No implementation until §14 raw-evidence plan executed" — this is an explicit architectural gate, not a suggestion. HCP_01 marks §14 execution as 🚫 BLOCKED. The proposal tries to rationalize working around this gate by claiming "executing it is the first sub-step of this card," but that contradicts the decision's intent: §14 evidence must be captured and Eric-approved BEFORE implementation begins.

**Verified claims:**

- ADR-SEED-015 and ADR-SEED-016 are DECIDED and LIVE (cis_get_open_decisions)
- TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md exists at docs/ (42,446 bytes, cis_list_dir). The approval claim is TRUE.

- ADR-SEED-016's "No implementation until §14 raw-evidence plan executed" gate is UNMET. HCP_05 shows "Execute §14 raw-evidence capture plan" as BLOCKED (cis_search_files, HCP_05_NEXT_ACTIONS.md line 74). The proposal's O2 acknowledges this gate exists but dismisses it with "executing it is the first sub-step" — this contradicts the ADR's sequencing requirement.

- The "Claude Code runs inside cis-pipeline container with rw mount" claim: I cannot verify this without docker inspect access, but the proposal's D1 reference to "queue-framing-v3" is not a file I can locate.

- CARD-claude-code-submit-loop: I cannot find this as a queue item (cis_get_queue_item returned error). The proposal cites it as deferring this work, but the reference is unverifiable from available artifacts.

- "reviewer-isolation card": cis_search_files returned "git grep failed" — I cannot verify this card exists or what it established.

**Critical timing problem:**

cis_get_current_phase shows Eric's 2026-09-12 direction: "Container transition (Eric directed 2026-09-12): TG2 two-way report (queue 3.31) is current. Then Author consolidation, 3.29 result-size caps, 3.30 spine persistence."

The enforcement node exists as PENDING but is NOT the current priority. Eric has directed work on container transition (3.31), not enforcement implementation. The proposal frames this as "prerequisite to CARD-claude-code-submit-loop" but that card does not exist in the queue system I can query.

**The §14 gate is load-bearing:**

ADR-SEED-016 explicitly gates implementation on §14 evidence capture. The proposal tries to collapse this gate into "first sub-step of this card," but that's a sequencing violation. The ADR requires evidence captured AND Eric-approved BEFORE implementation begins — not captured-during-implementation.

**What's actually needed:**

If the implementer wants to do this work, the correct sequence is:
1. Execute §14 raw-evidence capture (currently BLOCKED per HCP_05)
2. Get Eric approval on §14 evidence
3. THEN implement the enforcement primitive

The proposal skips step 1-2 and tries to fold them into step 3.

**Summary:**

The enforcement primitive is approved architecture (TRUE), the build plan node is PENDING (TRUE), and the design in TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md is sound. But this is the wrong work at the wrong time because:

1. Eric has directed container transition work (3.31), not enforcement
2. The §14 evidence gate is unmet and cannot be collapsed into "first sub-step"
3. The proposal references cards (claude-code-submit-loop, reviewer-isolation) I cannot verify exist
4. The HCP status shows §14 execution is BLOCKED, not PENDING

The proposal is architecturally correct but temporally wrong. Do the §14 evidence capture first, get Eric's approval, then this card becomes the right work.
