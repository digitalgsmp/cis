# Default-to-Success Antipattern — The Pipeline's Core Disease

Session: 2026-07-08 (commit 1ad844d)
Context: After fixing 5 data integrity bugs (see `data_integrity_patterns.md`),
a full audit of pipeline_relay.py found 10 MORE bugs — all the same root
pattern: **the system reports success when it hasn't actually succeeded.**

Eric's insight: "I think this is the result of any LLM building unaccountable
to other LLM oversight. When I had to make Claude and ChatGPT review each piece
of code written, the implementer agent never left shortcuts like this."

## The Pattern

Every LLM-built system has this disease unless peer-reviewed. The LLM writes
code that defaults to "success" and only fails if it explicitly detects failure.
The correct pattern is the opposite: **default to "incomplete" and only succeed
when explicitly verified.**

The fix is not case-by-case. The fix is a principle: every state transition
must be earned by evidence, not assumed by absence of failure.

## The 10 Bugs (Second Audit)

### Bug 1: Verify with no FINAL_JSON = automatic PASS

**Where:** `_verification()` line 1293-1315
**Problem:** If Verify returned garbage with no FINAL_JSON block, `parsed` was
None, `status` was `""`, the `if status == "FAIL"` check was False, and the
run went to `CONSENSUS_REACHED`. No verdict = pass.
**Fix:** Added explicit check: if `not parsed or status not in ("PASS", "FAIL")`
→ escalate. Verify MUST produce a valid verdict or the run escalates.

### Bug 2: Menter output stored as drafter_output

**Where:** `_execution()` line 1232
**Problem:** Menter's output was stored as `drafter_output`, which is the same
column Draft's proposal uses. Verify then queried `drafter_output ORDER BY id
DESC LIMIT 1` — getting Menter's self-report instead of Draft's directive.
Verify was checking Menter's claims about what it built, not the spec it was
told to build.
**Fix:** New `menter_output` column (migration 0016). Verify now queries
`drafter_output WHERE drafter_role = 'draft'` for the directive and
`menter_output` for Menter's self-report separately. Prompt now includes both:
"FINAL_DIRECTIVE (what Menter was told to build)" and "MENTOR'S SELF-REPORT
(what Menter claims it did)" with explicit "NOT evidence" label.

### Bug 3: New rounds start with reviewer_signal = CONSENSUS_REACHED

**Where:** `_start_round()` line 191
**Problem:** Every new deliberation round was born claiming consensus. If the
pipeline crashed between `_start_round()` and `_complete_round()`, the DB had
a round with `CONSENSUS_REACHED` that never actually happened. Phantom
consensus from crashes.
**Fix:** New rounds start as `PENDING`.

### Bug 4: workflow_runs.result defaults to CONSENSUS_REACHED

**Where:** `_create_run()` line 148
**Problem:** A run that just started already claimed consensus in the `result`
column. Any query on `result` before completion saw a lie.
**Fix:** Defaults to `PENDING`.

### Bug 5: Brain/Draft/Menter output not validated before proceeding

**Where:** `_brain_phase()`, `_draft_phase()`, `_execution()`
**Problem:** Brain output was accepted unconditionally — no check for
FINAL_JSON status "READY". Draft accepted without "PROPOSAL_READY". Menter
accepted without any completion status. If any agent returned garbage, the
pipeline just kept going as if it had succeeded.
**Fix:** Each phase now validates the FINAL_JSON status before proceeding:
- Brain: must have status "READY" or "NEEDS_CLARIFICATION"
- Draft: must have status "PROPOSAL_READY" or "REVISION_READY"
- Menter: must have status "CONSENSUS_REACHED" or "DONE" or "COMPLETE"
Invalid output → trajectory marked failed, round escalated, run escalates.

### Bug 6: Circuit breaker in-memory only

**Where:** `_circuit_breaker` dict (line 70)
**Problem:** Process restart = circuit breaker reset. A gateway that was
failing before crash recovery wasn't tripped after restart. The pipeline
happily kept hitting a dead gateway with no memory of prior failures.
**Fix:** New `circuit_breaker_state` table (migration 0017). `_breaker_load()`
reads from DB on cache miss, `_breaker_save()` persists on every state change.
Circuit breaker now survives process restarts.

### Bug 7: Pre-discovery errors silently swallowed

**Where:** `_pre_discovery()` lines 284, 302
**Problem:** If trajectory search or web search failed, the exception was
caught with `except Exception: pass`. The agent got no context and didn't know
it was missing. The agent produced worse output and neither it nor the
pipeline knew why.
**Fix:** Errors now reported to the agent as part of the pre-discovery output:
`"## Prior Agent Trajectories\n(Search error: {e})"`.

### Bug 8: config_version silently empty on git failure

**Where:** `_record_trajectory()` line 385
**Problem:** If git HEAD couldn't be captured, `config_version = ""`. Future
retrieval couldn't filter by code state — trajectories from unknown code
versions were mixed in.
**Fix:** `config_version` defaults to `"unknown"`, captures git error message
or exception text. Never silently empty.

### Bug 9: Worktree tempdir leak on creation failure

**Where:** `_run_isolated_l1()` line 770-783
**Problem:** `tempfile.mkdtemp()` creates the directory BEFORE `git worktree
add` is tried. If worktree add failed, the tempdir was never removed. Orphan
directories accumulated in /tmp.
**Fix:** On worktree creation failure, `shutil.rmtree(worktree_path,
ignore_errors=True)` before setting `worktree_path = None`.

### Bug 10: Verify FAIL stash has no DB audit trail

**Where:** `_verification()` line 1302
**Problem:** `git stash push -m "CIS compensation: ..."` worked, but the stash
ref wasn't stored in the spine. If Eric needed to see what was reverted, he had
to dig through `git stash list`.
**Fix:** Stash ref stored in `deliberation_rounds.objections_json` as
`{"stash_ref": "...", "status": "FAIL"}`. Queryable from DB.

## Migrations Applied

- **0016**: `ALTER TABLE deliberation_rounds ADD COLUMN menter_output TEXT DEFAULT ''`
- **0017**: `CREATE TABLE circuit_breaker_state (role TEXT PRIMARY KEY, failures INTEGER, last_failure_ts REAL, updated_at TEXT)`

## The Meta-Lesson

Eric's observation: LLMs building without peer review leave shortcuts. The
Claude/ChatGPT mutual review pattern (each piece of code reviewed by the other
before acceptance) produced code without these shortcuts. The CIS pipeline
itself had the disease it was designed to cure — Menter built pipeline_relay.py
alone, with no code review gate, and left "default to success" throughout.

**Design decision: Code Review Gate.** After Eric approves the proposal,
Review1 and Review2 shift from proposal review to code review mode. Menter
builds in chunks (default 300 lines / 1 file), each chunk reviewed by both
reviewers before incorporation into the codebase. This is the automated
version of what Eric did manually with Claude and ChatGPT.

**Spec written: `docs/SPEC_CODE_REVIEW_GATE.md` (commit 06e8e8d).**
Key design: Brain generates a Pattern Catalog (project-specific, not
hardcoded), universal checks are language-agnostic (compiles, tests pass,
no secrets, no silent errors), pattern-specific checks come from the
catalog. Chunk params: 300 lines, 1 file, 3 revisions, 20 chunks max.
Knowledge base integration: reviewer prompts include prior Claude/ChatGPT
review findings from the spine FTS5. See
[Code Review Gate Design](references/code_review_gate_design.md).
