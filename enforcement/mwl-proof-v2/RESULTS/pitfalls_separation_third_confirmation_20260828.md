# Pitfalls.md Per-Role Separation — Third Confirmation Report

**Filename:** pitfalls_separation_third_confirmation_20260828.md
**Generated:** 2026-08-28 (UTC), 14:34Z
**Purpose:** Third confirmation that each of the six pipeline agents has its own separate references/pitfalls.md.
**Authorship:** This file was created by the Implementer per Drafter spec, not by the Brain.
**Write guard:** `test -e` on the target filename returned ABSENT — no collision, no -HHMMSS fallback applied. Final filename used as specified.
**Long-form proof:** pitfalls_separation_post_rebuild_verification_20260827.md

## Verdict

**PASS** — 6 of 6 roles have separate pitfalls.md in repo masters; 6 of 6 in live profile homes. Six distinct inodes per location, hardlink count 1 on every file, live-home md5 matches repo-master md5 per role, zero symlinks under any profile home. No drift from the spec's expected table: no DRIFT section required.

## Repo Masters (all regular files, links=1, distinct inodes)

| role    | path                                                                 | inode     | links | size  | md5                              |
|---------|----------------------------------------------------------------------|-----------|-------|-------|----------------------------------|
| brain   | /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/brain/references/pitfalls.md   | 12061253  | 1     | 49927 | 4402048502571f657727192e5cfe4b8c |
| draft   | /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/draft/references/pitfalls.md   | 12061312  | 1     | 48112 | 202a0511c99755acfd1f88db5dc76b53 |
| review1 | /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/review1/references/pitfalls.md | 12061386  | 1     | 48099 | 371ad49ae97f4384740e96cfb33d5019 |
| review2 | /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/review2/references/pitfalls.md | 12061455  | 1     | 50709 | f2b6b9902b55c09b0c1a455b2f7bbd2d |
| menter  | /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/menter/references/pitfalls.md  | 12061515  | 1     | 48099 | 371ad49ae97f4384740e96cfb33d5019 |
| verify  | /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/verify/references/pitfalls.md  | 12061672  | 1     | 48099 | 371ad49ae97f4384740e96cfb33d5019 |

Six distinct inodes: 12061253, 12061312, 12061386, 12061455, 12061515, 12061672.

## Live Profile Homes (same md5 per role, links=1, distinct inodes)

Path template: /home/worker/.hermes-&lt;role&gt;/skills/software-development/cis-pipeline-architecture/references/pitfalls.md

| role    | inode     | links | size  | md5                              | matches_repo_master |
|---------|-----------|-------|-------|----------------------------------|---------------------|
| brain   | 13790927  | 1     | 49927 | 4402048502571f657727192e5cfe4b8c | yes                 |
| draft   | 13790999  | 1     | 48112 | 202a0511c99755acfd1f88db5dc76b53 | yes                 |
| review1 | 13791149  | 1     | 48099 | 371ad49ae97f4384740e96cfb33d5019 | yes                 |
| review2 | 13791224  | 1     | 50709 | f2b6b9902b55c09b0c1a455b2f7bbd2d | yes                 |
| menter  | 13791071  | 1     | 48099 | 371ad49ae97f4384740e96cfb33d5019 | yes                 |
| verify  | 13791295  | 1     | 48099 | 371ad49ae97f4384740e96cfb33d5019 | yes                 |

Six distinct inodes: 13790927, 13790999, 13791149, 13791224, 13791071, 13791295. All six live-home md5s match their repo-master counterparts.

## Symlink Scan

`find /home/worker/.hermes-brain /home/worker/.hermes-draft /home/worker/.hermes-review1 /home/worker/.hermes-review2 /home/worker/.hermes-menter /home/worker/.hermes-verify -type l | wc -l`

Result: **0** — expected 0. No symlinks under any of the six profile homes.

## Nuance Clause (prior-ruled)

review1, menter, and verify pitfalls.md are byte-identical (md5 371ad49ae97f4384740e96cfb33d5019) but are three separate file objects with distinct inodes and link count 1. This is **NUANCE, not FAIL**: the documented purpose of the split (cis-skills-per-role / skill-split-per-profile.md) is independent write targets to fix write contention, not content divergence.

## Untouched Priors

The 7 pre-existing RESULTS/ files, with mtimes recorded before this write:

| file                                                    | before mtime (UTC)         | epoch before |
|---------------------------------------------------------|----------------------------|--------------|
| build_proof_20260703.txt                                | 2026-07-03 04:41:08        | 1783053668   |
| pitfalls_separation_post_rebuild_verification_20260827.md | 2026-08-28 00:05:24      | 1787875524   |
| pitfalls_separation_short_confirmation_20260828.md      | 2026-08-28 01:11:00        | 1787879460   |
| run_v6.txt                                              | 2026-07-01 12:35:47        | 1782909347   |
| run_v7.txt                                              | 2026-07-01 12:35:47        | 1782909347   |
| shellhook_seen.log                                      | 2026-07-01 12:35:47        | 1782909347   |
| standing_container_block_proof.txt                      | 2026-07-01 12:35:47        | 1782909347   |

After the write (2026-08-28 14:35 UTC), all seven files were re-statted. After-mtimes: build_proof_20260703.txt 1783053668, pitfalls_separation_post_rebuild_verification_20260827.md 1787875524, pitfalls_separation_short_confirmation_20260828.md 1787879460, run_v6.txt 1782909347, run_v7.txt 1782909347, shellhook_seen.log 1782909347, standing_container_block_proof.txt 1782909347.

**Assertion result: PASS — every after-mtime is identical to its before-mtime; none of the 7 pre-existing RESULTS files was modified.**

## Command Appendix (exact read-only commands run at write time)

```
test -e /workspace/cis/enforcement/mwl-proof-v2/RESULTS/pitfalls_separation_third_confirmation_20260828.md && echo EXISTS
stat -c '%i %h %s' /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/{brain,draft,review1,review2,menter,verify}/references/pitfalls.md
md5sum /workspace/cis/enforcement/mwl-proof-v2/cis-skills-per-role/{brain,draft,review1,review2,menter,verify}/references/pitfalls.md
stat -c '%i %h %s' /home/worker/.hermes-{brain,draft,review1,review2,menter,verify}/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
md5sum /home/worker/.hermes-{brain,draft,review1,review2,menter,verify}/skills/software-development/cis-pipeline-architecture/references/pitfalls.md
find /home/worker/.hermes-brain /home/worker/.hermes-draft /home/worker/.hermes-review1 /home/worker/.hermes-review2 /home/worker/.hermes-menter /home/worker/.hermes-verify -type l | wc -l
stat -c '%Y %y %n' <each of the 7 pre-existing RESULTS files>   (before the write, and re-run after the write)
```

All evidence values above were gathered by re-running these commands at write time; none were copied from the spec.
