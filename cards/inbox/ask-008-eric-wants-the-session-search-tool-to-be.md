CARD cis-session_search-profile: Add profile parameter to session_search tool
SOURCE: message r1:20260522_175442_698d1c, 2026-05-22 17:54
INTENT (Eric, verbatim): "Resume Phase 1 of the Unified Knowledgebase Architecture — add the `profile` parameter to `session_search` tool."
BUILD: The session_search tool will accept a new `profile` parameter, allowing users to filter search results by a specific profile. When the parameter is provided, the tool will route the query to the appropriate profile-specific index.
DONE WHEN:
  - The session_search tool accepts a `profile` parameter in its input
  - The tool returns search results filtered by the specified profile
EVIDENCE:
  - curl -s "http://localhost:8080/session_search?profile=agent1&query=test" | grep -q "results"
  - sqlite3 /tmp/cis.db "SELECT name FROM sqlite_master WHERE type='table' AND name='profile_agent1'" | grep -q "profile_agent1"
NOT IN THIS CARD: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure
