# CIS Conflict Register
# Updated automatically — do not edit header manually
# Canonical path: /mnt/projects/cis/docs/CIS_CONFLICT_REGISTER.md

Purpose:
Track discovered contradictions, filesystem conflicts, naming collisions,
stale documentation, deferred bugs, and governance/runtime mismatches.
Any conflict not resolved immediately must be entered before session close.

Status values:
  OPEN       — identified, not yet resolved
  DEFERRED   — acknowledged, resolution scheduled
  RESOLVED   — fix confirmed and verified
  SUPERSEDED — made irrelevant by other architectural change

---

## 2026-04-30 19:00 — ADR-046 Identity Conflict Across Primer Stack

Status:    RESOLVED
Severity:  HIGH
Category:  Documentation / Governance

Conflict:
ADR-046 was assigned to Automation Reduction Requirement on 2026-04-30 but
three primer files (01_CURRENT_STATE.md, 04_ACTIVE_COMPONENTS.md,
07_KNOWN_RISKS.md) still referenced ADR-046 as Filesystem Governance.
ADR-047 is the correct number for Filesystem Governance.

Risk:
Future AI sessions would misattribute governance authority — citing ADR-046
as Filesystem Governance when it is Automation Reduction, causing contract
violations and incorrect build sequencing.

Observed During:
Session 2026-04-30 — primer stack review after dashboard ADR list screenshot
revealed mismatch between displayed ADR numbers and primer file content.

Immediate Action:
All five affected primer files corrected and re-issued.
Historical distillation (2026-04-29) left untouched — it accurately reflects
state at that date.

Required Resolution:
RESOLVED — corrections verified clean via grep across all output files.

---

## 2026-04-30 19:30 — Manifest Namespace Collision

Status:    DEFERRED
Severity:  HIGH
Category:  Filesystem / Naming / Governance

Conflict:
Three distinct manifest concepts share the bare noun "manifest" without
canonical namespace separation:
  - /mnt/projects/cis/logs/manifests/     — verification/session manifests
  - /mnt/projects/cis/runtime/manifests/  — origin unclear, pre-ADR-033
  - INGEST_ROOT/source_id/manifest.json   — per-source processing manifests

No config.py constants existed for any manifest path. All references were
hardcoded strings scattered across individual files.

Risk:
Future scripts or AI sessions may write to, read from, or reason from the
wrong manifest location. Once agents perform autonomous filesystem actions
this becomes a data integrity and audit failure risk.

Observed During:
Session 2026-04-30 — filesystem screenshot of /logs and /runtime revealed
two folders both named "manifests" with different purposes.

Immediate Action:
config.py updated with three named constants:
  VERIFICATION_MANIFEST_DIR
  RUNTIME_MANIFEST_DIR (flagged as governance question — do not write here)
  SOURCE_MANIFEST_NAME
session.py updated to import and use constants. Bare paths prohibited in
new code. runtime/manifests/ contents and origin not yet investigated.

Required Resolution:
ADR-047 Filesystem Governance and Canonicality must define:
  - manifest taxonomy (names, ownership, lifecycle, retention)
  - zone classification for runtime/manifests/
  - whether runtime/manifests/ should be renamed, archived, or deprecated
ADR-047_SCOPE_PREDRAFT.md written this session as input to that work.

Notes:
Do not move or delete runtime/manifests/ until ADR-047 is locked.

---

## 2026-04-30 19:45 — 2_CIS_REORIENTATION.md Not Updated After ADR-045 Progress

Status:    RESOLVED
Severity:  MEDIUM
Category:  Documentation / Governance

Conflict:
2_CIS_REORIENTATION.md stated "Next required build step is execution_jobs
table creation" and "ADR-045 — LOCKED / NOT BUILT" after Steps 1–4 were
partially or fully complete. The bak file and the live file were identical,
indicating the intended update was never saved.

Risk:
Any AI session starting from this file would believe ADR-045 had not begun,
potentially re-proposing already-completed work or skipping Step 4 patch
validation as a prerequisite.

Observed During:
Session 2026-04-30 — reorientation doc review at session start.

Immediate Action:
2_CIS_REORIENTATION.md rewritten using ChatGPT recommendation as base with
Claude corrections. Layer stack, current phase, ADR-045 status block, and
gotchas all updated. File issued for VM deployment.

Required Resolution:
RESOLVED — corrected file verified and issued.

---

## 2026-04-30 20:00 — Field 5 Verification Status Had No Automation Path

Status:    RESOLVED
Severity:  MEDIUM
Category:  Runtime / Human Middleware

Conflict:
Session close protocol requires Field 5 — Verification Status containing
manifest count, verification run count, and unresolved FAIL count. No
dashboard field existed for this. Human had been manually constructing and
pasting this data into the Notes field for approximately 10 session closes.

Risk:
Manual construction is error-prone and inconsistent. Data was being silently
lost into the Notes field rather than recorded as a structured named field
in the handoff file. Violates ADR-046 Automation Reduction Requirement.

Observed During:
Session 2026-04-30 — human reported the workaround during session close
automation discussion.

Immediate Action:
New GET /api/session/verification-status endpoint added to session.py.
Field 5 textarea added to SessionPanel in cis_dashboard.html — auto-populated
on panel mount, editable, displays CLEAN/FAIL indicator.
session/close POST now accepts and writes verification_status as a named
field in the handoff file.

Required Resolution:
RESOLVED — both files issued for VM deployment. Deploy and restart Flask
to activate.

---

## 2026-05-01 22:03 — ADR form auto-increment resets to ADR-020 after log

Status:    OPEN
Severity:  LOW
Category:  UI

Conflict:
After logging a decision, the ADR Number field resets to ADR-020 instead of next consecutive number.

Risk:
Operator logs ADR with wrong number without noticing.

Observed During:
2026-05-01

Immediate Action:
Fix ADR panel auto-increment logic in cis_dashboard.html

Required Resolution:
DEFERRED

Notes:
Non-blocking. Address during frontend modularization pass.

---

## 2026-05-03 23:09 — ADR-048 draft checksum whitespace sensitivity

Status:    OPEN
Severity:  LOW
Category:  ADR-048

Conflict:
Checksum hashes raw payload string only. Equivalent JSON with different whitespace or key ordering produces different checksums.

Risk:
Duplicate detection will miss semantic duplicates with formatting differences.

Observed During:
2026-05-04 during ADR-048 Phase 1 L3 audit

Immediate Action:
Defer to Phase 2 — normalize JSON payloads before hashing

Required Resolution:
DEFERRED

---

## 2026-05-04 20:50 — CIS Live rounds form session dropdown does not update without browser refresh

Status:    OPEN
Severity:  LOW
Category:  UI

Conflict:
Session dropdown in rounds form fetches session list once on load and does not re-fetch after a new session is opened. New sessions are invisible until browser refresh.

Risk:
Operator opens session, attempts to log round, selects wrong or missing session.

Observed During:
2026-05-04 operator observation

Immediate Action:
Re-fetch session list after successful session open in the same UI flow.

Required Resolution:
DEFERRED

---
