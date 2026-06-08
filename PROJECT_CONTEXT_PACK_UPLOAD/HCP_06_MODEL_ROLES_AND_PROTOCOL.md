# Model Roles and Protocol — CIS Advisor Loop
Generated: 2026-06-08 21:30 UTC | Run: run-c40ec6dce649
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## Role Identity Rule

**Role identity must be derived from HERMES_HOME and gateway endpoint, not from briefing text or model self-description.**
Terminal sessions must print HERMES_HOME before any FINAL_DIRECTIVE.
Implementation directives route only to hermes-v4impl port 8646.

## CIS Pipeline Roles

| Label | Profile | Port | Function |
|-------|---------|------|----------|

| Flash/Research | hermes-prime | 8642 → NeMo 8800 | Evidence firewall (NeMo) + topic grounding |
| V4 Drafter | hermes-v4pro | 8645 | Proposal author. Drafts, does not build |
| V4 Reviewer | hermes-r1 | 8643 | Adversarial challenge. OBJECTIONS or CONSENSUS_REACHED |
| V4 Implementer | hermes-v4impl | 8646 | Executes FINAL_DIRECTIVE only. No deliberation |
| Qwen (paused) | hermes-qwen | 8644 | Future judge/evaluator role |

## External Advisor Protocol

| Advisor | Role | Context Source | Authority |
|---------|------|---------------|-----------|

| Hermes | Root operator, pipeline engine | AGENTS.md (native) | Deterministic context owner |
| ChatGPT | External advisor, escalation reviewer | Generated HCP exports | Review, consult. No execution |
| Claude | External advisor, proposal author | Generated HCP exports | Review, consult, draft proposals when asked |

## Pipeline Protocol

1. **TRIAGE:** Router creates Kanban card, assigns Research profile
2. **RESEARCH → DRAFT → REVIEW ↔ LOOP:** Adversarial deliberation. 2-3 rounds typical before CONSENSUS_REACHED
3. **CONSENSUS_REACHED:** Structured Reviewer signal meaning no material objections remain
4. **ERIC_GATE:** Eric reviews resolved proposal. Pass → IMPLEMENT. Redirect/Insight → DRAFT
5. **IMPLEMENT:** V4 Implementer executes FINAL_DIRECTIVE only
6. **VERIFY:** Deterministic scripts check evidence independently
7. **STATE_WRITE:** Only after VERIFY PASS. Writes to SQLite, triggers export, git commit

## Why V4 Models are Direct (not through NeMo)

NeMo's response pipeline strips `reasoning_content` and `reasoning_tokens` from
DeepSeek thinking models (Gate 5C). V4 Drafter/Reviewer/Implementer are routed direct.
NeMo preflight is used for evidence collection only.

## Verification-Hardening Rule (2026-05-31)

**V4 Implementer self-report is not a source of truth.** Completion is accepted only after
deterministic evidence. Accepted evidence: git diff, test output, DB queries, endpoint
responses, service health, browser/UI state, independent reviewer pass/fail.

## Evidence-Backed Response Rule

**Evidence-Backed Response Rule**

CIS must not rely on trust-based agent self-reporting.
Every consequential agent response must be accompanied by:
1. Raw local evidence: command output, git status/show, file contents,
   DB query output, test output, artifact path plus verification.
2. External research evidence: cited source, document reference,
   quoted or summarized source material with citation.
Agent summaries may follow evidence, but must not replace it.
Claims such as "passed," "clean," "unchanged," "verified," "no mutation,"
"ready to commit," or "complete" are incomplete unless accompanied by evidence.
Report pattern: command/source → raw evidence → interpretation.
The operator should not be required to manually rerun routine verification
commands unless Hermes lacks access, the command requires operator-only credentials,
or an external advisor explicitly requests independent human verification.
The verification-hardening rule is the V4 Implementer-specific application of
this general principle.

## Exact-Format Instruction Rule

**Exact-Format Instruction Rule**

When requesting evidence or verification from a CIS agent, do not include
optional labels or extra explanatory categories that can be interpreted as
alternatives to raw evidence. Use only the exact structure required.

Preferred evidence format:

COMMAND: <exact command>

OUTPUT: <full raw terminal output>

Repeat for each command.

FINAL: Proceed / Blocked — one sentence.

Do not ask for "interpretation," "summary," "result," "evidence reference,"
or "short explanation" when raw command output is required. Those words can
cause the agent to summarize instead of pasting evidence.

This rule ensures external advisors (ChatGPT, Claude) request evidence in a
format that produces machine-verifiable output rather than narrativized
summaries.

## Kanban Contingency

Kanban is preferred for pipeline coordination. `kanban.db` is shared
across profiles. If Kanban is profile-scoped or unavailable, pipeline uses Flask/CIS
database task tables as the coordination layer.
