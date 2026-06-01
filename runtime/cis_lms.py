#!/usr/bin/env python3
"""
cis_lms.py — CIS Learning Management System

Discovers tutorial folders, registers courses as Projects, lessons as Assets,
indexes content into ChromaDB vector store for semantic search, and provides
training schedule auto-suggestion.

Architecture:
  TUTORIAL FOLDER → Course Scanner → Projects (courses) + Assets (lessons)
                                    → ChromaDB (semantic search)
                                    → Training Scheduler (calendar slots)
                                    → Agent Query API

Usage:
  python3 cis_lms.py --scan           # Discover and register new courses
  python3 cis_lms.py --index          # Index all course content into vector DB
  python3 cis_lms.py --search "color grading"  # Search across course content
  python3 cis_lms.py --suggest "proj_xxx"      # Suggest training for a project
  python3 cis_lms.py --catalog        # List all registered courses
"""

import os, sys, time, json, re, subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# ── Configuration ──────────────────────────────────────────────────────────
CIS_DB_PATH = Path("/mnt/projects/cis/memory/cis_app.db")
CHROMA_PATH = Path("/mnt/projects/cis/memory/chromadb")

# Tutorial source folders — these are our course libraries
TUTORIAL_ROOTS = {
    "image_blender":     Path("/mnt/archive/_3 Image/Creative 24/Blender Tuts"),
    "image_photoshop":   Path("/mnt/archive/_3 Image/Creative 24/Photoshop Tuts"),
    "image_nuke":        Path("/mnt/archive/_3 Image/Creative 24/Nuke Tuts"),
    "image_resolve":     Path("/mnt/archive/_3 Image/Creative 24/Resolve Studio Tuts"),
    "image_learnsq":     Path("/mnt/archive/_3 Image/Learn Squared – Production Concept Art (2018) with Jan Urschel"),
    "action_animation":  Path("/mnt/archive/_4 Action/Animation"),
    "action_cascadeur":  Path("/mnt/archive/_4 Action/Animation/Cascadeur_2022.3"),
    "action_blender":    Path("/mnt/archive/_4 Action/Animation/Blender Tuts"),
}

# Subdirectories or folders to EXCLUDE (asset libraries, not courses)
EXCLUDE_SUBDIRS = {"Blender Addons", "Blender Assetts", "Unreal Assetts",
                   "Motion Capture Files", "_Kitbash", "_Bigmediumsmall",
                   "create 2024 Software", "Jam Boards", "Luts",
                   "Filmmaking Software", "Blender Tuts"}

# Graceful course name cleaning — remove known non-course entries
EXCLUDE_COURSE_PREFIXES = {"_", "."}

# Software/tool tags derived from folder path
FOLDER_SOFTWARE_MAP = {
    "blender": "Blender",
    "nuke": "Nuke",
    "photoshop": "Photoshop",
    "resolve": "DaVinci Resolve",
    "unreal": "Unreal Engine",
    "cascadeur": "Cascadeur",
    "maya": "Maya",
    "substance": "Substance Painter",
    "zbrush": "ZBrush",
    "houdini": "Houdini",
}

# Level hints from course names
LEVEL_KEYWORDS = {
    "beginner": ["beginner", "absolute", "introduction", "fundamentals", "basics", "101", "starter"],
    "intermediate": ["intermediate", "advanced", "pro", "mastering", "production", "in-depth"],
    "professional": ["master", "expert", "professional", "senior", "production-ready"],
}

LOG_FILE = Path("/mnt/projects/cis/runtime/cis_lms_log.md")


# ── Logger ─────────────────────────────────────────────────────────────────

def log(msg, level="INFO"):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] [LMS] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


# ── Helpers ────────────────────────────────────────────────────────────────

def _now():
    return datetime.utcnow().isoformat()


def detect_software(folder_path: str, course_name: str) -> list:
    """Detect which software/tool a course covers from path + name."""
    path_lower = folder_path.lower() + " " + course_name.lower()
    found = []
    for keyword, software in FOLDER_SOFTWARE_MAP.items():
        if keyword in path_lower and software not in found:
            found.append(software)
    if not found:
        # Check for common tools in the name
        for tool in ["blender", "nuke", "photoshop", "maya", "zbrush", "houdini", "substance",
                      "resolve", "unreal", "cascadeur", "motionbuilder", "cinema 4d", "lightroom"]:
            if tool in path_lower:
                found.append(tool.title())
                break
    return found or ["General"]


def detect_level(course_name: str) -> str:
    """Detect difficulty level from course name."""
    name_lower = course_name.lower()
    for level, keywords in LEVEL_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return level
    return "intermediate"  # Default


def detect_domain(course_name: str, folder_path: str) -> str:
    """Detect which WIAS domain a course belongs to."""
    path = folder_path.lower()
    name = course_name.lower()
    combined = path + " " + name
    if any(w in combined for w in ["animation", "film", "video", "cinematic", "vfx", "motion"]):
        return "action"
    if any(w in combined for w in ["sound", "audio", "music", "mixing"]):
        return "sound"
    if any(w in combined for w in ["web", "code", "python", "programming", "script"]):
        return "web"
    return "image"  # Default — most visual arts courses


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:80]


def parse_duration_from_name(course_name: str) -> Optional[float]:
    """Try to extract total course hours from name (e.g., '20+ hours')."""
    m = re.search(r'(\d+)\s*\+?\s*hours?', course_name, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r'(\d+)\s*\+?\s*days?', course_name, re.I)
    if m:
        return float(m.group(1)) * 3
    return None


# ── Database ───────────────────────────────────────────────────────────────

def get_db():
    import sqlite3
    conn = sqlite3.connect(str(CIS_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def course_exists(course_slug: str) -> bool:
    """Check if a course project already exists."""
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM projects WHERE id = ? OR name = ?",
        (course_slug, course_slug)
    ).fetchone()
    conn.close()
    return row is not None


def get_course(course_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (course_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def register_course(name: str, source_path: str, software: list, level: str,
                    domain: str, description: str = "") -> Optional[str]:
    """
    Register a course as a Project in CIS.
    Returns project ID or None.
    """
    import sqlite3
    pid = "course_" + slugify(name)
    if course_exists(pid):
        return pid

    now = _now()
    duration_hours = parse_duration_from_name(name)
    desc = description or f"Course covering {', '.join(software)} — {level} level — {domain} domain"

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO projects (id, name, owner, start_date, due_date, level,
                                  type, goal, domain, description, status,
                                  progress, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pid, name, "LMS", now, "", level,
            "course", "learning",
            domain, desc,
            "initiated", 0, now, now
        ))
        conn.commit()
        log(f"Registered course: {name} ({pid}) — {level}, {', '.join(software)}")
        return pid
    except Exception as e:
        log(f"Failed to register course {name}: {e}", "ERROR")
        return None
    finally:
        conn.close()


def register_lesson(course_id: str, name: str, source_path: str,
                    software: list, level: str, lesson_number: int = 1,
                    duration_minutes: Optional[float] = None) -> Optional[str]:
    """
    Register a lesson as an Asset linked to a course project.
    Returns asset ID or None.
    """
    now = _now()
    aid = "lesson_" + slugify(f"{course_id}_{name}")[:60]

    # Determine asset type from file extension
    ext = Path(source_path).suffix.lower()
    asset_type = "learning"
    if ext in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
        asset_type = "video"
    elif ext in (".pdf", ".doc", ".docx", ".txt"):
        asset_type = "reference"
    elif ext in (".zip", ".rar", ".7z"):
        asset_type = "resource"

    tags = list(set(software + [level, "lesson", f"lesson-{lesson_number}"]))

    notes = ""
    if duration_minutes:
        notes = f"Duration: {duration_minutes:.0f} min"

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO assets (id, name, type, path, project_id, category,
                                notes, tags, status, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            aid, name, asset_type, source_path, course_id,
            "lesson", notes, json.dumps(tags),
            "draft", now, now
        ))
        conn.commit()
        return aid
    except Exception as e:
        log(f"  Failed to register lesson {name}: {e}", "WARN")
        return None
    finally:
        conn.close()


def get_all_courses() -> list:
    """Get all registered courses (projects with type=course)."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM projects WHERE type = 'course' ORDER BY created DESC"
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        for field in ['linked_research', 'linked_references', 'linked_learning',
                      'linked_templates', 'linked_checklists', 'schedule_slots']:
            if field in d and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except:
                    pass
        # Count lessons
        conn2 = get_db()
        d['lesson_count'] = conn2.execute(
            "SELECT COUNT(*) FROM assets WHERE project_id = ?", (d['id'],)
        ).fetchone()[0]
        conn2.close()
        results.append(d)
    return results


def get_course_lessons(course_id: str) -> list:
    """Get all lessons (assets) for a course."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM assets WHERE project_id = ? ORDER BY created ASC",
        (course_id,)
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("tags"), str):
            try:
                d["tags"] = json.loads(d["tags"])
            except:
                d["tags"] = []
        results.append(d)
    return results


def get_dashboard_stats() -> dict:
    """LMS-specific dashboard stats."""
    conn = get_db()
    courses = conn.execute("SELECT COUNT(*) FROM projects WHERE type = 'course'").fetchone()[0]
    lessons = conn.execute(
        "SELECT COUNT(*) FROM assets WHERE project_id IN (SELECT id FROM projects WHERE type = 'course')"
    ).fetchone()[0]
    videos = conn.execute(
        "SELECT COUNT(*) FROM assets WHERE type = 'video'"
    ).fetchone()[0]
    conn.close()
    return {
        "courses": courses,
        "lessons": lessons,
        "videos": videos,
    }


# ── Tutorial Scanner ───────────────────────────────────────────────────────

def scan_tutorial_folders(dry_run: bool = False) -> list:
    """
    Walk TUTORIAL_ROOTS, discover course folders, register them.
    Returns list of discovered course records.
    """
    log("=" * 60)
    log("SCANNING tutorial folders")
    log("=" * 60)

    discovered = []

    for label, root_path in TUTORIAL_ROOTS.items():
        if not root_path.exists():
            log(f"  Skipping {label} — not found: {root_path}")
            continue

        log(f"  Scanning {label}: {root_path}")

        # Each immediate subdirectory is a potential course
        for entry in sorted(root_path.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("."):
                continue
            if entry.name in EXCLUDE_SUBDIRS:
                log(f"    Skipping (excluded): {entry.name}")
                continue
            if any(entry.name.startswith(p) for p in EXCLUDE_COURSE_PREFIXES):
                log(f"    Skipping (prefix excluded): {entry.name}")
                continue

            course_name = entry.name.strip()
            software = detect_software(str(entry), course_name)
            level = detect_level(course_name)
            domain = detect_domain(course_name, str(entry))

            log(f"    Found course: {course_name}")
            log(f"      Software: {', '.join(software)}")
            log(f"      Level: {level} | Domain: {domain}")

            if dry_run:
                discovered.append({
                    "name": course_name,
                    "path": str(entry),
                    "software": software,
                    "level": level,
                    "domain": domain,
                    "lessons": []
                })
                continue

            # Register the course
            course_id = register_course(
                name=course_name,
                source_path=str(entry),
                software=software,
                level=level,
                domain=domain
            )

            if not course_id:
                continue

            # Scan for lesson files inside the course folder
            lessons = []
            lesson_number = 0
            for lesson_file in sorted(entry.rglob("*")):
                if not lesson_file.is_file():
                    continue
                ext = lesson_file.suffix.lower()
                # Only process media and document files
                if ext not in (".mp4", ".mov", ".avi", ".mkv", ".webm",
                               ".pdf", ".txt", ".md", ".doc", ".docx",
                               ".zip", ".rar", ".7z", ".pptx", ".xlsx",
                               ".py", ".js", ".json", ".blend", ".uproject",
                               ".psd", ".tiff", ".png", ".jpg", ".jpeg",
                               ".exr", ".fbx", ".obj"):
                    continue
                # Skip system files
                if lesson_file.name.startswith(".") or lesson_file.name.startswith("~"):
                    continue

                lesson_number += 1
                lesson_name = lesson_file.stem[:80]
                
                # Estimate duration from file size for videos
                duration = None
                if ext in (".mp4", ".mov", ".mkv", ".webm"):
                    size_mb = lesson_file.stat().st_size / (1024 * 1024)
                    duration = max(5, size_mb / 10)  # rough: 10MB ≈ 1min

                lid = register_lesson(
                    course_id=course_id,
                    name=lesson_name,
                    source_path=str(lesson_file),
                    software=software,
                    level=level,
                    lesson_number=lesson_number,
                    duration_minutes=duration
                )

                if lid:
                    lessons.append({
                        "id": lid,
                        "name": lesson_name,
                        "path": str(lesson_file),
                        "ext": ext,
                        "duration": duration
                    })

            discovered.append({
                "name": course_name,
                "path": str(entry),
                "id": course_id,
                "software": software,
                "level": level,
                "domain": domain,
                "lessons": lessons
            })

            log(f"    → Registered {len(lessons)} lessons")

    log(f"\n  Total courses discovered: {len(discovered)}")
    total_lessons = sum(len(c["lessons"]) for c in discovered)
    log(f"  Total lessons registered: {total_lessons}")
    return discovered


# ── Vector Indexer (ChromaDB) ──────────────────────────────────────────────

def get_chroma_collection():
    """Get or create the ChromaDB collection for course content."""
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        collection = client.get_collection("course_content")
        log(f"ChromaDB collection 'course_content' exists ({collection.count()} documents)")
    except:
        collection = client.create_collection(
            name="course_content",
            metadata={"description": "CIS Learning Management — course and lesson content"}
        )
        log("Created ChromaDB collection 'course_content'")
    return collection


def get_embedding_model():
    """
    Get the embedding model for vectorizing content.
    Uses sentence-transformers for local embeddings.
    """
    from sentence_transformers import SentenceTransformer
    log("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim, fast, local
    log("Embedding model loaded (384-dim)")
    return model


def index_courses(force: bool = False) -> dict:
    """
    Index all course content into ChromaDB.
    Creates embeddings for each course (description) and each lesson.
    """
    log("=" * 60)
    log("INDEXING course content into ChromaDB")
    log("=" * 60)

    courses = get_all_courses()
    log(f"Found {len(courses)} registered courses")

    collection = get_chroma_collection()
    model = get_embedding_model()

    indexed = {"courses": 0, "lessons": 0, "chunks": 0}

    for course in courses:
        course_id = course["id"]

        # Check if already indexed
        existing = collection.get(ids=[f"course_{course_id}"])
        if existing["ids"] and not force:
            log(f"  Skipping {course['name']} — already indexed")
            indexed["courses"] += 1
            continue

        # Build course-level document
        course_text = f"Course: {course['name']}\nDescription: {course.get('description', '')}\n"
        course_text += f"Level: {course.get('level', '')}\nDomain: {course.get('domain', '')}\n"
        course_text += f"Software: {course.get('type', '')}"

        # Embed course description
        course_embedding = model.encode(course_text).tolist()
        collection.add(
            ids=[f"course_{course_id}"],
            embeddings=[course_embedding],
            metadatas=[{
                "type": "course",
                "course_id": course_id,
                "name": course["name"],
                "level": course.get("level", ""),
                "domain": course.get("domain", ""),
                "source": "lms"
            }],
            documents=[course_text]
        )
        indexed["courses"] += 1
        log(f"  Indexed course: {course['name']}")

        # Index each lesson
        lessons = get_course_lessons(course_id)
        for lesson in lessons:
            lesson_id = lesson["id"]

            existing_l = collection.get(ids=[f"lesson_{lesson_id}"])
            if existing_l["ids"] and not force:
                indexed["lessons"] += 1
                continue

            lesson_text = f"Course: {course['name']}\nLesson: {lesson['name']}\n"
            lesson_text += f"Type: {lesson.get('type', '')}\n"
            if lesson.get("notes"):
                lesson_text += f"Description: {lesson['notes']}\n"
            lesson_text += f"Path: {lesson.get('path', '')}"

            lesson_embedding = model.encode(lesson_text).tolist()
            collection.add(
                ids=[f"lesson_{lesson_id}"],
                embeddings=[lesson_embedding],
                metadatas=[{
                    "type": "lesson",
                    "course_id": course_id,
                    "lesson_id": lesson_id,
                    "name": lesson["name"],
                    "course_name": course["name"],
                    "asset_type": lesson.get("type", ""),
                    "path": lesson.get("path", ""),
                    "source": "lms"
                }],
                documents=[lesson_text]
            )
            indexed["lessons"] += 1

        if len(lessons) > 0:
            indexed["chunks"] += 1

    log(f"\n  Total indexed: {indexed['courses']} courses, {indexed['lessons']} lessons")
    return indexed


# ── Semantic Search ────────────────────────────────────────────────────────

def search_courses(query: str, limit: int = 10, level: str = None, domain: str = None) -> list:
    """
    Search across all indexed course content.
    Returns ranked results with relevance scores.
    """
    try:
        collection = get_chroma_collection()
        model = get_embedding_model()

        query_embedding = model.encode(query).tolist()

        where_filter = {}
        if level:
            where_filter["level"] = level
        if domain:
            where_filter["domain"] = domain

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter if where_filter else None
        )

        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "score": results["distances"][0][i] if results.get("distances") else None,
                "metadata": results["metadatas"][0][i],
                "text": results["documents"][0][i][:300] if results.get("documents") else ""
            })

        return formatted
    except Exception as e:
        log(f"Search failed: {e}", "ERROR")
        return []


# ── Training Suggestion Engine ────────────────────────────────────────────

def suggest_training(project_id: str = None, skill_needed: str = None, limit: int = 5) -> list:
    """
    Given a project or skill need, suggest relevant courses/lessons.
    Returns ranked suggestions that can be turned into calendar slots.
    """
    suggestions = []

    if skill_needed:
        # Direct skill search
        results = search_courses(skill_needed, limit=limit)
        for r in results:
            if r["metadata"]["type"] == "lesson":
                suggestions.append({
                    "type": "lesson",
                    "course": r["metadata"].get("course_name", ""),
                    "lesson": r["metadata"].get("name", ""),
                    "lesson_id": r["metadata"].get("lesson_id", ""),
                    "course_id": r["metadata"].get("course_id", ""),
                    "path": r["metadata"].get("path", ""),
                    "score": r["score"],
                    "reason": f"Matches your need: {skill_needed}"
                })

    if project_id:
        # Analyze project description for skill gaps
        conn = get_db()
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        conn.close()

        if project:
            project = dict(project)
            search_text = f"{project.get('name', '')} {project.get('description', '')} {project.get('goal', '')}"
            results = search_courses(search_text, limit=limit)

            for r in results:
                if r["metadata"]["type"] == "lesson":
                    suggestions.append({
                        "type": "lesson",
                        "course": r["metadata"].get("course_name", ""),
                        "lesson": r["metadata"].get("name", ""),
                        "lesson_id": r["metadata"].get("lesson_id", ""),
                        "course_id": r["metadata"].get("course_id", ""),
                        "path": r["metadata"].get("path", ""),
                        "score": r["score"],
                        "reason": f"Recommended for project: {project.get('name', '')}"
                    })

    # Deduplicate by lesson_id
    seen = set()
    unique = []
    for s in suggestions:
        if s["lesson_id"] not in seen:
            seen.add(s["lesson_id"])
            unique.append(s)

    return sorted(unique, key=lambda x: x["score"])[:limit]


# ── CLI Entry Point ────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CIS Learning Management System")
    parser.add_argument("--scan", action="store_true", help="Discover and register new courses")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scanned without registering")
    parser.add_argument("--index", action="store_true", help="Index all course content into ChromaDB")
    parser.add_argument("--reindex", action="store_true", help="Force reindex all content")
    parser.add_argument("--search", type=str, help="Search course content")
    parser.add_argument("--suggest", type=str, help="Suggest training for a project ID")
    parser.add_argument("--skill", type=str, help="Suggest training for a skill need")
    parser.add_argument("--catalog", action="store_true", help="List all registered courses")
    parser.add_argument("--limit", type=int, default=10, help="Max results")

    args = parser.parse_args()

    if args.scan:
        results = scan_tutorial_folders(dry_run=args.dry_run)
        print(f"\n📚 Discovered {len(results)} courses")
        for c in results:
            print(f"  [{c.get('id', 'DRY')}] {c['name']}")
            print(f"      {', '.join(c['software'])} · {c['level']} · {c['domain']}")
            print(f"      {len(c.get('lessons', []))} lessons")
            print()

    elif args.index or args.reindex:
        stats = index_courses(force=args.reindex)
        print(f"\n✅ Indexed: {stats['courses']} courses, {stats['lessons']} lessons")

    elif args.search:
        results = search_courses(args.search, limit=args.limit)
        print(f"\n🔍 Search: \"{args.search}\" — {len(results)} results\n")
        for r in results:
            meta = r["metadata"]
            score = f" (score: {r['score']:.3f})" if r["score"] else ""
            print(f"  [{meta['type']}] {meta.get('course_name', '')} / {meta.get('name', '')}{score}")
            print(f"      {r['text'][:200]}...")
            if meta.get("path"):
                print(f"      📁 {meta['path']}")
            print()

    elif args.suggest:
        suggestions = suggest_training(project_id=args.suggest, skill_needed=args.skill, limit=args.limit)
        print(f"\n🎯 Training Suggestions{' for project ' + args.suggest if args.suggest else ''}{' for skill: ' + args.skill if args.skill else ''}\n")
        for s in suggestions:
            print(f"  📖 {s['course']} → {s['lesson']}")
            print(f"     {s['reason']}")
            print(f"     📁 {s.get('path', '')}")
            print(f"     Score: {s['score']:.3f}")
            print()

    elif args.catalog:
        courses = get_all_courses()
        print(f"\n📚 Course Catalog ({len(courses)} courses)\n")
        for c in courses:
            print(f"  [{c['id']}] {c['name']}")
            print(f"      {c.get('level', '?')} · {c.get('domain', '?')} · {c.get('lesson_count', 0)} lessons")
            print(f"      {c.get('description', '')[:120]}...")
            print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
