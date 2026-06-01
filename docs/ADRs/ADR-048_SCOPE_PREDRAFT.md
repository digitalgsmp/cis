# ADR-048 — Staged Draft Intake Layer
# Status: PRE-DRAFT — scope only, not yet locked
# Updated: 2026-04-30
# Source: Multi-model architectural discussion (Claude + ChatGPT), 2026-04-30
# Do not implement until ADR-045 is fully closed.
# Lock via L1 + L3 verification before any build begins.

---

## Named Architectural Problem

"The human is still the API."

CIS has automated file generation (handoff, ADRs, logs) but not automated
field population. The human operator is still the transport layer between
AI-generated structured content and CIS canonical records.

For every session close, ADR proposal, task entry, conflict log, insight
record, and CIS Live round, the human must:
  - read AI output
  - mentally parse fields
  - copy each field individually into the correct dashboard form
  - submit

This is not a UX problem. It is an architectural gap.
The system has execution ownership (ADR-045) but no intake ownership.

This directly violates ADR-046 Automation Reduction Requirement:
repetitive field transfer is the single highest-burden manual action
remaining in the system.

---

## Governing Principle

AI drafts. CIS stages. Human approves. Runtime commits.

No AI model — platform or local — may write directly to canonical CIS
records. The staging layer is the mandatory buffer between AI output and
canonical state. Human approval is the promotion gate. Always.

This is the operational version of the governance/operational split
already established in CIS:

  Governance layer     — defines legal field structure, required approvals,
                         verification rules
  Staged Intake layer  — temporarily holds proposed structured data
  Operational Runtime  — saves approved data to DB/files
  Human Operator       — reviews and promotes
  AI/LLM               — drafts and proposes only

The staging layer solves both problems simultaneously:
  No direct AI write authority.
  No human copy-paste middleware.

---

## How It Fits the ADR Staircase

  ADR-044 — Operator abstraction
  ADR-045 — Execution ownership
  ADR-046 — Automation reduction governance
  ADR-047 — Filesystem governance
  ADR-048 — Staged draft intake      ← this ADR

ADR-048 is not a detour. It becomes the future interface between:
  platform models, local models, agents, governance, and canonical state.

The intake architecture scales forward. Whatever bridge is built now for
platform models becomes the same interface local workers and agents use later.

---

## Implementation Phases

### Phase 1 — Manual JSON Import (Platform Models, No Local Workers)

Platform models cannot directly POST to a local CIS dashboard.
The interim pattern:

  Platform model produces structured JSON block
  ↓
  Human copies one JSON block (not 5–20 fields)
  ↓
  Dashboard "Import Draft" button ingests it
  ↓
  CIS validates schema/type/required fields
  ↓
  CIS stages it — does not commit
  ↓
  Dashboard auto-populates correct form
  ↓
  Human reviews, edits if needed, approves
  ↓
  CIS commits to canonical DB/files

Minimum implementation:
  - "Import Draft JSON" input area on dashboard
  - /api/drafts/stage endpoint
  - Schema validation (type, required fields, source, timestamp)
  - Draft registry (DB table or structured file)
  - Dashboard form auto-population from staged draft
  - Approve/Reject controls

### Phase 2 — Downloads Folder Watcher

Eliminates the copy step. Human only clicks Download.

  Platform model generates cis_draft_*.json artifact
  ↓
  Human clicks Download in browser
  ↓
  File lands in ~/Downloads
  ↓
  cis_download_watcher.py detects matching filename
  ↓
  Watcher validates filename convention and schema
  ↓
  Watcher copies to /mnt/projects/cis/inbox/platform_drafts/
  ↓
  CIS stages it to /mnt/projects/cis/staging/drafts/
  ↓
  Dashboard shows "Draft ready — pending review"
  ↓
  Human opens dashboard, reviews, approves

Watcher rule: react ONLY to files matching cis_draft_*.json or cis_draft_*.md
The watcher must ignore all other Downloads content.
The watcher copies from Downloads — it does not operate from Downloads.
Downloads folder = untrusted external intake at all times.

### Phase 3 — Local Worker / API Direct Staging (Future)

Once local workers exist, they submit directly to /api/drafts/stage.
Still only into staged, unapproved state. Human approval gate unchanged.

  Local model / agent → POST /api/drafts/stage → staged → human approves

---

## Four-Zone Intake Path

  ~/Downloads/                              UNTRUSTED INTAKE
  ↓ watcher (cis_draft_* filter only)
  /mnt/projects/cis/inbox/platform_drafts/  QUARANTINE ZONE
  ↓ schema validator
  /mnt/projects/cis/staging/drafts/         REVIEWED CANDIDATES
  ↓ human approval
  canonical DB / docs / logs                APPROVED TRUTH

Required folders (create before Phase 2 build):
  mkdir -p /mnt/projects/cis/inbox/platform_drafts
  mkdir -p /mnt/projects/cis/staging/drafts
  mkdir -p /mnt/projects/cis/archive/imported_drafts
  mkdir -p /mnt/projects/cis/quarantine/rejected_drafts

---

## Draft Schema v1

{
  "schema": "cis.staged_draft.v1",
  "draft_type": "session_close",
  "source_model": "claude",
  "session_id": "optional — current active session id",
  "created_at": "2026-04-30T21:58:00",
  "sequence_hint": "session_close_after_adr045_step5",
  "fields": {}
}

The sequence_hint field allows CIS to detect out-of-sequence drafts and warn
before loading. It does not block — human decides whether to proceed.

---

## Draft Types and Required Fields

  session_close:
    session_focus, completed, next_steps, notes, verification_status

  adr:
    title, status (PROPOSED), context, decision, consequences

  task:
    title, description, priority, target_adr

  insight:
    title, category, content, source_session

  conflict:
    title, severity, category, conflict, risk, observed, action, resolution

  live_round:
    session_id, round_number, your_message, consolidated,
    gemini, claude, chatgpt

  handoff:
    session_focus, completed, next_steps, notes, verification_status

---

## Filename Convention (Phase 2)

  cis_draft_{type}_{YYYYMMDD}_{HHMM}_{source}.json

Examples:
  cis_draft_session_close_20260430_2158_claude.json
  cis_draft_adr_20260430_2200_chatgpt.json
  cis_draft_conflict_20260430_2145_claude.json
  cis_draft_insight_20260430_2210_claude.json

Watcher matches: cis_draft_*.json and cis_draft_*.md only.
All other filenames in Downloads are ignored.

---

## Draft Lifecycle and Status Values

  IMPORTED       — watcher detected and copied to inbox
  STAGED         — validated and placed in staging
  EDITED         — human modified the staged draft
  APPROVED       — human approved, pending commit
  COMMITTED      — runtime wrote to canonical DB/files
  REJECTED       — human rejected, moved to quarantine
  SUPERSEDED     — replaced by newer draft of same type
  OUT_OF_SEQUENCE — draft timestamp predates active session (warning state)

Versioning happens inside CIS, not in Downloads.
  imported → staged_v1 → (edit) → staged_v2 → approved → committed

---

## Dashboard Controls (Pending Drafts Panel)

For each staged draft:
  [View]
  [Edit]
  [Save New Version]
  [Load into Form]
  [Approve / Commit]
  [Reject]
  [Supersede]

Out-of-sequence warning:
  "This draft appears older than the current active session. Load anyway?"

---

## Conflict Logging Integration

cis_conflict_append.py is the current semi-automated backend utility.
Full automation path for conflict intake under ADR-048:

  Current (semi-automated):
    AI identifies conflict → AI provides CLI command → human runs it

  Phase 1 target:
    AI identifies conflict → AI produces cis_draft_conflict_*.json
    → human imports via dashboard → human approves → CIS appends register

  Phase 2 target:
    AI identifies conflict → watcher detects → CIS stages
    → human opens dashboard → clicks Approve → CIS appends register

  Future (CIS Live integration):
    CIS Live rounds tagged "conflict" or "deferred" auto-generate
    a staged draft conflict entry without human terminal action

---

## Priority and Sequencing

Do not begin ADR-048 implementation until ADR-045 is fully closed:
  - queue_worker.py patch confirmed canonical
  - Step 5 dashboard polling complete
  - Step 6 run_l2 complete
  - Step 7 cold start recovery validated
  - Step 8 FIFO enforcement validated

After ADR-045 closure, ADR-048 Phase 1 is the next build target.
ADR-047 Filesystem Governance may proceed in parallel during planning.

---

## Long Arc Context

Phase PD governance work was never the end goal.
It was the stabilization phase required before CIS could safely
rewrite and evolve itself.

The original problem became:
"How do we prevent a long-running AI-assisted system from collapsing
into drift, contradiction, hallucinated authority, hidden technical debt,
and human middleware chaos while it evolves?"

ADR-048 is the missing operational bridge between governance maturity
and runtime usability. Once intake is stabilized, the system can:

  Ingest 15 SESSION_INSIGHT_RECORDs (identified/mapped — not yet processed)
  ↓
  Structure, deduplicate, extract governing principles
  ↓
  Identify abandoned assumptions
  ↓
  Reconstruct authoritative CIS build plan from stabilized governance position
  ↓
  Resume application development under governed execution
  ↓
  Wire local workers, agents, orchestration, sovereign inference

The 15 SESSION_INSIGHT_RECORDs contain the architectural reasoning that
produced the entire Phase PD governance shift. Their ingestion is deferred
until the execution layer (ADR-045) and intake layer (ADR-048) are both
operational. Status: IDENTIFIED / MAPPED / DEFERRED — not ingested.

---

## Scope Boundary

ADR-048 covers:
  staged draft intake, schema validation, draft lifecycle, versioning,
  approval gates, dashboard draft panel, watcher design, conflict intake
  automation, and platform-model-to-CIS bridge.

ADR-048 does not cover:
  execution ownership (ADR-045), filesystem governance (ADR-047),
  local worker roles, agent orchestration, or direct AI write authority
  under any circumstances.

---

## Dependencies

Blocked by:   ADR-045 full closure
Blocks:       local worker draft submission, agent governance intake,
              15 SESSION_INSIGHT_RECORD ingestion pipeline
Parallel:     ADR-047 Filesystem Governance planning may proceed concurrently
