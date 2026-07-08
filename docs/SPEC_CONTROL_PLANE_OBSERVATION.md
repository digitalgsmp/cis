# CIS Control Plane — Observation Pipeline

**Status:** REVISION 3 | **Date:** 2026-07-03 | **Author:** Drafter (V4 Pro)
**Review History:** R1 (6 gaps resolved) → R2 (10 protocol gaps resolved) → R3 (reviewers demanded mechanism specifications for tasks models handle natively)

## Goal

Build a control plane that lets Eric observe the pipeline models thinking in real time, with three user-confirmation gates. The system must actively seek better approaches beyond the narrow scope of each topic — the Brainstorm role exists specifically to break the pattern of discovering better solutions weeks later.

Built on host first for iteration speed. The output of these sessions is the final formation of the contained Hermes — the permanent workshop in Proxmox LXC on wander (192.168.1.200) that runs CIS as its primary function.

## Principles

1. **Transparency over summarization** — Eric watches reasoning streams, not reads reports
2. **User gates, not roadblocks** — pipeline pauses for clarity checks, flows autonomously between gates
3. **Evidence-backed** — verification shows commands and outputs, not pass/fail badges
4. **Permanent workshop** — LXC provides persistent filesystem, SSH access, no rebuild cycle
5. **Learning system** — every reasoning stream, deliberation, and gate decision writes back to the knowledge base
6. **Mobile-capable gates** — Eric can confirm/reject from Telegram when away from desktop
7. **Cost-aware** — per-run budget tracking, guardrails against runaway token consumption
8. **Lateral thinking** — Brainstorm role challenges assumptions before the Drafter narrows
9. **Intelligence over mechanism** — the model IS the mechanism. CIS does not build extraction pipelines, query strategies, tagging systems, or pre-defined data paths where a model's inference ability suffices. When a task requires "find Eric's intentions about X," the instruction is: "Here is the knowledge base. Here is the topic. Find Eric's words." The model determines how. This principle is the core differentiator between CIS and enterprise architecture — it is what Eric discovered when a model inferred his intention from raw session data better than any extraction pipeline ever did.

### Anti-Bias Enforcement

Enterprise training bias causes reviewers to demand mechanism specifications (query strategies, data paths, format contracts, schema authority) for tasks that model inference handles natively. This bias must be detected and rejected.

**Bias detection rule:** When a reviewer objects that something is "underspecified" or "undefined," ask: is this something a model can determine with access and a clear question? If yes, the objection is bias. The spec is sufficient. The model handles it.

**Examples rejected by this rule:**
- "KB Research query strategy is undefined" → Model has KB + spec. It searches. Strategy is the model's job.
- "Drafter KB access mechanism not specified" → Drafter has KB tools. It queries. Mechanism is tool access, not a pipeline design.
- "Authoritative spine tables not addressed" → Migration converts old tables to observations. Done. No table needs authority.

**Examples NOT rejected (legitimate):**
- "Brainstorm cost contradicts itself" → factual error in the spec, not a mechanism demand
- "KB Research invocation path is undefined" → is it a script or a Hermes process? This affects setup, not inference

## Pipeline Team

| Port | Profile | Model | Role | Function |
|------|---------|-------|------|----------|
| 8644 | brainstorm | DeepSeek V4 Pro (DeepSeek bulk) | **Brainstorm** | Explores intentions broadly, challenges assumptions, finds better approaches outside software |
| 8645 | v4pro | DeepSeek V4 Pro (DeepSeek bulk) | **Drafter** | Writes precise specs incorporating Brainstorm findings + KB evidence |
| — | kb-research | DeepSeek V4 Flash (OpenRouter) | **KB Research** | Triggered after Gate 1 confirmation: receives confirmed intention definition + spec → queries knowledge base → compiles briefing packet. Called as Python subprocess by the adapter API. |
| 8643 | claude | Claude Sonnet 4 (OpenRouter) | **Reviewer** | Architecture alignment, constraints, adversarial review |
| 8647 | glm-reviewer | GLM-5.2 (OpenRouter) | **Reviewer** | Factual accuracy, completeness, catches what Claude misses |
| 8646 | v4impl | DeepSeek V4 (DeepSeek bulk) | **Implementer** | Builds approved specs, produces evidence. Hermes agent with terminal tools. |
| 8648 | glm-verifier | GLM-5.2 (OpenRouter) | **Verifier** | Receives build output → runs evidence commands → assesses alignment. Hermes agent with terminal tools. |

Brainstorm and Drafter use DeepSeek bulk API (no per-token cost, excluded from $0.50/run budget). KB Research uses OpenRouter V4 Flash (cheap, ~$0.02/run). Claude, GLM reviewer, and GLM verifier use OpenRouter and count against budget.

**Port 8644 (Qwen):** The Qwen gateway profile on 8644 was stopped (config was empty, crash-looping). The llama-server on port 8002 (qwen3-vl-30b) remains running as the local inference engine for the Docker container. Port 8644 is repurposed for Brainstorm. The llama-server on 8003 (GLM-4.7-Flash) is unrelated to the pipeline and left as-is.

## Key Design Decisions

### Intelligence over pipelines

Eric's discovery: when given raw session data in the right format, a model inferred his intention better than any extraction/tagging/categorization pipeline. This principle applies everywhere in CIS:

- **KB Research** receives spec + KB → finds relevant passages. No query strategy, no passage selection rules. The model decides what's relevant.
- **Drafter** queries KB during intention alignment → no predefined search method. The model asks what it needs.
- **Brainstorm** finds "what Eric tried before" → queries KB naturally, same as Drafter.
- **Verifier** receives build output → decides which evidence commands to run. No pre-scripted verification checklist.

The implementation provides access. The model provides intelligence.

### Brainstorm → Drafter split

Models default to enterprise patterns and narrow-scope thinking. The Brainstorm forces lateral thinking before the Drafter converges. Same engine (V4 Pro), opposite instructions. Both on DeepSeek bulk — no per-token cost.

### KB Research: model-driven, not pipeline-driven

A Python script that:
1. Receives the spec
2. Calls V4 Flash via OpenRouter with instructions to search the KB for Eric's verbatim intentions, past decisions, constraints, and anti-patterns related to the topic
3. Outputs a briefing packet: cited passages with source attribution
4. Format: markdown, same structure every time (passages grouped by theme)

No query strategy is specified. The model receives the KB and the question "what in here relates to this spec?" and determines the search approach. This is exactly what worked for Eric's archive problem.

### Reviewer KB access

Reviewers do NOT search the KB independently — they receive the KB Research briefing packet. This:
- Cuts reviewer token cost significantly
- Normalizes context (both reviewers judge against the same passages)
- Makes the briefing visible to Eric in the UI

### Cost Enforcement

- Per-run budget: $0.50 (covers KB Research + dual review + verification)
- Enforced at adapter API layer by summing `usage.total_tokens` from API responses
- Brainstorm and Drafter excluded (DeepSeek bulk, no per-token tracking needed)
- Budget counts: KB Research (V4 Flash), Claude reviewer, GLM reviewer, GLM verifier
- Warning at 75%, hard stop at 100% — pipeline pauses, Eric notified
- Estimated per-run: KB Research ~$0.02 + Dual review ~$0.15 + Verification ~$0.05 = ~$0.22

### Database Migration

Current spine has many tables built during governance-heavy phases. The 4-table design (observations, entities, intentions, verification_queue) replaces them. All existing data — including workflow_runs, deliberation_rounds, build_plan_nodes, ADRs — converts to observations with type tags. Nothing is lost. Nothing is authoritative — observations is an append-only event stream. The model determines relevance at query time.

Safety protocol: backup → create new tables → convert with dry-run → parallel validation (one pipeline cycle) → Eric sign-off → cutover → drop old after 30 days.

## Pipeline Flow

```
Eric ↔ Brainstorm (chat)
    │   Explores intentions broadly, challenges assumptions
    │   Queries KB: "what did Eric try before that failed? what constraints exist?"
    │
    ▼
Eric ↔ Drafter (handoff)
    │   Receives Brainstorm output, queries KB for Eric's intentions
    │
    ▼
[GATE 1: Intention Alignment]
    Drafter presents restatement → Eric watches reasoning stream
    Eric confirms or corrects → Drafter writes spec
    │
    ▼
[KB Research] (autonomous — V4 Flash script)
    Receives spec → queries KB → compiles briefing packet
    │
    ▼ (autonomous)
[Review Phase]
    Claude + GLM receive spec + KB briefing packet
    Each reviews against briefing content + own expertise
    Eric watches both reasoning streams side-by-side
    │
    ▼
[GATE 2: Deliberation Reconciliation]
    Consensus + both raw reviews + KB briefing presented
    Eric checks alignment, approves or refines (portal or Telegram)
    │
    ▼ (autonomous)
[Build Phase]
    Implementer receives approved spec + KB briefing
    Verifier watches build, decides which evidence commands to run
    Eric observes: terminal output, git diffs, test results
    │
    ▼
[GATE 3: Verification Check]
    Verifier evidence output displayed with raw results
    Original intention + KB passages shown alongside
    Eric confirms alignment (portal or Telegram)
```

### Reasoning Stream Format

Normalized to a simple JSON envelope. The model's raw reasoning passes through — the format wraps it, doesn't transform it:

```json
{
  "phase": "deliberation",
  "source": "claude",
  "timestamp": "ISO",
  "reasoning": "raw model reasoning text, unmodified",
  "is_final": false
}
```

DeepSeek uses `reasoning_content` field. Claude and GLM reasoning extracted from API response — both verified working (Claude 4,064 chars, GLM 8,139 chars in test).

### Telegram Gate Protocol

- Notification on gate arrival: summary + raw outputs
- `/approve` — proceeds
- `/revise <notes>` — returns to Drafter
- `/discuss` — Eric wants to talk, pipeline holds
- Timeout: 72 hours, saves state, closes with TIMEOUT
- No partial approval — binary decision prevents ambiguity

### SSE Authentication

SSE endpoints use URL parameter tokens (standard for EventSource API, which doesn't support custom headers). Tokens are session-scoped, expire on pipeline completion or timeout. Port 5000 is LAN/VPN only. Tokens appear in browser history and server logs — mitigated by short lifetime and local-only access.

### Error Handling

- **Model timeout:** SSE drops → auto-retry once, partial output with notice
- **Reviewer hang:** one exceeds 3x first reviewer's time → proceed with single review
- **Both reviewers hang:** pipeline aborts, Eric notified, state saved
- **Malformed spec:** auto-return to Drafter with validation output, one retry
- **Build failure:** verifier captures error, presents to Eric with analysis
- **SSE disconnect:** browser reconnects, resumes from last checkpoint (persisted to observations table every 30 seconds)
- **Adapter failure:** fallback to direct profile routing, Eric notified. SSE observation lost in degraded mode (stated explicitly).

### Concurrent Pipeline

- One active pipeline run at a time
- New intention while active → queued
- Emergency override: Eric kills current pipeline (state saved)
- No parallel runs (cost + complexity)

## What Gets Built

### Phase 0: Database Rebuild

Replace multi-table spine with 4-table design. All existing data converts to observations with type tags. Safety: backup → dry-run → parallel validation → sign-off → cutover → drop after 30 days.

### Phase B: Pipeline Wiring

- Brainstorm profile creation (port 8644, V4 Pro via DeepSeek bulk)
- KB Research script: Python calling OpenRouter V4 Flash, compiles briefing packet
- SSE endpoints for streaming model reasoning
- Bring up adapter API on port 5000 (currently down — first start, not just restart) with SSE endpoints and fallback routing
- Gate routing + cost tracking at adapter layer
- Telegram gate integration
- Profiles 8647 (glm-reviewer) and 8648 (glm-verifier) are already running — wire into pipeline routing

### Phase A: Control Plane UI

1. **Brainstorm + Intention View** — Brainstorm chat, Drafter handoff, KB briefing display, reasoning streams, confirmation card
2. **Deliberation View** — KB briefing packet displayed, split panel reasoning, reconciliation, approve/refine
3. **Verification View** — terminal output, verifier evidence, git diff, intention side-by-side

### Phase C: LXC Workshop

Proxmox LXC on wander (Ubuntu 24.04, 80GB disk, 8GB RAM, 4 cores). Hermes + 7 profiles + portal. CIS repo mounted RO from host. Daily Proxmox snapshots + weekly DB dumps. SSH access, LAN/VPN only. Firewall: observation ports LAN-only. All profiles respect READ_ONLY_STANDING_BY.

## Build Sequence

```
Phase 0 (Database Rebuild) → Phase B (Wiring) → Phase A (UI) → Phase C (LXC)
```

Each phase gates on Eric sign-off before next begins. Failed acceptance → fix before proceeding.

## Acceptance Criteria

1. Brainstorm explores intentions broadly before Drafter converges
2. Eric watches Brainstorm and Drafter reasoning streams in real time
3. Intention restatement confirmation via portal and Telegram
4. KB Research compiles briefing packet (model-driven, no query strategy specified)
5. Reviewers receive same KB briefing — no independent KB queries
6. Reviewers' reasoning streams visible simultaneously
7. Reconciliation presents raw reviewer output
8. Eric approves/refines from portal or Telegram at each gate
9. Implementer terminal output streams to verification view
10. Verifier evidence commands + raw outputs displayed
11. Gates timeout at 72 hours, pipeline saves state cleanly
12. Gate decisions + reviewer outputs + reasoning persisted to observations
13. Per-run cost tracked, $0.50 hard stop at adapter layer
14. Adapter failure falls back to direct routing (SSE lost, stated explicitly)
15. Database migration: backup → dry-run → validate → sign-off → cutover
16. LXC created on wander, daily snapshots + weekly backups
17. All profiles respect READ_ONLY_STANDING_BY
18. Single pipeline active, queue visible, emergency kill available
19. Anti-bias rule enforced: reviewers must justify objections with evidence from Eric's words, not enterprise architecture patterns

## Out of Scope

- Autonomous execution without gates
- Voice interaction
- Multi-project support
- Real-time mobile observation (mobile = gate confirmations only)
- Extraction pipelines, query strategies, tagging systems, or pre-defined data paths — the model handles these
