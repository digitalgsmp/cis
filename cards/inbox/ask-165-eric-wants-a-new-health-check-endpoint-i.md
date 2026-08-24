CARD cis-api-health-check: Simple health check endpoint
SOURCE: message v4pro:api-c96a7427791c74f5, 2026-07-09 07:39
INTENT (Eric, verbatim): "Eric wants a simple, standalone health check at `GET /api/health` that returns: {\"status\": \"ok\", \"timestamp\": \"2026-07-09T01:23:45.678901+00:00\"}" "This is a lightweight status reflector -- no database access, no side effects, no dependencies beyond Flask."
BUILD: Add a new endpoint at `/api/health` that responds to `GET` requests with a JSON object containing the status and timestamp.
DONE WHEN:
  - A browser or curl can access `GET /api/health` and see a JSON response with status "ok" and a timestamp
EVIDENCE:
  - curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/health | grep -q "200"
  - curl -s http://localhost:5000/api/health | grep -q '"status": "ok"'
  - curl -s http://localhost:5000/api/health | grep -q '"timestamp": "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}[+-][0-9]{2}:[0-9]{2}"'
NOT IN THIS CARD: database access, side effects, dependencies beyond Flask, authentication, logging, error handling, testing, deployment, monitoring, caching
