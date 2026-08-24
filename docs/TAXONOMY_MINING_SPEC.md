# TAXONOMY MINING SPEC v1.1 — Unified Intent & Concept Extraction
**Author:** Hermes (Prime) — 2026-07-23
**Review:** Claude Fable 5 + ChatGPT adversarial review × 2 rounds
**Status:** Directionally approved. Pass 0 authorized. Full implementation gated on Eric Gate 1.
**Previous:** v1.0 (superseded)

---

## 0. GOVERNING RESTATEMENT OF PURPOSE

The miner's goal is **not** to determine which messages express Eric's intent. Its goal is:

> Create a high-recall, context-preserving evidence index that allows Fable to reconstruct Eric's intent without rereading the unorganized archive. The miner organizes and annotates; it never decides what matters.

Three non-negotiable rules:

1. **No invisible discard path.** Every human message ends in exactly one of three states:
   - (a) assigned to ≥1 candidate concept
   - (b) placed in the unresolved/novelty queue
   - (c) excluded as confirmed technical noise — with exclusion counts and reasons logged
2. **Annotations never filter.** Thesaurus tags, stance labels, and cluster membership are metadata. Absence of a tag never removes a message from eligible evidence.
3. **Agent statements are never attributed to Eric.** Provenance of every claim (user vs. agent) is preserved end to end.

---

## 1. SCOPE CONTROL

The pipeline must not become a multi-week infrastructure project.

**Chat Corpus MVP** — buildable and verifiable in ≤2 working days:
- Pass 0 preflight census
- Evidence-unit extraction (5 SQLite sources)
- Lexical annotation + Tier 1 stance tags
- Embedding-based concept linking
- Duplicate grouping (exact + near-duplicate)
- Companion queues and manifests

**Drive Index Phase** — separate from Chat Corpus MVP, not on the critical path:
- Full file inventory during preflight (immediate)
- Known high-value documents processed first
- Text-native extraction in bounded batches
- Failure manifest for unsupported/malformed files
- Full indexing only after chat corpus miner is verified
- Drive processing does not block the first Fable reconstruction unless the census proves relevant ideas primarily live in Drive files

**Deferred to v1.1** (do not build now):
- Contradiction auto-detection
- Full stance classifier beyond the two-tier scheme (§6)
- Drive OCR / visual processing
- Any UI

**Timebox:** each phase that overruns 2× its estimate → stop and report rather than expand.

---

## 2. PASS 0 — PREFLIGHT CORPUS CENSUS

Pass 0 is a **lightweight preflight implementation**, permitted to:
- Read the databases
- Assemble provisional evidence units
- Estimate segmentation (natural language vs. terminal)
- Hash normalized messages for exact-duplicate counting
- Sample near-duplicate rates (not production-grade detection)
- Inventory Drive formats
- Extract a representative Drive sample (not full extraction)

### Census Report Contents

`pass0_census.json` + human-readable summary:

| Metric | Type | Source |
|--------|------|--------|
| Message counts per source, per profile, per month | Exact | DB queries |
| Estimated tokens per source (natural language + terminal/code split) | Sample-based estimate | Provisional parse |
| Evidence-unit token estimate with truncated agent context | Sample-based estimate | §3 rules applied to sample |
| Exact-duplicate rate | Exact | Hash comparison |
| Near-duplicate rate | Sample estimate | Representative sessions |
| Drive file counts by type | Exact | File scan |
| Extractable vs. visual-only percentages | Exact | Extension + header check |
| Largest sessions/documents | Exact | DB queries |
| Message-length distribution | Exact | DB queries |
| Per-tag match counts from lexical annotation | N/A | **Not available until Step 4** — report after annotation, not in initial census |
| Complete Fable Job 1 token-bundle estimate | Calculated | Sum of evidence units + Pass 1 + Eric-voice + instructions + output headroom |

### Census Decision Gate

The Path A/B decision uses a **context-budget calculation**, not a fixed 900K-token threshold:

1. Determine the **verified usable input window** for Fable 5 (published context window minus instruction/system overhead)
2. Calculate the **complete Job 1 bundle size**: evidence units + Pass 1 structural + Eric-voice doc + supporting documents + output headroom
3. **Path A** is permitted only when the Job 1 bundle ≤ **60–70% of verified usable input capacity**
4. Report the threshold, the bundle size, and the percentage. **Eric approves the path.**

| Path | Condition | Action |
|------|-----------|--------|
| **Path A (direct)** | Bundle ≤ approved % of input capacity | Ship full chronological annotated evidence archive to Fable Job 1 |
| **Path B (dossier map-reduce)** | Bundle exceeds threshold | Build concept dossiers per §10; send dossiers + queues + samples |

---

## 3. EVIDENCE UNITS

Normalize all five SQLite sources into one schema:

```json
{
  "unit_id": "prime_s123_t045",
  "source": "hermes_prime",
  "session_id": "123",
  "session_title": "...",
  "timestamp": "2026-06-18T16:42:00",
  "user_text": "...",
  "preceding_agent_context": "...",
  "following_user_resolution": "...",
  "content_segments": {
    "natural_language": "...",
    "terminal_output": "...",
    "code_or_config": "..."
  },
  "file_references": [],
  "original_message_ids": [],
  "hash": "...",
  "near_duplicate_group": null,
  "annotations": {
    "lexical_tags": [],
    "stance": null,
    "stance_target": null,
    "stance_target_id": null,
    "stance_evidence_span": null,
    "stance_confidence": null
  }
}
```

### Preceding Agent Context Rules

**Bounded representation** — the tail-only approach is insufficient. For each agent turn preceding a user message:

- **First 100–150 tokens** — the agent's opening claim or framing
- **Last 250–300 tokens** — the agent's conclusion or final statement
- **Any segment explicitly quoted or referenced** by the user in the following turn (when detectable)
- **Full preceding-turn message ID** — for retrieval

The combined context is capped at ~400 tokens total. Full agent turns remain retrievable by message ID.

### Additional Rules

- **following_user_resolution** only populated when a correction/approval follows within the same session.
- **Terminal output is segmented, not deleted** — some of it is implementation evidence.
- Eric's words remain the authority; agent text exists only to make corrections/approvals interpretable.
- Agent context is **never included in concept embeddings** (§7) — it serves only as interpretive context for human review.

**Sources unified:**
| # | Source | DB Path |
|---|--------|---------|
| 1 | CIS spine | `/mnt/projects/cis/data/cis_memory.db` |
| 2 | Prime (v4pro) | `~/.hermes-v4pro/state.db` |
| 3 | R1 | `~/.hermes-r1/state.db` |
| 4 | GLM-Verifier | `~/.hermes-glm-verifier/state.db` |
| 5 | Qwen | `~/.hermes-qwen/state.db` |

---

## 4. PASS 1 — STRUCTURAL EXTRACTION (unchanged)

Extract existing structured data:

**From WIASW workbook extraction analysis:**
- All 6 WIAS categories with sub-items
- Complete production status/stage list (in workbook order)
- All project goals, mediums, genres, story types
- Software/tool mappings per stage
- Schedule categories and fields
- Checklist and template taxonomies

**From CIS spine:**
- All 15 intentions (verbatim)
- Anti-patterns
- project_decisions, dev_pivot_status, functional_specs entries

**From session databases:**
- Session titles, topics, date ranges, message counts per role

**Output:** `pass1_structural.json`

---

## 5. PASS 2 — LEXICAL CANDIDATE ANNOTATION

Thesaurus-based tagging with the following constraints:

- **Annotates only; never gates forwarding.** Untagged messages still proceed to Fable.
- **Overly broad terms demoted** to low-weight tags: "project", "build", "system", "make", "show me", "I need", "I want", "use", "work", "thing"
- **Expanded thesaurus categories** include creative domains (t-shirt, book, song, animation, comic, dream, design, etc.), project definitions, workflow design, UI design, governance/trust, knowledge/memory

Output: `pass2_annotations.jsonl` — one line per message with matched categories and weights.

---

## 6. STANCE / AUTHORITY TAGS

Two-tier system. Stance detection operates **only on the user-authored natural-language segment**, excluding quoted material, pasted transcripts, terminal output, code, configuration, and agent context.

Every stance label includes:
- `stance_target` — what proposition or message the stance applies to (e.g., "preceding_agent_context", "concept:swa_rebuild", "agent_proposal:message_456")
- `stance_target_id` — the message ID or concept identifier
- `stance_evidence_span` — the exact text span triggering the classification
- `stance_confidence` — 0.0–1.0

Example:
```json
{
  "stance": "user-rejected",
  "stance_target": "preceding_agent_context",
  "stance_target_id": "message_456",
  "stance_evidence_span": "that's not what I meant",
  "stance_confidence": 0.98
}
```

### Tier 1 — Deterministic, trusted
High-precision surface patterns only. Conservative — when in doubt, no tag. Target ≥95% precision.

| Pattern | Label |
|---------|-------|
| "no,", "stop", "don't", "that's not what I meant", "you misunderstood" | user-rejected |
| "yes exactly", "that's right", "correct", "good", "perfect" | user-approved |
| "approved", "do it", "go ahead", "proceed", "implement" | user-approved |
| "maybe", "I think", "what if", "consider", "how about" | tentative |
| "that worked", "it works", "confirmed", "verified" | tested |

### Tier 2 — Local Qwen advisory
Local Qwen3-VL-30B on 4090 assigns labels with confidence. Labels are **advisory** — Fable may override.

Label set: `user-proposed`, `agent-proposed`, `user-approved`, `user-rejected`, `user-corrected`, `tentative`, `implemented`, `tested`, `proven`, `failed`, `superseded`, `unresolved`, `example-only`

---

## 7. PASS 3 — HYBRID CONCEPT LINKING

### Primary Embeddings

**Primary concept embeddings are generated from user-authored natural-language content only.** Agent context must be embedded separately or used only for contextual reranking. A long agent proposal must not dominate the vector and cause the miner to attribute the agent's architecture to Eric.

Agent context → separate contextual embedding OR used during reranking only.

**Embedding model:** Local sentence-transformers or Qwen embedding model on the 4090 — zero API cost.

### Supplementary Signals (union, not intersection)
- Exact-term / alias / acronym matching
- FTS5 full-text retrieval
- Time and session proximity
- Shared file / screen / table / card / project references
- Explicit rename statements: "now called", "used to be", "became", "part of", "replaced by", "not the same as"

N-grams demoted to supporting metadata.

### Verification Controls

**Positive control:** The chain WIAS → WIASW → "creative workflow system" → "PM layer of CIS" must link.

**Negative controls** (false-merge prevention):
- WIASW must not automatically merge with SWA
- A creative project idea must not merge with the infrastructure used to manage it
- Container enforcement must not merge with the entire CIS product
- Agent-generated proposals must not become user-origin concepts merely because Eric discussed them extensively

Report negative-control results in verification.

---

## 8. DUPLICATE GROUPING

Two distinct operations:

1. **Source preservation:** Never delete or merge originals. Every occurrence stays addressable. Frequency remains visible.
2. **Model-input compression:**
   - Exact duplicates → one representative + occurrence count + first/last dates + source list
   - Near-duplicates → grouped the same way
   - Meaningfully different revisions/corrections → stay separate

Fable can retrieve any full occurrence list on demand through the retrieval mechanism (§8a).

### 8a. Retrieval Mechanism

"Retrievable on demand" requires an actual mechanism. One of the following must be specified before implementation:

**Chosen approach:** Hermes provides a `retrieval_index.db` (SQLite) mapping message IDs to full content, plus a `fable_job1_bundle_manifest.json` that states:
- What Fable receives directly in the bundle
- What remains retrievable by message ID
- How to request retrieval (Fable lists IDs → Hermes returns supplemental evidence bundle in a follow-up call)

The manifest explicitly distinguishes "included" from "retrievable."

---

## 9. DRIVE CORPUS

Staged, local, zero API cost. **Separate from Chat Corpus MVP — does not block first Fable Job 1.**

### Preflight (during Pass 0)
- Full file inventory: count, types, extensions
- Extractable vs. visual-only split
- Representative sample extraction (10–20 files across types) for token estimation

### Phase 1 — High-Value Documents (can run parallel to chat corpus)
- Known important files: WIASW workbook, creative pipeline doc, parking lot, app concepts, Eric-voice sources
- Text-native extraction: `.md` / `.txt` full, `.docx` paragraphs+headings+tables, `.xlsx`/`.xlsb` sheet names+tables, `.pdf` text+page refs

### Phase 2 — Batched Indexing (after chat corpus verified)
- Remaining text-native files in bounded batches
- Searchable content index: FTS + embeddings over extracted text
- Failure manifest for unsupported/malformed files
- Relevance ranking: filename + headings + content + embeddings + dates + duplicate hashes

### Visual Files
- `VISUAL_FILES_REQUIRING_REVIEW.json` manifest — never silently excluded

Nothing near 5.8GB goes to any model. The index makes retrieval targeted.

---

## 10. CONCEPT DOSSIERS (Path B only)

One dossier per candidate concept:
- Working name; aliases
- The problem it answers
- Earliest/latest evidence
- Representative **verbatim** excerpts (quotes, never paraphrase)
- Corrections and rejections
- Chronological evolution
- Related/competing/merged/replaced concepts
- Implementation or proof evidence
- Apparent current status
- Contradictions (candidate only — not validated)
- Confidence
- Full source references

### Mandatory Companion Outputs (regardless of path)

- `UNCLUSTERED_NOVELTY_QUEUE.json`
- `CONTRADICTION_CANDIDATES.json` — populated only from: explicit contradiction language, different stance labels on same concept, manual flags, Fable Job 1 findings. **Not validated contradictions — candidate status until reviewed.**
- `REJECTED_MODEL_IDEAS.json` — candidate queue until attribution and stance are verified
- `UNRESOLVED_REFERENCES.json`
- `VISUAL_FILES_REQUIRING_REVIEW.json`
- `EXCLUSION_LOG.json` — counts + reasons for all noise-excluded content

---

## 11. MAP-STAGE MODEL TIERING

**Decided by test, not assumption.**

Priority order: deterministic extraction + embeddings → **local Qwen map pass** → cheap API model (Haiku/Sonnet) only for chunks where local confidence is low → Fable for cross-corpus work only.

**Gate:** Before spending any API credit, run local Qwen on one representative month and score:
- Recall, quote fidelity, alias recognition, stance recognition, false merges, false omissions

**Eric reviews the scorecard and approves the tiering.**

---

## 12. FABLE USAGE — THREE SEPARATE JOBS

### Job 1 — Reconstruction (archivist role)
**Inputs:** Path A archive OR Path B dossiers + queues + Pass 1 structural + Eric-voice doc + `fable_job1_bundle_manifest.json` + `retrieval_index.db`

**Outputs:**
- `CONCEPT_INVENTORY.md`
- `ALIAS_LEXICON.md`
- `CONCEPT_LINEAGE.md`
- `DECISIONS_AND_REJECTIONS.md`
- `UNCERTAINTIES.md`

**Rule:** Recommendations explicitly prohibited. Concept inventory built **without** forcing concepts into WIASW categories.

### Job 2 — Adversarial Audit
**Inputs:** Job 1 outputs + novelty queue + stratified raw-session sample + Eric-selected recall-test concepts + contradiction candidate file + negative-control test results (§7)

**Questions:** Missed concepts? False merges? Agent-suggestions misattributed? Overstated certainty? Contradicting evidence?

### Job 3 — Evaluation and Recommendation
**Only after Jobs 1–2 are stable and Eric has reviewed.**

**Outputs:**
- `TAXONOMY_UNIFIED.md`
- `WHAT_YOU_WERE_BUILDING.md`
- `TRAJECTORY_ASSESSMENT.md`
- `RECOMMENDED_SYSTEM_BOUNDARY.md`
- `PRIORITIZED_NEXT_WORK.md`

### Card Gate
Fable may list candidate card subjects in Job 3. **No card generation and no `cards/inbox/` admission until Eric approves the reviewed taxonomy and selects which concepts become active work.**

---

## 13. BUDGET AND PRICING VERIFICATION

- **Verify current published Fable 5 pricing, prompt-cache discount, and batch discount before locking budget math.** Working assumptions ($10/M in, $50/M out, 10× cache read discount, 50% batch) must be confirmed.
- Test prompt-cache behavior (identical-prefix requirement, TTL) on a small corpus before relying on it for the full run.
- Allocation ceilings:

| Job | Budget |
|-----|--------|
| Job 1 | $15–25 |
| Job 2 | $10–15 |
| Job 3 | $15–25 |
| Post-review follow-up reserve | $35–60 |

- **Do not plan to spend the full $100 in the first run.**

---

## 14. VERIFICATION

1. **Recall check:** 5 known ideas must appear in evidence index
2. **Noise check:** Random-sample 20 messages — verify actual intent, not log noise
3. **Evolution check (positive):** WIAS → WIASW → "creative workflow system" → "PM layer of CIS" must link
4. **Gap check:** WIASW workbook taxonomy complete in Pass 1
5. **Profile coverage:** All 4 Hermes profiles + CIS spine in source manifest with correct counts
6. **Exclusion accounting:** Total = assigned + queued + excluded. Excluded items sampled and justified.
7. **Census reconciliation:** Evidence-unit token totals match Pass 0 within 10%.
8. **Stance precision spot-check:** Sample 20 Tier 1 stance tags; target ≥95% precision.
9. **Drive recall check:** 3 known Drive documents with vague filenames; content index surfaces them.
10. **Context-cap check:** Sample 20 evidence units; agent context present, capped, sufficient to interpret.
11. **False-merge controls (§7 negative controls):** WIASW ≠ SWA, creative ideas ≠ infrastructure, agent proposals ≠ user intent. Report results.
12. **Stance target check:** Sample 10 stance labels; verify each identifies what proposition the stance applies to.

---

## 15. EXECUTION ORDER

| Step | Description | Approval Gate |
|------|-------------|---------------|
| 1 | Pass 0 preflight census → report + Path A/B recommendation | **Eric Gate 1** |
| — | **STOP. No implementation beyond Pass 0 until approved.** | — |
| 2 | Evidence-unit extraction (all 5 sources) + noise segmentation | — |
| 3 | Pass 1 structural (parallel with step 2) | — |
| 4 | Lexical annotation + Tier 1 stance tags | — |
| 5 | Embedding index + hybrid linking + duplicate grouping | — |
| 6 | Drive Phase 1 (high-value documents) — parallel, non-blocking | — |
| 7 | Local Qwen map test (one month) → scorecard → tiering decision | **Eric Gate 2** |
| 8 | Path A: chronological archive / Path B: dossiers + queues | — |
| 9 | Verification checks 1–12 → report | **Eric Gate 3** |
| 10 | Fable Job 1 → Eric review → Job 2 → Eric review → Job 3 → Eric review → card approval | — |

---

## 16. DO-NOT-ALLOW LIST

- ❌ Untagged or unclassified messages disappearing
- ❌ Agent suggestions attributed to Eric
- ❌ WIASW categories constraining initial concept discovery
- ❌ Duplicate compression erasing frequency or provenance
- ❌ Agent context included in concept embeddings
- ❌ Fable recommending architecture during Job 1
- ❌ Card generation before reviewed-taxonomy approval
- ❌ Miner scope expanding beyond §1 MVP without explicit Eric decision
- ❌ Drive indexing blocking chat corpus delivery
- ❌ Stance labels without targets

---

## 17. OUTPUT MANIFEST

```
data/taxonomy_mine/
├── pass0_census.json              # Exact + estimated measurements, clearly distinguished
├── pass1_structural.json          # WIASW taxonomy, intentions, decisions
├── evidence_units/
│   └── all_units.jsonl            # Unified evidence units (all 5 sources)
├── pass2_annotations.jsonl        # Lexical tags + stance labels with targets
├── pass3_links.json               # Hybrid concept links
├── pass3_negative_controls.json   # False-merge test results
├── duplicates.json                # Duplicate groups with provenance
├── concept_dossiers/              # One dossier per concept (Path B only)
├── UNCLUSTERED_NOVELTY_QUEUE.json
├── CONTRADICTION_CANDIDATES.json  # Candidate only — not validated
├── REJECTED_MODEL_IDEAS.json      # Candidate queue — unverified
├── UNRESOLVED_REFERENCES.json
├── VISUAL_FILES_REQUIRING_REVIEW.json
├── EXCLUSION_LOG.json
├── fable_job1_bundle_manifest.json  # Included vs. retrievable
├── retrieval_index.db               # Message ID → full content lookup
├── drive_index/
│   ├── file_manifest.json
│   ├── high_value_extracted/        # Phase 1 only — known important docs
│   ├── extracted_content/           # Phase 2 — batched
│   ├── content_index.db
│   ├── failure_manifest.json        # Unsupported/malformed files
│   └── relevance_ranked.json
└── source_manifest.json
```

---

**Authorization:** Pass 0 preflight census only. Stop at Eric Gate 1. Return exact vs. estimated measurements, Job 1 bundle estimate, Path recommendation, Drive boundary. No implementation beyond provisional parsers.
