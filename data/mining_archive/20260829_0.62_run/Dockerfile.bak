# /opt/cis-control/proofs/mwl-proof/Dockerfile
# Production Hermes worker image — pinned, non-root worker.
#
# SEAL MODEL (fixes yesterday's defeat where the worker disabled enforcement
# by editing files it owned under ~/.hermes):
#   - The enforcement CONFIG (hooks block + plugins.enabled + model pin) lives
#     in /etc/hermes/config.yaml (MANAGED SCOPE), root-owned 0644. Hermes treats
#     it as authoritative and REFUSES worker `hermes config set` on those keys.
#   - The enforcement SCRIPT lives at /opt/cis-hooks/cis_shell_hook.sh,
#     root-owned 0555. The worker can execute it but cannot rewrite it.
#     (The shell-hook consent allowlist keys on the command STRING, not the
#     script hash — so the script file itself MUST be unwritable by the worker.)
#   - HERMES_MANAGED_DIR and HERMES_ACCEPT_HOOKS are baked into image env so the
#     worker's own subprocess env cannot repoint or de-consent them at launch.
#   - The worker keeps a fully writable ~/.hermes for state.db, sessions,
#     memories — none of which are enforcement surfaces.
#
# Build (Eric, root, his terminal):
#   sudo docker build -t cis-hermes:pinned -f /opt/cis-control/proofs/mwl-proof/Dockerfile /opt/cis-control/proofs/mwl-proof
#
# Build context is /opt/cis-control/proofs/mwl-proof, so plugin/,
# cis_shell_hook.sh, and managed-config.yaml are copied from there by root.

FROM nikolaik/python-nodejs:python3.11-nodejs20

# --- install sqlite3 CLI for gate scripts ---
RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# --- install pyyaml for gate scripts (system python, not Hermes venv) ---
RUN pip3 install pyyaml

# --- install Claude Code CLI (baked at build time, worker uses at runtime) ---
# No ANTHROPIC_API_KEY baked — login via OAuth interactively (docker exec -it)
RUN npm install -g @anthropic-ai/claude-code

# --- install pinned Hermes as root, at build time, once ---
RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-browser \
    && /usr/local/bin/hermes --version \
    && echo "HERMES_PIN_OK"

# --- install Telegram adapter into Hermes venv (not in base install) ---
# Hermes venv ships without pip — bootstrap it, then install
RUN /usr/local/lib/hermes-agent/venv/bin/python -m ensurepip --upgrade \
    && /usr/local/lib/hermes-agent/venv/bin/python -m pip install 'python-telegram-bot[webhooks]==22.6'

# --- install Flask + httpx for the pipeline API and relay ---
RUN /usr/local/lib/hermes-agent/venv/bin/python -m pip install flask httpx pyyaml

# --- patch loop-breaker: vendor 0.17.0 lacks _success_repeat_counts (NA-SEED-018) ---
COPY tool_guardrails.py /usr/local/lib/hermes-agent/agent/tool_guardrails.py

# --- bake all 51 CIS gate scripts into /opt/cis-gates/ (root-owned, RO) ---
COPY gates/ /opt/cis-gates/
RUN chown -R root:root /opt/cis-gates \
    && find /opt/cis-gates -type d -exec chmod 0555 {} \; \
    && find /opt/cis-gates -type f -exec chmod 0555 {} \;

# --- bake the card-factory tools (card_gate.py, mine_asks.py, GENERATOR_PROMPT) ---
# Root-owned, RO — the worker cannot weaken its own card validator or generator prompt.
COPY cis-tools/ /opt/cis-tools/
RUN chown -R root:root /opt/cis-tools \
    && find /opt/cis-tools -type d -exec chmod 0555 {} \; \
    && find /opt/cis-tools -type f -exec chmod 0555 {} \;

# --- bake the container gate runner (pre-tool-call enforcement) ---
COPY container_gate_runner.py /opt/cis-gates/container_gate_runner.py
RUN chown root:root /opt/cis-gates/container_gate_runner.py \
    && chmod 0555 /opt/cis-gates/container_gate_runner.py

# --- bake the OBSERVER plugin, root-owned, world-readable, worker-unwritable ---
COPY plugin/ /opt/cis-policy/plugin/
RUN chown -R root:root /opt/cis-policy \
    && find /opt/cis-policy -type d -exec chmod 0555 {} \; \
    && find /opt/cis-policy -type f -exec chmod 0444 {} \;

# --- bake the MANAGED CONFIG (the sealed contract), root-owned 0644 ---
COPY managed-config.yaml /etc/hermes/config.yaml
RUN chown -R root:root /etc/hermes \
    && chmod 0755 /etc/hermes \
    && chmod 0644 /etc/hermes/config.yaml

# --- bake all 6 PROFILE CONFIGS (managed scope, root-owned) ---
COPY profiles/ /etc/hermes/profiles/
RUN chown -R root:root /etc/hermes/profiles \
    && find /etc/hermes/profiles -type d -exec chmod 0755 {} \; \
    && find /etc/hermes/profiles -type f -exec chmod 0644 {} \;

# --- bake the multi-profile launch script ---
COPY launch_profiles.sh /opt/cis-control/launch_profiles.sh
RUN chown root:root /opt/cis-control/launch_profiles.sh \
    && chmod 0555 /opt/cis-control/launch_profiles.sh

# --- bake the container entrypoint (gateways + pipeline API) ---
COPY entrypoint.sh /opt/cis-control/entrypoint.sh
RUN chown root:root /opt/cis-control/entrypoint.sh \
    && chmod 0555 /opt/cis-control/entrypoint.sh

# --- create the unprivileged worker user (NO sudo, NO root) ---
# Use UID/GID 1000 to match host user (eric) so mounted volumes are writable.
# Remove the base image's default 'pn' user (UID 1000) first.
RUN deluser pn 2>/dev/null; \
    groupadd -g 1000 worker 2>/dev/null; \
    useradd -m -s /bin/bash -u 1000 -g 1000 worker

# --- install the OBSERVER plugin into the worker's home AS ROOT, then seal it ---
# Observer only — not the wall. Sealed anyway so the worker can't tamper.
# Install into base .hermes AND all 6 profile homes (pre-created at build time
# so the plugin is root-owned and read-only; entrypoint only copies config.yaml)
RUN mkdir -p /home/worker/.hermes/plugins \
    && cp -a /opt/cis-policy/plugin /home/worker/.hermes/plugins/mwl-proof \
    && chown -R root:root /home/worker/.hermes/plugins/mwl-proof \
    && find /home/worker/.hermes/plugins/mwl-proof -type d -exec chmod 0555 {} \; \
    && find /home/worker/.hermes/plugins/mwl-proof -type f -exec chmod 0444 {} \; \
    && chown worker:worker /home/worker/.hermes /home/worker/.hermes/plugins

# --- bake CIS-specific skills into all 6 profile homes (root-owned, RO) ---
# cis-soul: behavior protocol for all profiles
# cis-pipeline-architecture: pipeline architecture reference
COPY cis-soul/ /tmp/cis-skills/cis-soul/
COPY cis-pipeline-architecture/ /tmp/cis-skills/cis-pipeline-architecture/
# Per-role variants of cis-pipeline-architecture. The 2026-08-25 split gave each
# profile its own SKILL.md and references/pitfalls.md so an agent can record a
# lesson without touching the other five. Baking the single shared copy into all
# six homes silently undid that split on every rebuild; these seed the split
# version instead, and the shared copy above remains the fallback.
COPY cis-skills-per-role/ /tmp/cis-skills-per-role/

# Pre-create all 6 profile home directories with sealed enforcement plugin
RUN for profile in brain draft review1 review2 menter verify; do \
        mkdir -p /home/worker/.hermes-$profile/plugins; \
        mkdir -p /home/worker/.hermes-$profile/skills/software-development; \
        cp -a /opt/cis-policy/plugin /home/worker/.hermes-$profile/plugins/mwl-proof; \
        cp -a /tmp/cis-skills/cis-soul /home/worker/.hermes-$profile/skills/software-development/cis-soul; \
        if [ -d /tmp/cis-skills-per-role/$profile ]; then \
            cp -a /tmp/cis-skills-per-role/$profile /home/worker/.hermes-$profile/skills/software-development/cis-pipeline-architecture; \
        else \
            cp -a /tmp/cis-skills/cis-pipeline-architecture /home/worker/.hermes-$profile/skills/software-development/cis-pipeline-architecture; \
        fi; \
        chown -R root:root /home/worker/.hermes-$profile/plugins/mwl-proof; \
        find /home/worker/.hermes-$profile/plugins/mwl-proof -type d -exec chmod 0555 {} \; ; \
        find /home/worker/.hermes-$profile/plugins/mwl-proof -type f -exec chmod 0444 {} \; ; \
        chown -R worker:worker /home/worker/.hermes-$profile/skills; \
        chown worker:worker /home/worker/.hermes-$profile /home/worker/.hermes-$profile/plugins; \
    done

# --- bake managed-scope + hook-consent env into the IMAGE (not runtime) ---
# Fixed here so the worker's subprocess env cannot repoint managed scope or
# silently de-consent the hook. The Hermes process inherits these at launch.
ENV HERMES_MANAGED_DIR=/etc/hermes \
    HERMES_ACCEPT_HOOKS=1

# Worker is the active runtime user.
USER worker
WORKDIR /home/worker

# ── CIS pipeline environment ──────────────────────────────────────────
# The CIS repo is mounted at /workspace/cis (volume, not baked — so code
# changes on the host show up immediately without rebuilding the image).
# The pipeline reads DB_PATH from CIS_SPINE_PATH env var.
ENV CIS_SPINE_PATH=/workspace/cis/data/cis_memory.db \
    CIS_PROJECT_ROOT=/workspace/cis \
    CIS_REPO=/workspace/cis \
    CIS_DB_PATH=/workspace/cis/data/cis_memory.db \
    PYTHONPATH=/workspace/cis/runtime

# Prove at build time the worker can READ the sealed managed config + plugin,
# and that managed scope is resolved (doctor reports the managed dir).
RUN echo "---MANAGED-SCOPE-RESOLVED---" \
    && /usr/local/bin/hermes doctor 2>&1 | grep -i managed || true ; \
    echo "---PLUGIN-OWNERSHIP---" \
    && ls -l /home/worker/.hermes/plugins/mwl-proof

# Default command: launch all 6 profiles, then start the pipeline API
CMD ["/opt/cis-control/entrypoint.sh"]
