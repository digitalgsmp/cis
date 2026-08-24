#!/usr/bin/env python3
"""card_gate.py — deterministic validator for BUILD CARDS. Exit 0 = pass, 1 = fail.

No model judgment anywhere. A card passes only if:
  1. All sections present, in order:
     CARD, SOURCE, INTENT, BUILD, DONE WHEN, EVIDENCE, NOT IN THIS CARD.
  2. Every quoted string (>= 15 chars) in INTENT exists verbatim in the spine
     (knowledge_messages FTS phrase match) or in a file under --docs.
     This is what makes interpretation mechanically detectable: an altered or
     invented quote fails here, automatically.
  3. BUILD and DONE WHEN contain no enterprise vocabulary (BANNED list).
  4. Every EVIDENCE bullet starts with a whitelisted runnable command.
  5. Card is <= 60 lines.

A generator may also output the single line NO_CARD (message had no direct ask);
that is accepted and reported as SKIP.

Usage:
  python3 tools/card_gate.py --db data/cis_memory.db \
      [--docs /mnt/projects/swa_audit/reports] cards/inbox/some_card.md
"""
import argparse
import os
import re
import sqlite3
import sys

ORDER = ['CARD', 'SOURCE', 'INTENT', 'BUILD', 'DONE WHEN', 'EVIDENCE',
         'NOT IN THIS CARD']
BANNED = ['architecture', 'framework', 'governance', 'roadmap', 'phase', 'tier',
          'milestone', 'scalable', 'scalability', 'enterprise', 'microservice',
          'refactor', 'ci/cd', 'sprint', 'stakeholder', 'best practice', 'robust',
          'comprehensive', 'production-ready', 'production ready', 'modular',
          'extensible', 'orchestrat', 'infrastructure']
CMD_OK = ('cd ', 'curl ', 'sqlite3 ', 'python3 ', 'pytest', 'grep ', 'test ',
          'ls ', 'cat ', 'pkill ', 'sleep ', 'bash ', 'sh ', '[ ', '( ')
MAX_LINES = 60


def norm(s):
    return re.sub(r'\s+', ' ', s).strip().lower()


def section_spans(lines):
    """Map section name -> (first_line, last_line) by scanning headers in order."""
    spans = {}
    current = None
    for i, line in enumerate(lines):
        head = line.strip().upper()
        for name in ORDER:
            if head.startswith(name):
                current = name
                spans.setdefault(name, [i, i])
                break
        if current:
            spans[current][1] = i
    return spans


def quote_in_spine(con, quote):
    toks = re.findall(r"[A-Za-z0-9']+", quote.lower())
    if len(toks) < 3:
        return True  # too short to phrase-match meaningfully
    phrase = ' '.join(t.replace("'", '') for t in toks[:8])
    try:
        n = con.execute(
            "SELECT count(*) FROM knowledge_messages_fts "
            "WHERE knowledge_messages_fts MATCH ?", (f'"{phrase}"',)).fetchone()[0]
    except sqlite3.OperationalError:
        n = 0
    return n > 0


def quote_in_docs(docs_dir, quote):
    if not docs_dir:
        return False
    target = norm(quote)
    for root, _, files in os.walk(docs_dir):
        for fn in files:
            path = os.path.join(root, fn)
            try:
                if os.path.getsize(path) > 5_000_000:
                    continue
                with open(path, errors='ignore') as f:
                    if target in norm(f.read()):
                        return True
            except OSError:
                pass
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--docs', default=None,
                    help='optional directory of approved source docs for quotes')
    ap.add_argument('card')
    a = ap.parse_args()

    text = open(a.card, errors='ignore').read()
    if text.strip() == 'NO_CARD':
        print('SKIP: generator reported no direct ask in source message')
        sys.exit(0)

    lines = text.splitlines()
    errors = []

    if len(lines) > MAX_LINES:
        errors.append(f'card is {len(lines)} lines; max {MAX_LINES} — split it')

    spans = section_spans(lines)
    missing = [s for s in ORDER if s not in spans]
    if missing:
        errors.append(f'missing sections: {", ".join(missing)}')
    else:
        starts = [spans[s][0] for s in ORDER]
        if starts != sorted(starts):
            errors.append('sections out of order')

    def section_text(name):
        if name not in spans:
            return ''
        i, j = spans[name]
        return '\n'.join(lines[i:j + 1])

    # 2. verbatim quotes
    con = sqlite3.connect(a.db)
    quotes = re.findall(r'"([^"]{15,})"', section_text('INTENT'))
    if not quotes:
        errors.append('INTENT has no verbatim quote of 15+ chars')
    for q in quotes:
        if not (quote_in_spine(con, q) or quote_in_docs(a.docs, q)):
            errors.append(f'quote not found verbatim in spine or docs: "{q[:60]}..."')

    # 3. banned vocabulary
    check_zone = (section_text('BUILD') + '\n' + section_text('DONE WHEN')).lower()
    for word in BANNED:
        if word in check_zone:
            errors.append(f'banned word in BUILD/DONE WHEN: "{word}"')

    # 4. evidence commands
    ev_lines = section_text('EVIDENCE').splitlines()[1:]
    ran = 0
    for line in ev_lines:
        cmd = line.strip().lstrip('-').strip()
        if not cmd:
            continue
        ran += 1
        if not cmd.startswith(CMD_OK):
            errors.append(f'EVIDENCE line is not a whitelisted command: {cmd[:60]}')
    if ran == 0:
        errors.append('EVIDENCE has no commands')

    if errors:
        for e in errors:
            print('FAIL:', e)
        sys.exit(1)
    print(f'PASS: {a.card}')
    sys.exit(0)


if __name__ == '__main__':
    main()
