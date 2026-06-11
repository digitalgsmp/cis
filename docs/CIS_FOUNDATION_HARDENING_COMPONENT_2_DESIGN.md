# Foundation Hardening Component 2 — Escalation Advisor Integration Protocol
## Design Document — Revision 2

**Status:** APPROVED — awaiting v4impl implementation directive
**Author:** Claude (external proposal author)
**Auditor:** ChatGPT (independent audit, 2026-06-10) — all 11 required revisions addressed
**Eric reconciliation:** APPROVED 2026-06-10 — Section 11 resolved: project_state confirmed present at commit f732cb4
**Date:** 2026-06-10
**Depends on:** Component 1 — Provenance and Lifecycle Base Schema (VERIFIED, commit aa3ffe0)
**Target file:** `docs/CIS_FOUNDATION_HARDENING_COMPONENT_2_DESIGN.md`
**Implements:** Nothing. Contract and schema intent only. Migration text (presumably 0009) is a v4impl deliverable under FINAL_DIRECTIVE after Eric approval.

**Revision log (v1 → v2):**
- R1: `project_state` reference qualified with deterministic existence check (see Section 11 — resolved: project_state confirmed present)
- R2: Packet versioning resolved — versioned packets under one escalation_id; no overwrites
- R3: Schema expanded from two tables to three (`advisor_escalation_packets` added)
- R4: Packets stored as `packet_raw` + structured metadata columns, not blob-only
- R5: Classification source/status model added; Eric remains final authority, not sole classifier
- R6: Per-advisor transmission/response state added; BOTH-advisor ambiguity eliminated
- R7: Mandatory-escalation enforcement re-scoped to "blocks implementation"; Eric Gate enforcement point deferred to Component 3
- R8: Router automation explicitly excluded from implementation scope; CLI/manual tooling only
- R9: HCP mirroring acceptance criterion added
- R10: Terminal states (ABANDONED / SUPERSEDED / CANCELLED_BY_ERIC) with reason fields added
- R11: Structured divergence fields added for BOTH-advisor reconciliation
- Open questions from v1 Section 10: all four resolved per audit; section replaced by Section 10 (Resolved Questions)

---

## 1. Purpose and Boundary Statement

Component 2 defines the formal boundary between two layers that already exist informally:

- **Hermes operational layer** — hermes-prime, hermes-v4pro, hermes-r1, hermes-v4impl. Deliberates, drafts, reviews, implements. All work flows through the spine.
- **Escalation advisor layer** — Claude and ChatGPT. Audit, object, propose, flag risk. No execution authority. No spine write access of their own.

Today this boundary is enforced only by Eric's discipline and by prose rules in HCP_06. Nothing in the spine records that an escalation happened, what was sent, what came back, or how Eric reconciled it. The Kanban situation persisted partly because advisor exchanges that touched on it left no queryable trace. Component 2 makes escalation a first-class, provenance-tracked lifecycle object.

**Handoff boundary with Component 3 (explicit, to prevent scope bleed):** Component 2 ends at *reconciliation recorded in the spine*. It defines what happens when Eric does not simply approve — escalate, redirect, reject — and records that disposition. Component 3 (Eric Gate redesign) *consumes* these records to build the gate briefing and the approval setter. Component 2 does not build the `eric_approved_at` setter, the gate briefing, or any approval UI.

---

## 2. Trigger Conditions

Three classes. Each escalation record carries a `trigger_class` and `trigger_reason`.

### 2.1 Handle internally (no escalation)

- Routine Drafter→Reviewer deliberation that reaches CONSENSUS_REACHED within configured max rounds.
- Reviewer OBJECTIONS resolved through normal loop-back to DRAFT.
- Deterministic gate failures with a known, previously-verified fix path (e.g., dirty working tree, stale export hash) — operational, not architectural.
- OPERATOR_COMMAND-class actions (closeout, regeneration). Deterministic; no deliberation, no advisory value.
- Read-only inspection and status reporting.

### 2.2 Discretionary escalation (Eric may escalate)

- Eric requests an external audit or second opinion, for any reason. Eric's request always suffices; `trigger_reason = ERIC_REQUEST`.
- Drafter/Reviewer produce a structurally valid consensus that Eric's goal-alignment sense flags as off — pattern-match discomfort without a nameable technical defect.
- Novel architecture decisions with long-lived consequences (new subsystem, new external dependency, new data contract) even when internal deliberation converged cleanly.

### 2.3 Mandatory escalation

Escalation is mandatory when any of the following holds for the workflow run in question:

1. **Open drift indicator.** Any unresolved `drift_indicators` row referencing the workflow run or the components it touches. This is the direct anti-Kanban mechanism.
2. **Deliberation exhaustion.** Max deliberation rounds reached without CONSENSUS_REACHED (the Tier 3 ESCALATE outcome, now formalized).
3. **Repeated verification failure.** VERIFY gate fails **twice** on the same directive scope (audit-confirmed default; configurability deferred). The third attempt requires external audit first.
4. **Unresolved or dismissed objection.** A Reviewer objection marked resolved without a corresponding `decision_trails` entry showing how, or explicitly dismissed.
5. **Governance-tier work.** Any Tier 6+ proposal, schema migration, or change to gates, the router, the orchestrator, or the closeout engine — the components that enforce the rules cannot self-certify changes to themselves.
6. **Eric mandate.** Eric declares a category mandatory for the remainder of a phase (recorded once, applies until revoked).

### 2.4 Enforcement semantics (revised per audit R7)

A mandatory escalation **blocks progression to implementation**: no FINAL_DIRECTIVE may issue for a workflow run whose mandatory escalation is not in a RECONCILED (or Eric-cancelled) state. Where possible the escalation should be surfaced before the run reaches Eric Gate review, so Eric reconciles with advisor input in hand rather than after the fact. **Component 3 defines the exact Eric Gate enforcement point and briefing behavior**; Component 2 only guarantees that the blocking fact is queryable from spine state alone:

> Deterministic check: given a workflow_run_id, SQL alone must answer (a) is escalation required, (b) if required, is it satisfied (RECONCILED) — with no model reasoning.

---

## 3. Escalation Packet Format

The packet is a single structured document with fixed sections in fixed order. Mandatory sections may not be omitted; the deterministic builder verifies presence of every section header at build time. Advisors should be able to answer from the packet alone.

### 3.1 Packet versioning (revised per audit R2)

- One escalation may have multiple packet versions, all under the same `escalation_id`.
- A CLARIFICATION_REQUEST response, or any Eric-directed amendment, produces a **new** `packet_version` with a new hash. Prior versions are never overwritten or edited — each is an immutable evidence artifact.
- Responses bind to a specific packet version via `packet_id` + `responded_packet_hash`.

### 3.2 Packet sections

**P0 — Header**
- `escalation_id`, `packet_version`
- Date/time, git HEAD at build time
- `workflow_run_id` (nullable only for phase-level questions not tied to a run)
- Advisor target: CLAUDE | CHATGPT | BOTH
- `trigger_class` (DISCRETIONARY | MANDATORY) and `trigger_reason`
- Packet content hash (SHA256 over sections P1–P6) — binds any response to this exact version

**P1 — Project position**
- Current phase and component, generated from existing spine state and generated context fields. The canonical source is the spine's project-state record (see Section 11 for the existence-check requirement); the builder must read it via query, never hardcode state strings, and must fail loudly at build time if the expected source is absent — it must not silently invent or assume one.
- Tier/component the workflow run advances
- One-paragraph plain-language statement of where the project stands

**P2 — Spine state excerpt**
- The `workflow_runs` row for the run in question (status, timestamps)
- `deliberation_rounds` summary: round count, per-round outcome signal, final Reviewer signal
- Open `active_blockers` touching the run's scope
- Last `session_closeouts` reference so the advisor knows the verified baseline

**P3 — Provenance and lifecycle records (Component 1 integration)**
- `goal_references`: which defined goal the work serves, which dependency-graph node it closes
- `decision_trails`: condensed problem → research → draft → review path producing the current proposal
- `drift_indicators`: all open indicators relevant to the run (mandatory triggers reproduced verbatim)
- `rejection_rationale`: alternatives already considered and rejected, so the advisor does not re-propose them blind

**P4 — The exact question**
- One explicit ask, or a numbered list of at most three tightly-related questions
- Requested response type: AUDIT (pass/fail with findings) | PROPOSAL_REVIEW | RISK_ASSESSMENT | DESIGN_INPUT
- What "done" looks like for the response (e.g., "PASS/FAIL with each objection enumerated")

**P5 — Constraints and authority limits**
- Standing statement: advisor has review/consult authority only; no execution authority; output is advisory input to Eric's reconciliation, not a directive
- The Exact-Format Instruction Rule (verbatim, from HCP_06)
- Scope fence: what the advisor must not expand into (named components, deferred tiers)
- Reminder that the Verification-Hardening and Evidence-Backed Response rules govern any claims the advisor relies on

**P6 — Evidence appendix**
- Raw terminal output relevant to the question (git log, sqlite queries, gate output). Raw only.

### 3.3 Storage model (revised per audit R3/R4)

Each packet version is stored **both** ways:
- `packet_raw` — the full verbatim packet text, the evidence artifact, hash-covered.
- Structured metadata columns for queryability: escalation_id, packet_version, workflow_run_id, advisor_target, trigger_class, trigger_reason, requested_response_type, git_head, packet_hash, packet_status, created_at, transmitted_at.

The raw text preserves the exact artifact; the structured columns make the spine queryable. Full per-section columns are not used — section presence is enforced by the build-time completeness gate, so decomposing P1–P6 into columns adds maintenance cost without query value.

### 3.4 Packet construction responsibility (revised per audit R8)

- **Component 2 implementation scope:** a deterministic CLI builder command that assembles P0–P3 and P6 by querying the spine and git directly. P4 and the P5 scope fence are authored by the Drafter or Eric, then frozen in. Hash computed last. No router involvement.
- **Component 4 (later):** the router invokes this same builder on escalation detection. The builder, not router logic, owns packet structure, so Component 4 inherits the contract unchanged. Router detection and automatic packaging are explicitly out of Component 2 scope.

---

## 4. Response Ingestion Contract

### 4.1 Recording

Every advisor response is written to the spine verbatim, as received, before any interpretation. The raw text is the record; classification and summary are annotations on it, never replacements.

Each response record carries:
- `escalation_id`, `packet_id`, and `responded_packet_hash`. If the hash does not match the stored hash for that packet version, ingestion sets `hash_match_status = MISMATCH` — the response is still recorded, but provenance is marked degraded and the mismatch is surfaced to Eric.
- Advisor identity (CLAUDE | CHATGPT) and `transmission_mode` (MANUAL_PASTE now; API after Tier 8).
- Timestamps: received, ingested.

### 4.2 Per-advisor transmission and response state (revised per audit R6)

When `advisor_target = BOTH`, one escalation expects two responses, transmitted and received at different times. Escalation-level status alone is ambiguous. Therefore:

- One `advisor_responses` row is created **per expected advisor** at transmission time, carrying its own lifecycle:
  `response_status = EXPECTED → TRANSMITTED → RECEIVED → INGESTED → CLASSIFIED`
- The escalation-level status advances to RESPONSES_COMPLETE only when every expected response row reaches INGESTED (or Eric explicitly waives a missing one, recorded with reason).
- Packet-level `transmitted_at` records first transmission of that version; per-advisor transmission timestamps live on the response rows.

### 4.3 Response type classification (revised per audit R5)

Primary type (exactly one) plus optional secondary flags:

| Type | Meaning |
|---|---|
| AUDIT_PASS | Advisor reviewed and found no material objections |
| AUDIT_OBJECTION | Advisor found defects; objections enumerated |
| PROPOSAL | Advisor proposes a design or course of action |
| CLARIFICATION_REQUEST | Advisor cannot answer from the packet; triggers a new packet_version. Track frequency — recurring clarification requests are a packet-quality defect signal |
| RISK_FLAG | Advisor identifies a risk outside the question asked |
| RECOMMENDATION | Non-binding advice short of a formal proposal |

Classification carries provenance of its own:
- `classification_source = ERIC | TOOL | HERMES_ASSISTED`
- `classification_status = PROPOSED | CONFIRMED | CORRECTED`

Deterministic tooling or Hermes may assign an initial PROPOSED classification (e.g., keyword/structure detection of "PASS WITH REQUIRED REVISIONS"); Eric confirms or corrects. **Eric remains final authority** — no classification reaches CONFIRMED without Eric attribution — but Eric is not required to be the mechanical classifier of every response. Misclassifications are corrected with an audit trail (CORRECTED), never silently.

### 4.4 Eric reconciliation representation

When all expected responses are in (or waived), Eric reconciles. The reconciliation record carries:

- Disposition: ACCEPT | ACCEPT_WITH_MODIFICATION | REJECT | RETURN_TO_DRAFT | ESCALATE_FURTHER
- A plain-language reconciliation note in Eric's words (pattern-matching terms — seed-intent-grade content)
- For BOTH-advisor escalations where advisors diverge (revised per audit R11):
  - `advisor_divergence_summary` — plain-language statement of where they disagreed
  - `advisor_positions_json` — minimal structured capture of each advisor's position on each contested point, so Component 3's gate briefing can render divergence deterministically
- Timestamp

Two Component 1 writes accompany reconciliation:
- A `decision_trails` entry: the escalation and its reconciliation become a stage in the run's decision path.
- A `rejection_rationale` entry whenever Eric rejects an advisor proposal or one advisor's position over the other's.

**What reconciliation is not:** it is not Eric Gate approval. Reconciliation closes the *advisory* loop; the gate (Component 3) closes the *authorization* loop.

### 4.5 Terminal states (revised per audit R10)

Escalations that will not complete normally must close cleanly, never linger half-open:

| Terminal state | Meaning | Required field |
|---|---|---|
| ABANDONED | Work it supported was dropped; escalation moot | `abandoned_reason` |
| SUPERSEDED | Replaced by a newer escalation (link to successor escalation_id) | `abandoned_reason` + successor reference |
| CANCELLED_BY_ERIC | Eric explicitly cancels | `abandoned_reason`, Eric-attributed |

A reason field is mandatory for every terminal state. Open escalations older than a configurable staleness window should be surfaced by the existing passive watchdog pattern (reporting only — no auto-close).

---

## 5. Current Path (Manual)

1. Trigger fires (Section 2) or Eric requests escalation.
2. Deterministic CLI builder assembles packet v1 from spine + git; Drafter or Eric authors P4/P5; hash computed; escalation + packet rows written (status PACKET_BUILT).
3. Eric copies the packet into the subscription Claude and/or ChatGPT interface. Per-advisor response rows created/marked TRANSMITTED (Hermes records on Eric's instruction).
4. Advisor responds in-interface. Eric copies the response back.
5. Response ingested verbatim via deterministic ingestion command (Hermes executes the insert on Eric's instruction; Eric never hand-edits the database). Response row → INGESTED; tool/Hermes may attach PROPOSED classification.
6. Eric confirms/corrects classification. If CLARIFICATION_REQUEST: builder produces packet v2 under the same escalation_id; cycle repeats from step 3.
7. When all expected responses are INGESTED (or waived), Eric records reconciliation. Escalation → RECONCILED.
8. Workflow run proceeds (toward Eric Gate, back to DRAFT, or wherever disposition directs). FINAL_DIRECTIVE remains blocked until any mandatory escalation is RECONCILED or Eric-cancelled.

Eric remains the only transport. This is accepted: the manual path is the protocol's proving ground, and every field it populates is the same field the API path will populate.

## 6. Future Path (API, Tier 8)

- Transport changes; contract does not. The packet schema, versioning rules, response record schema, classification model, and reconciliation representation defined here are frozen interfaces that Tier 8 automation must satisfy.
- `transmission_mode = API` replaces MANUAL_PASTE; transmission/ingestion timestamps become machine-set; everything else identical.
- Eric's reconciliation step is never automated. API integration removes Eric from the *relay* role only — exactly as the Tier 0 orchestrator did for Drafter/Reviewer — not from the reconciliation role.
- Anti-goal: Tier 8 must not introduce a second, "richer" escalation format. If the API path needs a field the manual path lacks, that is a Component 2 contract amendment requiring this same design protocol.

## 7. Role Boundaries (Restated as Enforceable Properties)

- **Claude and ChatGPT:** escalation advisors. Inputs: packets. Outputs: responses. No execution authority, no direct spine writes, no directive authority. An advisor response is never a FINAL_DIRECTIVE and must never be pasted to v4impl as one.
- **Hermes operational layer:** builds packets (deterministic builder), records responses and proposed classifications on Eric's instruction, never transmits to advisors on its own, never reconciles, never confirms classifications.
- **v4impl:** implements only FINAL_DIRECTIVEs issued by Eric after reconciliation. The escalation tables give downstream enforcement a queryable fact: "this run's mandatory escalation is/is not RECONCILED."
- **Eric:** sole transmitter (now), final classification authority, sole reconciler, always.

## 8. Acceptance Criteria

Implementation accepted only when all of the following pass with raw terminal evidence, per the Verification-Hardening Rule. Verification report ≠ commit authorization; these remain separate directive steps. Per audit R8, no criterion requires router integration.

1. **Schema gate.** `gate_db_state.py` extended to verify all three new tables: presence, column sets, FK integrity (`advisor_escalations.workflow_run_id` → `workflow_runs`; `advisor_escalation_packets.escalation_id` and `advisor_responses.escalation_id`/`packet_id` → parents), indexes. Evidence: gate exit 0 plus raw `sqlite3 .schema` output. The gate (or a build-time precondition documented with it) also verifies the P1 project-position source exists (Section 11).
2. **Packet completeness gate.** Deterministic check that a built packet contains every mandatory section P0–P6 and that the stored hash matches recomputation over P1–P6. Evidence: gate run on a synthetic packet (exit 0) and on a deliberately broken packet missing P3 (non-zero exit).
3. **Versioning test.** Synthetic CLARIFICATION_REQUEST produces packet v2 under the same escalation_id; v1 row remains byte-identical (hash unchanged); responses bind to the correct packet_id. Evidence: raw query output before/after.
4. **Mandatory-trigger computation test.** Synthetic workflow runs with (a) an open drift indicator, (b) none: trigger check returns ESCALATION_REQUIRED true/false respectively, from SQL alone. Plus the satisfaction check: required-and-unreconciled vs required-and-reconciled. Evidence: raw query output for all cases.
5. **Round-trip lifecycle test (BOTH-advisor).** Synthetic escalation targeting BOTH walked through build → two transmissions → two ingested dummy responses (one with deliberate hash mismatch, verifying MISMATCH flag) → proposed classification → Eric-confirmed classification → reconciliation with divergence fields populated → linked `decision_trails` entry. Evidence: raw SELECT output showing every provenance field.
6. **Terminal-state test.** Synthetic escalation cancelled via CANCELLED_BY_ERIC with reason; verify terminal state and reason recorded, and that a terminal escalation cannot transition further. Evidence: raw query output.
7. **Boundary negative test.** No code path can mark a reconciliation or CONFIRMED classification without an Eric-attributed action; nothing in orchestrator/router invokes reconciliation. Evidence: grep inspection output.
8. **HCP mirroring (revised per audit R9).** Generated HCP_06 (or a dedicated HCP escalation section) describes the approved escalation protocol, advisor authority limits, and packet/response lifecycle, sourced from static config so it survives regeneration. `gate_export_agreement.sh` passes after regeneration. Evidence: gate exit 0 + relevant HCP_06 excerpt from the generated file.
9. **Two-commit rule observed:** source changes first, regenerated exports second.

## 9. Integration with Component 1 and Schema Impact

### Component 1 fields used (no changes to them)

- `goal_references` — read into P3; reconciliation links the escalation to the goal the run serves.
- `decision_trails` — written at reconciliation; read into P3.
- `drift_indicators` — read for mandatory-trigger computation; reproduced in P3.
- `rejection_rationale` — read into P3; written when reconciliation rejects an advisor position.

### New schema (revised per audit R3/R4 — three tables)

An escalation is a lifecycle object; a packet version is an immutable evidence artifact; a response is a per-advisor record bound to a specific packet version. These are distinct objects with distinct lifecycles, so three tables:

**`advisor_escalations`** — one row per escalation lifecycle:
id, workflow_run_id (FK, nullable), trigger_class, trigger_reason, escalation_scope, status, reconciliation_disposition, reconciliation_note, advisor_divergence_summary, advisor_positions_json, created_at, reconciled_at, abandoned_at, abandoned_reason (+ successor reference for SUPERSEDED).

**`advisor_escalation_packets`** — one row per packet version:
id, escalation_id (FK), packet_version, packet_raw, packet_hash, git_head, advisor_target, requested_response_type, packet_status, created_at, transmitted_at.

**`advisor_responses`** — one row per expected advisor per packet exchange:
id, escalation_id (FK), packet_id (FK), advisor, transmission_mode, response_raw, responded_packet_hash, hash_match_status, primary_type, secondary_flags, classification_source, classification_status, response_status, received_at, ingested_at.

Exact column types, constraints, and index set are the implementation migration deliverable, constrained by this contract. No changes to Component 1 tables.

### Explicitly not in scope

- No changes to Component 1 tables.
- No `eric_approved_at` setter, gate briefing, or approval UI (Component 3).
- No router detection/automation (Component 4) — only the builder/ingestion/check contract the router will later call.
- No API transport (Tier 8).

## 10. Resolved Questions (formerly Open Questions)

1. **Clarification requests:** same escalation_id, new packet_version, prior versions immutable. (Audit-confirmed.)
2. **Verification-failure threshold:** 2, fixed for Component 2; configurability deferred. (Audit-confirmed.)
3. **Storage:** packet_raw + structured metadata columns; no full per-section decomposition. (Audit position adopted, replacing v1's blob-only draft position.)
4. **Divergence capture:** structured — `advisor_divergence_summary` + `advisor_positions_json` — in addition to the reconciliation note. (Audit position adopted.)

## 11. Section 11 RESOLVED — project_state confirmed present

Eric reconciliation result: `project_state` exists in the SQLite spine (verified via `sqlite3 data/cis_memory.db ".schema project_state"` at commit f732cb4). The ChatGPT audit's concern that the table "may not exist" was based on a stale HCP packet inventory. Claude's understanding was correct. The deterministic existence check in Section 3.2 P1 and acceptance criterion 1 stands — the builder queries project_state and fails loudly if absent. No P1 fallback revision is required.

---

*End of approved design. Per the Foundation Hardening design protocol: this document is approved and ready for a FINAL_DIRECTIVE to v4impl for implementation.*
