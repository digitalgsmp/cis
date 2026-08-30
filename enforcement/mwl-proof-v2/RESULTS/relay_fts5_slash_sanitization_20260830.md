# FTS5 Slash-Sanitization Verification — 2026-08-30

Question: Does runtime/abstraction/pipeline_relay.py still sanitize FTS5 keywords
with a character class that omits the forward slash?

Answer: NO.

Evidence (read-only filesystem inspection, re-verified 2026-08-30 UTC):
- Live module runtime/abstraction/pipeline_relay.py is 3895 lines and has exactly
  one sanitizer site, at line 273: re.sub(r"[^A-Za-z0-9_ ]", " ", text). The
  negated class keeps only A-Za-z0-9_ and space; "/" is not in the allowed set,
  so it is caught and replaced with a space. No path-named intent can reach FTS5
  with a slash intact. grep count of "A-Za-z0-9_" in the live file is exactly 1,
  at line 273 — no second site exists under any spelling.
- The fix-documenting comment sits at lines 260-263 (docstring of _fts_query):
  the old sanitizer missed "/", so any intent naming a path raised
  'fts5: syntax error near "/"' and was reported to the agent as
  "(KB search unavailable)" for 99 calls.
- The slash-omitting blacklist r'[."*(){}:^+\-]' survives only in the dated backup
  pipeline_relay.py.bak.20260827 (3577 lines) at lines 588 and 1024. That file is
  not the live module. grep count of "A-Za-z0-9_" in the backup is 0 — the fix
  class does not appear there.

Provenance (governed deviation from the draft template): the draft specification's
Section 3 template was frozen from evidence gathered before a 2026-08-30 refactor
of the live module and no longer matches it. Per the pattern catalog's
ground-truth correction and the revision directive's documented governance
exception to the no-rewrite rule, this record cites only the implement-time truth
above, verified fresh at write time; the template's stale line numbers were not
copied.
