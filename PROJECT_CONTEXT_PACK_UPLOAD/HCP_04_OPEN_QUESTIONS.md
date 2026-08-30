# Open Questions — Hermes Harness / CIS
Generated: 2026-08-30 14:43 UTC | Run: run-d9a7d6483cbe
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## q-001 — ComfyUI role in CIS/WIAS — is it running? How integrated?
Status: OPEN

## q-002 — Archive drives — /mnt/archive/ mounted? Contents?
Status: OPEN

## q-003 — CIS Flask app (Tier 10 UI) — running? What does Eric see?
Status: OPEN

## q-004 — Build plan FD.1-FD.4 — pending dual review + Eric approval
Status: OPEN

## q-005 — Escalation wiring — what is actually wired for ChatGPT/Claude?
Status: OPEN

## q-006 — Remaining gaps — anything else needed before CIS usable?
Status: OPEN

## OQ-SEED-006 — deliberation_rounds schema is lossy: no reviewer_output column exists, only reviewer_signal. Reviewe
Status: OPEN

## OQ-SEED-007 — 4-independent-installs migration scope contradiction: Qwen (port 8644) is out-of-scope in the spec b
Resolved 2026-06-17
Status: RESOLVED

## OQ-SEED-005 — Implementer scope expansion from inferred deliverables: Tier 6.4 exposed a scope-control gap. V4 Imp
Resolved 2026-06-17
Status: RESOLVED

## OQ-SEED-003 — Should stale context pack folder cleanup (Tier 5.7) wait for first successful generate_all.py run or
Status: OPEN

## OQ-SEED-002 — hermes-gateway.service HERMES_HOME anomaly (OQ-009) — prime profile HERMES_HOME confirmed /home/eric
Deferred — BLK-SEED-005 resolved as false positive
Status: DEFERRED

## OQ-SEED-001 — Google Drive backup integrity unverified
Status: OPEN

## OQ-T44-001 — Tier 4.4 migration applied cleanly?
Verified by gate
Status: RESOLVED

## OQ-SEED-004 — Closeout trigger design: define how CIS automatically requires closeout when a dependency-graph/buil
Status: OPEN
