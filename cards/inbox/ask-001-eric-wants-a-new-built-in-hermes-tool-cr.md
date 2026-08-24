CARD cis-retrieve-from-kb: Create Hermes built-in tool to retrieve from knowledge base
SOURCE: message qwen:20260521_001941_299714, 2026-05-21 00:19
INTENT (Eric, verbatim): "Create a Hermes built-in tool: retrieve_from_knowledge_base", "Return format: [{session_id, role, content, score, timestamp, source}]", "Execute the following directive."
BUILD: Add a new built-in tool in Hermes called retrieve_from_knowledge_base that accepts a query and returns results in a structured JSON format with session_id, role, content, score, timestamp, and source fields.
DONE WHEN:
  - A new tool named retrieve_from_knowledge_base appears in the Hermes tool list
  - The tool accepts a text query and returns a JSON array with the specified fields
  - The results include data from both FTS5 and ChromaDB searches
  - The tool supports multi-profile queries and returns hybrid results
EVIDENCE:
  - curl -s http://localhost:8080/api/tools | grep -q '"name": "retrieve_from_knowledge_base"'
  - curl -s -X POST http://localhost:8080/api/tool/retrieve_from_knowledge_base -d '{"query": "test"}' | python3 -c "import sys, json; data=json.load(sys.stdin); print('session_id' in data[0] if data else False)"
  - curl -s -X POST http://localhost:8080/api/tool/retrieve_from_knowledge_base -d '{"query": "test"}' | python3 -c "import sys, json; data=json.load(sys.stdin); print('role' in data[0] if data else False)"
  - curl -s -X POST http://localhost:8080/api/tool/retrieve_from_knowledge_base -d '{"query": "test"}' | python3 -c "import sys, json; data=json.load(sys.stdin); print('score' in data[0] if data else False)"
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
