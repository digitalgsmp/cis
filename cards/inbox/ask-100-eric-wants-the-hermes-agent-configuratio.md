CARD cis-v4pro-model-config: Update Hermes model config for Qwen:8002
SOURCE: message v4pro:api-6462e41c698f7f87, 2026-06-23 01:30
INTENT (Eric, verbatim): "The model config command failed — `hermes model set --provider openai-compatible ...` was rejected. The actual Hermes v0.17.0 CLI doesn't have that subcommand." "Both files need to be copied into the trust root. That requires sudo: sudo cp /tmp/harness.sh /opt/cis-control/proofs/mwl-proof/harness.sh sudo cp /tmp/in_container.sh /opt/cis-control/proofs/mwl-proof/in_container.sh"
BUILD: The Hermes agent must use environment variables to configure the Qwen:8002 model endpoint, and the updated scripts must be deployed to the trust root so they are available for the proof run.
DONE WHEN:
  - The `in_container.sh` script in `/opt/cis-control/proofs/mwl-proof/` uses environment variables to set the model endpoint
  - The `harness.sh` script in `/opt/cis-control/proofs/mwl-proof/` is updated to use the correct Hermes command syntax
  - The `in_container.sh` and `harness.sh` scripts are present in the trust root directory
EVIDENCE:
  - test -f /opt/cis-control/proofs/mwl-proof/in_container.sh && grep -q "QWEN_ENDPOINT" /opt/cis-control/proofs/mwl-proof/in_container.sh
  - test -f /opt/cis-control/proofs/mwl-proof/harness.sh && grep -q "hermes model set" /opt/cis-control/proofs/mwl-proof/harness.sh
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
