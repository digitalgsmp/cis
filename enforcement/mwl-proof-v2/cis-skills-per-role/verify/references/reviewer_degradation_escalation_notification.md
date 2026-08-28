# Reviewer Degradation + Escalation Notification

## Problem

Two failure modes caused pipeline runs to die unnecessarily:

1. **Transient model failure kills the run** — Reviewer 2 (GLM via OpenRouter) randomly returns empty output. The old `MAX_REVIEWER_RETRIES = 1` gave only 2 total attempts. If both failed, `_check_consensus()` returned `(False, False, None)` — "incomplete" — and the run escalated. Reviewer 1's valid objections were thrown away.

2. **Escalation is a silent dead end** — `_set_run_status(conn, run_id, "ESCALATED")` just wrote to the DB and stopped. Nobody was notified. Eric had to manually poll the API to discover a run failed, then ask an agent to dig through the spine to find out why.

## Fix 1: Reviewer Retry + Single-Reviewer Degradation

### Retry increase
`MAX_REVIEWER_RETRIES` changed from 1 to 2 in `_call_reviewers_parallel()`. Three total attempts per reviewer before giving up.

### Single-reviewer degradation in `_check_consensus()`
The old logic:
```python
if not r1_complete:
    return False, False, None  # r1 incomplete → escalate
if not r2_complete:
    return False, False, None  # r2 incomplete → escalate
```

The new logic: if one reviewer fails but the other completed, check what the survivor said:
- **OBJECTIONS** → return `(False, True, objection_text)` — send Brain back with the valid objections
- **CONSENSUS_REACHED** → return `(True, False, None)` — proceed with caution
- **Ambiguous** → return `(False, False, None)` — escalate (can't determine intent)

Both text-scan fallback (for unparseable FINAL_JSON) and JSON parsing are handled. The objection text includes a note that the other reviewer had no response (model failure).

Only escalates if:
- Both reviewers fail (empty/error on both sides)
- Both complete but can't reach consensus after MAX_BRAIN_ROUNDS

### Why this matters
Without this fix, a single transient OpenRouter timeout or rate limit on Reviewer 2 kills the entire run — even when Reviewer 1 had substantive, actionable objections that Brain could have used to revise. Valid feedback was being discarded because of a model hiccup on the other side.

## Fix 2: Escalation Notification

### `_notify_terminal_failure()` function
Added to `pipeline_relay.py`. Called by `_set_run_status()` whenever status is set to `ESCALATED`, `ERROR`, or `VERIFY_FAILED`.

**What it does:**
1. Queries the run's topic and last deliberation round (phase + signal)
2. Formats a Telegram message: run ID, phase, signal, intent preview (first 100 chars), and curl command to check status
3. Sends via Telegram Bot API (`POST https://api.telegram.org/bot{token}/sendMessage`)
4. If no Telegram credentials configured, logs to stdout instead

**Required env vars** (in `/workspace/secrets.env`):
```
CIS_TELEGRAM_BOT_TOKEN=<bot_token>
CIS_TELEGRAM_CHAT_ID=<chat_id>
```

These are loaded by `entrypoint.sh` via `set -a; source /workspace/secrets.env; set +a` and inherited by the pipeline API process.

### Safety
- Notification failures are caught and logged — they never crash the pipeline
- The notification is fire-and-forget — it doesn't block or retry
- Only terminal failures trigger notifications, not intermediate states

## Verification

- Run `run-86bc4d1009b8fb44-1783645778` (add comment to container_app.py): completed full 7-phase pipeline with CONSENSUS_REACHED — proves the execute_code fix works
- Run `run-12d5aa6946666b73-1783649571` (14-component SWA plan): re-fired after all fixes applied — tests reviewer degradation on large intents

## Key Files
- `runtime/abstraction/pipeline_relay.py` — `_check_consensus()`, `_call_reviewers_parallel()`, `_set_run_status()`, `_notify_terminal_failure()`
- `enforcement/mwl-proof-v2/managed-config.yaml` — `approvals: mode: "off"` in managed config
- `enforcement/mwl-proof-v2/entrypoint.sh` — stale pidfile cleanup, `set -a; source` for env vars
- `/tmp/cis-secrets.env` — `CIS_TELEGRAM_BOT_TOKEN` and `CIS_TELEGRAM_CHAT_ID`
