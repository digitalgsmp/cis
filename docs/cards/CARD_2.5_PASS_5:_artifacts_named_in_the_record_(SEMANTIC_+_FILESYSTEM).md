## CARD 2.5 — PASS 5: artifacts named in the record (SEMANTIC + FILESYSTEM)

```
The record names files, tools and components. For each one named, the question
is NOT whether the file exists.

Eric, 2026-08-29: "whether a named file still exists is mostly irrelevant. The
questions are: what FUNCTION did it serve, is that functionality still
relevant, and was it ever implemented?"

So for every artifact named in the corpus:
  - what function was it supposed to serve
  - is that function still needed for the pipeline
  - does that function exist in the code today (file:line, opened, not assumed)

A missing file whose function still matters is a TASK.
An existing file whose function was superseded is NOT.

found_by='P5-artifacts'.

PROOF: paste the artifact table — name, function, still needed y/n, implemented
y/n with file:line evidence. Every "implemented yes" needs a file:line you
opened.
```
