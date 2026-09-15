CARD_ID: CARD-reviewer-isolation
VERSION: 1.0
CANONICAL_TOKEN: RI-V1-20260910-A
STATUS: DRAFT_FOR_ADVERSARIAL_REVIEW
DEPENDS_ON: Architecture of contained CIS pipeline; intended companion to CARD-reviewer-measurement
SCOPE_LOCK: REVIEWER NON-MUTATION / PROCESS-BOUNDARY ISOLATION ONLY

# CARD-reviewer-isolation
Separate reviewer roles from mutator roles at the process/filesystem boundary so reviewers can observe but cannot change the protected system.

## PROBLEM
The contained pipeline currently places multiple roles in a shared container/workspace context. A reviewer-specific "cannot write" guarantee cannot be made trustworthy only by prompt instructions or by enumerating forbidden commands. The reviewer boundary must be enforced below the model/tool prompt layer.

## BUILD
Create a reviewer execution boundary for BOTH advisor (GLM lineage) and evaluator (Qwen lineage) that is separate from builder/mutator execution.

Required properties:
- Protected CIS workspace is mounted/readable to reviewers but not writable by the reviewer execution identity.
- Reviewer execution identity is non-root.
- Reviewer roles do not receive a writable bind/mount to the protected workspace, spine storage, queue/job registry, or protected artifact store.
- Reviewer tool/process context cannot directly dispatch/start a pipeline job.
- Arbitrary reviewer-originated network egress is denied at the container/process boundary. If model transport requires network connectivity, that exception must be explicit, minimal, and must not expose a general-purpose reviewer egress path.
- Review output persistence is performed by the harness outside the reviewer identity.
- Builder/mutator roles retain only the permissions they actually require; reviewer isolation must not silently turn the whole pipeline read-only.

Implementation mechanism is not prescribed by this card beyond the required boundary. The implementer must use the actual contained-pipeline architecture and prove the effective runtime permissions.

## DONE WHEN
1. FILESYSTEM BOUNDARY
   - In the actual reviewer execution context, the protected workspace is effectively read-only.
   - Create, modify, rename, and delete attempts against protected paths fail because of OS/container permissions, not because the model politely refuses.
   - The reviewer has no alternate writable mount/path that reaches the same protected state.

2. NON-ROOT
   - Advisor and evaluator execute under a non-root identity.
   - The reviewer identity cannot remount or change the protected mount permissions.

3. DISPATCH BOUNDARY
   - A reviewer-originated attempt to create/dispatch a pipeline run does not create a run, queue entry, job, or equivalent side effect.

4. NETWORK BOUNDARY
   - Reviewer-originated arbitrary external network access is unavailable.
   - Any network exception required solely for model transport is explicitly enumerated and cannot be repurposed as a general reviewer tool/command egress path.

5. OUTPUT OWNERSHIP
   - The reviewer cannot directly persist its own final findings into protected project storage.
   - The harness captures reviewer output and writes the review artifact using the harness identity, with provenance.

6. BOTH ROLES
   - Every isolation probe is run against advisor AND evaluator.

7. MUTATOR SEPARATION
   - The builder/implementer path remains operational in its separate mutator context.
   - No reviewer shares the builder's writable filesystem identity or writable protected-workspace mount.

## EVIDENCE
Produce a repeatable evidence report for BOTH reviewer roles.

Runtime identity/mount evidence:
- reviewer process/container identity and UID/GID
- effective mount information for protected CIS workspace and other protected state
- proof that protected mounts are read-only for the reviewer context

Negative filesystem probes:
- attempt create file in protected workspace -> OS/container denial
- attempt modify existing protected file -> OS/container denial
- attempt rename protected file -> OS/container denial
- attempt delete protected file -> OS/container denial
- protected-state hash/manifest unchanged after the probes

Dispatch probe:
- reviewer-originated dispatch/start attempt -> denied
- prove no new run ID, queue entry, job, or dispatch artifact was created

Network probe:
- attempt arbitrary external network access from reviewer execution context -> denied
- record the effective network policy/allowed exception set, if any

Harness-output probe:
- reviewer returns a known finding
- persisted review artifact is written by the harness identity
- provenance binds artifact to reviewer session/input/output hashes
- direct reviewer write to the protected artifact destination fails

Separation probe:
- builder/mutator can still perform an authorized write in its own execution context
- the same protected path remains non-writable from advisor and evaluator contexts

Pass condition:
- Every isolation test passes for BOTH reviewers.
- A model statement such as "I cannot write" is not evidence.
- An application-level hook denial alone is not evidence of the filesystem isolation required by this card.

## NOT IN THIS CARD
This card does not add reviewer measurement instruments, cross-feed, reconciliation logic, or reviewer reasoning prompts. Those are defined by CARD-reviewer-measurement.

This card also does not implement the later global blocking gate for all development stages. It establishes the reviewer process boundary needed for trustworthy reviewer verification.

## CLARITY FOR THE IMPLEMENTER
- Do not solve this with a longer blacklist of shell commands.
- Do not claim "read-only" from profile text or tool descriptions. Prove effective runtime permissions.
- The reviewer must have eyes without inheriting the builder's hands.
- Keep reviewer output persistence outside the reviewer execution identity.
- Any necessary model-transport exception must be narrow and explicit; do not turn it into a generic egress capability.
