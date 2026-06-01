import React, { useState, useEffect, useCallback, useRef } from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { api } from '../api'
import './SchedulePage.css'

const DOMAINS = ['personal', 'work', 'clients']
const PRIORITIES = ['low', 'medium', 'high', 'urgent']
const STATUSES = ['open', 'scheduled', 'in_progress', 'waiting', 'blocked', 'done']
const ITEM_TYPES = ['task', 'deadline', 'appointment', 'attention_item']

const DOMAIN_COLORS = { personal: '#7a8299', work: '#4a9eff', clients: '#3dffa0' }
const PRIORITY_COLORS = { low: '#7a8299', medium: '#ffb830', high: '#ff8c42', urgent: '#ff4a6a' }
const STATUS_COLORS = { open: '#7a8299', scheduled: '#ffb830', in_progress: '#4a9eff', waiting: '#ff8c42', blocked: '#ff4a6a', done: '#3dffa0' }
const STATUS_LABELS = { open: 'Noted', scheduled: 'Not Started', in_progress: 'Started', waiting: 'Waiting', blocked: 'Blocked', done: 'Done' }

const todayStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const statusNext = (s) => {
  const idx = STATUSES.indexOf(s)
  return STATUSES[idx >= 0 ? (idx + 1) % STATUSES.length : 0]
}

/* ---- Time dropdown helpers ---- */
const HOURS = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
const MINUTES = ['00', '15', '30', '45']

function timeToParts(timeStr) {
  if (!timeStr) return { hour: '', minute: '' }
  const [h, m] = timeStr.split(':')
  return { hour: h || '', minute: m || '' }
}

function partsToTime(hour, minute) {
  if (!hour && !minute) return ''
  return `${hour || '00'}:${minute || '00'}`
}

/* ---- TimeSelector component ---- */
function TimeSelector({ value, onChange, disabled }) {
  const { hour, minute } = timeToParts(value)
  return (
    <div className="time-selector">
      <select
        className="cis-select time-drop"
        value={hour}
        disabled={disabled}
        onChange={e => onChange(partsToTime(e.target.value, minute))}
      >
        <option value="">--</option>
        {HOURS.map(h => <option key={h} value={h}>{h}</option>)}
      </select>
      <span className="time-sep">:</span>
      <select
        className="cis-select time-drop"
        value={minute}
        disabled={disabled}
        onChange={e => onChange(partsToTime(hour, e.target.value))}
      >
        <option value="">--</option>
        {MINUTES.map(m => <option key={m} value={m}>{m}</option>)}
      </select>
    </div>
  )
}

/* ---- Calendar event mapper ---- */
function itemToEvent(item) {
  const color = DOMAIN_COLORS[item.domain] || '#7a8299'
  const date = item.display_date || item.scheduled_date || item.due_date || item.presented_date || todayStr()
  const isAllDay = item.all_day === 1 || (!item.all_day && !item.start_time)
  const start = isAllDay ? date : `${date}T${item.start_time}`
  const end = (!isAllDay && item.end_time) ? `${date}T${item.end_time}` : undefined
  return {
    id: item.id,
    title: item.title,
    start,
    end,
    allDay: isAllDay,
    backgroundColor: color,
    borderColor: color,
    textColor: '#fff',
    extendedProps: item,
  }
}

/* ---- Companion list row ---- */
function ItemRow({ item, onEdit }) {
  const dc = DOMAIN_COLORS[item.domain] || '#7a8299'
  const pc = PRIORITY_COLORS[item.priority] || '#7a8299'
  const sc = STATUS_COLORS[item.status] || '#7a8299'
  const sl = STATUS_LABELS[item.status] || item.status
  const isDone = item.status === 'done'
  const timeStr = item.all_day
    ? 'all day'
    : item.start_time
      ? `${item.start_time}${item.end_time ? ' \u2013 ' + item.end_time : ''}`
      : 'untimed'

  function cycleStatus(e) {
    e.stopPropagation()
    // Do inline optimistic update — just cycle and let parent handle
    onEdit({ ...item, status: statusNext(item.status) })
  }

  return (
    <div className={`sch-item${isDone ? ' sch-item-done' : ''}`} onClick={() => onEdit(item)}>
      <div className="sch-item-title">{item.title}</div>
      <div className="sch-item-meta">
        <span style={{
          background: `${dc}18`, color: dc, fontFamily: 'var(--mono)', fontSize: 8,
          padding: '1px 6px', borderRadius: 6, border: `1px solid ${dc}40`
        }}>{item.domain}</span>
        {item.item_type && (
          <span className="sch-item-type-tag">{item.item_type.replace('_', ' ')}</span>
        )}
        <span className="sch-item-dot" style={{ background: pc }} title={item.priority} />
        <span className="sch-item-time">{timeStr}</span>
        {item.client_name && <span className="sch-item-time">{item.client_name}</span>}
        <span
          className={`sch-status-badge${isDone ? ' sch-status-done' : ''}`}
          style={{ color: sc, borderColor: sc }}
          onClick={cycleStatus}
          title="Click to cycle: Noted → Not Started → Started → Waiting → Blocked → Done"
        >
          {isDone && <span className="sch-status-check">✓</span>}
          {sl}
          <span className="sch-status-chevron">▸</span>
        </span>
      </div>
    </div>
  )
}

function UpcomingList({ groups, onEdit }) {
  return Object.keys(groups).sort().map(date => (
    <React.Fragment key={date}>
      <div className="sch-group-header">{date}</div>
      {groups[date].map(item => <ItemRow key={item.id} item={item} onEdit={onEdit} />)}
    </React.Fragment>
  ))
}

/* ---- Edit Modal ---- */
function EditModal({ item: initial, onSave, onDelete, onClose }) {
  const [item, setItem] = useState({ ...initial })

  const upd = (field, value) => setItem(p => ({ ...p, [field]: value }))

  function toggleAllDay() {
    setItem(p => ({
      ...p,
      all_day: p.all_day ? 0 : 1,
      start_time: p.all_day ? p.start_time : null,
      end_time: p.all_day ? p.end_time : null,
    }))
  }

  function cycleStatus() {
    setItem(p => ({ ...p, status: statusNext(p.status) }))
  }

  const sc = STATUS_COLORS[item.status] || '#7a8299'
  const itype = item.item_type || 'task'
  const showDueDate = itype === 'task' || itype === 'deadline'
  const showScheduledDate = itype === 'task' || itype === 'deadline' || itype === 'appointment'
  const showTimes = itype === 'appointment'

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-hdr">
          <div className="modal-title">Edit Task</div>
          <button className="btn" onClick={onClose} style={{ padding: '4px 10px' }}>&times;</button>
        </div>
        <div className="modal-body">
          <div className="field-row">
            <label className="field-label">Title</label>
            <input className="cis-input" value={item.title || ''}
              onChange={e => upd('title', e.target.value)} />
          </div>

          {/* Item type */}
          <div className="det-row">
            <div className="det-field">
              <label>Type</label>
              <select className="cis-select" value={itype}
                onChange={e => upd('item_type', e.target.value)}>
                {ITEM_TYPES.map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
              </select>
            </div>
            <div className="det-field">
              <label>Domain</label>
              <select className="cis-select" value={item.domain || 'work'}
                onChange={e => upd('domain', e.target.value)}>
                {DOMAINS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="det-field">
              <label>Priority</label>
              <select className="cis-select" value={item.priority || 'medium'}
                onChange={e => upd('priority', e.target.value)}>
                {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>

          {/* Status */}
          <div className="field-row">
            <label className="field-label">Status</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <select
                className="cis-select"
                style={{ flex: 1, color: sc, borderColor: sc }}
                value={item.status || 'open'}
                onChange={e => upd('status', e.target.value)}
              >
                {STATUSES.map(s => (
                  <option key={s} value={s}>{STATUS_LABELS[s] || s}</option>
                ))}
              </select>
              <button
                className="btn"
                style={{ borderColor: sc, color: sc, textTransform: 'none', fontFamily: 'var(--mono)', fontSize: 10, whiteSpace: 'nowrap', cursor: 'pointer' }}
                onClick={cycleStatus}
                title="Click to cycle: Noted → Not Started → Started → Waiting → Blocked → Done"
              >
                {STATUS_LABELS[item.status] || item.status} ▸
              </button>
            </div>
          </div>

          {/* Completed at (shown when done) */}
          {item.status === 'done' && item.completed_at && (
            <div className="field-row" style={{ marginTop: -4 }}>
              <label className="field-label" style={{ color: '#3dffa0' }}>Completed</label>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#3dffa0', padding: '6px 0' }}>
                {item.completed_at}
              </span>
            </div>
          )}

          {/* Date fields */}
          <div className="det-row">
            <div className="det-field">
              <label>Presented</label>
              <input className="cis-input" type="date"
                value={item.presented_date || todayStr()}
                onChange={e => upd('presented_date', e.target.value)} />
            </div>
            {showDueDate && (
              <div className="det-field">
                <label style={itype === 'deadline' ? { color: '#ff4a6a' } : undefined}>Due{itype === 'deadline' ? ' *' : ''}</label>
                <input className="cis-input" type="date"
                  value={item.due_date || ''}
                  onChange={e => upd('due_date', e.target.value)} />
              </div>
            )}
            {showScheduledDate && (
              <div className="det-field">
                <label>Scheduled</label>
                <input className="cis-input" type="date"
                  value={item.scheduled_date || ''}
                  onChange={e => upd('scheduled_date', e.target.value)} />
              </div>
            )}
          </div>

          {/* Time fields (appointment only) */}
          {showTimes && (
            <div className="det-row" style={{ alignItems: 'flex-end' }}>
              <div className="det-field">
                <label>Start Time</label>
                <TimeSelector
                  value={item.start_time || ''}
                  disabled={item.all_day === 1}
                  onChange={v => upd('start_time', v || null)}
                />
              </div>
              <div className="det-field">
                <label>End Time</label>
                <TimeSelector
                  value={item.end_time || ''}
                  disabled={item.all_day === 1}
                  onChange={v => upd('end_time', v || null)}
                />
              </div>
              <div className="det-field" style={{ alignSelf: 'center', paddingTop: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={item.all_day === 1} onChange={toggleAllDay} />
                  All Day
                </label>
              </div>
            </div>
          )}

          {/* Client field */}
          {item.domain === 'clients' && (
            <div className="field-row">
              <label className="field-label">Client</label>
              <input className="cis-input" value={item.client_name || ''}
                onChange={e => upd('client_name', e.target.value)} />
            </div>
          )}

          {/* Outcome (edit only, not in add) */}
          <div className="field-row">
            <label className="field-label">Outcome / Result</label>
            <textarea className="cis-textarea" rows={2} value={item.outcome || ''}
              onChange={e => upd('outcome', e.target.value)}
              placeholder="What was the result?" />
          </div>

          <div className="field-row">
            <label className="field-label">Notes</label>
            <textarea className="cis-textarea" rows={3} value={item.notes || ''}
              onChange={e => upd('notes', e.target.value)} />
          </div>

          {(item.created_at) && (
            <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--t3)', marginTop: 8 }}>
              Created: {item.created_at}
              {item.started_at && `  |  Started: ${item.started_at}`}
              {item.completed_at && `  |  Done: ${item.completed_at}`}
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn-red" onClick={onDelete}>Delete</button>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn" onClick={onClose}>Cancel</button>
            <button className="btn btn-green" onClick={() => onSave(item)}>Save</button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ---- Main Page ---- */
export default function SchedulePage() {
  const [items, setItems] = useState([])
  const [domainFilter, setDomainFilter] = useState('all')
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [listTab, setListTab] = useState('today')
  const calRef = useRef(null)

  const [form, setForm] = useState({
    title: '', domain: 'work', item_type: 'task',
    presented_date: todayStr(), due_date: '', scheduled_date: '',
    start_time: '', end_time: '', all_day: false,
    priority: 'medium', client_name: '', notes: ''
  })

  const load = useCallback(async () => {
    try {
      const params = {}
      if (domainFilter !== 'all') params.domain = domainFilter
      const res = await api.schedule(params)
      setItems(res.items || [])
    } catch (e) { console.error('schedule load', e) }
  }, [domainFilter])

  useEffect(() => { load() }, [load])

  const filtered = domainFilter === 'all' ? items : items.filter(i => i.domain === domainFilter)
  const events = filtered.map(itemToEvent)

  /* ---- Quick create ---- */
  async function handleCreate(e) {
    e.preventDefault()
    if (!form.title.trim()) return

    const isDeadline = form.item_type === 'deadline'
    if (isDeadline && !form.due_date) {
      alert('Due date is required for deadlines.')
      return
    }

    try {
      const payload = {
        title: form.title,
        domain: form.domain,
        item_type: form.item_type,
        presented_date: form.presented_date,
        priority: form.priority,
        notes: form.notes || '',
        status: 'open',
      }

      // Conditional fields per item_type
      if (form.item_type === 'task') {
        payload.due_date = form.due_date || null
        payload.scheduled_date = form.scheduled_date || null
      } else if (form.item_type === 'deadline') {
        payload.due_date = form.due_date || null
        payload.scheduled_date = form.scheduled_date || null
      } else if (form.item_type === 'appointment') {
        payload.scheduled_date = form.scheduled_date || null
        payload.start_time = form.all_day ? null : (form.start_time || null)
        payload.end_time = form.all_day ? null : (form.end_time || null)
        payload.all_day = form.all_day ? 1 : 0
      }
      // attention_item: only presented_date (already set)

      if (form.domain === 'clients') {
        payload.client_name = form.client_name || null
      }

      await api.createScheduleItem(payload)
      setForm({
        title: '', domain: 'work', item_type: 'task',
        presented_date: todayStr(), due_date: '', scheduled_date: '',
        start_time: '', end_time: '', all_day: false,
        priority: 'medium', client_name: '', notes: ''
      })
      setShowForm(false)
      load()
    } catch (e) { console.error('create', e) }
  }

  /* ---- Edit save ---- */
  async function handleSave(savedItem) {
    try {
      const payload = {
        title: savedItem.title,
        domain: savedItem.domain,
        item_type: savedItem.item_type,
        presented_date: savedItem.presented_date,
        priority: savedItem.priority,
        status: savedItem.status,
        notes: savedItem.notes || '',
        outcome: savedItem.outcome || '',
      }

      const itype = savedItem.item_type || 'task'

      if (itype === 'task') {
        payload.due_date = savedItem.due_date || null
        payload.scheduled_date = savedItem.scheduled_date || null
      } else if (itype === 'deadline') {
        payload.due_date = savedItem.due_date || null
        payload.scheduled_date = savedItem.scheduled_date || null
      } else if (itype === 'appointment') {
        payload.scheduled_date = savedItem.scheduled_date || null
        payload.start_time = savedItem.all_day ? null : (savedItem.start_time || null)
        payload.end_time = savedItem.all_day ? null : (savedItem.end_time || null)
        payload.all_day = savedItem.all_day ? 1 : 0
      }
      // attention_item: only presented_date

      if (savedItem.domain === 'clients') {
        payload.client_name = savedItem.client_name || null
      } else {
        payload.client_name = null
      }

      await api.updateScheduleItem(savedItem.id, payload)
      setEditing(null)
      load()
    } catch (e) { console.error('save', e) }
  }

  /* ---- Delete ---- */
  async function handleDelete() {
    if (!editing || !window.confirm('Delete this task?')) return
    try {
      await api.deleteScheduleItem(editing.id)
      setEditing(null)
      load()
    } catch (e) { console.error('delete', e) }
  }

  /* ---- Drag-drop reschedule ---- */
  async function handleEventDrop(info) {
    const item = info.event.extendedProps
    const newDate = info.event.startStr.slice(0, 10)
    const oldDate = item.display_date || item.scheduled_date || item.due_date || item.presented_date
    if (newDate === oldDate) return
    try {
      await api.updateScheduleItem(item.id, { scheduled_date: newDate })
      load()
    } catch (e) {
      info.revert()
      console.error('drop', e)
    }
  }

  /* ---- Companion lists ---- */
  const today = todayStr()

  // Today: items where display_date = today, sorted overdue-first
  const todayItems = filtered
    .filter(i => {
      const dd = i.display_date
      return dd === today && i.status !== 'done'
    })
    .sort((a, b) => {
      const aOverdue = a.due_date && a.due_date < today
      const bOverdue = b.due_date && b.due_date < today
      if (aOverdue !== bOverdue) return aOverdue ? -1 : 1
      const aTime = a.start_time || ''
      const bTime = b.start_time || ''
      if (!!aTime !== !!bTime) return aTime ? -1 : 1
      return aTime.localeCompare(bTime)
    })

  // Overdue: display_date < today AND status != done
  const overdueItems = filtered
    .filter(i => {
      const dd = i.display_date
      return dd && dd < today && i.status !== 'done'
    })
    .sort((a, b) => {
      const ad = a.display_date
      const bd = b.display_date
      return (ad + (a.start_time || '')).localeCompare(bd + (b.start_time || ''))
    })

  // Upcoming: display_date > today AND status != done
  const upcomingItems = filtered
    .filter(i => {
      const dd = i.display_date
      return dd && dd > today && i.status !== 'done'
    })
    .sort((a, b) => {
      const ad = a.display_date
      const bd = b.display_date
      return (ad + (a.start_time || '')).localeCompare(bd + (b.start_time || ''))
    })

  // Completed: status = done, most recent first
  const completedItems = filtered
    .filter(i => i.status === 'done')
    .sort((a, b) => (b.completed_at || b.updated_at || '').localeCompare(a.completed_at || a.updated_at || ''))

  const upcomingGroups = {}
  for (const i of upcomingItems) {
    const dd = i.display_date
    if (!upcomingGroups[dd]) upcomingGroups[dd] = []
    upcomingGroups[dd].push(i)
  }

  /* ---- Render ---- */
  return (
    <div className="page-content">
      <div className="hdr">
        <div className="hdr-title">Schedule</div>
        <div className="hdr-sub">Calendar-first task scheduling with companion lists</div>
      </div>

      {/* Toolbar: domain filters + add button */}
      <div className="card sch-toolbar">
        <div className="sch-filters">
          {['all', 'personal', 'work', 'clients'].map(d => (
            <button key={d} className={`btn ${domainFilter === d ? 'btn-blue' : ''}`}
              onClick={() => setDomainFilter(d)}>
              {d.charAt(0).toUpperCase() + d.slice(1)}
            </button>
          ))}
        </div>
        <div style={{ flex: 1 }} />
        <button className="btn btn-blue" onClick={() => {
          setForm(f => ({ ...f, presented_date: todayStr() }))
          setShowForm(!showForm)
        }}>
          + Add Task
        </button>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--t3)', marginLeft: 12 }}>
          {filtered.length} items
        </span>
      </div>

      {/* Quick-entry form */}
      {showForm && (
        <div className="card">
          <div className="card-title">New Task</div>
          <form onSubmit={handleCreate}>
            <div className="row">
              <div className="col">
                <div className="field-row">
                  <label className="field-label">Title *</label>
                  <input className="cis-input" required value={form.title}
                    onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                    placeholder="What needs to be done?" />
                </div>
              </div>
              <div className="col" style={{ minWidth: 140 }}>
                <div className="field-row">
                  <label className="field-label">Domain</label>
                  <select className="cis-select" value={form.domain}
                    onChange={e => setForm(f => ({ ...f, domain: e.target.value }))}>
                    {DOMAINS.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
              </div>
              <div className="col" style={{ minWidth: 140 }}>
                <div className="field-row">
                  <label className="field-label">Type</label>
                  <select className="cis-select" value={form.item_type}
                    onChange={e => setForm(f => ({ ...f, item_type: e.target.value }))}>
                    {ITEM_TYPES.map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                  </select>
                </div>
              </div>
            </div>

            {/* Date row */}
            <div className="row">
              <div className="col" style={{ minWidth: 140 }}>
                <div className="field-row">
                  <label className="field-label">Presented</label>
                  <input className="cis-input" type="date" value={form.presented_date}
                    onChange={e => setForm(f => ({ ...f, presented_date: e.target.value }))} />
                </div>
              </div>
              {(form.item_type === 'task' || form.item_type === 'deadline') && (
                <div className="col" style={{ minWidth: 140 }}>
                  <div className="field-row">
                    <label className="field-label" style={form.item_type === 'deadline' ? { color: '#ff4a6a' } : undefined}>
                      Due{form.item_type === 'deadline' ? ' *' : ''}
                    </label>
                    <input className="cis-input" type="date" value={form.due_date}
                      onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} />
                  </div>
                </div>
              )}
              {(form.item_type === 'task' || form.item_type === 'deadline' || form.item_type === 'appointment') && (
                <div className="col" style={{ minWidth: 140 }}>
                  <div className="field-row">
                    <label className="field-label">Scheduled</label>
                    <input className="cis-input" type="date" value={form.scheduled_date}
                      onChange={e => setForm(f => ({ ...f, scheduled_date: e.target.value }))} />
                  </div>
                </div>
              )}
            </div>

            {/* Time row (appointment only) */}
            {form.item_type === 'appointment' && (
              <div className="row" style={{ alignItems: 'flex-end' }}>
                <div className="col" style={{ minWidth: 130 }}>
                  <div className="field-row">
                    <label className="field-label">Start Time</label>
                    <TimeSelector
                      value={form.start_time}
                      disabled={form.all_day}
                      onChange={v => setForm(f => ({ ...f, start_time: v }))}
                    />
                  </div>
                </div>
                <div className="col" style={{ minWidth: 130 }}>
                  <div className="field-row">
                    <label className="field-label">End Time</label>
                    <TimeSelector
                      value={form.end_time}
                      disabled={form.all_day}
                      onChange={v => setForm(f => ({ ...f, end_time: v }))}
                    />
                  </div>
                </div>
                <div className="col" style={{ minWidth: 100, display: 'flex', alignItems: 'center', paddingBottom: 8 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontFamily: 'var(--cond)', fontSize: 10, fontWeight: 600, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--t3)' }}>
                    <input type="checkbox" checked={form.all_day}
                      onChange={e => setForm(f => ({ ...f, all_day: e.target.checked }))} />
                    All Day
                  </label>
                </div>
              </div>
            )}

            {/* Priority row */}
            <div className="row">
              <div className="col" style={{ minWidth: 140 }}>
                <div className="field-row">
                  <label className="field-label">Priority</label>
                  <select className="cis-select" value={form.priority}
                    onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}>
                    {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
              </div>
            </div>

            {form.domain === 'clients' && (
              <div className="row">
                <div className="col" style={{ minWidth: 200 }}>
                  <div className="field-row">
                    <label className="field-label">Client</label>
                    <input className="cis-input" value={form.client_name}
                      onChange={e => setForm(f => ({ ...f, client_name: e.target.value }))}
                      placeholder="Client name" />
                  </div>
                </div>
              </div>
            )}

            <div className="field-row">
              <label className="field-label">Notes</label>
              <textarea className="cis-textarea" rows={2} value={form.notes}
                onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                placeholder="Optional notes..." />
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-blue" type="submit">+ Add</button>
              <button className="btn" type="button" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Main layout: Calendar + Companion sidebar */}
      <div className="sch-layout">
        <div className="sch-calendar">
          <FullCalendar
            ref={calRef}
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,timeGridWeek,timeGridDay'
            }}
            events={events}
            editable={true}
            eventClick={info => setEditing(info.event.extendedProps)}
            eventDrop={handleEventDrop}
            height="auto"
            firstDay={1}
          />
        </div>

        <div className="sch-sidebar">
          <div className="sch-tabs">
            {[
              { key: 'today', label: 'Today', count: todayItems.length },
              { key: 'overdue', label: 'Overdue', count: overdueItems.length },
              { key: 'upcoming', label: 'Upcoming', count: upcomingItems.length },
              { key: 'completed', label: 'Done', count: completedItems.length },
            ].map(t => (
              <button key={t.key}
                className={`sch-tab ${listTab === t.key ? 'active' : ''}`}
                onClick={() => setListTab(t.key)}>
                {t.label} <span className="sch-tab-count">{t.count}</span>
              </button>
            ))}
          </div>
          <div className="sch-list">
            {listTab === 'today' && todayItems.map(i => <ItemRow key={i.id} item={i} onEdit={setEditing} />)}
            {listTab === 'overdue' && overdueItems.map(i => <ItemRow key={i.id} item={i} onEdit={setEditing} />)}
            {listTab === 'upcoming' && <UpcomingList groups={upcomingGroups} onEdit={setEditing} />}
            {listTab === 'completed' && completedItems.map(i => <ItemRow key={i.id} item={i} onEdit={setEditing} />)}

            {listTab === 'today' && todayItems.length === 0 && <div className="empty-state">No tasks today</div>}
            {listTab === 'overdue' && overdueItems.length === 0 && <div className="empty-state">Nothing overdue</div>}
            {listTab === 'upcoming' && upcomingItems.length === 0 && <div className="empty-state">Nothing upcoming</div>}
            {listTab === 'completed' && completedItems.length === 0 && <div className="empty-state">Nothing completed</div>}
          </div>
        </div>
      </div>

      {/* Edit modal */}
      {editing && (
        <EditModal
          item={editing}
          onSave={handleSave}
          onDelete={handleDelete}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  )
}
