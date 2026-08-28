# Post-Rebuild Per-Profile pitfalls.md Separation Verification

## a. Header

- Run ID: MENTER-PITFALLS-SEP-20260828T000331Z
- Run timestamp (UTC): 2026-08-28T00:03:31Z
- Role performing verification: Menter (Implementer)
- Spec reference: Zero-build post-rebuild verification spec, drafted 2026-08-27 — confirm the 2026-08-26 per-profile skill split survived the 2026-08-27 container rebuild. Deliverable is this report. Change nothing.
- Read-only discipline: every command in this run was read-only (test, stat, find, md5sum, grep -c, mount, ls). The only write in the entire task is this report file. No live-file mtime is newer than the rebuild directory mtime 2026-08-27 16:17:19 UTC (see CHK mtime guard below) — evidence that nothing under the profile homes or repo masters was modified by this verification.

## b. Evidence Table (regenerated from fresh tool output, run 2026-08-28T00:03:31Z)

role    | live inode | links | bytes | pitfalls.md md5 (live)                 | file mtime (UTC)
--------|------------|-------|-------|-----------------------------------------|------------------------------
brain   | 13781319   | 1     | 49927 | 4402048502571f657727192e5cfe4b8c        | 2026-08-26 00:27:15
draft   | 13781391   | 1     | 48112 | 202a0511c99755acfd1f88db5dc76b53        | 2026-08-26 00:01:49
review1 | 13781541   | 1     | 48099 | 371ad49ae97f4384740e96cfb33d5019        | 2026-08-26 00:06:55
review2 | 13781616   | 1     | 50709 | f2b6b9902b55c09b0c1a455b2f7bbd2d        | 2026-08-26 00:27:35
menter  | 13781463   | 1     | 48099 | 371ad49ae97f4384740e96cfb33d5019        | 2026-08-26 00:06:55
verify  | 13781687   | 1     | 48099 | 371ad49ae97f4384740e96cfb33d5019        | 2026-08-26 00:06:55

All six parent skill directories carry mtime 2026-08-27 16:17:19.000000000 +0000 (the rebuild recreated the directories); all six pitfalls.md files carry 2026-08-26 mtimes (contents persisted through the rebuild). That is the "survived" claim, confirmed live.

## c. Per-Check Results

### CHK-1 — Presence: PASS

Command:

    for r in brain draft review1 review2 menter verify; do
      test -f /home/worker/.hermes-$r/skills/software-development/cis-pipeline-architecture/references/pitfalls.md \
        && echo "$r true" || echo "$r FALSE"
    done

Fresh output:

    brain true
    draft true
    review1 true
    review2 true
    menter true
    verify true

All six return true.

### CHK-2 — No Sharing: PASS

Commands:

    stat -c '%i %h %n' /home/worker/.hermes-$r/skills/software-development/cis-pipeline-architecture/references/pitfalls.md   (per role)
    find /home/worker/.hermes-$r/skills -type l                                                                             (per role)

Fresh output (stat):

    13781319 1 /home/worker/.hermes-brain/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    13781391 1 /home/worker/.hermes-draft/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    13781541 1 /home/worker/.hermes-review1/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    13781616 1 /home/worker/.hermes-review2/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    13781463 1 /home/worker/.hermes-menter/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    13781687 1 /home/worker/.hermes-verify/skills/software-development/cis-pipeline-architecture/references/pitfalls.md

Fresh output (symlink scan, one line per role, empty expected):

    [brain]
    [draft]
    [review1]
    [review2]
    [menter]
    [verify]

Six distinct inodes, hardlink count 1 each, zero symlinks. No two profiles share a file object.

### CHK-3 — No Content Drift (pitfalls.md): PASS

Command (per role):

    md5sum /home/worker/.hermes-$r/skills/software-development/cis-pipeline-architecture/references/pitfalls.md \
           /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/$r/references/pitfalls.md

Fresh output:

    [brain]
    4402048502571f657727192e5cfe4b8c  /home/worker/.hermes-brain/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    4402048502571f657727192e5cfe4b8c  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/brain/references/pitfalls.md
    [draft]
    202a0511c99755acfd1f88db5dc76b53  /home/worker/.hermes-draft/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    202a0511c99755acfd1f88db5dc76b53  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/draft/references/pitfalls.md
    [review1]
    371ad49ae97f4384740e96cfb33d5019  /home/worker/.hermes-review1/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    371ad49ae97f4384740e96cfb33d5019  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/review1/references/pitfalls.md
    [review2]
    f2b6b9902b55c09b0c1a455b2f7bbd2d  /home/worker/.hermes-review2/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    f2b6b9902b55c09b0c1a455b2f7bbd2d  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/review2/references/pitfalls.md
    [menter]
    371ad49ae97f4384740e96cfb33d5019  /home/worker/.hermes-menter/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    371ad49ae97f4384740e96cfb33d5019  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/menter/references/pitfalls.md
    [verify]
    371ad49ae97f4384740e96cfb33d5019  /home/worker/.hermes-verify/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    371ad49ae97f4384740e96cfb33d5019  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/verify/references/pitfalls.md

All six live files md5-match their per-role repo masters.

### CHK-4 — Post-Split SKILL.md, Not Stale Copy: PASS

Command (per role):

    md5sum /home/worker/.hermes-$r/skills/software-development/cis-pipeline-architecture/SKILL.md \
           /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/$r/SKILL.md

Fresh output:

    [brain]
    3b6eb4d2d1f47542d1c289c6d20bb820  /home/worker/.hermes-brain/skills/software-development/cis-pipeline-architecture/SKILL.md
    3b6eb4d2d1f47542d1c289c6d20bb820  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/brain/SKILL.md
    [draft]
    499fc4950a3a4b83d101925451732891  /home/worker/.hermes-draft/skills/software-development/cis-pipeline-architecture/SKILL.md
    499fc4950a3a4b83d101925451732891  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/draft/SKILL.md
    [review1]
    eb1e99edd4f933f907acd723aed0e4af  /home/worker/.hermes-review1/skills/software-development/cis-pipeline-architecture/SKILL.md
    eb1e99edd4f933f907acd723aed0e4af  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/review1/SKILL.md
    [review2]
    00b6cf3568eeb80a241b94da19182568  /home/worker/.hermes-review2/skills/software-development/cis-pipeline-architecture/SKILL.md
    00b6cf3568eeb80a241b94da19182568  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/review2/SKILL.md
    [menter]
    22e5aa436457e335df4fbbfcb88c0b00  /home/worker/.hermes-menter/skills/software-development/cis-pipeline-architecture/SKILL.md
    22e5aa436457e335df4fbbfcb88c0b00  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/menter/SKILL.md
    [verify]
    02131c42d3d149d487a5f34870dfd122  /home/worker/.hermes-verify/skills/software-development/cis-pipeline-architecture/SKILL.md
    02131c42d3d149d487a5f34870dfd122  /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/verify/SKILL.md

All six live SKILL.md files md5-match their per-role masters, and the six md5s are pairwise distinct (per-role tailoring exists at the SKILL.md level). No live file matches the stale 437-line pre-split copy at /workspace/cis/enforcement/mwl-proof-v2/cis-pipeline-architecture/SKILL.md — the stale copy was not re-seeded.

### CHK-5 — Pointer Line Present: PASS

Command (per role):

    grep -c "See references/pitfalls.md" /home/worker/.hermes-$r/skills/software-development/cis-pipeline-architecture/SKILL.md

Fresh output:

    brain: 1
    draft: 1
    review1: 1
    review2: 1
    menter: 1
    verify: 1

Count >= 1 for all six.

### CHK-6 — No Mounts Under Profile Homes: PASS

Command:

    mount | grep '/home/worker/.hermes'

Fresh output (empty; no lines between the command and the exit-code echo):

    grep exit code: 1

Exit code 1 = grep found zero matches. No bind mounts under any profile home.

### Mtime Guard (read-only discipline proof)

Command (per role):

    stat -c '%y %n' .../references/pitfalls.md ; stat -c '%y %n' .../SKILL.md ; stat -c '%y %n' .../cis-pipeline-architecture

Fresh output (pitfalls.md):

    2026-08-26 00:27:15.000000000 +0000 /home/worker/.hermes-brain/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    2026-08-26 00:01:49.000000000 +0000 /home/worker/.hermes-draft/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    2026-08-26 00:06:55.000000000 +0000 /home/worker/.hermes-review1/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    2026-08-26 00:27:35.000000000 +0000 /home/worker/.hermes-review2/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    2026-08-26 00:06:55.000000000 +0000 /home/worker/.hermes-menter/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
    2026-08-26 00:06:55.000000000 +0000 /home/worker/.hermes-verify/skills/software-development/cis-pipeline-architecture/references/pitfalls.md

Fresh output (SKILL.md):

    2026-08-26 00:22:21.000000000 +0000 /home/worker/.hermes-brain/skills/software-development/cis-pipeline-architecture/SKILL.md
    2026-08-25 23:42:32.000000000 +0000 /home/worker/.hermes-draft/skills/software-development/cis-pipeline-architecture/SKILL.md
    2026-08-26 00:06:55.000000000 +0000 /home/worker/.hermes-review1/skills/software-development/cis-pipeline-architecture/SKILL.md
    2026-08-26 00:27:30.000000000 +0000 /home/worker/.hermes-review2/skills/software-development/cis-pipeline-architecture/SKILL.md
    2026-08-26 00:06:55.000000000 +0000 /home/worker/.hermes-menter/skills/software-development/cis-pipeline-architecture/SKILL.md
    2026-08-26 00:06:55.000000000 +0000 /home/worker/.hermes-verify/skills/software-development/cis-pipeline-architecture/SKILL.md

Fresh output (parent skill dirs):

    2026-08-27 16:17:19.000000000 +0000 /home/worker/.hermes-brain/skills/software-development/cis-pipeline-architecture
    2026-08-27 16:17:19.000000000 +0000 /home/worker/.hermes-draft/skills/software-development/cis-pipeline-architecture
    2026-08-27 16:17:19.000000000 +0000 /home/worker/.hermes-review1/skills/software-development/cis-pipeline-architecture
    2026-08-27 16:17:19.000000000 +0000 /home/worker/.hermes-review2/skills/software-development/cis-pipeline-architecture
    2026-08-27 16:17:19.000000000 +0000 /home/worker/.hermes-menter/skills/software-development/cis-pipeline-architecture
    2026-08-27 16:17:19.000000000 +0000 /home/worker/.hermes-verify/skills/software-development/cis-pipeline-architecture

No live file mtime is newer than 2026-08-27 16:17:19 UTC. The verification modified nothing.

## d. Nuance Statement

Nuance clause (accepted by design, not a failure): review1, menter, verify pitfalls.md are byte-identical (md5 371ad49ae97f4384740e96cfb33d5019) but are three separate file objects. The split's documented purpose (skill-split-per-profile.md) was independent write targets to fix write contention, not differentiated content; role tailoring for those three lives in sibling reference files (review1: adversarial-review-methodology.md, git-snapshot-isolation-gap.md, l1_verification_snapshots.md; menter: menter-chunk-verification.md, zero-token-verification.md; verify: verify_scope_violation_detection.md). Report as NUANCE, not FAIL.

## e. Residual Risk Statement

R1. Future rebuilds could regress the split if skill seeding switches to the stale repo copy at enforcement/mwl-proof-v2/cis-pipeline-architecture/. The seeding step in run_container.sh is the thing to watch. Pre-existing, documented in skill-split-per-profile.md pitfall #1.

R2. review1/menter/verify pitfalls.md content convergence is intentional; anyone auditing for "differentiated content per role" must read the nuance clause first.

## f. Final Verdict

SPLIT SURVIVED REBUILD: PASS
