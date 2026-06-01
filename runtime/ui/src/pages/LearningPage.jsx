import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

const LEVEL_COLORS = {
  beginner: '#3dffa0',
  intermediate: '#ffb830',
  professional: '#ff4a6a'
}

const DOMAIN_ICONS = {
  image: '🖼️',
  action: '🎬',
  sound: '🎵',
  web: '🌐'
}

export default function LearningPage() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [searching, setSearching] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [courseLessons, setCourseLessons] = useState(null)
  const [lmsStats, setLmsStats] = useState({})
  const [filter, setFilter] = useState('all')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    loadCourses()
    api.lmsDashboard().then(setLmsStats).catch(() => {})
  }, [])

  async function loadCourses() {
    setLoading(true)
    try {
      const data = await api.lmsCourses()
      setCourses(data.courses || [])
    } catch (e) {
      setMsg('Failed to load courses: ' + e.message)
    }
    setLoading(false)
  }

  async function selectCourse(courseId) {
    setSelectedCourse(courseId)
    setCourseLessons(null)
    try {
      const data = await api.lmsCourse(courseId)
      setCourseLessons(data)
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) {
      setSearchResults(null)
      return
    }
    setSearching(true)
    try {
      const data = await api.lmsSearch({ query: searchQuery, limit: 15 })
      setSearchResults(data.results || [])
    } catch (e) {
      setMsg('Search error: ' + e.message)
    }
    setSearching(false)
  }

  async function handleScan() {
    try {
      const data = await api.lmsScan()
      setMsg(`Scan found ${data.courses || 0} courses`)
      setTimeout(() => setMsg(''), 3000)
      loadCourses()
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
  }

  async function handleIndex() {
    try {
      setMsg('Indexing course content into ChromaDB...')
      const data = await api.lmsIndex()
      const stats = data.indexed || {}
      setMsg(`✅ Indexed: ${stats.courses || 0} courses, ${stats.lessons || 0} lessons`)
      setTimeout(() => setMsg(''), 4000)
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
  }

  async function suggestStudy(courseId) {
    if (!courseId) return
    setMsg('Generating study suggestions...')
    try {
      const data = await api.lmsSchedule({ project_id: courseId, limit: 5 })
      const slots = data.slots || []
      // Create each suggested slot in the schedule
      let created = 0
      for (const slot of slots) {
        try {
          await api.createSlot({
            name: slot.title.slice(0, 80),
            duration: slot.duration,
            category: 'learning',
            project_id: slot.project_id,
            notes: slot.notes,
            status: 'planned'
          })
          created++
        } catch (e) {
          // Skip duplicates
        }
      }
      setMsg(`✅ ${created} study slots added to your schedule!`)
      setTimeout(() => setMsg(''), 5000)
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
  }

  const filtered = filter === 'all'
    ? courses
    : courses.filter(c => c.domain === filter || c.level === filter)

  // Count software categories
  const softwareCounts = {}
  courses.forEach(c => {
    const sw = c.description?.split('—')[0]?.replace('Course covering ', '')?.trim() || 'General'
    softwareCounts[sw] = (softwareCounts[sw] || 0) + 1
  })

  return (
    <div className="page-content">
      {/* Header */}
      <div className="hdr">
        <div className="hdr-title">🎓 Learning Hub</div>
        <div className="hdr-sub">
          {lmsStats.courses || courses.length} courses · {lmsStats.lessons || '?'} lessons · {lmsStats.videos || '?'} videos
        </div>
      </div>

      {/* Controls bar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <input className="cis-input"
          style={{ flex: 1, minWidth: 200, fontSize: 11 }}
          placeholder="🔍 Search courses and lessons..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        <button className="btn btn-blue" onClick={handleSearch} disabled={searching}
          style={{ fontSize: 10 }}>
          {searching ? 'Searching...' : 'Search'}
        </button>
        <button className="btn" onClick={handleScan} style={{ fontSize: 10 }}>📡 Scan</button>
        <button className="btn" onClick={handleIndex} style={{ fontSize: 10 }}>🧠 Index</button>
        <button className="btn" onClick={loadCourses} style={{ fontSize: 10 }}>↻ Refresh</button>
        {msg && <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 10, color: '#3dffa0' }}>{msg}</span>}
      </div>

      {/* Filter pills */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        <span style={{ color: '#7a8299', fontSize: 10 }}>Filter:</span>
        {['all', 'beginner', 'intermediate', 'professional', 'image', 'action'].map(f => (
          <button key={f}
            className={`btn ${filter === f ? 'btn-blue' : ''}`}
            onClick={() => { setFilter(f); setSearchResults(null) }}
            style={{ fontSize: 9, padding: '3px 10px' }}>
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Search results vs Course list */}
      {searchResults !== null ? (
        <div>
          <div style={{ color: '#7a8299', fontSize: 10, marginBottom: 8 }}>
            Search results: {searchResults.length} items
            <button className="btn" onClick={() => setSearchResults(null)} style={{ fontSize: 9, marginLeft: 8 }}>✕ Clear</button>
          </div>
          <div className="row" style={{ gap: 12 }}>
            {searchResults.map(r => (
              <div key={r.id} className="card" style={{ padding: 12, flex: '0 1 calc(50% - 6px)' }}>
                <div style={{ fontSize: 10, color: '#4a9eff', marginBottom: 4 }}>
                  {r.metadata?.type === 'course' ? '📚 Course' : '📖 Lesson'}
                </div>
                <strong style={{ fontSize: 11 }}>{r.metadata?.course_name || r.metadata?.name}</strong>
                {r.metadata?.type === 'lesson' && (
                  <div style={{ fontSize: 9, color: '#7a8299' }}>from: {r.metadata?.course_name}</div>
                )}
                <div style={{ fontSize: 9, color: '#5a6279', marginTop: 4, fontFamily: '"Share Tech Mono", monospace' }}>
                  Score: {(r.score || 0).toFixed(3)}
                </div>
                <div style={{ fontSize: 9, color: '#5a6279', fontFamily: '"Share Tech Mono", monospace' }}>
                  {r.metadata?.level} · {r.metadata?.domain}
                </div>
                {r.metadata?.type === 'course' && r.metadata?.course_id && (
                  <button className="btn" style={{ fontSize: 9, marginTop: 6 }}
                    onClick={() => selectCourse(r.metadata.course_id)}>
                    View Lessons →
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="row" style={{ gap: 16 }}>
          {/* Course list */}
          <div className="col" style={{ flex: 1 }}>
            {loading ? (
              <div className="empty-state">Loading courses...</div>
            ) : filtered.length === 0 ? (
              <div className="empty-state">No courses match this filter</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {filtered.map(c => {
                  const levelColor = LEVEL_COLORS[c.level] || '#7a8299'
                  const sw = c.description?.split('—')[0]?.replace('Course covering ', '')?.trim() || '?'
                  return (
                    <div key={c.id}
                      className={`card ${selectedCourse === c.id ? 'card-selected' : ''}`}
                      onClick={() => selectCourse(c.id)}
                      style={{
                        cursor: 'pointer', padding: 12,
                        border: selectedCourse === c.id ? '1px solid #4a9eff' : '1px solid #1e2338'
                      }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong style={{ fontSize: 12 }}>{DOMAIN_ICONS[c.domain] || '📚'} {c.name}</strong>
                        <span className="proj-status" style={{
                          fontSize: 9, padding: '2px 8px',
                          borderColor: levelColor, color: levelColor
                        }}>{c.level}</span>
                      </div>
                      <div style={{ display: 'flex', gap: 8, marginTop: 4, alignItems: 'center' }}>
                        <span className="tag" style={{ fontSize: 9 }}>{sw}</span>
                        <span className="tag" style={{ fontSize: 9 }}>{c.domain}</span>
                        <span className="tag" style={{ fontSize: 9 }}>{c.lesson_count || 0} lessons</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Lesson detail panel */}
          <div className="col" style={{ flex: 2 }}>
            {courseLessons ? (
              <div className="card">
                <div className="card-title">{courseLessons.course?.name || 'Course'}</div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
                  <button className="btn btn-blue" style={{ fontSize: 9, padding: '4px 10px' }}
                    onClick={() => suggestStudy(courseLessons.course?.id)}>
                    📅 Schedule Study
                  </button>
                  <span style={{ fontSize: 10, color: '#7a8299' }}>
                    {courseLessons.course?.level} · {courseLessons.course?.domain} · {courseLessons.lesson_count || 0} lessons
                  </span>
                </div>
                <div style={{ fontSize: 10, color: '#b0b8d0', marginBottom: 12 }}>
                  {(courseLessons.course?.description || '')}
                </div>

                <div style={{ fontSize: 11, color: '#4a9eff', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
                  Lessons
                </div>
                <div style={{ maxHeight: '50vh', overflowY: 'auto' }}>
                  {(courseLessons.lessons || []).map((lesson, i) => (
                    <div key={lesson.id}
                      style={{
                        padding: '8px 0',
                        borderBottom: '1px solid #1e2338',
                        fontSize: 11
                      }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{i + 1}. {lesson.name}</span>
                        <span className="tag" style={{ fontSize: 9 }}>{lesson.type || '?'}</span>
                      </div>
                      <div style={{ fontSize: 9, color: '#5a6279', fontFamily: '"Share Tech Mono", monospace', marginTop: 2 }}>
                        {lesson.path ? lesson.path.split('/').slice(-3).join('/') : 'No path'}
                        {lesson.notes && ` · ${lesson.notes}`}
                      </div>
                    </div>
                  ))}
                  {(!courseLessons.lessons || courseLessons.lessons.length === 0) && (
                    <div style={{ color: '#5a6279', fontSize: 10, padding: 12 }}>
                      No lessons registered yet — run a scan to discover lesson files
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="empty-state" style={{
                padding: 40, textAlign: 'center', color: '#5a6279',
                border: '1px dashed #1e2338', borderRadius: 8
              }}>
                <div style={{ fontSize: 24, marginBottom: 8 }}>🎓</div>
                Select a course to view its lessons
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
