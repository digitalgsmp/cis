# CIS Dependency Graph Build Plan v2.0
Hermes (deepseek-v4-pro) | 2026-06-05 | Based on CIS Build Proposal v1.0 (Claude/ChatGPT consensus)
Generated for ChatGPT + Claude consensus review

---

## Framing

CIS is a Hermes-native adversarial deliberation engine. The product is the guardrail
system that controls LLM behavior — deterministic verification, shared memory, and
automated deliberation — so Eric is not a manual API relay between agents.

This plan reorders CIS Build Proposal v1.0 into a dependency graph. Nothing is added.
Nothing is removed. Every artifact maps to a component from the original proposal.
Components are reordered so nothing is built before its dependencies exist.

The orchestrator is moved to the front. The reason: the original plan left Eric as
a manual relay for 5 tiers of infrastructure. The orchestrator removes Eric from the
relay in one artifact. Everything else is built while the orchestrator runs deliberation.

---

## Verified Substrate (COMPLETE — Phase A)

These facts are confirmed and all subsequent tiers assume them:

| Fact | Source |
|------|--------|
| Hermes Agent v0.13.0, Kanban fully available | A1, A2 |
| Kanban shareable via HERMES_KANBAN_DB + HERMES_KANBAN_HOME env vars | A3 |
| Cross-profile Kanban visibility confirmed (prime, v4pro, r1) | A3 |
| AGENTS.md auto-loaded by all 4 active profiles from git root | A4 |
| HERMES_CIS_BRIEFING_PATH present in all 5 profiles (transitional) | A5 |
| Gateway restart pending — Kanban env vars not active in gateway context | A3 |
| **Gateway restart COMPLETE (2026-06-06)** — all 5 gateways have KANBAN vars in process env. OQ-009 resolved. | Tier 2.2 |
| 4 active gateways: prime (8800), v4pro (8645), r1 (8643), v4impl (8646) | Phase 0 |
| Qwen paused on 8644 | Phase 0 |
| /api/advisor/route classifies and dispatches to correct gateway | Router v0.1 |
| **Hermes Kanban v0.13: no custom lanes/columns.** Built-in statuses only. | Tier 2.6 |

---

## Dependency Tiers

Each tier is gated on the tier above it. Nothing in a lower tier can be built or run
until everything it depends on exists and is verified.

### Tier 0 — Deliberation Engine (0 upstream dependencies)

**What it solves:** Eric is currently a manual relay — reading Drafter output, pasting
to Reviewer, reading Reviewer output, deciding loop or consensus. This artifact removes
Eric from that relay.

**Artifacts:**

| # | Artifact | Description | Dependencies |
|---|----------|-------------|--------------|
| 0.1 | `orchestrator.py` | State machine: DRAFT → REVIEW → CONSENSUS or LOOP. Calls existing gateway endpoints via `/api/advisor/route`. Runs until CONSENSUS_REACHED or max rounds (3). Presents final proposal to Eric. | Running gateways, /api/advisor/route endpoint |
| 0.2 | `orchestrator_config.yaml` | Maps agent roles to gateway endpoints. Defines max rounds, timeouts, CONSENSUS_REACHED signal format. | orchestrator.py |

**State machine:**
```
START → DRAFT(v4pro) → REVIEW(r1) → 
  ├─ CONSENSUS_REACHED → PRESENT_TO_ERIC
  └─ OBJECTIONS → DRAFT(v4pro) → REVIEW(r1) → ...
       (max 3 rounds, then ESCALATE to Eric with unresolved objections)
```

**What it does NOT do:**
- No Kanban integration (Tier 2)
- No SQLite storage (Tier 4)
- No gate script verification (Tier 1)
- No AGENTS.md generation (Tier 5)
- No Eric gate bypass — Eric still approves at CONSENSUS

**Acceptance test:** Eric types a topic. orchestrator.py runs Drafter→Reviewer loop.
Eric receives CONSENSUS_REACHED with proposal or ESCALATE with unresolved objections.
No manual copy-paste between agents.

---

### Tier 1 — Deterministic Verification Gates (depends on Tier 0)

**What it solves:** Currently there is no way to deterministically verify that
anything happened. Self-reports from agents are accepted as truth. These scripts
provide PASS/FAIL verification with no LLM in the path.

**Artifacts:**

| # | Artifact | Description | Dependencies |
|---|----------|-------------|--------------|
| 1.1 | `tools/gates/gate_git_state.sh` | Confirms git working tree is clean or has only expected files changed. Usage: `gate_git_state.sh [expected_files...]` | git |
| 1.2 | `tools/gates/gate_service_health.sh` | Confirms a port returns expected string. Usage: `gate_service_health.sh <port> <expected_string>` | curl, running services |
| 1.3 | `tools/gates/gate_endpoint.sh` | Confirms an API endpoint returns expected string. Usage: `gate_endpoint.sh <url> <expected_string> [auth_header]` | curl, running endpoints |
| 1.4 | `tools/gates/gate_no_secrets.sh` | Scans staged files for api_key, secret, password, token. Usage: `gate_no_secrets.sh` | grep, staged files |
| 1.5 | `tools/gates/gate_file_exists.sh` | Confirms a file exists with minimum line count. Usage: `gate_file_exists.sh <path> [min_lines]` | filesystem |

**Design rules for all gates:**
- Exit 0 on PASS, non-zero on FAIL
- Print PASS/FAIL reason to stdout
- No LLM in the verification path
- Standalone — each script runs independently
- Deterministic — same input always produces same output

**What gates in Tier 1 verify:**
- That orchestrator.py produced expected output files
- That gateway services are healthy before orchestrator runs
- That endpoint responses match expected format
- That no secrets are committed

**Acceptance test:** Each script is chmod +x. Each returns 0 or non-zero with a
reason printed to stdout. A manual orchestrator run is verified by gate_git_state.sh
confirming expected output files changed.

---

### Tier 2 — Kanban Coordination Layer (depends on Tier 0 + Substrate verification)

**What it solves:** Currently there is no visibility into what the orchestrator is
doing or what pipeline state a topic is in. Kanban provides a shared board that all
profiles can see and claim from.

**What Kanban is NOT:** Kanban is not the full CIS pipeline display. It lacks custom
lanes in Hermes v0.13 and cannot represent the 11-stage deliberation pipeline as
columns. Kanban is the shared coordination layer and human-readable active work area.
Custom lane displays are the responsibility of SQLite spine (Tier 4) and later CIS UI
views (Tier 6+).

**Note:** Tier 2 gates on Tier 0 (orchestrator) because the Kanban board tracks
orchestrator runs. It does NOT gate on Tier 1 (gates exist but Kanban doesn't
depend on them — gates will verify Kanban operations after Tier 2 is built).

**Artifacts:**

| # | Artifact | Description | Dependencies |
|---|----------|-------------|--------------|
| 2.1 | Gateway readiness check | Verify all 5 gateway services have HERMES_KANBAN_DB + HERMES_KANBAN_HOME in process env. Identify restart gaps. | HERMES_KANBAN_* set in .env files (done) |
| 2.2 | Gateway restart + env normalization | Add EnvironmentFile= to 4 service files matching v4impl pattern. Restart gateways. Verify all 5 processes have Kanban env vars. Fix prime HERMES_HOME anomaly (OQ-009). | 2.1 |
| 2.3 | Kanban board: cis-pipeline | `hermes kanban boards create cis-pipeline --switch`. Add data/ to .gitignore. | 2.2, shared kanban.db |
| 2.4 | Systemd template backup | Copy sanitized service files to runtime/config/systemd/. Commit. | 2.3 |
| 2.5 | Environment manifest | ENV_MANIFEST.md documenting required vars per profile. No secrets. | 2.4 |
| 2.6 | Kanban lane compatibility confirmed | **11-lane structure REJECTED** — Hermes Kanban v0.13 has no custom lanes/columns. Built-in statuses only: triage, todo, ready, running, blocked, done, archived. | 2.3 |
| 2.7 | `gate_runner.sh` (replaces gate_closeout_complete.sh) | Chains all 5 Tier 1 gates in sequence. Exits on first failure. | All Tier 1 gates exist |
| 2.8 | CIS Kanban card schema | Define minimal card format using supported fields: title (with stage prefix), body (structured markdown), tenant (domain namespace), parent (dependencies), assignee, workspace. | 2.6 |

**Kanban card schema (Tier 2.8):**

Hermes Kanban v0.13 supports these fields per card:
- `title` (required) — string
- `body` (optional) — markdown
- `assignee` — profile name
- `parent` — parent task IDs (repeatable, for dependencies)
- `workspace` — scratch | worktree | dir:<path>
- `tenant` — tenant namespace
- `priority` — priority tiebreaker
- `--triage` — flag, parks in triage status
- `idempotency-key` — dedup key
- `max-runtime` — per-task runtime cap
- `created-by` — author name
- `skill` — skills to load (repeatable)
- `max-retries` — retry count
- Built-in statuses: triage, todo, ready, running, blocked, done, archived

**Proposed CIS card convention:**

Title prefix encodes CIS stage: `[TRIAGE]`, `[RESEARCH]`, `[DRAFT]`, `[REVIEW]`,
`[CONSENSUS]`, `[ERIC_GATE]`, `[IMPLEMENT]`, `[VERIFY]`, `[STATE_WRITE]`, `[EXPORT]`,
`[DONE]`.

Body is structured markdown:
```
## Directive
<what the agent should do>

## Context
<relevant state, decisions, blockers>

## Evidence
<research artifacts, gate results>

## Handoff
<previous card ID, consensus signal>
```

Tenant encodes the project/domain (e.g., `cis-infra`, `cis-pipeline`).

Parent encodes card dependencies (e.g., DRAFT card has RESEARCH as parent).

Assignments follow the card-to-profile mapping:
- RESEARCH → hermes-prime
- DRAFT → hermes-v4pro
- REVIEW → hermes-r1
- IMPLEMENT → hermes-v4impl
- VERIFY → (gate scripts, unassigned or hermes-prime)

**Card lifecycle (Kanban statuses mapped to CIS stages):**

| CIS Stage | Kanban Status | Action |
|-----------|---------------|--------|
| TRIAGE | triage | Topic enters, awaiting classification |
| RESEARCH | todo | Prime investigates, attaches evidence |
| DRAFT | todo | v4pro drafts proposal from research |
| REVIEW | todo | r1 reviews, emits OBJECTIONS or CONSENSUS |
| CONSENSUS | ready | Awaiting Eric review |
| ERIC_GATE | ready | Eric approves, FINAL_DIRECTIVE generated |
| IMPLEMENT | running | v4impl executes FINAL_DIRECTIVE |
| VERIFY | running | Gate scripts run, check evidence |
| STATE_WRITE | done | Results written to SQLite spine |
| EXPORT | done | AGENTS.md + HCP generated |
| DONE | archived | Pipeline run complete |

**Acceptance test:** One canary card created with CIS schema format. Readable from
prime, v4pro, and r1 profiles. gate_runner.sh runs and exits with known code.

---

### Tier 3 — Pipeline Smoke Test (depends on Tier 0 + Tier 2)

**What it solves:** Proves orchestrator + Kanban coordination works end-to-end
before building anything that writes persistent state. Catches integration problems
early, when the stack is smallest.

**Artifacts:**

| # | Artifact | Description | Dependencies |
|---|----------|-------------|--------------|
| 3.1 | Smoke test run | One topic → orchestrator runs DRAFT/REVIEW → CONSENSUS_REACHED → Eric approves → card created in Kanban → pipeline stage changes recorded in card title/body metadata; Kanban status reflects only Hermes built-in lifecycle state → verified by gate_runner.sh | Tier 0, Tier 2 |

**Acceptance test:** Full run completes. Pipeline stage changes are recorded in card
title/body metadata; Kanban status (triage/todo/ready/running/done/archived) reflects
only Hermes built-in lifecycle state, not CIS pipeline stages. All 5 Tier 1
gates pass. Eric only touches the CONSENSUS and ERIC_GATE stage transitions — no relay between
Drafter and Reviewer.

---

### Tier 4 — SQLite Spine (depends on Tier 3 smoke test passing)

**What it solves:** Currently there is no persistent project memory. Every session
starts cold. The spine is the bidirectional bridge — verified pipeline runs write in,
future session context reads out.

**Artifacts:**

| # | Artifact | Description | Dependencies |
|---|----------|-------------|--------------|
| 4.1 | Spine schema (13 tables) | Schema from Build Proposal v1.0 §Phase D. Tables: workflow_runs, cards, research_artifacts, proposals, review_rounds, consensus_records, final_directives, implementation_artifacts, verification_runs, project_state, decisions, open_questions, next_actions, file_changes, export_manifests | SQLite |
| 4.2 | `database.py` | Write layer enforcing write authority model from Build Proposal v1.0 §Phase D. Table/column allowlists for all queries. | Schema exists |
| 4.3 | `gate_db_state.py` | Queries SQLite for expected values. Usage: `gate_db_state.py <db_path> <table> <column> <expected_value>`. Allowlisted tables/columns only. | Schema exists, database.py |

**Write authority model:** Write trigger and write actor defined per table.
Implementation artifacts explicitly labeled as self-report — excluded from
write authority for objective state. Only verification_run result (PASS/FAIL)
is truth.

**Acceptance test:** Schema created. database.py inserts one row per table.
gate_db_state.py queries and confirms. Write to non-allowlisted table is rejected.
Implementation artifact is inserted but does not propagate to project_state.

---

### Tier 5 — Context Export Pipeline (depends on Tier 3 + Tier 4)

**What it solves:** Currently context documents are maintained manually and go stale.
The export pipeline generates AGENTS.md (all Hermes profiles) and HCP_ files
(ChatGPT/Claude) from verified spine state. Manual HCP editing ends.

**Artifacts:**

| # | Artifact | Description | Dependencies |
|---|----------|-------------|--------------|
| 5.1 | `generate_agents_md.py` | Reads spine, writes /mnt/projects/cis/AGENTS.md. Content under 20,000 chars. Includes: current objective, build phase, architecture, prior proposals (last 5), active decisions, open questions, next actions, blockers, recent file changes. | Spine schema, database.py |
| 5.2 | AGENTS.md canary test | All 4 active profiles load AGENTS.md from git root and correctly read project state | generate_agents_md.py |
| 5.3 | Retire HERMES_CIS_BRIEFING_PATH | Remove from all 5 .env files after AGENTS.md canary passes all 4 profiles | AGENTS.md canary test passing |
| 5.4 | `generate_hcp.py` | Reads spine, writes HCP_00 through HCP_09 to PROJECT_CONTEXT_PACK_UPLOAD/. Each file stamped with generation timestamp and run_id. | Spine schema, database.py |
| 5.5 | `generate_all.py` | Runs both generators, writes export manifest with SHA256 hashes, runs gate_export_agreement.sh. | generate_agents_md.py, generate_hcp.py |
| 5.6 | `gate_export_agreement.sh` | Confirms AGENTS.md and HCP hashes match manifest. Exits 0 on match, 1 on mismatch (catches manual edits). | generate_all.py, export manifest |
| 5.7 | Stale folder cleanup | Archive PROJECT_CONTEXT_PACK, PROJECT_CONTEXT_PACK_GENERATED, PROJECT_CONTEXT_PACK_UPLOAD_GENERATED to deprecated_packs. | First successful export complete |

**Acceptance test:** One pipeline run completes and writes to spine. generate_all.py
runs. AGENTS.md loads in all 4 profiles — each correctly reads current phase and next
action. HCP_ files generated and match manifest hash. Manual edit to AGENTS.md is
detected by gate_export_agreement.sh (exits 1).

---

### Tier 6 — Pipeline Integration (depends on Tier 5)

**What it solves:** Currently orchestrator.py runs independently, Kanban is populated
manually, and gates run manually. Tier 6 connects them — orchestrator writes to Kanban,
gates run automatically on stage transitions, verified outputs flow to spine.

**Artifacts:**

| # | Artifact | Description | Dependencies |
|---|----------|-------------|--------------|
| 6.1 | `gate_closeout_complete.sh` (v2) | Updated to run all gates: 5 Tier 1 + gate_db_state + gate_export_agreement + pipeline-transition gates. | All gates exist |
| 6.2 | Orchestrator Kanban integration | orchestrator.py claims cards from the Kanban board instead of being called directly. Writes artifacts to Kanban card attachments. | Tier 3 smoke test passing, Kanban board |
| 6.3 | Pipeline-transition gates | gate_research_artifact_present, gate_proposal_schema_valid, gate_review_round_valid, gate_consensus_signal_valid, gate_final_directive_valid, gate_eric_approval_present, gate_implementation_artifact_present | Schema exists, CONSENSUS_REACHED JSON schema defined |
| 6.4 | End-to-end pipeline run | Router routes to Kanban → agents claim and process → verification gates auto-run → state writes to spine → exports generated. Eric only at ERIC_GATE. | All above |

**Acceptance test:** One topic enters via router. Full pipeline runs without Eric
touching anything except ERIC_GATE approval. All gates pass. AGENTS.md and HCP
exports generated from verified spine data. gate_closeout_complete.sh exits 0.

---

### Tier 7 — Router Reclassification (depends on Tier 6 stable)

**What it solves:** Currently classify_route() proxies responses to the best-suited
model. Target: classify_route() creates a Kanban card on cis-pipeline, assigns Research
profile, returns card ID to UI. Pipeline progress replaces chat response.

**Artifacts:**

| # | Artifact | Description | Dependencies |
|---|----------|-------------|--------------|
| 7.1 | Router Kanban integration | classify_route() creates Kanban card, returns card ID. UI shows pipeline progress instead of chat response. | Pipeline stable (Tier 6), Kanban board |

**This is a placeholder.** Do not design implementation until Tier 6 is verified stable.

---

### Tier 8 — MCP Bridge (depends on Tier 7 + pipeline stable)

From Build Proposal v1.0 §Phase H. MCP server at localhost:8888 exposes query tools
for current state, next actions, decisions, and prior proposals. The bidirectional
query tool that feeds Drafter context without full AGENTS.md regeneration.

---

### Tier 9 — Chroma/VDB (depends on Tier 8)

From Build Proposal v1.0 §Phase I. Chroma indexes collab session messages, research
artifacts, proposals, and review rounds. Retrieval only — never writes to spine.
Truth flows from verified pipeline runs, not semantic search.

---

## What Changed From Build Proposal v1.0

| Change | Reason |
|--------|--------|
| Orchestrator moved to Tier 0 (was implicit in Phase C) | Removes Eric from relay immediately — not after 5 infrastructure tiers |
| `gate_db_state.py` moved from Phase B to Tier 4 | Depends on SQLite schema (Tier 4), not curl/grep |
| `gate_export_agreement.sh` moved from Phase B to Tier 5 | Depends on AGENTS.md existing (Tier 5), not curl/grep |
| `gate_closeout_complete.sh` split: v1 (Tier 2) runs 5 gates; v2 (Tier 6) runs all | Can't run gates that don't exist yet |
| Kanban board moved ahead of SQLite (Tier 2 vs Phase D original) | Coordination layer before knowledge layer — Kanban is how agents discover work |
| Pipeline smoke test added as Tier 3 | Proves Kanban+orchestrator integration before building SQLite |
| Gateway restart moved to Tier 2 (was Phase C) | Required before Kanban board creation but not before orchestrator |
| Pipeline-transition gates moved from Phase B appendices to Tier 6 | Depends on schema, CONSENSUS_REACHED JSON, and pipeline being integrated |
| CONSENSUS_REACHED JSON schema from Build Proposal v1.0 Appendix preserved | Used by gate_consensus_signal_valid.py in Tier 6 |

## What Was Rejected From Build Proposal v1.0

| Item | Reason |
|------|--------|
| "Phase" labeling (A-I) | Replaced with "Tier" labeling. Phases implied sequential lock-step. Tiers express dependency only — some tiers can be built in parallel if they share no dependencies. |
| gate_file_exists.sh as closeout-only | Included in Tier 1 as generally useful verification. Not a closeout dependency. |
| Swarm topology definition in Phase C | Swarm not available in Hermes v0.13.0. Deferred. Kanban card claiming replaces swarm for now. |
| HCP file updates before Phase A verification | HCP updates deferred until Tier 6 when exports are generated from spine. Manual HCP editing ends then. |
| 11-lane custom Kanban column structure | **REJECTED (2026-06-06).** Hermes Kanban v0.13 has no custom lane/column support. Immutable built-in statuses only: triage, todo, ready, running, blocked, done, archived. CIS pipeline stage is encoded in card title prefix + body metadata, not custom lanes. Full 11-stage custom display moves to SQLite spine (Tier 4) + later CIS UI views. |

## Consensus Questions for ChatGPT and Claude

1. Is orchestrator.py the correct Tier 0 starting artifact? Does anything gate on it
   being built before it can be useful?

2. Are Tier 1 gate script specifications correct? Missing any gate that could be built
   with only git/curl/grep/filesystem?

3. Is the Kanban board ahead of SQLite correct? Or does the spine schema need to exist
   before Kanban card conventions can be meaningfully defined?

4. Is the smoke test (Tier 3) correctly placed? Could it be combined with Tier 2?

5. Are the 13 SQLite tables from the original proposal all necessary at Tier 4?
   Or should the schema be built incrementally — 2-3 tables first, rest as needed?

6. Does retiring HERMES_CIS_BRIEFING_PATH at Tier 5 introduce risk if AGENTS.md
   generation fails? Should retirement be deferred to Tier 6?

7. Is the full gate inventory from Build Proposal v1.0 (15 gates) correct? Are any
   redundant or could any be merged?

8. Does this plan solve Eric's core problem: being removed from the manual relay
   between agents, with deterministic verification replacing self-report?

---

*Generated by Hermes (deepseek-v4-pro) for ChatGPT + Claude consensus review.*
*Source: CIS Build Proposal v1.0 (Claude, 2026-06-01), HCP_01_CURRENT_STATE.md v2.5, HCP_05_NEXT_ACTIONS.md*
