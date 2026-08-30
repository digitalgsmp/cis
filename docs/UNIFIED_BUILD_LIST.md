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

---

# TIER 1 — blocks a run completing end to end

### 1.1 Prove a run completes past the gate
No run has ever gone intake -> deliberation -> gate -> implement -> verify ->
done. Furthest reached: ERIC_GATE. Depends on 1.2.

### 1.2 Approve or close run-e70293544935a92e-1787973534  — **Eric's decision**
Briefing renders, hash stable, goal_reference 12 exists. Two 2026-08-22
throwaways also sit at the gate (`"test"`, `"smoke check"`) — close those.

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

**Checkable form:** before any output that asks Eric something, the question
must survive three tests — (1) is it answerable from the code, the disk or the
record? then answer it instead; (2) is it settled by analysis already done? then
state the decision, not the menu; (3) do the options and their consequences sit
adjacent to the question, with a criterion for choosing? An earlier table does
not count. Only a question passing all three reaches him.

This is the gate 1.8 has to become, and it applies to assistants in these
sessions before it ever applies to a container agent — the failures logged here
are all from the session that wrote the item.

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
- **4.9** The documentation-gap loop, named in the record and still running:
  *"Undocumented configuration -> failure -> recovery -> no documentation ->
  future failure (negative loop)."* This list is itself evidence — an earlier
  session did the same archaeology for the same reason. 2.18 is its enforcement
  handle. **Carried from NEXT_SESSION.md F20; missed when this list was built,
  found by the coverage audit on 2026-08-30.**

---

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
