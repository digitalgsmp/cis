CARD cis-r1:api-ec6b3a5fa3b92900: Add TODO comment about relay blueprint refactor
SOURCE: message r1:api-ec6b3a5fa3b92900, 2026-07-08 13:40
INTENT (Eric, verbatim): "Add a TODO comment to the top of runtime/app.py noting that the relay blueprint should be refactored into its own module"
BUILD: Add a TODO comment at the top of runtime/app.py to indicate that the relay blueprint should be refactored into its own module.
DONE WHEN:
  - The file runtime/app.py contains a TODO comment at the top of the file
EVIDENCE:
  - grep -q "TODO: the relay blueprint should be refactored into its own module" runtime/app.py
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
