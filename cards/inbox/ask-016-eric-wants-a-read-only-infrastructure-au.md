CARD cis-verify-port-status: Qwen agent reports working directory and port listening status
SOURCE: message v4pro:api-21903888de5947de, 2026-05-31 04:27
INTENT (Eric, verbatim): "Draft a FINAL_DIRECTIVE for Qwen to report the current working directory and verify whether ports 8642, 8643, 8644, 8645, and 8800 are listening. Do not edit files."
BUILD: The Qwen agent will report the current working directory and check if ports 8642, 8643, 8644, 8645, and 8800 are listening, without modifying any files.
DONE WHEN:
  - The agent outputs the current working directory in the response
  - The agent confirms which of the ports 8642, 8643, 8644, 8645, and 8800 are listening
EVIDENCE:
  - python3 -c "import os; print(os.getcwd())" | grep -q "/home/eric"
  - netstat -tuln | grep -q "8642"
  - netstat -tuln | grep -q "8643"
  - netstat -tuln | grep -q "8644"
  - netstat -tuln | grep -q "8645"
  - netstat -tuln | grep -q "8800"
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
