# Advisor review — tg2-two-way-report

- packet: `reviews/pending/tg2-two-way-report.md`
- advisor: advisor on port 8649
- run tag: tg2-two-way-report @ 2026-09-12T16:03:19-05:00
- at: 2026-09-12T16:05:23
- prompt_tokens: 289308
- completion_tokens: 3973
- total_tokens: 293281
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

Now I have enough to deliver the verdict. Let me synthesize what I found.

FRAME: RIGHT_WORK

Queue item 3.31 is explicitly the current work. The cis_get_current_phase query returns next_action: "Container transition (Eric directed 2026-09-12): TG2 two-way report (queue 3.31) is current." The need_status on the queue item is OPEN. The project's seed intent 3 ("checks and balances") is the stated alignment, and the existing one-way pause_notify.py (verified at tools/pause_notify.py) is explicitly marked "ONE-WAY. There is no reply consumer" in its own docstring. The host is being retired (the entrypoint.sh and run_container.sh show the container transition is underway). This is the right item at the right time.

---

Now the technical review. I verified each claim I could against the repo. Findings below.

VERIFIED CLAIMS:

1. pause_notify.py is one-way. Confirmed — tools/pause_notify.py docstring (line 1, "ONE-WAY. There is no reply consumer. See the module note at the bottom.") and the module-bottom note: "THE REPLY PATH IS NOT WIRED, DELIBERATELY."

2. The --continue path flips PENDING to CONSENSUS_REACHED. Confirmed — tools/advisor_review.sh, pause_state() function, mode "release": line 278 executes `UPDATE deliberation_rounds SET reviewer_signal='CONSENSUS_REACHED', objections_json=? WHERE run_id=? AND round_number=?`. The run_id pattern is `advisor-<id>-pause` (line inside the Python: `RUN = "advisor-" + os.environ["ID"] + "-pause"`).

3. advisor_review.sh runs from the HOST and docker-execs into the container. Confirmed — line: `CONTAINER="${CIS_CONTAINER:-cis-pipeline}"` and the gateway call uses `docker exec -i -u worker "$CONTAINER"`. The script itself sets REPO_ROOT from BASH_SOURCE, not from /workspace/cis. So it is host-resident.

4. entrypoint.sh ends with `wait $PIPELINE_PID`. Confirmed — last line of the file.

5. run_container.sh does not currently pass CIS_TG_NOTIFY_TOKEN. Confirmed — the docker run command passes CIS_TG_BRAIN_TOKEN through CIS_TG_VERIFY_TOKEN, CIS_TG_HOME_CHANNEL, and the CIS_*_API_KEY vars, but no CIS_TG_NOTIFY_TOKEN. The proposal's scope item 4 (add it) is correct.

6. The container paths /workspace/cis and /workspace/secrets.env are the mounts. Confirmed — run_container.sh: `-v $CIS_REPO:/workspace/cis` and `-v $SECRETS_FILE:/workspace/secrets.env:ro`. The DB path inside the container would be /workspace/cis/data/cis_memory.db, matching the proposal.

7. Advisor (8649) and evaluator (8650) are on loopback inside the container. Confirmed — entrypoint.sh PROFILES and PORTS arrays, and advisor_review.sh REMOTE_SH curls `http://127.0.0.1:$port/v1/chat/completions`.

8. The pause row is the source of truth (row, not a blocked process). Confirmed — advisor_review.sh docstring: "THE WAITING STATE IS A ROW, NOT A BLOCKED PROCESS."

9. Chat id 6511416750 from TELEGRAM_ALLOWED_USERS. Confirmed — entrypoint.sh writes `TELEGRAM_ALLOWED_USERS=6511416750` into each profile .env, and pause_notify.py reads it from the env file.

COULD NOT VERIFY (git grep returned errors for all search_files calls — "git grep failed"):

- The bot id 8888718741 and username cis_notifyreply_bot. The search for "8888718741" and "cis_notifyreply" both returned "git grep failed", so I cannot confirm or deny the bot's presence in the repo. However, the proposal claims it was verified via Telegram's getMe API and is absent from .env files — this is an external-to-repo claim I cannot check with read-only repo tools. The proposal also claims the V3 bot id 8926607085 was wrong (the host prime gateway bot). I cannot verify this either, but the correction story is internally consistent.

- Whether tools/reply_consumer.py already exists. The search for "reply_consumer" also returned "git grep failed". The cis_list_dir on enforcement/mwl-proof-v2 did not show a reply_consumer.py in that directory, and the proposal scopes it as a NEW file under tools/. I could not list tools/ directly to confirm absence, but the proposal declares it new, which is consistent with pause_notify.py's "no reply consumer" note.

CONCERNS AND OBSERVATIONS:

A. R3 is the riskiest mechanism. The proposal says the reply consumer "flips the PENDING pause row to CONSENSUS_REACHED (the same one-line state flip --continue performs) and then calls the gateways on loopback (127.0.0.1:8649 / 8650) for the next round." I verified the state flip is indeed a one-liner (line 278). But the proposal does not specify what "calls the gateways for the next round" means concretely. The existing --continue path in advisor_review.sh does ONLY the release — it calls `pause_state release` and exits. The actual next-round invocation (round 1 review, reconcile, etc.) is a separate `advisor_review.sh <id>` call made by whatever external loop driver exists. The proposal says "This is the first step of moving the loop driver into the container" but does not name what currently drives the loop, nor what the consumer should call. This is a gap: the release is specified, but the advance is hand-waved. The DONE-WHEN says "the loop advances" but the mechanism for advancing is not specified beyond "calls the gateways on loopback." Calling the gateways is not the same as driving the review loop — the loop driver builds packets, hashes them, records rounds, and writes artifacts. The consumer would need to either invoke advisor_review.sh (which is host-resident and docker-execs in) or replicate its logic. This is the design's largest unresolved question.

B. The "hold" ack-state file at /tmp/cis-logs/reply_consumer.ack. The proposal says this is consumer-local state, consistent with 1.21's "row, not a blocked process" principle. That is correct — the spine row stays PENDING, and the ack is a sidecar. But /tmp is ephemeral across container restarts (docker restart preserves /tmp only if the container is not removed; run_container.sh does `docker rm -f` before each start). So a "hold" ack would be lost on container restart, and Eric would be re-notified for a pause he held. The proposal's F2 says "the spine row is the source of truth, so a restart re-reads the PPENDING row and loses nothing." That is true for the pause state (the spine row survives), but it is NOT true for the ack-state file. A restart would lose the "hold" ack and re-notify Eric. This is not a data-loss problem (the pause is safe), but it is a UX regression: Eric said "hold" and gets re-notified anyway. The proposal should either acknowledge this explicitly as an acceptable tradeoff for the MVP, or persist the ack set somewhere that survives container removal (e.g., a row in the spine, or a file under /workspace/cis which is the persistent mount).

C. The proposal says "The host pause_notify.py call in advisor_review.sh's pause path is replaced by this container-side post once it is live." I verified that call exists: advisor_review.sh's notify_stop() function calls `python3 "$REPO_ROOT/tools/pause_notify.py" "$ID" "$1"`. But the proposal also says coexistence is the default (D2: "two-way does not remove terminal --continue"). The replacement of the notify path is therefore a later policy decision, which is fine, but the proposal should be clearer about the transition: during coexistence, does the container push AND the host push both fire? That would double-notify Eric. The proposal should specify that the host notify_stop() is guarded (e.g., checking whether the consumer is running) or that only one push path is active at a time.

D. Scope says 4 files but the queue item's scope field (from cis_get_queue_item) lists "tools/pause_notify.py; enforcement/mwl-proof-v2/entrypoint.sh; tools/advisor_review.sh" — three files, no mention of run_container.sh or reply_consumer.py. This is expected since the queue item is a heading, not a spec, so the discrepancy is not a problem. But the proposal does not touch advisor_review.sh despite the queue item naming it. The proposal's R1 says the host pause_notify.py call in advisor_review.sh "is replaced by this container-side post once it is live" — that is a future change to advisor_review.sh, not part of this scope. That is consistent with D2 (coexistence is default), but the DONE-WHEN does not include any criterion about advisor_review.sh, which is correct: this item does not modify it.

E. The 30-second long-poll timeout is reasonable for a LAN container with no public HTTPS. The proposal correctly rules out webhooks. No issue.

F. F1 (reply consumed but release fails) — the proposal says the poller advances Telegram's update_id offset only after release succeeds. This is correct and important: it means a failed release will re-deliver the same update on the next poll cycle, giving the consumer another chance. But the proposal also says it replies "release failed — run --continue from the terminal." If the release keeps failing, Eric will get this message every 30 seconds. The proposal should specify a backoff or a max-retry before falling back to "run --continue."

G. F3/F4 (no PENDING row, already released) — the proposal handles this correctly: ACK and advance. This matches the existing --continue behavior, which prints "no open pause for this id — nothing to continue" and exits 0.

H. The proposal does not address what happens if Eric sends "go" for card A but there are multiple PENDING pause rows (multiple cards paused). The existing system's invariant is "one card at a time" (R4, and confirmed by pause_notify.py's other_open_stops function and the 2.25 note about one-card-waits-at-a-time). The proposal's R4 says "The poller resolves the card id from the single PENDING pause row." If there is exactly one PENDING row, this works. If there are zero, F3 applies. If there are more than one, the proposal does not specify behavior. The invariant says this should not happen, but the proposal should state what the consumer does if it does (e.g., reply "multiple cards paused, specify which" or refuse to act).

SUMMARY:

The proposal is the right work at the right time, and the mechanism is sound for the core flow (push from container, poll for reply, release the pause row). The two significant gaps are:

1. R3's "calls the gateways for the next round" is underspecified. The release is clear; the advance is not. The consumer needs a concrete contract for what "advance" means — does it invoke advisor_review.sh from inside the container (which currently docker-execs in from the host), does it call the gateway HTTP endpoints directly, or does it signal an external loop driver? This is the difference between "Eric can reply from his phone" and "Eric can reply from his phone and the loop actually continues."

2. The /tmp ack-state file for "hold" does not survive container removal (docker rm -f in run_container.sh). This means a restart re-notifies Eric for a pause he held. Either acknowledge this as acceptable for MVP, or persist the ack under /workspace/cis.

Minor issues: double-notification during coexistence (C), no backoff on repeated release failure (F), and no handling of the multiple-PENDING-rows edge case (H). None of these block the work; they should be resolved before implementation but are spec-level gaps, not design-level errors.

VERDICT: RIGHT_WORK, RIGHT_TIME. Approve with the R3 advance-mechanism gap and the /tmp ack persistence issue resolved before implementation begins.
