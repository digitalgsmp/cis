# Session Handoff — 2026-06-19

## Architecture Decision (settled)
Three-layer process isolation model adopted as the enforcement architecture:

1. **CIS control plane** — owns hooks, policy checker, task templates, frozen contracts. Lives at /opt/cis-control/, root-owned, mounted READ-ONLY into worker containers.
2. **Hermes worker** — executes inside Docker, reads context + contract, uses tools, writes ONLY to declared workspace.
3. **Workspace** — /mnt/cache/catalog/<run_id>/ — the only writable mount.

Docker provides kernel-level filesystem isolation (verified: RO mount of /mnt/projects/cis refused write to breach.txt — "Read-only file system", exit 1, no breach file created).

Source roots (/mnt/archive, /mnt/projects/cis, /mnt/projects/swa) mounted read-only. Enforcement files outside any path the worker can write — /opt/cis-control, not the CIS repo.

Key principle: the constrained agent cannot author, edit, or widen its own contract. Valid authors: Claude API proposal validated by deterministic local compiler against fixed template; Eric directly; prior approved DB row.

## Trust Root (load-bearing)
- Agent cannot author its own contract
- Compiler REJECTS proposals that widen paths/tools beyond template
- Enforcement files live OUTSIDE agent-writable paths
- Worker cannot launch Docker (eric not in docker group; control plane launches)
- Claude API may propose/review but cannot widen permissions

## Docker Containment Verified (current state)
- Docker 29.6.0 installed
- Read-only mount refused write: exit 1, "Read-only file system"
- No breach file created
- Caveat: eric not in docker group (correct — prevents worker from launching containers); sudo required for control-plane invocation

## Changes Made This Session
- Claude Code installed (v2.1.183), authenticated, CLAUDE.md created for audit
- Claude audit of 16 failure modes completed: 11 FAIL, 1 PARTIAL, 3 PASS, 1 bonus finding
- HCP_06 preamble added: "PURPOSE OF THIS FILE — READ FIRST" with governance-reset vocabulary disclaimer
- gate_runner.sh: PASS/SKIP/FAIL counters added, banner now honest ("4 PASSED, 4 SKIPPED, 0 FAILED")
- reviewer_reconcile.py: hardcoded R1 API key replaced with CIS_R1_API_KEY env var
- CIS_R1_API_KEY exported in runtime/config/runtime.env (gitignored)
- gate_deliberation.sh sources runtime.env before calling reviewer_reconcile.py
- HCP files regenerated (manifest updated)

## Parked Items (non-urgent, carry forward)
- Gate 7 exit-contract honesty (pre_execution_oversight internal SKIP counted as PASS)
- Dead key f0a78f... still in git history (matches no active profile, no rotation needed)
- HCP/spine row-count drift (DEV-PIVOT-02 vs live spine)
- Claude's bonus finding: hardcoded escalation/env var patterns confirmed clean elsewhere
- gate_runner.sh gate 7 internal-skip-vs-external-skip distinction

## Next Action
Hermes drafts TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md spec — see docs/NEXT_SESSION_DRAFTING_INSTRUCTION.md for the full instruction block. DRAFT ONLY. Proposal goes through Claude audit → ChatGPT audit → Eric approval before any /opt/cis-control/ files are created.
