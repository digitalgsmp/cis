#!/usr/bin/env python3
"""Sync project_state cache from build_plan_nodes. CLI wrapper."""
import sys
sys.path.insert(0, '/mnt/projects/cis/runtime')
from db.database import init_db
from db.build_plan import sync_project_state_from_build_plan

if __name__ == '__main__':
    conn = init_db()
    sync_project_state_from_build_plan(conn, 'CIS')
    conn.commit()
    conn.close()
    print("project_state synced from build_plan_nodes")
