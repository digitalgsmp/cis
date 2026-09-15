#!/usr/bin/env python3
"""Answer, in plain language: what did I ask for, does it do that yet, what is in the way.

Built 2026-09-09 because the operator said the reporting was unreadable to him:
"I ask for it to do xyz, is it doing xyz and if not what needs to be addressed
to make it work. That is what I should be choosing from."

Everything printed here is in the operator's shape, not the machinery's. No
component names, no file names, no card names, no assumption that he remembers
a previous session.

THE SOURCE IS THE REVIEWERS, NOT CLAUDE CODE. The capability list is read from
the most recent slate the two reviewers produced -- their words, as recorded in
deliberation_rounds. Claude Code writing its own progress report is the thing
this exists to stop.

Usage:  python3 tools/where_are_we.py
"""
import json
import os
import re
import sqlite3
import sys

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")


def latest_slate(conn):
    """The newest capability list any reviewer produced. Returns [(wanted, works, needed)]."""
    rows = conn.execute(
        "SELECT objections_json FROM deliberation_rounds "
        "WHERE round_number = 3 AND reviewer_role != 'pause' "
        "ORDER BY created_at DESC LIMIT 6").fetchall()
    for (oj,) in rows:
        try:
            body = json.loads(oj)[0].get("objection", "")
        except Exception:
            continue
        entries, cur, last = [], {}, None
        for line in body.split("\n"):
            t = line.strip().lstrip("*# ").strip()
            m = re.match(r"^(WANTED|WORKS TODAY|NEEDED)\s*:\s*(.+)$", t, re.I)
            if m:
                field, val = m.group(1).upper(), m.group(2).strip()
                if field == "WANTED":
                    if cur.get("WANTED"):
                        entries.append(cur)
                    cur = {"WANTED": val}
                else:
                    cur[field] = val
                last = field
            elif t and last and cur:
                # A wrapped continuation of the field above. Without this the
                # tail of a sentence is silently dropped and words fuse.
                cur[last] = (cur[last] + " " + t).strip()
            elif not t:
                last = None
        if cur.get("WANTED"):
            entries.append(cur)
        if entries:
            return entries
    return []


def waiting(conn):
    rows = conn.execute(
        "SELECT run_id, objections_json FROM deliberation_rounds "
        "WHERE reviewer_role='pause' AND reviewer_signal='PENDING'").fetchall()
    out = []
    for run_id, oj in rows:
        card = run_id[len("advisor-"):-len("-pause")]
        try:
            stop = json.loads(oj)[0].get("stop", "")
        except Exception:
            stop = ""
        plain = {
            "card-written": "a plan is written and not yet checked",
            "reviews-landed": "it has been checked and is ready to run",
            "result-reviewed": "it has run and been checked",
        }.get(stop, stop)
        out.append((card, plain))
    return out


def wrap(text, width, indent):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(indent + line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(indent + line)
    return out


def main():
    conn = sqlite3.connect(DB)
    L = ["", "WHERE THE BUILD IS", "=" * 60, ""]

    entries = latest_slate(conn)
    if not entries:
        L.append("No capability list has been produced yet. It comes from the")
        L.append("reviewers when a piece of work finishes.")
    else:
        L.append("WHAT YOU ASKED FOR, AND WHETHER IT DOES IT")
        L.append("")
        for i, e in enumerate(entries, 1):
            works = e.get("WORKS TODAY", "")
            head = works.split("—")[0].split("--")[0].strip().rstrip(".").upper()
            flag = {"YES": "YES   ", "PARTLY": "PARTLY", "NO": "NO    "}.get(head, "?     ")
            # Strip the component label wherever it sits. The reviewers are
            # asked to put it in brackets; the operator does not read them.
            want = re.sub(r"\s*\[[^\]]*\]", "", e["WANTED"]).strip(" .") + "."
            wl = wrap(want, 50, "")
            L.append("%s  %d. %s" % (flag, i, wl[0]))
            for extra in wl[1:]:
                L.append(" " * 11 + extra)
            rest = works.split("—", 1)[-1].split("--", 1)[-1].strip()
            if rest and rest.upper() != head:
                L += wrap("now: " + rest, 56, " " * 11)
            if e.get("NEEDED"):
                L += wrap("in the way: " + e["NEEDED"], 56, " " * 11)
            L.append("")

    w = waiting(conn)
    L.append("-" * 60)
    if not w:
        L.append("NOTHING IS WAITING ON YOU.")
    else:
        L.append("WAITING ON YOU (%d):" % len(w))
        for card, plain in w:
            L.append("  %s — %s" % (card, plain))
    L.append("")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
