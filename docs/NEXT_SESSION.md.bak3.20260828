# NEXT SESSION — updated 2026-08-26

Paste this file as the first message of a new session.
Rewrite it at session end. Never append.

## Constraints (every card)
Interpreter and cwd explicit. Pipeline: /usr/local/lib/hermes-agent/venv/bin/python, cd /workspace/cis
ask_history.py: python3.12 only, positional args, no flags.
Verify every claim with a command. If a lookup fails twice, stop and report.
Container clock is UTC, host is local. Never run python from data/drive_imports.

## Blockers — pipeline cannot complete a run
1. Verification-only runs always escalate. Empty files_planned is treated as failure:
   pipeline_relay.py ~2838. Proven by run-5c80ece4fdd0122d-1787703333, escalated 23:21 UTC
   after passing every prior phase. Design gap, not a bug. Note: only affects runs that
   decide to build nothing — a code-change run should pass this gate.
2. MCP gates report ERROR as SKIP, so write enforcement never runs. Wrong path
   /runtime/mcp_bridge, missing /workspace/cis prefix. Seen live in the same run.
3. project_dir is derived by stripping the DB filename, yielding data/ not the repo root:
   pipeline_relay.py 2667 and 2822. Catalogs have landed in data/runtime/catalogs since Jul 9.
4. Escalations record no cause. dead_letter_queue id=25 says only "ESCALATED".

## After a run completes end to end
5. Verify baseline never passed to the verify prompt — still untested, downstream of item 1.
6. Export gate expects 12 artifacts, finds 13. Warns every commit.
7. CLAUDE.md says spine is runtime/spine.db; that file is 0 bytes. Real spine is data/cis_memory.db.
8. gateway_status_qwen (project_state id=101) stale — claims Qwen is 2nd reviewer on 8644.
9. Wire ingest_sessions.py + append_embeddings.py into closeout.sh.
10. Retention policy for data/backups/ — 4.8GB per spine write, 72GB free.
11. Deferred until the pipeline can review it: Claude Code sessions produce nothing for the KB.
    Raw transcripts already exist at ~/.claude/projects/.

## Done 2026-08-26
Approved run-5c80ece4fdd0122d-1787703333 at ERIC_GATE — first run past the gate. Pattern
catalog reached consensus; escalated at code review on empty files_planned. No files modified,
six pitfalls.md byte-identical before and after. Gateways confirmed 6/6 healthy on 8643-8648 via
the API's own health check; host and container are separate agent sets. Guardrails fired
correctly during the run (skill_manage read-before-write, gateway self-restart, hardline block).
