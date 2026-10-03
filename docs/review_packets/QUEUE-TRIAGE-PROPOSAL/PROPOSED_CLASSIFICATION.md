# Proposed Classification — 56 Unclassified Queue Items

Produced: 2026-10-03 · HEAD `99b1c30b4f05b7cdc88c18a9c33544d7c71e513d`
Actor: claude-opus-5 · **NOT APPLIED.** See `BLOCKING_SET.md` for why.

Scope vocabulary is the one the existing 63 classified rows already use —
`CONTAINER`, `REPO`, `HOST`, `NOT_IN_CONTAINER_PATH`, `UNDETERMINED` — whose
meaning the build list itself states: *"Scope says whether the finding was
verified against the container in production or against code the container does
not execute; the latter is not the same as irrelevant."*

`need_status` values are only those the column's CHECK constraint permits.
There is no `NEEDS_ARCHITECT_DECISION` value; the existing equivalent is
**`NEEDS_ERIC`**, and that is what is proposed wherever the record is ambiguous
or the next action is a decision rather than work. No new status was invented.

Plain-English lines are written for the Project Map's reviewed vocabulary layer
(`tools/state/project_intelligence_vocabulary.json`, which currently holds 3
entries). They are drawn from each item's own recorded text, not inferred.

---

## Batch 1 — Tier 1 (12 items)

### 1.2 · `DONE` · scope `REPO — the approval record in eric_gate_approvals, written by tools/eric_gate/record_decision.py`
Evidence:
```
$ sqlite3 ... "SELECT workflow_run_id, decision, decided_at FROM eric_gate_approvals
               WHERE workflow_run_id LIKE 'run-e70293544935a92e%';"
run-e70293544935a92e-1787973534 | APPROVE | 2026-08-30T17:35:14Z
$ sqlite3 ... "SELECT id, created_at FROM workflow_runs WHERE status='ERIC_GATE';"
run-4bbeea78056e2607-1788140226 | 2026-08-31T01:37:06
```
The named run was approved. The two 2026-08-22 throwaways the item says to close
are no longer at the gate. **Note, not part of this item:** a *different* run is
parked at ERIC_GATE now, and it is the `ask_history` task — see 3.1.
*Plain:* "The one run waiting on Eric's yes/no got its answer, and the two junk test runs beside it are gone."

### 1.3 · `OPEN` · scope `CONTAINER — the relay state machine in runtime/abstraction/pipeline_relay.py and runtime/api/relay.py`
```
human_review_required: 0   retry_pending: 0
failed_timeout: 0          contradiction_detected: 0     (both files, 2026-10-03)
```
*Plain:* "When a step fails there is no rulebook for what happens next — the run is either killed or the failure is ignored."

### 1.4 · `OPEN` · scope `CONTAINER — retry and escalation policy in pipeline_relay.py`
Only `_db_retry` (database contention) and the deliberation round caps
`MAX_BRAIN_ROUNDS` / `MAX_DRAFT_ROUNDS` exist. Same grep basis as 1.3.
*Plain:* "If an agent fails there is no 'try again, then give up and tell someone' policy."

### 1.5 · `OPEN` · scope `CONTAINER — pipeline_relay.py is the only writer of knowledge_messages under runtime/`
*Plain:* "Work that gets approved stays a loose file; nothing files it as the official record."

### 1.6 · `OPEN` · scope `CONTAINER — the agent-call path that writes agent_trajectories`
```
$ sqlite3 ... "SELECT COUNT(*), SUM(tokens_in>0) FROM agent_trajectories;"
507|0
```
Matches ADR-PIPE-003's recorded "0 of 507".
*Plain:* "Nobody measures how big a prompt is, so one too large to handle fails without saying so."

### 1.7 · `OPEN` · scope `CONTAINER — the gateway call in pipeline_relay.py`
*Plain:* "You cannot watch an agent work; the system guesses it is alive from a log it does not always write."

### 1.8 · `OPEN` · scope `CONTAINER — the Eric Gate briefing output and the role overlays`
Framing superseded 2026-09-04 by `docs/DECISIONS/2026-09-04_recommendation_standard.md`:
options-with-consequences is the floor, a named recommendation is the target.
Relationship is **authoritative** (the item cites the decision record by path);
no queue edge proposed, per ADR-PIPE-006.
*Plain:* "Agents ask Eric technical questions he has no way to answer; they should recommend, with evidence."

### 1.9 · `OPEN` · scope `CONTAINER — the two approval paths: tools/eric_gate/record_decision.py and runtime/api/relay.py`
*Plain:* "There are two ways to approve a run, and the documented one silently parks it forever."

### 1.10 · `OPEN` · scope `REPO — the pre-commit hook, the existing briefing renderer, and record_decision.py`
The item states its own step 1 is unblocked and that its open decisions do not
block it. Proposed OPEN rather than NEEDS_ERIC on that basis.
*Plain:* "Changes an assistant makes directly never pass the review gate that pipeline runs must pass."

### 1.11 · `OPEN` · scope `CONTAINER — gateway response handling and the relay's retry path`
**Live relevance:** this is the exact defect that the current provider-funding
condition triggers — an unfunded credential returns HTTP 200 carrying a billing
refusal, which is stored as model output and retried. Relationship to the P0
blocker observed, **not authoritative**; no edge proposed.
*Plain:* "When the bill is not paid the system blames the AI model instead of saying 'out of credits'."

### 1.12 · `OPEN` · scope `CONTAINER — build_briefing.py and the agent_trajectories rows it does not read`
*Plain:* "Eric approves the proposer's own summary; the 14,608 characters the independent reviewers wrote never reach him."

### 1.13 · `OPEN` · scope `CONTAINER — exception formatting and the heartbeat in pipeline_relay.py`
*Plain:* "When an agent times out the error message is blank, so you cannot tell what broke."

---

## Batch 2 — Tier 2, first half (11 items)

### 2.1 · `NEEDS_ERIC` · scope `CONTAINER — the 30 guardrail functions in runtime/abstraction/guardrails.py, called on every container run`
The item's own stated next action is a decision: *"Audit all 30 and decide per
guardrail whether its default should enforce."* Queue 0.6 already records that
arming the guardrails needs an override policy that does not exist, so the
decision is genuinely upstream of the work.
*Plain:* "Thirty safety checks run, but only seven can actually stop bad work. Someone has to decide which of the other 23 should."

### 2.2 · `OPEN` · scope `CONTAINER — guardrails.py`
Four named guardrails absent: Honesty Reporter, Model Diversity Enforcement,
Position Randomizer, Example Diversifier.
*Plain:* "Four safety checks that were designed were never written, including the one that stops a model reviewing its own work."

### 2.3 · `OPEN` · scope `CONTAINER — guardrails.py plus the single-POST call shape at pipeline_relay.py:1175`
`sequential_review` appears 4× in guardrails.py — defined, never appended to a
report. The item records the cause as structural: every agent call is one
independent POST with no history, so the reviewers cannot see each other.
*Plain:* "The check meant to stop two reviewers sharing a blind spot never runs, because neither reviewer can see the other's answer."

### 2.4 · `OPEN` · scope `CONTAINER — spine writes and the absent needs_review quarantine flag`
```
$ grep -rl "needs_review" --include="*.py" runtime/ tools/ | grep -v "/\.venv/" | wc -l
0
```
*Plain:* "Nothing checks that data going into the system is valid, and the flag for quarantining bad data was never built."

### 2.5 · `OPEN` · scope `REPO/CONTAINER — the spine schema and runtime/schema/migrations`
```
$ sqlite3 ... "SELECT COUNT(*) FROM sqlite_master WHERE type='table'
               AND name IN ('schema_versions','schema_migrations','migration_log');"
0
```
*Plain:* "There is no record of which database changes have been applied, which has already orphaned rows once."

### 2.6 · `OPEN` · scope `CONTAINER — agent_trajectories and the MCP tool surface`
No `tool_calls` table exists (0 rows in `sqlite_master`). Blocks 2.7.
*Plain:* "Nothing records which files an agent actually opened."

### 2.7 · `OPEN` · scope `CONTAINER — capability_claim_verifier in guardrails.py`
Item states *"Needs 2.6"* in its own body — an explicit, authoritative
dependency. A `2.7 depends_on 2.6` edge is **justified but not proposed here**,
because edge writes are outside this pass and `queue_edges` was left at 45.
*Plain:* "An agent should not be able to claim something about a file it never opened."

### 2.8 · `OPEN` · scope `CONTAINER — the gate_outcomes readers`
`gate_outcomes` is read only to display. Six loops named in the record
(correction, governance, retrieval-improvement, archive-learning,
continuity/memory, project-output); none exist. Related: 4.4.
*Plain:* "The system records whether its checks passed and then does nothing with the answer."

### 2.9 · `OPEN` · scope `REPO/CONTAINER — active_blockers and its six readers`
```
$ sqlite3 ... "SELECT COUNT(*) FROM active_blockers;"   ->  7
```
Six files read it; none blocks on it.
*Plain:* "Known blockers are written down and then nothing stops work because of them."

### 2.10 · `OPEN` · scope `CONTAINER — runtime/, excluding venv and rails`
Counts refreshed 2026-10-03 — the defect class persists and the shape of it has
moved:
```
broad `except Exception`      374   (recorded 2026-08: 445)
of those followed by `pass`    77   (recorded 2026-08:  62)
```
*Plain:* "Hundreds of places in the code swallow errors silently, so the system can fail without saying so."

### 2.11 · `OPEN` · scope `CONTAINER — prompt construction in pipeline_relay.py`
Named by the item as the common cause of 1.6 and 3.9.
*Plain:* "There is no agreement about what a task handed to an agent must contain, so prompts vary without limit."

---

## Batch 3 — Tier 2, second half (11 items)

### 2.12 · `HALF_DONE` · scope `REPO/CONTAINER — the primer documents and the runtime they assert about`
One of two named instances closed: `CLAUDE.md` corrected 2026-09-04 and the
0-byte `runtime/spine.db` decoy deleted 2026-09-05. `gateway_status_qwen` is
unchanged and **no detector exists for either**. HALF_DONE is the honest value:
the instances are half closed, the class is untouched.
*Plain:* "Documents that tell agents how the system works have gone out of date, and nothing notices when they do."

### 2.13 · `NEEDS_ERIC` · scope `UNDETERMINED — rests on build_plan_nodes, which ADR-PIPE-006 declares RETIRED`
```
$ sqlite3 ... "SELECT COUNT(*), SUM(workflow_run_id IS NULL) FROM build_plan_nodes;"
30|30
```
Investigated 2026-09-07 and recorded as a wiring gap, not a missing capability:
`runtime/db/build_plan.py:74 complete_node()` accepts and writes
`workflow_run_id`. **But ADR-PIPE-006 retires the whole mechanism.** Calling
this OPEN asserts live work on a retired table. See `BLOCKING_SET.md` §6 C1.
*Plain:* "Nothing records which planned piece of work a given run was advancing — on a planning table that has since been retired."

### 2.14 · `UNCLEAR` · scope `UNDETERMINED — the item itself flags its recognition as possibly stale`
The item says: *"Verify current state before building — a 2026-05-01 build
manifest records this as eliminated, so the recognition may be stale."*
The gate written to detect exactly this, `gate_ui_no_pipeline_bypass`, is among
2.15's never-fired scripts — so nothing has either confirmed or refuted the
elimination claim. UNCLEAR, with the verification named, is the honest value.
*Plain:* "Some operator shortcuts may still bypass the pipeline; a 2026-05 note says this was fixed and nothing has checked since."

### 2.15 · `OPEN` · scope `REPO — enforcement/mwl-proof-v2/gates/ and the gate_outcomes table`
Count refreshed: **55** gate scripts on disk as of 2026-10-03 (recorded: 51).
The never-fired subset was not re-derived — `gate_outcomes` has no `gate_name`
column under that name, so the recorded cross-reference needs its own check.
*Plain:* "Most of the safety scripts that were written have never once been run."

### 2.16 · `NEEDS_ERIC` · scope `UNDETERMINED — runtime/tier7r/, orphaned, and counted COMPLETE on the retired build_plan_nodes`
```
$ ls runtime/tier7r/*.py | wc -l                                      -> 8
$ grep -rn "tier7r" --include="*.py" runtime/abstraction/ runtime/api/ -> 0
```
The item's own stated next action is a decision: *"Decide: wire it, or record it
as superseded by pipeline_relay.py and stop counting it as complete."*
Compounded by C1.
*Plain:* "Eight modules were built as the intent-to-workflow layer, are marked complete, and nothing imports them. Wire them or retire them."

### 2.17 · `OPEN` · scope `CONTAINER — the insert at runtime/api/relay.py:663, which omits the id column`
Refreshed 2026-10-03 — the defect persists and is no longer universal:
```
$ sqlite3 ... "SELECT COUNT(*), SUM(id IS NULL), SUM(supersedes_approval_id IS NOT NULL)
               FROM eric_gate_approvals;"
29|26|0
```
26 of 29 rows still have a NULL primary key (3 newer rows, written via the CLI
path, carry ids). `supersedes_approval_id` is still set on 0 rows, so no
approval can say what it replaced.
*Plain:* "Every approval the container recorded is missing its ID, so the record cannot say which earlier decision it replaced."

### 2.18 · `OPEN` · scope `REPO/CONTAINER — the declared-versus-exists check across specs and code`
Cites `build_plan_nodes.workflow_run_id` as one instance, so C1 touches it, but
the item's substance — a gate making declarations checkable against existence —
survives the retirement independently.
*Plain:* "Things get declared in specs, look finished, and nothing ever checks whether they were built."

### 2.35 · `OPEN` · scope `REPO — the ordering in enforcement/mwl-proof-v2/gates/gate_export_agreement.sh`
The gate does compare `sha256`, `char_count` and `line_count` (lines 191-234);
the defect is that it regenerates the manifest from the broken queries *before*
comparing, so it certifies its own output. Manifest holds 13 artifacts.
*Plain:* "The check that exports are correct rebuilds them first and then compares them to themselves, so it always passes."

### 2.36 · `OPEN` · scope `CONTAINER — the truncation at pipeline_relay.py:729`
`project_brief = f.read()[:3000]` against `AGENTS.md`, now **19,525 bytes** —
so the fraction reaching an agent is ~15%, slightly worse than the 16% recorded
2026-09-07. Sections 4 and 6 (Active Decisions, Next Actions) never arrive.
*Plain:* "Agents are given only the first sixth of the project briefing they are told to follow."

### 2.37 · `OPEN` · scope `REPO — the 13 generated exports and whatever reads them`
*Plain:* "Documents are generated and maintained on every commit without anyone checking whether anything reads them."

### 2.38 · `OPEN` · scope `REPO — the survey method used before a schema change`
A rule to adopt, not a defect to repair: enumerate by the object touched, then
classify each reference as read / write / schema. Same root session as 2.35.
*Plain:* "Before changing the database, list everything that touches it by name — searching for text patterns has missed sites twice."

---

## Batch 4 — Tier 3 (13 items)

### 3.1 · `OPEN` · scope `REPO — tools/ask_history.py, host tooling`
**Live relevance:** this is the task currently parked at ERIC_GATE and the topic
of all five most recent pipeline runs, every one PENDING with 0 rounds.
Relationship observed, **not authoritative**; no edge proposed.
*Plain:* "The history search tool only does keyword matching, while the pipeline's own search also does meaning-based matching."

### 3.2 · `OPEN` · scope `REPO/HOST — the deletion paths over data/chroma_data`
A 4.9GB Chroma segment directory was deleted 2026-08-29 after an ad-hoc manual
check. Nothing but care stood between that and deleting something live.
*Plain:* "Nothing checks before something is deleted; 4.9GB went on a manual eyeball."

### 3.3 · `HALF_DONE` · scope `CONTAINER — the pre-flight in enforcement/mwl-proof-v2/run_container.sh plus the assigned kb-health repair`
An assigned repair card exists (`container-kb-health-20260917`, parent queue
item 3.3, assigned to Claude Code, verifier Codex) and work is on disk but
**uncommitted**: `runtime/chroma_health.py`, `runtime/tests/test_chroma_health.py`
and `runtime/tests/test_container_app_system_health.py` are all untracked at
HEAD. HALF_DONE reflects work started and not landed.
*Plain:* "The container barely checks its own setup before starting; a repair for this is written but not yet committed."

### 3.4 · `OPEN` · scope `REPO — logs/manifests versus runtime/manifests`
Both directories exist on disk; the "do not write there" rule is unenforced.
*Plain:* "There are two manifest folders and no rule anyone enforces about which is the real one."

### 3.5 · `OPEN` · scope `REPO — gate_export_agreement.sh, same root cause as 2.35`
*Plain:* "The export check warns about a wrong artifact count on every single commit and passes anyway."

### 3.7 · `NEEDS_ERIC` · scope `REPO — the .gitignore policy over data/`
Whether `container_sessions/` and `drive_imports/` should be versioned is a
policy call, and 3.12 shows `drive_imports/` alone is 11,763 files / 5.8GB.
*Plain:* "Two data folders are outside version control; whether they should be is a decision, not a bug."

### 3.8 · `NO_CHECK_WRITTEN` · scope `UNDETERMINED — which store is meant is not named`
`check_class` is already `NO_CHECK`. The item names no store, so no command can
settle it: the spine KB, ChromaDB and the Hermes `memories/` directory are three
different answers with three different governance questions.
*Plain:* "The memory store has no access control, audit trail or deletion policy — but the item does not say which memory store it means."

### 3.9 · `OPEN` · scope `CONTAINER — guardrails.py:3012`
`effort_metric` adjusts for brain/review1/review2 and omits draft, so draft's
prose is scored by code complexity. Named by 2.11 as a downstream effect.
*Plain:* "The drafter writes prose and is graded as if it wrote code."

### 3.10 · `OPEN` · scope `CONTAINER — the seven SKILL.md files the container agents read at runtime`
`enforcement/mwl-proof-v2/cis-pipeline-architecture/SKILL.md` plus one per role.
*Plain:* "Nobody has checked whether what the agents are told to do matches what the safety checks actually enforce."

### 3.11 · `OPEN` · scope `REPO — cis_kernel/source/architecture_maps/13_RUNTIME_TOPOLOGY.md`
Claims "Status: OPERATIONAL — populated from verified runtime truth as of
2026-05-05"; now five months stale. The item's stated action is "verify or
retire it" — both are work, so OPEN rather than NEEDS_ERIC.
*Plain:* "The document that answers 'how does the system actually run' has not been checked in five months."

### 3.12 · `NEEDS_ERIC` · scope `REPO/HOST — data/drive_imports/`
```
$ ls data/drive_imports | wc -l   ->  11763      (confirmed 2026-10-03)
```
The item concludes leaving it unindexed is **correct** on the archive's own
grounds, which makes the open part a decision to record the exclusion formally,
not work to index it.
*Plain:* "11,763 dumped files are not searchable, and the item argues that is the right answer — it needs confirming, not fixing."

### 3.24 · `NEEDS_ERIC` · scope `UNDETERMINED — the item states it is not a task`
Verbatim: *"This is recorded so it stops being an assumption. It is not a
task."* The operational spine is 6,240 rows — one tenth of one percent — inside
a 9,064,880-row database shared with the corpus. Whether to split them is an
architect question.
*Plain:* "The project's own records are a thousandth of the database they live in, shared with the knowledge corpus. Whether to separate them is an open question."

### 3.27 · `OPEN` · scope `REPO — collab_rounds.py:1091, collect_all_material.py:196-200, synthesize_full.py:79, synthesize_phased.py:60`
Three readers point at files that do not exist, and the third resolves to a
hand-written 2026-08-02 file that is not one of the 13 generated artifacts — so
nothing errors and the caller silently gets the wrong document.
*Plain:* "Four tools read files that were renamed or never existed; one quietly reads the wrong file instead of failing."

---

## Batch 5 — Tier 4 (9 items)

### 4.1 · `OPEN` · scope `REPO — the closeout hook in tools/closeout.sh`
Scope taken from the already-classified item **1.22**, whose authoritative scope
text reads: *"this is 4.1 restated with a deadline attached. Both ingest tools
exist and work; neither fires. The closeout hook is where they would fire, and
it is four lines in `tools/closeout.sh`."* That makes 1.22 the check 4.1 lacks.
*Plain:* "Both tools that file session history work, and nothing ever runs them."

### 4.2 · `OPEN` · scope `CONTAINER — container session history and the knowledge base`
*Plain:* "What the container's agents say to each other never reaches the searchable knowledge base."

### 4.3 · `NEEDS_ERIC` · scope `UNDETERMINED — the self-regulation boundary is not drawn anywhere`
The item carries its own constraint — *"Approval must never automate"* — which
is a governance boundary, not an implementation.
*Plain:* "Which decisions the system may make for itself, and which must always wait for Eric, has never been written down."

### 4.4 · `OPEN` · scope `CONTAINER — the approve/reject record and whatever would read it`
One of the six loops 2.8 names as absent.
*Plain:* "The system never learns anything from what Eric approves or rejects."

### 4.5 · `NEEDS_ERIC` · scope `REPO/HOST — data/mining_archive`
601 mined asks at roughly 8% yield for hours of local GPU. Whether that rate
justifies continuing is a cost decision only Eric can make.
*Plain:* "Mining old sessions for work items produced 601 candidates at about 8% usefulness. Worth continuing or not is a judgement call."

### 4.6 · `NEEDS_ERIC` · scope `HOST — the host Hermes profiles`
A want, not a defect, and it interacts with the recorded model reality that the
paid per-token gateways are dead.
*Plain:* "Eric wants one of the project's own agents present in these working sessions."

### 4.7 · `OPEN` · scope `UNDETERMINED — the agents, after deterministic workflows are stable`
The item carries a **recorded sequencing decision**: *"agents come after
deterministic workflows are stable."* So it is future work with its gate already
decided — OPEN, explicitly sequenced late, not NEEDS_ERIC.
*Plain:* "Giving the agents a theory of their own roles waits until the plain mechanical workflows are reliable."

### 4.8 · `OPEN` · scope `HOST — /mnt/archive`
Prose versus software split, with Troy's drive excluded.
*Plain:* "The big archive still needs splitting into writing worth keeping and software that is not."

### 4.9 · `OPEN` · scope `REPO — the documentation-gap loop, with 2.18 as its enforcement handle`
*"Undocumented configuration -> failure -> recovery -> no documentation ->
future failure."* The item names 2.18 as its handle — authoritative, stated in
the item text; no edge proposed.
*Plain:* "Fixes get made and never written down, so the same failure comes back. This list is itself evidence of it."

---

## Tally

| need_status | count | items |
|---|---|---|
| `OPEN` | 42 | 1.3–1.13, 2.2–2.11, 2.15, 2.17, 2.18, 2.35–2.38, 3.1, 3.2, 3.4, 3.5, 3.9, 3.10, 3.11, 3.27, 4.1, 4.2, 4.4, 4.7, 4.8, 4.9 |
| `NEEDS_ERIC` | 9 | 2.1, 2.13, 2.16, 3.7, 3.12, 3.24, 4.3, 4.5, 4.6 |
| `HALF_DONE` | 2 | 2.12, 3.3 |
| `DONE` | 1 | 1.2 |
| `UNCLEAR` | 1 | 2.14 |
| `NO_CHECK_WRITTEN` | 1 | 3.8 |
| **total** | **56** | |

| scope | count |
|---|---|
| `CONTAINER` | 26 |
| `REPO` | 14 |
| `UNDETERMINED` | 7 |
| `REPO/CONTAINER` | 4 |
| `REPO/HOST` | 3 |
| `HOST` | 2 |
| **total** | **56** |

No item was classified `NOT_IN_CONTAINER_PATH`. That value appears 14 times
among the already-classified rows and was considered for several items here, but
every one of these 56 either runs in the container path or is repo/host work the
container path depends on.

**Nothing proposed here adds, removes or alters a `queue_edges` row.** Four
dependencies are explicitly stated in item text and would be defensible edges
(2.7→2.6, 4.1→1.22, 4.9→2.18, 1.8→the 2026-09-04 recommendation standard); they
are reported, not written, because edge creation is outside this pass.
