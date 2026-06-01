# CIS_FILE_MAP.mdVersion: 0.1Status: ACTIVELast Updated: 2026-04-28---# PurposeCIS_FILE_MAP.md defines the canonical filesystem authority structure for CIS.This document exists to:- reduce orientation drift- prevent stale-file confusion- identify canonical runtime authority- distinguish active vs legacy artifacts- guide future refactors- support multi-session AI continuity- support ADR-046 filesystem governance workThis is NOT a recursive file listing.This is:- a governance map- a canonicality map- an execution authority map---# Core PrincipleThe CIS filesystem currently contains:1. Active runtime infrastructure2. Canonical governance artifacts3. Sync mirrors4. Historical archives5. Legacy experiments6. Chat-derived artifacts7. Transitional/refactor remnantsNot all files are authoritative.Future sessions must distinguish:- ACTIVE- MIRROR- ARCHIVE- LEGACY- TRANSITIONAL- UNKNOWNbefore making structural changes.---# PRIMARY AUTHORITIES## Runtime AuthorityCanonical runtime authority:```text/mnt/projects/cis/runtime/
This contains:

active Flask app

API routes

runtime scripts

DB helpers

orchestration logic


operator layer

verification scripts

schemas

No duplicate runtime copies elsewhere should be treated as authoritative.

Database Authority
Canonical DB:
/mnt/projects/cis/memory/cis_memory.db
Primary persistent operational state.
Known tables:

captures

corrections

decisions

extraction_runs

insights

knowledge_spines

live_rounds

live_sessions

manifests

migration_log

models

schema_versions

segments

session_log

spine_nodes

tasks

Future:

execution_jobs (ADR-045)

Contract Authority
Canonical contracts:
/mnt/projects/cis/docs/contracts/
Current critical contract:

CIS_Execution_Layer_Contract_v1.md

Contracts define:

execution law

orchestration constraints

verification boundaries

state authority

Contracts supersede conversational reasoning.

ADR Authority
Canonical ADR location:
/mnt/projects/cis/docs/ADRs/
ADRs are authoritative architectural decisions.
Important:
Some early ADRs were logged late or superseded retroactively.
Historical ADR interpretation may require transcript insight records.

Reorientation Authority
Canonical orientation document:
/mnt/projects/cis/docs/2_CIS_REORIENTATION.md
Operational orientation source.
Contains:

current runtime state

operational workflow

path references

dashboard status

infrastructure notes

Must remain synchronized with actual runtime.

Project Primer Authority
Canonical AI orientation layer:
/mnt/projects/cis/docs/claude_chat_transcripts/ChatGTP_Project_Primer/
Purpose:

reduce startup overhead

reduce AI orientation drift

preserve operational truth

provide compressed machine-facing continuity

Contains:

CURRENT_STATE

NEXT_BUILD_TARGET

SYSTEM_MAP

ACTIVE_COMPONENTS

ADR summaries

known risks

open questions

session distillations

This layer is now part of the execution governance strategy.

ACTIVE RUNTIME STRUCTURE
Flask Entry Point
runtime/app.py
Current canonical backend entry point.
Replaced earlier monolithic:
cis_dashboard.py
Old monoliths should not be reused.

Runtime Configuration
runtime/config.py
Canonical path authority.
No runtime path should be hardcoded elsewhere.
All future modules must import path constants from config.py.

API Layer
runtime/api/
Contains modular Flask blueprints.
Known important modules:

session.py

live.py

operator.py

pipeline.py

tasks.py

Operator abstraction begins here.

DB Layer
runtime/db/
Known important modules:

connection.py

live_db.py

Database schema authority and DB access helpers.

Utility Layer
runtime/utils/
Shared helper logic.
Avoid business logic duplication into API routes.

Verification Layer
runtime/cis_verify.pyruntime/cis_verify_semantic.py
L1:
deterministic verification
L2:
semantic verification
Current insight:
operator abstraction is required because manual verifier orchestration became unsustainable.

CURRENT ARCHITECTURAL LAYERS
Operator Layer (ADR-044)
Purpose:
human-safe runtime controls
Current state:
PARTIAL
Key insight:
operator buttons may trigger execution
but may not define legal state.

Execution Layer
Purpose:
state governance and orchestration law
Current state:
PARTIAL
Execution law defined by:

ADR-043

execution contracts

Queue ownership not yet implemented.

Queue Ownership Layer (ADR-045 direction)
Purpose:
serialized execution ownership
Current state:
NOT BUILT
Required because:

hardware constraints prohibit parallel heavy execution

operator routes currently execute work directly

resumability and ownership do not yet exist

Future authority:
execution_jobs table + worker system

Verification Layer
Purpose:
artifact integrity and execution governance
Current state:
ACTIVE
Key insight:
verification matured before operator ergonomics.

FRONTEND STATUS
Dashboard Frontend
Current file:
runtime/templates/cis_dashboard.html
Status:
MONOLITHIC
Known issue:
frontend was never modularized after backend refactor.
Technical debt:
HIGH
Current policy:
no major UI expansion before refactor.

CIS LIVE
Canonical Live Infrastructure
Current concepts:

live sessions

live rounds

external model collaboration

serialization to markdown

Originally:
LXC + Flask + Cloudflare architecture
Later evolved:
direct project filesystem serialization
Important:
historical sessions reference older SCP-based write flow.
Do not assume older infrastructure descriptions remain current.

MIRROR / SYNC STRUCTURE
Vault Mirror
Vault directory is:
MIRROR
not authority
Used for:

Obsidian sync

markdown browsing

secondary reference

Edits here may diverge from runtime authority.
Canonical source remains runtime/project directories.

ARCHIVE / LEGACY ZONES
Legacy Runtime Artifacts
Potential locations:
/mnt/projects/cis_legacy//docs/_archive//runtime_scripts mirrors/
Status:
NON-CANONICAL
May contain:

obsolete runtime assumptions

superseded ADR interpretations

stale schemas

abandoned pivots

Do not use as authority without explicit verification.

KNOWN HIGH-RISK AREAS
Frontend Monolith
Risk:
single-file failure surface
Issue:
one syntax error can break entire UI.

Transcript-Derived Artifacts
Risk:
conversational assumptions mistaken for locked architecture.
Mitigation:
contracts + ADRs + primer files override chat reasoning.

Duplicate Runtime References
Risk:
multiple historical copies of runtime files.
Mitigation:
runtime/ is authoritative.

Session Drift
Risk:
sessions beginning without proper orientation.
Mitigation:
Session Start Protocol
Project Primer
handoff governance

CURRENT GOVERNANCE REALITY
CIS now consists of two interdependent systems:
1. Runtime System
Executes workflows.
2. Institutional Memory System
Preserves continuity.
The second system is now critical infrastructure.

CURRENT BUILD PRIORITIES
ACTIVE

ADR-045 Queue Ownership Layer

Queue-backed Verify Contract

Execution serialization

Frontend refactor planning

Filesystem governance

DEFERRED

Full transcript archaeology

Full repo cleanup

Full frontend componentization

Multi-agent parallel orchestration

Expanded operator surface

IMPORTANT OPERATIONAL RULES
Rule 1
Do not trust filesystem proximity as authority.
Rule 2
Contracts override conversational reasoning.
Rule 3
Runtime authority lives in runtime/.
Rule 4
Vault is mirror, not source.
Rule 5
Operator buttons may trigger execution but not bypass governance.
Rule 6
Sequential deterministic orchestration is an intentional hardware-aware design constraint.
Rule 7
Human procedural burden is now treated as a first-class architectural problem.

NEXT REQUIRED DOCUMENTS
Future governance artifacts likely needed:

ADR-045_Execution_Queue_Ownership.md

ADR-046_File_Governance_and_Canonicality.md

EXECUTION_STATE_MACHINE.md

QUEUE_WORKER_SPEC.md

FRONTEND_REFACTOR_PLAN.md

INSTITUTIONAL_MEMORY_ARCHITECTURE.md

END
