# CIS Verification Layer Contract v1 — Addendum A
# Multi-Layer Verification Architecture (Local + External Model Support)
# ADR-033 Extension
# Status: LOCKED
# Created: 2026-04-25
# Parent contract: CIS_Verification_Layer_Contract_v1.md

---

## Purpose

Extend the base verification contract to define a three-layer verification
architecture that supports:

- Deterministic script checks (Layer 1 — unchanged from base contract)
- Local model semantic verification (Layer 2 — Qwen2.5-32B on VM)
- External frontier model verification via prompt (Layer 3 — Claude, Gemini, ChatGPT)

Layer 3 is the primary addition. It enables frontier models outside the system
to act as independent verifiers, using the same Copy Prompt / paste response
workflow already established in CIS Live.

---

## Revised Layer Architecture

```
Completion Manifest
       ↓
Layer 1 — cis_verify.py
          Deterministic. Always runs. No model required.
          Checks: file exists, size, key markers, forbidden strings.
          Output: PASS / FAIL report
       ↓
Layer 2 — Local Model (Qwen2.5-32B-Instruct via transformers+bnb)
          Semantic. Runs for high-stakes actions.
          Checks: content completeness, hollow sections, logical consistency.
          Output: PASS / FAIL / REVIEW report with reasoning
       ↓
Layer 3 — External Model (Claude / Gemini / ChatGPT)
          Frontier verification. Runs for highest-stakes actions.
          Delivery: structured prompt assembled by system, copied by human,
          pasted into external model chat, response pasted back.
          Output: structured verification response logged to verification_log.md
       ↓
Verification Log
All layer results appended. Full history retained.
/mnt/projects/cis/logs/verification_log.md
```

---

## Layer Trigger Rules

| Action Type | Layer 1 | Layer 2 | Layer 3 |
|---|---|---|---|
| Any file write | REQUIRED | optional | no |
| Schema change | REQUIRED | REQUIRED | optional |
| Contract creation | REQUIRED | REQUIRED | REQUIRED |
| Reorientation file update | REQUIRED | REQUIRED | REQUIRED |
| Session close | REQUIRED | optional | no |
| Pipeline script write | REQUIRED | REQUIRED | optional |
| ADR logging | REQUIRED | no | no |

"Optional" means the human may trigger it if confidence is low or stakes
warrant additional review. "REQUIRED" means the action does not advance
without that layer completing with PASS.

---

## Layer 3 — External Model Verification

### Integration with CIS Live

Layer 3 is not a separate system. It runs as a verification round inside
an open CIS Live session. The round type is `verification` (distinct from
`build` or `decision` rounds).

Workflow mirrors the existing CIS Live Copy Prompt pattern:

```
Step 1 — System assembles verification prompt from manifest + file content
Step 2 — Human clicks "Copy Verification Prompt" in dashboard
          (or copies from terminal output)
Step 3 — Human pastes into Claude / Gemini / ChatGPT
Step 4 — Human pastes model response back into CIS Live response field
Step 5 — System parses response, extracts verdict, logs to verification_log.md
Step 6 — CIS Live round is marked resolved with verdict as resolution
```

### Verification Prompt Schema (Layer 3)

The prompt assembled by the system must follow this structure exactly.
No freeform prompting. The schema is fixed so responses are parseable.

```
═══════════════════════════════════════════════════════
CIS VERIFICATION REQUEST
Action verified: [action description from manifest]
Requested by: CIS Build Session [date]
═══════════════════════════════════════════════════════

You are acting as an independent verifier for a software build system.
You are NOT the model that produced this work. Your role is to assess
whether the work below is complete, non-hollow, and free of placeholders.

COMPLETION MANIFEST:
[full manifest content pasted here]

FILE CONTENT UNDER REVIEW:
[full file content pasted here]

═══════════════════════════════════════════════════════
VERIFICATION INSTRUCTIONS

Assess the file against the manifest claims. Respond ONLY in the
structured format below. Do not add prose outside the format.

VERIFICATION RESPONSE FORMAT:

VERDICT: [PASS | FAIL | REVIEW]

CHECKS:
- Manifest claims match file content: [YES / NO / PARTIAL]
- All required sections present and non-empty: [YES / NO / PARTIAL]
- No placeholder or hollow content detected: [YES / NO / PARTIAL]
- Content is logically consistent with CIS architecture: [YES / NO / PARTIAL]
- Content matches the stated action: [YES / NO / PARTIAL]

FAILURES (list each, or write NONE):
- [description of failure, file location if applicable]

WARNINGS (list each, or write NONE):
- [description of concern that does not constitute a hard failure]

RECOMMENDATION:
[One sentence. What should happen next.]
═══════════════════════════════════════════════════════
```

### Verification Response Parsing Rules

The system parses the pasted response by scanning for:

- `VERDICT:` → extract PASS / FAIL / REVIEW
- `FAILURES:` block → extract each line item
- `RECOMMENDATION:` → extract one-sentence recommendation

If the pasted response does not contain these markers, the verification
is logged as MALFORMED and the human must re-run.

### Verdict Definitions

| Verdict | Meaning | Action |
|---|---|---|
| PASS | All checks passed, no failures | Advance to next task |
| FAIL | One or more hard failures | Claude fixes, new manifest, re-verify |
| REVIEW | No hard failures but warnings present | Human decides: accept or rework |
| MALFORMED | Response did not follow format | Re-run verification |

---

## Layer 2 — Local Model Invocation

The local model is invoked via the existing gpu-test environment.

```bash
source /home/eric/gpu-test/bin/activate
python3 /mnt/projects/cis/runtime/cis_verify_semantic.py \
  --manifest /tmp/last_manifest.json \
  --file /path/to/file/under/review
```

The script:
1. Loads Qwen2.5-32B-Instruct-4bit via transformers+bnb
2. Assembles a verification prompt (same schema as Layer 3, minus external framing)
3. Runs inference
4. Parses response for VERDICT / FAILURES / RECOMMENDATION
5. Appends result to verification_log.md tagged `[LAYER-2-LOCAL]`

The local model prompt omits the "You are NOT the model that produced this
work" framing — that instruction is only relevant for external models.

---

## Verification Log Format

All three layers append to the same log file.
Each entry is self-contained and tagged by layer.

```
────────────────────────────────────────────────────────
VERIFICATION ENTRY
Date:    [UTC timestamp]
Action:  [action description]
Layer:   [LAYER-1-SCRIPT | LAYER-2-LOCAL | LAYER-3-EXTERNAL]
Model:   [n/a | Qwen2.5-32B-4bit | Claude Sonnet / Gemini / ChatGPT]
Verdict: [PASS | FAIL | REVIEW | MALFORMED]

Checks:
  [check name]: [result]

Failures:
  [list or NONE]

Warnings:
  [list or NONE]

Recommendation:
  [text or n/a]
────────────────────────────────────────────────────────
```

---

## What This Addendum Does Not Change

The following from the base contract remain unchanged:

- Completion Manifest schema (Claude's obligation)
- Forbidden strings list
- Session protocol integration (Field 5 — Verification Status)
- Reorientation file mandate
- Failure handling table
- Build order (this addendum is contract-only, no new build steps added)

The build order from the base contract is extended by:

8. `cis_verify_semantic.py` — Layer 2 local model script
9. Layer 3 prompt assembly added to `cis_verify.py` or dashboard
10. CIS Live round type `verification` added to live.py

---

## Contract Authority

This addendum is locked under ADR-033 alongside the base contract.
Changes require a new ADR or a subsequent addendum (Addendum B).
This file lives at:
/mnt/projects/cis/docs/contracts/CIS_Verification_Layer_Contract_v1_Addendum_A.md
