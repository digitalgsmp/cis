# Tests and gates run for this durability commit

All runs on `/mnt/projects/cis`, measured at
`bf01df4d45a9de8981c2d057cf629e4cd24ba514`, before the commit was created.
`python3.12` throughout — pytest is not installed on either interpreter on this
host, so the suites are plain-python with their own runners, the convention
`tools/export/tests` already uses.

## 1. KB source-coverage suite — 34/34

```sh
python3.12 tools/kb/tests/test_kb_coverage.py
# 34/34 passed.
```

Every case builds its own temporary spine and its own source tree, so a pass
means the logic is right rather than that today's corpus happens to be clean.
Covers discovery, both key conventions, `min_bytes`, grace windows, provenance,
idempotent re-ingestion, supersession on change, fail-closed behaviour on an
unreadable spine or policy, and the default/`--closeout` split.

**One intermediate failure worth recording, because it is the mechanism
working.** After the two reports were copied into `docs/review_packets/` but
before they were ingested, this suite reported 33/34 — `production measurable
families contribute no closeout blocker` failed with:

```
repository_docs: coverage 98.8% below required 100% (6 source(s) never ingested)
```

That is the coverage gate detecting six real new durable documents on its own,
from filesystem discovery, with no edit to `config/kb_source_policy.yaml`. The
family was then ingested through the sanctioned path and the suite returned to
34/34. The failure is reported here rather than quietly skipped past: it is the
only end-to-end evidence in this packet that the gate catches genuinely new
material and not just synthetic fixtures.

## 2. SessionEnd hook installer suite — 25/25

```sh
python3.12 tools/kb/tests/test_install_session_end_hook.py
# 25/25 passed.
```

New with this commit. Each case builds its own settings file in a temp dir;
none touches `~/.claude/settings.json`. Asserts that unrelated top-level keys
(`model`, `theme`, `permissions`, `autoMemoryEnabled`) survive byte-for-byte,
that an unrelated hook event survives, that a foreign `SessionEnd` hook is kept
alongside ours and its group is not reshaped, that re-running never duplicates
the entry, that a hand-customised timeout is not overwritten, that `--dry-run`
writes nothing, and that malformed JSON or an unrecognised `hooks` shape is
refused and left untouched.

One defect was found and fixed by this suite: `registered()` ran before shape
validation and raised on a non-object `"hooks"`, so `--check` could exit with a
traceback instead of a refusal. Shape is now validated first, in every mode.

## 3. KB source-coverage gate

```sh
python3.12 tools/gates/gate_kb_source_coverage.py            # default
python3.12 tools/gates/gate_kb_source_coverage.py --closeout # stage closeout
```

| Family | Required | Coverage | Eligible / ingested | Status |
|---|---|---|---|---|
| `repository_docs` | yes | 100.0% | 501 / 501 | OK |
| `external_dev_handoffs` | yes | 100.0% | 239 / 239 | OK |
| `cis_kernel` | yes | 100.0% | 1311 / 1311 | OK |
| `claude_code_sessions` | yes | 100.0% | 76 / 76 | OK |
| `chatgpt_sessions` | yes | — | — | INGESTION PATH MISSING |
| `claude_ai_sessions` | yes | — | — | INGESTION PATH MISSING |

- **default mode: GATE FAIL** — correct and deliberate. The two browser-history
  families are `required: true` with `measurable: false`, so the unresolved
  architecture decision stays visible and cannot be forgotten.
- **`--closeout` mode: GATE PASS**, printing
  `POLICY UNDECIDED (not blocking in --closeout): chatgpt_sessions, claude_ai_sessions`.

That is the split this card had to preserve: the impossible families remain
visibly unresolved **without** making every closeout permanently fail. The
browser-history policy itself was not changed.

## 4. Closeout integration — `tools/development/discovery.py`

```python
check_closeout(conn, "WB.1")
```

```
ready_to_close: False
evidence_checked: {"total_events": 136, "discoveries_checked": 60,
                   "kb_coverage_checked": true, "kb_coverage_blockers": 0}
blockers: unresolved_before_stage_closeout (revision 127),
          unresolved_unfinished_work x2
```

`kb_coverage_checked: true` is the point — the closeout reports out loud that
coverage was actually measured, so a pass can never be confused with a silent
skip. With all measurable families at 100%, `kb_coverage_blockers` is 0 and the
KB contributes nothing to WB.1's blocker list.

WB.1 remains **OPEN**, blocked by **revision 127** — the live public
trust-boundary exposure. This commit does not touch it.

## 5. Ingestion idempotency

```sh
python3.12 tools/kb/ingest_files.py --family repository_docs --dry-run
# [repository_docs] 6 never ingested, 0 changed since ingest
#   173 chunk(s), 131,410 chars
#   --dry-run: nothing written.

python3.12 tools/ingest_claude_code_sessions.py --dry-run
# 12 previously-ingested sessions: 0 new chunk(s) each
# 32 new chunk(s), 27,262 chars   (the live session only)
```

Both planners are incremental and keyed by `source_key`: of 501 eligible
documents and 76 eligible transcripts, only the genuinely new ones plan any
work. `0 changed since ingest` is the sha256 provenance check agreeing that no
previously-ingested document drifted.

The real ingestion that followed — after `README.md` and this file were written,
so eight new documents rather than the six the dry run saw:

```sh
python3.12 tools/kb/ingest_files.py --family repository_docs
# [repository_docs] 8 never ingested, 0 changed since ingest
#   199 chunk(s), 149,911 chars
#   knowledge_messages: +199 · embedded 199/199
```

`repository_docs` returned to 100% (501/501) and the suite in §1 returned to
34/34. This file was ingested once more after the 501/501 figure above was
corrected into it, so its committed sha256 is the one the manifest records.

## 6. SessionEnd hook, end to end

```sh
echo '{"hook_event_name":"SessionEnd","reason":"test"}' | bash tools/kb/session_end_ingest.sh
# exit 0
# logs/kb_session_end_ingest.log:
#   2026-10-07T17:55:48Z OK 44s knowledge_messages: +32
```

`+32` matches the dry-run plan exactly. The script drains stdin, exits 0
unconditionally, and never interferes with the harness shutting down.

Lock serialization verified by holding the flock and running a second instance:

```
2026-10-07T17:59:39Z SKIP another session_end ingest holds the lock
```

The loser skips rather than queues, as designed — concurrent writers to the same
Chroma collection is what the lock exists to prevent, and the ingester is
incremental so the skipped material is picked up by the next run.

Registration itself:

```sh
python3 tools/kb/install_session_end_hook.py --check
# ALREADY REGISTERED: SessionEnd -> /mnt/projects/cis/tools/kb/session_end_ingest.sh
```

`~/.claude/settings.json` was byte-identical (md5 `7ea52bdb…`) before and after
every run in this session.

## 7. Export agreement and build-state coherence

```sh
bash tools/gates/gate_export_agreement.sh
# PASS: build state is coherent — no completed tiers listed as gated
# PASS: all 13 artifacts match manifest
```

This is the gate the repository's own pre-commit hook runs, so it had to be
green before the commit could be made.

## 8. Secret scan

See `secret_scan.txt`. Two independent CIS mechanisms: the index-time filter
from `runtime/mcp_bridge/chroma_index.py` over all 18 files (0 hits), and
`gate_no_secrets.sh` against the real Git index after staging.

```sh
bash tools/gates/gate_no_secrets.sh
# PASS: no secrets or sensitive files in staged changes
```

The gate failed once on the way there, on a false positive worth recording: the
first draft of `secret_scan.txt` quoted the gate's own patterns verbatim, so the
gate matched its own pattern text inside the scan report. The report now
describes the patterns instead of quoting them — the convention
`WB-RECOVERY-03-SYSTEM-CONTEXT/secret_scan.txt` already uses. No finding was
suppressed, and no real secret existed anywhere in the commit, so nothing
required sanitisation and no provenance was altered.
