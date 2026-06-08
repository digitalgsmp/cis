# CIS Tier 6.1 — Closeout Trigger Design

Date: 2026-06-07
Status: REVISED — not yet committed
Tier: 6.1 (Pipeline Integration — design artifact)
Dependencies: Tier 0-5 complete

---

## 1. Trigger Model

Closeout is **STATE_WRITE-triggered**. The chain is:

```
VERIFY (all gates PASS) → STATE_WRITE (write to spine) → CLOSEOUT (finalize node)
```

STATE_WRITE is the sole gated durable spine-write path. No other process writes
verified pipeline state to the spine. Closeout fires only when STATE_WRITE
completes successfully — because closeout finalizes a node, and a node cannot be
finalized without verified truth in durable storage.

The STATE_WRITE script is invoked by `gate_closeout_complete.sh v2` (Tier 6.2)
on successful exit of all pre-STATE_WRITE gates. It is not invoked manually and
not invoked by the orchestrator. The gate runner is the sole trigger.

### Why not cron/watchdog as primary trigger

Cron/watchdog is passive only. It detects stale conditions (dirty git, failed
gates, missing closeout, exports older than threshold) and alerts. It does not
initiate STATE_WRITE or closeout. The primary trigger must be deterministic and
synchronous — gate runner exits 0 → STATE_WRITE runs immediately → closeout runs
immediately. A cron-based trigger introduces a time gap where state could change
between verification and write, violating determinism.

### Why not orchestrator-triggered

The orchestrator writes to Kanban and blackboard only (Tier 6.3 constraint).
It never writes durable state. The orchestrator does not know whether gates
passed — it only knows whether deliberation reached CONSENSUS or ESCALATE.
Verification is a separate concern.

---

## 2. STATE_WRITE Execution — Gate Ordering

### Corrected gate chain

The gate runner must NOT require final durable spine rows or export artifacts
before STATE_WRITE creates them. The ordering is: verify preconditions →
STATE_WRITE → regenerate exports → verify postconditions → closeout.

```
gate_closeout_complete.sh v2
  │
  ├─ PHASE 1: Pre-STATE_WRITE verification ─────────────────────
  │   ├── gate_git_state.sh              (Tier 1.1)
  │   ├── gate_no_secrets.sh             (Tier 1.4)
  │   ├── [optional: gate_service_health, gate_endpoint, gate_file_exists]
  │   └── [pipeline-transition gates]    (Tier 6.4 — verify Kanban card markers)
  │         ├── gate_research_artifact_present.sh
  │         ├── gate_proposal_schema_valid.sh
  │         ├── gate_review_round_valid.sh
  │         ├── gate_consensus_signal_valid.sh
  │         ├── gate_eric_approval_present.sh
  │         └── gate_implementation_artifact_present.sh
  │
  ├─ ANY PRE-GATE FAILS → STOP. No STATE_WRITE. Card → blocked.
  │
  ├─ ALL PRE-GATES PASS ─────────────────────────────────────────
  │     │
  │     └── state_write.py runs
  │           ├── inserts/updates workflow_runs row: status='COMPLETE'
  │           ├── inserts/updates deliberation_rounds rows
  │           ├── writes closeout manifest (Section 2.3 schema)
  │           └── exits 0
  │
  ├─ STATE_WRITE FAILS → STOP. No closeout. Card → blocked.
  │
  ├─ STATE_WRITE PASSES ─────────────────────────────────────────
  │     │
  │     ├── generate_all.py (regenerate exports from updated spine)
  │     │
  │     ├─ PHASE 2: Post-STATE_WRITE verification ───────────────
  │     │   ├── gate_export_agreement.sh   (Tier 5.6 — exports match manifest)
  │     │   └── gate_db_state.sh           (Tier 4.3 — spine rows exist)
  │     │         gate_db_state.py value workflow_runs result COMPLETE --where id <run_id>
  │     │         gate_db_state.py count deliberation_rounds <n> --where run_id <run_id>
  │     │
  │     └── ALL POST-GATES PASS ─────────────────────────────────
  │           │
  │           └── closeout.sh runs
  │                 ├── writes CLOSEOUT_<date>_<node>.md
  │                 ├── runs generate_all.py if not already done
  │                 └── logs completion
  │
  └── ANY POST-GATE FAILS → STOP. Card → blocked.
       Spine rows exist but closeout incomplete. Watchdog will detect.
```

### Why gate_db_state runs AFTER STATE_WRITE

`gate_db_state.sh` verifies that the spine contains the expected rows. Those
rows do not exist until STATE_WRITE creates them. Running it before STATE_WRITE
would always fail — the rows it checks for haven't been written yet. It is a
postcondition check: did STATE_WRITE actually write what it was supposed to?

### Why gate_export_agreement runs AFTER STATE_WRITE

Exports (AGENTS.md, HCP files) must include the updated spine state. Running
`generate_all.py` before STATE_WRITE would produce exports that don't reflect
the completed node. Exports must be regenerated after STATE_WRITE, and
`gate_export_agreement.sh` must run after that regeneration to confirm the
manifest matches.

### Evidence required in each phase

**Before STATE_WRITE (Phase 1):**

| Evidence | Source | Checked by |
|----------|--------|------------|
| Working tree clean or expected-only | gate_git_state.sh | Tier 1.1 |
| No secrets staged | gate_no_secrets.sh | Tier 1.4 |
| Pipeline stage markers present in Kanban card | pipeline-transition gates | Tier 6.4 |

**After STATE_WRITE (Phase 2):**

| Evidence | Source | Checked by |
|----------|--------|------------|
| Export manifest matches generated artifacts | gate_export_agreement.sh | Tier 5.6 |
| Spine has workflow_run row with result=COMPLETE | gate_db_state.sh | Tier 4.3 |
| Spine has expected deliberation_rounds count | gate_db_state.sh (count) | Tier 4.3 |

STATE_WRITE does not re-verify. It trusts the Phase 1 gate runner's exit code.
If any Phase 1 gate failed, the gate runner exits non-zero and STATE_WRITE
never runs. If STATE_WRITE fails, Phase 2 never runs and closeout never runs.

---

### STATE_WRITE actions

1. Insert or update `workflow_runs` row: status = 'COMPLETE', completed_at = now
2. Insert or update `deliberation_rounds` rows for each round
3. Update build-plan node status in spine (if tracked): node → COMPLETE
4. Write closeout manifest JSON (schema below)
5. Exit 0 on success, non-zero on any failure

### Closeout manifest schema

Written to `runtime/manifests/CLOSEOUT_<run_id>.json`. This is the structured
record that closeout.sh and the watchdog read. Schema:

```json
{
  "run_id": "string — unique run identifier (UUID or run-<timestamp>)",
  "node_id": "string — dependency graph node identifier (e.g., 'Tier 6.1')",
  "node_description": "string — human-readable node description",
  "timestamp_started": "ISO8601 — when gate_closeout_complete.sh v2 started",
  "timestamp_completed": "ISO8601 — when closeout.sh completed (null if failed)",
  "git_head": "string — full commit SHA at time of closeout",
  "gates": [
    {
      "name": "string — gate script name (e.g., 'gate_git_state.sh')",
      "command": "string — full command with arguments",
      "exit_code": "integer — 0 for PASS",
      "status": "string — PASS | FAIL | SKIP",
      "output_excerpt": "string — first 500 chars of gate stdout"
    }
  ],
  "state_write": {
    "status": "string — PASS | FAIL",
    "rows_written_or_updated": "integer — number of spine rows affected",
    "error": "string — error message if FAIL, null if PASS"
  },
  "export": {
    "status": "string — PASS | FAIL | SKIP",
    "manifest_path": "string — path to EXPORT_MANIFEST.json"
  },
  "closeout_file_path": "string — path to CLOSEOUT_*.md (empty if closeout failed)",
  "final_git_status": "string — git status --short output at closeout",
  "next_action": "string — next action per dependency graph"
}
```

All fields required unless noted as nullable. `gates` array includes every
gate that was configured to run, including skipped gates (status=SKIP).
`state_write.error` is null on PASS. `closeout_file_path` is empty string
if closeout did not complete.

---

### Closeout artifact

Written to `session_handoffs/CLOSEOUT_<YYYYMMDD>_<NODE_DESCRIPTION>.md`.

Required content:
- Date, commit hash, run_id
- Tier/node completed
- What changed (artifacts created/modified)
- Verification results (which gates ran, PASS/FAIL — from manifest)
- git status at closeout
- Boundaries held
- Next action per dependency graph

---

## 3. Pipeline-Stage Gate Markers (Spec for Tier 6.4)

These markers are the **specification** that Tier 6.4 gate scripts implement
against. No marker rules may be invented during 6.4 implementation — only
these markers.

All markers are checked in the Kanban card body unless otherwise noted.
Kanban card ID is passed as `$CIS_KANBAN_CARD_ID` env var.

### 3.1 RESEARCH — `gate_research_artifact_present.sh`

**Required markers:**
```
## Research Artifact
```
Must be present. Content after the heading must be non-empty (at least one line
of non-whitespace text after the heading).

**PASS:** Heading present, content non-empty.
**FAIL:** Heading missing, or heading present but zero content below it.

### 3.2 DRAFT — `gate_proposal_schema_valid.sh`

**Required markers:**
```
## Proposal
```
Must be present. Must contain at minimum:
```
### Summary
```
Non-empty content.
```
### Recommendation
```
Non-empty content.

Optional sub-sections that do not affect PASS/FAIL: `### Analysis`, `### Risks`,
`### Alternatives`.

**PASS:** Proposal heading present, Summary and Recommendation present with
non-empty content.
**FAIL:** Proposal heading missing, or mandatory sub-section missing/empty.

### 3.3 REVIEW — `gate_review_round_valid.sh`

**Required markers:**
```
## Review
```
Must be present. Must contain exactly ONE of:
- `CONSENSUS_REACHED`
- `OBJECTIONS`
- `ESCALATE`

Signal matching is **case-insensitive** (`consensus_reached`, `OBJECTIONS`,
`Escalate` all match).

Signal markers must be **standalone tokens** — appearing on a line by themselves
or as the first word on a line, not embedded in incidental text. A Reviewer
output stating "we did not reach CONSENSUS_REACHED" does NOT trigger the signal
because `CONSENSUS_REACHED` is not a standalone token in that context.

If `CONSENSUS_REACHED`, must also contain exactly:
```
remaining_objections: none
```
The value `none` is case-insensitive (`none`, `None`, `NONE` all pass).
Does NOT accept `0`, `[]`, or any other variation. The canonical Reviewer
output contract, enforced by the orchestrator's `normalize_review_section`,
writes `remaining_objections: none` to Kanban cards.

If `OBJECTIONS`, must contain at least one line starting with `- ` (bullet
point) after the OBJECTIONS header. Only dash bullets (`- `) are accepted per
the Reviewer prompt contract.

**PASS:** Review heading present, exactly one standalone signal present, required
sub-fields present for that signal.
**FAIL:** Heading missing, zero or multiple signals, signal embedded in text
(not standalone), required sub-field missing or incorrect value.

### 3.4 CONSENSUS — `gate_consensus_signal_valid.sh`

**Required markers:**
```
CONSENSUS_REACHED
remaining_objections: none
requires_eric_review: true
```

All three lines must appear. Order is not enforced — they may appear anywhere
within the Review section.

`CONSENSUS_REACHED` matching is **case-insensitive** and must be a **standalone
token** (per §3.3 standalone rule). This gate and `gate_review_round_valid.sh`
use identical matching logic for `remaining_objections`.

`remaining_objections` value: exactly `none` (case-insensitive: `none`, `None`,
`NONE` all pass). Does NOT accept `0`, `[]`, or any other variation.

The value `true` for `requires_eric_review` is case-insensitive (`true`, `True`,
`TRUE` all pass).

**`requires_eric_review: true` is permanent CIS policy for Tier 6.**

Eric Gate is the human authority boundary. No consensus path may skip Eric
review. This is not a configurable default, not an env var, and not a gate
parameter that a future tier could toggle off. Any future architectural change
that would allow a consensus path to bypass Eric Gate requires an explicit ADR
— it is a structural change to the human-in-the-loop boundary, not a gate
configuration adjustment.

The gate enforces this by failing if `requires_eric_review` is `false` or
missing. A Reviewer output that signals CONSENSUS_REACHED without
`requires_eric_review: true` is rejected.

**PASS:** All three lines present in Review section, requires_eric_review is
true (case-insensitive).
**FAIL:** Any line missing, or requires_eric_review is false.

### 3.5 ERIC_GATE — `gate_eric_approval_present.sh`

**Required marker:**
```
## Eric Gate
```
Must be present. The section must contain `APPROVED` on a line by itself
(surrounded by whitespace or line boundaries, not embedded in other text).

**What Tier 6 validates:** Marker presence only. The gate checks that the
`## Eric Gate` section exists and contains `APPROVED` on its own line. This is
a structural guardrail — it ensures the approval workflow was followed and the
marker was placed in the designated section.

**What Tier 6 does NOT validate:** Authorship or identity. The gate cannot
determine who wrote the marker. It cannot prove that Eric (as opposed to a
model, a script, or another process) placed the `APPROVED` marker. Identity
validation and write-level authorship enforcement belong to Tier 7 router
reclassification, where the router will block Drafter and Reviewer profiles
from writing to the `## Eric Gate` section.

In Tier 6, Eric places the marker by manually editing the Kanban card body or
issuing a FINAL_DIRECTIVE that the v4impl agent writes to the card. The gate
trusts the process — it does not prove the actor.

A model-generated `APPROVED` string elsewhere in the card body (e.g., inside
`## Proposal` text describing hypothetical approval) does NOT trigger a false
positive because the match is scoped to the `## Eric Gate` section:
```
## Eric Gate\n\nAPPROVED\n
```
or equivalent whitespace variants. `APPROVED` inside any other section is
ignored.

**PASS:** Eric Gate heading present, APPROVED present on its own line in that
section.
**FAIL:** Heading missing, or APPROVED not found in Eric Gate section.

### 3.6 IMPLEMENT — `gate_implementation_artifact_present.sh`

**Required markers:**
```
## Implementation
```
Must be present. Must contain at least one of:

1. A git commit hash matching `\b[0-9a-f]{7,40}\b` (7-40 hex chars)
2. A file path with change evidence: line matching `Created:` or `Modified:`
   followed by a path under `/mnt/projects/cis/`

**PASS:** Heading present, commit hash OR file change evidence present.
**FAIL:** Heading missing, or no commit hash and no file evidence.

### 3.7 VERIFY — handled by `gate_closeout_complete.sh v2`

Not a separate gate. The gate runner itself is the VERIFY stage. All gates
chained in sequence across two phases (pre-STATE_WRITE, post-STATE_WRITE).
Exit 0 = VERIFY PASS. Exit non-zero = VERIFY FAIL.

### 3.8 STATE_WRITE — `gate_db_state.sh` (Tier 4.3, already exists)

Runs in Phase 2 (post-STATE_WRITE) only. Verifies that the spine contains the
expected rows after STATE_WRITE has written them:

```bash
gate_db_state.py value workflow_runs result COMPLETE --where id <run_id>
gate_db_state.py count deliberation_rounds <expected_count> --where run_id <run_id>
```

If these checks run before STATE_WRITE, they will always fail because the rows
do not exist yet. The corrected gate chain (Section 2 diagram) places them
after STATE_WRITE.

---

## 4. What Counts as DONE

A build-plan node is DONE when all of the following are true:

| Condition | Verified by | Phase |
|-----------|-------------|-------|
| Working tree clean (or expected-only) | gate_git_state.sh | Pre |
| No secrets staged | gate_no_secrets.sh | Pre |
| Pipeline stage markers present in Kanban card | pipeline-transition gates | Pre |
| STATE_WRITE has written results to spine | state_write.py exit 0 | Mid |
| Export manifest matches generated artifacts | gate_export_agreement.sh | Post |
| Spine contains expected rows | gate_db_state.sh | Post |
| Closeout artifact exists in session_handoffs/ | gate_file_exists.sh | Post |
| Closeout manifest written to runtime/manifests/ | gate_file_exists.sh | Post |
| AGENTS.md reflects completed node | Manual or generate_all.py run | Post |

A node that meets all conditions is DONE and may be committed.

---

## 5. Failure Handling

### Pre-STATE_WRITE gate failure (Phase 1)

Any gate exits non-zero → `gate_closeout_complete.sh v2` stops immediately.
STATE_WRITE does not run. Closeout does not run.

The Kanban card status is set to `blocked`. The failure reason is appended
to the card body under:

```
## Verification Failure
Phase: pre-STATE_WRITE
Gate: <gate_name>
Exit: <exit_code>
Output: <first 500 chars of gate output>
```

### STATE_WRITE failure

If `state_write.py` exits non-zero, Phase 2 does not run. Closeout does not
run. The failure is appended to the Kanban card body. The node state in spine
remains at its previous value (not updated to COMPLETE). The closeout manifest
is NOT written (STATE_WRITE writes it — if STATE_WRITE fails, no manifest
exists).

### Post-STATE_WRITE gate failure (Phase 2)

Spine rows exist (STATE_WRITE succeeded) but a postcondition check failed.
Examples: gate_db_state finds wrong count, gate_export_agreement finds hash
mismatch. Closeout does not run. The card is set to `blocked`. The failure
is logged to the card body under `## Verification Failure` with phase
`post-STATE_WRITE`.

Spine rows written by STATE_WRITE are NOT rolled back on Phase 2 failure.
STATE_WRITE committed durable state. The failure is a verification gap,
not a data corruption. The watchdog will detect the incomplete closeout.

### Cron/watchdog detection (passive only)

A cron job (Tier 6.x, separate from closeout trigger) checks:
- Nodes in spine marked COMPLETE but with no closeout manifest → ORPHANED_WRITE
- Nodes in spine not DONE with no active Kanban card in `running` or `todo` → STALE
- git working tree dirty beyond threshold → DIRTY
- Export manifest older than AGENTS.md → STALE_EXPORT
- Last closeout older than last commit → MISSING_CLOSEOUT

The watchdog alerts Eric. It does NOT trigger STATE_WRITE, closeout, or any
state mutation.

---

## 6. Eric Gate Representation

### Tier 6 scope: marker validation, not identity proof

The `## Eric Gate` section is a designated region in the Kanban card body.
The `gate_eric_approval_present.sh` script validates that the section exists
and contains the `APPROVED` marker on its own line.

This is **marker presence validation** — structural, not identity-based.
It verifies the workflow was followed (Eric Gate section exists, marker
placed). It does not and cannot verify authorship.

### What the gate checks

- `## Eric Gate` heading exists in the Kanban card body
- `APPROVED` appears on its own line within that section
- The match is scoped to the section — `APPROVED` in any other section is ignored

### What the gate does NOT check (deferred to Tier 7)

- Who placed the marker
- Whether the marker was model-generated
- Whether the marker originated from a Drafter/Reviewer write
- Whether the marker was placed by an authorized process

### Placement mechanisms (Tier 6)

- Eric manually edits the Kanban card body via `hermes kanban cards edit`
- Eric issues a FINAL_DIRECTIVE that the v4impl agent writes to the card
- (Future Tier 7: Eric clicks `/approve` in browser UI — router enforces write authority)

### Anti-spoofing (Tier 6 scope)

The section-scoped match prevents a Drafter proposal saying "Eric should
approve this" from triggering a false positive, because `APPROVED` in the
`## Proposal` section is not in the `## Eric Gate` section.

Tier 7 router reclassification adds write-level enforcement: Drafter and
Reviewer profiles are structurally blocked from writing to the `## Eric Gate`
section. Until then, the section-scoped match is a structural guardrail, not
an identity proof. Tier 6 is explicit about this limitation.

---

## 7. Explicitly Out of Scope

- Implementation of any code (6.2, 6.3, 6.4, 6.5)
- STATE_WRITE script implementation (state_write.py)
- closeout.sh implementation
- Orchestrator modification or refactor
- Kanban read/write integration (orchestrator Kanban claims)
- Spine schema changes
- Tier 7 router reclassification
- Browser UI for Eric Gate
- AGENTS.md or HCP generation changes
- ADR-SEED-009 (project isolation model)
- Tier 5.7 stale folder cleanup
- Judge implementation (gated on Tier 6)
