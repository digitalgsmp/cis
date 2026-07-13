# Code Review Gate Design

Session: 2026-07-09 (spec commits 06e8e8d, 7682ad1, 056a360)
Implementation: commit e44268f (658 lines in pipeline_relay.py)
Spec: `docs/SPEC_CODE_REVIEW_GATE.md` (REV-2)

## The Problem

Eric's insight: "I think this is the result of any LLM building
unaccountable to other LLM oversight. When I had to make Claude and
ChatGPT review each piece of code written, the implementer agent never
left shortcuts like this."

The CIS pipeline had the disease it was designed to cure. Menter built
pipeline_relay.py alone, with no code review, and left 10 "default to
success" bugs. The manual Claude/ChatGPT mutual review pattern that
Eric used never produced these shortcuts because each piece was checked
by a second model before acceptance.

## The Solution: Four-Part Design

### Part 1: Pattern Catalog (Project Onboarding)

When CIS starts on a new project, Brain reads the codebase and produces
a PATTERN_CATALOG.md. This is project-specific — not hardcoded CIS
patterns. It identifies:

1. Language and toolchain (Python/pytest, Go/go test, JS/jest, etc.)
2. Architectural patterns found in the code
3. Convention rules (naming, file org, error handling style)
4. Test convention
5. Completion criteria per pattern — what "done" looks like
6. List of files Menter will need to create or modify

The catalog is saved to `runtime/catalogs/PATTERN_CATALOG.md`, versioned
via git. Brain can update it on subsequent runs if new patterns are
introduced.

**Key insight**: the catalog makes CIS universal. Different codebases
have different patterns. The catalog is derived from the actual code on
disk, not from a library of examples. Each project gets assessed once,
same as a new developer joining a team and learning conventions.

**IMPLEMENTED**: `_read_codebase_overview()` scans project files (find,
language detection by extension, test file detection, git log). Brain
receives this overview + the approved directive and produces the catalog
with `files_planned` in FINAL_JSON.

### Part 2: Universal Rules (Baked Into Menter)

Universal criteria are not just a review checklist — they are part of
Menter's baseline behavior. The `MENTER_UNIVERSAL_RULES` constant (8
rules) is injected into Menter's prompt at build time. Menter self-checks
before submitting each chunk. The review catches what Menter missed —
but Menter is trying first.

The 8 universal rules:
1. Default to incomplete — no function returns success without completing its job
2. Handle errors explicitly — silent `except: pass` is forbidden
3. No secrets in code — use env vars or config files
4. No debug leftovers — no print(), no commented-out code, no TODO without context
5. Claims must match reality — self-report is a claim, not evidence
6. Clean up after yourself — no orphan temp files, no leftover artifacts
7. State must persist — in-memory only is not acceptable for state that matters
8. Validate before proceeding — empty or malformed output is an error, not silent success

**L1 Universal Checks** (run by pipeline, not Menter):
`_run_chunk_l1()` checks: file exists + non-empty, diff non-empty, no
hardcoded secrets, no silent except:pass, no print() debug, Python syntax
check (py_compile), existing test collection (pytest --co).

### Part 3: Sequential Three-Pass Review

**Eric's manual process that informed this design:**

> "I let the less competent model review, then fed that to the more
> competent to build upon and see maybe what the other didnt. lastly I
> gave the second review back to the less competent model for consensus
> or to push back when they had evidence. then the lesser but still
> competent model delivered the revision back to the Implementer."

Review is **sequential, not parallel**. This is better than parallel
review because:

| Problem with parallel | Solved by sequential |
|----------------------|----------------------|
| Both miss the same blind spot | B sees what A found, can find deeper issues |
| Disagreement with no judge | Consensus reached through back-and-forth in pass 3 |
| Two conflicting revision lists | A delivers one consolidated directive |
| No one builds on prior findings | B explicitly builds on A's review |
| "Who decides consensus?" | A decides, with evidence — or concedes to B |

**Reviewer assignment** (configurable per project):
- Reviewer A = the less competent model (catches obvious issues first)
- Reviewer B = the more competent model (builds on A, finds deeper issues)

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

PASS 3 — Reviewer A (consensus pass)
  Input:  chunk diff + L1 results + pattern criteria + directive
          + own review_a + Reviewer B's output (review_b)
  Output: final_verdict: APPROVED or CHANGES_REQUESTED
          + consensus_summary + dissent (if any) + revision_directive
  Role:   Accept B's findings or push back with evidence.
          Deliver one consolidated revision directive to Menter.
```

**Consensus outcomes:**
- APPROVED — both agree chunk is acceptable. A delivers approval.
- CHANGES_REQUESTED — both agree changes needed. A delivers one
  consolidated revision directive. Menter revises (max 3 cycles).
- DISAGREEMENT — A disagrees with B and has evidence. If substantive,
  chunk escalates to Eric. If A concedes (no evidence), B's findings stand.

### Part 4: Pattern-Specific Checks

Each chunk is checked against the pattern catalog's completion criteria
for the pattern(s) it matches.

**If a chunk doesn't match any pattern**: reviewers assess it on its
own merit. Eric's explicit guidance: "these are smart LLMs they'll
figure it out." Universal rules still apply, but pattern-specific criteria
are derived by the reviewers' own judgment for novel patterns. New
patterns discovered this way are added to the catalog on the next
revision, so the catalog grows organically from real code.

## Chunk Parameters

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| Max lines per chunk | 300 | Complete function/route, small enough to review thoroughly |
| Max files per chunk | 1 | Reviewer sees complete file context |
| Max revisions per chunk | 3 | Prevents infinite revision loops |
| Max chunks per run | 20 | Prevents runaway builds |

Configurable per project via the pattern catalog.

## Knowledge Base Integration

Reviewer prompts include prior findings from Claude/ChatGPT review
sessions, extracted from the spine FTS5 index. Key patterns found in
the knowledge base:

**Claude's success criteria pattern:**
"Before execution: proposed action with explicit success criteria. Not
just 'run this command' but 'run this command, expected output is X,
failure looks like Y.' After execution: Hermes returns the actual
terminal output. You paste it to Claude or ChatGPT for verification."

**ChatGPT's handoff object pattern:**
"A Final Directive is not just a summary. It is the handoff object
between deliberation and execution. It must answer: What did we decide?
What exactly should happen next? What is out of scope? What proves it is
done? What evidence must Hermes return?"

**R1's evidence standard:**
"Summaries are not accepted. RUN all gates. Paste raw output for each —
COMMAND, full OUTPUT, exit code. COMPLETE status is withdrawn until
gates exist, run, and pass with pasted evidence."

## Implementation Details (commit e44268f)

### New Code in pipeline_relay.py (658 lines, now 2,132 total)

- `MENTER_UNIVERSAL_RULES` constant — 8 rules injected into Menter's prompt
- `_run_chunk_l1()` — universal L1 checks for any code chunk (file exists,
  diff non-empty, no secrets, no silent except:pass, no print(), syntax
  check, test collection)
- `_read_codebase_overview()` — scans project: file list, languages by
  extension, test files, git log. Feeds to Brain for catalog generation.
- `_pattern_catalog()` — Brain phase: reads codebase, produces catalog,
  saves to disk, extracts `files_planned` from FINAL_JSON
- `_code_review_gate()` — orchestrator: iterates files, calls
  `_review_single_chunk` per file, checks for escalation between chunks
- `_review_single_chunk()` — the three-pass sequential review per chunk:
  Menter builds → L1 checks → A reviews → B reviews (sees A) → A consensus
  (sees B) → APPROVED or CHANGES_REQUESTED with revision loop

### New States

`PATTERN_CATALOG` — Brain is generating the pattern catalog
`CODE_REVIEW_GATE` — Menter is building chunks, reviewers are checking

### Database Schema (migration 0018)

```sql
CREATE TABLE code_review_chunks (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    chunk_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    diff_text TEXT DEFAULT '',
    l1_results TEXT DEFAULT '',
    review_a_pass1 TEXT DEFAULT '',        -- Reviewer A first pass
    review_b_pass2 TEXT DEFAULT '',        -- Reviewer B second pass (sees A)
    review_a_consensus TEXT DEFAULT '',    -- Reviewer A consensus (sees B)
    final_verdict TEXT DEFAULT 'PENDING',
    revision_directive TEXT DEFAULT '',
    revision_number INTEGER DEFAULT 1,
    incorporated INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE(run_id, chunk_number, revision_number)
);
```

### API Update

`runtime/api/relay.py` — Eric Gate approval now routes to `PATTERN_CATALOG`
instead of `EXECUTION`. The old single Menter execution phase is replaced
by the pattern catalog → code review gate → verification flow.

### Resolved Questions

1. **Should Menter see completion criteria before building?** Yes.
   Universal criteria are baked into Menter's system prompt. Project-
   specific criteria from the pattern catalog are also included. Menter
   self-checks before submitting.

2. **Should reviewers see each other's output?** Yes — sequentially.
   B sees A's output. A sees B's output in the consensus pass.

3. **Who judges consensus when reviewers disagree?** Nobody from outside.
   Consensus is reached through the process itself. A delivers the final
   verdict after seeing B's review. If A has evidence to push back, the
   chunk escalates to Eric. If A concedes, B's findings stand.

4. **What if a chunk doesn't match any pattern?** Reviewers assess it on
   its own merit. "These are smart LLMs they'll figure it out." New
   patterns are added to the catalog on the next revision.

## Worked Example: 7 Patterns in pipeline_relay.py

When auditing pipeline_relay.py (1,476 lines at time of audit), 7
distinct structural patterns were identified. Each has its own
completion criteria. This is the worked example of what a Pattern
Catalog looks like.

### Pattern 1: Phase Method

Each pipeline phase follows the same skeleton:
1. Print entry with phase name + round
2. Query prior phase output from DB
3. `_start_round()` — create deliberation round (PENDING)
4. `_pre_discovery()` — mandatory context injection
5. Build prompt (discovery + context + role + FINAL_JSON format)
6. `try: _call_agent(role, prompt)`
7. `except:` breaker → ERROR → complete round → trajectory → return
8. `_record_trajectory` → `_parse_final_json` → validate status
9. If invalid: failed trajectory → ESCALATE → return
10. `_update_trajectory_outcome(success)` → `_complete_round(CONSENSUS)`
11. `_set_run_status(next_phase)` → `await self._next_phase()`

### Pattern 2: DB Helper
### Pattern 3: Agent Dispatch
### Pattern 4: Validation Gate
### Pattern 5: Evidence Collector
### Pattern 6: State Persistence
### Pattern 7: Prompt Construction

(See SKILL.md pitfalls section for the completion criteria of each pattern
— they are the same criteria the Code Review Gate checks against.)

## End-to-End Test Results (commit 44cfd1c, 2026-07-09)

Run `run-fcb0058efcaa0f28-1783570097` — intent: "Add a health check
endpoint at /api/health that returns JSON with status ok and timestamp"

### Full Pipeline Trace

| Round | Phase | Signal | Output Size |
|-------|-------|--------|-------------|
| 1 | brain | CONSENSUS_REACHED | 3,439 chars |
| 2 | intent_review | CONSENSUS_REACHED | 2,062 chars |
| 3 | draft | CONSENSUS_REACHED | 4,002 chars |
| 4 | proposal_review | OBJECTIONS | 2,490 chars |
| 5 | draft (revision) | CONSENSUS_REACHED | 5,949 chars |
| 6 | proposal_review | CONSENSUS_REACHED | 3,173 chars |
| — | ERIC GATE | — | approved |
| 7 | pattern_catalog | CONSENSUS_REACHED | 6,683 chars |
| 8 | code_review | CONSENSUS_REACHED | 1,538 chars |
| 9 | verification | PENDING | (timed out) |

### Code Review Chunk Details

| Field | Value |
|-------|-------|
| Chunk | 1 (runtime/app.py) |
| Verdict | APPROVED |
| Revision | 1 (approved on first try) |
| Incorporated | Yes |
| Diff size | 1,998 chars |
| Review A pass 1 | 3,466 chars |
| Review B pass 2 | 4,817 chars |
| Review A consensus | 2,602 chars |

### What Each Reviewer Did

**Reviewer A (first pass):** Checked 12 pattern criteria — import
placement, function naming (api_ prefix), decorator style (inline
@app.route), section header (em-dash style), return convention
(jsonify), timestamp convention (ISO 8601 UTC), route placement (before
SPA catch-all), no DB dependency, auth unchanged, no existing behavior
modified, response shape matches directive, single file change. All 12
passed. Noted L1 "MISSING" flag was a false positive.

**Reviewer B (second pass):** Confirmed file exists on disk (48,808
bytes, 1,174 lines). Agreed with all of A's findings. Added 4
observations A missed: (1) measured section header widths numerically
(81 chars), (2) ran py_compile independently — got SYNTAX_OK, (3)
verified no untracked files created, (4) confirmed localhost bypass
covers health endpoint without auth changes.

**Reviewer A (consensus):** Accepted all 4 of B's additions.
Acknowledged "I should have included py_compile before approving" —
explicitly noted the gap in first pass. Delivered consolidated APPROVED
with no dissent.

### Menter's Actual Code (verified clean)

```python
from datetime import datetime, timezone

@app.route("/api/health")
def api_health():
    """Return service health status — no database dependency."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
```

11 lines added to runtime/app.py. Clean diff, no deletions, correct
placement, all universal rules followed. This is what a chunk looks like
when Menter self-checks against universal rules before submitting.

### Bugs Found During Testing

1. **SQLite CHECK constraint failure** — `workflow_runs.result` had
   CHECK constraint only allowing `CONSENSUS_REACHED`/`ESCALATE`/`ERROR`.
   The `PENDING` default from the default-to-success fix violated it.
   Same issue with `deliberation_rounds.reviewer_signal`. Fixed with
   migrations 0019 and 0020 (table rebuild pattern).

2. **FINAL_JSON parser grabbed wrong JSON block** — Draft's response
   contained an example payload `{"status": "ok", "timestamp": "..."}`
   earlier in the text. Parser returned that instead of the actual
   FINAL_JSON at the end. Draft correctly produced `PROPOSAL_READY` but
   the parser missed it, causing false escalation. Fixed: parser now
   collects all JSON candidates and prefers ones with `role` field.

## Provenance

The sequential three-pass review process is derived from Eric's manual
workflow with Claude and ChatGPT, as described in session on 2026-07-09:

> "I let the less competent model review, then fed that to the more
> competent to build upon and see maybe what the other didnt. lastly I
> gave the second review back to the less competent model for consensus
> or to push back when they had evidence. then the lesser but still
> competent model delivered the revision back to the Implementer. now
> that I write it out, I see may have been more complete than two
> individual reviews the container has where I dont really know who
> judges the consensus."
