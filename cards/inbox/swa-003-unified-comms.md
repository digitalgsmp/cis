CARD swa-003: Unified Daily Work View
SOURCE: message 788, 2026-05-27
INTENT (Eric, verbatim): "the reason I started focusing on the schedule is because everyday I fall behind in my tasks." and "I need all of this unified"
BUILD: A single daily dashboard that shows Eric's schedule, pending progress notes, and task list all on one screen. The dashboard is what Eric sees when he logs in. It shows what's due today, what's overdue, and what's coming up.
DONE WHEN:
  - Eric opens the app and sees appointments, pending notes, and tasks on one page
  - Overdue progress notes are highlighted at the top
  - Completed items disappear from the active view
EVIDENCE:
  - curl -s http://127.0.0.1:5001/ | grep -c "overdue\|pending"
  - sqlite3 /mnt/projects/swa/data/swa.db "SELECT count(*) FROM progress_notes WHERE status='pending'"
  - curl -s http://127.0.0.1:5001/api/dashboard | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'appointments' in d and 'pending_notes' in d and 'tasks' in d"
NOT IN THIS CARD: email integration, phone call logging, Proton Mail bridge, Android text sync, calendar ICS import, billing reports, client communication history
