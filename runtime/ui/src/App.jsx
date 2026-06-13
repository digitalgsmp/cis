import React, { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import { api } from './api'
import IdeasPage from './pages/IdeasPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetail from './pages/ProjectDetail'
import SchedulePage from './pages/SchedulePage'
import DamPage from './pages/DamPage'
import AssetDetail from './pages/AssetDetail'
import ReviewQueue from './pages/ReviewQueue'
import LearningPage from './pages/LearningPage'
import IngestionPage from './pages/IngestionPage'
import SpineGraphPage from './pages/SpineGraphPage'
import InfraPage from './pages/InfraPage'
import ChatConsole from './pages/ChatConsole'
import AdvisorChat from './pages/infra/AdvisorChat'
import HomePage from './pages/HomePage'
import PipelinePage from './pages/PipelinePage'
import EricGatePage from './pages/EricGatePage'
import ArchiveSearchPage from './pages/ArchiveSearchPage'
import SessionArchivePage from './pages/SessionArchivePage'
import DecisionsPage from './pages/DecisionsPage'
import './index.css'

const NAV = [
  { path: '/ideas', label: 'Ideas' },
  { path: '/projects', label: 'Projects' },
  { path: '/schedule', label: 'Schedule' },
  { path: '/dam', label: 'DAM' },
  { path: '/learn', label: 'Learn' },
  { path: '/review', label: 'Review' },
  { path: '/ingest', label: 'Ingestion' },
  { path: '/spines', label: 'Map' },
  { path: '/infra', label: 'Infra' },
  { path: '/chat', label: 'Chat' },
  { path: '/advisor-chat', label: 'Advisor Chat' },
  { path: '/pipeline', label: 'Pipeline' },
  { path: '/eric-gate', label: 'Eric Gate' },
  { path: '/archive/search', label: 'Archive' },
  { path: '/archive/sessions', label: 'Sessions' },
  { path: '/decisions', label: 'Decisions' },
]

export default function App() {
  const [stats, setStats] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    api.dashboard().then(setStats).catch(() => {})
  }, [])

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#09090c', display: 'flex', flexDirection: 'column' }}>
      {/* Top bar */}
      <div className="topbar">
        <div className="tb-logo" style={{cursor:'pointer'}} onClick={() => navigate('/')}>CIS █</div>
        <div className="tb-nav">
          {NAV.map(n => (
            <NavLink key={n.path} to={n.path}
              className={({ isActive }) => isActive ? 'active' : ''}>
              {n.label}
            </NavLink>
          ))}
        </div>
        <div style={{ flex: 1 }} />
        <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 9, color: '#3dffa0' }}>
          ● kernel
        </span>
      </div>

      {/* Content */}
      <div className="main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/ideas" element={<IdeasPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/schedule" element={<SchedulePage />} />
          <Route path="/dam" element={<DamPage />} />
          <Route path="/dam/:id" element={<AssetDetail />} />
          <Route path="/review" element={<ReviewQueue />} />
          <Route path="/learn" element={<LearningPage />} />
          <Route path="/ingest" element={<IngestionPage />} />
          <Route path="/spines" element={<SpineGraphPage />} />
          <Route path="/infra" element={<InfraPage />} />
          <Route path="/chat" element={<ChatConsole />} />
          <Route path="/advisor-chat" element={<AdvisorChat />} />
          <Route path="/pipeline" element={<PipelinePage />} />
          <Route path="/eric-gate" element={<EricGatePage />} />
          <Route path="/archive/search" element={<ArchiveSearchPage />} />
          <Route path="/archive/sessions" element={<SessionArchivePage />} />
          <Route path="/decisions" element={<DecisionsPage />} />
        </Routes>
      </div>

      {/* Status bar */}
      <div className="statusbar">
        <span className="sb"><span style={{width:4,height:4,borderRadius:'50%',background:'var(--green)',display:'inline-block'}}></span> CIS Kernel</span>
        <span style={{fontFamily:'"Share Tech Mono", monospace',fontSize:9,color:'#7a8299'}}>|</span>
        <span className="sb">{stats.projects_total || 0} projects</span>
        <span className="sb">{stats.assets_total || 0} assets</span>
        <span className="sb">{stats.ideas_total || 0} ideas</span>
        <span className="sb">{stats.slots_total || 0} slots</span>
      </div>
    </div>
  )
}
