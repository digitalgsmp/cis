CARD portal-resizable-panels: Make portal panels resizable and full-screen
SOURCE: message v4pro:api-ee3f0c18c3b5f2d0, 2026-06-21 21:49
INTENT (Eric, verbatim): "can you make the portal panels resizable and full screen to the browser dimensions"
BUILD: Users can drag the edges of portal panels to resize them and see the panels fill the entire browser window.
DONE WHEN:
  - A user can drag the border between two panels to change their size
  - The panels automatically adjust to fill the full width and height of the browser window
EVIDENCE:
  - curl -s http://localhost:8080/portal | grep -q "resizable-panel"
  - curl -s http://localhost:8080/portal | grep -q "full-screen"
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
