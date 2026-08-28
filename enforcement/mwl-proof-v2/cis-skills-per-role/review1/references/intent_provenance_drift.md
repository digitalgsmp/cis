# Intent Provenance & Drift Detection (2026-07-11)

## Eric's Core Concern

Eric's concept of provenance is NOT about linking individual factual claims
to web sources. It's about **intent alignment** — ensuring the pipeline
produces what Eric actually asked for, tracing actions back to intent.

> "provenance somehow guiding the pipeline to actually produce what I ask
> for which is laid out in great detail throughout the KB. between the
> gates, provenance, tool restrictions and all the rest of the container
> guardrails, this is the ultimate behavior of the cis tool I am hoping
> to have."

> "I am looking to curb guesses and assumptions from the models. I dont
> want to be working on something cutting edge and the models are
> delivering stale training data."

Eric clarified he doesn't want unnecessary web searches on every claim
(the pipeline is already slow). The real problem is **intent drift through
the pipeline** — each phase reinterprets the previous phase's output, and
the original intent degrades.

## Architecture

```
Eric's Intent → Brain enriches (KB search) → LOCK as enriched intent
                                                      │
                                                      ▼
         ┌────────────────────────────────────────────┐
         │  INTENT ANCHOR (locked in intent_provenance) │
         │  Injected into EVERY downstream phase prompt │
         └────────────────────────────────────────────┘
                    │          │          │          │          │
                    ▼          ▼          ▼          ▼          ▼
               Intent Rev  Draft     Prop Rev   Menter     Verify
                    │          │          │          │          │
                    ▼          ▼          ▼          ▼          ▼
               _measure_drift() at each phase boundary
                    │          │          │          │          │
                    ▼          ▼          ▼          ▼          ▼
               phase_drift table (score, reasons, verdict)
                              │
                              ▼
               gate_intent_verification.py (final aggregate check)
```

## Database Schema (Migration 0029)

```sql
CREATE TABLE intent_provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    original_intent TEXT NOT NULL,
    enriched_intent TEXT,        -- Brain's structured understanding
    kb_context_hash TEXT,        -- SHA-16 of KB context that informed enrichment
    brain_session_id TEXT,       -- links to brain_chats if from conversation
    locked_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE phase_drift (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,          -- brain, intent_review, draft, proposal_review, menter, verify
    round INTEGER NOT NULL,
    intent_snapshot TEXT NOT NULL, -- enriched intent copied for immutability
    phase_output TEXT,
    drift_score REAL,             -- 0.0 = perfectly aligned, 1.0 = completely diverged
    drift_reasons TEXT,          -- JSON array of detected misalignments
    verdict TEXT,                 -- ALIGNED, MINOR_DRIFT, SIGNIFICANT_DRIFT, DIVERGED
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## Provenance Functions (pipeline_relay.py)

### `_lock_intent_provenance(conn, run_id, original_intent, enriched_intent, kb_context, brain_session_id)`

Called ONCE after Brain phase completes. Brain's output becomes the
enriched intent anchor. Every downstream phase is checked against this.

```python
_lock_intent_provenance(
    self.conn, run_id,
    original_intent=intent,
    enriched_intent=output,  # Brain's understanding
    kb_context=discovery,
)
```

### `_get_enriched_intent(conn, run_id)`

Retrieves the locked enriched intent. Falls back to `workflow_runs.topic`
if no enriched intent is locked (for backward compatibility).

### `_intent_anchor_block(conn, run_id)`

Builds the injection block for downstream phase prompts:

```
## ══ INTENT ANCHOR (enriched — do not drift from this) ══
[Brain's enriched understanding here]
## ══ END INTENT ANCHOR ══
```

Wired into ALL 6 downstream phases:
- `_intent_review` prompt
- `_draft_phase` prompt
- `_proposal_review` prompt
- `_pattern_catalog` prompt
- Menter execution prompt
- `_verification` prompt

### `_measure_drift(intent, output, phase) → (score, reasons, verdict)`

Deterministic heuristic — NOT an LLM judgment. Three weighted axes:

1. **Keyword overlap (40%)**: How many intent concepts appear in output?
   - Filters stop words (the, a, an, to, for, etc.) and CIS domain words
   (pipeline, brain, draft, verify, json, sqlite, etc.)
   - overlap_ratio = |intent_words ∩ output_words| / |intent_words|

2. **Scope expansion (30%)**: Did output introduce many unrelated concepts?
   - output_unique = output_words - intent_words - stop_words
   - expansion_ratio = |output_unique| / |output_words|

3. **Action alignment (30%)**: Did output honor intent action verbs?
   - Checks for: add, fix, remove, update, create, build, implement,
     refactor, test, deploy, configure, redesign, rework, change,
     replace, wire, connect, integrate, migrate, document
   - action_ratio = |actions_found| / |intent_actions|

**Drift score**:
```
drift_score = (1 - overlap_ratio) * 0.4
            + expansion_ratio * 0.3
            + (1 - action_ratio) * 0.3
```
Clamped to [0.0, 1.0].

**Verdict thresholds**:
- ALIGNED: drift < 0.2
- MINOR_DRIFT: 0.2 ≤ drift < 0.4
- SIGNIFICANT_DRIFT: 0.4 ≤ drift < 0.6
- DIVERGED: drift ≥ 0.6

### `_record_phase_drift(conn, run_id, phase, round_num, phase_output, score, reasons, verdict)`

Stores drift measurement in `phase_drift` table. Copies the current
enriched intent as `intent_snapshot` for immutability (even if the
enriched intent changes later, the drift record shows what it was at
measurement time).

## Guardrail: `guardrail_intent_drift` (guardrails.py)

ADVISORY mode — flags drift but does not block. Phase B will determine
which drift levels should block.

- **SKIP** on brain phase (that's where intent is created, not checked)
- **SKIP** if no locked enriched intent exists
- **PASS** for ALIGNED and MINOR_DRIFT
- **FAIL** for SIGNIFICANT_DRIFT and DIVERGED

Wired into `run_guardrails()` as Tier 5, runs on ALL phases when
`conn` and `run_id` are available.

Also records drift in `phase_drift` table via `_record_phase_drift()`.

## External Gate: `gate_intent_verification.py`

Runs at the verify phase. Checks aggregate drift across all phases.

**Exit codes**:
- 0 = PASS (all phases within threshold)
- 1 = FAIL (any phase DIVERGED, or max drift > 0.6)
- 2 = SKIP (no enriched intent or no drift records)

**Logic**:
1. Reads `intent_provenance` for the enriched intent
2. Reads all `phase_drift` rows for the run
3. If any phase has verdict DIVERGED → FAIL
4. If max drift_score > 0.6 → FAIL
5. If significant drift but not diverged → PASS with advisory warning
6. Otherwise → PASS

Wired into `PHASE_GATE_MAP["verify"]` as ADVISORY.

## API Feed Integration

`GET /api/relay/<run_id>/feed` now returns:
- `provenance`: the locked intent provenance record
- `drift`: array of phase drift records with scores and verdicts

The UI (`PipelineLive.jsx`) renders drift scores as colored badges on
each phase card:
- Green: ALIGNED
- Orange: MINOR_DRIFT / SIGNIFICANT_DRIFT
- Red: DIVERGED

## Eric's Correction on Provenance Scope

When I first tried to build provenance as "link every factual claim to a
web source," Eric corrected:

> "this is sensitive, its already a slow pipeline. I dont want to be
> doing unnecessary searches. these LLMs are pretty smart, I think my
> concern is more about alignment of action taken with the understood
> intent."

The provenance system is about **intent alignment**, not claim verification.
The models are smart enough to produce coherent work — the problem is
they drift from what Eric asked for.

## Key Files

- `runtime/abstraction/pipeline_relay.py` — provenance functions + injection
- `runtime/abstraction/guardrails.py` — `guardrail_intent_drift` + wiring
- `tools/gates/gate_intent_verification.py` — final verification gate
- `enforcement/mwl-proof-v2/gates/gate_intent_verification.py` — container copy
- `runtime/schema/migrations/0029_intent_provenance_drift.sql` — DB tables
- `runtime/api/relay.py` — provenance + drift data in feed endpoint
- `runtime/ui/src/PipelineLive.jsx` — drift badges in UI

## Two-Layer Drift Detection (Updated 2026-07-11)

The drift system now has two layers:

### Layer 1: Deterministic Heuristic (fast, zero cost)
Same as described above — keyword overlap (40%), scope expansion (30%),
action alignment (30%). Runs on every phase output. Returns `det_score`.

### Layer 2: Semantic Comparison via Local LLM (Qwen3-VL-30B)
Fires ONLY when the deterministic score is ambiguous (0.15 ≤ det_score ≤ 0.65).
This is the "uncertain zone" where word overlap can't tell if the meaning
has drifted.

**How it works:**
- `_semantic_drift_check(intent, output, phase)` calls the local Qwen model
  at `http://127.0.0.1:8002/v1/chat/completions`
- Prompts Qwen to rate alignment 0-10 with a one-sentence reason
- Converts: drift_score = (10 - raw_score) / 10
- Returns `(semantic_score, [reason])` or `(None, [])` if Qwen unavailable

**Combined score when semantic runs:**
```
final_drift = det_score * 0.4 + semantic_score * 0.6
```
60% weight to semantic (it's more accurate) when it fires. If Qwen is
unavailable, falls back to deterministic-only — no pipeline breakage.

**Why local LLM, not DeepSeek:** Eric explicitly said "there is only 2
dollars left on the deepseek account so dont call any deepseek apis."
Local LLM on RTX 4090 = zero cost, no external dependency. Qwen3-VL-30B
MoE with 3B active params runs at ~23 tokens/sec on the 4090.

**Qwen server setup:**
- Model: `/home/eric/models/Qwen3-VL-GGUF/qwen3-vl-30b-a3b-instruct-q4_k_m.gguf`
- Server: llama.cpp on port 8002, systemd service `llama-server-qwen.service`
- `--n-gpu-layers -1 --cpu-moe --no-mmap --flash-attn on --ctx-size 32768`
- Load time ~2-3 minutes (MoE layers go to CPU memory)
- Also available: GLM-4.7-Flash at `/home/eric/models/GLM-4.7-Flash-Q4_K_M.gguf`

## What's NOT Built Yet

- **Intent drift as BLOCK mode**: Currently ADVISORY. Phase B (threshold
  tuning) will determine which drift levels should hard-block the pipeline.
- **Drift-triggered revision loop**: If a phase drifts significantly, it
  should go back for revision, not just get flagged. The drift score is
  recorded but doesn't trigger a revision cycle yet.
- **Structured intent document**: Brain's raw output is the enriched intent.
  A structured document (goals, constraints, success criteria) would be
  easier to check against than free-form text.
- **Intent enrichment from KB**: Brain currently uses its own output as
  the enriched intent. A deeper enrichment would pull Eric's full vision
  from the KB (past sessions, decisions, working methods) and build a
  richer intent document. The brain_chats conversation IS a form of this,
  but it's not yet deeply integrated with the KB archive.
