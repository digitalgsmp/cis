CARD container-secure-build: Seal config and hook at build time
SOURCE: message v4pro:20260625_025701_daed90, 2026-06-25
INTENT (Eric, verbatim): "Now I can see the full picture. The current Dockerfile seals the plugin correctly but never bakes or seals config.yaml, .env, or the hook script. Those are all written at runtime by the worker in in_container.sh — the defeatable surface." "Here's the restructure. All config setup moves into the build as the worker, then root seals the directories. The hook script moves out of /tmp into a root-owned path."
BUILD: The Dockerfile must include the config.yaml, .env, and hook script as part of the build process, and these files must be sealed during image creation. The hook script must be moved to a root-owned directory instead of /tmp.
DONE WHEN:
  - The Dockerfile includes config.yaml, .env, and the hook script as part of the image build
  - The hook script is located in a root-owned directory, not /tmp
  - The config.yaml and .env files are sealed during the build process
EVIDENCE:
  - docker build -t test-image . && docker run --rm test-image ls /root/config.yaml
  - docker build -t test-image . && docker run --rm test-image ls /root/hook.sh
  - docker build -t test-image . && docker run --rm test-image cat /root/config.yaml | grep "enable-state"
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
