# Advisor review — reconciliation-assessment

- packet: `reviews/pending/reconciliation-assessment.md`
- advisor: advisor on port 8649, no tools
- run tag: reconciliation-assessment @ 2026-09-12T12:44:21-05:00
- at: 2026-09-12T12:45:11
- prompt_tokens: 126052
- completion_tokens: 1336
- total_tokens: 127388
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

This is the right work at the right time. The project is mid-reframe — the host pipeline is being retired (ADR-SEED-013 already decided), roles are consolidating (Brain+Draft into one Author), and the queue is migrating from markdown into the spine (item 3.21 is OPEN, need_status OPEN). The 11 Drafter commits exist in git history (all 11 hashes verified against actual commit diffs), but per ADR-SEED-002 none of them carry verified evidence of success — they're self-reported completions that need independent verification before being trusted. Reconciling the reframing decisions with the unverified claims and the queue state into one assessable list is exactly the prerequisite for the next phase of work. Nothing here is premature or off-track.

---

Now my assessment against the four questions:

## 1. FRAME: is this the right, complete set of work?

Mostly yes, with gaps. The packet correctly identifies the three streams that need reconciliation: design reframing (A), open blocks (B), and unverified Drafter claims (C). But it's missing several things that matter:

MISSING FROM THE LIST:

a) **Item 3.21 completion state.** The queue item for "move the queue into the spine" is OPEN with need_status=OPEN, but commits 0869c97 and 16a30bf (claims C2, C3) claim to have done exactly that. The reconciliation list doesn't flag that 3.21's status in the DB hasn't been updated to reflect the work the Drafter claims to have done. Either the claims are false (the migration didn't run) or the claims are true but the queue wasn't updated (the queue can't track its own item's completion). This is a structural gap — ADR-3.21-001 decided queue_items won't carry run-link/success, but nothing in this list addresses how 3.21 gets closed.

b) **The ask_history.py run (run-4bbeea78056e2607-1788140226) is still in ERIC_GATE.** It's the most recent pipeline run, it's pending Eric's approval, and it's not mentioned anywhere in the reconciliation packet. If the host pipeline is being retired (section A4), what happens to this in-flight run?

c) **The lineage map (A2) is "proposed but not confirmed by Eric."** The packet lists this as an "open sub-decision" but doesn't assign it a queue item or tracking number. If the advisor/evaluator bots and the Author consolidation (B1-B3) all depend on the lineage assignment, the unconfirmed Claude-as-coder decision blocks the two-way Telegram work (B3, E). The list should make that dependency explicit.

d) **Migration 0033 (classify_check.sql) is in the commit but not in the list.** Commit 16a30bf adds `runtime/schema/migrations/0033_check_class.sql` — a new schema migration. The reconciliation list doesn't mention that a new migration was introduced and whether it was applied to the live spine.

e) **No mention of whether the HCP/AGENTS.md auto-regeneration (A3) was actually removed from the pre-commit hook.** It's listed as "decided" but not as an open block. Was the hook already disabled? If not, it should be in section B.

## 2. What is missing from this list?

Covered above. To summarize the concrete additions needed:
- A5: Close or retire the in-flight ask_history.py run (ERIC_GATE) — or explicitly decide it's abandoned under "retire the host pipeline."
- A7: The lineage-map sub-decision (Claude-as-coder) needs a tracking item and a stated blocker on B3/E.
- B5: Migration 0033 — was it applied? Does it need verification?
- B6: HCP/AGENTS.md pre-commit hook removal — confirm it was done or add as open block.
- D2: How does item 3.21 get marked complete? The queue can't track its own success (ADR-3.21-001), but the current need_status is still OPEN despite the work being claimed done.

## 3. Correct priority/order — what unblocks what?

The dependency chain I see:

1. **Verify the 11 claims (C1-C11)** — this is first because everything downstream depends on knowing what actually exists. Per ADR-SEED-002, self-report is not truth. Several of these commits are heavy (0869c97 adds 509 lines across 19 files, 185ac25 adds 520 lines across 15 files) and touch core infrastructure (spine, mcp_bridge, queue tools). If any are doc-churn-only or broken, the design reframing assumptions built on top of them collapse.

2. **B2 (un-strip the Author's read-only MCP)** — this unblocks the Author's ability to do anything useful, including verifying the claims. If the Author can't read the DB, the Author can't self-verify.

3. **B1 (consolidate Brain+Draft)** — the V2 card is drafted and advisor-reviewed, ready to implement. This is the structural prerequisite for B3.

4. **B3 (wire the Author's chat path)** — depends on B1 (consolidated role) and the lineage sub-decision from A2. Two-way Telegram is the user-facing deliverable.

5. **B4 (load design-spec items into queue DB)** — depends on the queue authority migration (C3/0869c97) being verified. If the migration didn't run, there's no queue table to load into.

6. **E (Telegram bot wiring)** — depends on B3 for the bot path, but the entrypoint.sh slot-filling (adding CIS_TG_ADVISOR_TOKEN + CIS_TG_EVALUATOR_TOKEN) can proceed in parallel with B1/B3 since it's pure configuration.

7. **ADR-015/016 enforcement gates** — correctly noted as a separate track. No dependency on the author consolidation. Can proceed independently but should not block the pipeline work.

## 4. Are any of the 11 claims mischaracterized?

All 11 commits exist and match their described scope. But the characterizations need refinement on a few:

**C1 (3f7359c — intent_bridge.py):** Correct. 132 lines of new Python in tools/intent_bridge.py. But it also churned 44 lines of EXPORT_MANIFEST.json and touched 12 HCP docs. The functional artifact exists; whether it's wired into the front-door flow is not visible from the diff stat alone.

**C2 (16a30bf — deterministic item classifier):** Correct. Adds tools/queue/classify_check.py (179 lines) and migration 0033. This is a new schema migration — the list should flag that the live spine may need this migration applied.

**C3 (0869c97 — database becomes queue authority):** Correctand substantial. 509 lines across 19 files, including migration 0032_queue_authority.sql, tools/queue/queue_set.py, render_build_list.py, and extract_queue_items.py. This is real infrastructure, not doc-churn. But the queue item 3.21 is still need_status=OPEN in the DB, which means either the migration was never applied to the live spine, or it was applied but the item wasn't updated. This is the core reconciliation question the list should foreground.

**C4 (d9bc5ca — pause notifications):** Correct. Modifies tools/pause_notify.py (168 lines changed, net -50). Real code change to the notification path.

**C5 (4df51dd — advisor loop writes knowledge record):** Correct. Adds tools/queue/ingest_advisor_rounds.py (121 lines) and modifies tools/advisor_review.sh (15 lines). New ingestion tool exists.

**C6 (198fc71 — semantic search cache + MCP timeout):** Correct. Modifies runtime/mcp_bridge/spine.py (76 lines changed) and 4 profile YAMLs. The cache singleton fix and timeout raise are in the bridge layer, not just doc churn.

**C7 (6fdeefe — fix KB search + cis_list_dir + secrets exclusion):** Correct and substantial. Touches runtime/mcp_bridge/chroma_index.py (19 lines), spine.py (108 lines), tools.py (51 lines), and both reviewer profile YAMLs. This is the "un-blind the reviewers" infrastructure prep. Real.

**C8 (0c5fbc1 — add --resolve triage):** Correct. Modifies tools/advisor_review.sh (169 lines) and tools/pause_notify.py (112 lines). The --resolve flag is added to the triage path.

**C9 (e58abac — un-blind reviewers, read-only MCP):** Correct and the heaviest of the set. 426 lines across 17 files, including runtime/mcp_bridge/tools.py (288 new lines) and server.py (30 lines). This is the MCP tool exposure for reviewers. Real infrastructure, not doc-churn.

**C10 (185ac25 — wire round-2 reconciliation):** Correct. 520 lines across 15 files. Heavy modifications to tools/advisor_review.sh (277 lines) and tools/pause_notify.py (237 lines). The cross-feed wiring is in the orchestration scripts.

**C11 (a3f7dea — docs merge candidate items):** Correct but NOTE: this is almost entirely doc-churn. 4,071 of 4,147 added lines are docs/PHASE_2_CANDIDATE_ITEMS.md. This is the one claim that is primarily documentation, not functional code. The list should distinguish C11 from the infrastructure commits — it's not "mischaracterized" (the commit message says "docs:"), but if the verification standard is "does it run," C11 has no runnable artifact.

---

Summary of what I'd tell the reviewer who picks this up:

The 11 commits are all real and match their described scope. None are fabricated. But "committed" is not "verified working" — per ADR-SEED-002, each needs independent execution evidence. The two highest-risk claims are C3 (queue authority — because the DB still shows 3.21 as OPEN) and C11 (because it's 98% documentation). The list is missing the in-flight ERIC_GATE run, the unconfirmed lineage sub-decision's blocking effect, the migration 0033 application question, and the 3.21 closure mechanism. Priority: verify claims first, then B2 (un-strip Author), then B1 (consolidate), then B3 (chat path), then B4 (load queue), with E (Telegram config) in parallel.
