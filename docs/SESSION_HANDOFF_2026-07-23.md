# SESSION HANDOFF — July 23, 2026
**From:** Hermes Prime / Eric
**To:** Next session (any profile)
**Topic:** Pass 0 Preflight Census — CORRECTIONS NEEDED before Gate 1

---

## Current State

Pass 0 preflight executed. Census is **directionally correct (Path B)** but has errors flagged by ChatGPT review. **Gate 1 is NOT approved.** Census must be corrected and re-presented.

**Spec:** `/mnt/projects/cis/docs/TAXONOMY_MINING_SPEC.md` (v1.1, 497 lines)
**Census (flawed):** `/mnt/projects/cis/data/taxonomy_mine/pass0_census.json`
**Amendments:** `/mnt/projects/cis/docs/DIRECTIVE_TAXONOMY_MINING_v1_1.md`

---

## What Pass 0 Established (correct)

| Datum | Value |
|-------|-------|
| Human messages | 5,991 (across 5 DBs) |
| Est. human tokens | ~1.74M |
| Exact dup rate | 2.3% (low — dedup won't solve size) |
| Near-dup rate (sample) | ~5.6% |
| Path | **B — Dossier map-reduce** |

**Key discovery:** CIS spine uses `role='human'` (4,395 msgs), not `role='user'` (only 7).

---

## FIX LIST (ChatGPT Review)

### 1. CONTEXT WINDOW — CRITICAL
- **Wrong:** `verified_usable_window_claude: 180000`
- **Correct:** Claude Fable 5 has **1,000,000 token context window** (1M input, 128K output)
- Must identify where 180K came from (client/gateway restriction?)
- Recalculate: bundle 3.54M / 1M = 354% (still Path B, but chunk sizing changes)
- 65% threshold at 1M window = 650K input tokens

### 2. 100 MISSING MESSAGES
- Counted: 5,991 human messages
- Hashed: 5,891
- **100 unaccounted** — violates "no invisible discard path"
- Must trace: empty bodies, null content, type mismatches, hash exceptions, query differences
- Log exclusions with reasons

### 3. DUPLICATE METRICS — REDEFINE
- Current `exact_duplicate_rate: 0.0229` = 135 groups / 5,891 (measures groups, not occurrence rate)
- Actual duplicate occurrence: (5,891 - 5,658) = 233 repeated messages = 3.96%
- Near-dup: clarify whether "28/500" means 28 messages with a near-dup partner, or 28 total pairs
- Report both group count AND occurrence rate with clear denominators

### 4. MISSING CENSUS ITEMS

Each must be added to pass0_census.json:

| # | Item | Type |
|---|------|------|
| a | **Token counts per month** (not just per source) | Exact, from timestamps |
| b | **NL vs. terminal/log/code token split** per source | Sample-based estimate |
| c | **Largest sessions and documents** by token count | Exact |
| d | **Message-length distribution** (quartiles, histogram) | Exact |
| e | **Drive extracted-character estimates** per format category | Sample-based estimate |
| f | **Extractable/visual/unknown percentages** (have counts, need %) | Exact |
| g | **Itemized 3.54M bundle breakdown** — every component listed with formula | Calculated |
| h | **Agent-context formula** — 200 tokens/msg was flat assumption, must sample-validate | Sample-based estimate |
| i | **Must-not-merge pairs** — Eric provides 3-5 pairs at Gate 1 | Eric input |
| j | **Human-readable ISO dates** for ALL profiles | Normalize Unix timestamps |

### 5. DATE FORMAT — NORMALIZE
- CIS spine uses ISO timestamps ✓
- Prime, R1, GLM, Qwen return Unix timestamps — convert to ISO
- All profiles must use same timezone/format

### 6. AGENT-CONTEXT FORMULA
- Current: 1,198,200 context tokens ÷ 5,991 msgs = exactly 200/msg
- This is a **flat assumption**, not a measurement
- Must state it as `total_human_msgs × 200` and validate against a sample of actual preceding agent turns
- If sample shows average is 350 tokens, recalibrate

### 7. DRIVE — PATH-LEVEL CATEGORIES

Current inventory treats all 9,966 "extractable" files equally. Must split into:

| Category | Examples |
|----------|----------|
| User-authored docs | .md plans, .txt notes, .xlsx workbooks |
| Current project source | CIS runtime/, tools/ |
| Historical/archived source | Old repos, backups |
| Third-party/vendor | node_modules, package deps |
| Generated/build artifacts | .map, .pyc, bundles |
| Databases/machine state | .db, .json state files |
| Visual unsupported | Images, video, .blend |

Generated JS maps, .pyc, package directories → logged but NOT semantically indexed.

---

## 5 Source Paths

```
cis_spine:    /mnt/projects/cis/data/cis_memory.db       4.5 GB  (role='human')
prime_v4pro:  ~/.hermes-v4pro/state.db                   156 MB  (messages, role='user')
r1:           ~/.hermes-r1/state.db                      97 MB
glm_verifier: ~/.hermes-glm-verifier/state.db             56 MB
qwen:         ~/.hermes-qwen/state.db                     5.5 MB
drive:        /mnt/projects/cis/data/drive_imports/       11,775 files, 5.7 GB
```

## Key Files

| File | Purpose |
|------|---------|
| `/mnt/projects/cis/docs/TAXONOMY_MINING_SPEC.md` | Authoritative spec v1.1 (497 lines) |
| `/mnt/projects/cis/docs/DIRECTIVE_TAXONOMY_MINING_v1_1.md` | Eric's A1-A12 amendments |
| `/mnt/projects/cis/docs/DIRECTIVE_TAXONOMY_MINING_v1.md` | Original v0.5→v1.0 directive |
| `/mnt/projects/cis/data/taxonomy_mine/pass0_census.json` | Current (flawed) census |

## Model Decisions (Eric)

- **Tier 2 stance model:** GLM 5.2 (z-ai/glm-5.2), NOT Qwen3-VL-30B

## Budget Context (ChatGPT)

- Fable 5: $10/M input tokens, $50/M output tokens
- Sending full 3.54M bundle = ~$35 input alone — over 1/3 of remaining credit
- **Target:** Local GLM produces 250K-500K token reconstruction bundle → Fable pass ~$5-7.50
- Preserves credit for adversarial review, architecture eval, code work

## What Fable Ultimately Needs (two packages)

1. **Historical reconstruction package** — concepts, aliases, corrections, rejected agent ideas, decisions, verbatim evidence
2. **Current execution package** — repo state, architecture, schema, what exists on machine, enforcement constraints, single authorized task

## Eric Gate 1 Decision

**Do NOT approve yet.** Hermes must correct Pass 0 (items 1-7 above), re-present census, then Eric approves Path B.

Next deliverable after Gate 1: **Small stratified GLM mapping test** across early/middle/recent samples — prove GLM can produce grounded concept dossiers before processing all 14 months.

---

*Generated: 2026-07-23 | Hermes Prime | deepseek-v4-pro*
