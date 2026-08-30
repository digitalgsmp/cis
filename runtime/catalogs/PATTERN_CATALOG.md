# Pattern Catalog

Generated: 2026-08-30T17:39:38.506402+00:00

PATTERN CATALOG — Brain, relay FTS5 slash-sanitization record (run-e70293544935a92e-1787973534)

PRIORITY FLAG — GROUND TRUTH DRIFTED SINCE THE DIRECTIVE WAS FROZEN
The directive's evidence (live file 3745 lines; two sanitizer sites at 644 and 1094; comments at 638-641 and 1087-1090) was true at draft time but is STALE now. Re-verified read-only this run:
- Live /workspace/cis/runtime/abstraction/pipeline_relay.py is now 3895 lines (171313 bytes, mtime 2026-08-30 15:50:44 UTC), clean working tree, HEAD is 3895 lines. Four commits touched it today (c7151f8, d00a964, fe8f843, 3b9a0bb).
- The two sanitizer sites were consolidated into exactly ONE: line 273, re.sub(r"[^A-Za-z0-9_ ]", " ", text). grep of "A-Za-z0-9_" in the live file = 1 match (line 273); grep of "re.sub" = 1 match; no second site under any spelling.
- The fix-documenting comment now sits at lines 260-263 (docstring of the consolidated tokenizer): the old sanitizer missed "/", so path-named intents raised 'fts5: syntax error near "/"' and were reported as "(KB search unavailable)" for 99 calls.
- The .bak.20260827 backup is unchanged: 3577 lines, mtime 2026-08-27 14:16 UTC, old slash-omitting blacklist at 588 and 1024, zero occurrences of the fix class.

ANSWER TO ERIC'S QUESTION IS UNCHANGED: NO. The live module does not sanitize with a slash-omitting class; the single live site uses the negated class that catches "/". Only the citation evidence changed. The spec's Section 3 template would write FALSE line numbers into the results file if used verbatim — Menter must record the current truth below, not the stale template.

1. LANGUAGE AND TOOLCHAIN
- Python is the dominant language (3455 .py); orchestration lives in tools/pipeline/ (Python + bash, 33 .sh).
- Markdown is the artifact format (2845 .md). This delta touches zero code — one markdown record.
- No build, no tests, no toolchain surface. Any CI/gatework would be over-engineering drift; reject it.

2. ARCHITECTURAL PATTERNS FOUND
- Evidence-over-assertion recording: every RESULTS/ artifact records raw evidence (line numbers, hashes, inodes, mtimes), never bare self-report. This file must carry line citations.
- Read-only verification before write: brain/draft inspect, menter creates, verifier compares hashes/mtimes. Ground truth is re-verified fresh at every phase, never inherited on faith — this run's drift proves why.
- Dated snapshot discipline: pre-change backups as .bak.YYYYMMDD (pipeline_relay.py.bak.20260827, several *.bak.20260830_pre_* files). The .bak is a frozen historical record, never the live module.
- Append-only proof ledger: RESULTS/ is a growing archive of one-question-per-file records (9 files today); existing files are never rewritten.
- Fast-mutating live code: pipeline_relay.py received 4 commits today. Any record that cites line numbers must cite the CURRENT file at implement time, or it records a falsehood.

3. CONVENTION RULES
- Naming: RESULTS/ files use snake_case + _YYYYMMDD suffix (pitfalls_separation_short_confirmation_20260828.md). This file: relay_fts5_slash_sanitization_20260830.md (implement-time UTC date; today is 20260830, so the stale template's 0829 is wrong).
- File organization: single flat RESULTS/ directory, one file per verified question, no subdirectories.
- Error-handling/hygiene: exactly one create; never edit the live module or any .bak while recording; no git commit, no symlinks, no directory changes; file content states answer first, evidence second.
- Date rule: if creation lands on a different UTC date, use that date; format stays relay_fts5_slash_sanitization_YYYYMMDD.md.

4. TEST CONVENTION
- No test files for a recording artifact; the verifier pass IS the test: content contains answer NO, current line citations (273, 260-263, 3895; bak 588, 1024, 3577), and RESULTS/ goes 9 to 10 files with zero other delta.
- Pre-existing 9 files proven untouched via before/after inode + mtime + md5sum comparison; live module and .bak hashes unchanged.
- Raw evidence (ls -i, md5sum) reported in closeout; assertion without evidence fails.

5. COMPLETION CRITERIA (WHAT DONE LOOKS LIKE)
- Exactly one new regular file at /workspace/cis/enforcement/mwl-proof-v2/RESULTS/relay_fts5_slash_sanitization_20260830.md.
- Content records: answer NO; live site line 273 on r"[^A-Za-z0-9_ ]" (negated class catches "/"); comment at 260-263; live file 3895 lines; old blacklist r'[."*(){}:^+\-]' only in .bak.20260827 at 588 and 1024 (3577 lines, not live).
- The stale spec template (644/1094/3745/two-sites) must NOT be written — it would embed false evidence.
- RESULTS/ count 9 to 10 with no other delta; live module and .bak mtimes/hashes unchanged; verifier closeout carries ls -i and md5sum output.

6. FILES MENTER WILL CREATE OR MODIFY
- CREATE: /workspace/cis/enforcement/mwl-proof-v2/RESULTS/relay_fts5_slash_sanitization_20260830.md (date adjusted only if UTC date differs at implement time)
- MODIFY: none — no edits to pipeline_relay.py, the .bak, or any existing RESULTS/ file.

PRIOR DISPOSITIONS CHECK: the "fts5" disposition ruled on eric_catalog_fts table DDL (a different question) and the "write" disposition ruled write authority lives at the application layer — neither is contradicted here; this record is a read-only-evidence artifact and the answer stays NO. No governance machinery is warranted; the single-delta contract already covers it.

FINAL_JSON:
{"role":"brain","status":"READY","summary":"Pattern catalog with one critical correction: the directive's line evidence is stale. Live pipeline_relay.py was refactored today (committed; 3895 lines vs 3745 recorded) and now has exactly ONE FTS5 sanitizer site at line 273, not two at 644/1094. Site 273 uses the negated class r'[^A-Za-z0-9_ ]' which catches '/', so the answer to Eric's question remains NO. Fix comment now at 260-263 (mentions the old class missed '/' and 99 '(KB search unavailable)' calls). The slash-omitting blacklist survives only in .bak.20260827 (3577 lines) at 588 and 1024. RESULTS/ holds 9 files with zero relay/fts5 coverage; today is 20260830. Menter must create exactly one file, relay_fts5_slash_sanitization_20260830.md, citing the CURRENT evidence (273, 260-263, 3895; bak 588, 1024), NOT the stale template's 644/1094/3745. No edits to live module or .bak; verifier must show 9-to-10 file delta with inode/mtime/hash proof.","files_planned":["/workspace/cis/enforcement/mwl-proof-v2/RESULTS/relay_fts5_slash_sanitization_20260830.md"]}