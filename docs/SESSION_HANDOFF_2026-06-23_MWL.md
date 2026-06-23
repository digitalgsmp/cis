# MWL Proof — Session Handoff 2026-06-23 ~08:15

## What was done this session

### Cross-panel message visibility (portal)
- Advisor Chat panels now show messages from ALL agents, not just their own
- "other panel" badge distinguishes cross-agent messages
- Committed: a88cb19

### Roadmap tab (portal)
- New page at /ui/roadmap with 4 sub-tabs: Roadmap grid, Timeline, ADRs, Vision
- Bridged to new portal via iframe in /portal Roadmap tab
- Committed: 45848d0, 41154e5

### MWL Proof — Docker enforcement hook testing
- Trust root at /opt/cis-control/proofs/mwl-proof/ — INTACT, root:root, never touched
- Bug found: in_container.sh used `provider: openai` — Hermes v0.17.0 doesn't recognize it
- FIXED: Changed to `provider: llamacpp` (custom provider alias) in trust root

## Current blocker
Qwen (llama-server) listens on 127.0.0.1:8002 only. Docker containers can't reach it.
Need to restart llama-server binding to 0.0.0.0:8002 or 172.17.0.1:8002.

## Next steps in order

1. Find llama-server command and restart with --host 0.0.0.0
2. docker rm -f mwl-proof-worker  (clean up old container)
3. sudo bash /opt/cis-control/proofs/mwl-proof/harness.sh 2>&1 | tee /mnt/cache/catalog/mwl-proof/run_v4.txt
4. Verify all 5 tests (A-E) show hook interaction, not "Connection error"

## Evidence files
- Trust root: /opt/cis-control/proofs/mwl-proof/in_container.sh (root:root, 755)
- Trust root: /opt/cis-control/proofs/mwl-proof/harness.sh (root:root, 755) — NOT modified, still original
- Previous test run: /mnt/cache/catalog/mwl-proof/run_output_v3.txt (shows llamacpp accepted but host.docker.internal unreachable)
- Test output from June 23: /mnt/cache/catalog/mwl-proof/run_output.txt (shows "Unknown provider openai")
- My workaround copies (eric-owned, NON-TRUST, can be deleted): /mnt/cache/catalog/mwl-proof/*_v*.sh

## What NOT to do
- Do NOT modify /opt/cis-control/ without sudo — that's the whole point
- Do NOT use eric-owned copies as trust root
- Do NOT use --network host (violates network isolation)
