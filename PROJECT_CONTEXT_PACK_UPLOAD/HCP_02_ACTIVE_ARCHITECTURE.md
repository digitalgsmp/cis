# Active Architecture — Hermes Harness / CIS
Generated: 2026-09-24 15:24 UTC | Run: run-c7ffcef28503
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## Current Architecture

**AGENTS.md-native context architecture.**
AGENTS.md is the sole live context for all 4 active Hermes gateways.
HERMES_CIS_BRIEFING_PATH is permanently retired from all 5 profiles.
AGENTS.md discovery depends on cwd/TERMINAL_CWD in gateway mode, not automatic git-root discovery.
terminal.cwd in config.yaml does not currently replace TERMINAL_CWD for context file discovery.

### External Advisor Packet

- **Internal context:** AGENTS.md — auto-loaded by all 4 active gateways via TERMINAL_CWD.
- **External advisor context:** PROJECT_CONTEXT_PACK_UPLOAD/HCP_* — permanent packet for ChatGPT, Claude, and frontier-model escalation.
- **After Tier 5.4–5.6:** HCP files generated from spine + static config, verified by gate_export_agreement.sh. Manual maintenance ends; the packet itself remains.

### Stack
- React + Vite frontend at /mnt/projects/cis/runtime/ui/
- Flask backend at /mnt/projects/cis/runtime/app.py (port 5000)
- SQLite databases: data/cis_memory.db (spine), data/kanban.db (coordination)
- Git versioning: https://github.com/digitalgsmp/cis

### Multi-Hermes Gateway Architecture (topology repaired 2026-06-07)

| Service | Role | Port | HERMES_HOME | Model |
|------|------|------|------|------|
| unknown | Brain | 8644 | /home/eric/.hermes-brainstorm | deepseek-v4-pro |
| hermes-gateway-v4pro | Draft | 8645 | /home/eric/.hermes-v4pro | deepseek-v4-pro |
| hermes-gateway-r1 | Review1 | 8643 | /home/eric/.hermes-r1 | qwen/qwen3.7-max |
| unknown | Review2 | 8647 | /home/eric/.hermes-glm-reviewer | z-ai/glm-5.2 |
| unknown | Menter | n/a (kernel sandbox) | n/a | claude-code (sandboxed coder) |
| unknown | Verify | 8648 | /home/eric/.hermes-glm-verifier | z-ai/glm-5.2 |
| hermes-gateway | Prime/Chat | 8642 | /home/eric/.hermes | deepseek-v4-pro |
| nemo-fast | NeMo Guardrails | 8800 | — | — |

**Context:** AGENTS.md auto-loaded by all 4 active gateways via TERMINAL_CWD=/mnt/projects/cis. HERMES_CIS_BRIEFING_PATH retired at Tier 5.3.

### NeMo Guardrails
- nemo-fast.service on port 8800
- Evidence firewall for Research/Evidence
- Tavily web search, execution-claim blocking, pattern-matched intents
- Path: /mnt/projects/cis/runtime/rails/

### Advisor Loop (Router v0.1)
```
User prompt
  → classify_route() — 8-pass classifier
     ├─ Research signals → Research/Evidence (NeMo:8800 → Flash:8642)
     ├─ Drafter signals → V4 Drafter (8645)
     ├─ Reviewer signals → V4 Reviewer (8643)
     ├─ Research + Drafter → multihop (NeMo preflight → V4 Drafter)
     ├─ FINAL_DIRECTIVE prefix → V4 Implementer (8646, deterministic)
     └─ Ambiguous → V4 Drafter (8645, low confidence)

  → POST /api/advisor/route (auth-gated, X-CIS-API-Key)
  → routing_decisions table — all routes logged
```

### V4 Models Direct (Not Through NeMo)
NeMo's response pipeline strips `reasoning_content` and `reasoning_tokens` from
DeepSeek thinking models (Gate 5C). V4 Drafter/Reviewer/Implementer are routed direct.
NeMo preflight is used for evidence collection only.

---

## CIS Deterministic Pipeline Architecture (Approved 2026-06-01)

CIS is a Hermes-native adversarial deliberation engine. The pipeline is the product.

### Pipeline Lanes (Kanban)
```
TRIAGE → RESEARCH → DRAFT → REVIEW ↔ LOOP → CONSENSUS → ERIC_GATE
→ IMPLEMENT → VERIFY → STATE_WRITE → EXPORT → DONE
```

| Lane | Profile | Action | Gate |
|------|---------|--------|------|
| TRIAGE | Router | Topic classifier creates workflow_run, assigns Research | — |
| RESEARCH | hermes-prime | Grounds topic in evidence (NeMo firewall + Tavily) | Research artifact attached |
| DRAFT | hermes-v4pro | Generates structured proposal from research + spine briefing | Proposal artifact attached |
| REVIEW | hermes-r1 | Adversarial challenge. Emits OBJECTIONS or CONSENSUS_REACHED | Loop back to DRAFT or promote |
| CONSENSUS | — | Waiting for Eric review | Eric approves, redirects, or injects insight |
| ERIC_GATE | Eric | Human sanity/output gate. Not bypassable | Pass → IMPLEMENT |
| IMPLEMENT | hermes-v4impl | Executes FINAL_DIRECTIVE only. No deliberation | Implementation artifact |
| VERIFY | Bash/Python scripts | Deterministic gate checks: git diff, service health, endpoint, db | PASS or FAIL |
| STATE_WRITE | Gated worker | Writes verified results to SQLite spine. Triggers export. Git commit | Only after VERIFY PASS |
| EXPORT | generate_all.py | AGENTS.md (Hermes) + HCP_ files (ChatGPT/Claude) | Generated, not manual |
| DONE | — | Pipeline run complete. Spine enriched | — |

### Pipeline Coordination (ADR-013)

Kanban is retired as pipeline transport per ADR-013.
workflow_runs is the authoritative in-flight work object.
Deliberation rounds stored in deliberation_rounds.
Implementation evidence in workflow_run_artifacts.
Eric approval recorded in workflow_runs.eric_approved_at.

### Tier 0/1 — Built Artifacts

**Tier 0 — Orchestrator (`9d84351`):**
- `runtime/orchestrator.py` (444 lines) — Drafter→Reviewer deliberation loop
- `runtime/orchestrator_config.yaml` (49 lines) — timeouts, truncation, max rounds
- Test mode (`--test`) for bounded execution
- Acceptance: CONSENSUS_REACHED in Round 2 (~256s)

**Tier 1 — Gate Suite (`bc49beb`–`635a646`):**
- `tools/gates/gate_git_state.sh` — working tree verification
- `tools/gates/gate_service_health.sh` — port health check
- `tools/gates/gate_endpoint.sh` — HTTP endpoint string match
- `tools/gates/gate_no_secrets.sh` — pre-commit secret blocker
- `tools/gates/gate_file_exists.sh` — file + line count check
- `tools/gates/gate_runner.sh` — sequential gate orchestrator

**Build order authority:** `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` (CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md)

### Bidirectional Spine
The state spine is bidirectional:
- **Briefs the pipeline:** Each Drafter session starts with accumulated project knowledge from AGENTS.md (prior decisions, resolved proposals, active blockers, project state)
- **Receives from the pipeline:** Only verified outputs from completed runs are written to SQLite (STATE_WRITE lane, gated on VERIFY PASS)

### External Advisor Protocol
- **Hermes** — root operator, deterministic context owner, pipeline engine
- **ChatGPT** — external advisor, escalation reviewer, consumes generated HCP exports
- **Claude** — external advisor, escalation reviewer, proposal author when asked
- Tier 3 escalation: pass/fail review when V4 deliberation does not satisfy Eric

---

## Active API Endpoints

### Advisor Agent Routing (api/advisor.py)
- GET /api/advisor/agents — list registered agent instances
- GET/POST /api/advisor/threads — create/list advisor threads
- GET /api/advisor/threads/<id>/messages — thread message history
- POST /api/advisor/chat — route message to named agent gateway
- POST /api/advisor/route — classify and auto-route (Router v0.1)

### Collab Tracker (api/collab_rounds.py)
- Full CRUD for rounds, exchanges, directives, handoffs
- Session import via import_session.py

## Database Tables

- collab_agents, collab_status, collab_activity
- collab_rounds, collab_exchanges, collab_final_directives
- collab_session_imports, collab_session_messages
- agent_instances, advisor_threads, advisor_messages
- routing_decisions (Router v0.1)

## Key Files
- /mnt/projects/cis/runtime/app.py — Flask entry point
- /mnt/projects/cis/runtime/api/advisor.py — routing + agent dispatch
- /mnt/projects/cis/runtime/api/collab_rounds.py — collab lifecycle
- /mnt/projects/cis/runtime/orchestrator.py — Tier 0 deliberation loop
- /mnt/projects/cis/runtime/orchestrator_config.yaml — Tier 0 config
- /mnt/projects/cis/tools/gates/ — Tier 1 gate suite + runner
- /mnt/projects/cis/docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md — build order authority
- /mnt/projects/cis/runtime/ui/src/pages/infra/AdvisorChat.jsx — 4-panel UI
- /mnt/projects/cis/tools/export/generate_agents_md.py — AGENTS.md generator
- /mnt/projects/cis/tools/export/generate_hcp.py — HCP_ file generator
- /mnt/projects/cis/docs/CIS_CURRENT_STATE.md — canonical state doc
- /mnt/projects/cis/cis_kernel/build/CIS_SCRATCHPAD.md — running log
