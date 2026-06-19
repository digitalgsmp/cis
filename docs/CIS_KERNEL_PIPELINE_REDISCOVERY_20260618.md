# CIS Kernel v1 — Original Processing Strategy (Rediscovered)

**Date:** 2026-06-18
**Session:** session_20260618_103228_024c7b (hermes-v4pro)
**Status:** VERBATIM REFERENCE — do not summarize

## What was found

The two-pass catalog (DEV-PIVOT-12/13) was an attempt to restart extraction work. But a more in-depth processing strategy already exists in the project — the CIS Kernel v1 WIASW pipeline.

## Key files

| File | Purpose |
|------|---------|
| `docs/cis_kernel_file_structure.md` | Design doc — the full WIASW pipeline as a file system |
| `docs/cis_kernel_source_registry.md` | All 518 source files registered with authority levels (HIGH/MEDIUM) |
| `docs/cis_kernel_source_topology.md` | Topological categorization: Vision Docs (38), Chat Transcripts (38), Extraction Analyses (21), Build Plans (67), Architecture Maps (10) |
| `cis_kernel/extraction/functional_intents/` | ~40 extraction analyses already produced |

## The pipeline (WIASW stages as file system)

```
source/       → raw material, ingested but not processed          (WORD)
extraction/   → distilled requirements, patterns, conflicts, gaps (WORD→IMAGE)
research/     → agent-discovered solutions, references            (IMAGE)
design/       → mockups, architecture, locked decisions           (IMAGE→ACTION)
build/        → implementation plans, code, tests, progress       (ACTION)
polish/       → bugs, friction, feedback                          (SOUND)
release/      → packaged releases, docs, launch notes             (WEB)
```

## State of the kernel

```
cis_kernel/
├── identity/     ✓ populated (concept.md, intent.md, domain.cfg)
├── source/       ✓ populated (MANIFEST.md, SESSION_LOG.md, transcripts/)
├── extraction/   ✓ populated (~40 functional intent analyses)
├── research/     ✗ empty
├── design/       ✗ empty
├── build/        △ partial (SCRATCHPAD, HANDOFF, plan/, cis_app.db)
├── polish/       ✗ empty
└── release/      ✗ empty
```

## Relationship to DEV-PIVOT-12/13

The two-pass catalog covers only extraction (Pass 1 = flat catalog of Eric's words, Pass 2 = knowledge graph). The cis_kernel covers the full WIASW lifecycle from identity through release. The extraction phase was already partially executed — ~40 functional intent analyses exist in `cis_kernel/extraction/functional_intents/`.

## Finding this conversation

Full verbatim transcript: `~/.hermes-v4pro/sessions/session_20260618_103228_024c7b.json`
This reference file: `docs/CIS_KERNEL_PIPELINE_REDISCOVERY_20260618.md`
