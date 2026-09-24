<!-- DO NOT EDIT — generated from queue_items (the spine). -->
<!-- Change a status with tools/queue/queue_set.py; this file regenerates on commit. -->
<!-- state_revision: 423d64c651dbeab5 -->
# UNIFIED BUILD LIST — what is NOT in the code

**Date:** 2026-08-29
**Replaces:** `docs/NEXT_SESSION.md` as the working list. That file keeps its
Goal, Method and Decisions-to-Protect sections — those are not tasks.

## TWO PLANES, AND THIS LIST GOVERNS ONE — Eric, 2026-09-06

**This is a list of unimplemented needs for the CONTAINER to be work-ready.**
The development apparatus — Eric, chat Claude, Claude Code, and the three dev
agents — is a **separate plane**. It is how the container gets built; it is not
what the container is.

**Tier order governs the container plane only.** Read against that, several
items look mis-tiered and are not: **1.8, 1.10, 1.15, 1.18–1.22 and 2.25** are
apparatus items sitting in a container list. They are Tier 1 because **building**
the container blocks on them, not because the container does. A reader who
assumes one plane will conclude the tiers are wrong; the tiers are right and the
planes are two.

This is not a task. It is the frame the rest of the list is read through.

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

### WB.1 — CURRENT PRIORITY: conversation-first pipeline workbench
**Need: OPEN.** Eric prioritized this on 2026-09-17. Work through the pipeline top to bottom. This item precedes previous tier ordering for the workbench build; existing tasks remain intact.

**Goal:** A fresh, simple iPad-friendly work surface where Eric starts a project, talks with Braingate, and sees and interacts with each stage. Retire experimental pages from active use; preserve them as reference. No decorative working-state claims.

**Requirements recovered:** queue item 1.10 and docs/CIS_PIPELINE_VISIBLE_PORTAL_SPEC.md (historical draft: use behavioral requirements, not its unconfirmed layout); KB rows 300459 and 889678 (transparency/work surface); Braingate references 753852/753878. Eric's current instructions override the old interface experiments.

**Ordered build and acceptance:**
1. Project + conversation: create a named project without filesystem knowledge; persist conversation server-side; reconnect after reload; send to the real Braingate adapter; show explicit provider failure and prevent duplicate submissions. Show retrieved sources and a bounded context window. This is the current implementation slice.
2. Clarified direction: editable statement, explicit confirmation recorded separately from execution authorization; subsequent conversation invalidates stale confirmation. Prove conversation alone cannot start work.
3. Reviewed work card: show proposed scope, dependencies, rationale and acceptance evidence; expose objections, revisions and Eric's decision before dispatch. Connect only after backend behavior is verified.
4. Execution visibility: display actual stage/actor/events, tool/gate outcomes, blockers and user requests. Wire pause/redirect/resume with acknowledgements; never label an interjection as a pause.
5. Verification + outcome: implementation claims and independent evidence side-by-side in plain language; unresolved objections stay visible; persist accepted outcome and next recommendation.
6. Recovery: reload/restart resumes the right project/run with no duplicate execution; iPad touch/keyboard and narrow-screen checks; distinguish disconnected, idle, blocked and completed states.

**Scope rule:** Complete one connected slice at a time. No new agent orchestration, knowledge mining, health repair, or legacy dashboard renovation under this card. Existing model/provider funding can block real responses; show it honestly. No pipeline dispatch merely from the chat UI.

**Retirement:** previous active React source/public/build preserved at data/ui_archive/workbench-20260917. Old host-only pages remain historical and are not served by the new workbench entry point.


#### 2026-09-19 — Proposed host-side development continuity step

**Status: Corrected development scope recorded at Eric’s request; mechanism not yet implemented or verified. This correction does not dispatch agents or resume paused work.** Recorded from the Codex conversation investigating PROJECT-KNOWLEDGE-MODEL-RESEARCH-HANDOFF.md and Eric's subsequent continuity questions. Preserve WB.1 as the parent outcome: a usable conversation-first Braingate/card-factory workbench. Auth implementation and C4 activation remain paused. Historical card text below is not renewed authorization.

**Eric's current problem (verbatim excerpts):** “What is needed is to somehow turn the kb/db into the queue.” “Right now these latest insights a those from earlier in this session are only in this session chat.” “so what mechanism could support that in the un contained env in order to build the contained env?”

**Eric’s scope corrections (verbatim):** “Your framing includes reviewers, this mechanism we are trying to build is for Claude and Chatgtp, still the external developers of the pipeline where the reviewers live.” “Make the corrections so we can implement and return to the work of building on the interfaces connection to braingate and the card factory, followed by developing the rest of the pipeline using the kb instead of relying on my memory.” His preceding correction identifies stale information when activity is not recorded until closeout. Therefore updates during work are required; startup and closeout are recovery/completeness checks, not the publication mechanism.

**Recovered findings, not new implementation claims:** Projects and knowledge have overlapping, evolving roles. Original evidence supports reusable references, unaffiliated knowledge, promotion/demotion without knowledge loss, project branching/merging, and output feedback. Single-project permission inheritance is not an approved consequence. Private/shared multi-user access must be reconciled with these relationships before resuming auth; transport and app authorization are distinct. Evidence: KB 41270 (Eric requests demotion), 41971–41979 (DAM/promotion/demotion), 48639–48644 (project evolution), 48687–48698 (Blender production/knowledge feedback), 694535–694536 (Eric's life/creation intent), 694558–694563 (concept spines), 530637–530642 (SWA overlapping workflow relationships). Original workbook /mnt/archive/WIAS/0admin/WIAS Project Manager.xlsx, projects rows 4–7, repeats idea/research references across distinct project IDs. Cardinality, identity-through-promotion, ownership/grant inheritance, derivative access and revocation remain unresolved. ADR-SEED-010 concerns per-repository runtime spines; its relationship to application-level sharing requires explicit reconciliation.

**Existing lineage to recover before building:** docs/SPEC_KNOWLEDGE_SURFACE_AGENT.md and docs/SPEC_INTENTION_DRIVEN_CIS_KNOWLEDGE_SURFACE.md (historical proposals); docs/PROPOSAL_SESSION_TO_SPINE_WRITE_PATH.md (historical proposal identifying session/context propagation failure); docs/cards/CARD_0.1_inventory_prior_mining_(INVESTIGATE).md; CARD_2.2_PASS_2:_reasoning_that_implies_a_task_(SEMANTIC).md; CARD_4.2_merge_against_the_build_list_(BUILD).md; CARD_5.1_one_card_per_task_(BUILD).md. Existing tools/index_themes_to_sources.py and tools/link_cards_to_themes.py are leads; their output coverage/usefulness has not been verified. Do not rerun mining by default or execute old proposed SQL.

**Observed integration gap (source inspection, not live audit):** runtime/workbench_app.py searches current message terms, takes five FTS results and sends 200 characters per hit; returns source category without stable message IDs and converts search errors to no results. runtime/card_factory_app.py supplies ask plus optional proposal fields to the bounded generator. cards/GENERATOR_PROMPT.txt and tools/card_gate.py constrain direct asks and quotations; they do not establish reconciliation with prior reasoning. Implementation read-scope restrictions mean recovery belongs before card finalization.

**Bounded next development task:** Establish host-side continuity for Claude Code and ChatGPT/Codex as the external developers building CIS. This mechanism is outside the unfinished container and independent of its internal reviewers, gateways and activation. It connects the existing queue, original KB evidence and a continuously maintained development record to the external developers’ actual working sessions. Claude implements; ChatGPT/Codex scopes, coordinates and independently evaluates evidence within the authorized workflow. Eric directs outcomes and resolves genuine product choices; he must not supply forgotten search terms, relay accessible records, or manually reconstruct dependencies.

**Reuse and authority:** First identify the active queue reader/writer, applicable development-record stores and existing session-to-KB import path. Retain this queue as task authority; reuse existing retrieval/source readers and recording paths where adequate. Do not introduce a second queue or assume historical scripts are working integrations. Task-specific context packets are derived views, tied to source and queue/card revisions. Label Eric’s instructions, original discussion, recovered evidence, model proposals, accepted decisions and verified implementation separately. Preserve source excerpts and reasoning, not summaries alone. Persist full exchanges through an identified import path with source identity, authorship and deduplication; identify unavailable transcripts honestly rather than claiming that a summary or this queue entry imported the chat.

**During-work publication:** Record consequential discoveries, changed requirements, proposals/decisions, card revisions, implementation progress/evidence, objections and unresolved blockers when they arise, before dependent work proceeds. Include actor, affected task, source/evidence references and revision. Represent unfinished, unverified and superseded work explicitly. A model’s proposed interpretation is not an accepted decision. Both external developers must be able to discover changes without waiting for session closeout or asking Eric to relay them. This is event-based publication, not capture of every keystroke or a claim of instantaneous visibility.

**Use and freshness:** Before either external developer plans, implements or evaluates work, load the current parent outcome, exact task, protected decisions, blockers, relevant original KB evidence and return point. Bind the task/handoff and any evaluation to the revisions actually read. If relevant shared information changes during a task, expose the change and reconcile its impact before the result is accepted or dependent work proceeds; do not silently reuse an outdated assessment. Concurrent updates must preserve both writers’ contributions, identify conflicts, and avoid last-writer loss. A missing or failed publication/read must be visible, not treated as an up-to-date record. These checks concern the external development workflow, not implementation of internal pipeline reviewer behavior.

**KB recovery and scope continuity:** At task preparation and consequential design changes, derive bounded searches from the intended behavior and affected concepts, follow prior terminology and references to original discussions, and reconcile preserve/adapt/conflict/unknown. Classify discoveries as blockers, constraints within the active task, or later work with a reason. Discovery alone neither makes a prerequisite nor authorizes implementation. Keep the original WB.1 outcome visible throughout. Startup restores the latest shared record; closeout checks that events and evidence were captured and the next permitted action is recoverable. Neither may defer during-work updates.

**Control boundary:** Standing instructions guide direct interactive sessions. Host preparation/publication/freshness checks can enforce requirements for launches and handoffs routed through them; they cannot guarantee compliance by unrestricted agents outside that path or prove semantic completeness. Inspect the actual external Codex/Claude launch and session interfaces before choosing wiring; do not assume one model can push into every active conversation. Changes may be pulled at defined work boundaries, provided freshness is checked before consequential dependent action. Use existing subscription-backed sessions; no new paid gateway, automatic dispatch, background mining or internal reviewer integration is implied. Do not hand-edit generated AGENTS.md; use its source if a change is subsequently required and authorized.

**Acceptance:**
- With no inherited chat, an external developer recovers this investigation, WB.1 as parent, the auth/C4 pause, active task and original evidence without Eric retelling them.
- While the originating session remains open and no closeout has occurred, it records a consequential change; the other external developer’s next preparation/freshness check receives that change with its revision and source.
- A task/evaluation begun on an earlier relevant revision cannot authorize dependent work until the later change is reconciled. Unrelated updates do not force needless restarts.
- Concurrent updates retain both contributions or surface an explicit conflict; publication/retrieval failure is distinct from an empty result or a current record.
- A representative remote-access request retrieves Cloudflare and studio/field distinctions without product names supplied by Eric. Recovered proposals remain distinguishable from decisions and live implementation.
- A new discovery is recorded and classified without silently replacing the active objective. Full source reasoning remains accessible; generated context is traceable to original evidence.
- Startup and closeout recover/check the same during-work record. Closeout is unnecessary for the cross-session visibility test.

**Stop and return:** Once the bounded external-development mechanism passes these checks, return to the existing WB.1 interface connection to Braingate and the card factory, using its current implementation evidence and the KB to identify the next unfinished slice. Continue subsequent pipeline development through the same mechanism and existing queue. Do not redo verified interface work or expand this continuity step into a universal knowledge platform. Auth implementation and C4 activation remain paused pending their own reconciled scope and authorization; returning to WB.1 does not bypass those pauses. No corpus-wide re-mining, new queue, internal reviewer changes, or assertion that all historical requirements are resolved.

#### Active implementation card: WB.1A
Assigned to Claude Code. Full dispatch card: `data/agent_handoffs/WB-1A-workbench/CARD.md`. Completion claims: `completion.json`; raw evidence: `evidence.md`; independent review: `verification.json` in that same directory. No completion is accepted from self-report.

# WB.1A — Fresh workbench: project and Braingate conversation
Parent and priority: WB.1, first in the existing queue.
Owner: Claude Code implements. Codex acts as Braingate and independent reviewer.
Status: ASSIGNED. No self-certification of completion.

## Eric's instruction
Retire previous experimental UI from active use and start a fresh simplified workbench where he can begin a project and converse with Braingate. Build pipeline functionality from beginning to end, exposing its actual behavior and allowing interaction at each step. Keep token use focused. Claude implements; Codex scopes, coordinates, and verifies. Eric must not relay messages between agents.

## This card's deliverable
One simple, usable, iPad-friendly workbench page with:
- Named project creation without requiring repository paths or other technical choices. Persist projects server-side; distinguish planning projects from provisioned application repositories.
- A project-scoped conversation with the actual configured Brain/Braingate gateway. Persist messages and replies across reloads and project switches. Show pending, failed, interrupted and completed response states honestly; prevent accidental duplicate submission. Never present provider failure text as a successful answer.
- A compact context panel showing the source excerpts actually sent with the request, their available stable identifiers and retrieval limitations. Reuse existing KB facilities without a corpus mining/reindexing project. Use existing secret redaction before sources/results reach the page.
- A clear current stage: exploration. Keep execution/approval/agent work visibly unconnected until implemented; no placeholder progress, invented evidence, or implicit dispatch. No start-pipeline controls in this slice. Braingate's role is clarification, not execution. Inspect and report the existing gateway's tool permissions; a prompt alone is not a deterministic execution gate. Do not claim containment that is not enforced.
- A readable conversation-first layout, touch-sized controls, responsive behavior, keyboard submission, loading/error states, and reload recovery. Keep error drafts recoverable. Avoid decorative dashboards and giant technical panels.
- Optional small editable direction note if straightforward; do not add an authorization workflow or mark an intent approved without a durable, reviewed gate.

## Starting state — checked by Codex
Repo /mnt/projects/cis is mounted at /workspace/cis inside cis-pipeline. The old built UI is still serving from runtime/ui/dist; source directory runtime/ui/src is currently EMPTY because retirement/archive succeeded before implementation was interrupted. Old public/cis-container-dashboard.html was also removed. Complete original src/public/dist/index.html and entrypoint backups are at data/ui_archive/workbench-20260917/runtime/ and .../enforcement/ respectively. Restore/reuse build plumbing as needed but do not reuse the experimental screen design.
Neither runtime/workbench_app.py nor runtime/schema/migrations/0035_workbench.sql exists; the interrupted implementation command did not create them. Independently check schema before choosing a migration number.
Existing runtime/ui has React/Vite package.json, package-lock.json, vite.config.js, node_modules. Use installed dependencies; avoid a framework migration.
Existing brain/chat endpoint: runtime/api/relay.py around 1340, returns brain_response and kb_context. The old UI incorrectly expected response/references. Existing brain/start is NOT a confirmed-intent gate and must not be wired into this page.
The old project registration API requires filesystem paths and uses INSERT OR REPLACE. Do not expose that destructive/upsert contract as new-project creation or fabricate repo paths. Implement a small durable planning-project/conversation mapping with explicit additive migration if needed; do not refactor the whole spine.
The old gateway uses port 8644. Model API credits have previously been exhausted. Implement truthful unavailable/error behavior; do not substitute a fake model or silently switch provider. No paid-model calls in your automated tests.

## Scope and reference budget
Read CLAUDE.md/AGENTS.md for applicable instructions, but Eric's current request supersedes old instructions that would make him relay work or stop after each file write. Complete this bounded card.
Relevant behavioral references: queue item 1.10; docs/CIS_PIPELINE_VISIBLE_PORTAL_SPEC.md is a historical DRAFT, not an approved layout. Requirements: stay in conversation; clarify before execution; eventually show stages, objections, gates and evidence; allow intervention. KB source IDs 300459 and 889678 support transparency/work-surface intent. Do not re-mine histories or investigate other queue items.
Allowed implementation scope: runtime/ui; a narrowly scoped workbench server/API module; an additive schema migration and necessary tests; minimal serving/entrypoint wiring staged for review. Do not modify pipeline_relay.py, change mounts, run the pipeline, restart/recreate the live container, touch secrets, fix health probes, commit/push, or perform unrelated cleanup. No subagents.
Preserve unrelated dirty files. Pending unaccepted health changes already exist in runtime/container_app.py and runtime/chroma_health.py; do not accidentally deploy or overwrite them. Prefer an isolated workbench entrypoint or propose the minimal activation change for Codex review. Old host-only UI experiments may remain historical; ensure the proposed active workbench serves none of them. Archive before overwriting existing files.

## Acceptance evidence
1. Build succeeds using existing UI tooling.
2. Tests using a temporary database and mock gateway show create/reopen project, persistence, isolation between two projects, successful reply/context rendering contract, provider failure, malformed input, and duplicate-send behavior. No tests mutate the real KB or call paid models.
3. Show that this workbench exposes no pipeline-start action. Explain any remaining gateway-side execution-permission limitation explicitly.
4. A browser check if locally available, otherwise an honest untested label: desktop and iPad-sized page, project creation, sending, failure display, reload. Do not install a browser stack just to do this.
5. Record exact commands, exit codes, raw output and changed files. State what is mock-tested versus live-tested. Do not claim the running service has loaded staged changes.
6. Provide a short activation/rollback procedure accounting for the actual live container and pending unrelated edits; Codex will review before activation. Keep the broader WB.1 item open.

## Evidence handoff (no user copy/paste)
Shared directory: /mnt/projects/cis/data/agent_handoffs/WB-1A-workbench (container /workspace/cis/data/agent_handoffs/WB-1A-workbench).
Save source preimages under backups/. Write evidence.md with implementation claims, commands/results and limitations. Write completion.json LAST: card_id='WB.1A', status='READY_FOR_VERIFICATION' or 'BLOCKED', changed_files, tests, evidence_path, remaining_limitations, activation_steps. Never label your own work VERIFIED. If blocked, preserve progress and report the exact blocker; do not expand scope.
Your final response is automatically captured here. Codex reads this location directly.

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

**CONDITIONALLY DONE — correct for the BATCH model only. 2026-09-06.** Every
assumption below is right for a scheduled bulk ingest and inverts under
continuous per-turn writes:

- **Readers give up after 5s and degrade to keyword.** Sound when a write is a
  rare 40-minute rebuild. Under continuous writes, degradation becomes the
  normal case rather than the exception.
- **Writers raise rather than proceed.** Sound when the caller is a batch job
  that can be re-run. Under continuous writes the caller is a live turn, so a
  refused write means a record is **dropped rather than delayed**.
- **Writers hold the lock for a whole run.** Sized for a rebuild that must not
  be seen half-built. For a per-turn append it holds a global exclusive lock for
  a single row.

Nothing here is wrong and nothing needs reverting. The lock stays as the correct
answer for batch ingest. **Real-time writing needs a different contract, and that
is 1.26** — which modifies this lock rather than replacing it.

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


### 0.6 ARMING A GUARDRAIL NEEDS AN OVERRIDE POLICY THAT DOES NOT EXIST

2.1 reads as "arm the 23 advisory guardrails." Run
`run-e70293544935a92e-1787973534` is the counterexample, and it is already in
this list: `intent_drift` FAILED twice — 0.63 DIVERGED, then 0.42
SIGNIFICANT_DRIFT — and it was **right**. The run deliberately deviated from a
spec whose own verification criteria would have certified a falsehood. Had
`intent_drift` been in BLOCK mode, it would have killed the correct answer.

**So arming is not a switch.** It requires a stated policy for when a guardrail
that fires CORRECTLY should be overridden, and by whom. Nothing on this list
defines one. 0.4's open fail-mode half is where that policy belongs: it is the
same question — what happens when the gate says no — asked of a gate that is
working rather than one that has failed.

**Scope:** CONTAINER — the guardrail modes and the override plane are both
repo-level and apply to both pipelines.

**Need:** OPEN — no override policy exists in the code, in `docs/`, or on this
list.

**Ordering:** this is a **prerequisite to 2.1**, not a sibling. Arming the
guardrails before the policy exists means the first correct block with no
sanctioned way past it is the v2.0 deadlock again, in a system that today avoids
that outcome only because it fails open.

**Related:** 0.4 (the override plane is built and proven; the fail-mode half is
where this policy lands), 2.1 (the item this gates).


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
4. Add the independent verifier. 1.1 is DONE (run-e70293544935a92e-1787973534, 2026-08-30) — this step is unblocked.
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

**SUPERSEDED IN FRAMING, 2026-09-04 — see `docs/DECISIONS/2026-09-04_recommendation_standard.md`.**
This item says: give Eric options with consequences. **That now stands as the
floor, not the target.** The standard is that agents **recommend** rather than
interrogate — an informed, researched recommendation with the evidence and the
reasoning, and a choice surfaced only where the evidence genuinely leaves one
open. Asking Eric what he intends fails twice over: he is not a coder, so his
intentions are not stated in engineering terms, and the agents are stateless, so
nothing carries the answer to the next call. The decision record carries the
other half — the recommendation must be checked against Eric's recorded method
first, because a model asked for "best practice" reaches for enterprise defaults,
and this is not a standard application or a standard development process. Read
that file before building anything against this item.

**The rule, stated so it can be checked:** any output that asks Eric to decide
must carry, for each option, (a) what it means in plain language, (b) the
evidence behind it, (c) what goes right if chosen, (d) what goes wrong. An open
technical question with no options is a defect, not a request. Under the 2026-09-04
standard, an output that stops at (a)–(d) without naming which option it would
take and why is also incomplete.

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

**THE DESIGN RECORD — Eric, hermes_v4pro, 2026-07-03.** Recovered 2026-09-04 by the P7-design mining pass, two months before this item was written. Verbatim, typos his:

> this is not correct drafter has to stop for clarity and understanding check. then when approved it writes the spec and passes it to the reviewers. the pass is the only thing done with out waiting. the rreviewers have to stop to deliberate and reconcile any differences, that is presented to the user again for clarity, understanding and alignment check. if ok'ed it is returned to drafter for refinement or sent to the implementor. the implementor's work is quality checked and verified. that is a stop where the user needs to be observing and making sure that what is being done is aligned with goal and intention.

**For this item:** *"drafter has to stop for clarity and understanding check"* — before it writes anything. This item was framed as reviewing the CARD before it runs; the record asks for the same thing one step earlier and inside the pipeline, an understanding check the drafter itself must pass before drafting. The card-review design is the right shape; it was arrived at independently, and the record specifies where it belongs.

**Read the whole excerpt against what runs.** It names four stops. The pipeline implements one — the Eric Gate — and the single step Eric said should proceed *without* waiting ("the pass is the only thing done with out waiting") is the only one built. That inversion is the finding, and it is the shared root of 1.18, 1.19, 1.21 and 2.3.

### 1.19 One-shot critique loses what multi-round exchange catches

`advisor_review.sh` gives the reviewer one look and no reply. Eric, 2026-09-02: "them not looking at each other's responses is not how you were catching additional issues through me transporting."

Evidence from this week, all of it from exchanges rather than verdicts: the three-enforcement-layer confusion took two rounds to resolve, VM-versus-container took three, and the `wc -l` off-by-one surfaced only because a number was questioned and the raw output came back. A single verdict would have carried all three errors forward.

Fix: Claude Code may answer an objection with evidence; the reviewer withdraws it or holds it. Capped at two rounds, written to `reviews/` as a thread rather than a file per verdict. No vote and no arbiter — the exchange is the product, not a score derived from it. This is why `deliberation_rounds` exists in the spine rather than a single verdict field.

**Scope:** CONTAINER — `tools/advisor_review.sh` writes one response file per packet and exits. A thread needs the packet, the objection, the answer and the withdrawal in one artifact.

**Need:** OPEN — verified in the code this session: the script posts once, writes `reviews/done/<id>.response.md`, and has no reply path.

**The one check that settles it:** re-run a review where the advisor made a factually wrong objection, answer it with evidence, and see whether the withdrawal changes the finding set. On 2026-09-02 the advisor claimed three existing backups did not exist; one round with the `ls` output would have retracted it.

**Related:** 2.7's absence-from-outside-scope variant is the failure a reply round closes. Needs 1.20 to be worth running twice.

**THE DESIGN RECORD — Eric, hermes_v4pro, 2026-07-03.** Recovered 2026-09-04 by the P7-design mining pass, two months before this item was written. Verbatim, typos his:

> this is not correct drafter has to stop for clarity and understanding check. then when approved it writes the spec and passes it to the reviewers. the pass is the only thing done with out waiting. the rreviewers have to stop to deliberate and reconcile any differences, that is presented to the user again for clarity, understanding and alignment check. if ok'ed it is returned to drafter for refinement or sent to the implementor. the implementor's work is quality checked and verified. that is a stop where the user needs to be observing and making sure that what is being done is aligned with goal and intention.

**For this item:** *"the rreviewers have to stop to deliberate and reconcile any differences"* — this is the exchange, specified. Not a second opinion collected in parallel, but two reviewers stopping, deliberating, and **reconciling**, with the reconciled result presented to Eric. This item argues one-shot critique loses what exchange catches; the record already required exchange, and required it between the reviewers rather than between an advisor and a packet.

**One consequence worth carrying:** the record says the reconciliation output goes to the user "for clarity, understanding and alignment check". So the exchange this item builds is not finished when the two agree — agreement is the input to a human check, not a substitute for one.

### 1.20 Add Qwen (8643) as technical evaluator

Eric, 2026-09-02: he cannot evaluate code or technical choices. That is the gap GLM's objections do not close — GLM critiques the result packet, not the engineering. Every technical decision this session was made and checked by the same model family.

Three roles, three lineages: Claude Code builds, GLM (review2, 8647) objects to the result, Qwen (review1, 8643) evaluates the code and the method. Qwen leads on agentic coding benchmarks and is furthest from Claude's lineage, which is the point — 1.19 buys nothing if both reviewers share a blind spot (failure mode 16).

Qwen needs the same advisor treatment review2 got: skills disabled, toolsets trimmed, the scope line, and `mcp_servers.cis-knowledge.enabled: false` so it carries no `cis_dispatch_*` tools. Measured, not assumed — review1's loadout has never been audited, and `platform_toolsets` is unset in all six configs.

**Scope — REPOINTED 2026-09-07. It is `evaluator` on 8650, not review1 on 8643.**
This item was written 2026-09-02, when review1 was the only Qwen in the system and
borrowing it looked like the only route. The `evaluator` profile
(`enforcement/mwl-proof-v2/profiles/evaluator.yaml`) was created 2026-09-03 for
exactly this purpose: `qwen/qwen3.7-max` on port 8650, already at the advisor
loadout — 79 skills disabled, `platform_toolsets: []`, `cis-knowledge` disabled so
it carries no `cis_dispatch_*` tools (2.23). `advisor_review.sh` takes
`CIS_ADVISOR_PROFILE` and `CIS_ADVISOR_PORT`, so nothing needed building.

**DO NOT TRIM review1. This is 1.17 repeated, and it was proposed on 2026-09-07.**
3.22 gave review1 `file, terminal, code_execution` on measured evidence — **271
tool calls, the largest sample of any role** (terminal 196, read_file 57,
execute_code 13, search_files 5). review1 is a live participant in every pipeline
dual review. Stripping it to `[]` would create a *second* zero-tool Qwen advisor
while destroying the loadout its own history justifies — borrowing a pipeline
reviewer as an advisor, which is precisely what 1.17 cost.

**Need: HALF DONE 2026-09-07. The trim half never needed doing; the measurement is
done. What remains is the judgement.**

**THE CHECK RAN — 2026-09-07.** The identical packet (sha256 `a38ed0b8…`, verified
byte-identical, same recorded `packet_hash` on both rows) went to GLM
(`advisor`, 8649) and Qwen (`evaluator`, 8650). Both at the advisor loadout, both
round 1, no reply round.

| | GLM (advisor, 8649) | Qwen (evaluator, 8650) |
|---|---|---|
| prompt_tokens | 1,406 | 1,497 |
| completion_tokens | 2,253 | 1,355 |

**FINDINGS ONLY QWEN RAISED — 2:**
1. **The rebuilt table has no `REFERENCES projects(id)`, so `pragma
   foreign_key_check` is vacuous evidence.** Verbatim: *"the join returning 30
   rows proves the values match, not that referential integrity is enforced…
   `foreign_key_check` returns empty because there is no foreign key to check."*
   **Verified:** `pragma foreign_key_list(build_plan_nodes)` returns one row, and
   it is `workflow_run_id -> workflow_runs`. There is no FK on `project_id`. The
   card used `foreign_key_check` as proof of a thing it cannot see.
2. **Indexes and triggers are silently dropped by DROP + RENAME.** **Verified:**
   `idx_bpn_project_status` and `idx_bpn_project_sequence` exist on the table and
   the card recreated neither.

**FINDINGS ONLY GLM RAISED — 5:** the `DEFAULT 'CIS'` is never verified (the
card's central claim, untested by its own EXPECT); column-order misalignment
silently corrupting `node_label`/`tier`; the `UNIQUE` constraint claimed but
unchecked; the backup step being literal pseudo-code that produces nothing; and
no check that 0021 does not collide with an existing migration. A sixth —
`workflow_runs` still broken — was **WITHDRAWN** in round 2 against `select`
output showing 105 rows, all `'cis'`, zero uppercase.

**THE NUMBER 1.20 ASKS FOR: 2.** The criterion is that a zero means the second
lineage is not paying for itself. It is not zero. Recorded without argument
either way — the judgement is Eric's.

**The one check that settles it — SATISFIED.** Give both advisors the same packet
and count the findings only one raised. Done above. Re-run it on a second packet
before treating one sample as a pattern: two different models will differ on any
single document, and one comparison does not establish that they differ
*usefully* and repeatably.

**SECOND PACKET — 2026-09-07.** `reviews/pending/migration-0030-r2.md`, sha256
`4419478f6a20df0d…`, same recorded `packet_hash` on both rows, both MATCH. GLM
(`advisor`, 8649) prompt 3,626 / completion 11,393; Qwen (`evaluator`, 8650)
prompt 3,778 / completion 2,307.

| | GLM only | Qwen only | Both |
|---|---|---|---|
| findings | 3 | 1 | 3 |

GLM alone: `NOT NULL` on `project_id` untested; `AUTOINCREMENT` untested; and it
asked for the collation of `projects.id`, saying it could not assess the FK
without it — a request for evidence rather than a finding, and the right move.
Qwen alone: **the `ON DELETE CASCADE` is never tested.** Shared: index
definitions, non-`project_id` column corruption, the `status` CHECK.

**Qwen's single finding was the one that mattered.** It became check 12, and
check 12 is the only one that could have caught the rebuild silently breaking the
dependency graph while all fourteen others passed — the exact hazard 0030 was
shaped to avoid. A 3–1 split understates it: the count is not the measure, and
this is the second time the *lower*-scoring lineage found the more serious thing.

**Two packets. The split is holding and two is not a pattern.** Packet 1 was 2–5,
packet 2 was 1–3, and in both the smaller number was the more consequential. That
is suggestive and nothing more. A third packet is worth running before this is
treated as settled.

**A third, partial data point, recorded because it is about the harness rather
than the models.** Revision 1 of the 0030 packet went to both lineages and **GLM
did not answer** — the gateway returned HTTP 200 carrying
`{"error":{"code":"agent_incomplete"}}` after four continuation attempts. The
cause was `CIS_ADVISOR_MAX_TOKENS` defaulting to 2,000 against a reply that
needed 11,393. This is **1.11 recurring**: a gateway laundering an upstream
failure into a success status. The script's guard checked the `docker exec` exit
code and the empty string, and both passed. `advisor_review.sh` now inspects the
response **body** for an `error` key or absent `choices`, counts that lineage as
failed, continues to the next, and exits non-zero with a warning against reading
a single-lineage result as a dual review. Guarding the transport is not guarding
the result.

**EVERY COUNT ABOVE WAS COLLECTED UNDER A MISLABELED PROMPT — recorded 2026-09-09.**
`advisor_review.sh`'s scope line opened *"You are reviewing a result packet"*
from the day the script was created. Every packet ever sent under it has been a
**proposal** — migration 0030 r1, migration 0030 r2, and both reviews of the
3.21 card, which is all three of the divergence measurements recorded above.
Corrected 2026-09-09: round 1 now says *"proposal packet — work that has NOT
been done yet"*, and the result wording moved to round 3, where a result is
actually what arrives.

**The counts are not retracted.** The findings were substantively about the
right things — the missing FK, the untested CASCADE, the unverified DEFAULT —
and none of them depended on the label. What cannot be claimed is that they were
collected under the prompt this item assumes. A model told it is auditing
finished work may weigh differently than one told it is auditing a plan, and
that difference is unmeasured in both directions. **Recorded beside the counts,
not in place of them.** The third packet this item asks for will be the first
taken under the corrected label, which makes it worth more than a tiebreaker.

**Related:** 3.22 is the measurement this depends on. 2.23 is why the MCP server must be disabled rather than merely untooled. 2.41 (the reviews of anything built on a changed assumption are void, which is how the mislabel survived three packets).
### 1.21 The loop must stop and wait, not run past Eric

Eric, 2026-09-02: "having the loop waiting on my approval is a lot better for me than physically being locked to a screen watching, reading, understanding and copy pasting every exchange."

This is not a kill switch, and the distinction matters. On 2026-08-31 the drafter ignored nine minutes of interrupts because it was mid-call and working — nothing was broken, and a stop button would have solved nothing. The requirement is that the loop reaches a state where it is WAITING, so nothing is lost while he is away and a wrong direction stops early instead of after four cards.

PAUSE POINTS: between queue items, and before any card that writes. A read-only card does not need him; a card editing `runtime/abstraction/pipeline_relay.py` does. That is the consequence-class split already sketched in 1.10 — the same read/write line, applied to when the loop asks rather than to what a gate blocks.

**Scope:** UNDETERMINED — no loop runner exists yet. Whether the waiting state lives in a script, in the spine, or in the relay is not settled, and choosing wrong here is expensive.

**Need:** OPEN — today the loop is Eric issuing one card per turn, which is a pause point at every step and the very hand-carrying this is meant to remove. The failure mode being designed against is the opposite one: a loop that runs four cards past a wrong turn.

**The one check that settles it:** decide where the waiting state lives before building it — a script that blocks, or a queue row the loop polls. The second survives a restart; the first does not.

**Related:** 1.14 (stop button) is the different problem — that one interrupts work in flight, this one declines to start it. 2.25 depends on this: a feed with no waiting loop is a notification stream.

**THE DESIGN RECORD — Eric, hermes_v4pro, 2026-07-03.** Recovered 2026-09-04 by the P7-design mining pass, two months before this item was written. Verbatim, typos his:

> this is not correct drafter has to stop for clarity and understanding check. then when approved it writes the spec and passes it to the reviewers. the pass is the only thing done with out waiting. the rreviewers have to stop to deliberate and reconcile any differences, that is presented to the user again for clarity, understanding and alignment check. if ok'ed it is returned to drafter for refinement or sent to the implementor. the implementor's work is quality checked and verified. that is a stop where the user needs to be observing and making sure that what is being done is aligned with goal and intention.

**For this item, the excerpt settles the open question.** This item records that where the waiting state lives is undecided and "choosing wrong here is expensive". The record does not answer where it lives, but it does answer **how many there are and where they fall**, which is the harder half:

1. drafter stops before writing the spec — clarity and understanding check
2. reviewers stop to deliberate and reconcile with each other
3. the reconciled result stops for Eric — clarity, understanding, alignment
4. the implementer's work stops for verification, "where the user needs to be observing"

And it names the one place that must NOT wait: *"the pass is the only thing done with out waiting"* — the hand-off from drafter to reviewers.

**This item's PAUSE POINTS were drawn as "between queue items, and before any card that writes."** That is a read/write consequence split, invented here. The record's split is different and better founded: pauses fall wherever **understanding could have diverged**, not wherever a write could occur. A read-only card that misunderstands the intent is exactly as expensive as a write, and it is what four attempts at the ask_history intent produced.

**Today the pipeline implements one of the four**, the Eric Gate, and implements the one step Eric said should not wait as its only synchronous behaviour.

### 1.22 Nothing the loop produces reaches the KB — BLOCKS 1.18 through 1.21 and 2.25

As designed, the loop captures nothing. Verified 2026-09-02:

- `tools/catalog/ingest_sessions.py` scans `~/.hermes-*/sessions/session_*.json`. A direct API call to a gateway writes no session file, so the advisor exchanges are invisible to it.
- `reviews/` is files on disk reaching no index. The first two exist as of this session and are tracked in git and nowhere else.
- Telegram replies (2.25) reach nothing at all.
- `grep -c ingest tools/closeout.sh` returns **0**. Closeout commits code and never ingests knowledge.

ERIC'S INPUTS ARE THE POINT. Everything the 2026-08/09 mining recovered came from him reframing — VM-versus-container, the on-the-fly documents, rejecting the sampling. `docs/NEXT_SESSION.md` records why: the corpus is the counterweight to enterprise bias and the only one, because nobody else wrote this method down. A loop that produces those reframings and loses them rebuilds the same archaeology in three months, and the mining pass that recovered 4,479 candidates is the measure of what that costs.

Three things need capturing: the review threads in `reviews/`; Eric's redirects WITH what they redirected, since an objection separated from what it changed is his own stated failure; and Claude Code's sessions, which `tools/ingest_claude_code_sessions.py` handles and nothing triggers.

**Scope:** REPO — this is 4.1 restated with a deadline attached. Both ingest tools exist and work; neither fires. The closeout hook is where they would fire, and it is four lines in `tools/closeout.sh`.

**Need: HALF DONE 2026-09-05 — the session-ingest half is wired.** Commit
`e90e598` added step 1c to `tools/closeout.sh`; `grep -c ingest tools/closeout.sh`
now returns **6**, where the item was written when it returned 0. The first real
run ingested **+2,260 rows**, of which **514 are this session's own Claude Code
transcript** — the session that recovered a lost design record *because* Claude
Code transcripts reached no index put itself into the index.

**What remains open is real-time availability, not ingest wiring.** Closeout runs
at session end, so a fact recorded at 10:00 is unavailable to an agent at 10:05
and becomes available only after the session closes. Stateless agents inside one
session still cannot see each other's output. That is a different problem from
the one this item was written about, and it is 1.26.

The original second half also stands: a direct API call to a gateway writes no
session file, so advisor exchanges remain invisible to `ingest_sessions.py`. That
is not a wiring problem either — it needs the loop to write its own record.

**DO NOT READ 2026-09-07 AS CLOSING THAT HALF — corrected 2026-09-08.** The
evidence looks like closure and is not. Closeout ingested **474 Claude Code rows
on 2026-09-07**, and both advisor threads from that day did land in the KB:
`migration-0030` appears **29 times** in `knowledge_messages`, `self-certifying`
**8 times** — a phrase that did not exist there before that afternoon.

**They arrived from the transcript, not from the spine.**
Put plainly: why the threads reached the KB is not the mechanism the row counts
suggest. All 29 rows carry
`source='claude_code'` and a `source_key` under one Claude Code session id. Zero
rows in `knowledge_messages` come from `deliberation_rounds` or any
advisor-sourced root — `SELECT count(*) ... WHERE source LIKE '%delib%'` returns
**0** against 2.65M rows. The threads reached the corpus because they happened to
be **quoted inside a session that was ingested**, not because the loop records
itself.

**So the capture is incidental and breaks silently.** A review run outside a
Claude Code session, a trimmed transcript, or a session that ends without
closeout leaves the thread in `deliberation_rounds` and never in the KB. Checked
the same day: the two `queue-3.21-preflight` reviews return **0 hits** in
`knowledge_messages` — they exist as rows and as files and have reached no index.

The second half of this item is therefore exactly as open as when it was
written. What changed on 2026-09-07 is that the failure is now harder to see.

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

### 1.25 MENTER DOES THE WRITES; REVIEWERS REVIEW

Review2 writing to disk duplicates the implementer's role. **Menter is the role
that writes** — it holds `code_execution`, and the architecture skill records it
making the first successful file mutation in the container
(`run-86bc4d1009b8fb44-1783645778`, all seven phases).

**Assign writes by ROLE, not by inherited toolset.** This is the same defect
class as 2.23: a capability arrives because it shipped in a bundle, and nobody
decided the role should have it. A reviewer that can write can act on its own
verdict, which removes the separation the two-reviewer design exists to create —
evaluator-must-not-be-the-builder, in the same place 4.10 and 4.19 guard it
elsewhere.

**Scope:** CONTAINER — the per-role `platform_toolsets` in
`enforcement/mwl-proof-v2/profiles/*.yaml`, and whatever the review prompts ask
the reviewers to produce.

**Need:** OPEN — the 2026-09-04 trim gave review1 and review2
`file, terminal, code_execution` on measured usage, which includes write
capability. Usage justified it; role assignment was never the question asked.

**The one check that settles it:** confirm whether any reviewer output has ever
written to disk, then decide the role boundary before the next trim rather than
inheriting it from the last one.

**Related:** 2.23 (capability by inheritance rather than decision), 4.10, 4.19,
3.22 (the trim that assigned the current loadouts, by usage not by role).

### 1.26 KB WRITES HALT CARD WORK — 0.3's ARBITRATION HAS NO PRIORITY MODEL

**The conflict: while the KB is being written, card tasks stop.**

0.3 resolved this for batch ingest — readers take a SHARED lock, wait 5s, then
give up and degrade to keyword search. **That is correct when ingest is
occasional.** Under synchronized updating it becomes the normal case: every write
window degrades whatever is running, and **card work halts against the very thing
meant to keep it informed.**

**0.3 arbitrates by ORDER OF ARRIVAL.** It has no notion of who is waiting or
why. A 40-minute rebuild and a live card read are the same request to it.

**ERIC'S POLICY, 2026-09-06 — a priority model, in order:**

1. **The user has priority.** A write never degrades a live interaction.
2. **A dependency has priority.** If the next step needs it, it goes now.
3. **Everything else defers to idle.** Low-activity means *Eric is idle* —
   nothing runs automatically in background.
4. **Completion status is itself the payload.** Whether a task succeeded or
   failed is what the next step needs, regardless of embedding state.

**THE DESIGN CONSEQUENCE — split the status write from the corpus write.** They
are different operations and only one is time-critical:

| | status write | corpus write |
|---|---|---|
| target | spine row | Chroma embedding |
| contends with | **6,240 operational rows** | **5.9 GB / 2.6M vectors** |
| cost | milliseconds | seconds to minutes |
| when | **now — never queues behind the corpus** | **defers to idle** |

The dependent step reads status immediately; the vector catches up at idle. Rule
4 is what makes that safe — the next step needs the *outcome*, not the embedding.

**THIS REFRAMES 0.3 RATHER THAN REPLACING IT.** The lock is still needed for the
corpus write, and the corpus write is still the thing that must not be
interrupted mid-rebuild. **What is missing is that nothing time-critical sits
behind it.**

**Tier 1, and the tier is the point.** Card work halting on a KB write is not a
cost problem — it is a **stall in the mechanism meant to process the queue**. It
blocks the advisor loop, which is why this sits in Tier 1 rather than with the
other KB items in Tier 2.

**Scope:** the lock is `runtime/mcp_bridge/chroma_lock.py`; the readers are
`pipeline_relay`'s semantic branch and `tools/ask_history.py`; the writers are
the five ingest tools (and `tools/catalog/append_embeddings.py`, wired
2026-09-05).

**Need:** OPEN — the lock arbitrates by arrival order and there is no status/corpus
split. Verified 2026-09-05: a 40-minute sweep held the exclusive lock throughout
and every reader in that window degraded to keyword.

**The one check that settles it:** start a KB write, then run a card that reads
status. **The status read completes; the semantic read defers without failing the
card.** If the card stalls, the split is not real.

**ORDERING — recorded 2026-09-08. 3.21 comes first.** The status write this
item splits out needs somewhere to write the status *to*. That target is 3.21's
queue table, with 2.13 folded into it — 2.13 is what supplies the link from a
queue item to the run that advanced it, and both advisor lineages independently
called it a hard prerequisite to 3.21 on 2026-09-08. Building 1.26 before 3.21
means building the time-critical status write **against markdown**, which is the
prose-parsing problem 3.21 exists to end. Sequence: **3.21 (2.13 folded in),
then 1.26.**

**Related:** 0.3 (conditional DONE — correct for batch, not for synchronized),
1.22 (what gets written, and when), 3.24 (the same contention problem SQLite-side,
recorded as not-yet-symptomatic), 2.30 (which needs the status half to be
readable in time to be useful), 3.21 and 2.13 (the table the status write needs).

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


### 1.27 SIX ITEMS ARE ONE DESIGN: THE SYSTEM CANNOT CLASSIFY A FAILURE

1.3 (no failure routing), 1.4 (a retry policy that retries the non-retryable),
1.11 (the gateway returns HTTP 200 wrapping an upstream error), 1.13 (a
timed-out agent reports nothing), 2.10 (445 broad excepts, 62 of them
`except Exception: pass`), and the five fail-open paths in 0.4 are the same
defect seen six ways: **nothing in the system distinguishes an infrastructure
failure from a model failure from a correct refusal.**

The order matters. Fixing retry without fixing classification retries the
non-retryable more politely. Fixing routing without classification routes on a
wrong label.

**Demonstrated 2026-09-07.** `tools/advisor_review.sh` guarded a gateway call by
exit code. The gateway returned HTTP 200 wrapping
`{"error":{"code":"agent_incomplete"}}`, `docker exec` exited 0, both guards
passed, and the script died two steps later under `set -e`. That is 1.11
recurring in new code — written hours after both parties had read 1.11.

**Scope:** CONTAINER — the gateway response handling, the relay's exception
surface, and the guard patterns in `tools/`.

**Need:** OPEN — all six items are open, and the 2026-09-07 recurrence is new
code, not legacy.

**How to work it:** as one design, **classification first**. Record the
grouping; do not merge the items — they are built separately, the same way the
review loop is.

**Related:** 0.4 (the five fail-open paths), 1.3, 1.4, 1.11, 1.13, 2.10.

### 1.28 1.23 IS GATED ON THE BRIEFING, NOT ONLY ON THE RUN

1.23 (a code run has never completed end to end) is treated as the next
milestone. 1.12 measures what the operator would actually be approving at the
end of it: on the one run that did complete, the two reviewers produced 14,608
characters of analysis and **none of it reached the briefing** —
`objections_json` empty on every pre-gate round, `decision_trails` zero rows, so
section 3 rendered "Consensus reached after 4 rounds — no objections were
recorded."

A code run completing under those conditions means Eric approving a code change
on the proposer's own account of its own proposal. That is failure mode 3 at the
one point in the pipeline where a human is supposed to be the check.

**Scope:** CONTAINER — the briefing renderer and the tables it reads.

**Need:** OPEN — 1.12 is open, and nothing has changed in what the briefing
carries.

**Ordering:** 1.12 is a prerequisite to 1.23 being **MEANINGFUL**, not merely to
it being pleasant. A run that completes into an empty briefing has proven the
plumbing and nothing about the judgement.

**Related:** 1.12 (the empty briefing), 1.23 (the milestone this gates), 1.18
through 1.22 (the review loop, which exists to supply the same missing
perspective on the other plane).


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

**CORRECTION to the paragraphs above — 2026-09-05.** The claim that identical
reviewer payloads are themselves the defect was wrong, and I wrote it into this
item without checking whether the arrangement was chosen. It was.

From `chatgpt_export`, a verification pass headed **"No Agent Sees Another's
Answer"**:

> Confirmed by code structure: Line 225: base_messages frozen before any gateway
> calls. Line 237: Every call_one() receives the same base_messages list. Lines
> 244–249: All three calls run concurrently from that single snapshot. Each agent
> sees … identical for all three, containing zero assistant responses from the
> current round. **Phase 2 verification complete. All 9 checks pass.**

`docs/SPEC_PRODUCTION_PIPELINE_RELAY.md` (2026-07-08) agrees: *"Review1 and
Review2 receive the same input simultaneously via asyncio + httpx."*
Independence within a round is deliberate, verified against nine checks, and
protects against anchoring — the second opinion is worthless if it has already
read the first. Objections travel back through Brain on revision rounds
(`pipeline_relay.py:2564`), so the cross-feed exists; it is mediated, not absent.

**What survives the correction, and it is the real defect:** the reviewers never
deliberate WITH each other at any point. Independence within a round is sound.
Independence *forever* is not what was asked for, and the record is explicit —
see the design record below. `CLAUDE.md`'s stated mitigation for failure mode 15,
*"Objections cross-fed between reviewers; must address each"*, describes
reviewer-to-reviewer exchange and the code cross-feeds to Brain instead. And
review2's `BIAS_OVERLAY` still instructs it to "correct by finding what Review1
missed", which no round ever lets it do.

**THE DESIGN RECORD — Eric, hermes_v4pro, 2026-07-03.** Recovered 2026-09-04 by
the P7-design mining pass. Verbatim, typos his:

> this is not correct drafter has to stop for clarity and understanding check. then when approved it writes the spec and passes it to the reviewers. the pass is the only thing done with out waiting. the rreviewers have to stop to deliberate and reconcile any differences, that is presented to the user again for clarity, understanding and alignment check. if ok'ed it is returned to drafter for refinement or sent to the implementor. the implementor's work is quality checked and verified. that is a stop where the user needs to be observing and making sure that what is being done is aligned with goal and intention.

**For this item:** *"the rreviewers have to stop to deliberate and reconcile any
differences"*. That is a reconciliation phase between the two reviewers, after
their independent passes and before Eric sees anything — which is precisely what
`sequential_review` was written to guard and precisely what does not exist. The
guardrail is not dead because someone forgot to wire it. It is dead because the
phase it belongs to was never built.

The fix is therefore not "show Review2 the Review1 output in the same round" —
that would destroy the independence the nine checks confirmed. It is a
**reconciliation step after both have answered independently**, whose output is
what goes to Eric. Both properties then hold: independent first pass, genuine
deliberation second.

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
**Two instances as originally found:** `gateway_status_qwen` claims Qwen is
2nd reviewer on 8644 — the container uses review1/8643 and review2/8647.
`CLAUDE.md` named `runtime/spine.db` as the spine; that file was 0 bytes.
Nothing detects the divergence. Fix the class, not the two cases.

**Status: one of the two is closed.** `CLAUDE.md` was corrected 2026-09-04 and
the empty file deleted 2026-09-05 (see below). `gateway_status_qwen` is
unchanged, and no detector exists for either. Both statements above are kept in
their found form deliberately — an item about stale assertions should not quietly
rewrite its own.

**The `runtime/spine.db` decoy — full history, 2026-09-05.** This item's second
named instance has now been ruled on three separate times and is still on disk:

- **2026-06-19**, `docs/DEV-PIVOT-17_ENFORCEMENT_ARCHITECTURE.md:105` —
  *"Dead spine.db (0 bytes) confirmed a decoy, not a live fault — no action
  needed."* Investigated and closed.
- **`docs/ISSUE_FINDINGS.md:770`** — recorded again: *"CLAUDE.md still names
  `runtime/spine.db` as the spine; that file is 0 bytes."*
- **This item**, which has named it since it was written.
- The 2026-08/09 mining pass clustered it a fourth time, in
  `cards/corpus_clusters.json` under *"Documentation drift between spine.db and
  cis_memory.db"*, 4 records — including the sharpest phrasing anyone has given
  it: *"The spine DB is a 0-byte file, while the system uses cis_memory.db,
  creating a false sense of integrity."* That cluster never reached this queue.

**On 2026-09-04 it was reported as a fresh discovery and fixed as a single
case** — `CLAUDE.md` was corrected, committed, and the prior records were not
consulted. That is this item happening in the act of editing this item, which is
the strongest evidence available that "fix the class, not the two cases" is the
right instruction and that nothing enforces it.

**The concrete residue:** `runtime/spine.db` is 0 bytes, dated `Jun 9 00:22`,
**untracked** (excluded by `.gitignore:14 *.db`), and referenced by **no
production code** — only `tests/mcp_bridge/*`, which build their own temporary
`test_spine.db`. The real spine is `data/cis_memory.db`, as
`ARCHITECTURE_VERIFIED_20260824.md:41` states.

**IT IS A CLASS OF 29, NOT TWO INSTANCES — 2026-09-07.** A filesystem sweep
found **29 zero-byte `.db` / `.sqlite3` files** across the repo. `runtime/spine.db`,
deleted below as "the decoy", was one of thirty. **Three are named
`cis_memory.db`** — the same name as the real 5.9 GB spine — at `./`,
`./runtime/` and `./runtime/memory/`. `./pipeline_cards.db` sits empty at root
while the real one is `cards/pipeline_cards.db` at 110 KB. Every one of them
answers a `ls` or an `os.path.exists` truthfully and a query with silence.

**CANDIDATE CAUSE — CHECKED AND IT DOES NOT HOLD FOR THE CONTAINER.**
`pipeline_relay.py:34` defaults to a **host** path:
`DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")`,
and SQLite creates an empty file rather than failing when a path does not exist.
The card proposing this said to check before treating it as established.
**Checked 2026-09-07:** the container sets
`CIS_SPINE_PATH=/workspace/cis/data/cis_memory.db` and
`CIS_PROJECT_ROOT=/workspace/cis`, so the host-path default never applies there.
**The cause of the 29 is unexplained and stays unexplained** — recorded as
refuted rather than carried as a plausible story. What remains true is the
mechanism: any code that opens a spine path without that env var set will create
an empty file instead of failing, which is how a decoy is born.

**DELETED 2026-09-05.** `rm runtime/spine.db`, after confirming in the same
command that it was 0 bytes, last written `2026-06-09 00:22:03`, and untracked.
Three months and four rulings after it was first identified. It cannot come back
by accident — nothing in the codebase creates it, and `.gitignore:14 *.db` means
it was never in the repo to restore.

**The residue is closed. The item is not.** Deleting the file removes one
instance; it does nothing about the class. `gateway_status_qwen` still claims
Qwen is 2nd reviewer on 8644. Nothing detects either divergence, and the
2026-09-04 recurrence above shows what that absence costs: a documented,
four-times-ruled fact was rediscovered from scratch and fixed as a novelty. What
this item still needs is the check — something that compares what the primer
asserts against what the runtime does, and fails when they disagree.

### 2.13 Runs are not linked to what they advance
**Checked:** `build_plan_nodes.workflow_run_id` is NULL on all 30 rows. The
Eric Gate briefing's Dependency Node and Tier Advanced fields render blank.
**Eric's call:** does a run name its DEV-PIVOT at intake, or are repairs marked
maintenance? Do not let brain infer it.

**INVESTIGATED 2026-09-07. WIRING GAP, NOT AN UNBUILT CAPABILITY.**
`runtime/db/build_plan.py:74` `complete_node()` accepts `workflow_run_id` and
writes it:

```sql
UPDATE build_plan_nodes
   SET status='COMPLETE', evidence_path=?, commit_hash=?, workflow_run_id=?,
       completed_at=datetime('now'), updated_at=datetime('now')
 WHERE id=? AND status='IN_PROGRESS'
```

**Nothing calls it.** The only caller of anything in that module is
`seed_build_plan.py`, which uses `create_node` and `create_dependency` only. The
writer exists and has never fired — the column is empty for want of a call, not
for want of code. Nothing needs building here; something needs connecting.

**PREMISE CORRECTION — THE STATED SYMPTOM POINTS AT A DIFFERENT TABLE.**
This item says the Eric Gate briefing's Dependency Node and Tier Advanced fields
render blank *because* `workflow_run_id` is NULL. **They do not.**
`build_plan_nodes` appears **zero times** in `tools/eric_gate/build_briefing.py`.
Those two fields come from `goal_references`:

- `build_briefing.py:252-283` — *"Build goal trace from `goal_references`"* —
  selects `dependency_node, tier_advanced` and remaps them to
  `dependency_graph_node` / `tier_advanced`
- `build_briefing.py:568-569` renders `goal.get('dependency_graph_node')` and
  `goal.get('tier_advanced')`, defaulting to `UNKNOWN`

**And they are blank for a reason measured the same day:**

```
goal_references rows                : 30
dependency_node NULL/empty          : 30
tier_advanced   NULL/empty          : 30
```

**All thirty rows are empty in both columns.** So the symptom is real and the
diagnosis in this item is wrong: populating `build_plan_nodes.workflow_run_id`
would not change those fields by one character. **This item must be rescoped
before it is built** — as written it would produce a correct-looking change that
leaves the reported symptom exactly as it is, and the verification would pass
because it would check the column that was changed. (That is 2.38's failure
shape, found in a queue item rather than a migration.)

**SEEDING, PARTIALLY UNEXPLAINED — RECORDED, NOT RESOLVED.**
`tools/build_plan/seed_build_plan.py` hardcodes **15 tuples**. **Thirty rows
exist.** The origin of the other 15 — the `7R.*`, `11A–D`, `12`, `13` and
`ENFORCEMENT` nodes — **is not in the record.** No explanation is constructed
here. Node ids also jump **15 → 46**, so rows were deleted at some point; that is
why GLM's `AUTOINCREMENT` concern on migration 0030 was worth recording even
though it went untested. Reused ids would collide with dependency rows that still
point at them.

**WHAT REMAINS ERIC'S CALL, UNCHANGED BY ANY OF THE ABOVE:** does a run name its
DEV-PIVOT at intake, or are repairs marked maintenance? Do not let brain infer
it. This rescoping establishes what the code does and does not do. It does not
make that decision and must not be read as having made it.

**FOLDED INTO 3.21 — Eric's decision 2026-09-09.** This item is no longer
independent. 3.21's queue table answers three of 2.30's four questions and
cannot answer *did it succeed*, because the link from a queue item to the run
that advanced it does not exist — which is this item. Both advisor lineages
identified it as a hard prerequisite to 3.21 on the same packet. **Build them as
one design;** the ordering and the reasoning are recorded in 3.21, and 1.26 sits
behind both. The open decision above is unchanged by the fold and is still
Eric's to make.

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

**DECIDED 2026-09-06 — split read from dispatch in the server. Not "withhold the
toolset".** KB access for the advisor is **mandatory**: an advisor that cannot
read the record cannot check a claim against it, which is the job. So the answer
is not to take `cis-knowledge` away — it is that the server must stop shipping
retrieval and run-starting as one set.

**The fix is in `runtime/mcp_bridge/tools.py`**, where all 18 tools are defined
and registered together. **Config cannot do this** — `platform_toolsets` can only
take or leave the whole set, which is why the 2026-09-04 trim had to disable
`cis-knowledge` entirely on all six profiles and thereby removed retrieval it
would rather have kept.

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

**This item's own status line was unreadable to the extractor until
2026-09-09** — `BUILT` was not in its vocabulary, so this item was projected into
`queue_items` as having no status at all. Recorded against 3.21, where the fix
lives. The spelling below is deliberately unchanged: normalising it would have
hidden the defect instead of proving the fix.

**Need: BUILT 2026-09-09, ONE-WAY.** `tools/pause_notify.py`, called from the
three stops in `tools/advisor_review.sh`. Host-side `urllib` POST, no agent on
either end, exactly as this item settled. Delivered live at all three stops —
message ids 1159, 1160, 1161, continuing from 1155.

**What the message carries, and where it comes from.** Signal, verdict, packet
hash status, token cost and the opening of the objection, all read from
`deliberation_rounds.objections_json` as recorded. **Claude Code's account of a
review is not what goes in the message.**

**What it deliberately does NOT carry: unique-findings-per-lineage.** 1.20's
measure needs both objections read side by side, and anything mechanical would be
a summary wearing the advisors' name. The message says so in those words rather
than leaving the reader to assume the omission is completeness.

**A failed send does not fail the pause.** Tested with a deliberately bad token:
the POST returned 401, the stop was still recorded PENDING, and the script exited
0. Losing the message loses visibility, not state — the stop is a row first and a
notification second.

**ONE-WAY IS A DECISION, NOT AN OMISSION.** Eric's replies arrive with no
`reply_to_message` field — measured 2026-09-02 and recorded above — so Telegram's
own threading cannot say which card a reply answers. Consuming a reply needs
something polling `getUpdates`, and **a long-running poller reintroduces exactly
what 1.21's row was chosen to avoid**: a process that dies with its terminal and
takes the loop's position with it. Wiring one would contradict the design the
feed exists to serve. So: read the stop on the phone, release from the terminal
with `--continue`. That is worse than replying "go" and far better than a stop
nobody sees.

**The inbound path was NOT re-proven on 2026-09-09.** `getMe` confirmed the token
and identity; `getUpdates` returned **zero** updates, which shows the endpoint is
reachable and authorized but exercises no round trip. **The 2026-09-02 proof
above stands unchallenged rather than re-verified** — a distinction worth keeping,
because "it worked a week ago and the endpoint answers today" is not the same
claim as "it works."

**The one check that settles it — DONE 2026-09-02, both directions.** Message 1149 out via a plain `curl` POST to `sendMessage`; Eric's "go" came back as message 1150 through `getUpdates`, from uid 6511416750, matching the `TELEGRAM_ALLOWED_USERS` value — so the loop can verify the reply is his and not another group member's.

**The destination is a private chat, not a group.** The test ran in `CIS_Test_Group` (-5563618057), which held four bots besides Eric — three of them backed by running VM gateways, silent only because `TELEGRAM_REQUIRE_MENTION=true` in their configs. He deleted the group on 2026-09-02 rather than police that membership, and the feed now DMs him directly (uid 6511416750, verified: message 1155). A DM gives one agent by construction — there is no member list, so no second bot can appear — and `require_mention` does not apply in private chats. The bot is `@cis_kernel_bot`, bot id 8926607085, display name renamed to **HermesFeed** on 2026-09-02 so it is identifiable among the seven Hermes bots; the token and id are unchanged by that rename.

**Replies arrive unthreaded — the loop needs its own correlation.** Eric's "go" carried no `reply_to_message` field, so Telegram's threading cannot tell the loop which card a reply answers. Either one card waits at a time, which 1.21's waiting state gives for free, or each message carries a short tag the reply must quote. The first is simpler and is what 1.21 already implies.

**Stale, and NOT fixed by the pass that was supposed to fix it — corrected
2026-09-09.** All seven host `.env` files still name the deleted group as
`TELEGRAM_HOME_CHANNEL`, and five of those profiles have running gateways that
would get a 403 on any post there. This item said *"fix it in the same pass that
wires the feed."* **That pass happened on 2026-09-09 and did not fix it.** The
notifier reads the uid from `TELEGRAM_ALLOWED_USERS` and never touches
`TELEGRAM_HOME_CHANNEL`, so the feed works while the stale value survives
untouched in seven files.

**Routing around a stale value leaves it more dangerous, not less.** It now
looks configured, it is referenced by five live gateways, and the one component
that would have exercised it deliberately does not. **Nothing detects it.** That
is the primer/runtime divergence of 2.12 in a credential file: a value that reads
as current, is wrong, and has no reader left to fail loudly against it.

**The fix is still the one this item named** — point the seven files at the uid
rather than at a new group. It is now outstanding beyond the window this item set
for it, which is recorded here rather than in a new item because splitting one
defect across two places is 2.12's own shape.

**Depends on:** 1.21. A feed without a waiting loop is a notification stream nobody reads by noon. **Blocked by:** 1.22 — replies that reach no index are the same loss as reviews that reach no index.

**THE PAUSE FILTER IS LOAD-BEARING AND LIVES IN ONE SCRIPT — recorded
2026-09-09, against 1.21.** A loop stop is a `deliberation_rounds` row with
`reviewer_signal='PENDING'`. So are **11 legacy pipeline rows** from June to
August, carrying `reviewer_role=''` and `objections_json` **NULL**. The only
thing separating the two is `reviewer_role='pause'`, and that predicate exists
in exactly one place: `tools/advisor_review.sh`.

**What a reader without it gets.** Querying `PENDING` alone returned **13 rows
where 2 were loop stops**, and `json.loads` threw on the first NULL before
printing anything — measured 2026-09-09 on a query that omitted the filter. So
the failure is not subtle drift; it is a wrong count and an exception, which is
the better of the two ways this could go wrong.

**Why it matters beyond one query.** 1.21's whole justification is that the
waiting state is a **row**, readable by something that was not running when the
pause was set. That promise is only kept if the other reader knows the filter —
and nothing carries it: not the schema, not a view, not a comment on the table.
The `reviewer_role` column has `DEFAULT ''`, so a legacy row and a malformed
pause row are indistinguishable to anything that does not already know what
`'pause'` means.

**The shape of the fix:** put the predicate somewhere a second reader inherits
it rather than has to reconstruct it — a view over `deliberation_rounds`, or the
separate table this deliberately avoided needing. Recorded now because the cost
lands on whoever reads pauses next, not on the script that writes them.

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

### 2.30 The spine is the stateless agents' source of truth

A stateless agent needs one place that answers four questions: **what is the
current item, what does it depend on, what was just done, and did it succeed.**

Today that is **four places**: a markdown queue, git history, `workflow_runs`,
and the previous session's output. No agent can assemble all four, and each
reader parses the prose differently — which is exactly how 2.12's divergence
happens.

**This is the requirement 3.21 serves, and it is recorded here so 3.21 is not
read as UI work.** Moving the queue into the spine is not about rendering a
roadmap; it is about giving stateless agents a single readable state. The
roadmap is a consequence, not the purpose.

**Scope:** CONTAINER — the agents that need it run there.

**Need:** OPEN — all four sources exist and none is authoritative.

**Related:** 2.12 — divergence is what happens when each reader parses prose
differently. 3.21 is the implementation. 1.26 supplies the "did it succeed" half
in time to be useful.

### 2.32 SUPERSESSION HAS NO SCHEMA REPRESENTATION

The 2026-09-06 dependency read found a section at **line 2044**, *"Recorded, not
queued — superseded by the container"*, carrying two entries written explicitly
so they are not mined again. **Nothing in any schema can express what they are.**

There is no supersession edge type anywhere: not in `build_plan_dependencies`
(which has `HARD` and `SOFT` only), not in `mined_tasks`, not in the proposed
`queue_edges`. So an abandoned approach and a current one are indistinguishable
to anything reading the data — and the only thing preventing a superseded item
being mined back in is a prose heading a parser will not see.

**Scope:** REPO/CONTAINER — the queue schema 3.21 creates.

**Need:** OPEN — the section exists, the edge type does not.

**Depends on:** 3.21 — there is no table to add the edge kind to until the queue
is one.

**The one check that settles it:** take the two entries at line 2044 and ask
whether a query can distinguish them from open items. Today it cannot.

**Related:** 2.12 (a superseded thing that still reads as current is the same
failure), C/3.25 below (the other edge kind the same read found missing).

### 2.33 DESCRIPTION INDEX OVER THE IDENTIFIED SPECS

`tools/find_specs_by_content.py` identified **210 specification documents, 132 of
them invisible to a filename search**. Roughly **200 have never been read.** They
are found today only by someone already knowing to look.

**The fix is the mechanism skills already use.** One line per document — what
capability it covers, when it applies — loaded at session start the way skill
descriptions are, so the model matches against the line and opens the document
only when it is the right one. It does not need to search for what it does not
know exists.

**SIZE IT AT ~10K TOKENS LOADED. NOT A PERCENTAGE OF CONTEXT.** Skill
descriptions cost ~29 tokens each (measured, 3.22), so 210 lines is under 6K.
The window is **200K, not 1M**, and **every turn re-sends it** — 3.23 measured
what fixed context costs when it is repeated per call. A percentage-of-context
budget grows silently as models grow; a token ceiling does not.

**The failure mode to design against: a description that overstates coverage is
2.12.** A line claiming a document covers something it does not sends the reader
to the wrong place with confidence, which is worse than the document being
invisible.

**Scope:** REPO — the index is generated from the documents; the loading is a
per-role prompt concern.

**Need:** OPEN — 210 identified, ~200 unread, no index exists.

**The one check that settles it:** ask for a capability covered by one of the 132
filename-invisible documents and see whether the index surfaces it without a
search.

**Cost is the reading, not the writing.** Generating 210 lines mechanically is
easy and produces 210 plausible wrong lines. Each has to be read.

### 2.35 THE EXPORT GATE IS SELF-CERTIFYING
**Found 2026-09-07, from a live failure.** Migration 0030 lowercased
`build_plan_nodes.project_id`; 14 code sites still compared against `'CIS'` and
began matching zero rows. The pre-commit hook regenerated all 13 exports from the
broken queries and the gate printed **`PASS: all 13 artifacts match manifest`**
while `HCP_05_NEXT_ACTIONS.md` silently lost its entire 30-row tier table. That
result was committed in `049cdba`.

**CORRECTED 2026-09-07, SAME DAY. THIS ITEM FIRST SAID THE GATE DOES NOT CHECK
CONTENT. THAT IS WRONG, AND THE TRUTH IS WORSE.**
`gate_export_agreement.sh:191-234` **does** check `sha256`, `char_count` **and**
`line_count` against the manifest. It has the data. The defect is **ordering**:

```
▸ Regenerating exports from spine...
[generate_all] Manifest written: runtime/manifests/EXPORT_MANIFEST.json
▸ Running export agreement gate...
PASS: all 13 artifacts match manifest
```

`generate_all.py` writes `EXPORT_MANIFEST.json` **from the artifacts it has just
produced**, and the gate then compares those artifacts to that manifest. The
check's success criteria are derived from the thing being checked. It can catch
corruption *between generation and verification* and nothing else — never bad
content, because the manifest describes whatever was generated. HCP_05 lost 30
rows; **artifact and manifest changed together and agreed perfectly.**

**Same class as the poisoned verification criterion 1.1 caught.** A check whose
pass condition comes from its own subject cannot fail for the reason it exists.
Adding more fields to the manifest does not fix it — sha256, char_count and
line_count are already there and all three passed.

**What to build:** a criterion that does not come from the artifact. A content
floor per artifact — minimum row/section counts held in a **checked-in expectations
file, not the generated manifest** — so an export that empties fails the gate.
Failure mode 11, inside the enforcement layer itself.

**Related:** 2.36 is the second, independent defect on the same path. Fixing
either alone leaves the other: fix the fallback and the gate still passes on
empty content; fix this and the gate still cannot see a substitution, because the
artifact is full.

### 2.36 AN AGENT'S PROJECT_BRIEF IS 16% OF THE DOCUMENT IT IS NAMED AFTER
**Found 2026-09-07 while checking how far the 2.35 failure reached.**
`pipeline_relay.py:729` builds PROJECT_BRIEF from `AGENTS.md` and truncates:

```python
project_brief = f.read()[:3000]  # truncate to 3000 chars
```

Measured the same day:

```
AGENTS.md total chars: 18376
injected into prompts: 3000 (16%)
LAST LINE THAT REACHES AN AGENT: '- /hom'

## 3.                 at char  1453   REACHES agent
## 4.                 at char  3408   NEVER REACHES AGENT
## 6. Next Actions    at char 10624   NEVER REACHES AGENT
## 7. Active Blockers at char 10763   NEVER REACHES AGENT
```

**Nothing says so at either end.** The prompt calls it PROJECT_BRIEF and the file
calls itself the agents' context; neither records that five of seven sections are
cut. An agent asked what it knows about the project would answer from the first
16% and have no way to know the rest exists. **Failure mode 5 — context amnesia —
built into the transport rather than caused by the model.**

**THE FALLBACK, AND THE RANKING THIS ITEM CORRECTS.**
`generate_agents_md.py:58` carries a deliberate fallback: *"if no
PENDING/IN_PROGRESS build nodes, pull from `next_actions`."* When 0030 broke the
build-plan query it fired, filling AGENTS.md §6 with three `NA-SEED-*` rows from
a table the comment eight lines above calls **non-authoritative**. The section
looked populated. Nothing in the file, the run log or the gate recorded that a
substitution had happened. That is real and it should announce itself.

**But it was ranked as the more dangerous of the two defects, and that was wrong.**
The claim behind the ranking was that AGENTS.md is what every stateless agent
reads. §6 begins at character 10,624 and the injection stops at 3,000. **The
substitution's only audience was the manual handoff — it never reached the
pipeline.** Recorded because a wrong severity call sends the work to the wrong
place, and this one was made and corrected within a day.

**What to decide:** whether 3,000 characters is the intended brief. If it is, the
file should be built to fit it and say so; if it is not, the truncation is a
silent context loss on every dispatch. Do not fix by raising the number without
answering which.

**Related:** 2.35 (the other defect on this path), 3.23 (payload composition).

### 2.37 NOTHING TESTS THE ARTIFACTS FOR WHETHER ANYTHING EXERCISES THEM
**Found 2026-09-07.** This list's own header test — *is this capability in the
code today* — has only ever been pointed at the queue. **Nothing points it at the
artifacts**, and the same shape keeps surfacing when anyone looks:

| Surface | What was found | Item |
|---|---|---|
| Generated HCP exports | **11 of 13 read by nothing.** Written on every commit; no commit in their git history ever changed one on purpose | this item |
| `runtime/tier7r/` | eight modules, marked COMPLETE across nodes 7R.1–7R.7, **imported by nothing** | 2.16 |
| `runtime/spine.db` | 0-byte decoy, **ruled on four times across three months** before deletion | 2.12 |
| Gate scripts | **33 of 51 never called once** | 2.15 |
| `route_task.py`, `push_cis_live()` | described and never built; a function with no caller | 2.18 |
| Specification documents | `find_specs_by_content.py` found **210, of which 132 are invisible to a filename search and ~200 unread** | 2.33 |

**The common shape: a thing is declared, it is maintained, and no one has ever
asked whether anything consumes it.** Each of the six above was found by a
separate investigation that went looking for something else. That is not a
detection method, it is luck applied repeatedly.

**What to build:** 2.18's gate, pointed at artifacts rather than specs — for
anything declared (an export, a module, a gate script, a spec), a check of
whether anything reads, imports, or calls it, and a record when the answer is
nothing. Cheap: the six findings above were each one `grep` by object name.

**This is 2.12's instruction applied here: fix the class, not the cases.** Six
instances are recorded and none of them generalised. Closing them one at a time
is how the seventh gets found by accident too.

**Not a retirement proposal.** Establishing that nothing reads a thing is not the
same as deciding it should go. See the HCP disposition note in 3.27.


### 2.34 PER-ROLE STATE SLICES, DERIVED NOT AUTHORED

Not every role needs the whole state, and sending it to all of them is what 3.23
measured as 20% byte-identical repetition per call.

- **Brain gets full state.** It is the entry point where direction is set, and a
  narrowed view is exactly where a wrong direction starts.
- **Reviewers get the task plus its dependency neighbours** — what it supersedes,
  what it blocks.
- **Verify gets the claim and the evidence path.** Nothing else bears on whether
  the claim holds.

**DERIVED, NOT AUTHORED. Each slice is a query against one table**, so slices
cannot diverge from each other. Hand-authored slices drift, and that drift is
2.12.

**EVERY SLICE CARRIES ITS OWN BOUNDARY** — *these items are in scope, others
exist, out-of-scope is not absence.* 2.7 already recorded the failure this
prevents: a reviewer whose file access was narrower than its subject ran ~14
empty searches and reported "the backup file does not exist" under a heading
reading WHAT I OBJECT TO. All three backups existed. **A narrowed context without
a stated boundary manufactures false absence.**

**PREREQUISITE — 2.13, and it is a hard one.** `build_plan_nodes.workflow_run_id`
is NULL on all 30 rows, so **no gate has ever checked a run against the queue
item it advances.** Until that join works, full context is the only thing holding
alignment, and narrowing any role's view removes the only check there is. Build
2.13 first or this makes things worse.

**Scope:** CONTAINER — prompt assembly in `runtime/abstraction/pipeline_relay.py`.

**Need:** OPEN — every role receives the same constructed context today.

**Depends on:** 2.13 (the join that makes alignment checkable), 3.21 (the table
the slices are queries against).

**The one check that settles it:** give a reviewer a slice and confirm it can
still state what it was NOT shown. If it cannot, the boundary is missing and 2.7
recurs.

**Collapses most of 3.23's fixed-context cost** as a side effect, but the reason
to build it is alignment, not tokens.

### 2.31 Constrain queue writes before any agent gets them

**An agent that can write the queue can mark its own work done.** That is
evaluator-must-not-be-the-builder in a new place, and it is the same failure
4.10 guards against in the harness and 4.19 guards against in card selection.

Once 3.21 makes the queue a table, write access becomes a live question rather
than a theoretical one — a markdown file nobody can edit mid-run is an accidental
protection that a table removes.

**Write access to the queue table must be settled BEFORE any agent is given it.**
Not after the first agent needs it, because by then the answer will be shaped by
what is convenient.

**Scope:** CONTAINER.

**Need:** OPEN — the queue is not yet a table, so nothing has write access. This
item exists to be answered before that changes.

**Depends on:** 3.21.

**Related:** 4.10 (the harness must not edit its own scorer), 4.19 (the pipeline
must not select its own work), 2.17 (what a silently-wrong write to an audit
table costs).


### 2.39 THE CONFIRM-BEFORE-WORKING STEP IS A HUMAN REMEMBERING

HOW TO WORK THIS LIST says to confirm an item is still not in the code before
working it, because the items were checked on 2026-08-29 and the code moves.
Nothing enforces that. It is a human remembering, every time, under no prompt.

**What one session turned up without looking for it.** 2026-09-06/07 produced
four staleness findings: 1.22's ingest half was already wired by commit
`e90e598`; 2.5's migrations exist (0011 through 0030) though no tracking table
does; 3.5's export-gate warning appears resolved — the gate now prints PASS on
13 artifacts; and 2.13's stated symptom pointed at the wrong table entirely.

Every count and status line in this list carries an implicit timestamp, and most
of them read 2026-08-29.

**Scope:** REPO — this list and whatever comes to check it.

**Need:** OPEN — nothing compares an item's claims against the code.

**The shape of the fix:** a check that compares an item's claims against the
code, run **when the item is opened** rather than remembered. Not a periodic
sweep of every item; the cost belongs at the moment one is picked up.

**Related:** 2.12 (primer/runtime divergence — this is the same defect pointed
at the queue instead of at the primer), 2.38 (a check derived from the change
cannot see what the change breaks).


### 2.40 THE ADVISOR LOOP RECORDS WHAT WAS SAID, NOT WHETHER IT WAS RIGHT

Every exchange writes a `deliberation_rounds` row: run id, round, signal, and the
thread in `objections_json` as an array of objects carrying objection, evidence,
verdict and packet hash. **Nothing records the outcome.**

On migration 0030 the record shows that GLM raised the DEFAULT objection. It does
not show that GLM was *correct*, twice. It does not show that Qwen's single
CASCADE finding was the one that would have caught a silently broken dependency
graph. And on the 3.21 card, 2026-09-08, it does not show that **both lineages
built their main remedy on a false premise** — live adapter writers to
`build_plan_nodes` that are two comments, not code — or that one `grep` retracted
it and collapsed both remedies at once.

The stored thread is identical in all three cases. A reader six weeks from now
cannot tell the objection that saved a migration from the objection that was
wrong, because the field that would say so does not exist.

**What this costs.** 1.20's measure is the count of findings only one lineage
raised, *and which of them mattered*. The first half is countable from the rows.
The second half is not, so it is recounted by hand every session and lost when
the session ends — which is the same reason the 2026-08/09 mining pass had to
recover 4,479 candidates by archaeology.

**The fix, and where it goes.** An outcome written back into the thread after
execution: the objection was HELD, WITHDRAWN, or **PROVEN WRONG by the result**.
That value is knowable at exactly one moment — when the result review runs — and
that is where it should be written. The round-3 result review built on
2026-09-08 is the hook; it currently records a verdict on the *work* and nothing
about the *reviews that preceded it*.

**Scope:** REPO — `tools/advisor_review.sh` and the `objections_json` thread it
writes. No schema change: the outcome is another key in the existing array of
objects.

**Need:** OPEN — the round-3 verdict field exists as of 2026-09-08 and applies to
the executed work, not to the prior objections.

**The one check that settles it:** pick any completed card and ask the spine
which of its objections turned out to be right. The answer is in a human's
memory or in a transcript, and nowhere in the row.

**Related:** **2.8** — the same shape, one stage earlier. `gate_outcomes` holds
**4,694 rows** (the item says 4,375, checked 2026-08-29; the drift is 2.39's
point) read only to display: nothing aggregates across runs and nothing detects a
guardrail that never fires. The advisor loop is building that shape a second
time, and it is cheaper to add the field now than to mine it back later. Also
1.20 (the measure this makes countable), 1.18 and 1.19 (the rounds that produce
the thread), 1.22 (whether any of it reaches the KB at all).


### 2.41 A CHANGE THAT ALTERS AN ASSUMPTION INVALIDATES THE REVIEWS OF EVERYTHING BUILT ON IT

The reply round (1.19) was built and proven on 2026-09-07 with a single lineage
forced through `CIS_ADVISOR_PROFILE`. Dual lineage landed **the same day**.
Nothing re-checked round 2 against it.

**Found 2026-09-09, two defects, neither ever executed:**

- In dual-lineage mode round 2 **exits 1 before contacting any gateway.** `PRIOR`
  is the fixed path `reviews/done/<id>.response.md`, while dual lineage writes
  `<id>.<profile>.response.md`. The file it needs cannot exist.
- Had that path resolved, `BODY` was built **once, outside the lineage loop**, so
  both lineages would have been handed **the same lineage's objection** to
  answer — a reply round that reads as two independent answers and is one.

Neither was caught because round 2 had only ever run in the mode the defects do
not appear in.

**What this cost, concretely.** The reply round was recommended to Eric for the
3.21 review **two turns before the defects were found**. It could not have run.
And round 3 — the result review — was then written with the identical structure
and would have inherited both, because the structure was assumed reviewed.

**The rule this item exists to record:** when a change alters an assumption
another component depends on, the dependent component's review is **void, not
merely older**. Single-lineage was not a setting; it was the premise round 2 was
proven under, and dual lineage removed it silently the same afternoon.

**Nothing tracks which reviews rest on which assumptions.** `deliberation_rounds`
records the packet hash, so a review is bound to the artifact it read — but not
to the surrounding state that made the artifact true. A packet can hash
identically and be answering a question that no longer exists.

**Scope:** REPO — the review record in `deliberation_rounds`, and whatever comes
to invalidate it.

**Need:** OPEN — the two defects were fixed 2026-09-09; the mechanism that let
them survive was not.

**The one check that settles it:** name a change made in the last month and list
the reviews it invalidated. There is no query for this, and the answer is
currently a person remembering.

**Related:** **2.38** — a check derived from the change cannot see what the
change breaks. This is that failure one layer up: in the *review* rather than in
the verification. **1.20**, whose three divergence counts were all taken under a
prompt label that changed underneath them. **2.39** (staleness in the queue) and
**2.12** (divergence between two copies) are the same defect aimed at documents
rather than at reviews.


# TIER 3 — independent defects, no dependants

- **3.1** `ask_history` does not merge FTS5 with vector search. The relay does;
  `ask_history` does not.
- **3.2** No pre-delete or archive-policy validation. **Checked: absent.** On
  2026-08-29 a 4.9GB Chroma segment directory was deleted after a manual ad-hoc
  check. Nothing but care stood between that and deleting something live.
- **3.3** Container pre-flight checks are partial. **Checked:** `run_container.sh`
  has 3 file/directory tests — one hand-written case for the secrets file being a
  directory. No systematic mount verification, and mounts were added today.

### Assigned repair: container-kb-health-20260917

# Container knowledge-health repair

Card ID: container-kb-health-20260917
Parent queue item: 3.3 (partial container pre-flight checks)
Assigned to: Claude Code
Independent verifier: Codex
State: ASSIGNED; all implementation claims require independent verification.

## User authorization
Eric asked: "Run the readiness check. When you identify the task, I what you to create the card somewhere Claude can know it landed and proceed with the work. Then paste it’s evidence claims somewhere you can know it’s finished so you can verify the evidence and I don’t have to copy paste".
The current development team is Claude Code and Codex. This is a bounded development repair, not permission to start the paid-model pipeline.

## One behavior
The container system-health endpoint must truthfully report the readability of the actual embedded knowledge store, without depending on a nonexistent Chroma HTTP server or creating a replacement database.

## Observed failure
GET /api/relay/system/health returns ChromaDB healthy=false, url=localhost:8000. runtime/mcp_bridge/chroma_index.py explicitly uses chromadb.PersistentClient (embedded). The live container's CIS_CHROMA_PATH is /workspace/cis/data/chroma_data. Its existing chroma.sqlite3 has collection knowledge_messages; an actual tools/ask_history.py search completed successfully during this check. Thus the current HTTP-server probe is the wrong probe.

## Scope
Inspect runtime/container_app.py and relevant storage configuration. Replace only the Chroma health probe with a cheap read-only embedded-store check. Keep the response's existing services shape and healthy boolean compatible with the UI. Make the name/detail explicit that success means embedded store/knowledge collection readable, not model-provider availability, semantic retrieval quality, or a completed pipeline. Honor CIS_CHROMA_PATH; fallback should follow the existing repo-root convention and work from /workspace/cis and /mnt/projects/cis. Do not silently fall back if an explicitly configured path is invalid.
Do not instantiate a Chroma client, load embeddings, download models, call paid APIs, ingest, mutate schema/data, or create a missing store in this polling endpoint. Use short timeouts and close connections. Do not expose secrets or stack traces in HTTP output.
Limit implementation to runtime/container_app.py, an optional narrowly scoped helper under runtime/, and focused tests. No UI redesign. Do not fix unrelated SQLite/gateway/llama-server checks, change mounts, modify pipeline_relay.py, restart/recreate services, commit, or push. Preserve pre-existing dirty files.

## Acceptance evidence
1. Reproduce the before-state from the existing source/record.
2. A real temporary embedded Chroma metadata SQLite fixture with knowledge_messages gives healthy=true and embedded/readability wording, without contacting port 8000.
3. Missing directory, missing database, invalid/corrupt database, and missing knowledge_messages collection give healthy=false with useful bounded details; missing paths remain absent. Test actual read-only behavior and ensure polling does not create data or alter fixture contents.
4. Explicit configured path wins; no host-only fallback or accidental new store. Test relevant path resolution.
5. Exercise the Flask health endpoint with unrelated gateway checks mocked, asserting the existing response contract and new embedded result. Do not let mocks make the storage failure cases vacuous.
6. Run focused tests, report exact commands, exit codes, and output. Record changed files and diffs. A test-client check is not a claim that the already-running Flask process has loaded the change.
7. Codex will independently re-run tests and inspect the actual container. Do not mark parent queue item 3.3 DONE; this repairs only its knowledge-health subtask.

## Handoff and completion
This file is a dispatch snapshot of the card attached to queue_items[3.3], not a second queue. Shared host directory: /mnt/projects/cis/data/agent_handoffs/container-kb-health-20260917 ; same container directory: /workspace/cis/data/agent_handoffs/container-kb-health-20260917 .
Before editing an existing source file save its preimage under this directory/backups/, preserving relative paths. Explain the proof then carry out this one bounded card; Eric's current instruction authorizes the complete implementation and evidence handoff rather than stopping after each file write.
Write evidence.md here with commands, raw results, limitations and claimed acceptance outcomes. Write completion.json here LAST, with card_id, status (READY_FOR_VERIFICATION or BLOCKED), changed_files, tests, evidence_path, and remaining_limitations. Never label your own result VERIFIED. If permissions or account limits prevent completion, report BLOCKED accurately. The supervising Codex process captures your final response and exit status automatically; Eric should not relay anything.

- **3.4** Two manifest directories, canonical status unresolved.
  `logs/manifests/` vs `runtime/manifests/`, with an unenforced "do not write
  there".
- **3.5** Export gate warns "expected 12 artifacts, found 13" on every commit.
- **3.6** `projects.id` is `'cis'`, `build_plan_nodes.project_id` is `'CIS'`.
  A plain join returns 0 of 30 rows; `relay.py:1058` papers over it with
  COLLATE NOCASE.
  **SCOPE CORRECTED IN BOTH DIRECTIONS, 2026-09-07.**
  **Wider than written — a data-only fix does not hold.** The two schemas
  disagree *by default*: `build_plan_nodes.project_id TEXT NOT NULL DEFAULT
  'CIS'` against `workflow_runs.project_id TEXT DEFAULT 'cis'`. An `UPDATE` that
  lowercases the 30 rows is reverted by the next default insert, and **SQLite
  cannot `ALTER` a column default** — changing it means a table rebuild. The fix
  is a migration, not an update.
  **Narrower than reported — `corpus_entries` is not in scope.** On 2026-09-06 I
  reported "243 rows across two tables". 213 of those were
  `corpus_entries.project_tag`, found by matching any column name containing
  "project". Checked 2026-09-07: it is `project_tag TEXT DEFAULT 'CIS'` with the
  comment `-- CIS, SWA, WIAS`, **no `REFERENCES projects`** — a free-text tag,
  not a foreign key, with an FTS5 shadow that a rewrite would have to rebuild for
  no benefit. It does not join to `projects.id` and does not need to.
  **Real scope: 30 rows in one table, plus one column default.** Recorded in both
  directions so neither the overreach nor the underreach is repeated.
  **DONE 2026-09-07 — `runtime/schema/migrations/0030_build_plan_nodes_project_id.sql`,
  run against `data/cis_memory.db`.** The plain join now returns 30 of 30.
  What the migration did: lowercased 30 rows to `'cis'`; changed the column
  DEFAULT from `'CIS'` to `'cis'` **by table rebuild, because SQLite cannot
  `ALTER` a column default**; added the missing `FOREIGN KEY` on `project_id`
  to `projects(id)`; recreated both named indexes, which a rebuild drops
  silently; and preserved the 25 `ON DELETE CASCADE` rows in
  `build_plan_dependencies` via `foreign_keys=OFF` **and**
  `legacy_alter_table=ON` together — under 0020's `RENAME`-first shape those
  rows are destroyed two different ways, and neither pragma alone prevents both.
  **The executable SQL was byte-identical across all three revisions**
  (`a4dbf0712cda5e85…`, comments stripped, 12 statements). Revisions 2 and 3
  changed the verification block only, so the SQL two advisors endorsed is the
  SQL that ran. Numbered 0030, not 0021 — `0021_corpus_entries.sql` exists.
  **15 checks, all passing, every one a command that can fail:**
  (1) counts 30 and 25; (2) `project_id` = `[('cis', 30)]`; (3) DEFAULT as
  declared = `'cis'`, notnull=1; (4) both FKs present; (5) the `project_id` FK
  rejects a bad parent; (6) both indexes present; (7) `UNIQUE` still rejects a
  duplicate; (8) `foreign_key_check` empty, `integrity_check` ok; (9) all 25
  dependency rows **resolve** to live node ids, 0 fail to resolve; (10) the
  DEFAULT applies **in practice** — an insert omitting the column stored `'cis'`,
  rolled back; (11) the `workflow_run_id` FK rejects a bad parent; (12) **the
  CASCADE still fires** — deleting node id 2 removed one dependency row,
  25 → 24, rolled back to 25; (13) index **definitions** match, not just names —
  `(project_id, status)` and `(project_id, sequence)`; (14) `NOT NULL` on
  `project_id` rejects an explicit NULL; (15) the `status` CHECK rejects `'BOGUS'`.
  No probe rows survived: `node_label LIKE '%-probe%'` returns 0.
  Checks 9–11 came from Qwen's review of revision 1; 12–15 from the dual review
  of revision 2. Check 12 is the one that mattered — see 1.20.
  **AUTOINCREMENT on `id` is uncovered BY DECISION, not oversight.** GLM raised
  it: if the rebuild dropped it, all fifteen checks still pass and the damage
  appears later, when reused ids collide with dependency rows that still point at
  them. Testing it needs a delete-then-insert probe across a transaction
  boundary. It is declared in the CREATE TABLE and left to inspection, and the
  migration file says so in as many words so the gap stays a decision.
  **Follow-on, NOT done: `relay.py:1058`'s `COLLATE NOCASE` is now dead weight.**
  It was load-bearing this morning and is not any more. Left in place
  deliberately — removing it is a change to production query code and belongs in
  its own item, not smuggled into a migration's commit.
  Backups: `data/backups/build_plan_20260907T163931Z.sql` (2 CREATE, 55 INSERT).
  **THE MIGRATION BROKE 14 CALL SITES AND THE REVIEW COULD NOT HAVE CAUGHT IT.**
  Found 2026-09-07, after the commit. Every site comparing `project_id = 'CIS'`
  exactly now matched zero of 30 rows. Fixed the same day — `'CIS'` → `'cis'` at
  14 sites in 9 files, plus 15 tuples in `seed_build_plan.py`, which the new FK
  would otherwise have rejected outright. Backup:
  `data/backups/case_fix_20260907T180202Z/`.
  Sites: `generate_agents_md.py` ×2, `generate_hcp.py`, `runtime/app.py`,
  `dashboard_api.py`, `pipeline.py` ×2, `mcp_bridge/spine.py` ×3,
  `db/build_plan.py` ×2 (default parameters, not queries),
  `sync_project_state.py`, and the seeder.
  **`relay.py:1068` was the only site that kept working — because of the
  `COLLATE NOCASE` this item called a workaround.** It was the one place that had
  adapted to the disagreement. Called "dead weight" in this item hours before it
  turned out to be the sole survivor; the note above it stands corrected.
  **WHY THE DUAL REVIEW DID NOT CATCH IT: the packet told both advisors
  "Writers of build_plan_nodes in production code: NONE (only tests)."** That was
  false. `runtime/db/build_plan.py:19` writes via `INSERT OR IGNORE INTO`, which
  a grep for `INSERT INTO` cannot see. Two independent lineages reasoned
  correctly from a false premise. **This is the review's real limit: it audits
  the artifact in front of it, and a wrong fact in the packet is invisible to
  both models no matter how many there are.** Fifteen checks passed because every
  one queried the table directly; not one asked whether anything else still could.
  **THE SAME MISTAKE HAPPENED TWICE IN ONE SESSION.** The first enumeration of
  broken sites found 9 and was reported as complete. A second pass by table name
  found 14 — `grep "project_id='CIS'"` cannot see `project_id = 'CIS'` with
  spaces. Both misses are one class: **enumerating a blast radius by statement
  syntax instead of by the object being touched.** Enumerate by table name, then
  classify each hit. See 2.35.
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

**The one check that settles the scope — REWRITTEN 2026-09-06. The original was
backwards.** It read: *decide which surface renders the roadmap before choosing
where the table lives.* That makes a presentation venue the gate on a data
structure. **The UI is a venue for what is already in the DB and the KB; it
cannot be built until the structure is reconciled and functioning.**

The table's location is settled by the **stateless-agent requirement (2.30)**,
not by a surface decision. The check is therefore: **can a stateless agent read
the current item, its dependencies, and the last completion status from one
place?** When that is true the table is right, whatever renders it — and until
it is true, no surface can help.

**This item is not UI work.** 2.30 records why it exists.

**Depends on: 2.13 — folded in, Eric's decision 2026-09-09.** This line read
*"nothing"* until that date and it was false. Both advisor lineages found it
independently on the 3.21 pre-flight packet, from opposite directions and with
no shared prompt beyond the packet itself.

**Why.** 2.30 asks four questions: what is the current item, what does it depend
on, what was just done, and **did it succeed.** A queue table extracted from the
markdown answers the first three. The fourth was to be joined at read time from
`workflow_runs` and `gate_outcomes` — and **there is no join key.** Nothing links
a build-list item number to a run. That missing link is 2.13. As the advisor put
it: this is not a gap in the verification, it is a gap in the design.

**The two are one design.** 3.21 supplies the item, its identity and its
dependencies; 2.13 supplies what became of it. Built alone, 3.21 ships the thing
2.30 was opened to fix, minus the half it was opened for.

**And the fourth question is the Eric-facing half.** The first three serve a
stateless agent picking up work. *Did it succeed* is what Eric reads to know
whether the last thing worked. **A queue that cannot say whether the last thing
succeeded does not replace him as the integration layer** — it just moves where
he has to stand to do it himself.

**Note the shape of 2.13 before building.** It was rescoped 2026-09-07: its
stated symptom pointed at the wrong table, and the fix as originally written
would have passed its own verification while leaving the symptom untouched.
Whatever supplies the join key here must be chosen against that correction, not
against the item's original text.

**Blocks** 4.18 (the card factory needs a table to read) and the UI roadmap.

**BUILT 2026-09-09 — migration `0031_queue_items.sql`, one row per item.** No
count is written here on purpose: the table is regenerated from this file, so any
number recorded in the file it describes is stale the moment an item is added.
Adding 3.28 below took it from 119 to 120 within the same card. The extractor
is `tools/queue/extract_queue_items.py`, the verification
`tools/queue/verify_queue_items.py`, and the first reader
`spine.query_queue_item()` behind the MCP tool `cis_get_queue_item`.
`cis_get_build_status` now redirects on a dotted item number instead of
answering *"No build_plan_node found with label: 3.21"*. Three advisor packets
and a round-3 result review are in `reviews/done/queue-3.21-*`.

**What it answers: ONE of 2.30's four questions**, not three. *What was just
done* — the 10 completion-bearing items. *What is the current item* and *what
does it depend on* need regenerated edges and are marked NOT AVAILABLE in the
reader's own response. *Did it succeed* is absent by decision, `ADR-3.21-001`.

**STANDING OBLIGATION, UNENFORCED — recorded 2026-09-09.** Every edit to
`docs/UNIFIED_BUILD_LIST.md` invalidates `queue_items` until the extractor
re-runs. The table is a projection; the markdown is authoritative; nothing
notices when they part.

`source_sha` makes the drift **detectable, not automatic** — check 8b compares
the stored hash against the file, but only when somebody runs the verifier. **It
happened twice on 2026-09-09** — once adding item 3.28, once adding the two 2.25
records — and was caught by hand both times because the same session that edited
the file also remembered to re-extract. A different session, or the same one an
hour later, has nothing to remind it.

**This is 2.39 pointed at the projection rather than at the queue.** 2.39 is a
human remembering to confirm an item is still not in the code; this is a human
remembering to rebuild a table after editing its source. Same defect, one layer
down, and the same fix shape: a check that runs where a stale projection would do
damage rather than where someone thinks to invoke it. **Three candidate homes:**
`tools/closeout.sh`, the pre-commit hook that already regenerates six files, or
`spine.query_queue_item()` itself — the reader refusing to answer from a
projection whose `source_sha` no longer matches the file. The third is the only
one that protects an agent reading the table between sessions.

**Related:** 2.39 (the same defect aimed at the queue), 2.12 (two copies
drifting is what this prevents, and what it becomes if left alone).

**THE BLIND SPOT WAS DEMONSTRATED WITHIN HOURS — 2026-09-09.** The r3 review
named it: rule 6 catches unknown **values**, not unknown **shapes**. It was
recorded as known-uncovered, and then hit the same day by the person who
recorded it.

Item 2.25's status line read `**Need: BUILT 2026-09-09, ONE-WAY.**` — written by
me that morning. The extractor's second shape matched only the four literal
known tokens, so `BUILT` fell through every branch to **NULL**, and 2.25 was
recorded as *"no status stated"* while plainly stating one. `UNPARSED` never
fired, because it only triggered on the `**Need:** VALUE` shape with an
unrecognised value. **All 32 checks passed**, because 57 NULLs is a normal
outcome and no check knows which items ought to be in that bucket.

**Fixed by making an unrecognised token FAIL rather than fall through.** Both
`**Need:` shapes now capture any token and validate it; anything outside the
vocabulary returns UNPARSED, and UNPARSED stops the run without importing.
Proven by a negative test against a scratch copy: an injected
`**Need: NONSENSE` exits 1, writes **zero** rows, and names the item. A partial
queue is not imported.

**`BUILT` is recognised but stored as `DONE`.** `need_status` carries a CHECK
constraint of five values and `BUILT` is not one of them; storing it literally
needs a schema change. This follows the `RESOLVED -> DONE` mapping already in
the same function — the vocabulary is what the parser can READ, the CHECK is
what the column can HOLD, and `need_raw` preserves the literal either way.
2.25 now reads `need_status=DONE, need_raw=BUILT`.

**STILL UNCOVERED, and this fix does not touch it:** an item stating its status
without a `**Need:` marker at all — Qwen's `"Status: BLOCKED on 2.13"` — is
indistinguishable from an item that genuinely states nothing. Both are NULL and
nothing fires. **The gap narrowed from "any unrecognised status" to "any status
not written as a `**Need:` marker", and it did not close.**

**One more property, found by a negative test that first failed to fail.**
`classify_status` returns on the FIRST marker it finds in an item body, so an
item carrying two `**Need:` lines only ever reports the earlier one. The first
attempt at the negative test injected `**Need: NONSENSE` into item 3.28, which
already had `**Need:** OPEN` above it; the run passed and proved nothing. Not a
defect today — no item has two — but it is a silent precedence rule with no
check.

**THE DUPLICATE-MARKER RULE — added 2026-09-09, second pass.** `classify_status`
returned on the FIRST `**Need:` marker in a body, so an item with two of them
silently reported the earlier one. **Two status claims in one item is not a
precedence question — the item's status is ambiguous, and saying so is the only
honest answer.** A second marker now fires UNPARSED and stops the run.

Detection is anchored to line start, and that detail is load-bearing: **this very
item discusses `**Need:` markers in its own prose nine times inside backticks.**
An unanchored count reads those as nine extra markers and fails the run on a
correct file — a check that cannot survive being written about is not a check.
Verified: anchored, 61 items carry zero markers, 59 carry exactly one, none
carries more; and re-classifying all 120 items against the live table produced
**zero** changes, so the anchoring fixed the counting without moving any status.

**The test that failed to fail, now failing correctly.** Injecting a second
`**Need:` line into 3.28 — which already carries `**Need:** OPEN` — exits 1,
names the item, and writes zero rows:

```
UNPARSED : 1
  3.28   "2 '**Need:' markers in one item — status ambiguous"
```

**RESIDUAL GAP — narrowed twice, still open, and deliberately not closed.**
Status written as prose *outside* any marker — Qwen's `"Status: BLOCKED on
2.13"` — still lands in the NULL bucket beside items that genuinely say nothing.

**What would close it, and why it is not being done.** Closing it means detecting
status prose with no marker to key on, which is guessing at natural language.
**A parser that guesses is worse than one with a stated boundary**: a wrong guess
writes a confident status nobody checks, while a stated boundary produces a NULL
that is honest about what it does not know. The boundary IS the fix. The NULL
bucket is not a gap in the parser; it is the parser declining to invent.

What remains is a convention question, not a parsing one: if statuses must be
written as `**Need:` markers, that belongs in HOW TO WORK THIS LIST, and the
extractor already enforces it for every shape it can see.

**2.25's `BUILT` spelling is left unnormalised on purpose.** Rewriting it to
`DONE` would erase the only live instance of the defect this fix was built
against, and the next reader would find a fix with nothing to test it on.

**THREE LIMITS STAY OPEN. They are known-uncovered, not oversights.**

1. **The partition can be wrong in a way every check accepts.** Checks 7b, 7c
   and 7d were added beyond the design and catch a split, a truncation
   compensated by a neighbour, and a merge that swallowed a marker. GLM gave the
   case that survives all three: **a preamble line absorbed into the preceding
   item's body** keeps the ranges contiguous, non-overlapping, and every marker
   inside a row — and the partition is still wrong. Narrowed, not closed.
2. **109 of the 119 items share the parser's definition.** The 10 hand-read
   completion items are the only evidence no parser produced. If the definition
   of "an item" is wrong, every count agrees with every other count and they are
   wrong together.
3. **The test suite never ran** — see the pytest item in Tier 3. The three test
   files touching these objects were read and their asserted paths fall in the
   unchanged set. That is inspection, not execution.

**What the round-3 result review caught, recorded because it is the point.**
Both lineages returned **NOT_ESTABLISHED** on the first live result review. The
build was sound; the *evidence packet* asserted `ADR-3.21-001` had been written
and showed no query proving it. The row existed. The claim was unevidenced —
**failure mode 1, self-reported completion without evidence, found by the
artifact built to find it.** Check 11 now queries that row, and check 12 resolves
the dashboard's route without a browser.

**A pre-existing routing collision, found while checking the client side and NOT
caused by this change.** Two blueprints register `/api/pipeline/status/<...>`:
`runtime/api/pipeline.py:93` as `<source_id>` and
`runtime/api/pipeline_views.py:37` as `<path:node_label>`. Werkzeug matches the
plain converter first, so a single-segment request reaches the *manifest* route
and `pipeline_views.build_status` is **reachable only for labels containing a
slash**. `cis_dashboard.html:1672` reads `r.found`, which only the manifest route
returns — so the dashboard is consistent today, and would silently render
nothing if the collision were ever resolved the other way. Recorded, not fixed.

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

### 3.25 THE REFERENCE-DOCUMENTS TABLE IS A DEPENDENCY MAP WITH NO EDGE KIND

The `REFERENCE DOCUMENTS` table near the end of this file maps **ten documents to
the items they cover** — 1.3, 1.4, 2.4, 2.5, 2.1, 2.2, 2.11, 2.7, 2.8, 4.3, 3.4,
1.5, 2.9. It is a real dependency map and nothing treats it as one.

**Found the same way 2.32 was:** the 2026-09-06 edge extraction produced edges
from those table rows and I dismissed them as table noise, then the item-by-item
read showed they were not noise. There is no edge kind for *document covers
item* — the proposed `queue_edges` has `depends_on`, `blocks`, `blocked_by`,
`related`, `supersedes`, `same_root`, and no `documents`.

**Needs an edge kind before the next mining pass**, or the same rows get
discarded again by whoever writes the next extractor.

**Scope:** REPO — the queue schema 3.21 creates.

**Need:** OPEN — the table exists, the edge kind does not.

**The one check that settles it:** ask which document covers item 2.8. The answer
is in the file and no query can reach it.

**Related:** 2.32 (the other missing edge kind, same read), 3.21.

### 3.26 DEAD TELEGRAM NOTIFICATION CODE IN THE RELAY

`runtime/abstraction/pipeline_relay.py` carries two notification functions —
`_notify_terminal_failure` (:376) and `_notify_eric_gate` (:431) — that build a
Telegram `sendMessage` call and post it. **They have never fired.**

They read `CIS_TELEGRAM_BOT_TOKEN` and `CIS_TELEGRAM_CHAT_ID`. `entrypoint.sh`
writes `TELEGRAM_BOT_TOKEN` and `TELEGRAM_HOME_CHANNEL`. **Different names**, so
the lookups return empty and both functions take their fallback branch:
`"(no Telegram notification configured)"`.

**This is 2.18's shape exactly** — code that reads as a built feature, degrades
politely, and does nothing. It looked finished for long enough that a session on
2026-09-02 concluded the container had no Telegram path at all, having checked
the `.env` files and the entrypoint rather than the relay.

**NOTE AGAINST 2.25, which settled the feed as HOST scope: this is dead relay
code, not the feed.** Do not read this item as reopening that decision. The two
answers can both stand — the feed is a host-side HTTP POST, and these two
functions are unreachable code that should be either wired to the real variable
names or deleted.

**Scope:** CONTAINER — `runtime/abstraction/pipeline_relay.py`, on the
do-not-modify list.

**Need:** OPEN — both functions present, both unreachable.

**The one check that settles it:** set the two variables the relay actually reads
and force a terminal failure. Either a message arrives, or the code is dead in a
second way as well.

**Related:** 2.18 (placeholders not marked as placeholders), 2.25 (the feed —
separate, settled, host scope).

### 2.38 A SCHEMA CHANGE'S BLAST RADIUS MUST BE ENUMERATED BY OBJECT, NOT BY STATEMENT SYNTAX
**Two misses in one session, 2026-09-07, from the same cause.**

1. `grep "INSERT INTO build_plan_nodes"` missed `runtime/db/build_plan.py:19`,
   which writes via **`INSERT OR IGNORE INTO`**. That miss was then asserted to
   two advisors, in the review packet, as *"Writers of `build_plan_nodes` in
   production code: NONE (only tests)."*
2. `grep "project_id='CIS'"` missed five sites written **with spaces around the
   equals** — including three in `runtime/mcp_bridge/spine.py`, which is what
   the container's agents query for build state.

**Fourteen sites existed.** The first survey found nine and was reported as
complete. The second found all fourteen, and only because it enumerated every
reference to the table **by name** and classified the hits afterwards.

**THE RULE: enumerate by the object being touched — the table, the function, the
file — then classify each reference as read, write, or schema, and for each
read/write record whether it constrains the changed column and with what literal.
Never enumerate by the syntax you expect to find.** A syntax pattern returns the
statements you already imagined; the gap it leaves is invisible, because a grep
that finds nothing and a grep that cannot see look identical.

**THE SECOND HALF, AND IT IS THE LOAD-BEARING ONE.** Migration 0030 passed
**fifteen** verification checks and broke **eight code paths**. Every one of the
fifteen queried the changed table directly. Not one asked whether anything else
still could. **Checks run against the changed object cannot see its callers**, so
a green verification run and a broken system were the same output — and the run
was green enough to commit.

**What to build:** the call-site survey as a required section of any migration's
verification block, not a habit. For any column appearing in a `WHERE` clause:
enumerate every reference to the table, classify each, and record the result in
the migration file. Cheap — one `grep` by object name — and the one time it was
skipped it cost a commit that emptied the context exports.

**This is also the demonstrated limit of dual review, and that is worth more than
the grep lesson.** Both lineages reviewed 0030 competently and neither could have
caught this, because the packet handed them a false premise and **review audits
the artifact in front of it**. A wrong fact in the packet is invisible to every
model regardless of how many review it. More reviewers do not fix a bad input;
they agree about it faster. The survey belongs to whoever assembles the packet,
before it is sent, and no number of lineages substitutes for it.

**Related:** 3.6 (where both misses occurred; the detail is recorded in its
body), 2.18 (a gap that announces nothing), 1.20 (the dual-review measure this
bounds), 2.35 and 2.37 (checks that cannot fail for the reason they exist).

### 3.27 DANGLING CONSUMERS IN THE EXPORT PATH
**Checked 2026-09-07.** Three readers point at files that do not exist:

- `runtime/api/collab_rounds.py:1091` — `PROJECT_CONTEXT_PACK_UPLOAD_GENERATED`.
  **No such directory.**
- `tools/collect_all_material.py:196-200` — **4 of 5 targets missing**
  (`HCP_02_SYSTEM_ARCHITECTURE`, `HCP_03_ACTIVE_WORKSPACE`,
  `HCP_04_DECISIONS_AND_RATIONALE`, `HCP_05_KNOWLEDGE_BASE` — names from an
  older scheme than the generated set).
- `tools/synthesize_full.py:79` and `tools/synthesize_phased.py:60` —
  `HCP_01_INTENTIONS_AND_MISSION.md`. This one **exists**, is **hand-written**,
  dated **2026-08-02**, and is **not one of the 13 generated artifacts**. The
  most misleading of the three: it resolves, so nothing errors, and the caller
  gets a file that no longer tracks the spine.

The directory also holds ten `05_*.md`-style files from **2026-05-19** and eight
`HCP_escalation_*` transcripts from **2026-06-17** — none generated, none in the
manifest, all sitting beside the generated set under the same prefix.

**Why this is Tier 3 and not urgent:** two of the three fail loudly if they ever
run. The third does not, and that is the one to look at first.

**HCP DISPOSITION IS OPEN, NOT DECIDED — recorded so the question is visible.**
The live surface of the whole export pack is exactly two things:

1. `AGENTS.md`'s first 3,000 characters, via `pipeline_relay.py:729` (see 2.36)
2. one `^Status:` line in `HCP_01_CURRENT_STATE.md`, via
   `gate_build_state_coherence.sh:77`

Everything else is committed and checksummed, **which is not the same as read**.
The six role `SKILL.md` files contain zero HCP references; so do the profiles.

**Cost is not the argument.** Full regeneration takes **0.16 s** and fires on
every commit unconditionally. Nothing is being saved by retiring it and nothing
is being spent by keeping it, so the decision has to rest on whether the manual
advisor handoff is still a path worth feeding — which is not readable off disk.

Eric, 2026-09-07: *the docs are not the priority or the truth; the concepts and
functionality are.* Recorded here rather than acted on, in either direction.

**Related:** 2.35, 2.36, 2.37, 3.4 (two manifest directories, canonical status
unresolved).

### 3.24 Corpus and spine share one database — an open question, not work

**This is recorded so it stops being an assumption. It is not a task.** Measured
2026-09-05 against `data/cis_memory.db`:

| category | tables | rows | share |
|---|---|---|---|
| CORPUS (the KB) | 27 | 8,562,850 | 94.5% |
| OPERATIONAL (the spine) | 28 | 6,240 | **0.1%** |
| MINING | 2 | 15,351 | 0.2% |
| OTHER | 20 | 480,439 | 5.3% |
| | **77** | **9,064,880** | |

The operational spine — every run, gate outcome, deliberation round and Eric Gate
approval this project has ever recorded — is **6,240 rows, one tenth of one
percent of the file it lives in**. `gate_outcomes` 4,694, `agent_trajectories`
507, `deliberation_rounds` 361, `workflow_runs` 105, `build_plan_nodes` 30,
`eric_gate_approvals` 29. The 5.9 GB is corpus: `knowledge_messages` 2,647,151
plus its FTS shadows, `dam_extracted_text` 189,161, `observations` 287,712.

**Three consequences, all currently theoretical:**
- Every operational query pays corpus costs. Backup, `VACUUM`, `PRAGMA
  integrity_check` and `foreign_key_check` all traverse 5.9 GB to protect 6,240
  rows.
- The write patterns are opposite. The corpus is bulk-ingested then read-only;
  the spine is small, transactional and constantly updated. They contend for one
  file lock — which is also why 0.3's Chroma arbitration has a SQLite-shaped
  cousin nobody has hit yet.
- A corpus rebuild and a live pipeline run touch the same file.

**Why this is an open question rather than a defect.**
`ARCHITECTURE_VERIFIED_20260824.md:41` records the arrangement as a fact —
*"Spine: data/cis_memory.db, 4.8GB, ~70 tables"* — and no document anywhere asks
whether it should be one file or two. It was never decided; it accumulated. That
is worth knowing before someone treats it as settled architecture in either
direction.

**Do not act on this yet.** The cost is theoretical until something is slow or a
backup fails, and splitting a database that 30+ tools open by path is a large
change for a benefit nobody has felt. Revisit it when there is a symptom.

**One authoritative table count, because three have been in circulation.**
`data/cis_memory.db` has **77 tables**. Not 178 — that figure counted indexes,
triggers and FTS internals from `sqlite_master`. Not 76 — that is the corrected
figure currently in `CLAUDE.md`, off by one. **77.**

**Related:** 2.12 (the `runtime/spine.db` decoy, and why "the spine" needed
settling at all), 0.1 (FK enforcement, which pays the traversal cost described
above), 0.3 (the same contention problem solved for Chroma).

### 3.28 THE TEST SUITE CANNOT BE RUN ON THIS HOST — pytest IS NOT INSTALLED

Checked 2026-09-09 while building 3.21: `import pytest` fails under
`python3.12`, under `/usr/local/lib/hermes-agent/venv/bin/python`, and under
`python3`. There is no interpreter on this host that can execute `tests/`.

**This is 2.15's shape pointed at the tests.** 2.15 records thirty-three of
fifty-one gate scripts that have never fired. A test suite nobody can run is the
same defect: the artifact exists, it is committed, it is cited in review as
evidence — and it has never executed. The 3.21 build cited three test files as
unaffected on the strength of **reading** them.

**What it cost, concretely.** `tools.py` and `spine.py` were both modified on
2026-09-09. `tests/mcp_bridge/test_tools.py`, `tests/mcp_bridge/test_spine.py`
and `tests/ui/test_ui_integration.py` all exercise the changed functions. None
could be run. The change went in on inspection plus a purpose-built verifier,
which is better than nothing and is not a regression test.

**Scope:** REPO — the host's interpreters, not the container's. Whether the
container can run them is unchecked and is the first thing to establish.

**Need:** OPEN — no interpreter on the VM has pytest.

**The one check that settles it:** `python -m pytest tests/ -q` from somewhere,
anywhere, and record which interpreter it was. If the answer is "only inside the
container", that is the answer and it should be written down.

**Related:** 2.15 (gate scripts that never fire — same defect, different
artifact), 2.37 (nothing tests the artifacts for whether anything exercises
them), 3.21 (the build that surfaced it).


### 3.29 Cap MCP tool result sizes and match each profile's tool surface to its role

After reviewers were given read-only MCP instruments, one advisor review ballooned to ~1M prompt tokens (advisor 697,334; evaluator 303,099 on queue-framing-v3). The cost is not the schemas (3.22 already trimmed those) — it is the result size plus the semantic tools. cis_get_recent_runs returns ~27K chars, cis_get_open_decisions ~24K, cis_get_eric_gate_status ~34K, cis_get_dev_pivot_status ~18K, and the three semantic tools (cis_search_semantic, cis_get_similar, cis_search_knowledge) each pay a ~70s torch+sentence_transformers+chromadb cold start (~1.6 GB) plus oversized blobs.

**Scope:** CONTAINER — runtime/mcp_bridge/tools.py + spine.py handlers; per-profile MCP and native tool surfaces in enforcement/mwl-proof-v2/profiles/*.yaml.

**Need: HALF DONE.** Reviewer read-only surface already cut: cis_search_semantic / cis_get_similar / cis_search_knowledge removed from READONLY_TOOL_NAMES (20 to 17 tools). Remaining: add hard result-size caps (row limits + char truncation) to the spine-query handlers, then extend 3.22's per-role audit to the MCP surface and the advisor/evaluator profiles.

### 3.30 Persist review output + token counts to the spine (append-only); fix overwrite bugs

Round-1 review of spine-baseline-discipline confirmed the gap: a before/after claim (e.g. "prompt_tokens 5,118 → 303,099") is unverifiable because the BEFORE lives only in an ephemeral gateway log and the rerun overwrites the response file. deliberation_rounds already has reviewer1_output/reviewer2_output (migrations 0015/0016) but advisor_review.sh never populates them — it writes only reviewer_signal. Token columns do not exist on deliberation_rounds.

**Scope:** runtime/schema/migrations (new numbered migration for prompt_tokens/completion_tokens); tools/advisor_review.sh (write output + tokens, append-only, unique run_id per invocation); runtime/orchestrator.py:306 (INSERT OR REPLACE → append); runtime/mcp_bridge/spine.py:312 (cis_search_sessions sc.created_at bug).

**Need: OPEN.** Card reviews/pending/spine-baseline-discipline.md is V2 (RIGHT_WORK, objections addressed). Not yet implemented.

### 3.31 Two-way report: verdict to Eric's phone, reply releases the stop

pause_notify.py is one-way by design (replies arrive unthreaded; a getUpdates poller is a terminal-tied process the row-based pause 1.21 avoids). Advisor/evaluator bots are now wired (TG1). TG2 makes the report two-way from inside the container: a stop is pushed to Eric's phone, and his "go" reply releases it via the existing --continue path.

**Scope:** tools/pause_notify.py (container-scoped mirror); a reply-consumer process started in enforcement/mwl-proof-v2/entrypoint.sh; advisor_review.sh pause path.

**Need: OPEN.** Card reviews/pending/tg2-two-way-report.md is V2 (spec in review). Not yet implemented.

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

  **PREREQUISITE, and it is the real gate: 1.23.** The loop runs on evidence
  from completed runs — HASE's mismatch set is *proxy said good, oracle said
  bad*, which here is *Menter said done, Verify said fail*. A run completed
  2026-08-30 (`run-e70293544935a92e-1787973534`), but it was a documentation
  task whose three BLOCK-mode verification guardrails all SKIPPED — no code was
  checked, so the mismatch set still has no members. The gate did not open; it
  moved from 1.1 to 1.23. Until a code run completes and Verify fires, the loop
  would have nothing to reason from and would recommend from the code's
  appearance rather than its behaviour. That is guessing with extra steps.

  **Cheapest first step, and the record calls it out as highest value / lowest
  cost:** prompts are hardcoded in `pipeline_relay.py`. Move them to versioned
  files, add `prompt_version` and a run-outcome record, and the mismatch data of
  2.8 starts accumulating on its own. That work is useful whether or not the
  full loop is ever built, and it has no dependency on 1.23 — it is unblocked
  now.

  **Related and already listed:** 2.8 (verification results change nothing — the
  mismatch set is exactly this), 4.4 (no learning loop from approve/reject),
  2.11 (no CIS-task-to-agent-task contract), 1.6 (prompt size unmeasured).
  **Sequencing already on the record:** agents and self-evolution come after the
  deterministic layer is stable — see Decisions to Protect.

  Not applicable from HASE, checked rather than assumed: RL weight training
  (GRPO/PPO, 8×H20) and evolutionary search over hundreds of candidate harnesses
  per phase. Both need infrastructure CIS does not have.

- **NINE MONTHS OF SPECS, NOTHING COMPLETED — WHY THE CONTAINER EXISTS.**
  *Context, not a task.* **Eric, 2026-09-06:** transporting work between models
  by hand, plus stateless amnesia, has never allowed work to get **past the
  current topic**. That is why the same requests recur across nine months of
  documentation with solutions worked out and never finished.

  This is the operator-side statement of the loop 4.9 describes from the
  system's side. 4.9 says undocumented configuration causes failure causes
  recovery causes no documentation causes future failure. This says why the loop
  never broke: **nothing survived the end of a topic**, so every session
  re-derived what the last one had already solved.

  It is the reason the container exists, and the measure of whether it works.
  The 210 specification documents (2.33), the 4,479 mining candidates, and this
  list itself are all artifacts of the same loop — solutions produced and lost.
  Recorded here so the container is judged against ending it, not against
  producing more of it.

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

**The one check that settles the shape — ANSWERED 2026-09-06. It needs
replacing.** `cards/pipeline_cards.db` holds 32 rows and its schema is
`id, title, intent, source_session, source_profile, source_date, priority,
status, times_requested, done_when, not_in_card`. **No `scope`, no
`need_status`, no `evidence_count`, no `candidate_ids`.** It is card-shaped, not
queue-shaped.

**And the generator is destructive by design.** `tools/seed_pipeline_cards.py`
opens with `if os.path.exists(DB): os.remove(DB)` — it deletes and rebuilds the
database on every run, seeded from **five hand-written `cards/inbox/*.md` files
dated 2026-08-02** plus goals hardcoded in the script.

**So "wire the factory to the queue" is a rewrite, not a wiring job.** Pointing
the existing generator at a queue table means replacing its source, its schema
and its destroy-and-rebuild behaviour — at which point nothing of it survives but
the name.

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

### 4.20 Contained-pipeline deterministic-enforcement capability set

**Eric/ChatGPT, 2026-09-20 (CARD 5).** The host-side tooling built in WB.1C
and its Cards 1–4 (`tools/development/`: continuity events, packet
freshness, queue-reference following, discovered-work disposition,
stage-closeout gates, card contracts) proves these controls work for the
EXTERNAL developers (Claude Code, ChatGPT/Codex) building CIS from outside
the container. The contained pipeline itself — the internal DRAFT →
REVIEW → MENTER → VERIFY loop, `card_runner.py`'s own dispatch, the
in-container agents — does not yet have equivalent deterministic
enforcement. This item is the authoritative record of that gap, grouped
rather than split into ten flat top-level items because all ten are one
coherent capability set with one shared governing principle: **never rely
on model compliance where the host can deterministically enforce, reject,
detect, or verify the rule instead.**

**Sequencing, already on the record (4.7):** agents/role theory comes
after deterministic workflows are stable. This item does not reorder that
— it is future work, explicitly not scheduled ahead of the pipeline's own
deterministic layer.

**Scope:** CONTAINED PIPELINE — everything below is about the in-container
system, not the host-side tooling that already exists and is out of scope
here (that work is done, see WB.1C/Cards 1–4 evidence in
`data/agent_handoffs/WB-1C-host-continuity/`).

**Need: OPEN** — none of the ten sub-capabilities below exist inside the
contained pipeline today; each was checked against `runtime/card_runner.py`,
`runtime/abstraction/pipeline_relay.py`, and `runtime/container_app.py`
before this item was written, not assumed absent.

1. **Deterministic discovered-work registry.** The contained pipeline's
   own agents (draft/review/menter/verify) have no structural way to
   record a consequential mid-run discovery — it currently only exists in
   model output/logs. Host precedent: `tools/development/discovery.py`
   (Card 3) — same shape, different environment.

2. **Stage-closeout gate.** No deterministic check currently prevents a
   contained-pipeline stage from being marked complete while blocking
   discovered work remains open. Host precedent: `discovery.check_closeout()`
   / `close-task` (Cards 3–4).

3. **Pipeline advancement gate.** `card_runner.py` dispatches on request;
   nothing currently requires the PRIOR stage's own closeout to have
   succeeded before the next stage starts. A model stating "the prior step
   is done" is not currently checked by the host.

4. **Machine-readable work-card contract.** Contained-pipeline cards are
   prose files (`CARD.md`) today, the same as the host-side cards this
   session has been executing. Host precedent:
   `tools/development/card_contract.py` (Card 4) — declares scope,
   forbidden areas, required checks/evidence, closeout requirement, next
   return point, but does not yet verify actual changes against the
   declaration (see sub-item 5).

5. **Deterministic scope verification.** *(Carries forward WB.1C-R1
   addendum item A, from Card 4's evidence.)* Neither the host tooling nor
   the contained pipeline currently compares actual changed
   files/resources against a card's declared allowed scope, forbidden
   areas, or expected outputs. Required future behavior, where practical:
   compare changed files to allowed scope; fail on forbidden-subsystem
   changes; identify unexpected files; verify required outputs are
   present; produce machine-readable evidence. Not a full sandbox — bounded
   comparison against a git diff / file-list, not process isolation (that
   already exists separately via `runtime/card_runner.py`'s sandboxing for
   dispatched runs).

6. **Production-vs-fixture boundary enforcement.** The host tooling
   already does this for itself (`continuity_store.ProductionGuardError`,
   `mode=ro` reads throughout `tools/development/`) — the contained
   pipeline's own agents have no equivalent explicit, machine-verifiable
   boundary between production and fixture/test state.

7. **Structured deferral.** *(Carries forward WB.1C-R1 addendum item D.)*
   The host-side `discovery.py` (Card 3) already requires
   `EXPLICITLY_DEFERRED` records to carry reason/destination/trigger/
   blocking — but does NOT validate that a stated `destination` is a real,
   existing authoritative task. Checked during Card 5: implementing that
   validation now in `discovery.py` would couple it to queue-lookup logic
   and would reject the many currently-valid free-text destinations
   already in use and tested (e.g. "WB.2" as a loose forward reference,
   not yet a real item) — judged improper coupling for a narrow queue-
   creation card. Captured here instead: the contained pipeline's own
   structured-deferral mechanism (when built) should validate destination
   references against the THEN-authoritative task system from the start,
   rather than retrofitting validation onto references that predate it.

8. **Continuity/freshness inside contained agents.** Bring the host
   mechanism's core property — revision-bound context, stale-state
   detection, explicit reconciliation, no silent overwrite of another
   agent's assumption — into the contained pipeline's own DRAFT/REVIEW/
   MENTER/VERIFY agents, which currently share state without any of this.

9. **Deterministic acceptance evidence.** *(Relates to WB.1C-R1 addendum
   item B, from Card 4's evidence.)* The contained pipeline should capture
   real execution evidence (exact command, exit status, changed resources,
   fingerprints) rather than accepting a model's self-reported completion
   — the same principle `close-task`/`verify-closeout` (Card 4) already
   enforce host-side. A minimal, bounded version of the CONSUMER half of
   this — checking a completion artifact against `verify-closeout`'s real
   answer before trusting it — was implemented host-side in this same
   Card 5 pass (`tools/development/cli.py verify-completion`, see Card 5
   evidence); the contained pipeline's own equivalent remains open.

10. **Independent acceptance / separation of implementation and review.**
    The component that implemented a change should not be the sole
    authority declaring it accepted — already the working pattern for
    THIS session's own host-side cards (Codex/ChatGPT independently
    reviewing Claude Code's work), but not yet a structural property of
    the contained pipeline's own internal review loop, which currently
    relies on the same models across roles rather than a deterministic
    gate or a genuinely separate reviewer.

**Related and already on the record:** 4.6 (a Hermes agent in these
working sessions), 4.7 (role theory sequencing — already answers "not yet,
not until the deterministic layer is stable," which this item does not
contest), 4.10 (the harness self-improvement loop — a different, larger
proposal; this item is about enforcement primitives, not self-modification).

**Evidence:** WB.1C (host mechanism, independently ChatGPT-reviewed PASS,
2026-09-19/20), Cards 1–4 (migration 0039 activated in production, Card 1–2
evidence; discovered-work/closeout, Card 3 evidence, 29/29 tests; workflow
integration/card contracts, Card 4 evidence, 22/22 tests) — all in
`data/agent_handoffs/WB-1C-host-continuity/`. Created via
`tools/queue/queue_add.py` (Card 5), not a raw SQL insert — see
`queue_item_events` for this item's creation record.

### 4.26 Restore AGENTS.md generator headroom

**Discovered during CARD 4 (2026-09-20), carried forward per the CARD 5
addendum.** `tools/export/generate_agents_md.py` enforces a hard
20,000-character ceiling on generated `AGENTS.md` and refuses to write
past it (`ERROR: Output is N chars, exceeds 20000 limit.`, confirmed live
this session). After Card 4's own necessary addition, the file generates
at 19,997 characters — **3 characters of remaining headroom.** Any future
addition to `config/agents_static.yaml`'s prose, by any card or any
session, will now need to trim something else first merely to fit, not
because the new content is unimportant.

**Need: DONE.**

**Do NOT** simply delete existing directives to make room, and **do NOT**
weaken the generator's hard-limit enforcement — both explicitly ruled out
by the card that raised this.

**Preferred solutions (from the originating card, recorded verbatim as
the requirement, not yet chosen between):**
- remove redundant generated prose;
- move detailed workflow documentation out of the bounded instruction
  artifact and reference a canonical project document instead;
- reduce duplication between generated instructions and other maintained
  sources (`CLAUDE.md`, `docs/`);
- establish a compact generated directive layer with linked detailed
  documentation;
- otherwise increase capacity only if the 20,000-character ceiling is not
  itself an intentional host/platform boundary (unconfirmed either way as
  of this item's creation — the ceiling's own rationale was not
  re-derived by Card 4 or Card 5, only its enforcement behavior).

**Required result:** meaningful headroom restored, AND the canonical
durable development rules stay discoverable by future host models — not a
trade of one for the other.

**Why not resolved in Card 4 or Card 5:** both cards' own scope is
narrower (workflow integration/documentation-regeneration; queue-creation
mechanism, respectively) than an audit of ~20,000 characters of existing,
Eric-authored `config/agents_static.yaml` content to judge what is safely
redundant — that judgment call deserves its own bounded pass, not a
rushed trim under a different card's time pressure.

**Evidence:** `python3 tools/export/generate_agents_md.py --dry-run` on
the pre-Card-4 content already showed 19,999/20,000; a first Card 4 draft
addition pushed it to 20,021 and was correctly refused
(`ERROR: Output is 20021 chars, exceeds 20000 limit.`); the final,
twice-trimmed Card 4 addition generates at 19,997. See
`data/agent_handoffs/WB-1C-host-continuity/card4-workflow-integration/EVIDENCE.md`.
A `BEFORE_STAGE_CLOSEOUT` discovery record naming this item as its
destination is filed against task `WB.1` in `dev_continuity_events`
(Card 5) — see `data/agent_handoffs/WB-1C-host-continuity/card5-queue-mechanism/EVIDENCE.md`.

### 4.27 Codex transcript import — blocked on an inspectable Codex transcript source

**Discovered during WB.1C (2026-09-19), carried forward through CARD 5,
corrected in scope by CARD 6R (2026-09-20).**

**Need: OPEN** — genuinely open work, currently blocked on an external
precondition this project does not control, not on missing design or effort.

**What already exists:** `runtime/schema/migrations/0039_dev_continuity.sql`'s
`dev_continuity_transcripts` table and `tools/development/transcript_import.py`
already support explicit transcript import for `source='claude_code'` (reuses
`tools/ingest_claude_code_sessions.py`'s JSONL parser, verified with a real
fixture, 46/46 `test_continuity.py` checks). `source='codex'` deliberately
raises `UnsupportedFormatError` rather than guessing a structure.

**What is blocking this item:** no live Codex chat transcript export/file was
available to inspect during WB.1C, Card 5, or this audit. Building a parser
against a guessed or fabricated format was explicitly ruled out by the card
that discovered this (`data/agent_handoffs/WB-1C-host-continuity/CARD.md`) and
reaffirmed by CARD 6 and CARD 6R.

**Do NOT** invent, guess, or reverse-engineer a Codex transcript format to
close this item. That would produce a parser with no basis for correctness.

**Trigger:** Codex exposes a documented, inspectable transcript export format
(a real file this project can read and structurally verify against). When that
exists, extend `transcript_import.py`'s `source='codex'` branch the same way
`source='claude_code'` was built — inspect a real fixture first, write the
parser against it, then test.

**Why this is a real queue item and not just a discovery-record destination:**
CARD 6R found that dev_continuity_events revision 5 (task WB.1) recorded this
as `EXPLICITLY_DEFERRED` with a destination of "future queue item, not yet
created" — a non-authoritative placeholder, inconsistent with the rule (queue
item 4.20 sub-item 7) that a deferred destination should be a real task. This
item is that real task, created via the sanctioned `tools/queue/queue_add.py`
mechanism (Card 5), so the deferred record now points at something authoritative.

**Evidence:** `data/agent_handoffs/WB-1C-host-continuity/card6r-remediation/AUDIT-REPORT.md`
(Part B1); original discovery at `dev_continuity_events` task=WB.1 revision 5.

### 4.28 Independent review pass for WB.1A, WB.1B-1, WB.1B-2

**Discovered during CARD 6 (2026-09-20), reclassified BEFORE_STAGE_CLOSEOUT
by CARD 6R (2026-09-20).**

**Need: DONE.**

**Problem:** `data/agent_handoffs/{WB-1A-workbench,WB-1B-1-backend,WB-1B-2-runner}/`
each carry only a self-reported `READY_FOR_VERIFICATION` `completion.json` —
no standalone independent reviewer `verification.json` of their own. Their
introduced files were later re-reviewed and passed, but only incidentally, as
part of WB.1B-2A's/WB.1B-2B's/WB.1B-3's own narrower, focused re-reviews (see
`WB-1B-4-activate/evidence.md`'s sha256 cross-check table) — never as a
deliberate independent review of WB.1A/C1/C2 judged on their own original
claims. CLAUDE.md's standing rule ("No completion is accepted from
self-report") and the pattern already used for WB.1B-2A/2B/3 and WB.1C
(R1/R2) both require this before their work is trusted.

**Scope:** An independent reviewer (Codex, matching the WB.1B-2A/2B/3
pattern) reads WB.1A's, WB.1B-1's, and WB.1B-2's own cards, evidence.md and
completion.json, and the files each introduced (per their own `changed_files`
lists), and issues a real PASS/FAIL `verification.json` in each card's own
output folder — not a re-review of what WB.1B-2A/2B/3 already covered a
second time, only the parts of C1/C2/WB.1A's original claims those later
passes did not exercise.

**Blocking classification:** blocks WB.1 stage closeout (this item, per CARD
6R) and separately blocks WB.1B activation (already recorded as a
precondition in the WB-1B-4-AUTH-successor activation card).

**Evidence:** directory listings confirmed absent `verification.json` for
these three cards, CARD 6 (2026-09-20) and reconfirmed CARD 6R (2026-09-20);
`data/agent_handoffs/WB-1C-host-continuity/card6r-remediation/AUDIT-REPORT.md`
Part B3.

### 4.29 Single authoritative CIS state contract (read-model consolidation)

**Proposed 2026-09-21 — Eric's own prioritization; cards drafted by ChatGPT
at his direction, registered here by Claude Code.**

**Need: DONE.**

**Problem:** CIS currently has several independently-generated "current
state" artifacts — AGENTS.md, the HCP packet, the rendered
`docs/UNIFIED_BUILD_LIST.md`, and ad hoc operating-state reports — with no
single enforced authority between them. A live inspection on 2026-09-20/21
already found one instance of drift: CLAUDE.md's documented spine-DB table
count does not match the live database. Building further UI (Braingate,
Card Factory) on top of this risks compounding that drift.

**Scope:** Full spec:
`data/agent_handoffs/CIS_WORKBENCH_RECOVERY_CARDS/CARD_01_SINGLE_AUTHORITY_CONTRACT.md`.
Inventory existing DB-backed authority (queue/discovery/decision/closeout
tables), implement one canonical host-side read model over it (no new
authority table unless a hard gap is proven and documented), and make
AGENTS.md/HCP/build-list/any operating-state markdown explicit projections
of it, never independent truth. No UI in this card.

**Sequencing:** First of a 4-card sequence (4.29-4.32, see
`README_CARD_SEQUENCE.md`). Must independently PASS review before 4.30
starts.

**Blocking classification:** Explicitly precedes resumption of
Braingate/Card Factory UI work (WB.1's remaining slices) — Eric's own
prioritization decision, recorded here rather than left only in chat.

**Evidence:**
`data/agent_handoffs/CIS_WORKBENCH_RECOVERY_CARDS/README_CARD_SEQUENCE.md`,
`CARD_01_SINGLE_AUTHORITY_CONTRACT.md`.

### 4.30 External recovery packet from canonical CIS state

**Proposed 2026-09-21 — Eric's own prioritization; cards drafted by ChatGPT
at his direction, registered here by Claude Code.**

**Need: DONE.**

**Problem:** There is currently no single, deterministic, bounded packet an
external advisor (ChatGPT, or Claude in a fresh subscription session) can
be given to diagnose/repair CIS when internal pipeline/container pieces are
down. Today Eric manually uploads the separately-generated HCP packet,
which is not guaranteed to reflect the same authority as 4.29's read model.

**Scope:** Full spec:
`data/agent_handoffs/CIS_WORKBENCH_RECOVERY_CARDS/CARD_02_EXTERNAL_RECOVERY_PACKET.md`.
Build one host-side recovery-packet generator (full and issue-focused
variants) that draws only from 4.29's canonical read model, works with
Braingate/Card Factory/Card Runner/pipeline gateways unavailable, and
either makes HCP consume this same layer or has this packet supersede
HCP's current-state/next-action portions. No UI in this card.

**Sequencing:** Second of the 4-card sequence (4.29-4.32). Requires 4.29
independently PASS-reviewed and accepted first; must reverify 4.29's
interface still matches its reviewed revision before starting.

**Blocking classification:** Same as 4.29 — precedes Braingate/Card Factory
UI resumption.

**Evidence:**
`data/agent_handoffs/CIS_WORKBENCH_RECOVERY_CARDS/CARD_02_EXTERNAL_RECOVERY_PACKET.md`.

### 4.31 Workbench System Context / Recovery UI

**Proposed 2026-09-21 — Eric's own prioritization; cards drafted by ChatGPT
at his direction, registered here by Claude Code.**

**Need: DONE.**

**Problem:** Eric has no screen today where he can see, in plain English,
what CIS is doing, what is blocked, what just completed, and what to hand
an external advisor — he currently relies on Claude Code producing an ad
hoc report on request.

**Scope:** Full spec:
`data/agent_handoffs/CIS_WORKBENCH_RECOVERY_CARDS/CARD_03_WORKBENCH_SYSTEM_CONTEXT_UI.md`.
Add one Workbench panel ("System Context / Recovery") that calls 4.29's
read model and 4.30's packet generator only — no separate UI-specific
state queries. Must clearly separate authoritative state from observed
live runtime health, degrade honestly on partial failure, and provide
copy/export of the recovery packet. Explicitly excludes resuming Braingate
conversation or Card Factory feature work, dispatching agents from this
screen, or broadening auth.

**Activation note:** unlike 4.29/4.30, this card needs the Workbench UI
shell reachable in a browser to be usable — but only enough to serve this
one panel, not Braingate's chat feature or Card Factory. See conversation
2026-09-21: this is also the natural seam where multi-user
access/authentication (tier 2: workbench control plane + user access,
including the paused Cloudflare/session auth proposal and the
Sunshine+Moonlight+Tailscale remote-access thread) resurfaces — that is
explicitly out of scope for this card and not yet a queued item.

**Sequencing:** Third of the 4-card sequence (4.29-4.32). Requires 4.29 and
4.30 independently PASS-reviewed and accepted first.

**Blocking classification:** Same as 4.29 — precedes Braingate/Card Factory
UI resumption.

**Evidence:**
`data/agent_handoffs/CIS_WORKBENCH_RECOVERY_CARDS/CARD_03_WORKBENCH_SYSTEM_CONTEXT_UI.md`.

### 4.32 Recovery drill, authority audit, and closeout

**Proposed 2026-09-21 — Eric's own prioritization; cards drafted by ChatGPT
at his direction, registered here by Claude Code.**

**Need: DONE.**

**Problem:** Verification/closeout only — proves 4.29-4.31 did not create a
second source of truth and that the recovery path actually works during
partial failure, before returning to feature work.

**Scope:** Full spec:
`data/agent_handoffs/CIS_WORKBENCH_RECOVERY_CARDS/CARD_04_RECOVERY_DRILL_AND_CLOSEOUT.md`.
Single-authority audit across DB/read-model/packet/HCP/build-list/UI;
failure-mode recovery drill (Braingate/Card Factory/pipeline-worker/stale
HCP/dirty git tree/failing health probe) without destructive changes;
generate one real recovery packet and check it's usable by a fresh
external-advisor session; confirm freshness/regeneration behavior; close
via the existing discovery/closeout mechanism. Does not start new feature
work.

**Sequencing:** Fourth and last of the 4-card sequence. Requires 4.29-4.31
independently PASS-reviewed and accepted first.

**Return point:** explicitly recorded in the card itself — after this
closes, the next development return point is resuming Workbench user
workflow work (Braingate conversation first, then Card Factory, then
execution/review/results), not starting automatically.

**Evidence:**
`data/agent_handoffs/CIS_WORKBENCH_RECOVERY_CARDS/CARD_04_RECOVERY_DRILL_AND_CLOSEOUT.md`.
