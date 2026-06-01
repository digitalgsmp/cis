# CIS Document Map — Your Guide to What's Where

This is a map for YOU (Eric), not for an AI. Each entry tells you what the folder or file is in plain language.

---

## The Top Level — /mnt/projects/cis/docs/

| File/Folder | What It Is |
|---|---|
| `ADRs/` | Architecture Decision Records. Locked decisions about how CIS is built. Think of them as signed contracts — what was decided and why. 5 files. |
| `architecture_atlas/` | The extraction analyses folder. 16 chat conversations were processed into structured summaries here. Each one represents a major development session. |
| `_archive/` | Old stuff. Backup orientations, legacy build plans, model responses from Gemini, extracted transcript .docx files, and the original vision docs (the X_ files). Not active but contains foundational material. |
| `claude_chat_transcripts/` | Raw chat transcripts from Claude sessions. 21 dated files. Also contains the Project Primer (ChatGPT's orientation docs), capture folder for new triangulation output, and the insights folder for finished extraction records. |
| `CIS_Creative_Intelligence_System_v1/` | The Obsidian vault. Synced to GitHub. Contains handoffs, knowledge records, the CIS_LIVE.md file, and runtime_scripts mirrors. |
| `contracts/` | Formal contract documents. Define how each subsystem must behave. 12 files. |
| `references/` | External reference materials (PDFs). |
| `CIS_FILE_MAP.md` | The AI-facing file map. Tells models which files are authoritative. Dense — not really for human browsing. |
| `CIS_CONFLICT_REGISTER.md` | Log of contradictions and inconsistencies discovered during development. |
| `HANDOFF_SCHEMA.md` | Defines the format for session handoff documents. |

---

## architecture_atlas/ — The 16 Extracted Sessions

These are model-written summaries of your conversations. Each has a source chat and an extraction analysis.

### Source Chats (the raw conversations)

All in `architecture_atlas/original_CISChats/` as `CIS_Chat_2026-04_001.md` through `016.md`.

### Extraction Analyses (what a model thought was important)

Same folder, numbered the same way. These are what I just read through.

### Also in this folder

- `cis_build_plan_v_2_memory_capture_strategy.md` — Build plan version 2
- `CIS_Canonical_Build_Sequence.md` and the plain language version — the official build order
- `architecture_atlas_prompt.md` — the prompt used to create the atlas
- A screenshot of an architecture topology diagram

---

## claude_chat_transcripts/ — The Raw Claude Sessions

21 dated files from April 14-26. Each is a full conversation with Claude. These are the primary material we need to process.

Plus:

| Item | What It Is |
|---|---|
| `ChatGTP_Project_Primer/` | A set of 16 orientation documents created by ChatGPT. Contains current state, system map, ADR summaries, risks, open questions. 16 numbered docs plus backups. |
| `ChatGTP_Project_Primer_backup_20260501_012957/` | A backup of the above from May 1. |
| `captures/` | Where new triangulation captures will land. Currently has a README. |
| `insights/` | Finished extraction records. Currently has the integrated vision record I just wrote. |
| `TRIANGULATION_WORKFLOW.md` | The guide for how three-model collaboration works. |
| `CIS Session Transcript Extraction Contract v1.md` | The contract defining how each transcript should be extracted. The rules of extraction. |
| `data-b54cc197-.../` | Raw data export from ChatGPT (conversations, memories, projects, users JSON). |
| `drive-download-20260426T063855Z-3-001/` | A massive download of ~180 .docx files from Google Drive. These are early versions of your conversations and designs in Word format. |

---

## _archive/CIS_Creative_Intelligence_System_LegacyBuildFiles/ — The Original Vision

This is the most important folder for understanding what CIS was *supposed* to be, before the pipeline architecture emerged.

| File | What It Is |
|---|---|
| `X_00_OPERATOR_MODEL.md` | How the system should behave toward you. Collaborative, non-intrusive, human-led. **Read this first.** |
| `X_00A WORKING METHOD md.txt` | How CIS itself is designed. Extract human logic, define contract, lock it, implement. **Read this second.** |
| `X_01_SYSTEM_BLUEPRINT.md` | The full system identity. Story-first creative production infrastructure. WIAS model. Eight layers. |
| `X_02_MEMORY.md` | Decision log with 58 entries. The history of why things were built the way they were. |
| `X_03_STATE.md` | Current state at the time. What was working, what was partial, what was missing. |
| `X_04_MASTER_ARCHITECTURE_MAP.md` | The full system architecture as a structured outline. Vision → layers → data model. |
| `X_05_Core Tool Stream.md.md` | How tools (Houdini, Blender, ComfyUI) fit into the system. |
| `X_06_Intelligence Stream.md` | How model-based extraction works. Multi-pass approach. |
| `X_07_Knowledge Stream.md` | How the 10TB archive gets processed into structured knowledge. |
| `X_08_Workflow Stream.md` | How work moves through the system. |
| `X_09_Agent Stream.md` | Future agent roles (Librarian, Teacher, Producer, etc.) |
| `X_10_Application Stream.md` | The eventual dashboard/interface. |
| `X_11_Sound Stream.md` | Sound/music domain in WIAS. |
| `X_CIS_DISCOVERY_MODEL.md` | **Key philosophy doc.** Structure is discovered through interaction with real material, not predefined. |
| `X_CIS_CRITICAL ADDITION.md` | One line: "Intake triggers knowledge formation." |
| `X_CIS_EXECUTION_LAYER.md` | The execution layer spec. |
| `X_CIS_REINFORCEMENT_MODEL.md` | How the system learns from corrections. |
| `X_CIS_RELATIONSHIP_MAP.md` | How all the docs relate to each other. |
| `X_CIS_RUNTIME_SPEC_v1.md` | Runtime behavior spec. |
| `X_CIS ROUTER SPEC.md` | Model routing and orchestration. |
| `X_CIS WORKFLOW_EXECUTION SPEC v1.md` | Workflow execution spec. |
| `X_CONTROL.md` | Safety rules — what actions are safe/controlled/restricted. |
| `_CIS_The pattern across the CIS docs.md` | **Most insightful doc.** Explains why the documents form a recursive feedback network, not a linear stack. |
| `x_CIS Discovery Workbench v1.md` | Design for the discovery workbench UI. |
| `x_CIS Intake + Knowledge Workbench v1.md` | Design for the intake workbench UI. |
| `x_CIS_WORKBENCH_V1.md` | General workbench design. |
| `Hand-offs/` | Subfolder with handoff documents. |
| `Sunshine-Moonlight/` | Remote desktop setup docs. |

---

## _archive/CIS_Canonical_Build_Sequence/ — The Build Plan

| File | What It Is |
|---|---|
| `CIS_Canonical_Build_Sequence.md` | The official build order in detail. Phases PD through H. |
| `CIS_Plain_Language_Build_Roadmap.md` | The same build plan written for a human. Uses a factory construction analogy. **Best single document in the entire project.** |
| `CIS_build_dependency_graph.svg` | A visual diagram of dependencies. |
| `cis_mockup.html` | An HTML mockup of the dashboard. |

---

## Which Files Matter Right Now

**For understanding what CIS is:** Read the legacy X_ docs. Start with `_CIS_The pattern across the CIS docs.md`, then `X_00_OPERATOR_MODEL.md`, then `X_01_SYSTEM_BLUEPRINT.md`.

**For what we're currently building:** The extraction contract in `claude_chat_transcripts/CIS Session Transcript Extraction Contract v1.md` and the integrated vision record in `insights/`.

**For what comes next:** The raw chat transcripts in `claude_chat_transcripts/` (21 files) and `architecture_atlas/original_CISChats/` (16 files). These are the material to process.

**Everything else** is either archive, backup, or AI-facing documentation you don't need to read yourself.
