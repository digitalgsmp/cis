# TG-PIPE: Telegram Pipeline Interface Spec v1.0

**Status:** DRAFT — for Eric review
**Author:** Hermes (V4Pro Drafter)
**Date:** 2026-07-26
**Replaces:** Container-based orchestrator pipeline (temporary — not deleted, just sidelined)

---

## 1. Problem Statement

The containerized orchestrator pipeline (Brain→Draft→Review1→Review2→Impl→Verify) works technically but doesn't ship projects. Every session where real progress happened followed a different pattern: **Eric manually routing between models, copy-pasting between Claude and ChatGPT, and making judgment calls at every step.**

The missing element is Eric's direct involvement. The automated pipeline treats Eric as a gate (approve/reject). The working pattern treats Eric as the **conductor** — he decides which model does what, when to escalate to external advisors, and when to reframe the problem entirely.

This spec defines a Telegram-based pipeline interface that formalizes the working pattern instead of replacing it.

---

## 2. Core Principle: Eric Is the Orchestrator

**Not a gate. Not a reviewer. The conductor.**

The pipeline does not run autonomously. It presents structured output at each step and waits for Eric's direction. Eric can:

- Approve and advance to the next step
- Reject with reframing (send it back with new instructions)
- Escalate to external advisors (copy-paste to Claude/ChatGPT, paste results back)
- Skip steps (e.g., go straight to implement for simple tasks)
- Interject at any point

The system's job is to make Eric's routing decisions **fast and low-friction** — not to make those decisions for him.

---

## 3. Architecture: Three-Bot Telegram Group

### 3.1 Physical Layout

```
┌─────────────────────────────────────────────────┐
│              CIS Pipeline (Telegram Group)        │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │          │  │          │  │          │       │
│  │  BRAIN   │  │   GATE   │  │ VERIFY   │       │
│  │  Bot     │  │   Bot    │  │  Bot     │       │
│  │          │  │          │  │          │       │
│  │ DeepSeek │  │  GLM 5.2 │  │ GLM 5.2  │       │
│  │ V4 Pro   │  │          │  │          │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │              │
│       └─────────────┼─────────────┘              │
│                     │                            │
│               ERIC (human)                       │
│               + Claude (copy-paste)              │
│               + ChatGPT (copy-paste)             │
└─────────────────────────────────────────────────┘
```

### 3.2 Bot Assignments

| Bot | Model | Provider | Role | Telegram Token Profile |
|-----|-------|----------|------|------------------------|
| **Brain** | deepseek-v4-pro | DeepSeek API | Spec drafting, decomposition, architecture | `hermes-brainstorm` (port 8644) |
| **Gate** | glm-5.2 | GLM/Z.AI API | Implementation + Eric approval tracking | `hermes-v4impl` (port 8646, repurposed) |
| **Verify** | glm-5.2 | GLM/Z.AI API | Evidence verification, diff checking | `hermes-glm-verifier` (port 8648) |

**Retired from Telegram pipeline (but kept running for API access):**
- `hermes-r1` (port 8643) — Claude Reviewer. Removed from pipeline. Eric copy-pastes to Claude web UI instead.
- `hermes-glm-reviewer` (port 8647) — GLM Reviewer. Removed from pipeline. Eric copy-pastes to ChatGPT web UI instead.
- `hermes-v4pro` (port 8645) — Drafter. Role folded into Brain bot.

> **Why this split:** DeepSeek is stronger at reasoning, architecture, and spec writing. GLM 5.2 is stronger at code generation and structured output. Using each for what it's best at, with Eric routing between them.

### 3.3 Review Replacement Strategy

The automated dual-reviewer loop (Review1 + Review2 → consensus) is replaced with:

1. **Eric's judgment** — He reads Brain's output. If it looks right, he approves. If not, he reframes.
2. **External advisor escalation** — When Eric wants a second opinion, he copy-pastes Brain's output to Claude (web UI) and/or ChatGPT (web UI), then pastes their feedback back into the Telegram group.
3. **Verifier as sanity check** — After implementation, Verify checks the actual git diff/files against the approved spec. No "trust me" self-reports.

This is faster, cheaper (no OpenRouter markup on review models), and matches the pattern that actually ships work.

---

## 4. Pipeline Flow (Step by Step)

### Step 0: Eric Submits Intent

```
Eric: /new "Add rate limiting to the API relay"
```

System creates a task record in SQLite with status `INTENT_SUBMITTED`.

### Step 1: Brain Drafts Spec

Brain receives the intent + project context. Produces:

```markdown
## Spec: Add Rate Limiting to API Relay

### What
Add per-IP rate limiting to /api/relay/* endpoints.

### Scope
- File: runtime/api/relay.py
- New dependency: flask-limiter
- Default: 60 req/min per IP

### Acceptance Criteria
1. curl test: 61st request in 60s returns 429
2. Rate limit header present on responses
3. Configurable via env var

### Risks/Unknowns
- Flask-Limiter uses in-memory storage by default (lost on restart)
- Need to decide: Redis backend or accept in-memory?

### Eric Decision Required
[ ] APPROVE — proceed to implement
[ ] REFRAME — (provide new instructions below)
[ ] ESCALATE — copy to external advisor first
[ ] ASK — I have a question (type below)
```

**Token efficiency measures:**
- No "I hope this finds you well" fluff
- Structured template, not freeform
- Decision checklist at the bottom
- Project context injected once at session start, not repeated

### Step 2: Eric Reviews

Eric reads the spec. He can:

- **Approve:** Reply `/approve` or just say "go"
- **Reframe:** Reply with new instructions — Brain regenerates
- **Escalate:** Copy Brain's spec to Claude/ChatGPT, paste feedback back, then `/approve` or `/reframe`
- **Ask:** Reply with a question — Brain answers, spec stays open

This is where Eric's judgment is the catalyst. He knows when a spec is "good enough to code" vs "needs more thinking" — a heuristic models don't have.

### Step 3: Gate Implements

On Eric's approval, Gate (GLM 5.2) receives:

1. The approved spec
2. The relevant file paths
3. Any constraints from Eric

Gate produces:
- Code changes (via patch/file write)
- A summary of what changed
- Test commands to run

Gate does NOT self-report success. It produces artifacts, then steps aside.

### Step 4: Eric Verifies (or Delegates to Verify)

Eric can:
- Run the test commands himself
- Ask Verify to check: `/verify`
- Do both

Verify bot checks:
- `git diff` — do the changes match the spec scope?
- Test output — do the tests pass?
- File state — were the right files modified?

Verify produces an evidence report:

```markdown
## Verification Report: Rate Limiting

### Scope Match
✓ Only relay.py modified (matches spec)
✗ requirements.txt also modified (not in spec — flagging)

### Test Results
✓ curl test: 429 received on 61st request
✓ Rate limit header: X-RateLimit-Remaining present

### Verdict
PASS WITH NOTE — requirements.txt change should be documented
```

### Step 5: Eric Closes or Continues

Eric marks the task complete: `/done` or continues with `/continue "also add..."`

---

## 5. Task Tracking

### 5.1 Data Model (SQLite)

```sql
CREATE TABLE tg_pipeline_tasks (
    id TEXT PRIMARY KEY,              -- uuid
    project TEXT NOT NULL,            -- e.g., "cis", "swa", "wiast"
    intent TEXT NOT NULL,             -- Eric's original intent
    status TEXT NOT NULL,             -- see state machine below
    brain_output TEXT,                -- Brain's spec (markdown)
    brain_approved_at TEXT,           -- timestamp
    brain_reframe_count INTEGER DEFAULT 0,
    gate_output TEXT,                 -- Gate's implementation summary
    gate_diff_summary TEXT,           -- which files changed
    verify_output TEXT,               -- Verify's evidence report
    verify_verdict TEXT,              -- PASS / FAIL_WITH_NOTES / FAIL
    eric_notes TEXT,                  -- Eric's comments at each step
    external_review_input TEXT,       -- what was sent to Claude/ChatGPT
    external_review_output TEXT,      -- what came back
    created_at TEXT,
    updated_at TEXT,
    completed_at TEXT
);

CREATE TABLE tg_pipeline_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    step_name TEXT NOT NULL,          -- INTENT, BRAIN_DRAFT, ERIC_REVIEW, GATE_IMPL, VERIFY, DONE
    actor TEXT NOT NULL,              -- eric, brain, gate, verify, claude, chatgpt
    content TEXT,                     -- message content
    decision TEXT,                    -- APPROVE, REFRAME, ESCALATE, ASK (for Eric steps)
    created_at TEXT,
    FOREIGN KEY (task_id) REFERENCES tg_pipeline_tasks(id)
);
```

### 5.2 Status State Machine

```
INTENT_SUBMITTED
    │
    ▼
BRAIN_DRAFTING          ←── Eric reframes
    │
    ▼
AWAITING_ERIC_REVIEW    ←── Eric escalates to external
    │                         (status doesn't change, step logged)
    ├── Eric approves ──────▶ GATE_IMPLEMENTING
    ├── Eric reframes ──────▶ BRAIN_DRAFTING (reframe_count++)
    └── Eric asks ──────────▶ AWAITING_ERIC_REVIEW (question answered, stays)
                                   │
                                   ▼
                            GATE_IMPLEMENTING
                                   │
                                   ▼
                            AWAITING_VERIFICATION
                                   │
                            ┌──────┴──────┐
                            ▼              ▼
                         COMPLETE       Eric reframes → GATE_IMPLEMENTING
```

### 5.3 Telegram Commands

| Command | Who Uses | What It Does |
|---------|----------|--------------|
| `/new <intent>` | Eric | Submit new task |
| `/list [project]` | Eric | List active tasks |
| `/status [task_id]` | Eric | Show current task state + step history |
| `/approve` | Eric | Approve current step, advance pipeline |
| `/reframe <new instructions>` | Eric | Send back with new framing |
| `/escalate` | Eric | Mark as escalated (logs step, waits) |
| `/ask <question>` | Eric | Ask current bot a question |
| `/verify [task_id]` | Eric | Trigger verification |
| `/done` | Eric | Mark task complete |
| `/diff [task_id]` | Eric/Verify | Show git diff for task |
| `/trace [task_id]` | Eric | Show full step history |
| `/brain <question>` | Eric | Direct query to Brain (outside pipeline) |
| `/gate <instruction>` | Eric | Direct query to Gate (outside pipeline) |
| `/help` | Anyone | Show commands |

---

## 6. Token Efficiency Design

### 6.1 The Problem

Current pipeline burns tokens on:
- Long system prompts with CIS governance
- Redundant context (project background in every message)
- Reviewers re-explaining what the Drafter already said
- Consensus-building boilerplate
- "I am a large language model trained by..." disclaimers

### 6.2 Solutions

**Minimal role prompts.** Each bot gets a 2-3 sentence role definition, not a constitution:

```
Brain system prompt: "You are the CIS Brain. Your job: take Eric's intent,
ask clarifying questions if needed, then produce a structured spec with
scope, acceptance criteria, risks, and a decision checklist. Be concise.
Do not implement. Do not review your own output."
```

```
Gate system prompt: "You are the CIS Gate. Your job: implement exactly what
the approved spec says. Produce code changes and test commands. Do not design.
Do not question the spec. If the spec is ambiguous, ask Eric — do not guess."
```

```
Verify system prompt: "You are the CIS Verifier. Your job: compare the
implementation against the approved spec using deterministic evidence
(git diff, test output, file state). Report what matches and what doesn't.
Do not re-litigate design decisions."
```

**Project context injected once.** When Eric says `/new`, the system loads the relevant AGENTS.md or project context and sends it as the first message. Subsequent steps reference the task, not the full context.

**Structured output, not prose.** Every bot output follows a template. Eric knows where to look for scope, risks, and the decision checklist. No hunting through paragraphs.

**No deliberation loops.** Brain writes spec. Eric reads it. Done. No "Reviewer 1 says X, Reviewer 2 says Y, now let's reconcile." Eric is the reconciler.

**External advisor context is explicit.** When Eric copy-pastes to Claude/ChatGPT, he sends only the relevant spec section — not the entire pipeline history. The `/escalate` command formats a clean export for external use.

---

## 7. The "Eric Pattern" — What Needs Harnessing

### 7.1 What Eric Brings (That Scripts Don't)

From the session history and Eric's own description, the pattern is:

1. **Triage judgment** — Eric knows when a task is "just do it" vs "needs a spec" vs "needs external review." Models default to spec-everything.

2. **Reframing instinct** — When a model gets stuck or produces something off-target, Eric doesn't debug the prompt. He reframes the problem. "Don't build a rate limiter — just add a decorator that counts requests." This reframing shortcut is faster than any prompt-engineering loop.

3. **External escalation intuition** — Eric knows which advisor (Claude vs. ChatGPT) to ask for which kind of problem. Claude for architecture, ChatGPT for code patterns. This routing intuition is earned, not automated.

4. **Progress-over-perfection instinct** — Eric knows when a spec is "good enough to start coding" even if it has open questions. Models want to resolve all unknowns first.

5. **Stuck-detection** — Eric recognizes when a model is spinning (repeating itself, over-engineering, losing the plot) and kills the loop. Automated orchestrators don't have this instinct.

### 7.2 What CAN Be Scripted

While Eric's judgment can't be fully automated, these supporting patterns can be scripted:

**Decision capture.** Every Eric decision (approve, reframe, escalate, ask) is logged with timestamp and context. Over time, this builds a dataset of "what Eric would do" that could inform future automation.

**Context packaging for external advisors.** When Eric escalates, the system should export a clean, self-contained brief:

```markdown
## External Review Request

### Original Intent
[Eric's intent]

### What Brain Produced
[Brain's spec]

### What Eric Is Unsure About
[Eric's specific question for the external advisor]

### Relevant Code/Context
[trimmed to what's needed]
```

**Stuck-detection heuristics.** Simple rules that flag potential spinning:
- Bot produces 3+ messages without Eric interjecting → pause and ask "continue or reframe?"
- Bot's output is >80% similar to its previous output → flag as potential loop
- Bot asks more than 2 clarifying questions → suggest Eric reframe

**Reframe history.** When Eric reframes, the system records the before/after. Over time, this builds a library of "here's how Eric reframed similar problems" that could be suggested proactively.

### 7.3 What Stays Manual (By Design)

- Eric deciding whether to approve, reframe, or escalate
- Eric reading and judging output quality
- Eric copy-pasting to/from external advisors
- Eric deciding when a task is "done"

---

## 8. Implementation Plan

### Phase 1: Bot Configuration (1-2 hours)

1. **Repurpose existing bots:**
   - `hermes-brainstorm` (port 8644) → Brain Bot. Already has Telegram token. Update system prompt.
   - `hermes-v4impl` (port 8646) → Gate Bot. Already has Telegram token. Switch model to GLM 5.2, update system prompt.
   - `hermes-glm-verifier` (port 8648) → Verify Bot. Already configured with GLM 5.2. Update system prompt.

2. **Disable Telegram on retired pipeline bots:**
   - `hermes-r1` (port 8643) — Remove TELEGRAM_BOT_TOKEN from .env. Keep gateway running for API access.
   - `hermes-glm-reviewer` (port 8647) — Remove TELEGRAM_BOT_TOKEN from .env. Keep gateway running for API access.
   - `hermes-v4pro` (port 8645) — Keep as-is (Eric's main chat). Optionally repurpose or leave.

3. **Create Telegram group "CIS Pipeline"** and add Brain, Gate, Verify bots.
4. **Disable privacy mode** for all three bots (so they can see each other's messages).

### Phase 2: Pipeline Logic (2-4 hours)

1. **Create task tracking database:**
   - SQLite file at `/mnt/projects/cis/data/tg_pipeline.db`
   - Schema from Section 5.1

2. **Create pipeline handler** (Python script or cron job):
   - Location: `/mnt/projects/cis/tools/tg_pipeline/handler.py`
   - Watches for `/new` commands → creates task → sends to Brain
   - Routes messages between bots based on task state
   - Logs all steps to database

3. **Create slash command handlers:**
   - `/new`, `/approve`, `/reframe`, `/escalate`, `/verify`, `/done`, `/list`, `/status`, `/trace`
   - These can be implemented as a lightweight bot or as slash commands registered with each bot

### Phase 3: Scripts & Harnessing (2-3 hours)

1. **External advisor export script:**
   - `/mnt/projects/cis/tools/tg_pipeline/export_for_external.py`
   - Formats current task state as a clean markdown brief for Claude/ChatGPT

2. **Stuck-detection watchdog:**
   - `/mnt/projects/cis/tools/tg_pipeline/stuck_watchdog.py`
   - Monitors pipeline steps for spinning/looping patterns
   - Alerts Eric via Telegram DM if detected

3. **Reframe history logger:**
   - Records every reframe with before/after
   - Builds a searchable library of reframing patterns

### Phase 4: Polish (ongoing)

1. **Task dashboard:** Simple web view or Telegram inline view of all tasks
2. **Cost tracking:** Log token usage per step, surface in `/status`
3. **Project templates:** Pre-load project context for CIS, SWA, etc.

---

## 9. Cost Analysis

### Current Pipeline Cost (per task, estimated)

| Step | Model | Provider | Tokens (est.) | Cost (est.) |
|------|-------|----------|---------------|-------------|
| Brain draft | deepseek-v4-pro | DeepSeek API | 2,000-4,000 | $0.01-0.02 |
| Review1 (Claude) | claude-sonnet-4 | OpenRouter | 3,000-5,000 | $0.03-0.05 |
| Review2 (GLM) | glm-5.2 | OpenRouter | 3,000-5,000 | $0.02-0.04 |
| Consensus loop | both again | OpenRouter | 2,000-4,000 | $0.02-0.04 |
| Implement | deepseek-v4-pro | DeepSeek API | 3,000-6,000 | $0.02-0.04 |
| Verify | glm-5.2 | OpenRouter | 1,000-2,000 | $0.01-0.02 |
| **Total** | | | **14,000-26,000** | **$0.11-0.21** |

### TG-PIPE Cost (per task, estimated)

| Step | Model | Provider | Tokens (est.) | Cost (est.) |
|------|-------|----------|---------------|-------------|
| Brain draft | deepseek-v4-pro | DeepSeek API | 1,500-3,000 | $0.01-0.02 |
| Eric review | human | free | 0 | $0.00 |
| Gate implement | glm-5.2 | GLM/Z.AI API | 2,000-4,000 | $0.01-0.02 |
| Verify check | glm-5.2 | GLM/Z.AI API | 500-1,000 | $0.00-0.01 |
| **Total** | | | **4,000-8,000** | **$0.02-0.05** |

**Savings: 60-75% per task** plus Eric gets results faster because there's no deliberation loop.

External advisor costs (Claude/ChatGPT) are separate — Eric's subscription accounts. These only fire when Eric chooses to escalate, which is not every task.

---

## 10. Open Questions

1. **Pipeline handler architecture:** Should the pipeline logic run as a cron job polling task state, a long-running script, or as slash commands registered natively with each bot? The cron approach is simplest but has latency. Native slash commands are snappiest but require more Hermes integration.

2. **Message routing:** When Eric types in the group, how does the system know which step he's responding to? Options:
   - Context-aware (system tracks current task + step per user)
   - Explicit (Eric always specifies task ID)
   - Hybrid (current task is default, explicit override available)

3. **Brain's project context:** Should Brain load the full AGENTS.md or a trimmed project brief? AGENTS.md is 240 lines — most of it irrelevant to any single task. Recommendation: create per-project brief files (~20 lines) and load those instead.

4. **Error recovery:** What happens if Gate produces broken code? Does Eric reframe (back to Gate) or go back to Brain for a revised spec? The state machine should allow both paths.

5. **Multi-task parallelism:** Can Eric have multiple tasks in flight simultaneously? The data model supports it (task_id is the foreign key), but the Telegram group UX might get confusing with interleaved conversations.

---

## 11. Eric Decision Required

This spec is a DRAFT. Eric needs to:

- [ ] **Confirm the three-bot architecture** (Brain/Gate/Verify)
- [ ] **Confirm retiring Review1 and Review2 from automated pipeline**
- [ ] **Confirm Gate using GLM 5.2** (not DeepSeek) for implementation
- [ ] **Answer Open Question #2**: How should message routing work?
- [ ] **Approve or reframe** the implementation plan
