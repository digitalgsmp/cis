"""
cis_db.py — Central database module for CIS kernel.
SQLite-backed, provides all CRUD for ideas, projects, assets, schedule, users.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/mnt/projects/cis/memory/cis_app.db")

# ── Schema ──────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,          -- hashed
    role        TEXT NOT NULL DEFAULT 'user',  -- 'admin', 'user', 'viewer'
    display_name TEXT DEFAULT '',
    created     TEXT NOT NULL,
    last_login  TEXT
);

CREATE TABLE IF NOT EXISTS ideas (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    link        TEXT DEFAULT '',
    date        TEXT DEFAULT '',
    description TEXT DEFAULT '',
    context     TEXT DEFAULT '',
    domain      TEXT DEFAULT 'creative',
    category    TEXT DEFAULT '',
    medium      TEXT DEFAULT '',
    story_type  TEXT DEFAULT '',
    user_level  TEXT DEFAULT 'beginner',
    tags        TEXT DEFAULT '[]',      -- JSON array
    content     TEXT DEFAULT '',         -- full document text / file content
    file_path   TEXT DEFAULT '',         -- path to attached file
    status      TEXT DEFAULT 'captured', -- captured, promoted
    owner_id    TEXT DEFAULT '',
    created     TEXT NOT NULL,
    updated     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    owner           TEXT DEFAULT '',
    owner_id        TEXT DEFAULT '',
    start_date      TEXT DEFAULT '',
    due_date        TEXT DEFAULT '',
    level           TEXT DEFAULT 'beginner',
    type            TEXT DEFAULT '',
    goal            TEXT DEFAULT '',
    domain          TEXT DEFAULT 'creative',
    description     TEXT DEFAULT '',
    source_idea_id  TEXT DEFAULT '',
    status          TEXT DEFAULT 'initiated',
    progress        INTEGER DEFAULT 0,
    linked_research  TEXT DEFAULT '[]',
    linked_references TEXT DEFAULT '[]',
    linked_learning  TEXT DEFAULT '[]',
    linked_templates TEXT DEFAULT '[]',
    linked_checklists TEXT DEFAULT '[]',
    schedule_slots   TEXT DEFAULT '[]',
    created         TEXT NOT NULL,
    updated         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    type        TEXT DEFAULT 'reference',  -- research, reference, learning, template, checklist, output, note
    url         TEXT DEFAULT '',
    path        TEXT DEFAULT '',
    project_id  TEXT DEFAULT '',
    category    TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    tags        TEXT DEFAULT '[]',
    status      TEXT DEFAULT 'draft',      -- draft, reviewed, approved, locked, deprecated
    owner_id    TEXT DEFAULT '',
    created     TEXT NOT NULL,
    updated     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schedule_slots (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    duration    REAL DEFAULT 1.0,
    date        TEXT DEFAULT '',
    start_time  TEXT DEFAULT '',
    end_time    TEXT DEFAULT '',
    category    TEXT DEFAULT '',
    project_id  TEXT DEFAULT '',
    tool        TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    status      TEXT DEFAULT 'planned',   -- planned, active, completed, blocked
    owner_id    TEXT DEFAULT '',
    created     TEXT NOT NULL,
    updated     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS domains (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    label       TEXT DEFAULT '',
    categories  TEXT DEFAULT '[]',
    media       TEXT DEFAULT '[]',
    created     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS idea_attachments (
    id          TEXT PRIMARY KEY,
    idea_id     TEXT NOT NULL,
    type        TEXT NOT NULL,       -- image, audio, video, document, link, youtube, capture_audio, capture_video, capture_photo
    name        TEXT NOT NULL DEFAULT '',
    path        TEXT DEFAULT '',      -- local file path (archive files or captures)
    url         TEXT DEFAULT '',      -- web URL (YouTube, links, etc.)
    mime_type   TEXT DEFAULT '',
    file_size   INTEGER DEFAULT 0,
    notes       TEXT DEFAULT '',
    sort_order  INTEGER DEFAULT 0,
    created     TEXT NOT NULL,
    FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_attachments_idea ON idea_attachments(idea_id);

CREATE TABLE IF NOT EXISTS permissions (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    object_type TEXT NOT NULL,   -- 'project', 'asset', 'schedule'
    object_id   TEXT NOT NULL,
    permission  TEXT DEFAULT 'view',  -- 'view', 'edit', 'admin'
    granted_by  TEXT DEFAULT '',
    created     TEXT NOT NULL
);
"""


# ── Connection ──────────────────────────────────────────────────────────────

def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

    # ── Migrate: add content/file_path columns to ideas table ──────────
    conn = get_db()
    try:
        conn.execute("ALTER TABLE ideas ADD COLUMN content TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # already exists
    try:
        conn.execute("ALTER TABLE ideas ADD COLUMN file_path TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # already exists
    conn.commit()
    conn.close()

    # Seed default domains if empty
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM domains").fetchone()[0]
    if existing == 0:
        default_domains = [
            ('creative', 'Creative Production (WIAS)',
             json.dumps(['Word / Web','Image','Action','Sound','Non-Digital Product','Wildcard']),
             json.dumps(['Poetry','Fiction','Script / Screenplay','Song Lyric','Nonfiction / Essay',
                        'Drawing','Painting','2D Animation','3D Animation','3D Game','Film / Video',
                        'Music Production','Sound Design','Learning Course','Stream Content','Web Post',
                        'AR / VR','Photo','Comic','Zine','Installation','Performance'])),
            ('socialcare', 'Social Care / Work',
             json.dumps(['Case Management','Assessment','Referral','Intervention','Reporting','Supervision','Training','Policy']),
             json.dumps(['Intake Form','Case Note','Assessment Report','Support Plan','Risk Assessment',
                        'Referral Letter','Progress Note','Care Plan','Discharge Summary','Audit Record',
                        'Policy Document','Training Material','Client Correspondence','Team Handoff'])),
            ('personal', 'Personal / Life',
             json.dumps(['Home','Body','Mind','Finance','Relationships','Projects','Infrastructure','Philosophy']),
             json.dumps(['Task List','Journal Entry','Habit Tracker','Budget Plan','Goal Sheet',
                        'Inventory','Calendar Event','Note','Decision Log','Review','Routine','Reflection'])),
            ('technical', 'Technical / Infrastructure',
             json.dumps(['Infrastructure','Development','Deployment','Security','Data','Integration','Research','Documentation']),
             json.dumps(['Architecture Doc','API Spec','Config','Script','Test Plan','Deployment Runbook',
                        'Incident Report','Performance Review','Security Audit','Migration Plan','ADR',
                        'Knowledge Base','Changelog','Roadmap'])),
            ('learning', 'Learning / Education',
             json.dumps(['Skill Building','Theory','Practice','Research','Teaching','Certification','Exploration']),
             json.dumps(['Course Note','Tutorial','Exercise','Study Guide','Flashcard','Reading List',
                        'Project Log','Lab Report','Workshop Plan','Curriculum','Assessment','Reflection'])),
        ]
        conn.executemany(
            "INSERT INTO domains (id, name, label, categories, media, created) VALUES (?, ?, ?, ?, ?, ?)",
            [(d[0], d[1], d[1], d[2], d[3], datetime.utcnow().isoformat()) for d in default_domains]
        )
        conn.commit()
    conn.close()


# ── Helpers ─────────────────────────────────────────────────────────────────

def _now():
    return datetime.utcnow().isoformat()

def _json_list(val):
    if isinstance(val, str):
        return val
    return json.dumps(val or [])

def _json_load(val):
    if isinstance(val, str):
        return json.loads(val)
    return val or []

def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    for field in ['tags', 'linked_research', 'linked_references', 'linked_learning',
                  'linked_templates', 'linked_checklists', 'schedule_slots',
                  'categories', 'media']:
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# ── User CRUD ───────────────────────────────────────────────────────────────

def create_user(username, password_hash, role='user', display_name=''):
    conn = get_db()
    uid = 'user_' + datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    now = _now()
    try:
        conn.execute(
            "INSERT INTO users (id, username, password, role, display_name, created) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, username, password_hash, role, display_name, now)
        )
        conn.commit()
        return {'success': True, 'id': uid}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'Username already exists'}
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_last_login(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (_now(), user_id))
    conn.commit()
    conn.close()


# ── Ideas CRUD ──────────────────────────────────────────────────────────────

def create_idea(data):
    conn = get_db()
    uid = 'idea_' + _now().replace(':', '').replace('-', '')
    now = _now()
    conn.execute("""
        INSERT INTO ideas (id, name, link, date, description, context, domain,
                          category, medium, story_type, user_level, tags,
                          content, file_path, status, owner_id, created, updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uid, data['name'], data.get('link', ''), data.get('date', ''),
        data.get('description', ''), data.get('context', ''),
        data.get('domain', 'creative'), data.get('category', ''),
        data.get('medium', ''), data.get('story_type', ''),
        data.get('user_level', 'beginner'),
        _json_list(data.get('tags', [])),
        data.get('content', ''), data.get('file_path', ''),
        data.get('status', 'captured'),
        data.get('owner_id', ''),
        now, now
    ))
    conn.commit()
    conn.close()
    return {'success': True, 'id': uid}


def get_ideas(domain=None, status=None, owner_id=None):
    conn = get_db()
    query = "SELECT * FROM ideas WHERE 1=1"
    params = []
    if domain:
        query += " AND domain = ?"; params.append(domain)
    if status:
        query += " AND status = ?"; params.append(status)
    if owner_id:
        query += " AND owner_id = ?"; params.append(owner_id)
    query += " ORDER BY created DESC"
    rows = conn.execute(query, params).fetchall()
    ideas = [row_to_dict(r) for r in rows]
    # Attach attachments to each idea
    for idea in ideas:
        atts = conn.execute(
            "SELECT * FROM idea_attachments WHERE idea_id = ? ORDER BY sort_order, created",
            (idea['id'],)
        ).fetchall()
        idea['attachments'] = [row_to_dict(a) for a in atts]
    conn.close()
    return ideas


def get_idea(idea_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    if not row:
        conn.close()
        return None
    idea = row_to_dict(row)
    atts = conn.execute(
        "SELECT * FROM idea_attachments WHERE idea_id = ? ORDER BY sort_order, created",
        (idea_id,)
    ).fetchall()
    idea['attachments'] = [row_to_dict(a) for a in atts]
    conn.close()
    return idea


def update_idea(idea_id, data):
    conn = get_db()
    now = _now()
    fields = []
    params = []
    for key in ['name', 'link', 'date', 'description', 'context', 'domain',
                'category', 'medium', 'story_type', 'user_level', 'content',
                'file_path', 'status']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if 'tags' in data:
        fields.append("tags = ?")
        params.append(_json_list(data['tags']))
    if fields:
        fields.append("updated = ?")
        params.append(now)
        params.append(idea_id)
        conn.execute(f"UPDATE ideas SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {'success': True}


def delete_idea(idea_id):
    conn = get_db()
    conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()
    return {'success': True}


# ── Projects CRUD ───────────────────────────────────────────────────────────

def create_project(data):
    conn = get_db()
    uid = 'proj_' + _now().replace(':', '').replace('-', '')
    now = _now()
    conn.execute("""
        INSERT INTO projects (id, name, owner, owner_id, start_date, due_date,
                             level, type, goal, domain, description, source_idea_id,
                             status, progress, linked_research, linked_references,
                             linked_learning, linked_templates, linked_checklists,
                             schedule_slots, created, updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uid, data['name'], data.get('owner', ''), data.get('owner_id', ''),
        data.get('start_date', ''), data.get('due_date', ''),
        data.get('level', 'beginner'), data.get('type', ''),
        data.get('goal', ''), data.get('domain', 'creative'),
        data.get('description', ''), data.get('source_idea_id', ''),
        data.get('status', 'initiated'), data.get('progress', 0),
        _json_list(data.get('linked_research', [])),
        _json_list(data.get('linked_references', [])),
        _json_list(data.get('linked_learning', [])),
        _json_list(data.get('linked_templates', [])),
        _json_list(data.get('linked_checklists', [])),
        _json_list(data.get('schedule_slots', [])),
        now, now
    ))
    conn.commit()
    conn.close()

    # If sourced from an idea, mark the idea promoted
    if data.get('source_idea_id'):
        conn = get_db()
        conn.execute("UPDATE ideas SET status = 'promoted', updated = ? WHERE id = ?",
                     (now, data['source_idea_id']))
        conn.commit()
        conn.close()

    return {'success': True, 'id': uid}


def get_projects(domain=None, status=None, owner_id=None):
    conn = get_db()
    query = "SELECT * FROM projects WHERE 1=1"
    params = []
    if domain:
        query += " AND domain = ?"; params.append(domain)
    if status:
        query += " AND status = ?"; params.append(status)
    if owner_id:
        query += " AND owner_id = ?"; params.append(owner_id)
    query += " ORDER BY updated DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_project(project_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


def update_project(project_id, data):
    conn = get_db()
    now = _now()
    fields = []
    params = []
    for key in ['name', 'owner', 'start_date', 'due_date', 'level', 'type',
                'goal', 'domain', 'description', 'status', 'progress']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    for arr_key in ['linked_research', 'linked_references', 'linked_learning',
                     'linked_templates', 'linked_checklists', 'schedule_slots']:
        if arr_key in data:
            fields.append(f"{arr_key} = ?")
            params.append(_json_list(data[arr_key]))
    if fields:
        fields.append("updated = ?")
        params.append(now)
        params.append(project_id)
        conn.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {'success': True}


def delete_project(project_id):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return {'success': True}


def get_project_stats():
    conn = get_db()
    rows = conn.execute("SELECT status, COUNT(*) as count, domain FROM projects GROUP BY status, domain").fetchall()
    total = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    conn.close()
    return {
        'total': total,
        'breakdown': [dict(r) for r in rows]
    }


# ── Assets CRUD ─────────────────────────────────────────────────────────────

def create_asset(data):
    conn = get_db()
    uid = 'asset_' + _now().replace(':', '').replace('-', '')
    now = _now()
    conn.execute("""
        INSERT INTO assets (id, name, type, url, path, project_id, category,
                           notes, tags, status, owner_id, created, updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uid, data['name'], data.get('type', 'reference'),
        data.get('url', ''), data.get('path', ''), data.get('project_id', ''),
        data.get('category', ''), data.get('notes', ''),
        _json_list(data.get('tags', [])),
        data.get('status', 'draft'), data.get('owner_id', ''),
        now, now
    ))
    conn.commit()
    conn.close()
    return {'success': True, 'id': uid}


def get_assets(project_id=None, asset_type=None, status=None, owner_id=None, search=None):
    conn = get_db()
    query = "SELECT * FROM assets WHERE 1=1"
    params = []
    if project_id:
        query += " AND project_id = ?"; params.append(project_id)
    if asset_type:
        query += " AND type = ?"; params.append(asset_type)
    if status:
        query += " AND status = ?"; params.append(status)
    if owner_id:
        query += " AND owner_id = ?"; params.append(owner_id)
    if search:
        query += " AND (name LIKE ? OR notes LIKE ? OR category LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])
    query += " ORDER BY updated DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def update_asset(asset_id, data):
    conn = get_db()
    now = _now()
    fields = []
    params = []
    for key in ['name', 'type', 'url', 'path', 'project_id', 'category', 'notes', 'status']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if 'tags' in data:
        fields.append("tags = ?")
        params.append(_json_list(data['tags']))
    if fields:
        fields.append("updated = ?")
        params.append(now)
        params.append(asset_id)
        conn.execute(f"UPDATE assets SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {'success': True}


def delete_asset(asset_id):
    conn = get_db()
    conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    conn.commit()
    conn.close()
    return {'success': True}


# ── Schedule CRUD (schedule_items) ──────────────────────────────────────────

def create_schedule_item(data):
    conn = get_db()
    uid = 'sched_' + _now().replace(':', '').replace('-', '')
    now = _now()
    all_day = 1 if data.get('all_day') else 0
    item_type = data.get('item_type', 'task')
    # Default status: appointment → scheduled, everything else → open
    if 'status' not in data:
        status = 'scheduled' if item_type == 'appointment' else 'open'
    else:
        status = data['status']
    # presented_date defaults to today if not provided
    presented = data.get('presented_date') or now[:10]
    conn.execute("""
        INSERT INTO schedule_items (id, title, domain, client_name, item_type,
                    presented_date, due_date, scheduled_date,
                    start_time, end_time, all_day, priority,
                    status, notes, outcome, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uid, data['title'], data.get('domain', 'personal'),
        data.get('client_name'), item_type,
        presented, data.get('due_date'), data.get('scheduled_date'),
        data.get('start_time'), data.get('end_time'), all_day,
        data.get('priority', 'medium'), status,
        data.get('notes', ''), data.get('outcome', ''), now, now
    ))
    conn.commit()
    conn.close()
    return {'success': True, 'id': uid}


def get_schedule_items(domain=None, date_from=None, date_to=None,
                        status=None, item_type=None, client_name=None):
    conn = get_db()
    query = "SELECT * FROM schedule_items WHERE 1=1"
    params = []
    if domain:
        query += " AND domain = ?"; params.append(domain)
    if date_from:
        query += " AND (scheduled_date >= ? OR (scheduled_date IS NULL AND due_date >= ?) OR (scheduled_date IS NULL AND due_date IS NULL AND presented_date >= ?))"
        params.extend([date_from, date_from, date_from])
    if date_to:
        query += " AND (scheduled_date <= ? OR (scheduled_date IS NULL AND due_date <= ?) OR (scheduled_date IS NULL AND due_date IS NULL AND presented_date <= ?))"
        params.extend([date_to, date_to, date_to])
    if status:
        if status == 'active':
            query += " AND status IN ('open','scheduled','in_progress','waiting','blocked')"
        else:
            query += " AND status = ?"; params.append(status)
    if item_type:
        query += " AND item_type = ?"; params.append(item_type)
    if client_name:
        query += " AND client_name = ?"; params.append(client_name)
    query += " ORDER BY COALESCE(scheduled_date, due_date, presented_date), start_time"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    items = []
    for r in rows:
        item = row_to_dict(r)
        # Compute display_date for frontend
        item['display_date'] = item.get('scheduled_date') or item.get('due_date') or item.get('presented_date')
        items.append(item)
    return items


def update_schedule_item(item_id, data):
    conn = get_db()
    now = _now()
    fields = []
    params = []
    for key in ['title', 'domain', 'client_name', 'item_type',
                'presented_date', 'due_date', 'scheduled_date',
                'start_time', 'end_time', 'all_day', 'priority',
                'status', 'notes', 'outcome']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if fields:
        fields.append("updated_at = ?")
        params.append(now)
        # started_at: set when status→in_progress, only if not already set
        if 'status' in data and data['status'] == 'in_progress':
            fields.append("started_at = COALESCE(started_at, ?)")
            params.append(now)
        # started_at: clear only when explicitly reset to open or scheduled
        if 'status' in data and data['status'] in ('open', 'scheduled'):
            fields.append("started_at = NULL")
        # completed_at: set when status→done
        if 'status' in data and data['status'] == 'done':
            fields.append("completed_at = ?")
            params.append(now)
        # completed_at: clear when moved from done to anything else
        if 'status' in data and data['status'] != 'done':
            fields.append("completed_at = NULL")
        params.append(item_id)
        conn.execute(f"UPDATE schedule_items SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {'success': True}


def delete_schedule_item(item_id):
    conn = get_db()
    conn.execute("DELETE FROM schedule_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {'success': True}


# ── Domain CRUD ─────────────────────────────────────────────────────────────

def get_domains():
    conn = get_db()
    rows = conn.execute("SELECT * FROM domains ORDER BY name").fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_domain(domain_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM domains WHERE id = ?", (domain_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


def update_domain(domain_id, data):
    conn = get_db()
    fields = []
    params = []
    for key in ['name', 'label']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if 'categories' in data:
        fields.append("categories = ?")
        params.append(_json_list(data['categories']))
    if 'media' in data:
        fields.append("media = ?")
        params.append(_json_list(data['media']))
    if fields:
        params.append(domain_id)
        conn.execute(f"UPDATE domains SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {'success': True}


# ── Dashboard stats ─────────────────────────────────────────────────────────

def get_dashboard_stats():
    conn = get_db()
    stats = {}
    stats['projects_total'] = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    stats['projects_active'] = conn.execute("SELECT COUNT(*) FROM projects WHERE status IN ('initiated','active')").fetchone()[0]
    stats['projects_complete'] = conn.execute("SELECT COUNT(*) FROM projects WHERE status = 'complete'").fetchone()[0]
    stats['projects_blocked'] = conn.execute("SELECT COUNT(*) FROM projects WHERE status = 'blocked'").fetchone()[0]
    stats['ideas_total'] = conn.execute("SELECT COUNT(*) FROM ideas").fetchone()[0]
    stats['assets_total'] = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    stats['slots_total'] = conn.execute("SELECT COUNT(*) FROM schedule_items").fetchone()[0]
    stats['users_total'] = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return stats


# ── Idea Attachments CRUD ─────────────────────────────────────────────────

def create_idea_attachment(idea_id, data):
    conn = get_db()
    uid = 'att_' + datetime.now().strftime('%Y%m%d%H%M%S%f')
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO idea_attachments (id, idea_id, type, name, path, url,
                                      mime_type, file_size, notes, sort_order, created)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uid, idea_id,
        data.get('type', 'image'),
        data.get('name', ''),
        data.get('path', ''),
        data.get('url', ''),
        data.get('mime_type', ''),
        data.get('file_size', 0),
        data.get('notes', ''),
        data.get('sort_order', 0),
        now
    ))
    conn.commit()
    conn.close()
    return {'success': True, 'id': uid}


def get_idea_attachments(idea_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM idea_attachments WHERE idea_id = ? ORDER BY sort_order, created",
        (idea_id,)
    ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def update_idea_attachment(attachment_id, data):
    conn = get_db()
    fields = []
    params = []
    for key in ['type', 'name', 'path', 'url', 'mime_type', 'file_size', 'notes', 'sort_order']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if fields:
        params.append(attachment_id)
        conn.execute(f"UPDATE idea_attachments SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {'success': True}


def delete_idea_attachment(attachment_id):
    conn = get_db()
    conn.execute("DELETE FROM idea_attachments WHERE id = ?", (attachment_id,))
    conn.commit()
    conn.close()
    return {'success': True}


def delete_idea_attachments_by_idea(idea_id):
    conn = get_db()
    conn.execute("DELETE FROM idea_attachments WHERE idea_id = ?", (idea_id,))
    conn.commit()
    conn.close()
    return {'success': True}


# ── Init on import ──────────────────────────────────────────────────────────
init_db()
