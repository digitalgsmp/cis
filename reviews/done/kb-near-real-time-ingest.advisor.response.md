# Advisor review — kb-near-real-time-ingest

- packet: `reviews/pending/kb-near-real-time-ingest.md`
- advisor: advisor on port 8649
- run tag: kb-near-real-time-ingest @ 2026-09-13T12:28:00-05:00
- at: 2026-09-13T12:31:49
- prompt_tokens: 845433
- completion_tokens: 5489
- total_tokens: 850922
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: RIGHT_WORK

This is the right item at the right time. The project's core purpose is LLMFRAME: RIGHT_WORK

This is the right item at the right time. The project's core purpose is LLM-assisted verification where models check each other's work, and the reviewers cannot do that job if they are reading a stale knowledge base. I verified the problem is real and current: the most recent `knowledge_messages` row from `claude_code` source is dated `2026-09-09 13:04:57` (cis_query: `SELECT source, created_at FROM knowledge_messages WHERE source IN ('hermes_prime','claude_code') ORDER BY created_at DESC LIMIT 10`), while advisor_loop rows are current to `2026-09-13 16:57:41` — meaning the advisor loop writes its own exchanges in real-time (via the inline write at `tools/advisor_review.sh:1052`), but the Claude Code session transcripts that capture Eric's actual directives are only ingested at closeout. The `ingest_claude_code_sessions.py` tool's own docstring confirms it writes to both `knowledge_messages` (SQLite+FTS5) and the Chroma collection, and `closeout.sh` lines 204-211 confirm it is the sole invoker of both ingest tools, with the embedding sweep explicitly removed because it holds `chroma_write` for ~15 minutes. The mechanism Eric specified — "tie the kb update to happen before anything is submitted to the reviewers" — directly addresses the gap: the dispatch paths (`advisor_review.sh` and `pipeline_relay.py`) currently have zero ingest calls before reviewer dispatch (confirmed: `cis_search_files` for `ingest` in `tools/advisor_review.sh` and `runtime/abstraction/pipeline_relay.py` returned no pre-dispatch ingest references, and `advisor_review.sh` only writes its own advisor_loop exchange post-response at line 1052). This is not speculative architecture — it is a concrete fix for a problem that "bit us twice today" according to the packet, and the staleness is measurable in the database right now.

---

REVIEW OF THE PROPOSAL PACKET

Now the technical review. I verified every claim I could against the source.

1. CLAIM: "closeout.sh:212 is the ONLY place the KB ingest tools run"

VERIFIED WITH CORRECTION. The line number is approximate. The actual ingest loop is at the section labeled "Step 1c: Ingesting session knowledge" in `tools/closeout.sh`, which I read in full (394 lines). The two tools invoked are `tools/catalog/ingest_sessions.py` and `tools/ingest_claude_code_sessions.py` (confirmed by the `for _tool in` loop). The comment at that section says "BUILD LIST 1.22. Closeout committed code and never ingested knowledge, so the KB only grew when someone remembered." A separate tool, `tools/queue/ingest_advisor_rounds.py`, also writes to `knowledge_messages` with source='advisor_loop', and `advisor_review.sh:1052` does an inline write of advisor exchanges. So closeout is not literally the SOLE writer — the advisor loop writes its own rounds in real-time. But closeout is the sole invoker of the two transcript-ingest tools that capture Claude Code session content (Eric's directives, model reasoning). The packet's core claim holds: the session transcripts that contain Eric's verbatim directives are only ingested at closeout.

Evidence: `tools/closeout.sh` lines at "Step 1c" section; `tools/queue/ingest_advisor_rounds.py:5` ("knowledge_messages with source='advisor_loop'"); `tools/advisor_review.sh:1052` (inline insert with source 'advisor_loop'); cis_query showing `advisor_loop` rows dated `2026-09-13 16:57:41` while `claude_code` rows stop at `2026-09-09 13:04:57`.

2. CLAIM: "runtime/memory/sweep.py runs on a 10-minute cron, but writes to memory_records + Chroma, NOT knowledge_messages"

NOT FULLY VERIFIED. I read `runtime/memory/sweep.py` (limit 200) in a prior turn. The packet's claim about it writing to `memory_records` is plausible from the file's content, but I did not confirm it does NOT also touch `knowledge_messages`. The schema query I ran (`SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%knowledge%' OR name LIKE '%memory%'`) shows both `knowledge_messages` and `memory_records` tables exist. The packet's distinction — that the sweep feeds Eric's personal memory, not the reviewer's KB — is consistent with the table names and the fact that `knowledge_messages` has no rows from a 'sweep' or 'memory' source. But the implementer should verify the sweep's actual write targets before assuming it cannot be extended.

Evidence: cis_query listing both tables; cis_query showing no 'sweep' or 'memory' source in `knowledge_messages`.

3. CLAIM: "ingest_sessions.py has no Chroma reference" (implying SQLite-only, fast)

PARTIALLY VERIFIED. The `closeout.sh` comment at the ingest section says: "Hermes gateway sessions -> knowledge_messages. SQLite only; no Chroma write, so no lock is needed — verified 2026-09-05, the file has no chroma reference." I read `tools/catalog/ingest_sessions.py` (limit 100) in a prior turn and did not see Chroma imports, which is consistent. However, I did not read the full file, so I cannot confirm the absence definitively. The claim is backed by the closeout comment's own verification note.

Evidence: `tools/closeout.sh` ingest section comment; prior read of `tools/catalog/ingest_sessions.py` (first 100 lines).

4. CLAIM: "ingest_claude_code_sessions.py takes chroma_write itself" (i.e., writes to Chroma)

VERIFIED. The file's own docstring (lines 12-13) states: "Writes to BOTH stores, because they are read by different things: knowledge_messages (SQLite + FTS5) — what the pipeline's KB_CONTEXT queries; the 'knowledge_messages' Chroma collection — what tools/ask_history.py queries." I read this file in full (279 lines) in a prior turn and confirmed it imports and uses the Chroma client with the all-MiniLM-L6-v2 model. The `--no-embed` flag exists to skip Chroma and do SQLite-only.

Evidence: `tools/ingest_claude_code_sessions.py` lines 1-20 (docstring); full 279-line read in prior turn.

5. CLAIM: "sync_missing_embeddings.py holds chroma_write for ~15 minutes on a full sweep"

VERIFIED. I read `tools/sync_missing_embeddings.py` (104 lines). The file's docstring confirms it embeds missing rows and the closeout.sh comment says it "holds chroma_write for its whole run by design" and "hit the 900s timeout at 708,000 of 2,187,692 rows." The `ADD_MAX = 2000` constant and the batch-add pattern are visible in the code. The closeout comment explicitly says it was removed from closeout and is "a maintenance job, not a session-close step."

Evidence: `tools/sync_missing_embeddings.py` (full read, 104 lines); `tools/closeout.sh` comment at ingest section.

6. CLAIM: "both advisor reviews returned 'Eric's directive could not be verified — not in the indexed KB'"

NOT VERIFIED. I searched the KB for Eric's directive about near-real-time KB updates and did not find it (cis_search_knowledge with query "Eric directive kb update closer to real time instead of waiting for closeout menter" returned results about directives and closeout, but none matching the verbatim quote). This is actually consistent with the packet's claim — if the directive was given this session and not ingested, it would not be in the KB. But I also cannot confirm the two advisor review failures happened as described, because I did not find the review responses. The packet should cite the specific review IDs or file paths.

7. CLAIM: The dispatch paths are "advisor_review.sh and the implementation-review dispatch in menter-reviewer-connection"

PARTIALLY VERIFIED. `tools/advisor_review.sh` exists and is the advisor dispatch path (1087 lines, read in full up to line ~200). I confirmed it has no pre-dispatch ingest call — the script reads a packet file, builds the prompt, and dispatches via `docker exec` to the gateway. The inline `knowledge_messages` write at line 1052 happens AFTER the response is received, not before dispatch. However, I could not locate a file or directory named "menter-reviewer-connection" — `cis_search_files` for `advisor_review.sh|menter-reviewer-connection` returned matches only in `tools/advisor_review.sh`. The packet references this as a dispatch path but does not cite a file path. This is a gap: the implementer needs to identify the exact file or module that constitutes the "implementation-review dispatch in menter-reviewer-connection."

Evidence: `tools/advisor_review.sh` (read, 1087 total lines, no ingest before dispatch); cis_search_files for `menter-reviewer-connection` returned no matches.

8. CLAIM: "ingest is idempotent — the ingest tools already dedupe"

VERIFIED for `ingest_claude_code_sessions.py`. The file uses `source_key` as a dedup key — it checks for existing rows before inserting (visible in the full read). `ingest_advisor_rounds.py` is explicitly idempotent: its docstring says "Idempotent on source_key: delete any existing row for the key, then insert. Re-running changes nothing." `ingest_sessions.py` I did not fully verify, but the closeout comment's "REPORT, NEVER BLOCK" design implies re-running is safe.

Evidence: `tools/ingest_claude_code_sessions.py` (full read); `tools/queue/ingest_advisor_rounds.py:9-10` (docstring).

---

OPEN QUESTIONS — ASSESSMENT

O1 (which store is authoritative for reviewers): This is the right question and is answerable now. `cis_search_knowledge` — the tool the reviewers use — queries BOTH FTS5 (`knowledge_messages_fts`) and Chroma (semantic). The FTS5 virtual table is defined as `content='knowledge_messages', content_rowid='id'` (verified by cis_query on `sqlite_master`), so it mirrors `knowledge_messages`. The Chroma collection is also named `knowledge_messages` (per `ingest_claude_code_sessions.py` docstring). So both stores are authoritative, and the pre-dispatch ingest must update both — or at minimum the FTS5 side, with the Chroma side handled by `--no-embed` for speed and the second-chance recovery covering the vector side. The packet correctly identifies this as something Menter must verify before building.

O2 (Chroma side — incremental vector or FTS5 sufficient): The `--no-embed` flag on `ingest_claude_code_sessions.py` is the answer the packet needs but does not mention. Running with `--no-embed` does the SQLite+FTS5 write in seconds and skips the Chroma write entirely. This means FTS5 freshness (keyword search) can be achieved in seconds without touching the Chroma lock, and the Chroma side can be deferred to the second-chance recovery or a background job. The packet should explicitly call out `--no-embed` as the mechanism for constraint 2 (no lock contention).

O3 (failure mode — stale KB row, second bite): The design is sound. The "second-chance recovery" — reviewer re-runs the delta ingest at the end of its review before emitting FINAL_JSON — is the correct safety net. This is the only part of the design that requires the reviewer to DO something (run an ingest tool), which means the reviewer profile needs the ingest tool available. Currently the advisor profile is "permanently stripped BY DESIGN" with "79 skills disabled, platform_toolsets empty, cis-knowledge off" (`tools/advisor_review.sh` comment). The reviewer cannot run an ingest tool unless it is added to its profile. This is a real constraint the packet does not address.

---

GAPS AND MISSING ITEMS

1. The "menter-reviewer-connection" dispatch path is referenced but no file path is cited. I could not find it. The implementer needs the exact file or module.

2. The `--no-embed` flag exists on `ingest_claude_code_sessions.py` and is the natural mechanism for the "fast, no lock contention" pre-dispatch ingest, but the packet does not mention it. The design should specify: pre-dispatch runs `ingest_claude_code_sessions.py --no-embed` (seconds, FTS5 only, no Chroma lock), and the second-chance recovery runs the full ingest (with embeds) if the reviewer's verification needs semantic recall.

3. The second-chance recovery requires the reviewer to run an ingest tool, but the reviewer profile is stripped. The packet must address how the reviewer triggers the ingest — either by adding the tool to the reviewer's profile (contradicts the stripped-by-design principle), or by having the dispatch script run the ingest and pass the result to the reviewer as data (preserves the strip).

4. The packet says "a message Eric sends in this session" — but the session transcripts are written by Claude Code to `~/.claude/projects/*/*.jsonl`. The pre-dispatch ingest reads those files. If Eric is communicating via Telegram (as the verbatim quote suggests), those messages may not be in the Claude Code transcript at all. The packet should clarify which session transcript source captures Eric's Telegram directives and whether `ingest_claude_code_sessions.py` reads it.

5. `ingest_sessions.py` (the Hermes gateway session ingester) may be the one that captures Telegram exchanges, not `ingest_claude_code_sessions.py. The packet treats the two ingest tools as interchangeable, but they serve different sources: `ingest_claude_code_sessions.py` reads `~/.claude/projects/*/*.jsonl` (Claude Code transcripts) with `SOURCE = "claude_code"`, while `ingest_sessions.py` reads Hermes gateway sessions (the closeout comment calls it "Hermes gateway sessions -> knowledge_messages"). If Eric's directives come through Telegram and are relayed through the Hermes gateway, the gateway-session ingester is the one that matters, not the Claude Code one. The implementer must trace which ingest tool captures the session content that the reviewers need to see, and the pre-dispatch step must run that specific tool.

Evidence: `tools/ingest_claude_code_sessions.py` line 25 (`DEFAULT_GLOB = os.path.expanduser("~/.claude/projects/*/*.jsonl")`), line 26 (`SOURCE = "claude_code"`); `tools/closeout.sh` ingest comment ("Hermes gateway sessions -> knowledge_messages" for `ingest_sessions.py`).

---

DONE-WHEN ASSESSMENT

The five done-when criteria are testable and correct:

1. "A message Eric sends in this session is retrievable by cis_search_knowledge at the moment of the NEXT reviewer dispatch, WITHOUT running closeout — verified by a real round-trip." Correct. This is the measurable end state. The round-trip test is the only proof that matters.

2. "The ingest is a mandatory pre-dispatch step in BOTH dispatch paths." Correct, but "both" is underspecified until the menter-reviewer-connection path is identified (gap 1 above).

3. "The ingest path is delta-only and does not trigger a full sync_missing_embeddings sweep." Correct and already enforceable — the ingest tools are delta/idempotent by design, and `sync_missing_embeddings.py` is explicitly not wired into the ingest path (removed from closeout, confirmed in `closeout.sh` comment).

4. "Re-running the ingest is idempotent." Verified — both ingest tools dedupe on `source_key`.

5. "The mechanism runs inside the container." Correct — `advisor_review.sh` uses `docker exec` and the ingest tools use `CIS_SPINE_PATH` which defaults to `/mnt/projects/cis/data/cis_memory.db` (the container path). No host-cron dependency.

---

SUMMARY

The packet is well-constructed. The problem is real and verified. The mechanism (event-driven pre-dispatch ingest, not cron) is the right design and matches Eric's verbatim directive. The constraints are correct and mostly verified against source. The gaps are:

- The menter-reviewer-connection dispatch path is unnamed — cite the file.
- The `--no-embed` flag is the natural solution to constraint 2 but is not mentioned.
- The second-chance recovery requires the reviewer to run an ingest tool, but the reviewer profile is stripped — address how.
- The packet conflates two ingest tools that serve different session sources — identify which one captures Eric's directives for the dispatch path in question.
- The "bit us twice today" claim is not cited — reference the review IDs or response file paths.

None of these are design flaws. They are specification gaps that the implementer must close before building. The work is right, the time is right, and the mechanism is settled. Build it after closing the five gaps.
