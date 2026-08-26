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

## Session end 2026-08-24
Checkpoint commit 03b2143. Two status docs re-dirty after every
commit (pre-commit hook regenerates them).
Menter CAN write pipeline_relay.py as worker. Self-modification is possible.
Baseline fix specified but NOT built: _pre_exec_head is captured in
_execution and never passed to the verify prompt. Needs a working-tree
snapshot, not a commit hash, and must persist on the run row to survive resume.
Run run-1a53c843b1e4d4ca-1787616060 escalated: both reviewer gateways
failed with EMPTY error strings. Gateways healthy after. Reviewer spent
its turn on skill_manage writes, produced no review.
A SKILL.md somewhere is over the 100000-char limit; every write fails.
read_file is denied to background review — reviewers cannot inspect code.
Spine KB is populated: 298616 knowledge_messages, 287712 observations,
213 corpus_entries. Unknown whether pipeline agents can reach it.
Unattributed edits to runtime files at 16:42 and DEV-PIVOT_STATUS at 18:58.

## Enforcement architecture (verified 2026-08-24)
managed-config.yaml mounts as /etc/hermes/config.yaml, root-owned. Pins
plugins.enabled AND plugins.disabled (both required — a worker previously
escaped by writing to disabled, which wins over enabled).
approvals.mode is off: no human prompt on execute_code.
THE WALL = mwl-proof plugin pre_tool_call hook. It logs every call to
hook_payload.jsonl then shells to container_gate_runner.py for the decision.
FAIL-OPEN: any exception or timeout in the gate runner returns None = allow.
Gate runner checks: secrets in args, dangerous commands, forbidden write
paths, and blocks ALL MCP write tools. Default is allow.
CONSEQUENCE: agents can READ the spine via MCP cis-knowledge but cannot
WRITE to it. Shared knowledge is one-directional. Agents contribute only
via per-profile SKILL.md files, which are all now over the size cap.
Models: brain/draft/menter deepseek-v4-pro, review1 qwen3.7-max,
review2/verify glm-5.2. All max_turns 90.
tool_guardrails.py is a LOOP BREAKER (call fingerprinting), not permissions.

## Semantic search RESTORED 2026-08-24
tools/ask_history.py — MUST run as python3.12 (chromadb lives in
/home/eric/.local/lib/python3.12, NOT in system python3 or the Hermes venv).
Usage: python3.12 tools/ask_history.py "question" [top_k]
Chroma store: data/chroma_data, 9.3GB, one collection knowledge_messages,
287648 embeddings. Local all-MiniLM-L6-v2, no API needed.
CRITICAL: must filter source to claude_export/chatgpt_export/
claude_transcripts. Unfiltered queries return GPL license headers from
the 165482-chunk archive source.

## Guidelines for next session
1. Ask history BEFORE designing. Four unknowns (resume-on-approval,
   escalation causes, MCP write policy, gate design) were likely already
   reasoned through in past sessions. Query first, propose second.
2. Verify claims with commands. Six confident diagnoses failed this
   session; every one was caught by the next command.
3. Fix order: SKILL.md split (mechanical, unblocks reviewers), then MCP
   write policy (design decision), then verify baseline.
4. OPEN: does spine.py check_eric_gate_approval read the wrong table
   and compare APPROVED vs stored APPROVE? Found in history, unconfirmed.
5. Interpreter and cwd must be explicit in every card. Five failures
   this session traced to wrong python or wrong directory.
