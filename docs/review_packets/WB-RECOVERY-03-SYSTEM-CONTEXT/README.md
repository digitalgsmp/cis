# Card 03 — System Context runtime restoration

**Entry point for an independent reviewer.** Everything needed to review this
work is in this directory, in Git. No access to the development machine at
`/mnt/projects/cis` is required.

| | |
|---|---|
| **Baseline before the repair** | `353738753dc082cb0fad88007f121d8a35c428ae` |
| **`CARD03_RUNTIME_SHA`** | `9e0a749fc700451bdf3e44beeb183f037b44e54b` |
| **`CARD03_EVIDENCE_SHA`** | the commit that added this directory |
| **Status** | `CARD03_DEPENDENCY_RESTORED` |
| **WB.1 status** | **OPEN** — unchanged |
| **Discoveries 20 / 26 / 27 / 28** | unchanged, unresolved |

---

## What this is, in one paragraph

Recovery Card 03 (queue 4.31) built a read-only System Context / Recovery view
for the Workbench. It was completed and independently accepted — see
`CARD_03_verification_PASS.json`. But its runtime and UI code was **never
committed**. Card 04, which closed the recovery sequence, committed only
documentation and generated projections. The code survived for weeks as an
uncommitted working-tree layer. WB.1's authentication work was then built on top
of it and now hard-depends on it, so WB.1 could not be committed without first
committing this. Commit `9e0a749` restores it.

This is a **pre-existing repository-history omission**, not a defect in WB.1.

## Why WB.1 was blocked

| WB.1 file | depends on | if missing |
|---|---|---|
| `runtime/ui/src/App.jsx` | `./SystemContext` | production build fails — unresolved import |
| `runtime/ui/src/api.js` | System Context GET wrappers | `SystemContext.jsx` has nothing to call |
| `test_braingate_conversation_boundary.py` check 10b | `container_app.py` → `api/system_context.py` | boundary check fails |

## What is in commit `9e0a749`

Eight files of Card 03 work, plus 14 deterministic export projections the
repository's own pre-commit hook regenerated and auto-staged. The projections
are not part of the review scope; their only deltas are a timestamp, a run id, a
DB state revision and a recorded HEAD.

**Five files are byte-for-byte the content that received the Card 03 PASS:**

```
runtime/api/system_context.py             5f7f8662…
runtime/tests/test_system_context_api.py  13ea50af…
runtime/ui/src/App.jsx                    4abe5594…
runtime/ui/src/api.js                     e2d767a3…
runtime/ui/src/index.css                  d2fcc851…
```

**Three files are NOT covered by that PASS and need fresh review:**

```
runtime/ui/src/SystemContext.jsx          bdab848f…   Card 04 R1 post-image
runtime/ui/src/SystemContext.test.jsx     d30f4b06…   Card 04 R1 post-image
runtime/container_app.py                  51029675…   System Context hunk only
```

Read **`INTEGRATION_REVIEW_REQUIRED.md`** before reviewing. It explains exactly
why each of the three differs and what you are being asked to check. Nothing was
fabricated to make a hash match, and nothing unreviewed is labelled as reviewed.

## Files in this packet

| File | What it is |
|---|---|
| `README.md` | this file |
| `completion.json` | machine-readable state: SHAs, file classification, tests, non-activation, blockers |
| `CARD_03_verification_PASS.json` | the original independent PASS record, copied verbatim |
| `changed_sha256.txt` | SHA-256 of every committed file, split by review status, plus the auto-staged projections |
| `INTEGRATION_REVIEW_REQUIRED.md` | **the three files needing new review**, and why |
| `test_summary.md` | fresh test results with commands and historical comparison |
| `test_output.txt` | raw captured output of those runs |
| `route_inventory.txt` | URL map generated from the committed tree |
| `secret_scan.txt` | scan proving no secret value is present in this packet |
| `SOURCE_EVIDENCE_MAP.md` | provenance back to the local `data/agent_handoffs/…` bundles, and how the mixed files were reconstructed |

## How to reproduce the checks

**Verify a file is the Card 03 PASS content:**

```sh
git cat-file -p 9e0a749:runtime/ui/src/api.js | sha256sum
# e2d767a34d6af4144e9c5210b9890b9f3d8fc622be10f6e97189847da617c7ab
```

Compare against `changed_sha256.txt`, or `sha256_new_review_files` in
`CARD_03_verification_PASS.json`'s sibling `completion.json` on the dev machine.

**Confirm the Card 03 diff carries no WB.1 content:**

```sh
git diff 3537387 9e0a749 -- runtime/container_app.py runtime/ui/src/App.jsx runtime/ui/src/api.js
```

There should be no authentication, session, CSRF, OIDC, SignIn or Braingate
content anywhere in it.

**Reproduce the frontend result from a clean tree:**

```sh
git worktree add --detach /tmp/verify 9e0a749
cd /tmp/verify/runtime/ui && npm ci && npx vitest run && npx vite build
# 24/24 passed · 27 modules transformed
```

**Backend suites** need the spine DB (`data/cis_memory.db`, ~5.9 GB, gitignored)
and so only run on the development machine. Recorded results are in
`test_summary.md`; raw output in `test_output.txt`.

## What did NOT happen

No migration was applied (0035, 0036, 0037, 0038 all untouched). Braingate was
not registered. Card Factory and Card Runner remain unexposed. Auth0 was not
configured, Cloudflare routing was not changed, `cis-pipeline` was not
restarted. No paid model call, no agent subprocess, no live database mutation.

The developer working tree was never overwritten — staging was done into the Git
index only, so the full WB.1 implementation is still present there, uncommitted.

## What happens next

WB.1 — Freeze, Commit, and Publish OIDC Review Evidence, against this repaired
baseline. WB.1 remains OPEN and is not closed by this repair.
