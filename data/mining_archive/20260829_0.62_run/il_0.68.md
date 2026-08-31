# ISSUE LIST — distilled from the mined record

Built by tools/build_issue_list.py from docs/SECONDARY_QUEUE.md and
docs/SECONDARY_QUEUE_SEMANTIC.md. Statements that mean the same thing
are clustered into ONE issue. This is the working list; those two
files are the raw material behind it.

PROVENANCE for every entry: `support` is how many separate statements
in the corpus say this; `docs` is how many distinct documents said it.
High docs count = independently recognised in different places, which
is stronger evidence than the same sentence repeated in one file.

An entry proves a recognition was WRITTEN DOWN. It does NOT prove the
issue is still open. Verify before acting — several checked on
2026-08-29 turned out to be implemented by other means.

- clusters: 4,117
- with 2+ supporting statements: 1,225
- of those, already on the working queue: 4
- of those, NOT on the working queue: 1,221
- single-statement clusters (listed last): 2,892


## NOT on the working queue — candidates to merge  (1221)

### Architectural Significance**: Structured conflict logging with CLI tool; rule that unresolved conflicts must be logged before session close
- support: 24 statements across 12 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Now, session start checks for unresolved failures, and session end requires zero failures to close cleanly.
- support: 18 statements across 12 document(s)
- nearest queue item 5 is only sim 0.42 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...ce_System_v1/runtime_scripts/runtime/2_CIS_REORIENTATION.md`
  - `...chat_2026_04_005_extraction_analysis_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Schema validation**: No validation that payload matches expected schema for draft type
- support: 12 statements across 12 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...action/functional_intents/cis_ingest_extraction_analysis.md`
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`
  - `...extraction/functional_intents/drafts_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`

### ``` Field 5 — Verification Status: Manifests produced: [count] Verifications run: [count] Unresolved FAILs: [count — must be 0 to close cleanly] Verification log: /mnt/projects/cis/logs/verification_log.md ```
- support: 12 statements across 11 document(s)
- nearest queue item 16 is only sim 0.43 — treat as NEW
  - `...-9d9c-e83384f51db8:Starting a new session with files#r1`
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Session Validation** — No validation that session has meaningful content before resolution
- support: 13 statements across 10 document(s)
- nearest queue item 8 is only sim 0.36 — treat as NEW
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...n/functional_intents/session_extract_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Before this file, governance was a set of documents. After this file, governance is an operational system with: - Explicit provenance requirements (--approved-by, --architect) - Two-phase atomic apply with preview enforcement - Process lock enforcement - Conflict logging with structured format - Que
- support: 12 statements across 10 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `...0260505_0058_01_current_state_extraction_analysis.md#r1`
  - `...0345839_x_01_system_blueprint_extraction_analysis.md#r6`
  - `...0502_0047_09_governance_state_extraction_analysis.md#r0`
  - `...0502_0047_09_governance_state_extraction_analysis.md#r5`
  - `...d_start_new_ai_session_prompt_extraction_analysis.md#r4`
  - `...direct_access_to_google_ai_69_extraction_analysis.md#r5`

### Impact**: All previously planned build targets are now deferred until after execution layer is operational
- support: 10 statements across 10 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### Unresolved Application Surface: Full Application Layer
- support: 10 statements across 10 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...lligence_routing_model_orchestration_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Unresolved Storage Rules: Memory Archival**: The rules for archiving old memory entries are not defined.
- support: 10 statements across 10 document(s)
- nearest queue item 18 is only sim 0.50 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Decisions API has a silent failure mode**: Missing the `description` field causes the API to return `{"success": false}` but the error message is only visible if you parse the JSON response.
- support: 25 statements across 9 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...26-04-21_Session close and handoff process clarification.md`
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Architectural Significance**: CIS_CONFLICT_REGISTER.md is now a required artifact for tracking unresolved contradictions, drift, and terminology issues.
- support: 12 statements across 9 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...itutional_memory_governance_revision_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...pts/ChatGTP_Project_Primer/archive/PROJECT_PRIMER_UPDATE.md`
  - `...ranscripts/ChatGTP_Project_Primer/10_OPERATIONAL_REALITY.md`

### The "no new governance surface" rule is adopted but not formalized as an ADR.** This is a governance gap that needs resolution.
- support: 11 statements across 9 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Runtime Impact**: Every session must pass through OPEN→ACTIVE→RESOLVED→ARCHIVED lifecycle; unresolved sessions block continuity
- support: 9 statements across 9 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...on/functional_intents/implementation_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### - **Architectural Significance**: Identifies a critical missing layer between Workflow Stream (descriptive) and Application Layer (UI). The Execution Layer is the operational engine that makes the system executable by someone other than the architect. - **Affected Layers**: Workflow Stream, Applicat
- support: 9 statements across 9 document(s)
- nearest queue item 12 is only sim 0.38 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._legacybuildfiles_x_02_memory_extraction_analysis.md#r2`
  - `...an AI platform for professional project guidance.md:333`
  - `...is_workflow_execution_spec_v1_extraction_analysis.md#r1`

### Dashboard HTML refactor deferred | 2736-line monolith cannot be safely restructured mid-build | Blocks frontend modularization
- support: 17 statements across 8 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Model registry API → Intel sidebar | GET /api/models endpoint does not exist | HIGH — blocks ADR-024/025
- support: 10 statements across 8 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0547_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`

### Missing Layers:** The staged draft intake layer (ADR-048) and filesystem governance layer (ADR-047) are identified as missing layers that will be implemented after ADR-045 closure.
- support: 10 statements across 8 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...intents/20260502_0047_05_adr_summary_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### No Governance or Validation Exists**: The system has no governance layer, no validation logic, no authority structures, and no quality control mechanisms.
- support: 8 statements across 8 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### Architectural Significance**: ADR-048 Phase 3 (commit layer) is intentionally deferred because approval and commit are architecturally separate concerns.
- support: 18 statements across 7 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Verification Layer**: Blocked by chunked verification architecture, contract verification sequencing
- support: 13 statements across 7 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### Gap:** Workflow stages are defined but stage schema (input, output, validation, state transition) is not formalized.
- support: 12 statements across 7 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Architectural Significance**: Identifies that the human operator had become middleware between incomplete orchestration layers, creating a critical bottleneck in the execution pipeline.
- support: 10 statements across 7 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ions_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ntents/hand_offs_cis_handoff_phase_d_extraction_analysis.md`
  - `...ve/SESSION_DISTILLATIONS/2026-04-28_operator_layer_pivot.md`
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Intake Ownership Layer** — [DEFERRED → PRIMARY TARGET] Previously deferred, now identified as the missing architectural layer.
- support: 9 statements across 7 document(s)
- nearest queue item 11 is only sim 0.33 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...P_Project_Primer/_backups/20260505_0058/01_CURRENT_STATE.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### Intake layer is the biggest gap**: ADR-048 intake layer not yet built means human manually transfers structured content - this is the primary automation gap.
- support: 9 statements across 7 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...Project_Primer/archive/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...ranscripts/ChatGTP_Project_Primer/10_OPERATIONAL_REALITY.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### 5. **Missing Governance Infrastructure**: The file reveals significant gaps in governance (no override mechanisms, no escalation paths, no audit trails) that must be addressed before implementation.
- support: 8 statements across 7 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `...al_intents/moved_requirements_extraction_analysis.md#r5`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...tional_intents/x_cis_execution_layer_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Architectural Significance**: Filesystem Governance and Staged Draft Intake are recognized as future layers but have no implementation yet.
- support: 8 statements across 7 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_02_0558_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### CREATION pipeline proven first, LIFE domains deferred.** But design decisions made with LIFE in mind may need revision based on CREATION pipeline experience.
- support: 7 statements across 7 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Missing Validation Layers: Schema Validation.** There is no schema validation for the knowledge records or the manifest files.
- support: 7 statements across 7 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...extraction/functional_intents/health_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Missing Validation Logic**: No structured validation exists for extraction quality
- support: 7 statements across 7 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### Architectural Significance**: Missing Phase 0 contract documents are identified: source manifest, processing profile, review states.
- support: 13 statements across 6 document(s)
- nearest queue item 2 is only sim 0.51 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Manual Paste Confirmed:** Auto-fetch model responses deferred — manual paste is the confirmed input method (ADR-029)
- support: 9 statements across 6 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:36`
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### States**: Incomplete (some dependencies not mapped), Complete (all dependencies mapped), Validated (dependencies have been validated)
- support: 9 statements across 6 document(s)
- nearest queue item 5 is only sim 0.44 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

### No Validation Layer**: There is no explicit validation of handoff package completeness, phase accuracy, or stream relevance.
- support: 8 statements across 6 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0410_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### After this file, it is explicitly identified as an **architectural gap** — a missing layer in the system topology.
- support: 7 statements across 6 document(s)
- nearest queue item 22 is only sim 0.41 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### States**: Downloaded, Evaluated, Registered, Operational, Deferred.
- support: 7 statements across 6 document(s)
- nearest queue item 5 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`
  - `...primer_update_governance_contract_v1_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### Build Impact**: Does NOT block ADR-048 Phase 2; explicitly deferred to build-plan reconstruction stage
- support: 7 statements across 6 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...traction/functional_intents/cis_live_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Two runtime bugs are known and deferred** — Field 5 FAIL count reads full historical log (not scoped to current session), and ADR form auto-increment resets to ADR-020 after log.
- support: 7 statements across 6 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`
  - `...transcripts/ChatGTP_Project_Primer/Current State Updated.md`
  - `cis_handoffs/CIS_Handoff_2026-05-02_0558_CORRECTED.md`

### Architectural Significance**: Identifies that the human operator currently functions as the transport bridge between AI-generated content and canonical CIS records, creating a systemic bottleneck and audit gap
- support: 7 statements across 6 document(s)
- nearest queue item 21 is only sim 0.36 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Transitional Gap Governance Loop**: Named gap → target resolution → gap resolved → reduction implemented
- support: 7 statements across 6 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### This session was supposed to open Phase 1 build work beginning with the three missing Phase 0 contracts — source manifest, processing profile, and review states — and then move into building cis_spine_intake.py.
- support: 7 statements across 6 document(s)
- nearest queue item 8 is only sim 0.43 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### LOCKED — final, constitutionally authoritative OPERATIONAL — governing current behavior in runtime TRANSITIONAL — partially implemented or temporary PRE-DRAFT — scope written, not yet locked for build PLANNED — identified and directionally decided DEFERRED — known, postponed
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `..._Primer/_backups/20260502_0047/09_GOVERNANCE_STATE.md:2`
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...enerated_script_artifacts/042926_Project_Primer.txt:121`
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `...scripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md:2`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Draft States**: PRE-DRAFT (not yet built), STAGED (future), APPROVED (future), REJECTED (future), SUPERSEDED (future)
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.47 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `...ve_06_foundational_control_contracts_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Runtime Impact**: Runtime cannot proceed with unresolved contradictions that affect operational behavior.
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...itutional_memory_governance_revision_extraction_analysis.md`
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...on/functional_intents/implementation_extraction_analysis.md`

### Validating → Failed**: Output fails validation (missing required sections, incorrect format)
- support: 6 statements across 6 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...extraction/functional_intents/collab_extraction_analysis.md`
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...on/functional_intents/cis_preprocess_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Gap**: Records must be in source-contained directories, but no specific storage rules defined.
- support: 6 statements across 6 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...xtraction/functional_intents/helpers_extraction_analysis.md`

### Session→Resolution→Handoff→Reorientation**: Continuity maintained through structured handoffs; unresolved sessions break continuity
- support: 6 statements across 6 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### It contains the complete architectural extraction with all sections preserved, including discovered entities, dependency chains, execution flows, orchestration behavior, workflow stages, state transitions, validation logic, governance implications, unresolved gaps, build-order implications, canonica
- support: 6 statements across 6 document(s)
- nearest queue item 22 is only sim 0.34 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### It introduces a new architectural layer: Staged Draft Intake.** This is not a feature request—it is a missing architectural layer that must exist between model output and canonical records.
- support: 6 statements across 6 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### Foundational Prerequisites:** The missing Phase 0 contracts (source manifest, processing profile, review states) must be written before any Phase 1 pipeline scripts are built.
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### ## 6. KNOWLEDGE-LAYER IMPLICATIONS None. ## 7. APPLICATION-LAYER IMPLICATIONS None. ## 8. FEEDBACK LOOP DISCOVERIES None. ## 9. UNRESOLVED GAPS + MISSING LAYERS - **Complete Absence of Architectural Content:** This file provides zero architectural intelligence. It cannot be used for topology generat
- support: 6 statements across 6 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `.../session_distillations_readme_extraction_analysis.md#r4`
  - `..._2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...n_debrief_2025_08_23_16_57_30_extraction_analysis.md#r1`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...ring_plan_checklist_arpc_v1_6_extraction_analysis.md#r3`
  - `...ware_development_deployment_6_extraction_analysis.md#r4`

### Filesystem Governance Layer:** Blocked until ADR-047 is locked (which is blocked by ADR-048).
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Architectural Significance**: A single stray `)` character in LivePanel caused complete UI failure — indicates no validation layer exists between panel code and runtime execution
- support: 11 statements across 5 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`

### No automation reduction included and no "NO AUTOMATION REDUCTION FOUND" statement | Contract violation — block treated as incomplete
- support: 9 statements across 5 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...ChatGTP_Project_Primer/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`
  - `...ve_06_foundational_control_contracts_extraction_analysis.md`
  - `contracts/CIS_Automation_Reduction_Contract_v1.md`

### Conflict panel | View/register/resolve conflicts | Not implemented | /api/conflicts + dashboard
- support: 9 statements across 5 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Review is the Next Dependency**: `cis_review.py` is referenced as the next step but does not exist yet.
- support: 8 statements across 5 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### The `route_task.py` routing layer was described architecturally — it queries the model registry to decide which tier handles a given task — but does not exist as code.
- support: 8 statements across 5 document(s)
- nearest queue item 8 is only sim 0.43 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...tion/functional_intents/all_insights_extraction_analysis.md`

### Intelligence Layer as Critical Missing Piece**: The system is at a hard boundary where setup is complete but intelligence is absent.
- support: 7 statements across 5 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `...42767492025744_x_07_knowledge_stream_extraction_analysis.md`
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### Gap:** Projects exist but are not connected to tasks, schedule, DAM, knowledge, or
- support: 7 statements across 5 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Session Close Input Validation**: focus, completed, next_steps are REQUIRED — returns 400 if missing
- support: 7 statements across 5 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`
  - `...xtraction/functional_intents/session_extraction_analysis.md`

### Missing Merge Stage**: OCR + visual extraction → structured synthesis → normalized record is missing, causing fragmented outputs and inconsistent record quality.
- support: 7 statements across 5 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### Session Archive Storage**: Resolved session storage format undefined; handoff persistence rules incomplete
- support: 7 statements across 5 document(s)
- nearest queue item 15 is only sim 0.42 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### The fourth layer (execution bridge) was previously implicit and is now explicitly recognized as missing.
- support: 6 statements across 5 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...nd_offs_cis_handoff_current_position_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Gap**: No validation that one model's output is valid input for next model
- support: 6 statements across 5 document(s)
- nearest queue item 5 is only sim 0.25 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### CIS Live session #020 remains unresolved — flagged in last handoff, not addressed this session, must be resolved before next session closes
- support: 6 statements across 5 document(s)
- nearest queue item 2 is only sim 0.42 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-28_0553.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### ADR candidate 4 — Notes field definition The Notes field in session close is defined with specific qualifying criteria: pending decisions, warnings, gotchas, partially built work, deferred context.
- support: 6 statements across 5 document(s)
- nearest queue item 22 is only sim 0.37 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `CIS_Creative_Intelligence_System_v1/Phase_PD/ADRs.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_012.md`

### Unresolved Application Surfaces: Dashboard Integration.** The dashboard integration is described but not specified.
- support: 6 statements across 5 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Before**: ADR-001 through ADR-020 existed; ADR-021 through ADR-026 were attempted but failed silently
- support: 6 statements across 5 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Architectural Significance**: Unresolved sessions create cognitive fragmentation and architectural drift; resolution became an operational governance requirement, not optional cleanup
- support: 6 statements across 5 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### Human as API Layer**: The most significant architectural gap is that humans are currently acting as the integration layer between AI output and system forms.
- support: 6 statements across 5 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...intents/archive_02_next_build_target_extraction_analysis.md`
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`

### Write missing Phase 0 contracts — source manifest, processing profile, review states Build cis_spine_intake.py Ingest first spine — Blender documentation Install PySceneDetect and test against a video — now segments have a spine to map to Write ADR-033 — segmentation policy locked after spine and Py
- support: 6 statements across 5 document(s)
- nearest queue item 17 is only sim 0.46 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### assert res24[0] == FunctionDefinition( NoneToken(), name=String('func'), parameters=(), body=CodeBlock( Declaration( Variable(Symbol('a'), type=FloatType( String('float32'), nbits=Integer(32), nmant=Integer(23), nexp=Integer(8) ) ) ), Declaration( Variable(Symbol('c1'), type=Type(String('bool')) ) )
- support: 6 statements across 5 document(s)
- nearest queue item 6 is only sim 0.21 — treat as NEW
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r0`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r1`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r4`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r5`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r6`

### Build Impact:** Deferred but recognized as critical; refactoring into component files is a prerequisite for stability
- support: 5 statements across 5 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...onal_intents/x_10_application_stream_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Missing**: No explicit state transition validation (e.g., cannot go from `discovered` to `active` without intermediate states)
- support: 5 statements across 5 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `.../extraction/functional_intents/state_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `...extraction/functional_intents/collab_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Gap**: No validation for field content — empty strings may be accepted
- support: 5 statements across 5 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: No CHECK constraint or trigger enforcing valid status transitions
- support: 5 statements across 5 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...raction/functional_intents/decisions_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Handoff File Overwrite**: The handoff file is overwritten on each session close, creating a risk of data loss if the close sequence fails silently.
- support: 5 statements across 5 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Missing Validation Layer: Memory Validation**: The rules for validating the structure and content of the memory file are not fully defined.
- support: 5 statements across 5 document(s)
- nearest queue item 17 is only sim 0.37 — treat as NEW
  - `...85_2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### Knowledge record gap**: The knowledge record in /mnt/projects/cis/knowledge/records/ does not contain infrastructure documentation
- support: 5 statements across 5 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### **7. Architecture Gaps as Unresolved Layers** - Significant gaps exist in: - Runtime bridges (encapsulation to security, module to deployment, DI to object creation) - Undefined objects (encapsulation boundary, module contract, DI container) - Unstable schemas (encapsulation, module, DI, singleton, 
- support: 5 statements across 5 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `...lopment_system_architecture_7_extraction_analysis.md#r1`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Unresolved Orchestration: Multi-Model Output Reconciliation
- support: 5 statements across 5 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...s/cis_pre_development_system_chatgtp_extraction_analysis.md`

### Dashboard expansion** - blocked by monolith; requires modularization ADR
- support: 5 statements across 5 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Queue Execution Validation**: verify_contract execution operational but patch incomplete
- support: 5 statements across 5 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Runtime Impact**: L2 verification silently fails or produces incomplete results for large contracts.
- support: 5 statements across 5 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### ADR-048 Phase 3 is intentionally deferred because the ingest/draft pipeline boundary must be preserved.
- support: 5 statements across 5 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Governance Layer**: Cannot enforce policies without authentication/authorization
- support: 5 statements across 5 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...traction/functional_intents/pipeline_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### push_cis_live() exists but has no integration point**: This function was created without a corresponding application update cycle to wire it into, indicating a gap between function development and system integration.
- support: 11 statements across 4 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...de_chat_transcripts/2026-04-20_Resuming creative VM work.md`
  - `...unctional_intents/cis_live_handoff_1_extraction_analysis.md`

### Job status polling missing | Needed after queue refactor | ADR-045 dashboard polling
- support: 8 statements across 4 document(s)
- nearest queue item 10 is only sim 0.34 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...s/ChatGTP_Project_Primer/11_TRANSITIONAL_IMPLEMENTATIONS.md`
  - `_archive/generated_script_artifacts/042926_Project_Primer.txt`

### Knowledge gap detection must exist before knowledge filling** — AI cannot fill gaps without identifying them first
- support: 8 statements across 4 document(s)
- nearest queue item 3 is only sim 0.33 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`
  - `...nctional_intents/x_00_operator_model_extraction_analysis.md`
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Summary of gaps: Schema files missing: source manifest, processing profile, review states, project object, segment Spec docs missing: everything — no contract has a written specification document
- support: 8 statements across 4 document(s)
- nearest queue item 13 is only sim 0.42 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### files_written polymorphism is unstable**: Workaround exists but formal fix deferred to ADR-047 - manifest structure has known instability.
- support: 8 statements across 4 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...ts/ChatGTP_Project_Primer/archive/10_OPERATIONAL_REALITY.md`

### Missing `description` field causes silent failure — no error returned, no record created.
- support: 7 statements across 4 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Missing Automation**: The entire automation layer is currently missing - no scripts, no tools, no interfaces exist for the defined pipeline.
- support: 7 statements across 4 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...traction/functional_intents/pipeline_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Multi-Agent Orchestration**: Blocked by agent execution layer; cannot coordinate without agent roles and protocols
- support: 7 statements across 4 document(s)
- nearest queue item 21 is only sim 0.55 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...lligence_routing_model_orchestration_extraction_analysis.md`

### 3. **Governance-Implementation Divergence**: Governance documents had become more mature than the implementation they govern. This creates ceremonial governance risk — contracts describing ideal states rather than actual operational behavior. Previously, governance maturity was assumed to indicate i
- support: 7 statements across 4 document(s)
- nearest queue item 21 is only sim 0.30 — treat as NEW
  - `...ayer_pivot_and_pd5_governance_extraction_analysis.md#r2`
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Architectural Significance**: Previously implicit risk now explicitly tracked in 07; distinct from execution ownership gap and intake ownership gap
- support: 6 statements across 4 document(s)
- nearest queue item 21 is only sim 0.34 — treat as NEW
  - `.../2026-04-30_primer_stabilization_and_intake_architecture.md`
  - `...26-05-02_constitutional_memory_governance_primer_rewrite.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Validation not implemented** → Bad records pass through → Knowledge layer contaminated
- support: 6 statements across 4 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...onical_build_sequence_plain_language_extraction_analysis.md`

### State Taxonomy Gap Identified**: The current status vocabulary (PRE-DRAFT / OPERATIONAL / LOCKED / NOT YET BUILT) is insufficient for hierarchical implementation state expression.
- support: 6 statements across 4 document(s)
- nearest queue item 5 is only sim 0.41 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

### Gap**: No automated pipeline exists to trigger extraction when a session completes
- support: 6 statements across 4 document(s)
- nearest queue item 8 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Also need to check — ADR-008 and ADR-009 exist but there's no ADR-008 gap issue since the DB shows them both present.
- support: 6 statements across 4 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### The system has multiple unresolved ADRs** — ADR-047 (manifest directory) pending.
- support: 6 statements across 4 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `cis_handoffs/CIS_Handoff_2026-05-02_0558_CORRECTED.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### The session then encountered a chain of failures in the session close process — duplicate DB entries, a missing Path import, multiple failed close attempts — before the session close finally completed cleanly.
- support: 6 statements across 4 document(s)
- nearest queue item 8 is only sim 0.45 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Intel Sidebar Tab Wiring**: `local`/`remote`/`agent` tabs are not wired to any data source.
- support: 5 statements across 4 document(s)
- nearest queue item 10 is only sim 0.35 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Content Validation**: No validation that written content is valid markdown or complete.
- support: 5 statements across 4 document(s)
- nearest queue item 6 is only sim 0.32 — treat as NEW
  - `.../functional_intents/primer_update_v3_extraction_analysis.md`
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`
  - `...unctional_intents/ingest_extractions_extraction_analysis.md`

### Runtime Manifest Validation** — No validation layer for runtime manifest operations
- support: 5 statements across 4 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`

### Defines the total map of layers and where execution fits structurally, including the critical clarification that the execution layer exists between intelligence and application.
- support: 5 statements across 4 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...cyBuildFiles/_CIS_The pattern across the CIS docs.md:26`
  - `...em_LegacyBuildFiles/_CIS_The pattern across the CIS docs.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...yBuildFiles/_CIS_The pattern across the CIS docs.md:219`

### Slot 3 registration intentionally deferred — Qwen3.6-27B is a stronger architectural fit for CIS multimodal routing needs but requires real performance comparison before committing
- support: 5 statements across 4 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-27_2152.md`
  - `cis_v1_vault/Phase_PD/CIS_Handoff_2026-04-27_2152.md`

### Gap**: No document exists that makes explicit how all other docs relate and how changes propagate.
- support: 5 statements across 4 document(s)
- nearest queue item 1 is only sim 0.43 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Human Review**: Required when validation fails, ambiguity unresolved, retries exhausted
- support: 5 statements across 4 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...887271442881_x_cis_critical_addition_extraction_analysis.md`
  - `..._legacybuildfiles_x_cis_workbench_v1_extraction_analysis.md`
  - `...s/cis_legacybuildfiles_consolidation_extraction_analysis.md`
  - `...s_cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Architectural Significance**: vLLM Slot 1 requires manual start each session; port pre-check fixed but daemonization incomplete
- support: 5 statements across 4 document(s)
- nearest queue item 14 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`

### Validation Rules**: Missing fields, hallucination, narrative drift, incorrect tagging, missing uncertainty = FAIL
- support: 5 statements across 4 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...s/cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Validation Gates → Execution**: Cannot enforce execution without validation rules
- support: 5 statements across 4 document(s)
- nearest queue item 13 is only sim 0.40 — treat as NEW
  - `...chat_2026_04_005_extraction_analysis_extraction_analysis.md`
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### The Execution Layer is the missing foundational layer that makes everything else real.**
- support: 5 statements across 4 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...hoosing an AI platform for professional project guidance.md`
  - `...ntents/phase_0_5_replan_orchestrator_extraction_analysis.md`
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### It identifies the 15 SESSION_INSIGHT_RECORDs as deferred backlog, not implemented.** They remain identified/mapped/deferred, awaiting execution layer stability.
- support: 5 statements across 4 document(s)
- nearest queue item 15 is only sim 0.47 — treat as NEW
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`
  - `...rchChatsProjectsCodeCustomizeDesignMoreRecentsHidePhase.txt`

### Implication:** Knowledge layer must support gap-driven retrieval, not just query-driven retrieval
- support: 5 statements across 4 document(s)
- nearest queue item 1 is only sim 0.47 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Gap**: Knowledge object schema is not fully defined; it will emerge from drive audit.
- support: 5 statements across 4 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Governance Layer**: Blocked by undefined state management and application layer
- support: 5 statements across 4 document(s)
- nearest queue item 21 is only sim 0.52 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Dependency Impact**: ADR-044 (operator abstraction), ADR-045 (execution ownership - CLOSED), ADR-048 (intake ownership - Phase 1/2 COMPLETE, Phase 3 DEFERRED)
- support: 5 statements across 4 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### ADR-048 must be locked before any new intake work begins.** ADR-045 closure makes this the sole remaining gap.
- support: 5 statements across 4 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### The model registry work to make them functional was deferred to ADR-024/025, which was still not implemented at this point.
- support: 5 statements across 4 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Everything else that was supposed to be a contract document from the roadmap — source manifest, processing profile, review states — does not exist as a file on disk.
- support: 5 statements across 4 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### Verification is an ongoing process with explicit metrics.** 568 verifications run, 41 unresolved FAILs.
- support: 5 statements across 4 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0413_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### This represents a significant knowledge gap that may contain architectural decisions, constraints, or requirements.
- support: 5 statements across 4 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Review this proposal against the locked ADRs and identify gaps, risks, and missing dependencies.
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...is_predev_infrastructure_plan_claude_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `_archive/orientation_backups_20260430/09_GOVERNANCE_STATE.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Missing Manifest**: Blocks preprocessing with exit code 1
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...on/functional_intents/cis_preprocess_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`

### Missing Validation Layers**: Kernel validation (domain-agnostic), configuration validation (configuration loading).
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...nts/runtime_implementation_contracts_extraction_analysis.md`

### None implemented**: No validation that project concept is coherent or non-contradictory
- support: 4 statements across 4 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...traction/functional_intents/projects_extraction_analysis.md`

### Current State**: 0 manifests produced, 0 verifications run, 0 unresolved FAILs
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...traction/functional_intents/pipeline_extraction_analysis.md`
  - `...xtraction/functional_intents/session_extraction_analysis.md`
  - `CIS_CONFLICT_REGISTER.md`

### This is not a minor configuration issue—it is a fundamental architectural gap that must be resolved before the system can operate as designed.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...buildfiles_x_cis_reinforcement_model_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...orm Chat/vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md`

### Missing Runtime Bridges**: No explicit runtime bridges exist for workspace switching, node tree compilation, material compilation, world compilation, ViewLayer evaluation, or brush initialization.
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nctional_intents/cis_handoff_phase_d_extraction_analysis.md`
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### The system has no validation layers**: Input validation, response validation, and format validation are minimal or absent.
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `.../cis_canonical_build_sequence_extraction_analysis.md:99`
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...ion/functional_intents/collab_rounds_extraction_analysis.md`
  - `...lender_2_80_fundamentals_transcripts_extraction_analysis.md`

### Dependency Impact**: Creates a dependency on a session-project bridge that does not exist in the current architecture.
- support: 4 statements across 4 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Conflict Resolution Transition**: Unresolved conflicts → logged to CIS_CONFLICT_REGISTER.md → session close allowed.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `HANDOFF_SCHEMA.md`

### L2 Context Constraint Validation** — No validation for files exceeding context limit
- support: 4 statements across 4 document(s)
- nearest queue item 18 is only sim 0.27 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Missing Runtime Bridge: Memory-to-Documentation Fallback
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### But the canonical relationship between this folder, Obsidian vault, knowledge records, and ADR/reorientation updates remains unresolved.
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Gap:** Interface must move material toward structured knowledge but validation is not implemented.
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Unresolved Orchestration**: The orchestration between `cis_intake.py` and the downstream pipeline steps (classify, preprocess, etc.) is not yet defined.
- support: 4 statements across 4 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Unresolved Orchestration: Memory as Orchestrator**: The role of the memory in orchestrating complex, multi-step workflows is unclear.
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...nts/runtime_implementation_contracts_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### This analysis is what triggered the recognition in subsequent sessions that session transcript extraction is the missing capability — the "session end hook" Karpathy describes is exactly what the current extraction work is building.
- support: 4 statements across 4 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Dashboard HTML refactor | Deferred to dedicated session | Not scheduled
- support: 4 statements across 4 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Dependency Impact**: Blocked until ADR-045 fully closed; no implementation allowed
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...P_Project_Primer/_backups/20260502_0047/01_CURRENT_STATE.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### `system says success → user asks to verify → command output checked → incomplete visibility rejected → verification method corrected`
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:195`
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:365`
  - `Hermes Agent Full Documentation.md:9365`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### The most significant architectural realization is that the **Application Layer is a dependent surface layer** that cannot function without all underlying layers operational. The application does not create, generate, or replace any system capability; it only coordinates and exposes. This fundamental
- support: 4 statements across 4 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...91549056_x_10_application_stream_extraction_analysis.md`
  - `...is_workflow_execution_spec_v1_extraction_analysis.md#r3`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### The second direction change was the decision to defer video entirely from Phase 0. Rather than partially implement video support with a known-flawed segmentation method, the session concluded that video is Phase 1 work and Phase 0 should exit cleanly on static images only. This was the correct call.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...aec072e4:CIS phase 1 intelligence extraction handoff#r6`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_003.md:213`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_003.md`

### ADR-048.md | LOCKED | Staged Draft Intake Layer — Phase 1 + Phase 2 complete; Phase 3 deferred
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._transcripts/ChatGTP_Project_Primer/02_NEXT_BUILD_TARGET.md`
  - `..._transcripts/ChatGTP_Project_Primer/04_ACTIVE_COMPONENTS.md`
  - `...t_transcripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md`
  - `...transcripts/ChatGTP_Project_Primer/Current State Updated.md`

### Tier 7: BLOCKED (placeholder per build plan: "Do not design implementation until Tier 6 is verified stable")
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md:79`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md`
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md:9`

### Lifecycle**: Staged → Approved/Rejected/Superseded → Committed (Phase 3 deferred)
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### The prompt version tracking gap was identified and explicitly deferred as lower priority. It was not added to the task list or the next steps.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...-24_CIS phase 1 intelligence extraction handoff.md:1062`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Gap**: No defined permissions, prohibited actions, approval gates, log requirements, failure behavior
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.45 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Resolve is fully working. Session #008 shows RESOLVED in green, solution text displayed, decided by and date confirmed. The full flow is proven end to end.
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...pts/2026-04-22_Model registry API implementation.md:512`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:393`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:466`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:467`

### * input * process * output * validation * failure rules * state change
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_009_extraction_analysis.md:575`
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:1504`
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:3016`
  - `...uence/3 Platform Chat/CIS_Pivot_Chain of Thought.md:527`

### **Second reason it wouldn't have hard-stopped anyway:** `hard_stop_enabled: bool = False` by default. Out of the box this guardrail only *warns* — it never halts. The `[BLOCKED: ...4 times]` you saw on `search_files` was the warn/block path on the idempotent-no-progress counter, which does block at 
- support: 4 statements across 4 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...b662dad0751:Loop-breaker block-contract schema draft#r1`
  - `PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md:25`
  - `PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md:28`
  - `PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md:30`

### ## Discovery 1: Guardrail as Single Source of Truth (SSOT) - **Architectural Significance**: Guardrail is NOT a safety net—it is the authoritative reference the AI must consult before ANY action - **Affected Layers**: Governance (02_GUARDRAIL), Execution (03_ENGINE), Application (04_INTERFACE) - **D
- support: 4 statements across 4 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `..._are_these_files_in_guardrail_extraction_analysis.md#r1`
  - `..._x_cis_discovery_workbench_v1_extraction_analysis.md#r1`
  - `...ld you give me a paragraph explanation for eac....md#r1`
  - `hermes_session/v4pro/session_20260825_170835_7fee96c8/10.0`

### Deployment has a gap**: ensure_models_table is not wired into ensure_tables(), meaning fresh DB deployments will fail.
- support: 11 statements across 3 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### The Resolve button form was never built.** The backend route existed but the frontend form was missing — a feature gap from the monolith refactor that blocked session hygiene.
- support: 8 statements across 3 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### No Reliable Fetch Target Exists**: Auto-fetch feature permanently deferred; no development resources should be allocated to it.
- support: 7 statements across 3 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:12`
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...reative_Intelligence_System_v1/memory_additions_20260420.md`

### Gap Retrieval Loop**: Gaps retrieved → resolution patterns identified → gap resolution improved → faster resolution
- support: 7 statements across 3 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Session Review**: Live sessions must be resolved before close — unresolved sessions block next build
- support: 7 statements across 3 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Verification Pipeline Incomplete**: Despite 5 manifests produced and 0 unresolved FAILs, verification remains manual terminal-only — no automated verification pipeline exists.
- support: 7 statements across 3 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### Missing relationship map**: No single doc governs doc hierarchy, change propagation, or archive reality updates.
- support: 6 statements across 3 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...nd_offs_cis_handoff_current_position_extraction_analysis.md`

### Loop:** Gap identified → ADR proposed → ADR locked → Gap resolved → Knowledge base updated → Future reviews reference resolved gap
- support: 6 statements across 3 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Phase 0 video work is entirely deferred** — No video preprocessing code will be written in Phase 0.
- support: 6 statements across 3 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_001_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Manifest Path Resolution**: runtime/manifests/ origin unresolved → cannot write there → cannot resolve without writing
- support: 5 statements across 3 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### Primary theme: Pre-intelligence capture infrastructure, session continuity, project-aware intake, dashboard UX, and discovery of missing data-capture gates before intelligence extraction.
- support: 5 statements across 3 document(s)
- nearest queue item 15 is only sim 0.39 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Conflict Logging → Resolution**: 3 conflicts resolved, 1 deferred — governance loop exists but is human-mediated
- support: 5 statements across 3 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### The intake panel feedback gap — no visual response after clicking INTAKE — was identified but not fixed this session.
- support: 5 statements across 3 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### This also closes a gap that already exists: the Intel sidebar has LOCAL, REMOTE, AGENT tabs listing models, but those lists are currently decorative — not wired to anything functional.
- support: 5 statements across 3 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Phase 0-to-Phase 1 Bridge**: Missing contracts identified but not blocking; must be resolved before Phase 1 exits
- support: 5 statements across 3 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Video Preprocessing↔Knowledge Formation**: Video pipeline declared but not implemented; ffmpeg, Whisper, vision extraction not operational
- support: 5 statements across 3 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Dependency Impact**: Phase 3 (commit) is deferred - creates incomplete pipeline
- support: 5 statements across 3 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### Architectural Significance**: Two manifest directories exist: /mnt/projects/cis/logs/manifests/ (canonical) and runtime/manifests/ (status unresolved per ADR-047).
- support: 5 statements across 3 document(s)
- nearest queue item 5 is only sim 0.32 — treat as NEW
  - `...extraction/functional_intents/config_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/13_RUNTIME_TOPOLOGY.md`

### Draft panel | View/Edit/Approve/Reject/Supersede drafts | Not implemented | ADR-048 Phase 1
- support: 5 statements across 3 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Register Slot 1 and Slot 2 in models table (ADR-024/025) — Slot 3 registration deferred
- support: 4 statements across 3 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-27_2152.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-28_0239.md`

### Config constants have been established (VERIFICATION_MANIFEST_DIR, RUNTIME_MANIFEST_DIR, SOURCE_MANIFEST_NAME), but runtime/manifests/ origin and status remain unresolved.
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### No validation at entry**: File type is inferred from extension only; no content validation; no integrity verification against source
- support: 4 statements across 3 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `...action/functional_intents/cis_intake_extraction_analysis.md`
  - `...raction/functional_intents/librarian_extraction_analysis.md`
  - `...unctional_intents/ingest_extractions_extraction_analysis.md`

### Filesystem canonicality is unresolved** — files_written polymorphism and runtime/manifests/ status create ambiguity about authoritative write paths.
- support: 4 statements across 3 document(s)
- nearest queue item 17 is only sim 0.35 — treat as NEW
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Description:** If state update fails after output generation, execution is incomplete.
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Gap:** No `runs` table in DB; no mechanism to log extraction runs
- support: 4 statements across 3 document(s)
- nearest queue item 13 is only sim 0.39 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Missing directories**: Script creates directories but doesn't validate parent paths
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...action/functional_intents/cis_intake_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### This is a major architectural correction. The file reveals that the missing layer is not more model capability. The missing layer is **capture, verification, and promotion infrastructure** that allows intelligence work to become trustworthy system knowledge.
- support: 4 statements across 3 document(s)
- nearest queue item 22 is only sim 0.35 — treat as NEW
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:564`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Operator Abstraction Layer (ADR-044)**: The human operator was acting as middleware between incomplete system layers.
- support: 4 statements across 3 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Now it is known to be filename-pattern based, requiring operator naming discipline and missing non-standard filenames.
- support: 4 statements across 3 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`

### Section 6 (Next Actions) depends solely on `build_plan_nodes WHERE status IN ('PENDING','IN_PROGRESS')` — empty when all nodes are COMPLETE/DEFERRED
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.55 — treat as NEW
  - `DEV-PIVOT-04_APPLICATION_ENFORCEMENT_SPEC.md`
  - `DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md`
  - `PROPOSAL_SESSION_TO_SPINE_WRITE_PATH.md`

### Session Close Fields**: Schema is defined (focus, completed, next steps, notes) but not enforced by runtime.
- support: 4 statements across 3 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Handoff Assembly → Downloadable Package**: Bridge proposed (cis_build_handoff_package.py) but not implemented
- support: 4 statements across 3 document(s)
- nearest queue item 8 is only sim 0.47 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...hat_transcripts/ChatGTP_Project_Primer/08_OPEN_QUESTIONS.md`

### Session Close:** No validation of duplicate sessions — allows multiple closes
- support: 4 statements across 3 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap Knowledge:** Identified gaps become knowledge artifacts for future reviews
- support: 4 statements across 3 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### ADR Numbering:** Sequential numbering with gap detection (ADR-008 out of sequence noted)
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Unresolved Orchestration: Session Initialization Orchestration
- support: 4 statements across 3 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Deferred work**: ADR-045, ADR-046, PD.5 Steps 1-6, Frontend modularization all tracked.
- support: 4 statements across 3 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...intents/20260502_0047_05_adr_summary_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Phase 1 routing (route_task.py)**: Not started — blocked by Qwen weights and registry stability
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.48 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### Gap**: No governance for writing contract specification documents
- support: 4 statements across 3 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`

### Authority Source** | Architecture specs and ADR-derived rules; standalone contract missing
- support: 4 statements across 3 document(s)
- nearest queue item 21 is only sim 0.27 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Governance Classification is Architectural** — The six-state classification system (LOCKED, OPERATIONAL, TRANSITIONAL, PRE-DRAFT, PLANNED, DEFERRED) is not metadata—it is architectural topology.
- support: 4 statements across 3 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Schema Migration Gap**: No schema versioning or migration mechanism exists, despite having both inline and file-based schema definitions that could drift over time.
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...action/functional_intents/connection_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### No Content Validation**: The API performs no validation of extraction file content before ingestion; it trusts the external script entirely.
- support: 4 statements across 3 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`
  - `...ion/functional_intents/ingest_spines_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### Loop: extract → review → gap identification → prompt tuning → re-extract → improved quality.
- support: 4 statements across 3 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Primary Discovery: The Human-As-Transport-Layer Gap is the Primary Architectural Problem
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.23 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### CIS_LIVE Auto-fetch Permanently Deferred**: Major models (Claude, Gemini, ChatGPT) do not expose stable public share URLs suitable for programmatic fetch.
- support: 3 statements across 3 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...reative_Intelligence_System_v1/memory_additions_20260420.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### None implemented**: Only validation failure is missing title
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`
  - `...traction/functional_intents/projects_extraction_analysis.md`

### Dependency Impact**: Introduces unstable dependencies — components that appear to work but have unresolved underlying issues
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Discovery 6: Ingestion Pipeline Lacks Merge Stage (Critical Gap)
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...em_LegacyBuildFiles/_CIS_The pattern across the CIS docs.md`

### Gap:** No validation of file paths, command strings, or timeout values
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...raction/functional_intents/librarian_extraction_analysis.md`
  - `...xtraction/functional_intents/helpers_extraction_analysis.md`

### Field 5 Validation**: Currently shows incorrect data; validation layer missing
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.22 — treat as NEW
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### No Relationship Validation**: No validation that parent-child relationships are correct
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`
  - `...unctional_intents/ingest_extractions_extraction_analysis.md`

### The update path is: real behavior reveals a gap → architect documents the insight → this roadmap is versioned and updated → subsequent build steps reflect the correction.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### Video preprocessing in `cis_preprocess.py` — ffmpeg frame sampling plus Whisper transcription — was identified as the next build target but was not implemented.
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Fail**: Missing STATE.md, missing required streams, phase mismatch, alignment broken.
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Application development** — deferred until Phase 0–4 exit criteria are met; building the app before the runtime is premature regardless of how ready it feels
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Dependency Impact:** Without decision logging, the knowledge base for future projects is incomplete
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.33 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### This is a recognition that the current architecture has a missing layer that must be built before CIS can scale beyond human-mediated operation.
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `.../cis_predev_infrastructure_plan_docx_extraction_analysis.md`
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`

### Error Handling Gap**: Silent failures (log missing → return None) hide operational issues.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Errors: 400 (missing/invalid fields), 500 (database error)
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### Application Layer UI/UX**: Not defined; deferred to end-state
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### FAIL:** "FAIL: Consensus signal invalid — missing <marker>" or "FAIL: requires_eric_review is false"
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### This is a deterministic error, distinct from "section missing" (heading not
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`
  - `CIS_TIER_6_3_ORCHESTRATOR_KANBAN_INTEGRATION_DESIGN.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### API decisions endpoint requires description field — batch curl commands must include it or they fail silently
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Gap:** `load_json` and `save_json` raise exceptions directly, while `run_command` captures them
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...xtraction/functional_intents/helpers_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Gap**: Manifest structure is assumed but not formally defined
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Gap**: No batch processing for multiple transcripts
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Gap**: No defined translation layer between operator interface actions and runtime commands
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### If Intelligence is incomplete, Knowledge is incomplete, and Agents cannot operate.
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.48 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...ybuildfiles_x_06_intelligence_stream_extraction_analysis.md`

### Impact**: Specification documents may be incomplete or incorrect
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`

### Intake Validation**: No validation for staged content before approval
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Merge Validation** — No validation that merge produces coherent records
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.25 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...tents/1776042143355379182_x_03_state_extraction_analysis.md`

### Merge layer not implemented** → No draft knowledge_records → No validation → No review → No indexing → No retrieval
- support: 3 statements across 3 document(s)
- nearest queue item 7 is only sim 0.31 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`

### Missing Execution Specs**: Workbenches cannot operate without execution behavior defined
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### Missing state machine** → blocks all source processing
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...ents/cis_execution_layer_contract_v1_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_execution_layer_extraction_analysis.md`

### Segmentation Validation**: Not implemented — PySceneDetect not installed
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Missing Worker Layer**: The most critical gap is the absence of any worker implementation to actually execute jobs.
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...hoosing an AI platform for professional project guidance.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### This is a validation gap — no error surface for missing required fields.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...l_intents/1777410199041831732_readme_extraction_analysis.md`

### Check the runtime manifests folder — that's likely where the manifest template or spec lives:
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...4-24_CIS phase 1 intelligence extraction handoff.md:129`
  - `..._chat_transcripts/2026-04-17_Hand off evaluation.md:107`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Missing optional fields represented as `null` consistently (never omit a known field).
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `...l_intents/1777410199041831732_readme_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### Governance Layer**: Blocked on validation engine — cannot enforce contract without validation
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...lender_2_80_fundamentals_transcripts_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### This is a fundamental topology gap where AI-generated structured content cannot reach CIS canonical records without human mediation.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### States:** Open (identified but unresolved), Resolved (ADR proposed and locked)
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### The gap is not the concept — it's that the verification chain has only been applied to build artifacts, not to planning documents and decisions.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### This represents a **governance gap** in the storage layer that must be addressed for production reliability.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...tion/functional_intents/dedup_memory_extraction_analysis.md`
  - `...tional_intents/cis_slot1_healthcheck_extraction_analysis.md`

### Unresolved Application Surface: Session Management Interface
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Unresolved FAILs: 0 this session (41 shown is cumulative — no build actions taken)
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-01_0548.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`

### Claude responded: ADR-008 and ADR-010 are missing from the database — they were written in conversation but never actually logged with cis-log decision.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### This was flagged as a known design flaw from the previous session that needed to be fixed as the first task of the following session but had not been fixed yet. ________________
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...e_atlas/original_CISChats/CIS_Chat_2026-04_016.md:81#r2`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Governance Gaps**: The memory store has no access control, no audit trail, no validation, no deletion capability, and no lifecycle management.
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.39 — treat as NEW
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...tion/functional_intents/memory_store_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Architectural Significance:** The session close protocol has a fundamental gap — work performed after commit has no capture path to any endpoint (DB, ADRs, knowledge records, system log)
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ents/post_commit_addendum_2026_04_18_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Session → Context Gap → Memory Update → Session**: Context gaps trigger memory updates
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Knowledge Layer**: Blocked by institutional memory integration path (requires ADR-048 Phase 1)
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...al_intents/archive_08_open_questions_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Handoff File Validation**: No validation that handoff file is correctly formatted
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Missing Runtime Bridge**: There is no automated bridge between the CIS Live session resolution and the handoff file generation.
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`

### Runtime Impact**: Session close captures deferred decisions, warnings, mid-thought work — not next steps.
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### Whether the runtime code (/mnt/projects/cis/runtime/) had a git repo initialized at the time of this session was explicitly flagged as uncertain — "if initialized — verify with git status." This uncertainty about whether the code was version-controlled is a significant gap that was never formally cl
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_014_extraction_analysis.md:383`
  - `...ession_insight_record_2026_04_17_002_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Unresolved Application Surface: Memory Search**: The application interface for searching the memory file is not defined.
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### The Slot 1 4096 token context limit means that L2 verification silently breaks for contracts exceeding ~300 lines.
- support: 3 statements across 3 document(s)
- nearest queue item 22 is only sim 0.35 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### The actual knowledge records table does not exist in this DB yet, which means `knowledge_records` is stored as files on disk (`record_001.json`) but has not been migrated into the SQLite DB as a table.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...at_transcripts/2026-04-23_Starting a new session.md:763`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Runtime Impact:** Bad outputs cannot silently contaminate the knowledge base.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...nal_CISChats/CIS_Canonical_Build_Sequence_Plain_Language.md`
  - `...nts/cis_plain_language_build_roadmap_extraction_analysis.md`
  - `...onical_build_sequence_plain_language_extraction_analysis.md`

### Knowledge does not exist as primary input layer**—it is generated through Intelligence processing
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...telligence_System_LegacyBuildFiles/X_01_SYSTEM_BLUEPRINT.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Agents blocked by lack of validated knowledge and workflow context.
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.46 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Knowledge Layer (Layer 5):** Blocked by Intelligence Layer completion
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.55 — treat as NEW
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### No Content Index**: Full-text search not implemented
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.45 — treat as NEW
  - `...l/extraction/functional_intents/logs_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Not implemented**: No mechanism to improve retrieval based on usage patterns.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.50 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Index must be complete for reliable retrieval | Incomplete index degrades retrieval
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.52 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`

### Architectural Significance**: Knowledge Layer does NOT exist at system start.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`
  - `...nce_System_LegacyBuildFiles/X_01_SYSTEM_BLUEPRINT.md:86`
  - `...telligence_System_LegacyBuildFiles/X_01_SYSTEM_BLUEPRINT.md`

### Knowledge record storage** — naming convention defined but storage hierarchy incomplete
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### - "Embedded governance" is a Build Plan v2 philosophical target. The creator should eventually experience trust and continuity — not visible constitutional machinery. Governance should become ambient, not explicit.
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.34 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...2_constitutional_memory_governance_primer_rewrite.md:17`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Not implemented**: No mechanisms to stabilize or validate knowledge
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `...raction/functional_intents/decisions_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Knowledge retrieval validation**: No validation for retrieval queries
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.46 — treat as NEW
  - `.../functional_intents/mnt_projects_cis_extraction_analysis.md`
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### No retrieval feedback | Capture retrieval not measured | **MISSING**
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.45 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### The knowledge records are the most important gap.** Those are the actual output of the system.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### Missing**: No mechanism to communicate *why* failure occurred to pipeline orchestrator beyond log
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...onal_intents/x_cis_critical_addition_extraction_analysis.md`

### Build Impact:** Delays full automation; requires staged draft intake (ADR-048 pre-draft) as missing layer
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_05_02_0558_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### Effect:** Reduces hallucination by forcing gap identification before knowledge provision
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.22 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `..._legacybuildfiles_x_cis_workbench_v1_extraction_analysis.md`

### The Session Close Protocol emerged to govern that gap until future orchestrator behavior can generate and validate session close content automatically.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`

### Retry → Escalation bridge**: Logic described but not implemented
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Governance Gap**: While verification creates governance records, there's no automated governance enforcement, no escalation, no override mechanism, and no human sign-off requirement.
- support: 3 statements across 3 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### Unresolved Orchestration: The Merge Step**: The document says the Merge step is "REQUIRED" but does not define the orchestration logic.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Missing Validation Layer**: The validation layer for contract actions is non-functional.
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### No hallucination controls**: No validation of extraction outputs beyond human review
- support: 3 statements across 3 document(s)
- nearest queue item 22 is only sim 0.22 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### Gap**: Specific interface panels and their behavior are not defined.
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.31 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Governance State Panel** — Display LOCKED, OPERATIONAL, TRANSITIONAL, PRE-DRAFT, PLANNED, DEFERRED status
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### 2 | Missing contract specs or explicit deferral reasons | Governance completeness
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `...nts/runtime_implementation_contracts_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Architectural Significance:** A result is invalid if: required fields missing, unsupported claims present, schema broken, uncertainty not expressed.
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.37 — treat as NEW
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### The actual gap is a `manifest_v1.json` schema file in `runtime/schemas/` to match the other schemas written last session.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### HARD_FAIL | Required output missing, schema invalid, forbidden strings detected | Cannot proceed.
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...42767492025744_x_07_knowledge_stream_extraction_analysis.md`
  - `contracts/CIS_Execution_Layer_Contract_v1.md`

### Missing DB file**: Migration exits with error code 2
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### `ensure_tables()`** — Tasks table must exist; this function creates it if missing.
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### No Schema Validation**: No validation of memory record schema
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...on/functional_intents/update_prefill_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### Storage Implications**: Logged to database; unresolved sessions block next build
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Storage Implications**: Missing record blocks verification same as missing Completion Manifest
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.34 — treat as NEW
  - `...ChatGTP_Project_Primer/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`

### Verification Validation**: No validation that proof-of-work is genuine
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.23 — treat as NEW
  - `...857838508_x_11_sound_stream_expanded_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### File Not Found → Re-execute Write → Re-verify**: Corrects missing files.
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.37 — treat as NEW
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify_semantic.py`

### Gap Chunking**: Each gap is a chunk with fields: subsystem, gap_description, target_resolution
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### This is explicitly classified as an architectural gap, not a UX problem.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### Every gap identified references a specific architectural principle
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.27 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Architectural Significance:** Multiple close attempts created duplicate session rows, encountered a missing `Path` import, and exposed possible Git push/handoff completion uncertainty.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.43 — treat as NEW
  - `...chat_2026_04_006_extraction_analysis_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### Contract-first discipline requires three missing Phase 0 documents before the spine ingestion pipeline can be built: source manifest, processing profile, and review states.
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.42 — treat as NEW
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Check the runtime manifests folder — that's likely where the manifest template or spec lives: bashls /mnt/projects/cis/runtime/manifests/ The "missing Phase 0 contracts" task from the handoff may mean the spec documents describing the rules — not the manifests themselves, which already exist.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.43 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`

### Commit validation**: Phase 3 deferred - no commit validation layer
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Two active entries exist (ADR auto-increment reset, CIS Live rounds session dropdown bug), both DEFERRED/LOW.
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`
  - `...transcripts/ChatGTP_Project_Primer/Current State Updated.md`

### Escalation triggers: missing required fields, output too short, forbidden patterns, low confidence, failed JSON
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...lligence_routing_model_orchestration_extraction_analysis.md`

### Pipeline stages blocked by state machine**: Cannot implement pipeline stages without state machine
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...intents/cis_source_manifest_contract_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### The selectors in v2 (`textarea[placeholder*='Send a message']`, `[data-message-author-role="assistant"]`, etc.) are best guesses from the v1 script.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`
  - `claude_chat_transcripts/captures/README.md`

### Cause**: Incomplete extraction, missing provenance, accuracy issues
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.41 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### Provenance chain | No validation on re-segmentation | Broken links
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### API Key Missing: Initial → Fetching → Validating → Building Prompt → Calling Prime → Return 500
- support: 3 statements across 3 document(s)
- nearest queue item 10 is only sim 0.34 — treat as NEW
  - `...ction/functional_intents/idea_drafts_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### 401 Unauthorized**: Returned when API key is missing or invalid for remote requests
- support: 3 statements across 3 document(s)
- nearest queue item 10 is only sim 0.27 — treat as NEW
  - `...ction/functional_intents/gpt_gateway_extraction_analysis.md`
  - `...el/extraction/functional_intents/app_extraction_analysis.md`
  - `...el/extraction/functional_intents/gpt_extraction_analysis.md`

### This is: 👉 **CAPABILITY LAYER + EXECUTION ENVIRONMENT DEFINITION** It defines: - how tools exist **inside the system** - how capability is made **usable** --- ## 🔧 NORMALIZED ADDITIONS (Core Tool Stream integrated) ### 🔹 **CAPABILITY SYSTEM (NEW COMPONENT TYPE)** **Tool Stream** - defines **how capa
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.34 — treat as NEW
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:1128`
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:1191`
  - `chatgpt_export/69dd351d-9d94-83ea-9c60-a97bf3e2e2c4#r1`

### As I remmember the decision was made to create an entirely new db. the schema should be in the project file documentation.
- support: 3 statements across 3 document(s)
- nearest queue item 10 is only sim 0.31 — treat as NEW
  - `...4-24_CIS phase 1 intelligence extraction handoff.md:251`
  - `...at_transcripts/2026-04-23_Starting a new session.md:614`
  - `...ea-2b7ec4d6d90c:Project Design and Database Integration`

### Architectural Significance**: The Resolve button in the Live panel toggled state but the form (solution textarea, decided by field, confirm button) was never implemented — backend route existed but frontend form was always missing
- support: 6 statements across 2 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### Session Resolution**: Added as mandatory governance step; resolve form implementation identified as gap
- support: 6 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Architectural Significance**: Four defined states (OPEN, DEFERRED, RESOLVED, SUPERSEDED) with implied transitions
- support: 5 statements across 2 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Missing execution-bridge layer**: Previously assumed workflow stream was sufficient; now identified as missing enforceable runtime actions, pass/fail conditions, review states, operational responsibilities
- support: 5 statements across 2 document(s)
- nearest queue item 12 is only sim 0.48 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...intents/cis_handoff_current_position_extraction_analysis.md`

### No project → capture feedback | Project context not used to guide capture | **MISSING**
- support: 5 statements across 2 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### cis_download_watcher.py | Watch for downloads | Not implemented | Automated download management
- support: 5 statements across 2 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...s/20260505_0058_02_next_build_target_extraction_analysis.md`

### Current**: Execution layer gap made explicit; operational direction is multi-pass extraction
- support: 5 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Execution Queue Ownership Layer** (ADR-045 direction): Not yet built, but architecturally identified as required layer between operator layer and execution layer.
- support: 5 statements across 2 document(s)
- nearest queue item 21 is only sim 0.25 — treat as NEW
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Gap:** Intake creates structured entries but routing to Project Pipeline is not implemented.
- support: 5 statements across 2 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Session insights**: Captured via cis-log insight subcommand (not implemented)
- support: 5 statements across 2 document(s)
- nearest queue item 15 is only sim 0.46 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`

### Not defined in this session** — segmentation policy deferred to ADR-033
- support: 5 statements across 2 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`

### Handoff checklist failure → Identify missing items → Complete items → Re-validate
- support: 5 statements across 2 document(s)
- nearest queue item 5 is only sim 0.25 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...raction/functional_intents/x_control_extraction_analysis.md`

### Session Start**: Blocked if handoff folder is missing or `cis-start` command is not installed.
- support: 5 statements across 2 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### The index file — a `KNOWLEDGE_INDEX.md` that maps all records by domain, sub-domain, and spine position — was identified as missing and important but not created.
- support: 5 statements across 2 document(s)
- nearest queue item 17 is only sim 0.51 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Temperature=0.0 fix | Opus 4.7 Migration | Migration was independent | Migration blocked by `cis_verify_semantic.py` parameter
- support: 5 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...TIONS/2026-04-29_operator_layer_pivot_and_pd5_governance.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Distillations are chunked by schema: Session Focus, Key Decisions, Architectural Insights, Operational Changes, Risks Identified, Deferred Work, Next Actions.
- support: 5 statements across 2 document(s)
- nearest queue item 1 is only sim 0.36 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### The ADR panel sort/filter improvement (newest-first toggle, status filter buttons) was identified as useful, logged as a task in the dashboard, and explicitly deferred as not blocking build work.
- support: 5 statements across 2 document(s)
- nearest queue item 7 is only sim 0.31 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Queue ownership is prerequisite, not optional** - Previously assumed execution could proceed without centralized queue, now recognized as critical missing layer blocking all reliable execution
- support: 4 statements across 2 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Project must exist (if `project_id` is provided) before task creation — though not enforced at database level.
- support: 4 statements across 2 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### If workflow step cannot be executed consistently on real material → it is incomplete and must be refined
- support: 4 statements across 2 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Documentation Gap Pattern**: There is a systemic pattern where important infrastructure details are set up correctly in the moment but never formally documented.
- support: 4 statements across 2 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`

### The system has **no validation of capture types**, **no content moderation**, **no duplicate detection**, and **no quality scoring**.
- support: 4 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### Session → Insight display | Not implemented | Insights not visible at session start
- support: 4 statements across 2 document(s)
- nearest queue item 15 is only sim 0.43 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### Knowledge Module**: Not built — knowledge accumulation not implemented
- support: 4 statements across 2 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Knowledge capture is not implemented** — Resolved sessions do not yet feed into the knowledge base.
- support: 4 statements across 2 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### A formal governance layer is missing and must be created immediately.** The CIS_Primer_Update_Governance_Contract.md must exist and be locked before any further primer updates.
- support: 4 statements across 2 document(s)
- nearest queue item 5 is only sim 0.44 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...update_governance_contract_dicussion_extraction_analysis.md`

### Direct API routing to Claude/ChatGPT is deferred** - all model communication goes through Hermes Gateway.
- support: 4 statements across 2 document(s)
- nearest queue item 20 is only sim 0.48 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`
  - `PHASE_LOG.md`

### Sequencing Constraint**: ADR-043 must be verified (no contradictions, no undefined transitions, no missing authority boundaries, no impossible verification requirements) and frozen before any runtime implementation begins.
- support: 4 statements across 2 document(s)
- nearest queue item 22 is only sim 0.30 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Blocking**: cis_spine_intake.py, missing contract specification documents
- support: 4 statements across 2 document(s)
- nearest queue item 17 is only sim 0.42 — treat as NEW
  - `...egrated_vision_cis_core_architecture_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### First: qwen_vl_utils appeared to be missing but was actually installed — the problem was that #!/usr/bin/env python3 picked up the system Python instead of the gpu-test Python.
- support: 4 statements across 2 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Model registry → local/remote/agent tabs | Dynamic roster not wired to sidebar | HIGH — blocks intelligence connection
- support: 4 statements across 2 document(s)
- nearest queue item 15 is only sim 0.40 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### raise except ValueError as e: raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail=str(e) ) except Exception as e: logger.error(f"Error updating provider availability: {e}") raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update provider ava
- support: 4 statements across 2 document(s)
- nearest queue item 15 is only sim 0.21 — treat as NEW
  - `swa_project/social_work_ai/01_CORE/main.py#r0`
  - `swa_project/social_work_ai/01_CORE/main.py#r1`

### Session close → Post-commit work → Session close** — work done after close has no capture path, creating a circular gap
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.36 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`

### None** - No validation that source_type is correct
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `.../functional_intents/advisor_external_extraction_analysis.md`
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`

### System state visibility (users cannot easily tell if ComfyUI is running — identified gap)
- support: 3 statements across 2 document(s)
- nearest queue item 22 is only sim 0.23 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### Blocked by:** Nothing (can proceed in parallel with other setup)
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.42 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`

### FAIL Placeholder detected: "TODO" found at line 47 of /path/to/file
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### The cleanest solution is a # NOCHECK marker pattern, or simply: when running self-check, skip the forbidden strings check (the content is the list definition, not placeholder content).Check the lines flagged by self-checkCheck the lines flagged by self-checkThe forbidden strings are in the list defi
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.29 — treat as NEW
  - `...rchChatsProjectsCodeCustomizeDesignMoreRecentsHidePhase.txt`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### QR Code / Shareable URL Gap**: URL returned by push endpoint but not displayed in UI.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### The issue is likely a **currently attached device** that's blocking new snapshots — most commonly a USB device or PCI passthrough that was added after that snapshot was taken.
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`
  - `...anscripts/2026-04-21_Proxmox VM snapshot creation.md:37`

### This is a recurring failure mode — updating the reorientation doc keeps getting deferred and added to next steps, but next steps are what get deferred first when a session runs long.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Set `status = 'DEFERRED'` if a gap exists and Eric defers it.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md`

### Blocked By:** Phase E (Knowledge Foundation) not complete
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Fix CIS Live rounds form session dropdown (deferred, LOW severity)
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-05_0427.md`

### Mediate → form knowledge | DeepSeek processes mediated output | **NOT IMPLEMENTED**
- support: 3 statements across 2 document(s)
- nearest queue item 20 is only sim 0.29 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Execution layer does not exist** as unified, deterministic system—exists only as fragmented shell scripts and manual steps
- support: 3 statements across 2 document(s)
- nearest queue item 4 is only sim 0.27 — treat as NEW
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### Transitional Gap Naming**: Trust is enforced through explicit gap identification
- support: 3 statements across 2 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Draft rejection → (no path)**: Gap - no correction feedback to source
- support: 3 statements across 2 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0413_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### Exit codes: 0 = success, 1 = no files found, 2 = root directory missing
- support: 3 statements across 2 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `...action/functional_intents/cis_intake_extraction_analysis.md`
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### FAIL:** "FAIL: Implementation section missing" or "FAIL: no artifact evidence in Implementation section"
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.36 — treat as NEW
  - `...itutional_memory_governance_revision_extraction_analysis.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### Field 5 FAIL Count Loop**: Incorrect FAIL count → fix deferred → known issue → future fix → correct scope
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.47 — treat as NEW
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### Transitional Gap Identification**: If a reduction cannot be made, the builder must identify the gap and its target resolution.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Gap**: No retention policy for CIS_LIVE.md versions
- support: 3 statements across 2 document(s)
- nearest queue item 18 is only sim 0.41 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: No queue management logic (polling, priority sorting, worker assignment)
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### State Registry**: Required for proper hierarchical status expression, but explicitly deferred to build-plan reconstruction stage
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

### Mediation Gap**: The most significant architectural gap is the missing mediation automation — the Hermes agent must manually read script output and perform mediation.
- support: 3 statements across 2 document(s)
- nearest queue item 20 is only sim 0.44 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Missing Runtime Bridge: Application ↔ Runtime State Synchronization
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Slot 3 is DEFERRED**: Qwen3.6-35B-A3B-FP8 (42 shards, ~35GB) is downloaded at /mnt/models2/, but registration is blocked pending Qwen3.6-27B evaluation.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

### Placeholder check: No TODO, ..., or placeholder strings present in contract.
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`

### 1172: e('textarea', { placeholder:'Notes — pending decisions, warnings, deferred context (optional)', value:notes, onChange:ev=>setNotes(ev.target.value), style:taStyle(48), disabled:!!closeResult?.success })
- support: 3 statements across 2 document(s)
- nearest queue item 22 is only sim 0.20 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Any session that started without the addendum silently lost the post-commit work.
- support: 3 statements across 2 document(s)
- nearest queue item 14 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Status Vocabulary Separation**: Current coarse vocabulary (PRE-DRAFT / OPERATIONAL / LOCKED / NOT YET BUILT) must be separated into hierarchical implementation state (ADR overall vs.
- support: 3 statements across 2 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...traction/functional_intents/cis_live_extraction_analysis.md`
  - `CIS_Creative_Intelligence_System_v1/CIS_LIVE.md`

### After: vLLM zombie processes are a known issue with an identified root cause (missing port pre-check) and a planned fix (Step 3).
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0836_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-29_0836.md`

### Dependency Impact**: Creates a persistent gap in the session record — post-close work is invisible to future sessions
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.36 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Missing Runtime Bridge: Error Handling.** The session close sequence has no defined error handling.
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### The fix was built and deployed this session, but the fact that this gap existed undetected across multiple sessions is significant — it means the branch record system that CIS Live is supposed to provide had been non-functional from the start.
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Runtime Impact**: If any sync fails, session close is incomplete — no recovery path documented
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### The verification step gets triggered by Claude, not requested by you.** After any significant build action, Claude produces the manifest and immediately asks: "Run verification now or flag this as deferred?" Deferred items are tracked and surface at session start next time.
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.41 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`

### 15 SESSION_INSIGHT_RECORD ingestion deferred until ADR-045 and ADR-048 operational
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`

### Video Pipeline Validation**: Frame sampling quality, transcription accuracy, vision extraction validation not implemented
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.18 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Knowledge Formation Layer:** Blocked by image storage and pipeline services
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.36 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`

### Missing Downstream Layers**: The capture layer reveals significant gaps in extraction, knowledge formation, retrieval, and application layers that must be built.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.40 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### New Knowledge Formation Gap**: Conversations are stored but **never processed** for knowledge extraction.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Knowledge Formation**: 15 SESSION_INSIGHT_RECORDs not ingested → knowledge incomplete → cannot form complete architectural picture
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.48 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Verification Layer Gap Identified**: The verification layer (`cis_verify.py`) is now understood to have a critical gap.
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

### Storage Implications**: Must be stored in gap tracking system with indexing by subsystem and target resolution
- support: 3 statements across 2 document(s)
- nearest queue item 18 is only sim 0.34 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### New Understanding**: Execution layer is a distinct missing layer that bridges stream theory and actual runtime.
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.44 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Gap**: No orchestration for verifying schema against pipeline output
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.39 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### GAP**: No verification that registered sources are correct or complete
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...raction/functional_intents/librarian_extraction_analysis.md`

### The explicit recognition that the commit layer is NOT YET BUILT, creating a known architectural gap that blocks full automation of the intake pipeline, did not exist before.
- support: 3 statements across 2 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Low effort feature deferred to next Live panel iteration.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### Step 6 blocked by**: Step 5 completion (dashboard polling) — NOT STARTED
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_1852_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Operator Routes:** Still directly execute runtime scripts - this is an incomplete bridge that requires queue-backed execution.
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.38 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### route_task.py**: Blocked by model registry completion — registry is built but route_task.py not yet started
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### PD.5 Steps 1-6 | ADR-045 Execution Queue | Queue could be built independently | Queue blocked by verification pipeline
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `_archive/generated_script_artifacts/042926_Project_Primer.txt`

### Contract missing → contract registry creation → validation enabled → governance restored
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### The gap between "decision made in conversation" and "decision in DB" was entirely dependent on remembering to run SQL at the right moment.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### FAIL:** "FAIL: Proposal section missing", "FAIL: Proposal missing ### Summary", "FAIL: Proposal missing ### Recommendation", "FAIL: Proposal ### Summary empty", or "FAIL: Proposal ### Recommendation empty"
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### Missing Governance:** Trigger point ownership and accountability
- support: 3 statements across 2 document(s)
- nearest queue item 11 is only sim 0.35 — treat as NEW
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### No retry logic**: If database write fails, it's silently skipped
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...action/functional_intents/cis_review_extraction_analysis.md`
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### Infrastructure dependencies are unverified** — sqlite3 CLI was missing on the target VM.
- support: 3 statements across 2 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### DB table exists but schema/spec status is incomplete at this point in the transcript.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Gap:** The original report called this a "dual database" split.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Architectural Significance**: queue_worker.py invokes cis_verify.py with unsupported --file flag, indicating incomplete contract between queue worker and verification tool
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Gap**: Need a CapabilityClaim object with validation status, provenance, and correction history
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`

### `cis_lint.py`**: Future script for health checks (gap detection, stale data, broken links).
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Verification Log**: 41 unresolved FAILs — no retention/cleanup policy
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...xtraction/functional_intents/session_extraction_analysis.md`

### Extraction quality on multi-figure comic covers is a known gap — do not scale ingestion until multi-pass is proven in Phase 1
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.18 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_003.md`

### Architectural Significance**: Six specific bugs were identified and resolved during the audit process: empty verification checks, circular SHA extraction, model whitelist replacement, missing check_artifact_identity_block, migration re-run safety, and row_factory crash bug.
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.44 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0408_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-27_0408.md`

### The gap between current state and required state is substantial across all architectural dimensions: storage, retrieval, governance, security, and knowledge formation.
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Run the .tables check and paste the result.You said: How will you know when to add Frame-level data (deferred — not needed for Phase 1) to the table?How will you know when to add Frame-level data (deferred — not needed for Phase 1) to the table?Apr 23Claude responded: You will tell me.You will tell 
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.20 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Phase 1 Application Layer**: Blocked by Segment definition and batch extraction mode design.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Not yet built**: Phase 3 (retrieval) is after Phase 2 (knowledge layer)
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.38 — treat as NEW
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### What CIS is missing is the index file, backlinks, linting, session end hook, and daily flush process.
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Unresolved Storage Rules:** **File Naming Convention** - The file does not specify a naming convention for distillation files within the `README.md` container.
- support: 3 statements across 2 document(s)
- nearest queue item 17 is only sim 0.37 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...l_intents/1777410199041831732_readme_extraction_analysis.md`

### If `live_rounds` does not exist when the migration runs, the migration fails.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`
  - `ADRs/ADR-041_Artifact_Registry_Schema.md`

### Pipeline pagination**: Blocked by current single-source operator design; needs list endpoint
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.34 — treat as NEW
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Agent tab**: Depends on agent discovery service — not yet built
- support: 3 statements across 2 document(s)
- nearest queue item 21 is only sim 0.48 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### None**: No validation of course content, no provenance tracking for suggestions
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### Missing:** Explicit interface between drift detection and user notification
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...nctional_intents/x_00_operator_model_extraction_analysis.md`

### Rule:** If interface allows material to enter without producing structured output, it is incomplete.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.28 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Versioning, not replacement | MASTER_ARCHITECTURE_MAP | Records are versioned; existing records are never silently overwritten
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.33 — treat as NEW
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Contract 6:** Output must be actionable — each gap/risk must have proposed resolution
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### In your docs, the merge layer is required because OCR and visual alone are incomplete.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.23 — treat as NEW
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`
  - `...yBuildFiles/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md`

### Flask/Node/npm missing; Flask was installed, React served by CDN.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`

### Distributed execution (hardware constraint makes this out of scope)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`
  - `ADRs/ADR-045_Execution_Queue_Ownership_Layer.md`

### Missing Validation Layer: Visual Output Quality Metrics
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...e_system_legacybuildfiles_x_03_state_extraction_analysis.md`
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`

### Missing File**: Returns 400 with "No file provided"
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### New Understanding:** The system is not blocked by infrastructure.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`

### No quality → capture feedback | Capture quality not measured or fed back | **MISSING**
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Status**: Defined in skill documents but not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### And critical unresolved gaps are identified for the build plan.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Log file append**: If log file is locked or missing, test still passes but warning is emitted
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...on/functional_intents/cis_test_queue_extraction_analysis.md`

### Black screen dashboard bug fixed — missing comma between OperatorPanel and DraftIntakePanel createElement calls
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-05_0323.md`

### Dependency Impact**: Requires project-to-domain mapping convention; no validation of project parameter
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...extraction/functional_intents/spines_extraction_analysis.md`
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Error Recovery**: Blocked by missing retry/rollback logic
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...traction/functional_intents/pipeline_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Note**: The application layer is blocked by the execution layer.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Fail**: File missing, JSON invalid, fields missing → silent skip.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...n/functional_intents/project_helpers_extraction_analysis.md`
  - `...nctional_intents/deepseek_mcp_bridge_extraction_analysis.md`

### Deferred Cycle**: Drafts preserved → explicit resume required
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `...primer_update_governance_contract_v1_extraction_analysis.md`
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### Paste the output and I will give you the exact fix for that specific line.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...l build sequence and architectural dependencies.md:2363`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Gap 3 — cis-log current signature: Current cis-log commands:
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`

### Input Validation**: source_id required, returns 400 if missing
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### File missing → Layer 1 fails → Immediate correction → File written correctly
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### The file says logs must not be empty or truncated but does not define thresholds or validation rules.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_014_extraction_analysis.md:408`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Missing paths**: If TUTORIAL_ROOTS don't exist, scan silently skips
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### Project Linkage is Incomplete**: `project_id` is stored but `project_title` is None.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Missing**: Metrics (records produced, errors, latency)
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...traction/functional_intents/pipeline_extraction_analysis.md`

### No validation layer exists to catch this before runtime.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### No validation** of record `status` values — assumes they match expected state machine.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...n/functional_intents/project_helpers_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### Project Before Capture**: If project_id is provided, the project must exist (though not enforced)
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...traction/functional_intents/captures_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Review Workflow** - Blocked by status machine, governance rules
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...action/functional_intents/record_001_extraction_analysis.md`
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`

### Runtime Impact**: Silent failure mode — operator unaware of missing records.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Runtime Impact**: Unresolved next actions block or inform subsequent workflows
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Architectural Significance**: Confirms execution queue as canonical runtime layer with verified operational status for Step 1 (execution_jobs table), but reveals 6 remaining implementation steps (Steps 2-7) that are not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `...ation_backups_20260430/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`

### New Object**: Slot 3 (pending) — deferred, requires evaluation
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`

### This is a documentation failure: the placeholder was not clearly marked as a placeholder and the user ran it expecting it to work.
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.27 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### This is not implemented but is identified as highly relevant.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.25 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_002_extraction_analysis.md:366`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Application Layer**: Blocked by missing workbench behavior and all upstream layers
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...cybuildfiles_x_cis_critical_addition_extraction_analysis.md`

### Unresolved Routing:** Output distribution mechanism
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Validation layer does not exist**—outputs that fail validation are not flagged needs_review
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### Validation Object**: No validation rules for solution quality
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.32 — treat as NEW
  - `...l/extraction/functional_intents/live_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### You're building a system where Claude proposes and writes code or content, you trust that it landed correctly, and later discover it didn't — placeholder text instead of real content, omitted fields, incomplete writes.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...pts/2026-04-25_Verification mechanism for completed work.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Duplicate Open Questions File**: 08_OPEN_QUESTIONS_final.md in outputs is a duplicate of 08_OPEN_QUESTIONS.md, creating a file management issue.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`
  - `_archive/generated_script_artifacts/042926_Project_Primer.txt`

### Confirm when saved and I'll generate the Completion Manifest.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `...-bf01c31eefb7:Phase 1 intelligence extraction setup#r11`
  - `contracts/CIS_Automation_Reduction_Contract_v1.md`

### ADR-045 closure**: Corrected execution ownership gap
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.46 — treat as NEW
  - `...e_chat_transcripts/ChatGTP_Project_Primer/07_KNOWN_RISKS.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`

### “No error shown” is not sufficient if output is truncated or incomplete.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### '− Cancel' : '+ Add Task' 1255: e('input', { type:'text', placeholder:'Task title', value:title, onChange:ev=>setTitle(ev.target.value) }) 1267: e('button', { className:'btn btn-primary', onClick:addTask, disabled:!title.trim() }, '+ Add') 1271: ?
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.20 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`

### 2 — Script error (bad args, file missing, vLLM unreachable)
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify_semantic.py`

### Application Layer on Underlying Layers**: Application cannot function if any underlying layer is incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.27 — treat as NEW
  - `...818091549056_x_10_application_stream_extraction_analysis.md`
  - `...action/functional_intents/x_03_state_extraction_analysis.md`

### Artifact status** — Which artifacts exist, which are missing
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.43 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...primer_update_governance_contract_v1_extraction_analysis.md`

### Cannot silently preserve contradictions—escalation is required.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `...itutional_memory_governance_revision_extraction_analysis.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Workflow Pipeline**: Not yet implemented; Phase F deferred
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Blocked by:** Vault must exist with subdirectories
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...ents/cis_dashboard_monolith_20260420_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### No Business Rule Validation**: No validation of domain/sub_domain combinations
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Conflict register session dropdown**: Does not refresh without browser refresh (LOW severity, DEFERRED)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### CREATION and LIFE are top-level domains** with CREATION proven first — LIFE domains (Home, Body, Mind) are deferred.
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.23 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`

### Filesystem Validation** — No validation layer for filesystem canonicality
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.29 — treat as NEW
  - `.../functional_intents/primer_update_v3_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Lifecycle**: Sequential execution in early phases; concurrent execution deferred
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### Content Validation**: No validation that file content is appropriate for public consumption
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.23 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`

### Cross-field validation**: No validation that corrections don't create inconsistencies
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`

### Corrupt Manifests**: L2 fails if manifest is malformed or missing required fields
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...tion/functional_intents/queue_worker_extraction_analysis.md`

### Cross-Slot Validation**: No validation for model slot interoperability.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

### Cross-reference validation**: No validation that draft doesn't conflict with existing canonical records
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### DAM Panel**: Blocked by undefined DAM object schema and missing asset management infrastructure.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Deferred**: Application Layer depends on Execution Layer being proven first
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Dependency Impact:** Requires input validation that accepts partial/evolving definitions rather than rejecting incomplete inputs.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Contract Gap**: Contract rejected if implementation reveals missing dependencies
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Description**: The following queue subsystems are identified as missing but required:
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Insight capture is a missing architectural layer**
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### from using the CIS application: the missing bridge from discovery to execution.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...with_these_files_cis_operating_model_extraction_analysis.md`
  - `DEV-PIVOT-08_FRONT_DOOR_SPEC.md`

### Discovery 4: Application Layer Blocked by Execution/Core Workflow
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Discovery 5: Cold start validation is not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`

### Documentation correction loop**: Missing documentation → discovery through failure → retroactive documentation → (partial) documentation
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...85_2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`

### No validation for draft file naming** — What if naming convention is violated?
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...primer_update_governance_contract_v1_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### FAIL — one or more hard failures (missing file, placeholder, hollow section, contradiction)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify_semantic.py`

### 1 — Validation failure (missing FINAL_JSON, wrong role/status, untracked files, DB error)
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`
  - `CIS_TIER_11C_DRAFTER_REVIEWER_HANDOFF_SPECIFICATION.md`

### Fail Condition**: Incomplete corpus access, pattern document not read first, output is a summary
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Fail**: Violates constitutional layer, transition incomplete, feedback loop broken
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...update_governance_contract_dicussion_extraction_analysis.md`

### Fail**: backbone missing fields, structure inconsistent, uncertainty unknown
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...gacybuildfiles_x_cis_discovery_model_extraction_analysis.md`
  - `...tional_intents/x_cis_discovery_model_extraction_analysis.md`

### Missing Feedback Loops**: The system has no correction, governance, retrieval-improvement, archive-learning, continuity/memory, or project-output feedback loops.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### No validation** — Flask reads file and returns it as-is; no content validation, no format checking, no size limits
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.24 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`
  - `...unctional_intents/cis_live_handoff_1_extraction_analysis.md`

### Fill Gap Actions**: Identify gaps, propose solutions, implement solutions
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### First: ChatGPT's description of Claude Projects is partially outdated or incomplete.** The document it produced describes Projects as essentially a "big shared prompt folder" with no real indexing.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.34 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### New Understanding**: Cold start recovery validation is DEFERRED, meaning queue state may be lost on restart.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Gap**: No defined object for capturing and storing Eric's corrections
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.33 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Gap**: How all four feedback loops coordinate is not defined
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Gap**: Initial routing pointed to www subdomain with path filter
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### Transitional Gap Logging Command**: New command to log named transitional gaps
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Gap**: No defined storage layer for intermediate processing outputs
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`

### Gap**: No defined rules for what constitutes canonical vs.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.31 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Gap**: No documentation exists for how users interact with the system at runtime.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.29 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Gap**: How proposed structures are routed to appropriate reviewers is not defined.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.33 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...intents/cis_source_manifest_contract_extraction_analysis.md`

### ADR-008 and ADR-010 are missing from the display — they were logged but the harness shows gaps in the sequence.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### No deduplication | No mechanism to detect duplicate captures | **MISSING**
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...tion/functional_intents/dedup_memory_extraction_analysis.md`

### Gap**: No notification system for processing completion
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap**: No retry logic for transient failures (GPU OOM, file system errors)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...xtraction/functional_intents/helpers_extraction_analysis.md`

### Gap**: No tracking of how often models are used or their success rates
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Manual Mediation Handoff Point |  | Explicit human-in-the-loop gap between capture and mediation
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Correction Loop: Gap Audit Before Intelligence Work
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap:** Format defined but no formal object model
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.26 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Implementation reveals gap → ADR updated → contract registry updated → spec doc updated
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### Add or defer processing profile override with explicit gap note.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Impact**: If missing, query returns no results or errors
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...ents/cis_dashboard_monolith_20260420_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Incomplete Insight Records**: Must be updated before insights folder is complete
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Impact:** Data loss risk if addendum is forgotten or incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.29 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ents/post_commit_addendum_2026_04_18_extraction_analysis.md`

### Source Manifest | Structure not fully specified | Intake metadata incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`

### Interface layer blocked by material analysis capability
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.32 — treat as NEW
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Invalid JSON**: Missing or malformed request body causes 400
- support: 2 statements across 2 document(s)
- nearest queue item 19 is only sim 0.31 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### No validation tested for**: Missing fields, malformed payload, duplicate jobs
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `...on/functional_intents/cis_test_queue_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### *DRAFT status: This document is a Hermes-generated proposal. It does not represent an Eric-approved decision. Items classified as Deferred-unscheduled are NOT cancelled — they await scheduling by Eric after external advisor review.*
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.47 — treat as NEW
  - `PLAN_RECONCILIATION.md`
  - `PLAN_RECONCILIATION.md:31`

### Lifecycle**: Created → Initializing → Ready/Incomplete/Failed → Active → Closed
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Lifecycle**: Defined at capability level; implementation deferred
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`

### Lifecycle**: OPEN → (DEFERRED | RESOLVED | SUPERSEDED)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `HANDOFF_SCHEMA.md`

### Manifest Namespace Objects**: Three classes defined but namespace separation not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.21 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`

### Unresolved Application Surface: Progress Monitoring
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`

### Missing Runtime Bridge: Dashboard to CLI**: The exact mechanism for the Dashboard to execute CLI commands (`cis-log`, `cis-start`, `git`) is not defined.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.30 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Missing Runtime Bridge: STATE.md ↔ Phase Definitions
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Missing `CIS_API_KEY` environment variable blocks remote API access
- support: 2 statements across 2 document(s)
- nearest queue item 14 is only sim 0.32 — treat as NEW
  - `...ction/functional_intents/gpt_gateway_extraction_analysis.md`
  - `...el/extraction/functional_intents/app_extraction_analysis.md`

### Missing `project_id` will fail or produce orphaned manifests.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`

### `CIS_FILE_MAP.md` at `/mnt/projects/cis/` — the orientation document you've been missing
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `...26-04-21_Session close and handoff process clarification.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Partial Pass**: Record created with missing fields; flagged for review
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Workflow Output Validation**: No validation rules for workflow outputs
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`

### Missing**: No linkage between project outputs and model registry.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Missing**: No rejection reason collection or analysis
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Missing**: Progress indicator, cancel button, error display, attach instructions after close
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...n/functional_intents/captures_readme_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Model Evaluation View**: Admin registry view for model evaluation work (testing/benchmarked models) not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Model registry validation | No validation for model data | MEDIUM — will be needed
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.25 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### No Request Validation**: No validation of request parameters
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.20 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...extraction/functional_intents/health_extraction_analysis.md`

### Forbidden strings check (TODO, FIXME, PLACEHOLDER, HARDCODED, etc.) — skip content inside triple-backtick fences (known bug fix)
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...rchChatsProjectsCodeCustomizeDesignMoreRecentsHidePhase.txt`

### None detected**: No validation feedback that corrects user input
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...ion/functional_intents/ingest_spines_extraction_analysis.md`
  - `...xtraction/functional_intents/app_api_extraction_analysis.md`

### Not implemented**: No message review, moderation, or approval workflow
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### The backlink syntax for knowledge record MD files was designed but not implemented in `cis_normalize.py`.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Response Validation** — No validation that pasted responses are from actual models
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.22 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### Pie Menu System**: Blocked by UI system and hotkey hold detection
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.21 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### Post-Commit Work Validation** — no validation that post-commit work is captured
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Conflict register is the mechanism for tracking unresolved knowledge contradictions.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...ChatGTP_Project_Primer/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Purpose**: Represents missing or unclear structure in interpretation
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.37 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### Purpose**: Prevent placeholder text from passing as complete
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.42 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Push Validation** — No validation that push actually updated live site
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Update Validation**: No validation that SCP transfer was successful
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.21 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Recovery behavior details**: Interrupted jobs, stale jobs, crash recovery — behavior defined at high level but not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.29 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Routing Layer**: Blocked by registry schema implementation; cannot function without capability filtering and resource validation
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Remote GUI access (Parsec/Moonlight) is deferred until after pipeline validation.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...ative Intelligence System (CIS)/cis_system_bundle/MEMORY.md`
  - `...ystem (CIS)/cis_system_bundle/Handoff_Summary_03_31_2026.md`

### Requirement:** Visibility into unresolved questions (08_OPEN_QUESTIONS.md)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...de_chat_transcripts/ChatGTP_Project_Primer/00_START_HERE.md`

### Returns `False` otherwise (including when `run_id` does not exist).
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.26 — treat as NEW
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`
  - `cis_v1_vault/runtime_scripts/runtime/api/drafts.py`

### Runtime Impact**: Missing files cause context drift and execution errors
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Runtime Impact**: Potential for stale or missing manifest if previous operations failed
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Runtime Impact**: Missing system packages will cause runtime failures.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `.../functional_intents/mnt_projects_cis_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Runtime Impact:** State machines must handle "incomplete" as a valid initial state.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Snapping System**: Blocked by geometry query system and transformation system
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.25 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### Commit Layer (ADR-048 Phase 3):** Blocked by build plan rewrite
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### States**: Idle, Coordinating, Complete, Blocked (missing agent/dependency), Awaiting Approval
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.41 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`

### States:** Written (successful), Partial (failed close), Missing (close not completed)
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### States**: valid (all required fields present), invalid (missing fields → exit)
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `...ctional_intents/cis_download_watcher_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`

### are you referring to the task list as the deferred list?
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### The build plan did not fail because components were missing.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...re_atlas/cis_chat_2026_04_001_extraction_analysis.md:10`
  - `architecture_atlas/cis_chat_2026_04_001_extraction_analysis.md`

### The gap between "system we understand" and "system someone else can run" was not explicitly recognized
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### This is a governance gap that must be resolved before scaling.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...tents/1776042143355379182_x_03_state_extraction_analysis.md`

### This is a foundational gap that must be resolved.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`

### This is not a minor gap — it is the single point of failure preventing the entire CIS system from becoming operational.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Title handling | Project Initiation | Generate working title if missing
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.21 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### No validation** — no schema validation, no uniqueness enforcement.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### Unresolved Application Surface: Detach Button Discoverability
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### Unresolved Routing: Memory-Based Routing**: The logic for routing requests based on memory context is undefined.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### View Layer System**: Blocked by render engine and collection system
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.26 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### If validation rules are incomplete, Worker 4 cannot verify
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.35 — treat as NEW
  - `...i_execution_infrastructure_primer_v1_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Constraint 2 — Execution layer gap.** The execution layer — the headless runtime that converts workflow intent into deterministic commands, state transitions, and validated outputs — does not yet exist in unified form.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Zero unresolved FAILs required before constitutional closure** — Verification gate.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/13_RUNTIME_TOPOLOGY.md`

### `Mark DEFERRED in appropriate primer file` - Alternative to conflict register
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...pts/ChatGTP_Project_Primer/archive/PROJECT_PRIMER_UPDATE.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### cis_review.py is the missing final command that moves a record from draft to checked/approved and captures human corrections.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.41 — treat as NEW
  - `..._Master_Handoff_files/CIS_Handoff_Review_Command_Session.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### return jsonify({"error": f"Missing required fields: {missing}"}), 400
- support: 2 statements across 2 document(s)
- nearest queue item 19 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/api/models.py`

### This session also crystallized the post-commit work problem as a structural gap that affects the entire build.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.39 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Architectural Significance**: The root cause of recurring context and orientation loss is NOT missing features but a missing execution layer.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-28_0553.md`

### Handoff Package Builder**: Not yet built (Build 7)
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### Handoff folder creation** — no automated creation if missing
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`

### Memory Rule: keep decisions, rationale, deferred ideas; do not keep transient errors, repeated explanations
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.36 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`

### Memory is project-scoped.** Cross-project memory sharing does not exist.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Runtime Implication**: Unresolved sessions create knowledge debt
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Session workbench**: Not yet built — interface for session management
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.49 — treat as NEW
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`

### The gaps I flagged are still valid observations about the handoff documents themselves — but the framing should have been "here is what is missing from this handoff package" not "do this before you close."
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### Runtime Impact:** Once CIS Live is wired, branch notes become the missing lightweight documentation layer between handoffs and ADRs.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.32 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### Whether handoff files should be copied, moved, or generated directly into canonical folder is unresolved.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `...04-21_App showing black screen after code change.md:907`
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`

### 4 conflicts logged this session: 3 RESOLVED, 1 DEFERRED (manifest namespace)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.42 — treat as NEW
  - `...ect_Primer/_backups/20260502_0047/10_OPERATIONAL_REALITY.md`
  - `HANDOFF_SCHEMA.md`

### After:** The **branch note** concept fills this gap — three fields (Branched from, Why, Return point) captured as a CIS Live round at the moment of deviation.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Missing STATE.md**: Cannot start any session without current state
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...is_predev_infrastructure_plan_claude_extraction_analysis.md`

### Deferred Work Tracking**: All deferred items explicitly listed for next session
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Deferred Work → Next Actions → Session Focus → Execution | Work continuity | Working
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Fail**: Missing field, failed sync check, missing handoff folder, ADR numbering gap
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`

### Gap**: Exact handoff protocol between models undefined
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Gap**: No proven local model backend with sufficient context
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.28 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Gap**: Session sequence position uses controlled vocabulary (earliest, early, mid, recent, current) but no mechanism exists to determine position
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Gap**: No session persistence or re-authentication mechanism
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.31 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap**: Dashboard used for session close fields but integration not fully defined
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Handoff Package Object**: Contents defined but bundling format and delivery mechanism unresolved
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.19 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Impact:** Handoff payload may be incomplete or inconsistent.
- support: 2 statements across 2 document(s)
- nearest queue item 9 is only sim 0.32 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Impact:** Six decisions from this session unrecorded; ADRs.md incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### Memory missing → re-discovery → extraction triggered → memory formed
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.33 — treat as NEW
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Missing Project Context**: All modules fail if no active project context
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...cybuildfiles_x_10_application_stream_extraction_analysis.md`
  - `...onal_intents/x_10_application_stream_extraction_analysis.md`

### Missing Session Log Template**: Cannot properly close sessions
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.50 — treat as NEW
  - `...is_predev_infrastructure_plan_claude_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### the information in this current chat expands the overall goals even more. Plus you have the original build plan to refer to in the project files. as a matter of fact lets close this session now so that everything in the project file will be available to the next chat
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...4bed004644e:Building cis_verify.py layer 1 verification`
  - `...rchChatsProjectsCodeCustomizeDesignMoreRecentsHidePhase.txt`

### Prompt completeness not validated (models may receive incomplete context)
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`

### Let me know when that's open and we'll start with the Resolve button — that's blocking session hygiene for everything downstream. You said: open
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.36 — treat as NEW
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:392`

### Instead it became an archaeology session — verifying what actually existed on disk, discovering a schema file that had never been updated to reflect the real pipeline output, clearing stale test data, and ultimately identifying that the session memory system is the most critical missing capability i
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.41 — treat as NEW
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Session reference validation | Not implemented | Broken references
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.38 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`

### The memory system was described as having "locking" functionality that does not exist.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### The `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` flag must be permanently added to the gpu-test activation script.** It has been an unresolved note across every session.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### The runtime reality is that every session starts with incomplete context unless explicit verification occurs.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.43 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Form knowledge → archive | Structured knowledge stored | **NOT IMPLEMENTED**
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Application Layer:** Blocked by knowledge object schema and governance rules
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.32 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`

### resolve --action <action_id> --status <resolved|deferred|escalated>
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Draft intake bridge | Dashboard panel | /api/drafts/stage → DB | Not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.35 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Insight → Knowledge formation bridge not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `...e_system_legacybuildfiles_x_03_state_extraction_analysis.md`

### Knowledge scaling is blocked by review/promotion UI.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Missing ChromaDB Package**: Entire vector search capability fails
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...n/functional_intents/session_extract_extraction_analysis.md`
  - `...tion/functional_intents/memory_store_extraction_analysis.md`

### No search optimization | Search not improved based on results | **MISSING**
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.44 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Now let me document the future features before building.Searched project for “future features deferred decisions memory”Searched project for “future features deferred decisions memory”Good — the Memory doc is the right place.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `_archive/Refactoring CIS application into modular structure.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_008.md`

### Gap**: No knowledge formation logic discussed in this build target document
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Chunked semantic verification**: No validation for large files
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`

### Creative work produced → Feedback collected → Knowledge updated → Future work improved
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `...818091549056_x_10_application_stream_extraction_analysis.md`
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Draft retrieval improvement | Draft DB → Query → Better indexing → Faster retrieval | Positive reinforcement | Not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.43 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### Fail**: material unanalyzable → structure incomplete → user rejected → knowledge discarded
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`

### Fields in the real record that are missing from knowledge_v1.json: record_id, record_type, source_name, source_unit, knowledge_category, subject, tags, summary, visible_text, scene_description, layout_description, mood_style, uncertainty, retrieval_text, project_title, active_stages, source_origin, 
- support: 2 statements across 2 document(s)
- nearest queue item 19 is only sim 0.35 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Gap**: Need automatic session type detection and routing
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Knowledge Gap**: Verification results are stored but not indexed, not queried, not aggregated, and not fed back into system behavior — creating a **write-only knowledge pattern**.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.41 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Query issued → Knowledge not found → Gap logged → Intelligence processes → New knowledge created → Gap filled
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.40 — treat as NEW
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### The CIS architecture has a missing layer between the Application Layer and the Knowledge Layer: the **Session Initialization Layer**.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Multi-Tier Intelligence Routing Bridge**: Not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...818091549056_x_10_application_stream_extraction_analysis.md`
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`

### Knowledge Tier Validation**: No validation for tier classification
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...818091549056_x_10_application_stream_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### Knowledge layer operations** blocked by unverified Source Manifest, Processing Profile, and Review States contracts
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`

### Missing Review State Machine**: Blocks production use of knowledge (cannot determine trust level)
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...tional_intents/x_07_knowledge_stream_extraction_analysis.md`

### Synthesis layer | Knowledge formation | Intelligence Stream confirms missing merge
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Missing project context**: Agents cannot operate without project_id, stage, knowledge.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.46 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `...functional_intents/x_09_agent_stream_extraction_analysis.md`

### Not yet defined — deferred until retrieval system is built
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.37 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...s_cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Missing Governance**: There is no governance rule for what happens when `cis_verify.py` returns a FAIL.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Unresolved Storage Rules:** The storage rules for spine node MD files in the Obsidian vault are not yet defined (naming convention, folder structure, etc.).
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.57 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Runtime Impact**: Retrieval may return incomplete results until ingestion is complete
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### Storage Implications**: Relationship database, retrieval indexes, gap records
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.41 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0413_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`

### Storage implications**: Must be versioned; existing records never silently overwritten; retrieval priority by state
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.40 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### Unresolved Routing: Agent Requests**: How does a user request an agent?
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.48 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`

### Missing Session Cognition Pipeline** - Prevents architectural continuity
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.34 — treat as NEW
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### ChatGPT architectural insight captured in CIS Live #034 — governed state registry, drift detection, and phase-aware status taxonomy deferred to build plan rewrite
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-05_0323.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-05_0427.md`

### Automatic Retry**: Out of scope for this ADR (max_attempts reserved for future use)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`
  - `ADRs/ADR-045_Execution_Queue_Ownership_Layer.md`

### Swarm/multi-agent orchestration** — deferred until single-role agents are stable; prerequisites are stable knowledge layer, reliable retrieval, consistent workflow structure, controlled intelligence execution
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.43 — treat as NEW
  - `...s_cis_legacybuildfiles_consolidation_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Architectural Significance**: The document explicitly identifies multiple instances where humans serve as the operational interface between system components, revealing a fundamental architectural gap in the automation layer.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### This reframes the entire intake problem from "we need better tools" to "we need a missing architectural layer."
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.30 — treat as NEW
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Drift Detection, Phase-Aware Status, and Inheritance Integrity are Unified**: These three capabilities are expressions of the same missing layer (State Registry), not separate concerns.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...traction/functional_intents/cis_live_extraction_analysis.md`
  - `CIS_Creative_Intelligence_System_v1/CIS_LIVE.md`

### Unresolved Orchestration:** The orchestration logic for the full pipeline (spine → source intake → concept mapping → segmentation → extraction → record formation) is not yet designed.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Aspirational/Not Yet Built**: Intake layer (ADR-048), manifest stability (ADR-047), Slot 1 automation, run_l2 dashboard polling, expansion policy
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Automated Verification Pipeline**: Blocked by broken queue worker and missing Slot 1 automation
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Draft Intake**: Still using human copy-paste, ADR-048 Staged Draft Intake not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/api/session.py`

### Blocked by: nothing — can be drafted in parallel with ADR-045 completion.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.38 — treat as NEW
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `ADRs/ADR-047_SCOPE_PREDRAFT.md`

### No validation loop**: No mechanism to verify infrastructure configuration
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`

### Gap**: No defined orchestration for the extraction workflow (who triggers, who validates, who publishes)
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Gap**: No defined orchestration logic for distillation pipeline
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Gap**: Session insights, decisions, and architecture discoveries are not automatically captured.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### I correctly identified the three missing components: pipeline state table, orchestrator script, approval queue panel.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...ntents/phase_0_5_replan_orchestrator_extraction_analysis.md`
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### Intelligence execution flow** — Trigger → Orchestration → Reasoning → Action → Output → Retention defined but implementation details missing
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Later: CIS Live rounds can auto-detect “conflict/deferred” tags and log them automatically.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...st_try/insights_First_Try/_Automation_Discussion_ChatGTP.md`
  - `ADRs/ADR-048_SCOPE_PREDRAFT.md`

### Missing Runtime Bridge: Automated Extraction Pipeline
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Missing Validation Layer: Pre-Snapshot Validation Automation
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.20 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`
  - `...cybuildfiles_x_cis_critical_addition_extraction_analysis.md`

### Gap**: No explicit provenance tracking for execution jobs
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### Session close gate logic**: Pre-close state check defined but not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.41 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### No Validation Layers Exist**: LivePanel rendering, Decisions API, and broadcast orchestration all lack validation layers.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`

### If you're seeing this in your own code or infrastructure, the next useful step is checking logs for the actual error being swallowed before the retry. Want to share more context about where this appeared?
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...6-04-24_Retry attempt taking longer than expected.md:12`

### The most important realization is that CIS is a self-structuring system with explicit feedback loops, and the execution bridge layer is the critical missing piece that must be defined before any implementation can proceed.**
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.28 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...onical_build_sequence_plain_language_extraction_analysis.md`

### Description**: If any pipeline component is missing, intake blocks.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...onal_intents/x_cis_critical_addition_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Unresolved Orchestration:** **Distillation Workflow** - The exact workflow (who creates, who reviews, how is it promoted) is not defined.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...l_intents/1777410199041831732_readme_extraction_analysis.md`

### The SCP write function was written and documented but not wired into the dashboard app at session end.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### The dashboard HTML monolith — 2736 lines in a single file — was explicitly deferred again.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Frontend Monolith is Deferred Risk** — The explicit decision to keep frontend as single HTML file creates technical debt that will cascade through subsequent sessions.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_20_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Storage Implications:** UI component, blocked by frontend modularization ADR
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.23 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`

### Gap:** `cis_review.py` exists but has no dashboard trigger
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`

### They didn't land. The commands returned no error but nothing was written. The API is likely returning a success-looking response but silently failing. Check what the endpoint actually returns on a post:
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.30 — treat as NEW
  - `...04-21_App showing black screen after code change.md:225`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### The project files are read-only so I'll produce this as a document to copy into the Memory doc, then build the Live panel.Memory additions — future features deferred from sessionMemory additions — future features deferred from sessionGood — that's documented.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0139_extraction_analysis.md`
  - `_archive/Refactoring CIS application into modular structure.md`

### Application Gap**: There's no application-layer interface for verification — no dashboard, no API, no CLI beyond the raw script — making it invisible to any higher-level system monitoring.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.29 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Application Layer**: Blocked by dashboard modularization decision, draft management interface design
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.33 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Application growth | Frontend monolith risk + missing transcript/governance surfaces
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.21 — treat as NEW
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Corrected:** Frontend refactor is deferred indefinitely
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0547_extraction_analysis.md`
  - `...ession_insight_record_2026_04_20_001_extraction_analysis.md`

### Minimal dashboard should be built in Phase 1**: Not deferred to Phase 5.
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Decision Logging Form**: Blocked by missing dashboard endpoint for decision CRUD operations.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Draft Routes**: Human → API endpoint routing not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`

### Final plan acceptance | state = awaiting_approval after full plan elaboration | Complete Build Plan v2, verification summary, open questions
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.44 — treat as NEW
  - `...ents/cis_execution_layer_contract_v1_extraction_analysis.md`
  - `contracts/CIS_Execution_Layer_Contract_v1.md`

### Implication**: The "human is still the API" gap is being closed.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.30 — treat as NEW
  - `...intents/archive_02_next_build_target_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Project Management Panel**: Blocked by undefined project management object schema and missing timeline/milestone infrastructure.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Structure Proposal Panel** - Shows detected, uncertain, and missing structure
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...gacybuildfiles_x_cis_discovery_model_extraction_analysis.md`
  - `...tional_intents/x_cis_discovery_model_extraction_analysis.md`

### "The Human is Still the API" is an architectural gap, not a UX problem.** This reframes the entire intake problem.
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.34 — treat as NEW
  - `...intents/archive_02_next_build_target_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Execution worker | Does not exist | ADR-045 queue worker
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.26 — treat as NEW
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `_archive/generated_script_artifacts/042926_Project_Primer.txt`

### This means ADR-032 needs to define the full domain taxonomy including Home/Body/Mind, and note that creative production domains are built first with life management domains deferred to a later phase.
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.27 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Number order** — ADR-008, ADR-010, ADR-002-SUPERSEDED are missing from the visible list.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Governance Layer** blocked by pattern detection
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.32 — treat as NEW
  - `...06699132426333_x_cis_discovery_model_extraction_analysis.md`
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`

### Here is what is missing from the contract that would prevent this from happening again:
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...-24_CIS phase 1 intelligence extraction handoff.md:1595`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Task completion governance**: No validation that tasks are actually complete before marking them done.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Execution jobs table** (defined but not implemented — ADR-045)
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.26 — treat as NEW
  - `...hive/orientation_backups_20260430/10_OPERATIONAL_REALITY.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`

### "models table does not exist — roster enforcement deferred.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `CIS_Creative_Intelligence_System_v1/Phase_PD/ADRs.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### No capture governance loop | No review of capture quality | **MISSING**
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### Then paste the decisions output so we can see the full ADR list and confirm nothing is missing.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### appropriate phase and logged as an ADR direction or open question.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Purpose**: Track discovered contradictions, filesystem conflicts, naming collisions, stale documentation, deferred bugs, and governance/runtime mismatches
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `CIS_CONFLICT_REGISTER.md`

### ADR-047 Does Not Exist Yet**: This is a pre-draft scope document.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### `add_fields(proposal, fields)` — User adds missing fields
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...2471347_x_cis_discovery_workbench_v1_extraction_analysis.md`
  - `...ldfiles_x_cis_discovery_workbench_v1_extraction_analysis.md`

### Logs must be append-only and immutable. No log entry may be modified after writing.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `contracts/CIS_Execution_Layer_Contract_v1.md:146`

### Contract Authority Application Surface**: Registry management interface not implemented.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### Dependency Impact**: Governance cannot be enforced until implementation catches up; creates validation gap between documented governance and actual system behavior.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.27 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### ```text Governance → Authority Boundaries → Internal Writer / External Reader Split → Documentation as Continuity Authority ```
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_009_extraction_analysis.md:347`
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Runtime Bridge**: Governance contracts reference operational reality but cannot enforce it until implementation catches up.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Missing Governance Rule: No Unverified Reassurance
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_010_extraction_analysis.md`

### The missing bridge is the contract register that shows which expected contracts exist, which are missing, and which implementations were built without the contract-first discipline.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Model identity governance**: No validation of builder_model_id values
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`

### Record promotion governance**: No validation that records meet quality thresholds before promotion.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Notes field must follow defined criteria (deferred decisions, warnings/gotchas, mid-thought work, deferred non-next-step items)
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`

### runtime/manifests/**: Unknown ownership, may be deprecated — creates governance gap
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Status**: Deferred until after ADR-045 complete
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`

### This represents a **governance-implementation gap** that must be resolved before the draft intake layer can be considered stable.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### This proposal addresses the core gap Eric identified: governance as documentation versus governance as application.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...re_atlas/cis_chat_2026_04_004_extraction_analysis.md:34`
  - `DEV-PIVOT-04_APPLICATION_ENFORCEMENT_SPEC.md`

### Execution jobs table**: Not yet built in cis_memory.db.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### The segmentation decision that would have allowed the schema to be finalized was deferred.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### The video source_unit schema was proposed and then blocked by the segmentation strategy question.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_22_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Discovery 5: ensure_models_table Not Wired into ensure_tables
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### Missing column detection**: ALTER TABLE adds missing columns on re-run
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.19 — treat as NEW
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### Comparing it against what's in the DB now, one gap stands out — it was written on 2026-04-20 and describes CIS_LIVE as "not yet wired into cis_dashboard.html." That's now outdated.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Task States:** `deferred`, `backlog` — no active or completed tasks posted
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Dependency Impact**: Fresh DB deployments will fail silently — models table missing breaks all downstream services.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### Manifest format correction | Schema lock → Format error → Corrected manifest | Negative feedback | Not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Gap**: `project_id` is a field, not a storage partition
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### If many records fail validation due to a missing field, the schema may need to be updated rather than forcing data into the old shape.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### Current**: Explicitly deferred until Layers 1-5 stable
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `...tional_intents/x_01_system_blueprint_extraction_analysis.md`

### `ADR database audit → schema audit → runtime artifact audit → contract register → missing contracts → implementation verification`
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Schema must be defined first** — Cannot enforce without schema
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...2471347_x_cis_discovery_workbench_v1_extraction_analysis.md`
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`

### The decision was made that session transcript extraction is the highest priority build target, above `cis_spine_intake.py` and above writing the missing contract specification documents.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Fail**: Governance hierarchy incomplete, dependency cycle detected, evidence uninterpretable, document update conflict, loop oscillation
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...7059416496004_x_cis_relationship_map_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### No retry or escalation logic exists**: Any failure in the session close workflow results in incomplete state persistence.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### LIFE domain spines are deferred until at least one CREATION domain pipeline is operational end-to-end.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.33 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Missing or invalid `DB_PATH` configuration will cause health check failure
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/health_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### Missing table detection**: CREATE TABLE IF NOT EXISTS creates missing tables
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...action/functional_intents/cis_review_extraction_analysis.md`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`

### Validation Contract**: No missing fields, no unsupported claims, schema intact, uncertainty expressed
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...gacybuildfiles_x_cis_execution_layer_extraction_analysis.md`
  - `...on/functional_intents/update_prefill_extraction_analysis.md`

### Unresolved Application Surfaces:** The "Spine Manager" panel in the workbench is not yet designed or built.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.48 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Content Gap Identified**: `CIS_LIVE.md` currently contains only a test string
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Verification pass**: All required layers pass, no unresolved FAILs
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`

### cis_vllm_slot1.sh port pre-check gap: zombie processes possible
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...hive/orientation_backups_20260430/10_OPERATIONAL_REALITY.md`
  - `_archive/orientation_backups_20260430/01_CURRENT_STATE.md`

### After:** Check unresolved verification failures → Surface failures → Block if failures exist → Load reorientation → Begin work
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.43 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Authority Source**: ADR-033 (identified verification gap, defined contract).
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_0722_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Blocked Layers**: Layer 2 verification is blocked by the missing model stack.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.41 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

### Forbidden strings prevent placeholder content from entering pipeline
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.30 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...unctional_intents/cis_convert_export_extraction_analysis.md`

### Input validation | Check source integrity | NOT IMPLEMENTED
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Paste me the output of Step 2 (the build) and Step 5 (the confirm) — if either shows an error, stop and paste it before continuing to the next step.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.39 — treat as NEW
  - `...pts/2026-04-25_Verification mechanism for completed work.md`
  - `claude-session-20260701-container-msg9-chunk1`

### Missing Validation Discovered**: Raw output format is not validated, creating risk for downstream normalize.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.40 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### Pre-Write Zone Check**: No validation layer for zone classification before file writes
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`

### Step 7 (cold start recovery test)**: Blocked by Step 6 completion — BLOCKED
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_1852_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### It does not solve a model confidently producing plausible but wrong content that passes all three layers. That failure mode requires domain knowledge at the human review step — the chain surfaces it, but a human who doesn't know what correct looks like will still miss it. That is a documentation and
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...-04-25_Verification mechanism for completed work.md:155`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Runtime Impact**: Every manifest write must include model provenance; missing field causes verification failure
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `...nts/adr_041_artifact_registry_schema_extraction_analysis.md`

### FAILED_REVIEW | Verifier blocking concerns unresolved | RESOLVE or TERMINATE
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...primer_update_governance_contract_v1_extraction_analysis.md`

### Slot 1 is running but fragile, Layer 2 is the only missing verification gate, and Slot 3 registration is blocked by an unresolved evaluation decision.**
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`

### Architectural Significance**: ADR-045 implementation is partially operational but not fully closed; verify_contract worker has unresolved flag mismatch bug
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...GTP_Project_Primer/_backups/20260502_0047/07_KNOWN_RISKS.md`
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`

### Architectural Significance**: The execution layer (headless runtime) does not exist in unified form.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.22 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### Deferred because:** Remote access architecture needs security review before exposing
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...reative_Intelligence_System_v1/memory_additions_20260420.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### Architectural Significance**: Intelligence may regenerate summaries, tags, constraints, risk flags; may NOT silently overwrite user decisions, source identity, canonical IDs, locked project associations
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...chat_2026_04_006_extraction_analysis_extraction_analysis.md`
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`

### Architectural Significance:** The session identifies a gap between application UI and execution reality.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...chat_2026_04_006_extraction_analysis_extraction_analysis.md`

### The session start script (`cis-start`) becomes a gate, not just an orientation tool.** It checks for unresolved verification failures from the last session before presenting the reorientation context.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`

### The application layer is not the next build target. The missing piece remains the execution/core workflow that sits underneath it.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `...CIS HANDOFF — vLLM _ Qwen VL Evaluation (April 12, 2026).md`
  - `...DOFF — vLLM _ Qwen VL Evaluation (April 12, 2026).md:60`

### process and architecture are still likely the deeper issue, but the model evaluation remains incomplete because the system has not yet been instrumented **during** inference.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...orm Chat/vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md`
  - `...vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md:1801`

### ## Discovery 2: Missing Schema Implementation - **Architectural Significance**: Tables not created means the entire data model is unimplemented despite likely being designed - **Affected Layers**: Storage Layer, Data Model Layer - **Dependency Impact**: All CRUD operations are blocked - **Build Impa
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...ts/04_data_setup_instructions_extraction_analysis.md#r1`

### Architectural Significance**: Establishes a 6-tier governance maturity model (LOCKED → OPERATIONAL → TRANSITIONAL → PRE-DRAFT → PLANNED → DEFERRED) that governs all CIS architectural components
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`

### Architectural Significance**: Formal zone classification (ACTIVE, MIRROR, ARCHIVE, LEGACY, TRANSITIONAL, DEPRECATED) for ADR-047 is unresolved
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Architectural Significance:** The `local`, `remote`, `agent` tabs in the right sidebar are currently hardcoded model cards (lines 2484-2492) and NOT wired to anything.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.37 — treat as NEW
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### Architectural Significance:** Three critical capture systems missing before Phase 1 extraction can begin: decision logging form, extraction run logging table, review/promotion UI
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`

### Dependency Impact**: Unresolved sessions may contain architectural decisions that affect Phase 1 routing design.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### Gap**: No unified retrieval structure for architectural knowledge
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.40 — treat as NEW
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### Runtime Impact**: Potential for missing context when analyzing early architectural decisions.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_0722_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### This represents an unresolved architectural conversation that may contain critical decisions or constraints.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `...ldfiles_x_cis_discovery_workbench_v1_extraction_analysis.md`

### LIFE domains must remain architecturally present even if deferred in build order
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Storage validation**: No validation that all drives are mounted.
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### The eventual application layer that exposes CIS capabilities to other users is Phase 5 and was explicitly out of scope for this phase.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### What's missing from Phase 0 exit criteria: **10–20 records from real archive material in draft state.** The commands exist but haven't been run on real archive files at scale yet.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...transcripts/2026-04-22_Model registry API implementation.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### The Sound Stream file was retrieved in that search, which means it was indexed and available — I just did not draw from it heavily in the roadmap because Sound is a deferred domain that does not affect build order for the infrastructure phases.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.32 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Build Impact**: Changes build sequencing — Intel sidebar is deferred
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### This needs to be the first thing built in the next session, not Phase 5.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `...l build sequence and architectural dependencies.md:2534`

### Phase 1 (Intelligence Extraction)**: Blocked by Phase 0 exit criteria — 10-20 draft knowledge records from real archive material
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### That's the transcript import work from the Foundation Plan (currently classified as deferred-unscheduled) plus Chroma/VDB at Tier 9.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.38 — treat as NEW
  - `PLAN_RECONCILIATION.md`
  - `Routining the quick advisor.txt`

### There are significant unresolved gaps** — retry logic, escalation logic, queue prioritization, worker scaling, verification path selection, handoff routing, and many governance rules are not yet defined.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`
  - `...ts/20260505_0119_13_runtime_topology_extraction_analysis.md`

### Next action: Prepare Tier 7 Router Reclassification proposal only. Do not implement Tier 7 yet. Do not reopen Tier 6 remediation. Do not expand PLAN_RECONCILIATION.md into a new governance phase.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `chatgpt_export/6a2720f6-47a8-83ea-93b6-a3d06a284498#r5`
  - `proposals/POST_TIER10_PLANNING_REVIEWER_RESPONSE.md`

### The segmentation thresholds, merge floor, and quality gate criteria mentioned in ADR-031's rationale were deferred explicitly to ADR-033, which was not written this session.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Dependency Impact**: Without persistent memory, system cannot enforce contract-first discipline across sessions
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.28 — treat as NEW
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### *What this enables:* The system cannot produce invalid outputs. Every object in the system has a documented, enforced history of what happened to it.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...Chats/CIS_Canonical_Build_Sequence_Plain_Language.md:43`
  - `...extraction/functional_intents/memory_extraction_analysis.md`

### Constraint bypass through placeholder data | NOT NULL FKs enforced with 409 rejection, no auto-create | Placeholder goal_reference defeats the approval gate
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `CIS_16_FAILURE_MODES.md`
  - `DEV-PIVOT-05_HERMES_INTEGRATION_ASSESSMENT.md`

### CIS policy hook** (policy brain): pre_tool_call check blocks wrong tools, wrong paths, missing evidence, missing review.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `DEV-PIVOT-17_ENFORCEMENT_ARCHITECTURE.md`
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Gap**: Memory files are staging area — but no retention policy
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.49 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Gap**: Sanity check is a binary gate, but no UI or prompt mechanism is defined.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.45 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### ### Object 1: "Capability" - **Description**: What constitutes a "critical capability" is undefined - **Impact**: Cannot enforce primary + fallback requirement without capability definition - **Required**: Capability taxonomy, criticality criteria, mapping to tools ### Object
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...ents/x_05_core_tool_stream_md_extraction_analysis.md#r4`
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`

### New plan must be organized around problems actually blocking work: session context loss, build discipline not enforced, verification not happening, build plan stale, reorientation doc out of date.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### No implementation without Eric approval (Eric Gate).
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.44 — treat as NEW
  - `CIS_EXTERNAL_ADVISOR_BRIEFING_2026-06-25.md`
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Status Values**: Documented but not enforced by SQLite CHECK constraint
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/migrate_execution_jobs.py`

### Ingest State**: Incoming, Processing, Completed, Legacy, Incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.40 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### The question is: do we design the spine ingestion pipeline now and write all migrations together, or do we write the Segment migration as a placeholder with `anchor_node_id` as a nullable field and design the spine pipeline in a dedicated session?
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### The question that determines the work order is: **does the Live tab currently show anything functional, or is it a placeholder?** That screenshot will answer it and we go from there.
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.27 — treat as NEW
  - `...04-20_Refactoring CIS application into modular structure.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_008.md`

### eric@creative-vm:~$ sqlite3 /mnt/projects/cis/memory/cis_memory.db ".tables" captures decisions schema_versions tasks corrections insights session_log eric@creative-vm:~$ sqlite3 /mnt/projects/cis/memory/cis_memory.db ".schema extraction_runs" 2>/dev/null || echo "table does not exist" eric@creative
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`

### Circular Dependency (Potential):** If the spine ingestion pipeline depends on a processing profile, and the processing profile contract is missing, there is a circular dependency on undefined work.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.39 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Archive Ingestion Layer**: Blocked by NTFS format; requires NTFS compatibility resolution
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0410_extraction_analysis.md`

### Merge Layer** blocked by: Preprocessing Pipeline, Extraction Components
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.29 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`

### Missing Runtime Bridge:** **Transcript-to-Distillation Bridge** - There is no defined mechanism for how a raw transcript is transformed into a structured distillation.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...l_intents/1777410199041831732_readme_extraction_analysis.md`

### Missing Runtime Bridge:** There is no runtime bridge between the spine ingestion pipeline and the segmentation pipeline.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### - **Runtime Impact**: Failure to install dependencies results in `ImportError` at runtime, blocking application execution entirely.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...direct_access_to_google_ai_39_extraction_analysis.md#r2`
  - `...ion/functional_intents/collab_rounds_extraction_analysis.md`

### Spine Ingestion Validation**: Not implemented — pipeline is designed but not built
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.51 — treat as NEW
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Build Impact**: Agent implementation deferred until after archive processing pipeline
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.44 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...tional_intents/x_01_system_blueprint_extraction_analysis.md`

### Empty Round 4 from "Rounds in Right Sidebar" will be silently dropped from the markdown output
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.25 — treat as NEW
  - `...04-20_Refactoring CIS application into modular structure.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Missing archive audit**: System cannot be grounded in reality
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...acybuildfiles_x_cis_relationship_map_extraction_analysis.md`

### Missing Pipeline**: The most significant gap is the missing draft-to-project pipeline.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `..._Master_Handoff_files/CIS_Handoff_Review_Command_Session.md`
  - `...ction/functional_intents/idea_drafts_extraction_analysis.md`

### Missing `system_log.md`**: The system log file did not exist and was not being written to by pipeline commands.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`

### Pipeline Key Wiring:** Blocked by the need to define the pipeline API endpoints.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Dashboard ↔ Pipeline | Not implemented | Pipeline status not visible in dashboard
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Escalate**: Blocked by missing dependency → resolve dependency first
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...acybuildfiles_x_cis_relationship_map_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### 4. **The Drafter may not invent or materially alter the initiating goal.** If the Drafter identifies a gap in the intent, it may flag it for Eric but must not rewrite the goal to fill the gap.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `DEV-PIVOT-10_ADR-SEED-014_CONTRACT.md`
  - `DEV-PIVOT-10_ADR-SEED-014_CONTRACT.md:14`

### No formal escalation logic documented** — this is a gap
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0413_extraction_analysis.md`
  - `...s/cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Gap**: No integration between persistent model server and pipeline execution
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.28 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Intake is independent | Intake is blocked by verification deployment
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0408_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`

### Modifier Stack**: Blocked by mesh data system and execution pipeline
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### evidence is missing, Verifier sends OBJECTIONS back to Implementer.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `DEV-PIVOT-15_SESSION_OPEN_ITEMS.md`

### After: Registry must distinguish `available` (weights on disk), `loaded` (in GPU memory), and `unavailable` (weights missing or env broken).
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...tion/functional_intents/all_insights_extraction_analysis.md`

### Archive → Intelligence Bridge** — Not yet built.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`
  - `...ntents/hand_offs_cis_handoff_phase_d_extraction_analysis.md`

### Archived**: Not implemented (no deletion/archive logic)
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Filesystem Governance Gap**: CIS has no formal filesystem authority layer.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.26 — treat as NEW
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Missing `/mnt/archive`, `/mnt/models`, and `/mnt/cache` mounts.
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.28 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`

### Missing FINAL_JSON | Repair prompt, then fallback text scanning | Model produces analysis but no machine-parseable verdict
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `CIS_16_FAILURE_MODES.md`
  - `DEV-PIVOT-05_HERMES_INTEGRATION_ASSESSMENT.md`

### Layer 6 Agents**: Deferred to Phase G; blocked until Workflow System established
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.54 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...action/functional_intents/x_03_state_extraction_analysis.md`

### No validation for agent outputs** — No hallucination checks on agent responses
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.40 — treat as NEW
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`
  - `...nts/cis_plain_language_build_roadmap_extraction_analysis.md`

### Copy Prompt:** Pass = prompt generated with all fields; Fail = missing role or session context
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.22 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0547_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`

### Missing Governance Gap**: The minutes agent operates with zero governance - no validation, no provenance, no audit trail.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.43 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`

### Processing Profile**: The contract document for processing profile does not exist as a file.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.33 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Gap:** Who receives Architect output after human approval?
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Review Panel**: Approve, reject, edit, mark uncertainty, merge categories, add missing fields
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.25 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Approved Knowledge Records → Archive → Future Processing Reference**: Stored knowledge informs future work
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...tional_intents/x_cis_execution_layer_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Dependency Impact:** Record provenance is incomplete without prompt version linkage
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`

### Permission Enforcement**: Declared but not implemented - security depends on application layer
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.26 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...extraction/functional_intents/cis_db_extraction_analysis.md`

### Security model is unresolved** — dashboard has no authentication.
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.27 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### No hallucination controls documented**: L3 CIS Live Copy Prompt is operational but no validation of its output.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...tion/functional_intents/memory_store_extraction_analysis.md`

### Claude responded: All drives are mounted and the cache drive is missing from this output — which means /mnt/cache did not auto-mount after reboot.
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.38 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Go back to **Proxmox → VM 100 → Hardware** and add each missing drive.
- support: 2 statements across 2 document(s)
- nearest queue item 19 is only sim 0.17 — treat as NEW
  - `...26-04-21_Session close and handoff process clarification.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### # Transitional Implementations # Updated: 2026-04-29 # Purpose: Prevent temporary fixes from becoming invisible permanent architecture. # Every item here has a planned replacement. Track it explicitly.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.44 — treat as NEW
  - `...TP_Project_Primer/11_TRANSITIONAL_IMPLEMENTATIONS.md#r0`
  - `...n_backups_20260430/11_TRANSITIONAL_IMPLEMENTATIONS.md:0`

### This represents a **three-layer expansion** of the architecture: 1. **Input Layer**: Audio capture/upload added 2. **Processing Layer**: AI extraction and staging added 3. **Governance Layer**: Human review gate added 4. **Reporting Layer**: Timeline aggregation added
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...Intelligence_System_LegacyBuildFiles/X_02_MEMORY.md:145`
  - `...tant_master_prompt_version_41_extraction_analysis.md#r3`

### That's what the build plan needs to address. And that's what was missing from the previous assumed build plan. --- Before we go further, what are the things you wanted to address before the build plan rewrite? You said there were a few. Let's get them on the table so we're working against a complete
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.35 — treat as NEW
  - `...406-b978-6e0379ba80ea:Build plan rewrite preparation#r2`
  - `...at_transcripts/2026-04-23_Starting a new session.md:516`

### ``` This block is not supported on your current device yet. ``` Understood. Before the build plan rewrite, you have things to address first. Go ahead — what are they?
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...0-4406-b978-6e0379ba80ea:Build plan rewrite preparation`
  - `...an AI platform for professional project guidance.md:147`

### /its just that the eample and the replacement code is not identical with what is there. can you tell in the picture where I start and where I end Apr 22 Claude responded: Yes.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...86e-87a3-fbbd98f2b494:Model registry API implementation`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:252`

### Conversation history — If you're on claude.ai, check your past conversations. The code should still be in the chat thread where it was built. You can scroll back and copy it out. Browser cache — If you were on a web browser, the page may still be cached if you haven't cleared it. Rebuild from spec —
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `...Refactoring CIS application into modular structure.md:1`
  - `...efactoring CIS application into modular structure.md:14`

### Apr 22 Claude responded: Good question to resolve before locking the schema, because the answer changes the data model.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.30 — treat as NEW
  - `...04-23_Video preprocessing schema definition setup.md:54`
  - `...e_atlas/original_CISChats/CIS_Chat_2026-04_003.md:43#r1`

### Run the schema update above first, then confirm and I will write the ensure\_tables() additions.You said: I am confused, are we continuing to expand the db tables or are you rolling back to a file base structure.I am confused, are we continuing to expand the db tables or are you rolling back to a fi
- support: 2 statements across 2 document(s)
- nearest queue item 19 is only sim 0.26 — treat as NEW
  - `...at_transcripts/2026-04-23_Starting a new session.md:766`
  - `_archive/CIS_Handoff_2026-04-23_0434_ChAT.md:276#r1`

### 1. `source_unit` table status confirmed (exists or needs to be created alongside) 2. Schema confirmed — no further field changes 3. You say write it
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...hat_transcripts/2026-04-23_Starting a new session.md:77`
  - `_archive/CIS_Handoff_2026-04-23_0434_ChAT.md:23`

### The `schema_version` table stores a single integer. Simple column additions are handled declaratively by `_reconcile_columns()` (which diffs live columns against `SCHEMA_SQL` and ADDs any missing ones). The version-gated chain is reserved for data migrations and index/FTS changes that can't be expre
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.26 — treat as NEW
  - `Hermes Agent Full Documentation.md:10006`
  - `Hermes Agent Full Documentation.md:10008`

### it's fixed but I accidently removed the chat from the project
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...61:Hermes implementation for topology extraction issues`
  - `...a1b97644fdc7:Execution queue ownership layer deployment`

### You did not paste the error message or screenshot. What did you see? Paste the terminal output or share a screenshot and I will tell you exactly what to do.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...canonical build sequence and architectural dependencies`
  - `...pts/2026-04-22_Model registry API implementation.md:246`

### The traceback in the first terminal will show exactly what's failing. Paste it and I'll fix it. You said: Press CTRL+C to quit
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...l build sequence and architectural dependencies.md:1387`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:194`

### ## All other documents must defer to STATE.md for phase status.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...d-offs/X_Where Phases Are Defined (Current State).md:98`
  - `...ve_Intelligence_System_LegacyBuildFiles/X_03_STATE.md:4`

### This is a Phase 1 architectural decision that needs to be made and logged now:
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...at_transcripts/2026-04-23_Starting a new session.md:277`
  - `...at_transcripts/2026-04-23_Starting a new session.md:727`

### /mnt/projects/cis/PROJECT_CONTEXT_PACK_UPLOAD/HCP_05_NEXT_ACTIONS.md Updated next session queue (4→6 items), Immediate Queue (4→6 items), and deferred Phase 4B status note. /mnt/projects/cis/PROJECT_CONTEXT_PACK_UPLOAD/HCP_07_RECENT_HANDOFF.md Updated Immediate Next Action section with corrected 5-s
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `chatgpt_export/6a1c4ab1-f3ac-83ea-93ba-5b7550ed6e89#r4`
  - `hermes_session/v4impl/session_20260531_160314_2467ba/5.13`

### **Why:** This is the automation of what Eric did manually this session — Reviewer challenged, Eric carried to Implementer, Implementer defended, Eric carried back. The system should absorb this labor.
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.34 — treat as NEW
  - `CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md:14`
  - `DEV-PIVOT-15_SESSION_OPEN_ITEMS.md:8`

### **Right now — manual paste is the only method.** You copy the relevant section and paste it into whichever model you're talking to. That's the current workflow.
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.22 — treat as NEW
  - `...04-18_Session execution and image pipeline setup.md:985`
  - `..._Intelligence_System_v1/memory_additions_20260420.md:11`

### What I *can* do is produce everything needed so that running it is close to a single copy-paste operation. But someone has to be at the terminal.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.20 — treat as NEW
  - `...al build sequence and architectural dependencies.md:102`
  - `...canonical build sequence and architectural dependencies`

### 2. What failed or didn't work Nothing failed. This was a research and design session — one question, one comprehensive answer. The transcript is complete and clean.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...-24_CIS phase 1 intelligence extraction handoff.md:1133`
  - `...action_first_try/insights_First_Try/_all_insights.md:19`

### Output is valid when: - Every failure mode is specific and reproducible - Every proposed fix is concrete and implementable - The verdict is unambiguous — pass or fail, not maybe - At least three failure modes were tested even if none were found
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...l build sequence and architectural dependencies.md:1762`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_015.md:190`

### These will take a few minutes. Paste any errors that come up — success output can be skipped, just confirm when both are done. Apr 22 Claude responded: Both installed cleanly.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `...pts/2026-04-22_Model registry API implementation.md:899`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:699`

### if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor( std_logging.DEBUG ): # pragma: NO COVER _LOGGER.debug( "Created client `google.ai.generativelanguage_v1beta3.DiscussServiceAsyncClient`.", extra={ "serviceName": "google.ai.generativelanguage.v1beta3.DiscussService", "universeDomain": getattr( se
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...project/social_work_ai/01_CORE/moved_async_client.py#r5`
  - `swa_project/social_work_ai/01_CORE/async_client.py#r5`

### **Why:** Building around an unavailable capability would add complexity with no return. The manual workflow is fast when the UI is designed for it.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:38`
  - `cis_v1_vault/memory_additions_20260420.md`

### ## Object 3: Capabilities Manifest - **Purpose:** Authoritative list of actual system capabilities for validation. - **Lifecycle:** Created → Maintained → Validated → Updated - **Authority Source:** System architecture documentation. Must be maintained by developers. - **Related Objects:** Memory (c
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `..._04_20_ai_memory_capabilities_extraction_analysis.md#r3`
  - `...insight_record_2026_04_19_001_extraction_analysis.md#r5`

### Result: FAIL — 2 check(s) failed Blocking: YES — do not advance until resolved Logged to: /mnt/projects/cis/logs/verification_[log.md](http://log.md) eric@creative-vm:~$
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.43 — treat as NEW
  - `...-a83d-a4a21870b2d7:CIS execution layer phase 0 setup#r4`
  - `contracts/CIS_Verification_Layer_Contract_v1.md:33`

### The health and CLEAN claims — did it actually run the curls and the log grep, or assert it? I'd want to see the four `ok`s and the `CLEAN` from the log, since this is the second "confirmed" without output attached. Probably true given the reverts were real, but this is the one conversation where con
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...f5b-5c39-4e77-8476-521153c1e51a:Project files update#r1`
  - `...f5b-5c39-4e77-8476-521153c1e51a:Project files update#r2`

### oh, I thought you were just asking if the enforcement works.Let me know if these files answer the question. 8:31 PM
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.34 — treat as NEW
  - `...ting up multi-panel control plane for model observation`
  - `claude crystallizes the vision.txt:153`

### **The core principle that prevents re-bricking: every guardrail ships with its own-off switch tested *before* the guardrail is trusted.** Today's hook had no escape hatch — that single absence is what turned a guardrail into a trap. So my non-negotiable rule: you never deploy a blocking gate until y
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.32 — treat as NEW
  - `...f5b-5c39-4e77-8476-521153c1e51a:Project files update#r1`
  - `...f5b-5c39-4e77-8476-521153c1e51a:Project files update#r2`

### **Gate requirement:** No gate blocks on `rejection_rationale`. It is populated as part of normal deliberation. The Eric Gate briefing surfaces any `rejection_rationale` rows for the active trail — Eric sees what was considered and rejected before approving the chosen path. An empty table is visible 
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.45 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_1_DESIGN.md:108`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_1_DESIGN.md:63`

### [asked] I don't quite follow what claude is talking about here. can you help me understand and follow up on this issue. The bypass is gone. §3.2 now rejects with 409 instead of auto-creating, and the rationale is stated correct... The reason this defect got as far as it did is that it satisfied the 
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.41 — treat as NEW
  - `...bcd-4be2-a60a-dd490fccbe35:Awaiting ChatGPT proposal#r2`
  - `...session/glm-reviewer/session_20260614_172934_5046b0/9.3`

### ### Missing Governance: 1. **Template Governance**: Rules for template instantiation not defined. 2. **Domain Governance**: Rules for domain instantiation not defined. 3. **Phase Governance**: Rules for phase transitions not defined. 4. **Category Governance**: Rules for category definition not defi
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.30 — treat as NEW
  - `...app_concept_workflow_template_extraction_analysis.md#r2`
  - `...lopment_system_architecture_7_extraction_analysis.md#r2`

### Deferred items logged → Session start surfaces them → Verification completed → No item forgotten
- support: 12 statements across 1 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### implementation_artifacts | No | **Deferred-unscheduled** — no v2.0 tier
- support: 8 statements across 1 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `PLAN_RECONCILIATION.md`

### Missing Runtime Bridge: Review Feedback to Implementation Process
- support: 6 statements across 1 document(s)
- nearest queue item 16 is only sim 0.43 — treat as NEW
  - `...unctional_intents/adversarial_review_extraction_analysis.md`

### The dashboard architecture has a fundamental flaw**: It attempts to load local filesystem data from a local HTML file, which is blocked by browser security models.
- support: 6 statements across 1 document(s)
- nearest queue item 22 is only sim 0.30 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Not implemented**: Queue.py does not contain knowledge formation logic
- support: 5 statements across 1 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### SCP is a critical path dependency** — Without SSH key configured, the push operation fails silently.
- support: 5 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### UI Redesign Before Frontend Modularization:** The frontend modularization is also deferred until the UI redesign (mockup integration) is complete.
- support: 5 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Gap**: No mechanism to improve retrieval based on reconciliation outcomes
- support: 4 statements across 1 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### The most critical architectural gap is the missing governance layer** for AI self-description, capability claims, and memory limitation disclosure.
- support: 4 statements across 1 document(s)
- nearest queue item 21 is only sim 0.44 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Conflict Escalation Loop:** Conflict identified → Cannot resolve → Appended to conflict register → Deferred → Next audit → (repeat until resolved)
- support: 4 statements across 1 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### PASS WITH WARNINGS:** All required files present, phase-required streams present, optional streams missing or excluded files present
- support: 4 statements across 1 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Material Validation**: Check for missing textures, invalid shaders
- support: 4 statements across 1 document(s)
- nearest queue item 3 is only sim 0.20 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### No validation layer → model routing cannot escalate properly
- support: 4 statements across 1 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`

### Session panel | Initialize session with handoff package | Not implemented | ADR-048 Build 7
- support: 4 statements across 1 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Build Impact**: L2 semantic verification of execution contract deferred to next session.
- support: 4 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Idempotent migrations are possible**: The script can be re-run safely, adding missing columns without data loss
- support: 4 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`

### Every reaction must be**: correct, refine, accept, reject, or add missing structure
- support: 4 statements across 1 document(s)
- nearest queue item 11 is only sim 0.32 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`

### Correction feedback path is missing** — ADR-006 implies multi-pass extraction with corrections feeding back, but no mechanism exists.
- support: 4 statements across 1 document(s)
- nearest queue item 13 is only sim 0.36 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### Primer update correction | Provenance validation → Missing provenance → Corrected update | Negative feedback | Stable
- support: 4 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Prerequisite for remote field access workflow and full tunnel activation.","phase":"deferred","priority":3}' | python3 -m json.tool
- support: 3 statements across 1 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Conflict Panel**: Unresolved conflict display and logging interface
- support: 3 statements across 1 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`

### 15_INHERITANCE_INDEX.md**: Not yet populated, blocked by build plan rewrite
- support: 3 statements across 1 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### L1 PASS → L2 rerun:** Deferred for operator abstraction flow
- support: 3 statements across 1 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### The fix required identifying that state variables (`showResolve`, `solution`, `decidedBy`) and a `resolve()` function existed but the JSX that renders when `showResolve` is true was simply missing.
- support: 3 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### VETO, RETURN_TO_DRAFT | Deferred to full Component 3 implementation.
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `CIS_TIER_11_UI_USABILITY_SPECIFICATION.md`

### Conflict register must be indexed by: issue, status (open/resolved/deferred), affected files.
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Gap**: No full-text search, no category tags, no date range filtering
- support: 3 statements across 1 document(s)
- nearest queue item 1 is only sim 0.45 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap:** Storage rules for inheritance relationships not defined
- support: 3 statements across 1 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Gap:** No defined quality standards for sound assets
- support: 3 statements across 1 document(s)
- nearest queue item 18 is only sim 0.34 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Runtime Impact**: Snapshot operations fail silently with misleading error messages ("current guest configuration does not support taking new snapshots"), requiring diagnostic steps to identify blockers.
- support: 3 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`

### Missing Runtime Bridge: Hermes to Approved Tools/Scripts
- support: 3 statements across 1 document(s)
- nearest queue item 20 is only sim 0.50 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Pre-Creation Config Check**: No validation layer for config.py constant before path creation
- support: 3 statements across 1 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`

### Permission Validation Engine**: Referenced but not implemented
- support: 3 statements across 1 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...ntents/1775995115163043436_x_control_extraction_analysis.md`

### ViewLayer Validation**: Check for missing collections, invalid render passes
- support: 3 statements across 1 document(s)
- nearest queue item 7 is only sim 0.26 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### This reveals a communication gap that must be bridged by the Session Initialization Layer.
- support: 3 statements across 1 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Architectural Significance**: The intake layer for ADR-048 (handoff package builder) is not yet built.
- support: 3 statements across 1 document(s)
- nearest queue item 5 is only sim 0.22 — treat as NEW
  - `...ional_intents/10_operational_reality_extraction_analysis.md`

### States**: Incomplete (some files missing), Complete (all files present), Loaded (all files loaded into memory), Analyzed (corpus has been analyzed)
- support: 3 statements across 1 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Pipeline keys are not wired** — Stream Deck pipeline and knowledge keys are placeholders only.
- support: 3 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### The constitutional recognition of the human as an architectural gap is perhaps the most significant discovery — it reframes all current human-in-the-loop operations as temporary debt to be systematically resolved through abstraction layers, not as permanent design features.**
- support: 3 statements across 1 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Architectural Significance**: The document explicitly identifies that execution rules, discovery-driven structure formation, reinforcement through review, and workbench behavior are **missing** from current documentation.
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.39 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Gap**: Need a Claim Audit Panel in the application surface
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`

### Gap**: Orchestration of multi-pass extraction across intelligence tiers is not defined.
- support: 3 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### No error handling exists for the dashboard**: The infinite spinner indicates a missing error state in the dashboard's state machine, providing no feedback to the user about what went wrong.
- support: 3 statements across 1 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Flask dashboard**: Deferred — 2736-line monolith needs refactoring
- support: 3 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`

### Deferred Frontend Integration**: Dashboard changes are explicitly deferred to the next session, creating a temporary gap where the schema exists but the UI cannot create records with the new fields.
- support: 3 statements across 1 document(s)
- nearest queue item 10 is only sim 0.25 — treat as NEW
  - `...nts/adr_041_artifact_registry_schema_extraction_analysis.md`

### L2 validation: PASS for execution contract (deferred), UNCERTAIN for governance contract (acceptable)
- support: 3 statements across 1 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Runtime Impact**: L2 has no explicit temperature setting - this is a potential governance gap
- support: 3 statements across 1 document(s)
- nearest queue item 22 is only sim 0.27 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### Dashboard insight capture → Database | Not implemented | Cannot capture from dashboard
- support: 3 statements across 1 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`

### Transitional Gap Schema**: Needs formal definition with fields for gap type, severity, target resolution, status
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Condition**: Verification fails due to incomplete constraints
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Required file validation:** Fail if STATE.md, SYSTEM_BLUEPRINT.md, or MASTER_ARCHITECTURE_MAP.md missing
- support: 3 statements across 1 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Task API:** Accepts `phase` field with values: deferred, backlog, active, completed
- support: 3 statements across 1 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Not implemented**: No review/promotion states in extraction_runs
- support: 3 statements across 1 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Runtime Impact**: No validation that `source_id` corresponds to an ingested file before pipeline execution.
- support: 3 statements across 1 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...traction/functional_intents/pipeline_extraction_analysis.md`

### Gap:** Memory extraction schema is system-managed and not controllable.
- support: 3 statements across 1 document(s)
- nearest queue item 18 is only sim 0.40 — treat as NEW
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Verification ↔ Operator Abstraction**: Verification complexity exposed missing operator abstraction, but operator abstraction requires verification pipeline understanding.
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Missing exclusion → Cancel → Reconfigure**: Impractical backup size triggers correction
- support: 3 statements across 1 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`

### Commit Route is Missing**: The most critical gap — approved drafts cannot become canonical knowledge.
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`

### Missing Action Endpoints**: The approval flow is incomplete - only listing exists, no approve/reject actions
- support: 3 statements across 1 document(s)
- nearest queue item 5 is only sim 0.41 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Container Start Fails**: If the bind mount directory does not exist, the container fails to start with "Script exited with status 9".
- support: 3 statements across 1 document(s)
- nearest queue item 14 is only sim 0.37 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`

### work by actively trying to find failure modes, edge cases, missing
- support: 2 statements across 1 document(s)
- nearest queue item 9 is only sim 0.23 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Exit codes: 0 = success, 1 = inventory file missing, 2 = all files failed
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.39 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### Missing Merge Script**: Blocks auto record population
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Cloudflare full tunnel — deferred feature, should be a task with `deferred` status
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Missing Validation Layer**: There is no validation that the reconciliation accurately represents the parallel responses, creating a trust gap.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### GAP**: No mechanism to detect when registered sources are modified
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...raction/functional_intents/librarian_extraction_analysis.md`

### The single largest architectural gap is the **missing queue subsystem formalization**.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Missing Benchmark Infrastructure**: Blocks visual output certification
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`

### Missing Staging Directory**: Causes immediate exit with error
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `.../functional_intents/primer_update_v2_extraction_analysis.md`

### Missing Validation Layer: Phase Completion Validation
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Missing parent directory → Create parent directory → Create register → Append entry
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.20 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Missing phase-required stream → blocks phase-specific execution
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.40 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Missing source**: Blocks job creation with 400 error
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### Missing Content Validation**: No verification of course content quality
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Model registry schema**: Exists but Qwen cannot be PATCHed active — schema is incomplete without weight path field
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`

### None identified**: No validation layer between AI inputs and knowledge capture
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### Question Lifecycle**: Open questions have states (OPEN, RESOLVED, IN PROGRESS, DESIGNED NOT BUILT)
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Source File Existence**: No validation that source_path exists before processing
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...on/functional_intents/cis_preprocess_extraction_analysis.md`

### 2026-04-18T10:37:58.490327+00:00 | ERROR: Missing dependency: No module named 'qwen_vl_utils'
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### The placeholder path `/path/to/downloaded/` in the git copy command was taken literally, causing a "No such file or directory" error.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Transitions**: Pending → Validating → Complete/Incomplete/Failed
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.43 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Runtime and primer WILL diverge silently over time without audits.
- support: 2 statements across 1 document(s)
- nearest queue item 9 is only sim 0.22 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### Validation Rule | Not defined per stage | Quality control incomplete
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`

### This tells us whether video preprocessing and extraction are stubbed, partially implemented, or missing entirely — and that determines whether we're one afternoon of work away from a viable proof of concept or facing a deeper gap.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.18 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### "CRITICAL: missing builder_model_id was not detected — "
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### 10 | Missing status reader artifact | Added tools/eric_gate/show_status.py (Section 13)
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### Absent or not root-owned → STOP: "/opt/cis-control missing/not-root — trust root must be
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.30 — treat as NEW
  - `MINIMAL_WORKER_LAUNCH_PROOF_v2.md`

### Async Synthesis Bridge**: HHR-016 not implemented; no async job + polling mechanism
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### BLOCKED | Dependency missing, cannot proceed | → CLOSE (with blocker logged)
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### Batch curl commands with `&&` chaining fail silently on first error, preventing subsequent posts.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.20 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Missing documentation layer | Branch notes via CIS Live sessions | Three-field lightweight format
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`

### Brush**: Texture validation prevents missing references
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.19 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Build workbench**: Not yet built — interface for build sequence management
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`

### No Review Logic**: State transitions are not enforced or validated
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.46 — treat as NEW
  - `...extraction/functional_intents/cis_db_extraction_analysis.md`

### CIS Live Dependency:** CIS Live is designed to solve the multi-model collaboration gap, but CIS Live was not operational during the session where it was being used as a collaboration tool.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`

### Capture list | List of `.md` files in `captures/` | **NOT IMPLEMENTED**
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.29 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### The component status taxonomy is formalized**: OPERATIONAL, OPERATIONAL/TRANSITIONAL, OPERATIONAL/RISK, ACTIVE, PRE-DRAFT, LOCKED, MISSING.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...intents/archive_04_active_components_extraction_analysis.md`

### Connection Management Gap**: The connection factory creates new connections per call with no pooling, transaction management, or lifecycle management - a significant operational gap.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `...action/functional_intents/connection_extraction_analysis.md`

### Architectural Significance**: Executor worker is a stub that does not call any model and generates placeholder output
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`

### DEFERRED** | WIAS full operationalization | ⬜ After CIS complete
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `DEV-PIVOT-06_BUILD_DIRECTION.md`

### MCP is deferred to after this stack is operational.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...sponse_to_vscode_obsidian_and_github_extraction_analysis.md`

### Discovery**: Draft → Review → Gap Identification → Resolution → Re-review
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Architectural Significance**: The Downloads watcher's runtime model (daemon vs Flask-started) is unresolved, creating a process architecture gap
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Error Handling is Silent**: Malformed records are silently skipped, creating invisible data loss.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Error handling blocked by error_state structure**: Cannot handle errors without error_state implementation
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...intents/cis_source_manifest_contract_extraction_analysis.md`

### Step 4: If deferred items exist → display items → require resolution
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Execution → Intelligence | Core Tool Stream | Intelligence Layer | Not yet built
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Exit codes: 0 = success, 1 = graph file missing, 2 = contradictions found (non-zero for CI gating)
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### File map creation | Document exists with all files listed | Missing files; incorrect status
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.34 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Missing:** Explicit interface between intent detection and AI state machine
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Missing:** Explicit interface between constraint monitoring and project planning
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### The gap between foundation/setup and application layer is now documented
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Gap**: Form strip removal created dependency on syntax integrity
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`

### Gap**: No defined application interface for action tracking
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.20 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Gap**: No defined routing for UNCERTAIN verdicts
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Gap**: No defined source quality assessment before processing
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### Gap**: No validation for task priority ranges or phase values
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap**: No automated orchestration of content updates
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`

### Gap**: No mechanism for parallel mediation of multiple captures
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap**: No visual workflow map showing where user is in the lifecycle
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap:** Manual file-gathering burden not yet automated
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Gap:** No validation that execution matched handover
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Gap:** Who detects trigger points for Architect invocation?
- support: 2 statements across 1 document(s)
- nearest queue item 11 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Remote Access → Heavy Compute Jobs**: Blocked by GPU requirement
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`

### Missing SSH Key:** If the SSH key is not set up, the push-to-live-site feature will fail.
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.23 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Architectural Significance**: Intake layer not yet built - human manually transfers structured content
- support: 2 statements across 1 document(s)
- nearest queue item 11 is only sim 0.33 — treat as NEW
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Intake Retry**: If project_id missing, operator must resubmit with project_id
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`

### Architectural Significance**: The unified control surface (Layer 8) is explicitly deferred until underlying systems are mature
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.23 — treat as NEW
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`

### Mediation Notes as Placeholder**: The mediation notes section exists as an empty structure, awaiting integration with a mediation workflow that doesn't yet exist.
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`

### Missing Intelligence Layer**: Sound operations cannot access structure or transformation
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.25 — treat as NEW
  - `...l_intents/x_11_sound_stream_expanded_extraction_analysis.md`

### Missing Slot 1**: Returns 503 BLOCKED for L2 operations
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Missing ViewLayer configuration**: Blocks render pass execution
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.21 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Missing node tree compilation**: Blocks shader/geometry evaluation
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Missing `command` field on a task blocks the `/run` endpoint (returns 400).
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`

### Missing Contract**: Extension validation, size limits, content-type verification, malware scanning
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### Missing**: Rules for validating across multiple sources
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`

### Preprocessing Validation**: Validation of preprocessing normalization quality not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`

### Missing Columns:** `superseded_by`, `version`, `author`, `tags`, `category`, `references`
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.42 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### No Content Validation**: No validation that new content is valid primer format
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.22 — treat as NEW
  - `.../functional_intents/primer_update_v2_extraction_analysis.md`

### No consistency checks | No validation that captures are complete | **MISSING**
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### No validation for confirmation of CONTROLLED actions
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `...raction/functional_intents/x_control_extraction_analysis.md`

### Open Questions Board**: Shows all open questions with status
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Output Validation**: Requirements defined but implementation deferred
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`

### Plugin Compatibility Validation**: No validation logic defined.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...action/functional_intents/myproject3_extraction_analysis.md`

### Plugin Enablement as State Machine**: Plugin enablement is now recognized as a state machine with states: Enabled, Disabled, Resolved, Unresolved.
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `...action/functional_intents/myproject3_extraction_analysis.md`

### Population deferred until operational necessity.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Primer Review:** Current, Stale, Updated, Deferred
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Questions**: `OPEN` → `DESIGNED, NOT YET BUILT` (alternative path)
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Runtime Impact**: Queue-backed operator routing exists but incomplete; worker-status endpoint operational
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.40 — treat as NEW
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### Related Objects:** Component, Decision, Gap, Risk
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Reorganization**: Blocked by file map creation and knowledge record resolution.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Runtime Impact:** Phase D validation checks for Intelligence Stream inclusion; missing stream blocks execution
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Runtime Impact**: Script will silently fail or capture garbage if selectors change
- support: 2 statements across 1 document(s)
- nearest queue item 9 is only sim 0.21 — treat as NEW
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Runtime Impact:** Deferred — lower priority than decision logging, run logging, and review UI
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Architectural Significance**: Runtime Service Ownership Layer has a known operational gap where Slot 1 requires manual start despite automation elsewhere
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.25 — treat as NEW
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### Segment integrity | No validation on creation | Data integrity risk
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.29 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Selection Layer** blocked by Viewport Navigation Layer
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.24 — treat as NEW
  - `...lender_2_80_fundamentals_transcripts_extraction_analysis.md`

### Sequence validation service** - Not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`

### Exception Handling**: Silent `pass` on errors — hides corruption, missing files, or permission issues.
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.33 — treat as NEW
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### Slot 1 Validation**: No validation that Slot 1 is running before L2
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### States**: Idle, Lock acquired, Phase 1 applying, Phase 2 applying, Complete, (MISSING) Rolled back, (MISSING) Failed
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Stream execution rejected if dependencies unresolved
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...7059416496004_x_cis_relationship_map_extraction_analysis.md`

### Trust Failure**: Snapshot corruption or incomplete state capture
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.33 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`

### Type-specific commit handlers**: Not yet built; required for full automation
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Unresolved Application Surface:** cis-log API or interface for ADR logging
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.28 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Workflow Execution | Completed stage with output | Incomplete step requiring refinement
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`

### `PENDING_PROCESSING`: File awaiting downstream processing (not implemented)
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### `cis_classify.py text__all_insights__001`: Phase 1 pipeline execution (deferred)
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`

### Description**: Display session status (Initializing, Ready, Incomplete, Failed) at all times
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Missing Runtime Bridge: Memory Locking**: There is no defined mechanism for locking the memory file to prevent concurrent write conflicts.
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/memory_extraction_analysis.md`

### cis-log command is a foundational prerequisite.** Without it, no implementation session can complete its handoff.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...on/functional_intents/implementation_extraction_analysis.md`

### Runtime Impact**: 0 verifications and 0 FAILs this session from build actions, but cumulative counts show 568 verifications and 41 unresolved FAILs
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.44 — treat as NEW
  - `..._intents/cis_handoff_2026_05_02_0558_extraction_analysis.md`

### Section separation needs a visual gap/divider between SESSION START and SESSION CLOSE
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.26 — treat as NEW
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`

### The file also exposes a missing runtime requirement: CIS needs a formal **session rehydration protocol**.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_010_extraction_analysis.md`

### ADR-024/025 implementation | Rate limit, governance priority | Deferred 3 sessions
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`

### Build Impact:** Deferred work includes full transcript archaeology.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### Build Work Layer**: Blocked by Live Session Infrastructure
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`

### Conflict archive learning | Resolved conflicts → Pattern analysis → Better prevention | Learning loop | Not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Gap**: No defined test for context length, reliability, response format, bounded task performance
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Gap:** There is no defined routing for continuity fallback.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Live Session Resolution Loop**: If Live session is unresolved, note in Notes field
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`

### Missing**: No project ID, idea ID, or context identifier attached to uploads
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### No cross-capture chunking | No linking between related captures | **MISSING**
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### No supersession tracking | Lineage gap — cannot track decision evolution | MEDIUM
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.28 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### The object model is incomplete** — missing author, project linkage, supersession, versioning, and audit trail
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Resolve Form**: Missing but required; must support session resolution, handoff generation, ADR capture
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.19 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Runtime Impact**: If file is not attached, session context is incomplete.
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`

### Build Impact**: Embedding/vector DB implementation deferred; retrieval text generator heuristic acceptable
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Gap Acknowledgment**: If corpus is incomplete, gaps must be explicitly acknowledged
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.42 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### 2_CIS_REORIENTATION.md versioning**: Needed but deferred — reorientation may drift
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`

### After**: Sound creates assets that become knowledge references for future work, creating a feedback loop.
- support: 2 statements across 1 document(s)
- nearest queue item 20 is only sim 0.24 — treat as NEW
  - `...l_intents/x_11_sound_stream_expanded_extraction_analysis.md`

### Architect Panel:** Input area for ADRs + proposals, output area for gap lists/ADR drafts/risk flags
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Blocked by knowledge_spine availability and segmentation policy.
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.39 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Conflict resolution improvement | Dashboard visibility → Faster resolution → Better visibility | Positive reinforcement | Not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Contract panel | Browse/search contract files | Not implemented | Future contract surface
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.29 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Description**: There is no validation layer that checks if the corpus is complete before analysis.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Session archive learning | Completed sessions → Pattern analysis → Better handoff packages | Learning loop | Not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Exit codes: 0 = success, 1 = corpus file missing, 2 = DB write error
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### Gap**: Files are saved but not routed to any processor, indexer, or workflow
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### Gap**: No application surface for viewing or searching session transcripts
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Hidden Until**: Session handoff identified deployment gap
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`

### Insight categorization | Defined but not enforced | Unstructured insights
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`

### No indexing improvement | Index not updated based on usage | **MISSING**
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Research Module**: Not built — agent-based categorization not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.45 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Dependency Impact**: Without formal queue definitions, the orchestrator cannot handle task prioritization, retry logic, crash recovery, or deferred execution.
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Missing intake layer**: Blocks automated content ingestion.
- support: 2 statements across 1 document(s)
- nearest queue item 11 is only sim 0.38 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`

### The "next step" is printed to stdout but not enforced or automated.
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`

### Build Impact**: Agent tab wiring is deferred — not a Phase 1 concern.
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.51 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`

### Missing Agents Module**: The Agents module is a placeholder.
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.53 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Manifest Gap Identified**: Session manifests exist as chat downloads only, with no automated pipeline to the canonical drop location — a significant gap in the verification architecture.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`

### Automated Handoff Copy:** Proposed but not implemented — session close should auto-copy handoff to `/mnt/projects/cis/handoff/`
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Missing Execution Bridge Layer prevents reliable cross-layer coordination
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`

### Dependency Impact**: All stream docs are incomplete without execution bridge docs.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.48 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Session close orchestration is blocked by**: Database, `cis-log`, `cis-start`, manifest system, knowledge record system, git integration, vault setup
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Draft intake | No validation (human copy-paste) | Schema validation at /api/drafts/stage
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Gap**: No automated validation engine that checks extraction output against contract rules
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Governed state registry and visual orchestration deferred to build plan rewrite.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`

### Tradeoff on what to build first: fix the auth config (5 min, unblocks orchestrator.py path entirely) before building the proposal-dispatch bridge — because draft's report suggests orchestrator.py may already run the full Drafter→reviewer loop once authed, which would mean impl's "missing bridge" exi
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `Claude Roadmap Audit 20260624.txt`

### Workflow Layer**: Blocked by missing execution bridge and source type schema
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Missing Feedback Loops**: No mechanism to learn from approval decisions to reduce future approval burden
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### No selector improvement loop | Broken selectors not automatically updated | **MISSING**
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Orchestration Layer Is a Foundational Gap:** Must be built before automated workflows can function.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `...tents/1776042143355379182_x_03_state_extraction_analysis.md`

### Orchestration is NOT implemented in Phase C.** It is defined for later phases.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Application Layer**: Blocked by pipeline and storage availability
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...76106784688228799_x_cis_workbench_v1_extraction_analysis.md`

### Unresolved Orchestration: Conditional Runtime Repo**: The logic for conditionally committing the runtime repo is not defined.
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Queue Worker Reload Bridge**: Missing verification step between patch deployment and runtime
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`

### Missing**: No sync endpoints for `transformers`, `comfyui`, `vllm`, or `api_remote` runtimes
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Current Gap**: Dashboard loads from filesystem; Flask serves public endpoint
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.26 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Grepping the archive confirmed it was missing from both the current modular dashboard and the original monolith — this was a feature that had never existed at any point in the build, not something lost during the refactor.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### /api/conflicts | Not implemented | GET/POST endpoints | Future
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### /api/session/initialize | Not implemented | POST endpoint | ADR-048 Build 7
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### 3.4 — Quick Capture panel on Advisor Chat | **Deferred-unscheduled** | Depends on notes capture (2D).
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `PLAN_RECONCILIATION.md`

### ADR Panel**: Depends on decisions API — working; sort/filter deferred
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.25 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`

### Dashboard ↔ System Log**: Displays operational history (deferred)
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### Gap:** No UI to add decisions; six decisions from this session unrecorded
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.30 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Gap:** No route from dashboard to decisions table
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Poll endpoint**: `/api/queue/job/<N>` referenced but not implemented in this file
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Router not implemented | No task classification or model tier selection | HIGH
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### Broken when**: ADRs fail to post (missing fields), decisions not documented
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### "ADR-040 synthetic: missing auditor model name is rejected",
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### 14_GOVERNANCE_GLOSSARY.md**: Not yet populated, blocked by build plan rewrite
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### Resolution:** Live verification confirms ADR-SEED-017 does not exist in project_decisions.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`

### Blocked By**: Session transcript extraction, contract specification documents
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Run Validation** — no validation that extraction runs are logged
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Gap**: Dual-machine file sync conflicts are identified as risk, but no conflict resolution governance is defined.
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.26 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### No governance for AI inference fields** — Labeled as proposals but no validation rules
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `...nts/cis_plain_language_build_roadmap_extraction_analysis.md`

### No governance for DAM view operations** — Promote, Link, Demote have no validation rules
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `...nts/cis_plain_language_build_roadmap_extraction_analysis.md`

### Non-critical failures** (column missing, test failure): Continue to log, then `sys.exit(1)`
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.29 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### Post the 4 deferred tasks to the DB now — that's just 4 more curl commands.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Should notes capture (2D) be explicitly scheduled as Tier 7.5 or Tier 8 prerequisite rather than deferred to Tier 10?
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.23 — treat as NEW
  - `PLAN_RECONCILIATION.md`

### Missing Spine Data**: `/api/spines/<id>/nodes` returns 404 if spine_id not found
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.52 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`

### Action**: Check execution_jobs table for incomplete jobs
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Schema Definition**: Reduction record, gap, and debt schemas must be defined before systematic tracking
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.32 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Blocked by:** Database must have `live_sessions` and `live_rounds` tables
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...ents/cis_dashboard_monolith_20260420_extraction_analysis.md`

### DB schema constraints are invisible** — NOT NULL and other constraints fail silently without surfacing in error messages.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### Domain configuration loading | Configuration validated and activated | Configuration invalid or missing dependencies | Retry with corrected configuration
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Incomplete question→file routing table:** AI systems cannot reliably route queries.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`

### "Audit round: roster check deferred (ADR-042 not yet implemented)",
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### No Integrity Validation**: No validation that database state is consistent after insert
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.20 — treat as NEW
  - `...unctional_intents/ingest_extractions_extraction_analysis.md`

### print(f" Running schema steps anyway to apply any missing columns.\n")
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.25 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_migrate_041.py`

### Step 5 blocked by**: Step 4 completion (verify_contract end-to-end) — COMPLETE
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_1852_extraction_analysis.md`

### Extraction Quality Gap → Multi-Pass:** missed characters on X-Men 001 triggers multi-pass requirement.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### "Audit response is missing or too short — full response must be logged verbatim"
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### "CRITICAL: missing dependencies field was not detected — dependency check is broken"
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### "CRITICAL: missing model name was not caught — auditor identity check broken"
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### 9 | Missing test fixture artifact | Added tools/eric_gate/seed_test_fixture.py (Section 13)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.41 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### Requirement:** User must be able to see when AI actions are blocked by alignment check
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Step 3: If no failures → check for deferred verification items
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.29 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Discovery 1: Verification Gap Between Reported and Actual Work
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Fail = missing verification status or unresolved conflicts not logged.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### No decision audit trail (decision logging form missing)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`

### Previous**: verification_status may have been implicit or missing
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Validate phase-optional streams present → note if missing
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### The missing piece is not model size anymore** — it is designing the feedback and acceptance structure around it.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...2471347_x_cis_discovery_workbench_v1_extraction_analysis.md`

### Description**: Incomplete context leads to hallucinated architectural decisions.
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.37 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Missing MASTER_ARCHITECTURE_MAP.md → blocks all execution
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Verification Complexity as Architecture Revealer**: The verification pipeline's complexity was not just a technical problem — it was an architectural signal revealing missing abstraction boundaries.
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Live sessions are architectural debt**: 5 open sessions (#002–#006) represent unresolved decisions that could affect Phase 1 design.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### Producer**: project state/workflow stage → track → return next steps/reminders/missing pieces.
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `...functional_intents/x_09_agent_stream_extraction_analysis.md`

### Swarm architectures deferred (future capability, not current build target)
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.25 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`

### Draft promotion to canonical** — Blocked by Phase 3 not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.34 — treat as NEW
  - `...extraction/functional_intents/config_extraction_analysis.md`

### Old Tier 7 (node 8, "Full Durable Router Pipeline") remains DEFERRED permanently.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### Intake Pipeline** — Phase 1 (manual JSON import) → Phase 2 (watcher service) → Phase 3 (commit layer, deferred)
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### It carries forward phase state, locked ADRs, completed work, next steps, open questions, and critical paths.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...nctional_intents/context_compression_extraction_analysis.md`

### Build Impact:** PM and DAM are deferred to Phase 8 (expanded application surface) with minimal scaffolding in Phase 4 (workbench).
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### CIS Live Fixes**: Blocked by filesystem cleanup (Next Steps 2-5)
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`

### Gap**: How Worker 1 determines next worker based on task type
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Multi-pass extraction | Adequate extraction quality | Extraction | Not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Phase 4B** — 12 files (3.4MB) downloaded, knowledge base extraction deferred
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.36 — treat as NEW
  - `CIS_CURRENT_STATE.md`

### task_queue schema, execution packet format, queue arbitration policy, retry queue strategy, deferred queue handling, queue replay/recovery, context assembly layer, role prompt packaging
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.30 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Runtime Impact**: Agent tier models are all in `discovered` status (Phase 4), meaning agent tabs will show empty or placeholder content until Phase 4
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.41 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Re-segmentation provenance:** `segmentation_run_id` field proposed but not implemented.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Explicitly deferred by Human Gate with logged rationale
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.36 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### Alignment logic, decision gates, parking lot for deferred ideas
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...tional_intents/x_01_system_blueprint_extraction_analysis.md`

### Source Model Tracking**: Model identity preserved but not enforced
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.29 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`

### Segmentation Pipeline**: Scene detection + duration fallback + transcript-assisted option (deferred to ADR-033)
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.22 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`

### No extension validation** - whitelist defined but not enforced
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.19 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### Gap 4 — No Contract Exists for Mapping CIS Tasks to Hermes Agent Tasks
- support: 2 statements across 1 document(s)
- nearest queue item 20 is only sim 0.60 — treat as NEW
  - `...tivation_session_extraction_analysis_extraction_analysis.md`

### Gap**: `approval_required` is hardcoded per task; no policy table
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.42 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Hook crash (segfault, missing interpreter):** In enforcement mode (production), fail-closed → exit 1, block all tool calls.
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Knowledge Layer is a Gap**: Despite being called "knowledge records," there is no knowledge formation, semantic indexing, or ontology enforcement.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Governance Layer**: Blocked by glossary trigger definition, inheritance surface process, filesystem zone classification
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Session Resolution**: Unresolved sessions detected; resolution enforced before archive; correction prevents drift
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### print("FAIL live_rounds table does not exist — ADR-040 enforcement cannot operate")
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.25 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_migrate_041.py`

### Cross-modal validation is missing.** There is no defined mechanism to ensure scene descriptions are consistent with extracted text, creating a hallucination risk.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`

### /mnt/cache/catalog | **DOES NOT EXIST** — needs creation (see §3.3)
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.30 — treat as NEW
  - `DOCKER_CONTAINMENT_PROPOSAL.md`

### Failure Modes**: Missing `Path` import (fixed), git push hang (temporarily disabled)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Missing `Path` import:** Blocks session close handoff write (fixed)
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.42 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Extraction Quality Gap:** Multi-figure scenes poorly handled.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.19 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Gap**: No defined interface between session completion and distillation trigger
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Runtime Impact**: If model is missing, extraction fails immediately.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`

### Session Close API**: Returns HTTP 500 on unhandled exceptions (e.g., missing import)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Distribution Governance**: Not yet defined; distribution pipeline deferred
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`

### No validation pipeline**: Title, concept, scope are accepted without validation rules
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...traction/functional_intents/projects_extraction_analysis.md`

### A9 | Missing required field returns error dict | cis_dispatch_drafter with empty topic | Returns dict with error key, no crash | Check error key present, no traceback
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Error returns | `{ "error": "<message>" }` if run_id missing, not Eric-approved, or dispatch fails
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Reviewer feedback loop visibility:** The reviewer returns OBJECTIONS with specific missing/incorrect files.
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.28 — treat as NEW
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Storage/VM capacity assessment (deferred per Eric's instruction, design §5)
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.52 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### Unresolved Storage Rules: Handoff Storage**: The handoff document has a dual storage path (VM disk vs.
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.36 — treat as NEW
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Hard Rejection**: Missing inputs, missing agent, missing key → HTTP error
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### The first real archive run will expose missing profiles and validation failures.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...onical_build_sequence_plain_language_extraction_analysis.md`

### Agent Object**: Execution layer still placeholder; agent roles, capabilities, lifecycle undefined
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.51 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Runtime Impact**: Missing or inactive agents return 404; no retry or fallback mechanism
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.42 — treat as NEW
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Prompt File Missing**: System exits with error message
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### Prompt Review State:** No validation that generated prompt is complete and correct
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`

### Contract State**: Missing → Drafted → Approved → Active
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`

### Extraction Layer**: Blocked by missing approval workflow
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.43 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Worker 4 (Verifier/Skeptic)**: Checks unsupported claims, missing provenance
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Missing Task Context**: Approval list lacks sufficient context for informed decision-making
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Missing**: Approval/rejection decisions should reinforce the AI's understanding of which tasks need human oversight
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Missing**: Approval list should be filterable by project or workflow
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Missing Authorization**: No access control on who can view or act on approvals
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### API key must be validated before any extraction** - System exits if key is missing
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### File permission**: Write permission denied → project creation fails silently (no error handling)
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.27 — treat as NEW
  - `...traction/functional_intents/projects_extraction_analysis.md`

### Processing**: Check schema conformity, unsupported claims, missing provenance, contract violations, safety/permission violations, whether frontier escalation needed
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Must Not Have**: Unsubstantiated claims, missing drift check, incomplete sections
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.41 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### No governance yet**: No validation of captured content, no provenance tracking, no hallucination detection at capture time
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.25 — treat as NEW
  - `...n/functional_intents/captures_readme_extraction_analysis.md`


## Already represented on the working queue  (4)

### Agent objects**: Librarian, Researcher, Teacher — defined in architecture but not implemented.
- support: 3 statements across 3 document(s)
- MATCHES queue item 21 (sim 0.63): IMPLEMENT THE ROLE THEORY INTO THE AGENTS. Eric's note, 2026-08-29, recorded
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### Agents (librarian, researcher, teacher, producer, guardrail, worker, orchestrator) are explicitly deferred until foundational layers (1-5) are stable.
- support: 2 statements across 2 document(s)
- MATCHES queue item 21 (sim 0.61): IMPLEMENT THE ROLE THEORY INTO THE AGENTS. Eric's note, 2026-08-29, recorded
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `...reative_Intelligence_System_LegacyBuildFiles/X_02_MEMORY.md`

### Agent and Application Streams are explicitly deferred.
- support: 2 statements across 2 document(s)
- MATCHES queue item 12 (sim 0.65): Stream agent completions instead of blocking on one call. Gateways support it
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Gap 7 — Local Model Backend Is Not Yet Proven for Hermes Agent
- support: 2 statements across 1 document(s)
- MATCHES queue item 20 (sim 0.63): Put a hermes agent INTO these working sessions (Eric's ask, 2026-08-28).
  - `...tivation_session_extraction_analysis_extraction_analysis.md`


## Single-statement recognitions — weakest evidence  (2892)

### Orchestration gap — the human is still the bridge — 464
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.22 — treat as NEW
  - `?`

### A cleaner inline superseded marker was noted as a future improvement but not implemented.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Find edge cases not covered by current validation rules
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.19 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### which you can see are separated by a small gap, contain your scene specific properties.
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.26 — treat as NEW
  - `_archive/Blender 2.80 Fundamentals Transcripts.md`

### ❌ What’s missing (this is the gap you’re feeling)**
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.19 — treat as NEW
  - `...ystem_LegacyBuildFiles/X_CIS_ WORKFLOW_EXECUTION SPEC v1.md`

### 👉 That level of detail does NOT exist in your current doc.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...ystem_LegacyBuildFiles/X_CIS_ WORKFLOW_EXECUTION SPEC v1.md`

### Purpose**: Documents active blockers - one note per unresolved issue
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `...is_predev_infrastructure_plan_claude_extraction_analysis.md`

### The four feedback loops, the WIAS multi-exit model, the AI inference layer, the execution layer gap, and the field authority rules are not features to list.
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.25 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### manifest && e('div', { style:{display:'flex', gap:8, marginBottom:8, alignItems:'center'} },
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.10 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Am I missing something that will allow this to work?
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.19 — treat as NEW
  - `_archive/_LXC container to sandbox the CIS_LIVE.md`

### Constraint:** If a workflow step cannot be executed without explanation, it is incomplete.
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### If `pdftotext` or `pdftoppm` are missing, install them:
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.19 — treat as NEW
  - `...yBuildFiles/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md`

### None of it can be deferred without creating exactly the placeholder problem you are describing.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Prerequisite | Required By | Impact if Missing
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.23 — treat as NEW
  - `...traction/functional_intents/projects_extraction_analysis.md`

### The Build_Sequence/README.md exists but is presumably a placeholder — it is the only file in that folder.
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.42 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### The existing HTML has a Live tab already in the tab bar — it just needs the real component replacing the placeholder.
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.10 — treat as NEW
  - `...04-20_Refactoring CIS application into modular structure.md`

### The following are explicitly deferred or constrained:
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.22 — treat as NEW
  - `_archive/CIS Formal Phased Construction Plan.md`

### This is exactly the gap you identified — the system has been building forward without all its foundations formally locked as files.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.37 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### What was left unresolved Work that was started but not finished.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### What you need to add to CIS (the real missing artifact)**
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `...uild_Sequence/3 Platform Chat/CIS_Pivot_Chain of Thought.md`

### 👉 **invalid outputs must FAIL, not pass silently**
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `_archive/CIS Formal Phased Construction Plan.md`

### Are open questions separated from confirmed facts?
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.22 — treat as NEW
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### Blocked Layer | Blocked By | Unblock Condition
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.33 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Claude responded: The /path/to/downloaded/ was a placeholder — I should have been more specific.
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Claude responded: The cache entry is missing from fstab — it was not saved when we edited the file earlier.
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.35 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Claude responded: The commands got concatenated — missing line break.
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.38 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_005.md`

### Claude responded: Yes — and that's a fundamental UX gap in what's been built.
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.25 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`

### Conflict Register Layer** - Unresolved contradiction tracking
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...itutional_memory_governance_revision_extraction_analysis.md`

### The Core Loop (This is what you were missing)**
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `...fs/X_How You Work With These Files (CIS Operating Model).md`

### This was explicitly deferred in the reorientation doc as a parking lot item.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### You said: we need to str=art figuring out how to close the gap you mention between the other tabs.
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.22 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### 004.md is the most significant gap — 1653 unread lines.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.35 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### 1432: e('input', { type:'text', placeholder:'source_id e.g.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.22 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### 9.10 Missing Application Surface: WIAS Filters
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_008_extraction_analysis.md`

### 9.7 Missing Application Surface: Real Model Status
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_008_extraction_analysis.md`

### AI assistance must not silently reclassify missing artifacts as “bureaucratic detours.”
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Accurate status is that changes were drafted but not implemented.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`

### Application Layer** blocked by uncertainty tracking
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...06699132426333_x_cis_discovery_model_extraction_analysis.md`

### Application Layer**: Blocked by missing pagination and filtering
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.39 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Approving updates with unresolved constitutional concerns
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### At line 1160 of the script there's a stray `)` — the closing of the scrollable thread `e('div', ...)` is missing a closing paren and has an extra one.
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.25 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Authority: Loop 4 correction — real execution revealed missing substrate layer
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Blocked from meaningful production use by missing run logging and review/promotion.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Build Impact**: Stage management system is not yet built.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Build States**: blocked (prerequisite missing), ready (all dependencies met), in-progress
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`

### Canonical placement of Obsidian readable mirrors remains unresolved.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.17 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`

### Concurrent requests**: Blocked by single-threaded design
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...nctional_intents/deepseek_mcp_bridge_extraction_analysis.md`

### Content-based draft classification**: Not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`

### Current implementation will fail silently on large datasets.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### DAM nav/surface is defined but not implemented.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.22 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### DAM usability is blocked by source/record list and unaffiliated filtering.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Deferred**: Tool installation postponed to later phase
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`

### Dependency Impact**: LLaVA rejected creates a gap in model availability; Qwen2.5-VL-7B as fallback creates failover path
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.43 — treat as NEW
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`

### Dependency**: POST fails hard if source_id is missing
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.30 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Discovery 2: The Execution Layer is the Missing Coordinator
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...ntents/phase_0_5_replan_orchestrator_extraction_analysis.md`

### Discovery 3: Queue Subsystem as Missing Formal Layer
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Does that cover what you mean, or is there anything missing from that list before I build it?
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### Does this match what you had in mind, and is anything missing before I seed it?
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.24 — treat as NEW
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### Dynamic model roster is decided but not yet built.
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### Eight specific elements are identified as missing:
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.33 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Everything after that was truncated — about 150 lines of the script are missing.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### Execution queue: NOT RUNNING — does not exist yet
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...hive/orientation_backups_20260430/10_OPERATIONAL_REALITY.md`

### File does not exist | Claude re-executes the write and produces a new manifest
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.38 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### From the screenshots, you now have the three things that were missing in the earlier attempt:
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `_archive/ChatGTP’s response to vscode, obsidian and github.md`

### Full application remains deferred, but early operator console is required.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Gap**: No content hash or source version tracking
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Gap**: No validation of record structure on read
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Gap: No Terminal-State Rules for Incomplete Work
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### If ffmpeg is missing we install both in one shot: bash
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.15 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### If manifest state wrong → update manifest or mark source incomplete
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### If not, we install what's missing and proceed.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### If record mirror missing/stale → rerun normalization
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.21 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### If true, that is a major unresolved variable for the 32B evaluation.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...orm Chat/vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md`

### If vLLM is simply missing from site-packages entirely, reinstallation is the right call and we do it cleanly into the existing environment at its new location.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.17 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### Integration Layer**: Blocked by missing application update cycle
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Intelligence scaling blocked by missing execution foundation.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`

### It cannot be deferred as documentation hygiene.
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.26 — treat as NEW
  - `...ild_plan_v_2_memory_capture_strategy_extraction_analysis.md`

### It is a missing substrate layer discovered through
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### It stores why understanding changed, what failed, what was assumed, and what remains unresolved.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Job progress**: Not implemented — no progress tracking
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### Key marker missing | Claude inspects and corrects the file, new manifest
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.29 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Missing Application Surface: Taxonomy Merge/Correction
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`

### Missing Deduplication**: No detection of duplicate courses across tutorial roots
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.20 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Missing Messages: Initial → Fetching → Validating → Return 404
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Missing Ontology Mapping**: No connection to WIAS domain structure
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Missing Progress Tracking**: No mechanism to track learning progress
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Missing Runtime Bridge: Human Override Protocol
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `...unctional_intents/adversarial_review_extraction_analysis.md`

### Missing SYSTEM_BLUEPRINT.md → blocks all execution
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Missing Update Detection**: No mechanism to detect changed/updated courses
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Missing Validation Layer: Cross-Modal Consistency
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`

### Missing `job_type` | Enqueue | 400 | "job_type is required"
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.28 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### Missing `source` | Enqueue | 400 | "source is required"
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### Missing base_path directories** cause groups to be silently skipped
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.30 — treat as NEW
  - `...raction/functional_intents/librarian_extraction_analysis.md`

### Missing canonical zone transitions**: Only inbox/inbox is currently valid
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`

### Missing config**: `WIAS_STAGES` not defined → all GET detail operations fail
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...traction/functional_intents/projects_extraction_analysis.md`

### Missing directory**: `PROJECTS_DIR` not created → all POST operations fail
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...traction/functional_intents/projects_extraction_analysis.md`

### Missing operability for non-operator users**: System cannot scale beyond current operator
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.21 — treat as NEW
  - `...intents/cis_handoff_current_position_extraction_analysis.md`

### Missing version control → runtime_scripts mirror.
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`

### Missing**: No link back to individual assistant responses in reconciliation record
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.28 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Missing**: No linkage to broader project state or other ADRs
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### Missing**: No review/promotion workflow for course quality
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Missing:** Formal definition of "intent" as a system object
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.23 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### New Layer**: Documents marked as "Optional/Later" represent deferred implementation
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.22 — treat as NEW
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`

### No Correction Feedback**: No mechanism to detect unresolved conflicts
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### No placeholder or hollow content detected: [YES / NO / PARTIAL]
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1_Addendum_A.md`

### No update/delete actions**: Not implemented in this file
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...traction/functional_intents/projects_extraction_analysis.md`

### No validation of record structure before processing
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.18 — treat as NEW
  - `...action/functional_intents/cis_review_extraction_analysis.md`

### No validation rule for whether an artifact is low-noise enough for primer exposure.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `...ild_plan_v_2_memory_capture_strategy_extraction_analysis.md`

### No validation that the application runtime exists
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.21 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### No validation** of `active_stages` alignment between project and records.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### None** — no validation or rejection; any content written is served
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`

### None**: No validation that conflict is real or accurate
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### None**: No validation that parsed fields are accurate.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Not implemented yet, but structurally implied:
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.32 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_015_extraction_analysis.md`

### Not implemented**: Entire content stored as single file
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.28 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Not implemented**: No promotion path from raw to processed
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Notes** — promoted from single-line input to expandable textarea with descriptive placeholder
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.12 — treat as NEW
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`

### Now send 005.md and we close out the last gap.
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.30 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Now update the ADRs.md in the vault to include the missing ones, then do a final git commit for the day:
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### Optional/Later Deferral**: Some components can be deferred
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`

### Output:** manifest terminal state or flagged incomplete state
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### Paste both outputs — that will tell us if the push is actually working or silently failing.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.20 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Placeholder detected | Claude fixes the content, rewrites, new manifest
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Pre-Review Validation**: No validation before ChatGPT review
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...l_intents/src_20260508_045512_16b932_extraction_analysis.md`

### Preserve current phase, active task, capabilities, and unresolved gaps.
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_010_extraction_analysis.md`

### Rationale**: Fills gap where neither operator nor execution layer owned scheduling or job tracking
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`

### Register Creation**: If missing, create with header
- support: 1 statements across 1 document(s)
- nearest queue item 19 is only sim 0.13 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Reject and redirect if concerns are unresolved
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.18 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### Remote access**: Blocked by stdio-only transport
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...nctional_intents/deepseek_mcp_bridge_extraction_analysis.md`

### Replace hardcoded Gemini/Claude/ChatGPT with dynamic model roster drawn from the Intel sidebar registry *(closes the decorative tab gap)*
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Requires an unanchored state for early or unresolved records.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Resolution**: No validation on `solution` or `decided_by` content
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### Risk**: Invalid status queries return empty results silently
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Risk: incomplete registration without notification
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.24 — treat as NEW
  - `...raction/functional_intents/librarian_extraction_analysis.md`

### Runtime Blocker: Missing source_id Returns 400
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Runtime Impact**: Interface is incomplete if material enters without structured output
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.18 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`

### Runtime Impact**: Synthesis requests may timeout if async not implemented; polling mechanism needed
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Runtime blocker:** Without wiring, the app visually implies intelligence capability that does not exist.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### SCP Retry** — Not implemented; single attempt with status reporting
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Source path and source identity must not be silently overwritten.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_015_extraction_analysis.md`

### Spreadsheet rows are structured source data, but it is unresolved whether they become:
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`

### Stating "None" when there is genuine ambiguity about whether the central antagonist is human or non-human is a quality gap.
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.18 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### Streaming responses**: Blocked by subprocess-based execution
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.53 — treat as NEW
  - `...nctional_intents/deepseek_mcp_bridge_extraction_analysis.md`

### TRANSITIONAL — partially implemented, gap between intent and reality
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.26 — treat as NEW
  - `_archive/orientation_backups_20260430/09_GOVERNANCE_STATE.md`

### That tells us whether video is in scope for this run or needs to be explicitly deferred with a documented reason.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### That will let us answer the open questions much more cleanly, especially:
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.20 — treat as NEW
  - `...orm Chat/vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md`

### That will show exactly what's attached and what's missing so we can restore it precisely.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.32 — treat as NEW
  - `...26-04-21_Session close and handoff process clarification.md`

### The `runs` state and `loadRuns` function never got injected — the replacement failed silently.
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.26 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### The batch likely failed silently because the `&&` chain broke on the first conflict.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### The broken file is missing one level of nesting that the strip provided.
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### The button toggles showResolve but the form with the solution textarea and submit button is missing from the render.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.12 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### The close action must surface incomplete source states.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### The issue must be a JS syntax error that silently kills the whole React app.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.19 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### The key behavior: AI runs first, proposes everything, you correct what's wrong or incomplete.
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Then run this to replace the broken line and add the missing content:
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### Third, what is genuinely missing and needs to be created as part of the Track 1 infrastructure build.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.25 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### This file does not define project-specific close fields, so that remains a gap.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### This is a critical gap — the entire review/promotion workflow is undefined.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`

### This is a known limitation that will miss non-standard filenames.
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`

### This is a known, unresolved runtime stability issue.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0836_extraction_analysis.md`

### This is the largest gap of the remaining updates.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Uninitialized** — kernel directory does not exist
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...raction/functional_intents/librarian_extraction_analysis.md`

### Unresolved Application Surface: Bulk Operations
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.25 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`

### Unresolved FAILs: [count — must be 0 to close cleanly]
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Unresolved Routing: Status Change Notifications
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.47 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`

### Update Status**: Change conflict status (OPEN→DEFERRED, etc.)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### ValidationResult object** — defined conceptually but not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.20 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Visual → Merge Bridge**: Not implemented (merge script missing)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.19 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### What remains genuinely unresolved** but isn't a cleanup problem — it's a build problem:
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### What's missing is a place in the app to surface and manage these floating records.
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.28 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`

### What's missing**: Graceful error handling for data loading failures
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Your LMS mental model is not outdated — it's just incomplete now.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_003.md`

### \- Flag any assumption not covered by the task packet
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...and the Phase PD Build Plan/CIS_Phase_PD_Build_Plan.docx.md`

### \- \[BLOCKER-001\] Description of unresolved issue
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.26 — treat as NEW
  - `...and the Phase PD Build Plan/CIS_Phase_PD_Build_Plan.docx.md`

### active application) is unknown, indicating a missing state documentation requirement.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### deferred work prematurely, or misrepresent the current phase boundary.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### generated, current, superseded, missing, invalid.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`

### illegal state transition for idea_note, and incomplete artifact clearing rule.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.37 — treat as NEW
  - `CIS_Creative_Intelligence_System_v1/Phase_PD/ADRs.md`

### missing `/data` failed → internal path created
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### missing mutability constraints, incorrect lineage cardinality.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `CIS_Creative_Intelligence_System_v1/Phase_PD/ADRs.md`

### what else is missing from the file that is making the process fail.
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.41 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### ��'��(@�Yr���.1�<�i�mu�@�y�'z� �#M�q�3C% ��gap��e��,Nռl�*:�Ɋ�:�W3��(j�$K�r���Y4�����qpNh��S[���"��VE����X�s�s�D��q}a��
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.15 — treat as NEW
  - `...s_Before_Build_03282026/Questions Ready to Ask_03282026.pdf`

### 👉 This fills the **largest execution gap identified earlier**
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...yBuildFiles/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md`

### "[fill in]", "[insert]", "PLACEHOLDER", "TBD"]
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.16 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_convert_export.py`

### "failure mode", "fail mode", "edge case", "risk:", "gap:",
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### "reasoning": "Placeholder detected in section 3."
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.30 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### (b) Identify the minimal correct fix: rename the config vars, OR add the missing exports,
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.45 — treat as NEW
  - `Claude Roadmap Audit 20260624.txt`

### (not standalone), required sub-field missing or incorrect value.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.23 — treat as NEW
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`

### 1 | FAIL — required markers missing, empty, malformed, or ambiguous
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### 13, 14, 15 are PRE-DRAFT stubs with structure reserved but content deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### 1: File Discovery | Source path missing | `find` returns empty | Log missing paths, skip, continue with available sources
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`

### 4 | Configuration error (missing required arg, invalid env).
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `CIS_TIER_6_2_GATE_CLOSEOUT_COMPLETE_V2_DESIGN.md`

### 400 for Missing Parameters**: Rejection of incomplete requests
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`

### 6 (Promote to project) | ❌ MISSING | No promotion path.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24.md`

### A cron-based trigger introduces a time gap where state could change
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.29 — treat as NEW
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`

### A formal trust zone model has been proposed but not implemented:
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.21 — treat as NEW
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### A placeholder summary ("Unknown project type")
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `...tion/functional_intents/instructions_extraction_analysis.md`

### A source root missing from source_roots (incomplete scan)
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.28 — treat as NEW
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Action scope boundaries** — defined conceptually but not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`

### Action:** Silently dropped from markdown serialization
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.14 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Ad hoc saved files | (TBD — Eric to identify) | Various | DEFERRED
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.29 — treat as NEW
  - `DEV-PIVOT-09_FRONT_DOOR_BUILD_PLAN.md`

### Add**: Add missing field types, tags, relationships
- support: 1 statements across 1 document(s)
- nearest queue item 19 is only sim 0.15 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`

### Address missing criteria in order of dependency
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### Affected Layers:** Execution Layer (missing), Synthesis Layer (missing), Merge Layer (missing)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### After**: Qwen2.5-32B-Instruct-AWQ is the specific primary model; vision models are explicitly deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...sponse_to_vscode_obsidian_and_github_extraction_analysis.md`

### After:** The 2736-line monolith is identified as a deferred refactoring task.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Alignment Mode features (user taste encoding, refined tagging) are deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...ybuildfiles_x_06_intelligence_stream_extraction_analysis.md`

### Alignment Mode** blocked by: Foundation Mode completion, Volume/Pattern thresholds
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`

### Alignment**: System no longer described as only foundation/setup; execution layer gap explicit
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### All internal layers are missing** - this file only defines the system boundary
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `...xtraction/functional_intents/read_me_extraction_analysis.md`

### Analytics Layer** - Blocked by record population
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...action/functional_intents/record_001_extraction_analysis.md`

### And this closes a gap in everything I've been framing.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.17 — treat as NEW
  - `claude crystallizes the vision.txt`

### Animation System** blocked by Transformation Layer
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.15 — treat as NEW
  - `...lender_2_80_fundamentals_transcripts_extraction_analysis.md`

### App Integration Bridge**: `push_cis_live()` not wired into app cycle
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...unctional_intents/cis_live_handoff_1_extraction_analysis.md`

### Application Layer** — partially blocked (missing CRUD operations)
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Are error paths handled or silently swallowed?
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.22 — treat as NEW
  - `CIS_MODEL_REVIEW_ARCHITECTURE_NOTE.md`

### Are there forward-looking features that should be deferred?
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `CIS_MODEL_REVIEW_ARCHITECTURE_NOTE.md`

### Authority classification editor | Assign and edit classifications | Not yet built
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.24 — treat as NEW
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`

### Autonomous Action Attempt**: Blocked by restricted capabilities
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`

### Because this functionality is core to the intended use of the system I am not sure if it should be deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...transcripts/2026-04-22_Model registry API implementation.md`

### Blocked By:** Explicitly deferred to Build Plan v2
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.46 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Blocked by: Missing capture layer infrastructure
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`

### Blocker 8: Missing artifact_id in completed items
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.37 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`

### Blocking:** If intent detection is missing, AI cannot proceed past step 1 (Wait)
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.47 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Blocking:** If missing, projects cannot branch or merge
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Blocking:** If missing, structure cannot adapt when ineffective
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.36 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Blocking:** If missing, system cannot remind user of required actions
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.42 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Branch note validation | No validation for branch note format | LOW — not yet formalized
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Bridges the gap between "chat about an idea" and "structured project with assets and schedule."
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.25 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24.md`

### Broadcast Validation:** No validation that broadcast content is correct or complete
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.22 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`

### Broader CIS Development:** Blocked by build-plan reconstruction
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Build Impact**: Initial implementation must be rule-based; adaptive routing is explicitly deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...lligence_routing_model_orchestration_extraction_analysis.md`

### Build Impact**: Low priority but creates technical debt if deferred
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Build Impact**: Requires content classification before OCR invocation; merge script must handle missing OCR output
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Build Impact**: Requires implementation of placeholder modules as swappable components.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Build Impact:** Intelligence Execution Stack is defined but not implemented in Phase C.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.37 — treat as NEW
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Build Impact:** Textarea replaces input field; placeholder text defines criteria
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.20 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Build Plan Validation**: No validation for reality-aware plan
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### CIS does not fail because components are missing.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### CIS has a feedback loop**: Review → Structure loop is the only defined feedback mechanism; all other learning loops are missing
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.25 — treat as NEW
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### CREATION**: Primary build target; LIFE deferred
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`

### Card status set to `blocked` with reason: "DRAFT validation failed: missing ### Summary"
- support: 1 statements across 1 document(s)
- nearest queue item 19 is only sim 0.32 — treat as NEW
  - `CIS_TIER_6_3_ORCHESTRATOR_KANBAN_INTEGRATION_DESIGN.md`

### Category validation | Not implemented | Invalid categories
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`

### Chrome Extension for Future Exports**: Not yet built.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_0722_extraction_analysis.md`

### Classification accuracy validation**: No validation that folder-structure classification is correct
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0139_extraction_analysis.md`

### Claude responded: Good catch — that's a real gap.
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.23 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`

### Client does not exist, PRE_PLAN | stage_candidate (create client + schedule intake)
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### Collision-to-Runtime Bridge**: How runtime handles unresolved collisions
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.18 — treat as NEW
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`

### Completed state object**: Referenced but not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.26 — treat as NEW
  - `...action/functional_intents/cis_intake_extraction_analysis.md`

### Component 3.5 closes this gap by making the dependency graph machine-readable before Component 4 and Component 5 consume it.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md`

### Concurrent runs**: Blocked by single-run lock; no queue
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...ion/functional_intents/ingest_spines_extraction_analysis.md`

### Conflict Register** — Real-time visibility into unresolved conflicts
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Conflict Status**: Unresolved conflicts count and details
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`

### Conflict: Deferred (not rejected, but postponed)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Consolidation Validation**: No validation of consolidated responses
- support: 1 statements across 1 document(s)
- nearest queue item 9 is only sim 0.24 — treat as NEW
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### Constraint 1: Application Layer Blocked by Infrastructure Wiring
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.22 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Constraint**: Malformed files are silently skipped
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Content Moderation**: No validation of content before publication.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.21 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`

### Content incomplete → Layer 2 fails → Rebuild triggered → Content completed
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Content is placeholder** — actual CIS_LIVE.md content and update frequency are undefined
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.25 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`

### Contradictions Unresolved**: Update blocked until resolution
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...update_governance_contract_dicussion_extraction_analysis.md`

### Control Layer** — defined conceptually but not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`

### Convergence Engine** blocked by User Feedback Loop
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.38 — treat as NEW
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`

### Conversation title** — may be missing (defaults to "Untitled")
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...unctional_intents/cis_convert_export_extraction_analysis.md`

### Correction Loop: Missing Files → User Notification → File Upload
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Covered:** NO — not covered in original report.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.46 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Create the directory first (does not exist currently)
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.21 — treat as NEW
  - `DOCKER_CONTAINMENT_PROPOSAL.md`

### Current Alternative:** Local HTML file (blocked by browser)
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.20 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Current App.jsx nav structure — placeholder scaffolding, reference only
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.25 — treat as NEW
  - `CHAT_FIRST_CIS_ARCHITECTURE_v1.md`

### Current Gap:** No promotion path for non-terminal users
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.19 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Current State:** Infrastructure ready, wiring incomplete
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Current State:** Not built; no validation mechanism
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Current Status**: Missing — this is a blocker.
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Current Status**: Missing — this is a coordination gap.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Current**: No validation between trigger and execution
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.26 — treat as NEW
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`

### Current**: Status changes are direct field updates with no validation of state transition legality.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Currently decorative placeholders — not wired to live data.
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.23 — treat as NEW
  - `...tion/functional_intents/all_insights_extraction_analysis.md`

### Currently missing — button shows no success/failure.
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### DEFERRED** | SWA application | ⬜ Separate project
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.21 — treat as NEW
  - `DEV-PIVOT-06_BUILD_DIRECTION.md`

### DEFERRED_EXISTS | Deferred items | Must resolve before close
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Dead Letter Channel for out-of-scope | Unrecognized domains must not silently create work | Invalid Message Channel (Hohpe/Woolf)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### Deferred work identified**: Previously deferred work was undefined.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ions_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### Deferred**: Non-blocking recommendations deferred
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### Dependencies must include status (resolved, unresolved, blocking)
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Dependency 2:** Gap tracker application depends on Architect output
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Dependency Impact**: Missing validation creates silent data loss.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Dependency Impact**: References to open questions must specify which file to use
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.18 — treat as NEW
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`

### Dependency Impact**: Tag quality depends on keyword coverage - missing genres will be "uncategorized"
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...action/functional_intents/cis_ingest_extraction_analysis.md`

### Dependency Impact**: These stubs block downstream dependencies until populated; creates placeholder for future work
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Dependency Impact**: Vault is incomplete without this folder.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Dependency Impact:** No dependency chain issue — pure syntax error from incomplete refactoring
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Dependency Impact:** The application layer depends on the infrastructure layer for serving, but the wiring between them is incomplete.
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.18 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Description**: Human review interface for draft records does not exist
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`

### Description**: No validation of cross-references between records
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`

### Description**: No validation that phase objectives are met before transition
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Description**: Non-critical components that can be deferred
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.24 — treat as NEW
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`

### Design note:** Full payload persistence is a known gap.
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `CIS_TIER_11D_REVIEWER_SIDE_HANDOFF_SPECIFICATION.md`

### Design**: Defined conceptually but not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...ntents/phase_0_5_replan_orchestrator_extraction_analysis.md`

### Discovery 13: Intel Sidebar Tabs Are Decorative — Not Wired to Any Function
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Discovery 14: Glossary Entry Trigger Unresolved
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Discovery 1: Execution Layer Gap as Primary Blocker
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### Discovery 2: Missing File Map / Orientation Document
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.30 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Discovery 3: Branch Note Gap (Missing Artifact Type)
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.43 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Discovery 4: Recurring Documentation Gap Pattern
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`

### Discovery 6: Version Control Gap for Runtime Assets
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Do Not Start Yet** — What is explicitly deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `CIS_CONTEXT_CONTRACT.md`

### Do you want to do that work now — read the 15 insight records and build the plan — or do you want me to draft a plan based on what's in the current documentation and you tell me what it's missing?
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### Document Relationship Layer (Missing, To Be Created)
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.23 — treat as NEW
  - `...nd_offs_cis_handoff_current_position_extraction_analysis.md`

### Documentation gap reinforcement**: Undocumented configuration → failure → recovery → no documentation → future failure (negative reinforcement cycle)
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`

### Download Watcher → Draft Registry**: Missing watcher bridge
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`

### Draft State**: Missing → needs draft registry visibility
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`

### Draft Type Inference**: Must match known patterns; unrecognized types silently skipped
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.32 — treat as NEW
  - `...ctional_intents/cis_download_watcher_extraction_analysis.md`

### Draft Type Taxonomy Gap**: Unrecognized filename patterns are silently skipped, potentially causing data loss if operators are unaware of the naming convention requirements.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...ctional_intents/cis_download_watcher_extraction_analysis.md`

### Draft Workflow**: (MISSING) No workflow exposure for draft intake
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### E3: Build-plan workflow visibility — explicitly deferred
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.37 — treat as NEW
  - `proposals/POST_TIER10_PLANNING_REVIEWER_RESPONSE.md`

### Empty project structure** | CRITICAL | The auto-generated file contains no actual project tree, indicating either a failed generation, an empty project, or a placeholder awaiting population.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `...tion/functional_intents/instructions_extraction_analysis.md`

### Error returns | `{ "error": "<message>" }` if topic/intent missing or subprocess fails
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Error: 400 (missing manifest), 503 (Slot 1 not running), 500 (enqueue failure)
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Error: 400 (missing path), 404 (file not found), 500 (enqueue failure)
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.21 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Error: 400 for missing/invalid fields, 409 for duplicate id
- support: 1 statements across 1 document(s)
- nearest queue item 19 is only sim 0.27 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Error: missing required fields for target type
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.18 — treat as NEW
  - `...gacybuildfiles_x_07_knowledge_stream_extraction_analysis.md`

### Every deferred reduction must have a target resolution.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### FAIL: Missing requirements, validation errors, transition blocked
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`

### FAIL: Output is missing fields, has invalid tags, or is unstructured text.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`

### FORBIDDEN_STRINGS = ["TODO", "[placeholder]", "[coming soon]", "[to be completed]",
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_convert_export.py`

### Fail (400)**: Missing thread_id, no messages, no user messages
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.28 — treat as NEW
  - `...ction/functional_intents/idea_drafts_extraction_analysis.md`

### Fail**: Missing criteria → remediate before proceeding
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### Fail**: Preprocessing incomplete, task blocked
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...70617043874_x_06_intelligence_stream_extraction_analysis.md`

### Fail: Exception caught silently, record skipped
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Fail: invalid transition, missing authority, record locked
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.32 — treat as NEW
  - `...gacybuildfiles_x_07_knowledge_stream_extraction_analysis.md`

### Fail:** Tool fails to launch, dependency conflicts unresolved, no output generated
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.30 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`

### Failure Mode**: Missing manifest → exit code 2
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Failure Modes**: Missing `description` field returns error but curl may not display it
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Feedback workbench**: Not yet built — interface for feedback loop management
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.21 — treat as NEW
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`

### Field authority rules | Defined in legacy docs | Not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.21 — treat as NEW
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### File Format Validation**: No validation that CIS_LIVE.md is valid before serving
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.33 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`

### File Map Reinforcement Loop:** Missing orientation → Claude proposes map → Map created → User navigates better → Map updated
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.25 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### File Sync Validation Engine**: Referenced but not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.25 — treat as NEW
  - `...ntents/1775995115163043436_x_control_extraction_analysis.md`

### File map**: Rejected → Missing files → Add → Re-review.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Firefox Configuration is a Missing Prerequisite
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.12 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`

### Format Validation**: WAV/MIDI format validation not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.15 — treat as NEW
  - `...857838508_x_11_sound_stream_expanded_extraction_analysis.md`

### Future State**: May need multi-worker or priority queueing (explicitly deferred)
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### GUI Layer**: Blocked by record management stability
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.25 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Gap 2: Cloudflare Tunnel for Hermes (ChatGPT → Hermes)
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.45 — treat as NEW
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Gap Object**: How are gaps in structure represented?
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.19 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`

### Gap Routing**: Where do transitional gaps go after identification?
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.29 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Gap Tracker**: No application surface for tracking transitional gaps
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.13 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Gap Visibility**: Visibility into named transitional gaps
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.26 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Gap → Output Risk Loop**: Named gaps → known risks → mitigation strategies → reduced output risk → fewer gaps
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.22 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Gap**: App update function not yet integrated into main application
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: Function exists but has no integration point
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.20 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Gap**: How app consolidates three model responses not defined
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: How are classified actions passed to the execution engine?
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.26 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### Gap**: How tasks are assigned to models undefined
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.29 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Gap**: Log format is hardcoded in Python string
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Gap**: Logging goes to /logs/system_log.md, but no routing logic for different action types.
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### Gap**: Models not yet configured to read from creative-intelligence-system.com
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.29 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: No alerting mechanism for infrastructure failures
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`

### Gap**: No constraint limiting job_type to known values
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.23 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`

### Gap**: No controlled vocabulary — phase values are free text
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap**: No defined confidence thresholds for PASS/FAIL/UNCERTAIN
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Gap**: No defined consequences for model misbehavior
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.21 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Gap**: No defined interface for human intervention
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.25 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Gap**: No defined object for feedback injection into model behavior
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.19 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap**: No defined strategy for managing commit history
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Gap**: No defined thresholds for hardware monitoring
- support: 1 statements across 1 document(s)
- nearest queue item 9 is only sim 0.25 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Gap**: No detection of model unavailability before script execution
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.22 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap**: No exact JSON-like output structures for each worker pass
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.23 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Gap**: No formal state tracking for infrastructure components
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`

### Gap**: No interface for viewing or managing jobs
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.24 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`

### Gap**: No mechanism to detect or report slow queries
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Gap**: No model selection algorithm in registry
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Gap**: No ontology versioning defined for corrections
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.27 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`

### Gap**: No progress bar or percentage completion
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`

### Gap**: No tracking of where model weights are stored
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.21 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Gap**: No validation of job parameters before enqueue
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.21 — treat as NEW
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Gap**: No workflow exposure requirements discussed
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Gap**: Trust zone validation logic not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Gap**: Where CIS_LIVE.md lives relative to project structure
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: Workbench requirements are identified but not defined
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Gap**: `benchmark_score` is a free-form text field
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Gap**: live.creative-intelligence-system.com vs root domain
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.21 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap/Risk Tracking Exists:** Gaps and risks are now formal objects with lifecycle states.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Gap: App Not Yet Wired to Write Real CIS_LIVE Content
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### Gap: Public File Sensitive-Content Filter Missing
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.25 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### Gap: Response Capture Path from External Models Is Undefined
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### Gap:** Assets are de facto LMS content, not a general DAM.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.22 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Gap:** Complete count would require scanning all 50+ runtime Python files.
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Gap:** FAIL count may not reflect correct scope
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.46 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Gap:** How do other domains request sound assets?
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.21 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap:** How do projects request assets from library?
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.22 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap:** How does Sound integrate with project workflow?
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap:** How does Sound query Intelligence Layer?
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap:** Lifecycle states defined but not formalized
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap:** No UX review performed beyond Eric's observations.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Gap:** No defined connection between creative tools and execution stack
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`

### Gap:** No defined copyright validation process
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.24 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap:** No defined mechanism for asset transfer between tools
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.25 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`

### Gap:** No defined mechanism for phase transitions
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.15 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`

### Gap:** No formal process for handling post-commit addendum
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

