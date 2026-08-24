CARD cis-advisor-input-router: Implement AdvisorChat Input Router v0.1
SOURCE: message api-ad1cd3884171d27f, 2026-05-31 12:34
INTENT (Eric, verbatim): "Implement AdvisorChat Input Router v0.1." "Build only: classify_route() function in advisor.py, POST /api/advisor/route endpoint in advisor.py, routing_decisions SQLite table, Shared input component changes in AdvisorChat.jsx" "Do not touch: Gateway ports (8642, 8643, 8644, 8645, 8800), NeMo config or Colang flows, Model configs or Hermes profiles, Any Phase 4B knowledge base work, Any Archon verifier DAG work" "Do not change external behavior of /chat, /chat-stream, or existing advisor endpoints."
BUILD: Add a new classification function in advisor.py that routes input based on intent. Create a new API endpoint at POST /api/advisor/route to handle routing requests. Store routing decisions in a new SQLite table named routing_decisions. Update the Shared input component in AdvisorChat.jsx to send input to the new endpoint.
DONE WHEN:
  - The classify_route() function is defined in advisor.py and returns a routing decision
  - The POST /api/advisor/route endpoint is available and accepts input
  - The routing_decisions table exists in the database and stores routing results
  - The Shared input component in AdvisorChat.jsx sends input to the new endpoint
EVIDENCE:
  - python3 -c "from advisor import classify_route; print(classify_route('test'))" && echo "success"
  - curl -s -X POST http://localhost:8642/api/advisor/route -d '{"input": "test"}' | grep -q "routing"
  - sqlite3 advisor.db "SELECT name FROM sqlite_master WHERE type='table' AND name='routing_decisions'" && echo "success"
  - grep -q "POST /api/advisor/route" AdvisorChat.jsx && echo "success"
NOT IN THIS CARD: Gateway ports, NeMo config, Colang flows, Model configs, Hermes profiles, Phase 4B knowledge base, Archon verifier DAG
