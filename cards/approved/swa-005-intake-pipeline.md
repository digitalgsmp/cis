CARD swa-005: Post-Intake Pipeline View
SOURCE: message 6290, 2026-04-18
INTENT (Eric, verbatim): "so what happens after the intake button is click because the is not event or activity that demonstrateds that the file has been ingested to the system"
BUILD: After clicking "Submit Intake," the screen changes to show a pipeline view. The new client intake appears as a card in the first column. Eric can see what stage each client is in: Intake → Assessment → Active → Discharge. Clicking a client card opens their full record.
DONE WHEN:
  - Eric submits a new intake and the screen changes to a pipeline board
  - The new client appears as a card in the "Intake" column
  - Eric can click the card to open the full client record
  - The pipeline has columns for Intake, Assessment, Active, Discharge
EVIDENCE:
  - curl -s http://127.0.0.1:5001/ | grep -i pipeline
  - sqlite3 /mnt/projects/swa/data/swa.db "SELECT stage, count(*) FROM clients GROUP BY stage"
  - curl -s -X POST http://127.0.0.1:5001/api/clients -F "name=PipelineTest" -F "referral=Test" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['stage']=='intake'"
NOT IN THIS CARD: drag-and-drop between pipeline stages, automated stage transitions, notification on stage change, clinical assessment forms, discharge summary generation
