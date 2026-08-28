# Data Integrity Patterns — Pipeline Relay

Session: 2026-07-08 (commits 6c2207d → 8dc6bf2 → bafca21)
Context: User said "I want every step along the pipeline to fulfill its function
so that the application produces factual and accurate outcomes."
Then: "if a reviewer returns nothing it should not review returned and something
to kick it back so that the reviewer performs a review. if something is ambiguous
it should record as ambiguous and kick it back for an unambiguous review.
if this data is to be used as memory and trajectories, the agent has to be
completing its role."

## Core Principle

**Agents must complete their role.** If a reviewer returned nothing, it didn't
review. That's not a "failed review" in the memory — it's "no review." The
trajectory must not record success for an agent that didn't do its job.

Three distinct outcomes:
- **Consensus** — both reviewers completed their role and agreed
- **Objection** — both reviewers completed their role, at least one disagreed
- **Incomplete** — at least one reviewer didn't complete its role (empty, error, unparseable)

Incomplete is NOT an objection. An objection is a real disagreement from a
reviewer who did the work. Incomplete means the reviewer didn't show up.

## Bug 1: Empty output treated as consensus

### Problem
`_check_consensus(r1_output, r2_output)` parsed FINAL_JSON from both reviewers.
If r1_output was `""` (gateway returned nothing), `r1_json` was None, `r1_status`
was `""`. If r2 parsed OK and said `CONSENSUS_REACHED`:
- `consensus = ("" == "CONSENSUS_REACHED" and ...)` = False
- `has_obj = ("" == "OBJECTIONS" ...)` = False
- Result: consensus=False, has_obj=False → fell through to `else` → treated as consensus

A failed reviewer silently became a yes.

### Fix — Three-State Model
`_check_consensus` now takes error params and returns three states:
```python
def _check_consensus(r1_output, r2_output, r1_error=None, r2_error=None):
    # A reviewer with an error did not complete its role
    r1_complete = r1_output.strip() and not r1_error
    r2_complete = r2_output.strip() and not r2_error

    if not r1_complete or not r2_complete:
        return False, False, None  # INCOMPLETE — not an objection
    # ... both completed, parse and check signals
```

The caller distinguishes incomplete from objection:
```python
consensus, has_obj, obj_text = _check_consensus(r1_out, r2_out, r1_err, r2_err)
if not consensus and not has_obj and obj_text is None:
    # INCOMPLETE — escalate, don't fake an objection
    _set_run_status(self.conn, run_id, "ESCALATED")
```

## Bug 2: Signal stored before consensus check

### Problem
Both review phases called `_complete_round(conn, round_id, "CONSENSUS_REACHED")`
BEFORE checking actual consensus. The DB said consensus even when reviewers objected.

### Fix
Compute consensus first, store actual signal:
```python
consensus, has_obj, obj_text = _check_consensus(r1_out, r2_out, r1_err, r2_err)
actual_signal = "CONSENSUS_REACHED" if consensus and not has_obj else "OBJECTIONS"
_complete_round(self.conn, round_id, actual_signal, {...})
```

## Bug 3: Trajectory outcome marked success unconditionally

### Problem
`_update_trajectory_outcome(conn, run_id, "review1", "intent_review", "success")`
was called before checking if the output was empty.

### Fix
Outcome based on actual completion, not just "the HTTP call returned":
```python
_update_trajectory_outcome(self.conn, run_id, "review1", "intent_review",
                          "failed" if r1_err else "success")
```
Error handlers in all 6 phases now record failed trajectories.

## Bug 4: Single reviewer failure silently ignored

### Problem
Only escalated if BOTH reviewers errored. A single empty response was ignored
and consensus was declared based on the other reviewer alone.

### Fix — Retry Then Escalate as Incomplete
`_call_reviewers_parallel` now retries once on empty/ambiguous:
```python
async def _call_with_retry(role: str):
    for attempt in range(MAX_REVIEWER_RETRIES + 1):
        output = await _call_agent(role, prompt, run_id)
        if not output.strip():
            if attempt < MAX_REVIEWER_RETRIES:
                continue  # retry
            return "", "empty output"
        parsed = _parse_final_json(output)
        if parsed and parsed.get("status") in ("CONSENSUS_REACHED", "OBJECTIONS", "ESCALATE"):
            return output, None  # completed its role
        # ambiguous — retry
    return output, "ambiguous output"
```

If still incomplete after retry → escalate with "Review incomplete" message.
Not an objection — the reviewer didn't complete its role.

## Bug 5: _call_agent recorded success on empty response

### Problem
```python
_breaker_record_success(role)  # called BEFORE checking content
choices = data.get("choices", [])
if choices:
    return choices[0].get("message", {}).get("content", "")
return ""  # silently returns empty
```

The circuit breaker never tripped because successes were recorded even on
empty responses. The pipeline kept calling a dead gateway.

### Fix
```python
choices = data.get("choices", [])
if not choices:
    _breaker_record_failure(role)
    raise ConnectionError(f"Gateway {role} returned no choices — zombie process")
content = choices[0].get("message", {}).get("content", "")
if not content.strip():
    reasoning = choices[0].get("message", {}).get("reasoning_content", "")
    if reasoning and reasoning.strip():
        content = reasoning  # fallback for models that use reasoning_content
if not content.strip():
    _breaker_record_failure(role)
    raise ConnectionError(f"Gateway {role} returned empty content — model backend not working")
_breaker_record_success(role)  # only after content validated
return content
```

## Verification

5 unit tests for `_check_consensus` (updated for three-state model):
1. Both empty + errors → incomplete `(False, False, None)`
2. One empty + error, one valid → incomplete `(False, False, None)`
3. Both consensus → consensus `(True, False, None)`
4. One objects → real objection `(False, True, "...")`
5. Both have output but text-scan fallback → consensus/objection based on keywords

All pass.
