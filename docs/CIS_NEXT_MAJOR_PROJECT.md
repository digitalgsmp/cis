# CIS Next Major Project — Hermes Integration Push

**Logged:** 2026-06-17 | **Source:** Eric directive | **Status:** PENDING

## Overview

The next major push integrates all CIS components into Hermes' native framework,
future-proofs against Hermes updates, transitions oversight from external scripts
into agent-native harness, and overhauls the UI.

## 1. CIS → Hermes Framework Integration

All CIS components should register on Hermes primitives rather than existing as
parallel custom code:

| CIS Component | Current | Target (Hermes v0.16.0) |
|--------------|---------|-------------------------|
| Pipeline (Drafter/Reviewer/Implementer) | Bash + Python scripts in repo | Hermes profiles with role-specific skills |
| Eric Gate | Manual Telegram approval | Hermes cron + messaging pipeline |
| Deliberation (R1+Qwen) | `reviewer_reconcile.py` calls API directly | MCP-based coordination between profiles |
| Gates | Bash scripts in `tools/gates/` | Hermes skills loaded by agent harness |
| AGENTS.md regeneration | `generate_agents_md.py` from spine | Hermes dashboard view + auto-regenerate cron |
| Closeout triggers | Manual | Hermes cron scheduler |
| Staleness check | `staleness_check.py` + DDG | Hermes web_search tool + cron watchdog |
| UI (Tier 10) | Flask + React custom stack | Hermes dashboard extensions or MCP views |

## 2. Abstraction Layer — Future-Proof Against Hermes Updates

Per Claude's recommendation: build a middleware layer between CIS methodology
and Hermes implementation. When Hermes ships v0.17.0+:

- CIS methodology (adversarial review, FINAL_JSON, Eric Gate, verification hardening)
  stays stable — it's the protocol, not the implementation.
- The implementation layer adapts to new Hermes primitives without changing CIS
  behavior.
- Example: Profiles system obsoletes 4-independent-installs migration. The
  abstraction layer decides which Hermes feature to use, CIS doesn't care.

**Design:** CIS defines what it needs (multi-model deliberation, evidence-backed
verification). The adapter layer maps those needs to current Hermes features.
When Hermes changes, only the adapter changes.

## 3. Oversight Transition — Bash Gates → Agent Harness

Current: Gates are external bash scripts. Agents can bypass them (as demonstrated
2026-06-17 — `generate_agents_md.py` run directly without oversight firing).

Target: Oversight is baked into the agent's tool-call harness. Before any
`write_file`, `patch`, `terminal git commit`, or `sqlite3 INSERT`, the agent
checks: "Has this action been through oversight?"

Implementation options:
- **CIS oversight skill** (`.hermes-r1/skills/`): Loaded automatically in CIS
  working directory. Hooks tool calls. Enforces gate sequence at agent level.
- **Hermes profile constraints**: Implementer profile has no `write_file` tool
  until Reviewer profile returns CONSENSUS_REACHED.
- **Pre-commit/CI hooks**: Catch bypasses at the repo level (defense in depth).

## 4. Refactoring for Hermes v0.16.0 Features

| v0.16.0 Feature | CIS Adoption |
|----------------|-------------|
| Profiles (isolated config/model/gateway per role) | Collapse 5 installs → 1 install with 5 profiles. Per-profile model assignment via model picker. |
| Skills marketplace (agentskills.io) | Publish CIS pipeline as "CIS Adversarial Pipeline" bundle. Install once, propagate to all profiles. |
| Web dashboard | Expose pipeline state (deliberation rounds, gate status, Eric Gate) as dashboard extensions. |
| Cron scheduler | Replace custom closeout trigger code with `hermes cron "Check stale workflow_runs" every 4h`. |
| Sub-agent delegation | Implementer spawns parallel workers for builds. Reviewer spawns audit sub-agents. |
| MCP client/server | Each profile exposes state via MCP. Orchestrator queries through MCP instead of custom HTTP. External advisors connect via MCP. |
| Model picker | Assign different models per profile for adversarial diversity (different training blind spots). |
| Multi-platform messaging | Eric Gate approval requests arrive on any platform. Closeout notifications follow Eric. |

## 5. UI Overhaul — Display Hermes Infrastructure

The Tier 10 CIS UI needs to display the Hermes framework that CIS now tracks:

- **Gateway status dashboard**: All profiles (ports, models, health). Live.
- **Deliberation view**: R1 vs Qwen side-by-side, objection cross-feed, consensus history.
- **Staleness feed**: Which tools are behind, last checked, versions.
- **Profile manager**: CRUD for Hermes profiles, model assignment, skill loading.
- **Pipeline timeline**: Build plan nodes → deliberation rounds → Eric Gate → implement → closeout.

Prefer Hermes dashboard extensions over custom React. If dashboard plugins aren't available, expose via MCP and use any MCP client.

## 6. Dependency Notes

- **BLK-SEED-005**: hermes-gateway-r1.service must be stabilized before profile-based migration.
- **OQ-SEED-007**: 4-independent-installs migration may be obsoleted by profiles — evaluate.
- **OQ-SEED-006**: deliberation_rounds needs reviewer_output column before MCP exposure.
- **ADR-SEED-010**: Project isolation model (--project-root) applies — don't couple CIS to a single Hermes install.

## 7. Out of Scope (This Push)

- VDB pipeline rebuild
- Briefing Center UI redesign
- Discord/Telegram gateway (CIS uses Hermes messaging, not custom)
- Schedule field-use work (SWA)
- CIS Foundation Build Plan Phases 1-3

## 8. Milestones

| Phase | Description | Depends On |
|-------|-------------|------------|
| M1 | CIS oversight skill (agent-harness enforcement) | None |
| M2 | Profiles evaluation — can 5 installs → 1? | OQ-SEED-007 resolution |
| M3 | Abstraction layer design (CIS ↔ Hermes adapter) | M3 |
| M4 | Gate migration (bash → skills) | M1, M2 |
| M5 | UI overhaul (dashboard extensions or MCP views) | M2 |
| M6 | Hermes v0.16.0 refactoring pass | M2, M3 |

## 9. Immediate Next Action

Build the **CIS oversight skill** — the agent-harness level enforcement that prevents
direct tool-call bypass of the gate sequence. This is the single highest-leverage
item: once the skill exists, no agent working in the CIS repo can circumvent oversight.

See also: conversation 2026-06-17 where `generate_agents_md.py` was run directly,
bypassing gate_runner.sh — proving the need for harness-level enforcement.
