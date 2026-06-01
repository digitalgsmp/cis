### **CIS Session Transcript Extraction Contract v1**

**Purpose:** Extract institutional memory from raw chat transcripts. Capture reasoning, failures, scope shifts, and realized understanding that is not recorded in ADRs, handoffs, tasks, or schema files.

**Input:** A raw Claude.ai chat transcript in markdown format.

**Output format — fixed structure, every transcript:**

---

#### **SESSION INSIGHT RECORD**

**Source file:** `filename.md` **Approximate date:** derived from content **Session sequence position:** earliest / early / mid / recent / current

---

**1\. What this session was trying to do** One paragraph. The actual goal, not the handoff label.

---

**2\. What failed or didn't work** Every attempt that failed, every assumption that was wrong, every dead end. Specific. Not sanitized.

---

**3\. What changed direction** The moment or realization that shifted the approach. What triggered it. What was understood before versus after.

---

**4\. What was built or decided — and why** Not just what. The reasoning behind it. What alternatives were considered and rejected.

---

**5\. What was left unresolved** Work that was started but not finished. Questions that were raised but not answered. Tensions that exist in the design.

---

**6\. What this session assumed that later sessions should know was assumed** Explicit assumptions made during this session that could be wrong or that constrained future decisions without being recorded.

---

**7\. Scope or understanding that changed** If this session expanded, contracted, or reframed what CIS is or does — capture it here in full.

---

**Output location:** `/mnt/projects/cis/docs/claude_chat_transcripts/insights/SESSION_INSIGHT_RECORD_YYYY-MM-DD_NNN.md`

**Rules:**

* Write in plain prose, not bullet lists  
* Do not sanitize failures or dead ends — they are the most valuable content  
* Do not duplicate what is already in the ADR record  
* If something is already captured correctly in an ADR, reference the ADR number and move on  
* Minimum length: as long as the session warrants — no artificial brevity  
* If the transcript is too noisy to extract signal from a section, say so explicitly rather than guessing

