# Advisor review — container-loop-residency

- packet: `reviews/pending/container-loop-residency.md`
- advisor: advisor on port 8649
- run tag: container-loop-residency @ 2026-09-13T11:31:53-05:00
- at: 2026-09-13T11:33:34
- prompt_tokens: 222561
- completion_tokens: 3764
- total_tokens: 226325
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

I have now verified all material claims in this card. Let me compile the review.

FRAME: RIGHT_WORK

Eric's directive to "replicate all of that structure into the container" and his correction that "pause notify was not suppose to be built on the host in the first place" are corroborated by the broader project trajectory — multiple knowledge-base entries show Eric repeatedly pushing to build into the container and retire host infrastructure (km_300336: "build that into the container"; km_887666: "kill the docker telegram until the full transition is complete"; km_300214: "i need this stuff built it the container"). The review loop driver is the last host-resident piece of the pipeline that actually executes logic, and moving it is the direct continuation of the host retirement that began with the container build. The item is right; the timing is right; it is what the project is for.

---

REVIEW OF THE CARD — evidence-verified findings

VERIFIED CLAIMS (all checked against source):

1. docker exec call sites at lines 498, 705, 838 — CONFIRMED.
   Source: cis_search_files on tools/advisor_review.sh for "docker exec" returned exactly those three lines plus two comments (125, 851).

2. CIS_CONTAINER default at line 131 — CONFIRMED.
   Source: cis_search_files for "CONTAINER.*cis-pipeline" returned line 131: CONTAINER="${CIS_CONTAINER:-cis-pipeline}".

3. DB default hardcoded to host path at lines 212, 570, 942 — CONFIRMED.
   Source: cis_search_files for "CIS_SPINE_PATH" returned all three lines, each defaulting to "/mnt/projects/cis/data/cis_memory.db".

4. pause_notify.py hardcodes host paths — CONFIRMED.
   - Line 42: REPO = "/mnt/projects/cis" (hardcoded, not env-derived).
   - Line 43: ENV_FILE defaults to "/home/eric/.hermes/.env".
   Source: cis_read_file of tools/pause_notify.py, and cis_search_files for "/home/eric" returned line 43.

5. pause_notify.py invoked at line 294 of advisor_review.sh — CONFIRMED.
   Source: cis_search_files for "pause_notify" returned line 294: python3 "$REPO_ROOT/tools/pause_notify.py" "$ID" "$1".

6. REPO_ROOT resolves via dirname of BASH_SOURCE — CONFIRMED.
   Line 130: REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)". This is path-relative, so inside the container it resolves to /workspace/cis. The card's claim that "REPO_ROOT resolves correctly when invoked from the container path" is correct.

7. entrypoint.sh starts 8 gateways (8644-8650) + Flask API + reply_consumer — CONFIRMED.
   Source: cis_read_file of enforcement/mwl-proof-v2/entrypoint.sh. PROFILES array has 8 entries (brain draft review1 review2 menter verify advisor evaluator), PORTS array has 8 entries (8644 8645 8643 8647 8646 8648 8649 8650). reply_consumer.py is started conditionally on CIS_TG_NOTIFY_TOKEN at the end of the script.

8. reply_consumer.py is already container-resident and uses container paths — CONFIRMED.
   Source: cis_read_file of tools/reply_consumer.py. Line: REPO = os.environ.get("CIS_REPO_ROOT", "/workspace/cis"). DB defaults to f"{REPO}/data/cis_memory.db". Token from CIS_TG_NOTIFY_TOKEN env or /workspace/secrets.env fallback. No /home/eric references. This file is already container-native.

9. pause_notify.py already has partial CIS_TG_NOTIFY_TOKEN support — CONFIRMED but incomplete.
   Line 348: token = (os.environ.get("CIS_TG_NOTIFY_TOKEN") or read_env("/mnt/projects/cis/secrets.env").get(...). The env-var path works in-container, but the fallback still points to a host path, and ENV_FILE (line 43) and REPO (line 42) are still hardcoded host paths. The card correctly identifies these.

10. Card claims the container has no docker binary — NOT VERIFIED. I cannot run docker commands or inspect the container from my read-only instruments. The claim is plausible and likely correct (containers typically don't have the docker client), but I could not confirm it from the repo. This is the one claim I could not verify.

---

ISSUES AND CORRECTIONS

ISSUE 1 — Card says entrypoint starts "8 gateways (8644-8650)" but the port list has a gap.

The PORTS array is (8644 8645 8643 8647 8646 8648 8649 8650). Port 8643 is review1, which is out of sequence. The entrypoint header comment itself says "Gateway ports: 8644-8648 (internal only)" — it does not mention 8649-8650 in that comment line, though the PROFILES/PORTS arrays do include advisor and evaluator. This is a documentation inconsistency in entrypoint.sh, not in the card, but the card should note it: the gateways are on 8643-8650, not a clean 8644-8650 range.

ISSUE 2 — pause_notify.py REPO is hardcoded, not env-derived.

The card's R3 says to fix pause_notify.py to resolve DB from CIS_SPINE_PATH. But it does not mention that REPO (line 42) is also hardcoded to "/mnt/projects/cis". The resolve_for() function uses os.path.join(REPO, "reviews", "done", ...) and card_ask() uses os.path.join(REPO, "reviews/pending", ...). These will break inside the container. R3 should also change REPO to be env-derived:

    REPO = os.environ.get("CIS_REPO_ROOT", "/workspace/cis")

This is the same pattern reply_consumer.py already uses. The card misses this.

ISSUE 3 — pause_notify.py has a /mnt/projects/cis/secrets.env fallback in send().

Line 349: read_env("/mnt/projects/cis/secrets.env").get("CIS_TG_NOTIFY_TOKEN", ""). Inside the container this path does not exist (secrets are at /workspace/secrets.env, sourced by entrypoint.sh). The card's R3 says to remove the /home/eric/.hermes/.env dependency, but does not mention this second host-path fallback in the token resolution chain. It should be changed to /workspace/secrets.env or removed entirely (the env var is already set by entrypoint.sh's source).

ISSUE 4 — The card does not address the where_are_we.py import in pause_notify.py.

pause_notify.py line: from where_are_we import latest_slate, with sys.path.insert(0, os.path.join(REPO, "tools")). If REPO is fixed to /workspace/cis, this import will work — but only if where_are_we.py is present at /workspace/cis/tools/where_are_we.py. The card should verify this file exists inside the container (it is in the bind mount, so it should, but the card should state it).

ISSUE 5 — The Eric directive quotes could not be verified verbatim.

I searched the knowledge base with multiple queries for both quoted directives ("replicate all of that structure into the container" and "pause notify was not suppose to be built on the host"). Neither returned an exact match. The closest results (km_300336, km_300214, km_887666) show Eric repeatedly directing work into the container and retiring host infrastructure, which is directionally consistent. But I cannot confirm the card's quotes are verbatim Eric words from 2026-09-13. The card attributes them to "2026-09-13" which is today — they may be from a session not yet indexed in the knowledge base. This is not necessarily wrong, but I cannot verify it, and the card should note the source session.

---

ANSWERS TO THE CARD'S REVIEWER QUESTIONS

Q1: Is the mode-guard (R2) the right transition mechanism, or should docker exec be deleted outright?

The mode-guard is the right call. The host path is the only proven path right now, and the container path has never been exercised end-to-end. A guard that defaults to the existing host behavior and activates container mode via CIS_CONTAINER_MODE=1 is the lowest-risk transition. Deleting docker exec outright would make the host driver non-functional before the container path is proven, which violates ADR-SEED-002 (verification-hardening: completion accepted only after deterministic evidence). The guard stays until R6 passes, then R5 removes it. This is correct.

Q2: Should CIS_SPINE_PATH be mandatory in container mode, or default to /workspace/cis/data/cis_memory.db?

Default to /workspace/cis/data/cis_memory.db, not mandatory. The pattern across the codebase is env-with-default. reply_consumer.py already defaults to /workspace/cis/data/cis_memory.db and works. Making it mandatory adds a failure mode for no benefit — the container path is deterministic. The card's own R1 suggests "prefer mandatory and fail fast," but this contradicts the established pattern and adds friction without safety. Default to the container path.

Q3: Is on-demand invocation (R4) correct, or does the loop need a watcher?

On-demand is correct. The project's invariant is pull-only — Eric starts each session, nothing self-starts. This is consistent across the codebase: reply_consumer.py is the only long-running process, and it is a poller that releases pauses, not a loop driver. The pause row is the waiting state, not a blocked process (pause_notify.py module note, lines at the bottom of the file). A watcher would contradict this design. R4 is right.

Q4: Anything the host loop does today that this card's six work items miss?

Yes — three things:

(a) The REPO hardcoded path in pause_notify.py (line 42), as noted in ISSUE 2 above. The card's R3 addresses DB and token but misses REPO.

(b) The /mnt/projects/cis/secrets.env fallback in pause_notify.py's send() function (line 349), as noted in ISSUE 3.

(c) The card does not address what happens to pause_notify.py's build_context() function, which imports where_are_we.py. If REPO is fixed, this should work, but it is an untested import path inside the container and should be explicitly verified in R6.

Additionally, the card does not mention that advisor_review.sh itself contains embedded Python (the DB = os.environ.get lines are inside heredoc-quoted Python blocks, not shell variables). R1 says to "change the three DB-default strings" — this is correct, but Menter needs to know these are inside Python heredocs, not shell assignments, to avoid a sed mistake.

---

SUMMARY

The card is the right work at the right time. Every code-level claim I could verify from the repo checked out exactly (line numbers, paths, call sites, entrypoint contents, reply_consumer state). The work items are sound and correctly scoped. Three additions are needed before Menter executes:

1. R3 must also fix REPO (line 42 of pause_notify.py) to env-derived /workspace/cis.
2. R3 must also fix the /mnt/projects/cis/secrets.env fallback (line 349) to /workspace/secrets.env or remove it.
3. R6 should explicitly verify the where_are_we.py import works inside the container.

The Eric directive quotes are directionally consistent with the knowledge base but could not be verified verbatim — the card should cite the session they came from.
