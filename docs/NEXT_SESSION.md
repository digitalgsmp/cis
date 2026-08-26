# NEXT SESSION — updated 2026-08-26

Paste this file as the first message of a new session.
Rewrite it at session end. Never append. Keep under 15 lines.

## Constraints (every card)
Interpreter and cwd explicit. Pipeline: /usr/local/lib/hermes-agent/venv/bin/python, cd /workspace/cis
ask_history.py: python3.12 only, positional args, no flags.
Verify every claim with a command. If a lookup fails twice, stop and report.
Container clock is UTC, host is local.

## Queue
1. Wire ingest_sessions.py + append_embeddings.py into closeout.sh. Closeout commits code but never ingests knowledge.
2. MCP gates error exit 2 on a wrong path (/runtime/mcp_bridge, missing /workspace/cis prefix) and render as SKIP. Write enforcement never runs.
3. Verify baseline not built: _pre_exec_head captured in _execution, never passed to verify prompt.
4. gateway_status_qwen (project_state id=101) stale — claims Qwen is 2nd reviewer on 8644. Same class as the build_phase orphans.
5. Export gate expects 12 artifacts, finds 13. Warns every commit.
6. Confirm 8643-8646 are live. Only 8642/8647/8648 answered on the host.
7. Retention policy for data/backups/ — 4.8GB per spine write, 72GB free.
8. Parked run at ERIC_GATE: run-5c80ece4fdd0122d-1787703333.

## Done 2026-08-26
CLAUDE.md working rules + architecture corrected (7 roles / 6 endpoints). Spine build_phase orphans superseded — row 118 replaces 108/116/117. AGENTS.md and HCP regenerated. Claude Code installed and logged in, not yet used for work.
