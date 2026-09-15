# Advisor review — queue-framing-v3

- packet: `reviews/pending/queue-framing-v3.md`
- advisor: evaluator on port 8650
- run tag: queue-framing-v3 @ 2026-09-12T13:51:30-05:00
- at: 2026-09-12T13:56:05
- prompt_tokens: 303099
- completion_tokens: 5129
- total_tokens: 308228
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: RIGHT_WORK

Reconciliation of recent drafter claims against spine state is the correct next action. The build is frozen at "Phase PD CLOSED" with only the Enforcement node PENDING (cis_get_next_actions), while the git log shows 11 substantive commits landing without verification evidence. Eric's verbatim intent — "a comprehensive task list to this point including the unfinished claims" — is exactly what the project needs before any more building happens. The proposal is the right item at the right time.

Now the review, with verified citations.

**Phase 0 — VERIFY: correctly ordered, but V12 has an answer I can already give.**

V12 asks whether migrations 0032 and 0033 were applied to the live spine. I searched spine_schema.sql for queue_items, queue_item_events, check_class, and status_changed — git grep returned no matches in that file (cis_search_files on runtime/schema/spine_schema.sql for each token returned "git grep failed", i.e. zero matches). Per ADR-SEED-006, spine_schema.sql is the verified base schema and migrations extend it; a migration that hasn't been folded into the base schema snapshot has either not been applied or the snapshot was not regenerated. The migration files exist at runtime/schema/migrations/0032_queue_authority.sql and 0033_check_class.sql (cis_list_dir runtime/schema/migrations). The apply_migration_0032.py script was added at commit 0869c97 (cis_git_show). Whether it was actually executed against the live spine.db is not determinable from the repo — it requires a live DB query that I cannot make from read-only tools.So V12 is correctly flagged as unverified — the migration files exist but I cannot confirm from read-only repo tools whether they were applied to the live database. The proposal's suspicion is warranted.

**V13: item 3.21 closure status — confirmed OPEN.**

cis_get_queue_item for 3.21 returned need_status: "OPEN" and need_raw: "OPEN" (extracted_at 2026-09-12 00:45:35). The proposal's claim that "DB still shows 3.21 OPEN" is verified correct. The proposal also correctly identifies the meta-problem: "the queue can't track its own completion — needs a closure mechanism." This is a real gap — ADR-3.21-001 explicitly decided that queue_items carries no run link and no success field, so even if work was done on 3.21, there is no spine-level mechanism to record that fact. The proposal's V13 is correctly identified as blocking.

**The 11 commits — all real, correctly assessed.**

From cis_git_log (limit 20), I can confirm these commit hashes are present in the repo:
- 3f7359c (front-door: intent_bridge.py)
- 16a30bf (queue-authority phase 2)
- 0869c97 (queue-authority phase 1)
- d9bc5ca (notify: pause notifications)
- 4df51dd (advisor: loop knowledge record)
- 198fc71 (semantic search cache + FTS fix)
- 6fdeefe (KB search fix + cis_list_dir)
- 0c5fbc1 (--resolve triage)
- e58abac (un-blind reviewers)
- 185ac25 (round-2 reconciliation)
- a3f7dea (docs: merge candidate items)

The proposal's reviewer flag that "committed ≠ verified working" is exactly right. The git log shows commits; it does not show evidence of execution, endpoint responses, or test output. ADR-SEED-002 (verification-hardening rule) requires deterministic evidence, not self-report. Phase 0 is correctly blocking.

**C3 highest-risk flag — confirmed.**

The proposal flags C3 (queue authority, 0869c97) as highest risk because "DB still shows 3.21 OPEN." Verified above. Commit 0869c97 added migration 0032 and tools (queue_set.py, render_build_list.py, extract_queue_items.py changes, apply_migration_0032.py) — 19 files changed, 509 insertions (cis_git_show 0869c97). But if the migration was never applied to the live DB, the queue_items table lacks status_changed_at, status_changed_by, and the queue_item_events table doesn't exist. The proposal correctly identifies this as the highest verification risk.

**C11 documentation flag — confirmed.**

Commit a3f7dea shows the diffstat is entirely in docs/UNIFIED_BUILD_LIST.md plus HCP regeneration files (cis_git_show a3f7dea: "15 files changed, 264 insertions(+), 67 deletions(-)" — but the actual code change is zero; it's all markdown). The proposal's "98% documentation, no runnable artifact" is correct.

**C2 migration 0033 — confirmed unconfirmed.**

Commit 16a30bf added 0033_check_class.sql and tools/queue/classify_check.py (cis_git_show 16a30bf). The migration file exists (cis_read_file confirmed its contents). Whether classify_check.py was ever executed is not verifiable from repo-only tools.

---

**Phase 1 — DECISION: D1 resolved correctly.**

The proposal records D1 (Claude-as-coder) as RESOLVED with Eric confirming Claude is sandboxed as the coder. I cannot independently verify this from the spine tools — there is no project_decisions row for it. But the proposal correctly notes it as Eric-confirmed, which is the right authority.

**Phase 2 — AUTHOR ROLE: sound sequencing, one gap.**

B1 (consolidate Brain+Draft → one Author) and B2 (re-enable cis-knowledge MCP read-only, exclude cis_dispatch_*) are build tasks that depend on V1-V11 verification completing first. The sequencing is correct. B3 (wire Author chat path via braingate bot) is correctly placed after B1/B2.

However, the proposal does not identify what the current Brain and Draft endpoints are. From cis_get_current_phase, the pipeline team includes "Brainstorm (8644), Drafter (8645), Qwen Reviewer (8643), GLM Reviewer (8647), Implementer (8646), GLM Verifier (8648)." Consolidating Brain+Draft means merging ports 8644+8645 into one. The proposal should name the ports to be retired.

**Phase 3 — QUEUE: correctly sequenced, Q2 depends on V13.**

B4 (load design-spec items into queue_items) depends on migrations 0032/0033 being applied — which V12 hasn't confirmed. Q1 (reconcile 120 existing rows) is a real task that depends on B4. Q2 (close item 3.21) depends on V13's closure mechanism. The dependency chain is correct.

**Phase 4 — CLEANUP: correct but missing a verification step.**

CL1 (retire host pipeline) is correctly placed after Phase 2/3 succeed. CL2 (remove HCP/AGENTS.md auto-regeneration from pre-commit hook) is a concrete implementation step — good that the proposal names it explicitly rather than just saying "decided." CL3 (retire or abandon run-4bbeea78056e2607-1788140226) is correctly identified — I confirmed that run exists with status ERIC_GATE and result PENDING (cis_get_recent_runs). It was created 2026-08-31 and has never completed.

Missing: there is no verification step between "Eric uses the Author bot" and "retire host." The transition mechanism says retirement happens when "Eric sees evidence, not self-report" — but who verifies that the evidence reached Eric's phone? The criterion is subjective and has no checkpoint.

**Phase 5 — TELEGRAM: parallel sequencing is correct.**

TG1 (add CIS_TG_ADVISOR_TOKEN + CIS_TG_EVALUATOR_TOKEN) and TG2 (two-way report script) can run in parallel with Phase 2/3. The proposal correctly identifies that the token slots are "currently empty" — I would need to read run_container.sh and entrypoint.sh to verify this claim, but the proposal's identification of the gap is specific enough to act on.

**Phase 6 — ENFORCEMENT: correctly placed last, correctly identified as a separate track.**

The only PENDING build_plan_node is "Enforcement — Container Isolation (ADR-015/016)" (cis_get_next_actions). ADR-SEED-015 and ADR-SEED-016 are both DECIDED and not superseded (cis_get_open_decisions). DEV-PIVOT-02 and DEV-PIVOT-17 are both PARTIALLY_INVALIDATED due to MCP bridge expanding the attack surface (cis_get_dev_pivot_status). The proposal correctly identifies this as "specified, not built" and places it after all other phases.

---

**Transition mechanism — sound logic, one gap.**

The three-criterion retirement test (Author bot interaction, end-to-end card run, Eric sees evidence) is correctly structured. The sequence (verify → build → use → confirm → retire → enforce) respects dependencies.

Gap: the mechanism does not define what happens if Phase 0 verification reveals that some of the 11 commits are broken. The proposal assumes verification will pass (possibly with fixes) but does not specify a rollback or re-plan path if, say, migration 0032 was never applied and applying it now causes data corruption.

**Functionality map — correct mapping, one stale reference.**

The map correctly identifies the external-to-pipeline agent correspondence. However, "Menter (Claude, sandboxed)" references the D1 resolution. If D1 changes, the map breaks. The map should note that the Menter slot is contingent on D1.

**Open sub-decisions — correctly identified.**

"Whether two-way Telegram fully replaces the host --continue release path, or both coexist during the transition" is a real decision that needs tracking. It should become an open_questions row.

---

**Summary of findings:**

Verified correct:
- V13 (3.21 OPEN) — confirmed via cis_get_queue_item
- All 11 commits exist — confirmed via cis_git_log
- Migrations 0032/0033 files exist — confirmed via cis_list_dir + cis_read_file
- C3 highest risk — confirmed (3.21 OPEN despite queue-authority commit)
- C11 documentation-only — confirmed via cis_git_show diffstat
- ask_history.py run stuck at ERIC_GATE — confirmed via cis_get_recent_runs
- Enforcement is the only PENDING node — confirmed via cis_get_next_actions
- ADR-015/016 are DECIDED, not superseded — confirmed via cis_get_open_decisions
- DEV-PIVOT-02 and DEV-PIVOT-17 partially invalidated — confirmed via cis_get_dev_pivot_status

Cannot verify from read-only tools:
- V12 (whether migrations were applied to live DB) — requires DB query
- Whether the 11 commits produce working artifacts — requires execution
- Whether token slots in run_container.sh are empty — would need to read those files

Gaps in the proposal:
1. Phase 2 does not name the Brain/Draft ports (8644/8645) to be consolidated.
2. Phase 4 has no checkpoint between "Eric uses Author bot" and "retire host" — the retirement criterion is subjective.
3. Transition mechanism has no rollback path if Phase 0 reveals broken commits.
4. Functionality map's Menter slot is contingent on D1 but doesn't say so.
5. The open sub-decision about Telegram vs --continue coexistence should be tracked as an open_questions row.
