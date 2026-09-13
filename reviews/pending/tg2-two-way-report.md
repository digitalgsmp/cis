# TG2 — two-way report: verdict to Eric's phone, and he can reply

VERSION 5 — revised after round-4 review. Queue item 3.31.

CHANGES (V4 → V5):
- R3 SCOPE CORRECTED (advisor's gap 1): the reply consumer does ONLY the release
  (flip PENDING → CONSENSUS_REACHED). It does NOT "advance the loop." The loop
  advance is currently MANUAL — the Drafter re-invokes `advisor_review.sh` after
  observing the release. There is no programmatic next-round function to call
  (verified: no cron, no systemd timer, no loop driver; the only `--continue`
  references are message text inside `pause_notify.py`). Building a loop driver
  is a SEPARATE item, not TG2.
- "hold" ack state moved to the persistent mount `/workspace/cis/state/` (not
  `/tmp`, which `docker rm -f` wipes) so a restart does not re-notify a held pause.
- Notify is SINGLE-path: the host `pause_notify.py` notify is disabled once the
  container consumer is live (guarded), so Eric is not double-notified.
- F1: added retry cap + backoff before falling back to "run --continue."
- Added multi-pause edge case (H): refuse to act, reply "multiple cards paused."

GOAL_ALIGNMENT: seed intent 3 — checks and balances.

## Problem

`tools/pause_notify.py` pushes a stop to Eric's phone but is one-way; Eric must
run `--continue` from a terminal to release it. The host is being retired, so
the feed moves into the container and the release works from the phone.

## Requirement

A review stop is pushed to Eric's phone from inside the container, and his reply
on the dedicated bot releases the stop — no terminal. **TG2 is release-from-phone
only.** Driving the next review round is out of scope (still manual).

## Scope (4 files)

1. `tools/reply_consumer.py` — NEW. The getUpdates long-poll + release/ack logic.
2. `tools/pause_notify.py` — container-scoped mirror of the push (or a
   `--container` flag) that reads container paths.
3. `enforcement/mwl-proof-v2/entrypoint.sh` — start the consumer before
   `wait $PIPELINE_PID`, under a restart-on-exit wrapper.
4. `run_container.sh` — pass `CIS_TG_NOTIFY_TOKEN` into the container env.

## Mechanism

R1. Container notify (push). A container-scoped mirror of `pause_notify.py`
    reads the stop from `deliberation_rounds`, renders the phone message, posts
    it via `CIS_TG_NOTIFY_TOKEN`. Chat id from `TELEGRAM_ALLOWED_USERS`
    (6511416750). The host `pause_notify.py` notify in `advisor_review.sh`'s
    pause path is DISABLED (guarded by a flag/env) once the container consumer
    is live, so only one push fires.

R2. One reply consumer (pull + release, single process). `tools/reply_consumer.py`
    runs a `getUpdates` long-poll on `CIS_TG_NOTIFY_TOKEN` (30-second timeout,
    not webhook — LAN container, no public HTTPS). On a valid reply it releases
    the pause. Supervised in `entrypoint.sh` as a background process with a
    restart-on-exit wrapper, started BEFORE `wait $PIPELINE_PID`.

R3. Release only (no loop advance). The consumer flips the PENDING pause row to
    `CONSENSUS_REACHED` (the same one-line state flip `--continue` performs:
    `UPDATE deliberation_rounds SET reviewer_signal='CONSENSUS_REACHED' ...`).
    It does NOT run the next review round — that is currently the Drafter's
    manual re-invocation of `advisor_review.sh` after observing the release.
    Building a container-side loop driver is a separate, larger item.

R4. One card at a time (invariant). The poller resolves the card id from the
    single PENDING pause row.

## Path translation (container mirrors read container paths)

The host `pause_notify.py` reads `/home/eric/.hermes/.env` and
`/mnt/projects/cis`. Inside the container those are `/workspace/secrets.env` (or
the injected env var) and `/workspace/cis`. The container-scoped mirror and the
reply consumer must read:
- token: from env var `CIS_TG_NOTIFY_TOKEN` (injected) or `/workspace/secrets.env`
- spine DB: `/workspace/cis/data/cis_memory.db`
- never the host `/home/eric/.hermes/.env`.

## Failure modes

F1. Reply consumed but release fails. The poller advances Telegram's
    `update_id` offset only after the release succeeds. On failure it replies
    "release failed — run --continue from the terminal" and retries; after 3
    consecutive failures it stops re-notifying (backoff) and leaves the row
    PENDING for the terminal path.
F2. Poller crash. Restart-on-exit wrapper restarts it; the spine row is the
    source of truth, so a restart re-reads the PENDING row and loses nothing.
F3. No open pause (already released, e.g. Eric also ran --continue). The poller
    treats "no PENDING row" as success: it ACKs and advances the offset rather
    than looping on the message.
F4. "go" for an already-released pause (terminal/poller race). The consumer
    replies "already released" and advances the offset (same as F3).
F5. Multiple PENDING pause rows (should not happen under R4). The consumer
    replies "multiple cards paused — use the terminal" and does NOT act, rather
    than releasing the wrong card.

## Reply vocabulary

"go" / "continue" — release. "hold" — stay paused AND suppress re-notification.
Anything else — the poller replies with the two valid words and does not act.

## "hold" re-notification suppression

"hold" ACKs and writes the pause run_id to an ack state file under the
persistent mount: `/workspace/cis/state/reply_consumer.ack` (NOT `/tmp`, which
`docker rm -f` wipes on restart). The R1 notify mirror skips re-pushing any pause
whose run_id is in the ack set, until either Eric sends "go" or a NEW pause row
appears. No schema change — the spine row stays PENDING, the ack is consumer-local
state persisted on the durable mount.

## Logging

The reply consumer logs to `/tmp/cis-logs/reply_consumer.log`, matching the
existing `$LOG_DIR` pattern in `entrypoint.sh`.

## Decisions

D1. RESOLVED — dedicated bot `CIS_TG_NOTIFY_TOKEN` = id 8888718741,
    username `cis_notifyreply_bot` (verified new via getMe, absent from host
    `.env` and `secrets.env` pre-write, no gateway polls it). Per-lineage bots
    (advisorgate/evaluategate) stay for addressing a specific reviewer's objection.

D2. Coexistence is the DEFAULT (rollback): two-way release does not remove
    terminal `--continue`; both release the same pause row. Replacement is a
    later policy decision. The NOTIFY push, however, is single-path (R1): the
    host notify is disabled when the container consumer is live.

D3. TG2 does NOT build a loop driver. The next review round remains the
    Drafter's manual `advisor_review.sh` invocation. A container-side loop
    driver is a separate queue item.

## DONE-WHEN

- Reply consumer (`tools/reply_consumer.py`) runs inside the container,
  supervised with restart-on-exit, started before `wait $PIPELINE_PID`.
- `CIS_TG_NOTIFY_TOKEN` reaches the container via `run_container.sh`.
- Eric receives a pause notification on his phone from the container.
- Eric replies "go" → the pause row flips to CONSENSUS_REACHED within one
  polling cycle.
- Eric replies "hold" → ACK + no re-notification of that pause (ack survives a
  container restart).
- Eric sends an unrecognized word → reply listing valid words.
- Terminal `--continue` still works alongside the reply path.
- Consumer crash + restart does not lose the pause state or the hold-ack.
- No PENDING row → consumer ACKs and continues polling.
- Host notify is disabled when the container consumer is live (no double-push).
