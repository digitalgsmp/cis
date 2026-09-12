#!/usr/bin/env python3
"""intent_bridge.py — the live clarify -> confirm -> gate -> route.

The single missing artifact of the front door (DEV-PIVOT-08/09). The router
keyword-matches and the MCP dispatch tools fire on demand; neither forces the
step Eric named: Brain clarifies the intention, Eric confirms it, and only the
CONFIRMED clarification's direction routes to an action.

This tool is the deterministic gate + route:

  1. Record the clarified intent to intent_map with review_decision='CONFIRMED'
     and eric_confirmed_at=now. That field is the deterministic gate — the
     confirmation is data, not a model's guess. (Same gate the offline
     CIS_INTENT_ALIGNMENT_WORKFLOW_SPEC pipeline uses.)
  2. Route on the confirmed direction. `--direction` is a controlled vocabulary,
     NOT a free-form model guess; each value maps to one pipeline entry point:
       next       -> propose_next.py   (answer "what's next / what else")
       draft      -> drafter_start.py  (draft/spec a crystallized topic)
       review     -> reviewer_reconcile.py
       implement  -> hermes-v4impl (implementer) — REFUSED without Eric Gate approval

It refuses to fire without --confirm: the whole point is that nothing dispatches
on a raw phrase. Brain (8644) calls this AFTER Eric confirms the clarification,
so the pipeline fires on the confirmed direction, not on "draft this" keyword
matching.

Usage:
    python3 tools/intent_bridge.py --topic "..." --intent "..." \
        --interpretation "..." --direction next --confirm

Without --confirm it prints what it WOULD record and route, and exits 2.
"""
import argparse
import datetime
import os
import sqlite3
import subprocess
import sys

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
REPO = os.environ.get("CIS_REPO_ROOT", "/mnt/projects/cis")

# controlled direction vocabulary -> pipeline entry point
DIRECTIONS = {
    "next": ("tools/queue/propose_next.py", []),
    "draft": ("tools/pipeline/drafter_start.py", None),  # args built from topic
    "review": ("tools/pipeline/reviewer_reconcile.py", None),
    "implement": None,  # handled specially — requires Eric Gate approval
}


def record_intent(topic, intent, interpretation, direction, by):
    """Write the confirmed intent to intent_map. The deterministic gate."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = sqlite3.connect(DB)
    cur = conn.execute(
        "INSERT INTO intent_map "
        "(intent_text, model_interpretation, mapped_layer, mapped_component, "
        " source_file, voice, review_decision, eric_confirmed_at) "
        "VALUES (?,?,?,?,?, 'eric-verbatim', 'CONFIRMED', ?)",
        (intent or topic, interpretation, "abstraction-layer", direction,
         "live:intent_bridge", now))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid, now


def route(direction, topic, intent):
    """Return (script, argv) for the confirmed direction, or None if refused."""
    if direction == "implement":
        # Implementer requires a prior Eric Gate approval — refuse to build
        # blindly. This is the one direction this tool will not fire on its own.
        return None, ["REFUSED: implement requires Eric Gate approval first"]
    if direction == "draft":
        return DIRECTIONS["draft"][0], [topic, "--intent", intent]
    if direction == "review":
        return DIRECTIONS["review"][0], ["--run-id", topic]  # topic = run_id
    entry = DIRECTIONS.get(direction)
    if entry is None:
        return None, ["REFUSED: unknown direction %r (known: %s)"
                      % (direction, ", ".join(sorted(DIRECTIONS)))]
    return entry[0], entry[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, help="the crystallized work description")
    ap.add_argument("--intent", required=True, help="why — the underlying need")
    ap.add_argument("--interpretation", default="", help="model's reading of the intent")
    ap.add_argument("--direction", required=True,
                    choices=sorted(DIRECTIONS) + ["implement"],
                    help="confirmed direction (controlled vocabulary)")
    ap.add_argument("--confirm", action="store_true",
                    help="Eric confirmed the clarification — record the gate and fire")
    ap.add_argument("--by", default="", help="who confirmed")
    a = ap.parse_args()

    if a.direction == "implement":
        print("implement is refused by intent_bridge — it requires Eric Gate "
              "approval on a completed run, not a fresh dispatch.")
        return 2

    if not a.confirm:
        print("NOT CONFIRMED — nothing fired.")
        print("Would record to intent_map:")
        print("  intent:     %s" % a.intent[:80])
        print("  direction:  %s" % a.direction)
        print("  route:      %s" % DIRECTIONS[a.direction][0])
        print("Add --confirm (Eric confirmed the clarification) to fire.")
        return 2

    rid, now = record_intent(a.topic, a.intent, a.interpretation, a.direction,
                             a.by or os.environ.get("USER", ""))
    script, argv = route(a.direction, a.topic, a.intent)
    if script is None:
        print("\n".join(argv))
        return 2

    print("intent_map #%d recorded CONFIRMED at %s" % (rid, now))
    print("routing %s -> %s" % (a.direction, script))
    r = subprocess.run(
        [sys.executable, os.path.join(REPO, script)] + (argv or []),
        cwd=REPO, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.stderr:
        sys.stderr.write(r.stderr[-2000:])
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
