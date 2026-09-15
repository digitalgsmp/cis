# Advisor review — container-working-state-blocks

- packet: `reviews/pending/container-working-state-blocks.md`
- advisor: evaluator on port 8650
- run tag: container-working-state-blocks @ 2026-09-13T11:09:02-05:00
- at: 2026-09-13T11:15:40
- prompt_tokens: 483568
- completion_tokens: 7493
- total_tokens: 491061
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

## Current blocks to container working state

**BLOCK 1 — Host notify path not disabled (CRITICAL)**

What: `tools/advisor_review.sh` line 294 unconditionally calls `python3 "$REPO_ROOT/tools/pause_notify.py"`. No guard checks whether the container consumer is live.

Why it blocks: If the pipeline runs inside the container and hits a pause, both the host notify (if the host is still running) and the container consumer could fire, double-notifying Eric. The proposal's R1 requires "the host pause_notify.py notify is disabled once the container consumer is live (guarded)" — that guard is absent.

Evidence: `cis_search_files` pattern `pause_notify` → `tools/advisor_review.sh:294`. No guard logic found in advisor_review.sh.

Next action: Add a guard to advisor_review.sh's `notify_stop()` function that checks for a container-consumer-running flag (e.g., env var `CIS_CONTAINER_CONSUMER_LIVE` or a lock file) and skips the host notify when the container path is active.

---

**BLOCK 2 — pause_notify.py reads host paths, not container paths (CRITICAL)**

What: `tools/pause_notify.py` defaults to `DB = "/mnt/projects/cis/data/cis_memory.db"` and `ENV_FILE = "/home/eric/.hermes/.env"`. Inside the container, those paths don't exist — the spine is at `/workspace/cis/data/cis_memory.db` and the token comes from `CIS_TG_NOTIFY_TOKEN` env var or `/workspace/secrets.env`.

Why it blocks: If a pause fires inside the container and advisor_review.sh calls pause_notify.py, the script will fail to find the token or spine DB, so Eric never gets notified from the container. The proposal's R1 scopes a "container-scoped mirror" of pause_notify.py, but I found no evidence it was built.

Evidence: `cis_read_file` path `tools/pause_notify.py` lines 36-37 show hardcoded host paths. No container-scoped variant found in `cis_list_dir` tools/ or `cis_search_files`.

Next action: Either (a) build the container-scoped mirror (e.g., `tools/pause_notify_container.py`) that reads `/workspace/cis` paths and `CIS_TG_NOTIFY_TOKEN`, then wire advisor_review.sh to call it when running inside the container; or (b) make pause_notify.py path-aware via env var `CIS_CONTAINER_MODE=1` that switches to container paths.

---

**BLOCK 3 — Full-loop completion not verified (UNKNOWN)**

What: The proposal claims the container is "up to working state" but I cannot verify a card has run the full loop: Author → advisor review → Claude sandbox → pipeline review → verification → evidence reaches Eric's phone → Eric releases from phone.

Why it blocks: Without evidence of a successful end-to-end run, we don't know what else might fail. The recent workflow_runs I queried (cis_get_recent_runs) show runs from August 28-31 with status ERIC_GATE, ESCALATED, or ERROR — none show a completed full-loop card.

Evidence: `cis_get_recent_runs` limit=10 shows no CONSENSUS_REACHED runs with a full pipeline signature. The most recent successful run is `run-e70293544935a92e-1787973534` from August 29, which was a verification task, not a full card.

Next action: Run one card end-to-end inside the container with logging enabled at each stage. Verify: (1) advisor_review.sh fires and calls the container-scoped notify (not the host one); (2) the pause notification reaches Eric's phone from the container; (3) Eric replies "go"; (4) reply_consumer.py flips the row to CONSENSUS_REACHED; (5) the Drafter re-invokes advisor_review.sh and the loop advances.

---

**BLOCK 4 — Stale PENDING pause rows (DATA INCONSISTENCY)**

What: The proposal claims "8 stale PENDING pause rows superseded (0 remaining)" but my query shows 11 PENDING rows still exist in deliberation_rounds (all with requires_eric_review=0, dated July-August 2026).

Why it blocks: If the reply_consumer.py's single-card invariant (F5) triggers on >1 PENDING row, it will refuse to act and reply "multiple cards paused." The proposal says those rows were "superseded" but they still show PENDING in the spine.

Evidence: `cis_query` SQL `SELECT ... FROM deliberation_rounds WHERE reviewer_signal='PENDING'` returns 11 rows, most recent from 2026-08-24.

Next action: Verify whether those 11 PENDING rows are actually stale (belong to closed/superseded runs) and if so, flip them to a terminal state (CONSENSUS_REACHED or ERROR) so only one PENDING row exists when the container loop runs. Alternatively, confirm the invariant is enforced at the workflow_runs level, not deliberation_rounds level.

---

**Summary**

The proposal correctly identifies Block 1 (CIS_TG_NOTIFY_TOKEN) as FIXED. But three other blocks remain: host notify not disabled (BLOCK 1), pause_notify.py reads wrong paths (BLOCK 2), full-loop not verified (BLOCK 3), and stale PENDING rows (BLOCK 4). Until these are cleared, the container cannot reach working state as defined.
