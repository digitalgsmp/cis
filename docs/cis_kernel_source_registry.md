# CIS Kernel v1 — Source Material Registry

This registers all existing CIS project files as source material for the CIS Kernel v1 project.
Files are categorized topologically by type, not by folder location.

## Source Groups

### Vision Documents (38 files)
The original design docs written WITH Eric, not by models. Located in `_archive/CIS_Creative_Intelligence_System_LegacyBuildFiles/`.
**Authority level:** HIGH — ground truth for what CIS was meant to be.
- Operator Model, Working Method, Control (constitutional layer)
- System Blueprint, State, Memory, Architecture Map (identity layer)
- Intelligence, Knowledge, Workflow, Agent, Application, Sound, Tool Streams (operational layer)
- Discovery Model, Execution Layer, Reinforcement Model, Relationship Map, Runtime Spec, Router Spec
- Discovery Workbench, Intake + Knowledge Workbench, Workbench v1
- The Pattern Across the CIS Docs (the recursive feedback model)

### Chat Transcripts (38 files)
Raw conversations with models during development.
**Authority level:** MEDIUM — contains reasoning, decisions, and drift.
- 21 Claude transcripts in `claude_chat_transcripts/2026-04-*`
- 16 original CIS chats in `architecture_atlas/original_CISChats/CIS_Chat_2026-04_*`
- 1 text file

### Extraction Analyses (21 files)
Model-written summaries of chat sessions. Processed intelligence.
**Authority level:** MEDIUM — useful synthesis, but written by models.
- 16 numbered extraction analyses (001-016)
- 3 build plan extractions
- 1 architecture atlas prompt extraction
- 1 "rant twice by accident" extraction

### Build Plans (67 files)
Construction sequences, roadmaps, dependency graphs.
**Authority level:** HIGH for planning, but many are outdated.
- Canonical Build Sequence (markdown + plain language)
- CIS Formal Phased Construction Plan
- Phase PD Build Plan
- CIS_Plain_Language_Build_Roadmap (best single document)
- Build dependency graph (SVG)
- Various handoff documents containing build sequencing

### Architecture Records (10 files)
Maps, topologies, cross-reference documents.
- CIS_FILE_MAP.md (AI-facing)
- YOUR_DOCUMENT_MAP.md (human-facing)
- Architecture atlas prompt
- Topology diagrams (PNG)
- HANDOFF_SCHEMA.md
- CIS_CONFLICT_REGISTER.md

### ADRs (5 files)
Architecture Decision Records. Locked decisions.
**Note:** These represent the enterprise-governance drift. Most need review.
- ADR-041 Artifact Registry Schema
- ADR-045 Execution Queue Ownership Layer
- ADR-047 Filesystem Governance (predraft)
- ADR-048 Staged Draft Intake Layer (predraft + full)
- ADR-049 Constitutional Memory Governance

### Contracts (21 files)
Formal subsystem behavior contracts.
**Authority level:** VARIES — some are solid, some are governance overreach.

### Handoffs (44 files)
Session-to-session transfer documents.
**Authority level:** SITUATIONAL — useful for continuity, prone to drift.

### Code (57 files)
Running backend application.
- Flask app.py, API routes (16 modules)
- Pipeline scripts (cis_extract, cis_intake, cis_normalize, etc.)
- Config, schemas, utilities
- primer_update scripts (governance machinery)

### Mockups (3 files)
UI design prototypes.
- cis_kernel_v1.html (NEW — modular kernel UI)
- cis_mockup.html (StreamDeck layout)
- cis_live_panel.html (Live session panel)

### Other (155 files)
References, backups, PDFs, images, config files, miscellaneous.

## Registration Status
- [ ] All 518 files catalogued by type
- [ ] Vision documents registered as source material
- [ ] Chat transcripts flagged for extraction
- [ ] Extraction analyses indexed
- [ ] Build plans consolidated
- [ ] ADRs reviewed for relevance to kernel approach
- [ ] Conversation captures archived (including this session)
