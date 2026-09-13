# Advisor review — sandbox-claude-code

- packet: `reviews/pending/sandbox-claude-code.md`
- advisor: advisor on port 8649
- run tag: sandbox-claude-code @ 2026-09-12T20:09:08-05:00
- at: 2026-09-12T20:10:48
- prompt_tokens: 429073
- completion_tokens: 3420
- total_tokens: 432493
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: WRONG_WORK

The proposal is architecturally sound and correctly cites real, verified ADRs (ADR-SEED-015, ADR-SEED-016 both DECIDED in the spine, confirmed via cis_get_open_decisions). The spec file exists at docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md (703 lines, verified via cis_read_file). The build_plan_node "Enforcement — Container Isolation (ADR-015/016)" is PENDING with no blocked_reason (verified via cis_get_build_status). But the timing is wrong. The current phase (cis_get_current_phase) says Eric directed on 2026-09-12 that queue item 3.31 (TG2 two-way report) is current, followed by Author consolidation, 3.29, 3.30. The enforcement node is PENDING but is not the directed next action — it has been pending since 2026-07-01 and was not picked up. More critically, ADR-SEED-016 explicitly gates implementation: "No implementation until §14 raw-evidence plan executed." The HCP_01_CURRENT_STATE.md (verified via cis_search_files) shows §14 raw-evidence capture is still marked BLOCKED at line 319/378. The proposal itself acknowledges this in O2 and says "if it is still an unmet gate, executing it is the first sub-step." But the proposal's DONE-WHEN lists full implementation — RO mount, policy hook, .GATE_DISABLED — which goes well beyond "execute the §14 evidence plan." The proposal silently collapses two distinct work items (evidence capture vs. implementation) into one card, and the §14 gate has not been cleared. The right work at the right time is: execute §14 raw-evidence capture first as a standalone step, then implement. This card jumps ahead.

---

REVIEW

1. Claims verified against sources

- ADR-SEED-015 (three-layer process isolation): DECIDED, 2026-06-19. Text matches the proposal's description. Source: cis_get_open_decisions.
- ADR-SEED-016 (enforcement primitive approved, no implementation until §14): DECIDED, 2026-06-19. Text says "No implementation until §14 raw-evidence plan executed." Source: cis_get_open_decisions.
- docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md: exists, 703 lines. Verified via cis_read_file. Contains all 15 sections referenced in the proposal packet (§2 trust root, §3 three-layer architecture, §5 policy hook, §7 override plane, §14 evidence gate). The spec is a PROPOSAL ONLY document — its header says "Status: PROPOSAL ONLY" and "Constraint: No implementation."
- §14 raw-evidence capture status: BLOCKED. Source: cis_search_files on TASK_CONTRACT_ENFORCEMENT, HCP_01_CURRENT_STATE.md line 319: "Execute §14 raw-evidence capture plan... BLOCKED". HCP_05_NEXT_ACTIONS.md line 74: same item, BLOCKED.
- Build plan node "Enforcement — Container Isolation (ADR-015/016)": PENDING, tier ENFORCEMENT, no blocked_reason, no evidence_path, no commit_hash. Created 2026-07-01. Source: cis_get_build_status.
- Current directed work: cis_get_current_phase returns next_action = "Container transition (Eric directed 2026-09-12): TG2 two-way report (queue 3.31) is current. Then Author consolidation, 3.29 result-size caps, 3.30 spine persistence." Queue item 3.31 (cis_get_queue_item) confirms need_status=OPEN, need_raw=OPEN.
- CARD-claude-code-submit-loop: I could not find this file in the repo. cis_search_files for "claude-code-submit-loop" returned git grep failed (no matches). The cards/inbox and cards/approved directories (cis_list_dir) do not contain a file by that name. The proposal claims this card exists and excludes sandbox work in its "NOT IN THIS CARD" section. I cannot verify that claim — the card may exist outside the repo, in a different branch, or may not exist. This is a gap, not a contradiction.
- reviewer-isolation card: Similarly not found via cis_search_files. The cards/inbox directory contains CARD-reviewer-measurement.md and CARD-reviewer-readonly-and-reconciliation.md, which may be the referenced cards, but neither filename matches "reviewer-isolation" exactly. The proposal's reference to a "reviewer-isolation card" that "established the OS-level-over-prompt-level philosophy" is plausibly CARD-reviewer-readonly-and-reconciliation.md, but I did not read it to confirm.
- "D1 in queue-framing-v3": The proposal claims Claude Code as coder is "Eric-confirmed, recorded as D1 in queue-framing-v3." cis_search_files found queue-framing-v3 referenced in docs/UNIFIED_BUILD_LIST.md line 3221, but only as a cost observation about advisor review token usage, not as a decision record. I could not verify the "D1" designation. This claim is unverified.
- Docker mount claim: The proposal says the cis-pipeline container mounts the repo read-write and cites `docker inspect`. I cannot run docker inspect (read-only tools only, and this is a review). The spec file itself (§3) says "Verified 2026-06-19: container with /mnt/projects/cis mounted read-only refused write to breach.txt" — this is a past verification of RO behavior, which contradicts the proposal's claim that the repo is currently mounted read-write. One of these is stale. The proposal needs to resolve this discrepancy at implement time (and O1 acknowledges this).

2. Structural issues

- The proposal conflates two distinct gated items. ADR-SEED-016 says no implementation until §14 evidence is captured. The §14 evidence capture is separately tracked and still BLOCKED (HCP_01, HCP_05). This card's DONE-WHEN includes full implementation (RO mount, policy hook, .GATE_DISABLED override, denied-write test). The §14 evidence capture is a precondition, not a sub-step of implementation. Folding it in risks the implementer treating the gate as satisfied by doing implementation work, rather than doing the evidence capture first and independently.
- The proposal says "if it is still an unmet gate, executing it is the first sub-step of this card, not a reason to defer." This is the right instinct but the wrong structure. If §14 is unmet, the first sub-step produces evidence that must be reviewed and approved before implementation proceeds. That is a gate pass, not a sub-step. The card should either (a) be scoped to §14 evidence capture only, with implementation as a follow-on card, or (b) explicitly split into two phases with a review gate between them.
- The spec file's own header says "PROPOSAL ONLY" and "No implementation." The card proposes implementation. The card's D2 says "If implement-time findings conflict with the ADR, the live ADR text wins." But the spec file's status line is not the ADR — ADR-SEED-016 is the ADR, and it says "No implementation until §14." The card should cite the ADR gate, not the spec file's header.

3. What is missing

- CARD-claude-code-submit-loop: Not found in the repo. If this card exists and establishes a dependency chain (sandbox is prerequisite to submit-loop), the proposal's framing depends on it. I need to see this card to verify the prerequisite claim. It may be in a location I cannot access, or it may not exist yet.
- Evidence that §14 has been executed or its status resolved. The HCP files say BLOCKED. The spine (cis_get_open_decisions) carries the gate text. There is no session_closeout or workflow_run showing §14 was executed. I searched for TASK_CONTRACT_ENFORCEMENT and found extensive session history showing multiple attempts to run the §7 override-plane test (NA-SEED-014, NA-SEED-016) but no evidence that §14 evidence capture was completed and approved.
- The "D1 in queue-framing-v3" designation is unverified. The proposal builds on Claude Code being the Eric-confirmed coder. If this designation is not actually recorded where the proposal says it is, the problem statement's premise weakens.
- The reviewer-isolation card is referenced but not verified. The proposal says it "established the OS-level-over-prompt-level philosophy for the reviewers." I found CARD-reviewer-readonly-and-reconciliation.md in cards/inbox but did not read it. If the proposal depends on that card's philosophy as precedent, it should cite the file path.

4. Summary assessment

The work itself — building OS-level write isolation for the coder — is the right eventual work for this project. It implements an approved ADR (ADR-SEED-015) and addresses a real enforcement gap (reviewer holds are advisory without a write boundary). But it is not the right work at the right time for three reasons:

(a) Eric's directed current work is 3.31 and the control-plane observation pipeline, not enforcement. The enforcement node has been pending since July 1 with no directive to pick it up.

(b) The §14 raw-evidence gate is still BLOCKED. The proposal acknowledges this but structurally folds evidence capture into implementation, which undermines the gate's purpose. The gate exists to prove the override plane works before trusting the hook — that proof must be complete and reviewed before implementation begins.

(c) Two referenced predecessor artifacts (CARD-claude-code-submit-loop, the "D1 in queue-framing-v3" designation) could not be verified in the repo. If either is missing or misrepresented, the prerequisite chain the proposal builds on may not hold.

Recommendation: Split this into two cards. Card 1: execute §14 raw-evidence capture (override-plane test, evidence artifacts, review). Card 2: implement the sandbox (RO mount, policy hook, .GATE_DISABLED) — gated on Card 1's completion and Eric approval. Do not start Card 2 until Card 1 is done. And confirm with Eric that enforcement is the directed next work after the current 3.31/3.29/3.30 sequence, or whether it should wait.
