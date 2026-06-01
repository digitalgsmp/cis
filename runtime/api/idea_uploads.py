"""
api/idea_uploads.py — File upload endpoint for the Ideas page.
Routes:
    POST /api/ideas/upload  — accept a file, save to CIS incoming, return path
"""

import os
import uuid
from pathlib import Path
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

idea_uploads_bp = Blueprint("idea_uploads", __name__, url_prefix="/api/ideas")

UPLOAD_DIR = Path("/mnt/projects/cis/ingest/incoming")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp',
    'pdf', 'doc', 'docx', 'txt', 'md', 'csv', 'json', 'yaml', 'yml',
    'mp3', 'wav', 'ogg', 'mp4', 'mov', 'avi',
    'zip', 'gz', 'tar',
}


@idea_uploads_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Secure the filename and add a UUID prefix to avoid collisions
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    safe_name = f"{uuid.uuid4().hex[:8]}_{original_name}"
    save_path = UPLOAD_DIR / safe_name

    file.save(str(save_path))

    return jsonify({
        "success": True,
        "path": str(save_path),
        "name": original_name,
        "size": os.path.getsize(str(save_path)),
        "type": file.content_type,
    })
