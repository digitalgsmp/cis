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

- clusters: 3,200
- with 2+ supporting statements: 1,261
- of those, already on the working queue: 4
- of those, NOT on the working queue: 1,257
- single-statement clusters (listed last): 1,939


## NOT on the working queue — candidates to merge  (1257)

### ``` Field 5 — Verification Status: Manifests produced: [count] Verifications run: [count] Unresolved FAILs: [count — must be 0 to close cleanly] Verification log: /mnt/projects/cis/logs/verification_log.md ```
- support: 26 statements across 21 document(s)
- nearest queue item 13 is only sim 0.44 — treat as NEW
  - `...-9d9c-e83384f51db8:Starting a new session with files#r1`
  - `...-a83d-a4a21870b2d7:CIS execution layer phase 0 setup#r4`
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_02_0558_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`

### Validating → Failed**: Output fails validation (missing required sections, incorrect format)
- support: 21 statements across 21 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...e_atlas/cis_chat_2026_04_009_extraction_analysis.md:575`

### Missing Layers:** The staged draft intake layer (ADR-048) and filesystem governance layer (ADR-047) are identified as missing layers that will be implemented after ADR-045 closure.
- support: 31 statements across 20 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...P_Project_Primer/_backups/20260505_0058/01_CURRENT_STATE.md`
  - `...Project_Primer/archive/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `..._intents/cis_handoff_2026_05_02_0558_extraction_analysis.md`
  - `..._transcripts/ChatGTP_Project_Primer/04_ACTIVE_COMPONENTS.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Before this file, governance was a set of documents. After this file, governance is an operational system with: - Explicit provenance requirements (--approved-by, --architect) - Two-phase atomic apply with preview enforcement - Process lock enforcement - Conflict logging with structured format - Que
- support: 27 statements across 20 document(s)
- nearest queue item 21 is only sim 0.42 — treat as NEW
  - `...0260505_0058_01_current_state_extraction_analysis.md#r1`
  - `...0345839_x_01_system_blueprint_extraction_analysis.md#r6`
  - `...0502_0047_09_governance_state_extraction_analysis.md#r0`
  - `...0502_0047_09_governance_state_extraction_analysis.md#r5`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...ayer_pivot_and_pd5_governance_extraction_analysis.md#r2`

### ## 6. KNOWLEDGE-LAYER IMPLICATIONS None. ## 7. APPLICATION-LAYER IMPLICATIONS None. ## 8. FEEDBACK LOOP DISCOVERIES None. ## 9. UNRESOLVED GAPS + MISSING LAYERS - **Complete Absence of Architectural Content:** This file provides zero architectural intelligence. It cannot be used for topology generat
- support: 20 statements across 20 document(s)
- nearest queue item 22 is only sim 0.41 — treat as NEW
  - `.../session_distillations_readme_extraction_analysis.md#r4`
  - `..._2026_04_004_extraction_analysis_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._legacybuildfiles_x_02_memory_extraction_analysis.md#r2`
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Architectural Significance**: Structured conflict logging with CLI tool; rule that unresolved conflicts must be logged before session close
- support: 33 statements across 14 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Architectural Significance**: Identifies that the human operator had become middleware between incomplete orchestration layers, creating a critical bottleneck in the execution pipeline.
- support: 18 statements across 14 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### The fix was built and deployed this session, but the fact that this gap existed undetected across multiple sessions is significant — it means the branch record system that CIS Live is supposed to provide had been non-functional from the start.
- support: 16 statements across 14 document(s)
- nearest queue item 2 is only sim 0.42 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-28_0553.md`
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`

### Runtime Impact**: Failure at any step (e.g., missing manifest, unflushed corrections) breaks continuity for the next session.
- support: 14 statements across 14 document(s)
- nearest queue item 8 is only sim 0.43 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...itutional_memory_governance_revision_extraction_analysis.md`

### Unresolved Application Surfaces: Dashboard Integration.** The dashboard integration is described but not specified.
- support: 16 statements across 13 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Impact**: All previously planned build targets are now deferred until after execution layer is operational
- support: 15 statements across 13 document(s)
- nearest queue item 4 is only sim 0.46 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`

### LOCKED — final, constitutionally authoritative OPERATIONAL — governing current behavior in runtime TRANSITIONAL — partially implemented or temporary PRE-DRAFT — scope written, not yet locked for build PLANNED — identified and directionally decided DEFERRED — known, postponed
- support: 14 statements across 13 document(s)
- nearest queue item 2 is only sim 0.47 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._Primer/_backups/20260502_0047/09_GOVERNANCE_STATE.md:2`
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...enerated_script_artifacts/042926_Project_Primer.txt:121`

### Missing Validation Layers: Schema Validation.** There is no schema validation for the knowledge records or the manifest files.
- support: 14 statements across 13 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Architectural Significance**: CIS_CONFLICT_REGISTER.md is now a required artifact for tracking unresolved contradictions, drift, and terminology issues.
- support: 21 statements across 12 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...itutional_memory_governance_revision_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...pts/ChatGTP_Project_Primer/archive/PROJECT_PRIMER_UPDATE.md`

### Gap**: No defined permissions, prohibited actions, approval gates, log requirements, failure behavior
- support: 19 statements across 12 document(s)
- nearest queue item 5 is only sim 0.45 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Missing execution-bridge layer**: Previously assumed workflow stream was sufficient; now identified as missing enforceable runtime actions, pass/fail conditions, review states, operational responsibilities
- support: 17 statements across 12 document(s)
- nearest queue item 12 is only sim 0.48 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### Missing Runtime Bridge: Error Handling.** The session close sequence has no defined error handling.
- support: 15 statements across 12 document(s)
- nearest queue item 8 is only sim 0.50 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`

### Dependency Impact**: ADR-044 (operator abstraction), ADR-045 (execution ownership - CLOSED), ADR-048 (intake ownership - Phase 1/2 COMPLETE, Phase 3 DEFERRED)
- support: 15 statements across 12 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `..._transcripts/ChatGTP_Project_Primer/02_NEXT_BUILD_TARGET.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`

### Missing**: No explicit state transition validation (e.g., cannot go from `discovered` to `active` without intermediate states)
- support: 14 statements across 12 document(s)
- nearest queue item 16 is only sim 0.46 — treat as NEW
  - `.../extraction/functional_intents/state_extraction_analysis.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ctional_intents/cis_download_watcher_extraction_analysis.md`
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `...extraction/functional_intents/cis_db_extraction_analysis.md`

### Unresolved Storage Rules: Memory Archival**: The rules for archiving old memory entries are not defined.
- support: 12 statements across 12 document(s)
- nearest queue item 18 is only sim 0.50 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Dashboard HTML refactor deferred | 2736-line monolith cannot be safely restructured mid-build | Blocks frontend modularization
- support: 24 statements across 11 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`

### The session then encountered a chain of failures in the session close process — duplicate DB entries, a missing Path import, multiple failed close attempts — before the session close finally completed cleanly.
- support: 16 statements across 11 document(s)
- nearest queue item 8 is only sim 0.45 — treat as NEW
  - `...ce_System_v1/runtime_scripts/runtime/2_CIS_REORIENTATION.md`
  - `...chat_2026_04_006_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...on/functional_intents/import_session_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`

### Two runtime bugs are known and deferred** — Field 5 FAIL count reads full historical log (not scoped to current session), and ADR form auto-increment resets to ADR-020 after log.
- support: 13 statements across 11 document(s)
- nearest queue item 2 is only sim 0.47 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md`

### Intelligence Layer as Critical Missing Piece**: The system is at a hard boundary where setup is complete but intelligence is absent.
- support: 11 statements across 11 document(s)
- nearest queue item 21 is only sim 0.39 — treat as NEW
  - `...42767492025744_x_07_knowledge_stream_extraction_analysis.md`
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Dependency Impact**: Introduces unstable dependencies — components that appear to work but have unresolved underlying issues
- support: 11 statements across 11 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `...acybuildfiles_x_cis_relationship_map_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `...extraction/functional_intents/spines_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Gap:** Workflow stages are defined but stage schema (input, output, validation, state transition) is not formalized.
- support: 21 statements across 10 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Knowledge gap detection must exist before knowledge filling** — AI cannot fill gaps without identifying them first
- support: 17 statements across 10 document(s)
- nearest queue item 22 is only sim 0.45 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nctional_intents/x_00_operator_model_extraction_analysis.md`

### Summary of gaps: Schema files missing: source manifest, processing profile, review states, project object, segment Spec docs missing: everything — no contract has a written specification document
- support: 16 statements across 10 document(s)
- nearest queue item 16 is only sim 0.45 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0836_extraction_analysis.md`
  - `...ction/functional_intents/idea_drafts_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Architectural Significance:** The session close protocol has a fundamental gap — work performed after commit has no capture path to any endpoint (DB, ADRs, knowledge records, system log)
- support: 13 statements across 10 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...chat_2026_04_006_extraction_analysis_extraction_analysis.md`
  - `...ents/post_commit_addendum_2026_04_18_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Write missing Phase 0 contracts — source manifest, processing profile, review states Build cis_spine_intake.py Ingest first spine — Blender documentation Install PySceneDetect and test against a video — now segments have a spine to map to Write ADR-033 — segmentation policy locked after spine and Py
- support: 13 statements across 10 document(s)
- nearest queue item 17 is only sim 0.51 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...egrated_vision_cis_core_architecture_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Missing Runtime Bridges**: No explicit runtime bridges exist for workspace switching, node tree compilation, material compilation, world compilation, ViewLayer evaluation, or brush initialization.
- support: 11 statements across 10 document(s)
- nearest queue item 16 is only sim 0.41 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nctional_intents/cis_handoff_phase_d_extraction_analysis.md`
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Knowledge Gap**: Verification results are stored but not indexed, not queried, not aggregated, and not fed back into system behavior — creating a **write-only knowledge pattern**.
- support: 11 statements across 10 document(s)
- nearest queue item 3 is only sim 0.41 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`

### The gap between current state and required state is substantial across all architectural dimensions: storage, retrieval, governance, security, and knowledge formation.
- support: 11 statements across 10 document(s)
- nearest queue item 1 is only sim 0.40 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### The system has no validation layers**: Input validation, response validation, and format validation are minimal or absent.
- support: 10 statements across 10 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `.../cis_canonical_build_sequence_extraction_analysis.md:99`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...cybuildfiles_x_cis_critical_addition_extraction_analysis.md`
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Decisions API has a silent failure mode**: Missing the `description` field causes the API to return `{"success": false}` but the error message is only visible if you parse the JSON response.
- support: 26 statements across 9 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...26-04-21_Session close and handoff process clarification.md`
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Architectural Significance**: ADR-048 Phase 3 (commit layer) is intentionally deferred because approval and commit are architecturally separate concerns.
- support: 24 statements across 9 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-04_0413.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Loop:** Gap identified → ADR proposed → ADR locked → Gap resolved → Knowledge base updated → Future reviews reference resolved gap
- support: 16 statements across 9 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Gap:** Intake creates structured entries but routing to Project Pipeline is not implemented.
- support: 13 statements across 9 document(s)
- nearest queue item 1 is only sim 0.43 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Gap**: Records must be in source-contained directories, but no specific storage rules defined.
- support: 11 statements across 9 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### No Validation Layer**: There is no explicit validation of handoff package completeness, phase accuracy, or stream relevance.
- support: 11 statements across 9 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0410_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...raction/functional_intents/x_control_extraction_analysis.md`

### CREATION pipeline proven first, LIFE domains deferred.** But design decisions made with LIFE in mind may need revision based on CREATION pipeline experience.
- support: 10 statements across 9 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### The "no new governance surface" rule is adopted but not formalized as an ADR.** This is a governance gap that needs resolution.
- support: 9 statements across 9 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Validation**: required fields → unsupported claims → schema drift → hallucination indicators → missing uncertainty → malformed tags → structural integrity
- support: 9 statements across 9 document(s)
- nearest queue item 13 is only sim 0.37 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...action/functional_intents/cis_ingest_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_execution_layer_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...intents/x_cis_discovery_workbench_v1_extraction_analysis.md`

### No Schema Validation**: No validation that new content follows primer schema
- support: 9 statements across 9 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `.../functional_intents/primer_update_v2_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`
  - `...extraction/functional_intents/drafts_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### Check the runtime manifests folder — that's likely where the manifest template or spec lives: bashls /mnt/projects/cis/runtime/manifests/ The "missing Phase 0 contracts" task from the handoff may mean the spec documents describing the rules — not the manifests themselves, which already exist.
- support: 14 statements across 8 document(s)
- nearest queue item 2 is only sim 0.43 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`

### The `route_task.py` routing layer was described architecturally — it queries the model registry to decide which tier handles a given task — but does not exist as code.
- support: 12 statements across 8 document(s)
- nearest queue item 16 is only sim 0.48 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### States**: Idle, Lock acquired, Phase 1 applying, Phase 2 applying, Complete, (MISSING) Rolled back, (MISSING) Failed
- support: 11 statements across 8 document(s)
- nearest queue item 5 is only sim 0.44 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`

### Model registry API → Intel sidebar | GET /api/models endpoint does not exist | HIGH — blocks ADR-024/025
- support: 11 statements across 8 document(s)
- nearest queue item 10 is only sim 0.31 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0547_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Session Validation** — No validation that session has meaningful content before resolution
- support: 11 statements across 8 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...n/functional_intents/session_extract_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Handoff File Overwrite**: The handoff file is overwritten on each session close, creating a risk of data loss if the close sequence fails silently.
- support: 10 statements across 8 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Session→Resolution→Handoff→Reorientation**: Continuity maintained through structured handoffs; unresolved sessions break continuity
- support: 10 statements across 8 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...chat_2026_04_005_extraction_analysis_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...on/functional_intents/implementation_extraction_analysis.md`

### Dependency Impact**: Governance cannot be enforced until implementation catches up; creates validation gap between documented governance and actual system behavior.
- support: 10 statements across 8 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...7059416496004_x_cis_relationship_map_extraction_analysis.md`
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### The gap is that there's no tooling making that validation fast or systematic during the build phase itself.
- support: 9 statements across 8 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`

### This represents a **governance-implementation gap** that must be resolved before the draft intake layer can be considered stable.
- support: 9 statements across 8 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`
  - `...tents/1776042143355379182_x_03_state_extraction_analysis.md`
  - `...tion/functional_intents/dedup_memory_extraction_analysis.md`

### Governance Layer**: Blocked on validation engine — cannot enforce contract without validation
- support: 8 statements across 8 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`
  - `...chat_2026_04_005_extraction_analysis_extraction_analysis.md`
  - `...extraction/functional_intents/collab_extraction_analysis.md`
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`
  - `...lender_2_80_fundamentals_transcripts_extraction_analysis.md`

### Resolve is fully working. Session #008 shows RESOLVED in green, solution text displayed, decided by and date confirmed. The full flow is proven end to end.
- support: 8 statements across 8 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...4-18_Session execution and image pipeline setup.md:1254`
  - `...4-18_Session execution and image pipeline setup.md:1406`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...pts/2026-04-22_Model registry API implementation.md:512`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:392`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:393`

### Knowledge Record → Search**: Records indexed → searchable → retrieved for future work → relevance feedback improves retrieval.
- support: 8 statements across 8 document(s)
- nearest queue item 3 is only sim 0.50 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `...tional_intents/x_cis_execution_layer_extraction_analysis.md`

### Governance Gap**: While verification creates governance records, there's no automated governance enforcement, no escalation, no override mechanism, and no human sign-off requirement.
- support: 8 statements across 8 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### No Governance or Validation Exists**: The system has no governance layer, no validation logic, no authority structures, and no quality control mechanisms.
- support: 8 statements across 8 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Config constants have been established (VERIFICATION_MANIFEST_DIR, RUNTIME_MANIFEST_DIR, SOURCE_MANIFEST_NAME), but runtime/manifests/ origin and status remain unresolved.
- support: 11 statements across 7 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...4-24_CIS phase 1 intelligence extraction handoff.md:129`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md`

### Schema Migration Gap**: No schema versioning or migration mechanism exists, despite having both inline and file-based schema definitions that could drift over time.
- support: 11 statements across 7 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...action/functional_intents/connection_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Verification Layer**: Blocked by chunked verification architecture, contract verification sequencing
- support: 10 statements across 7 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### No automation reduction included and no "NO AUTOMATION REDUCTION FOUND" statement | Contract violation — block treated as incomplete
- support: 10 statements across 7 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...ChatGTP_Project_Primer/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`
  - `...ve_06_foundational_control_contracts_extraction_analysis.md`

### Multi-Agent Orchestration**: Blocked by agent execution layer; cannot coordinate without agent roles and protocols
- support: 10 statements across 7 document(s)
- nearest queue item 12 is only sim 0.54 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Architectural Significance**: Two manifest directories exist: /mnt/projects/cis/logs/manifests/ (canonical) and runtime/manifests/ (status unresolved per ADR-047).
- support: 10 statements across 7 document(s)
- nearest queue item 5 is only sim 0.32 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...extraction/functional_intents/config_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...st_try/insights_First_Try/_Automation_Discussion_ChatGTP.md`
  - `...t_transcripts/ChatGTP_Project_Primer/13_RUNTIME_TOPOLOGY.md`

### Session Close Input Validation**: focus, completed, next_steps are REQUIRED — returns 400 if missing
- support: 9 statements across 7 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Missing Validation Layer: Memory Validation**: The rules for validating the structure and content of the memory file are not fully defined.
- support: 9 statements across 7 document(s)
- nearest queue item 17 is only sim 0.37 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...85_2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...on/functional_intents/update_prefill_extraction_analysis.md`
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Architectural Significance**: Confirms execution queue as canonical runtime layer with verified operational status for Step 1 (execution_jobs table), but reveals 6 remaining implementation steps (Steps 2-7) that are not yet built
- support: 8 statements across 7 document(s)
- nearest queue item 12 is only sim 0.38 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ation_backups_20260430/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Project Context Missing**: The system doesn't capture project context or link outputs to specific CIS projects.
- support: 8 statements across 7 document(s)
- nearest queue item 5 is only sim 0.32 — treat as NEW
  - `...cybuildfiles_x_10_application_stream_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...onal_intents/x_10_application_stream_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Session Close Fields**: Schema is defined (focus, completed, next steps, notes) but not enforced by runtime.
- support: 8 statements across 7 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### The explicit recognition that the commit layer is NOT YET BUILT, creating a known architectural gap that blocks full automation of the intake pipeline, did not exist before.
- support: 8 statements across 7 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...onal_intents/x_cis_critical_addition_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Unresolved Orchestration: The Merge Step**: The document says the Merge step is "REQUIRED" but does not define the orchestration logic.
- support: 8 statements across 7 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### A critical gap exists** — decisions can be created by anyone, with any status, and never updated or reviewed
- support: 7 statements across 7 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `...intents/cis_handoff_current_position_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Application Layer on Underlying Layers**: Application cannot function if any underlying layer is incomplete
- support: 7 statements across 7 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...818091549056_x_10_application_stream_extraction_analysis.md`
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### Build Impact:** Deferred but recognized as critical; refactoring into component files is a prerequisite for stability
- support: 7 statements across 7 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...intents/20260502_0047_05_adr_summary_extraction_analysis.md`
  - `...onal_intents/x_10_application_stream_extraction_analysis.md`

### Missing Runtime Bridge**: There is no automated bridge between the CIS Live session resolution and the handoff file generation.
- support: 7 statements across 7 document(s)
- nearest queue item 8 is only sim 0.44 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### It contains the complete architectural extraction with all sections preserved, including discovered entities, dependency chains, execution flows, orchestration behavior, workflow stages, state transitions, validation logic, governance implications, unresolved gaps, build-order implications, canonica
- support: 7 statements across 7 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`

### Unresolved Orchestration:** The orchestration logic for the full pipeline (spine → source intake → concept mapping → segmentation → extraction → record formation) is not yet designed.
- support: 7 statements across 7 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### It introduces a new architectural layer: Staged Draft Intake.** This is not a feature request—it is a missing architectural layer that must exist between model output and canonical records.
- support: 7 statements across 7 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### The most significant architectural realization is that the **Application Layer is a dependent surface layer** that cannot function without all underlying layers operational. The application does not create, generate, or replace any system capability; it only coordinates and exposes. This fundamental
- support: 7 statements across 7 document(s)
- nearest queue item 15 is only sim 0.25 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...91549056_x_10_application_stream_extraction_analysis.md`
  - `...Intelligence_System_LegacyBuildFiles/X_02_MEMORY.md:145`
  - `...an AI platform for professional project guidance.md:333`
  - `...is_workflow_execution_spec_v1_extraction_analysis.md#r1`
  - `...is_workflow_execution_spec_v1_extraction_analysis.md#r3`

### This is: 👉 **CAPABILITY LAYER + EXECUTION ENVIRONMENT DEFINITION** It defines: - how tools exist **inside the system** - how capability is made **usable** --- ## 🔧 NORMALIZED ADDITIONS (Core Tool Stream integrated) ### 🔹 **CAPABILITY SYSTEM (NEW COMPONENT TYPE)** **Tool Stream** - defines **how capa
- support: 7 statements across 7 document(s)
- nearest queue item 21 is only sim 0.36 — treat as NEW
  - `..._04_20_ai_memory_capabilities_extraction_analysis.md#r3`
  - `...ents/x_05_core_tool_stream_md_extraction_analysis.md#r4`
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:1123`
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:1128`
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:1191`
  - `...insight_record_2026_04_19_001_extraction_analysis.md#r5`

### This also closes a gap that already exists: the Intel sidebar has LOCAL, REMOTE, AGENT tabs listing models, but those lists are currently decorative — not wired to anything functional.
- support: 13 statements across 6 document(s)
- nearest queue item 15 is only sim 0.40 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Conflict panel | View/register/resolve conflicts | Not implemented | /api/conflicts + dashboard
- support: 11 statements across 6 document(s)
- nearest queue item 2 is only sim 0.42 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `HANDOFF_SCHEMA.md`

### Missing Automation**: The entire automation layer is currently missing - no scripts, no tools, no interfaces exist for the defined pipeline.
- support: 10 statements across 6 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...traction/functional_intents/pipeline_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### Architectural Significance**: vLLM Slot 1 requires manual start each session; port pre-check fixed but daemonization incomplete
- support: 9 statements across 6 document(s)
- nearest queue item 10 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `...hive/orientation_backups_20260430/10_OPERATIONAL_REALITY.md`
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`
  - `_archive/orientation_backups_20260430/01_CURRENT_STATE.md`

### Missing Merge Stage**: OCR + visual extraction → structured synthesis → normalized record is missing, causing fragmented outputs and inconsistent record quality.
- support: 9 statements across 6 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### Session Resolution**: Unresolved sessions detected; resolution enforced before archive; correction prevents drift
- support: 9 statements across 6 document(s)
- nearest queue item 15 is only sim 0.42 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### Architectural Significance**: Identifies that the human operator currently functions as the transport bridge between AI-generated content and canonical CIS records, creating a systemic bottleneck and audit gap
- support: 9 statements across 6 document(s)
- nearest queue item 21 is only sim 0.36 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### The second direction change was the decision to defer video entirely from Phase 0. Rather than partially implement video support with a known-flawed segmentation method, the session concluded that video is Phase 1 work and Phase 0 should exit cleanly on static images only. This was the correct call.
- support: 9 statements across 6 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `...aec072e4:CIS phase 1 intelligence extraction handoff#r6`
  - `...ession_insight_record_2026_04_22_001_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_003.md:213`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_003.md`

### The fourth layer (execution bridge) was previously implicit and is now explicitly recognized as missing.
- support: 8 statements across 6 document(s)
- nearest queue item 22 is only sim 0.35 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nd_offs_cis_handoff_current_position_extraction_analysis.md`

### Queue ownership is prerequisite, not optional** - Previously assumed execution could proceed without centralized queue, now recognized as critical missing layer blocking all reliable execution
- support: 8 statements across 6 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...hive/orientation_backups_20260430/10_OPERATIONAL_REALITY.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### No validation at entry**: File type is inferred from extension only; no content validation; no integrity verification against source
- support: 8 statements across 6 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `.../functional_intents/primer_update_v3_extraction_analysis.md`
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `...action/functional_intents/cis_intake_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Gap:** Projects exist but are not connected to tasks, schedule, DAM, knowledge, or
- support: 8 statements across 6 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### The model registry work to make them functional was deferred to ADR-024/025, which was still not implemented at this point.
- support: 8 statements across 6 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Gap**: No automated pipeline exists to trigger extraction when a session completes
- support: 8 statements across 6 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...tivation_session_extraction_analysis_extraction_analysis.md`

### Knowledge Formation**: 15 SESSION_INSIGHT_RECORDs not ingested → knowledge incomplete → cannot form complete architectural picture
- support: 8 statements across 6 document(s)
- nearest queue item 8 is only sim 0.48 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Architectural Significance**: queue_worker.py invokes cis_verify.py with unsupported --file flag, indicating incomplete contract between queue worker and verification tool
- support: 8 statements across 6 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...GTP_Project_Primer/_backups/20260502_0047/07_KNOWN_RISKS.md`
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Human as API Layer**: The most significant architectural gap is that humans are currently acting as the integration layer between AI output and system forms.
- support: 8 statements across 6 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...intents/archive_02_next_build_target_extraction_analysis.md`
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### No Content Validation**: The API performs no validation of extraction file content before ingestion; it trusts the external script entirely.
- support: 7 statements across 6 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`
  - `...ion/functional_intents/ingest_spines_extraction_analysis.md`
  - `...on/functional_intents/cis_preprocess_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`
  - `...raction/functional_intents/librarian_extraction_analysis.md`
  - `...unctional_intents/ingest_extractions_extraction_analysis.md`

### Gap**: No queue management logic (polling, priority sorting, worker assignment)
- support: 7 statements across 6 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Review this proposal against the locked ADRs and identify gaps, risks, and missing dependencies.
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-26_0722.md`
  - `...is_predev_infrastructure_plan_claude_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`
  - `ADRs/ADR-045_Execution_Queue_Ownership_Layer.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### If you're seeing this in your own code or infrastructure, the next useful step is checking logs for the actual error being swallowed before the retry. Want to share more context about where this appeared?
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...6-04-24_Retry attempt taking longer than expected.md:12`
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `...pts/2026-04-24_Retry attempt taking longer than expected.md`
  - `...traction/functional_intents/pipeline_extraction_analysis.md`
  - `...xtraction/functional_intents/helpers_extraction_analysis.md`

### Field 5 Validation**: Currently shows incorrect data; validation layer missing
- support: 6 statements across 6 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### None implemented**: No validation that project concept is coherent or non-contradictory
- support: 6 statements across 6 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...ntents/phase_0_5_replan_orchestrator_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...traction/functional_intents/projects_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Unresolved Routing: Memory-Based Routing**: The logic for routing requests based on memory context is undefined.
- support: 6 statements across 6 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nts/runtime_implementation_contracts_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Lifecycle**: Staged → Approved/Rejected/Superseded → Committed (Phase 3 deferred)
- support: 6 statements across 6 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `PLAN_RECONCILIATION.md`

### Runtime Impact**: 0 verifications and 0 FAILs this session from build actions, but cumulative counts show 568 verifications and 41 unresolved FAILs
- support: 6 statements across 6 document(s)
- nearest queue item 13 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_02_0558_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-01_0548.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### This was flagged as a known design flaw from the previous session that needed to be fixed as the first task of the following session but had not been fixed yet. ________________
- support: 6 statements across 6 document(s)
- nearest queue item 8 is only sim 0.41 — treat as NEW
  - `...at_transcripts/2026-04-22_CIS build continuation.md:349`
  - `...chat_transcripts/2026-04-17_Hand off evaluation.md:1183`
  - `...e_atlas/original_CISChats/CIS_Chat_2026-04_016.md:81#r2`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:472`
  - `chatgpt_export/69ee5349-cfb0-83ea-b6ec-92edf14a4c5d#r5`

### Missing**: No mechanism to communicate *why* failure occurred to pipeline orchestrator beyond log
- support: 6 statements across 6 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...76106784688228799_x_cis_workbench_v1_extraction_analysis.md`
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...onal_intents/x_cis_critical_addition_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### ## Discovery 2: Missing Schema Implementation - **Architectural Significance**: Tables not created means the entire data model is unimplemented despite likely being designed - **Affected Layers**: Storage Layer, Data Model Layer - **Dependency Impact**: All CRUD operations are blocked - **Build Impa
- support: 6 statements across 6 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ea-2b7ec4d6d90c:Project Design and Database Integration`
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...ts/04_data_setup_instructions_extraction_analysis.md#r1`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Unresolved Orchestration: Multi-Model Output Reconciliation
- support: 6 statements across 6 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`
  - `...s/cis_pre_development_system_chatgtp_extraction_analysis.md`

### Architectural Significance**: Introduces governance classifications (LOCKED, OPERATIONAL, TRANSITIONAL, PRE-DRAFT, PLANNED, DEFERRED) as first-class architectural concepts
- support: 6 statements across 6 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### HARD_FAIL | Required output missing, schema invalid, forbidden strings detected | Cannot proceed.
- support: 6 statements across 6 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...42767492025744_x_07_knowledge_stream_extraction_analysis.md`
  - `...gacybuildfiles_x_07_knowledge_stream_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`
  - `...tional_intents/x_cis_execution_layer_extraction_analysis.md`
  - `contracts/CIS_Execution_Layer_Contract_v1.md`

### Foundational Prerequisites:** The missing Phase 0 contracts (source manifest, processing profile, review states) must be written before any Phase 1 pipeline scripts are built.
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.51 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Architectural Significance**: A single stray `)` character in LivePanel caused complete UI failure — indicates no validation layer exists between panel code and runtime execution
- support: 12 statements across 5 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`

### Job status polling missing | Needed after queue refactor | ADR-045 dashboard polling
- support: 9 statements across 5 document(s)
- nearest queue item 10 is only sim 0.34 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...s/ChatGTP_Project_Primer/11_TRANSITIONAL_IMPLEMENTATIONS.md`
  - `_archive/generated_script_artifacts/042926_Project_Primer.txt`

### Manual Paste Confirmed:** Auto-fetch model responses deferred — manual paste is the confirmed input method (ADR-029)
- support: 8 statements across 5 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:36`
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Post the three missing ADRs (070→ADR-027, 071→ADR-028, 072→ADR-029) and the three deferred tasks now, while we're in the DB.
- support: 8 statements across 5 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...intents/20260502_0047_05_adr_summary_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Slot 3 registration intentionally deferred — Qwen3.6-27B is a stronger architectural fit for CIS multimodal routing needs but requires real performance comparison before committing
- support: 7 statements across 5 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-27_2152.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-28_0239.md`
  - `cis_v1_vault/Phase_PD/CIS_Handoff_2026-04-27_2152.md`

### Video preprocessing in `cis_preprocess.py` — ffmpeg frame sampling plus Whisper transcription — was identified as the next build target but was not implemented.
- support: 7 statements across 5 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Filesystem canonicality is unresolved** — files_written polymorphism and runtime/manifests/ status create ambiguity about authoritative write paths.
- support: 7 statements across 5 document(s)
- nearest queue item 17 is only sim 0.35 — treat as NEW
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`
  - `...ts/ChatGTP_Project_Primer/archive/10_OPERATIONAL_REALITY.md`

### Validation not implemented** → Bad records pass through → Knowledge layer contaminated
- support: 7 statements across 5 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`
  - `...onical_build_sequence_plain_language_extraction_analysis.md`

### cis_review.py is the missing final command that moves a record from draft to checked/approved and captures human corrections.
- support: 7 statements across 5 document(s)
- nearest queue item 8 is only sim 0.41 — treat as NEW
  - `..._Master_Handoff_files/CIS_Handoff_Review_Command_Session.md`
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### ADR-048 must be locked before any new intake work begins.** ADR-045 closure makes this the sole remaining gap.
- support: 7 statements across 5 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### ADR candidate 4 — Notes field definition The Notes field in session close is defined with specific qualifying criteria: pending decisions, warnings, gotchas, partially built work, deferred context.
- support: 7 statements across 5 document(s)
- nearest queue item 22 is only sim 0.37 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `CIS_Creative_Intelligence_System_v1/Phase_PD/ADRs.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_012.md`

### Gap**: Need a MemoryReliability schema that tracks session type, claim context, and validation status
- support: 7 statements across 5 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### It identifies the 15 SESSION_INSIGHT_RECORDs as deferred backlog, not implemented.** They remain identified/mapped/deferred, awaiting execution layer stability.
- support: 7 statements across 5 document(s)
- nearest queue item 15 is only sim 0.47 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Knowledge Layer is a Gap**: Despite being called "knowledge records," there is no knowledge formation, semantic indexing, or ontology enforcement.
- support: 7 statements across 5 document(s)
- nearest queue item 1 is only sim 0.55 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Storage Implications**: Must be stored in gap tracking system with indexing by subsystem and target resolution
- support: 7 statements across 5 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`

### Content Validation**: There is no validation of the content before it is served.
- support: 6 statements across 5 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`
  - `.../functional_intents/primer_update_v2_extraction_analysis.md`
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### This is a major architectural correction. The file reveals that the missing layer is not more model capability. The missing layer is **capture, verification, and promotion infrastructure** that allows intelligence work to become trustworthy system knowledge.
- support: 6 statements across 5 document(s)
- nearest queue item 22 is only sim 0.35 — treat as NEW
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:564`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### The actual gap is a `manifest_v1.json` schema file in `runtime/schemas/` to match the other schemas written last session.
- support: 6 statements across 5 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Gap**: No validation that one model's output is valid input for next model
- support: 6 statements across 5 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Human Review**: Required when validation fails, ambiguity unresolved, retries exhausted
- support: 6 statements across 5 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...887271442881_x_cis_critical_addition_extraction_analysis.md`
  - `..._legacybuildfiles_x_cis_workbench_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...s/cis_legacybuildfiles_consolidation_extraction_analysis.md`
  - `...s_cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Slot 1 is running but fragile, Layer 2 is the only missing verification gate, and Slot 3 registration is blocked by an unresolved evaluation decision.**
- support: 6 statements across 5 document(s)
- nearest queue item 16 is only sim 0.41 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Whether handoff files should be copied, moved, or generated directly into canonical folder is unresolved.
- support: 6 statements across 5 document(s)
- nearest queue item 18 is only sim 0.36 — treat as NEW
  - `...04-21_App showing black screen after code change.md:907`
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`

### The Blueprint is explicit: knowledge does not exist as a primary input layer.
- support: 6 statements across 5 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...nce_System_LegacyBuildFiles/X_01_SYSTEM_BLUEPRINT.md:86`
  - `...telligence_System_LegacyBuildFiles/X_01_SYSTEM_BLUEPRINT.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`
  - `architecture_atlas/cis_chat_2026_04_008_extraction_analysis.md`

### Gap**: Knowledge object schema is not fully defined; it will emerge from drive audit.
- support: 6 statements across 5 document(s)
- nearest queue item 3 is only sim 0.40 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Dependency Impact:** Record provenance is incomplete without prompt version linkage
- support: 6 statements across 5 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`

### assert res24[0] == FunctionDefinition( NoneToken(), name=String('func'), parameters=(), body=CodeBlock( Declaration( Variable(Symbol('a'), type=FloatType( String('float32'), nbits=Integer(32), nmant=Integer(23), nexp=Integer(8) ) ) ), Declaration( Variable(Symbol('c1'), type=Type(String('bool')) ) )
- support: 6 statements across 5 document(s)
- nearest queue item 6 is only sim 0.21 — treat as NEW
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r0`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r1`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r4`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r5`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r6`

### Corrupt Manifests**: L2 fails if manifest is malformed or missing required fields
- support: 5 statements across 5 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...tion/functional_intents/queue_worker_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### Runtime Manifest Validation** — No validation layer for runtime manifest operations
- support: 5 statements across 5 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`

### Missing Feedback Loops**: The system has no correction, governance, retrieval-improvement, archive-learning, continuity/memory, or project-output feedback loops.
- support: 5 statements across 5 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### Defines the total map of layers and where execution fits structurally, including the critical clarification that the execution layer exists between intelligence and application.
- support: 5 statements across 5 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...cyBuildFiles/_CIS_The pattern across the CIS docs.md:26`
  - `...em_LegacyBuildFiles/_CIS_The pattern across the CIS docs.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...yBuildFiles/_CIS_The pattern across the CIS docs.md:219`
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Draft Type Taxonomy Gap**: Unrecognized filename patterns are silently skipped, potentially causing data loss if operators are unaware of the naming convention requirements.
- support: 5 statements across 5 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...ctional_intents/cis_download_watcher_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`
  - `...primer_update_governance_contract_v1_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Error Handling Gap**: Silent failures (log missing → return None) hide operational issues.
- support: 5 statements across 5 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...raction/functional_intents/decisions_extraction_analysis.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md`

### Gap:** `load_json` and `save_json` raise exceptions directly, while `run_command` captures them
- support: 5 statements across 5 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...xtraction/functional_intents/helpers_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### If many records fail validation due to a missing field, the schema may need to be updated rather than forcing data into the old shape.
- support: 5 statements across 5 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`
  - `...l_intents/1777410199041831732_readme_extraction_analysis.md`
  - `...n/functional_intents/project_helpers_extraction_analysis.md`
  - `...on/functional_intents/update_prefill_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`

### States:** Open (identified but unresolved), Resolved (ADR proposed and locked)
- support: 5 statements across 5 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...xtraction/functional_intents/session_extraction_analysis.md`

### Aspirational/Not Yet Built**: Intake layer (ADR-048), manifest stability (ADR-047), Slot 1 automation, run_l2 dashboard polling, expansion policy
- support: 5 statements across 5 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Then paste the decisions output so we can see the full ADR list and confirm nothing is missing.
- support: 5 statements across 5 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### - "Embedded governance" is a Build Plan v2 philosophical target. The creator should eventually experience trust and continuity — not visible constitutional machinery. Governance should become ambient, not explicit.
- support: 5 statements across 5 document(s)
- nearest queue item 21 is only sim 0.34 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...2_constitutional_memory_governance_primer_rewrite.md:17`
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Partial round visibility** — Models see question-only state, reducing hallucination risk from incomplete context
- support: 5 statements across 5 document(s)
- nearest queue item 1 is only sim 0.22 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `..._legacybuildfiles_x_cis_workbench_v1_extraction_analysis.md`
  - `...ession_insight_record_2026_04_20_001_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### Dashboard expansion** - blocked by monolith; requires modularization ADR
- support: 5 statements across 5 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### The system has 6 unresolved gaps** that must be addressed for full operational maturity: queue worker validation, dashboard queue polling, run_l2 execution, cold start validation, draft intake, and filesystem governance.
- support: 5 statements across 5 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...lender_2_80_fundamentals_transcripts_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`
  - `...ts/20260505_0119_13_runtime_topology_extraction_analysis.md`

### Architectural Significance**: Formal zone classification (ACTIVE, MIRROR, ARCHIVE, LEGACY, TRANSITIONAL, DEPRECATED) for ADR-047 is unresolved
- support: 5 statements across 5 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Missing Governance:** The governance rules for deprecating a spine node and re-anchoring its records are defined but not implemented.
- support: 5 statements across 5 document(s)
- nearest queue item 17 is only sim 0.38 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_010_extraction_analysis.md`

### Architectural Significance**: Intelligence may regenerate summaries, tags, constraints, risk flags; may NOT silently overwrite user decisions, source identity, canonical IDs, locked project associations
- support: 5 statements across 5 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...chat_2026_04_006_extraction_analysis_extraction_analysis.md`
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### You did not paste the error message or screenshot. What did you see? Paste the terminal output or share a screenshot and I will tell you exactly what to do.
- support: 5 statements across 5 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...01_CORE/moved_SESSION_DEBRIEF_2025-09-07_21-57-27.md#r1`
  - `...canonical build sequence and architectural dependencies`
  - `...l build sequence and architectural dependencies.md:1387`
  - `...pts/2026-04-22_Model registry API implementation.md:246`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:194`

### push_cis_live() exists but has no integration point**: This function was created without a corresponding application update cycle to wire it into, indicating a gap between function development and system integration.
- support: 12 statements across 4 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...de_chat_transcripts/2026-04-20_Resuming creative VM work.md`
  - `...unctional_intents/cis_live_handoff_1_extraction_analysis.md`

### Transitional Gap Identification**: If a reduction cannot be made, the builder must identify the gap and its target resolution.
- support: 12 statements across 4 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Architectural Significance**: Previously implicit risk now explicitly tracked in 07; distinct from execution ownership gap and intake ownership gap
- support: 8 statements across 4 document(s)
- nearest queue item 21 is only sim 0.34 — treat as NEW
  - `.../2026-04-30_primer_stabilization_and_intake_architecture.md`
  - `...26-05-02_constitutional_memory_governance_primer_rewrite.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Mediation Gap**: The most significant architectural gap is the missing mediation automation — the Hermes agent must manually read script output and perform mediation.
- support: 8 statements across 4 document(s)
- nearest queue item 20 is only sim 0.44 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### No Reliable Fetch Target Exists**: Auto-fetch feature permanently deferred; no development resources should be allocated to it.
- support: 7 statements across 4 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:12`
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...reative_Intelligence_System_v1/memory_additions_20260420.md`

### Missing `description` field causes silent failure — no error returned, no record created.
- support: 7 statements across 4 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Authority Source** | Architecture specs and ADR-derived rules; standalone contract missing
- support: 7 statements across 4 document(s)
- nearest queue item 22 is only sim 0.39 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_0722_extraction_analysis.md`
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### The Execution Layer is the missing foundational layer that makes everything else real.**
- support: 6 statements across 4 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...egrated_vision_cis_core_architecture_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...ntents/phase_0_5_replan_orchestrator_extraction_analysis.md`

### Primary theme: Pre-intelligence capture infrastructure, session continuity, project-aware intake, dashboard UX, and discovery of missing data-capture gates before intelligence extraction.
- support: 6 statements across 4 document(s)
- nearest queue item 15 is only sim 0.39 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Gap**: No automated validation engine that checks extraction output against contract rules
- support: 6 statements across 4 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Missing Downstream Layers**: The capture layer reveals significant gaps in extraction, knowledge formation, retrieval, and application layers that must be built.
- support: 6 statements across 4 document(s)
- nearest queue item 1 is only sim 0.47 — treat as NEW
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### This analysis is what triggered the recognition in subsequent sessions that session transcript extraction is the missing capability — the "session end hook" Karpathy describes is exactly what the current extraction work is building.
- support: 6 statements across 4 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### The system has multiple unresolved ADRs** — ADR-047 (manifest directory) pending.
- support: 6 statements across 4 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...s/ChatGTP_Project_Primer/11_TRANSITIONAL_IMPLEMENTATIONS.md`
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### Phase 0-to-Phase 1 Bridge**: Missing contracts identified but not blocking; must be resolved before Phase 1 exits
- support: 6 statements across 4 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Description:** If state update fails after output generation, execution is incomplete.
- support: 5 statements across 4 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Governance Layer**: Blocked by undefined state management and application layer
- support: 5 statements across 4 document(s)
- nearest queue item 21 is only sim 0.52 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Gap Chunking**: Each gap is a chunk with fields: subsystem, gap_description, target_resolution
- support: 5 statements across 4 document(s)
- nearest queue item 13 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Merge layer not implemented** → No draft knowledge_records → No validation → No review → No indexing → No retrieval
- support: 5 statements across 4 document(s)
- nearest queue item 7 is only sim 0.31 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Dependency Impact**: Creates a persistent gap in the session record — post-close work is invisible to future sessions
- support: 5 statements across 4 document(s)
- nearest queue item 8 is only sim 0.36 — treat as NEW
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`

### L2 Context Constraint Validation** — No validation for files exceeding context limit
- support: 5 statements across 4 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### The CIS architecture has a missing layer between the Application Layer and the Knowledge Layer: the **Session Initialization Layer**.
- support: 5 statements across 4 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...chat_2026_04_001_rantwiceby accident_extraction_analysis.md`
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Circular Dependency (Potential):** If the spine ingestion pipeline depends on a processing profile, and the processing profile contract is missing, there is a circular dependency on undefined work.
- support: 5 statements across 4 document(s)
- nearest queue item 17 is only sim 0.39 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Loop: extract → review → gap identification → prompt tuning → re-extract → improved quality.
- support: 5 statements across 4 document(s)
- nearest queue item 13 is only sim 0.38 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Identified post-commit work gap — work done after close+commit has no capture path
- support: 4 statements across 4 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Multiple unresolved gaps remain, particularly around intelligence tier routing, cost/quality metrics, and non-linear project evolution.
- support: 4 statements across 4 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...onal_intents/x_10_application_stream_extraction_analysis.md`

### That's what the build plan needs to address. And that's what was missing from the previous assumed build plan. --- Before we go further, what are the things you wanted to address before the build plan rewrite? You said there were a few. Let's get them on the table so we're working against a complete
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...406-b978-6e0379ba80ea:Build plan rewrite preparation#r2`
  - `...at_transcripts/2026-04-23_Starting a new session.md:516`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### Dependency Impact**: Introduces formal state machine for memory updates with explicit states (APPROVED, REJECTED, DEFERRED, FAILED_APPLY, FAILED_REVIEW, CONFLICT_BLOCKED)
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...primer_update_governance_contract_v1_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Missing Validation Layer: Pre-Snapshot Validation Automation
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`
  - `...e_system_legacybuildfiles_x_03_state_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Project Linkage is Incomplete**: `project_id` is stored but `project_title` is None.
- support: 4 statements across 4 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...l/extraction/functional_intents/logs_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### None detected**: No validation feedback that corrects user input
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...ion/functional_intents/ingest_spines_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`
  - `...xtraction/functional_intents/app_api_extraction_analysis.md`

### This is a documentation failure: the placeholder was not clearly marked as a placeholder and the user ran it expecting it to work.
- support: 4 statements across 4 document(s)
- nearest queue item 22 is only sim 0.30 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### Known active entry: CIS Live rounds form session dropdown bug — DEFERRED/LOW.
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-05_0427.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`
  - `...transcripts/ChatGTP_Project_Primer/Current State Updated.md`

### Lifecycle**: Sequential execution in early phases; concurrent execution deferred
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### Dependency Impact:** Requires input validation that accepts partial/evolving definitions rather than rejecting incomplete inputs.
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### The most important realization is that CIS is a self-structuring system with explicit feedback loops, and the execution bridge layer is the critical missing piece that must be defined before any implementation can proceed.**
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `.../cis_predev_infrastructure_plan_docx_extraction_analysis.md`
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...onical_build_sequence_plain_language_extraction_analysis.md`
  - `DEV-PIVOT-08_FRONT_DOOR_SPEC.md`

### Constraint 2 — Execution layer gap.** The execution layer — the headless runtime that converts workflow intent into deterministic commands, state transitions, and validated outputs — does not yet exist in unified form.
- support: 4 statements across 4 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...hoosing an AI platform for professional project guidance.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### File Not Found → Re-execute Write → Re-verify**: Corrects missing files.
- support: 4 statements across 4 document(s)
- nearest queue item 17 is only sim 0.37 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify_semantic.py`

### API decisions endpoint requires description field — batch curl commands must include it or they fail silently
- support: 4 statements across 4 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Gap**: Specific interface panels and their behavior are not defined.
- support: 4 statements across 4 document(s)
- nearest queue item 8 is only sim 0.31 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### CIS Live Dependency:** CIS Live is designed to solve the multi-model collaboration gap, but CIS Live was not operational during the session where it was being used as a collaboration tool.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### ADR-048 intake layer not yet built — human still manually transfers structured content
- support: 4 statements across 4 document(s)
- nearest queue item 11 is only sim 0.33 — treat as NEW
  - `.../2026-04-30_primer_stabilization_and_intake_architecture.md`
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...ranscripts/ChatGTP_Project_Primer/10_OPERATIONAL_REALITY.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Draft intake | No validation (human copy-paste) | Schema validation at /api/drafts/stage
- support: 4 statements across 4 document(s)
- nearest queue item 11 is only sim 0.37 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Missing state machine** → blocks all source processing
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...ents/cis_execution_layer_contract_v1_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_execution_layer_extraction_analysis.md`
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`

### Conflict Routing**: No escalation path for unresolved conflicts
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.48 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Contract Gap**: Contract rejected if implementation reveals missing dependencies
- support: 4 statements across 4 document(s)
- nearest queue item 6 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### States**: draft, reviewed (not implemented), promoted (not implemented)
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `...traction/functional_intents/cis_live_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### Missing Governance**: There is no governance rule for what happens when `cis_verify.py` returns a FAIL.
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Unresolved Application Surface: Memory Search**: The application interface for searching the memory file is not defined.
- support: 4 statements across 4 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### New plan must be organized around problems actually blocking work: session context loss, build discipline not enforced, verification not happening, build plan stale, reorientation doc out of date.
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Handoff Assembly → Downloadable Package**: Bridge proposed (cis_build_handoff_package.py) but not implemented
- support: 4 statements across 4 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...hat_transcripts/ChatGTP_Project_Primer/08_OPEN_QUESTIONS.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### Decision Log** — Preserves decisions, rationale, deferred ideas; does not keep transient errors or repeated explanations
- support: 4 statements across 4 document(s)
- nearest queue item 18 is only sim 0.36 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### Session close is partially automated** — Field 5 auto-population and handoff file generation work, but manual handoff gathering for session start remains the largest automation gap.
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### The gaps I flagged are still valid observations about the handoff documents themselves — but the framing should have been "here is what is missing from this handoff package" not "do this before you close."
- support: 4 statements across 4 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### Missing or truncated logs (`extract.log`, `normalize.log`, `system_log.md`) block session close verification.
- support: 4 statements across 4 document(s)
- nearest queue item 8 is only sim 0.46 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...is_predev_infrastructure_plan_claude_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### No retry or escalation logic exists**: Any failure in the session close workflow results in incomplete state persistence.
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### But the canonical relationship between this folder, Obsidian vault, knowledge records, and ADR/reorientation updates remains unresolved.
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### *What this enables:* The system cannot produce invalid outputs. Every object in the system has a documented, enforced history of what happened to it.
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...Chats/CIS_Canonical_Build_Sequence_Plain_Language.md:43`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...nal_CISChats/CIS_Canonical_Build_Sequence_Plain_Language.md`
  - `...onical_build_sequence_plain_language_extraction_analysis.md`

### This creates a governance gap where knowledge layer behavior is governed by unverified contracts.
- support: 4 statements across 4 document(s)
- nearest queue item 1 is only sim 0.32 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...re_atlas/cis_chat_2026_04_001_extraction_analysis.md:45`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`

### Runtime Impact**: L2 verification may fail silently or produce incomplete results for large files
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Swarm/multi-agent orchestration** — deferred until single-role agents are stable; prerequisites are stable knowledge layer, reliable retrieval, consistent workflow structure, controlled intelligence execution
- support: 4 statements across 4 document(s)
- nearest queue item 21 is only sim 0.55 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...s_cis_legacybuildfiles_consolidation_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### This reframes the entire intake problem from "we need better tools" to "we need a missing architectural layer."
- support: 4 statements across 4 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Blocked by: nothing — can be drafted in parallel with ADR-045 completion.
- support: 4 statements across 4 document(s)
- nearest queue item 12 is only sim 0.38 — treat as NEW
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `ADRs/ADR-047_SCOPE_PREDRAFT.md`

### ADR-046 | Filesystem Governance — groundwork during PD.5, lock deferred post-ADR-045
- support: 4 statements across 4 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### ADR-048 — LOCKED (Phase 1 and Phase 2 complete; Phase 3 deferred)
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...transcripts/ChatGTP_Project_Primer/Current State Updated.md`

### Minimal dashboard should be built in Phase 1**: Not deferred to Phase 5.
- support: 4 statements across 4 document(s)
- nearest queue item 20 is only sim 0.34 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...l build sequence and architectural dependencies.md:2534`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Decision Logging Form**: Blocked by missing dashboard endpoint for decision CRUD operations.
- support: 4 statements across 4 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### ### Missing Governance: 1. **Template Governance**: Rules for template instantiation not defined. 2. **Domain Governance**: Rules for domain instantiation not defined. 3. **Phase Governance**: Rules for phase transitions not defined. 4. **Category Governance**: Rules for category definition not defi
- support: 4 statements across 4 document(s)
- nearest queue item 21 is only sim 0.36 — treat as NEW
  - `...app_concept_workflow_template_extraction_analysis.md#r2`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...lopment_system_architecture_7_extraction_analysis.md#r2`
  - `...tents/the_ai_ten_commandments_extraction_analysis.md#r2`

### ## Critical Gaps | Gap | Description | Impact | |-----|-------------|--------| | Complete architecture | All 20+ files are unread | BLOCKER - cannot proceed without content | | System topology | No internal structure defined | BLOCKER - no architecture to extract | | Execution model | No runtime beh
- support: 4 statements across 4 document(s)
- nearest queue item 22 is only sim 0.37 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...al_intents/moved_requirements_extraction_analysis.md#r5`
  - `...on/functional_intents/read_me_extraction_analysis.md#r3`

### Architectural Significance**: ADR-045 implementation is partially operational but not fully closed; verify_contract worker has unresolved flag mismatch bug
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...P_Project_Primer/_backups/20260502_0047/01_CURRENT_STATE.md`
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`

### Apr 22 Claude responded: Good question to resolve before locking the schema, because the answer changes the data model.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...04-23_Video preprocessing schema definition setup.md:54`
  - `...4-24_CIS phase 1 intelligence extraction handoff.md:251`
  - `...e_atlas/original_CISChats/CIS_Chat_2026-04_003.md:43#r1`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### The missing Phase 0 contracts also need to come before cis_spine_intake.py per the contract-first rule.
- support: 4 statements across 4 document(s)
- nearest queue item 17 is only sim 0.42 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...egrated_vision_cis_core_architecture_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### Verification Contract**: 568 verifications run, 41 unresolved FAILs — ongoing verification process
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0413_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### `system says success → user asks to verify → command output checked → incomplete visibility rejected → verification method corrected`
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:195`
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:365`
  - `Hermes Agent Full Documentation.md:9365`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### This represents a significant architectural gap that must be addressed before the extraction pipeline can be considered production-ready.
- support: 4 statements across 4 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...n/functional_intents/session_extract_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Tier 7: BLOCKED (placeholder per build plan: "Do not design implementation until Tier 6 is verified stable")
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md:79`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md`
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md:9`

### The segmentation thresholds, merge floor, and quality gate criteria mentioned in ADR-031's rationale were deferred explicitly to ADR-033, which was not written this session.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### **Gate requirement:** No gate blocks on `rejection_rationale`. It is populated as part of normal deliberation. The Eric Gate briefing surfaces any `rejection_rationale` rows for the active trail — Eric sees what was considered and rejected before approving the chosen path. An empty table is visible 
- support: 4 statements across 4 document(s)
- nearest queue item 5 is only sim 0.49 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_1_DESIGN.md:108`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_1_DESIGN.md:63`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md:152`
  - `DEV-PIVOT-02_ENFORCEMENT_ARCHITECTURE_V3.md`

### Extraction Validation**: No validation for extracted insights
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### The prompt version tracking gap was identified and explicitly deferred as lower priority. It was not added to the task list or the next steps.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...-24_CIS phase 1 intelligence extraction handoff.md:1062`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### **Second reason it wouldn't have hard-stopped anyway:** `hard_stop_enabled: bool = False` by default. Out of the box this guardrail only *warns* — it never halts. The `[BLOCKED: ...4 times]` you saw on `search_files` was the warn/block path on the idempotent-no-progress counter, which does block at 
- support: 4 statements across 4 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...b662dad0751:Loop-breaker block-contract schema draft#r1`
  - `PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md:25`
  - `PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md:28`
  - `PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md:30`

### So my answer to "how would you build in the guardrails I need": **exactly the design ChatGPT and I roughly agree on — override plane, thin hook, role-policy-from-data, human-only spine approval, advisory epistemic gates — but built one guardrail at a time, override-plane-first, each proven-disableab
- support: 4 statements across 4 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `...5b-5c39-4e77-8476-521153c1e51a:Project files update#r10`
  - `..._are_these_files_in_guardrail_extraction_analysis.md#r1`
  - `..._x_cis_discovery_workbench_v1_extraction_analysis.md#r1`
  - `hermes_session/v4pro/session_20260825_170835_7fee96c8/10.0`

### Deployment has a gap**: ensure_models_table is not wired into ensure_tables(), meaning fresh DB deployments will fail.
- support: 13 statements across 3 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### Architectural Significance**: The Resolve button in the Live panel toggled state but the form (solution textarea, decided by field, confirm button) was never implemented — backend route existed but frontend form was always missing
- support: 11 statements across 3 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### Dashboard insight capture → Database | Not implemented | Cannot capture from dashboard
- support: 9 statements across 3 document(s)
- nearest queue item 14 is only sim 0.32 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### PD.5 Steps 1-6 | ADR-045 Execution Queue | Queue could be built independently | Queue blocked by verification pipeline
- support: 8 statements across 3 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `_archive/generated_script_artifacts/042926_Project_Primer.txt`

### Missing relationship map**: No single doc governs doc hierarchy, change propagation, or archive reality updates.
- support: 7 statements across 3 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...nd_offs_cis_handoff_current_position_extraction_analysis.md`

### Architectural Significance**: Four defined states (OPEN, DEFERRED, RESOLVED, SUPERSEDED) with implied transitions
- support: 6 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...06699132426333_x_cis_discovery_model_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### GAP**: No verification that registered sources are correct or complete
- support: 6 statements across 3 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...raction/functional_intents/librarian_extraction_analysis.md`
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Documentation Gap Pattern**: There is a systemic pattern where important infrastructure details are set up correctly in the moment but never formally documented.
- support: 6 statements across 3 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`

### State Registry**: Required for proper hierarchical status expression, but explicitly deferred to build-plan reconstruction stage
- support: 6 statements across 3 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

### Live Session Resolution**: If unresolved, note in Notes field; do not block session close
- support: 6 statements across 3 document(s)
- nearest queue item 22 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Session panel | Initialize session with handoff package | Not implemented | ADR-048 Build 7
- support: 6 statements across 3 document(s)
- nearest queue item 8 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`

### Resolve Button Form**: Never built — required frontend implementation before session hygiene was possible
- support: 6 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Draft panel | View/Edit/Approve/Reject/Supersede drafts | Not implemented | ADR-048 Phase 1
- support: 6 statements across 3 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Gap**: No mechanism to improve retrieval based on reconciliation outcomes
- support: 5 statements across 3 document(s)
- nearest queue item 3 is only sim 0.42 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### Project must exist (if `project_id` is provided) before task creation — though not enforced at database level.
- support: 5 statements across 3 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`
  - `...n/functional_intents/project_helpers_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### First: qwen_vl_utils appeared to be missing but was actually installed — the problem was that #!/usr/bin/env python3 picked up the system Python instead of the gpu-test Python.
- support: 5 statements across 3 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Exit codes: 0 = success, 1 = inventory file missing, 2 = all files failed
- support: 5 statements across 3 document(s)
- nearest queue item 13 is only sim 0.39 — treat as NEW
  - `...action/functional_intents/cis_intake_extraction_analysis.md`
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`
  - `SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`

### New Understanding**: Cold start recovery validation is DEFERRED, meaning queue state may be lost on restart.
- support: 5 statements across 3 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_1852_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Application Gap**: There's no application-layer interface for verification — no dashboard, no API, no CLI beyond the raw script — making it invisible to any higher-level system monitoring.
- support: 5 statements across 3 document(s)
- nearest queue item 6 is only sim 0.38 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### No consistency checks | No validation that captures are complete | **MISSING**
- support: 5 statements across 3 document(s)
- nearest queue item 18 is only sim 0.35 — treat as NEW
  - `.../functional_intents/primer_update_v3_extraction_analysis.md`
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### FAIL:** "FAIL: Proposal section missing", "FAIL: Proposal missing ### Summary", "FAIL: Proposal missing ### Recommendation", "FAIL: Proposal ### Summary empty", or "FAIL: Proposal ### Recommendation empty"
- support: 5 statements across 3 document(s)
- nearest queue item 13 is only sim 0.36 — treat as NEW
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`
  - `CIS_TIER_6_3_ORCHESTRATOR_KANBAN_INTEGRATION_DESIGN.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### Session Start**: Blocked if handoff folder is missing or `cis-start` command is not installed.
- support: 5 statements across 3 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### No search optimization | Search not improved based on results | **MISSING**
- support: 5 statements across 3 document(s)
- nearest queue item 3 is only sim 0.45 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### A formal governance layer is missing and must be created immediately.** The CIS_Primer_Update_Governance_Contract.md must exist and be locked before any further primer updates.
- support: 5 statements across 3 document(s)
- nearest queue item 5 is only sim 0.44 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...update_governance_contract_dicussion_extraction_analysis.md`

### Sequencing Constraint**: ADR-043 must be verified (no contradictions, no undefined transitions, no missing authority boundaries, no impossible verification requirements) and frozen before any runtime implementation begins.
- support: 5 statements across 3 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### CIS_LIVE Auto-fetch Permanently Deferred**: Major models (Claude, Gemini, ChatGPT) do not expose stable public share URLs suitable for programmatic fetch.
- support: 4 statements across 3 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...reative_Intelligence_System_v1/memory_additions_20260420.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Exit codes: 0 — Success (new or existing run returned) 1 — Input error (empty intent, DB failure) ```
- support: 4 statements across 3 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`
  - `CIS_TIER_11C_DRAFTER_REVIEWER_HANDOFF_SPECIFICATION.md:26`
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### Log file append**: If log file is locked or missing, test still passes but warning is emitted
- support: 4 statements across 3 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...on/functional_intents/cis_test_queue_extraction_analysis.md`
  - `contracts/CIS_Execution_Layer_Contract_v1.md:146`

### The cleanest solution is a # NOCHECK marker pattern, or simply: when running self-check, skip the forbidden strings check (the content is the list definition, not placeholder content).Check the lines flagged by self-checkCheck the lines flagged by self-checkThe forbidden strings are in the list defi
- support: 4 statements across 3 document(s)
- nearest queue item 1 is only sim 0.29 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...rchChatsProjectsCodeCustomizeDesignMoreRecentsHidePhase.txt`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### The file says logs must not be empty or truncated but does not define thresholds or validation rules.
- support: 4 statements across 3 document(s)
- nearest queue item 13 is only sim 0.38 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_014_extraction_analysis.md:408`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### After: Registry must distinguish `available` (weights on disk), `loaded` (in GPU memory), and `unavailable` (weights missing or env broken).
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### 1172: e('textarea', { placeholder:'Notes — pending decisions, warnings, deferred context (optional)', value:notes, onChange:ev=>setNotes(ev.target.value), style:taStyle(48), disabled:!!closeResult?.success })
- support: 4 statements across 3 document(s)
- nearest queue item 22 is only sim 0.20 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Unresolved FAILs**: 41 remain unresolved, no retry logic documented
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...itutional_memory_governance_revision_extraction_analysis.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### This tells us whether video preprocessing and extraction are stubbed, partially implemented, or missing entirely — and that determines whether we're one afternoon of work away from a viable proof of concept or facing a deeper gap.
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `...transcripts/2026-04-22_Model registry API implementation.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### FAIL:** "FAIL: Consensus signal invalid — missing <marker>" or "FAIL: requires_eric_review is false"
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### CIS is missing: index file, backlinks, linting/health checks, session end hook, daily flush process.
- support: 4 statements across 3 document(s)
- nearest queue item 15 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### Gap**: Execution layer is identified as missing but not yet defined
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Documentation gap reinforcement**: Undocumented configuration → failure → recovery → no documentation → future failure (negative reinforcement cycle)
- support: 4 statements across 3 document(s)
- nearest queue item 6 is only sim 0.39 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Reviewer feedback loop visibility:** The reviewer returns OBJECTIONS with specific missing/incorrect files.
- support: 4 statements across 3 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Gap Retrieval Loop**: Gaps retrieved → resolution patterns identified → gap resolution improved → faster resolution
- support: 4 statements across 3 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Gap → Output Risk Loop**: Named gaps → known risks → mitigation strategies → reduced output risk → fewer gaps
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...tional_intents/cis_slot1_healthcheck_extraction_analysis.md`

### Gap**: No formal state tracking for infrastructure components
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Architectural Significance**: `cis-log insight` subcommand does not exist.
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Missing directories**: Script creates directories but doesn't validate parent paths
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...action/functional_intents/cis_intake_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Missing Runtime Bridge: Application ↔ Runtime State Synchronization
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Now it is known to be filename-pattern based, requiring operator naming discipline and missing non-standard filenames.
- support: 4 statements across 3 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`

### Operator Routes:** Still directly execute runtime scripts - this is an incomplete bridge that requires queue-backed execution.
- support: 4 statements across 3 document(s)
- nearest queue item 12 is only sim 0.40 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### Section 6 (Next Actions) depends solely on `build_plan_nodes WHERE status IN ('PENDING','IN_PROGRESS')` — empty when all nodes are COMPLETE/DEFERRED
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.55 — treat as NEW
  - `DEV-PIVOT-04_APPLICATION_ENFORCEMENT_SPEC.md`
  - `DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md`
  - `PROPOSAL_SESSION_TO_SPINE_WRITE_PATH.md`

### Governance Gaps**: The memory store has no access control, no audit trail, no validation, no deletion capability, and no lifecycle management.
- support: 4 statements across 3 document(s)
- nearest queue item 18 is only sim 0.40 — treat as NEW
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...tion/functional_intents/memory_store_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Continuity/Memory Loop: Handoff → State Transfer → State Verification → Gap Detection → Checklist Update
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...raction/functional_intents/x_control_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Instead it became an archaeology session — verifying what actually existed on disk, discovering a schema file that had never been updated to reflect the real pipeline output, clearing stale test data, and ultimately identifying that the session memory system is the most critical missing capability i
- support: 4 statements across 3 document(s)
- nearest queue item 15 is only sim 0.41 — treat as NEW
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Now: Files >~300 lines may exceed L2 verification context — creates verification gap for large governance contracts
- support: 4 statements across 3 document(s)
- nearest queue item 22 is only sim 0.40 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### Session close orchestration is blocked by**: Database, `cis-log`, `cis-start`, manifest system, knowledge record system, git integration, vault setup
- support: 4 statements across 3 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Verification Blocked by Operator Abstraction**: Previously, verification pipeline fixes were assumed to be independent.
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### Unresolved Orchestration:** **Distillation Workflow** - The exact workflow (who creates, who reviews, how is it promoted) is not defined.
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...l_intents/1777410199041831732_readme_extraction_analysis.md`
  - `...nts/runtime_implementation_contracts_extraction_analysis.md`

### Queue Worker Reload Bridge**: Missing verification step between patch deployment and runtime
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`

### Governance Layer**: Blocked by glossary trigger definition, inheritance surface process, filesystem zone classification
- support: 4 statements across 3 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...06699132426333_x_cis_discovery_model_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Resolution:** Live verification confirms ADR-SEED-017 does not exist in project_decisions.
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`

### Missing Governance:** Trigger point ownership and accountability
- support: 4 statements across 3 document(s)
- nearest queue item 11 is only sim 0.35 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Everything else that was supposed to be a contract document from the roadmap — source manifest, processing profile, review states — does not exist as a file on disk.
- support: 4 statements across 3 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### Infrastructure dependencies are unverified** — sqlite3 CLI was missing on the target VM.
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### No Integrity Validation**: No validation that database state is consistent after insert
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...tion/functional_intents/dedup_memory_extraction_analysis.md`
  - `...unctional_intents/ingest_extractions_extraction_analysis.md`

### Storage Implications**: Missing record blocks verification same as missing Completion Manifest
- support: 4 statements across 3 document(s)
- nearest queue item 18 is only sim 0.34 — treat as NEW
  - `...ChatGTP_Project_Primer/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`

### Verification**: Pass = proof-of-work shown; Fail = no verification, task considered incomplete
- support: 4 statements across 3 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_30_1852_extraction_analysis.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`

### Extraction quality on multi-figure comic covers is a known gap — do not scale ingestion until multi-pass is proven in Phase 1
- support: 4 statements across 3 document(s)
- nearest queue item 13 is only sim 0.18 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_003.md`

### Run the .tables check and paste the result.You said: How will you know when to add Frame-level data (deferred — not needed for Phase 1) to the table?How will you know when to add Frame-level data (deferred — not needed for Phase 1) to the table?Apr 23Claude responded: You will tell me.You will tell 
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Build Plan Rewrite is the Central Bottleneck**: Multiple downstream activities (ADR-048 Phase 3, 14, 15 population) are blocked by the build plan rewrite, which itself is blocked by CIS Live #034 insights integration.
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

### Unresolved Segmentation Policy:** The segmentation policy thresholds (duration cap, merge floor, quality gate criteria) are not yet locked.
- support: 4 statements across 3 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Fail**: Invalid profile value → pipeline blocked; missing model → profile blocked; state violation → rollback required
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ents/cis_processing_profile_contract_extraction_analysis.md`
  - `...intents/cis_source_manifest_contract_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Agent Object**: Execution layer still placeholder; agent roles, capabilities, lifecycle undefined
- support: 4 statements across 3 document(s)
- nearest queue item 21 is only sim 0.53 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Missing Authorization**: No access control on who can view or act on approvals
- support: 4 statements across 3 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Missing:** Explicit interface between drift detection and user notification
- support: 4 statements across 3 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...nctional_intents/x_00_operator_model_extraction_analysis.md`

### Rule:** If interface allows material to enter without producing structured output, it is incomplete.
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.28 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Because this functionality is core to the intended use of the system I am not sure if it should be deferred.
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`
  - `...transcripts/2026-04-22_Model registry API implementation.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### This is exactly the gap you identified — the system has been building forward without all its foundations formally locked as files.
- support: 3 statements across 3 document(s)
- nearest queue item 22 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0836_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### None implemented**: Only validation failure is missing title
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`
  - `...traction/functional_intents/projects_extraction_analysis.md`

### Description**: Per-update artifact containing proposed file changes, rationale, unresolved disagreements, model review notes, constitutional concerns, apply decision
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `...update_governance_contract_dicussion_extraction_analysis.md`
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### Black screen dashboard bug fixed — missing comma between OperatorPanel and DraftIntakePanel createElement calls
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-05_0323.md`

### return jsonify({"error": f"Missing required fields: {missing}"}), 400
- support: 3 statements across 3 document(s)
- nearest queue item 19 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...n/functional_intents/project_helpers_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/api/models.py`

### Gap**: App update function not yet integrated into main application
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### No Relationship Validation**: No validation that parent-child relationships are correct
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`
  - `...unctional_intents/ingest_extractions_extraction_analysis.md`

### Missing paths**: If TUTORIAL_ROOTS don't exist, scan silently skips
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Missing**: Metrics (records produced, errors, latency)
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.42 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...traction/functional_intents/pipeline_extraction_analysis.md`

### No validation** of record `status` values — assumes they match expected state machine.
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...n/functional_intents/project_helpers_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Cross-field validation**: No validation that corrections don't create inconsistencies
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`

### This is not implemented but is identified as highly relevant.
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.32 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_002_extraction_analysis.md:366`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_015_extraction_analysis.md`

### Protocol skip**: No retry mechanism identified — protocol compliance not enforced
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Placeholder Detected → Fix Content → Re-verify**: Corrects incomplete content.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Missing Worker Layer**: The most critical gap is the absence of any worker implementation to actually execute jobs.
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Not implemented in API layer**: Review states exist in data model (status field) but no review workflow endpoints
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...raction/functional_intents/decisions_extraction_analysis.md`
  - `...xtraction/functional_intents/app_api_extraction_analysis.md`

### The update path is: real behavior reveals a gap → architect documents the insight → this roadmap is versioned and updated → subsequent build steps reflect the correction.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### Unresolved Application Surfaces:** The "Spine Manager" panel in the workbench is not yet designed or built.
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.48 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...cybuildfiles_x_cis_critical_addition_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### What remains genuinely unresolved** but isn't a cleanup problem — it's a build problem:
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `...s/cis_pre_development_system_chatgtp_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### This is not a minor configuration issue—it is a fundamental architectural gap that must be resolved before the system can operate as designed.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...orm Chat/vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md`

### “No error shown” is not sufficient if output is truncated or incomplete.
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Affected Layers:** Execution Layer (missing), Synthesis Layer (missing), Merge Layer (missing)
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`
  - `...xtraction/functional_intents/read_me_extraction_analysis.md`

### Application development** — deferred until Phase 0–4 exit criteria are met; building the app before the runtime is premature regardless of how ready it feels
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### User corrections blocked by mutability validation**: Cannot accept user corrections without mutability validation
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...intents/cis_source_manifest_contract_extraction_analysis.md`
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`

### Cross-reference validation**: No validation that draft doesn't conflict with existing canonical records
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Missing:** Dashboard button to trigger verification and display results
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### Processing → Review | Extraction output | Human review interface | NOT IMPLEMENTED
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Discovery 4: Intake Ownership Gap — Missing Staged Intake Layer
- support: 3 statements across 3 document(s)
- nearest queue item 11 is only sim 0.38 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Qualifying criteria: deferred decisions, warnings/gotchas, mid-thought work, anything deferred that isn't a next step.
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `CIS_CONTEXT_CONTRACT.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Fail**: Missing contract authority, permission violation, validation failure, context insufficient
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...intents/cis_source_manifest_contract_extraction_analysis.md`

### This is a deterministic error, distinct from "section missing" (heading not
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`
  - `CIS_TIER_6_3_ORCHESTRATOR_KANBAN_INTEGRATION_DESIGN.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### Fail Condition**: Incomplete corpus access, pattern document not read first, output is a summary
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### Future State**: May need multi-worker or priority queueing (explicitly deferred)
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.42 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`
  - `PLAN_RECONCILIATION.md`

### Gap Tracker**: No application surface for tracking transitional gaps
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Runtime Impact**: Operator must fill in all fields correctly or handoff is incomplete.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Incomplete Insight Records**: Must be updated before insights folder is complete
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### *DRAFT status: This document is a Hermes-generated proposal. It does not represent an Eric-approved decision. Items classified as Deferred-unscheduled are NOT cancelled — they await scheduling by Eric after external advisor review.*
- support: 3 statements across 3 document(s)
- nearest queue item 20 is only sim 0.47 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`
  - `PLAN_RECONCILIATION.md`
  - `PLAN_RECONCILIATION.md:31`

### Lifecycle**: Identified → evaluated → either eliminated (becomes reduction) or deferred (becomes gap)
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### ### Promotion Logic - OPEN → DEFERRED (acknowledged, scheduled) - OPEN → RESOLVED (fix confirmed) - OPEN → SUPERSEDED (architectural change) - DEFERRED → RESOLVED (fix confirmed) - DEFERRED → SUPERSEDED (architectural change) ### Rejection Paths
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `...l_intents/cis_conflict_append_extraction_analysis.md#r5`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `HANDOFF_SCHEMA.md`

### Unresolved Application Surface: Progress Monitoring
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Missing Execution Specs**: Workbenches cannot operate without execution behavior defined
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### Segmentation Validation**: Not implemented — PySceneDetect not installed
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Missing optional fields represented as `null` consistently (never omit a known field).
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `...l_intents/1777410199041831732_readme_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### This is a validation gap — no error surface for missing required fields.
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Model registry validation | No validation for model data | MEDIUM — will be needed
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.25 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### No Request Validation**: No validation of request parameters
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...extraction/functional_intents/health_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### No validation layer exists for any component** — all bug detection is manual
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`

### Missing Validation Discovered**: Raw output format is not validated, creating risk for downstream normalize.
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.40 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### ## Discovery 5: Priority System (Reserved) - **Architectural Significance**: Priority column defined (lower number = higher priority) but marked as "reserved for future use" - **Affected Layers**: Execution Layer, Orchestration Layer, Queue Management - **Dependency Impact**: Future priority-based s
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...ntents/migrate_execution_jobs_extraction_analysis.md#r4`

### Project Definition → State Machine**: Not implemented — project creation doesn't trigger state machine
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Requirement:** Visibility into unresolved questions (08_OPEN_QUESTIONS.md)
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...de_chat_transcripts/ChatGTP_Project_Primer/00_START_HERE.md`
  - `DEV-PIVOT-11_CORPUS_SCRAPING_PROPOSAL.md`

### Returns `False` otherwise (including when `run_id` does not exist).
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.26 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`
  - `cis_v1_vault/runtime_scripts/runtime/api/drafts.py`

### States**: `OPEN`, `IN_PROGRESS`, `RESOLVED`, `DEFERRED`, `ESCALATED`, `BLOCKED`, `ARCHIVED`
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Anchor Validation**: Not implemented — enforcement logic is defined but not coded
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...action/functional_intents/myproject3_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### ADR form uniqueness validation**: No validation for ADR number uniqueness
- support: 3 statements across 3 document(s)
- nearest queue item 9 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`

### Claude responded: ADR-008 and ADR-010 are missing from the database — they were written in conversation but never actually logged with cis-log decision.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Architectural Significance**: The root cause of recurring context and orientation loss is NOT missing features but a missing execution layer.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.50 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-28_0553.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Session close gate logic**: Pre-close state check defined but not implemented
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.41 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`

### From `memory_additions_20260420.md` — three deferred features and three decisions that were generated as additions to MEMORY.md but never posted as ADRs or tasks:
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `...tive Intelligence System (CIS)/cis_system_bundle/README.txt`
  - `...ts/2026-04-21_App showing black screen after code change.md`
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`

### Runtime Bridge**: Governance contracts reference operational reality but cannot enforce it until implementation catches up.
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Session as governed work container**: Focus, active build target, open jobs, unresolved risks, close gates
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.49 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`

### Dependency Impact**: The log is consumed by session start protocol (to check for unresolved failures).
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`

### Knowledge Layer**: Blocked by institutional memory integration path (requires ADR-048 Phase 1)
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...al_intents/archive_08_open_questions_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Fail**: Missing field, failed sync check, missing handoff folder, ADR numbering gap
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `...ents/post_commit_addendum_2026_04_18_extraction_analysis.md`

### Gap**: Session sequence position uses controlled vocabulary (earliest, early, mid, recent, current) but no mechanism exists to determine position
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.37 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Session Resolution**: Added as mandatory governance step; resolve form implementation identified as gap
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### Memory missing → re-discovery → extraction triggered → memory formed
- support: 3 statements across 3 document(s)
- nearest queue item 7 is only sim 0.33 — treat as NEW
  - `...n/functional_intents/session_extract_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### The project files are read-only so I'll produce this as a document to copy into the Memory doc, then build the Live panel.Memory additions — future features deferred from sessionMemory additions — future features deferred from sessionGood — that's documented.
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0139_extraction_analysis.md`
  - `_archive/Refactoring CIS application into modular structure.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_008.md`

### Notes field must follow defined criteria (deferred decisions, warnings/gotchas, mid-thought work, deferred non-next-step items)
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Whether the runtime code (/mnt/projects/cis/runtime/) had a git repo initialized at the time of this session was explicitly flagged as uncertain — "if initialized — verify with git status." This uncertainty about whether the code was version-controlled is a significant gap that was never formally cl
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_014_extraction_analysis.md:383`
  - `...ession_insight_record_2026_04_17_002_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### This session was attempting to implement ADR-021 (CIS Live broadcasts active session only) and ADR-023 (copy prompt replaces copy URL), which had been deferred across multiple previous sessions.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### eric@creative-vm:~$ sqlite3 /mnt/projects/cis/memory/cis_memory.db ".tables" captures decisions schema_versions tasks corrections insights session_log eric@creative-vm:~$ sqlite3 /mnt/projects/cis/memory/cis_memory.db ".schema extraction_runs" 2>/dev/null || echo "table does not exist" eric@creative
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Knowledge States**: Forming, incomplete, stable, refined, archived
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`

### Draft intake bridge | Dashboard panel | /api/drafts/stage → DB | Not implemented
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.35 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`

### Not implemented**: No mechanism to improve retrieval based on usage patterns.
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.49 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`
  - `..._legacybuildfiles_x_cis_workbench_v1_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Impact**: Knowledge operations may receive incomplete context
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Fields in the real record that are missing from knowledge_v1.json: record_id, record_type, source_name, source_unit, knowledge_category, subject, tags, summary, visible_text, scene_description, layout_description, mood_style, uncertainty, retrieval_text, project_title, active_stages, source_origin, 
- support: 3 statements across 3 document(s)
- nearest queue item 19 is only sim 0.35 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ture_atlas/original_CISChats/CIS_Chat_2026-04_003.md:81`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### ### 6. Knowledge Formation is Blocked by Missing Transcript Pipeline **Before this file**: Knowledge formation was assumed to be directly from sessions. **After this file**: Knowledge formation requires a transcript pipeline that does not yet exist. This is a blocking dependency that must be resolve
- support: 3 statements across 3 document(s)
- nearest queue item 22 is only sim 0.36 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...intents/billing_reference_log_extraction_analysis.md#r2`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Knowledge formation is blocked by acceptance** - No output enters the knowledge layer without passing through review
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Knowledge retrieval validation**: No validation for retrieval queries
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.46 — treat as NEW
  - `.../functional_intents/mnt_projects_cis_extraction_analysis.md`
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Intelligence Layer** blocked by: Preprocessing Pipeline, Record Schema, Version Management, Routing Policy, Project Context System
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`

### Runtime Impact**: No runtime can be planned until the execution layer gap is understood in context of the full corpus.
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_0722_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`

### Blocked By**: Knowledge object schema, approval workflow, query protocol
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.46 — treat as NEW
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Video Pipeline**: Blocked by ffmpeg, Whisper, vision extraction implementation; cannot generate knowledge records without pipeline
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0139_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### **Right now — manual paste is the only method.** You copy the relevant section and paste it into whichever model you're talking to. That's the current workflow.
- support: 3 statements across 3 document(s)
- nearest queue item 20 is only sim 0.22 — treat as NEW
  - `...04-18_Session execution and image pipeline setup.md:985`
  - `..._Intelligence_System_v1/memory_additions_20260420.md:11`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### ## Discovery 3: Human as Harness Coordinator - **Architectural Significance**: The human is not a passive user but an active routing, validation, and state-update node in the system architecture. This is a first-class architectural role. - **Affected Layers**: Protocol layer, governance layer, execu
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.36 — treat as NEW
  - `...edev_infrastructure_plan_docx_extraction_analysis.md#r3`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Execution jobs table** (defined but not implemented — ADR-045)
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Architectural Significance**: Forces explicit identification of deferred automation.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`
  - `contracts/CIS_Automation_Reduction_Contract_v1.md`

### This is not just housekeeping — unresolved sessions represent incomplete architectural decisions or unlogged insights.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Missing Automation**: All handoff processes are manual — no automated construction, validation, or transfer exists.
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### No hallucination controls**: No validation of extraction outputs beyond human review
- support: 3 statements across 3 document(s)
- nearest queue item 22 is only sim 0.22 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### This gap — currently filled by shell scripts and manual steps — must be stabilized before any application work begins.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0836_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### - **New Layers:** None. The document describes a generic, idealized system architecture (e.g., "Layered Architecture," "Microservices") but does not introduce any new, concrete layers for the CIS. - **Split Layers:** None. - **Runtime Bridges:** None. - **Orchestration Changes:** None. - **Governanc
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...lopment_system_architecture_1_extraction_analysis.md#r2`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`

### Source Intake Panel**: File upload, intake trigger, feedback (currently missing — no spinner, no success state, no error message).
- support: 3 statements across 3 document(s)
- nearest queue item 11 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Record → Frontier Bridge**: Not implemented (frontier integration missing)
- support: 3 statements across 3 document(s)
- nearest queue item 20 is only sim 0.49 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...s/cis_pre_development_system_chatgtp_extraction_analysis.md`

### Feedback loop created**: Dashboard reveals missing project context → project schema refined.
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.41 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...chat_2026_04_013_extraction_analysis_extraction_analysis.md`

### Contract Authority Application Surface**: Registry management interface not implemented.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### Failure Mode**: Models appear `active` in registry but API calls fail due to missing/invalid keys
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### Gap**: Dashboard used for session close fields but integration not fully defined
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Now ADR-045, queue-backed Verify Contract, frontend modularization, full filesystem curation, full transcript archaeology, and L2 rerun are identified as deferred work items.
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...ions_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### Not implemented**: No tracking of who or what triggered the health check
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/health_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`
  - `...unctional_intents/cis_live_handoff_1_extraction_analysis.md`

### Also need to check — ADR-008 and ADR-009 exist but there's no ADR-008 gap issue since the DB shows them both present.
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Only gap in numbering is ADR-008 appearing out of sequence, which is a display issue not a data issue — not worth renumbering locked records.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### No capture governance loop | No review of capture quality | **MISSING**
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### It carries forward phase state, locked ADRs, completed work, next steps, open questions, and critical paths.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...nctional_intents/context_compression_extraction_analysis.md`
  - `YOUR_DOCUMENT_MAP.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Draft governance | Operator approval → Canonical record → Governance enforcement | Closed loop | Not implemented
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...nts/runtime_implementation_contracts_extraction_analysis.md`

### Intake Validation**: No validation for staged content before approval
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### The segmentation decision that would have allowed the schema to be finalized was deferred.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### The video source_unit schema was proposed and then blocked by the segmentation strategy question.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0139_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Failure Mode**: Missing table causes SQL errors on first API call
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `...action/functional_intents/cis_review_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### CREATE TABLE is skipped when table exists, so missing columns must be added here.
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...04-18_Session execution and image pipeline setup.md:334`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_migrate_041.py`

### `ensure_tables()`** — Tasks table must exist; this function creates it if missing.
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### The second direction change was the gap audit — the question of whether any critical data capture was missing before intelligence work began.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.40 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Content Gap Identified**: `CIS_LIVE.md` currently contains only a test string
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Execution Queue Completion**: Blocked by verify_contract patch validation
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Verification is immediate** — runs after every file write, not deferred
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.28 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...unctional_intents/cis_convert_export_extraction_analysis.md`

### It does not solve a model confidently producing plausible but wrong content that passes all three layers. That failure mode requires domain knowledge at the human review step — the chain surfaces it, but a human who doesn't know what correct looks like will still miss it. That is a documentation and
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.41 — treat as NEW
  - `...-04-25_Verification mechanism for completed work.md:155`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### The model registry was designed with a three-tier architecture (local, remote, agent) and a status model that reflects actual model state: available (weights on disk), loaded (in GPU memory), unavailable (weights missing or env broken).
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...tion/functional_intents/all_insights_extraction_analysis.md`

### The application layer is not the next build target. The missing piece remains the execution/core workflow that sits underneath it.
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `...CIS HANDOFF — vLLM _ Qwen VL Evaluation (April 12, 2026).md`
  - `...DOFF — vLLM _ Qwen VL Evaluation (April 12, 2026).md:60`
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### Architectural Significance:** Three critical capture systems missing before Phase 1 extraction can begin: decision logging form, extraction run logging table, review/promotion UI
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ents/post_commit_addendum_2026_04_18_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`

### Architectural Significance**: Running real files (not test files) through the pipeline to discover missing processing profiles, unanticipated file types, wrong validation rules
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `...nal_CISChats/CIS_Canonical_Build_Sequence_Plain_Language.md`
  - `...nts/cis_plain_language_build_roadmap_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### This was not a designed architecture—it emerged from missing abstraction boundaries.
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.31 — treat as NEW
  - `...ldfiles_x_cis_discovery_workbench_v1_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### Now it is a named architectural gap with a systematic reduction path (ADR-048).
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Storage validation**: No validation that all drives are mounted.
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `...gacybuildfiles_x_cis_execution_layer_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### # Transitional Implementations # Updated: 2026-04-29 # Purpose: Prevent temporary fixes from becoming invisible permanent architecture. # Every item here has a planned replacement. Track it explicitly.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.44 — treat as NEW
  - `...TP_Project_Primer/11_TRANSITIONAL_IMPLEMENTATIONS.md#r0`
  - `...buildfiles_x_cis_reinforcement_model_extraction_analysis.md`
  - `...n_backups_20260430/11_TRANSITIONAL_IMPLEMENTATIONS.md:0`

### What's missing from Phase 0 exit criteria: **10–20 records from real archive material in draft state.** The commands exist but haven't been run on real archive files at scale yet.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...onical_build_sequence_plain_language_extraction_analysis.md`
  - `...transcripts/2026-04-22_Model registry API implementation.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### Next action: Prepare Tier 7 Router Reclassification proposal only. Do not implement Tier 7 yet. Do not reopen Tier 6 remediation. Do not expand PLAN_RECONCILIATION.md into a new governance phase.
- support: 3 statements across 3 document(s)
- nearest queue item 22 is only sim 0.38 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md`
  - `chatgpt_export/6a2720f6-47a8-83ea-93b6-a3d06a284498#r5`
  - `proposals/POST_TIER10_PLANNING_REVIEWER_RESPONSE.md`

### Intake is independent | Intake is blocked by verification deployment
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0408_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Phase 3 deferred | Incomplete draft pipeline | Prioritize Phase 3 implementation
- support: 3 statements across 3 document(s)
- nearest queue item 4 is only sim 0.34 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...extraction/functional_intents/drafts_extraction_analysis.md`

### Unified Execution Layer**: controlling step sequencing, data flow, output normalization (missing)
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`

### Output is valid when: - Every failure mode is specific and reproducible - Every proposed fix is concrete and implementable - The verdict is unambiguous — pass or fail, not maybe - At least three failure modes were tested even if none were found
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...l build sequence and architectural dependencies.md:1762`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_015.md:190`
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Gap**: Memory files are staging area — but no retention policy
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.49 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Verification Log Storage**: Cumulative history stored; session-specific extraction rules missing
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Ingest State**: Incoming, Processing, Completed, Legacy, Incomplete
- support: 3 statements across 3 document(s)
- nearest queue item 8 is only sim 0.40 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...em_LegacyBuildFiles/_CIS_The pattern across the CIS docs.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### The question is: do we design the spine ingestion pipeline now and write all migrations together, or do we write the Segment migration as a placeholder with `anchor_node_id` as a nullable field and design the spine pipeline in a dedicated session?
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.37 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Content Validation**: No validation of extracted signal quality
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `...n/functional_intents/session_extract_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### No stage validation**: Pipeline stages can be triggered in any order, with no validation that prerequisites are met.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...onal_intents/x_cis_critical_addition_extraction_analysis.md`
  - `...traction/functional_intents/pipeline_extraction_analysis.md`
  - `...traction/functional_intents/projects_extraction_analysis.md`

### Dashboard ↔ Pipeline | Not implemented | Pipeline status not visible in dashboard
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### 1. Status clarity pass — human-readable labels, visible affordance, direct status dropdown or action buttons 2. Cycle order if kept: open → scheduled → in_progress → waiting → blocked → done 3. DONE state visually unmistakable, shows completed_at 4. Sidebar as status board 5. Fix TODAY and OVERDUE f
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.46 — treat as NEW
  - `...4631-9f82-a589d531d7bc:Hermes Pass 5 planning review#r1`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md:29`

### 4. **The Drafter may not invent or materially alter the initiating goal.** If the Drafter identifies a gap in the intent, it may flag it for Eric but must not rewrite the goal to fill the gap.
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `DEV-PIVOT-10_ADR-SEED-014_CONTRACT.md`
  - `DEV-PIVOT-10_ADR-SEED-014_CONTRACT.md:14`
  - `DEV-PIVOT-10_ADR-SEED-014_CONTRACT.md:42`

### Missing Validation Layer**: The Verifier stub provides no actual validation, meaning no unsupported claims detection, no schema validation, and no content verification exists.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `DEV-PIVOT-15_SESSION_OPEN_ITEMS.md`

### Unresolved Storage Rules**: The storage rules for the local model weights are not defined (e.g., where to download them, how to verify them).
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### The linear phase model also created a trap: it deferred agentic behavior to Phase G, but the problems you're experiencing right now — branches not captured, verification skipped, new ideas consuming sessions — are exactly what a minimal build-phase agent could address today, on existing infrastructu
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.47 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`

### The selectors in v2 (`textarea[placeholder*='Send a message']`, `[data-message-author-role="assistant"]`, etc.) are best guesses from the v1 script.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`
  - `claude_chat_transcripts/captures/README.md`

### Copy Prompt:** Pass = prompt generated with all fields; Fail = missing role or session context
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0547_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

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

### **Why:** This is the automation of what Eric did manually this session — Reviewer challenged, Eric carried to Implementer, Implementer defended, Eric carried back. The system should absorb this labor.
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md:14`
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md:122`
  - `DEV-PIVOT-15_SESSION_OPEN_ITEMS.md:8`

### Run the schema update above first, then confirm and I will write the ensure\_tables() additions.You said: I am confused, are we continuing to expand the db tables or are you rolling back to a file base structure.I am confused, are we continuing to expand the db tables or are you rolling back to a fi
- support: 3 statements across 3 document(s)
- nearest queue item 19 is only sim 0.28 — treat as NEW
  - `...at_transcripts/2026-04-23_Starting a new session.md:763`
  - `...at_transcripts/2026-04-23_Starting a new session.md:766`
  - `_archive/CIS_Handoff_2026-04-23_0434_ChAT.md:276#r1`

### Deferred items logged → Session start surfaces them → Verification completed → No item forgotten
- support: 14 statements across 2 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Distillations are chunked by schema: Session Focus, Key Decisions, Architectural Insights, Operational Changes, Risks Identified, Deferred Work, Next Actions.
- support: 8 statements across 2 document(s)
- nearest queue item 1 is only sim 0.36 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### The ADR panel sort/filter improvement (newest-first toggle, status filter buttons) was identified as useful, logged as a task in the dashboard, and explicitly deferred as not blocking build work.
- support: 8 statements across 2 document(s)
- nearest queue item 7 is only sim 0.32 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Conflict Escalation Loop:** Conflict identified → Cannot resolve → Appended to conflict register → Deferred → Next audit → (repeat until resolved)
- support: 7 statements across 2 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Missing Action Endpoints**: The approval flow is incomplete - only listing exists, no approve/reject actions
- support: 7 statements across 2 document(s)
- nearest queue item 16 is only sim 0.47 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Runtime Impact**: Snapshot operations fail silently with misleading error messages ("current guest configuration does not support taking new snapshots"), requiring diagnostic steps to identify blockers.
- support: 6 statements across 2 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`
  - `...anscripts/2026-04-21_Proxmox VM snapshot creation.md:37`

### The system has **no validation of capture types**, **no content moderation**, **no duplicate detection**, and **no quality scoring**.
- support: 6 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### cis_download_watcher.py | Watch for downloads | Not implemented | Automated download management
- support: 5 statements across 2 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...s/20260505_0058_02_next_build_target_extraction_analysis.md`

### No cross-capture chunking | No linking between related captures | **MISSING**
- support: 5 statements across 2 document(s)
- nearest queue item 17 is only sim 0.48 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### If workflow step cannot be executed consistently on real material → it is incomplete and must be refined
- support: 5 statements across 2 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Dependency Impact**: Session close depends on `from pathlib import Path` which was missing.
- support: 5 statements across 2 document(s)
- nearest queue item 8 is only sim 0.47 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

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

### States**: Incomplete (some files missing), Complete (all files present), Loaded (all files loaded into memory), Analyzed (corpus has been analyzed)
- support: 5 statements across 2 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Deferred Frontend Integration**: Dashboard changes are explicitly deferred to the next session, creating a temporary gap where the schema exists but the UI cannot create records with the new fields.
- support: 5 statements across 2 document(s)
- nearest queue item 10 is only sim 0.31 — treat as NEW
  - `...nts/adr_041_artifact_registry_schema_extraction_analysis.md`
  - `ADRs/ADR-041_Artifact_Registry_Schema.md`

### Gap**: Files are saved but not routed to any processor, indexer, or workflow
- support: 4 statements across 2 document(s)
- nearest queue item 1 is only sim 0.31 — treat as NEW
  - `...raction/functional_intents/librarian_extraction_analysis.md`
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### Transitional Gap Naming**: Trust is enforced through explicit gap identification
- support: 4 statements across 2 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### 15_INHERITANCE_INDEX.md**: Not yet populated, blocked by build plan rewrite
- support: 4 statements across 2 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### Gap**: No defined object for capturing and storing Eric's corrections
- support: 4 statements across 2 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### After**: Sound creates assets that become knowledge references for future work, creating a feedback loop.
- support: 4 statements across 2 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...l_intents/x_11_sound_stream_expanded_extraction_analysis.md`
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap**: Exact handoff protocol between models undefined
- support: 4 statements across 2 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Build Impact**: Requires queue refactor of Verify Contract; run_l2 queue job type deferred
- support: 4 statements across 2 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Runtime Impact:** Phase D validation checks for Intelligence Stream inclusion; missing stream blocks execution
- support: 4 statements across 2 document(s)
- nearest queue item 12 is only sim 0.44 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Model Routing:** Three-tier architecture designed but routing layer does not exist
- support: 4 statements across 2 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Status Vocabulary Separation**: Current coarse vocabulary (PRE-DRAFT / OPERATIONAL / LOCKED / NOT YET BUILT) must be separated into hierarchical implementation state (ADR overall vs.
- support: 4 statements across 2 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...traction/functional_intents/cis_live_extraction_analysis.md`
  - `CIS_Creative_Intelligence_System_v1/CIS_LIVE.md`

### 6 failure states (APPROVED, REJECTED, DEFERRED, FAILED_APPLY, FAILED_REVIEW, CONFLICT_BLOCKED)
- support: 4 statements across 2 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...primer_update_governance_contract_v1_extraction_analysis.md`

### Live sessions are architectural debt**: 5 open sessions (#002–#006) represent unresolved decisions that could affect Phase 1 design.
- support: 4 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### The verification step gets triggered by Claude, not requested by you.** After any significant build action, Claude produces the manifest and immediately asks: "Run verification now or flag this as deferred?" Deferred items are tracked and surface at session start next time.
- support: 4 statements across 2 document(s)
- nearest queue item 8 is only sim 0.41 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`

### None**: No validation of course content, no provenance tracking for suggestions
- support: 4 statements across 2 document(s)
- nearest queue item 3 is only sim 0.41 — treat as NEW
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### Dependency Impact**: Without formal queue definitions, the orchestrator cannot handle task prioritization, retry logic, crash recovery, or deferred execution.
- support: 4 statements across 2 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`
  - `CIS_TIER_11_UI_USABILITY_SPECIFICATION.md`

### The constitutional recognition of the human as an architectural gap is perhaps the most significant discovery — it reframes all current human-in-the-loop operations as temporary debt to be systematically resolved through abstraction layers, not as permanent design features.**
- support: 4 statements across 2 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Direct API routing to Claude/ChatGPT is deferred** - all model communication goes through Hermes Gateway.
- support: 4 statements across 2 document(s)
- nearest queue item 20 is only sim 0.48 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`
  - `PHASE_LOG.md`

### Contract missing → contract registry creation → validation enabled → governance restored
- support: 4 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### DB schema constraints are invisible** — NOT NULL and other constraints fail silently without surfacing in error messages.
- support: 4 statements across 2 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### DB table exists but schema/spec status is incomplete at this point in the transcript.
- support: 4 statements across 2 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Recommendation**: Add task state machine (backlog → planned → in_progress → completed → deferred)
- support: 4 statements across 2 document(s)
- nearest queue item 5 is only sim 0.36 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### Prompt Review State:** No validation that generated prompt is complete and correct
- support: 4 statements across 2 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`

### raise except ValueError as e: raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail=str(e) ) except Exception as e: logger.error(f"Error updating provider availability: {e}") raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update provider ava
- support: 4 statements across 2 document(s)
- nearest queue item 15 is only sim 0.21 — treat as NEW
  - `swa_project/social_work_ai/01_CORE/main.py#r0`
  - `swa_project/social_work_ai/01_CORE/main.py#r1`

### work by actively trying to find failure modes, edge cases, missing
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### Missing**: Rules for validating across multiple sources
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`

### Claude responded: All drives are mounted and the cache drive is missing from this output — which means /mnt/cache did not auto-mount after reboot.
- support: 3 statements across 2 document(s)
- nearest queue item 10 is only sim 0.38 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### System state visibility (users cannot easily tell if ComfyUI is running — identified gap)
- support: 3 statements across 2 document(s)
- nearest queue item 22 is only sim 0.23 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### Blocked by:** Nothing (can proceed in parallel with other setup)
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.42 — treat as NEW
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`

### Cloudflare full tunnel — deferred feature, should be a task with `deferred` status
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Missing source**: Blocks job creation with 400 error
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Batch curl commands with `&&` chaining fail silently on first error, preventing subsequent posts.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### The placeholder path `/path/to/downloaded/` in the git copy command was taken literally, causing a "No such file or directory" error.
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### This is a recurring failure mode — updating the reorientation doc keeps getting deferred and added to next steps, but next steps are what get deferred first when a session runs long.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Transitions**: Pending → Validating → Complete/Incomplete/Failed
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.43 — treat as NEW
  - `...intents/20260502_0047_05_adr_summary_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Hard Rejection**: Missing inputs, missing agent, missing key → HTTP error
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Build Impact**: Requires content classification before OCR invocation; merge script must handle missing OCR output
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Merge Validation** — No validation that merge produces coherent records
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...tents/1776042143355379182_x_03_state_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

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

### Draft rejection → (no path)**: Gap - no correction feedback to source
- support: 3 statements across 2 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0413_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### Error Handling is Silent**: Malformed records are silently skipped, creating invisible data loss.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`
  - `PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md`

### A9 | Missing required field returns error dict | cis_dispatch_drafter with empty topic | Returns dict with error key, no crash | Check error key present, no traceback
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Field 5 FAIL Count Loop**: Incorrect FAIL count → fix deferred → known issue → future fix → correct scope
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.46 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### Gap**: Logging goes to /logs/system_log.md, but no routing logic for different action types.
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### No Output Validation**: No validation that prefill JSON is well-formed
- support: 3 statements across 2 document(s)
- nearest queue item 19 is only sim 0.26 — treat as NEW
  - `...nctional_intents/deepseek_mcp_bridge_extraction_analysis.md`
  - `...on/functional_intents/update_prefill_extraction_analysis.md`

### Architectural Significance**: The unified control surface (Layer 8) is explicitly deferred until underlying systems are mature
- support: 3 statements across 2 document(s)
- nearest queue item 21 is only sim 0.23 — treat as NEW
  - `...ce_System_LegacyBuildFiles/X_01_SYSTEM_BLUEPRINT.md:121`
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`

### Lifecycle**: Created → Initializing → Ready/Incomplete/Failed → Active → Closed
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Manifest Namespace Objects**: Three classes defined but namespace separation not implemented
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`

### Mediation Notes as Placeholder**: The mediation notes section exists as an empty structure, awaiting integration with a mediation workflow that doesn't yet exist.
- support: 3 statements across 2 document(s)
- nearest queue item 21 is only sim 0.42 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Slot 3 is DEFERRED**: Qwen3.6-35B-A3B-FP8 (42 shards, ~35GB) is downloaded at /mnt/models2/, but registration is blocked pending Qwen3.6-27B evaluation.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

### raise ValueError("Cannot write to registry: artifact_identity.artifact_id is missing")
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.43 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### "CRITICAL: missing dependencies field was not detected — dependency check is broken"
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...uence_and_architectural_dependencies_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### Not implemented**: No message review, moderation, or approval workflow
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Routing Layer**: Blocked by registry schema implementation; cannot function without capability filtering and resource validation
- support: 3 statements across 2 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Reorganization**: Blocked by file map creation and knowledge record resolution.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Any session that started without the addendum silently lost the post-commit work.
- support: 3 statements across 2 document(s)
- nearest queue item 14 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Stream execution rejected if dependencies unresolved
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...7059416496004_x_cis_relationship_map_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### `PENDING_PROCESSING`: File awaiting downstream processing (not implemented)
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### `GET /api/collab/open-questions` - Retrieve all open questions
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.28 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24.md`

### Processing**: Read approved files, call approved tools/scripts, draft output, write only to sandbox or approved draft locations, record unresolved issues
- support: 3 statements across 2 document(s)
- nearest queue item 6 is only sim 0.41 — treat as NEW
  - `...i_execution_infrastructure_primer_v1_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### After: vLLM zombie processes are a known issue with an identified root cause (missing port pre-check) and a planned fix (Step 3).
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0836_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-29_0836.md`

### Live sessions #002–#006 unresolved**: Blocks next build work (governance requirement)
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### Missing Runtime Bridge: Memory Locking**: There is no defined mechanism for locking the memory file to prevent concurrent write conflicts.
- support: 3 statements across 2 document(s)
- nearest queue item 17 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Runtime Impact**: If the path is missing or unwritable, the handoff is lost.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Runtime Impact:** Once CIS Live is wired, branch notes become the missing lightweight documentation layer between handoffs and ADRs.
- support: 3 statements across 2 document(s)
- nearest queue item 22 is only sim 0.32 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### Build Impact:** Deferred work includes full transcript archaeology.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`

### Gap**: Dual-machine file sync conflicts are identified as risk, but no conflict resolution governance is defined.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Description**: Session becomes a first-class architectural object with states: Initializing, Ready, Incomplete, Failed
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...is_predev_infrastructure_plan_claude_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Conflict Logging → Resolution**: 3 conflicts resolved, 1 deferred — governance loop exists but is human-mediated
- support: 3 statements across 2 document(s)
- nearest queue item 21 is only sim 0.34 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Next is `SESSION_INSIGHT_RECORD_2026-04-22_002.md` (from 004.md) — this one was missing roughly 1650 lines covering the model registry build, the Resolve button fix, the WIAS workbook analysis, the archive structure revelation, the video tutorial use case clarification, the chat log ingestion revers
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.45 — treat as NEW
  - `...rchChatsProjectsCodeCustomizeDesignMoreRecentsHidePhase.txt`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### FAIL**: Missing tables, columns, indexes, or migration log entry
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`

### Multi-Tier Intelligence Routing Bridge**: Not implemented
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...818091549056_x_10_application_stream_extraction_analysis.md`
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`

### Gap**: No automated extraction of decisions from conversation — requires human to identify and post
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### The execution bridge docs are a newly identified gap between stream theory and runtime behavior.
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.48 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Tradeoff on what to build first: fix the auth config (5 min, unblocks orchestrator.py path entirely) before building the proposal-dispatch bridge — because draft's report suggests orchestrator.py may already run the full Drafter→reviewer loop once authed, which would mean impl's "missing bridge" exi
- support: 3 statements across 2 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `Claude Roadmap Audit 20260624.txt`
  - `claude crystallizes the vision.txt`

### Storage Implications:** UI component, blocked by frontend modularization ADR
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.23 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`

### Grepping the archive confirmed it was missing from both the current modular dashboard and the original monolith — this was a feature that had never existed at any point in the build, not something lost during the refactor.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### The frontend monolith, previously treated as deferred technical debt, becomes part of the topology risk map because a single syntax error can break the entire dashboard.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `...ession_insight_record_2026_04_20_001_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Agent Interface**: Not yet implemented; Phase H deferred
- support: 3 statements across 2 document(s)
- nearest queue item 21 is only sim 0.56 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Project Management Panel**: Blocked by undefined project management object schema and missing timeline/milestone infrastructure.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### route_task.py**: Blocked by model registry completion — registry is built but route_task.py not yet started
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...tion/functional_intents/all_insights_extraction_analysis.md`

### Task completion governance**: No validation that tasks are actually complete before marking them done.
- support: 3 statements across 2 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### The gap between "decision made in conversation" and "decision in DB" was entirely dependent on remembering to run SQL at the right moment.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Maturity Gap Loop**: Governance maturity > implementation maturity → ceremonial risk identified → PD.5 fixes defined
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Workflow Governance**: Not yet defined; workflow system deferred
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...action/functional_intents/record_001_extraction_analysis.md`

### Then we have a real picture of the gap and can decide whether writing spec docs into `docs/contracts/` is actually the right next move, or whether we go straight to `cis_spine_intake.py`.
- support: 3 statements across 2 document(s)
- nearest queue item 17 is only sim 0.39 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### 10: Container Mounts | Mount path doesn't exist | `docker run` exit code non-zero | Pre-flight mount check: `test -f /source/intent_memory.db || echo "MISSING"`.
- support: 3 statements across 2 document(s)
- nearest queue item 14 is only sim 0.32 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`

### Decision logging — confirmed gap The DB has a decisions table and ADRs.md regenerates from it, but there is no form to add decisions.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_012.md`

### Any governance contract or verification workflow that produces large outputs is operating with incomplete verification.
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.37 — treat as NEW
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### Requirement:** User must be able to see when AI actions are blocked by alignment check
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...nctional_intents/x_00_operator_model_extraction_analysis.md`

### `cis_lint.py`**: Future script for health checks (gap detection, stale data, broken links).
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### L3 audit rounds must complete before deployment** — cannot deploy with unresolved audit
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.44 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0413_extraction_analysis.md`
  - `...action/functional_intents/cis_verify_extraction_analysis.md`

### Architectural Significance**: Six specific bugs were identified and resolved during the audit process: empty verification checks, circular SHA extraction, model whitelist replacement, missing check_artifact_identity_block, migration re-run safety, and row_factory crash bug.
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.44 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0408_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-27_0408.md`

### The eventual application layer that exposes CIS capabilities to other users is Phase 5 and was explicitly out of scope for this phase.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### ADR-048 Phase 1 → Stub Population**: 13, 14, 15 population deferred until after ADR-048 Phase 1.
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

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

### Validation-to-Escalation Routing** - Not implemented
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.45 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Extraction Run Logging:** Required but not yet built — no mechanism for capturing run metadata
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
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

### Gap**: No defined interface between verification exit codes and pipeline state machine
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Missing drives**: VM boots without storage if drives are detached during snapshot.
- support: 3 statements across 2 document(s)
- nearest queue item 4 is only sim 0.18 — treat as NEW
  - `...26-04-21_Session close and handoff process clarification.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### File permission**: Write permission denied → project creation fails silently (no error handling)
- support: 3 statements across 2 document(s)
- nearest queue item 4 is only sim 0.27 — treat as NEW
  - `...raction/functional_intents/librarian_extraction_analysis.md`
  - `...traction/functional_intents/projects_extraction_analysis.md`

### Security model is unresolved** — dashboard has no authentication.
- support: 3 statements across 2 document(s)
- nearest queue item 10 is only sim 0.27 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### When analyzing documents, preserve: the four-loop feedback ecology, the WIAS model as both domains and production stages, the AI inference layer on Project objects, field authority and mutability rules on knowledge_records, and the execution layer gap as the primary current blocker.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.27 — treat as NEW
  - `...hoosing an AI platform for professional project guidance.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Versioning, not replacement | MASTER_ARCHITECTURE_MAP | Records are versioned; existing records are never silently overwritten
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.33 — treat as NEW
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Description**: Non-critical components that can be deferred
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.24 — treat as NEW
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`
  - `_archive/CIS Formal Phased Construction Plan.md`

### What was left unresolved Work that was started but not finished.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `YOUR_DOCUMENT_MAP.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Flask/Node/npm missing; Flask was installed, React served by CDN.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`

### The insight is about the build process itself: the gap between what Claude claims about its own capabilities in the moment and what is actually true about those capabilities caused a real disruption to the build workflow.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.33 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Discovery 4: Resolve Button Never Existed (Architectural Gap)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Distributed execution (hardware constraint makes this out of scope)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`
  - `ADRs/ADR-045_Execution_Queue_Ownership_Layer.md`

### New Understanding:** The system is not blocked by infrastructure.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`

### No output → project feedback | Captures not used to improve project | **MISSING**
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Current Status**: Not implemented (no retrieval system yet)
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`

### This was explicitly deferred in the reorientation doc as a parking lot item.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...tional_intents/x_01_system_blueprint_extraction_analysis.md`

### Current**: Status changes are direct field updates with no validation of state transition legality.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Build States**: blocked (prerequisite missing), ready (all dependencies met), in-progress
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Concurrent requests**: Blocked by single-threaded design
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...ion/functional_intents/ingest_spines_extraction_analysis.md`
  - `...nctional_intents/deepseek_mcp_bridge_extraction_analysis.md`

### Content-based draft classification**: Not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`

### Discovery 6: Ingestion Pipeline Lacks Merge Stage (Critical Gap)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Model registry API endpoint | Serve dynamic model roster | Not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### FAIL Placeholder detected: "TODO" found at line 47 of /path/to/file
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

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

### Input Validation**: source_id required, returns 400 if missing
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `.../functional_intents/advisor_external_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Decision Lock Protocol**: Immediate commit requirement replacing deferred documentation
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...ild_plan_v_2_memory_capture_strategy_extraction_analysis.md`
  - `...is_predev_infrastructure_plan_claude_extraction_analysis.md`

### The real missing layer (this is the answer to your question)**
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `...uild_Sequence/3 Platform Chat/CIS_Pivot_Chain of Thought.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Missing Progress Tracking**: No mechanism to track learning progress
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Missing Application Surface: Taxonomy Merge/Correction
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Missing Manifest**: Blocks preprocessing with exit code 1
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...on/functional_intents/cis_preprocess_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`

### Missing Ontology Mapping**: No connection to WIAS domain structure
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### This is a critical gap — the entire review/promotion workflow is undefined.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### No Correction Feedback**: No mechanism to detect unresolved conflicts
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### The file is an empty placeholder with no operational structure, no dependencies, no runtime behavior, and no governance rules.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.42 — treat as NEW
  - `...tion/functional_intents/instructions_extraction_analysis.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Runtime Selection Validation**: No validation that correct runtime is selected
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.21 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`

### There is no validation against an allowed set of types.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.20 — treat as NEW
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### Promoted**: (Not implemented — correction feedback path missing)
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Now update the ADRs.md in the vault to include the missing ones, then do a final git commit for the day:
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `cis_handoffs/CIS_Handoff_2026-05-02_0558_CORRECTED.md`

### Runtime Impact**: Silent failure mode — operator unaware of missing records.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ents/cis_dashboard_monolith_20260420_extraction_analysis.md`

### Impact**: Specification documents may be incomplete or incorrect
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...on/functional_intents/implementation_extraction_analysis.md`

### SCP Retry** — Not implemented; single attempt with status reporting
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### New Object**: Slot 3 (pending) — deferred, requires evaluation
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`

### Partial State Support:** Objects can exist in incomplete states (question-only rounds) and still be published
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### The removal cut the closing parenthesis that belonged to the outer flex container, leaving mismatched parens that silently killed the entire React app.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.25 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Unresolved Application Surfaces**: The application surface for monitoring the Phase 1 pipeline is not defined.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Validation Rule | Not defined per stage | Quality control incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### ValidationResult object** — defined conceptually but not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ntents/1775995115163043436_x_control_extraction_analysis.md`

### `draft` → `published` (future state, not implemented)
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

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

### what else is missing from the file that is making the process fail.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.41 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Missing Record**: Build rejected as verification-incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.36 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### ``` PROPOSED → PENDING → IN_PROGRESS → COMPLETE ↓ ↓ BLOCKED DEFERRED ```
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.43 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md:52`

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

### Transformation Tools** blocked by: Object System, Input Event System, Gizmo Rendering
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.20 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...lender_2_80_fundamentals_transcripts_extraction_analysis.md`

### Blocked By**: Missing cis_review.py, missing insight capture
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.36 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`

### Blocking:** If missing, system cannot remind user of required actions
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.42 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Dependency Impact**: Vault is incomplete without this folder.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...ents/cis_dashboard_monolith_20260420_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Runtime Blockers:** If any layer in the chain is missing, downstream layers cannot function.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Your CIS plan already gives the missing skeleton for that governance:
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...re-Development System/CIS_Pre-Development System_ChatGTP.md`

### Build Impact**: Requires implementation of placeholder modules as swappable components.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.36 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...anscripts/captures/2026-05-12_cis_kernel_session_capture.md`

### Build Impact**: cis_review.py is the highest priority missing component.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.41 — treat as NEW
  - `...egrated_vision_cis_core_architecture_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`

### Conflict register session dropdown**: Does not refresh without browser refresh (LOW severity, DEFERRED)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Claude responded: Starting with the most significant gap — SESSIONINSIGHTRECORD2026-04-23001.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Conflict Register** — Real-time visibility into unresolved conflicts
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Conflict: Deferred (not rejected, but postponed)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### The real blocker is not a missing feature — it's a trust and tracking problem.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### They are currently hardcoded placeholders (lines 2484-2492) and not wired to anything.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `...tion/functional_intents/all_insights_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Deferred work identified**: Previously deferred work was undefined.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_20_001_extraction_analysis.md`
  - `...ions_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### Deferred**: Application Layer depends on Execution Layer being proven first
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Dependency Impact:** The application layer depends on the infrastructure layer for serving, but the wiring between them is incomplete.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### `CIS_FILE_MAP.md` at `/mnt/projects/cis/` — the orientation document you've been missing
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `...26-04-21_Session close and handoff process clarification.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### That is the first real CIS production task, it's the intent source the trigger and the unified memory both need, and it's the thing that's been blocked for six months not by missing design but by missing constraint — which now exists.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...with_these_files_cis_operating_model_extraction_analysis.md`
  - `claude crystallizes the vision.txt`

### Discovery 5: Cold start validation is not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`

### Document Gap**: Operator documents transitional gap if no reduction possible
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.28 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Critical Missing Bridge**: The watcher has no API endpoint to push drafts into the database — it can only move files between filesystem zones.
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.27 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Draft Workflow**: (MISSING) No workflow exposure for draft intake
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### if self.error_code and self.error_message: # Note: `errors` can be removed once proposal A from # b/284179390 is implemented.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...intents/cis_source_manifest_contract_extraction_analysis.md`
  - `...project/social_work_ai/01_CORE/extended_operation.py#r2`

### Error: 400 for missing/invalid fields, 409 for duplicate id
- support: 2 statements across 2 document(s)
- nearest queue item 19 is only sim 0.27 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Fail Condition**: Missing sections, bullet list format, sanitized failures, missing ADR references where content overlaps
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify_semantic.py`

### FORBIDDEN_STRINGS = ["TODO", "[placeholder]", "[coming soon]", "[to be completed]",
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_convert_export.py`

### Missing knowledge record → Correction**: If `.json` or `.md` file is missing, human must regenerate before retrying close
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.29 — treat as NEW
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### FAIL:** "FAIL: Implementation section missing" or "FAIL: no artifact evidence in Implementation section"
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.36 — treat as NEW
  - `...itutional_memory_governance_revision_extraction_analysis.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

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

### No validation** — Flask reads file and returns it as-is; no content validation, no format checking, no size limits
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.24 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`
  - `...unctional_intents/cis_live_handoff_1_extraction_analysis.md`

### First: ChatGPT's description of Claude Projects is partially outdated or incomplete.** The document it produced describes Projects as essentially a "big shared prompt folder" with no real indexing.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.34 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Gap**: How all four feedback loops coordinate is not defined
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Gap**: How app consolidates three model responses not defined
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.28 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap: Response Capture Path from External Models Is Undefined
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.29 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### Gap**: Initial routing pointed to www subdomain with path filter
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### Gap**: Models not yet configured to read from creative-intelligence-system.com
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: How Worker 1 determines next worker based on task type
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`

### Gap**: No automated routing of content through trust zones
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Gap**: No defined rules for what constitutes canonical vs.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.31 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Gap**: No defined strategy for managing commit history
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Gap**: No defined translation layer between operator interface actions and runtime commands
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### Type:** Positive reinforcement — successful gap resolution strengthens the review process
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `...intents/cis_source_manifest_contract_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Gap:** No UX review performed beyond Eric's observations.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Gap:** How are superseded ADRs tracked and linked to replacements?
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Add or defer processing profile override with explicit gap note.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Gap**: No retry logic for transient failures (GPU OOM, file system errors)
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Gap**: No tracking of how often models are used or their success rates
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap:** Complete count would require scanning all 50+ runtime Python files.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Gap:** No defined mechanism for asset transfer between tools
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.25 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Phase Transition Authority Gap**: There is no defined authority or process for phase transitions.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.23 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Gap:** No formal separation yet — everything is intermingled.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_1_DESIGN.md`

### Processing path selection | Text, vision, hybrid defined but not implemented | Cannot execute
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.27 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Impact:** Data loss risk if addendum is forgotten or incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.29 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ents/post_commit_addendum_2026_04_18_extraction_analysis.md`

### Runtime Impact**: Unresolved next actions block or inform subsequent workflows
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.27 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Impact**: Cannot enforce primary + fallback requirement without capability definition
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Missing data**: If any sync target is missing or stale, session close is rejected
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### No output correction loop | Captured responses not verified | **MISSING**
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Response Validation** — No validation that pasted responses are from actual models
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `.../functional_intents/mnt_projects_cis_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Source Manifest | Structure not fully specified | Intake metadata incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`

### Intake Feedback:** No visual response after clicking INTAKE — gap identified but not fixed
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Intake Retry:** No retry mechanism because feedback is missing.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...action/functional_intents/cis_intake_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`

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

### Lifecycle**: Conflict identified → Append to register → (MISSING) Review → (MISSING) Resolve → (MISSING) Close
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Missing required file → improve retrieval mechanism**
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### Missing Intel sidebar wiring**: LOCAL tab not yet connected to live model data
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Missing Runtime Bridge: Dashboard to CLI**: The exact mechanism for the Dashboard to execute CLI commands (`cis-log`, `cis-start`, `git`) is not defined.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.30 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Slot 1 Validation**: No validation that Slot 1 is running before L2
- support: 2 statements across 2 document(s)
- nearest queue item 19 is only sim 0.26 — treat as NEW
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Missing `CIS_API_KEY` environment variable blocks remote API access
- support: 2 statements across 2 document(s)
- nearest queue item 14 is only sim 0.32 — treat as NEW
  - `...ction/functional_intents/gpt_gateway_extraction_analysis.md`
  - `...el/extraction/functional_intents/app_extraction_analysis.md`

### Missing items are identified and added to the package definition.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Missing state reporting**: If runtime doesn't report processing status, interface cannot show progress
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...tional_intents/x_cis_runtime_spec_v1_extraction_analysis.md`

### Missing Validation Gates**: Without enforcement, execution drifts from workflow
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.40 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...chat_2026_04_005_extraction_analysis_extraction_analysis.md`

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

### Preprocessing validation (does not interpret or modify meaning - but no validation specified)
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Impact**: Orphaned records possible; referential integrity not enforced
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Model Evaluation View**: Admin registry view for model evaluation work (testing/benchmarked models) not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### ### Runtime Pattern: Optimistic Operations All methods assume success and return None on failure rather than raising exceptions. This **optimistic pattern** pushes error handling to callers and creates silent failure modes. The system will silently swallow errors like database connection failures or
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `.../extraction/functional_intents/sweep_extraction_analysis.md`
  - `...intents/general_tasks_service_extraction_analysis.md#r5`

### Forbidden strings check (TODO, FIXME, PLACEHOLDER, HARDCODED, etc.) — skip content inside triple-backtick fences (known bug fix)
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...rchChatsProjectsCodeCustomizeDesignMoreRecentsHidePhase.txt`

### The most significant gap is the **undefined bridge between Pattern Memory and Future Output**.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `...buildfiles_x_cis_reinforcement_model_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### This is a major gap in the quality control feedback loop.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`

### The backlink syntax for knowledge record MD files was designed but not implemented in `cis_normalize.py`.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Pie Menu System**: Blocked by UI system and hotkey hold detection
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.21 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### Purpose**: Prevent placeholder text from passing as complete
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.43 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`

### Post-Commit Work Validation** — no validation that post-commit work is captured
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Preserving contradictions silently — must flag or log to conflict register
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.22 — treat as NEW
  - `...ChatGTP_Project_Primer/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Purpose**: Represents missing or unclear structure in interpretation
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.37 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### Recovery behavior details**: Interrupted jobs, stale jobs, crash recovery — behavior defined at high level but not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.29 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Remote GUI access (Parsec/Moonlight) is deferred until after pipeline validation.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...ative Intelligence System (CIS)/cis_system_bundle/MEMORY.md`
  - `...ystem (CIS)/cis_system_bundle/Handoff_Summary_03_31_2026.md`

### Runtime Impact**: File enumeration uses glob pattern `*.md`; non-markdown files are silently skipped
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...ion/functional_intents/ingest_spines_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Runtime Impact**: Every artifact creation must include builder_model_id; missing values default to empty string
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.41 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`

### Runtime Impact**: Prevents runtime crashes from missing editor-only plugins.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `.../functional_intents/mnt_projects_cis_extraction_analysis.md`
  - `...action/functional_intents/myproject3_extraction_analysis.md`

### Runtime Impact**: Runtime rendering can fail silently (black screen) without error surface visible to operator.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.21 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`

### Snapping System**: Blocked by geometry query system and transformation system
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.25 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### States:** Generated (complete), Incomplete (missing fields), Consumed (used by model)
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`

### are you referring to the task list as the deferred list?
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Primary Discovery: The Human-As-Transport-Layer Gap is the Primary Architectural Problem
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.21 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

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

### Title handling | Project Initiation | Generate working title if missing
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.21 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Unresolved Application Surface: Workbench First Screen
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...onal_intents/x_cis_critical_addition_extraction_analysis.md`

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

### Zero unresolved FAILs required before constitutional closure** — Verification gate.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/13_RUNTIME_TOPOLOGY.md`

### FAIL**: Missing required argument, invalid severity, filesystem error
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### `Mark DEFERRED in appropriate primer file` - Alternative to conflict register
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...pts/ChatGTP_Project_Primer/archive/PROJECT_PRIMER_UPDATE.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Step 2 — Classification (cis_classify.py exists, planning type missing) The classifier reads each file and tags it: SESSION_INSIGHT_RECORD, CONTRACT, ADR, SPINE_DOC, etc.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.43 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### no retirement trigger was defined and no model flagged the gap — is the
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `FOUNDATION_HARDENING_PHASE.md`

### Captures institutional memory from raw chat transcripts: goals, failures, direction changes, decisions, unresolved tensions, assumptions, and scope changes.
- support: 2 statements across 2 document(s)
- nearest queue item 14 is only sim 0.25 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Session start protocol enforcement | Protocol defined but not enforced programmatically | LOW — human-readable protocol
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Gap:** No automated cleanup of old handoffs in project folder
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ntation_backups_20260430/11_TRANSITIONAL_IMPLEMENTATIONS.md`

### Memory is project-scoped.** Cross-project memory sharing does not exist.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Supersession Chain**: No validation for circular supersession
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Produced by assembling the `cis-start` output plus any session-specific context (open questions, gap list, next task spec).
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.37 — treat as NEW
  - `...ts/2026-04-18_CIS session data synchronization checklist.md`
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### Your conclusion in the handoff is correct—but incomplete.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...orm Chat/vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Result: FAIL — 1 check failed Blocking: YES — do not advance until resolved ```
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md:33`

### Before this file, context loss across chat sessions was an unresolved problem.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...a1b97644fdc7:Execution queue ownership layer deployment`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Constraint**: Unresolved actions may block or inform new sessions
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Context Trust:** Models trusted to use provided context correctly; no validation of model understanding
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`

### System State**: Working/partial/not implemented → next session priorities
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Deferred Work → Next Actions → Session Focus → Execution | Work continuity | Working
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Documentation vs memory conflict resolution**: Layer to resolve conflicts between sources is missing
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Handoff File Validation**: No validation that handoff file is correctly formatted
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Handoff Package Object**: Contents defined but bundling format and delivery mechanism unresolved
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.19 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Impact:** Six decisions from this session unrecorded; ADRs.md incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Missing Governance: Rejection Paths.** There are no defined rejection paths for the session close sequence.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...primer_update_governance_contract_v1_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Missing Governance: Terminal State Definition**: The "correct terminal state for this session" is not defined.
- support: 2 statements across 2 document(s)
- nearest queue item 14 is only sim 0.31 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Missing Runtime Bridge: MEMORY.md ↔ Handoff Generation
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### the information in this current chat expands the overall goals even more. Plus you have the original build plan to refer to in the project files. as a matter of fact lets close this session now so that everything in the project file will be available to the next chat
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...4bed004644e:Building cis_verify.py layer 1 verification`
  - `...rchChatsProjectsCodeCustomizeDesignMoreRecentsHidePhase.txt`

### Session Close**: Form submitted → Field 5 auto-populated → Conflict check → Log if unresolved → Close
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Session-to-Project bridge**: Not yet built — sessions cannot inherit project context
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.41 — treat as NEW
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`

### The `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` flag must be permanently added to the gpu-test activation script.** It has been an unresolved note across every session.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### The watchdog alerts Eric. It does NOT trigger STATE_WRITE, closeout, or any state mutation.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.34 — treat as NEW
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md:101`

### ## Runtime Visibility Needs - **FAIL Count Visibility**: Current session FAIL count must be visible. Currently broken (reads full log). - **Primer Update Status**: Apply complete/backup created must be visible. - **Live Session Status**: Open/resolved status must be visible. - **Verification Status*
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...s/cis_handoff_2026_05_04_0214_extraction_analysis.md#r5`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`

### /mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1/ └── schemas/ ├── knowledge_record_v1.md ← existing ├── knowledge_spine_v1.md ← this document └── source_manifest_v1.md ← existing If the schemas/ folder does not exist yet it gets created now.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### Live session panel**: Not built — form was missing (fixed in this session)
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0139_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_008_extraction_analysis.md`

### Agent Stream**: Blocked by missing archive-derived knowledge patterns
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.48 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`

### Application, retrieval, and agent layers are no longer blocked by the total absence of a pipeline, but remain blocked by missing review and validation completion.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.49 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_015_extraction_analysis.md`

### resolve --action <action_id> --status <resolved|deferred|escalated>
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Inheritance Index Layer**: Blocked by population trigger.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.30 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Indexing remains future work but is now unblocked by the existence of canonical records.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.52 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_015_extraction_analysis.md`

### Intelligence → Knowledge Bridge**: Not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `...e_system_legacybuildfiles_x_03_state_extraction_analysis.md`
  - `...ntents/hand_offs_cis_handoff_phase_d_extraction_analysis.md`

### Merge Layer**: Not yet built — will combine vision extraction output with transcript text for segment-level knowledge records
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.33 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`

### Missing ChromaDB Package**: Entire vector search capability fails
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...n/functional_intents/session_extract_extraction_analysis.md`
  - `...tion/functional_intents/memory_store_extraction_analysis.md`

### Missing Chunking**: Large documents are embedded as single vectors
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...uence_and_architectural_dependencies_extraction_analysis.md`
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Missing Runtime Bridge: Image Storage to Knowledge Formation
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.27 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### No Content Index**: Full-text search not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.45 — treat as NEW
  - `...l/extraction/functional_intents/logs_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Now let me document the future features before building.Searched project for “future features deferred decisions memory”Searched project for “future features deferred decisions memory”Good — the Memory doc is the right place.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `_archive/Refactoring CIS application into modular structure.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_008.md`

### Search Interface** - Blocked by indexing, retrieval text generation
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.51 — treat as NEW
  - `...action/functional_intents/record_001_extraction_analysis.md`
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`

### Build Impact**: ADR-030 logged; workbook added to project files; formal ingestion as knowledge_record deferred to first archive run
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.33 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Creative work produced → Feedback collected → Knowledge updated → Future work improved
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `...818091549056_x_10_application_stream_extraction_analysis.md`
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Dependency Impact**: The missing capabilities (index, backlinks, session end hook) are prerequisites for the knowledge layer to function at scale
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.33 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Fail**: material unanalyzable → structure incomplete → user rejected → knowledge discarded
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`

### Knowledge record storage** — naming convention defined but storage hierarchy incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Gap Index:** Identified gaps should be indexed for pattern detection
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Gap: No Knowledge Record Created for This Infrastructure Change
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### The dominant architectural delta is the appearance of the Knowledge Spine as the missing bridge between:
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.29 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Unresolved Application Surfaces: The "Generate Knowledge" Action**: The document says a user can "generate knowledge" but does not define what this action does.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Knowledge Tier Validation**: No validation for tier classification
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...818091549056_x_10_application_stream_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### Loop:** Record created → reviewed → approved → becomes trusted knowledge → trusted knowledge used for future work → new records created
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Metadata indexing | Not implemented | **MISSING**
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### Missing Infrastructure**: The file reveals massive gaps in validation, governance, workflow, indexing, retrieval, and application layers that must be filled
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Missing Review State Machine**: Blocks production use of knowledge (cannot determine trust level)
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...tional_intents/x_07_knowledge_stream_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### Missing project context**: Agents cannot operate without project_id, stage, knowledge.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.46 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `...functional_intents/x_09_agent_stream_extraction_analysis.md`

### Phase 1 (Intelligence Extraction)**: Blocked by Phase 0 exit criteria — 10-20 draft knowledge records from real archive material
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### Not yet defined — deferred until retrieval system is built
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.37 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...s_cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Unresolved Storage Rules:** The storage rules for spine node MD files in the Obsidian vault are not yet defined (naming convention, folder structure, etc.).
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.57 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Forbidden strings as a governance mechanism.** Previously, placeholder detection was manual.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.42 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`

### Agent output panel**: Summaries, steps, references, directions, next steps, reminders, missing pieces.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.55 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...functional_intents/x_09_agent_stream_extraction_analysis.md`

### Runtime Impact**: Retrieval may return incomplete results until ingestion is complete
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### Runtime Impact:** Index remains incomplete until all governance surfaces are mature.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### STALLED** — Blocked by constraints (knowledge, technical, hardware, time, energy)
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.23 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

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

### 9.13 Unresolved Continuity Gap: Changes Need Automatic Capture
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_008_extraction_analysis.md`

### Architectural Significance**: Session start is a thin wrapper around running cis_harness.py — no state management, no validation, no orchestration
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.50 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...xtraction/functional_intents/session_extraction_analysis.md`

### Drift Detection, Phase-Aware Status, and Inheritance Integrity are Unified**: These three capabilities are expressions of the same missing layer (State Registry), not separate concerns.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...traction/functional_intents/cis_live_extraction_analysis.md`
  - `CIS_Creative_Intelligence_System_v1/CIS_LIVE.md`

### Staged draft intake addresses human-as-API gap**: Four-zone trust model (Downloads → inbox → staging → canonical) eliminates human as transport layer between AI output and canonical records.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`

### Architectural Significance**: Identifies that human copy-paste is not a UX problem but an architectural gap in intake ownership
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.29 — treat as NEW
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### This represents a **three-layer expansion** of the architecture: 1. **Input Layer**: Audio capture/upload added 2. **Processing Layer**: AI extraction and staging added 3. **Governance Layer**: Human review gate added 4. **Reporting Layer**: Timeline aggregation added
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...tant_master_prompt_version_41_extraction_analysis.md#r3`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### [asked] go ahead and run the pipeline with something [assistant] Major progress. Verification **ran for the first time in this database** — 4,110 characters of output in round 6. And the escalation now says `ESCALATED raised in verification()` with the phase recorded, where last night it said only "
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...-projects-cis/9ac1eaed-46f2-4c14-b131-84eb2b7c7a84/59.1`
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`

### Before:** Assumed orchestration existed implicitly or was not a critical gap.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...tents/1776042143355379182_x_03_state_extraction_analysis.md`

### Critical missing layers**: Session management, authorization, audit logging, search, notifications, caching, rate limiting, and workflow engine.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.40 — treat as NEW
  - `...on/functional_intents/cis_test_queue_extraction_analysis.md`
  - `...xtraction/functional_intents/app_api_extraction_analysis.md`

### Ingestion Pipeline** - Blocked by schema, status machine, model registry
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...action/functional_intents/record_001_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Gap**: No defined orchestration for the extraction workflow (who triggers, who validates, who publishes)
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Gap**: No session persistence or re-authentication mechanism
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

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

### Missing Runtime Bridge:** There is no runtime bridge between the spine ingestion pipeline and the segmentation pipeline.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Missing**: No mechanism to reduce approval burden over time as trust increases
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Phase 4 (Enhancement)**: Automated governance, feedback loops — BLOCKED by Phase 3
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.37 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### It is not about making the UI better; it is about building a missing middleware layer (ADR-048).
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.18 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Low effort feature deferred to next Live panel iteration.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### The SCP write function was written and documented but not wired into the dashboard app at session end.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### The session then spent significant time resolving Live session hygiene (eight open unresolved sessions dating back to the beginning of the build), locating Qwen model weights that were not at the expected path, discovering that the Resolve button in the Live panel had never actually been implemented
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### No validation contracts** — functions assume valid inputs
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...l/extraction/functional_intents/live_extraction_analysis.md`
  - `...xtraction/functional_intents/helpers_extraction_analysis.md`

### Dashboard review page**: Blocked by terminal script being transitional
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`

### Reality Check Panel | Unclear areas, conflicting signals, missing structure | Validation results
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### They didn't land. The commands returned no error but nothing was written. The API is likely returning a success-looking response but silently failing. Check what the endpoint actually returns on a post:
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.30 — treat as NEW
  - `...04-21_App showing black screen after code change.md:225`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### You implement it **before** the application layer by treating it as a **headless runtime contract**, not a UI.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...gacyBuildFiles/X_CIS_ WORKFLOW_EXECUTION SPEC v1.md:208`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Application Layer**: Blocked by dashboard modularization decision, draft management interface design
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.33 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Dashboard HTML refactor | Deferred to dedicated session | Not scheduled
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0547_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Draft Routes**: Human → API endpoint routing not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`

### The public endpoint exists but the application logic is not wired in.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.21 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

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

### No promotion audit trail (review/promotion UI missing)
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Phases 2–5 — Not started. Correctly deferred. What the WIAS workbook tells us about refinements needed
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.44 — treat as NEW
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:547`
  - `SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`

### **Current state:** URL is returned by the push endpoint but not displayed in UI. **Deferred because:** UI not yet built. Low effort — add in next Live panel iteration.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:16`
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`

### Record Promotion Buttons**: Blocked by missing dashboard endpoint for record status updates.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Structure Proposal Panel** - Shows detected, uncertain, and missing structure
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...gacybuildfiles_x_cis_discovery_model_extraction_analysis.md`
  - `...tional_intents/x_cis_discovery_model_extraction_analysis.md`

### This means ADR-032 needs to define the full domain taxonomy including Home/Body/Mind, and note that creative production domains are built first with life management domains deferred to a later phase.
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.27 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Architectural Significance**: The system has a gap between a handoff (session-scoped) and an ADR (locked decision).
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `_archive/orientation_backups_20260430/09_GOVERNANCE_STATE.md`

### Discovery 8 — Contract-First Discipline Was Incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.44 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Here is what is missing from the contract that would prevent this from happening again:
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...-24_CIS phase 1 intelligence extraction handoff.md:1595`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### The entire ADR-045 migration is incomplete without a worker implementation.
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.26 — treat as NEW
  - `...hive/orientation_backups_20260430/10_OPERATIONAL_REALITY.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Register Slot 1 and Slot 2 in models table (ADR-024/025) — Slot 3 registration deferred
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-27_2152.md`
  - `CIS_Creative_Intelligence_System_v1/Phase_PD/ADRs.md`

### 2 | Missing contract specs or explicit deferral reasons | Governance completeness
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Governance, monitoring, and fallback mechanisms are future work
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### `add_fields(proposal, fields)` — User adds missing fields
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...2471347_x_cis_discovery_workbench_v1_extraction_analysis.md`
  - `...ldfiles_x_cis_discovery_workbench_v1_extraction_analysis.md`

### All formal build-plan tiers are either COMPLETE or explicitly DEFERRED — there is no eligible PENDING node in the Dependency Graph Build Plan v2.0.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.43 — treat as NEW
  - `...orcement_architecture/CLAUDE_SESSION_VERBATIM_2026-06-19.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### ```text Governance → Authority Boundaries → Internal Writer / External Reader Split → Documentation as Continuity Authority ```
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_009_extraction_analysis.md:347`
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

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

### Review queue interface | ADR-049 review workflow | Not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### runtime/manifests/**: Unknown ownership, may be deprecated — creates governance gap
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.29 — treat as NEW
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### I can then tell you definitively whether the schemas match the DB, whether they reflect the ADR decisions, and what — if anything — is missing or inconsistent.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### The "table does not exist" message didn't print — that means the command succeeded but returned nothing, which means the table doesn't exist and the `||` fallback also silently succeeded.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...tion/functional_intents/all_insights_extraction_analysis.md`
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Missing column detection**: ALTER TABLE adds missing columns on re-run
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.19 — treat as NEW
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### Fail**: Qwen weights not found, ensure_models_table not wired, Live sessions unresolved
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.47 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### Manifest stabilization | files_written | Schema lock (ADR-047) | Not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.27 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Gap**: `project_id` is a field, not a storage partition
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Missing:** Database (SQLite, Postgres, or equivalent)
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### On a fresh DB, migration_log does not exist yet — must be created before
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_migrate_041.py`

### `ADR database audit → schema audit → runtime artifact audit → contract register → missing contracts → implementation verification`
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### 15 SESSION_INSIGHT_RECORD ingestion** blocked by ADR-045 and ADR-048 operational
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`

### Fix 1 (ChatGPT v8): ALTER existing table to add builder_model_id if missing.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_migrate_041.py`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### Gap**: No formal ontology document — spine is implicit in ADRs and handoff docs
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Runtime Impact**: Decision-to-DB gap is entirely human-dependent.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### This document records a structural gap identified in the CIS spine/control-plane model.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.42 — treat as NEW
  - `CIS_FUTURE_BUILD_PLAN_SPINE_REQUIREMENT.md`
  - `DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md`

### The architecture reveals significant gaps** - undefined schemas, missing bridges, unresolved routing, unstable governance
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `...tional_intents/x_cis_execution_layer_extraction_analysis.md`

### Missing or invalid `DB_PATH` configuration will cause health check failure
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/health_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### Missing Validation Layers:** There is no validation logic for ensuring that `anchor_node_id` references an existing, approved `spine_node`.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.52 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...action/functional_intents/spines_api_extraction_analysis.md`

### Missing Validation Layer: Uncertainty Marker Schema**: The document requires "uncertainty markers" but does not define their schema (e.g., a float from 0.0 to 1.0, a categorical value like "low/medium/high").
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `.../cis_creative_intelligence_system_v1_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`

### ADR form**: affected_files and verification_required fields identified but not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.25 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `...hive_11_transitional_implementations_extraction_analysis.md`

### Storage Implications**: Logged to database; unresolved sessions block next build
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`

### The earlier "every gate silently queries a dead DB" finding was wrong — the code resolves to cis_memory.db everywhere.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...orcement_architecture/CLAUDE_SESSION_VERBATIM_2026-06-19.md`
  - `DOCKER_CONTAINMENT_PROPOSAL.md`

### Dependency Impact**: Port pre-check gap is a known issue but not yet fixed.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0836_extraction_analysis.md`
  - `_archive/orientation_backups_20260430/07_KNOWN_RISKS.md`

### Karpathy's linting/health checks = not built (missing).
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Content Validation**: Original work verification not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`
  - `...857838508_x_11_sound_stream_expanded_extraction_analysis.md`

### Missing**: No mechanism to update project status based on verification
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Pre-Write Zone Check**: No validation layer for zone classification before file writes
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`

### Runtime Impact**: Every manifest write must include model provenance; missing field causes verification failure
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `...nts/adr_041_artifact_registry_schema_extraction_analysis.md`

### This is explicitly classified as an architectural gap, not a UX problem.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### The session went deep on architectural work — scope expansion, domain taxonomy, knowledge_spine design — and the operational task of installing and testing the library was deferred.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Deferred because:** Remote access architecture needs security review before exposing
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...reative_Intelligence_System_v1/memory_additions_20260420.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### This is not a future feature. It is the most important missing piece in the current build.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...4-24_CIS phase 1 intelligence extraction handoff.md:366`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### process and architecture are still likely the deeper issue, but the model evaluation remains incomplete because the system has not yet been instrumented **during** inference.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...orm Chat/vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md`
  - `...vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md:1801`

### Architectural Significance**: No defined lifecycle for rejected/superseded drafts creates unbounded storage growth and governance gap
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`

### Architectural Significance**: The commit layer that would promote staging → canonical is explicitly NOT YET BUILT, creating a known architectural gap
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Missing Infrastructure Ontology**: The CIS ontology does not include infrastructure objects (mount points, device mappings, fstab entries, recovery procedures).
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Build Priority Shift**: The discovery of stub implementations and missing validation means build priorities must shift from feature development to foundational infrastructure (session storage, model integration, validation engine, approval system).
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Gap**: Handoff package includes STATE.md, SYSTEM_BLUEPRINT.md, ARCHITECTURE_MAP.md, Core Tool Stream, but no format or structure defined.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### Project container**: Defined in architecture but not implemented.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.37 — treat as NEW
  - `...uence_and_architectural_dependencies_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### Purpose**: Bridge the gap between persistent project storage and ephemeral session context
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.37 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### The build order must prioritize Intelligence services before Knowledge base population, and both Agent and Application layers are deferred until foundational layers are stable.**
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.44 — treat as NEW
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`
  - `...tional_intents/x_01_system_blueprint_extraction_analysis.md`

### This is one of the most consequential scope decisions in the entire build history and it happened as a mid-session realization, not a planned architectural review.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...4-24_CIS phase 1 intelligence extraction handoff.md:601`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### [Full drafting instruction for TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md — architecture, trust root, spec must include 11 sections, out of scope, deliverable path]
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...orcement_architecture/CLAUDE_SESSION_VERBATIM_2026-06-19.md`
  - `DEV-PIVOT-15_SESSION_OPEN_ITEMS.md:7`

### Draft Pipeline**: (MISSING) No promotion logic defined for inbox → staging → database
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.34 — treat as NEW
  - `...extraction/functional_intents/config_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Not defined in this session** — deferred to Phase 0 contracts
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`

### Extraction output (that lives in knowledge_records, linked via extraction_run_id) Frame-level data (deferred — not needed for Phase 1)
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.33 — treat as NEW
  - `CIS_CURRENT_STATE.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### Build Impact:** Phase 0 video work is entirely deferred.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Phase 2** (Downloads Watcher) blocked by Phase 1 completion
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### The Sound Stream file was retrieved in that search, which means it was indexed and available — I just did not draw from it heavily in the roadmap because Sound is a deferred domain that does not affect build order for the infrastructure phases.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.32 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### **With Component 3.5:** Component 5 becomes a two-phase operation:
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md:122`

### Phase 3 Dashboard Panel**: Blocked by Phase 1 API endpoint
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### That's the transcript import work from the Foundation Plan (currently classified as deferred-unscheduled) plus Chroma/VDB at Tier 9.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.38 — treat as NEW
  - `PLAN_RECONCILIATION.md`
  - `Routining the quick advisor.txt`

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

### [user] but now instructions are coming and you did the work before. As we build the application, willl we be actually putting guardrails in place to prevent you from executing instructions? [assistant] Direct answer: not yet, but that gap is real and the plan already provides the mechanism to close 
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`
  - `hermes_session/v4impl/session_20260606_202223_9ccd36/4.0`

### Handoff File**: Schema is defined but not enforced by runtime.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...2471347_x_cis_discovery_workbench_v1_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`

### The following behaviors are prohibited and constitute governance violations:
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.22 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `ADRs/ADR-048_Staged_Draft_Intake_Layer.md:49`

### No implementation without Eric approval (Eric Gate).
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.44 — treat as NEW
  - `CIS_EXTERNAL_ADVISOR_BRIEFING_2026-06-25.md`
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Spine Ingestion Validation**: Not implemented — pipeline is designed but not built
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`

### Status Values**: Documented but not enforced by SQLite CHECK constraint
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/migrate_execution_jobs.py`

### as a gap; this creates enforcement through visibility before any technical check.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_1_DESIGN.md`
  - `claude crystallizes the vision.txt`

### are complete — short records reflect short sessions, not incomplete extraction
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-26_0722.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### The question that determines the work order is: **does the Live tab currently show anything functional, or is it a placeholder?** That screenshot will answer it and we go from there.
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.27 — treat as NEW
  - `...04-20_Refactoring CIS application into modular structure.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_008.md`

### GAP**: No promotion path from "registered" to "extracted" or "analyzed"
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...raction/functional_intents/librarian_extraction_analysis.md`

### Extraction State**: Multi-pass pipeline not yet built; individual scripts not yet created
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.28 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### No validation that extraction run logging covers dashboard and manual extract paths equally.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Not implemented**: No chunking metadata in extraction_runs
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...ents/cis_dashboard_monolith_20260420_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

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

### Missing:** Explicit interface between archived projects and pattern extraction
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.34 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`

### Review workbench**: Blocked by pipeline completion; needs extracted/normalized sources to test
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._Master_Handoff_files/CIS_Handoff_Review_Command_Session.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### Runtime Impact**: Classification happens at ingestion time; unrecognized files are silently skipped (potential data loss risk)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ctional_intents/cis_download_watcher_extraction_analysis.md`

### - **Runtime Impact**: Failure to install dependencies results in `ImportError` at runtime, blocking application execution entirely.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...direct_access_to_google_ai_39_extraction_analysis.md#r2`
  - `...ion/functional_intents/collab_rounds_extraction_analysis.md`

### Runtime Impact:** Any runtime behavior that depends on memory recall will fail if memory extraction is incomplete or delayed.
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.25 — treat as NEW
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Empty Round 4 from "Rounds in Right Sidebar" will be silently dropped from the markdown output
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.25 — treat as NEW
  - `...04-20_Refactoring CIS application into modular structure.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Escalation rules: schema failure, missing required sections, hallucination patterns detected, low-confidence signals, output too short or incomplete.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Missing archive audit**: System cannot be grounded in reality
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...acybuildfiles_x_cis_relationship_map_extraction_analysis.md`

### Missing `system_log.md`**: The system log file did not exist and was not being written to by pipeline commands.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`

### Retry → Escalation bridge**: Logic described but not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...s/cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Escalation**: If corrections cannot be applied (field missing), log error and skip
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`

### Operator opens session, attempts to log round, selects wrong or missing session.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`
  - `CIS_CONFLICT_REGISTER.md`

### Modifier Stack**: Blocked by mesh data system and execution pipeline
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### Retry**: (not implemented) Re-run pipeline with modifications
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `...unctional_intents/cis_convert_export_extraction_analysis.md`

### Missing `/mnt/archive`, `/mnt/models`, and `/mnt/cache` mounts.
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.28 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`

### Unresolved Storage Rules: Handoff Document Retention.** How long is the handoff document retained?
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.54 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Processing profiles are provisional until archive heterogeneity reveals missing cases.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `...onical_build_sequence_plain_language_extraction_analysis.md`

### Missing FINAL_JSON | Repair prompt, then fallback text scanning | Model produces analysis but no machine-parseable verdict
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `CIS_16_FAILURE_MODES.md`
  - `DEV-PIVOT-05_HERMES_INTEGRATION_ASSESSMENT.md`

### Runtime Impact**: Agents have no meaningful function if upstream layers fail or are incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.52 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`

### No validation for agent outputs** — No hallucination checks on agent responses
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.40 — treat as NEW
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`
  - `...nts/cis_plain_language_build_roadmap_extraction_analysis.md`

### Agent tab**: Depends on agent discovery service — not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.48 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### Missing Governance Gap**: The minutes agent operates with zero governance - no validation, no provenance, no audit trail.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.43 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`

### Review Panel**: Approve, reject, edit, mark uncertainty, merge categories, add missing fields
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.25 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Cause**: Incomplete extraction, missing provenance, accuracy issues
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.41 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Missing Provenance**: Worker 4 flags outputs without traceability
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### echo "Deferred: Authentication design not yet started." >> /mnt/projects/cis/docs/X_02_MEMORY.md
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `...reative_Intelligence_System_v1/memory_additions_20260420.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Missing Governance Layer**: The status endpoint exposes system internals (record count, project count, task count) without authentication, authorization, or rate limiting.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...extraction/functional_intents/system_extraction_analysis.md`
  - `...on/functional_intents/import_session_extraction_analysis.md`

### Permission Enforcement**: Declared but not implemented - security depends on application layer
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.26 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...extraction/functional_intents/cis_db_extraction_analysis.md`

### API key must be validated before any extraction** - System exits if key is missing
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...ction/functional_intents/hermes_chat_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### Any process producing or consuming knowledge records is blocked by schema drift until the canonical schema is corrected.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### No hallucination controls documented**: L3 CIS Live Copy Prompt is operational but no validation of its output.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...tion/functional_intents/memory_store_extraction_analysis.md`

### Failure: Missing fields → fail, hallucination → fail, narrative drift → fail
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...s/cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Gap**: No explicit hallucination controls for verification subsystem
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Missing:** Formal definition of "drift" as a system object
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...itutional_memory_governance_revision_extraction_analysis.md`

### looks for drift, missing dependencies, unsupported claims, false completion Optional fourth: Implementer
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.41 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### This is a critical missing dependency that must be fixed before any fresh deployment.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`
  - `PROPOSAL_SESSION_TO_SPINE_WRITE_PATH.md:105`

### This is the right question to ask before building anything. Let me think through it honestly given your constraints.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.28 — treat as NEW
  - `...-04-25_Verification mechanism for completed work.md:126`
  - `...al build sequence and architectural dependencies.md:188`

### ``` This block is not supported on your current device yet. ``` Understood. Before the build plan rewrite, you have things to address first. Go ahead — what are they?
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...0-4406-b978-6e0379ba80ea:Build plan rewrite preparation`
  - `...an AI platform for professional project guidance.md:147`

### known_functions = { # SymPy -> Maple 'Abs': 'abs', 'log': 'ln', 'asin': 'arcsin', 'acos': 'arccos', 'atan': 'arctan', 'asec': 'arcsec', 'acsc': 'arccsc', 'acot': 'arccot', 'asinh': 'arcsinh', 'acosh': 'arccosh', 'atanh': 'arctanh', 'asech': 'arcsech', 'acsch': 'arccsch', 'acoth': 'arccoth', 'ceiling
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `swa_project/social_work_ai/01_CORE/sympy_parser.py#r3`
  - `swa_project/social_work_ai/03_CLINICAL/maple.py#r1`

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

### These paths are always blocked from `@file:` references to prevent credential exposure:
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.33 — treat as NEW
  - `Hermes Agent Full Documentation.md:15707`
  - `Hermes Agent Full Documentation.md:2913`

### 'WONT_FIX' -- Explicitly decided not to address. Requires Eric approval -- and resolution_note. )),
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.51 — treat as NEW
  - `CIS_CONFLICT_REGISTER.md:28`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_1_DESIGN.md:72`

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

### These will take a few minutes. Paste any errors that come up — success output can be skipped, just confirm when both are done. Apr 22 Claude responded: Both installed cleanly.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `...pts/2026-04-22_Model registry API implementation.md:899`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:699`

### Real workers fail. Missing credentials, OOM kills, transient network errors. The dispatcher has two lines of defense: a **circuit breaker** that auto-blocks after N consecutive failures so the board doesn't thrash forever, and **crash detection** that reclaims a task whose worker PID went away befor
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.26 — treat as NEW
  - `Hermes Agent Full Documentation.md:3749`
  - `Hermes Agent Full Documentation.md:3761`

### 8. **Verification must be visible and granular.** The user cannot rely on implied success. The system must provide readable, complete validation outputs.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:559`
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:2057`

### * input * process * output * validation * failure rules * state change
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:1504`
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:3016`

### if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor( std_logging.DEBUG ): # pragma: NO COVER _LOGGER.debug( "Created client `google.ai.generativelanguage_v1beta3.DiscussServiceAsyncClient`.", extra={ "serviceName": "google.ai.generativelanguage.v1beta3.DiscussService", "universeDomain": getattr( se
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...project/social_work_ai/01_CORE/moved_async_client.py#r5`
  - `swa_project/social_work_ai/01_CORE/async_client.py#r5`

### except Exception as exc: logs: list[str] | None = textwrap.dedent(stream.getvalue()).splitlines() if not capture_logs: # If logs aren't being captured, then display the error inline # with the rest of the logs. logs = None if isinstance(exc, PipError): logger.error("%s", exc) else: logger.exception(
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `swa_project/social_work_ai/01_CORE/build_env.py#r1`
  - `swa_project/social_work_ai/01_CORE/moved_main.md#r1`

### We needed to **prove the machine can run *any* model correctly first**
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md:2788`
  - `...vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md:2815`

### **Why:** Building around an unavailable capability would add complexity with no return. The manual workflow is fast when the UI is designed for it.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:38`
  - `cis_v1_vault/memory_additions_20260420.md`

### Hermes' description of what happened is not verification. Show the terminal output. ``` This is the verification-hardening rule. Self-report is not evidence.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.39 — treat as NEW
  - `...d39-46f3e3b7d17b:Hermes missing project context file#r1`
  - `chatgpt_export/6a24c7a7-25d4-83ea-a892-abdb8fd1a26f#r3`

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

### [asked] I don't quite follow what claude is talking about here. can you help me understand and follow up on this issue. The bypass is gone. §3.2 now rejects with 409 instead of auto-creating, and the rationale is stated correct... The reason this defect got as far as it did is that it satisfied the 
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.41 — treat as NEW
  - `...bcd-4be2-a60a-dd490fccbe35:Awaiting ChatGPT proposal#r2`
  - `...session/glm-reviewer/session_20260614_172934_5046b0/9.3`

### **The override plane.** At every layer, a single out-of-band escape: the override file, checked first, flippable only from a bare shell. This is not one gate's feature — it's a property of the whole stack. Any gate, any layer, you can disable from outside. This is the anti-deadlock guarantee, archit
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.42 — treat as NEW
  - `...5b-5c39-4e77-8476-521153c1e51a:Project files update#r12`
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md:56`

### Eric Gate is the human authority boundary. No consensus path may skip Eric review. This is not a configurable default, not an env var, and not a gate parameter that a future tier could toggle off. Any future architectural change that would allow a consensus path to bypass Eric Gate requires an expli
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.43 — treat as NEW
  - `...s_execution_layer_contract_v1_extraction_analysis.md#r1`
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md:63`

### The reason it feels like a contradiction — "how are gates engaged if not through the UI" — is that today, **neither exists as enforcement.** The "gate" is a sentence in a protocol doc. You engage it by reading transcripts and saying "stop." That's why it feels like the UI must be the gate: because t
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.45 — treat as NEW
  - `...4c-b875-d7847eeea24b:Project file review and kickoff#r0`
  - `...4c-b875-d7847eeea24b:Project file review and kickoff#r3`

### 7. Move stripped governance content into a `docs/archive/governance_ceremony_2026-06-18.md` reference document (not loaded by any gateway). This preserves the design intent without burdening active sessions.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.38 — treat as NEW
  - `DEV-PIVOT-01_GOVERNANCE_RESET_PROPOSAL.md:82`
  - `DEV-PIVOT-04_APPLICATION_ENFORCEMENT_SPEC.md:68`

### SCP is a critical path dependency** — Without SSH key configured, the push operation fails silently.
- support: 8 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### PASS WITH WARNINGS:** All required files present, phase-required streams present, optional streams missing or excluded files present
- support: 7 statements across 1 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### implementation_artifacts | No | **Deferred-unscheduled** — no v2.0 tier
- support: 7 statements across 1 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `PLAN_RECONCILIATION.md`

### Required file validation:** Fail if STATE.md, SYSTEM_BLUEPRINT.md, or MASTER_ARCHITECTURE_MAP.md missing
- support: 6 statements across 1 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Missing Runtime Bridge: Review Capacity Management
- support: 5 statements across 1 document(s)
- nearest queue item 16 is only sim 0.43 — treat as NEW
  - `...unctional_intents/adversarial_review_extraction_analysis.md`

### Not implemented**: Queue.py does not contain knowledge formation logic
- support: 5 statements across 1 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### The most critical architectural gap is the missing governance layer** for AI self-description, capability claims, and memory limitation disclosure.
- support: 5 statements across 1 document(s)
- nearest queue item 21 is only sim 0.44 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Dependency Impact**: The dashboard depends on filesystem access via JavaScript, which is blocked by browser security policies (CORS/local file restrictions).
- support: 5 statements across 1 document(s)
- nearest queue item 22 is only sim 0.30 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### UI Redesign Before Frontend Modularization:** The frontend modularization is also deferred until the UI redesign (mockup integration) is complete.
- support: 5 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### 9.9 Missing Application Surface: Knowledge Deck Filters
- support: 4 statements across 1 document(s)
- nearest queue item 1 is only sim 0.33 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_008_extraction_analysis.md`

### Material Validation**: Check for missing textures, invalid shaders
- support: 4 statements across 1 document(s)
- nearest queue item 3 is only sim 0.20 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Domain configuration loading | Configuration validated and activated | Configuration invalid or missing dependencies | Retry with corrected configuration
- support: 4 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Gap:** There is no defined orchestration between memory and documentation.
- support: 4 statements across 1 document(s)
- nearest queue item 3 is only sim 0.33 — treat as NEW
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### L2 validation: PASS for execution contract (deferred), UNCERTAIN for governance contract (acceptable)
- support: 4 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Pipeline keys are not wired** — Stream Deck pipeline and knowledge keys are placeholders only.
- support: 4 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Idempotent migrations are possible**: The script can be re-run safely, adding missing columns without data loss
- support: 4 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`

### Every reaction must be**: correct, refine, accept, reject, or add missing structure
- support: 4 statements across 1 document(s)
- nearest queue item 11 is only sim 0.32 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`

### Verification Complexity as Architecture Revealer**: The verification pipeline's complexity was not just a technical problem — it was an architectural signal revealing missing abstraction boundaries.
- support: 4 statements across 1 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

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

### ADR-044 (Operator Abstraction) not started** — blocks resolution of human-as-transport-layer gap.
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Missing Benchmark Infrastructure**: Blocks visual output certification
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`

### Description**: The following queue subsystems are identified as missing but required:
- support: 3 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Question Lifecycle**: Open questions have states (OPEN, RESOLVED, IN PROGRESS, DESIGNED NOT BUILT)
- support: 3 statements across 1 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### The fix required identifying that state variables (`showResolve`, `solution`, `decidedBy`) and a `resolve()` function existed but the JSX that renders when `showResolve` is true was simply missing.
- support: 3 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### VETO, RETURN_TO_DRAFT | Deferred to full Component 3 implementation.
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `CIS_TIER_11_UI_USABILITY_SPECIFICATION.md`

### Step 4: If deferred items exist → display items → require resolution
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Discovery**: Draft → Review → Gap Identification → Resolution → Re-review
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Permission Validation Engine**: Referenced but not implemented
- support: 3 statements across 1 document(s)
- nearest queue item 17 is only sim 0.25 — treat as NEW
  - `...ntents/1775995115163043436_x_control_extraction_analysis.md`

### Gap**: No full-text search, no category tags, no date range filtering
- support: 3 statements across 1 document(s)
- nearest queue item 1 is only sim 0.45 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap:** No defined quality standards for sound assets
- support: 3 statements across 1 document(s)
- nearest queue item 18 is only sim 0.34 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Missing SSH Key:** If the SSH key is not set up, the push-to-live-site feature will fail.
- support: 3 statements across 1 document(s)
- nearest queue item 5 is only sim 0.23 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Missing ViewLayer configuration**: Blocks render pass execution
- support: 3 statements across 1 document(s)
- nearest queue item 1 is only sim 0.21 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Pre-Creation Config Check**: No validation layer for config.py constant before path creation
- support: 3 statements across 1 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`

### ViewLayer Validation**: Check for missing collections, invalid render passes
- support: 3 statements across 1 document(s)
- nearest queue item 7 is only sim 0.26 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Session archive learning | Completed sessions → Pattern analysis → Better handoff packages | Learning loop | Not implemented
- support: 3 statements across 1 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Gap**: Need a Claim Audit Panel in the application surface
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`

### No selector improvement loop | Broken selectors not automatically updated | **MISSING**
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Architectural Significance**: The CIS application layer (dashboard) is failing to load at runtime, revealing a critical architectural gap between the filesystem layer and the browser-based application layer.
- support: 3 statements across 1 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### No error handling exists for the dashboard**: The infinite spinner indicates a missing error state in the dashboard's state machine, providing no feedback to the user about what went wrong.
- support: 3 statements across 1 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Runtime Impact**: L2 has no explicit temperature setting - this is a potential governance gap
- support: 3 statements across 1 document(s)
- nearest queue item 22 is only sim 0.27 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### Draft schema correction | Schema validation → Error feedback → Corrected submission | Negative feedback | Not implemented
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### print(f" Running schema steps anyway to apply any missing columns.\n")
- support: 3 statements across 1 document(s)
- nearest queue item 17 is only sim 0.25 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_migrate_041.py`

### "CRITICAL: missing model name was not caught — auditor identity check broken"
- support: 3 statements across 1 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### Condition**: Verification fails due to incomplete constraints
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Description**: Incomplete context leads to hallucinated architectural decisions.
- support: 3 statements across 1 document(s)
- nearest queue item 1 is only sim 0.37 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Related Objects**: Workflow Layer, Project State, Workflow Stage, Next Steps, Reminders, Missing Pieces.
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `...functional_intents/x_09_agent_stream_extraction_analysis.md`

### Deferred-scheduled | 4 | FTS5/search (Tier 9), export_manifests (Tier 6), cards table (Tier 7+), UI Quick Capture (Tier 10)
- support: 3 statements across 1 document(s)
- nearest queue item 1 is only sim 0.44 — treat as NEW
  - `PLAN_RECONCILIATION.md`

### Task API:** Accepts `phase` field with values: deferred, backlog, active, completed
- support: 3 statements across 1 document(s)
- nearest queue item 10 is only sim 0.31 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Multi-pass extraction | Adequate extraction quality | Extraction | Not implemented
- support: 3 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Re-segmentation provenance:** `segmentation_run_id` field proposed but not implemented.
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Runtime Impact**: No validation that `source_id` corresponds to an ingested file before pipeline execution.
- support: 3 statements across 1 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...traction/functional_intents/pipeline_extraction_analysis.md`

### Gap**: No defined application interface for distillation creation
- support: 3 statements across 1 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Missing exclusion → Cancel → Reconfigure**: Impractical backup size triggers correction
- support: 3 statements across 1 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`

### Commit Route is Missing**: The most critical gap — approved drafts cannot become canonical knowledge.
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`

### Error: 400 (missing path), 404 (file not found), 500 (enqueue failure)
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.23 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### e('input', { type:'text', placeholder:'/mnt/archive/path/to/file', value:filePath,
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.22 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Missing Merge Script**: Blocks auto record population
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Missing Validation Layer**: There is no validation that the reconciliation accurately represents the parallel responses, creating a trust gap.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### File does not exist | Claude re-executes the write and produces a new manifest
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.38 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Missing Staging Directory**: Causes immediate exit with error
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `.../functional_intents/primer_update_v2_extraction_analysis.md`

### Missing parent directory → Create parent directory → Create register → Append entry
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.20 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Missing**: No validation that registered courses have actual content
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.48 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Not implemented**: No project association for captures
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Intermediate:** Operator abstraction layer (current, incomplete)
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### QR code URL display — deferred feature, low effort, should be a task
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Source File Existence**: No validation that source_path exists before processing
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...on/functional_intents/cis_preprocess_extraction_analysis.md`

### Then check what comes after line 140 to see if more content is missing:
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### Runtime and primer WILL diverge silently over time without audits.
- support: 2 statements across 1 document(s)
- nearest queue item 9 is only sim 0.22 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### Visual → Merge Bridge**: Not implemented (merge script missing)
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.21 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### 10 | Missing status reader artifact | Added tools/eric_gate/show_status.py (Section 13)
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### Constitutional Stubs as Reserved Chunks**: Structure reserved, content deferred.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Absent or not root-owned → STOP: "/opt/cis-control missing/not-root — trust root must be
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.30 — treat as NEW
  - `MINIMAL_WORKER_LAUNCH_PROOF_v2.md`

### Architectural Significance**: Vision model (Qwen2.5-VL-7B or InternVL3-8B) explicitly deferred to later delivery phases.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...sponse_to_vscode_obsidian_and_github_extraction_analysis.md`

### Alignment**: System no longer described as only foundation/setup; execution layer gap explicit
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Async Synthesis Bridge**: HHR-016 not implemented; no async job + polling mechanism
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Blocked By:** Phase E (Knowledge Foundation) not complete
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Blocking:** If intent detection is missing, AI cannot proceed past step 1 (Wait)
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.47 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Missing brush configuration**: Blocks paint/sculpt operations
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.21 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Build workbench**: Not yet built — interface for build sequence management
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`

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

### There is a gap between infrastructure readiness and application wiring.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Architectural Significance**: Executor worker is a stub that does not call any model and generates placeholder output
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`

### Description**: No validation that phase objectives are met before transition
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Branch Note Gap**: There is a missing artifact type between handoff and ADR.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.43 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`

### MCP is deferred to after this stack is operational.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...sponse_to_vscode_obsidian_and_github_extraction_analysis.md`

### Architectural Significance**: The Downloads watcher's runtime model (daemon vs Flask-started) is unresolved, creating a process architecture gap
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Exit codes: 0 = success, 1 = graph file missing, 2 = contradictions found (non-zero for CI gating)
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### If exit criteria not met: identify specific missing criteria
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### File Map Reinforcement Loop:** Missing orientation → Claude proposes map → Map created → User navigates better → Map updated
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.35 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### File map creation | Document exists with all files listed | Missing files; incorrect status
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.34 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### SOON** | Complete remaining CIS functionality (external escalation wiring) | ⬜ Deferred
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `DEV-PIVOT-06_BUILD_DIRECTION.md`

### Missing:** Explicit interface between constraint monitoring and project planning
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Gap**: Form strip removal created dependency on syntax integrity
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`

### Gap**: No defined source quality assessment before processing
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### Gap**: No validation for task priority ranges or phase values
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap**: No mechanism to detect or report slow queries
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.28 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Gap:** No validation layer for inheritance topology
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.23 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Gap:** No machine-readable format for contract constraints
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Gap:** Who detects trigger points for Architect invocation?
- support: 2 statements across 1 document(s)
- nearest queue item 11 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Remote Access → Heavy Compute Jobs**: Blocked by GPU requirement
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`

### Runtime Impact:** Handoff file written to both vault and project folder; project folder write silently skips if no project active
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Intake Retry**: If project_id missing, operator must resubmit with project_id
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`

### L1 PASS → L2 rerun:** Deferred for operator abstraction flow
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### Merge stage gap creates implicit synthesis reliance
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.22 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Missing Runtime Bridge: Hermes to Approved Tools/Scripts
- support: 2 statements across 1 document(s)
- nearest queue item 20 is only sim 0.50 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Missing node tree compilation**: Blocks shader/geometry evaluation
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Missing `command` field on a task blocks the `/run` endpoint (returns 400).
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`

### Missing**: Formal definition of quality assessment structure
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.38 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`

### Missing Contract**: Extension validation, size limits, content-type verification, malware scanning
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### Missing**: Dashboard showing minutes production status
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`

### Runtime Impact**: If Prime returns invalid domain, silently falls back to first domain in list; no error reported to user
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...ction/functional_intents/idea_drafts_extraction_analysis.md`

### Missing Columns:** `superseded_by`, `version`, `author`, `tags`, `category`, `references`
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.42 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### No concept extraction | Raw text only, no semantic processing | **MISSING**
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.42 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### No validation for confirmation of CONTROLLED actions
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `...raction/functional_intents/x_control_extraction_analysis.md`

### None implemented.** No validation of who created or completed a task.
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`

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

### Inheritance Index Population Orchestration**: Deferred until routing pain appears.
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

### Resolve Button Verification**: Root cause traced to missing JSX, not refactor loss.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Resource Arbitration**: VRAM allocation rules not implemented; concurrent model execution constraints unresolved
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Runtime Impact**: Script will silently fail or capture garbage if selectors change
- support: 2 statements across 1 document(s)
- nearest queue item 9 is only sim 0.21 — treat as NEW
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Runtime Impact**: Stale code runs silently; operator unaware of version mismatch
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

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

### Steps 6-8 deferred indicates feedback-driven prioritization
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...intents/20260502_0047_05_adr_summary_extraction_analysis.md`

### Tool Layer** is split into Anchor Tools vs Support Tools vs Deferred Tools.
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.31 — treat as NEW
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

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

### Description**: Display session status (Initializing, Ready, Incomplete, Failed) at all times
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### cis-log command is a foundational prerequisite.** Without it, no implementation session can complete its handoff.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...on/functional_intents/implementation_extraction_analysis.md`

### Segment States**: Not defined in this session (deferred to ADR-033)
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`

### The file also exposes a missing runtime requirement: CIS needs a formal **session rehydration protocol**.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_010_extraction_analysis.md`

### BLOCKED_MISSING_CAPABILITY | Required index, object, adapter, or gate does not exist | "Start Micro1 task planning" (out of scope)
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### Gap**: No defined test for context length, reliability, response format, bounded task performance
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Live session auto-select fix | Data integrity in development harness | Application | Not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Missing**: No project ID, idea ID, or context identifier attached to uploads
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### New Context Management Gap**: The advisor sends **single messages** to gateways without conversation history.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.44 — treat as NEW
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### No supersession tracking | Lineage gap — cannot track decision evolution | MEDIUM
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.28 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### The object model is incomplete** — missing author, project linkage, supersession, versioning, and audit trail
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### The AI claimed a "locking" mechanism for memory that does not exist.
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### The DAM is the starting point of a future full asset management capability.** As the knowledge base grows, the DAM becomes a searchable pool of material that agents can draw from, projects can reference, and future work can be seeded from.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Agents blocked by lack of validated knowledge and workflow context.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.43 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`

### Build Impact**: Embedding/vector DB implementation deferred; retrieval text generator heuristic acceptable
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### 2_CIS_REORIENTATION.md versioning**: Needed but deferred — reorientation may drift
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`

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

### Contract retrieval improvement | Registry → Search → Better organization → Faster location | Positive reinforcement | Not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Description**: There is no validation layer that checks if the corpus is complete before analysis.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Documentation Retrieval Fail:** Documentation missing or outdated
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.32 — treat as NEW
  - `...85_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Orchestration Layer | Phase C incomplete | Later phases
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Knowledge record validation**: No validation that vault copies match canonical.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.33 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Knowledge→Retrieval→Workflow→Execution→Feedback→Reinforcement**: Complete cycle not yet operational; reinforcement loop identified but not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Layer 2 Prompt Contract v1**: Not yet built, but defined as a requirement for cis_verify_semantic.py.
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

### Missing**: No ontology enforcement on `knowledge_category`
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Research Module**: Not built — agent-based categorization not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.45 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Dependency Impact**: Creates implicit ordering: Download → Watcher picks up → Moves to inbox → Manual or automated staging → Staging zone → (missing) API intake → DB persistence
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### The "next step" is printed to stdout but not enforced or automated.
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`

### Manifest Gap Identified**: Session manifests exist as chat downloads only, with no automated pipeline to the canonical drop location — a significant gap in the verification architecture.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`

### Gap:** How is handoff from Architect to Implementation orchestrated?
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Missing**: No sync endpoints for `transformers`, `comfyui`, `vllm`, or `api_remote` runtimes
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### 3.4 — Quick Capture panel on Advisor Chat | **Deferred-unscheduled** | Depends on notes capture (2D).
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `PLAN_RECONCILIATION.md`

### Dashboard ↔ System Log**: Displays operational history (deferred)
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### Flask dashboard | Application surface | Deferred (Phase 5)
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.27 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`

### Gap:** No route from dashboard to decisions table
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Queue Management UI**: Not yet built; dashboard expansion prohibited
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`

### Poll endpoint**: `/api/queue/job/<N>` referenced but not implemented in this file
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Architectural Significance**: The backend resolve route existed but the frontend form was never implemented — a feature gap from the monolith refactor
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`

### Router not implemented | No task classification or model tier selection | HIGH
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### Step 7 blocked by**: Step 6 completion (run_l2 verification) — NOT STARTED
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_1852_extraction_analysis.md`

### Blocked By**: Session transcript extraction, contract specification documents
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Dependency Impact**: Missing contract registry prevents clean audit trails
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`

### Core Entities:** ADR, Gap, Risk, Proposal, Component, Decision
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

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

### No retry logic**: If database write fails, it's silently skipped
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...action/functional_intents/cis_review_extraction_analysis.md`

### Should notes capture (2D) be explicitly scheduled as Tier 7.5 or Tier 8 prerequisite rather than deferred to Tier 10?
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.23 — treat as NEW
  - `PLAN_RECONCILIATION.md`

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

### Gap:** The original report called this a "dual database" split.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Incomplete question→file routing table:** AI systems cannot reliably route queries.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`

### "Audit round: roster check deferred (ADR-042 not yet implemented)",
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### lifecycle_events table | Missing | `.schema` returns no output
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `CIS_TIER_11_UI_USABILITY_SPECIFICATION.md`

### Conflict → Resolution → Verification**: Implied loop but not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Missing**: No bridge between verification and application layer
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### Extraction Quality Gap → Multi-Pass:** missed characters on X-Men 001 triggers multi-pass requirement.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### "Audit response is missing or too short — full response must be logged verbatim"
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### 9 | Missing test fixture artifact | Added tools/eric_gate/seed_test_fixture.py (Section 13)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.41 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### After:** Check unresolved verification failures → Surface failures → Block if failures exist → Load reorientation → Begin work
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Discovery 1: Verification Gap Between Reported and Actual Work
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Evidence: release returns status=BLOCKED, missing evidence listed
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.32 — treat as NEW
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Synthesis validation | Check normalized truth | NOT IMPLEMENTED
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.20 — treat as NEW
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Transitions**: `unresolved` → `resolved` (analysis complete), `resolved` → `validated` (cross-referenced)
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.41 — treat as NEW
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`

### The missing piece is not model size anymore** — it is designing the feedback and acceptance structure around it.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...2471347_x_cis_discovery_workbench_v1_extraction_analysis.md`

### This was previously invisible — the system appeared to function, but only because the operator was silently bridging architectural gaps.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Runtime Constraint:** Blocked by browser security policy (file:// access restrictions)
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Architectural Significance**: Source manifest, processing profile, review states are missing but not blocking Phase 1
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`

### Architectural Significance**: The verification gate is now proven operational across all three layers (Layer 1: 38/38 checks PASS, Layer 2: not yet built, Layer 3: ChatGPT audit PASS).
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

### Old Tier 7 (node 8, "Full Durable Router Pipeline") remains DEFERRED permanently.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### Intake Pipeline** — Phase 1 (manual JSON import) → Phase 2 (watcher service) → Phase 3 (commit layer, deferred)
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Build Impact:** PM and DAM are deferred to Phase 8 (expanded application surface) with minimal scaffolding in Phase 4 (workbench).
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### Staging → Database**: (MISSING) Requires Phase 1 API endpoint
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Phase 3 deferred**: No commit layer to canonical records
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### task_queue schema, execution packet format, queue arbitration policy, retry queue strategy, deferred queue handling, queue replay/recovery, context assembly layer, role prompt packaging
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.30 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Runtime Impact**: Agent tier models are all in `discovered` status (Phase 4), meaning agent tabs will show empty or placeholder content until Phase 4
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.41 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Tier 11C §11 Boundary | "Reviewer initiation (REVIEW_PENDING → REVIEWING) is out of scope.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `CIS_TIER_11D_REVIEWER_SIDE_HANDOFF_SPECIFICATION.md`

### Explicitly deferred by Human Gate with logged rationale
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.36 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### Source Model Tracking**: Model identity preserved but not enforced
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.29 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`

### Segmentation Pipeline**: Scene detection + duration fallback + transcript-assisted option (deferred to ADR-033)
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.22 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`

### Gap**: Need a CapabilityClaim object with validation status, provenance, and correction history
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`

### Hook crash (segfault, missing interpreter):** In enforcement mode (production), fail-closed → exit 1, block all tool calls.
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Next action: still the open question from my last message — is the enforced container proven enough to host a read-and-organize task (the corpus scrape) today, or does the container need work first?
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.46 — treat as NEW
  - `claude crystallizes the vision.txt`

### Pre-Delete Archive Check**: No validation layer for archive policy before file deletions
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.49 — treat as NEW
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`

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

### Archive Drive Object**: 10TB NTFS drive not fully defined as canonical object; ingestion planning deferred
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0410_extraction_analysis.md`

### Gap**: No standardized interface for querying ADRs during extraction
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.28 — treat as NEW
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Runtime Impact**: If model is missing, extraction fails immediately.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`

### Distribution Governance**: Not yet defined; distribution pipeline deferred
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`

### Eric receives CONSENSUS_REACHED with proposal or ESCALATE with unresolved objections.
- support: 2 statements across 1 document(s)
- nearest queue item 20 is only sim 0.32 — treat as NEW
  - `CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md`

### Error returns | `{ "error": "<message>" }` if run_id missing, not Eric-approved, or dispatch fails
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### No validation layer | Execution | Cannot detect bad outputs before storage
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.37 — treat as NEW
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### Storage/VM capacity assessment (deferred per Eric's instruction, design §5)
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.52 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### A primary goal of the Architect Agent is to perform "Chronological Reconciliation" to address the "Truth Gap" in the repository.3 The reasoning loop for this task must be explicitly defined in the agent's system prompt:
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.36 — treat as NEW
  - `...ild_03282026/Agent Orchestration and Sandboxing Research.md`

### Runtime Impact**: Missing or inactive agents return 404; no retry or fallback mechanism
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.42 — treat as NEW
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Missing Multimodal Model**: document_multimodal, reference_image, tutorial_video profiles blocked if multimodal model unavailable
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.22 — treat as NEW
  - `...ents/cis_processing_profile_contract_extraction_analysis.md`

### Prompt File Missing**: System exits with error message
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### Contract Missing → Draft → Approve → Activate**: Missing contracts trigger creation workflow
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`

### Image source management is undefined.** The source image itself has no object representation, creating a provenance gap.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`

### Missing Task Context**: Approval list lacks sufficient context for informed decision-making
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Missing**: Approval/rejection decisions should reinforce the AI's understanding of which tasks need human oversight
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### This creates a **provenance gap** where captures can exist without traceable origin.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...traction/functional_intents/captures_extraction_analysis.md`

### Processing**: Check schema conformity, unsupported claims, missing provenance, contract violations, safety/permission violations, whether frontier escalation needed
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Drifted**: Context lost due to missing files or wrong phase
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### No governance yet**: No validation of captured content, no provenance tracking, no hallucination detection at capture time
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.25 — treat as NEW
  - `...n/functional_intents/captures_readme_extraction_analysis.md`


## Already represented on the working queue  (4)

### Agents (librarian, researcher, teacher, producer, guardrail, worker, orchestrator) are explicitly deferred until foundational layers (1-5) are stable.
- support: 6 statements across 6 document(s)
- MATCHES queue item 21 (sim 0.61): IMPLEMENT THE ROLE THEORY INTO THE AGENTS. Eric's note, 2026-08-29, recorded
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...reative_Intelligence_System_LegacyBuildFiles/X_02_MEMORY.md`
  - `...tional_intents/x_01_system_blueprint_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Agent objects**: Librarian, Researcher, Teacher — defined in architecture but not implemented.
- support: 5 statements across 5 document(s)
- MATCHES queue item 21 (sim 0.63): IMPLEMENT THE ROLE THEORY INTO THE AGENTS. Eric's note, 2026-08-29, recorded
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...s/cis_legacybuildfiles_consolidation_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### The agent stream explicitly says agents come after deterministic workflows are stable, concurrent execution is avoided, and autonomous behavior is out of scope until late maturity.
- support: 3 statements across 3 document(s)
- MATCHES queue item 12 (sim 0.65): Stream agent completions instead of blocking on one call. Gateways support it
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Gap 4 — No Contract Exists for Mapping CIS Tasks to Hermes Agent Tasks
- support: 4 statements across 1 document(s)
- MATCHES queue item 20 (sim 0.63): Put a hermes agent INTO these working sessions (Eric's ask, 2026-08-28).
  - `...tivation_session_extraction_analysis_extraction_analysis.md`


## Single-statement recognitions — weakest evidence  (1939)

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

### In your docs, the merge layer is required because OCR and visual alone are incomplete.
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.23 — treat as NEW
  - `...yBuildFiles/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md`

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

### Claude responded: The commands got concatenated — missing line break.
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.38 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_005.md`

### The Core Loop (This is what you were missing)**
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `...fs/X_How You Work With These Files (CIS Operating Model).md`

### You said: we need to str=art figuring out how to close the gap you mention between the other tabs.
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.22 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### 004.md is the most significant gap — 1653 unread lines.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.35 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### AI assistance must not silently reclassify missing artifacts as “bureaucratic detours.”
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Application Layer** blocked by uncertainty tracking
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...06699132426333_x_cis_discovery_model_extraction_analysis.md`

### Application Layer**: Blocked by missing pagination and filtering
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.39 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

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

### Build Impact**: Project resolution system is a missing dependency.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Build Impact**: Stage management system is not yet built.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Canonical placement of Obsidian readable mirrors remains unresolved.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.17 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`

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

### Does this match what you had in mind, and is anything missing before I seed it?
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.24 — treat as NEW
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### Eight specific elements are identified as missing:
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.33 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Everything after that was truncated — about 150 lines of the script are missing.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### From the screenshots, you now have the three things that were missing in the earlier attempt:
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `_archive/ChatGTP’s response to vscode, obsidian and github.md`

### Full application remains deferred, but early operator console is required.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Gap 3 — cis-log current signature: Current cis-log commands:
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`

### Gap**: No content hash or source version tracking
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### If ffmpeg is missing we install both in one shot: bash
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.15 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

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

### It stores why understanding changed, what failed, what was assumed, and what remains unresolved.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Layer 1 catches this (file does not exist = FAIL)
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Missing Deduplication**: No detection of duplicate courses across tutorial roots
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.20 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Missing Messages: Initial → Fetching → Validating → Return 404
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Missing Runtime Bridge: Human Override Protocol
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `...unctional_intents/adversarial_review_extraction_analysis.md`

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

### Missing phase-required stream → blocks phase-specific execution
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.40 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

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

### Missing:** Formal definition of "intent" as a system object
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.23 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### New Layer**: Documents marked as "Optional/Later" represent deferred implementation
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.22 — treat as NEW
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`

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

### No validation** of `active_stages` alignment between project and records.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### None**: No validation that conflict is real or accurate
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Not implemented**: Entire content stored as single file
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.28 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Now send 005.md and we close out the last gap.
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.30 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Output:** manifest terminal state or flagged incomplete state
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### Paste both outputs — that will tell us if the push is actually working or silently failing.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.20 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Pre-Review Validation**: No validation before ChatGPT review
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...l_intents/src_20260508_045512_16b932_extraction_analysis.md`

### Preserve current phase, active task, capabilities, and unresolved gaps.
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_010_extraction_analysis.md`

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

### Runtime Impact**: Synthesis requests may timeout if async not implemented; polling mechanism needed
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Runtime blocker:** Without wiring, the app visually implies intelligence capability that does not exist.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

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

### The broken file is missing one level of nesting that the strip provided.
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

### The close action must surface incomplete source states.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### The key behavior: AI runs first, proposes everything, you correct what's wrong or incomplete.
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### Third, what is genuinely missing and needs to be created as part of the Track 1 infrastructure build.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.25 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### This file does not define project-specific close fields, so that remains a gap.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

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

### Unknown**: Default state when manifest missing
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.26 — treat as NEW
  - `...traction/functional_intents/pipeline_extraction_analysis.md`

### Unresolved Application Surface: Bulk Operations
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.25 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`

### Unresolved Routing: Status Change Notifications
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.47 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`

### Update Status**: Change conflict status (OPEN→DEFERRED, etc.)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

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

### ~~Execution Ownership Gap~~ — RESOLVED 2026-05-01
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.46 — treat as NEW
  - `...e_chat_transcripts/ChatGTP_Project_Primer/07_KNOWN_RISKS.md`

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

### (b) Identify the minimal correct fix: rename the config vars, OR add the missing exports,
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.45 — treat as NEW
  - `Claude Roadmap Audit 20260624.txt`

### (not standalone), required sub-field missing or incorrect value.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.23 — treat as NEW
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`

### 1: File Discovery | Source path missing | `find` returns empty | Log missing paths, skip, continue with available sources
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`

### 2026-04-18T10:37:58.490327+00:00 | ERROR: Missing dependency: No module named 'qwen_vl_utils'
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### 4 | Configuration error (missing required arg, invalid env).
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `CIS_TIER_6_2_GATE_CLOSEOUT_COMPLETE_V2_DESIGN.md`

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

### Analytics Layer** - Blocked by record population
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...action/functional_intents/record_001_extraction_analysis.md`

### And this closes a gap in everything I've been framing.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.17 — treat as NEW
  - `claude crystallizes the vision.txt`

### App Integration Bridge**: `push_cis_live()` not wired into app cycle
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...unctional_intents/cis_live_handoff_1_extraction_analysis.md`

### Application Layer** — partially blocked (missing CRUD operations)
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Application Layer**: Blocked by missing workbench behavior and all upstream layers
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Are error paths handled or silently swallowed?
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.22 — treat as NEW
  - `CIS_MODEL_REVIEW_ARCHITECTURE_NOTE.md`

### Are there forward-looking features that should be deferred?
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `CIS_MODEL_REVIEW_ARCHITECTURE_NOTE.md`

### Artifact status** — Which artifacts exist, which are missing
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.43 — treat as NEW
  - `...primer_update_governance_contract_v1_extraction_analysis.md`

### Authority classification editor | Assign and edit classifications | Not yet built
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.24 — treat as NEW
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`

### Autonomous Action Attempt**: Blocked by restricted capabilities
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`

### BLOCKED | Dependency missing, cannot proceed | → CLOSE (with blocker logged)
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### Before**: Contradictions could be silently preserved.
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `...itutional_memory_governance_revision_extraction_analysis.md`

### Blocked By:** STATE.md initialization, Phase definitions
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Blocked by: Missing capture layer infrastructure
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`

### Blocker 8: Missing artifact_id in completed items
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.37 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`

### Blocking:** If missing, projects cannot branch or merge
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Branch note validation | No validation for branch note format | LOW — not yet formalized
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Branch notes are the missing documentation layer
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`

### Bridges the gap between "chat about an idea" and "structured project with assets and schedule."
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.25 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24.md`

### Broadcast Validation:** No validation that broadcast content is correct or complete
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.22 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`

### Brush**: Texture validation prevents missing references
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.19 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Build Impact**: Initial implementation must be rule-based; adaptive routing is explicitly deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...lligence_routing_model_orchestration_extraction_analysis.md`

### Build Impact**: Low priority but creates technical debt if deferred
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`

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

### Business Rules**: No validation of state transitions
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...extraction/functional_intents/cis_db_extraction_analysis.md`

### CREATION and LIFE are top-level domains** with CREATION proven first — LIFE domains (Home, Body, Mind) are deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.23 — treat as NEW
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

### Constraint 1: Application Layer Blocked by Infrastructure Wiring
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.22 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Constraint**: Malformed files are silently skipped
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

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

### Cross-Slot Validation**: No validation for model slot interoperability.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.20 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

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

### Current Status**: Missing — this is a coordination gap.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Current**: No validation between trigger and execution
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.26 — treat as NEW
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`

### DAM module not implemented | No asset management | LOW
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.22 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### DEFERRED** | SWA application | ⬜ Separate project
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.21 — treat as NEW
  - `DEV-PIVOT-06_BUILD_DIRECTION.md`

### DEFERRED** | WIAS full operationalization | ⬜ After CIS complete
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `DEV-PIVOT-06_BUILD_DIRECTION.md`

### Dead Letter Channel for out-of-scope | Unrecognized domains must not silently create work | Invalid Message Channel (Hohpe/Woolf)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### Deferred**: Non-blocking recommendations deferred
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### Dependency 2:** Gap tracker application depends on Architect output
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Dependency Impact**: References to open questions must specify which file to use
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.18 — treat as NEW
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`

### Dependency Impact**: Tag quality depends on keyword coverage - missing genres will be "uncategorized"
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...action/functional_intents/cis_ingest_extraction_analysis.md`

### Dependency Impact**: runtime/manifests/ origin and status unresolved; prohibited write target
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.27 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`

### Dependency Impact:** No dependency chain issue — pure syntax error from incomplete refactoring
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Design note:** Full payload persistence is a known gap.
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `CIS_TIER_11D_REVIEWER_SIDE_HANDOFF_SPECIFICATION.md`

### Discovery 14: Glossary Entry Trigger Unresolved
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Discovery 1: Execution Layer Gap as Primary Blocker
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### Discovery 4: Application Layer Blocked by Execution/Core Workflow
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Discovery 6: Version Control Gap for Runtime Assets
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Do you want to do that work now — read the 15 insight records and build the plan — or do you want me to draft a plan based on what's in the current documentation and you tell me what it's missing?
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### Draft Type Inference**: Must match known patterns; unrecognized types silently skipped
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.32 — treat as NEW
  - `...ctional_intents/cis_download_watcher_extraction_analysis.md`

### E3: Build-plan workflow visibility — explicitly deferred
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.37 — treat as NEW
  - `proposals/POST_TIER10_PLANNING_REVIEWER_RESPONSE.md`

### Empty project structure** | CRITICAL | The auto-generated file contains no actual project tree, indicating either a failed generation, an empty project, or a placeholder awaiting population.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `...tion/functional_intents/instructions_extraction_analysis.md`

### Error States**: 400 (missing query), 500 (module error)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### Error returns | `{ "error": "<message>" }` if topic/intent missing or subprocess fails
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Error: 400 (missing manifest), 503 (Slot 1 not running), 500 (enqueue failure)
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Error: missing required fields for target type
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.18 — treat as NEW
  - `...gacybuildfiles_x_07_knowledge_stream_extraction_analysis.md`

### Every deferred reduction must have a target resolution.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Fail (400)**: Missing thread_id, no messages, no user messages
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.28 — treat as NEW
  - `...ction/functional_intents/idea_drafts_extraction_analysis.md`

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

### Firefox Configuration is a Missing Prerequisite
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.12 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`

### Format Validation**: WAV/MIDI format validation not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.15 — treat as NEW
  - `...857838508_x_11_sound_stream_expanded_extraction_analysis.md`

### GUI Layer**: Blocked by record management stability
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.25 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Gap 2: Cloudflare Tunnel for Hermes (ChatGPT → Hermes)
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.45 — treat as NEW
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Gap between foundation and application is now mapped
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Gap**: Function exists but has no integration point
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.20 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Gap**: How are classified actions passed to the execution engine?
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.26 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### Gap**: How often CIS_LIVE.md should be updated
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: Log format is hardcoded in Python string
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Gap**: No batch processing of multiple source_ids
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`

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

### Gap**: No defined thresholds for hardware monitoring
- support: 1 statements across 1 document(s)
- nearest queue item 9 is only sim 0.25 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Gap**: No mechanism to prevent future duplicates based on dedup history
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `...tion/functional_intents/dedup_memory_extraction_analysis.md`

### Gap**: No model selection algorithm in registry
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Gap**: No notification system for workflow events
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.21 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

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

### Gap**: No validation that compiled content is valid Markdown
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: No visual workflow map showing where user is in the lifecycle
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.25 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap**: `benchmark_score` is a free-form text field
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.35 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Gap**: live.creative-intelligence-system.com vs root domain
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.21 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap: Public File Sensitive-Content Filter Missing
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.25 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### Gap:** Assets are de facto LMS content, not a general DAM.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.22 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Gap:** How do other domains request sound assets?
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.21 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap:** How does Sound query Intelligence Layer?
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap:** Manual file-gathering burden identified
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Gap:** No validation of handover packet quality
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Gap:** Original report only listed 3 candidates.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.32 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Gap:** There is no defined capabilities manifest object.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Gaps: 5 missing objects, 4 missing rule sets, 3 missing interfaces
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...action/functional_intents/record_001_extraction_analysis.md`

### Goal formation is the missing upstream writer.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `DEV-PIVOT-15_SESSION_OPEN_ITEMS.md`

### Grader Validation**: No validation that graders are correct
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...hy_the_future_of_ai_is_a_file_system_extraction_analysis.md`

### Hash mismatch → error**: Not implemented (hash computed on copy)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `...action/functional_intents/cis_intake_extraction_analysis.md`

### Heartbeat Configuration Validation**: No validation of heartbeat parameters
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.17 — treat as NEW
  - `...hy_the_future_of_ai_is_a_file_system_extraction_analysis.md`

### Houdini**: Advanced/Long-Term Tool authority (deferred)
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`

### How to install the missing Python dependencies when using the Dify code execution module in Python?
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...ild_03282026/Agent Orchestration and Sandboxing Research.md`

### If SSH is unavailable, the update fails silently.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`

### If capability does not exist: REJECTED with correction
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.24 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### If it fails (e.g., a missing library), it reads the error and fixes its own code.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...ons_Before_Build_03282026/The Proxmox _Lab_ Architecture.md`

### If registry is down or incomplete, sidebar shows stale/empty state.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### If response parsing is not implemented, Layer 3 cannot run
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...ication_layer_contract_v1_addendum_a_extraction_analysis.md`

### Impact**: Exclusion lists may be incomplete or outdated
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`

### Impact**: If missing, query returns no results or errors
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.33 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Impact**: Parallel execution is possible but not implemented.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`

### Impact**: Partial writes could serve incomplete content
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.31 — treat as NEW
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Implication**: All five previous commands are incomplete without the sixth
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.29 — treat as NEW
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`

### Implication**: Promotion can be blocked by human unavailability
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.25 — treat as NEW
  - `...unctional_intents/adversarial_review_extraction_analysis.md`

### Implicit rejection:** Dependency conflicts unresolved (DaVinci Resolve library conflicts)
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`

### Incomplete diagnosis**: Root cause not identified
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.20 — treat as NEW
  - `...tional_intents/claude_session_primer_extraction_analysis.md`

### Insight review → Promotion | Not implemented | Insights not promoted
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`

### Intake layer status | ✓ | ✓ | ✓ if changed | If gap is risk
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.20 — treat as NEW
  - `HANDOFF_SCHEMA.md`

### Intelligence Services Layer**: Now active (previously not implemented)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...e_system_legacybuildfiles_x_03_state_extraction_analysis.md`

### Is the content complete (not truncated, not placeholder)?
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.22 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### It is deferred until the individual adapter build_plan_nodes (7R.2, 7R.3) are
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.48 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### It is only as good as the last time it was updated, and updating it keeps getting deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### It is the missing stage that prevents Phase D (Intelligence) from completing.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.24 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### It should not silently remain as an implied runtime destination.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.24 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### It's not wrong; it's incomplete in exactly the two places that make CIS different from a chat-triggered job runner.
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `claude crystallizes the vision.txt`

### Lifecycle**: Conflict detected → Logged via cis_conflict_append.py → Resolved (or deferred)
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Lifecycle**: Created → Logged → Resolved (or deferred)
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.28 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`

### Lifecycle**: RUN → PASS/FAIL → RESOLVED/UNRESOLVED
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`

### Limitation: global build-order validity is not asserted (deferred per Section 4.4.2).
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### Limitation:** No validation of solution quality
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.32 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Log aggregation across worker instances (not implemented)
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...l/extraction/functional_intents/logs_extraction_analysis.md`

### MCP Integration is Incomplete**: The deepseek-tui MCP server is configured but not fully connected to project scope.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...l_intents/deepseek_hermes_online_001_extraction_analysis.md`

### MCP Integration** blocked by MCP protocol understanding
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...functional_intents/user_expectations_extraction_analysis.md`

### Missing Application Surface: Cancellation Support
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.24 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`

### Missing Authority Tracking**: Blocks user correction workflows (cannot distinguish authoritative from system-generated)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...tional_intents/x_07_knowledge_stream_extraction_analysis.md`

### Missing Branch Tracking**: Without branch notes, orientation collapses during recursion
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...chat_2026_04_005_extraction_analysis_extraction_analysis.md`

### Missing Content Classification**: Blocks conditional OCR routing
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.29 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Missing Intelligence Layer**: Sound operations cannot access structure or transformation
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.20 — treat as NEW
  - `...l_intents/x_11_sound_stream_expanded_extraction_analysis.md`

### Missing Normalization Layer**: Blocks application-layer display (cannot transform canonical to views)
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.21 — treat as NEW
  - `...tional_intents/x_07_knowledge_stream_extraction_analysis.md`

### Missing Plugin**: If a plugin is enabled but not installed, the project fails to load.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...action/functional_intents/myproject3_extraction_analysis.md`

### Missing Preview Stamp**: Blocks apply entirely
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `.../functional_intents/primer_update_v3_extraction_analysis.md`

### Missing Question Rejection** — Push button disabled when question field empty
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.25 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Missing Runtime Bridge: Operator-to-Runtime Translation
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### Missing Runtime Bridge: STATE.md → Stream Mapping
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Missing Runtime Bridge: Seed → Incremental Processing
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`

### Missing Slot 1 returns 503 BLOCKED, not a queued job
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Missing Step:** User running diagnostic commands
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Missing VAULT_DIR**: Prevents git URL derivation
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### Missing Workbook**: Application data model cannot be finalized without workbook
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `...onal_intents/x_10_application_stream_extraction_analysis.md`

### Missing `queue_worker` module blocks app startup
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.28 — treat as NEW
  - `...el/extraction/functional_intents/app_extraction_analysis.md`

### Missing any mode means incomplete infrastructure.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...intents/cis_phase_pd_build_plan_docx_extraction_analysis.md`

### Missing canonical objects** → blocks all operations
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.30 — treat as NEW
  - `...gacybuildfiles_x_cis_execution_layer_extraction_analysis.md`

### Missing command entry points**: If runtime doesn't expose intake/processing/review commands, interface cannot function
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.25 — treat as NEW
  - `...tional_intents/x_cis_runtime_spec_v1_extraction_analysis.md`

### Missing commands** block coworker productivity
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Missing error handling → Return to Claude with specific requirement
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `.../cis_predev_infrastructure_plan_docx_extraction_analysis.md`

### Missing error handling**: If runtime doesn't surface failures, operator cannot retry
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...tional_intents/x_cis_runtime_spec_v1_extraction_analysis.md`

### Missing input — handles absent files gracefully (correct exit code)
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.26 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### Missing intent understanding blocks Suggest state
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...nctional_intents/x_00_operator_model_extraction_analysis.md`

### Missing items should block the close sequence.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Missing project type** | HIGH | "Unknown project type" prevents any layer inference or dependency mapping.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.30 — treat as NEW
  - `...tion/functional_intents/instructions_extraction_analysis.md`

### Missing required CLI arg | 4 | Print usage, exit
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.26 — treat as NEW
  - `CIS_TIER_6_2_GATE_CLOSEOUT_COMPLETE_V2_DESIGN.md`

### Missing thread returns 404**: Blocks review creation
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `.../functional_intents/advisor_external_extraction_analysis.md`

### Missing**: Formal definition of preprocessing rules
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`

### Missing**: Interface for viewing pattern analysis
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`

### Missing**: Manual trigger for minutes production
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.31 — treat as NEW
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`

### Missing**: No detailed list of removed records
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.42 — treat as NEW
  - `...tion/functional_intents/dedup_memory_extraction_analysis.md`

### Missing**: Rules for validating time-sensitive information
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`

### Missing**: Rules for which models can access which data
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`

### Missing: Process Integrity Layer Implementation
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.24 — treat as NEW
  - `...ntents/phase_0_5_replan_orchestrator_extraction_analysis.md`

### Missing:** Explicit interface between intent detection and AI state machine
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.26 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Missing:** No GET by ID, no PUT/PATCH, no DELETE — partial CRUD only
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Mitigation**: Basic installation + validation now; deep integration deferred
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`

### Mitigation**: Daemonization deferred but tracked
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Model benchmark validation**: No standardized benchmark process — `benchmark_score` field exists but no validation logic
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.27 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`

### Must capture: failures, dead ends, direction changes, unresolved work,
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ChatGTP_Project_Primer/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`

### My framing was incomplete and you've named exactly where.
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.22 — treat as NEW
  - `claude crystallizes the vision.txt`

### NOT YET BUILT**: Current coarse status for planned items
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

### No Business Rule Validation**: No validation of domain/sub_domain combinations
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.19 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`

### No Dependency Validation**: No validation that updated primers don't break dependencies
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `.../functional_intents/primer_update_v2_extraction_analysis.md`

### No error recovery | Hard failure on any error | **MISSING**
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### No fallback**: If deepseek-tui binary is missing, all DeepSeek calls fail
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...nctional_intents/deepseek_mcp_bridge_extraction_analysis.md`

### No implementation authority is granted beyond what this amendment explicitly allows.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.19 — treat as NEW
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1_AMENDMENT_1.md`

### No message content (missing Human/Claude markers)
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.22 — treat as NEW
  - `...unctional_intents/cis_convert_export_extraction_analysis.md`

### No ngrok/cloudflared tunnel**: Planned but not implemented.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`

### No pattern detection | No analysis of capture patterns | **MISSING**
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### No retry logic | Single attempt per service | **MISSING**
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### No timeout handling | Implicit Playwright timeouts only | **MISSING**
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### No trend identification | No identification of common failures | **MISSING**
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### No unresolved final objections exist in snapshot.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### No validation for Scope Declaration completeness** — What if scope is poorly defined?
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `...primer_update_governance_contract_v1_extraction_analysis.md`

### No validation for review record completeness** — What if categories are skipped?
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...primer_update_governance_contract_v1_extraction_analysis.md`

### No validation that a model must be `benchmarked` before `active`
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.19 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### No validation that capability tags match a controlled vocabulary
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`

### Node Tree Output Layer**: Blocked by Node Tree Layer
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Not implemented**: Each unit is a single record.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Not implemented**: Messages stored as complete units
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.41 — treat as NEW
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Not implemented**: No archival or learning from old conversations
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.33 — treat as NEW
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Not implemented**: No feedback loops for message quality
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Not implemented**: No linkage between advisor output and project artifacts
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.35 — treat as NEW
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Not implemented**: No mechanism to correct or update records.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Not implemented**: No mechanism to reinforce good responses
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.23 — treat as NEW
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Not yet built**: No application interface exists
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`

### Now a stray `)` caused a black screen, revealing a missing validation layer.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`

### Now known: core execution and validation layers are placeholder implementations
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.23 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`

### OCR Model Availability**: If Qwen3-VL-30B server is down, OCR fails silently
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...action/functional_intents/cis_ingest_extraction_analysis.md`

### Object Creation Layer** blocked by 3D Cursor System
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.15 — treat as NEW
  - `...lender_2_80_fundamentals_transcripts_extraction_analysis.md`

### Object must have no unresolved uncertainty flags
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`

### Observation minimum length | Not implemented | Empty observations
- support: 1 statements across 1 document(s)
- nearest queue item 9 is only sim 0.22 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`

### Open questions about usability gaps are honest, not aspirational.
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.20 — treat as NEW
  - `DEV-PIVOT-01_GOVERNANCE_RESET_PROPOSAL.md`

### Output Quality Validation Layer**: Not yet built
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.25 — treat as NEW
  - `...e_system_legacybuildfiles_x_03_state_extraction_analysis.md`

### Output Validation**: No validation of creative assets
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`

### Output definition stabilizes through repeated gap-filling cycles
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.23 — treat as NEW
  - `...nctional_intents/x_00_operator_model_extraction_analysis.md`

### Output must be valid `.md` | File must parse as markdown | **NONE** — no validation
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.38 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Output must contain both responses | Both ChatGPT and Claude responses | **NONE** — no validation
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.24 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Output validation**: No validation of data returned from `cis_lms`
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.20 — treat as NEW
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### PDF-to-Document Bridge**: Required but not implemented; parsing logic is assumed but undefined
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.23 — treat as NEW
  - `...extraction/functional_intents/record_extraction_analysis.md`

### PLANNED | TRANSITIONAL | Structure reserved, content placeholder
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.22 — treat as NEW
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`

### PM module not implemented | No project planning | LOW
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### PRE-DRAFT** - Scope document, no implementation
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...intents/archive_04_active_components_extraction_analysis.md`

### Partial Pass**: Record created with missing fields; flagged for review
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.26 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Pass 5 — Project Promotion | Deferred per existing blocking list.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `CIS_TIER_11_UI_USABILITY_SPECIFICATION.md`

### Pass/Fail: Pass=200 with array; Fail=exception caught silently
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Phase Completion Criteria Gap**: There are no defined criteria for what constitutes "complete" for each phase.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Phase-to-stream routing** — defined conceptually but not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.42 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Placeholder detection (thin or hollow sections)
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Population deferred until operational necessity.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Preprocessing incomplete**: Intelligence cannot operate on raw sources
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`

### Previous assumption: Components were either "implemented" or "not implemented"
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`

### Previously, the gap between AI-proposed content and canonical records was unnamed.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`

### Primer Update Application Surface**: Workbench requirements defined but not implemented.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Primer Updates** blocked by multi-model review
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

