[2026-05-15 22:34:08] [INFO] 🚀 CIS Batch Ingestion Pipeline Started
[2026-05-15 22:34:08] [INFO]     Mode: DRY RUN
[2026-05-15 22:34:08] [INFO] ============================================================
[2026-05-15 22:34:08] [INFO] STEP 1: SCANNING source folders
[2026-05-15 22:34:08] [INFO] ============================================================
[2026-05-15 22:34:08] [INFO] Scanning: /mnt/archive/_2 Word/Idea Bank/_ideabank Sorted/A
[2026-05-15 22:34:08] [INFO]   Found 5 processable files
[2026-05-15 22:34:08] [INFO]   New files (not yet in DB): 5 (filtered 0 already ingested)
[2026-05-15 22:34:08] [INFO] ============================================================
[2026-05-15 22:34:08] [INFO] STEP 2: EXTRACTING content
[2026-05-15 22:34:08] [INFO] ============================================================
[2026-05-15 22:34:08] [INFO]   [1/5] a bit of faust 11.jpg (.jpg)
[2026-05-15 22:34:08] [INFO]   [2/5] a bit of faust 11.psd (.psd)
[2026-05-15 22:34:08] [INFO]   [3/5] a bit of faust 12.jpg (.jpg)
[2026-05-15 22:34:08] [INFO]   [4/5] a bit of faust 12.psd (.psd)
[2026-05-15 22:34:08] [INFO]   [5/5] a bit of faust 2.jpg (.jpg)
[2026-05-15 22:34:08] [INFO] ============================================================
[2026-05-15 22:34:08] [INFO] STEP 3: ANALYZING content
[2026-05-15 22:34:08] [INFO] ============================================================
[2026-05-15 22:34:08] [INFO] ============================================================
[2026-05-15 22:34:08] [INFO] STEP 4: WRITING to database
[2026-05-15 22:34:08] [INFO] ============================================================
[2026-05-15 22:34:08] [INFO]   [1/5] [DRY RUN] Would create: a bit of faust
[2026-05-15 22:34:08] [INFO]   [2/5] [DRY RUN] Would create: a bit of faust
[2026-05-15 22:34:08] [INFO]   [3/5] [DRY RUN] Would create: a bit of faust
[2026-05-15 22:34:08] [INFO]   [4/5] [DRY RUN] Would create: a bit of faust
[2026-05-15 22:34:08] [INFO]   [5/5] [DRY RUN] Would create: a bit of faust
[2026-05-15 22:34:08] [INFO] 
  Total assets created: 0
[2026-05-15 22:34:08] [INFO] 
✅ Pipeline complete!
[2026-05-15 22:34:11] [INFO] 🚀 CIS Batch Ingestion Pipeline Started
[2026-05-15 22:34:11] [INFO]     Mode: LIVE
[2026-05-15 22:34:11] [INFO] ============================================================
[2026-05-15 22:34:11] [INFO] STEP 1: SCANNING source folders
[2026-05-15 22:34:11] [INFO] ============================================================
[2026-05-15 22:34:11] [INFO] Scanning: /mnt/archive/_2 Word/Idea Bank/_ideabank Sorted/A
[2026-05-15 22:34:11] [INFO]   Found 3 processable files
[2026-05-15 22:34:11] [INFO]   New files (not yet in DB): 3 (filtered 0 already ingested)
[2026-05-15 22:34:11] [INFO] ============================================================
[2026-05-15 22:34:11] [INFO] STEP 2: EXTRACTING content
[2026-05-15 22:34:11] [INFO] ============================================================
[2026-05-15 22:34:11] [INFO]   [1/3] a bit of faust 11.jpg (.jpg)
[2026-05-15 22:34:11] [INFO]     → OCR via llava vision model...
[2026-05-15 22:34:21] [INFO]     → Extracted 1033 chars
[2026-05-15 22:34:21] [INFO]     → Notes length: 1033
[2026-05-15 22:34:21] [INFO]   [2/3] a bit of faust 11.psd (.psd)
[2026-05-15 22:34:21] [INFO]     → Notes length: 52
[2026-05-15 22:34:21] [INFO]   [3/3] a bit of faust 12.jpg (.jpg)
[2026-05-15 22:34:21] [INFO]     → OCR via llava vision model...
[2026-05-15 22:34:32] [INFO]     → Extracted 745 chars
[2026-05-15 22:34:32] [INFO]     → Notes length: 745
[2026-05-15 22:34:32] [INFO] ============================================================
[2026-05-15 22:34:32] [INFO] STEP 3: ANALYZING content
[2026-05-15 22:34:32] [INFO] ============================================================
[2026-05-15 22:34:32] [INFO]   [1/3] a bit of faust 11.jpg → tags: ['creative_work', 'melancholy', 'transcribed', 'idea_bank', 'poem_story', 'handwritten']
[2026-05-15 22:34:32] [INFO]   [2/3] a bit of faust 11.psd → tags: ['image', 'uncategorized', 'idea_bank', 'artwork']
[2026-05-15 22:34:32] [INFO]   [3/3] a bit of faust 12.jpg → tags: ['creative_work', 'transcribed', 'idea_bank', 'reflective', 'poem_story', 'handwritten']
[2026-05-15 22:34:32] [INFO] ============================================================
[2026-05-15 22:34:32] [INFO] STEP 4: WRITING to database
[2026-05-15 22:34:32] [INFO] ============================================================
[2026-05-15 22:34:32] [INFO]   [1/3] ✓ Created asset asset_20260515223432605637: a bit of faust
[2026-05-15 22:34:32] [INFO]   [2/3] ✓ Created asset asset_20260515223432631534: a bit of faust
[2026-05-15 22:34:32] [INFO]   [3/3] ✓ Created asset asset_20260515223432649489: a bit of faust
[2026-05-15 22:34:32] [INFO] 
  Total assets created: 3
[2026-05-15 22:34:32] [INFO] 
✅ Pipeline complete!
[2026-05-15 22:34:32] [INFO]    3 assets created in 'draft' status — use --review to see them
[2026-05-15 22:34:32] [INFO]    Visit the Review Queue in the UI to approve/reject/edit each one
[2026-05-15 22:35:24] [INFO] ============================================================
[2026-05-15 22:35:24] [INFO] STEP 1: SCANNING source folders
[2026-05-15 22:35:24] [INFO] ============================================================
[2026-05-15 22:35:24] [INFO] Scanning: /mnt/archive/_2 Word/Idea Bank/_ideabank Sorted/A
[2026-05-15 22:35:24] [INFO]   Found 3 processable files
[2026-05-15 22:35:24] [INFO]   New files (not yet in DB): 3 (filtered 0 already ingested)
