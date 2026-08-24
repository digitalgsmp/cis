# DIRECTIVE — TAXONOMY_MINING_SPEC v1.0 → v1.1
**From:** Eric (consolidating Claude Fable 5 + ChatGPT round-2 reviews of spec v1.0)
**To:** Hermes (Prime)
**Status:** BINDING. Spec v1.0 is **directionally approved**. Apply amendments A1–A12 below, return v1.1, then execute **Pass 0 preflight only**. Stop at Eric Gate 1. No implementation beyond the preflight and its provisional parsers.

Everything in v1.0 not amended below stands as written, including: governing purpose and three non-negotiable rules (§0), lexical annotation as metadata-only (§5), two-tier stance scheme (§6), hybrid embedding-led linking (§7), non-destructive duplicate grouping (§8), three Fable jobs with the recommendation prohibition in Job 1 (§12), budget ceilings and pricing verification (§13), the three human gates (§15), and the do-not-allow list (§16).

---

## AMENDMENTS

### A1 — Redefine Pass 0 as a lightweight preflight (fixes circular dependency)

Pass 0 as written requires extraction, segmentation, and duplicate machinery that cannot exist "before any other implementation." Redefine Pass 0 as a **preflight implementation** permitted to:

- Read all five databases directly
- Assemble **provisional** evidence units (throwaway parser acceptable)
- Estimate NL vs. terminal/code segmentation via regex heuristics
- Hash normalized messages for exact-duplicate counts
- **Sample** near-duplicate rates (e.g., random 500-message sample), not production-grade detection
- Inventory all Drive files by type/size/date (full inventory — cheap)
- Extract a **representative Drive sample** (e.g., 100–200 files across formats) for character/token estimation and parser-failure-rate measurement

The census report must label every metric as one of: **exact**, **sample-based estimate**, or **unavailable until later processing**. Production-grade duplicate grouping and full Drive extraction are NOT prerequisites for Gate 1.

### A2 — Split Chat Corpus MVP from Drive Index Phase (fixes 2-day timebox conflict)

**Chat Corpus MVP (the ≤2-day scope):** five SQLite sources, known structural files, evidence units, annotation, embeddings, duplicate groups, Path A/B decision, Fable Job 1 readiness.

**Drive Index Phase (separate, after chat miner is verified):**
- Full file inventory happens in preflight (A1)
- Known high-value documents (WIASW workbook analysis, named pipeline docs, parking lots) extracted first
- Text-native extraction proceeds in **bounded batches** with a failure manifest for malformed/unsupported/legacy-format files
- Full 11,762-file indexing only after Gate 3, unless the census shows Eric's ideas live primarily in Drive — in which case report that finding at Gate 1 and Eric re-sequences

Drive processing must not block Fable Job 1. Verification check #9 (Drive recall) moves from Gate 3 to the Drive Index Phase.

### A3 — Rename CONTRADICTIONS → CONTRADICTION_CANDIDATES (fixes §1/§10 inconsistency)

Contradiction auto-detection remains deferred to v1.1 of the miner. For now, `CONTRADICTION_CANDIDATES.json` is populated only from:
- Explicit contradiction language in user text
- Conflicting stance labels attached to the same candidate concept
- Manual flags from Eric
- Fable Job 1 findings (appended after the fact)

Same status applies to `REJECTED_MODEL_IDEAS.json`: it is a **candidate queue** — entries carry evidence span, attribution, confidence, and `unverified` status until Fable Job 2 or Eric review confirms them.

### A4 — Retrieval mechanism: request-and-bundle (decision, not options)

"Retrievable on demand" is implemented as an **iterative bundle workflow**:
1. Every Fable job bundle ships with `fable_jobN_bundle_manifest.json` stating exactly what is included and what remains retrievable by ID
2. Fable is instructed to list needed message/occurrence/file IDs in its `UNCERTAINTIES.md` output
3. Hermes resolves those IDs into a supplemental evidence bundle for the next call

No read-only retrieval tool or live tool-use interface is to be built — that is infrastructure §1 prohibits. A local `retrieval_index.db` (ID → full record) supports Hermes's side of the workflow.

### A5 — Stance targets and segment scoping

Stance detection (both tiers) operates **only on the user-authored natural-language segment**, excluding: pasted transcripts, quoted agent text, terminal output, code/config, and the preceding agent context.

Extend the annotation schema:
```json
{
  "stance": "user-rejected",
  "stance_target": "preceding_agent_context",
  "stance_target_id": "message_456",
  "stance_evidence_span": "that's not what I meant",
  "stance_confidence": 0.98
}
```
A stance label without a target is incomplete; if the target cannot be identified, record `stance_target: "unresolved"` rather than guessing.

### A6 — Replace fixed 900K gate with a context-budget calculation

Path A is permitted only when the **complete Fable Job 1 bundle** — evidence archive + Pass 1 structural + Eric-voice doc + queues + instructions/system prompt — fits within **≤65% of verified usable input capacity**, after reserving output headroom.

"Verified usable" means empirically confirmed against current Fable 5 API limits and cache behavior (§13), not the marketing figure. Pass 0 reports the full bundle estimate, the computed ceiling, and the resulting Path A/B recommendation.

### A7 — Embedding scope: user-authored content only

Primary concept embeddings are generated from the **user-authored natural-language segment only**. Preceding agent context may receive a separate contextual embedding used solely for reranking. Agent proposals must not dominate concept-cluster formation — this is the embedding-level enforcement of §0 rule 3.

### A8 — Bounded agent-context representation: head + tail + quoted spans

Replace the tail-400 cap with:
- First ~100–150 tokens of the preceding agent turn
- Last ~250–300 tokens
- Any span the user directly quotes or references, when detectable by string match
- Full preceding-turn message ID (always)

Total cap unchanged (~400–450 tokens). Rationale: the claim Eric rejected often appears at the start of a long agent answer, not its conclusion.

### A9 — Negative clustering controls (must-not-merge tests)

Add to verification, alongside the positive WIAS-lineage check:
- WIASW and SWA must remain **distinct** concepts
- Creative project ideas must not merge with the infrastructure that manages them
- Container/enforcement must not merge with CIS-as-a-whole
- Agent-proposed architecture must not acquire user-origin attribution through discussion volume alone

Eric supplies 3–5 additional must-not-merge pairs at Gate 1 (he knows which concepts are adjacent but distinct). False-merge failures block Gate 3 the same way recall failures do.

### A10 — Tier 2 model selection is a Gate 2 outcome, not an assumption

Qwen3-VL-30B is the **first candidate** for Tier 2 stance tagging and the local map pass, not the decided model. The one-month scorecard (§11) evaluates it on recall, quote fidelity, alias recognition, stance recognition (with targets per A5), false merges, and false omissions. If it underperforms, the scorecard proposes alternatives (text-tuned local model, or escalation of specific chunk types to a cheap API model). Eric decides at Gate 2.

### A11 — Resolve output-name inconsistencies

- §5 says `pass2_intents.jsonl`; §17 says `pass2_annotations.jsonl`. Canonical name: **`pass2_annotations.jsonl`**. Fix §5.
- Per-tag match counts cannot appear in the initial Pass 0 census (annotation runs at Step 4). Move them to a post-annotation report, or regenerate the census after Step 4 and mark it `census_r2`.
- Update §17 manifest: `CONTRADICTIONS.json` → `CONTRADICTION_CANDIDATES.json`; add `fable_job1_bundle_manifest.json` and `retrieval_index.db`.

### A12 — Revised execution order

| Step | Description | Gate |
|------|-------------|------|
| 0 | Amend spec → v1.1, return for approval | Eric approves v1.1 |
| 1 | **Pass 0 preflight** (per A1): provisional units, sampled estimates, Drive inventory + sample, context-budget calc (A6), Path A/B recommendation, Drive-boundary proposal | **Eric Gate 1** |
| 2 | Evidence-unit extraction, production parser, noise segmentation | — |
| 3 | Pass 1 structural (parallel) | — |
| 4 | Lexical annotation + Tier 1 stance tags (A5 scoping) | — |
| 5 | Embedding index (A7 scope) + hybrid linking + duplicate grouping | — |
| 6 | High-value Drive documents only (per A2) | — |
| 7 | Local model test, one month → scorecard | **Eric Gate 2** (tiering + Tier 2 model) |
| 8 | Path A archive / Path B dossiers + queues + bundle manifest | — |
| 9 | Verification: checks 1–8, 10 + must-not-merge (A9) | **Eric Gate 3** |
| 10 | Fable Job 1 → review → Job 2 → review → Job 3 → review → card approval | per-job review |
| 11 | Drive Index Phase (full), verification check 9 | — |

---

## PASS 0 DELIVERABLES (due at Gate 1)

1. Census with every metric labeled exact / estimated / unavailable
2. Complete Fable Job 1 bundle token estimate + context-budget calculation + Path A/B recommendation
3. Drive inventory, sample extraction results, parser failure rates, proposed Drive-processing boundary
4. Any schema surprises or extraction failures across the five databases
5. Request for Eric's must-not-merge pairs (A9)

**Stop at Eric Gate 1.**
