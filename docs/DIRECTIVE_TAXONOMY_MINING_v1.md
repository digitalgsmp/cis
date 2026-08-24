# DIRECTIVE — TAXONOMY_MINING_SPEC revision v0.5 → v1.0
**From:** Eric (consolidating Claude Fable 5 + ChatGPT adversarial reviews)
**To:** Hermes (Prime)
**Status:** BINDING. Revise the spec to satisfy every item below, return v1.0 for approval before implementation.

---

## 0. GOVERNING RESTATEMENT OF PURPOSE

Replace the spec's implicit goal ("determine which messages express Eric's intent") with:

> Create a high-recall, context-preserving evidence index that allows Fable to reconstruct Eric's intent without rereading the unorganized archive. The miner organizes and annotates; it never decides what matters.

Corollary rules, non-negotiable:
1. **No invisible discard path.** Every human message ends in exactly one of three states: (a) assigned to ≥1 candidate concept, (b) placed in the unresolved/novelty queue, (c) excluded as confirmed technical noise — with exclusion counts and reasons logged.
2. **Annotations never filter.** Thesaurus tags, stance labels, and cluster membership are metadata. Absence of a tag never removes a message from eligible evidence.
3. **Agent statements are never attributed to Eric.** Provenance of every claim (user vs. agent) is preserved end to end.

---

## 1. SCOPE CONTROL (new — highest execution risk)

The revised pipeline must not become a multi-week infrastructure project.

- Define an **MVP miner** buildable and verifiable in ≤ 2 working days: Pass 0 census, evidence-unit extraction, lexical annotation, embedding clustering, duplicate grouping, queues, manifests.
- **Defer to v1.1** (do not build now): contradiction auto-detection, full stance classifier beyond the two-tier scheme in §6, Drive OCR/visual processing, any UI.
- Timebox each phase. If a phase overruns 2x its estimate, stop and report rather than expand.

---

## 2. PASS 0 — CORPUS AND TOKEN CENSUS (new, blocks everything)

Before any other implementation, produce `pass0_census.json` + human-readable summary:

- Message counts and **estimated tokens** per source, per profile, per month
- Token split: natural language vs. terminal/log/code content per source
- Evidence-unit token estimate **including truncated agent context** (per §3 cap)
- Exact-duplicate and near-duplicate rates
- Drive corpus: file counts by type, extractable vs. visual-only percentages, extracted-character estimates for text-native formats
- Largest sessions/documents; message-length distribution

### Census decision gate
- **Path A (direct):** if total evidence-unit tokens ≤ ~900K → skip dossier construction; ship the full chronological, annotated evidence archive to Fable Job 1 directly.
- **Path B (dossier map-reduce):** if > ~900K → build concept dossiers per §7 and send dossiers + queues + samples.
- Report the numbers and the recommended path; Eric approves the path before Phase B work begins.

---

## 3. EVIDENCE UNITS (replaces human-message-only extraction)

Normalize all five SQLite sources into one schema:

```json
{
  "unit_id": "prime_s123_t045",
  "source": "hermes_prime",
  "session_id": "123",
  "session_title": "...",
  "timestamp": "2026-06-18T16:42:00",
  "user_text": "...",
  "preceding_agent_context": "...",   // TAIL of prior agent turn, HARD CAP ~400 tokens
  "following_user_resolution": "...", // only when a correction/approval follows within same session
  "content_segments": {"natural_language": "...", "terminal_output": "...", "code_or_config": "..."},
  "file_references": [],
  "original_message_ids": [],
  "hash": "...",
  "near_duplicate_group": null,
  "annotations": {"lexical_tags": [], "stance": null, "stance_confidence": null}
}
```

Rules:
- Preceding agent context is capped (tail ~400 tokens) to prevent 3–5x census inflation. Full agent turns remain retrievable by message ID.
- Terminal output is **segmented, not deleted** — some of it is implementation evidence.
- Eric's words remain the authority; agent text exists only to make corrections/approvals interpretable.

---

## 4. PASS 1 — STRUCTURAL EXTRACTION (keep as specced)

Unchanged: WIASW workbook taxonomy, CIS intentions, anti-patterns, project_decisions, dev_pivot_status, functional_specs, session metadata, source manifest.

---

## 5. PASS 2 — RENAMED: LEXICAL CANDIDATE ANNOTATION

- Keep the expanded thesaurus, but it **annotates only**; it never gates forwarding.
- Overly broad terms ("project", "build", "system", "make", "show me") are demoted to low-weight tags to limit false-positive noise in downstream ranking.
- Output unchanged in format; add per-tag match counts to the census report.

---

## 6. STANCE / AUTHORITY TAGS (new) — two-tier

**Tier 1 — deterministic, trusted:** high-precision surface patterns only (e.g., "no,", "stop", "that's not what I meant", "yes exactly", "approved", "do it", "don't"). Conservative; when in doubt, no tag.

**Tier 2 — local-model advisory:** Qwen assigns from the label set below with confidence; labels are **advisory** — Fable adjudicates during Job 1/2 and may override.

Label set: user-proposed, agent-proposed, user-approved, user-rejected, user-corrected, tentative, implemented, tested, proven, failed, superseded, unresolved, example-only.

A wrong "user-approved" is worse than no label. Precision over recall for Tier 1; Tier 2 always carries confidence.

---

## 7. PASS 3 — REPLACED: HYBRID CONCEPT LINKING

Primary signal: **local embeddings** (run on the 4090; sentence-transformers or Qwen embedding model — zero API cost).
Supplementary signals, union not intersection:
- Exact-term / alias / acronym matching
- FTS5 or BM25 full-text retrieval
- Time and session proximity
- Shared file / screen / table / card / project references
- Explicit rename statements ("now called", "used to be", "became", "part of", "replaced by", "not the same as")

N-grams demoted to supporting metadata. Success criterion: the WIAS → WIASW → "creative workflow system" → "PM layer of CIS" chain must link (this is verification check #3).

---

## 8. DUPLICATE GROUPING (replaces "no deduplication")

Two distinct operations:
1. **Source preservation:** never delete or merge originals; every occurrence stays addressable; frequency stays visible.
2. **Model-input compression:** exact duplicates → one representative + occurrence count + first/last dates + source list. Near-duplicates grouped the same way. Meaningfully different revisions/corrections stay separate. Fable can retrieve any full occurrence list on demand.

---

## 9. DRIVE CORPUS (replaces filename-only manifest)

Staged, local, zero API cost:
1. Filename/path/date scan (cheap first pass — keep)
2. **Content extraction** for text-native formats: md/txt full; docx paragraphs+headings+tables; xlsx/xlsb sheet names+structured tables; pdf text+page refs
3. Build a **searchable content index** (FTS + embeddings) over extracted text
4. Visual-only / scan / image files → `VISUAL_FILES_REQUIRING_REVIEW.json` manifest, never silently excluded
5. Relevance ranking uses filename + headings + content + embeddings + dates + duplicate hashes

Nothing near 5.8GB goes to any model; the index makes retrieval targeted.

---

## 10. CONCEPT DOSSIERS (Path B only; format applies to map outputs either way)

One dossier per candidate concept: working name; aliases; the problem it answers; earliest/latest evidence; representative **verbatim** excerpts (quotes, never paraphrase); corrections and rejections; chronological evolution; related/competing/merged/replaced concepts; implementation or proof evidence; apparent current status; contradictions; confidence; full source references.

Mandatory companion outputs regardless of path:
- `UNCLUSTERED_NOVELTY_QUEUE`
- `CONTRADICTIONS`
- `REJECTED_MODEL_IDEAS`
- `UNRESOLVED_REFERENCES`
- `VISUAL_FILES_REQUIRING_REVIEW`
- `EXCLUSION_LOG` (counts + reasons for all noise-excluded content)

---

## 11. MAP-STAGE MODEL TIERING (decided by test, not assumption)

Order: deterministic extraction + embeddings → **local Qwen map pass** → cheap API model (Haiku/Sonnet) only for chunks where local confidence is low → Fable for cross-corpus work only.

**Gate:** before spending any API credit on a map model, run local Qwen on one representative month and score: recall, quote fidelity, alias recognition, stance recognition, false merges, false omissions. Eric reviews the scorecard and approves the tiering.

---

## 12. FABLE USAGE — THREE SEPARATE JOBS

**Job 1 — Reconstruction (archivist role).** Inputs: Path A archive or Path B dossiers + queues + Pass 1 structural + Eric-voice doc. Outputs: `CONCEPT_INVENTORY.md`, `ALIAS_LEXICON.md`, `CONCEPT_LINEAGE.md`, `DECISIONS_AND_REJECTIONS.md`, `UNCERTAINTIES.md`. **Recommendations explicitly prohibited in this pass.** Concept inventory is built **without** forcing concepts into WIASW; taxonomy-axis assignment comes after inventory.

**Job 2 — Adversarial audit.** Inputs: Job 1 outputs + novelty queue + stratified raw-session sample + Eric-selected recall-test concepts + contradiction file. Questions: missed concepts, false merges, agent-suggestions misattributed as intent, overstated certainty, contradicting evidence.

**Job 3 — Evaluation and recommendation.** Only after Jobs 1–2 are stable and Eric has reviewed. Outputs: `TAXONOMY_UNIFIED.md`, `WHAT_YOU_WERE_BUILDING.md`, `TRAJECTORY_ASSESSMENT.md`, `RECOMMENDED_SYSTEM_BOUNDARY.md`, `PRIORITIZED_NEXT_WORK.md`.

**Card gate:** Fable may list candidate card subjects in Job 3. No card generation and no `cards/inbox/` admission until Eric approves the reviewed taxonomy and selects which concepts become active work.

---

## 13. BUDGET AND PRICING VERIFICATION

- **Verify current published Fable 5 pricing, prompt-cache discount, and batch discount before locking budget math.** The figures cited in review ($10/M in, $50/M out, 10x cache read discount, 50% batch) are working assumptions, not confirmed facts.
- Test prompt-cache behavior (identical-prefix requirement, TTL) on a small corpus before relying on it for the full run.
- Allocation ceilings: Job 1 $15–25 · Job 2 $10–15 · Job 3 $15–25 · **reserve $35–60 for post-review follow-up.** Do not plan to spend the full $100 in the first run.

---

## 14. VERIFICATION (extends spec Section 9)

Keep all five original checks. Add:
6. **Exclusion accounting:** total messages in = assigned + queued + excluded; excluded items sampled and justified.
7. **Census reconciliation:** evidence-unit token totals match Pass 0 within 10%.
8. **Stance precision spot-check:** sample 20 Tier 1 stance tags; target ≥ 95% precision.
9. **Drive recall check:** pick 3 known Drive documents with vague filenames; verify the content index surfaces them.
10. **Context-cap check:** sample 20 evidence units; confirm agent context is present, capped, and sufficient to interpret the user turn.

---

## 15. EXECUTION ORDER

1. Pass 0 census → report → **Eric approves Path A or B**
2. Evidence-unit extraction (all 5 sources) + noise segmentation
3. Pass 1 structural (parallel with 2)
4. Lexical annotation + Tier 1 stance tags
5. Embedding index + hybrid linking + duplicate grouping
6. Drive content extraction + index + visual queue
7. Local Qwen map test (one month) → scorecard → **Eric approves tiering**
8. Path A: assemble chronological archive / Path B: build dossiers + queues
9. Verification checks 1–10 → report → **Eric approves Fable spend**
10. Fable Job 1 → Eric review → Job 2 → Eric review → Job 3 → Eric review → card approval

Three human approval gates; none may be skipped.

---

## 16. DO-NOT-ALLOW LIST

- Untagged or unclassified messages disappearing
- Agent suggestions attributed to Eric
- WIASW categories constraining initial concept discovery
- Duplicate compression erasing frequency or provenance
- Fable recommending architecture during Job 1
- Card generation before reviewed-taxonomy approval
- Miner scope expanding beyond §1 MVP without an explicit Eric decision
