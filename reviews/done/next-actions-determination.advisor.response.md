# Advisor review — next-actions-determination

- packet: `reviews/pending/next-actions-determination.md`
- advisor: advisor on port 8649
- run tag: next-actions-determination @ 2026-09-13T05:55:40-05:00
- at: 2026-09-13T06:01:14
- prompt_tokens: 439357
- completion_tokens: 3650
- total_tokens: 443007
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: RIGHT_WORK

Eric's intent is to give reviewers read-only measurement instruments and have them determine next steps — what to do, in what order, how to split deterministic vs judgment work. That is seed intent 3 ("checks and balances — dual-lineage reviewers determine next actions, not the Drafter") made operational. The packet asks the right three questions (ORDER, TOOL SPLIT, SCOPE) at the right time (reviewers just got access, a body of unverified work has accumulated, and the queue has 44 OPEN items with no prioritization). I verified the access claim is real — I am exercising the 21 read-only tools right now.

---

REVIEW

I verified every factual claim in the packet before answering. Here is what I found, cited, and what it means for each question.

VERIFIED CLAIMS

V12 (migrations applied): CONFIRMED. `PRAGMA table_info(queue_items)` shows columns `status_changed_at` (cid 11), `status_changed_by` (cid 12), `check_class` (cid 13). Tables `queue_item_events` and `queue_sections` both exist (cis_query against sqlite_master).

V13 (3.21 still OPEN): CONFIRMED. `need_status='OPEN'`, `need_raw='OPEN'`, `status_changed_at=NULL`, `status_changed_by=NULL`, `check_class='RUNNABLE'` (cis_query). The closure mechanism (`tools/queue/queue_set.py`, 89 lines, read in full) exists and is properly structured — it requires evidence for status changes, writes append-only event rows — but was never run against 3.21.

Queue count: CONFIRMED. `SELECT count(*) FROM queue_items` = 123. Breakdown matches exactly: 56 NULL, 44 OPEN, 11 UNASSESSED, 8 DONE, 4 HALF_DONE.

ask_history.py stuck runs (CL3): CONFIRMED. AGENTS.md lines 82-86 show 5 PENDING runs (run-4bbeea78056e2607, 5 attempts), all "0 rounds, incomplete", all attempting the same task: "Modify tools/ask_history.py so it merges keyword (FTS5) results."

Reviewer access: CONFIRMED by exercise. I used cis_query (read-only SQL, row-capped), cis_read_file, cis_search_files, cis_git_log, cis_git_show, cis_list_dir, cis_search_semantic, and the cis_get_* spine queries. All functional.

D1 (sandbox "PROVEN"): FALSE. This is the one claim in the packet that does not survive verification. The §14 evidence file exists (`enforcement/mwl-proof-v2/RESULTS/s14_evidence_20260912.md`, 88 lines, read in full). It contains 5 ad-hoc items of prose self-report, not the required 9-step test with raw terminal output. Reviewer 2 (GLM, `reviews/done/s14-evidence-capture.review2.impl.response.md`, 29 lines, read in full) returned OBJECTIONS with 7 specific failures: the disposable test root was never created on disk, the 9-step test script (`tools/override_plane_test.sh`) was never executed (no `raw_evidence.log`), evidence is prose self-report which ADR-SEED-002 disqualifies, conditions (d) and (f) were never tested, the Docker wall test used the wrong path, no PASS/FAIL/BLOCKED result format, and the operator/worker boundary was not demonstrated under real privileges (current user is `worker` not `eric`). Reviewer 1 (Qwen, `reviews/done/s14-evidence-capture.review1.impl.response.md`) timed out. So D1 is not PROVEN — it is REJECTED by the reviewer who could complete, and UNVERIFIED by the one who timed out.

The sandbox card (`reviews/pending/sandbox-claude-code.md`, 95 lines, read in full) remains pending and its DONE-WHEN criteria are unmet: no kernel-level RO mount demonstrated, no policy hook, no override plane tested. The §14 evidence file itself acknowledges "AWAITING ERIC APPROVAL" status and defers items 3-6.

Verification scope 11 -> 15 commits: PLAUSIBLE but UNVERIFIED. The git log shows 30 commits. The most recent 5 (60703c8 through 3f7359c) are the sandbox/wiring/front-door work. I cannot independently confirm the "V1-V15" enumeration because the packet does not list which 15 commits constitute the set. The packet asserts the count grew by 4 during sandbox work but does not name the 4 new Drafter commits. I would need the V1-V15 commit list to verify this claim.

---

ANSWERS TO THE THREE QUESTIONS

Q1. ORDER

The correct next action is (b) close 3.21 with evidence via queue_set.py — but only after the verification evidence is actually collected (see below). Here is why and in what order:

1. FIRST: Collect deterministic verification evidence per commit (Q1a). This is script-collectable raw data (git show, file hashes, schema checks) that requires no LLM judgment. It closes the verification debt that has been growing since the queue-framing-v3 review. The packet's claim of 15 commits needs the commit list specified, but the work itself is deterministic and should proceed.

2. SECOND: Close 3.21 via queue_set.py. The closure mechanism is built and verified (tools/queue/queue_set.py, 89 lines). Running it requires evidence — the deterministic evidence from step 1 IS that evidence. queue_set.py enforces this: its EVIDENCE_REQUIRED set includes "DONE" and "OPEN", and it refuses to write without --evidence. So step 1 must precede step 2.

3. THIRD: Retire the stuck ask_history.py runs (Q1c). AGENTS.md shows 5 identical PENDING runs (lines 82-86), all 0 rounds, all incomplete, all attempting the same FTS5 merge task. These are dead — the task either needs re-scoping or abandonment, but either way the 5 zombie runs should be cleared so they stop polluting the run history.

4. NOT YET: The sandbox card (D1). Reviewer 2 rejected the §14 evidence. The sandbox is not proven, the enforcement walls are not demonstrated in the required format, and the DONE-WHEN criteria are unmet. This work needs to be re-carded with the 9-step test actually executed against a real disposable root. It should not proceed until the evidence gap is closed.

Q2. TOOL SPLIT

DETERMINISTIC (script-collected, no LLM needed):
- Commit verification: `cis_git_show <hash>` + `cis_hash_file <path>` for each commit's changed files. Raw diff stat + file hashes. No judgment required.
- Queue status reconciliation: `cis_query` against queue_items for status counts, `cis_query` against queue_item_events for audit trail. Already demonstrated above.
- Schema verification: `PRAGMA table_info` + table existence checks. Already done.
- ask_history.py run status: `cis_query` against workflow_runs for the 5 stuck run IDs. Already confirmed via AGENTS.md.
- File existence checks (e.g., does raw_evidence.log exist, does the disposable test root exist): `cis_list_dir` or `cis_search_files`.

NON-DETERMINISTIC (requires reviewer judgment):
- Whether the §14 evidence satisfies ADR-SEED-016's gate. This is an alignment question — does the evidence meet the intent of the gate, not just the letter. Reviewer 2 already rendered this judgment (OBJECTIONS) and it was correct.
- Whether 3.21 should be marked DONE vs PARTLY vs OPEN. The queue items table shows 3.21 as "Move the queue out of markdown and into the spine" — the queue IS in the spine (queue_items table exists, 123 rows, the render pipeline works), but the status-closure mechanism was never exercised. This is a judgment call: is the work done, or is the missing closure a remaining need?
- Whether the 11 -> 15 commit scope expansion is correct or whether some commits are out of scope. This is a trajectory question.
- Whether the sandbox evidence gap should block all enforcement work or just the sandbox card specifically.
- Triage of the 56 NULL-status items: these need classification (RUNNABLE vs JUDGMENT) and the check_class column already provides it (I verified: 39 OPEN+RUNNABLE, 13 JUDGMENT items across various statuses). But deciding whether a NULL-status item is actually OPEN or UNASSESSED requires reading its body_md, which is judgment work.

Q3. SCOPE

Expanding 11 -> 15 is the wrong reconciliation if it means verifying 4 more commits by the same method that failed on the first 11. The smarter approach:

The verification debt is not a commit-count problem — it is an evidence-discipline problem. The §14 review proved this: the coder produced prose self-report where raw terminal output was required, and the reviewer caught it. The same pattern likely applies to the other commits. The right move is:

1. For each commit, collect the deterministic evidence first (git show, hash, schema check, file existence). This is script work, fast, no LLM.
2. For commits where the deterministic evidence is sufficient to confirm the claim, close them immediately via queue_set.py with the evidence string.
3. For commits where the deterministic evidence reveals a gap (like §14 did), escalate to reviewer judgment. This is where the 15-commit scope matters — but only for the subset where deterministic evidence is insufficient.

This means the scope should be driven by what the evidence reveals, not by a commit count. If 10 of 15 commits pass deterministic verification and 5 need reviewer judgment, the scope is 5, not 15. The packet's framing ("is 11 -> 15 the right reconciliation?") assumes all commits need the same depth of review. They do not.

ONE MISSING ITEM

The packet does not list the V1-V15 commit hashes. Without that list, I cannot verify the "4 new Drafter commits" claim or determine which commits are in scope. This is the one thing I would need that is not here — and it should be provided before the deterministic verification pass begins, since the commit list IS the work specification for step 1.
