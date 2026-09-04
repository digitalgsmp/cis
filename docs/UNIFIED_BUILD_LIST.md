# UNIFIED BUILD LIST — what is NOT in the code

**Date:** 2026-08-29
**Replaces:** `docs/NEXT_SESSION.md` as the working list. That file keeps its
Goal, Method and Decisions-to-Protect sections — those are not tasks.

## The test used to build this list

Eric, 2026-08-29:

> *"I don't care what the files say. All that is important is what issue the
> files addressed, if they are valid concerns that are still relevant to the
> pipeline functioning. If they are not currently in the code, it goes on the
> list."*

So every item below was checked **against the running code**, not against a
document. A specification saying something exists is not evidence. A contract
marked LOCKED is not evidence. The only question asked was: **is this capability
present in the code today?**

Where a spec exists it is noted as a *reference for when we build*, never as a
reason to demote or skip an item. Final evaluation of each item happens when we
reach it.

**Sources of the issues:** the knowledge base (6,578 mined statements ->
1,261 clusters, read individually), the filesystem (~120 distinct specs found by
reading content, not filenames), and 9 defects found by running commands on
2026-08-29.

---

# TIER 0 — trust preconditions

### 0.1 Foreign-key enforcement is off almost everywhere
**In code:** `PRAGMA foreign_keys = ON` appears in **5 places** — three
`eric_gate` tools, its tests, `gate_db_state.py`. `pipeline_relay.py`,
`runtime/api/relay.py` and every ingest tool open connections without it.
SQLite enforces per connection, and the factory creates a new connection per
call.
**Measured damage:** 80 `foreign_key_check` violations in the live spine.
`decision_trails` rows point at `workflow_runs_old`, a table that no longer
exists — and those are the rows the Eric Gate briefing reads. 15
`eric_gate_approvals` reference goal_references that do not exist.
**Do this first — one fix at the factory closes it everywhere.**

**DONE on the pipeline path, 2026-08-30.** The order mattered: eight tables
declared their FK against `workflow_runs_old`, and SQLite does not warn about a
constraint naming a missing table — it refuses the write. Flipping the pragma
first would have made the next gate approval fail with *"no such table:
main.workflow_runs_old"*. So the sequence was repair, then enforce:

1. `tools/repair_fk_definitions.py` — repointed 8 constraints across 7 tables
   at `workflow_runs`, rewriting the CREATE TABLE text in place via
   `writable_schema` so no table was rebuilt and no data moved. 80 -> 24.
2. `tools/repair_fk_orphans.py` — 15 July approvals carrying
   `goal_reference_id = 0` (a stand-in used before `goal_references` existed)
   were backfilled with a goal row each from their run's own topic, tagged
   `authored_by = 'BACKFILL_20260830'`; 9 rows of June debris with missing
   parents were deleted. 24 -> **0**. No approval was deleted.
3. `PRAGMA foreign_keys = ON` at both live factories —
   `pipeline_relay._db_connect` and `runtime/api/relay._db` — and `_heartbeat`
   routed through the factory rather than opening its own connection.

Verified: both factories report `foreign_keys = 1`, an insert naming a
nonexistent run is rejected with `IntegrityError`, `foreign_key_check` is 0,
`integrity_check` is ok, and `tests/test_eric_gate.py` passes 28/28.

**Still open — the ingest tools were not touched.** 18 tools under `tools/`
open the spine with no pragma, including `ingest_claude_code_sessions.py`,
`ingest_hermes_sessions_v2.py`, `rebuild_vector_index.py` and `state_write.py`.
The spine is at zero violations now, so any new one has a known source. One
behaviour change to know about: `INSERT OR IGNORE` does **not** suppress an FK
violation, so the never-used `/decompose` endpoint's caller-supplied
`depends_on` would now raise rather than silently no-op.

### 0.2 Secrets can reach agents through KB results — LIVE TODAY
**Checked in code:** `SecretFilterPipeline` exists in
`runtime/mcp_bridge/chroma_index.py` with patterns for private keys, bearer
tokens, JWTs, `sk-` API keys, AWS keys, GitHub tokens and generic
`API_KEY=`/`SECRET=` assignments. It is instantiated as `self._filter` and used
**only inside `index_from_spine()`**, which writes different collections
(`cis_sessions`, `cis_deliberations`, …).

- `pipeline_relay.py` KB_CONTEXT path: **0 references to the filter**
- `tools/ask_history.py`: no filter
- The two gates written to catch this — `gate_chroma_no_secrets_in_results` and
  `gate_chroma_secret_filter` — **have never fired** (see 2.15)
- **A live query for "api key token password secret" returned 2 secret-shaped
  strings in the top 20 results.** Placeholders this time
  (`SECRET='PASTE_NEW_SECRET_HERE'`), which proves the path, not the payload.

**Introduced/worsened 2026-08-29 by me:** `rebuild_vector_index.py`,
`ingest_claude_code_sessions.py`, `ingest_hermes_sessions_v2.py` and
`rechunk_for_embedding.py` all embed directly and bypass the filter. 451,167
chunks were indexed without it, and the container was then wired to query them.

**Two fixes needed:** filter at query time before results enter an agent prompt,
and filter at index time in the ingest tools.

**DONE 2026-08-30.** Both halves. `redact_secrets()` on the read side at three
choke points — `pipeline_relay._add_hit` (covers both KB_CONTEXT branches),
`pipeline_relay._pre_discovery` (the single join of everything it found), and
`tools/ask_history.py`. `filter_for_index()` on the write side, before every
`coll.add()` in all five ingest tools.

**Read redacts, write excludes** — deliberate, not an oversight. 112 KB rows
carry a PRIVATE KEY header and 111 are agents *discussing* key handling with no
key in them. Applying the index-time exclude rule at read time would drop all
112, so asking the pipeline how to handle secrets safely would return nothing.
Refusing to display an already-stored row protects nothing that masking does not.

Measured before and after on the same 100 live keyword results: **48 secret
values present before, 0 after.** Both gates in 2.15 fired for the first time
and PASS. `_redact_secrets` fails closed — if the filter cannot be imported the
KB material is withheld with the reason stated, never passed through.

Nothing found was a live credential: placeholders, documentation, and one
deliberately-corrupted RSA test fixture from the archive. The defect was that
nothing stood in the way.

Two defects found by testing the fix rather than trusting it, both now closed: a
PEM header is only the first *line* of a secret, so redacting the matched span
left the key body underneath it; and a block pattern requiring 16+ base64
characters per line leaked a key whose final line was 12 — chunking splits keys
mid-block, so the truncated case is the common one.

### 0.3 Chroma concurrency arbitration
**In code:** nothing. The container queries Chroma live; a host ingest during a
run corrupts the read — proven: *"Error deserializing pickle file: trailing
bytes found"*. Needs a lock, a maintenance window, or ingest moved inside.
**Blocks:** every item that runs an ingest.

**DONE 2026-08-30 — a lock, in `runtime/mcp_bridge/chroma_lock.py`.**

Not a maintenance window: that is a rule someone has to remember, and it has to
hold when nobody is watching. Not ingest-moved-inside: an image rebuild and a
larger change than the problem needs. A file lock is enforced by the kernel.

**It works across the container boundary, verified rather than assumed.** The
repo is bind-mounted and host and container share one kernel, so an `flock` on
the mounted file is the same lock on both sides. The lock sits beside the store
and is named from `CIS_CHROMA_PATH`, which the container sets and the host
defaults — both resolve to the same file.

**Asymmetric by design.** Readers take a SHARED lock, wait 5s, then **give up
rather than hang** — a run must never stall because an ingest started, so
`pipeline_relay` degrades to keyword search, which covers 100% of the corpus,
and says why. Writers take an EXCLUSIVE lock and **raise rather than proceed**:
an ingest that cannot get the lock must not write, because proceeding is what
corrupts a live read.

Wired: `pipeline_relay` semantic branch and `ask_history` as readers;
`rebuild_vector_index`, `rechunk_for_embedding`, `sync_missing_embeddings`,
`ingest_claude_code_sessions`, `ingest_hermes_sessions_v2` as writers. Each
writer holds the lock across its **whole** run, not per batch — rebuild drops
the collection before refilling it, and rechunk deletes each row before adding
its replacements, so a reader admitted between batches would see a half-built
index rather than a stale one.

Tested end to end with the container live: host reader refuses with exit 2 during
a write; container reader correctly kept out; the pipeline's own brief builder
returned in 5.2s instead of hanging, still produced keyword hits, and carried
the note *"semantic search skipped (KB ingest in progress)"*; a writer blocked by
a live reader refused with a plain-language message; two readers hold at once;
everything works normally once released.

---


## From the 2026-08/09 mining pass — added 2026-09-01

Evidence for every item below is in `data/mining_archive/MINED_TASKS.md`. Scope says whether the finding was verified against the container in production or against code the container does not execute; the latter is not the same as irrelevant.

### 0.4 Override plane and fail-mode policy before any blocking gate is trusted

The v2.0 deadlock came from a clearance token the gate itself could prevent you from writing. Build and prove an out-of-band override first; state fail-open vs fail-closed per mode.

**Scope:** CONTAINER — the .GATE_DISABLED override plane is repo-level and applies to both pipelines

**Need: HALF DONE 2026-09-04.** The override plane is built and proven. The fail-mode policy is not, and is now safe to change.

**Built:** `.gate-control/` on the host, mounted read-only at `/opt/cis-control/gate`, with the check as the **first statement** of `_pre_tool_call` in `plugin/__init__.py` — above the logging and above the subprocess, so a hook that cannot log and a runner that will not start can both still be overridden. `touch .gate-control/DISABLED` disables the wall, `rm` re-arms it, neither needs a restart. An unreadable override falls through to enforcement rather than disabling it: the failure of the off switch must not itself be an off switch.

**Read-only is the design.** The agents can read that file and can never create it — an override the constrained agent can set is a self-disable. Kernel-enforced at the mount layer, so it holds for root inside the container too.

**Proven, per the record's requirement that a deterministic test pass before the wall is trusted.** `tools/test_override_plane.sh`, run from a bare shell with no Hermes involved, six assertions all passing: blocked call blocked; container sees the file through the mount; same call allowed; the override recorded in `gate_override.log`; **the container refused to create the file itself**; block restored on removal. It refuses to run if the override is already active rather than deleting an operator's own flag during cleanup.

**Still open — the fail-mode half.** `plugin/__init__.py:50` still returns `None` on every failure path: a timeout at 10s, a missing runner, a non-zero exit, malformed JSON, empty stdout. Five routes to allow, and the gate cannot detect its own non-execution — failure mode 11, and the KB already flagged it: *"Fail-open default contradicts your fail-closed requirement. The hook system proceeds when the gate errors/times out."*

**Why the order was right.** Today's system cannot deadlock precisely *because* it fails open — the v2.0 deadlock happened when a hook failed closed with no escape hatch. The override plane is not protection against the system as it stands; it is the precondition for changing the failure mode. That change is now safe to make, and it is the remaining work on this item. Commit `de42c8c`.


**Evidence:** raised 2 times, 2026-06-27 to 2026-08-29; mining_candidates 1462,508; full record in `data/mining_archive/MINED_TASKS.md`.

### 0.5 Secure the operator surfaces before any field exposure

Flask has no app-level login and Phase 0 (backup safety net) is deferred with backup integrity unverified; /ui/schedule was blocked on an authentication review that never happened, and the page carries client, work and personal obligations.

**Scope:** NOT_IN_CONTAINER_PATH — the Flask dashboard and its login surface run on the VM

**Need:** OPEN — Flask has no app-level login and the field-access security review was never done. Neither pipeline supplies authentication for the operator surface, so the need stands.

**Evidence:** raised 2 times, 2026-06-01 to 2026-08-29; mining_candidates 15004,3620; full record in `data/mining_archive/MINED_TASKS.md`.


# TIER 1 — blocks a run completing end to end

### 1.1 Prove a run completes past the gate
No run has ever gone intake -> deliberation -> gate -> implement -> verify ->
done. Furthest reached: ERIC_GATE. Depends on 1.2.

**DONE 2026-08-30. `run-e70293544935a92e-1787973534` completed end to end** —
PATTERN_CATALOG -> CODE_REVIEW_GATE -> VERIFICATION -> `VERIFY PASS`, result and
`completed_at` written. It took the 1.9 repairs to get there: approval had been
structurally impossible, not merely unused.

**The output is factually correct, checked independently.** All seven of its
verifiable claims hold: live file 3895 lines, one sanitizer at line 273, grep
count 1, backup 3577 lines, blacklist at backup lines 588 and 1024, backup grep
count 0, docstring at 260-263.

**What makes this more than a green light — the review gate caught a poisoned
verification criterion.** The draft spec, frozen 2026-08-29, told the implementer
to write line numbers 644/1094 and attested *"GROUND TRUTH VERIFIED THIS RUN"*.
Brain's pattern catalog re-verified and got 3895/273. Reviewer A flagged that
following the spec would embed false evidence. Reviewer B escalated it:
> *"Section 0's claim is a lie independent of Section 3... The spec's Section 5
> verification criteria are poisoned. They instruct the verifier to confirm the
> file contains line references 644 and 1094. If Menter wrote the CORRECT numbers
> (273), the spec's own verifier would FAIL the correct file. If Menter wrote the
> FALSE numbers, the spec's verifier would PASS the false file. Following the
> spec's verification certifies a lie."*
First chunk came back CHANGES_REQUESTED; the revision was approved. The file
carries an explicit provenance note recording the governed deviation. **A run
detected that its own success criteria would have certified a falsehood** —
the "optimizes the referee" failure of 4.10, caught in the wild.

**144 guardrails fired: 128 PASS, 12 SKIP, 4 FAIL, none blocking.** Live data for
the 2.1 audit, and three findings worth keeping:
- `effort_metric` FAILED twice, *"sandbagging suspected"*, on a task whose correct
  output is a short markdown file. **3.9 confirmed in the wild.**
- The three BLOCK-mode verification guardrails all SKIPPED —
  `claim_action_verifier` (*"no file or function claims detected"*),
  `intent_compliance` (*"no Python code blocks to test"*),
  `capability_claim_verifier` (*"no capability claims detected"*). Legitimate for
  this task, and the point: **on a documentation task the three strongest checks
  are inert.** They are shaped for code. Same shape as 3.9.
- `intent_drift` FAILED twice (0.63 DIVERGED, 0.42 SIGNIFICANT_DRIFT) — and it
  was RIGHT: the run deliberately deviated from a spec that was wrong. Advisory,
  so nothing acted. Had it been BLOCK it would have killed a correct deviation.
  **2.1's tension in one run: the guardrail that fired correctly is the one that
  could not act, and arming it as-is would have blocked the right answer.**

**One data point, not a proof of reliability.** One small task, one file, no code
written. What it establishes is that the path is walkable.

**The code run is also the loop's first real test — added 2026-09-02.** A code
run produces a result neither Eric nor Claude Code can fully evaluate alone,
which is exactly the case the three-role review (1.20) exists for. Run it
through the loop rather than beside it: the card reviewed before it executes
(1.18), the result objected to and answered (1.19), the engineering evaluated by
Qwen (1.20). A code run checked the old way would prove the pipeline walks and
prove nothing about whether the check on it works.

### 1.2 Approve or close run-e70293544935a92e-1787973534  — **Eric's decision**
Briefing renders, hash stable, goal_reference 12 exists. Two 2026-08-22
throwaways also sit at the gate (`"test"`, `"smoke check"`) — close those.

### 1.9 Two approval paths, and the documented one does not continue the run
**Found 2026-08-30 while trying to action 1.2. This is very likely why 1.1 has
never happened.**

**`tools/eric_gate/record_decision.py`** — the path NEXT_SESSION.md documented
as *the* way to approve — records the approval, sets `eric_approved_at`, prints
*"Decision recorded: APPROVE"*, and **leaves `status` at `ERIC_GATE`**. It never
advances the run. `PipelineRelay.resume()` on an `ERIC_GATE` run prints
*"waiting at ERIC_GATE"* and returns. So an approval through the documented
route parks the run forever and reports success while doing it.

**`runtime/api/relay.py`** — sets `status = 'PATTERN_CATALOG'`, then spawns a
background thread to carry on. This one works.

**Neither path is complete, and their defects are complementary:**
- the CLI path writes a proper `id` but does not advance the run
- the API path advances the run but omits the `id` column entirely — that is
  2.17, why all 26 approvals have a NULL primary key

**And the working path is not currently usable.** Checked 2026-08-30: no
`CIS_PIPELINE_API_KEY` in the container and nothing answering on the relay port.

Failure mode 11 — a silent gate failure, inside the gate. An operator following
the written instructions gets a success message and a run that never moves, with
nothing anywhere saying why.

### 1.10 Assistant work reaches the code without ever passing a gate
**Eric, 2026-08-30, after a full day of repairs he could not independently
check:** *"How would I have been able to approve or check into any of what you
just did? Is there a solution to how the user will work in these situations?
Have I designed an interface where everything is explained and qualified for me
to give approval?"*

**Answer, checked: yes he designed it, and it was never built.**
`docs/CIS_PIPELINE_VISIBLE_PORTAL_SPEC.md`, 2026-06-23, written by
deepseek-v4-pro after Eric's design direction. Core principle, verbatim:
*"The user does not leave the conversation. The pipeline does not run in a black
box... Nothing executes without Eric seeing it. The panels ARE the pipeline."*
It specifies a mandatory clarification stage before anything fires, then live
panels for route, drafter, reviewers and each gate's PASS/FAIL, with an
interject box at every stage. `runtime/cis_dashboard.html` is 3,194 lines, last
modified 2026-05-04, never committed since. The 13 `gate_11a_*`/`gate_11b_*`
scripts were written to guard that approval UI and are among the 33 in 2.15 that
have never fired.

**But the portal would not have covered today, and that is the larger gap.**
The portal governs PIPELINE runs. On 2026-08-30 an assistant made ~20 commits to
the spine, the relay, the gate tooling and the ingest tools with no gate, no
reviewer, no verification and no approval. Eric had the assistant's own
descriptions and nothing else: the assistant chose the checks, ran them, and
reported the results. Three self-caught errors that day were self-caught —
nothing structural would have caught them otherwise. This is the failure Eric
named the same day as *"you are working on me correcting."*

**The artifact already exists.** The Eric Gate briefing renders action summary,
reversibility, files touched, goal trace, decision trail, objections and drift,
in plain markdown, with a hash that fixes it between reading and approving.
Nothing routes assistant work through it.

**Design constraint, to be settled before building:** the unit of approval must
be the WORK ITEM, not the commit. Per-commit briefings would have meant twenty
approvals in one day, and he would have stopped reading at the fourth. Four
briefings — one each for 0.1, 0.2, 0.3 and the gate repairs — is a load a person
sustains. Each answering: what was broken, what changed, what proves it, what
happens if it is wrong.

**Relationship to 4.10:** this is that idea's missing front half. A pipeline
that recommends and an API that implements still needs Eric in between, reading
something he can judge. Without it the loop is automated and he is outside it,
which inverts what the gate is for.

**Not the portal.** Tier 10/11 UI work is a bigger, later job. This is the
narrow version: make non-pipeline changes produce the same briefing and pass the
same gate that pipeline runs already do.

---

#### The design, 2026-08-30

Eric on the portal spec and the dashboard: *"there is no confirmed interface,
everything had been misinformed experiments."* So this starts from the workflow,
not from a screen, and reuses what already renders.

**The design input, and getting it wrong makes the interface decoration.**
He can read plain language, compare a claim against an observed output, say no,
and smell a wrong direction. He cannot read code and judge it correct, cannot
tell whether a test tested anything, and cannot detect a confident plausible
wrong claim. So an interface that shows him a diff has already failed, and so
has one that reports "tests passed".

**The unit is the WORK ITEM, not the commit.** 2026-08-30 would have been four
documents, not twenty. Twenty is not review — he stops reading at the fourth,
and unread approvals are worse than none because they look like oversight.

**A Work Order, in two halves.**

*Before — authorise.* What is broken, in plain language. Evidence it is broken,
as real command output. What will change, described as behaviour not code.
**What will prove it worked — the exact check, named in advance.** What breaks
if it goes wrong, and whether it is reversible. What else touches it.

*After — accept.* The predicted check, run, **with its actual output pasted in**,
not summarised. Before and after as numbers he can read without reading code
(*80 foreign-key violations -> 0*; *48 secret values -> 0*). What was NOT done
and why. What deviated from plan, including errors found and corrected on the
way — 2026-08-30 had three, and they belong in the record, not in conversation.
How to undo it: the backup path, the revert command.

Both halves hashed like the gate briefing already is, so the record shows the
document he actually read.

**The load-bearing part is naming the check before the outcome is known.** It is
the difference between *"I verified it"* and *"here is the thing I said
beforehand would prove this, and here is what it printed."* The operator rules
already require this; nothing records it, so nothing holds the work to it.

**Four classes, by consequence, so this does not collapse under its own weight:**
- **0, reading** — searches, greps, tests, read-only checks. No approval, logged.
  Most of any session.
- **1, reversible and contained** — a new tool, a new document. Approval after.
- **2, enforcement / schema / live path** — guardrails, gate scripts, spine
  schema, `pipeline_relay.py`, ingest tools. Approval before AND after.
  Everything on 2026-08-30 was Class 2.
- **3, irreversible** — deletion, dropping a collection, anything with no backup.
  Approval before, irreversibility stated in its own sentence, acknowledged
  separately.

The declared class is itself checkable: a change touching `enforcement/` that
declares Class 1 is a lie a script can catch.

**What stops a false Work Order — the honest limit.** Nothing above does. Three
things reduce it and only the third is enforcement: every proof line is a
command someone else can re-run; the check is named before the outcome is known;
and **a verifier that is not the author** checks the Work Order against the real
diff — does the diff do what the order says, does the named check test the
claim, was anything changed the order does not mention. Without that third one
this is better-organised trust. It is the same evaluator-must-not-be-the-builder
rule HASE states and 4.10 records.

**Does not solve:** a wrong claim whose check honestly measures the wrong thing;
whether the work was worth doing at all (correctly still Eric's); volume — if it
starts producing fifteen Work Orders a day the unit is drawn too small.

**Build order, smallest first, each step useful alone.**
1. Work Order as a file, rendered by the **existing** briefing renderer. No new
   UI — that renderer demonstrably works and produced a readable, stably hashed
   briefing on 2026-08-30. Reuse beats building.
2. Record it in the spine as a row with a hash and a decision, so it is not a
   loose file. Approval reuses `record_decision.py`, which now works.
3. Enforce the class rule in the pre-commit hook — a Class 2 path requires an
   approved Work Order. **Ships with a tested off switch**, as the record
   requires of every guardrail; a gate that can brick the repo is worse than the
   gap it closes.
4. Add the independent verifier. Depends on 1.1.
5. A served view **only if** reading files becomes the bottleneck. Not before.
   The portal failed because it was an interface looking for a workflow.

Steps 1 and 2 are days and reuse working code. Step 4 is the valuable one.

**Eric's open decisions — none block step 1:** does a rejected Work Order block
the commit or only record the objection; is Class 1 approval required or is
notification enough; do Work Orders live in the repo (versioned with the change)
or the spine (queryable).

### 1.11 An API refusal is reported as the model misbehaving
**Found 2026-08-30 by `run-4bbeea78056e2607-1788121167`, the first code-writing
run.** It escalated with:

> *"Review incomplete: Review1 (ambiguous output (no FINAL_JSON, no text-scan
> signal)), Review2 (ambiguous output ...) — ESCALATE"*

That diagnosis is wrong. Both reviewers returned exactly 152 characters:

> *"HTTP 402: This request would exceed your available credits given your current
> in-flight requests. Retry after in-flight requests settle, or add credits."*

**The OpenRouter account was out of credits.** Consistent with the provider
split — brain (DeepSeek) succeeded on the same run; review1 and review2
(OpenRouter) both failed.

**The mechanism:** the Hermes gateway returned **HTTP 200** with the billing
error as the assistant's message content. `_call_agent` calls
`raise_for_status()` and so never saw an error status; from the relay's side an
agent successfully returned a short message. The relay then tried to parse a
review out of it, found no FINAL_JSON, **retried twice**, and escalated blaming
the model.

**Three distinct defects, and the third is the expensive one:**
1. An infrastructure refusal is stored in `agent_trajectories.output_text` as if
   it were model output. The trajectory record is now false.
2. It is retried. A 402 is not transient; retrying cannot succeed and each
   attempt is another request.
3. **The operator is told the wrong thing.** Eric reads "ambiguous output, no
   FINAL_JSON" and reasonably concludes the model or the parser is broken. The
   actual fix is "top up the account". Nothing anywhere on the run says so.
   Failure mode 11 — and worse than silence, because it points at the wrong
   component.

**Not fixable by string-matching "HTTP 402".** The real repair is that the
gateway must not launder an upstream error into a 200 completion. Until then the
relay can at least classify a short output that parses as an API error as
INFRASTRUCTURE_FAILURE, refuse to retry it, and escalate with the actual reason.

**Blocks further pipeline runs** until credits are added — every run that needs
a reviewer or the verifier will fail this way.
*Related:* 1.3 (no failure routing), 1.4 (retry policy retries the
non-retryable), 2.10 (silent-by-design).

### 1.12 The gate briefing omits the reviewers entirely
**Eric, 2026-08-30, while a run was in flight:** *"Will the reviewers deliver an
explanation of what I am approving?"* Checked: **no.**

**Measured on `run-e70293544935a92e-1787973534`, the run he approved that day:**
the two reviewers produced **14,608 characters** of analysis before the gate —
review1 3,037 and review2 4,650 at intent_review, review1 3,693 and review2
3,228 at proposal_review. **None of it reaches the briefing.**

`build_briefing.py` reads three sources: the drafter's own output (the Action
Summary), `objections_json`, and `decision_trails`. On that run
`objections_json` was empty for **every** pre-gate round and `decision_trails`
had **zero rows** — the trail is written by the approval handler, i.e. after the
decision — so section 3 fell back to *"Consensus reached after 4 rounds — no
objections were recorded against the proposal."*

**So what Eric approves is the drafter's account of its own proposal, plus a
round count.** The independent check ran, produced 14,608 characters, and was
invisible to the person the check exists to inform. The only round that recorded
objections (782 chars) was `code_review` — *after* the gate. The sharpest output
the system produced that day, Reviewer B catching that the spec's own success
criteria would have certified a falsehood (see 1.1), could not have appeared in
the briefing even in principle.

**This is the gate's core purpose failing quietly.** Failure mode 3 is the
rubber-stamp review; a briefing that carries only the proposer's summary
manufactures exactly that, with the operator as the stamp.

**The fix is small.** The reviewer outputs are already in `agent_trajectories`,
keyed by run and phase. The briefing needs a section that renders them — what
each reviewer examined, what it accepted, what it doubted — before section 3's
resolution line. No new capture, no schema change; the data is sitting there.

**Also worth fixing while in there:** `objections_json` is empty on rounds that
reached consensus, so agreement is indistinguishable from silence. A reviewer
that agreed *and said why* should not render identically to one that said
nothing. *Related:* 1.8, 2.9, and 1.1's record of what the reviewers caught.

### 1.13 A timed-out agent reports no cause, and no warning precedes it
**Found 2026-08-30 by `run-4bbeea78056e2607-1788122307`**, which died as:

> *"DRAFT failed: Gateway draft (port 8645) failed after retry: "*

Nothing after the colon. **`str()` on an httpx timeout is the empty string** —
verified for `ReadTimeout`, `ConnectTimeout` and `ConnectError`. The relay
formats `f"...failed after retry: {e}"`, so the operator is told neither the
cause nor even which *kind* of failure it was. A connect timeout, a read timeout
and a refused connection are indistinguishable in the record. The gateway was
healthy on the next check, so the message also implies the wrong culprit.

**No warning precedes it.** The heartbeat reported `note='working'` at
`elapsed=600s`, with `idle=278s` against a `STALL_SECONDS` of 300 — 22 seconds
short of saying anything. There is no countdown against the timeout itself, so
"working normally" and "about to be killed" render identically. Compare 1.7:
liveness is inferred from gateway log activity, not from the call.

**And the budget looks wrong for the work.** `AGENT_TIMEOUTS` gives verify 1500s
and menter 1200s — both raised after they timed out doing real work, with a
comment recording why — while draft is still at 300s. This was the first task
asking draft to reason about modifying existing code under six constraints and
four non-goals. It exceeded 300s twice.

**Three separate fixes:**
1. Format exceptions as `{type(e).__name__}: {e}` and include the timeout that
   was hit. An empty message is worse than none — it reads like truncation.
2. Warn as a deadline approaches, not only when a log goes quiet. The heartbeat
   knows `elapsed`; it does not know the limit.
3. Decide draft's budget deliberately. Either raise it with a comment recording
   the evidence, as verify's was, or treat >300s as a signal the task is too
   large and should be split — but decide, rather than leaving it at a default
   that was never chosen for this.

*Related:* 1.11 (a failure reported as the wrong thing), 1.7, 1.4.

### 1.3 Failure routing — NOT IN CODE
**Checked:** `human_review_required`, `retry_pending`, `failed_timeout`,
`contradiction_detected` appear **0 times** in `pipeline_relay.py` and
`runtime/api/relay.py`.
Today a BLOCK-mode guardrail kills the run and an ADVISORY one is ignored.
There is no third outcome, no escalation ladder, no defined next action per
failure state.
*Reference when building:* Execution Layer Contract §21.

### 1.4 Retry and escalation for agent failures — NOT IN CODE
**Checked:** the only retry in the relay is `_db_retry` (database contention,
3 attempts) and `MAX_BRAIN_ROUNDS=2` / `MAX_DRAFT_ROUNDS=3`, which are
deliberation round caps. There is one repair prompt for malformed output.
**No retry on agent failure, no timeout policy, no escalation after N attempts.**
*Reference:* Execution Layer Contract §19-20.

### 1.5 Commit route — approved work does not become canonical
**Checked:** `pipeline_relay.py` is the only thing in `runtime/` that writes to
`knowledge_messages`. Nothing promotes an approved run's *output artefact* into
the knowledge layer as a canonical record.
A run is approved, the implementer writes a file, and the file is just a file.

### 1.6 Prompt size is never measured — NOT IN CODE
**Checked:** `agent_trajectories.tokens_in > 0` on **0 of 479** rows.
Across 469 calls the prompts averaged 12k chars, 62 exceeded 20k, max 63,802 —
and the three largest went to VERIFICATION, the phase whose job is checking
claims. Over-length input fails silently.

### 1.7 Stream agent completions
**In code:** nothing. Liveness is inferred from a gateway log that menter never
writes during a call (elapsed 180s / idle 180s). Gateways support streaming;
token cost is zero.

---

### 1.8 The pipeline asks Eric questions he cannot answer — NOT IN CODE
**Eric, 2026-08-30, stating the requirement:**

> *"The container agents must always recognize that I am not a coder and I don't
> have the experience to answer most of these technical questions. It must
> provide context and options to choose from along with the positive and
> negative consequences of the choices made based on evidence and good coding
> practices. The container cannot keep posing these scenarios — it's creating
> situations where I have to guess."*

**Why this is Tier 1, not a nicety:** the Eric Gate is on the critical path of
every run, and no run has ever passed it. A gate that presents a question the
operator cannot evaluate does not produce a decision — it produces a guess, or a
stall. Both are indistinguishable from the pipeline working. This is failure
mode 3 (rubber-stamp review) with the human on the receiving end: approval given
without the ability to evaluate is exactly the rubber stamp the gate exists to
prevent.

**The rule, stated so it can be checked:** any output that asks Eric to decide
must carry, for each option, (a) what it means in plain language, (b) the
evidence behind it, (c) what goes right if chosen, (d) what goes wrong. An open
technical question with no options is a defect, not a request.

**Where it lands:** the Eric Gate briefing first — that is the one surface where
a decision is mandatory and cannot be automated (see Decisions to Protect). Then
the role overlays, which currently say nothing about who the reader is.

**Checkable, in the same shape as the other gates:** a briefing whose decision
section contains a question mark but no enumerated options with consequences
fails. This is not a prompt instruction — a longer overlay is still a trait, and
traits do not hold. It has to be a gate on the output.

Applies to these working sessions too, where the same failure produced this
item — see 4.6.

**Named variants. Each one was produced in the session that recorded it, so
treat these as observed, not hypothetical:**

**(a) The bare question.** A technical question with no options attached. The
original form, 2026-08-30.

**(b) The dangling veto.** Options and costs ARE laid out, a choice IS made —
and then the output ends with *"say the word if you'd rather have the strict
version."* An invitation to reverse the decision with **no criterion for when
you would want to**. Eric, 2026-08-30: *"you asked if I want a strict version
without telling me the cost/benefit of either method."* The comparison existed
two paragraphs earlier and did not land, which is the lesson: **evidence
separated from the decision point is not evidence the reader has.** A reversal
offer must restate, at the point of asking, what choosing it costs and what
would make it the right call — or it must not be offered at all.

**(c) The buried recommendation.** The reasoning is present but the reader has
to assemble the verdict from it. State the verdict first, then the reasoning.

**(d) The false menu.** Options presented as a live choice when one is already
ruled out by the presenter's own analysis. Observed 2026-08-30: three options
offered for the secret filter, with *"I would not take this one"* written beside
the second and a recommendation attached to the third. Eric: *"it seems to me
there is no choice and I don't know why you are asking — this is another
dangling option to choose an option that exposes me to a weakened system, blind
agents and opportunity to miss something anyway."*

Two costs, and the second is the serious one. It spends the reader's attention
on evaluating something already decided. And it puts a **known-worse option in
front of someone who cannot independently rank them** — if he picks it, he has
been walked into a weaker system by the party who knew better. An option the
analysis has already eliminated is not a choice; it is background, and belongs
in the reasoning at most.

**The rule:** if the evidence settles it, decide and say why. Only surface a
choice where two options are genuinely live after the analysis — different
trade-offs a reasonable person could weigh differently, not one good answer
padded with alternatives. Eliminated options are stated as eliminated, never
offered.

**(e) Outsourcing the check.** Asking Eric to confirm something determinable
from the disk. Observed 2026-08-30, immediately after (a) through (d) were
recorded: *"the one thing worth your confirmation — whether drive_imports is SWA
material."* It was answerable in two commands, and was answered in two commands
once he pushed back. Dressing it as a courtesy does not change what it is.

**THE PATTERN UNDER ALL FIVE, and this is the one that matters.** Eric,
2026-08-30: *"you are working on me correcting. spell check."*

Every variant above shares one shape: **the output is emitted unchecked, and
Eric is the check.** That is not a communication defect, it is the system's
original failure reappearing at the top of the stack — the record already names
it, *"the system appeared to function, but only because the operator was
silently bridging the gaps."* The pipeline exists to stop him being the
integration layer. An assistant that ships an unverified question and waits for
him to catch it has rebuilt exactly that dependency, one level up, and burns his
day doing it.

The name he gave it is the right one. **A spell checker runs before the text is
sent, not after the reader finds the typo.** The check belongs inside the
producing step.

**(f) Too much of it.** Eric, 2026-08-30: *"I like the one sentence response,
the other format is overwhelming and I can't comprehend it because it's too
much. Limit the verbiage. Explain things directly to the point with relevant
information, options and consequences."*

Length is not thoroughness. An answer he cannot get through is the same as no
answer, and it fails the same way (a) does — he is left guessing, this time
because the answer was buried rather than absent. Volume also flattens
emphasis: when everything is stated at equal weight, nothing is.

**The rule:** one sentence answering the question, first. Then only what changes
the decision. Options as a table — one row each, what it gets him, what it
costs — never as paragraphs. Everything else goes below, or nowhere.

**Checkable form:** before any output that asks Eric something, the question
must survive four tests — (1) is it answerable from the code, the disk or the
record? then answer it instead; (2) is it settled by analysis already done? then
state the decision, not the menu; (3) do the options and their consequences sit
adjacent to the question, with a criterion for choosing? An earlier table does
not count; (4) does it fit the word budget, with the answer before the evidence
and options as rows rather than prose? Only a question passing all four reaches
him.

Test (4) is the deterministic part he asked for and needs no judgement: word
count, sentence count, answer-before-evidence ordering, and options-as-rows are
all countable by a script. That is what makes it a gate rather than a style
note.

This is the gate 1.8 has to become, and it applies to assistants in these
sessions before it ever applies to a container agent — the failures logged here
are all from the session that wrote the item.


## From the 2026-08/09 mining pass — added 2026-09-01

Evidence for every item below is in `data/mining_archive/MINED_TASKS.md`. Scope says whether the finding was verified against the container in production or against code the container does not execute; the latter is not the same as irrelevant.

### 1.14 Give the pipeline a stop button and validate its input

The relay blueprint exposes eight routes and none cancels a run; grep for 'cancel' returns 0. pipeline_relay.py accepts the intent string with no validation, so a malformed intent enters the pipeline and is caught only downstream.

**Scope:** CONTAINER — runtime/api/relay.py is the blueprint container_app.py registers at line 27; no _validate_intent in runtime/abstraction/pipeline_relay.py

**Need:** OPEN — verified absent: the relay blueprint exposes eight routes and grep -c cancel returns 0; there is no _validate_intent in pipeline_relay.py. Both halves stand.


**Evidence:** raised 2 times, 2026-07-08 to 2026-07-08; mining_candidates 15439,15418; full record in `data/mining_archive/MINED_TASKS.md`.

### 1.15 Remove Eric from the relay roles he still fills by hand

Human router, human triage clerk, human reviewer selector and human schema reconciler. The reviewer-implementer challenge loop halts on him; the Implementer-to-Verifier loop has no owner; the manual instruction template has no automation; escalation needs a snapshot-and-switch with an acknowledgement signal rather than a prompt-optimisation step.

**Scope:** NOT_IN_CONTAINER_PATH — the four relay roles and the escalation path are the VM-era manual workflow

**Need:** OPEN — he is still the relay — this very session ran as him passing directives between steps. The container has not removed the four roles; it changed where the work executes, not who routes it.

**Evidence:** raised 5 times, 2026-06-27 to 2026-08-29; mining_candidates 14561,541,1169,127,3552; full record in `data/mining_archive/MINED_TASKS.md`.

### 1.16 Close the gate bypass and generalise enforcement

The write-block was proven on one file and never generalised to the 16 failure modes. The pre_tool_call hook bypass describes the VM only.

**Scope:** NOT_IN_CONTAINER_PATH — no pre_tool_call configured in any /home/worker/.hermes-*/config.yaml; the container constrains agents by image and mount

**Need:** UNASSESSED — CORRECTION: the container does fire a pre_tool_call hook — plugin mwl-proof is enabled at config.yaml:52-55, registers the hook at plugin/__init__.py:55, and hook_seen.log shows FIRED entries through 2026-08-31. My earlier check grepped config.yaml for the hook name and missed it. Whether that hook closes the write-outside-the-project bypass is not established.

**The one check that settles it:** test whether the mwl-proof pre_tool_call hook blocks a write outside /workspace/cis

**Evidence:** raised 2 times, 2026-06-27 to 2026-08-29; mining_candidates 13418,14719; full record in `data/mining_archive/MINED_TASKS.md`.

### 1.17 Restore the dev-mode agent configs before any pipeline run

Review2 (glm-reviewer, port 8647) was stripped on 2026-09-02 so Claude Code could borrow it as a text advisor: 79 skills disabled through `skills.platform_disabled.api_server`, toolsets cut to `file` and `cis-knowledge` through `platform_toolsets.api_server`. Prompt cost went 15,853 → 4,502 tokens. The strip also removed `cis-soul` and `cis-pipeline-architecture`, the two CIS-specific skills a pipeline reviewer needs.

**Scope:** CONTAINER — /home/worker/.hermes-review2/config.yaml, two appended blocks both marked `# DEV MODE 2026-09-02`. Backups `config.yaml.bak.20260902-devmode` (pre-skills) and `config.yaml.bak.20260902-devmode-2` (pre-toolsets), both md5-verified and separately reversible. The other five agent configs were not touched.

**Need: DONE 2026-09-04 — closed by the rebuild, not by anyone remembering.** `entrypoint.sh:56` copies `/etc/hermes/profiles/<name>.yaml` over each profile's `config.yaml` unconditionally on every container start, and `run_container.sh` recreates rather than restarts. So the dev-mode strip — which lived only in the volume — was overwritten the moment the container came up. review2's config is now byte-for-byte the repo profile. `tools/check_dev_mode.sh` reports **PASS — all 8 agents clean**, checking eight configs rather than six because it globs the profile directories.

That is the item resolving itself by accident, and the accident is worth naming: a state that only exists inside a volume is not durable, and nobody would have known it reverted. The durable version is what 3.22 then did — the strip belongs in the repo profile, where it survives recreate, and review2 now carries a measured 7-tool loadout rather than either the 35-tool default or the borrowed advisor's zero.

**The follow-on this creates:** `tools/advisor_review.sh` still defaults to `review2` on 8647. That is no longer a stripped text advisor; it is a pipeline reviewer. The real advisor is on 8649 at 390 tokens. Repointing it is two lines and its header comment about depending on the dev-mode strip needs rewriting with them.

**The rule this needs:** a comment is not a check. Both blocks say MUST BE RESTORED and nothing enforces it. A startup check should refuse to run the pipeline while any agent config still carries a dev-mode marker. Rules become checks or they do not exist.

**The one check that settles it:** grep the six container configs for `DEV MODE` and confirm the pipeline refuses to start while any hit remains.

**The check exists and is NOT wired — 2026-09-02.** `tools/check_dev_mode.sh` reads all six container configs, reports what each stripped agent is missing (read from the parsed YAML, not from the comment — the comment is the thing being distrusted), and exits 1 when any is in dev mode, 0 when all are clean, 2 when it cannot check. An unverifiable state deliberately does not read as a pass. Tested this session: it names review2 with "79 skills disabled on api_server; ALL toolsets removed on api_server; MCP server 'cis-knowledge' disabled" and exits 1.

Half the item is therefore done: the rule is now expressible as a command. The other half — something actually calling it — is not, so today the check is a thing a person must remember to run, which is the same failure as a comment that says MUST BE RESTORED. **Wiring it is the remaining work.** `runtime/abstraction/pipeline_relay.py` is on the do-not-modify list, so the call site is a decision, not a detail; the options and their costs are in the session record for 2026-09-02.

**Closeout reports it as of 2026-09-02.** `tools/closeout.sh` calls the check at step 1b and prints what it finds, and the final summary carries a `Dev-mode agents:` line. It REPORTS, it does not block — a stripped agent is a fine state to end a session in, and refusing to close a session over one would only teach people to skip closeout. What it buys is that the state is never silently carried into tomorrow.

**This is not the check the item asks for.** Closeout runs after the work; it can only describe the state, never prevent a run from starting in it. The real guard belongs at run entry, and it is still open. The obstacle is not the writing but the placement: the relay has several paths into a run, and a guard on one of them is a check with a hole — worse than none, because it reads as covered. Finding the single chokepoint means reading `pipeline_relay.py` closely, which is reading, not modifying, so the do-not-modify constraint does not block it.

---

## The review loop — six items, added 2026-09-02

1.18 through 1.22 and 2.25 are one design. They are listed separately because
they are built separately, but none of them is worth building alone: a card
review with no exchange is a second opinion nobody can answer (1.18 needs 1.19);
an exchange with no technical evaluator only ever critiques packets (1.19 needs
1.20); a loop that never waits turns all of it into a transcript Eric reads
afterwards (1.21); a feed with no waiting loop is a notification stream (2.25
needs 1.21); and every one of them produces knowledge that currently reaches
nothing (1.22 blocks all five).

**Why these sit in Tier 1 and not behind the container work.** Eric, 2026-09-02:
working with LLMs produces confident wrong output structurally — "this madness
working with llms is a feature that can't be escaped" — so an external
perspective is permanent, not scaffolding removed once the container works. The
pipeline's own reviewers will need one too. The loop and the container address
the same defect in two places: a single model working alone cannot check itself.
Treating the loop as a detour on the way to the container misreads what the
container is for.

The standing constraint that follows: Eric does not fall back into transport
mode. A design that requires him to carry text between models is a regression
regardless of what it buys.

### 1.18 Cards are written and executed by the same party

A wrong card produces a result that satisfies a wrong EXPECT, and a review that checks the result against that EXPECT passes it. The whole check rests on the card, and nothing checks the card. This is evaluator-must-not-be-the-builder one level above where 4.10 guards it: 4.10 separates the agent that judges the work from the agent that did it, and leaves whoever wrote the instruction unexamined.

Fix: the packet goes to the advisor twice. Once with the card before it runs — "what would this fail to establish, and what result would satisfy it while being wrong" — and once with the result, as today. A card review is a few hundred tokens against the 2,083 a result review cost on 2026-09-02, so the cost objection does not hold.

**Scope:** CONTAINER — `tools/advisor_review.sh` sends one packet after the fact. A pre-flight mode is a second packet shape, not a second script.

**Need:** OPEN — every card this session was written and executed by the same party, and the review that followed checked the result against the card's own EXPECT.

**The one check that settles it:** take a card whose EXPECT was met and ask the advisor what that EXPECT would fail to establish. If it names something the result review missed, the gap is real.

**Related:** 4.10 (harness self-improvement loop) guards the level below this. Needs 1.19 — a card objection nobody can answer is a second opinion, not a check.

### 1.19 One-shot critique loses what multi-round exchange catches

`advisor_review.sh` gives the reviewer one look and no reply. Eric, 2026-09-02: "them not looking at each other's responses is not how you were catching additional issues through me transporting."

Evidence from this week, all of it from exchanges rather than verdicts: the three-enforcement-layer confusion took two rounds to resolve, VM-versus-container took three, and the `wc -l` off-by-one surfaced only because a number was questioned and the raw output came back. A single verdict would have carried all three errors forward.

Fix: Claude Code may answer an objection with evidence; the reviewer withdraws it or holds it. Capped at two rounds, written to `reviews/` as a thread rather than a file per verdict. No vote and no arbiter — the exchange is the product, not a score derived from it. This is why `deliberation_rounds` exists in the spine rather than a single verdict field.

**Scope:** CONTAINER — `tools/advisor_review.sh` writes one response file per packet and exits. A thread needs the packet, the objection, the answer and the withdrawal in one artifact.

**Need:** OPEN — verified in the code this session: the script posts once, writes `reviews/done/<id>.response.md`, and has no reply path.

**The one check that settles it:** re-run a review where the advisor made a factually wrong objection, answer it with evidence, and see whether the withdrawal changes the finding set. On 2026-09-02 the advisor claimed three existing backups did not exist; one round with the `ls` output would have retracted it.

**Related:** 2.7's absence-from-outside-scope variant is the failure a reply round closes. Needs 1.20 to be worth running twice.

### 1.20 Add Qwen (8643) as technical evaluator

Eric, 2026-09-02: he cannot evaluate code or technical choices. That is the gap GLM's objections do not close — GLM critiques the result packet, not the engineering. Every technical decision this session was made and checked by the same model family.

Three roles, three lineages: Claude Code builds, GLM (review2, 8647) objects to the result, Qwen (review1, 8643) evaluates the code and the method. Qwen leads on agentic coding benchmarks and is furthest from Claude's lineage, which is the point — 1.19 buys nothing if both reviewers share a blind spot (failure mode 16).

Qwen needs the same advisor treatment review2 got: skills disabled, toolsets trimmed, the scope line, and `mcp_servers.cis-knowledge.enabled: false` so it carries no `cis_dispatch_*` tools. Measured, not assumed — review1's loadout has never been audited, and `platform_toolsets` is unset in all six configs.

**Scope:** CONTAINER — `/home/worker/.hermes-review1/config.yaml`, port 8643, model `qwen/qwen3.7-max`, verified reachable 2026-09-02. `advisor_review.sh` already takes `CIS_ADVISOR_PROFILE` and `CIS_ADVISOR_PORT`, so no script change is needed to reach it.

**Need:** OPEN — review1 is untouched and still carries the full default loadout. A ping cost 16,568 prompt tokens on 2026-09-02, higher than review2's 15,853 before trimming.

**The one check that settles it:** trim review1 the same way and measure; then give both advisors the same packet and count the findings only one of them raised. If that number is zero, the second lineage is not paying for itself.

**Related:** 3.22 is the measurement this depends on. 2.23 is why the MCP server must be disabled rather than merely untooled.

### 1.21 The loop must stop and wait, not run past Eric

Eric, 2026-09-02: "having the loop waiting on my approval is a lot better for me than physically being locked to a screen watching, reading, understanding and copy pasting every exchange."

This is not a kill switch, and the distinction matters. On 2026-08-31 the drafter ignored nine minutes of interrupts because it was mid-call and working — nothing was broken, and a stop button would have solved nothing. The requirement is that the loop reaches a state where it is WAITING, so nothing is lost while he is away and a wrong direction stops early instead of after four cards.

PAUSE POINTS: between queue items, and before any card that writes. A read-only card does not need him; a card editing `runtime/abstraction/pipeline_relay.py` does. That is the consequence-class split already sketched in 1.10 — the same read/write line, applied to when the loop asks rather than to what a gate blocks.

**Scope:** UNDETERMINED — no loop runner exists yet. Whether the waiting state lives in a script, in the spine, or in the relay is not settled, and choosing wrong here is expensive.

**Need:** OPEN — today the loop is Eric issuing one card per turn, which is a pause point at every step and the very hand-carrying this is meant to remove. The failure mode being designed against is the opposite one: a loop that runs four cards past a wrong turn.

**The one check that settles it:** decide where the waiting state lives before building it — a script that blocks, or a queue row the loop polls. The second survives a restart; the first does not.

**Related:** 1.14 (stop button) is the different problem — that one interrupts work in flight, this one declines to start it. 2.25 depends on this: a feed with no waiting loop is a notification stream.

### 1.22 Nothing the loop produces reaches the KB — BLOCKS 1.18 through 1.21 and 2.25

As designed, the loop captures nothing. Verified 2026-09-02:

- `tools/catalog/ingest_sessions.py` scans `~/.hermes-*/sessions/session_*.json`. A direct API call to a gateway writes no session file, so the advisor exchanges are invisible to it.
- `reviews/` is files on disk reaching no index. The first two exist as of this session and are tracked in git and nowhere else.
- Telegram replies (2.25) reach nothing at all.
- `grep -c ingest tools/closeout.sh` returns **0**. Closeout commits code and never ingests knowledge.

ERIC'S INPUTS ARE THE POINT. Everything the 2026-08/09 mining recovered came from him reframing — VM-versus-container, the on-the-fly documents, rejecting the sampling. `docs/NEXT_SESSION.md` records why: the corpus is the counterweight to enterprise bias and the only one, because nobody else wrote this method down. A loop that produces those reframings and loses them rebuilds the same archaeology in three months, and the mining pass that recovered 4,479 candidates is the measure of what that costs.

Three things need capturing: the review threads in `reviews/`; Eric's redirects WITH what they redirected, since an objection separated from what it changed is his own stated failure; and Claude Code's sessions, which `tools/ingest_claude_code_sessions.py` handles and nothing triggers.

**Scope:** REPO — this is 4.1 restated with a deadline attached. Both ingest tools exist and work; neither fires. The closeout hook is where they would fire, and it is four lines in `tools/closeout.sh`.

**Need:** OPEN — verified this session: closeout contains no ingest call, and the session ingest tool cannot see gateway API calls because they produce no session file. The second half is not a wiring problem; it needs the loop to write its own record.

**The one check that settles it:** run a review round, then query the KB for what the reviewer objected to. If it is not there, the loop is lossy and none of the other five items should ship.

This is also what makes the external perspective cumulative. Without it every advisor session starts cold, and the reframings that produced this list are produced and lost. Eric, 2026-09-02.

**Related:** 4.1 is the same gap without the dependency. Blocks 1.18, 1.19, 1.20, 1.21 and 2.25 — the loop does not ship without this.

### 1.23 A code run has never completed end to end

1.1 proved the path is walkable on a documentation task — one file, no code written. On that run the three BLOCK-mode verification guardrails all SKIPPED: `claim_action_verifier` ("no file or function claims detected"), `intent_compliance` ("no Python code blocks to test"), `capability_claim_verifier` ("no capability claims detected"). Legitimate for that task, and the point stands — the three strongest checks are shaped for code and have never fired.

Two code-run attempts failed for unrelated reasons. `run-4bbeea78056e2607-1788121167`, the first code-writing attempt, escalated on an OpenRouter 402 reported as "ambiguous output" (1.11); the retry, `run-4bbeea78056e2607-1788122307`, timed out in draft with no cause recorded (1.13). Neither failure says anything about whether the code path works — both died before reaching it.

**Scope:** CONTAINER — the pipeline path is the same one 1.1 walked. What is untested is every check that only engages when there is code to check.

**Need:** OPEN — until a code run passes, nothing downstream is estimable and it is not known what else is broken. The guardrail evidence from 1.1 is evidence about a documentation task only.

**Also the review loop's first real test.** A code run produces a result neither Eric nor Claude Code can fully evaluate alone, which is the case 1.20 exists for. Run it through the loop, not beside it — the card reviewed before it executes (1.18), the result objected to and answered (1.19), the engineering evaluated by Qwen (1.20). A code run checked the old way would prove the pipeline walks and prove nothing about whether the check on it works.

**The one check that settles it:** a completed run whose guardrail summary shows the three named checks reporting PASS or FAIL rather than SKIP.

**Related:** 1.1 (the documentation run that established the path is walkable), 1.11 and 1.13 (the two failures that stopped the earlier attempts, both fixed or open on their own items), 2.1 (the guardrail audit this would give real code-path data to).

### 1.24 Brain is fed its own prior attempts, labelled successful, from runs that failed

Found 2026-09-04 by dumping the six payloads of `run-4bbeea78056e2607-1788140226`. The `## Prior Agent Trajectories` block inside `[PRE-DISCOVERY RESULTS]` hands brain three earlier trajectories — all of them `brain/brain` rows, all on the **same intent**, each tagged `success`:

```
--- Trajectory (run run-4bbeea78056e2607-1788129615, brain/brain, success) ---
--- Trajectory (run run-4bbeea78056e2607-1788122307, brain/brain, success) ---
--- Trajectory (run run-4bbeea78056e2607-1788121167, brain/brain, success) ---
```

**The label is true per row and misleading per run.** Those brain phases did succeed. The runs did not: `run-4bbeea78056e2607-1788122307` **failed at draft**, and `run-4bbeea78056e2607-1788121167` **failed at both intent reviews** — confirmed in `agent_trajectories.outcome`. The selection filters on phase outcome and never looks at what happened downstream, so a phase output that led nowhere is presented to the next attempt as a success to build on.

Brain therefore opens its turn reading three near-identical restatements of its own earlier answer to the identical question, and then produces a fourth. Nothing in the payload says these attempts went on to fail, or why.

**Why this is Tier 1 rather than a cost item.** It is failure mode 1 wearing the pipeline's own clothes — self-reported completion without evidence, recycled as input. The risk is not the 1,178 characters; it is that a wrong understanding which failed downstream is the most heavily weighted precedent the next brain sees, and the same intent has now been attempted four times.

**Scope:** CONTAINER — the trajectory selection in the pre-discovery builder in `runtime/abstraction/pipeline_relay.py`.

**Need:** OPEN — the payload for the run above contains all three, and the two failure outcomes are in the same table the selector reads.

**The one check that settles it:** for any run cited in a `Prior Agent Trajectories` block, confirm the run reached a terminal success state, not merely that the quoted phase row says `success`. A trajectory from a run that escalated or timed out should either be excluded or carry what became of it.

**Related:** 1.23 (the code run that has never completed — two of the three runs cited here are its failed attempts), 1.11 and 1.13 (why those two died: an API 402 reported as ambiguous output, and a draft timeout with no cause), 2.13 (runs are not linked to what they advance), and 2.3 / 3.23 for the rest of the payload composition.


# TIER 2 — blocks trusting what a run produces

### 2.1 Twenty-three guardrails observe and cannot act
**Checked in code:** 30 guardrail functions are called on every run. **7 are
BLOCK mode** — `capability_claim_verifier`, `claim_action_verifier`,
`evidence_hash_chain`, `intent_compliance`, `loop_detector`,
`output_schema_validator`, `path_contract_validator`. The other 23 report and
the run continues.
**Highest-value item on this list. The detection code already exists.** Audit
all 30 and decide per guardrail whether its default should enforce.

### 2.2 Four guardrails were never written
**Checked:** absent from `guardrails.py`.
- **Honesty Reporter** — PASS/SKIP/FAIL counters in every gate script. Failure
  mode 11, silent gate failures.
- **Model Diversity Enforcement** — config check that a model is not reviewing
  its own work. Failure mode 16, single-model blind spots. This is a config
  comparison, not research.
- Position Randomizer — positional bias in option ordering.
- Example Diversifier — anchoring on prompt examples.

### 2.3 `sequential_review` is dead code
**Checked:** defined in `guardrails.py`, never appended to any report. It is the
guardrail against shared blind spots between reviewers, and it never runs.

**Why it never runs — found 2026-09-04, and it is structural, not a wiring gap.**
`pipeline_relay.py:1175` builds every agent call as a single independent POST:

```python
"messages": [{"role": "user", "content": prompt}],
```

One user message. No history, no accumulation, no other agent's output. Both
reviewers receive the same constructed prompt and neither can see what the other
said, so sequential review has nothing to be sequential *about*. Confirmed on a
real run: review1 and review2 got byte-identical inputs in both the
`intent_review` and `proposal_review` phases — 22,128 and 27,074 characters,
matching exactly.

**This is the same defect as the token cost, seen from the other side.** Because
each call is independent, the agent's entire system prompt is rebuilt and
re-billed every turn — 98,586 of a deliberation's 131,383 tokens before the 3.22
trim. Giving reviewers a conversation would fix the blind-spot guardrail *and*
stop paying for the system prompt six times. **They are one piece of work, not
two**, and either one alone is the more expensive way to do it.

**Related:** 3.22 (the cost side, now measured and trimmed at the floor but not
at the turn count), 1.6 (prompt size never measured), 4.10 (evaluator must not
be the builder — cross-feeding reviewers is what makes deliberation genuine
rather than two parallel opinions), and failure mode 15, cross-model agreement
without genuine deliberation, which this arrangement guarantees.

**The prompt asks review2 for something the payload makes impossible — 2026-09-04.**
Review2's `[BIAS_OVERLAY]`, and its profile personality, both instruct it:

> Bias to admit: toward consensus. Correct by finding what Review1 missed.

Review1's output is not in review2's payload. The two calls are **byte-identical**
— 22,128 characters each in `intent_review`, 27,074 each in `proposal_review`,
confirmed on `run-4bbeea78056e2607-1788140226`. Review2 cannot find what Review1
missed because it has never seen what Review1 said.

This is worse than a dead guardrail. `sequential_review` failing to run is a
check that is absent; an overlay demanding an impossible comparison is an
instruction the model will comply with **by inventing** the thing it cannot
observe — producing a confident account of Review1's blind spots derived from
nothing. The bias correction the role depends on is not merely missing, it is
counterfeited.

Either the payload gains Review1's output, or the overlay stops asking for it.
Leaving both as they are is the arrangement most likely to produce agreement
that looks deliberated.

### 2.4 No validation layer — 23 independent recognitions in the record
**Checked:** `needs_review` — the quarantine flag — exists in **no table and no
code**. No validation of `project_id` existence, `source_type` against known
values, `source_path` before processing, state-transition legality, or
cross-field consistency. Constraints are declared (224 NOT NULL, 45 CHECK,
7 UNIQUE, 4 FK) and largely unenforced — see 0.1.
> *"No validation layer exists for any component — all bug detection is manual."*

### 2.5 No schema versioning or migration — NOT IN CODE
**Checked:** `schema_versions`, `schema_migrations`, `migration_log` — **all
three tables absent**. This already caused damage: the `workflow_runs_old`
references in 0.1 are a rename that left dependent rows orphaned.

### 2.6 Tool calls are not captured
**Checked:** `agent_trajectories` records prompt and output only. No
`tool_calls` table. Nothing records which files an agent read.
**Blocks 2.7 and any evidence-based gate.**

### 2.7 Never-guess gate — an agent may not assert what it did not open
Needs 2.6. `capability_claim_verifier` already exists in BLOCK mode and can be
extended rather than replaced.
*Reference:* the record already designed a `CapabilityClaim` object with
validation status, provenance and correction history.

**Variant: asserting absence from outside scope.** Observed 2026-09-02 on the
first real advisor call. Review2 was asked to review a config change under
/home/worker; its file tools are scoped to /workspace/cis. It ran ~14
search_files calls that each returned empty, then reported "The backup file does
not exist" and "the other five configs are unverifiable" under a heading reading
WHAT I OBJECT TO. All three backups existed. It converted "I cannot see it" into
"it does not exist."
This is distinct from the base rule. 2.7 asks whether an agent read the file it
describes. This asks whether the path was ever in the agent's scope. A reviewer
whose access is narrower than what it reviews will confidently report absence,
and nothing currently makes it say out-of-scope instead.
Checkable form: an agent asserting that something does not exist must show the
path was within its declared scope. An empty search outside scope is not
evidence of absence. Failure mode 2 — hallucinated claims as fact — reproduced
in the reviewer role on its first call.

### 2.8 Verification results change nothing
**Checked:** `gate_outcomes` (4,375 rows) IS read — but only to *display*:
a FAIL list for one run, and a recent-200 listing. Nothing aggregates across
runs, nothing feeds back into behaviour, nothing detects a guardrail that
never fires or always fires.
Six loops are named in the record — correction, governance,
retrieval-improvement, archive-learning, continuity/memory, project-output.
None exist.

### 2.9 Conflict register records but never blocks
**Checked:** `active_blockers` has 7 rows; six files read it — the briefing
builder, the export generator, the session-init scripts. **None blocks on it.**
The original rule was *"session close is blocked if unresolved conflicts exist."*

### 2.10 Silent-by-design code patterns — now measured
**Checked across `runtime/` (excluding venv and rails):**
- **445** broad `except` blocks
- **62** of them are `except Exception: pass` — the exact pattern that hid
  `(KB search unavailable)` for 99 agent calls

That is the scope of the audit. Mechanical fix, bounded, and every one is a
place where the system can fail without saying so.

### 2.11 No contract between a CIS task and an agent task
**In code:** `pipeline_relay.py` builds a prompt per role with no contract
governing size, required sections, or what the role is expected to produce.
This is why 1.6 (unmeasured prompts) and 3.9 (draft scored as code) both exist.

### 2.12 Primer and runtime diverge silently
**Two live instances in code/data today:** `gateway_status_qwen` claims Qwen is
2nd reviewer on 8644 — the container uses review1/8643 and review2/8647.
`CLAUDE.md` names `runtime/spine.db` as the spine; that file is 0 bytes.
Nothing detects the divergence. Fix the class, not the two cases.

### 2.13 Runs are not linked to what they advance
**Checked:** `build_plan_nodes.workflow_run_id` is NULL on all 30 rows. The
Eric Gate briefing's Dependency Node and Tier Advanced fields render blank.
**Eric's call:** does a run name its DEV-PIVOT at intake, or are repairs marked
maintenance? Do not let brain infer it.

### 2.15 Thirty-three of fifty-one gate scripts have never fired
**Checked:** 51 gate scripts exist in `enforcement/mwl-proof-v2/gates/`.
`gate_outcomes` has recorded 47 distinct names ever. Cross-referencing, **33
scripts on disk have never executed once.** Not disabled — never called.

The consequential ones, with what they were written to do:

| gate | purpose | maps to |
|---|---|---|
| `gate_ui_no_pipeline_bypass` | scans for pipeline module imports that bypass the relay | **2.14, failure mode 9** |
| `gate_pre_execution_oversight` | *"fires automatically before any execution directive reaches Eric"* | 1.3 |
| `gate_final_directive_allowed` | blocks FINAL_DIRECTIVE unless Eric approval exists | Eric Gate integrity |
| `gate_no_docs_only_diff` | *"FAIL any build run whose output is only documents"* | 1.1 — proves a run did real work |
| `gate_implementation_artifact_present` | implementer actually produced something | 1.1 |
| `gate_git_state` | git state verification | evidence |
| `gate_deliberation` | deliberation validity | 2.1 |
| `gate_drafter_closeout`, `gate_reviewer_closeout`, `gate_closeout_artifact`, `gate_closeout_complete` | closeout enforcement | 2.9 |
| `gate_chroma_no_secrets_in_results`, `gate_chroma_secret_filter` | **secrets in KB results** | **0.2** |
| `gate_export_agreement` | artifact count agreement | 3.5 |
| 13 × `gate_11a_*` / `gate_11b_*` | UI and approval-schema gates | Tier 10/11 UI work |

**Note from git history:** commit `c4ce0d8` — *"Delete 4 irrelevant gates + fix 2
broken guardrails"* — so gates have been pruned before. Before wiring any of
these, confirm it is still relevant rather than assuming.

**This is the same shape as 2.1 but worse:** 2.1 is code that runs and cannot
act; this is code that never runs at all.

### 2.16 `runtime/tier7r/` is an orphaned subsystem
**Checked:** eight modules — `process_manager.py`, `approval_gate.py`,
`classifier.py`, `dead_letter.py`, `scope_registry.py`, `work_intent.py`,
`domain_adapter.py`, plus `adapters/cis_adapter.py` and `adapters/swa_adapter.py`.
**Nothing in `runtime/abstraction/` or `runtime/api/` imports any of it.**

This is the Tier 7R Intent-to-Workflow architecture — the thing
`build_plan_nodes` marks COMPLETE across nodes 7R.1 through 7R.7. It was built
and never connected. Decide: wire it, or record it as superseded by
`pipeline_relay.py` and stop counting it as complete.

### 2.17 Every gate approval ever recorded has a NULL primary key
**Checked 2026-08-30, on the live spine:** `eric_gate_approvals` holds 26 rows.
**`id IS NULL` on all 26.** Not some — all of them.

**Cause, in code:** the relay's insert at `runtime/api/relay.py:663` omits the
`id` column entirely. The CLI path at `tools/eric_gate/record_decision.py:407`
does supply it. The relay is the path the container uses, so every approval on
record came in without an id. SQLite does not catch this: a `TEXT PRIMARY KEY`
is not implicitly NOT NULL — only `INTEGER PRIMARY KEY`, the rowid alias, is.

**What it breaks:** `supersedes_approval_id` is the field recording *this
approval replaces that earlier one*, and it references `eric_gate_approvals(id)`.
`record_decision.py:397-403` builds that link by selecting the prior row's `id` —
which returns NULL, so the link is silently stored as "no predecessor."
Confirmed: `supersedes_approval_id` is set on **0 of 26** rows, and `is_current`
is 1 on all 26. Revise a decision and the record cannot say what it revised.

Any `WHERE id = ?` against this table matches nothing, and reports no error —
NULL equals nothing, including itself. Found exactly that way: a repair UPDATE
keyed on `id` changed 0 rows and returned success.

**Failure mode 11, silent gate failure — inside the gate itself.** The fix is
one column in one INSERT, plus a decision on whether to backfill ids for the 26
existing rows. Note the supersede path has never actually been exercised: no run
has more than one approval, so nothing is currently mis-linked.

### 2.18 Placeholders are not marked as placeholders — gate candidate
**Carried from NEXT_SESSION.md F15, 2026-08-30. This was missed when the list
was built; the coverage audit found it.**

The mechanism behind most of this list. `route_task.py` described and never
built. `push_cis_live()` with no caller. `workflow_run_id` NULL on all 30
`build_plan_nodes` rows. `needs_review` named in the record and existing
nowhere. The Eric Gate briefing rendering empty fields. **Each one looked
finished. Nothing announced the gap.**

Item 2.17 is the newest instance: a primary key column that is NULL on every
row, in a table whose whole purpose is an immutable audit record.

**The gate:** anything declared in a spec should be checkable against whether it
exists. That is the difference between this list and the documents in the
reference table — those describe; nothing verifies.

### 2.14 Operator routes execute runtime scripts directly
Failure mode 9 in CLAUDE.md. **Verify current state before building** — a 2026-05-01
build manifest records this as eliminated, so the recognition may be stale.

---


## From the 2026-08/09 mining pass — added 2026-09-01

Evidence for every item below is in `data/mining_archive/MINED_TASKS.md`. Scope says whether the finding was verified against the container in production or against code the container does not execute; the latter is not the same as irrelevant.

### 2.19 Build the verification snapshot and provenance gaps

Execution snapshot and git snapshot isolation are both recorded as verified gaps never built; the gate approval endpoint inserts with no provenance system; after a session-gap recovery the agent has no record of what it did during the gap.

**Scope:** CONTAINER — all four documents are the container's own skill library describing its verification phase; 15815 still needs verify-snapshot-gap.md read in full

**Need:** OPEN — partly answered and still open. Git snapshot isolation IS built — _run_isolated_l1 (pipeline_relay.py:1958-1967) creates a worktree at the pre-execution HEAD so Menter cannot fabricate evidence, with an explicit fallback warning. The execution snapshot, gate provenance and session-gap memory remain unbuilt, and the fallback path is itself unverified.


**Evidence:** raised 5 times, 2026-07-13 to 2026-08-24; mining_candidates 15782,15784,15723,15720,15815; full record in `data/mining_archive/MINED_TASKS.md`.

### 2.20 Make review independence verifiable, not assumed

Nothing checks that a reviewer searched before delivering a verdict; a revision carries no objection-to-resolution mapping; an empty or ambiguous reviewer response is consumed as a review; and Eric has no guaranteed second opinion. NOTE: the model-sharing half of this is FALSE in the container.

**Scope:** CONTAINER — container review1 is qwen/qwen3.7-max and review2 is z-ai/glm-5.2 against draft deepseek-v4-pro — three lineages, so model-sharing does not apply; the independence CHECKS are still absent

**Need:** OPEN — verified absent in production code: pipeline_relay.py has _db_retry (line 244) for database calls only, and line 698 states that any failure returns empty and the phase continues. No check refuses to advance on an empty or unsearched reviewer response, so the need stands.


**Evidence:** raised 5 times, 2026-06-27 to 2026-08-29; mining_candidates 166,976,13826,14972,3563; full record in `data/mining_archive/MINED_TASKS.md`.

### 2.21 The reviewed diff must contain the deliverable

A code review ran against a diff that omitted the new file entirely while L1 confirmed it on disk, and reviewers evaluated proposal text that did not match the applied patch.

**Scope:** CONTAINER — the source rows are pipeline_code_review, i.e. container runs

**Need:** OPEN — pipeline_relay.py has no chunk_diff-to-directive comparison and no expected-file manifest, so nothing checks that the diff under review contains the deliverable. The need stands.


**Evidence:** raised 2 times, 2026-08-29 to 2026-08-29; mining_candidates 783,786; full record in `data/mining_archive/MINED_TASKS.md`.

### 2.22 Fix the construction-view data contract and its missing handlers

F3 mismatch — topic vs intent, rounds vs phases, no latest_output — makes the view non-functional, and the UI gate action handlers the directive assumes exist were never confirmed.

**Scope:** NOT_IN_CONTAINER_PATH — VM dashboard; container_app.py serves only static /ui/

**Need:** UNASSESSED — the view is a VM dashboard surface. Whether Eric still uses it, and whether the container needs an equivalent, is not settled by the record.

**The one check that settles it:** confirm whether the VM dashboard construction view is still in use

**Evidence:** raised 2 times, 2026-08-29 to 2026-08-29; mining_candidates 724,838; full record in `data/mining_archive/MINED_TASKS.md`.

### 2.23 The cis-knowledge toolset grants pipeline dispatch to anything that uses it

`cis-knowledge` registers 18 MCP tools, and three of them start pipeline work — `cis_dispatch_drafter`, `cis_dispatch_reviewer`, `cis_dispatch_implementer`. They ship in the same toolset as KB search, so any agent given KB access can start a run as a side effect. Verified 2026-09-02 on review2, which holds those three tools despite being trimmed to a read-only advisor.

**Scope:** CONTAINER — runtime/mcp_bridge/tools.py defines all 18 and the server registers them as one set (agent.log, 2026-08-29: "registered 18 tool(s)"). The fix is in the MCP server, not config: config can only take or leave the whole toolset.

**Need:** OPEN — this contradicts the standing rule that runs are not started without Eric. The capability arrived by inheritance, not by decision. Nothing ever chose to give reviewers dispatch.

**Affects:** every agent using cis-knowledge, not only review2.

**The one check that settles it:** confirm whether an agent holding only cis-knowledge can start a run, then decide whether the server should expose read and dispatch as separate toolsets.

### 2.24 The gateway caches OpenRouter replies on prompt identity

Verified 2026-09-02 while building the advisor protocol: five `OpenRouter response cache HIT` entries in the review2 agent log. A re-review returned in 0.4s with an identical body and `usage` reporting `prompt_tokens 0, completion_tokens 0, total_tokens 0`; the gateway log recorded the same call as `in=0 out=0 total=0`. The reply looks fresh and costs nothing to record.

The consequence is not the wasted call, it is the stale one. A packet that has been revised can be answered by the review of its earlier version, and the artifact will record a cost of zero for a review that never ran. Nothing in the response distinguishes a cached reply from a live one.

**Scope:** CONTAINER — the gateway's OpenRouter response cache, hit on the api_server path. `tools/advisor_review.sh` works around it with a per-call nonce (`RUN_TAG`), which is a workaround in one script, not a fix. The pipeline's own agent calls in runtime/abstraction/pipeline_relay.py carry no such guard.

**Need:** OPEN — the workaround covers the advisor path only. Whether a pipeline re-run after a revision can be answered from cache is not established, and that is the case that matters: a reviewer appearing to re-review revised work while returning its earlier verdict is a rubber-stamp review (failure mode 3) produced by infrastructure rather than by the model.

**The one check that settles it:** determine whether pipeline_relay's calls are cache-eligible and what identity the cache keys on — full prompt, message list, or something narrower. If the key is the prompt, a revised proposal changes it and the risk is bounded; if it is narrower, it is not.

**Related:** 3.22 — a cached reply also reports zero tokens, so any per-agent cost measurement that lands on a cache hit will understate the true cost.

### 2.25 The feed is a direct API call, not an agent

Part of the review loop added 2026-09-02 — see the note above 1.18.

One message per card: the item, one sentence on what happened, the objection if there was one, what is next. No code, no output dumps. The reply is "go" or a redirect.

NOT root Hermes. The host pipeline is being retired as soon as the container is functional, and building the advisor system on a component scheduled for retirement repeats the mistake the 2026-09-01 scope pass found in 12 mined tasks.

NOT a container agent either. Messaging is a transport, not a role, and an agent given the job inherits its loadout — that is exactly how cis-knowledge handed pipeline dispatch to a read-only advisor (2.23). An agent whose job is to send a sentence should not acquire the ability to start a run because the toolset it was given happened to carry one.

So: an HTTP POST from the loop script using the bot credentials. No agent on either end, no coupling to the VM.

**Scope:** HOST — settled 2026-09-02. The Telegram credentials live in the host Hermes profiles' `.env` files, seven bot tokens across `/home/eric/.hermes` and `/home/eric/.hermes-*`. They are readable by whoever runs Claude Code. The container has NONE: all six container profiles' `.env` files carry zero Telegram variables, because the `-e CIS_TG_*` plumbing in `run_container.sh:114-120` passes host variables that are unset. So a host-side feed works today with no credential move; a container-side feed needs a token plumbed in first.

The token being in the root Hermes profile is a credential LOCATION, not a dependency — nothing above changes. The feed is still an HTTP POST that uses a bot token; no Hermes process is involved on either end, so nothing here retires with the VM pipeline. Only the file the token is read from would need to move.

**Need:** OPEN — no feed script exists. The transport underneath it is proven, which is a different thing.

**The one check that settles it — DONE 2026-09-02, both directions.** Message 1149 out via a plain `curl` POST to `sendMessage`; Eric's "go" came back as message 1150 through `getUpdates`, from uid 6511416750, matching the `TELEGRAM_ALLOWED_USERS` value — so the loop can verify the reply is his and not another group member's.

**The destination is a private chat, not a group.** The test ran in `CIS_Test_Group` (-5563618057), which held four bots besides Eric — three of them backed by running VM gateways, silent only because `TELEGRAM_REQUIRE_MENTION=true` in their configs. He deleted the group on 2026-09-02 rather than police that membership, and the feed now DMs him directly (uid 6511416750, verified: message 1155). A DM gives one agent by construction — there is no member list, so no second bot can appear — and `require_mention` does not apply in private chats. The bot is `@cis_kernel_bot`, bot id 8926607085, display name renamed to **HermesFeed** on 2026-09-02 so it is identifiable among the seven Hermes bots; the token and id are unchanged by that rename.

**Replies arrive unthreaded — the loop needs its own correlation.** Eric's "go" carried no `reply_to_message` field, so Telegram's threading cannot tell the loop which card a reply answers. Either one card waits at a time, which 1.21's waiting state gives for free, or each message carries a short tag the reply must quote. The first is simpler and is what 1.21 already implies.

**Stale, and left deliberately:** all seven host `.env` files still name the deleted group as `TELEGRAM_HOME_CHANNEL`, and five of those profiles have running gateways that would get a 403 on any post there. Harmless until a VM agent tries to reach him that way. Fix it in the same pass that wires the feed, pointing them at the uid rather than at a new group.

**Depends on:** 1.21. A feed without a waiting loop is a notification stream nobody reads by noon. **Blocked by:** 1.22 — replies that reach no index are the same loss as reviews that reach no index.

### 2.26 Six buried plugin copies wait inside the profile volumes

Each of the six profile volumes still holds the `mwl-proof` copy seeded into it on 2026-08-29. Since 2026-09-03 those paths carry a read-only bind mount of `enforcement/mwl-proof-v2/plugin` from the repo, so the buried copies are masked and unreachable. Harmless while the mounts are there.

**The failure mode is removal, not conflict.** Delete those six `-v` lines from `run_container.sh` and the August copies resurface — root-owned, correctly permissioned, indistinguishable from current. The container would then run a plugin frozen at 2026-08-29 while the repo moved on. Nothing errors, nothing logs, and an inspection of the file shows a plausible plugin. This is the stale-copy shape that has cost this repo repeatedly: absence of an error read as evidence of correctness.

**The permission bits now lie, and this is the part that will mislead an auditor.** Under the bind mount the plugin reads `worker:worker 0644`, which looks strictly weaker than the previous `root:root 0444`. It is stronger. Verified 2026-09-03: a `touch` inside the mounted directory fails with *"Read-only file system"* — the kernel refuses at the mount layer, before permissions are consulted, and that holds for root as well as worker. Anyone auditing with `ls -la` and no knowledge of the mount will conclude the seal was loosened and may "fix" it back into a writable image copy.

**Scope:** REPO — `enforcement/mwl-proof-v2/run_container.sh` lines 123-128, and the six `cis-agent-*` Docker volumes.

**Need:** OPEN — the buried copies exist today and nothing detects either the resurrection case or the missing mount.

**Removing them is not recommended.** It costs one root-privileged throwaway container per volume to delete roughly 5 KB each, cannot be done while the live container holds the volumes, and trades a masked file for six privileged writes to persistent state. If it is ever done, do it inside a rebuild window when the container is already down.

**The one check that settles it:** at startup, md5 each mounted `plugins/mwl-proof` against `enforcement/mwl-proof-v2/plugin` and confirm the bind mount is actually present — not that the permission bits look right. A match plus a present mount is the pass; equal bits with no mount is the silent-failure case the check exists to catch.

**Related:** 2.15 (gate scripts that have never fired — the same absence-read-as-health pattern), 1.17 (a comment is not a check), 0.4 (the override plane, which is the other thing that must be verified rather than assumed before enforcement is trusted).

### 2.27 The web-research block returns marketing copy, with raw HTML, into every call

The `## Current Research (web)` section of `[PRE-DISCOVERY RESULTS]` is the staleness gate for failure mode 4 — training-data staleness — and on `run-4bbeea78056e2607-1788140226` it delivered this, verbatim, to all six calls:

```
## Current Research (web)
- Search engine optimization: liked <span class="searchmatch">its</span> simple design.
  Off-page factors (such as PageRank and hyperlink analysis) were considered as well as
  on-page factors (such as <span class="searchmatch">keywo
- Google Ads: AI Essentials: Ads Power Pair <span class="searchmatch">Best</span>
  <span class="searchmatch">Practices</span>&quot;. Google Ads Help. Retrieved 2024-11-01.
- Search engine marketing: or discuss which of the <span class="searchmatch">tools</span>
  works better to get the traffic for selected <span class="searchmatch">keywords</span>
```

The task was merging FTS5 keyword results into `tools/ask_history.py`. The query terms — search, keywords, best practices — retrieved Wikipedia articles on **search-engine marketing**. Not stale, not wrong: simply about a different subject that shares vocabulary.

**Two defects, and the second is the worse one.** The retrieval is unfiltered, and the output is not sanitised: `<span class="searchmatch">` markup and `&quot;` entities go into the prompt as-is, truncated mid-word (`keywo`). A block that ships raw HTML has had nothing between the search API and the agent.

701 chars x 6 calls = 4,206 characters, ~1,050 tokens. The cost is trivial. The problem is that a section headed *Current Research* carries content with no relation to the task, and an agent instructed to weigh pre-discovery has no way to tell that this particular block is noise.

**Scope:** CONTAINER — the web-research step of the pre-discovery builder in `runtime/abstraction/pipeline_relay.py`.

**Need:** OPEN — present in all six payloads of the run above.

**The one check that settles it:** take a run's web-research block and ask whether any line mentions the subject of the task. If not, the block is noise and should be omitted rather than included empty-handed — and either way the markup must be stripped before it reaches a prompt.

**Related:** failure mode 4 (this gate's purpose), 2.18 (placeholders not marked as placeholders — the same problem of unusable content presented as usable), 3.23 (the rest of the payload audit).

### 2.28 KB_CONTEXT is duplicated inside PRE-DISCOVERY in the same prompt

Both `[KB_CONTEXT]` and the `## Knowledge Base` section of `[PRE-DISCOVERY RESULTS]` are built in the same call and land in the same payload, carrying the same rows under two headings. On `run-4bbeea78056e2607-1788140226`, three of the four signals are identical:

```
[KB_CONTEXT]      round_355, round_357, round_361                (1,304 chars)
PRE-DISCOVERY     round_355, round_357, round_361, round_363     (1,128 chars)
```

Present in all six calls: 7,824 characters of `KB_CONTEXT` across the run, most of it repeated a few thousand characters further down the same prompt.

**The cost is minor; the effect on the agent is not.** Material repeated under two headings reads as two independent corroborating sources, which is exactly the signal an agent weighing evidence should not be given falsely. It is the retrieval-side version of failure mode 15 — agreement that is not independent.

**Scope:** CONTAINER — `_add_hit` and `_pre_discovery` in `runtime/abstraction/pipeline_relay.py` both query and both render; neither knows about the other.

**Need:** OPEN — verified in all six payloads of the run above.

**The one check that settles it:** extract the row identifiers from both blocks of one payload and intersect them. A non-empty intersection is the defect; the fix is one block or a documented reason for two.

**Related:** 0.2 (both blocks are redaction choke points, so both were already known to exist — the duplication was not), 3.23, 2.3.


# TIER 3 — independent defects, no dependants

- **3.1** `ask_history` does not merge FTS5 with vector search. The relay does;
  `ask_history` does not.
- **3.2** No pre-delete or archive-policy validation. **Checked: absent.** On
  2026-08-29 a 4.9GB Chroma segment directory was deleted after a manual ad-hoc
  check. Nothing but care stood between that and deleting something live.
- **3.3** Container pre-flight checks are partial. **Checked:** `run_container.sh`
  has 3 file/directory tests — one hand-written case for the secrets file being a
  directory. No systematic mount verification, and mounts were added today.
- **3.4** Two manifest directories, canonical status unresolved.
  `logs/manifests/` vs `runtime/manifests/`, with an unenforced "do not write
  there".
- **3.5** Export gate warns "expected 12 artifacts, found 13" on every commit.
- **3.6** `projects.id` is `'cis'`, `build_plan_nodes.project_id` is `'CIS'`.
  A plain join returns 0 of 30 rows; `relay.py:1058` papers over it with
  COLLATE NOCASE.
- **3.7** `data/` is gitignored — `container_sessions/` and `drive_imports/`
  are not in version control.
- **3.8** Memory store has no governance: no access control, no audit trail, no
  deletion capability, no lifecycle management, no retention policy.
- **3.9** `effort_metric` scores DRAFT by code complexity; draft writes prose.
  `guardrails.py:3012` adjusts for brain/review1/review2 and omits draft.
- **3.10** The seven `SKILL.md` files have never been audited against what the
  guardrails enforce. `enforcement/mwl-proof-v2/cis-pipeline-architecture/SKILL.md`
  plus one per role (brain, draft, review1, review2, menter, verify) — **these
  are what the container agents actually read at runtime**, along with their
  `references/pitfalls.md`. If an agent is told to do something no gate checks,
  or a gate checks something no agent was told, that gap is invisible today.
- **3.12** `data/drive_imports/` is outside the knowledge base entirely.
  **Measured 2026-08-30: 11,763 files, 5.8GB, 0 chunks.** Not partial coverage —
  absent from both the keyword and the semantic index. 3.7 mentions the
  directory but only about version control; nothing recorded that it is
  unindexed.
  **What it is, checked rather than assumed:** a flattened drive dump — one
  directory, no structure — mixing SWA's Miramont behavioural-health documents
  (2,130 md, 756 docx, 344 pdf, 229 txt; SWA sources do reference them) with
  several thousand library files (`ZodError.ts`, `zstd.js`, `zoneinfo.py`,
  `.map`, `.pyc`). The same shape as the archive's `_4 Action` at 90% source
  code.
  **Not a task to index it.** Leaving it out is correct on the archive's own
  evidence, and it is SWA material, which the record sequences after the
  container infrastructure. Recorded so the gap is deliberate and visible
  rather than merely unnoticed — which is 2.18's whole point.

- **3.11** `cis_kernel/source/architecture_maps/13_RUNTIME_TOPOLOGY.md` claims
  *"Status: OPERATIONAL — populated from verified runtime truth as of
  2026-05-05"* and answers *"how does the system actually run?"*. Four months
  stale, and it is the kind of document 2.12 (primer/runtime divergence) is
  about. Verify or retire it.

---


## From the 2026-08/09 mining pass — added 2026-09-01

Evidence for every item below is in `data/mining_archive/MINED_TASKS.md`. Scope says whether the finding was verified against the container in production or against code the container does not execute; the latter is not the same as irrelevant.

### 3.13 Resolve the memory seed failure

seed_memory.py failed with 'database or disk is full' across roughly a thousand extraction files; whether the seed completed or is still short was never recorded.

**Scope:** UNDETERMINED — the seed target and its current completeness were never established

**Need:** UNASSESSED — the failure is a single 2026-05 log entry. Whether the seed later completed is not recorded either way, and the disk-full condition may long since have cleared.

**The one check that settles it:** re-run seed_memory.py and compare its completion count against the extraction file count

**Evidence:** raised 1 times, 2026-08-29 to 2026-08-29; mining_candidates 3513; full record in `data/mining_archive/MINED_TASKS.md`.

### 3.14 Finish or retire the VM operator surfaces

Pipeline source list and pagination, intake auto-refresh, the Review page, the DAM nav surface and the LXC public endpoint are specified and unbuilt; the Intel sidebar tabs are decorative placeholders; the dashboard cannot track long-running subprocess work; creating a CIS Live session does not auto-populate the sidebar so rounds can be logged against the wrong session; cis_review.py was built with no contract.

**Scope:** NOT_IN_CONTAINER_PATH — all are VM dashboard surfaces; container_app.py registers only relay_bp plus health/UI

**Need:** OPEN — these are Eric's operator surfaces and he still works through them. The container serves only static /ui/, so nothing has replaced them — the need stands either as build or as an explicit retirement.

**Evidence:** raised 5 times, 2026-04-24 to 2026-06-27; mining_candidates 5138,15527,15230,5153,15551; full record in `data/mining_archive/MINED_TASKS.md`.

### 3.15 Record the decision rationale that was never written down

The file-size limit has no explanatory note; the build plan still depends on a spec cited as containing factual errors and no longer on disk; the 640-line spec has no risk register.

**Scope:** NOT_IN_CONTAINER_PATH — project_decisions is not read or written in the container path

**Need:** OPEN — neither pipeline records it. project_decisions is not read or written in the container path either, so the need is unmet rather than answered — the container needs its own answer.

**Evidence:** raised 3 times, 2026-06-27 to 2026-08-29; mining_candidates 161,147,152; full record in `data/mining_archive/MINED_TASKS.md`.

### 3.16 Retire the legacy inline relay in app.py

PIPELINE_RUNS, portal_pipeline_start and portal_pipeline_status are still at app.py:824-917, duplicating api/relay.py, with only a TODO at line 22. app.py now declares itself reference-only, so the question is whether the file retires wholesale.

**Scope:** NOT_IN_CONTAINER_PATH — app.py is not the container entry point; container_app.py is

**Need:** OPEN — the duplicate code is present at app.py:824-917 and the file's own header declares it reference-only. The cleanup stands regardless of which pipeline runs.

**Evidence:** raised 1 times, 2026-08-29 to 2026-08-29; mining_candidates 3337; full record in `data/mining_archive/MINED_TASKS.md`.

### 3.17 Build the ADR-045 execution queue and run logging

execution_jobs schema, queue worker and operator queue routing are all recorded as not built, and the Router Spec's required extraction run-logging table does not exist.

**Scope:** NOT_IN_CONTAINER_PATH — no execution_jobs or runs table in the spine; the queue is VM-era design

**Need:** UNASSESSED — the container pipeline keeps its own run records in workflow_runs and deliberation_rounds. Whether that makes a separate execution queue and run-logging table moot, or leaves a real gap, is not established.

**The one check that settles it:** decide whether workflow_runs and deliberation_rounds make a separate queue moot

**Evidence:** raised 2 times, 2026-04-26 to 2026-04-29; mining_candidates 15570,15625; full record in `data/mining_archive/MINED_TASKS.md`.

### 3.18 Add pagination to the capped list endpoints

runtime/api/extraction_runs.py:27,32 and captures.py:23,28 hardcode LIMIT 50 with no paging.

**Scope:** NOT_IN_CONTAINER_PATH — neither blueprint is registered in container_app.py

**Need:** UNASSESSED — extraction_runs and captures are not registered in container_app.py. Whether the VM app that serves them is still running is not settled by the record.

**The one check that settles it:** confirm whether the VM app serving extraction_runs and captures is still running

**Evidence:** raised 1 times, 2026-08-29 to 2026-08-29; mining_candidates 809; full record in `data/mining_archive/MINED_TASKS.md`.

### 3.19 Group parallel advisor rounds reliably

advisor_messages needs a nullable batch_id; thread_id plus timestamp proximity cannot separate interleaved parallel rounds.

**Scope:** NOT_IN_CONTAINER_PATH — advisor_messages is referenced nowhere in the container path

**Need:** UNASSESSED — advisor_messages is absent from the container path. Whether parallel advisor rounds are still run at all is not settled by the record.

**The one check that settles it:** confirm whether parallel advisor rounds are still run

**Evidence:** raised 1 times, 2026-08-29 to 2026-08-29; mining_candidates 1402; full record in `data/mining_archive/MINED_TASKS.md`.

### 3.20 Implement knowledge-record backlinks

The designed backlink syntax for knowledge-record markdown was never implemented in cis_normalize.py.

**Scope:** NOT_IN_CONTAINER_PATH — cis_normalize.py is VM ingestion tooling, not in the container path

**Need:** UNASSESSED — cis_normalize.py is not in the container path. Whether knowledge-record backlinks are still wanted in the current knowledge model is not settled.

**The one check that settles it:** confirm whether backlinks are still wanted in the current knowledge model

**Evidence:** raised 1 times, 2026-06-27 to 2026-06-27; mining_candidates 5158; full record in `data/mining_archive/MINED_TASKS.md`.



### 3.21 Move the queue out of markdown and into the spine

The build list is a markdown document, so any UI that shows it has to parse prose. `mined_tasks`
already proved the structural form this needs: one row per task carrying scope, need_status,
evidence count, first and last raised, and the candidate ids behind it. Moving the queue into the
spine as a table gives a UI something to read directly, and it removes the two-lists failure
permanently — 2.12 exists because a second queue drifted from the first, and prose is what makes
that drift possible.

**Eric, 2026-09-01:** the list should appear in the UI as a roadmap of ongoing development.

**Scope:** UNDETERMINED — the spine is shared by both pipelines, but which surface renders the
roadmap is not settled. The VM dashboard is Eric's operator surface today; container_app.py serves
only static /ui/.

**Need:** OPEN — stated as a requirement on 2026-09-01. `mined_tasks` demonstrates the shape works;
nothing yet renders it.

**The one check that settles the scope:** decide which surface renders the roadmap before choosing
where the table lives.

**Depends on:** nothing. Blocks 4.18 (the card factory needs a table to read) and the UI roadmap.

### 3.22 Audit token cost per agent against what the role actually needs

Measured on review2, 2026-09-02: the 79 skills cost 2,193 tokens, 14% of the prompt. Tool schemas cost the rest. `platform_toolsets.api_server` was unset, so all 14 toolsets loaded — including browser, image_gen, vision, cronjob and code_execution, none of which a reviewer uses. The five largest tool schemas were 24KB alone: session_search 5,919 bytes, terminal 5,675, delegate_task 5,573, skill_manage 4,138, memory 2,836.

**Scope:** CONTAINER — the six /home/worker/.hermes-*/config.yaml files. `platform_toolsets` is unset in all six; no agent's loadout has ever been matched to its role.

**Need: DONE 2026-09-04.** All six measured and cut.

**The split, isolated at last.** Three pings separated what nothing had separated before — a profile with skills off and toolsets off costs 390 tokens, skills off and toolsets at default costs 13,655, everything on costs 15,848. So of a 15,923-token profile: **tool schemas 13,265 (84%), the whole 75-skill index 2,193 (14%), base prompt 390 (2%)**. Skills are 29 tokens each, an index rather than bodies — `skill_view` fetches a body on demand, so skills were already lazy and there was nothing to win there. The cost was always the schemas.

**What each role actually calls**, from its own `state.db` message store rather than assumed — the spine records no tool calls at all (2.6), and `hook_payload.jsonl` carries an opaque `task_id` with no role in it, so the per-profile stores are the only attributable source:

| role | toolsets | tools | before | after | cut |
|---|---|---|---|---|---|
| brain | file, terminal, skills | 9 | 16,741 | 7,908 | 53% |
| draft | file, terminal, skills | 9 | 16,873 | 8,039 | 52% |
| review1 | file, terminal, code_execution | 7 | 16,563 | 4,843 | 71% |
| review2 | file, terminal, code_execution | 7 | 15,923 | 4,610 | 71% |
| menter | file, terminal, code_execution | 7 | 16,743 | 4,976 | 70% |
| verify | code_execution | 1 | 15,923 | 1,463 | 91% |

Down from 35 schemas each. On the six calls of a real deliberation, `run-4bbeea78056e2607-1788140226`: system overhead **98,586 → 34,853**, total **131,383 → 67,650**, overhead share **75% → 52%**. The 32,797 tokens of actual reasoning content are untouched — what went was schemas re-sent every turn.

`cis-knowledge` disabled on all six. Across every profile's history the only call to any of its 13 tools was one `cis_adapter_status` health check by review2; it was never once used for retrieval, and it carries the three `cis_dispatch_*` tools, so holding it means being able to start a pipeline run (2.23). Disabling the MCP server is required *alongside* the toolset list, not instead of it — a narrowed list is re-populated by the recovery block in `hermes_cli/tools_config.py`.

**Menter keeps `code_execution` although its history does not show it.** Its volume dates from 2026-08-29 and holds 18 calls; the architecture skill records what that sample misses — `run-86bc4d1009b8fb44-1783645778` completing all seven phases with Menter making the first successful file mutation in the container. Trimming to the sample would have removed the implementer's ability to run what it writes, the likeliest way to break the code run 1.23 waits on. The deviation was then **validated rather than argued**: menter's verification call produced its first ever recorded `execute_code`.

**Every role verified working, not assumed**, each against an answer confirmed on the host afterwards: brain returned the README's first line and 319; draft returned 1705 and wrote it to a file; review1 returned 68428079 and 80; review2 returned 134655089 and 319; menter computed the sum of the first 500 primes as 824693 and wrote it. `hook_seen.log` grew on every call, proving the wall is registered and firing per profile — better evidence than `plugin_load.log`, whose eight `register()` lines name no profile.

**Read the ping numbers correctly.** Those are idle-turn floors. The same agents doing real work cost far more — brain 16,162, draft 24,981, menter 15,966 — because file contents and tool results re-enter context. The trim removes fixed overhead, not work.

**Edited in the repo profiles, not container configs**, so it survives recreate. Commits `f86ed4d` and `256a72d`.

**Eric, 2026-09-02:** adaptability is part of the method — skills and tools should be optimised per use case, and the loadout should change between dev and production mode.

**The one check that settles it:** a PONG call per agent recording prompt_tokens before and after, against the loadout each role actually uses.

**Related:** 1.6 (prompt size is never measured) is the same blind spot seen from the cost side. 1.17 restores review2; this item decides what "restored" should mean.

Measured 2026-09-02: the trimmed advisor cost 109,778 prompt tokens on one real
review, against 4,502 on a ping. ~16 tool calls, each resending accumulated
context. The per-turn floor is not the cost of a review — turn count is. Cutting
skills and toolsets lowers the floor and does not touch this. Any advisor
protocol should hand the agent its evidence rather than making it search for it.

### 3.23 Two thirds of every relay payload is context repeated call to call

The full composition of `run-4bbeea78056e2607-1788140226`, six calls, 131,197 characters — the relay-side prompt, separate from the per-agent system prompt that 3.22 trimmed:

| component | chars | ~tokens | share |
|---|---|---|---|
| constraints + prior phase output | 46,087 | 11,521 | 35.1% |
| intent anchor | 31,815 | 7,953 | 24.2% |
| `[PRE-DISCOVERY RESULTS]` | 15,712 | 3,928 | 12.0% |
| `[PROJECT_BRIEF]` | 12,108 | 3,027 | 9.2% |
| `[KB_CONTEXT]` | 7,824 | 1,956 | 6.0% |
| intent restatement | 6,090 | 1,522 | 4.6% |
| `[RECENT_RUNS]` | 3,006 | 751 | 2.3% |
| `[PRIOR_DISPOSITIONS]` | 2,496 | 624 | 1.9% |
| task body (brain only) | 2,187 | 546 | 1.7% |
| `[ERICS_WORKING_METHODS]` | 1,242 | 310 | 0.9% |
| `[ROLE_OVERLAY]` | 1,047 | 261 | 0.8% |
| `[BIAS_OVERLAY]` | 1,024 | 256 | 0.8% |
| `[TASK]` | 324 | 81 | 0.2% |
| instruction header | 235 | 58 | 0.2% |

**4,446 characters are byte-identical on every call** — `KB_CONTEXT`, `PRIOR_DISPOSITIONS`, `RECENT_RUNS`, `PROJECT_BRIEF`, `ERICS_WORKING_METHODS` — sent six times for 26,676 chars, **6,669 tokens, 20% of the payload**. `PROJECT_BRIEF` is the one that varies, and it varies by exactly one line:

```
-Generated: 2026-08-30 22:34 UTC | Run: run-bb278c9e6ee9 | Latest pipeline: ...126284
+Generated: 2026-08-31 01:40 UTC | Run: run-0caadf8cedb4 | Latest pipeline: ...140226
```

**The intent anchor is restated in full to all four downstream calls** — 6,363 chars plus a 1,218-char restatement immediately after it, 9,476 tokens across the run, 29% of the payload. The anchor exists so phases do not drift from the intent; nothing establishes that repeating it verbatim per call, rather than once per run, is what achieves that.

Only the 35% labelled *constraints + prior phase output* differs by phase and carries the work — brain's understanding to the reviewers, draft's proposal to the proposal reviewers.

**Scope:** CONTAINER — prompt assembly in `runtime/abstraction/pipeline_relay.py`.

**Need:** OPEN — measured, unaddressed. This is Tier 3 because it is cost and shape, not correctness: no agent is misled by it, and 3.22 already took the larger bite. It becomes cheap to fix if 2.3 is done, because a conversation carries the fixed context once instead of per call.

**The one check that settles it:** diff any two payloads from the same run and measure the identical span. Anything byte-identical across every call in a run is a candidate to send once.

**Related:** **2.3** — the same root. Independent POSTs force both the re-sent context and the reviewers' blindness to each other; one change fixes both. 3.22 (the system-prompt side of the same bill, done), 1.6 (prompt size is never measured), 2.28 and 2.27 (specific defects inside these blocks), 1.24 (what the trajectory block feeds brain).

# TIER 4 — after the infrastructure works

- **4.1** Nothing triggers session ingest. Both ingest tools work; neither fires.
- **4.2** Container agent history does not reach the KB. State now persists.
- **4.3** What the container regulates itself vs what needs a human trigger.
  Approval must never automate.
- **4.4** No learning loop from approve/reject decisions.
- **4.5** 601 mined asks -> cards. Hours of local GPU, ~8% yield.
- **4.6** A hermes agent in these working sessions.
- **4.7** Role theory into the agents. **Sequencing decision on the record:**
  agents come after deterministic workflows are stable.
- **4.8** Archive processing — prose vs software split, Troy's drive excluded.
- **4.10 THE HARNESS SELF-IMPROVEMENT LOOP — Eric's design, 2026-08-30.**
  *"The pipeline should go through its code and make recommendations for
  improvements. The pipeline won't be able to modify its own files but it can
  recommend. Those recommendations are saved in a folder that triggers the
  Claude API to assess the recommendation and implement it if feasible."*

  **This is already in the record, with sources.** Session
  `hermes_session/glm-verifier/session_20260709_154626_907a1a`, 9 July 2026:
  - Lilian Weng, *"Harness Engineering for Self-Improvement"*, 4 July 2026. The
    RSI roadmap: instruction prompts -> structured context -> workflow ->
    harness code -> optimizer code.
  - **HASE**, arXiv:2607.03935, *"Harness-Aware Self-Evolving: Co-Evolving Model
    Weights, Harness, and Task Solutions"* — Luo et al., HKU / Jiutian Research.
    Headline: Qwen3-8B with an evolved harness matches GPT-OSS-120B.
  - The assessment already concluded **CIS is a harness** in Weng's sense — the
    relay, the six agents, the deliberation protocol, the gates, the spine.

  **Eric's design already answers the two hazards the record raised**, which is
  why it is worth building rather than re-litigating:
  - *"Having the pipeline change its own code while it's the thing being trusted
    to check work is a genuine circularity."* Recommend-only removes it.
  - HASE's own rule: **the evaluator must be separate from the builder,
    otherwise it optimizes the referee instead of the game.** A separate
    implementer via the Claude API is that separation.

  **THE CONSTRAINT THAT MUST BE BUILT IN, from HASE.** Split the harness in two
  and treat them differently:
  - **Guidance** — agent prompts, overlays, retrieval, memory. Safe to
    recommend against freely; it cannot make a wrong answer right.
  - **Evaluation** — guardrails, gate scripts, the verifier, the Eric Gate.
    **Off limits to self-recommendation.** A system that can propose edits to
    its own scorer will eventually propose the edit that makes it score well.
  CIS currently conflates the two, so the boundary has to be drawn before the
  loop can safely exist.

  **PREREQUISITE, and it is the real gate: 1.1.** The loop runs on evidence from
  completed runs — HASE's mismatch set is *proxy said good, oracle said bad*,
  which here is *Menter said done, Verify said fail*. **No run has ever gone end
  to end**, so today the loop would have nothing to reason from and would
  recommend from the code's appearance rather than its behaviour. That is
  guessing with extra steps.

  **Cheapest first step, and the record calls it out as highest value / lowest
  cost:** prompts are hardcoded in `pipeline_relay.py`. Move them to versioned
  files, add `prompt_version` and a run-outcome record, and the mismatch data of
  2.8 starts accumulating on its own. That work is useful whether or not the
  full loop is ever built.

  **Related and already listed:** 2.8 (verification results change nothing — the
  mismatch set is exactly this), 4.4 (no learning loop from approve/reject),
  2.11 (no CIS-task-to-agent-task contract), 1.6 (prompt size unmeasured).
  **Sequencing already on the record:** agents and self-evolution come after the
  deterministic layer is stable — see Decisions to Protect.

  Not applicable from HASE, checked rather than assumed: RL weight training
  (GRPO/PPO, 8×H20) and evolutionary search over hundreds of candidate harnesses
  per phase. Both need infrastructure CIS does not have.

- **4.9** The documentation-gap loop, named in the record and still running:
  *"Undocumented configuration -> failure -> recovery -> no documentation ->
  future failure (negative loop)."* This list is itself evidence — an earlier
  session did the same archaeology for the same reason. 2.18 is its enforcement
  handle. **Carried from NEXT_SESSION.md F20; missed when this list was built,
  found by the coverage audit on 2026-08-30.**

---


## From the 2026-08/09 mining pass — added 2026-09-01

Evidence for every item below is in `data/mining_archive/MINED_TASKS.md`. Scope says whether the finding was verified against the container in production or against code the container does not execute; the latter is not the same as irrelevant.

### 4.11 Automate the ADR-048 intake and handoff package

The record calls the manual transfer of structured content the largest remaining automation gap and it is still done by hand. The Downloads watcher runtime model and draft storage format were never settled; cis_build_handoff_package.py and cis_download_watcher.py were never built; a dropped return-dispatch pickup deadlocks the run.

**Scope:** UNDETERMINED — the ADR-048 staging path is VM-side, but whether the container pipeline's own intake replaces the need is not established

**Need:** OPEN — container_app.py exposes no intake, staging or drafts route, so the container has not replaced the ADR-048 staging path. The manual transfer the record calls the largest remaining automation gap is still unanswered by either pipeline.


**Evidence:** raised 4 times, 2026-05-13 to 2026-08-02; mining_candidates 15019,15020,15017,14994; full record in `data/mining_archive/MINED_TASKS.md`.

### 4.12 Settle the glossary-collision and inheritance-index schemas

Unresolved glossary term collisions block cross-layer operations with no collision-to-runtime bridge; the inheritance index has no machine-readable schema and neither session-initialization nor query-routing consumes it.

**Scope:** UNDETERMINED — would be settled by checking whether any container phase reads the glossary or the index

**Need:** UNASSESSED — no container phase reads a glossary or inheritance index — confirmed by grep over runtime/abstraction/ and container_app.py. Absence is not evidence the need stands: whether these artefacts are still wanted is a design decision nobody has recorded.

**The one check that settles it:** check whether any container phase reads the glossary or the inheritance index

**Evidence:** raised 2 times, 2026-05-13 to 2026-05-13; mining_candidates 15023,15024; full record in `data/mining_archive/MINED_TASKS.md`.

### 4.13 Close the system-learning loop

Corrections are logged but never fed back into the extraction model, so the review work produces no improvement.

**Scope:** UNDETERMINED — would be settled by establishing whether the container's pattern catalog consumes correction history

**Need:** OPEN — pipeline_relay.py contains no reference to corrections, so nothing feeds review outcomes back into any model. The loop the record describes is absent from the running pipeline, and the record states the intent plainly rather than leaving it open.


**Evidence:** raised 1 times, 2026-06-27 to 2026-06-27; mining_candidates 5162; full record in `data/mining_archive/MINED_TASKS.md`.

### 4.14 Define the capability taxonomy and criticality criteria

Without one, the primary-plus-fallback requirement cannot be enforced.

**Scope:** UNDETERMINED — no capability_taxonomy, CapabilityClaim or capability_registry anywhere under runtime/ — absent from both pipelines

**Need:** UNASSESSED — absent from both pipelines. The record names it as a prerequisite for enforcing primary-plus-fallback, but nothing establishes that that requirement is still live. Needs a decision on whether the taxonomy is wanted before it can be called open.

**The one check that settles it:** decide where the taxonomy is meant to live — it is absent from both pipelines

**Evidence:** raised 1 times, 2026-08-29 to 2026-08-29; mining_candidates 79; full record in `data/mining_archive/MINED_TASKS.md`.

### 4.15 Lock the video preprocessing decisions

Whisper model size and the segment-level video source_unit schema must be decided before video preprocessing is built.

**Scope:** NOT_IN_CONTAINER_PATH — video preprocessing is the VM creative-ingestion path

**Need:** UNASSESSED — video preprocessing is creative-runtime work the dev pivot deferred. The record does not say whether it was dropped or postponed.

**The one check that settles it:** decide whether video preprocessing is dropped or postponed

**Evidence:** raised 1 times, 2026-06-27 to 2026-06-27; mining_candidates 5149; full record in `data/mining_archive/MINED_TASKS.md`.

### 4.16 Settle model routing and the benchmark protocol

Intelligent routing between local and frontier models is unimplemented, the benchmark protocol is not operationalised, and the Qwen3-VL-32B FP8 test path is unsettled.

**Scope:** NOT_IN_CONTAINER_PATH — routing between local and frontier models is the VM ingestion concern; the container uses fixed per-role model config

**Need:** UNASSESSED — the container uses fixed per-role model config. Whether routing between local and frontier models is still wanted, or was answered by the fixed assignment, is not established.

**The one check that settles it:** decide whether fixed per-role model config answers the routing need

**Evidence:** raised 1 times, 2026-06-27 to 2026-06-27; mining_candidates 5141; full record in `data/mining_archive/MINED_TASKS.md`.



### 4.17 Automate issue intake — nothing adds to this list but a person

New issues reach this list only because someone writes them here by hand. That is why the
2026-08-31 mining recovery was necessary at all: months of recognitions sat in the record and never
became items, because the only intake path was human attention.

The raw material already exists and is already being captured. `hook_payload.jsonl` logs every tool
call, including blocked ones — written by `enforcement/mwl-proof-v2/plugin/__init__.py:22`. Nothing
reads it. `cis_shell_hook.sh:32` writes a second payload log with the same status.

**Scope:** CONTAINER — the plugin that writes the payload log runs in the container on every tool
call.

**Need:** OPEN — verified: grep across runtime/, tools/ and enforcement/ finds writers only, no
consumer of either payload log.

**The one check that settles the design:** decide what an automated intake produces — a candidate
row for adjudication, or a queue item directly. It must not be the latter without a gate, or the
list fills with noise.

**Related:** the end-of-day evaluation item — both are about the system noticing its own state
without Eric reading logs.

### 4.18 Wire the card factory to the queue

The card generators exist and stalled. `tools/generate_cards.py`, `tools/generate_intention_cards.py`
and `tools/seed_pipeline_cards.py` are all present, and `cards/pipeline_cards.db` holds 32 cards —
verified 2026-09-01. They were never pointed at the task queue, so nothing regenerates cards as the
queue changes.

Wiring them to read the tasks table would give one card per issue, kept in step with the queue
rather than hand-seeded.

**Carry this rule, from 2026-08-31:** a task nobody has investigated gets an INVESTIGATE card, never
a BUILD card. And PROOF on every card must be a command the operator can run — not a description of
what success looks like. A BUILD card for unexamined work is how the pipeline gets sent to build the
wrong thing confidently.

**Scope:** NOT_IN_CONTAINER_PATH — the generators and `cards/pipeline_cards.db` are VM tooling; none
is imported by `container_app.py` or `pipeline_relay.py`.

**Need:** OPEN — the generators exist, the card count has not moved from 32, and the queue now has a
structured form to read.

**The one check that settles the shape:** confirm whether `pipeline_cards.db`'s existing schema can
carry the mined_tasks fields (scope, need_status, evidence, candidate ids) or needs replacing.

**Depends on:** 3.21 — the factory needs a table, not a markdown document, to read.

### 4.19 A button that sends an issue card into the pipeline

**Eric, 2026-09-01.** From the roadmap in the UI, select a card and route it into the pipeline as a
run.

**TWO CONSTRAINTS ON THE RECORD — both must hold before this is built:**

1. **Eric selects the card. The pipeline must not pull its own work.** This is the
   evaluator-must-not-be-the-builder rule in a new place: a system that chooses which of its own
   defects to fix, and then judges whether it fixed them, has no independent check left anywhere in
   the loop. Selection stays with the operator.

2. **Nothing routes in until a run can be stopped.** Verified 2026-09-01: the relay blueprint
   exposes eight routes and `grep -c cancel runtime/api/relay.py` returns 0. A one-click path into
   an unstoppable process is worse than no button — today the friction of starting a run by hand is
   the only brake that exists.

**Scope:** CONTAINER — the pipeline the button would feed is the container pipeline.

**Need:** OPEN — stated as a requirement on 2026-09-01.

**The one check that settles readiness:** the stop button (Tier 1) must land first. Until then this
item is blocked by its own second constraint.

**Depends on:** the Tier 1 stop-button item, 3.21, and 4.18.

# REFERENCE DOCUMENTS — for when we reach each item, not before

These exist and describe some of the above. **None of them counts as
implementation.** Their only use is to save design time when we build.

| document | lines | covers |
|---|---|---|
| `docs/contracts/CIS_Execution_Layer_Contract_v1.md` | 782 | 1.3, 1.4, 2.4, 2.5 |
| `docs/DETERMINISTIC_GUARDRAIL_SPECIFICATION.md` | 728 | 2.1, 2.2 — and documents 51 dead gate scripts |
| `docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md` | 703 | 2.11 |
| `docs/_audit_eric_model_failures.md` | 110,477 | 2.7 — evidence base |
| `docs/contracts/CIS_Verification_Layer_Contract_v1.md` | 271 | 2.8 |
| `docs/contracts/CIS_Automation_Reduction_Contract_v1.md` | 223 | 4.3 |
| three Phase 0 contracts (source manifest, processing profile, review states) | 688 | 2.4 |
| `docs/ADRs/ADR-048_Staged_Draft_Intake_Layer.md` | — | 1.5 |
| `docs/ADRs/ADR-047_SCOPE_PREDRAFT.md` | — | 3.4 |
| `docs/CIS_CONFLICT_REGISTER.md` | 228 | 2.9 |

---


## Recorded, not queued — superseded by the container

- **Make inter-agent review traffic first-class and readable** — the container answers this a different way: deliberation_rounds carries reviewer1_output and reviewer2_output (spine_schema.sql:1003-1004), so a verdict is a stored per-round field rather than Drafter narration, and the container's own record shows the [:500] payload truncation was removed. The dispatch_log relay this describes is not how the container moves review output. (raised 3 times; mining_candidates 13859,13468,14616). Recorded so it is not mined again.
- **Keep test data out of canonical state** — a test transition wrote proposal_id='test-lifecycle-001' into live lifecycle_events. The stray row is gone: lifecycle_events now holds zero rows with a test- proposal_id, so the incident is closed. A guard against recurrence would be new work, not this item. (raised 1 time; mining_candidates 1360). Recorded so it is not mined again.

# HOW TO WORK THIS LIST

Take items in tier order. For each one, at the time you reach it:

1. **Confirm it is still not in the code.** Some of these were checked on
   2026-08-29 and the code changes.
2. **Confirm the concern is still valid for the container pipeline.** Several
   originate from the earlier host application. The function may still matter
   even when the implementation is gone.
3. **Read the reference document if one exists** — to save design time only.
4. **Then decide:** build, adapt, or drop with the reason recorded.

Nothing on this list has been dropped on the strength of a document claiming it
was done.

---

# COVERAGE — what this list is built from, and what it is not

Stated so the next session knows where the holes are.

**Searched thoroughly:**
- The knowledge base. 6,578 mined statements (lexical + semantic, 98% non-overlap
  between the two methods), 1,261 clusters, all read individually.
- The 51 gate scripts. Cross-referenced against `gate_outcomes`.
- `guardrails.py`. All 34 specified guardrails checked against implementation,
  invocation, and BLOCK/ADVISORY mode.
- ~15 specific capabilities verified directly against the code and schema.

**Searched by content, not filename:** 5,541 documents scanned, 255 duplicate
copies collapsed, **210 distinct documents scoring as specifications — 132 of
them (63%) invisible to any filename search.** Tool:
`tools/find_specs_by_content.py`.

**NOT searched — real holes:**
- **The archive.** 2,186,884 chunks, deliberately excluded from the semantic
  index, never mined for issues at all.
- **The 2,349 short fragments** dropped from mining for being under 45
  characters. "Not implemented" in a status-table cell is exactly that shape.
- **110 of 117 `runtime/` Python files.** Surveyed for structure and
  silent-failure patterns; not read.
- **The seven `SKILL.md` files** — see 3.10. Highest-value item remaining,
  because they are the agents' actual instructions.
- **~200 of the 210 content-identified specification documents.**
- **Git commit bodies.** 348 commits, 66 mention fix/bug/fail; only subjects
  were read.

The gate scripts and `guardrails.py` are the parts I would defend. The document
corpus is sampled, not exhausted.
