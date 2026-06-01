# CIS Chat 2026-04 006 — Extraction Analysis

**Source file:** `CIS_Chat_2026-04_006.md`  
**Extraction mode:** Implementation-grade architectural topology extraction  
**Purpose:** Extract operational architecture, dependency chains, runtime behavior, governance mutations, application implications, and build-order consequences from the session transcript.

---

# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery 1 — CIS Live Failure Was a Runtime-Surface Syntax Regression, Not a Routing Failure

- **Discovery Name:** LivePanel black-screen regression caused by malformed React/JS closure
- **Architectural Significance:** The session begins with a full app failure: the dashboard rendered only a black screen after a code change. The root cause was not routing, backend failure, model behavior, or deployment infrastructure. It was a frontend syntax failure in `LivePanel`, caused by removal of a workflow strip that left mismatched parentheses.
- **Affected Layers:**
  - Application Surface Layer
  - Runtime UI Layer
  - CIS Live collaboration surface
  - Debug / validation workflow
- **Dependency Impact:**
  - The dashboard depends on valid generated/edited frontend syntax.
  - UI component edits require structural validation before deployment.
  - Removing one UI region can break enclosing layout closure.
- **Build Impact:**
  - Introduces need for a frontend validation/check step before push.
  - Suggests that manual edits to `cis_dashboard.html` are brittle.
  - Supports later modularization of frontend components or automated syntax linting.
- **Runtime Impact:**
  - A single syntax error can kill the entire React app.
  - Runtime observability must distinguish backend health from frontend render failure.
  - “Site reachable” is not sufficient; rendered UI health must be verified.

## Discovery 2 — Copying a Live URL Is Not a Valid Multi-Model Collaboration Protocol

- **Discovery Name:** Bare URL broadcast lacks instruction context
- **Architectural Significance:** The user identified that pasting `https://creative-intelligence-system.com` into another model does not tell the receiving model what to do, which round to answer, what role to assume, or what problem thread is active. This invalidates the assumption that a shared live Markdown page alone can coordinate model collaboration.
- **Affected Layers:**
  - CIS Live
  - Application Surface
  - Intelligence Interface
  - Multi-model collaboration workflow
  - Prompt transport layer
- **Dependency Impact:**
  - Multi-model collaboration now requires a prompt-generation object/action.
  - URL sharing depends on injected session/problem/round/model-role metadata.
  - Live context must be paired with explicit task instruction.
- **Build Impact:**
  - Replace “Copy URL” with “Copy Prompt.”
  - Add prompt templates per model or per active model role.
  - The prompt generator becomes a required application function, not a convenience feature.
- **Runtime Impact:**
  - A model receives a portable instruction packet: URL + active problem + current round + assigned role.
  - Reduces ambiguity and wrong-round responses.
  - Turns CIS Live from passive broadcast into operational coordination protocol.

## Discovery 3 — CIS_LIVE.md Must Broadcast the Active Problem, Not the Entire Session Universe

- **Discovery Name:** Active-session-only broadcast requirement
- **Architectural Significance:** The transcript identifies that dumping all Live sessions/problems into `CIS_LIVE.md` creates ambiguity for receiving models. The active broadcast object should contain only the currently selected problem thread unless explicitly toggled otherwise.
- **Affected Layers:**
  - CIS Live runtime
  - Broadcast file generation
  - Model coordination protocol
  - Database-to-Markdown export
- **Dependency Impact:**
  - Live push depends on selected active problem ID.
  - Historical problems remain in DB but should not pollute active broadcast.
  - Context scope becomes a first-class export setting.
- **Build Impact:**
  - Implement active problem selection during push.
  - Add optional full-history toggle only when needed.
  - Add compact broadcast mode for late-round sessions.
- **Runtime Impact:**
  - Receiving models see only the relevant problem context.
  - Reduces context clutter and token waste.
  - Improves round-specific response accuracy.

## Discovery 4 — Round Compression Becomes a Context-Management Control

- **Discovery Name:** Compact mode after repeated rounds
- **Architectural Significance:** By round 10, models may already have earlier context in their own chats, so broadcasting full history becomes inefficient. The user proposes a toggle that keeps the problem statement but strips or compresses earlier rounds.
- **Affected Layers:**
  - CIS Live Markdown export
  - Context management
  - Prompt generation
  - Application controls
- **Dependency Impact:**
  - Requires active round count awareness.
  - Requires distinction between permanent problem statement and compressible discussion history.
  - Depends on model-side continuity assumptions.
- **Build Impact:**
  - Add compact mode toggle after a threshold, suggested after round 3.
  - Export most recent N rounds while preserving problem statement.
- **Runtime Impact:**
  - Broadcast stays short and relevant.
  - Earlier rounds remain stored in DB.
  - Models receive targeted continuation context.

## Discovery 5 — Model Identity Must Be Dynamic, Not Hardcoded

- **Discovery Name:** Dynamic model roster replaces fixed Gemini / Claude / ChatGPT slots
- **Architectural Significance:** The system previously assumed a fixed three-model collaboration roster. The transcript exposes the need to add or remove participants such as DeepSeek, Mistral, Llama, Grok, or local models during a session.
- **Affected Layers:**
  - Intelligence Layer
  - CIS Live schema
  - Model registry
  - Application Live panel
  - Intel sidebar
- **Dependency Impact:**
  - Each round needs a model response list, not fixed columns.
  - Model roster is defined at session/problem level but overridable per round.
  - Model identity becomes a canonical DB object.
- **Build Impact:**
  - Add `models` registry table or equivalent object.
  - Add `model_name`, `model_type`, `active_flag`, and role metadata.
  - Update Live panel UI to render variable model slots.
- **Runtime Impact:**
  - Models can drop out or join mid-session.
  - Copy prompts generated only for active models in that round.
  - Broadcast output attributes responses to arbitrary registered model names.

## Discovery 6 — Intel Sidebar Tabs Are Decorative Until Wired to a Model Registry

- **Discovery Name:** LOCAL / REMOTE / AGENT tabs need functional registry wiring
- **Architectural Significance:** The session identifies a gap between application UI and execution reality. The Intel sidebar has model tabs, but they do not yet drive model selection or invocation. The dynamic Live roster is the first functional bridge.
- **Affected Layers:**
  - Application Surface
  - Intelligence Layer
  - Model Registry
  - Future Execution Layer
  - Agent Layer
- **Dependency Impact:**
  - Live roster should draw from the same model registry as the Intel sidebar.
  - Local model invocation later depends on registered local model objects.
  - Agent roles eventually depend on the same registry or role system.
- **Build Impact:**
  - Convert sidebar model lists from static/decorative UI to DB-backed objects.
  - Add model selection and per-round roster generation.
  - Later add invoke actions for local models.
- **Runtime Impact:**
  - Model registry becomes the first real interface bridge between application UI and intelligence execution.
  - Sets up Phase 0 local model invocation.

## Discovery 7 — Documentation Gaps Are a Runtime Governance Failure

- **Discovery Name:** Decisions and tasks were being generated but not persisted to DB
- **Architectural Significance:** The user identified recurring loss of decisions, insights, and deferred features. The transcript shows that some items existed in memory additions and handoff files but were not promoted into the live DB decision/task system.
- **Affected Layers:**
  - Governance Layer
  - Memory / Continuity Layer
  - Session Close protocol
  - Task and ADR persistence
- **Dependency Impact:**
  - Session insights must be transformed into ADRs or tasks immediately.
  - Handoff files alone are insufficient as governance memory.
  - DB requires required fields, including `description`, for decision insertion.
- **Build Impact:**
  - Add validation to decision posting workflow.
  - Add UI affordance or automation for extracting session decisions into DB.
  - Add duplicate detection and required-field checks.
- **Runtime Impact:**
  - Prevents architectural drift across sessions.
  - Establishes DB as operational memory, not optional archive.

## Discovery 8 — Session Handoff Friction Is an Application-Layer Defect

- **Discovery Name:** Handoff files were scattered across multiple locations
- **Architectural Significance:** The user could not reliably remember where handoff files were written or which files to attach to a new session. This is not a user error; it is a control-surface and workflow design problem.
- **Affected Layers:**
  - Session lifecycle
  - Handoff protocol
  - Application Surface
  - Continuity / Memory Layer
- **Dependency Impact:**
  - Session start depends on predictable file location.
  - Session close must write handoff artifacts to centralized folder.
  - Reorientation document and latest handoff must co-locate.
- **Build Impact:**
  - Create `/mnt/projects/cis/handoff/` as canonical handoff folder.
  - Update Session Close API to write there automatically.
  - Future UI should display exact files to attach for next session.
- **Runtime Impact:**
  - Reduces cognitive load during handoff.
  - Prevents lost context at session boundaries.
  - Turns handoff from manual file hunt into repeatable protocol.

## Discovery 9 — Session Close Has Hidden Failure Modes: Git Push, Missing Imports, Duplicate DB Writes

- **Discovery Name:** Session Close needs transactional execution and validation
- **Architectural Significance:** Multiple close attempts created duplicate session rows, encountered a missing `Path` import, and exposed possible Git push/handoff completion uncertainty. This proves Session Close is not yet a governed runtime transaction.
- **Affected Layers:**
  - Execution Layer
  - Governance Layer
  - Session lifecycle
  - DB persistence
  - Git/vault sync
- **Dependency Impact:**
  - Handoff write depends on import correctness.
  - DB insert should not repeat blindly on retry.
  - Git commit/push should not block or invalidate session closure.
- **Build Impact:**
  - Add idempotency key or duplicate-detection for session close.
  - Separate DB commit, handoff write, Git commit, and remote push into visible steps.
  - Add step-level status and retry logic.
- **Runtime Impact:**
  - Prevents duplicate session log pollution.
  - Makes close operation inspectable and recoverable.
  - Prevents one failing side effect from obscuring completed work.

## Discovery 10 — Storage Reattachment Needs a Drive Manifest and Hardware Mapping Record

- **Discovery Name:** Rogue old Ubuntu disk appeared after storage reattachment
- **Architectural Significance:** After detaching drives for a VM snapshot and reattaching them, an extra 250GB disk appeared in Ubuntu Explorer. The system lacked a documented drive mapping record to distinguish current CIS disks from an old Ubuntu/test drive.
- **Affected Layers:**
  - Infrastructure Layer
  - Storage architecture
  - Runtime environment stability
  - Documentation / Memory governance
- **Dependency Impact:**
  - Correct mount structure depends on Proxmox hardware mapping.
  - Model availability depends on `/mnt/models` being mapped to the correct physical disk.
  - Snapshot procedures depend on knowing which disks are pass-through vs local-LVM.
- **Build Impact:**
  - Add storage manifest documenting physical drive serials, VM devices, mountpoints, roles.
  - Add a post-reattachment verification checklist.
  - Track old/test drives explicitly as detached/non-CIS.
- **Runtime Impact:**
  - Prevents accidental use of old OS drives.
  - Confirms `/mnt/models`, `/mnt/archive`, `/mnt/cache`, `/mnt/projects`, and `/` mappings.
  - Reduces file manager confusion and operator anxiety.

---

# 2. TOPOLOGY MUTATIONS

## 2.1 CIS Live Mutates From Passive Broadcast to Coordinated Collaboration Protocol

Previous topology:

```text
Live session → CIS_LIVE.md → copied URL → external model reads page
```

Mutated topology:

```text
Active Problem Thread
→ Round State
→ Model Roster
→ Per-Model Prompt Generator
→ CIS_LIVE.md Active Broadcast
→ External Model Response
→ Manual Paste Back Into Live Panel
→ Stored Round Response
```

Key changes:

- `CIS_LIVE.md` is no longer the full-history dump.
- The active problem becomes the exported unit.
- The copy action changes from URL copy to prompt copy.
- Round number and model role become part of the prompt payload.
- Model roster becomes dynamic and per-round.

## 2.2 Model Registry Becomes the Bridge Between Intel Sidebar and Live Collaboration

Previous topology:

```text
Intel Sidebar Tabs → visual labels only
Live Panel → hardcoded Gemini / Claude / ChatGPT slots
```

Mutated topology:

```text
Model Registry
→ LOCAL / REMOTE / AGENT Sidebar Tabs
→ Live Session Roster
→ Round-Specific Active Model List
→ Prompt Generation
→ Response Attribution
→ Future Local Invocation
```

Key changes:

- The model registry becomes a canonical system object.
- Sidebar tabs become backed by data rather than static display.
- Registered local models become future executable targets.
- Agents and models share registry logic or adjacent identity schema.

## 2.3 Session Close Becomes an Execution Pipeline Rather Than a Button

Previous topology:

```text
User fills form → click close → DB/handoff/git happen somewhere
```

Mutated topology:

```text
Session Close Form
→ Validate fields
→ Write session_log row
→ Generate handoff markdown
→ Write to vault
→ Write to project folder
→ Write to centralized handoff folder
→ Commit to Git
→ Optional push
→ Return step log
```

Key changes:

- Centralized handoff folder added.
- Session close requires visible step logging.
- Duplicate risk appears if retries are not idempotent.
- Git push is downgraded from mandatory hidden step to separable sync concern.

## 2.4 Handoff Storage Mutates From Project-Scattered to Centralized Context Kit

Previous topology:

```text
Handoff file → project folder
Reorientation file → separate runtime/project location
User manually finds both
```

Mutated topology:

```text
/mnt/projects/cis/handoff/
├── 2_CIS_REORIENTATION.md
├── CIS_Handoff_<timestamp>.md
└── archive/
```

Future implied topology:

```text
/mnt/projects/cis/handoff/
├── 2_CIS_REORIENTATION.md
├── latest_handoff.md
├── CIS_Handoff_<timestamp>.md
└── archive/
```

## 2.5 Infrastructure Storage Topology Mutates From Assumed Mounts to Verified Device Mapping

Previous topology:

```text
Storage drives attached → assumed correct
```

Mutated topology:

```text
Physical Drive
→ Proxmox Device / Serial
→ VM virtio device
→ Guest block device
→ Mountpoint
→ CIS role
→ Verification command
```

Extracted current mapping after cleanup:

| CIS Role | Guest Device | Mountpoint | Status |
|---|---:|---|---|
| VM system | `vda` / `vda2` | `/` | Correct |
| Projects | `vdb` | `/mnt/projects` | Correct |
| Archive | `vdc` / `vdc2` | `/mnt/archive` | Correct |
| Cache | `vdd` / `vdd2` | `/mnt/cache` | Correct |
| Models | `vdf` / `vdf1` | `/mnt/models` | Correct |
| Old Ubuntu/Test Drive | formerly `vde` | unmounted / file manager volume | Detached |

---

# 3. DEPENDENCY DISCOVERIES

## 3.1 Live Collaboration Depends on Instruction Payload, Not Just Shared Context

- **Hidden prerequisite:** A model must receive task instruction, model role, round target, and active problem label.
- **Sequencing constraint:** Prompt generator must be built before reliable multi-model collaboration.
- **Runtime blocker:** Bare URL causes ambiguity and wrong-round or non-response behavior.

## 3.2 Dynamic Model Roster Depends on a Model Registry

- **Hidden prerequisite:** Registered model objects must exist before per-round roster can work cleanly.
- **Sequencing constraint:** Build model registry before replacing hardcoded slots.
- **Unstable dependency:** Free-text model names can work temporarily but do not close the Intel sidebar gap.

## 3.3 Intel Sidebar Functionality Depends on Registry Wiring

- **Hidden prerequisite:** Sidebar tabs must read/write the same model registry used by Live panel.
- **Sequencing constraint:** Decorative sidebar tabs must become data-backed before invocation features.
- **Runtime blocker:** Without wiring, the app visually implies intelligence capability that does not exist.

## 3.4 DB Governance Depends on Required Field Validation

- **Hidden prerequisite:** The decision API requires `description`; earlier post commands failed without it.
- **Sequencing constraint:** DB write helpers or UI form must enforce required fields before submission.
- **Runtime blocker:** Silent or unclear API failure leads to false belief that decisions were stored.

## 3.5 Handoff Reliability Depends on File Centralization

- **Hidden prerequisite:** The operator must know exactly which files to attach to a new session.
- **Sequencing constraint:** Centralized handoff folder must exist before handoff can become low-friction.
- **Runtime blocker:** Separate project/handoff/reorientation locations create continuity failure.

## 3.6 Session Close Depends on Idempotency

- **Hidden prerequisite:** Retrying close must not duplicate session rows.
- **Sequencing constraint:** Add close-state tracking before repeated close attempts become safe.
- **Runtime blocker:** Multiple close clicks create duplicate `session_log` entries.

## 3.7 Storage Cleanup Depends on Physical-to-Virtual Drive Mapping

- **Hidden prerequisite:** Must distinguish physical drives, LVM virtual disks, Proxmox passthrough IDs, VM virtio IDs, and guest mountpoints.
- **Sequencing constraint:** Storage manifest should precede filesystem cleanup.
- **Runtime blocker:** Old OS disk appeared as file-manager volume and created uncertainty about active root system.

## 3.8 Filesystem Cleanup Depends on Correct Storage Baseline

- **Hidden prerequisite:** Confirm all mounted drives are intentional before reorganizing CIS files.
- **Sequencing constraint:** Storage audit and rogue disk detachment before filesystem cleanup.
- **Runtime blocker:** Cleanup could target wrong disk if old OS drive remains mounted/browsable.

---

# 4. EXECUTION-LAYER IMPLICATIONS

## 4.1 Commands Extracted

### Frontend black-screen diagnosis / fix

```bash
grep -n "^  )$" /mnt/projects/cis/runtime/cis_dashboard.html
sed -n '2230,2242p' /mnt/projects/cis/runtime/cis_dashboard.html
sed -i '2234d' /mnt/projects/cis/runtime/cis_dashboard.html
sed -n '2230,2241p' /mnt/projects/cis/runtime/cis_dashboard.html
```

### Decision DB verification and posting

```bash
curl -s http://127.0.0.1:5000/api/projects | python3 -m json.tool | grep -E '"id"|"title"|"project_id"'
curl -s "http://127.0.0.1:5000/api/decisions?project_id=PROJECT__CIS__BUILD__V1" | python3 -m json.tool | grep '"decision_number"'
```

Required decision POST fields discovered:

```json
{
  "project_id": "PROJECT__CIS__BUILD__V1",
  "decision_number": "ADR-###",
  "title": "...",
  "description": "...",
  "rationale": "...",
  "status": "accepted"
}
```

### Handoff centralization

```bash
mkdir -p /mnt/projects/cis/handoff/archive
cp /mnt/projects/cis/runtime/2_CIS_REORIENTATION.md /mnt/projects/cis/handoff/
cp /mnt/projects/cis/runtime/1_memory_additions.md /mnt/projects/cis/handoff/archive/
```

### Session close code inspection

```bash
grep -n "Handoff\|handoff" /mnt/projects/cis/runtime/api/session.py | head -20
sed -n '195,215p' /mnt/projects/cis/runtime/api/session.py
grep -n "PROJECTS_DIR\|VAULT_DIR\|HANDOFF\|BASE_DIR\|CIS_DIR" /mnt/projects/cis/runtime/config.py | head -20
```

### Session close fix: central handoff write

```python
handoff_folder = Path("/mnt/projects/cis/handoff")
handoff_folder.mkdir(exist_ok=True)
(handoff_folder / handoff_filename).write_text(handoff_content, encoding="utf-8")
```

Additional required import:

```python
from pathlib import Path
```

### Temporary Git push disabling

```python
# from:
f"git commit -m 'Session close: {focus}' && git push"

# to:
f"git commit -m 'Session close: {focus}'"
```

### Flask process management

```bash
ps aux | grep app.py | grep -v grep
pkill -9 -f "app.py"
fuser -k 5000/tcp
cd /mnt/projects/cis/runtime && python3 app.py &
```

### Storage / drive verification

```bash
lsblk | grep -E "NAME|vde2|sda|sdb|sdc|sdd|vd"
mount | grep vde2
sudo blkid /dev/vde2
sudo fdisk -l /dev/vde | head -20
ls /mnt/models
df -h /mnt/models
```

### Proxmox host mapping

```bash
cat /etc/pve/qemu-server/$(qm list | grep creative | awk '{print $1}').conf | grep -i "scsi\|sata\|virtio\|ide"
lvs | grep vm-100
lsblk -o NAME,SIZE,TYPE,TRAN,MODEL | head -30
```

## 4.2 Runtime States Extracted

### CIS Live problem states

- created
- active
- broadcasted
- compacted
- awaiting model response
- responded
- logged
- archived

### Round states

- round created
- active model roster selected
- prompt generated
- prompt sent manually
- model response pasted
- round complete
- next round prepared

### Model roster states

- registered
- active in session
- active in round
- dropped out
- added mid-session
- inactive
- future invokable

### Decision logging states

- insight identified
- ADR proposed
- ADR number checked
- required fields validated
- POST attempted
- success confirmed in DB/UI
- failed due to missing description
- reposted correctly

### Session close states

- form filled
- close submitted
- DB row written
- handoff generated
- handoff vault write
- handoff project write
- handoff centralized write
- Git commit attempted
- optional Git push
- UI complete / hung / failed

### Storage audit states

- drives reattached
- guest devices listed
- mountpoints checked
- unknown disk identified
- physical serial mapped
- old OS disk confirmed
- detached in Proxmox
- remaining drives verified

## 4.3 State Transitions

```text
Live Problem Selected
→ Push Requested
→ Active Problem Exported
→ Prompt Generated Per Active Model
→ Model Receives Role + Round Context
→ Model Responds
→ User Pastes Response
→ Round Stored
```

```text
Session Close Clicked
→ Validate Close Fields
→ Write Session Log
→ Generate Handoff Markdown
→ Write Handoff to Vault
→ Write Handoff to Project Folder
→ Write Handoff to /mnt/projects/cis/handoff/
→ Git Commit
→ Return Step Log
```

```text
Storage Reattachment
→ VM Shows Extra Volume
→ lsblk Identifies vde
→ blkid/fdisk Identify ext4 + EFI
→ Proxmox Config Maps Serial
→ User Confirms Old Test Drive
→ Detach virtio4
→ Verify vde Gone + vdf Models Still Mounted
```

## 4.4 Validation Behavior

- Frontend validation: React/JS syntax must be checked after layout edits.
- Decision API validation: `decision_number`, `title`, `description`, and `rationale` are required.
- Handoff validation: `/mnt/projects/cis/handoff/` must contain both reorientation and latest handoff.
- Storage validation: all CIS mountpoints must be present and rogue volumes absent.
- Session close validation: UI success is not enough; handoff file and DB row should be checked.

## 4.5 Retry / Escalation Logic

- If app black screen persists: inspect console/syntax, not just route/backend.
- If decision post appears successful but UI unchanged: query API and inspect JSON response.
- If Session Close hangs: inspect process, API error, Git step, and handoff folder; avoid repeated close clicks.
- If drive appears unexpectedly: identify by serial and mount contents before detaching.
- If command includes a tool-only instruction such as `str_replace`: convert to valid terminal/Python workflow.

---

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## 5.1 Authority Structures

- **Human authority:** User decides whether design changes reduce friction or introduce confusion.
- **DB authority:** ADRs/tasks in the DB are the live governance record.
- **File authority:** `X_02_MEMORY.md`, reorientation file, and handoff files preserve broader continuity but are insufficient without DB promotion.
- **Runtime authority:** Successful commands, actual mountpoints, and API responses override assumptions.

## 5.2 Review States

### ADR review path

```text
Insight / decision emerges
→ User flags documentation gap
→ Existing ADR numbers checked
→ New ADR number assigned
→ Required fields included
→ API response verified
→ UI/DB confirms accepted status
```

### Task review path

```text
Deferred feature identified
→ Convert to task
→ Assign phase: deferred/backlog
→ Assign priority
→ POST to tasks endpoint
→ Verify in DB/UI
```

### Handoff review path

```text
Session close produces handoff
→ Confirm file exists in /mnt/projects/cis/handoff/
→ Confirm reorientation file co-located
→ Confirm timestamp understood as UTC
→ Use both files for next session
```

## 5.3 Promotion Logic

- Session insights are not trusted as system memory until converted into ADRs/tasks or appended to controlled docs.
- `memory_additions_20260420.md` contents became authoritative only after backfilling ADR-027 through ADR-029 and appending MEMORY parking-lot features.
- CIS Live architecture decisions became authoritative only after corrected insertion as ADR-021 through ADR-026.

## 5.4 Rejection Paths

- Missing decision `description` caused API rejection.
- Incorrect ADR numbering caused collision/failure.
- Bare URL sharing was rejected as insufficient collaboration protocol.
- Scattered handoff locations were rejected as an unacceptable operator burden.
- Rogue `vde` disk was rejected as non-CIS active storage after verification.

## 5.5 Trust Enforcement

- Verify API writes with a GET query after POST.
- Verify UI state against DB state when UI appears stale.
- Verify storage devices by serial, not by assumed order.
- Verify running VM root with `findmnt /` before detaching suspected OS disk.
- Verify `Path` import before using `Path()` in runtime code.

## 5.6 Hallucination / Mistake Controls

The transcript exposes a required assistant/operator control rule:

- Commands must be valid for the target environment.
- Tool-only commands such as `str_replace` must not be given as terminal commands.
- Before code edits, inspect imports and context.
- Avoid repeated blind retries.
- When the user says the workflow feels like guessing, pause and re-verify state.

---

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## 6.1 Knowledge Formation Logic

This session shows that operational development sessions produce multiple knowledge types:

- code regression knowledge
- UI logic knowledge
- ADR governance knowledge
- task backlog knowledge
- handoff procedure knowledge
- storage hardware mapping knowledge
- process failure knowledge

These should not remain trapped in transcript form. They should become:

- ADRs
- tasks
- MEMORY updates
- storage manifests
- troubleshooting playbooks
- execution-layer rules

## 6.2 Retrieval Structure

Future retrieval should support queries such as:

- “Why did the app black screen after LivePanel edit?”
- “What fields are required by the decisions API?”
- “Where do I find files for new session handoff?”
- “Which drive is the models drive?”
- “What is the build order for CIS Live model roster?”
- “Why is Copy Prompt needed instead of Copy URL?”

## 6.3 Indexing Implications

This transcript should generate index entries under:

- `application_surface/cis_live`
- `governance/adr_logging`
- `workflow/session_close`
- `infrastructure/storage_mapping`
- `runtime/debugging`
- `intelligence/model_registry`
- `handoff/continuity`

## 6.4 Normalization Rules

Normalize this session into multiple record categories:

| Knowledge Category | Records |
|---|---|
| `learning` | Debugging frontend black screen; interpreting Proxmox disk mappings |
| `reference` | Drive mapping table; session close file paths |
| `template` | ADR POST payload; session close handoff structure |
| `checklist` | Session close validation; storage reattachment verification |
| `documentation` | CIS Live architecture decisions; handoff centralization rule |

## 6.5 Ontology / Spine Implications

The session adds or strengthens these ontology branches:

```text
CIS
├── Application Surface
│   ├── CIS Live
│   │   ├── Active Problem Broadcast
│   │   ├── Round Compression
│   │   ├── Copy Prompt
│   │   └── Dynamic Model Roster
│   └── Session Close Panel
├── Intelligence Layer
│   ├── Model Registry
│   ├── Local / Remote / Agent Categories
│   └── Future Invocation
├── Governance Layer
│   ├── ADR Persistence
│   ├── Task Backfill
│   └── Handoff Protocol
├── Infrastructure Layer
│   ├── Proxmox Mapping
│   ├── Storage Manifest
│   └── Mount Verification
└── Execution Layer
    ├── Commands
    ├── State Transitions
    ├── Validation
    └── Retry / Failure Handling
```

## 6.6 Stabilization Loops

- Session produces decisions → decisions must enter DB → DB drives roadmap.
- Handoff produces context → context must centralize → next session continuity improves.
- Drive audit produces mapping → mapping must become manifest → future storage confusion decreases.
- Live collaboration produces solved problems → solved problems become knowledge objects.

---

# 7. APPLICATION-LAYER IMPLICATIONS

## 7.1 Workbench Requirements

The dashboard needs more than panels. It needs operational controls that reduce user memory burden:

- Copy Prompt button per active model.
- Active problem selector with clear broadcast target.
- Compact mode toggle.
- Dynamic model roster editor.
- Model registry manager.
- Session close step log.
- Handoff file display after close.
- Duplicate session close protection.
- Storage manifest/status panel.

## 7.2 Interface Panels Extracted / Implied

### CIS Live Panel

Required controls:

- active problem dropdown
- current round indicator
- compact mode toggle
- model roster list
- add/remove model per round
- copy prompt buttons
- response paste fields
- push active problem only

### Intel Sidebar

Required controls:

- LOCAL models
- REMOTE models
- AGENT roles
- registered/inactive status
- use in Live roster
- future invoke button for local models

### Session Close Panel

Required controls:

- session focus
- completed
- next steps
- notes
- close + commit
- visible step log
- generated handoff path
- next-session attach instructions

### Storage / Infrastructure Panel

Implied future controls:

- list expected mountpoints
- list actual mountpoints
- show physical serial mapping
- show missing/extra drives
- storage cleanup readiness

## 7.3 Operator Actions

The transcript shows high-friction operator actions that should become UI actions:

- confirm ADRs landed
- backfill missing documentation
- copy handoff files
- locate latest handoff
- verify storage mappings
- restart dashboard safely
- detect duplicate session close attempts

## 7.4 Runtime Visibility Needs

- Show whether close is actively running, failed, or complete.
- Show exact failing step if close fails.
- Show whether Git push is skipped, failed, or complete.
- Show handoff files written.
- Show whether Flask has multiple instances / port conflict.
- Show if frontend render health is OK after code edit.

## 7.5 Application / Runtime Bridges

The session identifies concrete bridges:

```text
Intel Sidebar → Model Registry → CIS Live Roster
Session Close Form → DB Session Log → Handoff Files
CIS Live Push → Active Problem Export → Copy Prompt
Storage State → Drive Manifest → Cleanup Readiness
```

---

# 8. FEEDBACK LOOP DISCOVERIES

## 8.1 Development Feedback Loop

```text
Code change
→ Black screen
→ Runtime diagnosis
→ Targeted fix
→ Browser refresh
→ Site verified
→ Regression knowledge extracted
```

## 8.2 Collaboration Feedback Loop

```text
CIS Live used with models
→ URL ambiguity observed
→ Copy Prompt requirement discovered
→ Active problem broadcast requirement discovered
→ Dynamic model roster requirement discovered
→ Model registry bridge identified
```

## 8.3 Governance Feedback Loop

```text
User notices decisions not documented
→ Docs reviewed
→ Missing ADRs identified
→ ADR numbering corrected
→ Required API fields discovered
→ ADRs/tasks inserted
→ MEMORY.md updated
```

## 8.4 Handoff Feedback Loop

```text
User confusion at session boundary
→ File locations inspected
→ Handoff folder proposed
→ Files centralized
→ Session close API modified
→ Error exposed
→ Import fixed
→ Handoff verified in central folder
```

## 8.5 Infrastructure Feedback Loop

```text
Filesystem cleanup planned
→ Extra drive appears
→ Storage audit initiated
→ Proxmox mapping inspected
→ Old Ubuntu disk identified
→ Disk detached
→ Correct mounts verified
→ Cleanup may proceed
```

## 8.6 Assistant Correction Loop

```text
Assistant gives invalid/sloppy command
→ User challenges reliability
→ Pause and inspect error
→ Correct missing import
→ Restart cleanly
→ Operation succeeds
```

---

# 9. UNRESOLVED GAPS + MISSING LAYERS

## 9.1 Missing CIS Live Implementation Work

- Active problem only broadcast is decided but not fully implemented in the transcript.
- Copy Prompt replaces Copy URL is decided but not yet built.
- Round compression toggle is decided but not yet built.
- Dynamic model roster is decided but not yet built.
- Model registry wiring is identified but not yet implemented.

## 9.2 Missing Model Registry Schema

Unresolved fields:

- `model_id`
- `model_name`
- `model_type` (`local`, `remote`, `agent`)
- `provider`
- `access_mode` (`manual`, `api`, `local_runtime`)
- `active`
- `default_role`
- `capabilities`
- `notes`

## 9.3 Missing Live Round Schema Mutation

Current hardcoded response slots need replacement with:

```json
{
  "round_id": "...",
  "active_models": [
    {
      "model_id": "...",
      "model_name": "Claude",
      "role": "architect/verifier",
      "prompt_text": "...",
      "response_text": "...",
      "status": "pending|responded|skipped"
    }
  ]
}
```

## 9.4 Missing Session Close Idempotency

Current risk:

- repeated close clicks create duplicate DB rows.

Required:

- close attempt ID
- session hash
- duplicate detection
- disable button during close
- recover failed close without rewriting completed steps

## 9.5 Missing Handoff Latest Symlink / Alias

The centralized folder exists and receives timestamped handoff files, but future simplification still needs:

```text
/mnt/projects/cis/handoff/latest_handoff.md
```

or UI display that identifies the latest file.

## 9.6 Missing Git Sync Strategy

Git push was temporarily disabled or considered problematic. Unresolved:

- Should session close commit only?
- Should push be manual?
- Should push use SSH key/token?
- Should push failures block close?

## 9.7 Missing Storage Manifest

Need a persistent record of:

- physical drive serials
- Proxmox mapping
- guest devices
- mountpoints
- filesystem type
- CIS role
- status
- verification commands

## 9.8 Missing Filesystem Cleanup Plan

The session ends before filesystem cleanup begins. Required next step:

- Audit current `/mnt/projects/cis` layout.
- Identify duplicate docs/runtime/project folders.
- Define canonical paths.
- Move only after backup/snapshot and manifest.

## 9.9 Missing Frontend Validation Layer

The black screen proves need for:

- syntax check
- component-level test
- browser render check
- rollback plan

## 9.10 Missing Assistant Command Safety Rules

The invalid `str_replace` terminal command and missing import issue imply need for:

- command environment labeling
- verify-before-edit rule
- no-tool-command leakage
- pause on user confidence warning

---

# 10. BUILD-PLAN IMPLICATIONS

## 10.1 Foundational Prerequisites

Before wiring intelligence for the application:

1. Complete filesystem cleanup.
2. Establish storage manifest.
3. Stabilize session close / handoff workflow.
4. Prevent duplicate session close writes.
5. Fix CIS Live core logic.
6. Build model registry schema.
7. Wire Intel sidebar to registry.

## 10.2 Blocked Layers

### Intelligence Wiring is blocked by:

- decorative Intel sidebar tabs
- missing model registry
- no dynamic roster
- no local invocation bridge

### Application usability is blocked by:

- handoff friction
- unclear session close state
- file path confusion
- duplicate session records

### Knowledge accumulation is blocked by:

- Live solved problems not yet becoming knowledge records
- missing pipeline from session decisions to structured knowledge
- missing runtime-to-DB promotion automation

### Filesystem cleanup is blocked by:

- need for canonical path map
- need for storage manifest
- need to protect current mounts

## 10.3 Sequencing Implications

Recommended sequence extracted from the session:

```text
1. Stabilize handoff centralization and session close
2. Clean duplicate session_log rows from repeated close attempts
3. Create storage manifest and filesystem cleanup plan
4. Cleanup CIS filesystem paths
5. Implement CIS Live active problem broadcast
6. Implement Copy Prompt
7. Implement compact round mode
8. Replace hardcoded model slots with dynamic model roster
9. Wire model registry to Intel sidebar tabs
10. Add local model invocation button / first execution-layer intelligence bridge
```

## 10.4 Runtime-First Requirements

- Every UI action that triggers system mutation must return step-level status.
- Every DB write must be verified or visibly failed.
- Every handoff action must output next-session instructions.
- Every storage/mount change must be checked against manifest.

## 10.5 Governance-First Requirements

- New decisions must use next available ADR number.
- Required fields must be enforced in UI/API helper.
- Session close should recommend ADR/task creation from notes.
- Backfilled information must not remain only in transient files.

## 10.6 Execution-First Requirements

- Commands must be executable on target environment.
- Runtime code edits must be verified with import and context checks.
- Git push should be non-blocking or clearly separated.
- Flask process lifecycle needs one-command safe restart.

## 10.7 Application Dependencies

The future application depends on:

- DB-backed model registry
- DB-backed live sessions/rounds
- centralized handoff path
- storage manifest
- reliable session close API
- prompt-generation templates
- model roster UI

---

# 11. EXTRACTED CANONICAL OBJECTS

## Object 1 — CIS Live Problem Thread

- **Purpose:** Represents one active problem being discussed across models.
- **Lifecycle:** created → active → broadcasted → compacted → resolved/archived.
- **Authority Source:** User selection in Live panel.
- **Related Objects:** Live Round, Model Roster, CIS_LIVE.md, Prompt Packet.
- **States:** active, inactive, broadcasted, compacted, archived.
- **Storage Implications:** Stored in DB; exported selectively to `CIS_LIVE.md`.

## Object 2 — Live Round

- **Purpose:** Represents one exchange cycle within a Live problem.
- **Lifecycle:** created → prompts generated → responses collected → logged → next round.
- **Authority Source:** User / Live session workflow.
- **Related Objects:** Model Response, Model Roster, Prompt Packet.
- **States:** pending, active, waiting_for_responses, complete.
- **Storage Implications:** DB table should allow variable model responses.

## Object 3 — Model Registry Entry

- **Purpose:** Canonical model identity used by Intel sidebar, Live roster, and future invocation.
- **Lifecycle:** registered → active → selected for session → selected for round → invoked/responded → inactive.
- **Authority Source:** User-managed registry.
- **Related Objects:** Intel Sidebar Tab, Model Roster, Prompt Packet, Agent Role.
- **States:** active, inactive, local_available, remote_manual, api_available, future_invokable.
- **Storage Implications:** Requires DB table and UI management.

## Object 4 — Model Roster

- **Purpose:** Defines which models participate in a problem or round.
- **Lifecycle:** default roster → per-round override → response collection → stored attribution.
- **Authority Source:** User selection.
- **Related Objects:** Model Registry Entry, Live Round, Prompt Packet.
- **States:** default, modified, active_this_round, dropped, added.
- **Storage Implications:** Must support many-to-many relationship between rounds and models.

## Object 5 — Prompt Packet

- **Purpose:** Portable instruction payload replacing bare URL copy.
- **Lifecycle:** generated → copied → pasted into external model → response returned.
- **Authority Source:** Live panel prompt generator.
- **Related Objects:** Active Problem, Round, Model Role, CIS_LIVE.md URL.
- **States:** generated, copied, used, stale.
- **Storage Implications:** May be stored for audit or regenerated from round state.

## Object 6 — CIS_LIVE.md Active Broadcast

- **Purpose:** External-readable context file for multi-model collaboration.
- **Lifecycle:** generated from active problem → pushed/published → read by model → updated per round.
- **Authority Source:** Active Live problem state.
- **Related Objects:** Problem Thread, Rounds, Prompt Packet.
- **States:** full_history, compact, active_only, stale.
- **Storage Implications:** Should be generated artifact, not canonical source of truth.

## Object 7 — ADR Record

- **Purpose:** Stores accepted architectural decisions.
- **Lifecycle:** proposed → numbered → posted → accepted → referenced.
- **Authority Source:** User-approved governance process.
- **Related Objects:** Project, Task, Session Handoff, MEMORY.md.
- **States:** accepted, superseded, proposed, missing_required_field.
- **Storage Implications:** DB table requires `decision_number`, `title`, `description`, `rationale`.

## Object 8 — Task Record

- **Purpose:** Stores backlog/deferred implementation work.
- **Lifecycle:** identified → posted → prioritized → built/deferred.
- **Authority Source:** User / session decisions.
- **Related Objects:** ADRs, Build Queue, Session Handoff.
- **States:** backlog, deferred, active, completed.
- **Storage Implications:** DB task table; should include phase and priority.

## Object 9 — Session Handoff

- **Purpose:** Portable session continuity artifact for next chat.
- **Lifecycle:** generated at close → written to multiple locations → centralized → attached next session.
- **Authority Source:** Session Close panel.
- **Related Objects:** Reorientation File, Session Log, Project.
- **States:** generated, centralized, latest, archived.
- **Storage Implications:** Canonical folder: `/mnt/projects/cis/handoff/`.

## Object 10 — Reorientation Document

- **Purpose:** Persistent context restore document attached to every new session.
- **Lifecycle:** maintained → updated when architecture changes → copied to handoff folder → attached with latest handoff.
- **Authority Source:** System context documentation.
- **Related Objects:** Session Handoff, CIS-START output.
- **States:** current, outdated, updated.
- **Storage Implications:** Should reside in `/mnt/projects/cis/handoff/`.

## Object 11 — Session Close Transaction

- **Purpose:** Converts current work into DB log, handoff file, and sync artifacts.
- **Lifecycle:** submitted → writes DB → writes files → commits → returns status.
- **Authority Source:** Session Close API.
- **Related Objects:** Session Log, Handoff, Git Commit, Project.
- **States:** running, completed, failed, partially_complete, duplicate_attempt.
- **Storage Implications:** Needs idempotent transaction record.

## Object 12 — Storage Manifest

- **Purpose:** Canonical mapping of physical drives to VM devices and CIS mount roles.
- **Lifecycle:** created → verified after hardware changes → updated after detach/attach.
- **Authority Source:** Proxmox config + VM `lsblk` + user confirmation.
- **Related Objects:** Mountpoint, Drive Serial, Filesystem Role.
- **States:** verified, missing, extra, detached, retired.
- **Storage Implications:** Should become a persistent markdown/json record.

## Object 13 — Rogue / Detached Drive Record

- **Purpose:** Tracks old Ubuntu/test drive detached from the VM.
- **Lifecycle:** detected → identified → confirmed old OS → detached → retained physically.
- **Authority Source:** Storage audit commands and user confirmation.
- **Related Objects:** Storage Manifest, Proxmox VM hardware.
- **States:** attached_unknown, identified_old_os, detached, do_not_discard.
- **Storage Implications:** Should be stored in infrastructure notes to avoid future confusion.

---

# 12. ARCHITECTURAL DELTA SUMMARY

## What new understanding of CIS exists after this file that did not exist before?

This file changes CIS understanding in five major ways.

## 12.1 CIS Live Is Not Just a Markdown Broadcast; It Is a Multi-Model Coordination System

Before this session, CIS Live could be understood as a live page where session content was published. After this file, CIS Live is clearly a structured collaboration protocol requiring:

- active problem selection
- round awareness
- role-aware prompt generation
- dynamic model roster
- compact context management
- response attribution
- eventual model registry integration

The architectural delta is that external model collaboration needs an instruction-bearing object, not merely a shared URL.

## 12.2 The Intel Sidebar Becomes a Real Intelligence Bridge

Before this session, LOCAL / REMOTE / AGENT tabs could remain decorative. After this file, the model registry becomes the connective tissue between UI and intelligence execution. The Live roster is the first practical use of the registry; local invocation is the next runtime bridge.

The architectural delta is that the intelligence layer enters the application through a model registry object.

## 12.3 Session Continuity Is an Application Requirement, Not a User Memory Task

Before this session, handoff relied on the user remembering where files were located and what to attach. After this file, scattered handoff storage is recognized as a system design flaw. The handoff kit must be centralized, and Session Close must write to the canonical folder automatically.

The architectural delta is that continuity must be operationalized inside the application, not offloaded to the operator.

## 12.4 Governance Requires DB Promotion, Not Just Handoff Text

Before this session, decisions could live in handoff files or memory additions. After this file, the system recognizes that decisions/tasks not promoted to DB are effectively lapsed governance. Required DB fields, ADR numbering, and backfill workflows are now part of the governance model.

The architectural delta is that session outputs must pass through a governance promotion path.

## 12.5 Infrastructure Must Be Manifested, Not Remembered

Before this session, storage mappings were assumed from prior setup. After this file, drive reattachment confusion proves that CIS needs a storage manifest that records physical serials, Proxmox attachments, VM devices, mountpoints, roles, and detach/retain notes.

The architectural delta is that hardware topology must become documented system state.

## 12.6 Session Close Must Become a Transactional Execution Contract

Before this session, Session Close was treated as a button that “does the close.” After this file, it is revealed as a multi-step execution pipeline with failure modes:

- duplicate DB writes
- missing imports
- handoff path confusion
- Git sync uncertainty
- UI hang risk

The architectural delta is that Session Close needs idempotency, step-level status, validation, and non-blocking sync.

## 12.7 Build Order Changed

The next build sequence is now clearer:

```text
Storage and filesystem cleanup
→ Session close / handoff stabilization
→ CIS Live active-problem export
→ Copy Prompt
→ Round compression
→ Dynamic model roster
→ Model registry + Intel sidebar wiring
→ Local model invocation
→ Intelligence wiring for application
```

The session confirms that intelligence wiring cannot proceed cleanly until the application’s collaboration, handoff, and storage foundations stop creating friction.

---

# TOPOLOGY-READY NODE / EDGE SUMMARY

## Nodes

- `LivePanel`
- `CIS_LIVE.md`
- `Active Problem Thread`
- `Live Round`
- `Model Registry`
- `Model Roster`
- `Prompt Packet`
- `Intel Sidebar`
- `LOCAL Tab`
- `REMOTE Tab`
- `AGENT Tab`
- `Decision DB`
- `Task DB`
- `Session Close Panel`
- `Session Close API`
- `Session Log`
- `Handoff Markdown`
- `/mnt/projects/cis/handoff/`
- `2_CIS_REORIENTATION.md`
- `Git/Vault Sync`
- `Storage Manifest`
- `Proxmox VM Hardware Config`
- `/mnt/models`
- `/mnt/archive`
- `/mnt/cache`
- `/mnt/projects`
- `Detached Old Ubuntu Drive`

## Edges

```text
Active Problem Thread → CIS_LIVE.md
Active Problem Thread → Prompt Packet
Live Round → Model Roster
Model Registry → Model Roster
Model Registry → Intel Sidebar
Intel Sidebar → LOCAL / REMOTE / AGENT Tabs
Prompt Packet → External Model Response
External Model Response → Live Round
Live Round → CIS Live DB
Session Close Panel → Session Close API
Session Close API → Session Log
Session Close API → Handoff Markdown
Handoff Markdown → /mnt/projects/cis/handoff/
Session Close API → Git/Vault Sync
Decision Insight → ADR Record
Deferred Feature → Task Record
Proxmox Config → Storage Manifest
Storage Manifest → Mountpoint Verification
Old Ubuntu Drive → Detached / Retained
```

## Critical Build Edges

```text
Copy Prompt depends on Active Problem + Round + Model Role
Dynamic Model Roster depends on Model Registry
Intel Sidebar Functionality depends on Model Registry
Local Model Invocation depends on Model Registry + Runtime Execution Bridge
Clean Session Start depends on Centralized Handoff Folder
Filesystem Cleanup depends on Storage Manifest
Session Close Reliability depends on Idempotency + Step Logs
```
