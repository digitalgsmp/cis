# Source evidence map — where each file in this packet came from

This packet exists because of a durability defect, and that defect is the thing
this file has to be precise about.

The KB recovery mechanism and the architecture-phase handoff were both completed
on 2026-10-07 at `bf01df4d45a9de8981c2d057cf629e4cd24ba514`. Neither was in the
pushed repository. The handoff was written to
`data/agent_handoffs/CIS-ARCH-RECONSTRUCTION-PHASE-HANDOFF-2026-10-07/`, and
`.gitignore:136` excludes `/data/*`. So the artifact created specifically to let
an external developer cold-start from the remote was reachable only from inside
the VM it was meant to outlive.

## Why the path changed

`data/agent_handoffs/` is **local staging**. It has never held a tracked file —
`git log --all -- 'data/agent_handoffs/*'` is empty across the entire history —
and `config/kb_source_policy.yaml` declares it as the root of the
`external_dev_handoffs` family precisely so that locally-staged handoffs are at
least *retrievable*. Retrievable is not recoverable.

`docs/review_packets/<PACKET>/` is the **remote durability mechanism** this
repository already uses for exactly this purpose. The established pattern is a
curated subset of a local bundle, with a README that opens:

> "Entry point for an independent reviewer. Everything needed to review this
> work is in this directory, in Git. No access to the development machine at
> `/mnt/projects/cis` is required."
> — `docs/review_packets/WB-RECOVERY-03-SYSTEM-CONTEXT/README.md`

Four such packets already exist (`ADR-PIPE-006-TRIAGE-REVIEW`, `OQ-TRIAGE-003`,
`QUEUE-TRIAGE-PROPOSAL`, `WB-RECOVERY-03-SYSTEM-CONTEXT`). This is the fifth. No
new durability system was invented, `.gitignore` was not negated for `/data/`,
and the local bundles were left exactly where they are.

The copy is also still covered by the knowledge base: `docs` is the root of the
`repository_docs` family, so these files are ingested and retrievable the same
way the local originals were.

## Provenance of every file

| File in this packet | Source on the dev machine | Relationship |
|---|---|---|
| `INDEPENDENT_EXTERNAL_REVIEW_AND_PHASE_HANDOFF.md` | `data/agent_handoffs/CIS-ARCH-RECONSTRUCTION-PHASE-HANDOFF-2026-10-07/INDEPENDENT_EXTERNAL_REVIEW_AND_PHASE_HANDOFF.md` | **byte-for-byte identical** (`cmp` clean) |
| `KB_SOURCE_COVERAGE_AND_DEVELOPMENT_HISTORY_RECOVERY_REPORT.md` | `data/agent_handoffs/KB-COVERAGE-01/KB_SOURCE_COVERAGE_AND_DEVELOPMENT_HISTORY_RECOVERY_REPORT.md` | **byte-for-byte identical** |
| `hnsw_recall_measurement.txt` | `…PHASE-HANDOFF-2026-10-07/evidence/hnsw_recall_measurement.txt` | **byte-for-byte identical** |
| `recall_probe.py` | `…PHASE-HANDOFF-2026-10-07/evidence/recall_probe.py` | **byte-for-byte identical** |
| `retrieval_proof.txt` | `…PHASE-HANDOFF-2026-10-07/evidence/retrieval_proof.txt` | **byte-for-byte identical** |
| `retrieval_probe.py` | `…PHASE-HANDOFF-2026-10-07/evidence/retrieval_probe.py` | **byte-for-byte identical** |
| `README.md` | — | written for this packet |
| `SOURCE_EVIDENCE_MAP.md` | — | this file |
| `secret_scan.txt` | — | scan run for this commit |
| `test_summary.md` | — | tests run for this commit |

SHA-256 of the copied files, verifiable with
`git cat-file -p <SHA>:docs/review_packets/CIS-ARCH-RECONSTRUCTION-PHASE-HANDOFF-2026-10-07/<file> | sha256sum`:

```
4f096436a73574d0866b5993961f43838aaa4415c8e4572f5cb8a4940afbe577  INDEPENDENT_EXTERNAL_REVIEW_AND_PHASE_HANDOFF.md
de6aa50f92f6249927ad895468d4916c32a274d3d4c587d5c2d6fe4e1a704403  KB_SOURCE_COVERAGE_AND_DEVELOPMENT_HISTORY_RECOVERY_REPORT.md
4fb0e008301099a540745a2dc7925e452b19ff6ad39196757c6c93aed905f72e  hnsw_recall_measurement.txt
dffac7c63809f4cd724c0a047751ff3957f332f87d8323558c0281961bdd54ae  recall_probe.py
643f9b26b1c09304e922e94a6b43e285b198a3112173f00548b752b40b627780  retrieval_proof.txt
86c1a0f25f0b0d48af1c5cda8462e88ea192ba7a3bf3d21089c71a8ff78cc3cb  retrieval_probe.py
```

## One known stale reference, not repaired on purpose

`INDEPENDENT_EXTERNAL_REVIEW_AND_PHASE_HANDOFF.md` §D3 cites its measurement as
`evidence/hnsw_recall_measurement.txt`. In this packet that file is a **sibling**,
not under an `evidence/` subdirectory — the flat layout is what the four existing
review packets use.

The document was **not edited to fix the path**. It is independent external
review evidence and its bytes are its provenance; a packet that silently rewrites
the artifact it is preserving is worth less than one that explains the offset. The
mapping is: `evidence/<name>` in the document → `<name>` in this directory.

## What was deliberately left behind

| Not copied | Why |
|---|---|
| `evidence/coverage_gate_full.json`, `evidence/coverage_gate_closeout.json` | Deterministic output of `tools/gates/gate_kb_source_coverage.py`, which **is** in this commit. Regenerate it; the measurement needs the local 493k-chunk corpus, so a stored copy proves nothing a fresh run would not. Results recorded in `test_summary.md`. |
| `evidence/closeout_check_WB1.json` | Deterministic projection of spine state through `tools/development/discovery.py:check_closeout`, which **is** in this commit. Its substance — revision 127 blocking WB.1 — is stated in `README.md` and the handoff. |
| the rest of `data/agent_handoffs/KB-COVERAGE-01/` (`coverage_matrix.json`, `coverage_matrix.txt`) | Superseded by the gate's own output and by §D of the report. |
| `runtime/manifests/KB_SOURCE_MANIFEST.json` | 513 KB ledger of what *this host* has ingested. Machine-local runtime state; see `README.md` § "The manifest". |
| `~/.claude/settings.json` | Personal machine configuration. Replaced by `tools/kb/install_session_end_hook.py`, which registers the hook without the repository ever holding the settings. |

`hnsw_recall_measurement.txt` and `retrieval_proof.txt` were kept for the
opposite reason: they were measured against a 493,377-chunk Chroma collection
that is gitignored and cannot exist in a fresh checkout, so they are **not**
reproducible from the repository. They are the only durable record of the
revision-135 retrieval-recall finding, and `recall_probe.py` / `retrieval_probe.py`
are committed beside them so the measurement can be re-run on any host that has
the corpus.
