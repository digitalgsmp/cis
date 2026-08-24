CARD cis-api-health-check: Add health check endpoint
SOURCE: message r1:api-1278c2a0638f2aea, 2026-07-08 23:11
INTENT (Eric, verbatim): "Add a health check endpoint at /api/health that returns JSON with status ok and timestamp"
BUILD: Add a new endpoint at /api/health that returns a JSON response with status and timestamp when accessed.
DONE WHEN:
  - A GET request to /api/health returns a JSON response with status and timestamp
EVIDENCE:
  - curl -s http://localhost:5000/api/health | grep -q '"status":"ok"'
  - curl -s http://localhost:5000/api/health | grep -q '"timestamp"'
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
