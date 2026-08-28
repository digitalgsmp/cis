# Tier 2 Guardrail Implementation (2026-07-10, commit 141d742)

10 additional deterministic guardrails added to `runtime/abstraction/guardrails.py`,
bringing the total to 20 guardrails (Tier 1 + Tier 2). All fire on every pipeline phase.

## Guardrail Summary

| # | Name | Mode | Catches |
|---|------|------|---------|
| 11 | Context Budget Monitor | ADVISORY | Context window exhaustion (§2.9) |
| 12 | Mode Collapse Detector | ADVISORY | Diversity collapse in multi-agent (§2.3) |
| 13 | Loop Detector | BLOCK | Degeneration loops, revision cycling (§2.4) |
| 14 | Goal Anchoring Check | ADVISORY | Task drift over long horizons (§2.1) |
| 15 | Trajectory Monitor | ADVISORY | Repeated actions without progress (§2.14) |
| 16 | Verbosity / Density Metric | ADVISORY | Reward hacking via length (§2.20) |
| 17 | Sequential Review Enforcer | ADVISORY | Shared blind spots in parallel review (§1.8) |
| 18 | Model Diversity Enforcement | BLOCK | Same model reviewing its own work (§1.6) |
| 19 | Version Drift Check | ADVISORY | Silent model version changes (§2.8) |
| 20 | Output Sanitizer | BLOCK | Steganography, unicode tricks (§2.24) |

## Key Techniques

### Context Budget Monitor (#11)
- Per-role context thresholds in chars (~4 chars/token approximation)
- Default: 100K chars (~25K tokens), reasoning roles: 120K chars
- Warn at 80% of threshold, FAIL at 100%

### Loop Detector (#13) — BLOCK mode
Two-stage detection:
1. **Exact match**: SHA-256 hash of output compared against all previous outputs for the same phase
2. **Near-duplicate**: Jaccard similarity >95% = effectively a loop
Rationale for BLOCK: if the agent produces the same output as a previous round, it's stuck.
No amount of additional rounds will help — escalate immediately.

### Mode Collapse Detector (#12) — ADVISORY mode
Uses Jaccard similarity (word-level sets):
- >90% max similarity to any previous output = collapse
- >75% average similarity across all previous outputs = possible collapse
ADVISORY because high similarity can be legitimate convergence on the correct answer.

### Goal Anchoring Check (#14)
- Extracts significant words from intent (filters stop words, short words)
- Calculates overlap ratio with agent output
- Drift threshold gets **stricter in later rounds**: `min_expected = max(0.1, 0.3 - (round_num - 1) * 0.05)`
- Round 2: 25% overlap required, Round 3: 20%, Round 4: 15%, floor at 10%

### Trajectory Monitor (#15)
Queries `agent_trajectories` table for the role's recent history:
- **Repeated identical outputs**: if last N output_hashes are all the same → stuck
- **Consecutive failures**: if last 3+ outcomes are "failed" → degeneration
Requires DB connection and run_id — passed from `run_guardrails()` caller.

### Verbosity / Density Metric (#16)
Three measurements:
- **Word count**: >5000 words = verbosity hacking, <20 words for brain/draft/menter = insufficient
- **Density**: unique_words / total_words — low density with high word count = padding
- **Code ratio**: chars in code blocks / total chars — measures substance vs prose

### Model Diversity Enforcement (#18) — BLOCK mode
Checks that `review1` and `review2` use different model providers via `dispatch.py` PROFILES.
Same model reviewing its own work is a fundamental design violation — same blind spots.
Loads PROFILES from dispatch module; SKIP if unavailable (dev environment without container config).

### Version Drift Check (#19)
First call records baseline models from PROFILES. Subsequent calls compare:
- If any role's model changed from baseline → drift detected
- Updates baseline after detection to avoid repeated alerts
- Global state (`_KNOWN_MODELS` dict) persists within process lifetime

### Output Sanitizer (#20) — BLOCK mode
Checks for:
1. **Zero-width characters**: U+200B through U+2064 (invisible characters for steganography)
2. **Homoglyphs**: Cyrillic letters that look like Latin (а, е, о, р, с, х, у)
3. **Control characters**: U+0000-U+0008, U+000B-U+000C, U+000E-U+001F
4. **Mixed scripts**: >3 Cyrillic chars in primarily Latin text = homoglyph attack
Steganography is adversarial — BLOCK prevents propagation.

### Sequential Review Enforcer (#17)
Checks if reviewer 2's prompt contains reviewer 1's output (first 200 chars).
Currently ADVISORY because the pipeline uses parallel review by design.
Sequential review is the enhancement direction per Eric's workflow correction.

## Wiring Pattern

All Tier 2 guardrails are called from `run_guardrails()` in `guardrails.py`:
- Context budget: runs on prompt (all phases)
- Verbosity/density: runs on output (all phases)
- Output sanitizer: runs on output (all phases)
- Loop detector + mode collapse: run on output when `previous_outputs` is provided
- Goal anchoring: runs when `round_num > 1`
- Trajectory monitor: runs when `conn` and `run_id` are provided
- Model diversity + version drift: run on every call (config checks)

The `run_guardrails()` function signature was extended with: `previous_outputs`, `round_num`,
`conn`, `run_id`. All pipeline_relay.py call sites were updated to pass these parameters.

## Testing

All guardrails tested with positive and negative cases:
- Clean output → PASS
- Fabricated paths → FAIL (BLOCK)
- Hollow consensus → FAIL (sycophancy)
- Steganographic chars → FAIL (BLOCK)
- Identical repeated output → FAIL (loop, BLOCK)
- Large prompt → FAIL (context budget)
- Drifted output in round 3 → FAIL (goal anchoring)

Tests run via `execute_code` (Python import + direct function calls).
