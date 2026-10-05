# Independent review request — ADR-PIPE-006 review of the Formal Queue Triage

**You are being asked to judge 57 classifications, not to verify a commit.**

The commit that wrote them has already been reviewed and accepted by you from the
GitHub remote. That review answered *"did the write execute correctly and legally?"*
This one answers a different question that the repository review did not and could
not settle: **are the classification values actually justified?**

Those two are deliberately kept apart:

| | MECHANICALLY VALID | SUBSTANTIVELY ACCEPTABLE |
|---|---|---|
| question | was the write structurally and schema-legal, through the sanctioned path, with its audit trail intact? | is the value the right value for this item? |
| settled by | the repository review of `6efc331` / `23f245b` — **done, ACCEPT, REMOTE_VERIFIED** | **this review — outstanding** |

ADR-PIPE-006 exists to test the second one. A mechanically perfect write of a wrong
classification is still a wrong classification, and nothing in the repository review
would have caught it.

---

## 1. The live rule you are enforcing

ADR-PIPE-006 (`project_decisions`, DECIDED 2026-10-01, not superseded) — *"Roadmap and
queue are separate authorities; triage reconciles, it does not merge."* The clauses that
govern this review, verbatim:

> **QUEUE TRIAGE BOUNDARY:** triage occurs AFTER P0 and BEFORE P1. It is a bounded
> mechanical classification pass over the currently unclassified `queue_items` (56 of
> 132 rows carry neither scope nor need_status as of 2026-10-01). NO item redesign
> during triage. NO renumbering or merging simply to satisfy roadmap linkage. NO
> synthetic roadmap `queue_edges`. Structural problems discovered during triage become
> SEPARATELY REVIEWED work, not in-line fixes.

> **SEQUENCE:** finish P0 / WB.1 activation → bounded queue triage → **INDEPENDENT
> REVIEW OF TRIAGE** → P1 (Layer-2 run-plane read model + `/api/workbench/runs`) → the
> already-persisted P2–P6 roadmap.

Its own stated reason for existing names this step as its addition:

> Adds the independent-review-of-triage step, which ADR-PIPE-001 did not carry.

**What ADR-PIPE-006 does NOT define, and therefore what this packet does not assume
for you:** it names no review procedure, no reviewer identity, and no outcome
vocabulary. It requires that the review happen and that it be *independent*. The
procedure below is this packet's proposal for satisfying that requirement; it is not
an authority, and if you think it fails the ADR's intent, say so and that finding
takes precedence over anything written here.

## 2. Why Claude is not performing this review

Claude Code produced all 57 classifications. Every `queue_item_events` row written by
the pass says so in its own note. ADR-PIPE-006 requires the review to be *independent*,
and the project's governing principle on independence is already explicit in
ADR-XDEV-001:

> A developer's own verification of their own work — including this agent's — is never
> independent remote verification.

That clause is scoped to the repository checkpoint, so it does not *literally* govern a
classification review. The default principle **AUTHOR ≠ INDEPENDENT REVIEWER** is
applied instead, for the straightforward reason that an author grading their own
57 judgment calls produces no information. Claude therefore prepared this packet and
**stopped**, without recording a verdict, at `READY_FOR_INDEPENDENT_TRIAGE_REVIEW`.

Nothing in this directory contains a review result. If you find one, that is a defect.

## 3. What you can read from the remote

Repo `digitalgsmp/cis`, branch `master`. The classifications were written at
`6efc331a2a4f9a7a64dbeec8605575a677a06ba1`, which you accepted as part of
`23f245ba98a7de61d878d4399180c545260fc488`.

| path | what it is |
|---|---|
| `docs/review_packets/ADR-PIPE-006-TRIAGE-REVIEW/INDEX.md` | all 57 on one line each, plus the value distributions |
| `…/CLASSIFICATIONS_TIER_1.md` … `_TIER_4.md` | per item: final values, pre-triage state, measured evidence, rationale, and the item's own authoritative text |
| `…/RESIDUAL_PARTIAL_ROWS.md` | the 13 rows that are **not** in this population |
| `docs/UNIFIED_BUILD_LIST.md` | the generated projection of the queue — a projection, never the authority |
| `tools/queue/queue_set.py` | the only sanctioned classification write path; carries the `need_status` and `scope` contracts in source |
| `tools/queue/render_triage_review_packet.py` | the generator that produced the files above |

**The packet is designed so you never need the spine database.** `queue_items` and
`queue_item_events` are untracked SQLite; the generated files carry the verbatim
content of every row you need, so the review is reproducible from the remote alone.
If you find a classification you cannot judge from what is published here, that is a
packet defect — report it as **BLOCKED / INSUFFICIENT EVIDENCE** on that item rather
than guessing.

No secrets are in this packet, and that was checked rather than assumed: a pattern scan
over all six files for OpenAI/Google/GitHub/Telegram/Slack key shapes and PEM private-key
headers returns nothing, and the only strings of 32+ characters present are commit SHAs,
file paths and identifiers. The item bodies are the architect's and prior agents' own
prose; item `1.11` discusses a provider credential being out of credits as a *finding*,
and no credential value appears anywhere.

## 4. Provenance — the paragraph hoisted out of all 57 notes

Every one of the 57 notes opens with the identical paragraph below (57 of 57 carry it;
the generator verifies that count rather than assuming it). It is printed once here and
omitted from the per-item files so that what remains under each item is only that
item's own reasoning.

```
FORMAL QUEUE TRIAGE 2026-10-04. Authority: ADR-PIPE-001 defines the two-field pass;
ADR-PIPE-006 bounds it; ADR-PIPE-007 is the standing architect exception permitting it
while P0 closeout is externally blocked; the architect's 2026-10-04 Queue Triage card
authorized this execution after OQ-TRIAGE-003 was independently remote-verified at
81d12aa. PROVENANCE, STATED SO IT CANNOT BE READ WRONG: the architect authorized the
triage OPERATION. He did NOT individually supply this value. The classification was
derived by claude-opus-5 from the item's own recorded text plus the measured code facts
carried in this row's evidence field, prepared as the 56-item proposal of record and
applied here unchanged unless this note says otherwise. This is a MODEL-DERIVED
CLASSIFICATION UNDER ARCHITECT-AUTHORIZED OPERATION -- not an architect classification,
not historical extraction, not the ADR-PIPE-009 recovery of item 4.10, and not an
implementation claim.
```

**Read that as the central thing under review.** Eric authorized the *operation*. The
57 values are the model's. Whether a model was entitled to pick each particular value —
rather than route it to the architect — is a question this review is meant to answer,
not a question the triage already settled.

## 5. The vocabularies, and where their meaning comes from

### `need_status` — a closed set

`queue_items.need_status` carries a `CHECK` constraint permitting exactly ten values.
No value was invented; nine of the ten were available and six were used.

| value | meaning as this project uses it | used in the 57 |
|---|---|---|
| `OPEN` | the capability is not in the code and the next action is work | 43 |
| `NEEDS_ERIC` | the next action is an architect decision, not work | 9 |
| `HALF_DONE` | part of the item is built and evidenced; the rest is not | 2 |
| `DONE` | the item's stated need is satisfied, with evidence | 1 |
| `UNCLEAR` | the item's own record does not establish what is being asked | 1 |
| `NO_CHECK_WRITTEN` | the item names no verifiable check, so no check exists to run | 1 |
| `UNASSESSED` | not measured | 0 |
| `PARTLY` | legacy partial marker | 0 |
| `PRESENT_UNPROVEN` | code exists; the contract is not demonstrated | 0 |
| `UNPARSED` | recovery sentinel: a marker is present but unreadable — never a triage value | 0 |

Five of these (`DONE`, `OPEN`, `PARTLY`, `PRESENT_UNPROVEN`, `UNCLEAR`) are in
`queue_set.py`'s `EVIDENCE_REQUIRED` set and cannot be written without evidence or a
note; the write path enforces that, so the presence of evidence is mechanical and not
itself a sign of care.

There is no `NEEDS_ARCHITECT_DECISION` value in this schema. `NEEDS_ERIC` is the
existing equivalent and is what the pass used wherever it judged the next action to be
a decision.

### `scope` — free text by deliberate design

`scope` has **no** `CHECK` constraint and must not grow one: of the 63 values already
on the table before this pass, four were bare prose. `queue_set.py` therefore enforces
a *convention*, reports departures from it as a note, and writes the value anyway:

```
CONTAINER   REPO   REPO/CONTAINER   HOST   NOT_IN_CONTAINER_PATH   UNDETERMINED
```

The build list states what the distinction means: *"Scope says whether the finding was
verified against the container in production or against code the container does not
execute; the latter is not the same as irrelevant."*

Hard limits the write path does enforce: single line, non-blank, ≤300 characters. All
57 comply.

Distribution across the 57: `CONTAINER` 27, `REPO` 14, `UNDETERMINED` 7,
`REPO/CONTAINER` 4, `REPO/HOST` 3, `HOST` 2.

## 6. Methodology the pass claims to have followed

Stated here so you can test the classifications against it rather than against a
standard the pass never adopted:

1. **Both fields, one write.** `queue_set.py` was invoked once per item with `--status`
   and `--scope` together, so no row could half-land. 114 events across 57 distinct
   items; no raw SQL wrote a classification.
2. **Measured facts over the item's prose.** Where an item's body describes a
   capability and the code does not have it, the measurement decides. The evidence
   block on each item is the measurement.
3. **Population by reconciliation, not by count.** The prepared proposal covered 56
   items; the live awaiting-triage population was 57. The extra row, `4.10`, was proven
   to be the only delta by set comparison before anything was written, and the enforced
   invariant was *complete live-population coverage*, not the number 57.
4. **Evidence currency proven, not assumed.** The proposal measured at `99b1c30` on
   2026-10-03; the write happened at `81d12aa`. The diff between them touches no file
   under `runtime/abstraction/`, `runtime/api/`, `enforcement/` or `config/`, so none of
   the code these classifications assert about had changed.
5. **No edges, no redesign, no renumbering.** `queue_edges` unchanged at 45 with an
   identical hash.
6. **No widening of the population.** Rows already carrying one of the two fields were
   left alone, because ADR-PIPE-001 bounds the pass to rows carrying neither and
   ADR-PIPE-006 forbids item redesign.

## 7. Item 4.10 — the one item the prepared proposal never covered

`4.10` is the only classification with no proposal behind it, so it is the one most
worth your attention.

It entered `queue_items` on 2026-10-04 through ADR-PIPE-009 clause 8 as **content
recovery** of an item the original extraction had silently dropped, with both
classification fields deliberately left NULL so that recovering an item could not be
mistaken for classifying one. The triage then classified it `OPEN` /
`CONTAINER — the hardcoded prompts in runtime/abstraction/pipeline_relay.py; the
guidance/evaluation boundary spans guardrails.py and the gate scripts`.

The three claims to test, all stated in full in `CLASSIFICATIONS_TIER_4.md`:

- **`OPEN` and not `NEEDS_ERIC`** — on the grounds that the one architect-shaped
  question (the guidance-versus-evaluation boundary) is *already decided inside the
  item's own text*, which puts the guardrails, gate scripts, verifier and Eric Gate off
  limits to self-recommendation and gives the reason. Is that reading of the item's text
  correct, or did the model absorb a decision that was still Eric's?
- **not `DONE` and not `HALF_DONE`** — on measurement: `prompt_version` appears 0 times
  under `runtime/` and `tools/`, the agent prompts remain inline, and the only match for
  any self-improvement token anywhere is a string inside a test file.
- **`CONTAINER`** — on the grounds that the Claude-API implementer half of the design
  has no implementation anywhere to scope.

## 8. Where the pass itself says it made a judgment call

Four items record, in their own rationale, that `OPEN` was chosen *over* `NEEDS_ERIC`.
That boundary is where a model is most likely to have quietly made an architect's
decision, so these four are surfaced rather than left for you to find:

| item | the claim the rationale makes |
|---|---|
| `1.10` | the item states its own step 1 is unblocked and that its open decisions do not block it |
| `3.11` | the item's own stated action is "verify or retire it" — both are work, so `OPEN` |
| `4.7` | future work whose sequencing gate is already recorded is open work, not an open question |
| `4.10` | as §7 above |

Surfacing them is not a concession that they are wrong. It is the reverse of useful
review to have the author hide its own close calls.

## 9. Observations this packet makes about itself

Mechanical facts, offered so you are not asked to re-derive them. None is a verdict.

1. **Three scope values depart from the recorded convention.** `3.2`, `3.12` and `4.5`
   open with `REPO/HOST`, which is not one of the six convention tokens. `queue_set.py`
   printed its departure note and wrote them, as designed. The precedent for a compound
   token exists — one pre-existing row carries `REPO/CONTAINER` — but `REPO/HOST` is new
   with this pass. Whether a new compound is legitimate scope vocabulary or a convenient
   label is a judgment for you.
2. **Seven items carry `UNDETERMINED` scope.** `2.13`, `2.14`, `2.16`, `3.8`, `3.24`,
   `4.3`, `4.7`. `UNDETERMINED` is a convention token and an honest answer when the item
   does not establish where the work lives — and it is also the easiest place to hide a
   scope assignment that was never actually made. Each carries a reason; test them.
3. **Exactly one `DONE`.** `1.2`, resting on two SQL reads of `eric_gate_approvals` and
   `workflow_runs`. It is the only classification in the pass that asserts work is
   finished, so it is the cheapest one to falsify and the most damaging if wrong.
4. **Nine `NEEDS_ERIC`.** `2.1`, `2.13`, `2.16`, `3.7`, `3.12`, `3.24`, `4.3`, `4.5`,
   `4.6`. The failure mode in this direction is the mirror image: parking work as an
   architect decision when the item already says what to do just defers it with extra
   ceremony.
5. **Five dependency relationships were identified and deliberately not written.**
   `2.7→2.6`, `4.1→1.22`, `4.9→2.18`, `1.8→`the 2026-09-04 recommendation standard, and
   `4.10→1.23`. ADR-PIPE-006 puts edge creation outside this pass, so they are reported.
   If you think any of them should have been written anyway, that is a finding against
   the ADR's boundary, not against the triage.

## 10. The 13 rows that are not under review

`RESIDUAL_PARTIAL_ROWS.md` lists 13 rows carrying `need_status` with `scope` still
NULL. **They are not reviewed triage output and must not be treated as such.** They were
never in the population: ADR-PIPE-001 bounds the pass to rows carrying *neither* field.
Six of them (`4.20`, `4.28`–`4.32`) are precisely the rows whose `scope` ADR-PIPE-009
proved the old recovery path had fabricated out of wrapped prose, and their NULL is the
honest value a human chose.

Queue counters are published in pairs — `awaiting triage 0` beside `fully classified
120` of `133` — so that triage completion cannot be claimed from one number.

## 11. What to evaluate

At minimum:

- `scope` — does it represent actual architectural placement, or a convenient label?
- `need_status` — is each use consistent with the semantics in §5?
- is every `DONE` claim actually supported by its evidence?
- is destination architecture anywhere classified as implemented?
- were uncertain items converted into false certainty — or the reverse, was certainty
  laundered into `UNCLEAR` / `UNDETERMINED` / `NEEDS_ERIC` to avoid a call?
- were architect decisions made by the model?
- does any classification contradict the item's own authoritative text (published with
  it, so this is checkable without the database)?
- does any classification contradict the measured implementation state?
- is `4.10` defensible?
- does any classification require correction **before** the triage can be accepted?

## 12. How to answer

ADR-PIPE-006 defines no outcome vocabulary, so these four are proposed. Use whichever
you judge correct and name it explicitly:

| outcome | meaning |
|---|---|
| **ACCEPT** | all 57 are substantively acceptable |
| **ACCEPT WITH NON-BLOCKING OBSERVATIONS** | nothing needs correction before proceeding; follow-ups exist |
| **CORRECTIONS REQUIRED** | one or more classifications are substantively unsupported or wrong — name them |
| **BLOCKED / INSUFFICIENT EVIDENCE** | the classifications cannot be judged from what is published |

Please also state, whatever the outcome, whether this review satisfies ADR-PIPE-006's
independent-review-of-triage step, since that step — not P0 — is what gates P1.

**A finding is not a mutation.** If you judge a classification wrong, say so and say
why; the correction is a separately governed write through `queue_set.py`, performed
under its own authorization with its own audit event. Nothing in this review changes a
classification, and no classification will be quietly adjusted because a reviewer
raised a doubt.

## 13. What this review does not touch

P0 remains `ACTIVATED / CLOSEOUT BLOCKED` and is blocked on architect actions only:
Eric rotating `DEEPSEEK_API_KEY`, a runtime restart, a real Brain reply, and a real
browser login plus one real conversation turn. This review neither advances nor
unblocks any of that. Accepting the triage does not complete P0, does not activate P1,
and does not implement any destination architecture. ADR-PIPE-007 is explicit that the
triage exception is operational and temporary and must not become permanent roadmap
semantics.

---

*Hand-written review brief. The evidence files beside it are generated from the spine by
`tools/queue/render_triage_review_packet.py` and carry a DO-NOT-EDIT banner; this file is
the only one in the directory written by hand.*
