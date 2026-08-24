CARD cis-v4pro-routing-verification: Add routing verification and Qwen judge gate to NeMo action registration
SOURCE: message v4pro:api-f72b181f0744a9fc, 2026-05-31 03:09
INTENT (Eric, verbatim): "Add a routing verification step to the NeMo action registration proposal to sanity-check all agent endpoints at startup." "Add a Qwen judge gate to the `cis_v4pro_r1` NeMo Guardrails config. The gate uses the Qwen model on port 8644 as a lightweight classifier to approve, block, or flag proposals before they reach the user, reducing the risk of hallucinated execution claims, unsafe directives, or malformatted output leaking through the pipeline."
BUILD: At startup, the system will check all agent endpoints to ensure they are reachable and correctly configured. A Qwen-based classifier will be used to evaluate proposals before they are sent to the user, allowing only approved ones to pass through.
DONE WHEN:
  - The system logs a message indicating that routing verification has completed successfully at startup
  - A user sees a confirmation that the Qwen judge gate is active in the NeMo Guardrails configuration
  - The system blocks a proposal that contains unsafe content and shows a rejection message
  - The system allows a valid proposal to proceed without modification
EVIDENCE:
  - curl -s http://localhost:8644/health | grep -q "healthy"
  - sqlite3 /path/to/config.db "SELECT value FROM config WHERE key = 'qwen_judge_gate_active'" | grep -q "true"
  - grep -q "Routing verification completed" /var/log/cis/startup.log
  - curl -s http://localhost:8080/proposals | grep -q "approved"
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
