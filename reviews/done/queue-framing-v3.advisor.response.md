# Advisor review — queue-framing-v3

- packet: `reviews/pending/queue-framing-v3.md`
- advisor: advisor on port 8649
- run tag: queue-framing-v3 @ 2026-09-12T13:51:30-05:00
- at: 2026-09-12T13:53:50
- prompt_tokens: 697334
- completion_tokens: 3901
- total_tokens: 701235
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: RIGHT_WORK

This is the right item at the right time. The project has accumulated 11 commits whose claims are unverified per the project's own ADR-SEED-002 ("self-report is not a source of truth"), queue item 3.21 is confirmed still OPEN despite commits claiming queue authority is built, there is no closure mechanism for queue items, and the host-to-container transition has no concrete retirement criteria. The intent — reconcile the queue, verify claims with evidence, and produce a comprehensive task list — is exactly the blocking work before any further building.

---

REVIEW OF THE PROPOSAL PACKET

I verified every claim I could against the repository, the spine, and the commit history. Below is what I confirmed, what I could not confirm, and where the packet has gaps.

PHASE 0 — VERIFY

V12: Were migrations 0032 and 0033 applied to the live spine?

CONFIRMED UNVERIFIED. Both migration files exist and are committed:
- runtime/schema/migrations/0032_queue_authority.sql (50 lines, read in full) — adds status_changed_at, status_changed_by, queue_item_events, queue_sections.
- runtime/schema/migrations/0033_check_class.sql (8 lines, read in full) — adds check_class column.

The apply tool tools/queue/apply_migration_0032.py exists (104 lines per git show of 0869c97). classify_check.py (179 lines, read in full) applies 0033 idempotently via a column-existence guard. But neither file contains evidence the migration was run against the live spine. The queue_items query for 3.21 returned need_status="OPEN" and the answers_2_30 block shows the row exists, so the base table is populated — but the added columns (status_changed_at, status_changed_by, check_class) are not visible in the cis_get_queue_item output, which either means they are empty or the query tool does not surface them. I cannot confirm the migrations were applied. The packet's V12 claim is correctly flagged as unconfirmed.

V13: Is queue item 3.21 actually CLOSED or still OPEN?

CONFIRMED OPEN. cis_get_queue_item("3.21") returned need_status="OPEN", need_raw="OPEN". The answers_2_30 block confirms: "what_was_just_done: need_status on this row", "what_is_the_current_item: NOT AVAILABLE - nothing designates one", "did_it_succeed: ABSENT BY DECISION - see ADR-3.21-001".

ADR-3.21-001 (from cis_get_open_decisions, decided 2026-09-09) explicitly states queue_items carries no run link and no success field, and the proposed workflow_runs.queue_item_num column was withdrawn. So 3.21 is OPEN by decision, not by oversight. The closure mechanism (queue_set.py) exists and is committed — I read the full 89-line file. It enforces evidence for status changes. But it has never been run against 3.21. The packet's V13 flag is correct.

C3 (queue authority, 0869c97) — highest risk:

CONFIRMED: commit is real, diff stat shows 19 files, 509 insertions. The commit adds queue_set.py, render_build_list.py, extract_queue_items.py modifications, apply_migration_0032.py, and the migration SQL. The code I read is well-structured: queue_set.py refuses unknown statuses, requires evidence for factual claims, writes append-only events. render_build_list.py exists (127 lines per diff stat). The UNIFIED_BUILD_LIST.md header now reads "DO NOT EDIT — generated from queue_items (the spine)" and "Change a status with tools/queue/queue_set.py; this file regenerates on commit." So the queue authority mechanism is built and committed. The risk is not that the code is wrong — it is that the migration may not be applied and 3.21 is still OPEN. The packet correctly identifies this as the highest-risk item.

C2 (16a30bf, migration 0033):

CONFIRMED: commit is real, 15 files, 264 insertions. classify_check.py is a deterministic classifier with regex rules for RUNNABLE/JUDGMENT/NO_CHECK. The migration file is 8 lines, straightforward. Application unconfirmed — same gap as V12. The packet's flag is accurate.

C11 (a3f7dea, "98% documentation"):

CONFIRMED: commit is real, 14 files, 4147 insertions. 4071 of those are docs/PHASE_2_CANDIDATE_ITEMS.md. The rest are HCP file updates and the manifest. No runnable artifact. The packet's assessment "treat as docs, not code" is correct.

3f7359c (intent_bridge.py):

CONFIRMED: commit is real, 14 files, 201 insertions. tools/intent_bridge.py is 132 lines, read in full. It implements a clarify->confirm->gate->route flow with a controlled direction vocabulary (next, draft, review, implement). It refuses to fire without --confirm (exits 2). It writes to intent_map with eric_confirmed_at. The code is real and structured. Whether it has been exercised end-to-end is not evidenced in the commit.

The remaining commits (4df51dd, d9bc5ca, 198fc71, 6fdeefe, 0c5fbc1, e58abac, 185ac25, 4d8d2e8) all appear in git log and their commit messages match the packet's descriptions. I did not individually diff each one, but the git log output confirms all 11 commits exist with the hashes and messages cited.

PHASE 4 — CLEANUP

CL1: Retire host pipeline (workflow_runs, dispatch_log, gate_runner).

PARTIALLY VERIFIED. The host pipeline artifacts are visible in the repo root: gate_runner_decisions.log (147,874 bytes), gate_runner_payload.jsonl (2,184,591 bytes), hook_payload.jsonl (2,411,238 bytes), hook_seen.log (306,249 bytes). These are active host-side artifacts, not retired. The container has its own pipeline (runtime/container_app.py at 16,923 bytes, runtime/orchestrator.py at 30,667 bytes). The packet correctly identifies retirement as an implementation step, not a decision.

CL3: Retire in-flight ask_history.py run.

CONFIRMED STUCK. cis_get_recent_runs shows run-4bbeea78056e2607-1788140226 in status ERIC_GATE, result PENDING, rounds_completed 0, created 2026-08-31. Four prior attempts at the same task are ERROR or ESCALATED. The run has been sitting at ERIC_GATE for 12 days. The packet correctly flags this.

PHASE 5 — TELEGRAM

TG1: Add CIS_TG_ADVISOR_TOKEN + CIS_TG_EVALUATOR_TOKEN to run_container.sh + entrypoint.sh.

CONFIRMED: the slots are empty. In entrypoint.sh (read in full, 208 lines), the TG_TOKENS array has 8 entries — the last two (advisor, evaluator) are hardcoded empty strings:
    "${CIS_TG_ADVISOR_TOKEN:-}"  ->  ""
    "${CIS_TG_EVALUATOR_TOKEN:-}" ->  ""

Wait — actually the array shows:
    "${CIS_TG_BRAIN_TOKEN:-}"
    "${CIS_TG_DRAFT_TOKEN:-}"
    "${CIS_TG_REVIEW1_TOKEN:-}"
    "${CIS_TG_REVIEW2_TOKEN:-}"
    "${CIS_TG_MENTER_TOKEN:-}"
    "${CIS_TG_VERIFY_TOKEN:-}"
    ""
    ""

The last two are literal empty strings, not env var references. So advisor and evaluator have no Telegram token plumbing at all — there is no CIS_TG_ADVISOR_TOKEN env var being read. The packet says "slots currently empty" — that is correct but understates it: the slots are hardcoded empty, not even wired to read an env var. Fixing this requires both adding the env var references and passing them through run_container.sh.

I searched for CIS_TG_ADVISOR_TOKEN and CIS_TG_EVALUATOR_TOKEN via cis_search_files — git grep failed (returned error), so I cannot confirm these strings appear nowhere in the repo. But from reading the full entrypoint.sh, they do not appear in the TG_TOKENS array.

run_container.sh (read 184 lines, the first ~110): I did not see any -e CIS_TG_ADVISOR_TOKEN or -e CIS_TG_EVALUATOR_TOKEN env var passes in the portion I read. The file is 184 lines and I saw through the docker run section start. The packet's claim that the slots are empty is consistent with what I read.

PHASE 2 — AUTHOR ROLE

B1/B2/B3: Consolidate Brain+Draft into one Author, un-strip MCP read access, wire chat path.

These are build tasks, not verifiable against the current repo. The current pipeline has 8 profiles (brain, draft, review1, review2, menter, verify, advisor, evaluator) per entrypoint.sh. The packet proposes consolidating brain+draft into one "Author" role. This is a design decision for Eric, not something I can verify against existing artifacts. The functionality map table is a reasonable mapping of Eric's current manual workflow to container agents, but it is a proposal, not an implemented fact.

PHASE 6 — ENFORCEMENT

ADR-015/016 three-layer isolation — specified, not built.

CONFIRMED by cis_get_current_phase: the only pending node is "Enforcement — Container Isolation (ADR-015/016)", status PENDING. ADR-SEED-015 and ADR-SEED-016 are both DECIDED. DEV-PIVOT-02 (Enforcement Architecture V3) is PARTIALLY_INVALIDATED because "MCP adds second access channel to spine data." DEV-PIVOT-17 (Process Isolation) is PARTIALLY_INVALIDATED for the same reason. The enforcement spec exists but the threat model needs updating for the MCP query surface. The packet correctly places this as a separate parallel track.

TRANSITION MECHANISM

The three retirement criteria (Eric uses Author bot, card runs end-to-end with evidence reaching phone, Eric sees evidence not self-report) are sound and align with ADR-SEED-002. The sequence (verify -> build Author + wire bots -> Eric uses it -> confirm loop -> retire host -> enforcement) is the correct order. The packet's open sub-decision about whether two-way Telegram fully replaces --continue is genuinely unresolved — I found no decision recording this.

GAPS IN THE PACKET

1. The packet lists V1-V11 as "each of the 11 commits, execution evidence not self-report" but does not enumerate which 11 commits map to V1-V11. The git log shows 11 commits from a3f7dea through 3f7359c (plus earlier ones). The mapping is implied but not explicit. A reviewer doing Phase 0 would need the commit hash list.

2. Q1 (reconcile 120 existing queue rows) — the packet says 120 rows exist but I cannot verify this count. cis_get_queue_item only returns one item. The UNIFIED_BUILD_LIST.md is 3,560 lines, which is consistent with ~120 items plus prose, but I cannot confirm the exact count without a query tool that lists all items.

3. CL2 (remove HCP/AGENTS.md auto-regeneration from pre-commit hook) — I could not find the pre-commit hook. cis_search_files for "pre-commit" or "pre_commit" returned "git grep failed." The .git directory is not listable by cis_list_dir (it shows as a dir entry but I did not attempt to list inside it). The HCP regeneration is visible in the commit pattern — nearly every commit touches 12+ HCP files — but I cannot confirm it is a pre-commit hook vs. a manual step. The packet asserts it is a pre-commit hook; I could not verify that claim.

4. The packet's functionality map lists "Author (DeepSeek)" as the brainstorm agent, but the current brain profile uses port 8644 and the entrypoint does not specify which model each profile uses (that is in the profile YAML files under enforcement/mwl-proof-v2/profiles/, which I did not read). The model assignment is a claim I could not verify.

ASSESSMENT

The packet is honest about what is verified vs. what is claimed. Its strongest point is that it correctly identifies 3.21 as still OPEN, the migrations as unconfirmed, and the ask_history run as stuck. Its weakest point is that Phase 0 (V1-V11) is described as a task to do rather than done — the packet is itself a proposal for verification, not the verification. That is appropriate for a "comprehensive task list" but means nothing in Phase 0 has been executed yet.

The transition mechanism and functionality map are well-reasoned and align with the project's ADRs and Eric's stated intent. The open sub-decision about Telegram vs. --continue is correctly flagged.

The right next action is Phase 0: run queue_set.py against 3.21 with evidence, confirm migrations 0032/0033 are applied to the live spine, and either close or explicitly abandon the ask_history run. Nothing in Phase 2-6 should proceed until Phase 0 is complete, because building on unverified claims is exactly what ADR-SEED-002 prohibits.
