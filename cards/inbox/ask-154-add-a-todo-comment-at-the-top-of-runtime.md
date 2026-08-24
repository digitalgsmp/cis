CARD cis-r1-api-c341871fbcc30dd7: Add TODO comment about refactoring relay blueprint
SOURCE: message r1:api-c341871fbcc30dd7, 2026-07-08 13:36
INTENT (Eric, verbatim): "Add a TODO comment to the top of runtime/app.py noting that the relay blueprint should be refactored into its own module"
BUILD: Add a TODO comment at the top of runtime/app.py to indicate that the relay blueprint should be moved into its own module.
DONE WHEN:
  - The file runtime/app.py contains a TODO comment at the top of the file
EVIDENCE:
  - grep -q "TODO: the relay blueprint should be refactored into its own module" runtime/app.py
NOT IN THIS CARD: refactoring, module, blueprint, relay, architecture, code structure
