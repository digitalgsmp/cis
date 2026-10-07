# KB SOURCE COVERAGE + DEVELOPMENT-HISTORY RECOVERY REPORT

**Measured at** `bf01df4d45a9de8981c2d057cf629e4cd24ba514` · **2026-10-07** ·
read-write on the knowledge base only, read-only on everything else.
No reconstruction. No P1. No Hermes change. No WIASW implementation.

**Eric's concern was correct, and the true shape of the gap was different from
and larger than the one suspected.** The suspicion was that one or two months of
external-developer session logs were missing. What was actually measured: of 70
Claude Code session transcripts on disk, **7 were ingested** — the last ingestion
ran 2026-09-09 and every session since, plus most of September, was absent. On
top of that, **two entire source families had never been ingested at all** — the
352-file `data/agent_handoffs/` tree, which holds every external-development
handoff and review packet including the architecture-recovery packets, and
`docs/review_packets/`, which holds every prior independent review. Twelve of
thirty-seven architecture concepts this card was asked to test returned **zero**
retrieval hits before recovery, including `ADR-XDEV-001`, `ADR-WIASW-002`,
`ADR-PIPE-006`, "three-plane", "REMOTE_VERIFIED" and "recovery packet".

All of that has been recovered. Four source families now measure 100% coverage
with content-hash provenance, a deterministic coverage gate exists and passes on
them, and all twelve dead concepts are retrievable. Two families remain
unrecoverable without an architecture decision: ChatGPT and claude.ai browser
histories, whose only input is a manual account export, last taken 2026-06-13 and
2026-06-25 respectively.

**One prior conclusion is contradicted.** Continuity revision 131's headline — "44%
of docs/ was never ingested, 165 significant files, including
CIS_16_FAILURE_MODES.md, and DEV-PIVOT-17 scores zero on twelve verbatim probes"
— does not survive measurement. True pre-recovery `docs/` coverage was **81.5%**,
not 56%; CIS_16_FAILURE_MODES.md **was** ingested; DEV-PIVOT-17 **was** ingested
and answers all six verbatim probes run here. The over-statement has a specific
and instructive cause, given in section M, and the same cause produced a wrong
number in my own first pass before it was caught.

---

## A. Live State

Read live, not inherited.

| | |
|---|---|
| HEAD | `bf01df4d45a9de8981c2d057cf629e4cd24ba514` |
| origin/master | `bf01df4d45a9de8981c2d057cf629e4cd24ba514` |
| `git ls-remote origin master` | `bf01df4d45a9de8981c2d057cf629e4cd24ba514` |
| All three agree | yes |
| Working tree | 27 entries — 22 pre-existing at session start (16 modified, 6 untracked: the pre-commit hook's regenerated projections plus unrelated notes), 5 added by this card |
| P0 | **COMPLETE AND CLOSED** 2026-10-06, independently REMOTE_VERIFIED by a ChatGPT reviewer reading the GitHub remote; recorded at continuity revision 125 and `project_state.external_dev_checkpoint` |
| P1 | **NOT ACTIVATED.** Sequence unchanged: P0 CLOSED → Queue Triage → independent review of triage → P1 |
| Queue | 133 items; **0 unclassified**, 120 fully classified, 13 carrying scope-only; need_status: 91 OPEN, 15 DONE, 8 NEEDS_ERIC, 11 UNASSESSED, 6 HALF_DONE |
| Build-path read model | phase P0, status `active / blocked`, `state_revision c4f98939f400de3b` |

**Current records this card was asked to find:**

| Record | Where | State |
|---|---|---|
| KB completeness/coverage finding | `dev_continuity_events` **revision 131** (id 152), `unfinished_work` / `BEFORE_STAGE_CLOSEOUT`, blocking | **Addressed by this card.** Core claim confirmed, headline numbers contradicted — section M |
| Reconstruction / architecture-recovery initiative | **revision 126** (open), results at **128**, addendum **130**, deep handoff **132** | Open; awaiting independent ChatGPT architectural review |
| Live security / trust-boundary blocker | **revision 127**, `BEFORE_STAGE_CLOSEOUT`, blocking | **STILL OPEN — untouched by this card.** Two public Cloudflare hostnames reach `localhost:5000`; five of seven blueprints unauthenticated; `relay.py` auth fail-open because `CIS_PIPELINE_API_KEY` is empty |

`closeout-check WB.1` → `ready_to_close: false`, 4 unresolved blockers (revisions
126, 127, 130, 131). Open questions: **OQ-DEVPATH-001** and **OQ-INTAKE-001** both
OPEN; OQ-TRIAGE-001/002/003 RESOLVED. Active blocker rows: `BLK-SEED-004` (Drive
backup integrity unverified) is the only one still marked ACTIVE.

---

## B. Knowledge Ingestion Architecture

Traced from code, not from filenames.

```
SOURCE                  DISCOVERY            INGESTION                 NORMALIZATION          STORAGE / INDEX            RETRIEVAL
docs/**.md|txt          os.walk             tools/kb/ingest_files.py   paragraph→sentence     knowledge_messages (SQLite) ask_history.py  → Chroma
data/agent_handoffs/**  os.walk              (was: catalog/             chunks ≤900 chars      + knowledge_messages_fts    pipeline_relay  → FTS5 + Chroma
cis_kernel/**           os.walk               convert_to_knowledge.py,  (embedding model        (FTS5, trigger-synced)       (merged, both)
                                              one-shot, no dedup)       truncates past ~1k)   + Chroma "knowledge_messages"
~/.claude/projects/     glob (2 patterns)    ingest_claude_code_        exchange pairs,         (local MiniLM-L6-v2)
  */*.jsonl                                   sessions.py               ask repeated on
  */*/subagents/*.jsonl                                                 continuations
~/.hermes-*/sessions    glob                 ingest_hermes_sessions_v2  exchange pairs         (same two stores)
ChatGPT export .zip     manual               catalog/ingest_chatgpt_only
claude.ai export .json  manual               catalog/convert_to_knowledge
```

**Provenance.** `source` names the family, `source_key` names the source unit.
Three key conventions coexist in `cis_docs` — `path`, `path:N`, and `path:N#rM` or
`path#rM` after `tools/rechunk_for_embedding.py` split a row to fit the embedding
model. This is the direct cause of the mis-measurement in section M.

**Deduplication / update / supersession.** Before this card: the session ingester
was idempotent by `source_key`; the document loader was **not**, and had no change
detection and no provenance at all — running it twice duplicated every row it had
already written, which is why `docs/` had no safe top-up path for six weeks. The
rechunker deletes the row it replaces. Nothing recorded a content hash, so
"ingested then edited" was indistinguishable from "ingested and current".

**Secrets.** `filter_for_index()` drops offending chunks at Chroma index time;
`redact_secrets()` masks on **every** read path — `ask_history.py` and
`pipeline_relay.py:_add_hit()`. SQLite retains raw text; the mask is at the
boundary, not in the store. Both existing gates pass (section H).

**Scheduling.** **There is none.** No cron entry, no systemd timer, no hook, no
`.claude/settings` automation invokes any ingester. The single `@reboot` crontab
line runs `runtime/extractor_daemon.sh`, which is a different pipeline (DeepSeek
extraction into `observations` / `mining_candidates`) and writes no
`knowledge_messages`. Every ingestion in the corpus was run by hand. That is the
root cause of every freshness gap in section D, and it is the finding behind the
gate in section H.

**Two-layer model, and why it matters here.** `runtime/docs/CIS_CONTEXT_CONTRACT.md`
(APPROVED, 2026-05-26) defines Layer 1 — structured state (SQLite tables, HCP,
decision logs) answering *what is true now* — and Layer 2 — raw chat/session
content answering *why*, retrieved semantically. **The ADRs being absent from
`knowledge_messages` is by design, not a defect**: they are Layer 1, reachable
through `project_decisions`, `/api/relay/kb/decisions`, AGENTS.md and the HCP
export, all gated by `gate_export_agreement.sh`. What had failed is Layer 2.

---

## C. Source-Family Inventory

| | Family | Where it lives | Pre-recovery state |
|---|---|---|---|
| A | Repository documentation | `docs/**` | Partially ingested; whole subtrees absent |
| B | Authoritative DB records | `project_decisions`, `project_state`, `open_questions`, `dev_continuity_events`, `queue_items` | **Layer 1 by design** — not in retrieval, correctly |
| C | Claude Code development history | `~/.claude/projects/*/*.jsonl` + `*/*/subagents/*.jsonl` | **7 of 70 sessions**; last run 2026-09-09; subagent transcripts structurally unreachable |
| D | ChatGPT / Codex history | `/mnt/backup-win/chatgtp_data.zip` | Frozen at the **2026-06-13** export |
| D′ | ChatGPT reviewer verdicts | `dev_continuity_events` (9 rows) | Present as Layer 1 authority |
| E | Other external reviewers | `docs/_GLM 5.3 …`, `_QWEN 3.7 …`, `advisor_loop` (62 rows) | Review text on disk, not ingested; `advisor_loop` in SQLite but **not in Chroma** |
| F | Hermes history | `~/.hermes-*` (3,664 files) | 176k chunks ingested through 2026-09-07; 171,731 further chunks available |
| G | `cis_kernel` | `cis_kernel/**` | 476 of 1,311 documents; the entire `extraction/functional_intents/` subtree absent |
| H | Handoff / recovery / review material | `data/agent_handoffs/**` (352 files), `docs/review_packets/**` | **Zero rows. Never a source family.** |
| I | Conversation archive mechanism | — | No intentional mechanism; see section I |

**Authority classification, as recorded in `config/kb_source_policy.yaml`:**

- **authority** — `authoritative_db_records` only. No filesystem family may claim
  it; a test enforces that.
- **evidence** — `external_dev_handoffs`, `cis_kernel`, `claude_code_sessions`,
  `chatgpt_sessions`, `claude_ai_sessions`.
- **mixed** — `repository_docs`. `docs/` holds accepted decisions, superseded
  proposals and working notes side by side; membership implies nothing about
  currency.
- **projection** — `cards`.
- **transient** — `runtime_logs`, `hermes_sessions`.

Ingestion confers none of these. The class is declared in the policy and carried
through the coverage matrix precisely so retrieval output can be read correctly.

---

## D. Coverage Matrix

Machine-readable: `coverage_matrix.json`. Human-readable: `coverage_matrix.txt`.
Regenerate either with `python3 tools/gates/gate_kb_source_coverage.py [--json]`.

**BEFORE (measured 2026-10-07, before any write):**

| Family | Expected | Location | Eligible | Ingested | Missing | Coverage | Newest source | Newest ingested | Staleness | Mechanism | Authority |
|---|---|---|---|---|---|---|---|---|---|---|---|
| repository_docs | yes | `docs/` | 493 | 402 | 91 | **81.5%** | 2026-10-06 | 2026-08-29 | **38 d** | manual bulk, non-idempotent | mixed |
| external_dev_handoffs | yes | `data/agent_handoffs/` | 236 | **0** | 236 | **0.0%** | 2026-10-06 | — | never | **none** | evidence |
| cis_kernel | yes | `cis_kernel/` | 1,311 | 476 | 835 | **36.3%** | 2026-10-07 | 2026-08-29 | 38 d | manual bulk | evidence |
| claude_code_sessions | yes | `~/.claude/projects/` | 74 | 7 | 67 | **9.5%** | 2026-10-07 | 2026-09-09 | **28 d** | idempotent tool, unscheduled | evidence |
| chatgpt_sessions | yes | manual export | — | — | — | **NOT MEASURABLE** | 2026-06-13 | 2026-08-29 | ~4 months | **PATH MISSING** | evidence |
| claude_ai_sessions | yes | manual export | — | — | — | **NOT MEASURABLE** | 2026-06-25 | 2026-08-29 | ~3.5 months | **PATH MISSING** | evidence |
| hermes_sessions | no (policy) | `~/.hermes-*` | 3,664 files | — | — | not required | live | 2026-09-07 | 30 d | tool exists | transient |
| authoritative_db_records | no | spine tables | — | — | — | **NOT MEASURABLE — by design** | live | n/a | n/a | Layer 1 projections | **authority** |
| cards | no (policy) | `cards/` | — | — | — | excluded | 2026-09-17 | — | n/a | n/a | projection |
| runtime_logs | no | `logs/`, `*.jsonl` | — | — | — | excluded | live | n/a | n/a | n/a | transient |

**AFTER (gate output, same command):**

| Family | Coverage | Eligible | Ingested | Missing | Status |
|---|---|---|---|---|---|
| repository_docs | **100.0%** | 493 | 493 | 0 | OK, full sha256 provenance |
| external_dev_handoffs | **100.0%** | 237 | 236 | 0 | OK (1 inside the 12 h grace window) |
| cis_kernel | **100.0%** | 1,311 | 1,311 | 0 | OK |
| claude_code_sessions | **100.0%** | 74 | 74 | 0 | OK |
| chatgpt_sessions | — | — | — | — | **INGESTION PATH MISSING — ARCHITECTURE DECISION REQUIRED** |
| claude_ai_sessions | — | — | — | — | **INGESTION PATH MISSING — ARCHITECTURE DECISION REQUIRED** |

Gate verdict: **FAIL**, and correctly so — the two browser-export families are
required by policy and have no mechanism. That is the one honest remaining red.

**Two denominators are deliberately reported as unmeasurable rather than as 0%:**
ChatGPT and claude.ai have no filesystem source to discover, only an account
export. A denominator we cannot see is not the same as material we know is
missing, and fabricating a percentage there would be the exact failure
section 7 of the card warns about.

**Semantic-index coverage.** Chroma holds 493,143 of 2,657,795 rows (18.6%). That
figure is dominated by one family: `archive` contributes 2,186,884 SQLite rows and
only 22,345 embeddings (1.0%). **Every other source is embedded essentially in
full** — `cis_docs` 46,826/46,827, `cis_kernel` 54,110/54,110,
`cis_handoff_packets` 4,176/4,176, `claude_code` 7,538/7,538. The one real gap is
`advisor_loop`: 62 rows in SQLite, **0 in Chroma** — keyword-reachable, not
semantically reachable.

---

## E. Last-60-Days External Development Coverage (2026-08-08 → 2026-10-07)

152 commits. 153 continuity events, **all of them after 2026-09-20** — the
WB.1C continuity mechanism did not exist before that date, so the first six weeks
of this window have no structured development record at all and were represented
only by git and by un-ingested transcripts.

| Window | Activity | Durable representation | Classification |
|---|---|---|---|
| 2026-08-08 → 09-19 | 97 commits, ~35 Claude Code sessions, no continuity records | git + `project_state` only; transcripts un-ingested | **AUTHORITY REPRESENTED / HISTORY MISSING** → now **FULLY REPRESENTED** |
| 2026-09-20 → 09-30 | 74 continuity events, 19 commits | continuity + git; transcripts un-ingested after 09-09 | **PARTIALLY REPRESENTED** → now **FULLY REPRESENTED** |
| 2026-10-01 → 10-07 | 79 continuity events, 19 commits, 9 ChatGPT reviewer verdicts | continuity + git + packets, packets un-ingested | **AUTHORITY REPRESENTED / HISTORY MISSING** → now **FULLY REPRESENTED** |

**Per-developer:**

| Developer | Evidence on disk | Pre-recovery | Post-recovery |
|---|---|---|---|
| Claude Code (implementation agent) | 70 session transcripts + 6 subagent transcripts, 88 MB, 2026-09-13 → 10-07 | 7 sessions. 63 missing | **74/74. 4,433 new chunks** |
| ChatGPT (independent reviewer) | 9 `dev_continuity_events` verdicts, 2026-10-05 → 10-07; 18 review packets under `docs/review_packets/`; browser history not exportable without a manual action | Verdicts present (Layer 1). **Packets: 0 rows.** Raw reasoning: last export 2026-06-13 | Packets **100%**. Raw browser reasoning **still missing — no path** |
| GLM 5.3 / Qwen 3.7 (adversarial reviewers) | 7 review `.txt` files in `docs/`, 2026-09-10 | not ingested | ingested with `repository_docs` |
| Hermes gateway models | 3,664 session files | 176k chunks through 2026-09-07 | unchanged — deliberately, section F |
| Eric (architect) | operator turns inside every transcript | 7 sessions' worth | all 74 |

**Three sessions were classified NOT DURABLY REPRESENTED and are now recovered:**
the 2026-10-06 architecture-recovery session (revisions 126–130), the 2026-10-07
deep-architecture-handoff session (revision 132), and the 2026-10-06/07 KB
integrity audit (revision 131). In each case the continuity row preserved the
*verdict* and the packet on disk preserved the *reasoning* — and the packet was
not retrievable. That is the precise shape of the gap: **authority survived,
causality did not.**

---

## F. Missing Development History

Ranked by architectural value, not volume.

1. **`data/agent_handoffs/` — 352 files, 29 handoff directories, zero KB rows,
   never a declared source family.** This is the single largest finding. It holds
   `ARCH-RECOVERY-01-three-plane/ARCHITECTURE_REVIEW_PACKET.md`,
   `CIS_DEEP_ARCHITECTURE_HANDOFF_FOR_CHATGPT.md`, `ADDENDUM_02_KB_INTEGRITY.md`,
   and the WB-1A/1B/1C/1D and WB-RECOVERY packets — i.e. the entire reasoning
   record of the work that produced the current architecture. The verdicts were
   in `dev_continuity_events`; the reasoning behind them was unreachable.
2. **`docs/review_packets/` — 18 eligible files, zero rows.** Every prior
   independent review, including the ADR-PIPE-006 triage review packet that
   currently gates P1.
3. **63 of 70 Claude Code sessions**, 2026-09-13 → 2026-10-07. The ingester
   existed, was idempotent and was correct. Nothing ran it.
4. **Six subagent transcripts, 2.1 MB**, structurally unreachable: the ingester's
   glob was `~/.claude/projects/*/*.jsonl` and a delegated run writes to
   `<project>/<session>/subagents/agent-*.jsonl`. The tool reported success while
   never seeing them.
5. **`cis_kernel/extraction/functional_intents/` — 835 documents.** The
   per-module functional-intent extractions (`adapter_extraction_analysis.md`,
   `chroma_lock_extraction_analysis.md`, and 20 more) — the closest thing CIS has
   to a per-module design rationale, and directly relevant to a modular
   reconstruction.
6. **`docs/UNIFIED_BUILD_LIST.md`, `docs/DEV-PIVOT_STATUS.md`,
   `docs/DECISIONS/` — zero rows each.** CLAUDE.md names UNIFIED_BUILD_LIST as
   "the task queue… the only one".
7. **ChatGPT and claude.ai raw histories**, frozen at 2026-06-13 / 2026-06-25.
   **Not recovered. No mechanism exists.**

---

## G. Recovery / Re-Ingestion Performed

All through sanctioned paths, all deterministic, no model summarisation anywhere.
`knowledge_messages` went from **2,650,137 → 2,657,795** rows: **87,896 written**,
80,238 superseded or removed.

| Action | Mechanism | Result |
|---|---|---|
| 63 Claude Code sessions | existing `tools/ingest_claude_code_sessions.py`, unmodified | +4,307 chunks |
| 6 subagent transcripts | same tool, after widening `DEFAULT_GLOB` to two patterns | +126 chunks |
| `docs/**` — 349 never-ingested + 144 re-read for provenance | **new** `tools/kb/ingest_files.py` | 25,196 chunks; 100% coverage, full sha256 provenance |
| `data/agent_handoffs/**` | same, new family `cis_handoff_packets` | 4,176 chunks from 236 files |
| `cis_kernel/**` | same | 54,091 chunks from 1,311 files |
| Removed: extractor run log | targeted delete, both stores | −14,211 chunks. `cis_kernel/source/SESSION_LOG.md` is a 12.4 MB append-only daemon log that re-chunks on every run; `closeout.sh` already classifies it as generated. Now excluded by policy |
| Removed: duplicate old-convention `cis_docs` rows | targeted delete, both stores | −1,169 chunks. 144 documents briefly held both their pre-recovery and new chunks |
| **Not ingested — deliberately** | `tools/ingest_hermes_sessions_v2.py --dry-run` | **171,731 chunks withheld.** A ~36% increase in the CIS-relevant corpus of model-execution turns; the sample is *"Reply in one sentence: Hermes Agent is connected to the local llama.cpp backend."* The durable residue of a Hermes run is Layer 1. Declared `required: false` in policy so the choice is visible rather than implicit |

**Why a new ingester was necessary and what makes it legitimate.**
`tools/catalog/convert_to_knowledge.py` is a one-shot bulk loader with no dedup,
no change detection and no provenance: running it again would have duplicated
every row it had already written. `tools/kb/ingest_files.py` does the same job
for the same source names, with the same `source_key` conventions, writing the
same two stores through the same secret filter — incrementally. It is the
existing mechanism made re-runnable, not a new architecture.

**Reversibility.** Every row written is re-derivable from the file on disk, which
is the source. Rollback point recorded before the first write:
`max(knowledge_messages.id) = 3069556`.

---

## H. Coverage / Staleness Gate

`python3 tools/gates/gate_kb_source_coverage.py` — deterministic, exits 0 / 1 /
2, zero model judgement.

Declared once in **`config/kb_source_policy.yaml`**; discovery is from the
filesystem on every run, so adding a document under a declared root makes it
eligible with no edit anywhere. Provenance receipts live in
`runtime/manifests/KB_SOURCE_MANIFEST.json`, mirroring the existing
`EXPORT_MANIFEST.json` pattern that `gate_export_agreement.sh` already uses — **no
new database table, no new migration.**

It detects, with a test for each:

- expected source absent from ingestion
- coverage below the family's declared floor
- a source changed since it was ingested (sha256 mismatch)
- ingested rows carrying no provenance where provenance is required
- a required family with **no ingestion path at all**
- a required family that discovers **nothing** — 0/0 never reads as 100%
- policy, spine or root unreadable → **exit 2, fails closed**

Per-family policy, not one global percentage: `freshness: current | bounded`,
`min_coverage`, `max_age_days`, `grace_hours` (so a transcript being written right
now is not a failure), `min_bytes` (so a 0-byte stderr capture does not hold the
gate red forever and teach everyone to ignore it), `require_provenance`.

Policy values are grounded where authority exists and labelled where it does not.
`repository_docs` inherits its `diagrams/` and `audits/` exclusions from the
existing loader. `external_dev_handoffs` is required because ADR-XDEV-001 and
ADR-XDEV-002 make external-developer work durable only through verification and
visibility. `authoritative_db_records` is excluded citing
`CIS_CONTEXT_CONTRACT.md`'s two-layer model. `cards` and `hermes_sessions` are
marked POLICY-DEPENDENT and currently excluded, with the reason recorded —
**those two are architecture decisions this card declines to make for you.**

**Tests — `tools/kb/tests/test_kb_coverage.py`, 22/22 passing.** Every case builds
its own spine and its own source tree, so a pass means the logic is right rather
than that today's corpus happens to be clean. The suite found three real defects
during this card: a grace-window file driving coverage to 0%, a test writing the
production manifest, and the identity-matching bug in section M.

**Adjacent existing gates, all re-run, all PASS:**
`gate_chroma_secret_filter.py` (7/7 patterns) ·
`gate_chroma_no_secrets_in_results.py` (no secrets in 41 docs across 4
collections) · `chroma_health.check_embedded_chroma_health()` healthy ·
`gate_build_state_coherence.py` · `gate_export_agreement.sh` (13/13 artifacts
match manifest).

**What it does not do.** It does not measure retrieval *quality*, only presence,
currency and provenance. It does not schedule ingestion — see section O.

---

## I. Session-History Ingestion Policy (proposed, not built)

CIS has **no intentional mechanism** for preserving external-development
conversations. What exists is a correct tool nobody runs.

The proposal is deliberately small, because **the right structural home already
exists and is already an accepted open question**: **OQ-INTAKE-001**, under
**ADR-WIASW-004**, names exactly this gap — "general durable conversational
intake, the candidate-to-authority promotion workflow (candidate information →
accepted project knowledge → classified work → sequenced and authorized work),
target traceability… systematic deduplication and reconciliation." A session
ingestion policy is a sub-case of that question, not a new governance family.

| Question | Proposed answer |
|---|---|
| What is retained? | Operator turn + the reply it drew, verbatim. Already what the tool does: the reasoning lives in the **pair**, and keeping one half loses what changed. |
| Raw, summary, or findings? | **Raw pairs for Layer 2; durable findings stay in `dev_continuity_events` as Layer 1.** No model summary — a summary is a claim about a session, and the card's own rule is that ingestion must not manufacture unattributed knowledge. |
| Who creates it? | The ingester, deterministically. No model in the path. |
| Provenance | `source_key = claude_code/<dir>/<session>/<exchange>.<part>`, resolvable to the transcript on disk. |
| Secrets | `filter_for_index()` at index time, `redact_secrets()` on every read. Already enforced by two passing gates. |
| Authority class | `evidence`, declared in policy, surfaced in the coverage matrix. Never `authority` — a test forbids a filesystem family from claiming it. |
| Supersession | A transcript is append-only, so chunks are added, never rewritten. Documents supersede by deletion-and-replace on hash change. |
| Historical vs current | Structural, not heuristic: current truth is Layer 1 (`project_decisions`, `project_state`), sessions are Layer 2. The Source Authority Hierarchy in `CIS_CONTEXT_CONTRACT.md` already ranks "session history" **below** verified database state. |
| Automatic enough that Eric need not remember | **Not yet — this is the remaining gap.** The gate now *detects* staleness within 2 days. It does not *fix* it. Options in section O. |
| Context loss without permanent authority | Sessions are retrievable and explicitly classed as evidence; retrieval merges FTS and semantic hits with source labels, so a reader sees `[claude_code]` and `[cis_handoff_packets]` distinctly from Layer 1 output. |

**Recommended disposition: do not build a subsystem.** Fold the session-history
policy into OQ-INTAKE-001's answer, and in the meantime close the automation gap
with the smallest possible trigger (section O, option 1).

---

## J. Recent Architecture Retrieval Test

37 concepts, exact FTS5 probes against `knowledge_messages_fts`, identical queries
before and after. **Twelve went from zero hits to retrievable. None regressed.**

| Concept | Before | After | Where it is found now |
|---|---|---|---|
| P0 completion | **0** | 9 | evidence + history |
| independent remote verification (`REMOTE_VERIFIED`) | **0** | 131 | evidence + history |
| author ≠ verifier | **0** | 2 | evidence |
| pushed SHA vs accepted SHA | **0** | 27 | evidence + history |
| recovery / failsafe architecture | **0** | 307 | evidence + history |
| external-development continuity | **0** | 231 | evidence + history |
| three-plane | **0** | 62 | history + evidence |
| tool adapters | **0** | 7 | evidence |
| ADR-XDEV-001 | **0** | 31 | evidence + history |
| ADR-WIASW-002 | **0** | 25 | evidence + history |
| ADR-PIPE-006 triage review | **0** | 189 | evidence + history |
| deep architecture handoff | **0** | 43 | history |
| canonical state | 496 | 838 | both |
| queue authority / queue triage | 12 / 1 | 61 / 550 | both |
| Workbench | 7,991 | 10,611 | both |
| Mermaid / architecture visualization | 228 / 2 | 346 / 15 | both |
| ADR-SEED-018 layering | 13 | 72 | both |
| Hermes abstraction / replaceability | 78 / 7 | 99 / 13 | both |
| adapter boundary | 369 | 418 | both |
| provider/model replaceability | 3 | 7 | evidence |
| module contract | 12 | 37 | evidence |
| WIASW / W·I·A·S·W terms | 3,576 / 1,053 | 3,888 / 1,488 | both |
| destination architecture | 2 | 230 | both |
| execution contracts | 384 | 485 | both |
| creative-production control | 1,013 | 1,455 | both |
| professional DCC applications | 57,363 | 58,556 | both |
| harness independence / standalone CIS | 63 / 50 | 75 / 52 | both |
| task contract enforcement | 147 | 228 | both |
| DEV-PIVOT-17 enforcement architecture | 387 | 409 | both |
| 16 failure modes | 253 | 273 | both |
| trust boundary exposure | 102 | 149 | both |
| DeepSeek Harness | 80 | 88 | history only |

**Authority vs history, read correctly.** For every ADR-numbered concept, the
*decision* is in `project_decisions` (Layer 1) and the *reasoning* is now in
`knowledge_messages` (Layer 2). Before this card, 20 of 36 ADRs — every decision
from 2026-09-09 onward, i.e. the entire current architecture — had authority with
no retrievable causal history at all.

**Semantic retrieval confirmed through the surface Eric actually uses.**
`ask_history.py "why must Hermes be replaceable without rewriting CIS"` returns
DEV-PIVOT-05's "The adapter layer is the key. It isolates CIS from Hermes version
changes" as a top hit. `ask_history.py "who verified the P0 completion and why can
the author not verify their own push"` returns `cis_handoff_packets` — a family
that did not exist four hours ago.

**One standing hazard, not fixed here.** `cis_adrs` holds 61 rows of a **legacy**
ADR series (ADR-041, ADR-045, ADR-047, ADR-048) that is semantically retrievable
and authority-shaped, while the *current* series (ADR-SEED / PIPE / XDEV / WIASW)
is Layer 1 and is not. A semantic query for "ADR" ranks the superseded series
first. This is §9's "historical statement overriding current authority" with a
document wearing the costume. Flagged, not repaired: deciding what to do with a
retired ADR series is an architecture decision.

---

## K. WIASW Destination Coverage

**Present and durable as authority.** Six accepted decisions, 2026-10-02 →
2026-10-05:

- **ADR-WIASW-001** — Word · Image · Action · Sound + Web. "WIASW uses CIS…
  **CIS IS NOT THE ULTIMATE PRODUCT DESTINATION. WIASW IS NOT THE CURRENT
  IMPLEMENTATION PHASE.**"
- **ADR-WIASW-002** — "CIS is the generalized deterministic AI and control
  substrate underneath WIASW," owning "execution authorization, **stable
  execution contracts, adapter interfaces**, evidence capture, artifact
  provenance, validation, checkpoints, recovery."
- **ADR-WIASW-003** — deterministic validation ≠ perceptual review.
- **ADR-WIASW-004** — continuous development intake; **recorded as NOT
  implemented**; gap tracked as OQ-INTAKE-001.
- **ADR-WIASW-005** — reference outcome (cross-discipline creative + software
  production; capability-class reference only, explicitly not an instruction to
  reproduce anything).
- **ADR-WIASW-006** — executive development path; **not implemented**; gap
  tracked as OQ-DEVPATH-001.

Causal history now retrievable: "destination architecture" 2 → 230 hits,
"WIASW" 3,576 → 3,888, W·I·A·S·W term co-occurrence 1,053 → 1,488.
`tools/state/destination_architecture.py` exists as a read model and already
distinguishes *recorded* from *activated* destination architecture.

**Status preserved as DESTINATION ARCHITECTURE / CAPABILITY SPECIFICATION.**
Nothing in this card converts a destination capability statement into a present
implementation claim; ADR-WIASW-004 and -006 themselves record non-implementation,
and their gaps are carried as open questions rather than as features.

**One element of the destination specification is NOT in durable authority.**
The statement that *cards are early manual projections of a future structured
Execution Contract rather than authority themselves* appears **nowhere** in
`project_decisions`, `open_questions` or `dev_continuity_events`. After this
card's ingestion it is retrievable from exactly one place — `claude_code`, two
hits, because the card text that states it was itself ingested today. **It is
being carried by this card's own prose and by nothing else.** That is the
difference between an idea that was said and an idea that was recorded, and it is
worth an ADR if ChatGPT agrees the framing is accepted.

---

## L. Execution-Harness Abstraction Evidence

The general requirement — *CIS execution/governance should not be unnecessarily
coupled to one agent harness* — is **ALREADY AUTHORITATIVE as a principle.** A
generic execution-backend contract is **EXPLICITLY A PERMITTED FUTURE
GENERALIZATION, NOT YET SPECIFIED AND NOT AUTHORIZED.**

| Evidence | Source | Status |
|---|---|---|
| "LAYER 3 — HERMES BACKEND: **replaceable execution infrastructure ONLY** — Hermes gateways, Hermes profiles, containers, and model/provider execution configuration." | **ADR-SEED-018**, DECIDED 2026-09-30 | **authoritative** |
| "LAYER 2 — CIS ABSTRACTION / ADAPTER: the CIS-owned boundary between the control plane and Hermes." | **ADR-SEED-018** | **authoritative** |
| CIS owns "stable execution contracts, adapter interfaces… controlled external-tool execution." | **ADR-WIASW-002**, DECIDED 2026-10-02 | **authoritative** |
| "The destination **may GENERALIZE** the Layer-2 to Layer-3 relationship over time toward **CIS-owned stable contracts above replaceable execution backends**, but that is a future generalization of the existing architecture, **NOT a reclassification of currently accepted ownership**, and **nothing here authorizes refactoring Hermes**." | **ADR-WIASW-002** | **destination direction, deliberately not a contract** |
| "The adapter layer is the key. It isolates CIS from Hermes version changes. When Hermes ships v0.17.0 with a new feature, only the adapter changes. CIS methodology stays stable." | `docs/DEV-PIVOT-05`, line 127 | approved historical rationale, **now retrievable** |
| "CIS is a standalone application — its own identity, its own UI… CIS is to Hermes what a SaaS app is to AWS." / "NOT a fork of Hermes — Hermes updates independently." | `docs/DEV-PIVOT-06`, APPROVED 2026-06-27 | approved historical rationale |
| Five-install topology classified `ARCHITECTURAL_BOUNDARY_VIOLATION` | **ADR-SEED-017** | authoritative |

**Verdict: STRONGLY IMPLIED, PARTLY AUTHORITATIVE, NOT CONTRADICTED ANYWHERE,
AND CURRENTLY UNMET IN PRACTICE.** Harness replaceability is a stated property of
Layer 3 and an owned responsibility of Layer 2. A *generic harness contract* is
named as a future generalization and nothing more.

Continuity revision 130 supplies the acceptance test and its current answer:
*can Hermes be updated without changing CIS code?* Today, demonstrably **no**, on
four measured counts — four Hermes source patches still present in both host and
image; host install topology grew from five to eight; `runtime/api/adapter.py` is
built, marked COMPLETE and never registered by the authoritative listener; and
`pipeline_relay.py` hardcodes gateway ports, reads each gateway's private `.env`
and `config.yaml`, and parses Hermes **log files** to infer liveness. Container
Hermes is pinned three months stale at v0.18.2.

**DeepSeek Harness: 88 FTS hits, all historical, none authoritative.** The
substantive ones are Eric's own words in a Claude Code session — *"getting hermes
to work with claude may be where the new deepseek harness can play a role"* —
recoverable only because that session was ingested by this card. There is no
decision, no evaluation and no commitment anywhere in CIS authority. Nothing was
installed, evaluated or adopted here, and this card makes no recommendation on it.

**OQ-ARCH-009**, raised at revision 130 and still unanswered: if the founding
intent held Hermes *outside* the three parts, does promoting "Hermes Backend" to a
first-class plane re-admit as a peer the thing the abstraction was built to hold
at arm's length? That is a reviewer's question, not a conclusion.

---

## M. Architecture-Recovery Delta

| # | Prior conclusion | Verdict | Evidence |
|---|---|---|---|
| 1 | ADR-SEED-018 dependency architecture (L1 UI / L2 CIS adapter / L3 replaceable Hermes) | **CONFIRMED** | ADR text unchanged; causal history now retrievable (ADR-SEED-018 probe 13 → 72) |
| 2 | "Three" denotes four different decompositions — a real ambiguity | **CONFIRMED and REFINED** | "three-plane" 0 → 62 hits. Revision 130's fifth framing (UI / abstraction-app / DB, Hermes *outside*) is the only one supplying a *purpose*, and is now retrievable alongside the other four |
| 3 | Hermes abstraction / replaceability | **CONFIRMED** | Section L. No contradicting evidence found in 87,896 newly searchable chunks |
| 4 | A module contract is needed | **CONFIRMED, evidence base widened** | 12 → 37 hits; `cis_kernel/extraction/functional_intents/` (835 docs) is now retrievable and is the closest thing CIS has to per-module design rationale |
| 5 | Authority model — one authoritative result → automatic projections | **CONFIRMED and sharpened** | The two-layer model held: authority never went missing. **Causality did.** 20 of 36 ADRs had decisions with no retrievable reasoning |
| 6 | Recovery / continuity model | **CONFIRMED** | 0 → 307 hits for "recovery packet"; 0 → 231 for `dev_continuity_events` |
| 7 | External-development verification model (ADR-XDEV-001/002) | **CONFIRMED and strengthened** | ADR-XDEV-001 0 → 31 hits; "author ≠ verifier" 0 → 2; 9 ChatGPT verdicts in continuity |
| 8 | Workbench / Mermaid as generated projections | **UNAFFECTED** | 228 → 346 and 2 → 15 hits; no new contradicting evidence |
| 9 | WIASW destination architecture | **CONFIRMED, one element found undocumented** | Section K: the cards-as-Execution-Contract-projection framing has no authority row |
| 10 | Reconstruction prerequisites | **REFINED** | The KB prerequisite is discharged. Two prerequisites are not: the revision-127 trust-boundary exposure, and two unmeasurable source families |

### The one prior conclusion that is CONTRADICTED

**Revision 131 over-stated the documentary gap by roughly 2.4×, and the cause is
worth more than the correction.**

| Revision 131 claim | Measured |
|---|---|
| "44% of docs/ was never ingested — 253 of 571 files, 165 significant" | **18.5%** — 91 of 493 documents. True pre-recovery coverage **81.5%**, not 56% |
| "CIS_16_FAILURE_MODES.md never ingested" | **False.** 4 pre-recovery rows survive and are directly observable today |
| "DEV-PIVOT-17 scores 0 of 12 verbatim FTS probes — an ACTIVE ADR cites a document unreachable from the KB" | **False.** It held 24 rows before recovery, and all six verbatim probes run here return `cis_docs` hits: "Two enforcement walls", "the constrained agent CANNOT author or edit its own contract", "openable only from inside the locked room", "deterministic local compiler", "Read-only file system", "Enforcement Architecture"+"Process Isolation" |
| "82.6% of rows are exact duplicates" | **CONFIRMED and refined.** 84.2% of rows sit in duplicate groups — but **90.3% of `archive` versus 54.6% of everything else.** The duplication is concentrated in the one family that is not CIS knowledge |
| "source='archive' is 82.5% of the corpus" | **CONFIRMED exactly** — 2,186,884 of 2,650,137 |
| "cis_docs ingestion is a manual batch, last run 2026-08-29, with no trigger and no schedule" | **CONFIRMED exactly**, and true of *every* ingester |
| "The root cause is a missing gate, not a missing script" | **CONFIRMED. This was the correct diagnosis** and it is what this card acted on |

**The cause of the over-statement.** `cis_docs` carries three `source_key`
conventions. A document stored whole by the original loader is keyed `path`; the
rechunker then **deletes that row** and writes `path#r0…#rN`. A matcher that
strips only `:N` and `:N#rM` reduces `path#r0` to `path#r0`, which matches no file
on disk, so **an ingested document reads as never ingested.** 144 of 493 `docs/`
files are keyed that way.

**My own first measurement made the same mistake** and reported 51.9% coverage.
It was caught only because the coverage gate reported 2,269 "orphaned" source
keys, and 2,269 orphans in a corpus that small is not a plausible fact. The
corrected matcher, the arithmetic (493 = 258 `:N`-keyed + 144 `#rN`-keyed + 91
absent), and a regression test for all three conventions are now in the code.

**This does not weaken revision 131's conclusion, and in one respect strengthens
it.** The *qualitative* finding was right and was verified here by substring
probes that are immune to the key-convention problem: `data/agent_handoffs/**`,
`docs/review_packets/**`, `cards/**` and `UNIFIED_BUILD_LIST.md` each held
**exactly zero rows**. The largest gap was not a percentage of `docs/` at all — it
was two entire families that had never been declared. And the deeper point lands
harder for being measured twice: **until today, nothing in CIS could tell you
which of two contradicting measurements of its own knowledge base was right.** A
corpus with no coverage gate cannot adjudicate claims about itself — including
alarming ones. That is exactly failure mode 2 (hallucinated claims masquerading
as facts) operating on the defense built against it.

---

## N. Remaining Knowledge Gaps

1. **ChatGPT browser history — frozen at 2026-06-13.** ChatGPT is where
   independent review happens; its raw reasoning exists nowhere else in CIS. Only
   the verdicts survive, as 9 continuity rows. **INGESTION PATH MISSING.**
2. **claude.ai browser history — frozen at 2026-06-25.** Same shape.
3. **No ingestion is scheduled.** The gate now detects staleness within 2 days.
   Nothing fixes it. Eric still has to run a command — a smaller burden than
   remembering which sources belong in the KB, but not zero.
4. **`advisor_loop`: 62 SQLite rows, 0 embeddings.** Keyword-reachable,
   semantically invisible.
5. **`archive` is 82.5% of the corpus, 1.0% embedded, 90.3% duplicated.** Vendored
   third-party text competing on equal terms with CIS architecture material. There
   is **no source-authority weighting** in either retrieval path.
6. **The legacy `cis_adrs` series outranks the current one semantically.**
   Section J.
7. **Hermes session history — 171,731 chunks withheld by judgement**, not by
   authority. Policy-dependent, declared, undecided.
8. **`cards/` excluded by judgement**, on a destination-specification framing that
   section K shows has no authority row of its own.
9. **The pre-2026-09-20 continuity window cannot be reconstructed.** The mechanism
   did not exist. Those six weeks are now covered by transcripts and git, which is
   the best available, not a structured record.
10. **Retrieval quality is still unmeasured.** The gate proves presence, currency
    and provenance. It proves nothing about ranking — and revision 131's own
    vocabulary-mismatch story ("abstraction layer" vs "adapter layer") was a
    ranking failure, not a coverage failure.

---

## O. Remaining Architectural Decisions

**For ChatGPT and Eric, not for this card.**

1. **How do browser-product histories reach CIS?** Required by policy, no
   mechanism. Options: a scheduled manual-export reminder with a gate that fails
   when the newest export exceeds its freshness bound (cheap, honest, still
   manual); accept that only verdicts are durable and **downgrade the families to
   `required: false`**, recording that CIS deliberately does not retain external
   reviewer reasoning; or build export automation (largest, and ChatGPT offers no
   API for conversation export).
2. **What triggers ingestion?** The smallest change that removes Eric from the
   loop is a `SessionEnd` hook in `.claude/settings.json` running the session
   ingester, plus the coverage gate joining `tools/closeout.sh --check`. Both are
   small; neither is authorized here.
3. **Do raw Hermes gateway sessions belong in retrieval at all?** 171,731 chunks,
   ~36% corpus growth, model chatter. My judgement is no, and the durable residue
   is already Layer 1 — but it is a judgement, and it is recorded as one.
4. **Do cards belong in retrieval?** Section K shows the framing that excludes
   them is itself undocumented.
5. **What happens to the legacy `cis_adrs` series?** It is retrievable, superseded
   and authority-shaped.
6. **Source-authority weighting in retrieval.** 469 rows of ADRs and contracts
   compete on identical terms with 2.19M rows of vendored code. The remedy is
   either weighting or splitting `archive` into its own store.
7. **Where does session-history policy live?** Recommended: inside
   **OQ-INTAKE-001** under ADR-WIASW-004, not as a new governance family.
8. **Does a generic execution-backend contract get promoted from permitted
   generalization to specified contract, and when?** Section L. **Not before the
   four measured coupling points in revision 130 are discharged** — a contract
   above a backend you cannot actually swap is a document, not a boundary.

---

## P. Exact Evidence Index

| Claim | Evidence |
|---|---|
| HEAD = origin/master = ls-remote | `git rev-parse HEAD`, `git rev-parse origin/master`, `git ls-remote origin master` — all `bf01df4d` |
| P0 closed, remote-verified | `project_state` rows 174 (`external_dev_checkpoint`), 175 (`build_phase`), 176 (`current_direction`), all unsuperseded; continuity revision 125 |
| Trust-boundary blocker open | `dev_continuity_events` id 148, revision 127; `closeout-check WB.1` |
| Prior KB finding | `dev_continuity_events` id 152, revision 131 |
| 7 of 70 sessions ingested | `SELECT DISTINCT source_key FROM knowledge_messages WHERE source='claude_code'` → 7 session ids, vs 70 files under `~/.claude/projects/*/` |
| Last session ingest 2026-09-09 | `MAX(created_at)` where `source='claude_code'` = `2026-09-09 13:04:57` |
| agent_handoffs zero rows | `SELECT COUNT(*) … WHERE source_key LIKE '%agent_handoffs%'` → 0 (measured before any write) |
| review_packets / cards / UNIFIED_BUILD_LIST zero rows | same query form, same pre-write measurement → 0, 0, 0 |
| 20 ADRs with no retrievable history | `project_decisions` 2026-09-09 → 2026-10-05; FTS probes for ADR-XDEV-001, ADR-WIASW-002, ADR-PIPE-006 → 0 hits each |
| No scheduled ingestion | `crontab -l` (one `@reboot extractor_daemon.sh`); `systemctl --user list-timers`; `systemctl list-timers \| grep -iE 'cis\|ingest\|kb'` → none; `.claude/settings.local.json` has no hooks |
| Subagent glob gap | `tools/ingest_claude_code_sessions.py` `DEFAULT_GLOB` was `~/.claude/projects/*/*.jsonl`; six transcripts at `*/<session>/subagents/agent-*.jsonl`, 2.1 MB |
| Non-idempotent doc loader | `tools/catalog/convert_to_knowledge.py:convert_cis_docs()` — bare INSERT, no existence check |
| Two-layer model | `runtime/docs/CIS_CONTEXT_CONTRACT.md`, "Two-Layer Knowledge System" and "Source Authority Hierarchy" |
| Secret masking on read | `runtime/abstraction/pipeline_relay.py:758` `_add_hit()`; `tools/ask_history.py` `redact_secrets()` |
| DEV-PIVOT-17 reachable | 24 pre-recovery rows dumped directly; 6 verbatim FTS probes all return `cis_docs` |
| CIS_16_FAILURE_MODES reachable | 4 surviving pre-recovery `cis_docs` rows |
| Duplication split | `GROUP BY length(content), substr(content,1,160)`: archive 1,974,829/2,186,884 (90.3%); rest 257,598/472,080 (54.6%) |
| Hermes withheld volume | `tools/ingest_hermes_sessions_v2.py --dry-run` → 171,731 new chunks |
| Harness replaceability | `project_decisions` ADR-SEED-018, ADR-WIASW-002, ADR-SEED-017; `docs/DEV-PIVOT-05` line 127; `docs/DEV-PIVOT-06` lines 7–19 |
| Four coupling points | `dev_continuity_events` revision 130 |
| Coverage before / after | `coverage_matrix.json`, `coverage_matrix.txt`, this directory |
| Gate + tests | `tools/gates/gate_kb_source_coverage.py`; `tools/kb/tests/test_kb_coverage.py` → 22/22 |
| Adjacent gates | `gate_chroma_secret_filter.py` PASS; `gate_chroma_no_secrets_in_results.py` PASS; `chroma_health` healthy; `gate_build_state_coherence.py` PASS; `gate_export_agreement.sh` PASS 13/13 |
| Rollback point | `max(knowledge_messages.id) = 3069556` before the first write |

**Files added or changed by this card:**

```
config/kb_source_policy.yaml                      new   the policy; the only list of what belongs
tools/kb/__init__.py                              new
tools/kb/source_policy.py                         new   discovery, identity, measurement
tools/kb/ingest_files.py                          new   incremental idempotent file ingest
tools/kb/tests/__init__.py                        new
tools/kb/tests/test_kb_coverage.py                new   22 tests
tools/gates/gate_kb_source_coverage.py            new   the gate
tools/ingest_claude_code_sessions.py              edit  two globs instead of one (subagents)
runtime/manifests/KB_SOURCE_MANIFEST.json         new   provenance receipts
data/agent_handoffs/KB-COVERAGE-01/               new   this report + coverage matrices
```

Nothing under `runtime/` other than the manifest, no migration, no schema change,
no container change, no production change.

---

## Q. Recommendation to ChatGPT

**The corpus is now adequate to support an architecture-freeze decision. It was
not four hours ago, and the gap was not where it was thought to be.**

1. **The KB prerequisite from revision 131 is discharged.** Four source families
   at 100% with hash provenance, a deterministic gate with 22 passing tests, and
   twelve previously-dead architecture concepts retrievable. Recommend revision
   131 be marked resolved — with the correction in section M recorded, not
   quietly dropped.
2. **Recovery did not change a single architectural conclusion.** 87,896 newly
   searchable chunks, including every architecture-recovery packet and 63 sessions
   of the reasoning that produced the current design, confirmed or refined all ten
   prior conclusions and contradicted none of them. **That is the most useful
   result in this report**: the architecture recovery was done on an incomplete
   corpus and still got the architecture right.
3. **The freeze is not blocked by knowledge. It is blocked by the open
   trust boundary.** Revision 127 is live and unremediated: five of seven
   blueprints on a public listener with no authentication, and relay auth
   fail-open because `CIS_PIPELINE_API_KEY` is empty. No reconstruction should be
   designed on top of a trust boundary that is currently open.
4. **Decide the two unmeasurable families before freezing.** ChatGPT's own
   reasoning is the material CIS cannot retrieve. Either accept that only verdicts
   are durable and downgrade the requirement — recording that choice — or build a
   path. Leaving it as a red gate nobody can clear teaches everyone to ignore the
   gate.
5. **Do not promote the generic harness contract yet.** Replaceability is already
   authoritative for Layer 3 and already owned by Layer 2. The contract is named
   as a permitted generalization, and the acceptance test currently fails on four
   measured counts. Discharge those first. DeepSeek Harness has no standing in CIS
   authority at all and should not acquire any as a side effect of this report.
6. **Prefer the smallest automation that removes Eric from the loop** — a
   `SessionEnd` hook plus the gate in `closeout.sh --check` — over any new
   subsystem. And fold session-history policy into OQ-INTAKE-001 rather than
   creating a tenth governance family.

---

## STATUS

**STATUS: KB RECOVERY PARTIAL — SOURCE HISTORY STILL MISSING**

Four of six required source families are at 100% coverage with content-hash
provenance, all twelve previously-unretrievable architecture concepts are
retrievable, and a deterministic coverage/staleness gate exists, passes on those
four families, and is covered by 22 tests.

It is **PARTIAL** for two specific reasons, both of which are architecture
decisions rather than work left undone:

1. **ChatGPT and claude.ai raw session histories are frozen at 2026-06-13 and
   2026-06-25 and there is no supported ingestion path.** The ChatGPT material
   matters most: ChatGPT is the independent reviewer under ADR-XDEV-001, and its
   reasoning — as opposed to its verdicts — exists nowhere in CIS. Classified
   **INGESTION PATH MISSING — ARCHITECTURE DECISION REQUIRED**; sources preserved
   in place; the gate reports it as a standing red rather than letting it pass
   silently.
2. **Nothing schedules ingestion.** The gate now detects a stale source within two
   days of it going stale. It does not fix one. Until a trigger exists, coverage
   is mechanically *detectable* but not yet mechanically *maintained* — which was
   the card's stated aim.

It is **not BLOCKED**: the knowledge integrity sufficient to evaluate an
architecture freeze now exists, and the recovered history confirmed rather than
disturbed the existing architectural conclusions. What blocks the freeze is not
knowledge — it is the live public trust-boundary exposure at continuity revision
127, which this card was not authorized to touch and did not.

---

*Read-only on everything but the knowledge base. No reconstruction performed. No
clean environment created. `/mnt/projects/cis` not reorganized. P1 not activated.
Hermes not replaced, not upgraded, not evaluated. DeepSeek Harness not installed,
not evaluated, not adopted. No generic harness abstraction implemented. No WIASW
capability implemented. No unrelated cleanup.*
