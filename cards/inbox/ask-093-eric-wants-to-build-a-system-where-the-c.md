CARD cis-chat-to-pipeline: Chat-to-Pipeline Inference Trigger
SOURCE: message r1:api-e637710b22470fcf, 2026-06-22 23:38
INTENT (Eric, verbatim): "Chat-to-Pipeline Inference Trigger — connect Chat tab to CIS pipeline via model-inferred intent detection instead of manual Control tab submission." "User wants: Type in Chat tab → model detects task needing pipeline → auto-routes through classify_route → drafter → reviewer → deliberation → gates → result surfaces back in chat. User never leaves conversation. Trigger is model inference from full context, not keyword matching."
BUILD: When a user types in the Chat tab, the system detects that a pipeline task is needed based on the full context of the conversation, automatically routes the task through the classify_route, drafter, reviewer, deliberation, and gates stages, and returns the result directly in the chat without requiring the user to switch to the Control tab.
DONE WHEN:
  - A user types a message in the Chat tab and sees the result of a pipeline task appear in the same chat window
  - The system automatically routes the task through the classify_route, drafter, reviewer, deliberation, and gates stages without user input
  - The user does not need to navigate to the Control tab to initiate the pipeline
EVIDENCE:
  - curl -s http://localhost:8080/chat/12345 | grep -q "result"
  - sqlite3 /tmp/cis.db "SELECT COUNT(*) FROM pipeline_tasks WHERE chat_id = '12345' AND status = 'completed'"
  - python3 -c "import requests; r = requests.post('http://localhost:8080/chat', json={'text': 'test message'}); print(r.status_code == 200)"
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
