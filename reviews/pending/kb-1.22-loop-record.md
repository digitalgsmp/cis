CARD: KB-1.22-LOOP-RECORD
INTENT: 1.22's open half — the advisor loop writes its own record, so an
exchange survives without depending on being quoted inside a Claude Code
transcript that happens to get ingested. ONE write to tools/advisor_review.sh
plus one new tool. Back up first, state the paths. No schema change. No commit.

--- STEP 1 (read-only): confirm the item is still not in the code ---
sqlite3 data/cis_memory.db "select count(*) from knowledge_messages where source like '%advisor%' or source like '%delib%'"
sqlite3 data/cis_memory.db "select count(*) from deliberation_rounds where run_id like 'advisor-%' and reviewer_role!='pause'"
grep -c "knowledge_messages" tools/advisor_review.sh
Report all three. Expected 0, ~26, 0. If the first is non-zero, STOP — something
already ingests the loop and this card is written against a stale premise.

--- STEP 2: backup ---
cp tools/advisor_review.sh data/backups/advisor_review_$(date -u +%Y%m%dT%H%M%SZ).sh
sqlite3 data/cis_memory.db ".dump knowledge_messages" is 2.65M rows — do NOT dump it.
Instead record the row count before and after; that is the reversible fact.

--- STEP 3: THE BUILD ---

A. WRITE AT ROUND TIME, NOT AT CLOSEOUT.
   advisor_review.sh already opens the spine and inserts into
   deliberation_rounds. The knowledge write goes in the same block, immediately
   after, in the same connection. Closeout-only writing means every reader
   between two closeouts sees a loop that said nothing — 1.26's argument, and
   this is four lines rather than a new invocation point.

B. ONE ROW PER ROUND, NOT PER OBJECTION.
   A round is one lineage's answer to one packet. That is the natural unit of
   "what did this reviewer say". Splitting a 4,000-character answer into
   findings requires parsing prose and would be guessing at boundaries.

C. THE ROW MUST BE SELF-DESCRIBING.
   A search hit that returns reasoning with nothing to anchor it is retrievable
   and useless. The content field opens with a header line carrying the card,
   the round, the lineage, the frame verdict and the result verdict, then the
   text as the model wrote it:

     [advisor <card> round <n> <lineage>] frame=<FRAME> verdict=<VERDICT>
     <the objection text, verbatim>

   source     'advisor_loop'   — distinct from 'claude_code', which is how these
                                 exchanges have been arriving by accident
   source_key 'advisor/<card>/<lineage>/<round>'
   role       'assistant'
   timestamp  the round's created_at

D. IDEMPOTENT ON source_key.
   Delete any existing row with that source_key, then insert. A round that is
   re-run replaces its own row rather than accumulating duplicates.

E. BACKFILL THE 26 ROUNDS ALREADY RECORDED.
   tools/queue/ingest_advisor_rounds.py — same write, applied to every existing
   advisor round in deliberation_rounds. Without it, today's exchanges are the
   last generation lost, which is the exact failure this item names.

--- STEP 4: verify by output ---
1. Rows sourced from the loop, before and after backfill. Expect 0 -> 26 or more.
2. Run one live review round. Expect the count to rise by exactly 2 — one per
   lineage — with no closeout in between.
3. Run the backfill twice. The second run must not change the count.
4. THE CHECK THAT CATCHES THIS CARD LYING: search for a phrase that appears only
   in an advisor exchange and never in a Claude Code transcript, and confirm the
   hit's source is 'advisor_loop'. On 2026-09-07 this item looked closed because
   29 hits came back — all of them source='claude_code', arriving by transcript.
   A count going up is not evidence the loop wrote anything.
5. Print one ingested row in full and confirm a reader can tell, from the row
   alone, which card and which lineage it came from.

--- STEP 5: report ---
Row counts at each step, the full text of one ingested row, and check 4's result.

DONE WHEN: a review round writes its own knowledge rows with source
'advisor_loop' at the moment it runs, the 26 existing rounds are backfilled,
re-running changes nothing, and check 4 returns a hit that did not come from a
transcript.

IF ANY CHECK FAILS: stop, restore from the backup, report. Do not repair forward.

NOT IN THIS CARD — and this is the load-bearing exclusion:
  * RETRIEVAL. Capture is not retrieval. The reviewers have no tools and cannot
    query the knowledge base. This card makes the record exist; it does not make
    the next reviewer warm. Ending the cold start needs the packet assembly to
    put prior exchanges in front of them, which is separate work and is what
    1.22 is actually blocking 1.18 through 1.21 on.
  * Any schema change. knowledge_messages is used as it stands.
  * Real-time queue state (3.29), the reply path, closeout, any commit.
