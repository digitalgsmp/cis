#!/usr/bin/env python3
"""mine_asks_claude_code.py — extract Eric's direct asks from Claude Code sessions.

No LLM involved, and no interpretation: this copies Eric's own messages out of the
session transcripts Claude Code already writes to disk. Nothing a model wrote is
carried across, so there is no summary here to distrust.

Claude Code transcripts are not in the spine, so quotes taken from them cannot be
verified by card_gate's FTS check. This writes a companion directory of verbatim
source files for card_gate --docs to match against.

Usage:
  python3 tools/mine_asks_claude_code.py \
      --out cards/asks_claude_code.jsonl \
      --docs-out cards/claude_code_sources/

  # then, when validating a card generated from these asks:
  python3 tools/card_gate.py --db data/cis_memory.db \
      --docs cards/claude_code_sources/ cards/inbox/<card>.md
"""
import argparse
import glob
import json
import os
import re
import sys

DEFAULT_SESSIONS = os.path.expanduser(
    '~/.claude/projects/-mnt-projects-cis/*.jsonl')

# Same terminal-paste markers mine_asks.py uses, so both miners agree on noise.
NOISE = re.compile(
    r'(PS C:\\|Traceback \(|INFO: {2,}|npm error|Requirement already satisfied|'
    r'^\s*\$ |sudo |docker (exec|build|run)|^eric@|Get-ChildItem|=== T\d)', re.M)

# Harness-injected wrappers. These are not Eric speaking.
HARNESS = re.compile(
    r'<command-name>|<local-command-stdout>|<system-reminder>|'
    r'<command-message>|<command-args>|^\[Request interrupted', re.M)


def looks_prose(text):
    """True if the message contains at least one plain sentence of 8+ words."""
    for sent in re.split(r'[.!?\n]', text):
        words = sent.split()
        if len(words) >= 8 and not re.search(r'[\\/{}<>=]|--', sent):
            return True
    return False


def user_texts(path):
    """Yield (index, text) for each genuine Eric message in one transcript."""
    with open(path, errors='ignore') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get('type') != 'user':
                continue
            content = rec.get('message', {}).get('content')
            parts = []
            if isinstance(content, str):
                parts = [content]
            elif isinstance(content, list):
                for p in content:
                    # tool_result blocks are output, not Eric typing
                    if isinstance(p, dict) and p.get('type') == 'text':
                        parts.append(p.get('text', ''))
            text = '\n'.join(t for t in parts if t).strip()
            if text:
                yield i, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sessions', default=DEFAULT_SESSIONS,
                    help='glob for Claude Code .jsonl transcripts')
    ap.add_argument('--out', required=True)
    ap.add_argument('--docs-out', required=True)
    ap.add_argument('--project', default='cis')
    ap.add_argument('--min-chars', type=int, default=40)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.expanduser(a.sessions)))
    if not files:
        print(f'no transcripts matched {a.sessions}', file=sys.stderr)
        return 1

    os.makedirs(a.docs_out, exist_ok=True)
    kept = seen = 0

    with open(a.out, 'w') as out:
        for path in files:
            sid = os.path.basename(path)[:8]
            date = ''
            try:
                import datetime
                date = datetime.datetime.fromtimestamp(
                    os.path.getmtime(path)).strftime('%Y-%m-%d')
            except OSError:
                pass

            verbatim = []
            for idx, text in user_texts(path):
                seen += 1
                if HARNESS.search(text):
                    continue
                if len(text) < a.min_chars:
                    continue
                noisy = bool(NOISE.search(text))
                if noisy and not looks_prose(text):
                    continue
                verbatim.append(text)
                out.write(json.dumps({
                    'id': f'cc-{sid}-{idx}',
                    'date': date,
                    'project': a.project,
                    'noisy': noisy,
                    'text': text[:1500],
                }) + '\n')
                kept += 1

            if verbatim:
                doc = os.path.join(a.docs_out, f'session-{sid}.md')
                with open(doc, 'w') as d:
                    d.write(f'# Claude Code session {sid} — Eric verbatim\n')
                    d.write(f'# source: {path}\n\n')
                    for t in verbatim:
                        d.write(t + '\n\n---\n\n')

    print(f'{kept} candidate asks from {len(files)} session(s) '
          f'({seen} user messages seen) -> {a.out}')
    print(f'verbatim sources -> {a.docs_out} (pass to card_gate --docs)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
