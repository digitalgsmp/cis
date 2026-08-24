CARD swa-001: Field Worker Schedule Tracking
SOURCE: message 1427, 2026-05-21
INTENT (Eric, verbatim): "I have another app I developing for a social work field operator who would need schedules tracked, dap progress notes generated and other activities."
BUILD: A schedule page where Eric can see his daily and weekly appointments. Each appointment shows client name, time, location, and session type. Eric can add, edit, and mark appointments complete. The schedule is the home screen when opening the app.
DONE WHEN:
  - Eric opens the app and sees today's schedule as the first screen
  - Eric can add a new appointment with client name, date, time, and location
  - Completed appointments show as checked off and move below the active list
EVIDENCE:
  - curl -s http://127.0.0.1:5001/ | grep -i schedule
  - sqlite3 /mnt/projects/swa/data/swa.db "SELECT count(*) FROM appointments WHERE date = date('now')"
  - curl -s -X POST http://127.0.0.1:5001/api/appointments -H "Content-Type: application/json" -d '{"client":"Test","time":"12:00"}' | grep -i "created"
NOT IN THIS CARD: client intake form, D.A.P. note generation, billing, email integration, Google Calendar sync, recurring appointments, drag-and-drop reschedule, notification reminders
