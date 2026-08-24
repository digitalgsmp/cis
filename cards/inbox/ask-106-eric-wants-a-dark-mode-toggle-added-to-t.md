CARD portal-dark-mode-toggle: Add dark-mode toggle to settings panel
SOURCE: message r1:api-d57f18fdf985d505, 2026-06-24 13:20
INTENT (Eric, verbatim): "PROPOSAL: Add a dark-mode toggle to the portal settings panel."
BUILD: Add a toggle switch to the portal settings panel that lets users switch between light and dark themes. When toggled, the theme should change immediately and be saved to localStorage so it persists across sessions.
DONE WHEN:
  - A toggle switch appears in the portal settings panel
  - Clicking the toggle changes the theme to dark or light
  - The selected theme persists after refreshing the page
EVIDENCE:
  - curl -s http://localhost:3000/settings | grep -q 'dark-mode toggle'
  - curl -s http://localhost:3000/settings | grep -q 'data-theme="dark"'
  - curl -s http://localhost:3000/settings | grep -q 'data-theme="light"'
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
