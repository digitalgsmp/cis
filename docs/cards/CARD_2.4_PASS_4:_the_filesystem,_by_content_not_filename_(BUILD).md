## CARD 2.4 — PASS 4: the filesystem, by content not filename (BUILD)

```
Eric asked for this twice and it was done wrong both times — it searched for
files with "spec" or "contract" in the NAME.

"I'm talking about .MD files made on the fly that documented issues while
development was ongoing, these would have been some of the things deferred or
put off." (8/30)
"They are where I said they would be, in the cis folder if not in the root
folder, up to 3 layers down." (8/30)

So: find every .md file under /mnt/projects/cis to a depth of at least 3,
excluding node_modules, .git and data/drive_imports. Ignore the filename
entirely.

READ EACH ONE. For each, record: does this document describe a problem, a
missing capability, or a piece of functionality? If yes, queue it with
origin='file', found_by='P4-filesystem', excerpt = the part that describes it.

PROOF: paste the total .md count found, the count read, and the count queued.
The first two numbers must be equal — every file read, not sampled.
Then paste 10 file paths with one line each on what they describe.
EXPECT: the record mentions ~210 spec documents and 132 invisible to a filename
search. If your total is far under 200, the depth or the exclusions are wrong.
```
