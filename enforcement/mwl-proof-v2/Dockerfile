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

# --- install pinned Hermes as root, at build time, once ---
RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-browser \
    && /usr/local/bin/hermes --version | grep -q "0.17.0" \
    && echo "HERMES_PIN_OK"

# --- install Telegram adapter into Hermes venv (not in base install) ---
# Hermes venv ships without pip — bootstrap it, then install
RUN /usr/local/lib/hermes-agent/venv/bin/python -m ensurepip --upgrade \
    && /usr/local/lib/hermes-agent/venv/bin/python -m pip install 'python-telegram-bot[webhooks]==22.6'

# --- patch loop-breaker: vendor 0.17.0 lacks _success_repeat_counts (NA-SEED-018) ---
COPY tool_guardrails.py /usr/local/lib/hermes-agent/agent/tool_guardrails.py

# --- bake all 51 CIS gate scripts into /opt/cis-gates/ (root-owned, RO) ---
COPY gates/ /opt/cis-gates/
RUN chown -R root:root /opt/cis-gates \
    && find /opt/cis-gates -type d -exec chmod 0555 {} \; \
    && find /opt/cis-gates -type f -exec chmod 0555 {} \;

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

# --- create the unprivileged worker user (NO sudo, NO root) ---
RUN useradd -m -s /bin/bash worker

# --- install the OBSERVER plugin into the worker's home AS ROOT, then seal it ---
# Observer only — not the wall. Sealed anyway so the worker can't tamper.
RUN mkdir -p /home/worker/.hermes/plugins \
    && cp -a /opt/cis-policy/plugin /home/worker/.hermes/plugins/mwl-proof \
    && chown -R root:root /home/worker/.hermes/plugins/mwl-proof \
    && find /home/worker/.hermes/plugins/mwl-proof -type d -exec chmod 0555 {} \; \
    && find /home/worker/.hermes/plugins/mwl-proof -type f -exec chmod 0444 {} \; \
    && chown worker:worker /home/worker/.hermes /home/worker/.hermes/plugins

# --- bake managed-scope + hook-consent env into the IMAGE (not runtime) ---
# Fixed here so the worker's subprocess env cannot repoint managed scope or
# silently de-consent the hook. The Hermes process inherits these at launch.
ENV HERMES_MANAGED_DIR=/etc/hermes \
    HERMES_ACCEPT_HOOKS=1

# Worker is the active runtime user.
USER worker
WORKDIR /home/worker

# Prove at build time the worker can READ the sealed managed config + plugin,
# and that managed scope is resolved (doctor reports the managed dir).
RUN echo "---MANAGED-SCOPE-RESOLVED---" \
    && /usr/local/bin/hermes doctor 2>&1 | grep -i managed || true ; \
    echo "---PLUGIN-OWNERSHIP---" \
    && ls -l /home/worker/.hermes/plugins/mwl-proof

# Default command: gateway server (override with docker run args to shell in)
CMD ["hermes", "gateway", "run"]
