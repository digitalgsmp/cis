# Closeout Instruction — for Implementer (port 8646)

This is the standard closeout procedure. Run it after completing a tier,
prerequisite, or infrastructure task. Do not self-report COMPLETE — the
evidence below is the closeout.

---

## 1. Commit all work

```bash
git add -A
git status --short
# Review: no unexpected files. All changes belong to this task.
git commit -m "closeout: <tier/task name> — <one-line summary>"
```

## 2. Verify schema integrity (if database changes)

```bash
sqlite3 data/cis_memory.db ".tables"
# Confirm expected tables exist

sqlite3 data/cis_memory.db ".schema <new_table>"
# Paste full schema for each new or modified table
```

## 3. Run required gates

```bash
# Build state coherence
python3 tools/gates/gate_build_state_coherence.py
# Paste full output + exit code

# Export agreement (context/AGENTS.md matches spine)
bash tools/gates/gate_export_agreement.sh
# Paste full output + exit code

# No secrets in staged files
bash tools/gates/gate_no_secrets.sh
# Paste full output + exit code

# Tier-specific gates (if any)
for g in tools/gates/gate_<tier>_*.sh; do bash "$g"; done
# Paste output + exit code for each
```

## 4. Verify working tree

```bash
git log --oneline -3
# Confirm closeout commit is HEAD

git status --short
# Must be clean — no untracked or modified files
```

## 5. Required format

Every command must be reported as:

```
COMMAND: <exact command>
OUTPUT: <full raw terminal output>
EXIT: <exit code>
```

## 6. Final statement

```
FINAL: Proceed / Blocked — whether closeout is complete, committed, and clean.
If blocked, state the exact failing command and raw output.
```

---

Do not:
- Claim "gates pass" without pasting gate output
- Self-report "COMPLETE" in a commit message without evidence
- Leave untracked files in the working tree
- Skip gate runs — every gate listed must run and report

---

## Session Update — 2026-06-27

This closeout procedure remains current. Applied during the 2026-06-27 session
(commits 3478da1 through 9c921e2 — all 17 DEV-PIVOT files updated, HCP regenerated).
See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for the full session handoff.
