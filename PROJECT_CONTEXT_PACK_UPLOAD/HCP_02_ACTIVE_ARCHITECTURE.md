# Active Architecture — Hermes Harness / CIS
Last updated: 2026-06-01 (CIS Deterministic Pipeline Decision)

## Current Architecture (Router v0.1)

### Stack
- React + Vite frontend at /mnt/projects/cis/runtime/ui/
- Flask backend at /mnt/projects/cis/runtime/app.py (port 5000)
- Flask runs as user systemd service: cis-flask.service
- SQLite database: /mnt/projects/cis/runtime/db/cis_memory.db
- Git versioning: private repo at https://github.com/digitalgsmp/cis

### Multi-Hermes Gateway Architecture (Phase 0 verified)

| Agent | Role | Port | HERMES_HOME | Model | Reasoning | NeMo? |
|-------|------|------|-------------|-------|-----------|-------|
| hermes-prime | Flash/Research | 8642→8800 | ~/.hermes | deepseek-v4-flash | — | Yes |
| hermes-v4pro | V4 Drafter | 8645 | ~/.hermes-v4pro | deepseek-v4-pro | xhigh | Direct |
| hermes-r1 | V4 Reviewer | 8643 | ~/.hermes-r1 | deepseek-v4-pro | xhigh | Direct |
| hermes-v4impl | V4 Implementer | 8646 | ~/.hermes-v4impl | deepseek-v4-pro | xhigh | Direct |
| hermes-qwen | Qwen (paused) | 8644 | ~/.hermes-qwen | qwen3-vl-30b (local) | — | None |

**Context briefing:** All gateway profiles load `HERMES_CIS_BRIEFING_PATH` at startup.

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
     ├─ JUDGE_REQUEST prefix → Qwen (8644, deterministic, backend)
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
| TRIAGE | Router | Topic classifier creates Kanban card, assigns Research | — |
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

### Bidirectional Spine
The state spine is bidirectional:
- **Briefs the pipeline:** Each Drafter session starts with accumulated project knowledge from AGENTS.md (prior decisions, resolved proposals, active blockers, project state)
- **Receives from the pipeline:** Only verified outputs from completed runs are written to SQLite (STATE_WRITE lane, gated on VERIFY PASS)

### Context Loading — Transitional
- **Current (transitional):** `HERMES_CIS_BRIEFING_PATH` env var injects briefing into all profiles
- **Target (Phase E):** `/mnt/projects/cis/AGENTS.md` auto-loaded by all profiles natively
  - 20K char limit — fits full briefing
  - No custom env var required
  - Survives Hermes upgrades without patching
- `HERMES_CIS_BRIEFING_PATH` is transitional and must not remain as a parallel long-term source.
  Target retirement: Phase E, after AGENTS.md loading is verified across all active profiles.

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
- /mnt/projects/cis/runtime/ui/src/pages/infra/AdvisorChat.jsx — 4-panel UI
- /mnt/projects/cis/tools/generate_context_briefing.py — context briefing generator
- /mnt/projects/cis/docs/CIS_CURRENT_STATE.md — canonical state doc
- /mnt/projects/cis/cis_kernel/build/CIS_SCRATCHPAD.md — running log
