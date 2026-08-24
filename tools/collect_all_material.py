#!/usr/bin/env python3
"""
collect_all_material.py — Comprehensive data collection for synthesis.
Groups by signal density:
  1. Session conversations (highest signal — full narrative arcs)
  2. KB conversations (human + chatgpt_conversation + agent exchanges)
  3. Key CIS files (AGENTS.md, HCP, configs, decisions)
  4. Card factory output (already-mined intents)
  5. Drive import clusters (grouped by folder, metadata only)
  6. Code/doc summaries (not raw files — extracted docstrings/comments)

Output: cards/synthesis_input.jsonl — one entry per data point with source tracking.
"""
import json, os, re, sqlite3, sys, time
from pathlib import Path

OUTPUT = 'cards/synthesis_input.jsonl'
CIS_ROOT = '/mnt/projects/cis'


def write_entry(data):
    with open(OUTPUT, 'a') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')


def collect_session_conversations():
    """Phase 1: Full conversations from all 8 profile DBs — richest signal."""
    print("=== PHASE 1: Session conversations ===", flush=True)

    dbs = [
        ('/home/eric/.hermes/state.db', 'prime'),
        ('/home/eric/.hermes-v4pro/state.db', 'v4pro'),
        ('/home/eric/.hermes-v4impl/state.db', 'v4impl'),
        ('/home/eric/.hermes-r1/state.db', 'r1'),
        ('/home/eric/.hermes-qwen/state.db', 'qwen'),
        ('/home/eric/.hermes-glm-reviewer/state.db', 'glm-reviewer'),
        ('/home/eric/.hermes-glm-verifier/state.db', 'glm-verifier'),
        ('/home/eric/.hermes-brainstorm/state.db', 'brainstorm'),
    ]

    total = 0
    for db_path, label in dbs:
        if not os.path.exists(db_path):
            continue
        try:
            con = sqlite3.connect(db_path)
            con.row_factory = sqlite3.Row

            sessions = con.execute(
                "SELECT id, title, started_at FROM sessions ORDER BY started_at"
            ).fetchall()

            for sess in sessions:
                msgs = con.execute(
                    "SELECT role, content, timestamp FROM messages "
                    "WHERE session_id=? AND content IS NOT NULL "
                    "ORDER BY timestamp",
                    (sess['id'],)
                ).fetchall()

                user_msgs = [m for m in msgs if m['role'] == 'user']
                if len(user_msgs) < 1:
                    continue

                # Build conversation summary: every user message + key agent turns
                conversation_lines = []
                agent_lines = []
                for m in msgs:
                    content = m['content'].replace('\n', ' ').replace('\r', '')
                    if not content.strip():
                        continue
                    if m['role'] == 'user':
                        conversation_lines.append(f"USER: {content[:500]}")
                    elif m['role'] in ('assistant', 'tool', 'system'):
                        # Keep first and last agent messages for context
                        agent_lines.append(f"AGENT({m['role']}): {content[:300]}")
                    else:
                        agent_lines.append(f"{m['role'].upper()}: {content[:300]}")

                # Trim agent messages to avoid bloat — keep first and last 2
                if len(agent_lines) > 4:
                    agent_lines = agent_lines[:2] + agent_lines[-2:]
                conversation_lines = conversation_lines + agent_lines

                conversation_text = '\n'.join(conversation_lines)[:4000]  # Cap at 4K chars

                write_entry({
                    'source': 'session',
                    'profile': label,
                    'session_id': sess['id'],
                    'session_title': (sess['title'] or 'untitled'),
                    'date': str(sess['started_at'] or '')[:10],
                    'user_message_count': len(user_msgs),
                    'content': conversation_text
                })
                total += 1

            con.close()
            print(f"  {label}: {len(sessions)} sessions", flush=True)
        except Exception as e:
            print(f"  WARN {label}: {e}", flush=True)

    print(f"  Total: {total} session conversations", flush=True)
    return total


def collect_kb_conversations():
    """Phase 2: KB — human conversations, chatgpt exchanges, CIS pipeline exchanges."""
    print("\n=== PHASE 2: KB conversations ===", flush=True)
    kb = f'{CIS_ROOT}/data/cis_memory.db'
    if not os.path.exists(kb):
        print("  KB not found", flush=True)
        return 0

    con = sqlite3.connect(kb)
    con.row_factory = sqlite3.Row
    total = 0

    # Human messages — highest signal
    human_rows = con.execute(
        "SELECT id, content, source FROM knowledge_messages "
        "WHERE role='human' AND content IS NOT NULL AND length(content)>20 "
        "ORDER BY id"
    ).fetchall()
    for row in human_rows:
        write_entry({
            'source': 'kb_human',
            'kb_source': row['source'] or 'unknown',
            'content': row['content'][:2000],
            'msg_id': row['id']
        })
    print(f"  Human: {len(human_rows)}", flush=True)
    total += len(human_rows)

    # ChatGPT conversations — Eric pasting to/from external advisors
    chat_rows = con.execute(
        "SELECT content, source FROM knowledge_messages "
        "WHERE role='chatgpt_conversation' AND content IS NOT NULL AND length(content)>30 "
        "ORDER BY rowid"
    ).fetchall()
    for row in chat_rows:
        write_entry({
            'source': 'kb_chatgpt',
            'kb_source': row['source'] or 'unknown',
            'content': row['content'][:3000]
        })
    print(f"  ChatGPT: {len(chat_rows)}", flush=True)
    total += len(chat_rows)

    # CIS pipeline exchanges (brain, draft, review1, review2, implementer, verifier)
    pipeline_roles = ['brain', 'draft', 'review1', 'review2', 'menter', 'verify',
                      'review1_consensus', 'revision_directive']
    for role in pipeline_roles:
        rows = con.execute(
            "SELECT content, source FROM knowledge_messages "
            "WHERE role=? AND content IS NOT NULL AND length(content)>30 "
            "ORDER BY rowid",
            (role,)
        ).fetchall()
        for row in rows:
            write_entry({
                'source': f'kb_{role}',
                'kb_source': row['source'] or 'unknown',
                'content': row['content'][:2000]
            })
        if rows:
            print(f"  {role}: {len(rows)}", flush=True)
            total += len(rows)

    # Assistant messages — agent responses to Eric
    asst_rows = con.execute(
        "SELECT content, source FROM knowledge_messages "
        "WHERE role='assistant' AND content IS NOT NULL AND length(content)>30 "
        "ORDER BY rowid"
    ).fetchall()
    for row in asst_rows:
        write_entry({
            'source': 'kb_assistant',
            'kb_source': row['source'] or 'unknown',
            'content': row['content'][:2000]
        })
    print(f"  Assistant: {len(asst_rows)}", flush=True)
    total += len(asst_rows)

    con.close()
    print(f"  Total KB: {total}", flush=True)
    return total


def collect_key_files():
    """Phase 3: Key CIS files that encode decisions, architecture, and intent."""
    print("\n=== PHASE 3: Key CIS files ===", flush=True)

    key_files = [
        'AGENTS.md',
        'PROJECT_CONTEXT_PACK_UPLOAD/HCP_01_INTENTIONS_AND_MISSION.md',
        'PROJECT_CONTEXT_PACK_UPLOAD/HCP_02_SYSTEM_ARCHITECTURE.md',
        'PROJECT_CONTEXT_PACK_UPLOAD/HCP_03_ACTIVE_WORKSPACE.md',
        'PROJECT_CONTEXT_PACK_UPLOAD/HCP_04_DECISIONS_AND_RATIONALE.md',
        'PROJECT_CONTEXT_PACK_UPLOAD/HCP_05_KNOWLEDGE_BASE.md',
        'docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md',
        'docs/SPEC_CONTROL_PLANE_OBSERVATION.md',
        'docs/PHASE1_ROOT_DIRECTIVE_FOR_CLAUDE.md',
        'docs/DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md',
        'config/agents_static.yaml',
    ]

    total = 0
    for f in key_files:
        path = os.path.join(CIS_ROOT, f)
        if os.path.exists(path):
            try:
                content = open(path).read()
                write_entry({
                    'source': 'cis_file',
                    'file': f,
                    'content': content[:5000]
                })
                print(f"  {f}: {len(content)} chars", flush=True)
                total += 1
            except Exception as e:
                print(f"  WARN {f}: {e}", flush=True)

    # Also collect all .md files in docs/ and cards/
    for folder in ['docs', 'cards']:
        for root, dirs, files in os.walk(os.path.join(CIS_ROOT, folder)):
            for f in files:
                if f.endswith('.md') or f.endswith('.jsonl'):
                    path = os.path.join(root, f)
                    rel = os.path.relpath(path, CIS_ROOT)
                    try:
                        content = open(path).read()
                        if len(content) > 50:
                            write_entry({
                                'source': 'cis_file',
                                'file': rel,
                                'content': content[:3000]
                            })
                            total += 1
                    except:
                        pass

    print(f"  Total files: {total}", flush=True)
    return total


def collect_drive_clusters():
    """Phase 4: Drive imports — group by folder, extract metadata."""
    print("\n=== PHASE 4: Drive import clusters ===", flush=True)
    drive_root = f'{CIS_ROOT}/data/drive_imports'
    if not os.path.exists(drive_root):
        print("  No drive imports", flush=True)
        return 0

    # Count by extension
    ext_counts = {}
    folder_counts = {}
    total_files = 0

    for root, dirs, files in os.walk(drive_root):
        rel = os.path.relpath(root, drive_root)
        if rel == '.':
            rel = 'root'
        folder_counts[rel] = len(files)
        for f in files:
            ext = os.path.splitext(f)[1].lower() or '(no ext)'
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
            total_files += 1

    # Write a cluster summary entry
    write_entry({
        'source': 'drive_cluster',
        'total_files': total_files,
        'folder_breakdown': json.dumps(folder_counts),
        'file_types': json.dumps(ext_counts),
        'content': (
            f"Google Drive import: {total_files} files across {len(folder_counts)} folders. "
            f"Top folders: {dict(sorted(folder_counts.items(), key=lambda x: -x[1])[:20])}. "
            f"File types: {dict(sorted(ext_counts.items(), key=lambda x: -x[1])[:20])}"
        )
    })
    print(f"  {total_files} files in {len(folder_counts)} folders", flush=True)
    return 1  # one cluster entry


def main():
    # Clear output
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)

    total = 0
    total += collect_session_conversations()
    total += collect_kb_conversations()
    total += collect_key_files()
    total += collect_drive_clusters()

    # Count output
    with open(OUTPUT) as f:
        lines = f.readlines()
    size_mb = os.path.getsize(OUTPUT) / (1024*1024)

    print(f"\n=== COLLECTION COMPLETE ===", flush=True)
    print(f"Output: {OUTPUT} ({size_mb:.1f} MB, {len(lines)} entries)", flush=True)
    print(f"Total entries written: {total}", flush=True)


if __name__ == '__main__':
    main()
