# CIS Session Handoff Document
Generated: 2026-09-06 | Save to: /mnt/projects/cis/docs/CIS_SESSION_HANDOFF.md

---

## What this system is

CIS (Creative Intelligence System) is a multi-agent pipeline running inside a
Docker container named `cis-pipeline` on an Ubuntu VM (user: eric, IP:
192.168.1.15) hosted on a Proxmox server (node: wander, IP: 192.168.1.200).
The operator is not a coder. He cannot validate code by reading it. He
validates by checking output. Every action must be designed so a non-coder
can tell whether it worked.

The operator communicates with a root Hermes agent via Telegram. That root
Hermes agent runs on the host VM and is the operator's relay into the
contained pipeline. The contained pipeline is what is being built and
constrained.

---

## Pipeline architecture

Six model gateways inside the container, each on a fixed port:

| Role | Port |
|------|------|
| brain | 8644 |
| draft | 8645 |
| review1 | 8643 |
| review2 | 8647 |
| menter | 8646 |
| verify | 8648 |

Governed flow:
pre-discovery → brain → drafter writes spec → dual adversarial reviewers
critique → consensus → implementer writes code → verifier runs evidence checks

The orchestrator is runtime/abstraction/pipeline_relay.py (3,577 lines).
Do not modify it without asking the operator first.
Do not start pipeline runs without asking the operator first.

---

## Working rules (from CLAUDE.md)

- Back up any file before writing it. State where the backup is.
- One write per turn. Stop and report after each.
- State what output would prove the change worked, before making it.
- Verify every claim with a command. Never assert from memory or inference.
- If you reason about a file, read it first.
- Do not modify runtime/abstraction/pipeline_relay.py without asking first.
- Do not start pipeline runs without asking first.
- If a task grows beyond what you were asked, stop and say so.

Environment facts:
- Pipeline agents use: /usr/local/lib/hermes-agent/venv/bin/python
- Working directory for pipeline: /workspace/cis
- tools/ask_history.py: python3.12 only, positional args, no flags — it is
  semantic search over the KB, not a file reader
- Container clock is UTC; host is local. Do not compare mtimes across them.
- Never set cwd inside runtime/api/ — operator.py shadows the stdlib.
- Closeout: bash tools/closeout.sh (--check first, read-only)
- docs/NEXT_SESSION.md carries only standing context — no tasks, no status.
  It has 15 sections. Do not write tasks into it.
- There is one queue: docs/UNIFIED_BUILD_LIST.md. Do not create a second.

---

## What the operator wants

The operator wants to be removed from manually transporting cards between
this chat interface and the Claude Code session on the VM. Currently he
reads the output here, copies a card, pastes it into the Claude Code
terminal, copies the result back, and pastes it here. That is the transport
he wants eliminated.

The end state: operator sends a message via Telegram, a card enters the
pipeline, the pipeline works, operator observes results via Telegram. He
does not carry anything manually.

---

## Current system state

### Knowledge base
- 2,649,411 SQLite rows
- 2,649,403 Chroma vectors (gap of 8 — filter_for_index exclusions, by design)
- Semantic search at full corpus coverage as of 2026-09-06T01:57:48Z
- KB ingestion wired into closeout — session transcripts auto-ingest

### Recent commits
- 0d5dc3e — feat: add check_chroma_writers gate, two-sided proof confirmed
- e90e598 — ingestion wired into closeout, 514 rows from this session
- 8c774fc — sweep removed from closeout, append_embeddings.py concurrency proven
- Latest — fix: correct stale 1.1 references in 1.10 and 4.10, remove
  4.10 duplication

### Gate status
- tools/check_chroma_writers.py — proven and committed. Fails on pre-fix
  backup (exit 1, names both violations), passes on HEAD.
- Every Chroma writer must hold chroma_write (0.3) and apply
  filter_for_index (0.2).

### Dependency read — completed this session
- All 100 queue items read: 78 ### items plus 22 bullets (3.1-3.12 and
  4.1-4.10)
- Tiers 0, 1, 2, 3, 4 all read in full
- 13 class-5 unresolvable references across all items, 4 unresolvable
  in principle

### Three findings from the dependency read
1. Reference-documents table is a dependency map with no edge type in the
   schema. Ten documents mapped to items they cover. Needs a new edge kind
   before the next mining pass.
2. Supersession record at line 2044 — "Recorded, not queued — superseded
   by the container." Two entries. No schema representation. Needs a
   supersession edge type or separate store.
3. 4.10's prerequisite moved from 1.1 to 1.23. The 2026-08-30 run was a
   documentation task — BLOCK-mode verification guardrails all SKIPPED,
   no code was checked, mismatch set still has no members. Gate did not
   open; it moved.

### Stale text fixes applied this session
- 4.10: prerequisite repointed from 1.1 to 1.23 with reason, duplication
  removed, first step marked independently unblocked
- 1.10 step 4: "Depends on 1.1" corrected — 1.1 is DONE, step is unblocked

---

## The four remaining items to remove operator from transport

These must be executed in dependency order without asking the operator to
choose between them.

### 1. Fix 3.6 — case mismatch killing all joins
projects.id is 'cis' (lowercase).
build_plan_nodes.project_id is 'CIS' (uppercase).
Every join between these tables returns 0 of 30 rows.
Fix the mismatch. Verify with a join that returns the expected row count.

### 2. Build 3.21 — move queue out of markdown into the spine database
The queue currently lives in docs/UNIFIED_BUILD_LIST.md.
3.21 moves it into the spine database so it is queryable and machine-operable.
This is the explicit prerequisite for 4.18 and 4.19.
Read ### 3.21 in docs/UNIFIED_BUILD_LIST.md in full before writing anything.

### 3. Build 4.18 — wire card factory to the queue
Once the queue is in the spine, the card factory reads from it and produces
cards without the operator writing them manually.
Read ### 4.18 in docs/UNIFIED_BUILD_LIST.md in full before writing anything.

### 4. Build 4.19 — Telegram triggers card into pipeline
The operator sends a Telegram message. A card enters the pipeline. The
pipeline works. The operator observes results via Telegram.
This is the item that completes transport removal.
"Button" is figurative — it means a Telegram interaction, not a UI element.
Read ### 4.19 in docs/UNIFIED_BUILD_LIST.md in full before writing anything.

---

## How to work this list

Read the item in full from UNIFIED_BUILD_LIST.md before touching anything.
Back up before any write.
One write, then stop and report.
Verify with commands, not inference.
Do not ask the operator which item to do next — the dependency order above
is the sequence.
Stop only if a write would touch pipeline_relay.py or start a pipeline run.

---

## Known behavioral problems to avoid repeating

These are patterns that wasted operator time this session and must not recur:

1. Piecemeal cards — issuing a verification step as a separate card when
   it could be combined with the action that preceded it.

2. Asking the operator to choose — if the dependency order is known, execute
   it. Do not present options.

3. Asserting from memory — six confident diagnoses failed in one session on
   2026-08-24, every one caught by the next command. Read before reasoning.

4. Wrong tool for the job — ask_history.py is semantic search over the KB.
   It takes a question string. It cannot read files. Use cat/sed/grep for
   files.

5. Writing outside the else — guard logic that allows a write on a failed
   match. The write must sit inside the else branch so a non-unique match
   performs no write.

6. Present-tense claims that will age — any sentence asserting current state
   will become stale. Flag it when you write it.

---

## Where to find things

| What | Where |
|------|-------|
| Working rules | CLAUDE.md at project root |
| Standing context | docs/NEXT_SESSION.md |
| The queue | docs/UNIFIED_BUILD_LIST.md |
| Session logs | KB, source='claude_code' |
| Gate script | tools/check_chroma_writers.py |
| Embedding script | tools/catalog/append_embeddings.py |
| Closeout | bash tools/closeout.sh |
| Spine database | query UNIFIED_BUILD_LIST items for location |
| Backups | data/backups/ |

