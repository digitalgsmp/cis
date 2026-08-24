CARD cis-hermes-independence: Replace single Hermes install with four independent runtime cells
SOURCE: message r1:20260616_002559_47df04, 2026-06-16 00:27
INTENT (Eric, verbatim): "define the best way you can devise to replace the single installation of hermes with 4 individual entities that are full independent installations" "The best design is not 'copy the existing install four times.' The best design is make each Hermes profile a self-contained runtime cell with its own source tree, venv, service unit, logs, and verification gate, while preserving the existing profile homes and ports."
BUILD: Create four separate Hermes installations, each with its own source tree, virtual environment, service unit, logs, and verification process, while keeping the same profile homes and ports.
DONE WHEN:
  - Each profile (r1, v4pro, v4impl, etc.) has its own source tree in ~/.hermes/
  - Each profile has its own virtual environment in ~/.hermes/venv/
  - Each profile has its own service unit file in /etc/systemd/system/
  - Each profile has its own log directory in ~/.hermes/logs/
EVIDENCE:
  - test -d ~/.hermes/r1/source && test -d ~/.hermes/v4pro/source && test -d ~/.hermes/v4impl/source && test -d ~/.hermes/other/source
  - test -f ~/.hermes/r1/venv/bin/python && test -f ~/.hermes/v4pro/venv/bin/python && test -f ~/.hermes/v4impl/venv/bin/python && test -f ~/.hermes/other/venv/bin/python
  - test -f /etc/systemd/system/hermes-r1.service && test -f /etc/systemd/system/hermes-v4pro.service && test -f /etc/systemd/system/hermes-v4impl.service && test -f /etc/systemd/system/hermes-other.service
  - test -d ~/.hermes/r1/logs && test -d ~/.hermes/v4pro/logs && test -d ~/.hermes/v4impl/logs && test -d ~/.hermes/other/logs
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
