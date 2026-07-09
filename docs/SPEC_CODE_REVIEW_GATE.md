# SPEC: Code Review Gate
**Status:** DRAFT — awaiting Eric Gate review
**Date:** 2026-07-09
**Depends on:** pipeline_relay.py (commit 1ad844d), deliberation_rounds schema (migration 0016)

## 1. Purpose

After Eric approves the proposal (ERIC GATE), Review1 and Review2 shift
from proposal review to **code review mode**. Menter builds in chunks;
each chunk is reviewed by both reviewers before incorporation into the
codebase.

This closes the verification gap identified in session: an LLM building
code alone, unaccountable to peer review, leaves shortcuts. The Claude/
ChatGPT manual review pattern — where each piece of code was checked by
a second model before acceptance — is automated here.

## 2. Pipeline Flow (Revised)

```
Brain → Intent Review → Draft → Proposal Review → ERIC GATE
                                                          ↓
                                                   PATTERN CATALOG
                                                   (Brain reads codebase,
                                                    produces catalog,
                                                    reviewers validate)
                                                          ↓
                                                   CODE_REVIEW_GATE
                                                   (Menter builds chunk
                                                    → reviewers check
                                                    → incorporate or reject)
                                                          ↓
                                                   VERIFICATION
                                                   (L1 + L2 as before)
```

## 3. Pattern Catalog (Project Onboarding)

### 3.1 When Generated

On the first pipeline run against a new project, after Eric approves the
proposal but before Menter starts building. Brain's additional job is to
read the existing codebase and produce a pattern catalog.

If the codebase is empty (new project), the catalog is derived from the
proposal itself — Draft's spec defines the patterns the code will use.

### 3.2 What Brain Produces

Brain reads the project root and identifies:

1. **Language and toolchain** — Python/pytest, Go/go test, JS/jest, etc.
2. **Architectural patterns** — what structural forms exist in this code
   (MVC controllers, state machines, functional pipelines, etc.)
3. **Convention rules** — naming, file organization, error handling style
4. **Test convention** — how tests are written and run
5. **Completion criteria per pattern** — what "done" looks like for each
   structural form found in the codebase

### 3.3 Catalog Format

```markdown
# Pattern Catalog: [project name]

## Toolchain
- Language: Python 3.12
- Test runner: pytest
- Linter: pyright
- Build: none (interpreted)

## Patterns Found

### Pattern A: Route Handler (Flask)
**Found in:** runtime/api/relay.py, runtime/app.py
**Structure:**
  1. Decorator with route path
  2. Auth check (bearer token)
  3. Input validation
  4. Business logic call
  5. JSON response
**Completion criteria:**
  - [ ] Route registered in Flask app
  - [ ] Auth check present (not skipped)
  - [ ] Input validated before use
  - [ ] Returns JSON with status field
  - [ ] Error response on failure (not crash)
  - [ ] Test exists or is specified

### Pattern B: DB Helper
**Found in:** runtime/abstraction/pipeline_relay.py
**Structure:**
  1. Takes connection as param
  2. Parameterized SQL (no f-strings in WHERE)
  3. Commit after write
  4. Returns typed result or None
**Completion criteria:**
  - [ ] All SQL parameterized
  - [ ] Commit after every write
  - [ ] Defaults to "incomplete" not "success"
  - [ ] Not-found returns None or raises

[... additional patterns ...]
```

### 3.4 Catalog Validation

Reviewers check the catalog:
- Are the patterns real (do they actually exist in the code)?
- Are the completion criteria concrete and checkable?
- Is anything missing?

Catalog goes through ERIC GATE before Menter uses it.

### 3.5 Catalog Storage

Stored as `runtime/catalogs/PATTERN_CATALOG.md` in the project repo.
Versioned via git. Brain can update it on subsequent runs if new patterns
are introduced.

## 4. Code Review Gate

### 4.1 Universal Criteria (Baked Into Menter)

Universal criteria are not just a review checklist — they are part of
Menter's baseline behavior. Menter's system prompt includes these as
rules it must follow when writing any code, regardless of project.

**Menter's Universal Rules (always active):**

1. **Default to incomplete** — no function returns success without
   completing its job. No status field defaults to "success" or
   "consensus." Unknown states are errors, not passes.
2. **Handle errors explicitly** — every exception path must do something
   meaningful (log, raise, escalate). Silent `except: pass` is forbidden.
3. **No secrets in code** — no hardcoded API keys, passwords, tokens.
   Use environment variables or config files.
4. **No debug leftovers** — no print() statements, no commented-out code,
   no TODO without context.
5. **Claims must match reality** — if you say "added function X", the
   function X must exist in the code you wrote. Your self-report is a
   claim, not evidence.
6. **Clean up after yourself** — no orphan temp files, no leftover debug
   artifacts, no resources opened without being closed.
7. **State must persist** — if your code maintains state (circuit breaker,
   cache, counter), it must survive a process restart. In-memory only is
   not acceptable for state that matters.
8. **Validate before proceeding** — if your function calls another function
   or agent, validate the response before acting on it. Empty or malformed
   output is an error, not a silent success.

These rules are injected into Menter's prompt at build time. Menter
self-checks against them before submitting each chunk. The review process
catches what Menter missed — but Menter is trying first.

### 4.2 Project-Specific Criteria (From Pattern Catalog)

In addition to universal rules, each chunk is checked against the pattern
catalog. The reviewer receives the completion criteria for the pattern(s)
the chunk matches and must verify each criterion.

Example: if Menter writes a Flask route handler, the reviewer checks:
- Route registered?
- Auth present?
- Input validated?
- JSON response?
- Error handling?
- Test specified?

### 4.3 Chunking

Menter does not write the entire implementation in one shot. It builds in
chunks. A chunk is defined as:

**A single file or a set of related functions that form one complete unit
of work.**

The chunk boundary is determined by:
- Menter's FINAL_JSON includes `"files_planned": ["path/to/file1.py", ...]`
- Each file is one chunk
- If a file exceeds 300 lines of new code, Menter must split it into
  logical sections and submit each section separately

Menter's prompt includes: "Build one chunk (file). Self-check against
universal rules. Submit it for review before proceeding to the next."

### 4.4 Sequential Review Process (Three-Pass)

Review is sequential, not parallel. This mirrors Eric's manual process
with Claude and ChatGPT, where each reviewer builds on the previous one's
work and consensus is reached through back-and-forth, not by a third-party
judge.

**Reviewer assignment:**
- Reviewer A = the less competent model (catches obvious issues first)
- Reviewer B = the more competent model (builds on A, finds deeper issues)

Which gateway is A and which is B is configurable per project. The
pipeline does not assume — it reads the assignment from the pattern
catalog or config.

**The three-pass process:**

```
PASS 1 — Reviewer A (first pass, fresh eyes)
  Input:  chunk diff + L1 results + pattern criteria + directive
  Output: review_a (findings, checks_passed, checks_failed)
  Role:   Catch obvious issues. No knowledge of B's perspective.

PASS 2 — Reviewer B (second pass, builds on A)
  Input:  chunk diff + L1 results + pattern criteria + directive
          + Reviewer A's output (review_a)
  Output: review_b (findings, checks_passed, checks_failed,
          items_missed_by_a, disagreements_with_a)
  Role:   Find what A missed. Confirm or challenge A's findings.
          B sees everything A sees, plus A's conclusions.

PASS 3 — Reviewer A (consensus pass)
  Input:  chunk diff + L1 results + pattern criteria + directive
          + own review_a
          + Reviewer B's output (review_b)
  Output: final_verdict: APPROVED or CHANGES_REQUESTED
          + consensus_summary (what both agree on)
          + dissent (if A disagrees with B, with evidence)
          + revision_directive (actionable feedback to Menter)
  Role:   Accept B's findings or push back with evidence.
          Deliver one consolidated revision directive to Menter.
          This is the single voice Menter hears.
```

**Why this is better than parallel review:**

| Problem with parallel | Solved by sequential |
|----------------------|----------------------|
| Both miss the same blind spot | B sees what A found, can find deeper issues |
| Disagreement with no judge | Consensus reached through back-and-forth in pass 3 |
| Two conflicting revision lists | A delivers one consolidated directive |
| No one builds on prior findings | B explicitly builds on A's review |
| "Who decides consensus?" | A decides, with evidence — or concedes to B |

**Consensus outcomes from Pass 3:**

- **APPROVED** — both A and B found the chunk acceptable. A delivers
  approval. Chunk incorporated.
- **CHANGES_REQUESTED** — A and B agree changes are needed. A delivers
  one consolidated revision directive to Menter. Menter revises.
- **DISAGREEMENT** — A disagrees with B's findings and has evidence.
  A's evidence is recorded. If A's pushback is substantive (not just
  "I disagree"), the chunk goes to ESCALATE for Eric to decide.
  If A concedes (no evidence to push back), B's findings stand.

### 4.5 Revision Cycle

When CHANGES_REQUESTED:
1. Menter receives the consolidated revision directive from Reviewer A
2. Menter revises the same chunk
3. New diff captured, L1 checks re-run
4. Three-pass review repeats (A → B → A consensus)
5. Max 3 revision cycles per chunk
6. If max exceeded → ESCALATE to Eric

### 4.6 Reviewer Authority

Reviewers can:
- APPROVE a chunk (it proceeds)
- Request CHANGES (Menter must revise)
- ESCALATE to Eric (when the chunk is fundamentally wrong)

Reviewers cannot:
- Write code themselves
- Skip checks (every criterion must be explicitly checked)
- APPROVE with failing L1 universal checks
- APPROVE their own output (Menter's self-report is not evidence)
- Override universal criteria (these are non-negotiable)

### 4.7 Incorporation

When Reviewer A delivers APPROVED consensus:
- The chunk stays in the working tree (Menter already wrote it)
- The pipeline records the approval in the DB
- Menter proceeds to the next chunk

When all chunks are complete:
- Pipeline runs full test suite
- Pipeline proceeds to VERIFICATION phase (L1 isolated + L2 semantic)

## 5. Knowledge Base Integration

### 5.1 Lessons from Prior Reviews

The CIS knowledge base contains sessions where Claude and ChatGPT reviewed
each other's code. Key patterns extracted from those sessions that inform
the reviewer prompts:

**From Claude (claude_export):**
- "Before execution: proposed action with explicit success criteria.
  Not just 'run this command' but 'run this command, expected output is X,
  failure looks like Y.'"
- "After execution: Hermes returns the actual terminal output. You paste
  it to Claude or ChatGPT for verification against the success criteria."
- "Hermes executing work proposed by Claude/ChatGPT creates a verification
  gap. We need a practice where Hermes reports back in a way that Claude
  and ChatGPT can audit."

**From ChatGPT (chatgpt_export):**
- "A Final Directive is not just a summary. It is the handoff object
  between deliberation and execution. It must answer: What did we decide?
  What exactly should happen next? What is out of scope? What proves it
  is done? What evidence must Hermes return?"
- "Hermes executes only that action. Hermes returns proof. Claude and/or
  ChatGPT audit the proof. You approve the next step."

**From R1/Reviewer sessions:**
- "Summaries are not accepted. RUN all gates. Paste raw output for each —
  COMMAND, full OUTPUT, exit code."
- "COMPLETE status is withdrawn until gates exist, run, and pass with
  pasted evidence."

### 5.2 Reviewer Prompt Construction

Reviewer prompts for code review include:
1. The chunk diff (raw, not summarized)
2. L1 universal check results (raw command output)
3. The relevant pattern and its completion criteria
4. The directive excerpt for this chunk
5. Past review findings from the knowledge base for similar patterns
6. Instruction: "Check each completion criterion. APPROVED only if all
   pass. CHANGES_REQUESTED with specific list of what failed. Summaries
   are not accepted — cite the specific line or check that failed."

### 5.3 Knowledge Feedback Loop

When a reviewer finds a bug, that finding is stored as a trajectory in
the spine. Future reviewer prompts include prior findings for similar
patterns, so the same class of bug is caught earlier.

This creates a learning system: the knowledge base accumulates review
findings, and each new review benefits from prior findings.

## 6. Database Schema

### 6.1 New Table: code_review_chunks

```sql
CREATE TABLE IF NOT EXISTS code_review_chunks (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    chunk_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    diff_text TEXT DEFAULT '',
    l1_results TEXT DEFAULT '',              -- JSON: universal L1 check results
    -- Three-pass sequential review
    review_a_pass1 TEXT DEFAULT '',          -- Reviewer A first pass output
    review_b_pass2 TEXT DEFAULT '',          -- Reviewer B second pass (sees A's output)
    review_a_consensus TEXT DEFAULT '',      -- Reviewer A consensus pass (sees B's output)
    final_verdict TEXT DEFAULT 'PENDING',   -- APPROVED, CHANGES_REQUESTED, ESCALATE
    revision_directive TEXT DEFAULT '',     -- Consolidated feedback to Menter
    revision_number INTEGER DEFAULT 1,
    incorporated INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE(run_id, chunk_number, revision_number)
);
```

### 6.2 Reviewer Assignment Config

Which gateway is Reviewer A (first pass) and which is Reviewer B (second
pass) is stored in the pattern catalog or agents_static.yaml:

```yaml
code_review:
  reviewer_a: "review1"    # less competent — first pass
  reviewer_b: "review2"    # more competent — builds on A
```

This is configurable per project. The pipeline reads it — never hardcodes.

### 6.3 New States

```
CODE_REVIEW_GATE — Menter is building, reviewers are checking chunks
PATTERN_CATALOG  — Brain is generating the pattern catalog
```

### 6.4 Pipeline State Machine Addition

After ERIC GATE approval:
```
ERIC_GATE (approved)
    ↓
PATTERN_CATALOG (Brain generates catalog, reviewers validate)
    ↓
CODE_REVIEW_GATE (Menter builds chunks, reviewers check each)
    ↓
VERIFICATION (final L1 + L2)
```

## 7. Chunk Size Parameters

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| Max lines per chunk | 300 | Large enough for a complete function or route, small enough for a reviewer to read thoroughly |
| Max files per chunk | 1 | One file at a time — reviewer sees the complete context |
| Max revisions per chunk | 3 | Prevents infinite revision loops |
| Max chunks per run | 20 | Prevents runaway builds; if more needed, split the directive |

These are configurable per project via the pattern catalog.

## 8. What This Prevents

The bugs found in pipeline_relay.py (commit 1ad844d) are the exact class
of failures this gate would catch:

| Bug | How Code Review Would Catch It |
|-----|-------------------------------|
| Verify auto-PASS on no verdict | Completion criteria: "error path must escalate, not default to success" |
| Menter output stored as drafter_output | Completion criteria: "output stored in correctly named column" |
| Rounds start as CONSENSUS_REACHED | Completion criteria: "default state is PENDING, not success" |
| Silent except: pass | Universal check: "no silent error swallowing" |
| Circuit breaker in-memory only | Completion criteria: "state persists across restarts" |
| Worktree tempdir leak | Universal check: "no orphan temp files" |

## 9. Resolved Questions

1. **Should Menter see the completion criteria before building?**
   Yes. Universal criteria are baked into Menter's system prompt — they
   are rules Menter follows, not a checklist applied after the fact.
   Project-specific criteria (from the pattern catalog) are also included
   in Menter's prompt so it knows what "done" looks like before it starts.
   Menter self-checks before submitting.

2. **Should reviewers see each other's output?**
   Yes — sequentially. Reviewer B sees A's output. Reviewer A sees B's
   output in the consensus pass. This is the three-pass design (§4.4).
   This is better than parallel review because B builds on A's findings
   and consensus is reached through back-and-forth, not by a judge.

3. **Who judges consensus when reviewers disagree?**
   Nobody judges from outside — consensus is reached through the process
   itself. Reviewer A delivers the final verdict after seeing B's review.
   If A has evidence to push back, the chunk escalates to Eric. If A
   concedes, B's findings stand. There is no third-party tie-breaker
   because the back-and-forth IS the consensus mechanism.

4. **What if a chunk doesn't match any pattern in the catalog?**
   The reviewer applies universal criteria only and notes in the review
   that no pattern match was found. The pattern catalog is updated to
   include the new pattern on the next catalog revision. This is not an
   error — it's how the catalog grows.

## 10. Provenance

The sequential three-pass review process is derived from Eric's manual
workflow with Claude and ChatGPT, as described in session on 2026-07-09:

> "I let the less competent model review, then fed that to the more
> competent to build upon and see maybe what the other didnt. lastly I
> gave the second review back to the less competent model for consensus
> or to push back when they had evidence. then the lesser but still
> competent model delivered the revision back to the Implementer."

This is more complete than parallel individual reviews because:
- Each reviewer builds on the previous one's work
- Consensus is reached through evidence-based back-and-forth
- Menter receives one consolidated directive, not conflicting lists
- No third-party judge is needed — the process produces consensus
