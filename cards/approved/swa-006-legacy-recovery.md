CARD swa-006: Legacy Project Asset Recovery
SOURCE: message 1433, 2026-05-20
INTENT (Eric, verbatim): "I need to do some dev on a project that will help me get organized at work." and "this app was 80% complete with full db schema and much of the functionality worked out in code."
BUILD: A tool that scans the legacy project folders and extracts usable artifacts: database schemas, working code modules, UI layouts, and configuration files. The recovered assets are listed in a report showing what was found, what's reusable, and what needs to be rebuilt.
DONE WHEN:
  - Eric runs the recovery tool and sees a list of found artifacts
  - Database schemas are extracted and shown with table names and column counts
  - Working Python modules are listed with their importable functions
  - A summary report shows: total files scanned, usable files found, files needing rebuild
EVIDENCE:
  - python3 /mnt/projects/swa/tools/recover_legacy.py --source /mnt/projects/swa/social_work_ai --report
  - test -f /mnt/projects/swa/data/recovery_report.json
  - sqlite3 /mnt/projects/swa/data/swa.db ".tables" | wc -l
NOT IN THIS CARD: automated code migration, duplicate file removal, git history reconstruction, full app rebuild from legacy code, database migration scripts
