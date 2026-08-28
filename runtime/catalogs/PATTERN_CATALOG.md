# Pattern Catalog

Generated: 2026-08-28T01:10:14.600812+00:00

Ground truth re-checked live this run (read-only): six stat tuples and six md5sums match the spec's evidence table exactly; all six parent dirs carry the 2026-08-27 16:17:19 rebuild mtime; zero symlinks under each profile home; RESULTS/ holds exactly 6 files, long-form Menter report present (12463 bytes), target filename free.

PATTERN CATALOG

1. LANGUAGE AND TOOLCHAIN
Read-only POSIX shell evidence loops (stat -c "%i %h %s %y", md5sum, find -type l | wc -l) executed over the existing Python/bash pipeline substrate. No new runtime, no new dependencies, no new code — the deliverable is a markdown report, not software. Pitfall learned this run: stat -c takes the path as the file operand after the format string; embedding the path inside the format produces "stat: missing operand". Always format-then-operand, never path-inside-format.

2. ARCHITECTURAL PATTERNS
Evidence-backed write discipline: self-report is not truth; every claim in a RESULTS/ report must be a verbatim quote of live tool output re-gathered at write time. If fresh output differs from the spec's table, fresh values win. Verdict-first structure: CONFIRMED at the top, evidence table under it, honest nuance after that. Long-form proof + short confirmation split: the long Menter report is the underlying proof; the short report references it by filename and run ID and never duplicates its 209 lines. Per-role HERMES_HOME separation under /home/worker/.hermes-{role} is the thing being verified. READ_ONLY_STANDING_BY with a single explicitly directed exception. One deliverable per run; pre-existing RESULTS/ files are an immutable evidence archive.

3. CONVENTION RULES
Naming: lowercase, underscores, <topic>_<scope>_YYYYMMDD.md inside enforcement/mwl-proof-v2/RESULTS/. Header block: Run ID, Written date, scope line. Evidence as pipe-separated tables quoted verbatim from live output. Honest nuance is mandatory, not optional: the review1/menter/verify identical-bytes trio must be stated plainly (same size 48099, same md5 371ad49ae97f4384740e96cfb33d5019) with the separation-holds justification (distinct inodes, links=1), because content divergence is not Eric's criterion. Every report ends with a statement that it is the only write of its run. No new verification specs, no fix proposals, no governance language.

4. TEST CONVENTION
No unit tests exist or are needed. Verification is the test: the reviewers re-run the exact stat/md5/symlink loop and diff live output against the report's table character for character. File count check: RESULTS/ goes from 6 to 7 and nothing else changes (ls -la before/after identical apart from the one new file). A report whose table cannot be reproduced live is not done.

5. COMPLETION CRITERIA PER PATTERN (WHAT DONE LOOKS LIKE)
Evidence-loop pattern: six tuples quoted verbatim, one per role, each showing a distinct inode (13781319/13781391/13781541/13781616/13781463/13781687), links=1, size, and mtime. A missing tuple or an unquoted claim is not done.
Symlink pattern: count 0 quoted per profile home, all six, not a summary "none".
Rebuild-survival pattern: file mtimes 2026-08-26 (pre-rebuild) stated alongside the six parent-dir mtimes 2026-08-27 16:17:19 (rebuild), and the interpretation stated: dirs recreated, split files persisted.
Nuance pattern: the identical md5 trio named explicitly with the separate-file-object justification.
Cross-reference pattern: long-form filename and run ID (MENTER-PITFALLS-SEP-20260828T000331Z) cited in both the header scope line and the body.
Single-write pattern: exactly one new file created, zero modified, zero deleted; RESULTS/ count 6 to 7 verified by listing.

6. FILES MENTER WILL CREATE OR MODIFY
Create exactly one:
/workspace/cis/enforcement/mwl-proof-v2/RESULTS/pitfalls_separation_short_confirmation_20260828.md
Modify: none. Menter re-runs the one-line stat/md5 loop immediately before writing and quotes fresh output if it differs from the spec table.

Bias check: this is a one-file evidence write with shell checks — the anti-over-engineering pattern is the single-write discipline itself. No committees,No committees, no approval chains beyond the existing pipeline roles, no schema, no CI — none of that belongs in this run.

FINAL_JSON:
{"role":"brain","status":"READY","summary":"Pattern catalog for a single-file evidence write. Toolchain: read-only POSIX stat/md5sum/find loops, no new runtime. Ground truth re-checked live this run: six distinct inodes, links=1, zero symlinks, 2026-08-26 file mtimes under 2026-08-27 16:17:19 rebuild dir mtimes, RESULTS/ holds 6 files. Done = one new short confirmation report quoting live evidence verbatim, identical-content trio stated plainly, long-form proof cross-referenced, RESULTS/ 6 to 7, nothing else touched.","files_planned":["/workspace/cis/enforcement/mwl-proof-v2/RESULTS/pitfalls_separation_short_confirmation_20260828.md"]}