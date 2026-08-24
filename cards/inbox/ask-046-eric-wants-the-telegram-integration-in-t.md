CARD cis-resume-telegram-fix: Resume Telegram integration in Hermes gateway
SOURCE: message r1:20260616_020627_cac045, 2026-06-16 02:06
INTENT (Eric, verbatim): "resume the last session to fix telegram" "fix whatever you can"
BUILD: Restart the Hermes gateway and ensure the Telegram integration is working by applying the correct configuration settings.
DONE WHEN:
  - The Hermes gateway is running and shows no errors in the logs
  - The Telegram bot responds to a test message sent from a user
EVIDENCE:
  - curl -s http://localhost:8080/health | grep -q "status: OK"
  - python3 -c "import requests; r = requests.post('http://localhost:8080/telegram/test', json={'text': '/start'}); print(r.status_code)"; [ $? -eq 200 ]
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
