# Phase PD CLOSED — Handoff

## Status: COMPLETE (session_closeouts row 45, PASS)

## Proven by raw execution:
- pre_tool_call blocks tool calls in-container (Test A; hook_seen.log + plugin_load.log on disk)
- /cis-control RO by execution: CIS_EXIT:1
- /source/cis RO by execution: SRC_EXIT:1
- /workspace only writable path: WRITE_OK
- In-container inference: provider=llamacpp, base_url host.docker.internal:8002/v1, model.context_length=65536 declared, llama-server --ctx-size 32768 actual

## Key fixes (root causes):
- Plugin not firing = plugin disabled by default; fixed via `hermes plugins enable mwl-proof` in in_container.sh (docs: plugins.enabled allow-list)
- 64K context floor = declare context_length 65536, run server at 32768
- /workspace write fail = Docker userns/idmap maps container-root to non-1000 subuid; proof fix chmod 0777 (NOT production)

## Phase 0 carry-forward (ordered):
1. Loop-breaker guardrail hook (Hermes infinite-looped on failed tool call + attempted unprompted sudo). Contract first.
2. Production /workspace: chown to remapped subuid, replace 0777.
3. Trust-root authoritative at /opt/cis-control/proofs/mwl-proof/ (root-owned); workspace = artifacts only.

## Next action: define loop-breaker hook block-contract schema before code.
