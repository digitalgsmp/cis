import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from './api.js'
import BrainChat from './BrainChat.jsx'
import PipelineLive from './PipelineLive.jsx'
import RunsList from './RunsList.jsx'
import SystemDashboard from './SystemDashboard.jsx'

const TAB_BRAIN = 'brain'
const TAB_PIPELINE = 'pipeline'
const TAB_RUNS = 'runs'
const TAB_SYSTEM = 'system'

export default function App() {
  const [tab, setTab] = useState(TAB_BRAIN)
  const [activeRunId, setActiveRunId] = useState(null)
  const [health, setHealth] = useState(null)

  // Health check
  useEffect(() => {
    const check = async () => {
      try {
        const resp = await fetch('/api/health')
        setHealth(await resp.json())
      } catch {
        setHealth(null)
      }
    }
    check()
    const iv = setInterval(check, 30000)
    return () => clearInterval(iv)
  }, [])

  const handlePipelineStarted = (runId) => {
    setActiveRunId(runId)
    setTab(TAB_PIPELINE)
  }

  return (
    <div className="app-shell">
      <div className="topbar">
        <div className="topbar-logo">CIS Control Panel</div>
        <div className="topbar-nav">
          <button
            className={`nav-btn ${tab === TAB_BRAIN ? 'active' : ''}`}
            onClick={() => setTab(TAB_BRAIN)}
          >
            Brain
          </button>
          <button
            className={`nav-btn ${tab === TAB_PIPELINE ? 'active' : ''}`}
            onClick={() => setTab(TAB_PIPELINE)}
          >
            Pipeline
          </button>
          <button
            className={`nav-btn ${tab === TAB_RUNS ? 'active' : ''}`}
            onClick={() => setTab(TAB_RUNS)}
          >
            Runs
          </button>
          <button
            className={`nav-btn ${tab === TAB_SYSTEM ? 'active' : ''}`}
            onClick={() => setTab(TAB_SYSTEM)}
          >
            System
          </button>
        </div>
        <div className="topbar-spacer" />
        <div className="topbar-status">
          {health ? (
            <>
              <span className={`status-dot ok`}></span>
              Container OK
            </>
          ) : (
            <>
              <span className="status-dot down"></span>
              No connection
            </>
          )}
        </div>
      </div>

      <div className="main-content">
        {tab === TAB_BRAIN && (
          <BrainChat onPipelineStarted={handlePipelineStarted} />
        )}
        {tab === TAB_PIPELINE && (
          <PipelineLive
            runId={activeRunId}
            onRunIdChange={setActiveRunId}
          />
        )}
        {tab === TAB_RUNS && (
          <RunsList
            onSelectRun={(id) => {
              setActiveRunId(id)
              setTab(TAB_PIPELINE)
            }}
          />
        )}
        {tab === TAB_SYSTEM && (
          <SystemDashboard />
        )}
      </div>
    </div>
  )
}
