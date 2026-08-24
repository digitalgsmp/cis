CARD cis-v4pro: add todo comment about relay refactoring
SOURCE: message v4pro:api-2b8e5da89f7db408, 2026-07-08 13:37
INTENT (Eric, verbatim): "Add a TODO comment to the top of runtime/app.py noting that the relay blueprint should be refactored into its own module"
BUILD: Add a TODO comment at the top of runtime/app.py to indicate that the relay blueprint should be refactored into its own module.
DONE WHEN:
  - A TODO comment is visible at the top of runtime/app.py
EVIDENCE:
  - grep -q "TODO: relay blueprint should be refactored into its own module" runtime/app.py
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
