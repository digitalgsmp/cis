"""
cis_lms_api.py — LMS API Blueprint for CIS Flask backend.

Endpoints:
  GET  /api/lms/courses       — List all registered courses
  GET  /api/lms/courses/:id   — Get course with lessons
  POST /api/lms/search        — Semantic search across course content
  POST /api/lms/scan          — Scan for new courses
  POST /api/lms/index         — Index all courses into ChromaDB
  POST /api/lms/suggest       — Suggest training for a project or skill
  GET  /api/lms/dashboard     — LMS dashboard stats
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import json, os, sys

# Ensure we can import cis_lms
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

lms_bp = Blueprint('lms_api', __name__, url_prefix='/api/lms')


@lms_bp.route('/courses', methods=['GET'])
def list_courses():
    """List all registered courses."""
    try:
        from cis_lms import get_all_courses
        courses = get_all_courses()
        return jsonify({'courses': courses, 'total': len(courses)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@lms_bp.route('/courses/<course_id>', methods=['GET'])
def get_course(course_id):
    """Get a course with all its lessons."""
    try:
        from cis_lms import get_course, get_course_lessons
        course = get_course(course_id)
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        lessons = get_course_lessons(course_id)
        return jsonify({'course': course, 'lessons': lessons, 'lesson_count': len(lessons)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@lms_bp.route('/search', methods=['POST'])
def search():
    """Semantic search across course content."""
    try:
        from cis_lms import search_courses
        data = request.json or {}
        query = data.get('query', '')
        if not query:
            return jsonify({'success': False, 'error': 'Query required'}), 400
        limit = data.get('limit', 10)
        level = data.get('level')
        domain = data.get('domain')
        results = search_courses(query, limit=limit, level=level, domain=domain)
        return jsonify({'results': results, 'total': len(results)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@lms_bp.route('/scan', methods=['POST'])
def scan():
    """Scan tutorial folders for new courses."""
    try:
        from cis_lms import scan_tutorial_folders
        data = request.json or {}
        dry_run = data.get('dry_run', True)
        results = scan_tutorial_folders(dry_run=dry_run)
        return jsonify({
            'courses': len(results),
            'lessons': sum(len(c.get('lessons', [])) for c in results),
            'details': results[:50]  # Cap response
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@lms_bp.route('/index', methods=['POST'])
def index():
    """Index all course content into ChromaDB."""
    try:
        from cis_lms import index_courses
        data = request.json or {}
        force = data.get('force', False)
        stats = index_courses(force=force)
        return jsonify({'success': True, 'indexed': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@lms_bp.route('/suggest', methods=['POST'])
def suggest():
    """Suggest training for a project or skill need."""
    try:
        from cis_lms import suggest_training
        data = request.json or {}
        project_id = data.get('project_id')
        skill_needed = data.get('skill')
        limit = data.get('limit', 5)
        suggestions = suggest_training(
            project_id=project_id,
            skill_needed=skill_needed,
            limit=limit
        )
        return jsonify({'suggestions': suggestions, 'total': len(suggestions)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@lms_bp.route('/dashboard', methods=['GET'])
def lms_dashboard():
    """LMS-specific dashboard stats."""
    try:
        from cis_lms import get_dashboard_stats
        stats = get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@lms_bp.route('/schedule', methods=['POST'])
def suggest_schedule():
    """
    Suggest training blocks on the schedule.
    Given a skill need or project, returns suggested schedule slots
    that can be created via the schedule API.
    """
    try:
        from cis_lms import suggest_training
        data = request.json or {}
        project_id = data.get('project_id')
        skill_needed = data.get('skill')
        limit = data.get('limit', 3)

        suggestions = suggest_training(
            project_id=project_id,
            skill_needed=skill_needed,
            limit=limit
        )

        # Convert suggestions to schedule slot proposals
        slots = []
        for s in suggestions:
            # Estimate 45min per lesson
            duration = 45
            slots.append({
                'title': f"Study: {s['course']} - {s['lesson']}",
                'duration': duration,
                'category': 'learning',
                'project_id': s.get('course_id', ''),
                'notes': f"Auto-suggested from LMS\nCourse: {s['course']}\nLesson: {s['lesson']}\nReason: {s['reason']}",
                'source': 'lms_suggestion',
                'lesson_id': s.get('lesson_id', '')
            })

        return jsonify({'slots': slots, 'total': len(slots)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
