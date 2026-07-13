# Model Roles and Protocol — CIS Advisor Loop
Generated: 2026-07-13 18:09 UTC | Run: run-237494fd693c
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## PURPOSE OF THIS FILE — READ FIRST

This packet is REFERENCE CONTEXT for external advisors (Claude, ChatGPT). It
exists so that when the user escalates a question, the advisor understands the
pipeline's vocabulary — what "Drafter," "Reviewer," "Implementer," and the
gateway ports refer to.

It is NOT a rulebook for the user, and it is NOT instructions for the advisor to
enforce.

Per ADR-SEED-008 and the DEV-PIVOT-01 governance reset:
- These role and protocol descriptions describe INTENDED FINISHED-APP behavior.
- They are implemented (when implemented at all) as software affordances in the
  CIS application — database constraints, UI gates, routing — NOT as manual
  process the user performs by hand, and NOT as conduct an advisor should police.
- The user routes work however is convenient. They are not bound by the role matrix.
  Do not tell them which profile to use, do not flag "role confusion," do not
  warn them about manual steps. That ceremony was explicitly retired for the
  operator.

The ONLY operator-facing rules that survive the reset are:
  1. Do not destroy files or data.
  2. Do not claim completion without evidence (raw output, not summaries).
  3. Build the smallest working application path.

Advisor instruction: use the role names below ONLY to interpret what the user means
when they reference them. Treat everything in this file as vocabulary, not law.

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

| Brain | hermes-brainstorm | 8644 | — |
| Draft | hermes-v4pro | 8645 | Proposal author. Drafts, does not build |
| Review1 | hermes-r1 | 8643 | Adversarial challenge. OBJECTIONS or CONSENSUS_REACHED |
| Review2 | hermes-glm-reviewer | 8647 | — |
| Menter | hermes-v4impl | 8646 | Executes FINAL_DIRECTIVE only. No deliberation |
| Verify | hermes-glm-verifier | 8648 | — |
| Prime/Chat | hermes-prime | 8642 | Evidence firewall (NeMo) + topic grounding |

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
