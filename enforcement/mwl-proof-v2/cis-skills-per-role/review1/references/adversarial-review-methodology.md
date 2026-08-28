# Adversarial Review Methodology (Reviewer 1 Role)

## When to Use

This is the Reviewer 1 playbook for CIS pipeline runs. Applies whenever you're reviewing a draft spec or proposal against the live codebase. The goal: verify every claim independently, flag assumptions, and prevent fabrications from propagating to the implementer.

## Core Principle

Self-report is not truth. Evidence-backed response rule: every claim needs raw evidence. False consensus is worse than disagreement.

## Workflow

### 1. Enumerate All Draft Claims

Extract every factual claim from the draft: line numbers, function signatures, variable names, code behavior, DB schema details, import statements, call sites. Each becomes a row in the verification table.

### 2. Independently Verify Each Claim

Run a command that would confirm or refute the claim. Use `grep -n`, `sed -n 'START,ENDp'`, or `wc -l`. Record the exact output.

### 3. Build the Verification Table

Format:

| # | Draft Claim | My Evidence | Verdict |
|---|---|---|---|
| 1 | "function X at line Y" | `grep -n "def X"` → `Y: def X(...)` | ✓ CORRECT |
| 2 | "variable is a function parameter" | `sed` shows it's a local at line Z | ✗ WRONG |

Verdicts: ✓ CORRECT, ✗ WRONG, ⚠ PARTIALLY CORRECT (explain)

### 4. Classify Findings

After the table, categorize issues as:

- **Non-blocking refinements**: factual errors that don't affect the edit's validity (e.g., "project_dir is a function parameter" when it's actually a local variable, but the variable IS in scope so the edit still works)
- **Blocking issues**: claims that if wrong would cause the implementer to write incorrect code
- **Overstatements**: claims that are directionally correct but state stronger guarantees than the code actually provides (e.g., "mid-run commits cannot contaminate" when they actually can in edge cases)

### 5. End with FINAL_JSON

```json
{"role":"reviewer","status":"CONSENSUS_REACHED","summary":"..."}
```
or
```json
{"role":"reviewer","status":"OBJECTIONS","summary":"..."}
```

## Tool Pitfalls on Large Codebases

pipeline_relay.py is 3577 lines. These tools have quirks at that scale:

### search_files and Regex Metacharacters

`search_files` uses grep under the hood. Parentheses, brackets, and other grep metacharacters in the pattern cause "Unmatched ( or \\(" errors.

**Fix**: Omit metacharacters from the pattern or fall back to `terminal` with `grep -n`:
- BAD: `search_files(pattern="def _execution(")`
- GOOD: `search_files(pattern="def _execution")`
- GOOD: `terminal(command="grep -n 'def _execution' file.py")`

### read_file Dedup Blocks

After 3 reads of the same file region, `read_file` returns "File unchanged since last read" and refuses to re-return content. For adversarial review that needs to verify many sections, this becomes a blocker.

**Fix**: Use `terminal` with `sed` for on-demand reads:
```
terminal(command="sed -n '3196,3240p' runtime/abstraction/pipeline_relay.py")
```
No dedup, reads any region, works every time.

### execute_code and hermes_tools

When using `execute_code` to batch multiple `read_file` calls from `hermes_tools`, the return dict may not contain a `content` key if the tool returns an error. Always check the dict keys before accessing.

## What Makes a Good Review

1. **Independence**: Your verification command must not rely on the draft's own evidence. Run your own grep/sed.
2. **Precision**: Cite exact line numbers from YOUR grep output, not the draft's.
3. **Honesty**: If you can't verify a claim (e.g., can't find the function), say so — don't mark it ✓.
4. **Proportionality**: Flag overstatements even when the direction is right. The implementer reads the spec literally.
5. **Constructiveness**: When a claim is wrong but the edit is still valid, say so explicitly. "Claim X is factually wrong (Y not Z), but the edit is still correct because W."

## Per-Role Artifact Verification Pitfall (2026-08-26)

When verifying content conservation across per-profile split artifacts (e.g., a SKILL.md that was split into slim SKILL.md + references/pitfalls.md across all six pipeline profiles), **line offsets vary per role**. The pre-split backups have the `## Pitfalls` header at different lines depending on what content preceded it in each role's variant.

**Concrete example**: brain backup has Pitfalls at line 374 (content starts line 375), but review1 backup has it at line 376 (content starts line 377). A spec that says "verify line 375 of the backup matches line 5 of pitfalls.md" will pass for brain but fail for review1 — even though the content IS conserved, just at a different offset.

**Fix**: When verifying conservation across per-role artifacts, use `grep -n '## Pitfalls' <backup>` to find the actual header offset for that role, then check the content line immediately after it. Do not assume a uniform line number.

**When this applies**: Any verification of per-profile deployments where each profile has a slightly different variant of the same file (different line counts, different optional sections, different append history). This includes:
- SKILL.md splits across .hermes-{role}/ homes
- Config file variants per profile
- Any "same content, different wrapping" deployments

**Batch verification pattern** (proven efficient): Use a single `execute_code` block to collect stat/inode/ownership/size for all six profiles at once, then a second block for routing verification (HERMES_HOME in /proc/PID/environ), then a third for conservation with per-role grep offsets. Three execute_code calls beats 30+ terminal calls.
