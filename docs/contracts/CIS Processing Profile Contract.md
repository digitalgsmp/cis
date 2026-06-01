# CIS Processing Profile Contract v1.1
# Path: /mnt/projects/cis/docs/contracts/CIS Processing Profile Contract.md
# Status: DRAFT — awaiting verification
# ADR reference: ADR-007, ADR-037

---

## Purpose

The processing profile is the routing specification that determines how a
source is processed through the CIS pipeline. It is assigned at intake as
a safe default and confirmed or updated at classification. It governs which
pipeline stages run, which extraction path is used, and which model handles
extraction.

The processing profile is a control value, not a knowledge object.
It does not describe content — it describes how content will be handled.

---

## When a Profile Is Assigned

Profile assignment happens in two steps:

Step 1 — Intake (cis_intake.py):
cis_intake.py assigns an initial safe default profile based on source_type
at the moment the manifest is created. This ensures processing_plan can be
derived immediately and the manifest is never created without a valid profile.

Step 2 — Classification (cis_classify.py):
cis_classify.py confirms the initial profile or updates it based on deeper
inspection of the source. Classification may change the profile while
intake_state is arrived or classified.

If the operator has manually set a profile before classification runs,
the classifier must respect that assignment and not overwrite it.

---

## Allowed Profile Values

Exactly six profiles are defined for this contract version.
No profile outside this list is valid.

### document_text
Source is a text-dominant document (PDF, plain text, markdown).
Extraction path: text
Stages: classify → preprocess → extract → normalize → review
Model: primary text model or system default
Use for: manuals, articles, session transcripts, notes, scripts

### document_multimodal
Source is a document containing both text and significant visual content.
Extraction path: hybrid
Stages: classify → preprocess → extract → normalize → review
Model: multimodal model required (Qwen2.5-VL-32B-Instruct-4bit or equivalent)
Use for: comic pages, illustrated references, annotated diagrams,
         mixed-media PDFs

### reference_image
Source is a standalone image intended as reference material.
Extraction path: vision
Stages: classify → preprocess → extract → normalize → review
Model: multimodal model required
Use for: archive images, stills, reference photographs, illustrations

### tutorial_video
Source is a video containing instructional content.
Extraction path: hybrid (transcript + frame sampling)
Stages: classify → preprocess → extract → normalize → review
Model: multimodal model required; transcript model for audio track
Use for: tutorial recordings, walkthroughs, process documentation videos

### audio_lesson
Source is an audio file containing spoken content.
Extraction path: text (via transcript)
Stages: classify → preprocess → extract → normalize → review
Model: transcript model required; text model for extraction
Use for: recorded lessons, interviews, voice notes, podcasts

### idea_note
Source is a short unstructured human note or fragment.
Extraction path: text
Stages: classify → preprocess → extract → normalize → review
Note: the preprocess stage runs but is a no-op for idea_note sources —
      no preprocessing artifacts are produced; the state transition
      classified → preprocessed still occurs to maintain state machine
      integrity per ADR-037
Model: text model or system default
Use for: quick captures, idea fragments, session notes, voice-to-text dumps

---

## Profile Selection Rules

Step 1 — cis_intake.py safe default assignment (at intake):
1. If source_type is note, assign idea_note
2. If source_type is audio, assign audio_lesson
3. If source_type is video, assign tutorial_video
4. If source_type is image, assign reference_image
5. If source_type is pdf, assign document_text as safe default
6. If source_type is unknown, assign document_text as safe default
   and flag for human review

Step 2 — cis_classify.py confirmation or update (at classification):
1. If operator has manually assigned a profile, use it. Do not overwrite.
2. If source_type is note, confirm idea_note
3. If source_type is audio, confirm audio_lesson
4. If source_type is video, confirm tutorial_video
5. If source_type is image, confirm reference_image
6. If source_type is pdf:
   - if the document contains embedded images covering more than 30%
     of pages, update to document_multimodal
   - otherwise confirm document_text
7. If source_type is unknown, confirm document_text and retain
   human review flag

---

## Profile Mutability Rules

Processing profile may be changed by the human operator or by
cis_classify.py when intake_state is arrived or classified.

If processing_profile is changed after intake_state has advanced to
preprocessed or later:
- intake_state must be reset to arrived
- all derived artifacts produced at or after the preprocess stage must
  be cleared before reprocessing begins; this includes preprocessing
  artifacts, extraction outputs, normalization outputs, and review outputs
- immutable manifest fields and intake-stage data are never cleared
- this rule applies regardless of which stage the change occurs at

The pipeline may not change the profile during execution.

---

## Relationship to processing_plan

The processing_profile determines the extraction path and stage sequence.
The processing_plan (defined in the Source Manifest Contract v2.1) holds
the specific execution steps and model assignment for a given source.

Relationship:
- processing_profile is the template — it defines what is generally required
- processing_plan is the instance — it records what will actually run for
  this specific source

When cis_intake.py creates the manifest, it must derive an initial
processing_plan from the safe default profile assigned at intake.
When cis_classify.py confirms or updates the profile, it must update
the processing_plan to match the confirmed profile before advancing
intake_state to classified.

---

## Extraction Paths

Three extraction paths are defined. Each profile maps to exactly one path.

### text path
Runs: OCR or text extraction only
Produces: extracted text per source unit
Used by: document_text, audio_lesson (via transcript), idea_note

### vision path
Runs: visual model pass only
Produces: scene description, layout description per source unit
Used by: reference_image

### hybrid path
Runs: text extraction pass AND visual model pass; outputs merged
Produces: extracted text + scene description + layout description per unit
Used by: document_multimodal, tutorial_video

---

## What the Processing Profile Is Not

- It is not a knowledge record
- It is not a model configuration file
- It is not a pipeline log
- It does not describe the content of the source
- It does not change based on what extraction finds

---

## Schema File

The allowed profile values and profile selection rules must be reflected in:
/mnt/projects/cis/runtime/schemas/processing_profile_v1.json

The contract (this file) is the authoritative specification.
If the schema file and this contract conflict, this contract governs.

---

## Contract Status

Draft v1:   2026-04-26 — Claude (builder)
Draft v1.1: 2026-04-26 — updated after Layer 3 audit pass 1 (FAIL)
            Changes: removed invalid source_type "document" from selection
            rules (replaced with "pdf"); split profile assignment into two
            steps — intake safe default and classification confirmation;
            idea_note preprocess changed from skipped to no-op to maintain
            state machine integrity; artifact clearing rule expanded to cover
            all derived artifacts at or after preprocess, not preprocessing
            artifacts only
Author: Claude (builder) — requires Layer 3 audit by separate frontier model
Verification: pending cis_verify.py pass
