# Adversarial Reviewer Verification Pattern

When acting as Reviewer 1 (adversarial critique) in the CIS pipeline,
verify every draft claim against the live codebase. Do not accept
self-report. Do not be agreeable — be correct.

## The Pattern

1. **Claim-by-claim table.** For each numbered claim in the draft,
   find the exact file/line in the running tree using search_files
   and read_file. Render a table: claim, evidence, verdict (TRUE/FALSE).

2. **Runtime facts.** Check live process state, API responses, and env
   vars with terminal commands:
   - `ps aux | grep container_app` — process alive?
   - `curl -s http://127.0.0.1:5000/api/health` — server responding?
   - `curl -s http://127.0.0.1:5000/api/relay/health` — gateways up?
   - `cat /proc/<PID>/environ | tr '\0' '\n' | grep <VAR>` — env facts
   - `stat -c '%s' <file>` — file size claims

3. **Minor inaccuracy flagging.** Flag cosmetic errors (e.g. DB size
   4.5G vs claimed 4.8G) as non-blocking but noted. Precision matters
   even when immaterial — it builds trust in the review.

4. **Execution recipe audit.** Map each step in the proposed recipe to
   real code paths: confirm endpoints exist at the claimed line numbers,
   confirm state transitions match the dispatch table, confirm failure
   signatures are code-accurate.

5. **Bias check.** Confirm the proposal does not drift into over-building
   (adding test infrastructure for a one-shot verification, scaffolding
   CI for an ad-hoc check, etc.). The prior smoke checks were ad-hoc
   runtime verifications — new ones should match that pattern.

6. **Final verdict.** CONSENSUS_REACHED if all claims verified and the
   recipe is sound. OBJECTIONS if any claim is false or the recipe has
   a gap that would cause the implementer to fail or produce bad evidence.

## Key Distinctions

### Line citations vs function boundaries

A Brain intent anchor may cite "line 2862 (chunked execution entry point)"
implying it's inside `_execution()`. It may actually be inside
`_code_review_gate()` — a different method that flows to VERIFICATION
via a different path. Always verify which method a cited line belongs to:

```bash
grep -n 'def ' <file> | awk -F: '$1 <= <cited_line> {last=$0} END {print last}'
```

Or read the function signature above the cited line. A "both entry points"
claim is only valid if both lines are in the same method or both genuinely
serve the same architectural role. Different methods flowing to the same
downstream phase is NOT the same as two entry points of one method.

### Call-graph tracing for "both paths" claims

When a claim says "both execution paths" or "both entry points", trace the
actual pipeline flow to verify:

1. Find the dispatch table: `grep -n 'elif status ==' pipeline_relay.py`
2. Find what calls each cited function: `grep -n 'await self._<func>' pipeline_relay.py`
3. Find the status transitions each function sets:
   `sed -n '<start>,<end>p' pipeline_relay.py | grep '_set_run_status'`
4. Map the full path: does it go through the claimed downstream phase?

This catches the case where two code locations both set `_pre_exec_head` but
only one is in the path the drafter assumes — or where they flow to the same
downstream phase but via different routes with different guardrail coverage.

### Resume behavior: stale vs absent

When a claim says "after resume, _pre_exec_head is empty", verify which
resume branch is involved:
- `resume()` into EXECUTION re-runs the capture (stale, not absent).
- `resume()` into VERIFICATION skips the capture entirely (truly absent).
Both are bugs, but the fix differs: the stale case needs idempotent reuse
of the original snapshot; the absent case needs a reload from persistence.

### Stop states vs terminal states

- TERMINAL_STATES (pipeline_relay.py:94) = {CONSENSUS_REACHED, ESCALATED,
  VERIFY_FAILED, STALE, ERROR} — resume() returns immediately, no dispatch.
- STOP states = WAITING_FOR_HUMAN, ERIC_GATE — resume() prints a message
  and returns without advancing. NOT in TERMINAL_STATES.
- Both count as proof the mechanism worked — the daemon thread drove
  the run there.

### Two execution paths to VERIFICATION

pipeline_relay.py has TWO independent paths that both flow into
_verification(), not one. The chunked path (CODE_REVIEW_GATE, line 2809)
goes directly to VERIFICATION — it does NOT pass through _execution().
The regular path (ERIC_GATE → EXECUTION, line 3196) goes through
_execution() then VERIFICATION. Both capture _pre_exec_head in-memory
only (lines 2871 and 3211), neither persists it, and resume into
VERIFICATION loses it. See `references/pipeline_relay_execution_paths.md`
for full path tracing and the pre-exec snapshot gap.

### Evidence bar

Eric's verification-hardening rule: self-report is not truth. A prose
"it worked" without raw curl outputs is not a pass. The report must
contain verbatim: the POST response, at least three raw GET snapshots
(initial, transition, final), and the pre-POST /api/relay/health output.

### Failure disambiguation

Keep failure hypotheses separate in the report:
- F1: POST 500 = start_sync broke (not resume)
- F2: background.error non-null = resume exception
- F3: active false, no rounds, still BRAIN_PHASE = resume no-op
- F4: 10min BRAIN_PHASE stall, active=true, error=null = gateway hypothesis

Never attribute a gateway timeout to resume. Re-check /api/relay/health
and report per-gateway latency.

### Read-only enforcement

Do not call /api/relay/<run_id>/answer or /gate — that is acting as Eric.
Do not kill the server process, restart the app, or touch the DB. The
only write is the one sanctioned workflow_runs row created by the POST
itself; it stays as audit data, no cleanup.
