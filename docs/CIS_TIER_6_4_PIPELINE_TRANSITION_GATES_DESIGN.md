# CIS Tier 6.4 — Pipeline-Transition Gate Scripts Design

Date: 2026-06-08
Status: PROPOSED — not yet committed
Tier: 6.4 (Pipeline Integration — stage-transition verification gates)
Dependencies: Tier 6.1 marker spec (canonical), 6.2 gate_closeout_complete.sh v2, 6.3 orchestrator Kanban integration

---

## 1. Gates to Build

Six standalone gate scripts under `tools/gates/`. Each validates one pipeline
stage against the Tier 6.1 marker specification.

| Script | Stage | What it checks |
|--------|-------|---------------|
| `gate_research_artifact_present.sh` | RESEARCH | `## Research Artifact` heading with non-empty content |
| `gate_proposal_schema_valid.sh` | DRAFT | `## Proposal` heading containing `### Summary` and `### Recommendation`, both non-empty |
| `gate_review_round_valid.sh` | REVIEW | `## Review` heading with exactly one signal (CONSENSUS_REACHED, OBJECTIONS, or ESCALATE) and required sub-fields |
| `gate_consensus_signal_valid.sh` | CONSENSUS | `## Review` heading containing `CONSENSUS_REACHED`, `remaining_objections: none`, and `requires_eric_review: true` |
| `gate_eric_approval_present.sh` | ERIC_GATE | `## Eric Gate` heading with `APPROVED` on its own line |
| `gate_implementation_artifact_present.sh` | IMPLEMENT | `## Implementation` heading with commit hash or file change evidence |

All marker rules are defined by the Tier 6.1 design (§3.1–§3.6). These gates
implement against that spec. No new marker rules are invented here.

---

## 2. Shared Interface

### Card ID Input

Each gate accepts the Kanban card ID via (checked in order):

1. `--kanban-card-id <id>` CLI argument
2. `$CIS_KANBAN_CARD_ID` environment variable

If neither is provided, the gate exits 2 and prints `ERROR: no card ID`.

### Card Body Read

All gates read the card body via:

```
hermes kanban show <id> --json
```

The JSON output is parsed to extract the `body` field. The JSON wraps card
data in a `"task"` key:

```
{"task": {"id": "...", "title": "...", "body": "...", ...}}
```

The body is the raw markdown string. Newlines are escaped as `\n` in JSON but
are real newlines after parsing. Section isolation operates on the parsed body
string, not the raw JSON.

### Kanban CLI Output Contract

The design depends on the `hermes kanban show <id> --json` output shape:

```json
{"task": {"id": "...", "title": "...", "body": "...", ...}}
```

The `body` field is extracted from the `task` key. If the Kanban CLI JSON schema
changes, all six gates require updating. This dependency is an accepted risk:
the Kanban CLI is a CIS-controlled component (not an external service) and
schema changes are gated by the same verification pipeline.

### No Writes of Any Kind

Gates do not:
- Write to the Kanban card body or status
- Write to the SQLite spine
- Modify any file on disk
- Call any LLM, API, or external service
- Execute any state-mutating command

They read a card body and report PASS, FAIL, or ERROR. Nothing else.

---

## 3. Section Isolation

Each gate isolates its target section from the card body using exact heading
matching.

### Heading Matching Rules

Headings are matched at the start of a line, after optional leading whitespace.
The match is **exact** and **case-sensitive**:

- `## Proposal` matches `## Proposal` — does NOT match `## Proposal Archive`
  or `## Proposal (Round 1)` or `## Proposals`
- `## Review` matches `## Review` — does NOT match `## Review Notes` or
  `## Reviewer Output`
- `## Eric Gate` matches `## Eric Gate` — does NOT match `## Eric Gate Notes`

The heading is the entire trimmed line: `line.strip() == "## Heading"`.

### Section Boundaries

A section begins at its `## ` heading and ends at the next top-level
`## ` heading (or end of body). Nested `### ` sub-headings within a
section remain part of that section.

Example:
```
## Proposal
Some text.
### Summary
Summary content.
### Recommendation
Recommendation content.

## Review          <-- section boundary, ends Proposal section
Review content.
```

The Proposal section includes everything from `## Proposal` through the line
before `## Review`. The `### Summary` and `### Recommendation` are inside
the Proposal section and are checked there.

### Extraction Algorithm

```
1. Split body into lines
2. Scan for heading line where line.strip() == "## TargetHeading"
3. If not found → FAIL (section missing)
4. From heading line + 1, collect lines until:
   a. line.strip().startswith("## ") → section boundary (stop, do not include)
   b. End of body
5. Collected lines are the section content
6. Strip leading/trailing blank lines from section content
7. If section content is empty → FAIL (section empty)
```

### Duplicate Heading Behavior

If a required heading (e.g., `## Proposal`) appears more than once in the card
body, the gate exits 1 with a clear duplicate-heading message:

  `FAIL: duplicate ## Proposal heading in card body`

The gate does NOT attempt to select between duplicate sections. Ambiguity
indicates a corrupted or multi-write card body and must be resolved before
verification can proceed.

This is a deterministic error, distinct from "section missing" (heading not
found at all) and "section empty" (heading found but no content). All six gates
enforce this rule for their respective target headings.

---

## 4. Per-Gate Validation Rules

### 4.1 gate_research_artifact_present.sh

**Target heading:** `## Research Artifact`

**Checks:**
1. Heading exists in card body (exact match per §3)
2. Section content after heading is non-empty (at least one non-whitespace line)

**PASS:** "PASS: Research Artifact section present with content"
**FAIL:** "FAIL: Research Artifact section missing" or "FAIL: Research Artifact section empty"

### 4.2 gate_proposal_schema_valid.sh

**Target heading:** `## Proposal`

**Checks:**
1. Heading exists
2. Within the Proposal section, `### Summary` sub-heading exists
3. Content after `### Summary` is non-empty (until next `### ` or `## ` heading or end of section)
4. Within the Proposal section, `### Recommendation` sub-heading exists
5. Content after `### Recommendation` is non-empty

**Sub-heading matching:** Match `line.strip() == "### Summary"` and
`line.strip() == "### Recommendation"` within the Proposal section only.
Exact, case-sensitive match.

**PASS:** "PASS: Proposal section valid — Summary and Recommendation present with content"
**FAIL:** "FAIL: Proposal section missing", "FAIL: Proposal missing ### Summary", "FAIL: Proposal missing ### Recommendation", "FAIL: Proposal ### Summary empty", or "FAIL: Proposal ### Recommendation empty"

### 4.3 gate_review_round_valid.sh

**Target heading:** `## Review`

**Checks:**
1. Heading exists
2. Within the Review section, exactly ONE signal is present:
   - `CONSENSUS_REACHED` (case-insensitive, as a standalone word or line)
   - `OBJECTIONS` (case-insensitive, as a standalone word or line)
   - `ESCALATE` (case-insensitive, as a standalone word or line)
3. If `CONSENSUS_REACHED`: section must also contain `remaining_objections: none`
   (case-insensitive for the value `none`: `none`, `None`, `NONE` all pass).
   Does NOT accept `0`, `[]`, or any other variation. The canonical Reviewer
   output contract writes `remaining_objections: none` to Kanban cards.
4. If `OBJECTIONS`: section must contain at least one line starting with `- `
   (bullet point with content)
5. If `ESCALATE`: signal present is sufficient

**Signal detection:** Search the Review section text (case-insensitive) for
each signal as a standalone word. A signal is "standalone" if it appears on
a line by itself (surrounded by whitespace/newlines) or as the first word on
a line. It does NOT match if embedded in other text (e.g., "We reached
CONSENSUS_REACHED after deliberation" — this is embedded).

**Multiple signals:** If more than one signal is found, FAIL with "multiple
signals detected."

**PASS:** "PASS: Review section valid — signal <X> with required sub-fields"
**FAIL:** "FAIL: Review section missing", "FAIL: no valid signal in Review", "FAIL: multiple signals in Review", "FAIL: CONSENSUS missing remaining_objections: none", "FAIL: OBJECTIONS missing bullet list"

### 4.4 gate_consensus_signal_valid.sh

**Target heading:** `## Review`

**Checks:**
1. Heading exists
2. Within the Review section, ALL THREE of:
   - `CONSENSUS_REACHED` (case-insensitive, standalone)
   - `remaining_objections: none` (case-insensitive for the value `none`: `none`,
     `None`, `NONE` all pass). Does NOT accept `0`, `[]`, or any other variation.
     Uses identical matching logic as `gate_review_round_valid.sh` §4.3.
   - `requires_eric_review: true` (case-insensitive for `true`; fails if `false` or missing)

**Permanent policy:** `requires_eric_review: true` is not configurable. The gate
fails if the value is `false` or the field is absent. Per 6.1 §3.4, any
architectural change to skip Eric review requires an explicit ADR.

**PASS:** "PASS: Consensus signal valid — all three markers present"
**FAIL:** "FAIL: Consensus signal invalid — missing <marker>" or "FAIL: requires_eric_review is false"

### 4.5 gate_eric_approval_present.sh

**Target heading:** `## Eric Gate`

**Checks:**
1. Heading exists
2. Within the Eric Gate section, `APPROVED` appears on a line by itself
3. `APPROVED` must be the only non-whitespace content on that line

**False positive prevention:**
- `APPROVED` in any other section (e.g., `## Proposal`) is ignored — only
  the `## Eric Gate` section is checked.
- `APPROVED` embedded in other text (e.g., "This should be APPROVED soon")
  does NOT match — it must be a standalone line.
- The match is case-sensitive: `APPROVED`, not `approved` or `Approved`.

**What this gate does NOT validate (per 6.1 §3.5):**
- Who placed the APPROVED marker
- Whether Eric vs. a model wrote it
- Authorship or identity

Tier 6 validates marker presence in the designated section. Identity
enforcement requires Tier 7 router write-level blocking.

**PASS:** "PASS: Eric Gate section present with APPROVED"
**FAIL:** "FAIL: Eric Gate section missing" or "FAIL: APPROVED not found in Eric Gate section"

### 4.6 gate_implementation_artifact_present.sh

**Target heading:** `## Implementation`

**Checks:**
1. Heading exists
2. Within the Implementation section, at least one of:
   - Git commit hash: `\b[0-9a-f]{7,40}\b` (7-40 lowercase hex chars)
   - File change evidence: line matching `Created:` or `Modified:` followed by
     a path under `/mnt/projects/cis/` (e.g., `Created: /mnt/projects/cis/runtime/orchestrator.py`)

**PASS:** "PASS: Implementation section present with artifact evidence"
**FAIL:** "FAIL: Implementation section missing" or "FAIL: no artifact evidence in Implementation section"

---

## 5. Exit Codes

| Code | Meaning |
|------|---------|
| 0 | PASS — all required markers present and valid |
| 1 | FAIL — required markers missing, empty, malformed, or ambiguous |
| 2 | ERROR — no card ID provided, card not found, JSON parse failure, `hermes kanban` unavailable |

This matches the existing Tier 1 gate exit code convention and is compatible
with `gate_closeout_complete.sh v2`.

---

## 6. Read-Only Boundary

All six gates are read-only validators. They:

- Read a Kanban card body via `hermes kanban show <id> --json`
- Parse the body
- Check for markers
- Print PASS, FAIL, or ERROR
- Exit with the appropriate code

They do NOT:
- Write to Kanban (no body updates, no status changes)
- Write to the SQLite spine
- Modify any file on disk
- Call any LLM, API, or external service
- Execute any state-mutating command
- Create, delete, or modify Kanban cards

---

## 7. Test Plan

### 7.1 Passing fixture

Create a Kanban card with all valid markers:

```
## Research Artifact
Evidence collected.

## Proposal
### Summary
A valid summary.
### Recommendation
A valid recommendation.

## Review
CONSENSUS_REACHED
remaining_objections: none
requires_eric_review: true

## Eric Gate
APPROVED

## Implementation
Commit: 7295e92 — Fix keep_section swap
```

All six gates must return exit 0 against this card.

### 7.2 Missing section fixture

Card with no `## Proposal` section. `gate_proposal_schema_valid.sh` must exit 1
with "FAIL: Proposal section missing."

### 7.3 Empty content fixture

Card with `## Research Artifact` heading but no content after it (blank lines
until next `## ` heading). `gate_research_artifact_present.sh` must exit 1
with "FAIL: Research Artifact section empty."

### 7.4 Wrong-section false positive fixture

Card with `APPROVED` in `## Proposal` section but NOT in `## Eric Gate`.
`gate_eric_approval_present.sh` must exit 1 — APPROVED in wrong section
does not count.

Card with `CONSENSUS_REACHED` outside `## Review` section.
`gate_consensus_signal_valid.sh` must exit 1.

### 7.5 Section isolation fixture

Card with `## Proposal Archive` heading (not `## Proposal`).
`gate_proposal_schema_valid.sh` must exit 1 — `## Proposal Archive`
does not match the exact heading `## Proposal`.

Card with `## Review Notes` heading (not `## Review`).
`gate_review_round_valid.sh` must exit 1.

### 7.5b Duplicate heading fixture

Card with two `## Proposal` headings, where the second has valid content:

```
## Proposal

## Proposal
### Summary
Valid summary.
### Recommendation
Valid recommendation.
```

`gate_proposal_schema_valid.sh` must exit 1 with "FAIL: duplicate ## Proposal
heading in card body." The gate must reject on ambiguity — not silently pass
the valid second section, and not silently fail because the first section is
empty.

Same test for `## Review`, `## Eric Gate`, and `## Implementation` with their
respective gates.

### 7.6 Duplicate Review signal fixture

Card with `## Review` containing both `OBJECTIONS` and `ESCALATE`.
`gate_review_round_valid.sh` must exit 1 with "multiple signals."

### 7.7 Malformed/missing Kanban JSON

Card ID that does not exist → `hermes kanban show` exits non-zero → gate exits 2.
Empty `$CIS_KANBAN_CARD_ID` and no `--kanban-card-id` → gate exits 2.
`hermes kanban` CLI not on PATH → gate exits 2.

### 7.8 Integration with gate_closeout_complete.sh v2

```
GATE_RESEARCH=1 GATE_PROPOSAL=1 GATE_REVIEW=1 \
GATE_CONSENSUS=1 GATE_ERIC=1 GATE_IMPLEMENT=1 \
  tools/gates/gate_closeout_complete.sh \
    --run-id test-6.4 \
    --kanban-card-id <fixture_id> \
    --node-id Tier 6.4 \
    --skip-export
```

Verify each gate in the chain produces the expected status in the JSON results
file. A passing fixture must produce PASS for all six. A failing fixture must
produce FAIL for the specific gate and stop the chain.

---

## 8. Files Expected to Change

| File | Change | Approximate lines |
|------|--------|-------------------|
| `tools/gates/gate_research_artifact_present.sh` | New | ~55 |
| `tools/gates/gate_proposal_schema_valid.sh` | New | ~70 |
| `tools/gates/gate_review_round_valid.sh` | New | ~80 |
| `tools/gates/gate_consensus_signal_valid.sh` | New | ~65 |
| `tools/gates/gate_eric_approval_present.sh` | New | ~65 |
| `tools/gates/gate_implementation_artifact_present.sh` | New | ~60 |

Total: 6 new files, ~395 lines. No existing files modified.

---

## 9. Explicitly Out of Scope

- Implementation of the six gate scripts
- STATE_WRITE or closeout implementation
- End-to-end pipeline run (6.5)
- Orchestrator modification
- Spine schema changes
- Eric Gate identity/authorship enforcement (Tier 7)
- ADR-SEED-009
