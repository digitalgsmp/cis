# Skill Split Per-Profile (2026-08-26)

## What the split is

The CIS pipeline's shared skills (cis-pipeline-architecture, cis-soul) are split across six per-role Hermes homes, one per gateway profile:

| Role | HERMES_HOME |
|------|-------------|
| Brain | /home/worker/.hermes-brain |
| Draft | /home/worker/.hermes-draft |
| Review1 | /home/worker/.hermes-review1 |
| Review2 | /home/worker/.hermes-review2 |
| Menter | /home/worker/.hermes-menter |
| Verify | /home/worker/.hermes-verify |

Routing mechanism: `launch_profiles.sh` line 28 — `HERMES_HOME=/home/worker/.hermes-$profile`. Each gateway process gets a distinct HERMES_HOME even though ALL six run as user `worker` with identical `HOME=/home/worker`.

Each home has its own copy at `skills/software-development/cis-pipeline-architecture/` containing SKILL.md plus `references/pitfalls.md`. The split removed the long inline Pitfalls section from the old 437-line/100KB SKILL.md; live SKILL.md files are ~377 lines/53KB ending with the pointer "See references/pitfalls.md for the full list. Append new pitfalls THERE, not here." Each pitfalls.md (~68-70 lines) starts with "Append new pitfalls to THIS file, not to SKILL.md."

Reason for the split: six concurrent gateways appending pitfalls to one shared file = write contention. Each agent now records its own pitfalls independently.

Backups of the pre-split files: `enforcement/mwl-proof-v2/skill-backups-20260825/SKILL.<role>.bak` (mode 600, ~100KB each). Split rewrite timestamped 2026-08-26 00:06, backups 00:09.

## Verification procedure (proven this session)

To confirm "each agent can write to its references/pitfalls.md":

1. `ps aux | grep 'hermes gateway'` → get the 6 gateway PIDs.
2. `tr '\0' '\n' < /proc/<pid>/environ | grep HERMES_HOME` → prove each PID maps to its own home. NOTE: `HOME` is identical for all six; only `HERMES_HOME` disambiguates. Checking HOME alone proves nothing.
3. `find / -name pitfalls.md -not -path '*/proc/*'` → locate all six copies.
4. `stat -c '%i %U %a %n'` on each → inodes MUST be distinct (no hardlink/symlink sharing; a hardlink would mean "independent" files silently share content). Ownership should be worker:worker.
5. Writability: `[ -w <file> ]` as worker (access() check, no modification). A real round-trip (append + revert) is stronger but only when NOT under READ_ONLY_STANDING_BY.

## Pitfalls and maintenance implications

1. **Repo baked copy regresses the split on image rebuild.** `enforcement/mwl-proof-v2/cis-pipeline-architecture/SKILL.md` is still the OLD 437-line pre-split version (inline pitfalls). The split lives only in the six live homes. If the Docker image is rebuilt and skills are re-seeded from the repo, the split is undone. Verify seeding behavior in run_container.sh before rebuilding.
2. **Updates must be propagated to all six homes manually.** There is no sync mechanism. Patching one home's SKILL.md (e.g. via skill_manage from the Brain session) updates ONLY /home/worker/.hermes-brain. The other five copies drift. A skill update affecting all agents must be applied six times (or centralized, which defeats the split).
3. **Role copies are intentionally NOT byte-identical.** Draft carries extra spec-review-checklist references; line counts differ slightly (374-379). Do not "fix" these divergences — they are role tailoring.
4. Draft's pitfalls.md has a duplicated "## Pitfalls" header (70 vs 68 lines) — cosmetic, harmless.
