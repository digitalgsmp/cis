# Hermes Hardening — CIS Guardrail Integration Specification

## Specification Document v2.0 — REVISED DRAFT

## Eric Gate Status: PENDING_APPROVAL

This document defines the architectural direction for hardening the current
5-install Hermes deployment against 16 identified failure modes BEFORE the
profile migration. It is NOT an implementation directive. No code shall be
written, no files modified, and no spine rows updated under this document alone.
Implementation proceeds only after Eric Gate approval is recorded.

**Author:** R1 Reviewer (deepseek-v4-pro) — revised per dual-review findings
**Date:** 2026-06-17
**Revised:** v2.0 — rewired mechanism from skills to shell hooks
**Replaces:** v1.0 (Drafter-authored, 2026-06-17)
**Status:** REVISED DRAFT — awaiting Eric Gate review
**Gating dependency:** None — pre-migration hardening; blocks profile migration phase

---

## 1. Purpose

### 1.1 What this tier solves

The current CIS deployment can be bypassed by any Hermes agent calling tools
directly without going through the gate sequence. Proven 2026-06-17:
`generate_agents_md.py` was run via `terminal()` — no staleness check, no
deliberation, no Eric Gate. The bash gate scripts exist but are voluntary.
Sixteen failure modes from the CIS Integration Assessment remain unaddressed
at the harness level.

### 1.2 Core capability

> **Hermes shell hooks fire a CIS gate script before EVERY write/commit/mutate
> tool call. The script checks the spine. If no valid gate record exists, the
> tool is blocked. Agents cannot bypass — the check runs in the Hermes harness,
> not in the LLM's judgment.**

### 1.3 What changes for Eric

| Before Hardening | After Hardening |
|-----------------|----------------|
| Agents bypass gate_runner.sh by calling tools directly | Shell hook fires BEFORE any write tool executes; blocks if no gate record |
| Oversight is voluntary (manual invocation of bash scripts) | Oversight is automatic — fires on every tool call in CIS directory |
| 16 failure modes are documentation-only concerns | Each failure mode maps to a specific shell hook check |

---

## 2. Access Boundaries

### 2.1 What this specification SHALL touch

| Asset | Permission | Reason |
|-------|-----------|--------|
| Per-profile `config.yaml` (5 files) | Write: add `hooks:` block | Shell hooks are configured in config.yaml |
| `tools/gates/gate_runner.sh` | Read only — invoked by hooks | Existing gate sequence is the canonical audit trail |
| `tools/pipeline/staleness_check.py` | Read only — invoked by hooks | Freshness check runs as part of gate sequence |
| `tools/pipeline/reviewer_reconcile.py` | Read only — invoked by hooks | Dual-review deliberation runs as part of gate sequence |
| `/mnt/projects/cis/data/cis_memory.db` | Read only via sqlite3 in hook scripts | Hooks query spine for gate state |
| `tools/hooks/cis_pre_tool_gate.sh` | Create (new) | The single hook script all profiles point at |

### 2.2 What this specification SHALL NOT touch

| Asset | Reason |
|-------|--------|
| Hermes source code (run_agent.py, deepseek/__init__.py, etc.) | Source fragility resolved after profile migration |
| Systemd service files | Pre-migration hardening does not alter service management |
| AGENTS.md | Regeneration is a downstream effect |
| CIS spine schema | No migrations in this tier |
| Existing gate scripts | Hooks invoke gates; gates remain unchanged as audit trail |
| Skills directories | v1.0 proposed 10 SKILL.md files — replaced by 1 shell script + 5 config entries |

---

## 3. Relationship to the WorkIntent → Process Manager Flow

### 3.1 Where this tier sits in the architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Agent calls │────▶│ Shell hook fires │────▶│ Tool executes│
│  write_file  │     │ cis_pre_tool_    │     │ (if allowed) │
│  /patch/     │     │ gate.sh          │     │              │
│  terminal    │     │                  │     │              │
│  commit      │     │ Checks:          │     │              │
└──────────────┘     │ 1. Working dir?  │     └──────────────┘
                     │ 2. Spine gate    │            ▲
                     │    record valid? │            │
                     │ 3. Role allowed? │     ┌──────┴──────┐
                     │                  │     │  Exit 0     │
                     │ If any fails:    │     │  Proceed    │
                     │ exit 1 → BLOCK   │     └─────────────┘
                     └──────────────────┘
```

### 3.2 Flow relationship

The hook fires BEFORE every write_file, patch, and terminal(commit/mutate) call
when the agent's working directory is within `/mnt/projects/cis/`. It does not
fire for read-only tools (read_file, search_files, sqlite3 SELECT, grep, etc.).

### 3.3 What this tier must NOT do

- Must not modify existing gate script behavior
- Must not add new database tables
- Must not require new Python packages
- Must not change the Eric Gate approval model
- Must not block tools outside the CIS working directory

---

## 4. Minimum Architecture

### 4.1 Mechanism: Hermes Shell Hooks

Hermes v0.16.0 supports **shell hooks** — bash scripts configured in
`config.yaml` that fire on lifecycle events including `pre_tool_call`.
When a shell hook exits with a non-zero code, the tool call is BLOCKED.
This is the ONLY currently-functional pre-tool-call blocking mechanism
in Hermes. Skills (SKILL.md files) are context instructions only — they
cannot intercept tool calls. Plugin `pre_tool_call` hooks exist but are
broken in v0.16.0 (GitHub issue #41045: return values discarded).

**Reference:**
```
SOURCE: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
Shell hooks: "Drop-in scripts for blocking, auto-formatting, context injection"
Valid event: pre_tool_call (confirmed in GitHub issue #31480)
```

### 4.2 The Hook Script

One script: `tools/hooks/cis_pre_tool_gate.sh`

It receives the tool name and arguments as environment variables from Hermes,
checks the CIS spine for a valid gate record, and exits 0 (allow) or 1 (block).

```
Pseudocode:
1. Check if $TOOL_NAME is in BLOCKED_TOOLS list (write_file, patch, terminal)
2. If not a blocked tool → exit 0 (allow)
3. Check if working directory is /mnt/projects/cis/
4. If not CIS dir → exit 0 (allow — no oversight needed outside CIS)
5. Query data/cis_memory.db for valid gate record in current session
6. If valid gate record exists → exit 0 (allow)
7. If no valid gate record → echo "BLOCKED: pre-execution oversight required" → exit 1
```

### 4.3 Config Entries Per Profile

Each profile's `config.yaml` gets a `hooks:` block:

```yaml
hooks:
  pre_tool_call:
    - command: /mnt/projects/cis/tools/hooks/cis_pre_tool_gate.sh
      timeout: 10
```

### 4.4 Files to Create

| File | Purpose |
|------|---------|
| `tools/hooks/cis_pre_tool_gate.sh` | Single shell script: checks spine, allows or blocks tool calls |

### 4.5 Files to Modify

| File | Change |
|------|--------|
| `~/.hermes/config.yaml` (Prime, 8642) | Add `hooks:` block |
| `~/.hermes-r1/config.yaml` (Reviewer, 8643) | Add `hooks:` block |
| `~/.hermes-v4pro/config.yaml` (Drafter, 8645) | Add `hooks:` block |
| `~/.hermes-v4impl/config.yaml` (Implementer, 8646) | Add `hooks:` block |
| `~/.hermes-qwen/config.yaml` (Qwen, 8644) | No hook needed — Qwen has no tool access |

### 4.6 Technology Choices

| Choice | Rationale |
|--------|-----------|
| Shell hooks (not skills) | Shell hooks block at the harness level. Skills are voluntary instructions. |
| Bash (not Python plugin) | Plugin `pre_tool_call` hooks are broken in v0.16.0 (issue #41045). Shell hooks work. |
| One script, five configs | Single source of truth. Config entries are 3 lines each. |
| sqlite3 CLI for spine queries | Zero dependencies. sqlite3 is already on the system. |
| Exit code gating | `exit 0` = allow, `exit 1` = block. Hermes respects this natively. |

---

## 5. Required Tables, Files, and Schemas

### 5.1 New database tables

None. This tier requires no schema changes.

### 5.2 Existing tables used (read-only)

| Table | Purpose |
|-------|---------|
| `workflow_runs` | Gate state tracking — `status`, `result`, `rounds_completed` |
| `build_plan_nodes` | Tier/context awareness |
| `project_decisions` | Active decisions |
| `active_blockers` | Blocked items |

### 5.3 New configuration files

None. Configuration is added to existing `config.yaml` files.

### 5.4 Directory structure

```
/mnt/projects/cis/
└── tools/
    └── hooks/
        └── cis_pre_tool_gate.sh          ← NEW: the gate script
```

---

## 6. Security and Approval Boundaries

### 6.1 Environment isolation

No new environment variables. The hook script inherits the agent's environment.
No secrets are added. API keys are not read by the hook.

### 6.2 Data access

The hook script queries `data/cis_memory.db` via `sqlite3` in read-only mode.
It never writes to the database.

### 6.3 Network access

The hook script has no network access. It reads local files only.

### 6.4 Approval boundaries

The Eric Gate remains the final approval authority. Hardening enforces that
the gate sequence fires before tools execute, but Eric still makes the final
decision. The hook does not replace the Eric Gate — it ensures agents cannot
skip it.

### 6.5 Audit trail

When the hook blocks a tool call, it prints the reason to stderr. This output
appears in the agent's session log. Successful allows are silent — only blocks
are logged.

---

## 7. Deterministic Acceptance Criteria

### 7.1 Functional acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| A1 | Write blocked without gate | Agent in /mnt/projects/cis calls write_file without running gate_runner.sh | Hook exits 1. Tool blocked. Message: "BLOCKED: pre-execution oversight required" | Manual: prompt agent to write to CIS dir |
| A2 | Write allowed after gate | Agent runs gate_runner.sh (all PASS), then calls write_file | Hook exits 0. Tool executes. File written. | Manual: run gate_runner.sh, then write_file |
| A3 | Read never blocked | Agent calls read_file, search_files, sqlite3 SELECT anywhere | Hook exits 0. Tool executes. | Verify read operations never trigger hook block |
| A4 | Non-CIS dir unaffected | Agent in /tmp calls write_file | Hook exits 0 (working dir check passes through). Tool executes. | Manual: cd /tmp, write_file |
| A5 | Gate skip prevention — terminal commit | Agent calls terminal("git commit") without running gate_runner.sh | Hook exits 1. Tool blocked. | Manual test |
| A6 | Gate skip prevention — patch | Agent calls patch in /mnt/projects/cis without running gate_runner.sh | Hook exits 1. Tool blocked. | Manual test |
| A7 | gate_runner.sh still works standalone | Run tools/gates/gate_runner.sh directly | All gates execute as before (unchanged) | Manual: bash tools/gates/gate_runner.sh |
| A8 | Hook timeout doesn't crash agent | Hook script hangs (simulated) | Hermes kills hook after timeout (10s). Tool allowed (fail-open). Error logged. | Manual: add sleep 30 to hook, test |
| A9 | Gateway restart preserves hooks | Restart hermes gateway | hooks: block present in config → registered on startup | grep gateway.log for "shell hook registered" |
| A10 | Qwen profile unaffected | Qwen has no hooks block | No hooks fire for Qwen (inference-only, no tools) | Verify Qwen config lacks hooks block |

### 7.2 Security acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| S1 | No escalation bypass | Agent claims "Eric approved" without spine record | Hook blocks: checks `eric_approved_at` in workflow_runs | Manual test |
| S2 | No FK bypass | Agent attempts sqlite3 INSERT with non-existent FK | Hook validates FK; blocks if reference missing | Manual test |
| S3 | Hook script cannot be modified by agent | Agent attempts to edit tools/hooks/cis_pre_tool_gate.sh | Standard file permissions prevent modification during active session | Verify file ownership |

### 7.3 Integration acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| I1 | Hook fires on gateway session start | Start Telegram session, write to CIS dir | Hook fires, gate check runs | grep gateway.log for hook execution |
| I2 | All 5 profiles load hooks | Start each gateway: 8642, 8643, 8645, 8646 | `hermes hooks list` shows cis_pre_tool_gate registered | Manual per profile |
| I3 | Existing pipeline scripts unaffected | Run pipeline_dispatch.sh, reviewer_reconcile.py | Same behavior as pre-hardening | Manual regression test |

---

## 8. Required Tests and Gates Before Implementation

### 8.1 Pre-implementation gates

| Gate | What It Checks | Method |
|------|---------------|--------|
| G1: Git clean | No uncommitted changes in config files | `git status --short` |
| G2: No secrets | Hook script contains no API keys | `grep -E 'sk-|api_key|Bearer' tools/hooks/cis_pre_tool_gate.sh` |
| G3: Config syntax | All 4 config.yaml files parse as valid YAML | `python3 -c "import yaml; yaml.safe_load(open(p))"` per profile |
| G4: Hook script executable | `cis_pre_tool_gate.sh` has execute permission | `test -x tools/hooks/cis_pre_tool_gate.sh` |

### 8.2 Post-implementation verification gates

| Gate | What It Checks | Method |
|------|---------------|--------|
| G5: Hook registered | All 4 profiles have hook loaded | `hermes hooks list` per profile |
| G6: Block test | Write to CIS dir without gate → blocked | Manual test: A1 |
| G7: Allow test | Write to CIS dir after gate → allowed | Manual test: A2 |
| G8: Non-regression | gate_runner.sh produces same results | Run gate_runner.sh; compare to pre-hardening baseline |
| G9: Non-CIS pass-through | Writes outside CIS dir allowed | Manual test: A4 |

### 8.3 Test file structure

```
tools/tests/
  test_cis_hardening_v2/
    test_hook_block.sh          # A1, A2, A5, A6
    test_hook_allow.sh          # A2, A3
    test_hook_non_cis.sh        # A4
    test_hook_security.sh       # S1, S2, S3
    test_hook_integration.sh    # I1, I2, I3
```

---

## 9. Out of Scope

### 9.1 Explicitly not part of this tier

| Item | Reason |
|------|--------|
| Profile migration (5→1) | Gated on hardening completion |
| Hermes source patches | Post-migration concern |
| Plugin pre_tool_call hook fix (issue #41045) | Upstream Hermes fix — not CIS scope |
| Skills-based guardrails (v1.0 approach) | Replaced by shell hooks — more reliable mechanism |
| Qwen tool enforcement | Qwen has no tool access — dead code removed |
| External advisor integration (Claude/ChatGPT) | Deferred to post-migration |
| CIS UI overhaul | Tier 10 is complete; not modified here |
| Google Drive backup (BLK-SEED-004) | Independent concern |
| Closeout trigger automation | Independent concern |

---

## 10. Eric Gate Approval Required Before Implementation

### 10.1 Gating conditions

Implementation shall not begin until ALL of:

| # | Condition | Verification |
|---|-----------|-------------|
| 1 | This specification approved by Eric Gate | Eric's explicit message |
| 2 | Both reviewers (R1 + Qwen) have reviewed v2.0 | This document is the R1 review + Qwen review pending |
| 3 | No active blockers block this tier | BLK-SEED-004 is unrelated; BLK-SEED-005 resolved |
| 4 | Eric explicitly issues PROCEED or IMPLEMENT | Not automatic |

### 10.2 Approval record format

```
Decision: APPROVE
Workflow: Hermes Hardening v2.0 Specification
Rationale: [Eric's rationale]
Date: [ISO 8601]
Decided by: Eric
```

### 10.3 What happens after approval

1. Build_plan_nodes created in spine with status = PROPOSED
2. Eric issues IMPLEMENT → status moves to IN_PROGRESS
3. Implementer (8646) creates `cis_pre_tool_gate.sh` and adds hooks to 4 configs
4. Verification gates G1-G9 run
5. Status moves to COMPLETE only after all gates pass AND Eric approves closeout
6. Profile migration can proceed

### 10.4 What happens if approval is withheld

- Hardening remains unbuilt
- 16 failure modes remain unaddressed at harness level
- Profile migration is blocked
- Specification revised per Eric's direction

---

## 11. Phased Build Plan

### 11.1 Principle

Built as 4 sequential increments. Each requires verification before the next.

### 11.2 Build nodes

| Node | Label | Depends On | Scope |
|------|-------|-----------|-------|
| H1 | Hook script | None | Create `tools/hooks/cis_pre_tool_gate.sh` — the gate-checking script |
| H2 | Prime config | H1 | Add `hooks:` block to `~/.hermes/config.yaml` |
| H3 | Profile configs | H2 | Add `hooks:` block to R1, Drafter, Implementer configs |
| H4 | Verification | H3 | Run G1-G9 gates; acceptance tests A1-A10; Eric Gate closeout |

### 11.3 Node dependency graph

```
H1 (hook script)
  └── H2 (Prime config)
        └── H3 (R1 + Drafter + Implementer configs)
              └── H4 (verification + Eric Gate closeout)
```

### 11.4 What each node does NOT include

| Node | Exclusions |
|------|------------|
| H1 | Does not modify config files. Does not add database tables. |
| H2 | Only touches Prime config. Other profiles unchanged. |
| H3 | Qwen profile excluded (no tool access). |
| H4 | Does not run profile migration. Does not modify gate scripts. |

---

## 12. Recommendation

Approve this specification as the architecture basis for hardening the current
5-install Hermes deployment. The approach uses Hermes shell hooks — the only
currently-functional pre-tool-call blocking mechanism in Hermes v0.16.0 — to
enforce that every write, patch, or commit in the CIS working directory passes
through the gate sequence first. The mechanism is harness-level: the hook fires
in Hermes itself, not in the LLM's voluntary compliance. One shell script, five
config entries, zero new dependencies, zero schema changes. The v1.0 approach
(skills-based "interception") was rejected by dual review because SKILL.md files
are instructions in context, not enforcement hooks. This v2.0 approach corrects
that by using the actual mechanism Hermes provides. Hardening gates before
profile migration — profiles without harness-level enforcement would inherit the
same bypass vulnerability proven on 2026-06-17.

---

## Appendix A: Evidence References

### A.1 Shell hooks are the correct mechanism

```
SOURCE: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
| Shell hooks | hooks: block in config.yaml | CLI + Gateway |
  Drop-in scripts for blocking, auto-formatting, context injection |
```

```
COMMAND: grep -A5 "pre_tool_call" /home/eric/.hermes/hermes-agent/hermes_cli/plugins.py | head -10
OUTPUT: (Confirms pre_tool_call is a valid shell hook event — issue #31480 lists it among valid events)
```

### A.2 Skills cannot intercept tool calls (v1.0 rejection evidence)

```
SOURCE: https://github.com/NousResearch/hermes-agent/issues/41045
"pre_tool_call plugin hook returns discarded — cannot block or redirect tool calls"
"Root Cause: invoke_hook() uses emit(), not emit_collect().
 This means all pre_tool_call hook return values are silently discarded"
```

```
COMMAND: grep -n "get_pre_tool_call_block_message" /home/eric/.hermes/hermes-agent/agent/tool_executor.py
OUTPUT:
346:  from hermes_cli.plugins import get_pre_tool_call_block_message
347:  block_message = get_pre_tool_call_block_message(...)
```

The only pre-tool-call enforcement in Hermes is a Python plugin hook — skills
(markdown files) cannot register as plugins.

### A.3 All 5 gateways healthy

```
COMMAND: for port in 8642 8643 8644 8645 8646; do
  echo -n "Port $port: "
  curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$port/health
done
OUTPUT:
Port 8642: 200
Port 8643: 200
Port 8644: 200
Port 8645: 200
Port 8646: 200
```

### A.4 Build plan node status

```
COMMAND: sqlite3 /mnt/projects/cis/data/cis_memory.db "SELECT node_label, status FROM build_plan_nodes ORDER BY cast(tier as real);"
OUTPUT:
Tier 0 — Deliberation Engine|COMPLETE
Tier 1 — Deterministic Verification Gates|COMPLETE
Tier 2 — Kanban Coordination Layer|DEFERRED
[...]
Tier 11D — Reviewer-Side Handoff|COMPLETE
VERDICT: 25/27 COMPLETE, 2 DEFERRED
```

### A.5 Active blockers

```
COMMAND: sqlite3 /mnt/projects/cis/data/cis_memory.db "SELECT id, status FROM active_blockers WHERE status='ACTIVE';"
OUTPUT:
BLK-SEED-004|ACTIVE
VERDICT: Only BLK-SEED-004 active. Not a dependency for this tier.
```

### A.6 Gate runner — 5 gates (not the 7 claimed in v1.0)

```
COMMAND: grep -c "^run_gate" tools/gates/gate_runner.sh
OUTPUT: 5
```

### A.7 Git state

```
COMMAND: git rev-parse --abbrev-ref HEAD && git rev-parse HEAD && git status --short
OUTPUT:
master
4715758f
 M runtime/memory/current_context.json
?? docs/CIS_HERMES_HARDENING_SPECIFICATION.md
```

---

*End of Hermes Hardening Specification v2.0 — REVISED DRAFT*
*Status: REVISED DRAFT — awaiting Eric Gate review*
*Next step: Qwen review → Eric reads → approves → build_plan_nodes created → IMPLEMENT*
