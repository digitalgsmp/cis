# Files Changed Recently
Generated: 2026-06-28 06:03 UTC | Run: run-ecf3e2ccf63c
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## 4c3d396 feat(pipeline): CIS front door + intent-alignment + knowledge search

## .gitignore 

## cis_kernel/source/SESSION_LOG.md 

## docs/CIS_INTENTION_ALIGNMENT_PIPELINE_SPEC.md 

## docs/CIS_INTENT_ALIGNMENT_WORKFLOW_SPEC.md 

## docs/DEV-PIVOT-05_HERMES_INTEGRATION_ASSESSMENT.md 

## docs/DEV-PIVOT-06_BUILD_DIRECTION.md 

## docs/SESSION_HANDOFF_2026-06-25.md 

## docs/SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE.md 

## docs/SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md 

## enforcement/CATEGORY_TO_LAYER_MAP.md 

## enforcement/TAGGING_DIRECTIVE_v3.md 

## runtime/abstraction/__init__.py 

## runtime/abstraction/dispatch.py 

## runtime/api/adapter.py 

## runtime/api/intent.py 

## runtime/app.py 

## runtime/mcp_bridge/spine.py 

## runtime/mcp_bridge/tools.py 

## runtime/ui/public/portal.html 

## tools/catalog/append_embeddings.py 

## tools/catalog/apply_review.py 

## tools/catalog/batch_tag_claude.py 

## tools/catalog/build_embeddings.py 

## tools/catalog/convert_to_knowledge.py 

## tools/catalog/ingest_chatgpt_only.py 

## tools/catalog/ingest_intentions.py 

## tools/catalog/ingest_legacy.py 

## tools/catalog/search_catalog.py 

## tools/pipeline/drafter_start.py 

## tools/pipeline/measure_intent.py 

## tools/pipeline/reviewer_reconcile.py 

## 661c3b8 session handoff: intent recovery pipeline + 3-model tagging proof

## docs/SESSION_HANDOFF_2026-06-25.md 

## enforcement/TAGGING_DIRECTIVE_v3.md 

## enforcement/mwl-proof-v2/tagging_results/CIS_16_FAILURE_MODES__claude-opus.txt 

## enforcement/mwl-proof-v2/tagging_results/CIS_16_FAILURE_MODES__ds-reasoner.txt 

## enforcement/mwl-proof-v2/tagging_results/CIS_16_FAILURE_MODES__glm-5.2.txt 

## enforcement/mwl-proof-v2/tagging_results/MWL_PROOF_REPRODUCTION__claude-opus.txt 

## enforcement/mwl-proof-v2/tagging_results/MWL_PROOF_REPRODUCTION__ds-reasoner.txt 

## enforcement/mwl-proof-v2/tagging_results/MWL_PROOF_REPRODUCTION__glm-5.2.txt 

## enforcement/mwl-proof-v2/tagging_results/claude_crystallizes_the_vision.txt__claude-opus_v2.txt 

## enforcement/mwl-proof-v2/tagging_results/claude_crystallizes_the_vision__claude-opus.txt 

## enforcement/mwl-proof-v2/tagging_results/claude_crystallizes_the_vision__ds-reasoner.txt 

## enforcement/mwl-proof-v2/tagging_results/claude_crystallizes_the_vision__glm-5.2.txt 

## b1d4cfe enforcement: MWL sealed container — managed-scope pinning closes self-disable bypass

## enforcement/mwl-proof-v2/Dockerfile 

## enforcement/mwl-proof-v2/cis_shell_hook.sh 

## enforcement/mwl-proof-v2/managed-config.yaml 

## enforcement/mwl-proof-v2/verify.sh 

## enforcement/mwl-proof-v2/verify_seal.sh 

## c632b7f docs: add MWL proof reproduction reference document

## docs/MWL_PROOF_REPRODUCTION.md 

## d811f04 Regenerate context after session closeout

## AGENTS.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_00_README_START_HERE.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_01_CURRENT_STATE.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_02_ACTIVE_ARCHITECTURE.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_03_DECISIONS_LOG.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_04_OPEN_QUESTIONS.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_05_NEXT_ACTIONS.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_06_MODEL_ROLES_AND_PROTOCOL.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_07_RECENT_HANDOFF.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_08_FILES_CHANGED_RECENTLY.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_09_TERMS_AND_NAMING.md 

## PROJECT_CONTEXT_PACK_UPLOAD/READ_FIRST_HERMES_CONTEXT.md 

## runtime/manifests/EXPORT_MANIFEST.json 

## 8c543f1 docs: add Claude audit and vision crystallization from caged-worker session

## docs/Claude Roadmap Audit 20260624.txt

## docs/claude crystallizes the vision.txt

## 5a8052b Regenerate context after session closeout

## AGENTS.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_00_README_START_HERE.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_01_CURRENT_STATE.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_02_ACTIVE_ARCHITECTURE.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_03_DECISIONS_LOG.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_04_OPEN_QUESTIONS.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_05_NEXT_ACTIONS.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_06_MODEL_ROLES_AND_PROTOCOL.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_07_RECENT_HANDOFF.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_08_FILES_CHANGED_RECENTLY.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_09_TERMS_AND_NAMING.md 

## PROJECT_CONTEXT_PACK_UPLOAD/READ_FIRST_HERMES_CONTEXT.md 

## runtime/manifests/EXPORT_MANIFEST.json 

## 8a48416 fix(gate): handle non-numeric completed_tier (e.g. PD) in coherence gate

## tools/gates/gate_build_state_coherence.py 

## 4928108 feat(portal): live gateway monitor API + external advisor briefing

## docs/CIS_EXTERNAL_ADVISOR_BRIEFING_2026-06-25.md 

## runtime/app.py 

## runtime/ui/public/monitor-test.html 

## runtime/ui/public/portal.html 

## runtime/ui/public/roadmap-live.html 

## e713d76 session closeout 2026-06-24: Phase PD CLOSED, HCP regenerated, portal context labels, loop-breaker root cause committed to DB

## AGENTS.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_00_README_START_HERE.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_01_CURRENT_STATE.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_02_ACTIVE_ARCHITECTURE.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_03_DECISIONS_LOG.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_04_OPEN_QUESTIONS.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_05_NEXT_ACTIONS.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_06_MODEL_ROLES_AND_PROTOCOL.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_07_RECENT_HANDOFF.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_08_FILES_CHANGED_RECENTLY.md 

## PROJECT_CONTEXT_PACK_UPLOAD/HCP_09_TERMS_AND_NAMING.md 

## PROJECT_CONTEXT_PACK_UPLOAD/READ_FIRST_HERMES_CONTEXT.md 

## docs/PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md 

## docs/SESSION_HANDOFF_2026-06-24.md 

## runtime/app.py 

## runtime/ui/public/portal.html 

## f2daf33 Phase PD closeout handoff

## docs/HANDOFF_PHASE_PD_CLOSE.md 

## ddf8667 docs: session handoff — MWL proof state, trust root fix (openai→llamacpp), remaining blocker (Qwen bind)

## docs/SESSION_HANDOFF_2026-06-23_MWL.md 

## 41154e5 feat(portal): bridge new portal and React SPA — Roadmap tab in portal via iframe, ← Portal back-link

## runtime/ui/public/portal.html 

## runtime/ui/src/pages/RoadmapPage.jsx 

## 45848d0 feat(portal): Roadmap tab — status grid (Built/Specified/Theorized) + timeline + ADRs + Eric's vision

## runtime/ui/src/App.jsx 

## runtime/ui/src/pages/RoadmapPage.jsx 

## a88cb19 feat(portal): cross-panel message visibility in Advisor Chat — all panels show messages from all agents with 'other panel' badge for visual distinction

## runtime/ui/src/pages/infra/AdvisorChat.jsx 
