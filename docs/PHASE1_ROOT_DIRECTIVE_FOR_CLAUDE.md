# CIS Phase 1 — Root Configuration Directive
# For Claude (External Advisor)
# Date: 2026-06-28

═══════════════════════════════════════
WHAT CIS IS
═══════════════════════════════════════

CIS is a multi-agent pipeline that uses different AI models to check each other's work. The architecture has three layers:

1. CONTROL PLANE — Flask portal on port 5000. Eric's dashboard.
2. ABSTRACTION LAYER — Dispatch boundary. Routes intents to the right agent.
3. HERMES BACKEND — Five AI agents running as Hermes profiles, enforced inside a Docker container.

Pipeline: Eric submits intent → Drafter writes proposal → Reviewer critiques → Eric approves → Implementer builds.

═══════════════════════════════════════
WHAT WAS JUST BUILT (already done)
═══════════════════════════════════════

- Adapter API at http://127.0.0.1:5000/api/adapter/* (health, profiles, dispatch, chat)
- Knowledge base: 287,589 messages from 12 sources, FTS5 + ChromaDB dual search
- MCP bridge with 17 tools including cis_adapter_status, cis_adapter_dispatch
- Intent alignment API: /api/intent/alignment
- All built. Zero root required. Code lives at /mnt/projects/cis/

═══════════════════════════════════════
WHAT ERIC NEEDS YOU TO GUIDE HIM THROUGH
═══════════════════════════════════════

Eric is not a coder. Speak in plain steps. Show exact commands. Explain what each command does before he runs it.

Five tasks, in order:

TASK 1: Restart Qwen on 0.0.0.0:8002
──────────────────────────────────
PROBLEM: Qwen (llama-server) is bound to 127.0.0.1:8002. The Docker container can't reach it. It needs to bind to 0.0.0.0:8002 so containers on the Docker bridge (172.17.0.x) can access it.
VERIFY CURRENT STATE: sudo ss -tlnp | grep 8002
EXPECTED: Shows 127.0.0.1:8002
FIX: Find the llama-server process, stop it, restart with --host 0.0.0.0
VERIFY AFTER: curl http://192.168.1.15:8002/v1/models should return the model list

TASK 2: Complete the MWL enforcement proof
───────────────────────────────────────────
PROBLEM: The Minimal Worker Launch proof (Docker container with Hermes + enforcement hook) was never finished. The container exists but the test was blocked by Qwen binding and a provider name bug.
WHAT EXISTS:
  - /opt/cis-control/proofs/mwl-proof/harness.sh (root-owned, launches container)
  - /opt/cis-control/proofs/mwl-proof/in_container.sh (root-owned, configures Hermes)
  - Qwen provider fix applied (llamacpp instead of openai)
  - Container networking needs --add-host host.docker.internal:host-gateway
STEPS:
  1. Clean up old container: docker rm -f mwl-proof-worker
  2. Run: sudo bash /opt/cis-control/proofs/mwl-proof/harness.sh
  3. Verify the hook fires (should see "MWL_PROOF: plugin pre_tool_call fired INSIDE container")
  4. Verify the agent cannot disable the plugin (should fail)
DO NOT MODIFY /opt/cis-control/ without sudo. These files are root-owned for a reason.

TASK 3: Start the Prime gateway (port 8642)
─────────────────────────────────────────────
PROBLEM: The hermes-gateway.service (prime/research profile, port 8642) is DOWN. All other gateways are UP (8643, 8644, 8645, 8646).
COMMAND: systemctl --user start hermes-gateway
VERIFY: curl http://127.0.0.1:5000/api/adapter/health — should show all 5 profiles healthy

TASK 4: Restart gateways to activate MCP
─────────────────────────────────────────
PROBLEM: The cis-knowledge MCP server config was written to v4pro, r1, and v4impl config.yaml files on June 23, but the gateways were never restarted. They're still running without MCP knowledge access.
CURRENT PROCESSES (running since June 18):
  hermes-gateway-r1      PID 1583  port 8643
  hermes-gateway-v4impl  PID 1584  port 8646
  hermes-gateway-v4pro   PID 1585  port 8645
COMMANDS (one at a time, verify after each):
  systemctl --user restart hermes-gateway-v4pro
  systemctl --user restart hermes-gateway-r1
  systemctl --user restart hermes-gateway-v4impl
VERIFY: Check the gateway logs for MCP server startup. If a restart fails, check the log before proceeding.

TASK 5: Explain profile configuration
──────────────────────────────────────
PROBLEM: DEV-PIVOT-05 specifies per-profile SOUL.md and skill bundles for each role (Drafter, Reviewer, Implementer). This is designed but not built.
EXPLAIN TO ERIC:
  - What a SOUL.md file is and where it goes (~/.hermes-<profile>/SOUL.md)
  - What skills each role should load (defined in DEV-PIVOT-05 §6.3)
  - Whether to do this now or wait until after Phase 1 is complete
  - Whether the 5 separate installs should be collapsed to 1 install + 5 profiles

DO NOT create or modify any SOUL.md files without Eric's explicit approval. Just explain what needs to be done and let him decide.

═══════════════════════════════════════
WHAT NOT TO TOUCH
═══════════════════════════════════════

- /mnt/projects/cis/ — The CIS codebase. Everything there works. Don't modify.
- /opt/cis-control/proofs/mwl-proof/ — Trust root files. Only modify with sudo and Eric's approval.
- ~/.hermes-*/config.yaml — Only edit for MCP server additions. Don't change models, ports, or hooks.
- The Flask app on port 5000 — Leave it running. The adapter API is live.
- The ChromaDB at /mnt/projects/cis/data/chroma_data/ (9.3GB, 287,589 embeddings)

═══════════════════════════════════════
KEY PATHS
═══════════════════════════════════════

CIS codebase:    /mnt/projects/cis/
CIS database:    /mnt/projects/cis/data/cis_memory.db
ChromaDB:        /mnt/projects/cis/data/chroma_data/
Flask app:       /mnt/projects/cis/runtime/app.py (port 5000)
Adapter API:     http://127.0.0.1:5000/api/adapter/*
Trust root:      /opt/cis-control/ (root-owned, read-only in container)
Hermes profiles: ~/.hermes (prime), ~/.hermes-v4pro, ~/.hermes-r1, ~/.hermes-v4impl, ~/.hermes-qwen
Archive:         /mnt/archive/ (10TB drive)
Knowledge base:  287,589 messages, FTS5 + ChromaDB, searchable via cis_search_knowledge

═══════════════════════════════════════
AFTER ALL 5 TASKS
═══════════════════════════════════════

Confirm everything works:
  curl http://127.0.0.1:5000/api/adapter/health
  → All 5 profiles should show healthy: true

Then tell Eric: "Phase 1 complete. The system is runnable. Profiles are configured with MCP knowledge access. The MWL proof confirms enforcement works. Ready for Phase 2 — portal pipeline features."
