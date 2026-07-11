import { useEffect, useState } from 'react'

const STATUS_COLORS = {
  active: 'var(--green, #4caf50)',
  waiting: 'var(--t3)',
  idle: 'var(--t3)',
  in_progress: 'var(--accent, #00bcd4)',
}

const ROUND_TYPES = ['design decision','technical implementation','verification','research','wording / prompt','architecture']

function AdvisorWizard({ onClose }) {
  const [page, setPage] = useState(1)
  const [roundId, setRoundId] = useState(null)
  const [form, setForm] = useState({
    topic: '', round_type: '', eric_context: '', current_concern: '', desired_outcome: '',
    claude_input: '', chatgpt_input: ''
  })
  const [advisorPrompt, setAdvisorPrompt] = useState('')
  const [saving, setSaving] = useState(false)
  const [captureResult, setCaptureResult] = useState(null)
  const [copyFallback, setCopyFallback] = useState(false)
  const [error, setError] = useState('')
  const [importResult, setImportResult] = useState(null)
  const [ericAddendum, setEricAddendum] = useState('')
  const [followupPrompt, setFollowupPrompt] = useState('')
  const [confirmClose, setConfirmClose] = useState(false)
  const [capturedPass, setCapturedPass] = useState(0)
  const [directiveForm, setDirectiveForm] = useState({
    decision_made: '', accepted_basis: '', final_directive: '',
    scope: '', do_not_do: '', success_criteria: '',
    evidence_required: '', owner_executor: 'Hermes', next_action: '', status: 'draft'
  })
  const [directiveResult, setDirectiveResult] = useState(null)

  // Three explicit states for close protection:
  //   draft_dirty     = any text field has content AND capturedPass === 0 (or text changed since last capture)
  //   saved_captured  = capture succeeded, fields cleared, capturedPass > 0
  //   continuing_new_pass = user clicked Continue This Topic after a capture; fields reset, waiting for new input
  const isDirty = () => {
    // Only dirty if there's text AND it hasn't been captured yet (or new text since capture)
    const hasText = !!(form.topic || form.round_type || form.eric_context ||
                       form.current_concern || form.desired_outcome ||
                       form.claude_input || form.chatgpt_input ||
                       ericAddendum)
    // Context fields (topic, type, context, concern, outcome) are shared across passes.
    // Response fields (claude_input, chatgpt_input, ericAddendum) are per-pass.
    // Dirty if response fields have content (fresh input for a new pass).
    const hasResponseText = !!(form.claude_input || form.chatgpt_input || ericAddendum)
    return hasText && hasResponseText
  }

  const handleClose = () => {
    if (isDirty()) {
      setConfirmClose(true)
    } else {
      onClose()
    }
  }

  const discardAndClose = () => {
    setConfirmClose(false)
    onClose()
  }

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const inputStyle = {
    width: '100%', background: 'var(--bg2, #12131a)', border: '1px solid var(--border, #2a2d3a)',
    borderRadius: 4, color: 'var(--t1)', padding: '6px 8px', fontSize: 11,
    fontFamily: 'inherit', boxSizing: 'border-box', resize: 'vertical'
  }
  const labelStyle = { fontSize: 10, color: 'var(--t3)', display: 'block', marginBottom: 3 }

  const generateAdvisorPrompt = () => {
    const p = `I need your input on the following:

Topic: ${form.topic}
Type: ${form.round_type}

Context: ${form.eric_context}
Current Concern: ${form.current_concern}
Desired Outcome: ${form.desired_outcome}

Please give me your technical recommendation, any cautions, and your main position.`
    setAdvisorPrompt(p)
    setPage(3)
  }

  const saveContext = async () => {
    const res = await fetch('/api/collab/rounds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    const data = await res.json()
    setRoundId(data.id)
    generateAdvisorPrompt()
  }

  const saveInputs = async () => {
    if (!roundId) return
    await fetch(`/api/collab/rounds/${roundId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ claude_input: form.claude_input, chatgpt_input: form.chatgpt_input })
    })
    setPage(5)
  }

  const captureExchange = async () => {
    setSaving(true); setError('')
    try {
      const res = await fetch(`/api/collab/rounds/${roundId}/capture-exchange`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          claude_response: form.claude_input,
          chatgpt_response: form.chatgpt_input
        })
      })
      const data = await res.json()
      if (data.ok) {
        setCaptureResult(data)
        setCapturedPass(data.pass_number)
        // Clear per-pass response fields so isDirty() returns false
        setForm(f => ({ ...f, claude_input: '', chatgpt_input: '' }))
        setEricAddendum('')
        setPage(5)
      } else {
        setError(data.error || 'Capture failed')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const generateFollowup = async () => {
    const res = await fetch(`/api/collab/rounds/${roundId}/followup-prompt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ eric_addendum: ericAddendum })
    })
    const data = await res.json()
    if (data.ok) {
      setFollowupPrompt(data.prompt)
      setPage(6)
    }
  }

  const continueTopic = () => {
    // Start a new pass: clear per-pass fields, reset capture result, go to response entry
    setCaptureResult(null)
    setEricAddendum('')
    setFollowupPrompt('')
    setPage(4)
  }

  const openDirectivePage = () => {
    setDirectiveResult(null)
    setPage(7)
  }

  const saveDirective = async () => {
    setSaving(true); setError('')
    try {
      // Auto-fill decision_made from first line of final_directive if empty
      const body = { ...directiveForm }
      if (!body.decision_made && directiveForm.final_directive) {
        const firstLine = directiveForm.final_directive.split('\n')[0].trim()
        body.decision_made = firstLine ? firstLine.slice(0, 200) : 'Directive captured'
      }
      const res = await fetch(`/api/collab/rounds/${roundId}/final-directive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      const data = await res.json()
      if (data.ok) {
        setDirectiveResult(data)
      } else {
        setError(data.error || 'Directive save failed')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const setD = (k, v) => setDirectiveForm(f => ({ ...f, [k]: v }))

  const BASIS_OPTIONS = ['Claude','ChatGPT','Combined','Eric Override','Other']
  const STATUS_OPTIONS = ['draft','approved','executing','complete','verified']

  const copyPacket = async () => {
    try { await navigator.clipboard.writeText(advisorPrompt) } catch {}
    setCopyFallback(false)
  }

  const copyDirective = async () => {
    if (directiveResult && directiveResult.directive_id) {
      // Post-save: copy the full Hermes-ready instruction block
      const block = `DIRECTIVE ID: ${directiveResult.directive_id}
TASK: ${directiveForm.final_directive}
SUCCESS CRITERIA: ${directiveForm.success_criteria || '(none)'}
DO NOT DO: ${directiveForm.do_not_do || '(none)'}
EVIDENCE REQUIRED: ${directiveForm.evidence_required || '(none)'}
REPORT CALLBACK: POST http://127.0.0.1:5000/api/collab/directives/${directiveResult.directive_id}/report
REPORT SCHEMA: { "report": "<your execution summary>", "status": "EXECUTED" }

When your task is complete, POST your execution report to the callback above before responding in the terminal.`
      try { await navigator.clipboard.writeText(block) } catch {}
    } else {
      // Pre-save: copy raw directive text
      try { await navigator.clipboard.writeText(directiveForm.final_directive) } catch {}
    }
  }

  const btnDef = { padding: '6px 14px', fontSize: 11, borderRadius: 4, cursor: 'pointer', border: 'none' }

  return (
    <>
      <div style={{
        position: 'fixed', right: 0, top: 0, width: 440,
        height: '100vh', background: 'var(--bg1, #0e0f16)',
        borderLeft: '1px solid var(--border, #2a2d3a)',
        display: 'flex', flexDirection: 'column',
        padding: 16, boxSizing: 'border-box', overflowY: 'auto',
        zIndex: 1001
      }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--t1)' }}>🧭 Advisor Round</div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span style={{ fontSize: 10, color: 'var(--t3)' }}>Step {page}/7</span>
          <button onClick={handleClose} style={{ ...btnDef, background: 'transparent', color: 'var(--t3)', padding: '2px 6px' }}>✕</button>
        </div>
      </div>

      {page === 1 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 11, color: 'var(--t2)', marginBottom: 4 }}>Open a new collaboration round.</div>
          <div>
            <label style={labelStyle}>Topic</label>
            <input value={form.topic} onChange={e => set('topic', e.target.value)} style={{ ...inputStyle, resize: 'none' }} placeholder="Short name for this issue" />
          </div>
          <div>
            <label style={labelStyle}>Type</label>
            <select value={form.round_type} onChange={e => set('round_type', e.target.value)} style={inputStyle}>
              <option value="">Select type...</option>
              {ROUND_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <button onClick={() => setPage(2)} disabled={!form.topic}
            style={{ ...btnDef, background: 'var(--accent, #00bcd4)', color: '#000', marginTop: 8 }}>
            Start Round →
          </button>
        </div>
      )}

      {page === 2 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 11, color: 'var(--t2)', marginBottom: 4 }}>
            Briefly explain what you are trying to decide. This becomes the shared starting point for Claude and ChatGPT.
          </div>
          <div>
            <label style={labelStyle}>Your Context</label>
            <textarea rows={3} value={form.eric_context} onChange={e => set('eric_context', e.target.value)} style={inputStyle} placeholder="What are you trying to solve?" />
          </div>
          <div>
            <label style={labelStyle}>Current Concern</label>
            <textarea rows={2} value={form.current_concern} onChange={e => set('current_concern', e.target.value)} style={inputStyle} placeholder="What is worrying you about it?" />
          </div>
          <div>
            <label style={labelStyle}>Desired Outcome</label>
            <textarea rows={2} value={form.desired_outcome} onChange={e => set('desired_outcome', e.target.value)} style={inputStyle} placeholder="What would a good answer feel like?" />
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={() => setPage(1)} style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)' }}>← Back</button>
            <button onClick={saveContext} disabled={!form.eric_context}
              style={{ ...btnDef, background: 'var(--accent, #00bcd4)', color: '#000', flex: 1 }}>
              Generate Advisor Prompt →
            </button>
          </div>
        </div>
      )}

      {page === 3 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 11, color: 'var(--t2)', marginBottom: 4 }}>
            Send this prompt to both Claude and ChatGPT. Then come back and paste their responses.
          </div>
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 4, padding: 8, fontSize: 10, color: 'var(--t2)', whiteSpace: 'pre-wrap', lineHeight: 1.5, maxHeight: 200, overflowY: 'auto' }}>
            {advisorPrompt}
          </div>
          <button onClick={() => { try { navigator.clipboard.writeText(advisorPrompt) } catch {} }}
            style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)', fontSize: 10 }}>
            📋 Copy Prompt
          </button>
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            <button onClick={() => setPage(2)} style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)' }}>← Back</button>
            <button onClick={() => setPage(4)} style={{ ...btnDef, background: 'var(--accent, #00bcd4)', color: '#000', flex: 1 }}>
              I have responses →
            </button>
          </div>
        </div>
      )}

      {page === 4 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* LEGACY — deprecated in HHR-018, preserved for reference */}
          <div style={{ display: "none" }}>
          <div style={{ fontSize: 11, color: 'var(--t2)', marginBottom: 4 }}>Paste the responses from Claude and ChatGPT.</div>
          <div>
            <label style={labelStyle}>Claude Response</label>
            <textarea rows={5} value={form.claude_input} onChange={e => set('claude_input', e.target.value)} style={inputStyle} placeholder={"Paste Claude's response here..."} />
          </div>
          <div>
            <label style={labelStyle}>ChatGPT Response</label>
            <textarea rows={5} value={form.chatgpt_input} onChange={e => set('chatgpt_input', e.target.value)} style={inputStyle} placeholder={"Paste ChatGPT's response here..."} />
          </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            <button onClick={() => setPage(3)} style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)' }}>← Back</button>
            <button onClick={captureExchange} disabled={(!form.claude_input && !form.chatgpt_input) || saving}
              style={{ ...btnDef, background: (saving ? 'var(--bg2)' : 'var(--accent, #00bcd4)'), color: (saving ? 'var(--t3)' : '#000'), flex: 1 }}>
              {saving ? 'Saving...' : 'Save Exchange →'}
            </button>
          </div>
        </div>
      )}

      {page === 5 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 11, color: 'var(--green, #4caf50)', marginBottom: 4 }}>✓ Exchange captured.</div>
          {captureResult && (
            <div style={{ fontSize: 10, color: 'var(--t3)', background: 'var(--bg2)', padding: 4, borderRadius: 3 }}>
              Exchange #{captureResult.exchange_id} · Pass {captureResult.pass_number}
            </div>
          )}
          <div style={{ fontSize: 10, color: 'var(--t3)', marginTop: 4 }}>What next?</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <button onClick={continueTopic}
              style={{ ...btnDef, background: 'var(--accent, #00bcd4)', color: '#000' }}>
              ↩ Continue This Topic
            </button>
            <button onClick={openDirectivePage}
              style={{ ...btnDef, background: 'var(--accent, #00bcd4)', color: '#000' }}>
              📋 Final Directive →
            </button>
            <button onClick={() => { setPage(1); setForm({ topic:'', round_type:'', eric_context:'', current_concern:'', desired_outcome:'', claude_input:'', chatgpt_input:'' }); setRoundId(null); setCaptureResult(null); setCapturedPass(0); setEricAddendum(''); setFollowupPrompt(''); setError('') }}
              style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)' }}>
              + New Topic
            </button>
            <button onClick={handleClose}
              style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)' }}>
              Close
            </button>
          </div>
        </div>
      )}

      {confirmClose && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 11, color: '#ff5252', marginBottom: 4 }}>
            ⚠ You have unsaved advisor round text. Close and discard this draft?
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            <button onClick={() => setConfirmClose(false)}
              style={{ ...btnDef, background: 'var(--accent, #00bcd4)', color: '#000', flex: 1 }}>
              Keep Editing
            </button>
            <button onClick={discardAndClose}
              style={{ ...btnDef, background: 'var(--bg2)', color: '#ff5252', flex: 1 }}>
              Discard Draft
            </button>
          </div>
        </div>
      )}

      {page === 6 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 11, color: 'var(--t1)', marginBottom: 4 }}>🔄 Follow-up Round</div>
          <div style={{ fontSize: 11, color: 'var(--t2)', marginBottom: 4 }}>
            Add anything you want to steer this round, then copy the prompt for Claude and ChatGPT.
          </div>
          <div>
            <label style={labelStyle}>Your Addendum (optional)</label>
            <textarea rows={2} value={ericAddendum} onChange={e => setEricAddendum(e.target.value)}
              style={inputStyle} placeholder="Any direction, correction, or emphasis for this round..." />
          </div>
          <button onClick={generateFollowup}
            style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)', fontSize: 10 }}>
            ↺ Regenerate with Addendum
          </button>
          {followupPrompt && (
            <>
              <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 4, padding: 8, fontSize: 10, color: 'var(--t2)', whiteSpace: 'pre-wrap', lineHeight: 1.5, maxHeight: 160, overflowY: 'auto' }}>
                {followupPrompt}
              </div>
              <button onClick={() => { try { navigator.clipboard.writeText(followupPrompt) } catch {} }}
                style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)', fontSize: 10 }}>
                📋 Copy Follow-up Prompt
              </button>
            </>
          )}
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            <button onClick={() => setPage(5)} style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)' }}>← Back</button>
            <button onClick={() => { setForm(f => ({ ...f, claude_input: '', chatgpt_input: '' })); setPage(4) }}
              style={{ ...btnDef, background: 'var(--accent, #00bcd4)', color: '#000', flex: 1 }}>
              I have responses →
            </button>
          </div>
        </div>
      )}

      {page === 7 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {directiveResult ? (
            <>
              <div style={{ fontSize: 11, color: 'var(--green, #4caf50)', marginBottom: 4 }}>✓ Directive saved as draft.</div>
              {directiveResult.directive_id && (
                <div style={{ fontSize: 10, color: 'var(--t3)', background: 'var(--bg2)', padding: 4, borderRadius: 3 }}>
                  Directive #{directiveResult.directive_id} · Status: {directiveResult.status}
                </div>
              )}
              {error && <div style={{ fontSize: 10, color: '#ff5252', background: 'var(--bg2)', padding: 6, borderRadius: 4 }}>{error}</div>}
              <div style={{ display: 'flex', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
                <button onClick={copyDirective}
                  style={{ ...btnDef, background: 'var(--accent, #00bcd4)', color: '#000' }}>
                  📋 Copy Directive
                </button>
                <button onClick={() => setPage(5)} style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)' }}>← Back</button>
                <button onClick={() => { setPage(1); setForm({ topic:'', round_type:'', eric_context:'', current_concern:'', desired_outcome:'', claude_input:'', chatgpt_input:'' }); setRoundId(null); setCaptureResult(null); setCapturedPass(0); setEricAddendum(''); setFollowupPrompt(''); setDirectiveForm({ decision_made:'', accepted_basis:'', final_directive:'', scope:'', do_not_do:'', success_criteria:'', evidence_required:'', owner_executor:'Hermes', next_action:'', status:'draft' }); setDirectiveResult(null); setError('') }}
                  style={{ ...btnDef, background: 'var(--accent, #00bcd4)', color: '#000' }}>
                  + New Topic
                </button>
                <button onClick={handleClose}
                  style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)' }}>
                  Close
                </button>
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 11, color: 'var(--t2)', marginBottom: 4 }}>
                Paste the full Hermes-ready instruction below.
              </div>
              {error && <div style={{ fontSize: 10, color: '#ff5252', background: 'var(--bg2)', padding: 6, borderRadius: 4 }}>{error}</div>}
              <div>
                <label style={labelStyle}>Final Directive / Hermes-ready instruction</label>
                <textarea rows={8} value={directiveForm.final_directive} onChange={e => setD('final_directive', e.target.value)}
                  style={inputStyle} placeholder="Paste the complete directive as you want Hermes to receive it..." />
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Accepted Basis</label>
                  <select value={directiveForm.accepted_basis} onChange={e => setD('accepted_basis', e.target.value)} style={inputStyle}>
                    <option value="">Select...</option>
                    {BASIS_OPTIONS.map(o => <option key={o} value={o.toLowerCase().replace(' ','_')}>{o}</option>)}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Status</label>
                  <select value={directiveForm.status || 'draft'} onChange={e => setD('status', e.target.value)} style={inputStyle}>
                    {STATUS_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Owner</label>
                  <input value={directiveForm.owner_executor} onChange={e => setD('owner_executor', e.target.value)}
                    style={{ ...inputStyle, resize: 'none' }} placeholder="Hermes" />
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                <button onClick={() => setPage(5)} style={{ ...btnDef, background: 'var(--bg2)', color: 'var(--t3)' }}>← Back</button>
                <button onClick={saveDirective} disabled={!directiveForm.final_directive || saving}
                  style={{ ...btnDef, background: (saving ? 'var(--bg2)' : 'var(--accent, #00bcd4)'), color: (saving ? 'var(--t3)' : '#000'), flex: 1 }}>
                  {saving ? 'Saving...' : 'Save Directive'}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div></>
  )
}

function DirectivePanel({ directive, onDirectiveChange, onOpenNewRound }) {
  const [sending, setSending] = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [verifyBy, setVerifyBy] = useState('Claude')
  const [markError, setMarkError] = useState('')

  if (!directive) return null

  const instructionBlock = `DIRECTIVE ID: ${directive.id}
TASK: ${directive.final_directive}
SUCCESS CRITERIA: ${directive.success_criteria || '(none)'}
DO NOT DO: ${directive.do_not_do || '(none)'}
EVIDENCE REQUIRED: ${directive.evidence_required || '(none)'}
REPORT CALLBACK: POST http://127.0.0.1:5000/api/collab/directives/${directive.id}/report
REPORT SCHEMA: { "report": "<your execution summary>", "status": "EXECUTED" }

When your task is complete, POST your execution report to the callback above before responding in the terminal.`

  const markSent = async () => {
    setSending(true)
    try {
      const res = await fetch(`/api/collab/directives/${directive.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ execution_status: 'sent' })
      })
      const data = await res.json()
      if (data.ok) onDirectiveChange()
    } catch (e) { setMarkError('Failed to mark sent') }
    setSending(false)
  }

  const doVerify = async (result) => {
    setVerifying(true)
    try {
      const res = await fetch(`/api/collab/directives/${directive.id}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ result, verified_by: verifyBy })
      })
      const data = await res.json()
      if (data.ok) onDirectiveChange()
      else setMarkError(data.error || 'Verify failed')
    } catch (e) { setMarkError('Verify request failed') }
    setVerifying(false)
  }

  const copyDirectiveBlock = () => {
    navigator.clipboard.writeText(instructionBlock)
  }

  const copyReport = () => {
    navigator.clipboard.writeText(directive.execution_report || '')
  }

  const execStatus = directive.execution_status || 'draft'
  const statusBadge = {
    draft: { bg: 'var(--t3)', label: 'DRAFT' },
    sent: { bg: 'var(--accent, #00bcd4)', label: 'SENT' },
    executed: { bg: 'var(--orange, #ff9800)', label: 'EXECUTED' },
    verified_pass: { bg: 'var(--green, #4caf50)', label: 'VERIFIED PASS' },
    verified_fail: { bg: 'var(--red, #ff6b6b)', label: 'VERIFIED FAIL' },
    needs_revision: { bg: '#ff9800', label: 'NEEDS REVISION' },
  }[execStatus] || { bg: 'var(--t3)', label: execStatus.toUpperCase() }

  return (
    <div className="card" style={{ margin: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <div className="card-title" style={{ fontSize: 11, margin: 0 }}>
          📋 Directive #{directive.id} — {directive.topic || 'Untitled'}
        </div>
        <span style={{
          fontSize: 9, padding: '2px 8px', borderRadius: 3,
          background: statusBadge.bg, color: '#000', fontWeight: 600
        }}>{statusBadge.label}</span>
      </div>

      {/* Draft / Sent: show copyable block + Mark Sent button */}
      {(execStatus === 'draft' || execStatus === 'sent') && (
        <>
          <pre style={{
            fontSize: 10, background: 'var(--bg2)', color: 'var(--t3)',
            padding: 10, borderRadius: 4, overflowX: 'auto',
            whiteSpace: 'pre-wrap', margin: '0 0 8px 0'
          }}>{instructionBlock}</pre>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={copyDirectiveBlock} className="btn"
              style={{ padding: '4px 10px', fontSize: 10, cursor: 'pointer' }}>
              📋 Copy Instruction Block
            </button>
            {execStatus === 'draft' && (
              <button onClick={markSent} disabled={sending} className="btn"
                style={{ padding: '4px 10px', fontSize: 10, cursor: 'pointer' }}>
                {sending ? '...' : '▶ Mark as Sent'}
              </button>
            )}
          </div>
          {execStatus === 'sent' && (
            <p style={{ fontSize: 10, color: 'var(--t3)', margin: '6px 0 0' }}>
              Waiting for Hermes execution report…
            </p>
          )}
        </>
      )}

      {/* Executed: show report, verify controls */}
      {execStatus === 'executed' && (
        <>
          <div style={{
            fontSize: 10, background: 'var(--bg2)', color: 'var(--t2)',
            padding: 10, borderRadius: 4, whiteSpace: 'pre-wrap',
            maxHeight: 180, overflowY: 'auto', margin: '0 0 8px 0'
          }}>{directive.execution_report || '(empty)'}</div>
          <button onClick={copyReport} className="btn"
            style={{ padding: '4px 10px', fontSize: 10, cursor: 'pointer', marginBottom: 8 }}>
            📋 Copy Report
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 10, color: 'var(--t3)' }}>Verified by:</span>
            <select value={verifyBy} onChange={e => setVerifyBy(e.target.value)}
              style={{ fontSize: 10, padding: '3px 6px', background: 'var(--bg2)', color: 'var(--t1)', border: '1px solid var(--border)', borderRadius: 3 }}>
              <option value="Claude">Claude</option>
              <option value="ChatGPT">ChatGPT</option>
              <option value="Eric">Eric</option>
            </select>
            <button onClick={() => doVerify('verified_pass')} disabled={verifying} className="btn"
              style={{ padding: '4px 10px', fontSize: 10, cursor: 'pointer', background: 'var(--green, #4caf50)', color: '#000', borderColor: 'var(--green)' }}>
              {verifying ? '...' : '✅ Pass'}
            </button>
            <button onClick={() => doVerify('verified_fail')} disabled={verifying} className="btn"
              style={{ padding: '4px 10px', fontSize: 10, cursor: 'pointer', background: 'var(--red, #ff6b6b)', color: '#fff', borderColor: 'var(--red)' }}>
              {verifying ? '...' : '❌ Fail'}
            </button>
            <button onClick={() => doVerify('needs_revision')} disabled={verifying} className="btn"
              style={{ padding: '4px 10px', fontSize: 10, cursor: 'pointer', background: '#ff9800', color: '#000', borderColor: '#ff9800' }}>
              {verifying ? '...' : '🔧 Needs Revision'}
            </button>
          </div>
          {markError && <div style={{ fontSize: 10, color: 'var(--red)', marginTop: 4 }}>{markError}</div>}
        </>
      )}

      {/* verified_pass: final state */}
      {execStatus === 'verified_pass' && (
        <>
          <div style={{
            fontSize: 10, background: 'var(--bg2)', color: 'var(--t2)',
            padding: 10, borderRadius: 4, whiteSpace: 'pre-wrap',
            maxHeight: 180, overflowY: 'auto', margin: '0 0 8px 0'
          }}>{directive.execution_report || '(empty)'}</div>
          <div style={{ fontSize: 10, color: 'var(--green)', marginBottom: 4, fontWeight: 600 }}>
            ✅ VERIFIED PASS
          </div>
          <div style={{ fontSize: 10, color: 'var(--t3)' }}>
            Verified by {directive.verified_by || '?'} at {directive.verified_at ? directive.verified_at.slice(0,19).replace('T',' ') : '?'}
          </div>
        </>
      )}

      {/* verified_fail / needs_revision */}
      {(execStatus === 'verified_fail' || execStatus === 'needs_revision') && (
        <>
          <div style={{
            fontSize: 10, background: 'var(--bg2)', color: 'var(--t2)',
            padding: 10, borderRadius: 4, whiteSpace: 'pre-wrap',
            maxHeight: 180, overflowY: 'auto', margin: '0 0 8px 0'
          }}>{directive.execution_report || '(empty)'}</div>
          <div style={{ fontSize: 10, color: execStatus === 'verified_fail' ? 'var(--red)' : '#ff9800', marginBottom: 4, fontWeight: 600 }}>
            {execStatus === 'verified_fail' ? '❌ VERIFIED FAIL' : '🔧 NEEDS REVISION'}
          </div>
          <div style={{ fontSize: 10, color: 'var(--t3)', marginBottom: 6 }}>
            Verified by {directive.verified_by || '?'}
          </div>
          <button onClick={() => onOpenNewRound && onOpenNewRound()} className="btn"
            style={{ padding: '4px 10px', fontSize: 10, cursor: 'pointer' }}>
            📝 Open New Round
          </button>
        </>
      )}
    </div>
  )
}


export default function CollabTracker() {
  const [agents, setAgents] = useState([])
  const [status, setStatus] = useState(null)
  const [activity, setActivity] = useState([])
  const [showFullLog, setShowFullLog] = useState(false)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [handoffCopied, setHandoffCopied] = useState(false)
  const [handoffError, setHandoffError] = useState('')
  const [directive, setDirective] = useState(null)
  const [activeRoundId, setActiveRoundId] = useState(null)

  const fetchDirective = async () => {
    try {
      const roundsRes = await fetch('/api/collab/rounds')
      const rounds = await roundsRes.json()
      if (rounds.length > 0) {
        const latestRoundId = rounds[0].id
        setActiveRoundId(latestRoundId)
        const dirRes = await fetch(`/api/collab/rounds/${latestRoundId}/final-directive`)
        const dirData = await dirRes.json()
        if (dirData.directive) setDirective(dirData.directive)
      }
    } catch (e) {}
  }

  useEffect(() => {
    fetch('/api/collab/agents').then(r => r.json()).then(setAgents).catch(() => {})
    fetch('/api/collab/status').then(r => r.json()).then(setStatus).catch(() => {})
    fetch('/api/collab/activity').then(r => r.json()).then(setActivity).catch(() => {})
    fetchDirective()
  }, [])

  const copyHandoff = async () => {
    try {
      setHandoffError('')
      const res = await fetch('/api/collab/handoff')
      const data = await res.json()
      if (!res.ok || !data.ok) {
        throw new Error(data.error || 'Failed to generate handoff')
      }
      await navigator.clipboard.writeText(data.handoff)
      setHandoffCopied(true)
      setTimeout(() => setHandoffCopied(false), 3000)
    } catch (e) {
      setHandoffError('Handoff copy failed')
      setTimeout(() => setHandoffError(''), 4000)
    }
  }

  const latest3 = activity.slice(0, 3)
  const displayed = showFullLog ? activity : latest3

  return (
    <div style={{ display: 'flex', height: '100%', gap: 0 }}>
      {/* Main briefing area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12, padding: 16, overflowY: 'auto', minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={() => { if (!wizardOpen) setWizardOpen(true) }}
            style={{ padding: '5px 12px', fontSize: 10, borderRadius: 4, cursor: 'pointer', border: '1px solid var(--border)', background: wizardOpen ? 'var(--accent, #00bcd4)' : 'var(--bg2)', color: wizardOpen ? '#000' : 'var(--t3)' }}>
            {wizardOpen ? '🧭 Advisor Round Open' : '🧭 Open Advisor Round'}
          </button>
          <button
            onClick={copyHandoff}
            style={{
              padding: '5px 12px',
              fontSize: 10,
              borderRadius: 4,
              cursor: 'pointer',
              border: '1px solid var(--border)',
              background: 'var(--bg2)',
              color: handoffCopied ? 'var(--green, #4caf50)' : handoffError ? 'var(--red, #ff6b6b)' : 'var(--t3)',
              marginLeft: 6
            }}
          >
            {handoffCopied ? '✓ Copied' : handoffError ? '⚠ Copy Failed' : '📄 Copy Handoff'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          {status && (
            <div className="card" style={{ flex: 1, margin: 0 }}>
              <div className="card-title" style={{ fontSize: 11 }}>🎯 Current Focus</div>
              <p style={{ fontSize: 12, color: 'var(--t1)', margin: '6px 0 4px', lineHeight: 1.4 }}>{status.current_focus}</p>
              <div style={{ fontSize: 11, color: 'var(--t3)' }}>
                <strong>Next:</strong> {status.next_single_action}
              </div>
              {status.blocked_waiting && (
                <div style={{ fontSize: 11, color: 'var(--t3)', marginTop: 3 }}>
                  <strong>Blocked:</strong> {status.blocked_waiting}
                </div>
              )}
              <div style={{ fontSize: 10, color: 'var(--t3)', marginTop: 6 }}>
                {status.status} · {status.updated_by} · {status.updated_at ? status.updated_at.slice(0, 19).replace('T', ' ') : ''}
              </div>
            </div>
          )}
          <div className="card" style={{ width: 260, minWidth: 200, margin: 0, padding: '12px 14px' }}>
            <div className="card-title" style={{ fontSize: 11, marginBottom: 6 }}>🤝 Collaborators</div>
            {agents.map(a => (
              <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '3px 0', fontSize: 11 }}>
                <span style={{ color: STATUS_COLORS[a.status] || 'var(--t3)', fontSize: 10 }}>●</span>
                <span style={{ color: 'var(--t1)', fontWeight: 600 }}>{a.name}</span>
                <span style={{ color: 'var(--t3)', marginLeft: 'auto' }}>{a.role}</span>
              </div>
            ))}
          </div>
        </div>

        <DirectivePanel directive={directive} onDirectiveChange={fetchDirective} onOpenNewRound={() => setWizardOpen(true)} />

        <div className="card" style={{ margin: 0 }}>
          <div className="card-title" style={{ fontSize: 11 }}>📋 Recent Activity</div>
          <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
            {displayed.length === 0 && <p style={{ fontSize: 11, color: 'var(--t3)' }}>No activity yet.</p>}
            {displayed.map(a => (
              <div key={a.id} style={{ fontSize: 11, display: 'flex', gap: 6, alignItems: 'baseline', flexWrap: 'wrap' }}>
                <span style={{ color: 'var(--accent, #00bcd4)', fontWeight: 600, whiteSpace: 'nowrap' }}>{a.source}</span>
                <span style={{ color: 'var(--t3)', fontSize: 10 }}>[{a.activity_type}]</span>
                <span style={{ color: 'var(--t1)', flex: 1, minWidth: 0 }}>{a.summary}</span>
                {a.verdict && <span style={{ color: 'var(--t3)', fontSize: 10, whiteSpace: 'nowrap' }}>→ {a.verdict}</span>}
                <span style={{ color: 'var(--t3)', fontSize: 10, whiteSpace: 'nowrap', marginLeft: 'auto' }}>
                  {a.created_at ? a.created_at.slice(0, 19).replace('T', ' ') : ''}
                </span>
              </div>
            ))}
          </div>
          {activity.length > 3 && (
            <button onClick={() => setShowFullLog(v => !v)}
              className="btn" style={{ marginTop: 8, padding: '5px 12px', fontSize: 10 }}>
              {showFullLog ? '▲ Show Less' : `▼ Show Full Log (${activity.length} items)`}
            </button>
          )}
        </div>
      </div>

      {/* Advisor Round wizard overlay */}
      {wizardOpen && (
        <>
          <div
            style={{
              position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
              zIndex: 1000
            }} />
          <AdvisorWizard onClose={() => setWizardOpen(false)} />
        </>
      )}
    </div>
  )
}
