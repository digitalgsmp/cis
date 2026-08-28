# Pattern Catalog

Generated: 2026-08-28T18:12:02.399481+00:00

Ground truth re-verified live this run (read-only): all six inode/link tuples and md5s match the directive's evidence table exactly; zero symlinks; RESULTS/ inventory matches; target filename is collision-free. Catalog follows.

PATTERN CATALOG — Brain, run-e1e6daa1c63d (read-only; no writes this run)

1. LANGUAGE AND TOOLCHAIN
Python is the dominant language (3443 .py), with pipeline orchestration in tools/pipeline/ (Python + 33 bash .sh scripts). Markdown is the artifact format (2839 .md) — verification records, specs, and confirmations are all .md, never code. Evidence collection is done with coreutils (stat -c, md5sum, find), not custom tooling. The repo carries legacy noise (2316 .js, 756 .docx, 473 .map) but none of it is in the write path for this task.

2. ARCHITECTURAL PATTERNS FOUND
- Evidence-backed recording: every claim in a record is anchored to live filesystem output (inode, link count, hash) captured at write time — self-report is not truth. This is the governing pattern.
- Single-purpose artifact: one file per verification question; the question is "are the six pitfalls.md separate?" and the answer is one RESULTS/ file.
- Read-only standing by: observation runs (Brain/Drafter) verify and specify without modifying; only the Implementer creates, and only the one spec'd file.
- Collision-aware naming: new record names are chosen against the live RESULTS/ inventory, never assumed free.
- Two-fact honesty: records state both the favorable fact (6/6 separate files) and the caveat (3 of 6 byte-identical) rather than flattening to a yes.

3. CONVENTION RULES
- Naming: snake_case, descriptive, YYYYMMDD date suffix; sequence terms in name (third_confirmation, fourth_confirmation) not "final" — "final" asserts future state that cannot be verified.
- File org: verification evidence lives in enforcement/mwl-proof-v2/RESULTS/; per-agent material lives under enforcement/mwl-proof-v2/cis-skills-per-role/<agent>/references/pitfalls.md. Agent names follow the directories: brain, draft, review1, review2, menter, verify (menter = Implementer).
- Error handling pattern: verify before write — confirm the target path does not exist and that recorded hashes match a fresh run before creating.
- Ownership: records are worker-owned regular files (0644/0600 per prior siblings), matching existing RESULTS/ entries.

4. TEST CONVENTION
There is no unit-test layer for records; the RESULTS/ files themselves are the tests. Proof files (build_proof_20260703.txt, run_v6.txt, run_v7.txt, standing_container_block_proof.txt) demonstrate the convention: raw command output preserved as evidence. Verification = stat/md5sum re-run at implementation time and compared against the values inside the record.

5. COMPLETION CRITERIA PER PATTERN
- Evidence-backed recording — done when: file contains command provenance, a per-agent table (agent, relative path, present, inode, md5-prefix), and both facts stated without flattening.
- Single-purpose artifact — done when: exactly one new file exists and nothing else changed (no edits to pitfalls.md, SKILL.md, code, gates, or the three prior confirmations).
- Collision-aware naming — done when: stat of the new path returns a regular file, links=1, and no pre-existing RESULTS/ entry shares the name.
- Two-fact honesty — done when: the record says 6/6 separate files AND 4/6 unique content, naming review1/menter/verify as currently byte-identical (371ad49a...).
- Prior-record + repetition note — done when: the three existing confirmations are listed, this file identified as fourth, and the repetition pattern (fourth identical request in ~1 day, the Phase 0 loop-breaker signature) recorded as an observation, not acted on.

6. FILES MENTER WILL CREATE OR MODIFY
Create (exactly one):
- /workspace/cis/enforcement/mwl-proof-v2/RESULTS/pitfalls_separation_fourth_confirmation_20260828.md

Modify: none. Deletion, code, gate, and pipeline changes are all out of scope.

Flags: no enterprise drift — no governance, no committees, no pipeline over-engineering; this is a pure evidence artifact. The only pattern worth watching is the repetition itself: three prior confirmations exist (post_rebuild_verification_20260827, short_confirmation_20260828 01:11, third_confirmation_20260828 14:35) and the two most recent pipeline runs reached CONSENSUS_REACHED with 0 rounds on the identical topic. Fourth occurrence in one day. If it recurs again, the loop-breaker observation should escalate — but for this run the scope stays strictly one file.

FINAL_JSON
{"role":"brain","status":"READY","summary":"Pattern catalog for the fourth pitfall-separation confirmation. Ground truth re-verified live (read-only): 6/6 agents have separate references/pitfalls.md (six distinct inodes 12061253/12061312/12061515/12061386/12061455/12061672, links=1, zero symlinks); 4/6 unique md5s with review1/menter/verify byte-identical (371ad49a). Governing patterns: evidence-backed recording (hashes/inodes over bare yes), single-purpose artifact (one file, nothing else), collision-aware naming, two-fact honesty. Completion criteria: new file exists with per-agent table, both facts, prior-record list, and repetition observation; nothing else changed. Menter creates exactly one file; zero modifications.","files_planned":["/workspace/cis/enforcement/mwl-proof-v2/RESULTS/pitfalls_separation_fourth_confirmation_20260828.md"]}