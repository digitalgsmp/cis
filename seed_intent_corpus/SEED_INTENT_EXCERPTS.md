# Seed Intent Excerpts — Eric's CIS Vision in His Own Words

Extracted: 2026-05-29
Source: Raw Hermes session archive (~/.hermes/sessions/, 1,367 files scanned)
Method: Signal phrase scan across user-authored turns only — no model summaries
Purpose: Orient every new session with Eric's actual intent, not model interpretations

---

## Core Vision

> I don't want summaries, I am trying to build a system that works from the raw files.

> let me explain what I am trying to do. yesterday I installed three hermes folders one for deepseek v4, one for deepseek r1 and one for qwen 30b MOE. then made a ui interface with a chat for each so that I can have the models verify each others opinions on topics and check the code thats written since they all have different training data and different blind spots. I then was to build a knowledge base in the sqlite db that will vectorized and saved to a vdb.

> so I am trying to have the db and vdb as the memory, in a way bypassing the context window, I'm hoping the llm will be exposed to the stored data there instead of relying on the context window.

> yes, this is what I want. but I have a problem with the word extraction. I was doing topological extraction of these files and all of the conversational nuance was lost because the extraction process turned it into something different than what I was talking about. will your extraction pipeline do the same thing. I want something that will store the full text to get the full meanings not extractions.

> But I keep hearing that the stuff I feel has the real meaning and context of what I am trying to say is noise to an llm.

_Source: session_20260520_215551_16187f.json (May 20, 2026)_

---

## What CIS Is Supposed To Be

> the LLMs are the tools, I am trying to get LLMs to help me think by contributing factual information and expertise. when I sit down and interact with the LLMs they don't remember anything and the overall vision is not apparent to combine the vision of where I am trying to get to, to why we are working on the immediate task. And I get lost and can't keep things on track because of the volume of fixes or new systems that take me days away from the thing I originally sat down to do.

> a clean rebuild is the next question but the one priority over that is how do we save the rules somewhere to maintain the small footprint modularity to not fall into the sprawl again. All of these files were created on the back of a refactoring that was meant to break up the previous monolith docs. finally my vision is clearly worked out in detail in the chats and session files. I need a unified or shared knowledge base for the advisors configured correctly, sustained modularity, a place to capture insights so the project stays on track.

> I don't want just five foundations core boundary maps. I want to understand what everything is that has been built so far, because they were built to fulfill a purpose but the parts have not been properly integrated or maintained their modularity.

_Source: session_20260525_232304_b2d3b2.json (May 25, 2026)_

---

## Rejection of Enterprise Drift

> I'm reading over claude's documents and I feel like it is drawing from that enterprise training data and not giving me what I ask for once again. proving why the raw chats are so valuable to me.

_Source: session_20260525_232304_b2d3b2.json (May 25, 2026)_

---

## Chat-First Architecture

> We are at an architectural reset point. The current CIS application was built discovery-first and the nav/dashboard structure no longer reflects the actual intended application flow. The real application is chat-first: 1. User enters via a conversation interface 2. AI helps develop the idea through discussion 3. AI auto-structures the idea into a project form 4. User reviews and approves.

> Chat is the application. The conversation interface is the front door, not a tab or feature. Idea forms are structured outputs of chat, not the user's starting point. The AI fills the form from deliberation; the user reviews and approves.

_Source: session_20260522_194400_43dc87.json (May 22, 2026)_

---

## Separation of Powers — "I Am Not a Coder"

> I need checks and balance, I am not a coder and if I don't trust something one of you says I have to be able to paste it for another model to evaluate and give me independent analysis. that is what claude and chatgpt did to each other. I need a worker who is constrained to my working methods and two objective reviewers as expert advisors.

> stop trying to fix things and talk until we find a solution. explain what you think I am trying to accomplish.

> this is the behavior that had me go back to the other two models. I need you to always confer with me for an extended period of time to actually figure out the implications of everything we do. I know what I want and you do not, half the time you don't want to read the documents. you want to jump in and do something half cocked and I don't know how to stop this behavior and no other model seems interested in me being able to do that either.

> but the subagent is still you, I don't want you to be the builder.

_Source: session_20260518_203801_265262.json (May 18, 2026)_

---

## Earliest Signal — "Can Hermes Fix Itself?"

> hermes dashboard is up. can we ask hermes to fix itself?

_Source: session_20260509_095459_65cebc.json (May 9, 2026)_

---

## Intent Preservation Rule

These excerpts are raw. They were not summarized, rephrased, or interpreted.
They are Eric's words exactly as he typed them in Hermes session files.
Any model orientation that replaces these with summaries violates the core
intent of this corpus: to preserve what Eric actually said, not what a model
thinks he meant.
