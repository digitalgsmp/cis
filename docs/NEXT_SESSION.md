# NEXT SESSION — updated 2026-08-26

Paste this file as the first message of a new chat.
Rewrite it at session end. Never append — if it exceeds 15 lines, cut.

## Constraints (every card)
Interpreter and cwd explicit. Pipeline: /usr/local/lib/hermes-agent/venv/bin/python, cd /workspace/cis
ask_history.py: python3.12 only, positional args, no flags.
Verify every claim with a command. Container clock is UTC, host is local.

## Queue
1. Wire ingest_sessions.py + append_embeddings.py into closeout.sh. Few lines. Makes the KB self-maintaining — currently both steps are manual.
2. MCP gates error exit 2 on a wrong path (/runtime/mcp_bridge, missing /workspace/cis prefix) and render as SKIP. Write enforcement never actually runs.
3. Verify baseline not built: _pre_exec_head captured in _execution, never passed to verify prompt. Needs a working-tree snapshot, must persist on the run row.
4. Parked run at ERIC_GATE: run-5c80ece4fdd0122d-1787703333. Approval sets status only; needs detached --resume, or abandon it.
5. Retrieval ranking is weak. 4000-char chunks dilute procedural content. Open design question, not a patch.

## Done 2026-08-25
SKILL.md split across six profiles, verified by live run. Two closeout.sh defects fixed (allowlist, .sh/.py gate) — first successful closeout since June. 86 sessions ingested, embedding backlog closed. ask_history filter widened to include hermes_session.
