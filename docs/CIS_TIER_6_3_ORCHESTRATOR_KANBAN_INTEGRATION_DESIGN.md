# CIS Tier 6.3 — Orchestrator Kanban Integration Design

Date: 2026-06-07
Status: REVISED — not yet committed
Tier: 6.3 (Pipeline Integration — Kanban/blackboard read-write)
Dependencies: Tier 6.1 design, 6.2 implementation approved; orchestrator.py exists (Tier 0)

---

## 1. Exact Scope

Add Kanban read/write to `runtime/orchestrator.py` so it can consume a card
as input and write deliberation artifacts back to the card body. This is the
narrowest possible integration — no refactor, no spine, no closeout, no gates.

**In scope:**
- New `--kanban-card-id <id>` CLI argument
- Read card via `hermes kanban show --json` (title → topic, body → context)
- Write `## Proposal` section after each DRAFT round (validated per 6.1 spec)
- Write `## Review` section after each REVIEW round (normalized per 6.1 spec)
- Update card status: `claim` → `running`, `complete` → `done`, `block` → `blocked`
- Card body writes via direct SQLite (safe, no shell quoting of multi-line markdown)
- Raw topic mode preserved (no --kanban-card-id → existing behavior)

**Out of scope:**
- Spine inserts (no STATE_WRITE, no workflow_runs, no deliberation_rounds)
- Closeout logic (no closeout.sh invocation, no manifest writing)
- Gate execution (no gate scripts called by orchestrator)
- Eric Gate markers (no `## Eric Gate`, no `APPROVED`)
- Implementation markers (no `## Implementation`, no commit hashes)
- Refactor of the deliberation loop
- Blackboard file writes (Kanban card body IS the blackboard)

## 2. CLI / Interface Changes

### New argument

```
--kanban-card-id <id>    Read topic from Kanban card, write artifacts back
```

### Topic resolution (modified)

Current flow:
1. CLI positional arg → topic
2. stdin pipe → topic
3. Neither → error

New flow with `--kanban-card-id`:
1. `--kanban-card-id` provided → `hermes kanban show <id> --json`
2. Parse JSON: `.title` → topic, `.body` → context
3. Card must exist and be on the `cis-pipeline` board
4. If card read fails → error, exit non-zero

Without `--kanban-card-id`: existing behavior unchanged.

### Card status transitions

| Stage | Card status | CLI command |
|-------|-------------|-------------|
| Start (claim) | — → `running` | `hermes kanban claim <id>` |
| During deliberation loops | `running` (unchanged) | No status update |
| CONSENSUS_REACHED | `running` → `done` | `hermes kanban complete <id>` |
| ESCALATE | `running` → `blocked` | `hermes kanban block <id> "ESCALATE: max rounds reached"` |
| ERROR (API/IO failure) | `running` → `blocked` | `hermes kanban block <id> "ERROR: <message>"` |
| Card read failure | (unchanged) | No status update — card never claimed |

The orchestrator never sets `todo` status during internal loops. Status stays
`running` from claim through all DRAFT/REVIEW rounds. `todo` would only be set
if the orchestrator supported a `--single-round` mode that stops with work
remaining — that is not in 6.3 scope.

## 3. Marker Output

### 3.1 Proposal marker determinism

**Approach: A — prompt requirement + validation, not content invention.**

The Drafter prompt is extended to require specific output structure:

```
Your response MUST include the following sections with markdown headings:

### Summary
<concise summary of the proposal>

### Recommendation
<your recommendation and reasoning>

You may include additional sections (### Analysis, ### Risks, etc.) but
### Summary and ### Recommendation are REQUIRED.
```

The orchestrator validates Drafter output before writing to the card:

1. Check that `### Summary` heading exists in Drafter output
2. Check that `### Recommendation` heading exists in Drafter output
3. Check that content after each heading is non-empty (at least one non-whitespace line)

If validation passes: write `## Proposal` section containing the full Drafter
output (all sections preserved, not just Summary/Recommendation).

If validation fails: do NOT write to card. Record failure reason. Treat as a
DRAFT phase error — return ERROR result, set card status to `blocked`, exit
non-zero. The failure message includes which required heading was missing.

### Written section format

```
## Proposal

<full Drafter output verbatim — only written if validation passes>
```

### 3.2 Review marker determinism

The orchestrator normalizes Reviewer output so `## Review` always contains
exactly one valid signal with required sub-fields. This is done by parsing
the Reviewer's raw text, extracting the signal, and constructing a
deterministic `## Review` section.

**Signal detection order (first match wins):**

1. If Reviewer output contains `CONSENSUS_REACHED` (case-insensitive, as a
   standalone word/line) → signal is CONSENSUS_REACHED
2. If Reviewer output contains `OBJECTIONS` followed by bullet lines (`- ...`)
   → signal is OBJECTIONS
3. If neither: fallback → signal is ESCALATE

**Normalized `## Review` section for CONSENSUS_REACHED:**

```
## Review

CONSENSUS_REACHED
remaining_objections: none
requires_eric_review: true

<full Reviewer output>
```

The sub-fields `remaining_objections: none` and `requires_eric_review: true`
are always written by the orchestrator when CONSENSUS_REACHED is detected.
They are NOT extracted from Reviewer text — the orchestrator asserts them.
This guarantees the 6.1 gate spec is satisfied regardless of Reviewer output
variation.

**Normalized `## Review` section for OBJECTIONS:**

```
## Review

OBJECTIONS
- <objection 1>
- <objection 2>
...

<full Reviewer output>
```

Objections are extracted from Reviewer output: lines starting with `- ` after
the OBJECTIONS header. If no bullet lines found after OBJECTIONS, the
orchestrator treats this as unclear signal → fallback to ESCALATE.

**Normalized `## Review` section for ESCALATE (fallback):**

```
## Review

ESCALATE
Reviewer output did not contain a valid consensus or objections signal.

<full Reviewer output>
```

**Validation before write:** The orchestrator verifies that the constructed
`## Review` section contains:

- Exactly one signal line (CONSENSUS_REACHED, OBJECTIONS, or ESCALATE)
- For CONSENSUS_REACHED: `remaining_objections: none` and
  `requires_eric_review: true` present
- For OBJECTIONS: at least one `- ` bullet line
- For ESCALATE: signal line present (no sub-field requirements)

If the constructed section fails validation (should not happen since the
orchestrator constructs it deterministically), treat as internal error —
exit non-zero.

### 3.3 Sections explicitly NOT written

- `## Eric Gate` — orchestrator does not impersonate Eric
- `APPROVED` — orchestrator does not approve
- `## Implementation` — orchestrator does not execute
- `## Research Artifact` — orchestrator does not do research (future Tier)

### 3.4 Write strategy: incremental, per-stage

Sections are written to the card body immediately after each stage completes
and passes validation. Not batched at the end.

- After DRAFT validation passes → write `## Proposal` to card body
- After REVIEW normalization passes → write `## Review` to card body

If the orchestrator crashes mid-run, partial markers exist on the card.
The card body after a crash may have `## Proposal` but no `## Review`, or
vice versa. Detectability table in Section 5.

### 3.5 Card body assembly

The orchestrator reads the current card body, strips any existing
`## Proposal` and `## Review` sections, appends new sections, and writes
back. All other content is preserved unchanged.

**Section stripping is scoped precisely:**

| Section heading | Stripped? | Reason |
|-----------------|-----------|--------|
| `## Proposal` | Yes | Orchestrator-owned — replaces with current round |
| `## Review` | Yes | Orchestrator-owned — replaces with current round |
| `## Context` | No | User/manual content |
| `## Eric Gate` | No | Eric-only section |
| `## Implementation` | No | v4impl section |
| `## Research Artifact` | No | Future Research gateway section |
| `## Verification Failure` | No | Gate runner diagnostic section |
| Everything else | No | Preserved as-is |

The stripping implementation matches headings case-sensitively and exactly:
`## Proposal` and `## Review`. It does NOT match sub-headings like
`### Summary` — only the top-level `##` headings the orchestrator owns.

**Strip algorithm:**
1. Split body into sections by `## ` heading boundaries
2. Remove any section starting with `## Proposal` or `## Review`
3. Reassemble remaining sections
4. Append new `## Proposal` or `## Review` section

## 4. Kanban Body Write Mechanism

### Problem

`hermes kanban` CLI has no body-update command. `create` sets the initial
body; `edit` edits results/summaries; `comment` appends comments. Multi-line
markdown cannot be safely passed as a shell-quoted `--body` argument even if
a command existed — shell quoting breaks on code blocks, backticks, and
special characters.

### Solution: direct SQLite body update

The Kanban database is at the well-known path defined by `HERMES_KANBAN_DB`
(default: `/mnt/projects/cis/data/kanban.db`). The `tasks` table has a
`body TEXT` column with no constraints.

**Body write:**

```python
import sqlite3

def write_card_body(card_id, body, kanban_db):
    conn = sqlite3.connect(kanban_db)
    conn.execute("UPDATE tasks SET body = ? WHERE id = ?", (body, card_id))
    conn.commit()
    conn.close()
```

This is the ONLY direct SQLite operation the orchestrator performs. It does
not read from this database, does not modify any other column, and does not
touch any other table. Body is passed as a bound parameter — no SQL injection,
no shell quoting, no escaping fragility.

**Card read:** Uses `hermes kanban show <id> --json` (not direct SQLite).
This reads through the Hermes CLI so the orchestrator sees the same view
Eric sees. JSON output is parsed with `json.loads()`.

**Status updates:** Use Hermes CLI:
- `hermes kanban claim <id>` → sets to `running`
- `hermes kanban complete <id>` → sets to `done`
- `hermes kanban block <id> <reason>` → sets to `blocked`

Status updates do NOT use direct SQLite — the Kanban CLI manages claim locks,
timestamps, and run records that direct SQL would bypass.

## 5. Role Boundaries

| Action | Orchestrator may | Must not |
|--------|-----------------|----------|
| Coordinate Drafter/Reviewer deliberation | Yes | — |
| Write `## Proposal` and `## Review` to card body | Yes — after validation | — |
| Strip own sections from card body | Yes — `## Proposal`, `## Review` only | Other sections |
| Set Kanban card status | Yes — claim/complete/block | — |
| Write `## Eric Gate` | No | NEVER |
| Write `APPROVED` | No | NEVER |
| Write `## Implementation` | No | NEVER |
| Mark durable DONE (spine) | No | NEVER |
| Execute FINAL_DIRECTIVE | No | NEVER |
| Claim Eric authority | No | NEVER |
| Invent proposal content | No | NEVER — validates, does not generate |

Kanban status is coordination only — not verified truth. `done` status on the
card means the orchestrator finished, not that Eric approved or that gates
passed.

## 6. Failure Behavior

### Kanban card read fails

- Card not found, board mismatch, or CLI error → print error, exit non-zero
- Card status NOT modified (card was never claimed)

### Kanban card body write fails (SQLite error)

- SQLite error (locked DB, disk full, etc.) → print error with exception message
- Card body left in last successfully written state
- Orchestrator exits non-zero
- Card status left as `running` (was claimed but write failed)

### Proposal validation fails

- Required heading (`### Summary` or `### Recommendation`) missing from
  Drafter output → print which heading is missing
- Card body NOT updated (no `## Proposal` written)
- Card status set to `blocked` with reason: "DRAFT validation failed: missing ### Summary"
- Orchestrator exits non-zero

### Review normalization produces ESCALATE fallback

- Reviewer output contains no valid signal → normalize to ESCALATE
- Write `## Review` with ESCALATE signal and explanation
- Set card status to `blocked`
- Exit code 5 (distinct from CONSENSUS exit 0)

### Deliberation reaches ESCALATE (max rounds)

- Normalize last Review as ESCALATE
- Write `## Review` with ESCALATE signal
- Set card status to `blocked` with reason: "ESCALATE: max rounds reached without consensus"
- Exit code 5

### Deliberation reaches CONSENSUS

- Normalize Review as CONSENSUS_REACHED with required sub-fields
- Write `## Review` with consensus signal
- Set card status to `done` (`hermes kanban complete`)
- Exit code 0

### Reviewer returns OBJECTIONS (loop continues)

- Normalize Review as OBJECTIONS with bullet list
- Write `## Review` with OBJECTIONS
- Card status stays `running` (no change)
- Loop continues to next DRAFT round

### Existing marker sections on card

- Read current card body before deliberation
- Strip existing `## Proposal` and `## Review` sections (and only those)
- Preserve all other content
- This is a fresh run — no assumptions about prior state

### Orchestrator crashes mid-run

- Card body contains partial markers (whatever was written before crash)
- Card status is `running` (claim was done)
- No durable state was written (no spine inserts)
- Eric can inspect the card body to see what completed

### Partial marker detectability

| Card state | Meaning |
|------------|---------|
| No `## Proposal`, no `## Review`, status `running` | Orchestrator claimed but crashed before DRAFT write |
| `## Proposal` present, no `## Review`, status `running` | Orchestrator crashed during/after DRAFT |
| `## Proposal` + `## Review` with OBJECTIONS, status `running` | Orchestrator between rounds (normal or crashed) |
| `## Proposal` + `## Review` with CONSENSUS, status `done` | Deliberation complete, awaiting Eric Gate |
| `## Proposal` + `## Review` with ESCALATE, status `blocked` | Deliberation exhausted, Eric review needed |

## 7. ESCALATE Exit Code

ESCALATE uses exit code **5**. CONSENSUS_REACHED uses exit code **0**.

| Result | Exit code |
|--------|-----------|
| CONSENSUS_REACHED | 0 |
| ESCALATE (max rounds) | 5 |
| ESCALATE (fallback — no valid signal) | 5 |
| ERROR (API failure, validation failure, IO error) | 1 |

Rationale: automation (cron, gate runner, future pipeline) can distinguish
clean consensus from escalation without parsing stdout. Exit 5 is distinct
from the gate runner exit codes (0-4) to avoid ambiguity.

## 8. Implementation Approach

### Helper functions added to orchestrator.py

```python
def read_kanban_card(card_id):
    """Return (title, body) from Kanban card via `hermes kanban show --json`."""

def write_card_body(card_id, body):
    """Write body to Kanban card via direct SQLite UPDATE."""

def update_card_status(card_id, action, reason=None):
    """Update card status: claim/complete/block via `hermes kanban` CLI."""

def strip_orchestrator_sections(body):
    """Remove only ## Proposal and ## Review sections. Preserve all others."""

def validate_proposal_sections(drafter_output):
    """Check ### Summary and ### Recommendation exist with non-empty content.
    Returns (passed, missing_headings)."""

def normalize_review_section(reviewer_output, objections):
    """Construct deterministic ## Review section with exactly one valid signal.
    Returns normalized markdown string."""
```

### Injection points in run_deliberation()

1. **After topic resolution:** if `--kanban-card-id`, read card via
   `read_kanban_card()`, set topic, claim card → `running`.

2. **After DRAFT complete + validation:** `validate_proposal_sections()` →
   if pass: `strip_orchestrator_sections()` + append `## Proposal` +
   `write_card_body()`. If fail: block card, exit 1.

3. **After REVIEW complete + normalization:** `normalize_review_section()` →
   `strip_orchestrator_sections()` + append `## Review` + `write_card_body()`.

4. **On CONSENSUS_REACHED:** card status → `done` via `complete`.

5. **On OBJECTIONS:** card status unchanged (`running`). Loop continues.

6. **On ESCALATE:** card status → `blocked` via `block`. Exit 5.

The deliberation loop logic does not change. Injection points are write-only
side effects with validation gating.

### Kanban database path

```python
KANBAN_DB = os.environ.get("HERMES_KANBAN_DB", "/mnt/projects/cis/data/kanban.db")
```

Configurable via `HERMES_KANBAN_DB` env var with sensible default.

## 9. Verification Plan

### 9.1 Test with canary Kanban card

1. Create test card:
   ```bash
   hermes kanban create "Test: orchestrator 6.3 integration" \
     --body "## Context\n\nManual context for test." \
     --board cis-pipeline --tenant cis-pipeline
   ```
2. Run orchestrator with `--kanban-card-id <id> --test`:
   ```bash
   python3 runtime/orchestrator.py --kanban-card-id <id> --test
   ```
3. Read card back, verify exact markers:
   - `## Proposal` section present → non-empty
   - Drafter output contains `### Summary` with non-empty content (verified by orchestrator before write)
   - Drafter output contains `### Recommendation` with non-empty content
   - `## Review` section present → contains exactly ONE of:
     - `CONSENSUS_REACHED` with `remaining_objections: none` and `requires_eric_review: true`
     - `OBJECTIONS` with at least one `- ` bullet
     - `ESCALATE` with explanation
   - Original `## Context` section preserved
   - Card status: `done` (if consensus) or `blocked` (if escalate/error)

### 9.2 Prove no spine writes

```bash
stat -c %Y data/cis_memory.db > /tmp/spine_mtime_before
python3 runtime/orchestrator.py --kanban-card-id <id> --test
stat -c %Y data/cis_memory.db > /tmp/spine_mtime_after
diff /tmp/spine_mtime_before /tmp/spine_mtime_after
# Must be identical — no spine writes occurred
```

### 9.3 Prove raw topic mode still works

```bash
python3 runtime/orchestrator.py "Test topic without Kanban" --test
# Must produce deliberation output to stdout
# Must NOT read or write kanban.db (verify via strace or DB mtime)
# Must exit with expected code (0 for consensus, non-zero for error)
```

### 9.4 Prove marker sections satisfy 6.1 gate specs

After a successful run with `--kanban-card-id`, manually verify:

**gate_proposal_schema_valid (6.1 §3.2):**
- `## Proposal` heading present in card body ✓
- `### Summary` present with non-empty content ✓
- `### Recommendation` present with non-empty content ✓

**gate_review_round_valid (6.1 §3.3):**
- `## Review` heading present in card body ✓
- Exactly ONE signal line present ✓
- If CONSENSUS_REACHED: `remaining_objections: none` present ✓
- If OBJECTIONS: at least one `- ` bullet present ✓

**gate_consensus_signal_valid (6.1 §3.4):**
- `CONSENSUS_REACHED` present in Review section ✓
- `remaining_objections: none` present ✓
- `requires_eric_review: true` present ✓

### 9.5 Prove exit codes

```bash
# CONSENSUS (if test topic reaches it)
python3 runtime/orchestrator.py --kanban-card-id <id> --test; echo $?
# Expected: 0

# ESCALATE (use topic designed to provoke disagreement)
python3 runtime/orchestrator.py --kanban-card-id <id> --test; echo $?
# Expected: 5
```

## 10. Files Expected to Change

| File | Change | Lines affected |
|------|--------|---------------|
| `runtime/orchestrator.py` | Add `--kanban-card-id` arg, 6 helper functions, 6 injection points, validation logic, Drafter prompt extension, Review normalization, exit code 5 for ESCALATE | ~120 lines added |
| `runtime/orchestrator_config.yaml` | Add `kanban_board: cis-pipeline` default | 1 line |

Total: 2 files, ~120 new lines. No new files. No deletion of existing code.

## 11. Explicitly Out of Scope

- Implementation (6.3 code)
- STATE_WRITE / closeout (separate tiers)
- Pipeline-transition gates (6.4)
- End-to-end pipeline run (6.5)
- Spine schema changes
- `## Research Artifact` section (no Research gateway in 6.3)
- `## Eric Gate` or `APPROVED` markers
- `## Implementation` section
- Orchestrator refactor or loop restructure
- Blackboard file writes (body is the blackboard)
- ADR-SEED-009
