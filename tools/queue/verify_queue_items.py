#!/usr/bin/env python3.12
"""All checks for migration 0031 / queue_items. Raw output, no summarising.

Follows verify_0030.py's shape: every claim is a command that can fail, and the
actual result is printed whether it passes or not.
"""
import hashlib
import re
import sqlite3
import subprocess
import sys

DB = "/mnt/projects/cis/data/cis_memory.db"
SRC = "/mnt/projects/cis/docs/UNIFIED_BUILD_LIST.md"

conn = sqlite3.connect(DB)
FAILURES = []


def check(label, actual, expect, ok):
    print("\n--- %s" % label)
    print("    expect: %s" % expect)
    print("    actual: %r" % (actual,))
    if ok:
        print("    PASS")
    else:
        print("    ***FAIL***")
        FAILURES.append(label)
    return ok


# ---------------------------------------------------------------- 0. source
text = open(SRC, encoding="utf-8").read()
file_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
lines = text.split("\n")

# AMENDMENT (c): the expected count is RE-PARSED from the file now, at
# verification time. The r3 packet hardcoded 119, which fails a CORRECT
# extraction if an item lands between the count being taken and the run.
# Counted here with shell grep -- a different program from the extractor.
g1 = int(subprocess.run(["grep", "-c", r"^### [0-9]\+\.[0-9]\+", SRC],
                        capture_output=True, text=True).stdout.strip())
g2 = int(subprocess.run(["grep", "-c", r"^- \*\*[0-9]\+\.[0-9]\+\*\*", SRC],
                        capture_output=True, text=True).stdout.strip())
expected_total = g1 + g2
print("EXPECTED COUNT RE-DERIVED AT VERIFICATION TIME (grep, not the extractor)")
print("    headings: %d   bullets: %d   total: %d" % (g1, g2, expected_total))
print("    file sha256: %s" % file_sha)

# ---------------------------------------------------------------- 1. inventory
n = conn.execute("SELECT count(*) FROM queue_items").fetchone()[0]
check("1a. row count matches the file as counted right now",
      n, "%d (re-derived, not hardcoded)" % expected_total, n == expected_total)

forms = conn.execute(
    "SELECT form, count(*) FROM queue_items GROUP BY 1 ORDER BY 1").fetchall()
check("1b. form distribution", forms,
      "[('bullet', %d), ('heading', %d)]" % (g2, g1),
      dict(forms) == {"heading": g1, "bullet": g2})

# ---------------------------------------------------------------- 2. UNPARSED
u = conn.execute(
    "SELECT count(*) FROM queue_items WHERE need_status='UNPARSED'").fetchone()[0]
check("2. nothing silently defaulted", u, "0", u == 0)

# ---------------------------------------------------------------- 3. fixture
FIXTURE = {
    "0.1": "DONE", "0.2": "DONE", "0.3": "DONE", "1.1": "DONE",
    "3.6": "DONE", "1.17": "DONE", "3.22": "DONE",
    "0.4": "HALF_DONE", "1.20": "HALF_DONE", "1.22": "HALF_DONE",
}
rows = dict(conn.execute(
    "SELECT item_num, need_status FROM queue_items WHERE item_num IN (%s)"
    % ",".join("?" * len(FIXTURE)), tuple(FIXTURE)).fetchall())
check("3. the 10 completion-bearing items, read off the file BY HAND",
      rows, str(FIXTURE), rows == FIXTURE)

# ---------------------------------------------------------------- 4. identity
bad = conn.execute(
    "SELECT count(*) FROM queue_items WHERE item_num IS NULL OR item_num=''"
).fetchone()[0]
check("5a. every row has an item_num", bad, "0", bad == 0)
dups = conn.execute(
    "SELECT item_num FROM queue_items GROUP BY 1 HAVING count(*)>1").fetchall()
check("5b. item_num is unique", dups, "[]", dups == [])

# ---------------------------------------------------------------- 6. tier
wrong_tier = conn.execute(
    "SELECT item_num, tier FROM queue_items "
    "WHERE tier <> CAST(substr(item_num,1,instr(item_num,'.')-1) AS INTEGER)"
).fetchall()
check("6. tier came from the NUMBER, not the header (2.38 is the tell)",
      wrong_tier, "[]", wrong_tier == [])
t238 = conn.execute(
    "SELECT item_num, tier FROM queue_items WHERE item_num='2.38'").fetchone()
check("6b. 2.38 sits under '# TIER 3' in the file and must be tier 2",
      t238, "('2.38', 2)", t238 == ("2.38", 2))

# ------------------------------------------------- 7. partition / round-trip
db_items = conn.execute(
    "SELECT item_num, source_line, body_md FROM queue_items "
    "ORDER BY source_line").fetchall()

overlaps, byte_mismatch, gaps = [], [], []
spans = []
for item_num, start, body in db_items:
    blines = body.split("\n")
    spans.append((start, start + len(blines) - 1, item_num))
    actual = "\n".join(lines[start - 1:start - 1 + len(blines)])
    if actual != body:
        byte_mismatch.append(item_num)

for i in range(len(spans) - 1):
    end_i = spans[i][1]
    start_next = spans[i + 1][0]
    if end_i >= start_next:
        overlaps.append((spans[i][2], spans[i + 1][2]))
    elif end_i + 1 != start_next:
        between = lines[end_i:start_next - 1]
        if not any(l.startswith("# TIER") for l in between):
            gaps.append((spans[i][2], spans[i + 1][2], between[:2]))

check("7a. every row's body_md matches the file AT ITS OWN LINES",
      byte_mismatch, "[]", byte_mismatch == [])
check("7b. no two items' line ranges overlap (catches a split item)",
      overlaps, "[]", overlaps == [])
check("7c. consecutive items are contiguous unless a '# TIER' header "
      "separates them (catches truncation compensated by a neighbour)",
      gaps, "[]", gaps == [])

uncovered_markers = []
covered = set()
for s, e, _ in spans:
    covered.update(range(s, e + 1))
for idx, line in enumerate(lines, 1):
    if idx in covered:
        continue
    if re.match(r"^### [0-9]+\.[0-9]+", line) or re.match(r"^- \*\*[0-9]+\.[0-9]+\*\*", line):
        uncovered_markers.append((idx, line[:50]))
check("7d. no item marker falls outside every row (catches a merged item)",
      uncovered_markers, "[]", uncovered_markers == [])

# ---------------------------------------------------------------- 8. staleness
shas = [r[0] for r in conn.execute(
    "SELECT DISTINCT source_sha FROM queue_items").fetchall()]
check("8a. one source_sha across all rows", shas, "one value", len(shas) == 1)
check("8b. source_sha equals the file on disk right now",
      shas[0][:16] if shas else None, file_sha[:16],
      bool(shas) and shas[0] == file_sha)

# ------------------------------------------------- 9. THE READER, BY IDENTITY
sys.path.insert(0, "/mnt/projects/cis/runtime")
from mcp_bridge import spine as spine_mod  # noqa: E402

r = spine_mod.query_queue_item("3.21")
check("9a. reader returns something for 3.21",
      r is not None, "not None", r is not None)
check("9b. IDENTITY — the row returned IS 3.21, not merely a row",
      r.get("item_num") if r else None, "'3.21'",
      bool(r) and r.get("item_num") == "3.21")

db_title_321 = conn.execute(
    "SELECT title FROM queue_items WHERE item_num='3.21'").fetchone()[0]
check("9c. IDENTITY — a hand-verified field matches this specific item",
      (r or {}).get("title", "")[:46],
      "starts 'Move the queue out of markdown'",
      bool(r) and r.get("title", "").startswith("Move the queue out of markdown"))

r22 = spine_mod.query_queue_item("3.22")
check("9d. NEGATIVE — asking for 3.22 must not return 3.21's row",
      (r22 or {}).get("item_num"), "'3.22'",
      bool(r22) and r22.get("item_num") == "3.22"
      and r22.get("title") != db_title_321)

rmiss = spine_mod.query_queue_item("99.99")
check("9e. a missing item returns None, not a wrong row",
      rmiss, "None", rmiss is None)

check("9f. the reader states what it cannot answer",
      sorted((r or {}).get("answers_2_30", {}).keys()),
      "all four of 2.30's questions named",
      bool(r) and len(r.get("answers_2_30", {})) == 4)

check("9g. dependency edges are NOT served (both lineages required this)",
      "depends_on" in (r or {}), "False", "depends_on" not in (r or {}))

# ------------------------------------- 10. the deprecated tool no longer lies
sys.path.insert(0, "/mnt/projects/cis/runtime/mcp_bridge")
from mcp_bridge import tools as tools_mod  # noqa: E402

old = tools_mod.handle_get_build_status({"node_label": "3.21"})
check("10a. old tool no longer answers '3.21' with a bare not-found",
      "error" in old, "False", "error" not in old)
check("10b. old tool redirects and says why",
      old.get("redirected_from"), "'cis_get_build_status'",
      old.get("redirected_from") == "cis_get_build_status")
check("10c. the redirect carries the CORRECT item",
      (old.get("item") or {}).get("item_num"), "'3.21'",
      (old.get("item") or {}).get("item_num") == "3.21")

still = tools_mod.handle_get_build_status({"node_label": "Tier 8 — MCP Bridge"})
check("10d. the old tool still works for real node_labels (no regression)",
      still.get("node_label"), "'Tier 8 — MCP Bridge'",
      still.get("node_label") == "Tier 8 — MCP Bridge")

names = [t["name"] for t in tools_mod.TOOLS]
check("10e. cis_get_queue_item is registered",
      "cis_get_queue_item" in names, "True", "cis_get_queue_item" in names)
check("10f. it is wired into HANDLERS",
      "cis_get_queue_item" in tools_mod.HANDLERS, "True",
      "cis_get_queue_item" in tools_mod.HANDLERS)

# ----------------------------------- 11. THE ADR WRITE (round 3 caught this)
# Migration 0031's only effect nothing checked. Both lineages returned
# NOT_ESTABLISHED on 2026-09-09 because the result packet asserted this row
# existed and showed no query proving it. The row did exist; the claim was
# unevidenced, which is failure mode 1 in the artifact built to catch it.
adr = conn.execute(
    "SELECT id, status FROM project_decisions WHERE id='ADR-3.21-001'").fetchone()
check("11a. ADR-3.21-001 exists in project_decisions",
      adr, "('ADR-3.21-001', 'DECIDED')", adr == ("ADR-3.21-001", "DECIDED"))
adr_reason = conn.execute(
    "SELECT reason FROM project_decisions WHERE id='ADR-3.21-001'").fetchone()
check("11b. the ADR records WHY, not just that",
      (adr_reason or [""])[0][:60],
      "mentions the 1.24 false-success signal",
      bool(adr_reason) and "1.24" in (adr_reason[0] or ""))

# ------------------------- 12. THE CLIENT SIDE OF THE REDIRECT, without a browser
# GLM: the redirect changes the response shape and cis_dashboard.html:1672
# unpacks whatever comes back. Resolved by route matching rather than by a
# browser: TWO blueprints register /api/pipeline/status/<...>.
#   runtime/api/pipeline.py:93        <source_id>        returns {"found": ...}
#   runtime/api/pipeline_views.py:37  <path:node_label>  reaches the redirect
# Werkzeug prefers the plain string converter for a single segment, so the
# dashboard's call never reaches the changed code.
try:
    from werkzeug.routing import Map, Rule
    rmap = Map([
        Rule("/api/pipeline/status/<source_id>", endpoint="pipeline.manifest"),
        Rule("/api/pipeline/status/<path:node_label>",
             endpoint="pipeline_views.build_status"),
    ]).bind("localhost")
    hit = rmap.match("/api/pipeline/status/3.21")[0]
    check("12a. the dashboard's single-segment call does NOT reach the redirect",
          hit, "'pipeline.manifest'", hit == "pipeline.manifest")
    hit2 = rmap.match("/api/pipeline/status/a/b")[0]
    check("12b. the redirect is reachable only for labels containing a slash",
          hit2, "'pipeline_views.build_status'",
          hit2 == "pipeline_views.build_status")
except ImportError:
    check("12. route resolution", "werkzeug unavailable",
          "werkzeug importable", False)

# cis_dashboard.html:1672 reads `r.found`. pipeline_views.build_status has never
# returned that key, so if the collision above were ever resolved in its favour
# the dashboard would silently render nothing. Recorded, not fixed.
js = open("/mnt/projects/cis/runtime/cis_dashboard.html", encoding="utf-8").read()
check("12c. the client reads r.found, which only pipeline.manifest returns",
      "r.found ? r : null" in js, "True", "r.found ? r : null" in js)

print("\n" + "=" * 68)
if FAILURES:
    print("FAILURES: %d" % len(FAILURES))
    for f in FAILURES:
        print("   %s" % f)
    sys.exit(1)
print("ALL CHECKS PASS")
print("""
WHAT THESE CHECKS DO NOT ESTABLISH — stated, not implied:
  * That the %d items found are the %d a human would agree are items. Checks
    1, 5, 6 and 7 are all anchored to one definition of "an item". If that
    definition is wrong they agree with each other and are wrong together.
    Check 3 is the only anchor no parser produced, and it covers 10 items.
  * That the NULL status on items with no status prose is correct. An item
    stating its status in a shape this parser does not recognise AS status
    lands in that bucket and nothing fires.
  * That any agent will call the new tool. Check 10 proves the old tool
    redirects; it does not prove callers were updated.
""" % (expected_total, expected_total))
sys.exit(0)
