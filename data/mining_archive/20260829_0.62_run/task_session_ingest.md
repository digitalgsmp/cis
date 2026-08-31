# TASK: Get Claude Code session reasoning into the KB

## The problem, stated as evidence
The KB answers architecture questions well through roughly June 2026. It knows the
drive topology (vdc = archive, 9.1TB, per ADR-003), the contracts, the ADRs.

It cannot answer anything about the last three days. The cis-pipeline container was
designed and built 2026-08-26..28 entirely in Claude Code sessions. Nothing from
those sessions reaches the KB. Verified this session: an attempt to recover why
cis-pipeline's mounts were chosen returned only material about a different
(LXC/Proxmox) container.

Last intake by source: pipeline_* 2026-08-28 (the pipeline records itself fine),
host hermes agents 2026-08-26, chat exports before 2026-06-27,
SESSION_INSIGHT_RECORDs 2026-04-24.

This is a clean cutoff at the point the work moved into Claude Code, not a defect
in the KB's design.

## Scope
Source: `~/.claude/projects/-mnt-projects-cis/*.jsonl` on the HOST.
Currently 2 files, 3,085 records, from 2026-08-26 onward.

Out of scope, but design so they plug into the same path later:
- Container agent history (`/home/worker/.hermes-*/state.db`) — blocked on queue
  item 3 mounting those dirs; ingesting now captures a fragment.
- Host hermes agent sessions — `tools/catalog/ingest_sessions.py` handles these
  already; it is only stale.

## Execution boundary — assume this unless you argue otherwise
Extraction runs on the HOST. Only the result is submitted to the pipeline for
review. The pipeline does not get filesystem access to the transcripts.

Reason: the container currently mounts `/mnt/projects/cis` and little else. It has
no access to `~/.claude/projects`, `/mnt/archive`, or `/mnt/models`. The corpus
carries an explicit boundary principle — "The container never touches your DB,
never touches your dashboard, never touches your archive" — though that was stated
about a different container and no record was found for cis-pipeline specifically.

If you conclude the mount should be added instead, say so and justify it against
that principle. Do not add it silently.

## THE OPEN QUESTION — this is what you are being asked to decide
Two designs exist in the record for getting session material into the KB. Both were
built. They disagree, and the disagreement was never resolved.

**A. Distill.** `docs/contracts/CIS Session Transcript Extraction Contract v1.md`.
A model reads the session and writes a fixed 7-section record: what was attempted,
what failed, what changed direction, what was decided and why, what is unresolved,
what was assumed, what changed about scope. Rules forbid sanitizing failures and
forbid duplicating ADRs.
Ran by hand April 2026 over 15 transcripts -> 16 records, now in
`data/drive_imports/`. Roughly 265 rows in knowledge_messages.
Weakness: it is a model writing prose about a session. That is failure mode 1 and 2
(self-reported completion, hallucinated claims) sitting inside the memory layer.

**B. Raw intent.** The "Raw Intent Corpus Algorithm" in the corpus, implemented as
`tools/extract_corpus.py`, `corpus_to_asks.py`, `cluster_corpus_themes.py`,
`synthesize_intent.py`, `rank_cards_by_corpus.py`, `generate_intention_cards.py`.
Stated rules: privilege operator-authored language over model language; chunk around
moments of intent, correction, rejection, desire; cluster repeated pressures until
objectives emerge from recurrence. `tools/mine_asks_claude_code.py` applies this to
Claude Code and deliberately carries nothing a model wrote.
Weakness: it keeps the operator's objections and drops what they produced.

**C. The requirement neither satisfies.** The reasoning in a session lives in the
pair — an objection and the revision it caused. A keeps the conclusion but asks the
reader to trust a model's account of how it was reached. B keeps the challenge and
loses the outcome. Nothing preserves the link.

Decide between A, B, or a design that satisfies C. State the reasoning. If you pick
A, specify how a claim in a record is traced back to the transcript line supporting
it — `mine_asks_claude_code.py` already writes a verbatim companion directory for
`card_gate --docs` to match against; that is the existing precedent for provenance.

## Secondary decisions
1. **Input conversion.** Claude Code writes `.jsonl` with tool calls, system
   reminders, file-history snapshots, queue operations mixed in. Specify what is
   stripped. `mine_asks_claude_code.py` has NOISE and HARNESS filters that agree
   with `mine_asks.py`; prefer reusing them over writing new ones.
2. **Which model does the work**, and why that one. Models are local
   (`/mnt/models`, `/mnt/models2`) so GPU time is the cost, not API spend.
3. **Ingestion mechanics.** Source name, `source_key` convention, dedup rule, FTS
   rebuild. `tools/catalog/ingest_sessions.py` is the precedent.
4. **Trigger.** Manual or automatic. Queue item 4 proposes "ingest sessions after a
   run" as self-regulating. Decide and justify.
5. **Output location.** Contract v1 names
   `docs/claude_chat_transcripts/insights/SESSION_INSIGHT_RECORD_YYYY-MM-DD_NNN.md`.
   That directory holds one unrelated file; the April records went to
   `data/drive_imports/` instead, which is gitignored (queue item 7). Reconcile.

## Constraints
- `data/cis_memory.db` is 4.8GB and is both spine and KB. Every write is backed up
  at 4.8GB against 70GB free (queue item 11). Do not design something that writes
  per session tick.
- The operator is not a coder and validates by output, not by reading code.
- Do not modify `runtime/abstraction/pipeline_relay.py`.
- The KB is ~299,612 rows and only ~0.09% is distilled. Raw bulk is the norm here,
  not the exception. Do not assume the distilled form is the house style.

## Acceptance test — must be checkable by a non-coder
After the change, this returns reasoning from the 2026-08-28 session:

    python3.12 tools/ask_history.py "why prompt size is unmeasured on agent calls"

Today it returns nothing from that session. Passing means one command surfaces
reasoning that currently exists only in git commit messages.

A second check, harder and more honest — this is the question that failed today:

    python3.12 tools/ask_history.py "why cis-pipeline mounts only the repo"
