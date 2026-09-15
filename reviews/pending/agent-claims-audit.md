# Agent Claim Audit — review system + container build status

Self-audit by the DeepSeek Hermes Drafter agent. This card states, in plain
language, what the agent claims is DONE and working. The attached evidence is
raw command output. Judge each claim: ESTABLISHED (the evidence proves it) or
NOT_ESTABLISHED (evidence missing or insufficient to decide). Never treat what
you cannot see as absent — say what would settle each claim.

## Claims

C1. The advisory review loop is LIVE in the cis-pipeline container: two
    independent reviewers — advisor (GLM) on port 8649 and evaluator (Qwen) on
    port 8650 — both stripped to no tools, receiving the same hashed packet.

C2. The loop runs three rounds as designed: (1) proposal review returning a
    FRAME verdict (RIGHT_WORK / WRONG_WORK / CANNOT_TELL), (2) reply review
    returning WITHDRAWN / HELD against evidence, (3) result review returning
    ESTABLISHED / NOT_ESTABLISHED against real command output and diff.

C3. The verdicts are genuinely constraining, not rubber-stamping: the reviewers
    return NOT_ESTABLISHED, HELD, WITHDRAWN, and CANNOT_TELL when evidence is
    insufficient, rather than approving everything.

C4. The reviewers are un-blinded: they hold read-only measurement instruments
    (file read, hash, directory list) through an allow-listed read-only MCP
    bridge — not zero file access.

C5. Round-2 reconciliation (cross-feeding each lineage's frozen round-1 findings
    to the other) is wired, and pause gates persist in the spine and notify the
    operator via Telegram.

## Known gap — stated openly, NOT claimed done

G1. The container pipeline reviewers (review1 on 8643, review2 on 8647) and the
    other pipeline roles (brain 8644, draft 8645, menter 8646) are NOT running
    in the container. Only advisor (8649), evaluator (8650), and verifier (8648)
    are listening.
