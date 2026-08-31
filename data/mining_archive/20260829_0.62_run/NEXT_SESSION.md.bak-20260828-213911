# NEXT SESSION — updated 2026-08-28

Paste this file as the first message of a new session.
Rewrite it at session end. Never append.

## Constraints (every card)
Interpreter and cwd explicit. Pipeline: /usr/local/lib/hermes-agent/venv/bin/python, cd /workspace/cis
ask_history.py: python3.12 only, positional args, no flags.
Verify every claim with a command. If a lookup fails twice, stop and report.
Container clock is UTC, host is local. Never run python from data/drive_imports.
Gate scripts: edit tools/gates (a symlink to enforcement/mwl-proof-v2/gates).
Gate changes need a container image rebuild; runtime/ changes are mounted and live.

## State — the pipeline carries real work end to end
run-7207d316ce5a50a5-1787932828 finished CONSENSUS_REACHED across eleven rounds
(2026-08-28): proposal review objected once, code review objected three times,
the implementer wrote the planned file, verification confirmed it against the
filesystem. That is the adversarial loop working on real work, not a smoke test.
Six gateways healthy on 8643-8648.

Agents now report in every 60s while working (run_progress table, `progress`
field on /api/relay/<run_id>), so a slow phase and a hung one look different.
Verify timeout 1500s, menter 1200s.

## Queue
1. Ingest sessions into the KB. Persistent memory is the single most recurring
   blocker in the corpus (2,308 records, more than double anything else) and the
   reason every session starts by re-explaining the project. This was deferred
   because an unreviewed KB write could not be trusted — that condition has
   lifted now the pipeline completes runs, so route the change through it.
   CONFIRMED 2026-08-28: pipeline runs reach the KB (97 entries that day), Claude
   Code sessions reach it zero times. Today's reasoning survives only in git
   commit messages and code comments; ask_history cannot find any of it.
2. Measure prompt size on every agent call, then decide a cap. Nothing measures
   or limits the task prompt today (the soul document is capped at 8000 chars;
   what is built on top of it is not). Across 469 calls: avg 12k chars, 62 over
   20k, max 63,802 — and the three largest all went to VERIFICATION, the phase
   whose job is checking claims against reality. agent_trajectories.tokens_in
   exists and is 0 on every row. Over-length input fails silently: the model
   answers from part of the prompt and nothing records that it did.
3. Persist and rotate agent state. /home/worker/.hermes-* is not mounted, so
   every container recreate wipes it — brain went 422 messages -> 35 during
   2026-08-28's rebuilds. That accidental reset is currently masking the absence
   of a retention policy; when rebuilds stop, those DBs grow unbounded instead.
   Mount them, decide what is ingested, decide what is dropped.
4. Decide what the container regulates itself vs what needs a human trigger.
   Everything done by hand on 2026-08-27/28 — commit, image rebuild, container
   recreate, closeout, starting a run, approving at the gate — has no trigger
   and no automation. Suggested split: self-regulating = ingest sessions after a
   run, rotate agent state, record prompt sizes, rebuild when gates change.
   Human trigger = approve at gate, commit, start a run. Approval must never
   automate; that is the point of the gate.
5. Stream agent completions instead of blocking on one call. Gateways already
   support it (verified on 8648); token cost is zero, the same completion
   delivered in pieces. Replaces the heartbeat's weak liveness proxy with
   observed output, and gives the UI live visibility into every model.
   Known weakness it fixes: menter reported elapsed 180s / idle 180s, meaning
   its gateway log is never written during a call, so the proxy may measure
   nothing for that role.
6. Export gate warns "expected 12 artifacts, found 13" on every commit.
   tools/gates/gate_export_agreement.sh, EXPECTED_COUNT.
7. data/ is gitignored, so data/container_sessions/ (2,759 agent messages
   extracted 2026-08-27) is on disk but not in version control. Decide whether
   that matters.
8. Container agent history still does not reach the KB. ingest_sessions.py reads
   host paths and expects sessions/*.json; the container agents keep history in
   state.db under /home/worker/.hermes-*. Extraction exists, ingestion does not.
9. gateway_status_qwen (project_state id=101) stale — claims Qwen is 2nd reviewer
   on 8644. Container reviewers are review1 8643, review2 8647.
10. CLAUDE.md says the spine is runtime/spine.db; that file is 0 bytes. Spine and
   KB are both data/cis_memory.db.
11. Retention policy for data/backups/ — 4.8GB per spine write, 72GB free.
12. Deferred until the pipeline can review it: Claude Code sessions produce
   nothing for the KB. Raw transcripts exist at ~/.claude/projects/.
   tools/mine_asks_claude_code.py extracts asks from them; nothing ingests them.
13. 601 asks are mined and sitting in cards/*.jsonl; only 32 cards were ever
   generated. cards/asks_ranked.jsonl orders them by corpus weight. Running
   generate_cards.py over them is hours of GPU and yields roughly 8%.

## Gate status (2026-08-28)
gate_research_before_conclusion is BLOCK on brain and draft. 18 firings today:
16 PASS, 2 FAIL — both in one run, both false positives from subject parsing,
both fixed, 6 clean firings since. It has never caught a real unresearched
claim from a pipeline agent, so it is proven harmless, not yet proven useful.

## Method (learned the hard way 2026-08-27)
Absence is not defect. Four things were reported as gaps that the record already
explained as decisions: the orchestrator (set aside, no ADR), container session
logs (deliberate staging), NeMo (rejected — strips reasoning metadata), and a
"missing" seventh agent role (an arbitrary model choice). Search before
concluding: python3.12 tools/ask_history.py "<subject> decision"
gate_research_before_conclusion.py now BLOCKs on brain and draft for exactly
this, and briefs the agent up front via the same lookup.

## Done 2026-08-27
First complete run. Fixed: empty files_planned no longer escalates; project_dir
resolved to data/ not the repo root; escalations now name the phase that raised
them; capability guardrail read "I created zero files" as a claim; brain ignored
blocking gates on its success path; claim verifier could not find files named
without a folder. Seven gates derived their root by walking up from their own
file, resolving to "/" once sealed into /opt/cis-gates — all now use CIS_REPO.
tools/gates and enforcement/gates consolidated to one directory (symlink).
Dockerfile now seeds the six per-role skill sets instead of overwriting the
2026-08-25 split on every rebuild. /api/relay/<run_id> now returns stopped_by
and failed_checks. Commit 0365a18.
