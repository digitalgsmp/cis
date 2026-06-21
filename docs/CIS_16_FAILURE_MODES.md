# CIS 16 LLM Failure Modes

Source: DEV-PIVOT-05 §2.1–2.4. These are LLM behavior failures, not future app features.
Enforcement must be deterministic and live OUTSIDE the constrained agent.

## Trust Failures (1-3)

| # | Failure | How CIS Prevents It |
|---|---------|---------------------|
| 1 | Self-reported completion without evidence | Verification Hardening Rule: git diff, test output, DB queries required |
| 2 | Hallucinated claims masquerading as facts | Evidence-Backed Response Rule: raw terminal output pasted, not summarized |
| 3 | Rubber-stamp reviews | Dual-reviewer deliberation (R1+Qwen) with cross-feed objections |

## Knowledge Failures (4-6)

| # | Failure | How CIS Prevents It |
|---|---------|---------------------|
| 4 | Training-data staleness | Staleness gate: web freshness check before deliberation |
| 5 | Context amnesia across sessions | SQLite spine + AGENTS.md + HCP exports |
| 6 | Version drift in static configs | generate_agents_md.py regenerates from DB source of truth |

## Process Failures (7-12)

| # | Failure | How CIS Prevents It |
|---|---------|---------------------|
| 7 | Scope creep by implementer | Approved File Manifest enforced during implementation |
| 8 | Constraint bypass through placeholder data | NOT NULL FKs enforced with 409 rejection, no auto-create |
| 9 | Pipeline bypass (agents calling scripts directly) | Gate sequence in gate_runner.sh before Eric approval |
| 10 | Role confusion | HERMES_HOME + gateway endpoint derive role, not model self-description |
| 11 | Silent gate failures | PASS/FAIL criteria, numbered checks, COMMAND/OUTPUT evidence format |
| 12 | Concurrency races | Atomic UPDATE...WHERE + rowcount checks in dispatch scripts |

## Protocol Failures (13-16)

| # | Failure | How CIS Prevents It |
|---|---------|---------------------|
| 13 | Unstructured model output | FINAL_JSON required on every Drafter/Reviewer response |
| 14 | Missing FINAL_JSON | Repair prompt, then fallback text scanning |
| 15 | Cross-model agreement without genuine deliberation | Objections cross-fed between reviewers; must address each |
| 16 | Single-model blind spots | Two independent reviewers with different models (R1 + Qwen) |
