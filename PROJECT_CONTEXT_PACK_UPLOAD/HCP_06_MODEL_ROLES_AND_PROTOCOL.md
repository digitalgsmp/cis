# Model Roles and Protocol — CIS Advisor Loop
Generated: 2026-06-17 04:25 UTC | Run: run-bb3dfcb72059
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## Role Identity Rule

**Role identity must be derived from HERMES_HOME and gateway endpoint, not from briefing text or model self-description.**
Terminal sessions must print HERMES_HOME before any FINAL_DIRECTIVE.
Implementation directives route only to hermes-v4impl port 8646.

## READ_ONLY_STANDING_BY Startup Protocol

**READ_ONLY_STANDING_BY Startup Protocol**

On fresh session start, context handoff, or ambiguous startup/orientation prompt,
Hermes enters READ_ONLY_STANDING_BY mode. In this mode Hermes may only read context
and run inspection-only commands to confirm HEAD, dirty status, current completed
tier, and next allowed action. Inspection-only commands are: git status, git rev-parse,
grep, sed, cat, sqlite3 SELECT, and file listing. Hermes must not modify files, run
imports, apply migrations, patch code, alter databases, stage files, commit, or start
implementation. Hermes exits READ_ONLY_STANDING_BY only after Eric gives an explicit
execution instruction, such as PROCEED, IMPLEMENT, FINAL_DIRECTIVE, or an unambiguous
approval to perform a specific action. The required startup response ends with
"Standing by" and no next action is executed. This rule applies to all active Hermes
profiles regardless of which profile receives the session start signal.

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

1. **TRIAGE:** Router creates workflow_run, assigns Research profile
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

## Pipeline Contingency

Kanban is retired as pipeline transport (ADR-013). workflow_runs is the
authoritative in-flight work object. If the Flask API is unavailable,
pipeline coordination falls back to direct SQLite spine access.
Implementation evidence is stored in workflow_run_artifacts.
Eric approval is recorded in workflow_runs.eric_approved_at.
Approval setter (UI/API/CLI) is pending Foundation Hardening Phase.

## Escalation Advisor Integration Protocol (Component 2)

### Escalation Advisor Integration Protocol (Component 2, APPROVED)

Component 2 defines the formal boundary between the Hermes operational layer
and the external escalation advisor layer (Claude, ChatGPT).

**Advisor authority limits:**
- Claude and ChatGPT are escalation advisors only.
- No execution authority. No spine write access. No directive authority.
- An advisor response is never a FINAL_DIRECTIVE and must never be pasted to v4impl as one.
- Output is advisory input to Eric's reconciliation only.

**Trigger conditions:**
- Discretionary: Eric requests external audit at any time.
- Mandatory: open drift indicators, deliberation exhaustion (max rounds without consensus),
  verification failure twice on same scope, unresolved/dismissed objections,
  governance-tier work (Tier 6+), Eric mandate.
- A mandatory escalation blocks progression to implementation until RECONCILED or Eric-cancelled.

**Packet format (P0-P6):**
- P0: Header — escalation_id, version, git HEAD, advisor target, trigger class, hash.
- P1: Project position from spine project_state.
- P2: Spine state excerpt — workflow_run, deliberation rounds, active blockers.
- P3: Provenance records — goal references, decision trails, drift indicators, rejection rationale.
- P4: The exact question — one explicit ask, requested response type.
- P5: Constraints — advisor authority limits, Exact-Format Instruction Rule, scope fence.
- P6: Evidence appendix — raw terminal output.

**Response lifecycle:**
EXPECTED → TRANSMITTED → RECEIVED → INGESTED → CLASSIFIED.
Responses stored verbatim. Classification via deterministic tooling (PROPOSED),
confirmed or corrected by Eric (CONFIRMED/CORRECTED). Eric is final authority.

**Reconciliation:**
Eric records disposition (ACCEPT/ACCEPT_WITH_MODIFICATION/REJECT/RETURN_TO_DRAFT/ESCALATE_FURTHER)
with plain-language note. For BOTH-advisor escalations where advisors diverge,
captures divergence summary and structured positions.

**Terminal states:** ABANDONED, SUPERSEDED, CANCELLED_BY_ERIC — all require reason fields.

**Current path:** Manual copy-paste. Builder assembles packet from spine; Eric transmits;
response ingested via CLI tool. Eric remains sole transmitter and reconciler.

**Future path (Tier 8):** API transport replaces copy-paste. Contract unchanged.
Eric's reconciliation is never automated.
