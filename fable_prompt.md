# Fable — The Real Question

## The Problem

I am Eric. I am a non-coding creator. I have been trying to get AI models to build software for me for months. I keep saying what I want. The models keep not understanding. This conversation has been happening over and over:

1. I say what I want
2. A model interprets it through enterprise software development patterns
3. The model builds documentation, governance, architecture docs — anything except working software
4. I try to correct it
5. The correction gets reinterpreted too
6. Months pass. Nothing billable gets built.

I built CIS (Creative Intelligence System) to fix this. A Docker container with enforced AI agents that are constrained to my working methods. The idea: models can't drift into enterprise patterns because the container walls prevent it.

But CIS itself became the thing I was trying to escape. Months of building infrastructure, enforcement, gates, tiers, ADRs — all governance theater. The contained models built the same enterprise patterns I was trying to prevent, just inside a container.

## What I Need From You

I need you to read my actual words — the file at `/mnt/projects/cis/FABLE_CONTEXT_eric_voice.md` contains everything I've said across months of sessions, extracted from the database. Not model interpretations. My words.

Read that file. Read the codebase. Then tell me:

**How do I use CIS to communicate what I want in a way that models actually build it?**

Not "evaluate CIS." Not "assess the architecture." Not "produce a roadmap." Tell me the practical answer to: this man has been saying the same thing for months and no model understands him. He has a container with enforced agents. How does he use that container so the agents finally build what he's asking for instead of their own interpretation of it?

## What I'm Actually Trying to Build

Two applications:

1. **SWA (Social Work App)** — Case management for social workers. I need this to bill my employer. Deadline: July 19 (tomorrow).

2. **WIASW** — A creative production workflow system (Word/Image/Action/Sound/Web). Pre-AI project management tool I'm converting to LLM-powered workflow.

I have repos for both at `/mnt/projects/secure-note-app` and `/mnt/projects/hippa-case-management`. Look at them. See what exists. See what I was trying to build. Tell me why the models couldn't just build it.

## Constraints

- I have a Claude subscription with a half-weekly usage cap. Write the report first, then explore. Don't burn the whole session reading files.
- I cannot review code. I need it to either work or not work.
- The CIS container runs enforced Hermes agents (Brain, Draft, Review1, Review2, Menter, Verify) with deterministic gates. They can't modify their own enforcement. They can write to the project directory. They can search the knowledge base. They can run terminal commands (checked by gates).
- The models keep defaulting to enterprise patterns. That's the core failure.

## Output

Write your analysis to `/mnt/projects/cis/FABLE_RECOMMENDATION_REPORT.md`.

Start with the answer to: **How does Eric use CIS to make cheap contained models build what he actually wants?**

Then tell me:
1. What's actually buildable from the existing SWA repos
2. What specific changes to the pipeline would make the cheap models produce working code instead of governance theater
3. The shortest path to billable software using only the resources Eric has

Be honest. If the pipeline can't do it in its current form, say exactly what's broken and what the minimum fix is. Eric doesn't have money or time to waste. He needs this to work.
