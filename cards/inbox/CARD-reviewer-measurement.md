CARD reviewer-measurement: Give the advisor reviewers instruments to measure

VERSION: 1
SPLIT FROM: reviewer-readonly-and-reconciliation v3. This card is the "can measure" half only.
            The "cannot write" half is deferred to the reviewer-isolation slice (ADR-015/016, §14).
CHANGES: n/a — first version of the split card.

SOURCE: Eric, 2026-09-10 — "the advisory review is a fraud because the reviewers cannot measure anything. the reviewers were suppose to keep claude honest and transparent but that failed."

INTENT (Eric, verbatim): "I need checks and balance... a worker who is constrained to my working methods and two objective reviewers as expert advisors."

BUILD: Give advisor (8649) and evaluator (8650) read-shaped measurement instruments — read files (scoped), query the spine read-only, inspect git history, compare hashes — plus a reconciliation step with staged round-1 independence, item-by-item cross-feed, and a dissent-preserving artifact. Proven by positive behavioral evidence against BOTH roles.

DONE WHEN:
  - MEASUREMENT: a reviewer can, in a live review, pull a fact from the spine's run records and cite it. The measurement surface is: read source files, read logs, read-only spine query, read-only git inspection, hash comparison. A reviewer never needs a shell to measure — instruments are read-shaped by construction, not "terminal minus bad commands."
  - BOTH ROLES: advisor AND evaluator each pass every positive measurement test.
  - RECONCILIATION: after round 1, each lineage reads the other's full findings and responds item-by-item with explicit agreements, disagreements, and what-the-other-missed. The final artifact preserves dissent and references raw round-1 findings by hash. Not concatenation, not vacuous "we agree."
  - INDEPENDENCE: round-1 outputs are frozen before cross-feed; each lineage's round-1 is not handed to the other until both are complete.
  - PROVENANCE: the final artifact records which reviewer produced which findings (reviewer session IDs + input hashes + timestamps), so a fabricated or recycled review is detectable.

EVIDENCE (positive — "can measure", not "cannot write"):
  # Read/measure (non-gameable):
  - harness creates a random nonce file after session start, in an allowed path -> reviewer returns exact content or hash
  - reviewer answers a question that requires a fact pulled from the spine's run records -> correct citation, with the query or row it used
  - reviewer inspects git history (e.g. "what did the last commit change") -> correct answer citing a commit/hash
  # Reconciliation (real, not concatenation):
  - round-1 artifacts for both lineages, hashed and timestamped
  - cross-feed event log (advisor received evaluator round-1 hash/content, and vice versa)
  - round-2 item-by-item responses (agreements, disagreements, missed-items) from each lineage, each citing evidence or a finding item
  - final artifact references raw round-1 findings by hash and preserves dissent
  - a seeded-disagreement fixture forces disagreement handling, with a defined pass criterion
  # Both roles:
  - the nonce, spine-citation, and git-inspection tests pass for advisor AND evaluator

NOT IN THIS CARD: write prevention. Whether a reviewer can write, patch, delete, or dispatch is NOT established here and is NOT claimed. That guarantee is the reviewer-isolation slice — kernel-level read-only mount, non-root user, container-level network egress denial — delivered by ADR-015/016 (gated on §14). Until it lands, the reviewers are un-blinded but not yet provably non-mutating. This card gives them eyes; the isolation card takes away their hands. Both are required before the advisory review is trusted, but they are built and proven separately.

CLARITY FOR THE IMPLEMENTER (read before writing code):
  - The instruments are read-shaped, not a generic terminal. read_file with scoped path prefixes, a read-only spine query (mode=ro, SELECT only), git log/show/diff (local, no mutation commands), and hash comparison. No interpreter, no shell, no network. If a read tool is not trivially read-only by construction, it is not in the measurement surface.
  - "Has read access" is not "can measure." The done-when is not "the reviewer can open a file" — it is "the reviewer pulled a fact from the spine and cited it, with the query it used." A reviewer that quotes a README but cannot query the run record has not measured anything.
  - "Side by side" is not "reconciled." Concatenating two transcripts changes nothing. The reconciled artifact must contain per-lineage agreements, disagreements, and missed-items, each citing evidence, and reference raw findings by hash.
  - Independence means round-1 is frozen before cross-feed. Neither lineage sees the other's findings until both round-1 outputs exist. Otherwise "independent review" is two models reading each other's homework.
  - Provenance means the artifact binds findings to real reviewer sessions. If the harness fabricates both lineages' outputs, the missing session IDs and input hashes give it away. Do not let the harness generate the "review" itself and attribute it to a reviewer.
  - This card does NOT prevent writes. Do not claim it does. If a reviewer can still write after this card, that is expected and tracked separately — do not silently depend on write-blocking here, because it is not built yet.
