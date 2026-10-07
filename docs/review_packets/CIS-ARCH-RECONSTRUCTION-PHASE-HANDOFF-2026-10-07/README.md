# CIS Architecture Reconstruction — phase handoff and KB recovery, made remotely durable

**Entry point for an independent reviewer and for an external developer cold-starting
from the Git remote.** Everything needed is in this directory, in Git. No access to the
development machine at `/mnt/projects/cis` is required.

| | |
|---|---|
| **Baseline before this commit** | `bf01df4d45a9de8981c2d057cf629e4cd24ba514` |
| **What this commit is** | the durability closeout only — it makes already-completed work remotely recoverable |
| **Status** | `PUSHED — AWAITING INDEPENDENT CHATGPT REMOTE REVIEW` |
| **Independent review** | **NOT YET DONE.** Claude Code authored this commit and may not mark its own push `REMOTE_VERIFIED` (ADR-XDEV-001) |
| **WB.1** | **OPEN** — unchanged |
| **Phase** | post-P0 / pre-architecture-freeze / pre-reconstruction |
| **Next bounded action** | remediate **revision 127**, the live public trust-boundary exposure — *not* reconstruction, *not* P1 |

---

## The defect this commit closes

The KB recovery mechanism and the comprehensive architecture-phase handoff were
both completed on 2026-10-07. Neither was in the pushed repository.

The handoff was written to
`data/agent_handoffs/CIS-ARCH-RECONSTRUCTION-PHASE-HANDOFF-2026-10-07/`, and
`.gitignore:136` excludes `/data/*`. The mechanism — `tools/kb/`,
`config/kb_source_policy.yaml`, the coverage gate — was untracked.

So the artifact created specifically to let an external developer cold-start
from the remote, and the mechanism created specifically to make development
history recoverable, both existed **only on the machine they were meant to
outlive**.

> A recovery mechanism that exists only on the machine being recovered is not
> yet a recovery mechanism.

Nothing architectural was decided here. No reconstruction was performed, P1 was
not activated, revision 127 was not touched, and the retrieval-recall finding
(§5 below) was deliberately not fixed.

## Read in this order

1. **`INDEPENDENT_EXTERNAL_REVIEW_AND_PHASE_HANDOFF.md`** — the phase handoff
   itself, 58 KB, byte-for-byte as preserved. An independent ChatGPT external
   reviewer's architectural synthesis (Part A, verbatim), a
   promotion-candidate classification of each of its propositions (Part B),
   returned decisions (Part C), and the mechanism changes (Part D).

   **Authority: evidence, not decision.** Nothing in Part A becomes
   authoritative by appearing here. Layer-1 authority remains
   `project_decisions`, `project_state`, `open_questions`,
   `queue_items`/`queue_edges` and `dev_continuity_events` in the spine.
   Part B is the map of which propositions still need an explicit decision.

2. **`KB_SOURCE_COVERAGE_AND_DEVELOPMENT_HISTORY_RECOVERY_REPORT.md`** — 52 KB,
   the causal evidence the handoff interprets. It is here, not just referenced,
   because it carries findings that exist nowhere else: the measured shape of
   the gap (of 70 Claude Code transcripts on disk, 7 were ingested; two entire
   source families had never been ingested at all), the recovery performed, the
   exact evidence index (§P), and — importantly — **the one prior conclusion it
   contradicts**: continuity revision 131's "44% of `docs/` was never ingested"
   does not survive measurement. True pre-recovery coverage was 81.5%. A cold
   recovery that had the handoff without this report would inherit a
   superseded number as fact.

3. **`SOURCE_EVIDENCE_MAP.md`** — provenance of every file here, sha256s, why
   the path moved from `data/agent_handoffs/` to `docs/review_packets/`, and
   what was deliberately left behind.

4. **`test_summary.md`** — the suites and gates run for this commit, with
   results and commands.

5. **`secret_scan.txt`** — two independent CIS secret mechanisms over every
   file in the commit.

## What is now reproducible from a fresh checkout

The KB coverage mechanism, in full:

| Capability | Path in the repository |
|---|---|
| Source-family policy — the single declaration of what belongs in durable knowledge | `config/kb_source_policy.yaml` |
| Source discovery, coverage measurement, provenance, closeout verdict | `tools/kb/source_policy.py` |
| Incremental, idempotent ingestion keyed by `source_key` | `tools/kb/ingest_files.py` |
| Coverage / staleness gate, default and `--closeout` modes | `enforcement/mwl-proof-v2/gates/gate_kb_source_coverage.py`, invoked as `tools/gates/gate_kb_source_coverage.py` |
| Closeout integration — KB coverage as a stage-closeout blocker | `tools/development/discovery.py` |
| Claude Code session ingestion, including delegated subagent transcripts | `tools/ingest_claude_code_sessions.py` |
| SessionEnd automation | `tools/kb/session_end_ingest.sh` |
| **Hook registration, without the repository holding anyone's settings** | `tools/kb/install_session_end_hook.py` |
| Tests | `tools/kb/tests/test_kb_coverage.py` (34), `tools/kb/tests/test_install_session_end_hook.py` (25) |

Reconstructing the behaviour on a clean host:

```sh
python3 tools/kb/tests/test_kb_coverage.py                 # 34/34, temp spines only
python3 tools/kb/tests/test_install_session_end_hook.py    # 25/25, temp settings only
python3 tools/kb/install_session_end_hook.py               # register the SessionEnd hook
python3 tools/kb/ingest_files.py --all                     # rebuild coverage from local sources
python3 tools/gates/gate_kb_source_coverage.py --closeout   # verify
```

**The corpus is not in Git and is not supposed to be.** The spine
(`data/cis_memory.db`, ~6 GB) and the Chroma collection (493,377 chunks) are
gitignored. What this commit guarantees is the *mechanism*: a clean checkout plus
the local source trees reconstructs the indexes. It does not and cannot ship the
knowledge base.

### The SessionEnd hook, and why there is an installer

`tools/kb/session_end_ingest.sh` only fires because `~/.claude/settings.json`
names it — and that file is machine-local personal configuration (a model
choice, a theme, a permissions allowlist). Committing it was never an option,
so a clean recovery would have got the script and silently not got the
behaviour; the coverage gate would then have turned `claude_code_sessions` red
two days later with no visible cause.

`tools/kb/install_session_end_hook.py` resolves that from the other direction:
**the repository carries the registration, never the settings.** It merges one
`SessionEnd` entry into whatever `settings.json` already exists, is idempotent,
preserves every unrelated key and every unrelated hook verbatim, backs up before
writing, replaces atomically, and refuses rather than guesses on a file it
cannot parse. `--check` exits non-zero when registration is missing, so it is
safe in a recovery script.

The hook is registered at **user scope** on purpose: 60 of the 75 policy-eligible
transcripts on this host were written by sessions whose working directory is not
`/mnt/projects/cis`. A project-scope hook would have covered 15 of 75 and
reported success. See handoff §D1.

### The manifest

`runtime/manifests/KB_SOURCE_MANIFEST.json` is **not** in this commit, and
`.gitignore` now excludes it. It is a 513 KB per-file ledger of what *this host*
has ingested — `sha256`, `chunks` and `ingested_at` for 2,045 files across three
families. It describes the state of a knowledge base that is itself gitignored,
so in a fresh checkout it would be confidently wrong rather than useful. It is
regenerated by `tools/kb/ingest_files.py` as a side effect of ingestion, which
is the only operation that can make it true.

The contrast is `runtime/manifests/EXPORT_MANIFEST.json`, which *is* tracked: it
is 4.8 KB, it is a provenance record of a deterministic projection of the spine,
and `tools/gates/gate_export_agreement.sh` verifies the tracked projections
against it. One is a checkpoint over tracked artifacts; the other is a ledger
over untracked data. See `SOURCE_EVIDENCE_MAP.md`.

## Open findings this commit preserves rather than resolves

1. **Revision 127 — live public trust-boundary exposure.** Two public
   Cloudflare hostnames forward to `localhost:5000` with no Cloudflare Access
   policy, and five of seven registered blueprints check no credentials.
   Verified by measurement. **This is the next bounded action** and this commit
   deliberately does not touch it.

2. **Revision 135 / retrieval recall.** Measured, durable here, and *not fixed*:
   `hnsw_recall_measurement.txt` shows that for three of four probes the single
   closest chunk in the corpus is not returned at `n_results=50` or `100` — the
   top-50 window is not the true top 50. That is approximate-nearest-neighbour
   recall loss in Chroma's HNSW index at 493,377 chunks, and no reranking change
   can recover a chunk the search never returned. `tools/ask_history.py` queries
   at `n_results = max(k*10, 50)`, so a cold developer using the default tool
   gets this handoff in 3 of 7 probes, not 7 of 7. Compounded by `PER_SOURCE=2`
   crowding from model-execution chatter. Re-runnable with `recall_probe.py` and
   `retrieval_probe.py` on any host that has the corpus. Needs its own bounded
   card; handoff §A14 is explicit that retrieval quality must not become a
   reconstruction blocker.

3. **Browser-history families.** `chatgpt_sessions` and `claude_ai_sessions` are
   `required: true`, `measurable: false`, `ingestion_path: MISSING` — their only
   input is a manual account export, last taken 2026-06-13 and 2026-06-25. They
   print as `POLICY UNDECIDED` in `--closeout` and **FAIL** in default mode, so
   the decision stays visible without making every closeout permanently fail.
   The policy was not changed by this commit. ChatGPT is where independent
   review happens, so this family carries verifier reasoning that exists nowhere
   else.

4. **Architecture-freeze decisions.** Part B of the handoff lists ten
   promotion-candidate propositions (module contracts, generic execution-harness
   contracts, DeepSeek Harness standing, cards as Execution Contract
   projections, RECORD ONCE → DERIVE EVERYWHERE, phase-boundary handoff policy,
   and others). **No ADR was created or modified for any of them.** They remain
   architecture-freeze work, and Part B is the input to it.

5. **Duplicate retrieval copies.** The two reports now exist at two paths — the
   local staging bundle under `data/agent_handoffs/` and this tracked packet —
   and both are KB-eligible, so some chunks are indexed twice. This is inherent
   to the existing `local staging → docs/review_packets` convention
   (`WB-RECOVERY-03-SYSTEM-CONTEXT` is in the same position). Recorded as a
   retrieval-quality observation for finding 2's card, not fixed here.

## What did NOT happen

No reconstruction. No new architecture directory. P1 not activated. No
architecture freeze and no ADR touched. No module contract created. Hermes
unmodified. DeepSeek Harness not installed or evaluated. WIASW not implemented.
No HNSW or retrieval-ranking change. No migration applied. No container
restarted. No Cloudflare, ingress, authentication, OIDC or credential change.
Revision 127 untouched.

The repository was not cleaned or reorganized. `/mnt/projects/cis` is the
protected reference environment; this commit used an explicit file allowlist, so
roughly two dozen pre-existing unrelated working-tree entries were left exactly
as they were.

## What happens next

Eric gives the pushed SHA and the return packet to ChatGPT, which inspects the
GitHub remote independently. **The pushed SHA is not yet the accepted SHA**
(ADR-XDEV-001; `project_state.external_dev_checkpoint`). Only after independent
acceptance is the external-development durability closeout complete.

Then: **revision 127 remediation.**
