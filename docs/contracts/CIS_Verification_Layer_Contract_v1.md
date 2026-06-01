# CIS Verification Layer Contract v1
# ADR-033
# Status: LOCKED
# Created: 2026-04-25
# Purpose: Define proof-of-work verification before any build action is considered complete

---

## Problem Statement

Claude and all LLMs are unreliable self-reporters of task completion. Repeated
discovery of placeholder content, omitted fields, hollow writes, and incomplete
work across build sessions is causing rework and eroding trust in session output.
Claude reporting "done" is not evidence that the work exists on disk or is complete.

A verification layer is required. No build action is considered complete until
it passes verification. This is Pre-Development Harness infrastructure.

---

## Scope

This contract governs every significant build action performed during a CIS
session, including:

- File writes (new files, updated files)
- Schema changes
- Knowledge record creation or modification
- Protocol updates
- Contract creation
- Reorientation file updates
- Session close operations

Excluded: exploratory conversation, planning discussion, ADR drafting prior to
logging. Verification triggers when something is declared built or written.

---

## Core Rule

**No build action advances until it is verified.**

Claude must not proceed to the next task until the previous task has passed
verification. "Passes verification" means: disk reality matches the completion
manifest. The human confirms this before work continues.

---

## Contract Components

### 1. Completion Manifest (Claude's Obligation)

At the end of every significant build action, Claude must produce a Completion
Manifest. This is not prose. It is a structured checklist of verifiable claims.

**Manifest schema:**

```
COMPLETION MANIFEST
Action:       [one-line description of what was done]
Timestamp:    [UTC time]

Files written:
  - path: [exact absolute path]
    exists: CLAIMED
    min_size: [expected minimum bytes or line count]
    key_markers: [list of strings that must appear in the file]

Fields updated:
  - file: [path]
    field: [field name or section heading]
    expected_value: [what it should now contain]

State changes:
  - [description of any DB record, status flag, or config change]

Placeholder check:
  - No file listed above may contain: "TODO", "...", "[placeholder]",
    "coming soon", or any empty required field.
```

Claude produces this manifest immediately after completing the action,
before any further conversation.

---

### 2. Deterministic Verifier (Layer 1 — Script)

A script (`cis_verify.py`) reads the most recent Completion Manifest and
checks each claim against disk reality.

**Checks performed:**

| Check | Method |
|-------|--------|
| File exists | `os.path.exists(path)` |
| File is not empty | `os.path.getsize(path) > 0` |
| File meets minimum size | compare to `min_size` in manifest |
| Key markers present | string search within file content |
| No placeholder strings | scan for forbidden strings list |
| Field value present | locate section/field in file and confirm non-empty |

**Output format:**

```
VERIFICATION REPORT
Manifest action: [action description]
Run time: [UTC]

PASS  File exists:          /path/to/file
PASS  File non-empty:       /path/to/file
PASS  Key marker found:     "## Session Start Protocol"
FAIL  Placeholder detected: "TODO" found at line 47 of /path/to/file
PASS  Field present:        "## Where the Build Is Right Now"

Result: FAIL — 1 check failed
Blocking: YES — do not advance until resolved
```

**Invocation:**

```bash
# From VM terminal
python3 /mnt/projects/cis/runtime/cis_verify.py --manifest /tmp/last_manifest.json

# Or via dashboard button (Phase 1 enhancement)
POST /api/verify/last
```

The script writes its report to:
`/mnt/projects/cis/logs/verification_log.md`
(appended, not overwritten — full history retained)

---

### 3. Semantic Verifier (Layer 2 — Local Model)

**Status: Planned. Activates when Layer 1 is stable.**

Layer 2 uses the local reasoning model (Qwen2.5-32B-Instruct via transformers+bnb)
to assess content quality beyond what a script can detect.

**Checks performed:**

- Is the content substantive or hollow? (thin summaries, empty sections)
- Are required sections present and populated?
- Does the content match what the manifest claims it is?
- Are there logical contradictions with known locked decisions?

**Trigger:** Layer 1 passes AND the action type is high-stakes
(contract creation, reorientation update, schema change, session close).

**Output:** appended to the same verification_log.md with source tagged
`[LAYER-2-SEMANTIC]`.

---

### 4. Dashboard Integration (Phase 1 Enhancement)

A "Verify Last Action" button in the CIS dashboard:

- Reads the last manifest written to `/tmp/last_manifest.json`
- Runs `cis_verify.py` as a subprocess
- Displays the pass/fail report inline
- Logs result to `verification_log.md`

Button location: Session panel, adjacent to session close controls.
Button state: disabled until a manifest exists for the current session.

---

## Session Protocol Integration

### Added to Session Start Protocol

Before any build work begins, confirm the previous session's verification
log shows no unresolved FAILs. If unresolved FAILs exist, resolve them
before opening new build work.

### Added to Session End Protocol

Claude must include a Verification Status field in session close fields:

```
Field 5 — Verification Status:
  Manifests produced: [count]
  Verifications run: [count]
  Unresolved FAILs: [count — must be 0 to close cleanly]
  Verification log: /mnt/projects/cis/logs/verification_log.md
```

A session may not close cleanly with unresolved verification failures.

---

## Reorientation File Mandate

`2_CIS_REORIENTATION.md` is subject to the verification contract.

**Rule:** The reorientation file must be updated at the close of any session
where system state changed. The update is a build action and requires:
1. A Completion Manifest from Claude
2. A Layer 1 verification pass before the session closes

The reorientation file is never self-reported as updated. It is verified.

---

## Failure Handling

| Failure type | Response |
|---|---|
| File does not exist | Claude re-executes the write and produces a new manifest |
| Placeholder detected | Claude fixes the content, rewrites, new manifest |
| Key marker missing | Claude inspects and corrects the file, new manifest |
| Layer 2 flags hollow content | Human reviews, decides to accept or flag for rework |
| Manifest never produced | Block treated as unverified — do not advance |

---

## Forbidden Strings (Placeholder Detection List)

The verifier scans all written files for these strings. Any match = FAIL:

```
TODO
...
[placeholder]
[coming soon]
[to be completed]
[fill in]
[insert]
PLACEHOLDER
TBD
```

This list is maintained in:
`/mnt/projects/cis/runtime/config.py` as `VERIFICATION_FORBIDDEN_STRINGS`

---

## Build Order

This contract is Phase PD infrastructure. Build sequence:

1. This contract (complete)
2. `cis_verify.py` — Layer 1 deterministic script
3. Manifest format locked into session workflow
4. Verification log confirmed writing to disk
5. Reorientation file updated and verified
6. Dashboard "Verify Last Action" button (Phase 1)
7. Layer 2 semantic verifier (Phase 1, after Layer 1 stable)

---

## What This Does Not Solve

- Claude hallucinating that a file was written when no write was attempted:
  Layer 1 catches this (file does not exist = FAIL)
- Claude writing a file with correct structure but wrong content:
  Layer 2 addresses this partially; human review is the final check
- Verification of actions taken on the VM outside of Claude's session:
  Out of scope — this contract governs Claude-directed build actions only

---

## Contract Authority

This contract is locked under ADR-033.
Changes require a new ADR.
This file lives at: /mnt/projects/cis/docs/contracts/CIS_Verification_Layer_Contract_v1.md
