#!/usr/bin/env python3
"""classify_check.py — deterministic item classification feeding item selection.

Classifies every queue item RUNNABLE / JUDGMENT / NO_CHECK by fixed rules, not
human reading, and writes the result to queue_items.check_class. That column is
the routing primitive for the 'where to start' mechanism:

    RUNNABLE   an agent can advance it by running its check — no Eric
    JUDGMENT   only Eric can decide it — surfaces as a NEEDS_ERIC question
    NO_CHECK   blocked — no check written, so nobody can assess it yet

Same input always yields the same class, new items included, so a fresh item can
no longer land in NO_CHECK just because no one read it by eye.

Decision order (deterministic, first hit wins):
  1. An explicit check-bearing field — 'The one check that settles it:',
     'Checked:', 'Evidence:', or 'In code:' — is classified on its own text;
     but a field that yields NO signal falls through to the body, because a
     vague check line must not hide a concrete claim in the body.
  2. The title + body is classified: RUNNABLE if it states a verifiable claim
     (a file/table/column/count/command/state a command settles); else JUDGMENT
     if it asks a decision or is a bare build directive; else NO_CHECK.

Usage:
    python3 tools/queue/classify_check.py             # classify all, write column
    python3 tools/queue/classify_check.py --report    # classify, print counts only
    python3 tools/queue/classify_check.py --why <num> # print one item's reason
"""

import os
import re
import sqlite3
import sys

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")

# ── JUDGMENT: a decision, or a bare build directive with no verifiable claim ─
DECISION_RE = re.compile(
    r"\b(decide|should|still wanted|still in use|worth|drop or postpone|"
    r"ask the (?:advisor|evaluator|reviewer|model)|Eric's decision|settle)\b",
    re.I,
)
DIRECTIVE_RE = re.compile(
    r"^(Stream|Add|Build|Secure|Automate|Wire|Close|Finish|Retire|Settle|Define|"
    r"Lock|Group|Implement|Record|Resolve|Fix|Constrain|Move|Approve|Give|Prove|"
    r"Remove|Make|Generalise|Reduce|Create|Enable|Disable|Restore)\b",
    re.I,
)

# ── RUNNABLE: the item states a claim a command settles. ─────────────────────
RUNNABLE_RES = [
    (re.compile(r"\b[\w./-]+\.(py|sh|sql|md|json|yaml|yml|toml|js|css):\d+"), "file:line"),
    (re.compile(r"\b[\w./-]+\.(py|sh|sql|md|json|yaml|yml|toml|js|css)\b"), "file"),
    (re.compile(r"`[^`]+`"), "code/path"),
    (re.compile(r"(?:[A-Za-z_][\w.-]*/)+[\w.-]+"), "path"),
    (re.compile(r"\b(grep|count|select|md5|diff|pytest|curl|port|pragma|"
                r"check-ignore|md5sum|sqlite3|query|re-run)\b", re.I), "command"),
    (re.compile(r"\b(blocks?|warns?|hardcodes?|measured|verified|proven|checked|"
                r"running|reads|writes|records|returns|truncates?|duplicates?|"
                r"shares?|differs?|disagrees?)\b", re.I), "state"),
    (re.compile(r"\b(NULL|null|absent|present|missing)\b"), "presence"),
    (re.compile(r"\b\d+\s+(of|in|times|rows|items|artifacts|docs|specs|files|"
                r"scripts|sites|configs)\b|returns 0|0 times|LIMIT \d+", re.I),
     "measure"),
    (re.compile(r"\b[a-z_]+\.(id|name|status|project_id|need_status|"
                r"old_value|new_value|evidence|source_sha)\b"), "column"),
]

# check-bearing fields, in priority order (most explicit first)
FIELD_RES = [
    (re.compile(r"\*\*The one check that settles it:\*\*\s*([^\n]+)"), "check"),
    (re.compile(r"\*\*Checked:?\*\*[: ]*([^\n]+)"), "checked"),
    (re.compile(r"\*\*Evidence:?\*\*[: ]*([^\n]+)"), "evidence"),
    (re.compile(r"\*\*In code:?\*\*[: ]*([^\n]+)"), "in-code"),
]


def _runnable_signal(text):
    for rx, label in RUNNABLE_RES:
        m = rx.search(text)
        if m:
            return label, m.group(0)[:60]
    return None, None


def _decide(text):
    m = DECISION_RE.search(text)
    if m:
        return "JUDGMENT", "decision verb: %r" % m.group(0)
    label, hit = _runnable_signal(text)
    if label:
        return "RUNNABLE", "%s: %r" % (label, hit)
    return "NO_CHECK", "no runnable or judgment signal"


def classify(title, body):
    """Return (check_class, reason) for one item.

    Decision verbs are judged only on the title + check field + first body line
    (where an item states its nature); an incidental 'should' deep in the prose
    must not flip a runnable claim into a judgment. Runnable signals are judged
    anywhere, because a concrete claim anywhere means a command could settle it.
    """
    # 1. explicit check fields first, but a NO_CHECK field falls through
    for rx, label in FIELD_RES:
        m = rx.search(body)
        if m and m.group(1).strip():
            cls, why = _decide(m.group(1).strip())
            if cls != "NO_CHECK":
                return cls, "%s field -> %s" % (label, why)
    # 2. title + first body line: decision verbs matter here
    first = next((l for l in body.split("\n")
                  if l.strip() and not l.startswith("#") and not l.startswith("**")), "")
    cls, why = _decide((title + "\n" + first).strip())
    if cls != "NO_CHECK":
        return cls, "title/first-line -> %s" % why
    # 3. full body: runnable signal only (a concrete claim anywhere)
    label, hit = _runnable_signal(body)
    if label:
        return "RUNNABLE", "body -> %s: %r" % (label, hit)
    # 4. bare build directive with no claim
    if DIRECTIVE_RE.search(title.strip()):
        return "JUDGMENT", "bare build directive, no verifiable claim"
    return "NO_CHECK", "no runnable or judgment signal"


def ensure_column(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(queue_items)")}
    if "check_class" in cols:
        return False
    conn.execute(
        "ALTER TABLE queue_items ADD COLUMN check_class TEXT "
        "CHECK (check_class IN ('RUNNABLE','JUDGMENT','NO_CHECK'))"
    )
    conn.commit()
    return True


def main():
    conn = sqlite3.connect(DB)
    if ensure_column(conn):
        print("added queue_items.check_class")

    rows = conn.execute(
        "SELECT item_num, title, body_md FROM queue_items ORDER BY item_num"
    ).fetchall()

    counts = {"RUNNABLE": 0, "JUDGMENT": 0, "NO_CHECK": 0}
    updates = []
    why_target = None
    if "--why" in sys.argv:
        why_target = sys.argv[sys.argv.index("--why") + 1]

    for num, title, body in rows:
        cls, why = classify(title, body)
        counts[cls] += 1
        updates.append((cls, num))
        if num == why_target:
            print("[%s] %s\n    %s" % (num, cls, why))

    if "--report" not in sys.argv and "--why" not in sys.argv:
        conn.executemany(
            "UPDATE queue_items SET check_class=? WHERE item_num=?",
            [(cls, num) for cls, num in updates],
        )
        conn.commit()
        print("wrote check_class for %d items" % len(updates))

    total = sum(counts.values())
    print("RUNNABLE  %3d  (%d%%)" % (counts["RUNNABLE"], 100 * counts["RUNNABLE"] // total))
    print("JUDGMENT  %3d  (%d%%)" % (counts["JUDGMENT"], 100 * counts["JUDGMENT"] // total))
    print("NO_CHECK  %3d  (%d%%)" % (counts["NO_CHECK"], 100 * counts["NO_CHECK"] // total))
    print("total     %3d" % total)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
