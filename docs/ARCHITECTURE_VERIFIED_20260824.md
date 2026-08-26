# CIS Architecture — verified by command 2026-08-24
Every line confirmed by a command. Nothing inferred.

## Two installations
Root Hermes on host VM: executor via Telegram, has docker access.
Container cis-pipeline: six model gateways, Flask API on 5000.
One bind mount: /mnt/projects/cis = /workspace/cis

## Six agents
brain 8644 deepseek-v4-pro
draft 8645 deepseek-v4-pro
review1 8643 qwen3.7-max
review2 8647 glm-5.2
menter 8646 deepseek-v4-pro
verify 8648 glm-5.2
All max_turns 90. review2 and verify share a model.

## Pipeline phases
BRAIN, DRAFT, dual review, consensus, ERIC_GATE,
PATTERN_CATALOG, CODE_REVIEW_GATE, VERIFICATION.
Orchestrator: runtime/abstraction/pipeline_relay.py (3577 lines).

## Launch requirements — BOTH needed
Interpreter: /usr/local/lib/hermes-agent/venv/bin/python
Working dir: cd /workspace/cis
Use -u for unbuffered output and docker exec -d to detach.
Gate approval sets status only. No process resumes.
Every gated run needs an explicit detached --resume.

## Enforcement
managed-config.yaml mounts as /etc/hermes/config.yaml, root-owned.
Pins plugins.enabled AND plugins.disabled — both required.
approvals.mode off: no human prompt on execute_code.
THE WALL = mwl-proof plugin pre_tool_call hook.
Logs every call to hook_payload.jsonl, then shells to
container_gate_runner.py for the decision. FAIL-OPEN on exception.
Gate blocks: secrets, dangerous commands, forbidden paths, ALL MCP writes.
tool_guardrails.py is a loop breaker, not permissions.

## Storage
Spine: data/cis_memory.db, 4.8GB, ~70 tables.
298616 knowledge_messages, 287712 observations, 213 corpus_entries.
Also: knowledge_base.db, kanban.db, timeline_index.db (32866 msgs).
MCP cis-knowledge bridges the spine to agents READ-ONLY.

## Chroma semantic layer
data/chroma_data, 9.3GB, collection knowledge_messages.
287648 embeddings, all-MiniLM-L6-v2, fully local, no API.
Sources: archive 165482, cis_docs 75794, swa_project 23427,
claude_export 9467, chatgpt_export 3787, claude_transcripts 757.
Query via tools/ask_history.py — MUST run as python3.12.
Filter to the three conversation sources or results are license headers.
