# Menter Chunk Execution & Verification Evidence

How to execute a Menter "build this file" chunk in the CIS pipeline and — critically — what
counts as verification evidence at the end of the chunk.

## Verification evidence (non-negotiable)

- Inline `python -c` one-liners do NOT satisfy the workspace's "fresh passing verification
  evidence" check. A standalone script is required.
- Create a focused temp script under `/tmp` using an OS-safe tempfile path with filename
  prefix `hermes-verify-` (e.g. `/tmp/hermes-verify-relay-ping.py`).
- Run it against the changed behavior. It must exit 0 and print explicit PASS lines
  (assert-based, `sys.exit(1)` on failure).
- Clean it up afterward (`rm`) and confirm no `hermes-verify-*` artifacts remain.
- In the final summary, label it explicitly as "ad-hoc targeted verification, not a
  canonical suite run". Do NOT claim suite green when the repo has no suite. If
  verification is impossible, name the concrete blocker instead of claiming verified.

## Flask route insertion recipe (CIS runtime/container_app.py pattern)

1. Verify ground truth first: read the file and confirm the exact line numbers named in
   the directive (insertion boundary, sibling routes) BEFORE patching.
2. Patch with the patch tool. Its returned diff IS the record of exactly your insertion —
   keep the change to one block, no banner comments unless the directive includes them.
3. Verify (all four):
   - Import: `python3 -c "from runtime.container_app import app"` from `/workspace/cis`;
     count url_map rules (before N, after N+1).
   - Exact body: `app.test_client()` GET, assert `r.get_json() == {"status": "ok"}` by
     exact dict equality — no extra keys.
   - Route table: iterate `app.url_map.iter_rules()`, drop HEAD/OPTIONS from methods,
     assert the new rule appears exactly once with the expected methods.
   - Regressions: spot-check sibling routes (e.g. `/api/ping` still pong, `/api/health`
     fields intact). Do NOT hit heavyweight routes that sweep gateways (e.g. blueprint
     `/api/relay/health`) with the test client — verify their url_map presence only.
4. Codebase-local traps: copy-paste payloads from sibling routes (pong vs ok,
   timestamp/container fields), auth calls on sibling POST routes, gateway sweeps on
   blueprint health routes. The Brain/Draft directive usually exclusion-lists these;
   honor the list even when the tempting snippet is one line away.

## Shared-repo scoping pitfall

- `git status` / `git diff --stat` in the CIS workspace shows every other chunk's
  working-tree changes. Do NOT claim "zero collateral" based on repo-wide status — scope
  the claim to the files your own patch calls touched. The patch tool's `files_modified`
  field is authoritative for your delta.
