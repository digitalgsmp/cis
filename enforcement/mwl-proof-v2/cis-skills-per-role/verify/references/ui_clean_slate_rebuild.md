# UI Clean Slate Rebuild (2026-07-11)

## Context

Eric's directive: "start a new UI in the container, that will be the
control panel for the application. I just need a clean with no previous
UI experiments."

The old UI had:
- 15+ React page components (RelayPage, PipelinePage, DashboardPage,
  ChatConsole, EricGatePage, DecisionsPage, SchedulePage, LearningPage,
  ProjectDetail, ProjectsPage, RoadmapPage, InfraPage, ReviewQueue,
  IngestionPage, DamPage)
- Standalone HTML portals (portal.html, roadmap-live.html, monitor-test.html)
- cis_kernel/source/runtime_code/ directory with v1/v2/v3 HTML mockups
- dist-standalone directory (second build)
- ui_archive directory (old archived pages)

Multiple models wrote to different UI versions randomly — confusing.

## What Was Built

Old UI archived to `runtime/ui_legacy_backup/`. Fresh React app with
3 components only:

| Component | Purpose | Key Feature |
|-----------|---------|-------------|
| BrainChat | Pre-pipeline conversation with Brain | KB-enriched, session persists, "Start Pipeline" button |
| PipelineLive | Live observation feed | Phase cards, gate results, backchannel input box |
| RunsList | Recent run history | Polls /api/relay/runs, click to observe |

Package.json stripped to react + react-dom only (removed fullcalendar,
reactflow, react-router-dom). Vite base: '/ui/'.

## Key Design Decision: Backchannel, Not Checkpoints

Eric explicitly rejected checkpoint-based interaction. The pipeline runs
continuously. The backchannel input box in PipelineLive is always available
but never blocks the pipeline. Interjections are stored in
`pipeline_interjections` table and consumed by `_consume_interjections()`
in `_pre_discovery()` — injected into the next phase's prompt automatically.

See [Brain Chat & Backchannel Pattern](brain_chat_backchannel_pattern.md)
for full technical details.

## Supersedes

The old RelayPage.jsx (described in control_plane_build_complete.md Phase B1)
is no longer the active UI. The form-submission intent model is replaced by
the conversational Brain chat model.
