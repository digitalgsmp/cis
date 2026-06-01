**POST-COMMIT ADDENDUM — 2026-04-18**

Work continued after session close and commit. The following must be recorded to all endpoints at the start of the next session:

**Additional completed work:**

* Confirmed all 8 session close steps verified end to end via manual DB and filesystem checks  
* Identified context window limit as a session boundary risk  
* Identified post-commit work gap — work done after close+commit has no capture path

**Additional decisions to log as ADRs:**

* Handoff timestamp format (YYYY-MM-DD\_HHMM)  
* Handoff written to active project folder on close  
* Session Close Protocol embedded in handoff content  
* Notes field definition and qualifying criteria  
* Pipeline project association via project\_id  
* Archive file browser added to intake panel

**Required next session actions before anything else:**

* Log all six ADRs above into decisions table  
* Build decision logging form so this never requires manual SQL  
* Build extraction run logging table  
* Build review/promotion UI  
* Then begin intelligence extraction

---

**The permanent fix** is a standing rule baked into the next session's opening: if a post-commit addendum is present, the first action is to record everything in it to the DB before any other work begins. That becomes part of the session open protocol.

