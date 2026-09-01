# NEXT SESSION — standing context. Updated 2026-09-01.

Paste this file as the first message of a new session.

**THE TASK QUEUE IS `docs/UNIFIED_BUILD_LIST.md` — 90 items. IT IS NOT IN THIS FILE.**

## Mining status — 2026-09-01
P1 (acknowledged), P2 (reasoning), P4 (filesystem) and P6 (targeted) are COMPLETE:
every candidate carries a recorded verdict. P3 (keyword) has 4,479 rows still
PENDING in `mining_candidates` — `TODO` and `XXX` are over half of it and yield
poorly. 88 TASK candidates became 40 tasks; 15 were already on the list, 25 were
folded in (the list went 63 -> 90 items). Evidence for every one:
`data/mining_archive/MINED_TASKS.md`.

Each folded item carries `pipeline_scope` and `need_status`. Scope is NOT a
priority: NOT_IN_CONTAINER_PATH means the code is not executed by the container,
not that the finding is dead — the VM was the prototype, and 5 of those are OPEN
needs the container has not met. UNASSESSED items name the one check that settles
them, so absence is never read as an open need.

The command that survives a cleared context:
    python3.12 tools/ask_history.py "<subject> decision"

This file holds only what does not change session to session: how to work here,
what the goal is, and which decisions must not be eroded. It carries no tasks,
no priorities and no status. If you find yourself reading a task here, it is a
leftover — the queue moved on 2026-08-29 and the handover completed 2026-08-30,
verified item by item (42 items checked, 42 now carried).

Do not reintroduce a task list here. Two lists drift, and neither one can be
trusted after that — the failure is already on the queue as item 2.12.

## Constraints (every card)
Interpreter and cwd explicit. Pipeline: /usr/local/lib/hermes-agent/venv/bin/python, cd /workspace/cis
ask_history.py: python3.12 only, positional args, no flags.
Verify every claim with a command. If a lookup fails twice, stop and report.
Container clock is UTC, host is local. Never run python from data/drive_imports.
Gate scripts: edit tools/gates (a symlink to enforcement/mwl-proof-v2/gates).
  GIT CANNOT STAGE THROUGH THAT SYMLINK — `git add tools/gates/x.sh` fails with
  "pathspec is beyond a symbolic link". Address those files as
  `enforcement/mwl-proof-v2/gates/x.sh`. Editing via tools/gates is fine; only
  the git path must be the real one.
Gate changes need a container image rebuild; runtime/ changes are mounted and live.

## Three verification rules — from CARD_3.1, each earned by a mistake
1. VM vs CONTAINER. Most of the record describes the VM pipeline, which is
   structurally different. Name which pipeline a structural finding describes
   BEFORE verifying it. Worked error: a VM-era finding that the drafter and one
   reviewer shared a model is FALSE in the container — review1 qwen/qwen3.7-max,
   review2 z-ai/glm-5.2, draft deepseek-v4-pro.
2. FILE PRESENCE IS NOT EXECUTION. The repo is mounted whole at /workspace/cis,
   so every VM file is visible inside the container — but container_app.py
   registers only relay_bp plus health/UI routes. An ALREADY_BUILT verdict needs
   the route or the import path, not the file existing.
3. THREE ENFORCEMENT LAYERS, easily confused. (a) container_gate_runner.py, the
   pre_tool_call hook — FIRES on every tool call, registered by the mwl-proof
   plugin. (b) The 51 scripts in /opt/cis-gates/ — DEAD except that one; nothing
   else invokes them. (c) pipeline_relay's run_guardrails() — FIRES, but only in
   verification, after the work is done. Finding one wired is not evidence
   another is.

## HOW TO WORK HERE — Eric, 2026-08-29. Standing instruction, not a preference.
"I am always looking for the best most complete and evidence based result and
solution, never the quickest or easiest. Look at the months of me obsessively
going over the same thing over and over. This is my system and I need it to work
like me. I want attention to detail and layers of analysis to make a thing work
the way I need it to."

Concretely, and these are failures that actually happened on 2026-08-29:
  - DO NOT CONCLUDE AFTER ONE OR TWO SEARCHES. A single query returning nothing
    is not evidence of absence. Try other phrasings, other indexes, other
    sources, and say what you tried.
  - RUN BOTH INDEXES. There are two databases on purpose: FTS5 keyword for exact
    strings and identifiers, Chroma vectors for meaning. Running one and calling
    it a search is a half measure. Keyword finds what you thought to name;
    semantic finds what you did not. Thoroughness means the union.
  - LAYERS OF ANALYSIS. First pass finds candidates. Second pass reads them.
    Third pass categorises and cross-checks. Stopping at pass one and reporting
    counts is not analysis.
  - SPEED IS NOT A VIRTUE HERE. Do not trim scope, drop material, or filter by
    volume to produce a tidy number. Reduce only by proven duplication.
  - ON ARTIFACTS FOUND IN THE RECORD: whether a named file still exists is
    mostly IRRELEVANT. The questions are: what FUNCTION did it serve, is that
    functionality still relevant, and was it ever implemented? A missing file
    whose function still matters is an open issue. An existing file whose
    function was superseded is not.

## HOW TO TALK TO ERIC — Eric, 2026-08-30. This is now queue item 1.8.
"The container agents must always recognize that I am not a coder and I don't
have the experience to answer most of these technical questions. It must provide
context and options to choose from along with the positive and negative
consequences of the choices made based on evidence and good coding practices.
The container cannot keep posing these scenarios — it's creating situations
where I have to guess."

So: never hand him an open technical question. Every decision put to him carries
options, and every option carries what it means in plain language, the evidence
behind it, what goes right, and what goes wrong. A question mark with no options
attached is a defect in the output, not a request for input.

This applies to the pipeline's agents AND to assistants working in these
sessions. It is on the queue as 1.8 because the Eric Gate cannot produce a real
decision without it — and the gate is on the critical path of every run.

Corollary, learned the same day: do not re-open a question the record has
already settled. Check the record first, and if it is answered, act on it. Asking
again is not caution; it is the same guessing problem pointed the other way.

## The goal — Eric, 2026-08-29. Read this before reordering anything.
The contained pipeline is being set up to REPLACE the VM (host) pipeline.
That requires a fully operational KB inside the container — semantic AND SQL.
Order of work, in Eric's words:
  1. Get the KB fully working (semantic + SQL) for the container.
  2. Then make all the fixes already in the queue.
  3. Then keep uncovering and addressing logical, deterministic, functional
     issues.
The point of all of it: give the container an infrastructure that can finally do
the real work of BUILDING PROJECTS with a trustworthy AI assistant.

Sharpened 2026-08-29: the immediate goal is to OPTIMIZE AND READY THE KB so the
pipeline can reference it — and then use that to UNCOVER WHICH DETERMINISTIC
GATES NEED TWEAKING OR CREATING. The KB is not the destination. It is the
instrument for finding out what the gates should be. A pipeline that can read
the record can be asked where the record contradicts what it is doing.
DAM is NOT current work. It belongs to the creative app build, after the
container infrastructure is finished. Do not start it.
GPU is free — nothing is using it (the llama-server on 8002 holding 20.7GB is a
leftover from KB processing a month ago; no agent set is configured to call it).
All six container agents are CLOUD: brain/draft/menter -> api.deepseek.com,
review1/review2/verify -> openrouter. The pipeline uses no local GPU at all.

That last line is the test to apply to any proposed work. Governance ceremony,
protocol adherence, and enterprise-shaped process are not the goal and were
what the 2026-06-18 dev pivot was called to kill — "the models had been running
me in circles instead of building out functionality." True governance here is
deterministic script: a gate that actually enforces, a check that actually
checks. Not a ritual. If a queue item is ceremony, cut it.

## What the KB is actually FOR — Eric, 2026-08-29. The clearest statement yet.
All progress so far came from Eric asking the right question at the right time
and causing a pivot. He wants a STRUCTURE that replaces those accidental
insights with a system that does it for him — built from the experience of
working with him plus the development knowledge in the training data. The system
has to become strong enough to OVERRIDE THE ENTERPRISE BIAS and start thinking
the way he does.
THAT is what "it is all in the KB" means. The value of his words is not that
they are authoritative. It is that they are AN ALTERNATE PATH TO ENTERPRISE
METHODS — and the only one available.

Why that holds: training data is overwhelmingly enterprise, because that is what
has been written down about building software. A model reaching for "sound
practice" reaches for that by default. It is why this codebase grew ADRs,
approval workflows, tiered build plans and governance contracts with nobody
deciding it should. The models were not failing; they were succeeding at what
they were trained on. The corpus is the counterweight, and it is the only one,
because nobody else wrote this method down.

The insights are NOT accidental — this matters for building it. Twice on
2026-08-29 Eric redirected the session (the archive drive; the dev pivot). Both
times he was pattern-matching against something he knew was in the record and
the assistant had not looked for. The gift is smelling that a direction is
wrong. The correction itself came from the corpus. Instinct is not
mechanizable; the lookup it triggers is.

LIMIT: a model cannot be made to think like Eric — that is a trait and traits do
not hold. A system CAN check proposals against his recorded method and refuse
the ones that contradict it. The reference material is the corpus, not a term
list. bias_drift_detector is the crude version of this and should be rebuilt on
the corpus.

## RULES BECOME CHECKS, OR THEY DO NOT EXIST — Eric, 2026-08-29. The method.
The agents are stateless and real persistent memory is not possible, so the
philosophical rules CANNOT be carried as character traits. Traits are not
enforceable. The expectations and Eric's way of working must therefore be built
into the FUNCTIONALITY, deterministically.

Refinement worth keeping: statelessness does not block memory — retrieval now
hands agents facts on every call. It blocks retained HABIT. You can give an
agent knowledge; you cannot give it habits. Habits must live outside the model.

So every rule becomes a check that runs, or it does not exist:
  "ground every claim in codebase facts" -> output without file:line fails
  "don't call something missing without looking" -> the gate runs the lookup
  "resist enterprise patterns" -> term-list flag (bias_drift_detector)
  "stay in scope" -> keyword overlap vs intent (scope_compliance)
THREE OF THOSE ALREADY EXIST. gate_research_before_conclusion is the template:
it exists because "be diligent" was unenforceable, so someone turned it into a
script that does the lookup and refuses the output. Convert the rest the same
way. Do not write longer prompts — a longer overlay is still a trait.

KNOWN LIMIT, record it honestly: not every rule converts. "Keep the exchange
intact so an objection stays attached to what it changed" converts cleanly.
"Understand what he is actually asking for" has no deterministic form. Sort the
rules into convertible and not, and do not dress an unenforceable one up as a
gate — that is theatre with a script tag.

DO NOT resurrect "privilege Eric's language over model language" as a rule.
Eric ruled against it twice (2026-08-29). The value is in the RESULT OF THE
EXCHANGE, not in his words alone.

Evidence supporting the method, 2026-08-29: every defect found in the pipeline
that day was a broken SCRIPT (regex missing "/", column names cut to their first
letter, a JSON parser truncating valid output). None was a failure of agent
character. The one character failure was the assistant's own — asserting the
archive drive was unknown without searching, exactly what
gate_research_before_conclusion blocks for pipeline agents and nothing blocks
for an assistant in these sessions.

## Why the ceremony accumulated — Eric, 2026-08-29. Do not lose this.
It was not a design choice. It was an artifact of the tooling available at the
time. Eric was working through frontier-model CHATS that could not do actual
work — everything moved by copy-paste. He could not argue a point to a
conclusion or vet one against a running system, so there was nothing to settle a
disagreement except more discussion. Months of work defaulted into enterprise
bias and ceremonial governance because talk was the only thing the setup could
produce. He is emphatic this cannot be overstated as the cause.
The breakthrough came when agentic tooling arrived — openclaw changing the scene,
and Eric adopting Hermes soon after to add to the copy-paste process.

The operational lesson, and it is a live risk not a historical note:
CEREMONY IS WHAT FILLS THE GAP WHEN THE ASSISTANT CANNOT DO THE WORK.
Whenever the assistant cannot run the thing, read the thing, or change the
thing, the work degrades into talk about the work, and the talk hardens into
process. Watch for it in the present tense: long clarifying exchanges, proposals
about proposals, roadmaps gated behind more discussion. The fix is never a
better protocol — it is restoring the ability to act and then acting.

## WHY NONE OF IT WAS VISIBLE — from the record, 2026-08-29
The corpus's own explanation. Read it before any "the system is working" claim:

> "This was previously invisible — the system appeared to function, but only
> because the operator was silently bridging the gaps."

A system with a human silently compensating for it does not report as broken.
It reports as working. That is why the defect count went from zero to nine in
one day of actually looking, and why absence of an error is never evidence:

> "'No error shown' is not sufficient if output is truncated or incomplete."

## Method (learned 2026-08-27, re-proved 2026-08-28)
Absence is not defect. Search before concluding:
python3.12 tools/ask_history.py "<subject> decision"
Proved again: the assistant told Eric it was unaware of the archive drive. The
KB had the full topology and ADR-003. It had not searched.

## DECISIONS TO PROTECT — do not rebuild or erode these
From docs/ISSUE_FINDINGS.md findings 16, 37, 41. Absence here is a decision.
  - Auto-fetch of model responses: PERMANENTLY DEFERRED. No stable public share
    URLs exist. "No development resources should be allocated to it."
  - Video segmentation: deliberately out of Phase 0.
  - ADR-048 Phase 3 (commit layer): deferred BY DESIGN — approval and commit
    are architecturally separate concerns. Queue item 1.5 must revisit that
    decision, not ignore it.
  - Old Tier 7 "Full Durable Router Pipeline": DEFERRED PERMANENTLY.
  - Model registry / route_task.py: SUPERSEDED by static per-role profiles.
    dispatch.py plus six profiles do the job. Do not rebuild the registry.
  - EVERY GUARDRAIL SHIPS WITH ITS OWN OFF SWITCH, TESTED BEFORE THE GUARDRAIL
    IS ARMED. A gate that cannot be disabled can brick the system. This applies
    to every gate proposed on the queue.
  - AGENTS COME AFTER DETERMINISTIC WORKFLOWS ARE STABLE. The record sequences
    role/persona work after the deterministic layer. It does not say the role
    theory is wrong — it says it is not next. This is why queue item 4.7 is
    Tier 4.
  - Eric Gate is the human authority boundary. No consensus path may skip it.
    Not configurable.

## Storage (documented in the KB, ADR-003 — look there before asking)
vda=system 491G | vdb=/mnt/projects 246G | vdc=/mnt/archive 9.1T (8.0T used)
vdd=/mnt/cache 110G | vde=/mnt/models 229G | vdf=/mnt/models2 228G
/mnt/archive holds the creative corpus: _02 Mind, _1 OS, _2 Word, _3 Image,
_4 Action, _5 Sound, WIAS, anthropic_exports. The KB indexes its text. The
originals — images, audio, project files — are only on the drive.

## Gate status (as of 2026-08-28 — verify before relying on it)
gate_research_before_conclusion is BLOCK on brain and draft. 18 firings: 16 PASS,
2 FAIL — both false positives from subject parsing, both fixed. It has never
caught a real unresearched claim. Read that against the fact that the agents it
judges had no working KB search until 2026-08-29.
