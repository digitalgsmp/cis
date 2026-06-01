# cis_chat_2026_04_007_extraction_analysis

Source file: `CIS_Chat_2026-04_007.md`
Extraction mode: Implementation-grade architectural topology extraction

---

# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery Name: Handoff Location Friction Became a Runtime Architecture Defect

- **Architectural Significance**
  - The session close / start workflow exposed that continuity is not just a documentation problem; it is an operational path dependency.
  - Handoff files being split between `/mnt/projects/cis/projects/PROJECT__CIS__BUILD__V1/` and `/mnt/projects/cis/handoff/` created unnecessary operator burden and increased session-start failure risk.
  - The handoff process must be treated as a runtime object lifecycle, not a memory aid.

- **Affected Layers**
  - Governance Layer
  - Runtime / Execution Layer
  - Application Surface
  - Continuity / Memory Layer
  - Filesystem Governance

- **Dependency Impact**
  - Session start depends on a deterministic handoff package location.
  - Session close depends on canonical write routing.
  - CIS-START depends on the latest valid handoff artifact being discoverable.
  - Reorientation and handoff files must converge into a single operator-facing location.

- **Build Impact**
  - Build order changes: before further ADR implementation, handoff output routing must be corrected or explicitly carried as debt.
  - The close-session operation must write to `/mnt/projects/cis/handoff/` directly, or copy there as part of the close transaction.
  - A future handoff package builder is required to eliminate manual file assembly.

- **Runtime Impact**
  - Session close becomes a canonical artifact-generation event.
  - Session start becomes a deterministic package-load event.
  - The operator should not need to remember two separate source paths.

## Discovery Name: Filesystem Drift Became a First-Class Governance Problem

- **Architectural Significance**
  - The transcript reveals the system entered a high-risk “80% done destruction wall” state where progress exists, but structural ambiguity threatens stability.
  - Folder confusion was not cosmetic; it affected the operator’s ability to understand what is active, stale, duplicated, safe to move, or canonical.
  - The missing object was not another build feature; it was a filesystem authority map.

- **Affected Layers**
  - Filesystem Governance
  - Runtime Layer
  - Knowledge Layer
  - Memory Layer
  - Documentation / Obsidian Vault Layer

- **Dependency Impact**
  - Any cleanup depends on a snapshot, full file map, and no-delete migration plan.
  - Runtime stability depends on knowing which files are active.
  - Knowledge integrity depends on resolving duplicate record locations.
  - Database integrity depends on identifying the canonical database.

- **Build Impact**
  - New prerequisite: create `CIS_FILE_MAP.md` before reorganization.
  - Reorganization must happen through reviewed moves / renames only, not deletion.
  - Runtime app code and canonical DB must be explicitly protected.

- **Runtime Impact**
  - File structure becomes part of runtime state.
  - Stale duplicates create risk of editing or running the wrong artifact.
  - Obsidian-readable documentation and canonical runtime data need separation rules.

## Discovery Name: Snapshot Became a Mandatory Pre-Migration Gate

- **Architectural Significance**
  - The transcript formalizes a safety pattern: before filesystem restructuring or storage attachment work, a VM snapshot is required.
  - Snapshot naming and description became part of governance documentation.

- **Affected Layers**
  - Infrastructure Layer
  - Governance Layer
  - Runtime Recovery Layer
  - Operator Safety Layer

- **Dependency Impact**
  - Any structural cleanup depends on rollback availability.
  - VM snapshot requires temporary storage detachment or awareness of attached disks.
  - Reattachment order becomes part of recovery procedure.

- **Build Impact**
  - Future reorganization work must include a pre-flight snapshot checkpoint.
  - Snapshot description should encode system state, operational status, DB status, and migration purpose.

- **Runtime Impact**
  - Snapshot operations can mutate perceived disk availability.
  - Recovery procedures must include validation of mounted storage after snapshot operations.

## Discovery Name: Raw Disk Passthrough Recovery Became a Runtime Dependency

- **Architectural Significance**
  - The storage recovery sequence exposed that `/mnt/projects`, `/mnt/archive`, `/mnt/models`, and `/mnt/cache` are not just storage folders; they are runtime infrastructure dependencies.
  - The 10TB archive, model disk, cache disk, and project disk are part of the active CIS operating topology.

- **Affected Layers**
  - Infrastructure Layer
  - Intelligence Layer
  - Knowledge Layer
  - Runtime Layer
  - Archive Intake Layer

- **Dependency Impact**
  - `/mnt/archive` must be mounted before large-scale archive ingestion can continue.
  - `/mnt/models` must be mounted before local model workflows can run.
  - `/mnt/cache` must be mounted before cache-heavy processing can be trusted.
  - `/mnt/projects` must be mounted before runtime, memory, knowledge, and project paths resolve.

- **Build Impact**
  - A storage health check should precede all CIS runtime work.
  - VM config must preserve raw disk passthrough by stable `/dev/disk/by-id/` references.
  - `/etc/fstab` must avoid fragile device names where possible.

- **Runtime Impact**
  - Disk detachment during snapshot created a recovery workflow: inspect VM config, inspect Proxmox disk IDs, reattach via `qm set`, verify inside VM with `lsblk`, run `mount -a`, manually mount shifted devices if needed, then validate with `df -h`.

## Discovery Name: Canonical vs Human-Readable Mirror Split Emerged

- **Architectural Significance**
  - The user clarified that Obsidian is the human-readable representation of what is in the database.
  - This invalidates a simplistic “duplicates are stale” assumption.
  - Some duplicated-looking artifacts may be mirrors, not mistakes.

- **Affected Layers**
  - Knowledge Layer
  - Memory Layer
  - Obsidian Documentation Layer
  - Database Layer
  - Filesystem Governance

- **Dependency Impact**
  - Cleanup cannot assume identical folder names are redundant.
  - Canonical database / runtime records and human-readable mirrors need explicit authority rules.
  - Diffing record copies becomes mandatory before archiving or renaming.

- **Build Impact**
  - `CIS_FILE_MAP.md` must classify files as canonical, mirror, stale, active, deprecated, unknown, or archive.
  - Obsidian vault should be preserved as human orientation / mirror layer unless proven stale.

- **Runtime Impact**
  - Human-readable files may represent DB state but are not automatically canonical.
  - Runtime writes should target canonical DB / records; mirror sync should be explicit.

## Discovery Name: Canonical Database Identification Became a Required State Check

- **Architectural Significance**
  - The transcript identified multiple database files: `memory/cis_memory.db`, `memory/cis.db`, and a DB copy under `docs/.../runtime_scripts/memory/`.
  - The active application DB had to be located by runtime config rather than assumed by filename.

- **Affected Layers**
  - Memory Layer
  - Runtime Layer
  - Database Layer
  - Governance Layer

- **Dependency Impact**
  - Any DB cleanup depends on discovering the configured `DB_PATH`.
  - Stale DBs must be renamed, not deleted, until confirmed obsolete.

- **Build Impact**
  - `memory/cis_memory.db` becomes canonical if confirmed by runtime config.
  - `memory/cis.db` should be marked stale, not removed immediately.
  - DB path should be captured in file map and operational reality docs.

- **Runtime Impact**
  - Running app stability depends on not moving or renaming the canonical DB.
  - Duplicate DBs create a risk of editing the wrong institutional memory.

## Discovery Name: Cleanup Requires a Non-Destructive Migration Contract

- **Architectural Significance**
  - The user explicitly requested cleanup “without deleting anything.”
  - The system response evolved into a safe migration pattern: snapshot → file map → proposed move plan → user approval → one script → no deletions.

- **Affected Layers**
  - Governance Layer
  - Execution Layer
  - Operator Safety Layer
  - Filesystem Governance

- **Dependency Impact**
  - Structural changes require user approval.
  - No-delete policy precedes any move script.
  - Cleanup requires a known protected set: runtime app, canonical DB, canonical records, ingest, and Git vault.

- **Build Impact**
  - Filesystem governance must include move-only, archive-first, rename-stale patterns.
  - Any cleanup script must be reviewable before execution.

- **Runtime Impact**
  - Structural cleanup becomes a controlled action, not a maintenance convenience.
  - The operator’s anxiety is an architectural signal: when structure is unclear, system reliability is not trusted.

---

# 2. TOPOLOGY MUTATIONS

## New Layers

### Filesystem Governance Layer

- Emerged as a necessary bridge between runtime, documentation, memory, and knowledge storage.
- Must classify every file or folder by role:
  - canonical runtime
  - canonical database
  - canonical knowledge record
  - human-readable mirror
  - handoff artifact
  - stale duplicate
  - archive / legacy
  - unknown / requires review

### Recovery / Mount Validation Layer

- Storage mounts became runtime prerequisites.
- CIS requires a pre-work check for:
  - `/mnt/projects`
  - `/mnt/archive`
  - `/mnt/models`
  - `/mnt/cache`

### Handoff Package Layer

- Handoff is no longer just a file; it is a session transition package.
- The package must support:
  - latest session handoff
  - reorientation file
  - start prompt / CIS-START output
  - eventually primer set and active context

## Split Layers

### Runtime vs Obsidian Mirror

- Runtime code and canonical data live under `/mnt/projects/cis/runtime/`, `/mnt/projects/cis/memory/`, and `/mnt/projects/cis/knowledge/`.
- Obsidian represents human-readable orientation and mirrors, not necessarily executable runtime state.

### Canonical Knowledge Records vs Human-Readable Knowledge Records

- `/mnt/projects/cis/knowledge/records/` is treated as canonical.
- `docs/CIS_Creative_Intelligence_System_v1/knowledge_records/` may function as a readable or synced mirror, but cannot be assumed canonical without explicit authority.

### Handoff Generation vs Handoff Storage

- Session close generates handoff.
- Canonical storage must be `/mnt/projects/cis/handoff/`.
- Prior write path to project folder becomes legacy / transitional.

## Runtime Bridges

- Proxmox host → raw disk passthrough → creative VM → `/etc/fstab` → CIS mounted paths.
- Dashboard session close → handoff artifact → next-session CIS-START workflow.
- File map → migration script → protected runtime preservation.

## Orchestration Changes

- Operator confusion around “what’s first” revealed the need for a stricter command hierarchy:
  - acknowledge the next required action
  - do not offer competing options when one action is clearly first
  - protect operator from ambiguous branching during high-risk operations

## Governance Expansion

- Snapshot-before-cleanup becomes a governance gate.
- File map-before-migration becomes a governance gate.
- User approval-before-move-script becomes a governance gate.
- No deletion becomes a migration constraint.

## Object-Model Mutations

New or strengthened objects:

- `CIS_FILE_MAP.md`
- `handoff package`
- `storage mount state`
- `snapshot checkpoint`
- `canonical database`
- `human-readable mirror`
- `stale duplicate`
- `protected runtime set`

## Workflow / Execution Separation

- “Clean up the folder structure” was not directly executable until translated into:
  - inventory command
  - snapshot gate
  - classification object
  - move plan
  - approval checkpoint
  - migration script
  - validation checks

## Project-Container Evolution

- The build project folder was revealed as overloaded: project output, handoff storage, and session continuity artifacts were mixed.
- Handoff needs to leave the project folder and become a system-level continuity artifact.

---

# 3. DEPENDENCY DISCOVERIES

## Hidden Prerequisites

- Snapshot before filesystem restructuring.
- Storage mount validation before running file inventory or runtime cleanup.
- Canonical DB discovery before renaming duplicate DBs.
- Diff comparison before resolving duplicated knowledge records.
- File map before move script.
- User approval before structural moves.
- Stable handoff folder before reliable session start.

## Sequencing Constraints

1. Restore VM / mount state.
2. Confirm `/mnt/projects` availability.
3. Confirm archive/model/cache disks if relevant to current work.
4. Run `find /mnt/projects/cis -maxdepth 5 | sort`.
5. Build `CIS_FILE_MAP.md`.
6. Classify active / stale / mirror / unknown artifacts.
7. Propose non-destructive target structure.
8. Confirm canonical DB and record authority.
9. Execute one reviewed move-only script.
10. Validate runtime still launches.

## Circular Dependencies

- To clean filesystem, the system needs the file map; to build the file map, `/mnt/projects` must mount; mounting required VM recovery; VM recovery depended on knowing the prior storage topology that was not fully documented.
- Handoff exists to preserve continuity, but the handoff system itself required continuity knowledge to repair.

## Unstable Dependencies

- `/dev/sda2` path for the 10TB archive was unstable after disk reattachment; it shifted to `/dev/vdc2` inside the VM.
- Proxmox UI disk dropdown was insufficient for raw disk passthrough restoration.
- Console access was unreliable; VS Code SSH became the working access path.
- Duplicate DBs and records create unstable source-of-truth conditions.

## Runtime Blockers

- Missing `/mnt/archive`, `/mnt/models`, and `/mnt/cache` mounts.
- Frozen or non-responsive VM console.
- No guest agent / no IP display.
- Device path mismatch in `/etc/fstab`.
- Handoff file split across folders.

## Orchestration Bottlenecks

- Human operator had to mediate Proxmox, VM shell, VS Code, file paths, and recovery commands.
- Lack of a single system map forced repeated clarification.
- Current assistant behavior offering choices when one next action exists increased cognitive load.

---

# 4. EXECUTION-LAYER IMPLICATIONS

## Commands Extracted

### Session / Handoff

```bash
# End session through dashboard
CLOSE SESSION + COMMIT

# Start session through dashboard
RUN CIS-START
```

### File Inventory

```bash
find /mnt/projects/cis -maxdepth 5 | sort
```

### Snapshot Naming

```text
Snapshot name: cis-pre-reorg-20260421
Description: CIS dashboard operational. Flask modular backend running. 30 decisions in DB. Pre-folder reorganization and file map creation. Safe rollback point.
```

### Proxmox VM Config Inspection

```bash
cat /etc/pve/qemu-server/100.conf
```

### Proxmox Raw Disk ID Discovery

```bash
ls -la /dev/disk/by-id/ | grep -v part | grep -v loop
```

### Raw Disk Passthrough Reattachment

```bash
qm set 100 -virtio2 /dev/disk/by-id/ata-ST10000DM0004-2GR11L_ZJV684TL,iothread=1
qm set 100 -virtio3 /dev/disk/by-id/ata-Samsung_SSD_850_EVO_120GB_S21TNXAG621275D,iothread=1
qm set 100 -virtio4 /dev/disk/by-id/ata-WDC_WDS250G1B0A-00H9H0_172533803130,iothread=1
qm set 100 -virtio5 /dev/disk/by-id/ata-WDC_WDS250G1B0A-00H9H0_172563800132,iothread=1
```

### VM Mount Validation

```bash
df -h
cat /etc/fstab
lsblk
lsblk | grep vd
sudo mount -a
sudo mount /dev/vdc2 /mnt/archive
sudo sed -i 's|/dev/sda2|/dev/vdc2|' /etc/fstab
```

### DB / Record Authority Checks

```bash
grep -r "cis_memory\|cis\.db" /mnt/projects/cis/runtime/db/connection.py
cat /mnt/projects/cis/runtime/db/connection.py
cat /mnt/projects/cis/runtime/config.py

diff -rq /mnt/projects/cis/knowledge/records/ "/mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1/knowledge_records/records/"

diff /mnt/projects/cis/knowledge/records/IMAGE__WEIRD_WAR_TALES_COVER__001/record_001.json "/mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1/knowledge_records/records/IMAGE__WEIRD_WAR_TALES_COVER__001/record_001.json"
```

## States

### Storage Mount States

- unknown
- detached
- attached-to-Proxmox
- visible-to-VM
- mounted
- fstab-corrected
- validated

### Cleanup States

- unsafe / no snapshot
- snapshot complete
- inventory captured
- file map drafted
- proposed mapping ready
- user approved
- script generated
- migration executed
- runtime validated

### Artifact Authority States

- canonical
- mirror
- stale duplicate
- active but misplaced
- deprecated
- archive
- unknown / requires review

## Transitions

### Handoff Transition

```text
Session close form filled
→ CLOSE SESSION + COMMIT
→ handoff generated
→ handoff written to canonical folder
→ next session CIS-START references same folder
```

### Storage Recovery Transition

```text
Disks detached for snapshot
→ VM starts with missing mounts
→ Proxmox by-id disks discovered
→ raw disks reattached via qm set
→ VM block devices visible
→ mount points restored
→ df -h validates storage topology
```

### Cleanup Transition

```text
Operator confusion
→ snapshot gate
→ inventory command
→ file map creation
→ proposed structure
→ user approval
→ move-only script
→ runtime validation
```

## Runtime Contracts

- No cleanup without snapshot.
- No deletion during structural cleanup.
- No moving app code during file governance cleanup.
- No renaming canonical DB without runtime config confirmation.
- No assuming Obsidian copies are stale without diff and authority classification.
- No using unstable host/VM device names without validation.

## Validation Behavior

- `df -h` validates mounted storage.
- `lsblk` validates VM-visible disks.
- `cat /etc/fstab` validates persistent mount intent.
- `diff -rq` validates duplicate record divergence.
- `grep` / config read validates active DB path.
- Post-cleanup runtime launch must validate no breakage.

## Pass / Fail Structures

### PASS: Storage Restored

- `/mnt/projects` mounted.
- `/mnt/archive` mounted.
- `/mnt/models` mounted.
- `/mnt/cache` mounted.
- `df -h` confirms expected capacities.

### FAIL: Storage Incomplete

- Any required mount missing.
- Device exists but not mounted.
- fstab references wrong device.
- VM cannot see disk.

### PASS: Cleanup Safe to Proceed

- Snapshot complete.
- File inventory captured.
- Canonical DB identified.
- Duplicate record differences known.
- User approves move plan.

### FAIL: Cleanup Unsafe

- No snapshot.
- Unknown active DB.
- Unknown record authority.
- Script includes deletes.
- Runtime files are moved without explicit protection.

## Retry / Escalation Logic

- If Proxmox UI cannot attach raw disks, escalate to `qm set` with `/dev/disk/by-id/`.
- If Proxmox console is frozen, use VS Code / SSH.
- If `mount -a` fails due to device name mismatch, inspect `lsblk`, mount manually, update fstab.
- If duplicate records differ, do not resolve automatically; flag for separate authority review.

---

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## Authority Structures

- Human operator is final authority for structural cleanup approval.
- Runtime config is authority for active DB path.
- `/mnt/projects/cis/knowledge/records/` is the presumed canonical knowledge record path, pending mirror policy.
- Obsidian vault is human-readable / institutional memory surface, not automatically canonical runtime.
- Snapshot is the rollback authority for unsafe filesystem changes.

## Review States

### Filesystem Items

- active
- canonical
- human-readable mirror
- stale
- duplicate
- unknown
- archive
- protected

### Migration Plan

- drafted
- reviewed
- approved
- executed
- validated

## Promotion Logic

- A proposed folder structure is not promoted to action until user approval.
- A DB file is not marked stale until runtime config confirms canonical DB.
- A duplicate knowledge record is not archived until diff confirms whether it is a mirror or divergent content.
- Handoff path change is promoted only after close-session write behavior is changed and verified.

## Rejection Paths

- Reject any cleanup script that deletes files.
- Reject any migration that touches runtime app code without reason.
- Reject stale classification if Obsidian file is a live human-readable mirror.
- Reject any command sequence that assumes Proxmox UI state without shell verification.

## Trust Enforcement

- Trust comes from explicit validation commands, not conversational confidence.
- “Looks mounted” is insufficient; `df -h` is required.
- “This is stale” is insufficient; diff / config verification is required.
- “Snapshot is done” should be confirmed before structural work.

## Hallucination Controls

- Assistant must not claim access to `/mnt/projects/cis` from a sandbox.
- Assistant must ask for actual command output from the creative VM / Proxmox host.
- Assistant must distinguish VM shell from Proxmox host shell.
- Assistant must not infer deleted / moved state without evidence.

## Provenance Enforcement

- Snapshot name and description preserve pre-change state.
- `cat /etc/pve/qemu-server/100.conf` preserves VM hardware topology evidence.
- `df -h`, `lsblk`, and `fstab` preserve storage state evidence.
- `diff` preserves evidence for duplicate record resolution.

## Validation Contracts

- Cleanup contract: snapshot + file map + approved move plan + no deletion + runtime validation.
- Storage contract: by-id passthrough + VM-visible devices + mount validation + fstab correction.
- Handoff contract: single canonical handoff folder + session close write + session start read.

---

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## Knowledge Formation Logic

- The transcript does not primarily advance extraction model behavior; it advances knowledge system integrity.
- Knowledge records require canonical storage and readable mirrors to be governed as different objects.
- Duplicate record locations reveal that knowledge formation must include sync / mirror policy.

## Retrieval Structure

- Retrieval should point to canonical records, not Obsidian mirrors unless mirrors are formally indexed as human-readable views.
- If Obsidian mirrors represent DB contents, retrieval must know whether to search canonical JSON, markdown mirrors, or both.

## Indexing Implications

- `CIS_FILE_MAP.md` becomes a meta-index over the CIS filesystem.
- Knowledge records require source-of-truth tagging:
  - canonical JSON
  - markdown mirror
  - DB-backed record
  - stale export
  - divergent duplicate

## Normalization Rules

- Obsidian files should not be treated as loose duplicates until normalized into a known mirror relationship.
- Canonical DB and canonical knowledge records need one-way or two-way sync rules.
- Human-readable mirror files should carry provenance back to DB record ID or source record path.

## Ontology / Spine Implications

- A new filesystem ontology is required:
  - runtime zone
  - memory zone
  - knowledge zone
  - handoff zone
  - docs / mirror zone
  - archive zone
  - legacy zone
- This ontology supports future topology diagrams and build sequencing.

## Chunking Logic

- No direct chunking changes emerged, but filesystem drift suggests chunk provenance must include canonical source location and mirror location if both exist.

## Reinforcement Behavior

- The system learned from operator friction:
  - two handoff locations are invalid
  - unclear folder authority is a blocker
  - assistant branching behavior can increase confusion
  - non-destructive migration increases trust

## Project Linkage

- Handoff files should not remain embedded only in `PROJECT__CIS__BUILD__V1` if they are system-level continuity objects.
- Project folders should remain project containers, not general handoff or governance dumping grounds.

## Stabilization Loops

- Confusion → file inventory → file map → proposed structure → user correction → stable filesystem governance.
- Duplicate discovery → diff → authority classification → mirror policy → reduced drift.

---

# 7. APPLICATION-LAYER IMPLICATIONS

## Workbench Requirements

- The application layer needs a system status / filesystem health surface eventually, but not before the runtime contract is stable.
- A future operator-facing panel should show:
  - mounted storage status
  - canonical handoff folder
  - latest handoff file
  - active DB path
  - stale duplicate warnings
  - current session state

## Interface Panels

### Handoff Panel

- Shows latest handoff.
- Shows reorientation file.
- Allows copy / package / download.
- Confirms session close wrote to canonical folder.

### Storage Health Panel

- Shows `/mnt/projects`, `/mnt/archive`, `/mnt/models`, `/mnt/cache` mount status.
- Shows capacity and usage.
- Flags missing mounts before runtime actions.

### Filesystem Map Panel

- Displays active / stale / mirror / unknown classification.
- Allows approval of proposed move-only cleanup plans.

### Runtime Safety Panel

- Shows snapshot recommendation before high-risk operations.
- Shows protected runtime paths.
- Prevents deletion-based cleanup.

## Operator Actions

- Close session.
- Start session.
- Generate handoff package.
- Run storage health check.
- Generate file map.
- Review cleanup plan.
- Approve move-only migration.

## Runtime Visibility Needs

- The operator needs to know what is running, mounted, canonical, stale, and safe.
- Lack of visibility caused loss of confidence even when parts of the system were technically functional.

## Workflow Exposure

- Session close and session start should be visible as lifecycle flows, not hidden file writes.
- Cleanup should be exposed as a staged, reviewable workflow.

## Project-Centered Interaction

- Project folders should contain project artifacts.
- System-level session continuity should move to system-level handoff.
- Application should distinguish project context from system operation context.

## Application / Runtime Bridges

- UI button → queue / route → runtime command → artifact write → status update.
- File map object → interface review → migration script generation.
- Storage check command → dashboard status indicator.

---

# 8. FEEDBACK LOOP DISCOVERIES

## Reinforcement Loops

### Handoff Friction Loop

```text
Session start confusion
→ user identifies friction
→ folder split recognized as design flaw
→ canonical handoff folder proposed
→ future session close routing must change
```

### Filesystem Drift Loop

```text
Operator confusion
→ request full ls/find
→ snapshot gate introduced
→ file map required
→ cleanup plan becomes governed
```

### Recovery Loop

```text
Snapshot requires disk detachment
→ mounts missing
→ disk topology inspected
→ raw disk passthrough restored
→ fstab corrected
→ storage state validated
```

## Correction Loops

- Assistant initially misread physical disk attachment path; user correction forced Proxmox by-id passthrough procedure.
- Assistant initially treated Obsidian copies as stale; user corrected that Obsidian is human-readable representation of DB.
- Assistant offering options after stating “what’s first” was corrected as confusing; operator behavior rules must reduce branching.

## Governance Loops

- High-risk operation → snapshot → validate → proceed.
- Unknown file authority → map → classify → approve → move.
- Duplicate DB / records → inspect config / diff → classify → rename or retain.

## Retrieval-Improvement Loops

- File map improves retrieval of system artifacts.
- Canonical vs mirror distinction improves future search and reduces false duplicates.

## Archive-Learning Loops

- Restoring `/mnt/archive` is prerequisite to archive-driven knowledge formation.
- Archive mount status becomes part of readiness before intake / ingestion work.

## Continuity / Memory Loops

- Session close writes handoff.
- Session start reads handoff and reorientation.
- Misplaced handoff breaks continuity.
- Single-folder handoff package improves continuity.

## Project-Output Feedback Loops

- Not central in this transcript, but file governance affects whether project outputs and system outputs are stored in the correct layer.

---

# 9. UNRESOLVED GAPS + MISSING LAYERS

## Missing Runtime Bridges

- No automatic handoff package builder yet.
- No automatic storage health check visible in dashboard.
- No automated raw disk passthrough recovery documentation inside CIS.
- No runtime command that reports canonical DB, records path, handoff path, and mount status in one place.

## Undefined Objects

- `handoff package`
- `CIS_FILE_MAP.md` schema
- `storage_mount_state`
- `human_readable_mirror`
- `stale_duplicate`
- `protected_runtime_set`
- `cleanup_plan`
- `migration_script_manifest`

## Unstable Schemas

- File map schema not yet defined.
- Mirror / canonical relationship schema not yet defined.
- DB duplicate classification not formalized.
- Handoff file lifecycle not formalized.

## Unresolved Orchestration

- Session close still needs to write directly to `/mnt/projects/cis/handoff/`.
- The proposed cleanup script was not executed in the transcript.
- The difference in `IMAGE__WEIRD_WAR_TALES_COVER__001/record_001.json` remains unresolved.
- `runtime/live_db.py` stale status requires confirmation before move.

## Unresolved Routing

- Whether Obsidian knowledge records should be generated from canonical DB or manually maintained is unresolved.
- Whether handoff files should be copied, moved, or generated directly into canonical folder is unresolved.
- Whether all stale runtime scripts should be archived or replaced by links / mirrors is unresolved.

## Missing Governance

- Filesystem Governance ADR / contract needed.
- Handoff package contract needed.
- Mirror authority contract needed.
- Storage health preflight contract needed.

## Missing Validation Layers

- No automated diff review tool for canonical records vs Obsidian mirrors.
- No DB path validator exposed to operator.
- No mount validator exposed to operator.
- No stale duplicate detector.

## Unresolved Application Surfaces

- No dashboard view for storage mount state.
- No dashboard view for latest handoff package.
- No dashboard view for file map / duplicate risk.
- No dashboard review workflow for cleanup plans.

## Unresolved Storage Rules

- `/dev/vdc2` was patched into fstab, but stable UUID-based archive mounting should be reconsidered.
- Canonical placement of Obsidian readable mirrors remains unresolved.
- Handoff canonical storage is identified, but legacy copies remain.

---

# 10. BUILD-PLAN IMPLICATIONS

## Foundational Prerequisites

1. Validate storage mounts.
2. Confirm canonical DB.
3. Generate `CIS_FILE_MAP.md`.
4. Define file authority classes.
5. Fix handoff write path.
6. Establish no-delete cleanup script pattern.
7. Validate runtime after cleanup.

## Blocked Layers

- Application surfaces are blocked until runtime / filesystem authority is stable.
- Knowledge retrieval is weakened until canonical vs mirror paths are resolved.
- Handoff automation is blocked until canonical handoff package behavior is defined.
- Filesystem cleanup is blocked until user approval and file map exist.

## Sequencing Implications

### Correct Near-Term Sequence

```text
1. Storage health validation
2. File inventory
3. CIS_FILE_MAP.md
4. Canonical DB confirmation
5. Duplicate record diff review
6. Handoff write path fix
7. Move-only cleanup script
8. Runtime verification
9. Update operational docs
```

### Incorrect Sequence

```text
1. Move folders immediately
2. Delete duplicates
3. Build more UI
4. Continue ADR features while handoff remains split
```

## Runtime-First Requirements

- Runtime app code must remain untouched during cleanup.
- DB path must remain stable.
- Mounted disks must be present before file map or migration work.

## Governance-First Requirements

- Snapshot before reorganization.
- Human approval before structural changes.
- No deletion during first cleanup pass.
- Move plan must be visible before execution.

## Execution-First Requirements

- File map generation must be repeatable.
- Cleanup must be scriptable.
- Validation commands must be known.
- All results must be confirmable with command output.

## Application Dependencies

- Future UI needs runtime endpoints for:
  - mount status
  - DB path
  - latest handoff
  - file authority map
  - duplicate detection
  - cleanup plan review

---

# 11. EXTRACTED CANONICAL OBJECTS

## Object: Handoff Package

- **Purpose**
  - Preserve continuity between sessions with a deterministic set of required files / prompts.
- **Lifecycle**
  - generated at session close → stored in canonical handoff folder → loaded at session start → superseded by next close.
- **Authority Source**
  - Session Close process / CIS-START process.
- **Related Objects**
  - `CIS_Handoff_[latest].md`, `2_CIS_REORIENTATION.md`, CIS-START output, primer set.
- **States**
  - generated, current, superseded, missing, invalid.
- **Storage Implications**
  - Canonical location: `/mnt/projects/cis/handoff/`.

## Object: CIS_FILE_MAP.md

- **Purpose**
  - Provide one orientation document describing every file/folder, role, and authority state.
- **Lifecycle**
  - generated from inventory → reviewed → updated after migration → used for future governance.
- **Authority Source**
  - Filesystem inventory + operator confirmation.
- **Related Objects**
  - runtime, memory, knowledge, handoff, docs, Obsidian vault, archive.
- **States**
  - draft, reviewed, active, outdated.
- **Storage Implications**
  - Stored at `/mnt/projects/cis/CIS_FILE_MAP.md`.

## Object: Snapshot Checkpoint

- **Purpose**
  - Provide rollback before high-risk migration / reorganization.
- **Lifecycle**
  - created before migration → referenced in migration plan → retained until stability confirmed.
- **Authority Source**
  - Proxmox snapshot metadata.
- **Related Objects**
  - VM config, mounted disks, cleanup script, runtime state.
- **States**
  - requested, complete, verified, rollback-used, retired.
- **Storage Implications**
  - Lives in Proxmox snapshot system; must be named and described in CIS handoff / operational docs.

## Object: Storage Mount State

- **Purpose**
  - Represent availability of critical storage paths.
- **Lifecycle**
  - unknown → attached → visible → mounted → validated.
- **Authority Source**
  - `df -h`, `lsblk`, `/etc/fstab`, Proxmox VM config.
- **Related Objects**
  - `/mnt/projects`, `/mnt/archive`, `/mnt/models`, `/mnt/cache`.
- **States**
  - missing, attached, visible, mounted, validated, failed.
- **Storage Implications**
  - Should become a runtime status object or dashboard health check.

## Object: Canonical Database

- **Purpose**
  - Store active CIS institutional memory / runtime data.
- **Lifecycle**
  - configured → active → backed up → migrated if needed.
- **Authority Source**
  - Runtime config path.
- **Related Objects**
  - `cis_memory.db`, stale DB copies, Obsidian mirrors, runtime app.
- **States**
  - active, stale, backup, unknown.
- **Storage Implications**
  - Canonical file should remain `/mnt/projects/cis/memory/cis_memory.db` if config confirms.

## Object: Human-Readable Mirror

- **Purpose**
  - Provide Obsidian-readable representation of canonical DB / records.
- **Lifecycle**
  - generated or maintained from canonical source → reviewed → synced or marked divergent.
- **Authority Source**
  - Mirror policy, DB provenance, user correction.
- **Related Objects**
  - Obsidian vault, knowledge records, DB rows, markdown records.
- **States**
  - current mirror, stale mirror, divergent, unknown.
- **Storage Implications**
  - Must not be deleted as duplicate without authority review.

## Object: Stale Duplicate

- **Purpose**
  - Mark files that duplicate older runtime / DB / record content and should not be edited or executed.
- **Lifecycle**
  - detected → compared → classified → renamed or archived.
- **Authority Source**
  - Diff, runtime config, user confirmation.
- **Related Objects**
  - stale runtime scripts, stale DBs, duplicated knowledge records.
- **States**
  - suspected, confirmed, renamed, archived.
- **Storage Implications**
  - Rename pattern preferred: `.stale` or move to `_archive/`, not deletion.

## Object: Protected Runtime Set

- **Purpose**
  - Define files and folders that cleanup scripts must not move.
- **Lifecycle**
  - defined before migration → enforced during script generation → validated after cleanup.
- **Authority Source**
  - Runtime map and app configuration.
- **Related Objects**
  - `/mnt/projects/cis/runtime/`, `/mnt/projects/cis/memory/cis_memory.db`, `/mnt/projects/cis/knowledge/records/`, `/mnt/projects/cis/ingest/`.
- **States**
  - protected, movable, archive-only, unknown.
- **Storage Implications**
  - Cleanup scripts must explicitly exclude protected paths.

## Object: Cleanup Plan

- **Purpose**
  - Convert structural confusion into a reviewable migration path.
- **Lifecycle**
  - drafted → reviewed → approved → scripted → executed → validated.
- **Authority Source**
  - File map + user approval.
- **Related Objects**
  - move script, file map, snapshot, stale duplicates.
- **States**
  - draft, pending approval, approved, executed, failed, superseded.
- **Storage Implications**
  - Should be stored with handoff / governance artifacts.

---

# 12. ARCHITECTURAL DELTA SUMMARY

“What new understanding of CIS exists after this file that did NOT exist before?”

After this file, CIS is no longer understood only as a modular application, intelligence system, or knowledge pipeline. It is now understood as a fragile but recoverable runtime organism whose continuity depends on filesystem authority, storage topology, and handoff determinism.

The key new understanding is:

> CIS cannot become stable merely by adding features. It must first make its own operating structure legible, canonical, and recoverable.

The file reveals that:

- Handoff friction is an architecture defect, not a user inconvenience.
- Filesystem drift is a governance problem, not a housekeeping task.
- Storage mounts are runtime dependencies, not background infrastructure.
- Obsidian readable files may be mirrors of canonical DB state, not disposable duplicates.
- Cleanup must be governed by snapshot, file map, user approval, no deletion, and validation.
- The operator’s confusion is a valid topology signal: if the human cannot locate or trust the active system state, the system is not operationally mature.
- `CIS_FILE_MAP.md` becomes a necessary bridge between filesystem reality and application-layer control.
- The next stable CIS build path must include filesystem governance and handoff consolidation before further feature expansion.

The architectural delta is therefore:

```text
Previous understanding:
CIS needs more runtime features, ADR implementation, and application evolution.

New understanding:
CIS first needs canonical filesystem authority, deterministic handoff routing,
storage health validation, and non-destructive migration governance so that
existing runtime progress is protected and legible.
```

This transcript contributes a major topology correction: the system is not blocked by missing ambition or missing tools; it is blocked by hidden operational ambiguity around where truth lives, what is safe to move, what is canonical, and how sessions survive across time.

