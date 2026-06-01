# CIS Kernel v1 — File Structure Proposal

## Principle
The file system IS the interface. Files move through directories as the project advances.
Structure encodes state. No database queries needed to know where a project is.

## Proposed Root Structure

```
/projects/cis/                        # root (already exists)
├── cis_kernel/                       # the CIS Kernel v1 project directory
│   ├── identity/                     # who this project is — set once, rarely changes
│   │   ├── concept.md                # one-paragraph core idea
│   │   ├── intent.md                 # what it's supposed to do (distilled from source)
│   │   └── domain.cfg                # configuration file: universal | creative | software | research
│   │
│   ├── source/                       # raw material — ingested, not yet processed
│   │   ├── vision/                   # LegacyBuildFiles (X_ docs) — ground truth
│   │   ├── transcripts/              # chat sessions — raw exploration
│   │   ├── references/               # external references, XLSB, PDFs
│   │   └── captures/                 # session captures like this one
│   │
│   ├── extraction/                   # processed intelligence from source
│   │   ├── functional_intents/       # "CIS should do X" — distilled requirements
│   │   ├── patterns/                 # recurring structures and relationships
│   │   ├── conflicts/                # contradictions found across sources
│   │   └── gaps/                     # what's missing or unclear
│   │
│   ├── research/                     # agent-discovered solutions
│   │   ├── references/               # external references found by agents
│   │   ├── solutions/                # technical/business/creative approaches
│   │   └── experiments/              # throwaway proofs of concept
│   │
│   ├── design/                       # visual/structural design — the IMAGE stage
│   │   ├── mockups/                  # UI mockups, wireframes
│   │   ├── architecture/             # system diagrams, data flow
│   │   └── decisions/                # locked design decisions (not ADRs — lightweight)
│   │
│   ├── build/                        # implementation — the ACTION stage
│   │   ├── plan/                     # current build plan / task list
│   │   ├── code/                     # implementation (or pointer to code dir)
│   │   ├── tests/                    # verification
│   │   └── progress/                 # what's been built, what's next
│   │
│   ├── polish/                       # refinement — the SOUND stage
│   │   ├── issues/                   # bugs, friction points
│   │   └── feedback/                 # user feedback, refinement notes
│   │
│   └── release/                      # distribution — the WEB stage
│       ├── builds/                   # packaged releases
│       ├── docs/                     # user-facing documentation
│       └── notes/                    # launch notes, distribution targets
│
├── runtime/                          # existing — the running application
├── handoff/                          # existing — session continuity records
├── memory/                           # existing — database (may become optional)
└── docs/                             # existing — will be absorbed into source/
```

## How It Works

### File Movement = State Change
- Files enter through `source/` — raw, unprocessed
- After extraction, a summary/analysis goes to `extraction/`
- Research findings go to `research/`
- Design outputs go to `design/`
- Implementation plans go to `build/plan/`
- Completed work goes to `build/progress/`
- Refinement notes go to `polish/`
- Finished releases go to `release/`

The project's current stage is visible just by looking at which directories have recent activity. No database, no queries.

### The CIS Kernel Project Itself
We are currently in the `source/` → `extraction/` transition for this project:
- `source/vision/` — the LegacyBuildFiles sit here, unprocessed
- `source/transcripts/` — chat transcripts sit here
- `source/captures/` — session captures (like this one) sit here
- `extraction/functional_intents/` — needs to be populated from source
- `research/` — not yet started
- Everything below `research/` — not yet started

### What This Replaces
This replaces the current structure where:
- Vision docs are buried in `docs/_archive/`
- Transcripts are in `docs/claude_chat_transcripts/`
- Extraction analyses are in `docs/architecture_atlas/`
- Build plans are in `docs/_archive/CIS_Canonical_Build_Sequence/`
- Source material is scattered across folders organized by type, not by project stage

The kernel structure organizes everything around the project's progression through its lifecycle. The file tree tells you where the project is.
