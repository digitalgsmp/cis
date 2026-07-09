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

### 4.1 Chunking

Menter does not write the entire implementation in one shot. It builds in
chunks. A chunk is defined as:

**A single file or a set of related functions that form one complete unit
of work.**

The chunk boundary is determined by:
- Menter's FINAL_JSON includes `"files_planned": ["path/to/file1.py", ...]`
- Each file is one chunk
- If a file exceeds 300 lines of new code, Menter must split it into
  logical sections and submit each section separately

Menter's prompt includes: "Build one chunk (file). Submit it for review
before proceeding to the next."

### 4.2 Review Process Per Chunk

```
For each chunk:
  1. Menter builds chunk → submits with FINAL_JSON:
     {"role":"menter","status":"CHUNK_READY","file":"path","summary":"..."}
  2. Pipeline captures git diff for this chunk only
  3. Review1 and Review2 receive:
     - The chunk diff
     - The relevant pattern from PATTERN_CATALOG
     - The completion criteria for that pattern
     - The directive (what Menter was told to build)
  4. Each reviewer checks the diff against the completion criteria
  5. Reviewers emit FINAL_JSON:
     {"role":"reviewer","status":"APPROVED","summary":"...","checks_passed":[...],"checks_failed":[]}
     or
     {"role":"reviewer","status":"CHANGES_REQUESTED","summary":"...","checks_failed":[...]}
  6. If both APPROVED → chunk incorporated, proceed to next chunk
  7. If CHANGES_REQUESTED → Menter revises the same chunk (max 3 revisions)
  8. If max revisions exceeded → ESCALATE to Eric
```

### 4.3 Universal Checks (Always Applied)

Regardless of project, language, or pattern, every chunk is checked for:

1. **Compiles/imports** — does the code load without syntax errors?
2. **Existing tests pass** — do tests that passed before still pass?
3. **No secrets** — no hardcoded API keys, passwords, tokens
4. **No debug code** — no print() statements, commented-out code, TODO without owner
5. **Error handling** — exceptions are caught and handled, not silently passed
6. **No silent defaults** — no function that returns success without doing its job
7. **File exists and non-empty** — Menter claimed to write it; does it exist?
8. **Claims match diff** — if Menter said "added function X", does X appear in the diff?

These are deterministic L1 checks run by the pipeline before reviewers see
the chunk. Reviewers see the L1 results alongside the diff.

### 4.4 Pattern-Specific Checks

In addition to universal checks, each chunk is checked against the pattern
catalog. The reviewer receives the completion criteria for the pattern(s)
the chunk matches and must verify each criterion.

Example: if Menter writes a Flask route handler, the reviewer checks:
- Route registered?
- Auth present?
- Input validated?
- JSON response?
- Error handling?
- Test specified?

### 4.5 Reviewer Authority

Reviewers can:
- APPROVE a chunk (it proceeds)
- Request CHANGES (Menter must revise)
- ESCALATE to Eric (when the chunk is fundamentally wrong, not just incomplete)

Reviewers cannot:
- Write code themselves
- Skip checks (every criterion must be explicitly checked)
- APPROVE with failing L1 checks
- APPROVE their own output (Menter's self-report is not evidence)

### 4.6 Incorporation

When both reviewers APPROVE a chunk:
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
    l1_results TEXT DEFAULT '',         -- JSON: universal check results
    review1_status TEXT DEFAULT 'PENDING',  -- PENDING, APPROVED, CHANGES_REQUESTED, ESCALATE
    review2_status TEXT DEFAULT 'PENDING',
    review1_output TEXT DEFAULT '',
    review2_output TEXT DEFAULT '',
    revision_number INTEGER DEFAULT 1,
    incorporated INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE(run_id, chunk_number, revision_number)
);
```

### 6.2 New States

```
CODE_REVIEW_GATE — Menter is building, reviewers are checking chunks
PATTERN_CATALOG  — Brain is generating the pattern catalog
```

### 6.3 Pipeline State Machine Addition

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

## 9. Open Questions

1. Should the pattern catalog be regenerated when the codebase changes
   significantly, or is the initial catalog versioned and updated manually?
2. Should Menter see the completion criteria before building, or only
   after submitting (forcing it to self-check against unknown criteria)?
3. Should reviewers see each other's output before or after submitting
   their own review (to prevent anchoring bias)?
4. What happens when Menter's chunk doesn't match any pattern in the
   catalog? Auto-derive criteria, or escalate?
