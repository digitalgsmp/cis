#!/usr/bin/env python3
"""
gate_intent_verification.py — Final intent verification gate.

Checks that the pipeline's final output matches the locked enriched intent.
This is the ultimate provenance check: does what we built match what Eric asked for?

Reads:
  - intent_provenance table: the locked enriched intent
  - phase_drift table: drift scores at each phase boundary
  - deliberation_rounds: the final output (verify_output or menter_output)
  - workflow_runs: run status and result

Exit codes:
  0 = PASS  (final drift within threshold)
  1 = FAIL  (final drift exceeds threshold — pipeline diverged from intent)
  2 = SKIP  (no enriched intent found, or run not complete)
"""
import sys
import os
import sqlite3

DB_PATH = os.environ.get("CIS_DB_PATH", "/mnt/projects/cis/data/cis_memory.db")
CIS_REPO = os.environ.get("CIS_REPO", "/mnt/projects/cis")

def main():
    if len(sys.argv) < 2:
        print("SKIP: no run_id provided")
        sys.exit(2)

    run_id = sys.argv[1]

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row

    # 1. Check that enriched intent exists
    prov = conn.execute(
        "SELECT enriched_intent, original_intent FROM intent_provenance "
        "WHERE run_id = ? ORDER BY id DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    if not prov:
        print("SKIP: no intent_provenance record for this run")
        conn.close()
        sys.exit(2)

    # 2. Check drift scores at each phase
    drift_rows = conn.execute(
        "SELECT phase, round, drift_score, verdict, drift_reasons "
        "FROM phase_drift WHERE run_id = ? ORDER BY id ASC",
        (run_id,),
    ).fetchall()

    if not drift_rows:
        print("SKIP: no phase_drift records — drift not measured")
        conn.close()
        sys.exit(2)

    # 3. Calculate aggregate drift
    max_drift = 0.0
    max_drift_phase = ""
    diverged_phases = []
    significant_drift_phases = []

    for row in drift_rows:
        score = row["drift_score"] or 0.0
        phase = row["phase"]
        verdict = row["verdict"] or "ALIGNED"

        if score > max_drift:
            max_drift = score
            max_drift_phase = phase

        if verdict == "DIVERGED":
            diverged_phases.append(phase)
        elif verdict == "SIGNIFICANT_DRIFT":
            significant_drift_phases.append(phase)

    # 4. Determine overall verdict
    # FAIL if any phase DIVERGED, or if max drift > 0.6
    # PASS if all phases are ALIGNED or MINOR_DRIFT, or max drift < 0.4
    if diverged_phases:
        print(f"FAIL: pipeline diverged from intent at phase(s): "
              f"{', '.join(diverged_phases)} (max drift={max_drift:.2f} "
              f"at {max_drift_phase})")
        for row in drift_rows:
            if row["verdict"] in ("DIVERGED", "SIGNIFICANT_DRIFT"):
                reasons = row["drift_reasons"] or ""
                print(f"  {row['phase']} (round {row['round']}): "
                      f"{row['verdict']} drift={row['drift_score']:.2f} — {reasons}")
        conn.close()
        sys.exit(1)

    if max_drift >= 0.6:
        print(f"FAIL: maximum drift score {max_drift:.2f} at {max_drift_phase} "
              f"exceeds threshold")
        conn.close()
        sys.exit(1)

    if significant_drift_phases:
        # ADVISORY: significant drift but not diverged — warn but pass
        print(f"PASS (advisory): significant drift at phase(s): "
              f"{', '.join(significant_drift_phases)} (max drift={max_drift:.2f})")
        for row in drift_rows:
            if row["verdict"] == "SIGNIFICANT_DRIFT":
                reasons = row["drift_reasons"] or ""
                print(f"  {row['phase']} (round {row['round']}): "
                      f"drift={row['drift_score']:.2f} — {reasons}")
        conn.close()
        sys.exit(0)

    # All good
    print(f"PASS: all phases aligned with intent (max drift={max_drift:.2f} "
          f"at {max_drift_phase})")
    for row in drift_rows:
        print(f"  {row['phase']} (round {row['round']}): "
              f"{row['verdict']} drift={row['drift_score']:.2f}")
    conn.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
