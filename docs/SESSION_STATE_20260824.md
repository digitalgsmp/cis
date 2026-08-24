# CIS Pipeline — State 2026-08-24

## Confirmed working
Full 8-phase cycle completed: brain, draft, dual review, consensus,
ERIC_GATE, PATTERN_CATALOG, CODE_REVIEW_GATE, VERIFICATION.
Run: run-68ef184da2933837-1787603143

## What unblocked it
Container restart activated the 8/22 adapter.py auth patch.
Drafter 401s were the cause of every prior DRAFT escalation.

## Launch requirements (both needed)
Interpreter: /usr/local/lib/hermes-agent/venv/bin/python
Working dir: cd /workspace/cis (else import guardrails fails silently)
Use -u and docker exec -d.

## Gate behavior
HTTP approval sets status only. No process resumes.
Every gated run needs an explicit detached --resume after approval.

## Corrections to 8/22 doc
ESCALATED is a universal failure sink, not a gate timeout.
HUMAN_QUESTION_TIMEOUT never fired.
Telegram is not load-bearing; notify failures are caught and logged.
No CIS_TG_ vars exist in container or host. Aliasing plan was invalid.

## Open defects
Verify gate diffs against HEAD, not a pre-run snapshot. Dirty tree
produces false scope violations (reported 24 files, menter changed 0).
ext_gate paths drop /workspace/cis prefix: /runtime/mcp_bridge,
/data/cis_memory.db.
ext_gate_eric_approval is circular: fails because verify failed.
dead_letter_queue records status as phase. No cause captured.
Entrypoint health check runs at 10s, always reports 0/6.
container_app.py has 65 uncommitted insertions from 16:42, unattributed.
