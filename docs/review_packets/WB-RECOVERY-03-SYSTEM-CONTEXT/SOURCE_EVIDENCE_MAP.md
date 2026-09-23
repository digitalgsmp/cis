# Provenance map

Every file in this packet, and where it came from on the development machine.
The local sources live under `data/`, which `.gitignore:136` (`/data/*`)
excludes from Git — which is why this sanitized packet exists. The originals are
**not** deleted; they remain at the paths below on `/mnt/projects/cis`.

## Packet file → local source

| Packet file | Derived from |
|---|---|
| `README.md` | written for this packet |
| `completion.json` | written for this packet; incorporates `data/agent_handoffs/WB-RECOVERY-03-workbench-system-context-ui/completion.json` |
| `CARD_03_verification_PASS.json` | verbatim copy of `data/agent_handoffs/WB-RECOVERY-03-workbench-system-context-ui/CARD_03_verification_PASS.json` |
| `changed_sha256.txt` | computed fresh from commit `9e0a749`; cross-checked against the Card 03 bundle's `completion.json` → `sha256_new_review_files` |
| `test_summary.md` | fresh runs; historical columns from the Card 03 bundle's `completion.json` → `tests` and Card 04 R1's `completion.json` → `regression_test_summary` |
| `test_output.txt` | fresh runs captured while preparing `9e0a749` |
| `route_inventory.txt` | generated fresh from the committed tree at `9e0a749` |
| `INTEGRATION_REVIEW_REQUIRED.md` | written for this packet; hash claims cross-checked against the Card 03 bundle and `data/agent_handoffs/WB-RECOVERY-04-recovery-drill-closeout/correction-R1/postimage_hashes_round2.txt` |
| `SOURCE_EVIDENCE_MAP.md` | this file |

## Local evidence bundles referenced

| Bundle | Role |
|---|---|
| `data/agent_handoffs/WB-RECOVERY-03-workbench-system-context-ui/` | authoritative Card 03 record — `CARD_03_verification_PASS.json`, `completion.json`, `evidence.md`, `git_status.txt`, sample packet JSON, backend/frontend test output |
| `data/agent_handoffs/WB-RECOVERY-04-recovery-drill-closeout/` | Card 04 closeout; `evidence.md` line 26 is the contemporaneous record that Cards 01–03 deliverables were still uncommitted |
| `data/agent_handoffs/WB-RECOVERY-04-recovery-drill-closeout/correction-R1/` | source of the current `SystemContext.jsx` / `.test.jsx` content — `postimage_hashes_round2.txt`, `completion.json` |
| `data/agent_handoffs/WB-1-BRAINGATE-ACTIVATION-BOUNDARY/` | independently re-recorded the post-Card-03 hashes of `system_context.py`, `test_system_context_api.py`, `api.js`, `App.jsx` as "unchanged, verified untouched" |
| `data/agent_handoffs/container-kb-health-20260917/` | the separate Chroma-health stream deliberately excluded — see `INTEGRATION_REVIEW_REQUIRED.md` §3 |

## How the mixed files were reconstructed

`container_app.py`, `App.jsx`, `api.js` and `index.css` each contained Card 03
work interleaved with later WB.1 work. No backup held a Card 03-era snapshot:
every `*.HEAD-preimage` file in the WB.1 bundles is a copy of the **Git HEAD**
version, not the working tree — confirmed because
`WB-1-WORKBENCH-BROWSER-SESSION-AUTH/backups/runtime_workbench_auth.py.HEAD-preimage`
is 0 bytes, that file being untracked at HEAD.

The Card 03 content was therefore rebuilt deterministically from `3537387` plus
the isolated Card 03 hunks, and **verified by hash** against the Card 03
evidence before staging:

| File | Method | Result |
|---|---|---|
| `api.js` | HEAD + the System Context wrapper block appended | hashes to `e2d767a3…` ✅ |
| `App.jsx` | HEAD + import, `recovery` view branch, header button | hashes to `4abe5594…` ✅ |
| `index.css` | working tree truncated at the WB.1 `/* ── Sign-in ─` block | hashes to `d2fcc851…` ✅ |
| `container_app.py` | HEAD + the System Context registration only | hashes to `51029675…` — **not** the Card 03 hash; see `INTEGRATION_REVIEW_REQUIRED.md` §3 |

Staging was done into the Git index only (`git hash-object -w` +
`git update-index --cacheinfo`). The developer working tree was never
overwritten and still carries the full WB.1 implementation.

## Reproducing the hash checks

```sh
git cat-file -p 9e0a749:runtime/ui/src/api.js | sha256sum
# e2d767a34d6af4144e9c5210b9890b9f3d8fc622be10f6e97189847da617c7ab
```

Compare against `sha256_new_review_files` in the Card 03 bundle's
`completion.json`, or the table in `changed_sha256.txt`.
