# Reviewer Baseline Verification — Dirty Working Tree Pitfall

## The Problem

When the CIS pipeline's Brain/Draft phases produce a spec or pattern catalog,
they verify ground truth against the current working tree. If the working tree
has pre-existing uncommitted changes (common during active development), the
spec will describe that dirty state as "existing precedent" — and make false
claims about delta size like "exactly one insertion" or "no new imports".

Reviewer A (first pass) typically inherits these false premises and rubber-stamps
claims like `no_new_imports` and `no_collateral_files` as PASS without ever
checking the committed baseline.

Reviewer B (second pass) must catch this.

## The Fix — Always Check git diff HEAD

The ONLY command that shows the true delta from committed code is:

```bash
git diff HEAD --stat          # what actually changed vs last commit
git diff HEAD --name-only     # which files were touched
git show HEAD:<file>          # does the "existing precedent" exist in HEAD?
```

`git diff` (no args) shows only unstaged changes. `git diff --cached` shows only
staged changes. Neither shows the full picture when some changes are staged and
some aren't. `git diff HEAD` shows everything relative to the last commit.

## Verification Protocol for Reviewer B

1. Run `git diff HEAD --stat` to see the TRUE delta size. Compare to the spec's
   claimed delta size. If they differ, the spec was verified against a dirty tree.

2. For any spec claim about "existing precedent" (e.g. "POST /api/relay/run at
   line 39"), run `git show HEAD:<file> | grep -c '<pattern>'`. If the pattern
   doesn't exist in HEAD, it was added in the same uncommitted changeset — it's
   not precedent, it's collateral.

3. For "no new imports" claims, run:
   ```bash
   git diff HEAD -- <file> | grep "^+.*import"
   ```
   Any +import line that doesn't exist in HEAD is a new import in this changeset.

4. For "no collateral files" claims, run:
   ```bash
   git diff HEAD --name-only
   ```
   If more files appear than the spec claims to touch, there's collateral.

## Concrete Failure Case (2026-08-24)

Directive: Add GET /api/relay/ping to runtime/container_app.py — a 4-line route.

Spec claimed: "exactly one insertion", "no new imports", "no collateral files",
and described POST /api/relay/run as "existing precedent at line 39".

Reality (git diff HEAD): 66 insertions including:
- `request` added to Flask import line (new import)
- Full POST /api/relay/run route (~40 lines: threading, auth, PipelineRelay)
- GET /dashboard/ route serving 36KB HTML
- 3 new module-level imports (threading, time, _check_auth, etc.)

None of these existed in HEAD. The spec's pattern catalog was verified against
the dirty working tree, not HEAD, so it incorrectly described uncommitted work
as "existing precedent".

Reviewer A passed `no_new_imports` and `no_collateral_files` without running
`git diff HEAD`. Both were false passes.

Reviewer B caught it by running:
- `git diff HEAD -- runtime/container_app.py` (revealed 66 insertions)
- `git show HEAD:runtime/container_app.py | grep relay_run_start` (returned nothing)
- `git diff HEAD --name-only` (showed 24 files changed, not 1)

## Key Distinction

The ping route itself was correct (4 lines, exact body, no excluded patterns).
The collateral was pre-existing uncommitted work outside the directive's scope.
The false passes were in A's verification of "no new imports" and "no collateral"
— claims that could only be checked against HEAD, not the working tree.

The APPROVED verdict was still correct because the ping route met every spec
criterion. But the `items_missed_by_a` field documented the false passes for
the record.
