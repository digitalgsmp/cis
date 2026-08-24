CARD swa-002: D.A.P. Progress Note Generator
SOURCE: message 1427, 2026-05-21
INTENT (Eric, verbatim): "I have another app I developing for a social work field operator who would need schedules tracked, dap progress notes generated and other activities."
BUILD: A form where Eric pastes raw session notes and clicks a button to generate a formatted D.A.P. progress note. The note follows the standard D.A.P. template with Data, Assessment, and Plan sections. Eric can edit the generated note before saving it to the client's record.
DONE WHEN:
  - Eric pastes raw notes into a text box and clicks "Generate D.A.P."
  - A formatted note with D, A, P sections appears in a preview area
  - Eric can edit any section before clicking "Save to Client Record"
  - Saved notes appear in the client's history
EVIDENCE:
  - curl -s http://127.0.0.1:5001/ | grep -i "dap\|progress note"
  - curl -s -X POST http://127.0.0.1:5001/api/notes/generate -H "Content-Type: application/json" -d '{"raw_notes":"Met with client today","client_id":1}' | grep -E '"D\.|"A\.|"P\.'
  - sqlite3 /mnt/projects/swa/data/swa.db "SELECT count(*) FROM progress_notes WHERE generated=1"
NOT IN THIS CARD: billing code assignment, electronic signature, PDF export, concurrent documentation during session, voice-to-text dictation, PHI encryption at rest
