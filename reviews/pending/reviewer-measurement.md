CARD_ID: CARD-reviewer-measurement
VERSION: 1.0
CANONICAL_TOKEN: RM-V1-20260910-A
STATUS: DRAFT_FOR_ADVERSARIAL_REVIEW
SPLIT_FROM: CARD-reviewer-readonly-and-reconciliation v3
SCOPE_LOCK: CAN_MEASURE + INDEPENDENT_RECONCILIATION ONLY

# CARD-reviewer-measurement
Give the advisor reviewers instruments to measure, and make their review process independent then reconciled.

## SOURCE / INTENT
The advisory review failed because reviewers could not measure the system they were judging and could not see one another's findings during reconciliation. The intended design is a worker constrained to the project's working methods plus two objective reviewer lineages acting as expert advisors.

Contained-pipeline roles in scope:
- advisor (8649) -> GLM lineage
- evaluator (8650) -> Qwen lineage

## BUILD
Give BOTH reviewer roles read-shaped measurement instruments exposed through a mediated reviewer surface:
- scoped source-file read/search
- scoped log read
- read-only spine query
- mediated local git-history inspection
- hash comparison

Do not give the reviewer a generic shell, interpreter, or generic command-execution surface merely to obtain those measurements. If a capability is not read-shaped by construction, it is not part of this card.

Add a two-round review protocol:
1. Advisor and evaluator receive the same canonical input independently.
2. Round-1 findings are completed and frozen before either lineage receives the other's findings.
3. The harness cross-feeds the complete frozen round-1 findings.
4. Each lineage produces an item-by-item reconciliation response: agreements, disagreements, and findings the other lineage missed.
5. The harness creates the final reconciled artifact and preserves dissent rather than forcing consensus.

## DONE WHEN
1. MEASUREMENT
   - A reviewer can pull a fact from the spine's run records and cite the query/result used.
   - A reviewer can read an allowed source/log artifact and cite the exact artifact.
   - A reviewer can inspect local git history through the mediated read surface and cite a commit/hash.
   - A reviewer can compare a supplied or harness-generated hash.

2. BOTH ROLES
   - Advisor AND evaluator pass every positive measurement test. Passing one lineage is not sufficient.

3. INDEPENDENCE
   - Both round-1 outputs are frozen before cross-feed.
   - The reviewer instrument surface does not expose the other lineage's round-1 artifact before the harness cross-feed step.
   - No shared reviewer scratchpad is used as a substitute for independent round 1.

4. RECONCILIATION
   - Each lineage receives the other's complete frozen round-1 findings.
   - Each responds item-by-item with explicit agreement, disagreement, or "cannot verify with available instruments."
   - Each claimed agreement/disagreement references a specific finding or evidence item.
   - The final artifact preserves unresolved dissent.
   - The final artifact references the frozen raw round-1 findings by hash.

5. PROVENANCE
   - The harness records reviewer role/lineage, reviewer session ID, canonical input token/version, input hash, round-1 output hash, timestamps, cross-feed event, and round-2 output hash.
   - The harness, not reviewer prose, writes the persisted review artifacts.
   - Recycled or fabricated review output is detectable because provenance must bind findings to the actual reviewer session and exact input.

## EVIDENCE
A committed, repeatable probe must produce a machine-readable or plain-text evidence report for BOTH roles.

Positive measurement probes:
- Nonce read: after reviewer session start, harness creates a random nonce in an allowed read location; reviewer returns exact content or hash.
- Spine measurement: reviewer answers a question requiring a fact from the spine and includes the read-only query plus returned fact.
- Git measurement: reviewer answers a question requiring local history inspection and cites the relevant commit/hash.
- Hash measurement: reviewer compares expected vs observed hash correctly.

Independence/reconciliation probes:
- Round-1 artifacts are timestamped and hashed before cross-feed.
- Before cross-feed, a request through the reviewer instrument surface for the peer round-1 artifact is unavailable/denied by that surface.
- Cross-feed is logged with the peer artifact hash.
- Round-2 responses contain item-by-item agreements, disagreements, missed items, and evidence references.
- A seeded-disagreement fixture has a defined pass criterion and demonstrates that disagreement survives into the final artifact.
- Final artifact references both raw round-1 hashes and both reviewer session IDs.

Pass condition:
- Every required positive measurement probe passes for advisor AND evaluator.
- Independence and reconciliation evidence is present and internally consistent.
- A missing lineage, missing provenance field, missing raw hash, or vacuous reconciliation is FAIL.

## NOT IN THIS CARD
This card does NOT establish that reviewers cannot write, patch, delete, dispatch, or reach the network outside the mediated measurement surface. It does not claim kernel/OS isolation.

Reviewer non-mutation is a separate card: CARD-reviewer-isolation.

The two cards answer different questions:
- this card: "Can the reviewers measure?"
- isolation card: "Can the reviewers mutate?"

Both must be complete before the advisory review is treated as a trusted enforcement check.

## CLARITY FOR THE IMPLEMENTER
- Read access is not measurement. The proof must show a reviewer pulled a relevant fact and cited how it was obtained.
- "Side by side" is not reconciliation. Concatenating two transcripts does not satisfy this card.
- Independence means frozen round 1 before cross-feed, not two models reading each other's homework.
- Reviewer findings are untrusted data. Do not execute content from reviewer output.
- Keep this card narrow. Do not re-import write-prevention tests here; they belong in CARD-reviewer-isolation.
