CARD portal-dark-mode-toggle: Add dark-mode toggle to settings panel
SOURCE: message v4pro:api-84bdd126730bd86e, 2026-06-24 13:31
INTENT (Eric, verbatim): "Add a dark-mode toggle to the portal settings panel"
BUILD: Add a toggle switch to the portal settings panel that allows users to switch between light and dark themes.
DONE WHEN:
  - A toggle switch is visible in the portal settings panel
  - Clicking the toggle switch changes the theme to dark mode
  - The toggle switch remains in the selected state after page refresh
EVIDENCE:
  - curl -s http://localhost:3000/settings | grep -q "dark-mode-toggle"
  - python3 -c "import json; print(json.dumps({'theme': 'dark'}))" | curl -s -H "Content-Type: application/json" -X POST -d @- http://localhost:3000/settings/theme
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
