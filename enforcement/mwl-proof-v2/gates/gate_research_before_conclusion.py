#!/usr/bin/env python3
"""gate_research_before_conclusion.py — refuse unresearched claims of absence.

Exit 0: PASS — no absence claims, or every one is backed by the record
Exit 1: FAIL — the agent declared something missing that the record already
        explains (a decision, a deferral, a supersession)
Exit 2: SKIP — no output to check, or the knowledge base is unreachable

WHY THIS EXISTS
A model that finds something absent reports it as a defect. Absence and defect
are not the same thing: the thing may have been rejected, deferred, superseded,
or staged deliberately, and that reasoning is already in the knowledge base.
Reporting a decision as a gap sends the next session to rebuild something that
was thrown away on purpose. That is the single most expensive recurring failure
in this project's history, and it is invisible to the model committing it —
which is exactly what a deterministic gate is for.

Observed 2026-08-27, four times in one session: the orchestrator (set aside, no
ADR), container session logs (deliberate staging), NeMo (rejected on record for
stripping reasoning metadata), and a "missing" seventh agent role (an arbitrary
model choice with no architectural meaning). Each was reported as a gap. Each
was already answered in the record.

HOW IT DECIDES — no model judgment anywhere
  1. Find sentences asserting absence ("X is missing", "was never built", ...).
  2. Pull the subject of each claim.
  3. Search the spine for that subject alongside disposition language
     (decided, rejected, deferred, superseded, set aside, ADR, "on purpose").
  4. If the record holds such a disposition and the agent's own output never
     cites it, the claim is unresearched. FAIL, and print what it missed.

A claim survives by engaging the record, not by being right. An agent that says
"X is absent; the record shows it was deferred in ADR-013 and I believe that no
longer holds" passes, because it looked.

Usage:
  python3 gate_research_before_conclusion.py --workflow-run-id <RUN_ID>
  python3 gate_research_before_conclusion.py --text-file output.txt
"""
import argparse
import os
import re
import sqlite3
import sys

DB = os.environ.get("CIS_DB_PATH", "/workspace/cis/data/cis_memory.db")

# Sentences that assert something does not exist / was not done.
ABSENCE = re.compile(
    r"\b("
    r"(?:is|are|was|were)\s+(?:still\s+)?(?:completely\s+)?missing"
    r"|(?:is|are|was|were)\s+(?:not|never)\s+(?:built|implemented|wired|ported|created|done)"
    r"|(?:does|do|did)\s+not\s+exist"
    r"|(?:has|have|had)\s+no\s+equivalent"
    r"|(?:was|were)\s+never\s+(?:built|wired|ported|implemented|created|done)"
    r"|there\s+is\s+no\b"
    r"|no\s+\w+\s+exists\b"
    r"|nothing\s+(?:holds|does|implements|handles)\b"
    r"|(?:is|are)\s+absent\b"
    r"|lacks?\s+(?:any|a|an)\b"
    r")", re.I)

# A statement that a path or file is not on disk is an observation, not a claim
# about what was decided — and reporting it is exactly what a verifying agent is
# supposed to do. Only claims about things having never been built or wired need
# the record. Without this the gate blocked a brain phase for saying
# "hermes/profiles (that path does not exist)" (2026-08-28).
FILESYSTEM_FACT = re.compile(
    r"(/\w|\.\w{1,6}\b|\bpath\b|\bfile\b|\bdirectory\b|\bfolder\b|\binode\b|"
    r"\bsymlink\b|\bmount\b)", re.I)

# Words that mean "the record already ruled on this".
DISPOSITION = ("rejected", "deferred", "superseded", "set aside", "decided",
               "abandoned", "on purpose", "deliberate", "intentional",
               "not needed", "out of scope", "adr-", "descoped", "parked")

# Evidence the agent actually consulted the record. Deliberately narrow:
# naming the knowledge base is not the same as having searched it, and a loose
# pattern here excuses the very claims this gate exists to catch.
CITED = re.compile(
    r"(ask_history"
    r"|ADR-\d"
    r"|(?:the\s+)?record\s+(?:shows|says|holds|indicates|already)"
    r"|(?:searched|checked|queried)\s+(?:the\s+)?(?:kb|kb\b|corpus|history|record|spine|knowledge base)"
    r"|previously\s+(?:decided|rejected|deferred|superseded|set aside)"
    r"|disposition"
    r"|already\s+(?:decided|rejected|deferred|answered|ruled))", re.I)

STOP = {"the", "a", "an", "this", "that", "these", "those", "it", "there",
        "any", "some", "no", "not", "and", "or", "but", "in", "on", "for",
        "of", "to", "is", "are", "was", "were", "has", "have", "had", "we",
        "they", "he", "she", "you", "i", "our", "its", "their"}

# Words too generic to search on: the record holds a disposition about almost
# anything phrased this loosely, so matching on them produces false failures.
GENERIC = {"container", "pipeline", "system", "project", "everything",
           "anything", "nothing", "something", "equivalent", "implementation",
           "configuration", "component", "capability", "mechanism", "process",
           "structure", "reference", "requirement", "different", "existing",
           "following", "particular", "complete", "specific", "possible"}


def subjects(sentence):
    """Candidate subjects: identifiers, file names, quoted terms, capitalised words."""
    out = []
    out += re.findall(r"\b([a-z_][a-z0-9_]{4,})\.(?:py|sh|md|yaml|json)\b", sentence, re.I)
    out += re.findall(r"`([^`]{3,40})`", sentence)
    out += re.findall(r"\b([a-z][a-z0-9_]{4,}_[a-z0-9_]{2,})\b", sentence, re.I)
    out += re.findall(r"\b([A-Z][A-Za-z0-9]{2,})\b", sentence)
    # Plain lowercase nouns carry most real subjects ("orchestrator",
    # "guardrails") and match none of the rules above. Long words only, and
    # never the generic ones, or the record answers everything.
    out += [w for w in re.findall(r"\b([a-z]{8,})\b", sentence)
            if w not in GENERIC]
    clean = []
    for s in out:
        s = s.strip().strip("`.,;:()").lower()
        if (s and s not in STOP and s not in GENERIC
                and len(s) >= 3 and s not in clean):
            clean.append(s)
    return clean[:4]


class RecordUnreachable(Exception):
    """The spine could not be queried, so nothing can be concluded."""


def probe_record(db_path):
    """Confirm the record is actually queryable before judging anything.

    Without this the gate fails OPEN: a database error was caught per-query and
    reported as "no disposition found", so an unreadable spine silently passed
    every claim. That is precisely the defect found in gate_mcp_readonly on
    2026-08-26 — an error rendering as a pass — and a gate that cannot check
    must say so loudly rather than wave work through.
    """
    con = sqlite3.connect(db_path)
    con.execute("SELECT count(*) FROM knowledge_messages_fts "
                "WHERE knowledge_messages_fts MATCH ?", ('"pipeline"',)).fetchone()
    return con


def record_disposition(con, subject):
    """Return (found, sample) — does the spine already rule on this subject?"""
    toks = [t for t in re.findall(r"[a-z0-9]+", subject.lower()) if len(t) > 2]
    if not toks:
        return False, ""
    phrase = " ".join(toks[:4])
    try:
        rows = con.execute(
            "SELECT content FROM knowledge_messages_fts "
            "WHERE knowledge_messages_fts MATCH ? LIMIT 25", (f'"{phrase}"',)
        ).fetchall()
    except sqlite3.OperationalError as e:
        # A malformed FTS phrase is a per-subject problem; a dead database is
        # not. Anything that is not a query-syntax issue stops the gate.
        if "malformed MATCH" in str(e) or "fts5: syntax error" in str(e):
            return False, ""
        raise RecordUnreachable(str(e))
    for (content,) in rows:
        low = content.lower()
        idx = low.find(phrase)
        if idx < 0:
            continue
        window = low[max(0, idx - 400): idx + 400]
        for d in DISPOSITION:
            if d in window:
                start = max(0, idx - 160)
                return True, content[start:idx + 200].replace("\n", " ").strip()
    return False, ""


def advise(db_path, intent, limit=5):
    """Brief an agent BEFORE it writes, using the same lookup that judges it.

    Blocking is cheap to run (~60ms) but expensive to trigger, because a failed
    gate costs a whole model round trip. The fix is not to weaken the check —
    it is to make it almost never fire. So the same search runs up front on the
    intent, and whatever it finds is handed to the agent as context. An agent
    told "the record already rules on X" does not go on to call X missing.

    One implementation, two uses: advise before, enforce after. They cannot
    drift apart, so an agent is only ever judged on what it was already shown.
    """
    try:
        con = probe_record(db_path)
    except Exception:
        return ""  # advisory only — never block a phase because context is thin
    found = []
    seen = set()
    for subj in subjects(intent):
        if subj in seen:
            continue
        seen.add(subj)
        try:
            ok, sample = record_disposition(con, subj)
        except RecordUnreachable:
            break
        if ok:
            found.append((subj, " ".join(sample.split())[:220]))
        if len(found) >= limit:
            break
    con.close()
    if not found:
        return ""
    lines = ["[PRIOR_DISPOSITIONS] The record already rules on the following.",
             "Absence here may be a decision, not a gap. Engage these before "
             "calling anything missing — a claim that ignores them is rejected."]
    for subj, sample in found:
        lines.append(f"- {subj}: ...{sample}...")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow-run-id", dest="run_id", default=os.environ.get("CIS_RUN_ID", ""))
    ap.add_argument("--text-file")
    ap.add_argument("--advise-on", metavar="INTENT",
                    help="print prior dispositions for this intent and exit 0 "
                         "(used to brief an agent before it writes)")
    ap.add_argument("--db", default=DB)
    ap.add_argument("--max-claims", type=int, default=12)
    a = ap.parse_args()

    if a.advise_on:
        print(advise(a.db, a.advise_on))
        sys.exit(0)

    if a.text_file:
        try:
            text = open(a.text_file, errors="ignore").read()
        except OSError as e:
            print(f"SKIP: cannot read {a.text_file}: {e}")
            sys.exit(2)
    elif a.run_id:
        if not os.path.exists(a.db):
            print(f"SKIP: spine not found at {a.db}")
            sys.exit(2)
        con = sqlite3.connect(a.db)
        row = con.execute(
            "SELECT COALESCE(brain_output,'')||' '||COALESCE(drafter_output,'')||' '"
            "||COALESCE(reviewer1_output,'')||' '||COALESCE(reviewer2_output,'')||' '"
            "||COALESCE(verify_output,'') FROM deliberation_rounds "
            "WHERE run_id=? ORDER BY id DESC LIMIT 1", (a.run_id,)).fetchone()
        con.close()
        text = row[0] if row else ""
    else:
        print("SKIP: no --workflow-run-id or --text-file given")
        sys.exit(2)

    if not text.strip():
        print("SKIP: no agent output to check")
        sys.exit(2)

    if not os.path.exists(a.db):
        print(f"SKIP: spine not found at {a.db}")
        sys.exit(2)

    # Keep each claim's position so the citation check can look at the
    # surrounding passage. An agent usually states the absence in one sentence
    # and engages the record in the next — checking only inside the sentence
    # failed exactly the behaviour this gate is meant to reward.
    claims = []
    for m in re.finditer(r"[^.!?\n]{15,400}[.!?\n]", text):
        s = m.group(0).strip()
        if ABSENCE.search(s):
            claims.append((s, m.start(), m.end()))
        if len(claims) >= a.max_claims:
            break

    if not claims:
        print("PASS: no absence claims in this output")
        sys.exit(0)

    try:
        con = probe_record(a.db)
    except Exception as e:
        print(f"SKIP: cannot query the record ({type(e).__name__}: {e}).")
        print("This gate cannot verify anything without the spine — not passing by default.")
        sys.exit(2)

    unresearched = []
    for sentence, start, end in claims:
        if FILESYSTEM_FACT.search(sentence):
            continue  # an observation about disk, not a claim about decisions
        context = text[max(0, start - 100): end + 260]
        if CITED.search(context):
            continue  # the agent engaged the record around this claim
        for subj in subjects(sentence):
            try:
                found, sample = record_disposition(con, subj)
            except RecordUnreachable as e:
                print(f"SKIP: the record became unreadable mid-check ({e}).")
                sys.exit(2)
            if found:
                unresearched.append((subj, sentence[:150], sample[:240]))
                break
    con.close()

    if not unresearched:
        print(f"PASS: {len(claims)} absence claim(s), none contradicted by the record")
        sys.exit(0)

    print(f"FAIL: {len(unresearched)} absence claim(s) the record already answers.")
    print("The record is not proof the claim is wrong — it is proof it was not researched.")
    for subj, sentence, sample in unresearched:
        print(f"\n  SUBJECT:  {subj}")
        print(f"  CLAIMED:  {sentence}")
        print(f"  RECORD:   ...{sample}...")
    print("\nSearch the record for each subject, then restate the claim engaging "
          "what you find. Use: python3.12 tools/ask_history.py \"<subject> decision\"")
    sys.exit(1)


if __name__ == "__main__":
    main()
