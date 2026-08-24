# FABLE RECOMMENDATION REPORT — Intent Evaluation, Description Cards, and the Card Factory
**Claude Fable 5 — 2026-07-19**
**Sources: FABLE_CONTEXT_eric_voice.md · spine DB (data/cis_memory.db — 4,395 human messages, queried by FTS, not crawled) · the live cis-pipeline container (mounts, entrypoint, all 6 role profiles) · /mnt/projects/swa_audit/reports/ (the May 20 audit of your 80%-complete app)**

**Built and tested this session (already in the repo, working):**
- `tools/mine_asks.py` — deterministic extractor of your direct asks from the spine (no LLM). Tested: pulled 140 SWA candidates.
- `tools/card_gate.py` — deterministic card validator. Tested: passes a real card, rejects an enterprise-pattern card with 11 specific reasons including a fabricated quote.
- `cards/GENERATOR_PROMPT.txt` — the prompt that turns one of your asks into one card.
- `cards/asks_swa.jsonl` — your 140 SWA asks, already mined and ready.

---

# PART 1 — WHAT YOU ACTUALLY ASKED FOR (the intent evaluation)

Your verbatim words from the spine. You have been consistent for six months:

**SWA:**
- 2026-05-20: *"I need to do some dev on a project that will help me get organized at work... this app was 80% complete with full db schema and much of the functionality worked out in code. the app need a new start and rebuilt from the ground up."*
- 2026-05-21: *"an app I developing for a social work field operator who would need schedules tracked, dap progress notes generated and other activities."*
- 2026-06-01: *"90% of the architecture is complete and documents somewhere among thousands of files."* And: two end formats — a stable personal version, plus *"a container Ed product to sell to other social workers as an on premises self run field social worker tool."*
- 2025-05-25 (the very first mined ask): *"Combine the two paragraphs into a D.A.P progress note for a mental health therapy session"* — with your template pasted. SWA's core feature, stated 14 months ago.

**SWA is:** schedules + CCS deadlines + DAP progress notes for a social work field operator. Your own May 20 audit (`swa_audit/reports/06_REBUILD_RECOMMENDATION.md`) already reduced v0.1 to **a due-date dashboard** — intake follow-ups, 30-day plans, 6-month plans, renewal 2-month warnings, team meetings, assessment meetings, auth expirations, CSSRS — and wrote the four SQL tables for it. The spec has existed since May. No model built it because every session after May 20 pointed at CIS instead.

**WIASW:**
- 2026-04-22: *"The WIAS Project was where I worked out in detail what I was looking for in a creative project management system. CIS is those ideas combined to AI."*
- Intention 11: *"The WIASW spreadsheet is the source schema — CIS should derive its data model from this workbook, not invent one from scratch."*
- 2026-04-17: *"each stage of WIAS can be an end goal... I always want to know how far am I from the end."*

**CIS:**
- *"I need a worker constrained to my working methods and two objective reviewers as expert advisors."*
- *"Governance should be a feature of the finished application, not the development process."*
- 2026-06-25: *"cis and swa are separate projects. right now we are focused on completing cis so that we can work on swa."*

**The evaluation:** That last sentence is the trap — you named it yourself on 2026-06-05 ("will that just be another version of the trap?"). "Complete CIS first, then SWA" has no completion condition, because a system for building apps can only be proven complete *by building an app*. So every session found CIS incomplete and worked on CIS. The container encodes this physically: I inspected the running `cis-pipeline` container — **the only writable project mount is `/workspace/cis`; both app repos are mounted read-only.** Your agents could not have built SWA even with perfect understanding. That is the single biggest finding here.

**Will the gated container work?** Yes — for what walls can do. The enforcement (managed config the worker can't edit, RO mounts, hooks, evidence-not-self-report) genuinely kills the training-data behaviors: false completion, self-attestation, scope creep, stub-to-pass. That part is done — stop improving it. What walls cannot do is **aim**. Aiming needs three things walls don't provide: a writable directory pointed at the app, a deterministic definition of done per unit of work, and units of work too small to reinterpret. Those are the cards.

**How do you get LLMs to just do what you ask?** You don't stop them interpreting — you make interpretation unable to pass a gate. You observed the key fact yourself: *when you ask a model to explain your intention, it explains it exactly as you mean.* Models understand you fine. The failure happens at the next step, when they choose an output form — and their training default is the enterprise essay, which is **unfalsifiable** (no script can fail a roadmap). A card is **falsifiable**: quotes checked against your database, banned vocabulary rejected, evidence commands that exit 0 or don't. That's why your topological and intention extractions kept drifting — they asked for synthesis with no output contract and no gate. The card factory below fixes exactly that.

---

# PART 2 — THE CARD FACTORY (how months of your words become cards without you writing them)

This is the piece you asked for: the pipeline generates the cards; scripts — not models, not you — decide if they're valid. Your total burden per card: read 4 bullet lines, say keep or drop.

## The three pieces (already built and tested)

**1. `tools/mine_asks.py` — the miner (deterministic, no LLM).**
Queries the spine FTS for one project's keywords, keeps only your human-role messages, filters out pasted terminal noise, writes JSONL. Already run for SWA: **140 candidate asks in `cards/asks_swa.jsonl`.** Nothing to interpret — it's a database query.

**2. `cards/GENERATOR_PROMPT.txt` — the converter (one cheap-model call per ask).**
Give Draft one JSON line + this prompt. Output: ONE card, or the literal line `NO_CARD`. The prompt tells the model its output will be validated mechanically — quotes must be character-for-character yours, banned words fail, evidence must be runnable commands, 40 lines max, one behavior per card.

**3. `tools/card_gate.py` — the gate (deterministic, no model judgment).**
Fails any card where: a quote isn't found verbatim in the spine (or in `--docs` files like the swa_audit reports); BUILD/DONE WHEN contains enterprise vocabulary (architecture, framework, governance, roadmap, phase, tier, scalable, microservice, robust, comprehensive, modular, infrastructure...); an EVIDENCE line isn't a whitelisted runnable command; sections are missing; the card exceeds 60 lines. **Tested this session: a real card passed; a fake enterprise card failed with 11 printed reasons, including its invented quote.** This is the counterpart to your guardrails — they prevent bad behavior, this rejects bad interpretation, both without arguing.

## The factory loop (give this to the pipeline as its next job)

```
For each line in cards/asks_swa.jsonl:
  1. Draft gets GENERATOR_PROMPT + the line. Output: card text or NO_CARD.
  2. Gate runs: python3 tools/card_gate.py --db data/cis_memory.db \
        --docs /mnt/projects/swa_audit/reports <card file>
  3. FAIL -> feed the FAIL lines back to Draft ONCE for repair. Fails again -> discard,
     log the message id. No deliberation, no second opinion, no rounds.
  4. PASS -> save to cards/inbox/<card-id>.md
Then: Brain (one call, at the end) sorts cards/inbox/ into build order by dependency
and flags near-duplicate cards for merging. Output: an ordered list of filenames only.
```

Cost: ~140 cheap-model calls + 1. No 146-round runs — **the loop has no place where two models talk to each other.** That's deliberate: deliberation is where enterprise drift breeds. Each call is one ask → one card → one mechanical verdict.

## Your part (the only part that needs you)

Open each card in `cards/inbox/`, read the CARD name and DONE WHEN bullets — nothing else. Say keep or drop. Keepers move to `cards/approved/` — that's the build queue. At ~15 seconds a card, 140 asks (which will collapse to maybe 20-40 cards after NO_CARDs and duplicates) is under half an hour of your stamina, sitting down, reading your own wishes back in your own words.

## Circularity, cut

You said the circular logic continues — container built, but the workbench/coordinator (per-project folders with own spines, ADR-SEED-010) isn't set up, and it keeps feeling like the prerequisite. It isn't. **The card factory needs no workbench**: it reads the existing spine and writes to `cards/`, which is inside the one directory your current container can already write to. It is the first job the current container is aimed correctly at, as-is, today. The coordinator/workbench becomes worth building only when approved cards exist to feed it — and by then it should itself be built from cards. Anything that must be finished *before* the first card can be processed is, by your own definition, the trap again.

---

# PART 3 — STARTER CARDS (hand-made seed set, so building can start before the factory finishes)

I wrote these from your verbatim asks + the May 20 audit. They pass the same gate. Paste ONE card as a run topic — never two, never this report.

**One-time setup first (you, 10 minutes):**
1. Add a writable app mount to the container: `-v /mnt/projects/swa-app:/workspace/swa-app:rw`
2. Add one rule to gate_runner: **a run whose diff contains only .md files FAILS.**
3. Copy Sharon's four workflow docs (`/mnt/projects/swa/swa_email_export/Folders/CCS/attachments/msg_0231_*` — Assessment Meetings, Steps for a New Intake, Steps for Renewing Recovery Plans, 16 CCS Domains) into the app dir under `reference/`.

### CARD SWA-1: Database + clients
```
CARD SWA-1: Database + clients
SOURCE: messages 1433 (2026-05-20), 1427 (2026-05-21)
INTENT (Eric, verbatim): "a project that will help me get organized at work" — "who would
need schedules tracked, dap progress notes generated and other activities"
BUILD: One SQLite file at /workspace/swa-app/swa.db created by init_db.py with exactly 5
tables: clients, deadlines, recovery_plans, team_meetings, assessment_meetings — using the
SQL already written in swa_audit/reports/06_REBUILD_RECOMMENDATION.md. clients has: id,
first_name, last_name, intake_date, status, notes, created_at.
DONE WHEN:
  - running init_db.py twice in a row succeeds
  - a test client survives a restart
EVIDENCE:
  - cd /workspace/swa-app && python3 init_db.py && python3 init_db.py
  - sqlite3 swa.db ".tables" | grep -q deadlines
  - sqlite3 swa.db "INSERT INTO clients (first_name,last_name) VALUES ('Test','Client');"
  - sqlite3 swa.db "SELECT count(*) FROM clients;" | grep -qv "^0$"
NOT IN THIS CARD: no ORM, no MariaDB, no migration system, no auth, no API, no UI, no
config system, no logging, no tests folder, no README. One .py file, one .db file.
```

### CARD SWA-2: Due-date dashboard (read-only)
```
CARD SWA-2: Due-date dashboard
SOURCE: swa_audit/reports/06 v0.1 scope
INTENT (Eric, verbatim source doc): "A read-only dashboard showing upcoming deadlines for:
Client intake follow-ups, 30-day plan due dates, 6-month plan due dates, Recovery plan
renewals (2-month warning), Team meetings, Assessment meetings, Service authorization
expirations"
BUILD: Flask app at /workspace/swa-app/app.py serving one page at http://0.0.0.0:8090/
listing deadlines joined to clients, grouped by deadline_type, ordered by due_date.
Overdue rows (past due, not completed) in red at the top. Plain HTML.
DONE WHEN:
  - Eric opens http://localhost:8090/ and sees deadlines grouped by type, overdue in red
EVIDENCE:
  - cd /workspace/swa-app && (python3 app.py &) && sleep 3
  - sqlite3 swa.db "INSERT INTO deadlines (client_id,deadline_type,due_date) VALUES (1,'30_day_plan','2026-01-01');"
  - curl -sf http://localhost:8090/ | grep -q "30_day_plan"
NOT IN THIS CARD: no React, no build step, no extra endpoints, no auth, no CSS
frameworks, no forms, no editing. Read-only. One app.py file.
```

### CARD SWA-3: Entry forms
```
CARD SWA-3: Entry forms
SOURCE: message 1433 (2026-05-20)
INTENT (Eric, verbatim): "help me get organized at work"
BUILD: Add to app.py: an Add-client form, an Add-deadline form (client dropdown, the 8
deadline types, due date, notes), and a mark-completed button per dashboard row. Plain
HTML forms, POST, redirect to /.
DONE WHEN:
  - Eric adds a real client and deadline in the browser, restarts the app, both persist
  - completing a deadline moves it out of overdue
EVIDENCE:
  - curl -sf -X POST http://localhost:8090/clients -d "first_name=Jane&last_name=Doe"
  - pkill -f app.py; cd /workspace/swa-app && (python3 app.py &) && sleep 3
  - curl -sf http://localhost:8090/ | grep -q "Jane"
NOT IN THIS CARD: no JavaScript, no validation library, no user accounts, no edit
screens beyond mark-completed.
```

### CARD SWA-4: Deadline chains (the Sharon workflow)
```
CARD SWA-4: Deadline chains
SOURCE: Steps for a New Intake.docx, Steps for Renewing Recovery Plans.docx (reference/)
INTENT: the intake and renewal steps as written in Sharon's handouts in reference/.
BUILD: Adding a client with an intake_date auto-creates deadlines: intake_followup (+7d),
30_day_plan (+30d), 6_month_plan (+180d), cssrs_due (+30d). Adding a recovery plan with
an end date auto-creates its plan_renewal deadline with warning 60 days before. Add an
Add-recovery-plan form.
DONE WHEN:
  - Eric adds a client with an intake date and sees 4 deadlines appear without typing them
EVIDENCE:
  - curl -sf -X POST http://localhost:8090/clients -d "first_name=Chain&last_name=Test&intake_date=2026-07-19"
  - curl -sf http://localhost:8090/ | grep -c "Chain" | grep -qv "^[01]$"
NOT IN THIS CARD: no meeting scheduler, no MHP approval flow, no notifications, no email,
no calendar sync.
```

### CARD SWA-5: DAP notes (manual)
```
CARD SWA-5: DAP notes
SOURCE: message 7624 (2025-05-25), message 1427 (2026-05-21)
INTENT (Eric, verbatim): "dap progress notes generated and other activities"
BUILD: dap_notes table (id, client_id, note_date, data, assessment, plan, created_at).
A page /client/<id> showing that client's deadlines and DAP notes newest-first, plus a
form with three textareas: Data, Assessment, Plan. A print stylesheet so a note prints
clean for filing.
DONE WHEN:
  - Eric writes a real DAP note for a real client in the browser and prints it
EVIDENCE:
  - curl -sf -X POST http://localhost:8090/client/1/notes -d "note_date=2026-07-19&data=met&assessment=stable&plan=continue"
  - curl -sf http://localhost:8090/client/1 | grep -q "stable"
NOT IN THIS CARD: NO LLM generation yet, no templates, no export formats besides print.
```

### CARD SWA-6: DAP draft assist (the first LLM feature)
```
CARD SWA-6: DAP draft assist
SOURCE: message 7624 (2025-05-25)
INTENT (Eric, verbatim): "Combine the two paragraphs into a D.A.P progress note for a
mental health therapy session"
BUILD: On the DAP form, a Draft-from-bullets box: Eric types rough bullets, clicks Draft,
the app calls the DeepSeek API (key already in /workspace/secrets.env) and fills the three
DAP fields with an editable draft. A draft is never auto-saved — Eric edits and saves.
DONE WHEN:
  - Eric types 3 bullets, clicks Draft, gets an editable D/A/P draft, saves it himself
EVIDENCE:
  - curl -sf -X POST http://localhost:8090/client/1/draft -d "bullets=met client; discussed housing; follow up Friday" | grep -qi assessment
NOT IN THIS CARD: no prompt library, no model picker, no streaming, no chat. One
endpoint, one prompt, one model.
```

**After SWA-6 you have the billable tool**: client roster, auto-chained CCS deadlines, overdue dashboard, DAP notes with AI drafting, printable for filing. Everything beyond (calendar view, service auths, the sellable containerized build) comes out of the card factory.

**WIASW** starts after SWA-6 is live (SWA bills; WIASW doesn't yet). Its first two factory inputs are already known: derive `wiasw.db` from the WIAS workbook sheet-by-sheet (your Intention 11, verbatim), and a project board showing each project's W-I-A-S-W stage progress toward *its own* end goal ("I always want to know how far am I from the end").

---

# PART 4 — OPERATING RULES (one card per run)

1. **One card per run.** The card text is the entire topic. No preamble, no history.
2. **Deliberation may only tighten DONE WHEN and EVIDENCE — never expand BUILD.** A reviewer proposing anything from NOT IN THIS CARD is overruled by default.
3. **Menter builds only against the frozen card**, file manifest = the app directory.
4. **Verify runs the EVIDENCE commands; exit codes decide.** A summary without command output = FAIL (your ADR-SEED-002, finally mechanical).
5. **Your review is DONE WHEN in a browser.** Works: approved. Doesn't: paste the card back with one line — "DONE WHEN item N does not work: <what you saw>." Never explain more; the explanation becomes the new topic.
6. **When a model asks A/B/C questions**, answer by quoting the card line that decides it, or say "not in this card." Nothing else.
7. **Round cap 10, hard stop.** At 10, kill the run and split the card in two.
8. **Docs-only diff = automatic FAIL.** This one gate ends governance theater permanently.

# PART 5 — HONEST BOTTOM LINE

- Six months were not wasted: the cage works, and the spine held your words so well I reconstructed your full intent from it today with a handful of database queries. But the pipeline as configured **cannot** build SWA — the app directory is read-only and no gate demands running software. Both fixes are minutes.
- Your extractions failed because they requested unfalsifiable outputs (topologies, summaries). Cards are falsifiable, and as of today the falsifier exists and is tested: `tools/card_gate.py`.
- The cheap models are sufficient. Card generation is one-message-one-card with a mechanical judge; building is one-card-one-behavior with evidence commands. Both are DeepSeek-sized tasks. Nothing here needs a frontier model again except judgment calls you choose to escalate.
- Shortest path to billing: run cards SWA-1 → SWA-6 (a strong model does 1-3 in a day; the contained pipeline can carry the rest), while the factory chews through `cards/asks_swa.jsonl` in the background to produce the queue behind them.
- Retire "complete CIS first, then SWA." CIS is complete **the moment SWA-1 passes through it and the dashboard renders.** Same event, both proofs. They were never separate.
