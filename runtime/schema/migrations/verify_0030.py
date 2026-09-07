#!/usr/bin/env python3.12
"""All 15 checks for migration 0030. Raw output, no summarising."""
import sqlite3

DB = "/mnt/projects/cis/data/cis_memory.db"
c = sqlite3.connect(DB, isolation_level=None)
c.execute("PRAGMA foreign_keys = ON")
print("PRAGMA foreign_keys ->", c.execute("PRAGMA foreign_keys").fetchone()[0])

FAILURES = []

def q(label, sql, expect):
    """A check whose result is rows."""
    print("\n--- %s" % label)
    print("    expect: %s" % expect)
    try:
        rows = c.execute(sql).fetchall()
        print("    actual: %r" % (rows,))
        return rows
    except Exception as e:
        print("    actual: RAISED %s: %s" % (type(e).__name__, e))
        FAILURES.append(label + " (unexpected exception)")
        return None

def must_reject(label, sql, expect):
    """A check that PASSES only if the statement is rejected."""
    print("\n--- %s" % label)
    print("    expect: %s" % expect)
    try:
        c.execute(sql)
        print("    actual: ACCEPTED — NO ERROR RAISED.  *** CHECK FAILED ***")
        FAILURES.append(label + " (statement was accepted)")
    except Exception as e:
        print("    actual: rejected -> %s: %s" % (type(e).__name__, e))

# 1
q("1a. count build_plan_nodes", "SELECT count(*) FROM build_plan_nodes", "30")
q("1b. count build_plan_dependencies", "SELECT count(*) FROM build_plan_dependencies", "25")
# 2
q("2. the case fix", "SELECT project_id, count(*) FROM build_plan_nodes GROUP BY 1",
  "[('cis', 30)]")
# 3
q("3. the DEFAULT as declared",
  "SELECT name, \"notnull\", dflt_value FROM pragma_table_info('build_plan_nodes') WHERE name='project_id'",
  "dflt_value = 'cis', notnull = 1")
# 4
q("4. both foreign keys present",
  'SELECT "table", "from", "to" FROM pragma_foreign_key_list(\'build_plan_nodes\')',
  "projects/project_id/id AND workflow_runs/workflow_run_id/id")
# 5
must_reject("5. the project_id FK is real",
  "INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence) VALUES ('nonexistent','fk-probe','T',999)",
  "FOREIGN KEY constraint failed")
# 6
q("6. both named indexes present",
  "SELECT name FROM pragma_index_list('build_plan_nodes') ORDER BY name",
  "idx_bpn_project_sequence, idx_bpn_project_status, sqlite_autoindex_build_plan_nodes_1")
# 7
must_reject("7. UNIQUE still enforced",
  "INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence) "
  "SELECT project_id, node_label, tier, 998 FROM build_plan_nodes LIMIT 1",
  "UNIQUE constraint failed")
# 8
q("8a. PRAGMA foreign_key_check", "PRAGMA foreign_key_check", "empty list")
q("8b. PRAGMA integrity_check", "PRAGMA integrity_check", "[('ok',)]")
# 9
q("9a. dependency rows RESOLVE (inner join)",
  "SELECT count(*) FROM build_plan_dependencies d "
  "JOIN build_plan_nodes n1 ON d.node_id = n1.id "
  "JOIN build_plan_nodes n2 ON d.depends_on_id = n2.id", "25")
q("9b. dependency rows that FAIL to resolve",
  "SELECT count(*) FROM build_plan_dependencies d "
  "LEFT JOIN build_plan_nodes n1 ON d.node_id = n1.id "
  "LEFT JOIN build_plan_nodes n2 ON d.depends_on_id = n2.id "
  "WHERE n1.id IS NULL OR n2.id IS NULL", "0")
# 10
print("\n--- 10. the DEFAULT applies IN PRACTICE (rolled back)")
print("    expect: 'cis'")
c.execute("BEGIN")
c.execute("INSERT INTO build_plan_nodes (node_label, tier, sequence) VALUES ('default-probe','T',997)")
got = c.execute("SELECT project_id FROM build_plan_nodes WHERE node_label='default-probe'").fetchall()
print("    actual: %r" % (got,))
if got != [("cis",)]:
    FAILURES.append("10 (default not applied)")
c.execute("ROLLBACK")
print("    rolled back; probe rows now: %r" %
      (c.execute("SELECT count(*) FROM build_plan_nodes WHERE node_label='default-probe'").fetchall(),))
# 11
must_reject("11. the workflow_run_id FK is real",
  "INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence, workflow_run_id) "
  "VALUES ('cis','fk-probe-wr','T',996,'run-does-not-exist')",
  "FOREIGN KEY constraint failed")
# 12
print("\n--- 12. the CASCADE still fires (rolled back)")
print("    expect: deps drop below 25 when a referenced node is deleted")
c.execute("BEGIN")
before = c.execute("SELECT count(*) FROM build_plan_dependencies").fetchone()[0]
victim = c.execute("SELECT node_id FROM build_plan_dependencies ORDER BY id LIMIT 1").fetchone()[0]
c.execute("DELETE FROM build_plan_nodes WHERE id = ?", (victim,))
after = c.execute("SELECT count(*) FROM build_plan_dependencies").fetchone()[0]
print("    actual: deps before=%d, deleted node id=%d, deps after=%d (cascade removed %d)"
      % (before, victim, after, before - after))
if after >= before:
    FAILURES.append("12 (CASCADE did not fire)")
c.execute("ROLLBACK")
print("    rolled back; deps now: %d" %
      c.execute("SELECT count(*) FROM build_plan_dependencies").fetchone()[0])
# 13
q("13a. idx_bpn_project_status columns",
  "SELECT name FROM pragma_index_info('idx_bpn_project_status') ORDER BY seqno",
  "[('project_id',), ('status',)]")
q("13b. idx_bpn_project_sequence columns",
  "SELECT name FROM pragma_index_info('idx_bpn_project_sequence') ORDER BY seqno",
  "[('project_id',), ('sequence',)]")
# 14
must_reject("14. NOT NULL on project_id is enforced",
  "INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence) VALUES (NULL,'null-probe','T',995)",
  "NOT NULL constraint failed")
# 15
must_reject("15. the status CHECK constraint is enforced",
  "INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence, status) "
  "VALUES ('cis','check-probe','T',994,'BOGUS')",
  "CHECK constraint failed")

print("\n=== FINAL STATE ===")
print("nodes:", c.execute("SELECT count(*) FROM build_plan_nodes").fetchone())
print("deps: ", c.execute("SELECT count(*) FROM build_plan_dependencies").fetchone())
print("project_id:", c.execute("SELECT project_id, count(*) FROM build_plan_nodes GROUP BY 1").fetchall())
print("probe rows left behind:", c.execute(
    "SELECT count(*) FROM build_plan_nodes WHERE node_label LIKE '%-probe%'").fetchone())
print("\n=== VERDICT ===")
print("FAILURES:", FAILURES if FAILURES else "none — all 15 checks reported as expected")
