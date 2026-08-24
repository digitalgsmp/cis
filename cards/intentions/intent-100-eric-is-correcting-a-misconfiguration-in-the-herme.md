# Intention Card

**Intention:** Eric is correcting a misconfiguration in the Hermes CLI command that prevents the containerized system from connecting to the Qwen model, ensuring the proof can run correctly by validating the correct script syntax and deployment process.

**Mission Connection:** This aligns with the CIS mission of building a multi-agent pipeline where AI models validate each other’s work and produce verified builds. By fixing the script and ensuring proper deployment into the trust root, Eric is ensuring that the system’s control plane can reliably execute and validate proofs, maintaining the integrity of the containerized enforcement environment.

**What Was Learned:** The Hermes CLI v0.17.0 does not support the `model set` command with flags like `--provider` or `--base-url`. The correct approach is to use environment variables for configuration and ensure the script is properly structured and deployed with elevated privileges.

**Relevance to Frontier Model:** A frontier model must understand that CIS relies on precise CLI syntax and containerized deployment workflows. Misconfigurations in command structure can break the entire validation chain, so models must learn to validate CLI commands against actual tooling versions and ensure scripts are correctly formatted and deployed with proper permissions.

**Category:** container

**Session:** v4pro:api-6462e41c698f7f87
**Date:** 2026-06-23 01:30

**Verbatim Quotes:**
- "The model config command failed — `hermes model set --provider openai-compatible ...` was rejected. The actual Hermes v0.17.0 CLI doesn't have that subcommand."
- "The fix is already in `/tmp/`. Looking at the output, the old in_container.sh had this broken command: `hermes model set --provider openai-compatible --model ... --base-url ... --api-key unused` That syntax doesn't exist — `hermes model set` takes just a model name, no flags. Hence "unrecognized arguments.""
- "Both files need to be copied into the trust root. That requires sudo: sudo cp /tmp/harness.sh /opt/cis-control/proofs/mwl-proof/harness.sh sudo cp /tmp/in_container.sh /opt/cis-control/proofs/mwl-proof/in_container.sh"
