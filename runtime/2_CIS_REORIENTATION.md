# CIS — Session Reorientation
# Updated: 2026-04-30
# Purpose: Constitutional orientation for any AI model beginning a CIS session.
#          This file answers: What is CIS? What phase is it in? What governs it?
#          Operational detail lives in the Project Primer operational files and the current handoff.

---

## What CIS Is

A story-first creative production infrastructure — a studio operating system
that transforms raw source material into structured knowledge and finished
creative work across the WIAS domains (Word, Image, Action, Sound, Web) and
LIFE domains (Home, Body, Mind) — architected toward sovereign local inference
with frontier models in a verification and improvement role.

Tools are execution endpoints. Story is the system identity.
Human-led. AI proposes, human validates and promotes.
Contract-first. No subsystem built before its schema is defined.
Sequential build. Prove, stabilize, integrate, expand.

---

## Current Phase

Phase PD (Pre-Development Harness) — governance contracts locked, execution ownership implementation underway.

Phase 0 begins after:
- ADR-045 implementation closure
- execution serialization validation
- operational stabilization
- queue-backed verification flow completion

Current build center:
ADR-045 — Execution Queue Ownership Layer implementation.

Current active work:
- Step 5 dashboard polling/status refresh
- verify_contract worker patch validation
- queue worker canonicality verification

Do not return to PD.5 work unless verification reveals a defect.

---

## Governing Principles (Constitutional — Never Override)

1. Story-first. Tools serve narrative production, not the reverse.
2. Human-led. AI proposes. Human approves. Human promotes.
3. Contract-first. Every subsystem requires a locked schema before build.
4. Sequential deterministic orchestration. One execution at a time. Hardware constraint intentional.
5. Verification before advancement. No build action complete without required verification layers.
6. Operator buttons may trigger legal execution. They may not bypass governance.
7. Contracts override conversational reasoning. Always.
8. Runtime authority is /mnt/projects/cis/runtime/. No other location is canonical.
9. DB authority is /mnt/projects/cis/memory/cis_memory.db.
10. Vault is a mirror. Not a source of truth.
11. Human procedural burden is a first-class architectural problem.
12. Governance maturity and operational reality are distinct layers. Do not blur them.

---

## Canonical Authority Map

Runtime code:
    /mnt/projects/cis/runtime/

Database:
    /mnt/projects/cis/memory/cis_memory.db

Contracts:
    /mnt/projects/cis/docs/contracts/

ADRs:
    /mnt/projects/cis/docs/ADRs/

Logs:
    /mnt/projects/cis/logs/

Manifest persistence:
    /mnt/projects/cis/logs/manifests/

Handoff files:
    /mnt/projects/cis/handoff/

Project Primer:
    /mnt/projects/cis/docs/claude_chat_transcripts/ChatGTP_Project_Primer/

Archive (non-canonical):
    /mnt/projects/cis/docs/_archive/

Do not treat files outside these locations as current authority without explicit instruction.

---

## Layer Stack (Current)

Human Operator
↓
Operator Abstraction Layer (ADR-044) — OPERATIONAL / TRANSITIONAL
↓
Runtime Service Ownership Layer — OPERATIONAL / TRANSITIONAL
↓
Execution Queue Ownership Layer (ADR-045) — LOCKED / PARTIALLY IMPLEMENTED
↓
Execution Layer / Governance Law (ADR-043) — LOCKED
↓
Verification Layer (ADR-033/034/040) — OPERATIONAL
↓
Artifact Registry + Database + Logs
↓
Institutional Memory Layer

---

## ADR-045 Status

Verified complete:
- execution_jobs table
- api/queue.py routes
- Flask-started background worker

Operational/transitional:
- queue-backed verify_contract execution

Remaining:
- dashboard polling
- run_l2 queue execution
- cold start recovery validation
- single-worker FIFO validation under load
- queue_worker.py patch/canonicality validation

Known blocking issue:
queue_worker.py verify_contract handler previously invoked cis_verify.py
with unsupported --file flag. Patch exists but canonical deployment must be verified.

---

## Sovereign Intelligence Arc (ADR-036)

Phase A (current):
Frontier models build and verify. Local models assist.

Phase B:
Local stack becomes primary inference layer. Frontier models verify/audit.

Phase C:
Local stack + vectorized institutional memory become primary intelligence layer.
Frontier models become consultant/auditor systems.

Long-term objective:
Accumulated institutional knowledge + governed execution infrastructure.

---

## Session Start Protocol (Required — Every Session)

1. Read:
   - current handoff file
   - this document
   - Project Primer operational files

2. Check verification log for unresolved FAILs:
   cat /mnt/projects/cis/logs/verification_log.md

3. Open a CIS Live session before build work:
   Topic = current build target
   Problem = current state, intended build action, expected return point

4. Log architectural deviations, discoveries, or governance decisions as rounds.

5. Resolve the Live session before session close.

No build work begins before CIS Live is open.

---

## Session End Protocol (Required — Every Session)

Generate the following fields at exact session close moment:

Field 1 — Session Focus
Field 2 — Completed
Field 3 — Next Steps
Field 4 — Notes
Field 5 — Verification Status

Verification Status must include:
- manifests produced
- verification passes executed
- unresolved FAIL count
- verification log path

If additional work occurs after field generation:
"Those fields are now outdated — here are the updated ones:"

Sessions may not close cleanly with unresolved verification failures.

---

## Verification Chain (ADR-033/034/040 — LOCKED)

Every significant build action requires:

L1 — deterministic verification
    cis_verify.py

L2 — semantic verification
    cis_verify_semantic.py
    requires vLLM Slot 1

L3 — external audit
    CIS Live Copy Prompt
    used for contracts, schemas, governance updates, and critical architectural changes

Builder model may not serve as its own L3 auditor (ADR-034).

No significant build action is complete until required verification passes succeed.

ADR-044 automation reduction work removed manual manifest construction requirements.

---

## CIS Live — Constitutional Purpose

1. Multi-model scratchpad — problem, responses, resolution, auto-capture
2. Branch/deviation record — every build deviation logged with return point
3. Verification relay — L3 prompts delivered as verification rounds
4. Architectural reasoning capture

Only the current active session broadcasts to CIS_LIVE.md (ADR-021).

---

## Critical Gotchas (Constitutional — Do Not Repeat)

- Contracts override conversational reasoning. Always.
- Obsidian vault is a mirror. DB is canonical.
- Never paste large Python files into terminal directly. Use VS Code transfer.
- decisions DB API requires description field or silent failure occurs.
- Git push removed from session close subprocess. Push manually if needed.
- vLLM Slot 1 stops when terminal closes. Restart manually each session.
- Qwen3 emits think blocks; cis_verify_semantic.py strips them. Any other Slot 1 caller must too.
- cis_verify_semantic.py no longer passes explicit temperature.
- cis_verify_semantic.py max_tokens = 768 per PD.5 stabilization.
- Slot 1 max_model_len = 4096; large files may fail semantic verification. Always run L1 first.
- Flask reload behavior may leave stale worker code active after patch deployment.
- queue_worker.py canonicality must be confirmed after in-place patches.
- Any conflict discovered and not immediately resolved must be appended to
  CIS_CONFLICT_REGISTER.md before session close.
  Run: python3 /mnt/projects/cis/runtime/cis_conflict_append.py --help

---

## Current Architectural Reality

Named architectural problem: "The human is still the API."

The system is currently solving human middleware dependence between
partially completed governance layers. This manifests as:
  - copy-pasting AI-generated fields into dashboard forms
  - manually running terminal scripts to log conflicts
  - bridging AI output to governance records by hand

ADR-044 addresses operator abstraction.
ADR-045 addresses execution ownership.
ADR-046 governs automation reduction.
ADR-048 (pre-draft) addresses staged draft intake — the missing layer
between AI-proposed structured content and canonical CIS records.

Governance surfaces are now more mature than runtime implementation.
Do not mistake transitional operational behavior for final architecture.

---

## Operational References

See:
- 01_CURRENT_STATE.md
- 02_NEXT_BUILD_TARGET.md
- 03_SYSTEM_MAP.md
- 09_GOVERNANCE_STATE.md
- 10_OPERATIONAL_REALITY.md
- 11_TRANSITIONAL_IMPLEMENTATIONS.md
- current CIS_Handoff_[TIMESTAMP].md
- ChatGTP_Project_Primer/
