CARD cis-restore-telegram-bot: Restore Telegram wiring for cis_braingate_bot
SOURCE: message glm-verifier:20260714_205822_47c8c95d, 2026-07-14 20:58
INTENT (Eric, verbatim): "restore cis_braingate_bot Telegram wiring for the contained Brain agent, and make it permanent this time", "the name is cis_braingate_bot. you had is working until you killed yourself changing your yamls output economy code. it was never made permanent. > had drafter deepseek fix you but it couldnt fix the telegram for the contained agents", "drafter must have put it in the host brain. HTTP API: 8624510801:AAFH7lBXV5RR3G-Oz_oXLQdSCEDgPnOjl8I"
BUILD: Configure the cis_braingate_bot container to use the correct Telegram bot token and ensure the bot remains active after restarts by setting the token as a permanent environment variable.
DONE WHEN:
  - The bot responds to a /start message in Telegram
  - The bot token is visible in the container's environment variables
  - The bot continues to work after a container restart
EVIDENCE:
  - curl -s "https://api.telegram.org/bot8624510801:AAFH7lBXV5RR3G-Oz_oXLQdSCEDgPnOjl8I/getMe" | grep -q "ok"
  - docker exec cis_braingate_bot env | grep -q "TELEGRAM_TOKEN=8624510801:AAFH7lBXV5RR3G-Oz_oXLQdSCEDgPnOjl8I"
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
