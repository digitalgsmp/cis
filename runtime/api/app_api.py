"""
api_app.py — CIS Application API blueprint.
CRUD endpoints for ideas, projects, assets, schedule, domains, users, dashboard.
"""

from flask import Blueprint, jsonify, request
from cis_db import (
    create_idea, get_ideas, get_idea, update_idea, delete_idea,
    create_project, get_projects, get_project, update_project, delete_project, get_project_stats,
    create_asset, get_assets, update_asset, delete_asset,
    create_schedule_item, get_schedule_items, update_schedule_item, delete_schedule_item,
    get_domains, get_domain, update_domain,
    create_user, get_user_by_username, get_user_by_id, update_last_login,
    get_dashboard_stats,
    create_idea_attachment, get_idea_attachments, update_idea_attachment, delete_idea_attachment
)
from datetime import datetime
import hashlib

app_bp = Blueprint('app_api', __name__, url_prefix='/api/app')

SALT = 'cis_kernel_v1'


# ── Auth ────────────────────────────────────────────────────────────────────────

@app_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'success': False, 'error': 'Username and password required'}), 400

    username = data['username'].strip().lower()
    password = data['password']
    display = data.get('display_name', username)

    h = hashlib.sha256((password + SALT).encode()).hexdigest()
    result = create_user(username, h, role='user', display_name=display)

    if result['success']:
        return jsonify({'success': True, 'id': result['id']})
    return jsonify(result), 409


@app_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'success': False, 'error': 'Username and password required'}), 400

    username = data['username'].strip().lower()
    password = data['password']
    h = hashlib.sha256((password + SALT).encode()).hexdigest()

    user = get_user_by_username(username)
    if user and user['password'] == h:
        update_last_login(user['id'])
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'display_name': user['display_name'],
                'role': user['role']
            }
        })
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@app_bp.route('/auth/user', methods=['GET'])
def get_current_user():
    user_id = request.headers.get('X-CIS-User-Id', '')
    if not user_id:
        return jsonify({'success': False, 'error': 'No user specified'}), 401
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'display_name': user['display_name'],
            'role': user['role']
        }
    })


# ── Dashboard ───────────────────────────────────────────────────────────────────

@app_bp.route('/dashboard', methods=['GET'])
def dashboard():
    return jsonify(get_dashboard_stats())


# ── Ideas ───────────────────────────────────────────────────────────────────────

@app_bp.route('/ideas', methods=['GET'])
def list_ideas():
    domain = request.args.get('domain')
    status = request.args.get('status')
    owner = request.args.get('owner_id')
    ideas = get_ideas(domain=domain, status=status, owner_id=owner)
    return jsonify({'ideas': ideas})


@app_bp.route('/ideas', methods=['POST'])
def new_idea():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    result = create_idea(data)
    return jsonify(result), 201


@app_bp.route('/ideas/<idea_id>', methods=['GET'])
def get_single_idea(idea_id):
    idea = get_idea(idea_id)
    if not idea:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return jsonify(idea)


# ── Serve archive files (images, docs) for idea preview ────────────────────────

import mimetypes
import os as _os
from flask import send_file

ALLOWED_ROOTS = [
    "/mnt/archive",
    "/mnt/projects/cis",
]

@app_bp.route('/archive-file')
def serve_archive_file():
    """Serve a file from the archive for display in the UI.
    
    Security: only allows files under ALLOWED_ROOTS paths.
    Query param: ?path=/relative/path/to/file.jpg
    """
    file_path = request.args.get('path', '')
    if not file_path:
        return jsonify({'error': 'path parameter required'}), 400
    
    # Resolve and validate
    resolved = _os.path.abspath(file_path)
    allowed = False
    for root in ALLOWED_ROOTS:
        if resolved.startswith(_os.path.abspath(root)):
            allowed = True
            break
    
    if not allowed:
        return jsonify({'error': 'Access denied'}), 403
    
    if not _os.path.isfile(resolved):
        return jsonify({'error': 'File not found'}), 404
    
    mime_type, _ = mimetypes.guess_type(resolved)
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    return send_file(resolved, mimetype=mime_type)



@app_bp.route('/ideas/<idea_id>', methods=['PATCH'])
def modify_idea(idea_id):
    data = request.json
    result = update_idea(idea_id, data)
    return jsonify(result)


@app_bp.route('/ideas/<idea_id>', methods=['DELETE'])
def remove_idea(idea_id):
    result = delete_idea(idea_id)
    return jsonify(result)


@app_bp.route('/ideas/<idea_id>/attachments', methods=['GET'])
def list_attachments(idea_id):
    attachments = get_idea_attachments(idea_id)
    return jsonify({'attachments': attachments})


@app_bp.route('/ideas/<idea_id>/attachments', methods=['POST'])
def new_attachment(idea_id):
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Attachment data required'}), 400
    result = create_idea_attachment(idea_id, data)
    return jsonify(result), 201


@app_bp.route('/ideas/<idea_id>/attachments/<attachment_id>', methods=['PATCH'])
def modify_attachment(idea_id, attachment_id):
    data = request.json
    result = update_idea_attachment(attachment_id, data)
    return jsonify(result)


@app_bp.route('/ideas/<idea_id>/attachments/<attachment_id>', methods=['DELETE'])
def remove_attachment(idea_id, attachment_id):
    result = delete_idea_attachment(attachment_id)
    return jsonify(result)


@app_bp.route('/ideas/<idea_id>/attachments/upload', methods=['POST'])
def upload_attachment(idea_id):
    """Upload a file and attach it to an idea.
    
    Accepts multipart form data with:
      - file: the file to upload
      - name: display name (optional, defaults to filename)
      - type: attachment type (optional, inferred from mime type)
      - notes: optional notes
      - sort_order: optional sort position
    """
    import os as _os
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'Empty filename'}), 400
    
    # Determine attachment type from mime or extension
    name = request.form.get('name', file.filename)
    notes = request.form.get('notes', '')
    sort_order = int(request.form.get('sort_order', 0))
    
    # Detect type
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    ct = file.content_type or ''
    if ct.startswith('image/') or ext in ('jpg','jpeg','png','gif','webp','bmp','tiff'):
        att_type = request.form.get('type', 'image')
    elif ct.startswith('audio/') or ext in ('wav','mp3','flac','ogg','m4a','aac'):
        att_type = request.form.get('type', 'audio')
    elif ct.startswith('video/') or ext in ('mp4','mov','avi','webm','mkv'):
        att_type = request.form.get('type', 'video')
    elif ext in ('pdf','doc','docx','txt','md','rtf'):
        att_type = request.form.get('type', 'document')
    else:
        att_type = request.form.get('type', 'other')
    
    # Save to captures directory
    from datetime import datetime as _dt
    ts = _dt.now().strftime('%Y%m%d_%H%M%S')
    safe_name = f"{ts}_{file.filename}"
    save_dir = f"/mnt/projects/cis/captures/{att_type}"
    _os.makedirs(save_dir, exist_ok=True)
    save_path = _os.path.join(save_dir, safe_name)
    file.save(save_path)
    
    file_size = _os.path.getsize(save_path)
    
    result = create_idea_attachment(idea_id, {
        'type': att_type,
        'name': name,
        'path': save_path,
        'mime_type': ct or 'application/octet-stream',
        'file_size': file_size,
        'notes': notes,
        'sort_order': sort_order,
    })
    return jsonify(result), 201


# ── Projects ────────────────────────────────────────────────────────────────────

@app_bp.route('/projects', methods=['GET'])
def list_projects():
    domain = request.args.get('domain')
    status = request.args.get('status')
    owner = request.args.get('owner_id')
    projects = get_projects(domain=domain, status=status, owner_id=owner)
    return jsonify({'projects': projects})


@app_bp.route('/projects', methods=['POST'])
def new_project():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    result = create_project(data)
    if not result.get('success'):
        return jsonify(result), 400
    return jsonify(result), 201


@app_bp.route('/projects/<project_id>', methods=['GET'])
def get_single_project(project_id):
    project = get_project(project_id)
    if not project:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return jsonify(project)


@app_bp.route('/projects/<project_id>', methods=['PATCH'])
def modify_project(project_id):
    data = request.json
    result = update_project(project_id, data)
    return jsonify(result)


@app_bp.route('/projects/<project_id>', methods=['DELETE'])
def remove_project(project_id):
    result = delete_project(project_id)
    return jsonify(result)


@app_bp.route('/projects/stats', methods=['GET'])
def project_stats():
    return jsonify(get_project_stats())


# ── Assets ──────────────────────────────────────────────────────────────────────

@app_bp.route('/assets', methods=['GET'])
def list_assets():
    project = request.args.get('project_id')
    asset_type = request.args.get('type')
    status = request.args.get('status')
    owner = request.args.get('owner_id')
    search = request.args.get('search')
    assets = get_assets(project_id=project, asset_type=asset_type,
                        status=status, owner_id=owner, search=search)
    return jsonify({'assets': assets})


@app_bp.route('/assets', methods=['POST'])
def new_asset():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    result = create_asset(data)
    return jsonify(result), 201


@app_bp.route('/assets/<asset_id>', methods=['PATCH'])
def modify_asset(asset_id):
    data = request.json
    result = update_asset(asset_id, data)
    return jsonify(result)


@app_bp.route('/assets/<asset_id>', methods=['DELETE'])
def remove_asset(asset_id):
    result = delete_asset(asset_id)
    return jsonify(result)


# ── Schedule (schedule_items) ────────────────────────────────────────────────

@app_bp.route('/schedule', methods=['GET'])
def list_schedule():
    domain = request.args.get('domain')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    item_type = request.args.get('item_type')
    client_name = request.args.get('client_name')
    items = get_schedule_items(domain=domain, date_from=date_from,
                                date_to=date_to, status=status,
                                item_type=item_type,
                                client_name=client_name)
    return jsonify({'items': items})


@app_bp.route('/schedule', methods=['POST'])
def new_schedule_item():
    data = request.json
    if not data or not data.get('title'):
        return jsonify({'success': False, 'error': 'title is required'}), 400
    result = create_schedule_item(data)
    return jsonify(result), 201


@app_bp.route('/schedule/<item_id>', methods=['PATCH'])
def modify_schedule_item(item_id):
    data = request.json
    result = update_schedule_item(item_id, data)
    return jsonify(result)


@app_bp.route('/schedule/<item_id>', methods=['DELETE'])
def remove_schedule_item(item_id):
    result = delete_schedule_item(item_id)
    return jsonify(result)


# ── Domains ─────────────────────────────────────────────────────────────────────

@app_bp.route('/domains', methods=['GET'])
def list_domains():
    domains = get_domains()
    return jsonify({'domains': domains})


@app_bp.route('/domains/<domain_id>', methods=['GET'])
def get_single_domain(domain_id):
    domain = get_domain(domain_id)
    if not domain:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return jsonify(domain)


@app_bp.route('/domains/<domain_id>', methods=['PATCH'])
def modify_domain(domain_id):
    data = request.json
    result = update_domain(domain_id, data)
    return jsonify(result)
