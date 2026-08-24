CARD swa-004: Client Intake Form with File Upload
SOURCE: message 6646, 2026-04-18
INTENT (Eric, verbatim): "is it possible to have a browser button on the intake field, I would have to find the file then copy the url from the explorer the way it is set up now"
BUILD: A client intake form with text fields for name, contact info, referral source, and a file browser button next to each document upload field. Clicking the button opens the system file picker. After selecting a file, the path shows in the field. Eric clicks "Submit Intake" and the client record is created with attached documents.
DONE WHEN:
  - Eric clicks "New Client Intake" and sees a form with text fields
  - Next to each document field there is a "Browse" button that opens a file picker
  - After selecting a file, the filename appears in the field
  - Clicking "Submit Intake" creates the client record and confirms on screen
EVIDENCE:
  - curl -s http://127.0.0.1:5001/ | grep -i "intake\|new client"
  - curl -s -X POST http://127.0.0.1:5001/api/clients -F "name=Test" -F "referral=Court" | grep "created"
  - sqlite3 /mnt/projects/swa/data/swa.db "SELECT count(*) FROM clients"
NOT IN THIS CARD: document OCR processing, automatic file categorization, intake approval workflow, referral source auto-complete, duplicate client detection, consent form generation
