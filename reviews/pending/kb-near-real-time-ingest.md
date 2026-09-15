# Near-real-time KB ingestion — stop waiting for closeout

VERSION 3 — 2026-09-13. Folded dual-reviewer findings (both RIGHT_WORK, 2026-09-13).
Status: READY_TO_BUILD. Corrections since V2:
- **FTS5 "seconds" claim was WRONG** (evaluator). `ingest_sessions.py` runs a FULL
  `knowledge_messages_fts` rebuild (`VALUES('rebuild')`) every invocation — minutes,
  not seconds. Pre-dispatch ingest must use incremental FTS5 (triggers or row-level
  insert), and/or the `--no-embed` flag for the fast path. Constraint 5 corrected.
- **Second-chance recovery fixed** (advisor). The reviewer profile is stripped to
  zero tools — the reviewer CANNOT run an ingest tool. The DISPATCH SCRIPT runs the
  delta ingest and passes the result to the reviewer as data. Recovery preserves
  the strip.
- **Correct ingest tool identified** (advisor). Eric's Telegram directives live in
  Hermes GATEWAY sessions → `ingest_sessions.py` (not `ingest_claude_code_sessions.py`,
  which reads `~/.claude/projects/*.jsonl`). Pre-dispatch runs the gateway-session
  ingester.

GOAL_ALIGNMENT: seed intent 2 ("the LLMs are the tools, I am trying to get LLMs to
help me think... they don't remember anything") + seed intent 1 (models verify each
other's work). The reviewers must be able to see what Eric said THIS session, not
what was true at the last closeout.

Eric directive (verbatim, this Telegram session 2026-09-13):

> "then another job for menter is to make the kb update happen closer to real-time
> instead of waiting for a close out."

## Problem

The reviewers query the knowledge base (`cis_search_knowledge` → `knowledge_messages`
FTS5 + Chroma). That table is only populated at **closeout** — `tools/closeout.sh`
is the sole invoker of the ingest tools. So during a live session, the reviewers
cannot see anything Eric or the pipeline said since the last closeout.

This bit us twice today: both advisor reviews returned "Eric's directive could not
be verified — not in the indexed KB." The reviewers were reading a stale index and
flagged real directives as unverifiable because the ingestion only runs at closeout.

## Verified current state (evidence)

- `tools/closeout.sh:212` is the ONLY place the KB ingest tools run:
  `tools/catalog/ingest_sessions.py` + `tools/ingest_claude_code_sessions.py`.
  These write `knowledge_messages` (the FTS5 + Chroma store the reviewers read).
- `runtime/memory/sweep.py` runs on a **10-minute cron**, but it writes to
  `memory_records` + Chroma vectors — Eric's unified personal memory, NOT the
  `knowledge_messages` store the reviewers query. So even the existing near-real-time
  sweeper does not help the reviewers.
- Constraint (documented in `closeout.sh:204-211`): `tools/sync_missing_embeddings.py`
  holds `chroma_write` for ~15 minutes on a full sweep, blocking semantic search for
  the whole window. A full re-embed is a maintenance job, NOT a near-real-time step.
- **FTS5 rebuild is NOT incremental** (evaluator, verified): `ingest_sessions.py`
  runs `INSERT INTO knowledge_messages_fts(knowledge_messages_fts) VALUES('rebuild')`
  — a full index rebuild on every call, minutes on a 287K-row table. The fast path
  must avoid this.
- **Correct ingest tool** (advisor, verified): Eric's Telegram directives arrive via
  the Hermes GATEWAY session files → `tools/catalog/ingest_sessions.py` (source
  `hermes_prime` / gateway sessions). `tools/ingest_claude_code_sessions.py` reads
  `~/.claude/projects/*.jsonl` (source `claude_code`) — the wrong tool for Telegram
  directives. The pre-dispatch step must run the gateway-session ingester.

## Requirement

The KB the reviewers read (`knowledge_messages` + its vector index) must be updated
**immediately before every reviewer dispatch**, not only at closeout, so a directive
Eric gives this session is visible to the reviewers the moment they are asked.

Mechanism (settled): ingest is a mandatory pre-dispatch step. The dispatch path
(`advisor_review.sh` and the implementation-review dispatch in
`menter-reviewer-connection`) must run the delta ingest to completion BEFORE the
packet is built and the gateway call is made. No cron, no clock, no race.

Second-chance recovery (settled by Eric): if the pre-dispatch ingest did not
complete in time, the DISPATCH SCRIPT re-runs the delta ingest at the END of the
review — immediately before the FINAL_JSON verdict is emitted — and passes the
result to the reviewer as data so it can adjust its verdict if new content arrived.
The reviewer does NOT run the ingest tool itself: its profile is stripped to zero
tools by design, and that strip is preserved. The dispatch script is the actor; the
reviewer only reads the fresh data.

Constraints that must hold:
1. **Delta/append-only** — only NEW session messages since the last ingest, never a
   full rebuild. A full re-embed blocks semantic search (the `chroma_write` lock).
2. **No lock contention** — the FTS/SQLite side must be INCREMENTAL (FTS5 triggers
   or row-level insert, NOT `VALUES('rebuild')`), or use `--no-embed` for the fast
   pre-dispatch pass. The Chroma/vector side must be incremental or deferred.
3. **Idempotent** — re-running must not duplicate rows (the ingest tools already
   dedupe on `source_key`; the near-real-time path must preserve that).
4. **Runs inside the container** — not host cron, matching the container-residency
   direction.
5. **Must not block dispatch indefinitely** — the pre-dispatch ingest should be fast;
   if it cannot complete quickly, the dispatch proceeds with a recorded "stale KB"
   row, and the second-chance recovery (dispatch-script re-run + fresh data to the
   reviewer) covers the miss. Never a hard gate that deadlocks the pipeline.

## Open questions for reviewers to adjudicate

O1. **RESOLVED (advisor):** `cis_search_knowledge` reads BOTH FTS5
    (`knowledge_messages_fts`, content='knowledge_messages') AND the Chroma
    `knowledge_messages` collection. Both stores are authoritative; both need
    updating for full coverage.
O2. **RESOLVED:** reviewers need both for verification — FTS for exact directive
    text, vectors for semantic recall. Pre-dispatch uses `--no-embed` (SQLite+FTS5,
    fast); the Chroma side is incremental/deferred to the second-chance recovery.
O3. **RESOLVED (mechanism corrected):** if the pre-dispatch ingest fails or times
    out, dispatch proceeds with a "stale KB" row; the DISPATCH SCRIPT (not the
    reviewer) re-runs the delta ingest at end-of-review and passes fresh data to the
    reviewer before FINAL_JSON. Never deadlock.

## DONE-WHEN

- A message Eric sends in this session is retrievable by `cis_search_knowledge` at
  the moment of the NEXT reviewer dispatch, WITHOUT running closeout — verified by
  a real round-trip (send → dispatch → reviewer tool returns it).
- The ingest is a mandatory pre-dispatch step in BOTH dispatch paths (advisor card
  review + implementation review), and runs the GATEWAY-session ingester
  (`ingest_sessions.py`), not the Claude-transcript ingester.
- The FTS5 update is incremental (triggers or row-level insert), NOT a full
  `VALUES('rebuild')` — verified by timing a pre-dispatch ingest on the live table.
- The ingest path is delta-only and does not trigger a full `sync_missing_embeddings`
  sweep (no `chroma_write` lock held for minutes).
- Re-running the ingest is idempotent (no duplicate `knowledge_messages` rows).
- The mechanism runs inside the container.
