# Agent Call Retry Pattern

Session: 2026-07-09
Identified during code review gate escalation debugging (run-e4aac6f86dc70fd4)

## The Problem

The code review gate (`_review_single_chunk()` in pipeline_relay.py) makes
4 sequential agent calls per chunk revision cycle:

1. Menter builds the chunk
2. Reviewer A reviews (first pass)
3. Reviewer B reviews (second pass, sees A's output)
4. Reviewer A consensus (sees B's output, delivers verdict)

Originally, each call used a bare `try/except` that immediately escalated
on ANY exception — no retry, no backoff. A single transient failure
(timeout, empty response, momentary gateway hiccup) killed the entire
chunk and escalated the run.

### Root Cause: Run-e4aac6f86dc70fd4

Reviewer B (GLM-5.2 on port 8647) threw an exception on revision 3
of chunk 1. The exception message was empty (`str(e) == ""`), making
debugging difficult. The run escalated immediately with no recovery.

```
[pipeline] Reviewer B failed on chunk 1: 
[pipeline] Chunk 1 escalated — stopping.
```

Note the empty error message after the colon — that's the `str(e)` bug.

## The Fix: `_call_agent_with_retry()`

Added a method on `PipelineRelay` that wraps `_call_agent()` with:

1. **One retry** — original attempt + 1 retry = 2 total attempts
2. **2s backoff** — brief `asyncio.sleep(2)` between attempts
3. **Empty output detection** — retries on empty responses, not just exceptions
4. **`repr(e)` fallback** — uses `str(e) or repr(e)` to avoid empty error logs
5. **Escalation only after both attempts fail** — records to `code_review_chunks`
   with ESCALATE verdict and returns `None` so caller can `return` cleanly

### Usage Pattern

```python
# Before (no retry — single failure escalates):
try:
    output = await _call_agent("review2", prompt, run_id)
except Exception as e:
    _breaker_record_failure("review2")
    _complete_round(self.conn, round_id, "ERROR")
    print(f"Reviewer B failed: {e}")  # str(e) can be empty!
    # ... record escalation ...
    return

# After (retry with backoff):
output = await self._call_agent_with_retry(
    "review2", prompt, run_id, chunk_num, "Reviewer B",
    round_id, self.conn, diff_text, l1_results, revision,
    review_a_output=review_a_output)
if output is None:
    return  # escalation already handled
```

## Why Not Just Use `_call_reviewers_parallel()`?

The proposal review phase already has retry logic via `_call_reviewers_parallel()`,
which retries on empty/ambiguous output. But the code review gate calls
agents **sequentially** (A → B → A consensus), not in parallel, so it
can't use the parallel helper. Each sequential call needs its own retry.

## The `str(e)` Empty String Bug

httpx exceptions (TimeoutException, ConnectError, etc.) often have
`str(e) == ""`. This is because httpx stores error details in attributes
rather than the exception message. The result: error logs show nothing.

```python
# Bad — prints empty string for httpx exceptions:
print(f"Failed: {e}")

# Good — falls back to repr which always has content:
err_msg = str(e) or repr(e)
print(f"Failed: {err_msg}")
```

`repr(e)` includes the exception class name and constructor args, which
always produces a non-empty string. For example:
- `str(httpx.ReadTimeout(...))` → `""`
- `repr(httpx.ReadTimeout(...))` → `"ReadTimeout('')"`

## Commit

`8e620ec` — fix: add retry logic to code review gate agent calls

All 4 call sites in `_review_single_chunk()` (Menter, Reviewer A,
Reviewer B, consensus) now use `self._call_agent_with_retry()` instead
of bare `try/except _call_agent()`.
