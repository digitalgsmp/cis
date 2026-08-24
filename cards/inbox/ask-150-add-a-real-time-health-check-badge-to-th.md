CARD portal-health-badge: Add health-check badge to CIS portal header
SOURCE: message v4pro:api-2c1086a9a50a5796, 2026-07-08 11:57
INTENT (Eric, verbatim): "Add a health-check badge to the CIS portal header showing pipeline status"
BUILD: Replace the static "● kernel" text in the CIS portal header with a dynamic health-check badge that shows the status of the six pipeline gateway profiles.
DONE WHEN:
  - The CIS portal header displays a real-time health-check badge instead of the static "● kernel" text
  - The badge updates automatically as pipeline statuses change
EVIDENCE:
  - curl -s http://localhost:8080/api/health | grep -q '"status": "healthy"'
  - curl -s http://localhost:8080/api/health | grep -q '"gateway_profiles": 6'
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
