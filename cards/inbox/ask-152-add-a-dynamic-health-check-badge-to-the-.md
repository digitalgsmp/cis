CARD portal-health-badge: Add health-check badge to CIS portal header
SOURCE: message r1:api-28161ec61241d549, 2026-07-08 12:02
INTENT (Eric, verbatim): "Add a health-check badge to the CIS portal header showing pipeline status"
BUILD: Add a badge in the CIS portal header that displays the current health status of the gateway and the number of healthy agents.
DONE WHEN:
  - A badge appears in the portal header showing the health status and number of healthy agents
  - The badge updates in real time as the health status changes
EVIDENCE:
  - curl -s http://localhost:8080/api/adapter/health | grep -q '"status":"healthy"'
  - curl -s http://localhost:8080/api/adapter/health | grep -q '"healthy_agents":'
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
