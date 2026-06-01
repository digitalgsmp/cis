# CIS Source Manifest Contract v2.1
# Path: /mnt/projects/cis/docs/contracts/CIS Source Manifest Contract.md
# Status: DRAFT — awaiting verification
# ADR reference: ADR-007 (source manifest is the control object for all intake)

---

## Purpose

The source manifest is the canonical intake record created when raw material
enters CIS. It is created before any processing begins and governs all
downstream behavior for that source.

The manifest is a control object, not a knowledge object.
Knowledge begins only after extraction produces knowledge_record outputs.
The manifest remains as the lineage anchor for everything derived from it.

---

## When a Manifest Is Created

A manifest is created exactly once per source, at intake.
It is created by cis_intake.py when a source is registered.
It is never recreated. It is updated in place as state changes.

---

## Manifest Location

Every ingested source receives a container at:
/mnt/projects/cis/ingest/processing/<source_id>/

The manifest lives at:
/mnt/projects/cis/ingest/processing/<source_id>/metadata/manifest.json

---

## Canonical Fields

### Identity
- schema_version     string, required, immutable — schema version, currently "2"
- source_id          string, required, system-assigned UUID at intake
- source_name        string, required, human-readable filename or title
- source_path        string, required, absolute path to original file
- source_type        string, required — one of: pdf, image, video, audio, note
- source_origin      string, required — one of: archive, external, session,
                     generated
- checksum           string, required, immutable — SHA-256 hash of source file
                     format: sha256:<64 hex characters>
                     computed at intake, never recomputed

### Project Context
- project_id         string, optional — links source to a CIS project
- project_title      string, optional — human-readable project name
- domain             string, optional — LIFE or CREATION
- subdomain          string, optional — e.g. Word, Image, Action, Sound, Web,
                                         Home, Body, Mind

### Processing Control
- processing_profile  string, required — one of: document_text,
                       document_multimodal, reference_image, tutorial_video,
                       audio_lesson, idea_note
                       mutability rule: may only be changed by user when
                       intake_state is arrived or classified; changing after
                       preprocessed requires reset of intake_state to arrived

- processing_plan     object, required — defines extraction steps and model
                       selection for this source
                       required structure:
                         steps  array of strings, required — ordered list of
                                pipeline stages to execute; allowed values:
                                classify, preprocess, extract, normalize, review
                         model  string or null — model identifier to use for
                                extraction; null means use system default
                         notes  string or null — optional human notes on
                                processing intent
                       mutability rule: same as processing_profile — changes
                       after preprocessed require reset to arrived

- priority            string, optional — one of: normal, high, urgent

### Runtime State
- intake_state       string, required — current pipeline state
                     see State Machine section for allowed values
- intake_timestamp   string, required, immutable — ISO 8601 datetime at intake
- last_updated       string, required — ISO 8601 datetime of last state change
- error_state        object, required — structured error tracking
                     fields:
                       has_error     boolean, required
                       error_code    string or null
                       error_message string or null
                       timestamp     ISO 8601 or null
                     rule: if intake_state is failed, has_error must be true
                     rule: if has_error is true, error_code and error_message
                           must be populated

### Lineage
- manifest_version   integer, required — increments on every mutable update,
                     starts at 1, never decreases
- derived_records    array, required, default [] — list of knowledge_record IDs
                     produced from this source; empty array when no records
                     have been produced yet; append-only after creation

---

## Mutability Matrix

| Field               | Mutability                   | Notes                                        |
|---------------------|------------------------------|----------------------------------------------|
| schema_version      | immutable                    | fixed at "2" for this contract version       |
| source_id           | immutable                    | assigned once at intake                      |
| source_name         | immutable                    | original filename preserved                  |
| source_path         | immutable                    | original path preserved                      |
| source_type         | immutable                    | determined at intake                         |
| source_origin       | immutable                    | determined at intake                         |
| checksum            | immutable                    | integrity anchor, never recomputed           |
| intake_timestamp    | immutable                    | set once at intake                           |
| manifest_version    | controlled — increment only  | must increase on every mutable update        |
| intake_state        | controlled — state machine   | follows transition rules only                |
| last_updated        | mutable                      | updated on every state change                |
| error_state         | controlled — system only     | set and cleared by pipeline only             |
| derived_records     | append only                  | records added, never removed                 |
| project_id          | user-authoritative           | user corrections override system             |
| project_title       | user-authoritative           | user corrections override system             |
| domain              | user-authoritative           | user corrections override system             |
| subdomain           | user-authoritative           | user corrections override system             |
| processing_profile  | user-authoritative           | changes after preprocessed require           |
|                     | with state constraint        | reset of intake_state to arrived             |
| processing_plan     | user-authoritative           | same constraint as processing_profile        |
|                     | with state constraint        | changes after preprocessed require           |
|                     |                              | reset of intake_state to arrived             |
| priority            | user-authoritative           | user corrections override system             |

---

## State Machine

### Valid states
- arrived
- classified
- preprocessed
- extracted
- normalized
- reviewed
- approved
- archived
- failed

### Transition table

| From         | To           | Condition                                                     |
|--------------|--------------|---------------------------------------------------------------|
| arrived      | classified   | source type and profile confirmed                             |
| classified   | preprocessed | preprocessing complete                                        |
| preprocessed | extracted    | model extraction complete                                     |
| extracted    | normalized   | normalization complete                                        |
| normalized   | reviewed     | draft knowledge record written                                |
| reviewed     | approved     | human validation passed                                       |
| approved     | archived     | retention policy triggered                                    |
| any          | failed       | pipeline error encountered                                    |
| failed       | arrived      | human override — reset existing manifest to arrived;          |
|              |              | do not recreate manifest                                      |

### Enforcement rules
- State may only advance via the transition table above
- State may not skip steps
- State may not move backward except via the failed → arrived human override
- Transition to failed must populate error_state.has_error = true
- intake_state = failed does not delete the manifest
- Manifest is never recreated on retry — the existing manifest is reset
  to arrived state

---

## Deduplication Rule

At intake, cis_intake.py must:
1. Compute SHA-256 checksum of the incoming source file
2. Compare against checksums of all existing manifests
3. If a match is found: reject the source and log the duplicate;
   do not create a new manifest
4. If no match is found: create the manifest and record the checksum

A duplicate is defined as: identical checksum, regardless of filename or path.

---

## Lineage — Relationship to Downstream Objects

Cardinality: one source manifest produces zero or many knowledge_record objects.
Zero is valid — a manifest with no derived records represents a source that
has been ingested but not yet extracted, or was rejected before extraction.

Rules:
- Each knowledge_record must carry the source_id of its parent manifest
- knowledge_record objects may not exist without a parent manifest
- The manifest is the lineage anchor — it is never deleted while derived
  records exist
- derived_records is required and defaults to []; it is append-only after
  creation — records are added as extraction produces them, never removed

---

## What the Manifest Is Not

- It is not a knowledge record
- It is not a processing log (logs live in /metadata/logs/)
- It is not a schema for knowledge output
- It is not modified by extraction or normalization content —
  only intake_state, last_updated, error_state, manifest_version,
  and derived_records change after creation

---

## Schema File

The JSON schema for manifest.json lives at:
/mnt/projects/cis/runtime/schemas/source_manifest_v2.json

The contract (this file) is the authoritative specification.
The schema file is the machine-readable implementation of this contract.
If they conflict, this contract governs.

---

## Contract Status

Draft v1:   2026-04-26 — Claude (builder)
Draft v2:   2026-04-26 — updated after Layer 3 audit pass 1 (FAIL)
            Changes: checksum, schema_version, error_state, mutability matrix,
            state transition table, deduplication rule, lineage cardinality
Draft v2.1: 2026-04-26 — updated after Layer 3 audit pass 2 (FAIL)
            Changes: processing_plan structure defined, processing_profile and
            processing_plan mutability constraints added, processing_plan added
            to mutability matrix, failed→arrived condition clarified, lineage
            cardinality corrected to zero-or-many, derived_records made required
            with default []
Author: Claude (builder) — requires Layer 3 audit by separate frontier model
Verification: pending cis_verify.py pass
