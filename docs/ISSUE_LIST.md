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

- clusters: 5,097
- with 2+ supporting statements: 932
- of those, already on the working queue: 0
- of those, NOT on the working queue: 932
- single-statement clusters (listed last): 4,165


## NOT on the working queue — candidates to merge  (932)

### Architectural Significance**: Structured conflict logging with CLI tool; rule that unresolved conflicts must be logged before session close
- support: 13 statements across 9 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Decisions API has a silent failure mode**: Missing the `description` field causes the API to return `{"success": false}` but the error message is only visible if you parse the JSON response.
- support: 16 statements across 8 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Architectural Significance**: ADR-048 Phase 3 (commit layer) is intentionally deferred because approval and commit are architecturally separate concerns.
- support: 11 statements across 7 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Conflict Contract**: Unresolved conflicts must be logged before session close (OPERATIONAL)
- support: 10 statements across 7 document(s)
- nearest queue item 15 is only sim 0.28 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Missing Phase 0 contracts identified**: Source manifest, processing profile, review states exist only in build plan documents, not as standalone contract files.
- support: 9 statements across 7 document(s)
- nearest queue item 4 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### ADR form auto-increment resets to ADR-020 after log** — a deferred bug that affects governance tracking integrity.
- support: 7 statements across 7 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`
  - `...transcripts/ChatGTP_Project_Primer/Current State Updated.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Architectural Significance**: Filesystem Governance can be planned in parallel during ADR-045 closure, but not implemented
- support: 8 statements across 6 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### This session was supposed to open Phase 1 build work beginning with the three missing Phase 0 contracts — source manifest, processing profile, and review states — and then move into building cis_spine_intake.py.
- support: 7 statements across 6 document(s)
- nearest queue item 8 is only sim 0.36 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### LOCKED — final, constitutionally authoritative OPERATIONAL — governing current behavior in runtime TRANSITIONAL — partially implemented or temporary PRE-DRAFT — scope written, not yet locked for build PLANNED — identified and directionally decided DEFERRED — known, postponed
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `..._Primer/_backups/20260502_0047/09_GOVERNANCE_STATE.md:2`
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...enerated_script_artifacts/042926_Project_Primer.txt:121`
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `...scripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md:2`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Now it is known that 568 verifications have been run with 41 unresolved FAILs, and 0 manifests have been produced this session.
- support: 6 statements across 6 document(s)
- nearest queue item 2 is only sim 0.41 — treat as NEW
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0413_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `CIS_CONFLICT_REGISTER.md`

### Architectural Significance**: The constitutional recognition that "the human is still the API" identifies a fundamental architectural gap where the human operator functions as the transport layer between AI-generated structured content and CIS canonical records.
- support: 6 statements across 6 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Gap:** Pipeline steps (Classify, Preprocess, Extract, Normalize) have no orchestration logic
- support: 6 statements across 6 document(s)
- nearest queue item 15 is only sim 0.25 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Now, session start checks for unresolved failures, and session end requires zero failures to close cleanly.
- support: 8 statements across 5 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `...ce_System_v1/runtime_scripts/runtime/2_CIS_REORIENTATION.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`
  - `...transcripts/ChatGTP_Project_Primer/12_CONTRACT_AUTHORITY.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Dashboard HTML refactor deferred | 2736-line monolith cannot be safely restructured mid-build | Blocks frontend modularization
- support: 7 statements across 5 document(s)
- nearest queue item 2 is only sim 0.21 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### Verification Layer**: Blocked by chunked verification architecture, contract verification sequencing
- support: 6 statements across 5 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Human operator was accidental middleware** - Previously assumed as intentional orchestration layer, now recognized as systemic bottleneck created by incomplete architecture
- support: 6 statements across 5 document(s)
- nearest queue item 15 is only sim 0.25 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ions_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ve/SESSION_DISTILLATIONS/2026-04-28_operator_layer_pivot.md`
  - `_archive/generated_script_artifacts/042926_Project_Primer.txt`

### Gap**: No validation for duplicate ADR numbers — ADR-012 through ADR-017 conflict was discovered manually
- support: 6 statements across 5 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### The "no new governance surface" rule is adopted but not formalized as an ADR.** This is a governance gap that needs resolution.
- support: 6 statements across 5 document(s)
- nearest queue item 21 is only sim 0.24 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`
  - `ADRs/ADR-048_SCOPE_PREDRAFT.md`

### Intake layer is the critical missing piece** — ADR-048 is pre-draft and the current build target.
- support: 6 statements across 5 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...Project_Primer/archive/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/archive_00_start_here_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### assert res24[0] == FunctionDefinition( NoneToken(), name=String('func'), parameters=(), body=CodeBlock( Declaration( Variable(Symbol('a'), type=FloatType( String('float32'), nbits=Integer(32), nmant=Integer(23), nexp=Integer(8) ) ) ), Declaration( Variable(Symbol('c1'), type=Type(String('bool')) ) )
- support: 6 statements across 5 document(s)
- nearest queue item 6 is only sim 0.20 — treat as NEW
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r0`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r1`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r4`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r5`
  - `swa_project/social_work_ai/03_CLINICAL/test_c_parser.py#r6`

### Conflict Resolution Transition**: Unresolved conflicts → logged to CIS_CONFLICT_REGISTER.md → session close allowed.
- support: 5 statements across 5 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...ranscripts/ChatGTP_Project_Primer/10_OPERATIONAL_REALITY.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Architectural Significance**: CIS_CONFLICT_REGISTER.md is now a required artifact for tracking unresolved contradictions, drift, and terminology issues.
- support: 5 statements across 5 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...itutional_memory_governance_revision_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...pts/ChatGTP_Project_Primer/archive/PROJECT_PRIMER_UPDATE.md`
  - `...t_transcripts/ChatGTP_Project_Primer/13_RUNTIME_TOPOLOGY.md`

### Missing Validation Layer: Handoff Validation**: There is no validation step for the handoff document.
- support: 5 statements across 5 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Runtime Impact**: Every session must pass through OPEN→ACTIVE→RESOLVED→ARCHIVED lifecycle; unresolved sessions block continuity
- support: 5 statements across 5 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### - Unresolved gaps and missing layers including missing runtime bridges, undefined objects, unstable schemas, unresolved orchestration, unresolved routing, missing governance, missing validation layers, unresolved application surfaces, and unresolved storage rules - Build-plan implications including 
- support: 5 statements across 5 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `.../session_distillations_readme_extraction_analysis.md#r4`
  - `..._2026_04_004_extraction_analysis_extraction_analysis.md`
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `...lopment_system_architecture_7_extraction_analysis.md#r1`
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### ADR-048.md | LOCKED | Staged Draft Intake Layer — Phase 1 + Phase 2 complete; Phase 3 deferred
- support: 5 statements across 5 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `..._transcripts/ChatGTP_Project_Primer/04_ACTIVE_COMPONENTS.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md`
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### Schema validation**: No validation that payload matches expected schema for draft type
- support: 5 statements across 5 document(s)
- nearest queue item 6 is only sim 0.25 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`
  - `...extraction/functional_intents/drafts_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`
  - `...tion/functional_intents/queue_worker_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### "verification_status": "Manifests produced: 4; Verifications run: PASS; Unresolved FAILs: 0."
- support: 5 statements across 5 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...st_try/insights_First_Try/_Automation_Discussion_ChatGTP.md`
  - `...xtraction/functional_intents/session_extraction_analysis.md`
  - `HANDOFF_SCHEMA.md`

### Runtime Impact**: L2 verification silently fails or produces incomplete results for large contracts.
- support: 5 statements across 5 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### push_cis_live() exists but has no integration point**: This function was created without a corresponding application update cycle to wire it into, indicating a gap between function development and system integration.
- support: 7 statements across 4 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...de_chat_transcripts/2026-04-20_Resuming creative VM work.md`
  - `...unctional_intents/cis_live_handoff_1_extraction_analysis.md`

### Job status polling missing | Needed after queue refactor | ADR-045 dashboard polling
- support: 7 statements across 4 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...s/ChatGTP_Project_Primer/11_TRANSITIONAL_IMPLEMENTATIONS.md`
  - `_archive/generated_script_artifacts/042926_Project_Primer.txt`

### Model Registry ↔ route_task.py**: Registry designed for routing but `route_task.py` does not exist as code.
- support: 7 statements across 4 document(s)
- nearest queue item 8 is only sim 0.38 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...tion/functional_intents/all_insights_extraction_analysis.md`

### None explicitly documented** - potential gap in execution layer
- support: 6 statements across 4 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...hoosing an AI platform for professional project guidance.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Session Close Input Validation**: focus, completed, next_steps are REQUIRED — returns 400 if missing
- support: 6 statements across 4 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...xtraction/functional_intents/session_extraction_analysis.md`

### Model registry API → Intel sidebar | GET /api/models endpoint does not exist | HIGH — blocks ADR-024/025
- support: 6 statements across 4 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0547_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Gap**: No validation of verification results before session close
- support: 6 statements across 4 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Architectural Significance**: Governance artifacts exist in distinct states (LOCKED, OPERATIONAL, TRANSITIONAL, PRE-DRAFT, PLANNED, DEFERRED) that determine their architectural authority and implementation priority.
- support: 6 statements across 4 document(s)
- nearest queue item 21 is only sim 0.29 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...ional_intents/14_governance_glossary_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Manifest Directory Resolution**: ADR-047 pending — runtime/manifests/ status unresolved.
- support: 6 statements across 4 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...extraction/functional_intents/config_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/13_RUNTIME_TOPOLOGY.md`

### Merge layer does not exist**—OCR output and visual interpretation output cannot be merged into single structured record
- support: 5 statements across 4 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`
  - `...yBuildFiles/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md`

### Intel sidebar data flow | local/remote/agent tabs not wired | HIGH — blocks intelligence connection
- support: 5 statements across 4 document(s)
- nearest queue item 12 is only sim 0.38 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Gap**: No formal verification step — decisions may be implemented but not confirmed
- support: 5 statements across 4 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Notes field has qualifying criteria** — ADR-016 defines Notes captures deferred decisions, warnings, gotchas, and mid-thought work — not next steps.
- support: 5 statements across 4 document(s)
- nearest queue item 22 is only sim 0.26 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`

### Session Validation** — No validation that session has meaningful content before resolution
- support: 5 statements across 4 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `...n/functional_intents/session_extract_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`
  - `...xtraction/functional_intents/session_extraction_analysis.md`

### Gap**: How knowledge objects are stored, indexed, retrieved is not fully defined
- support: 5 statements across 4 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Dependency Impact**: Phase 3 (commit) is deferred - creates incomplete pipeline
- support: 5 statements across 4 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Missing Governance: Benchmark Definition Authority
- support: 5 statements across 4 document(s)
- nearest queue item 21 is only sim 0.25 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_010_extraction_analysis.md`

### Contract-first discipline requires three missing Phase 0 documents before the spine ingestion pipeline can be built: source manifest, processing profile, and review states.
- support: 5 statements across 4 document(s)
- nearest queue item 17 is only sim 0.42 — treat as NEW
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Review this proposal against the locked ADRs and identify gaps, risks, and missing dependencies.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `...is_predev_infrastructure_plan_claude_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`
  - `_archive/orientation_backups_20260430/09_GOVERNANCE_STATE.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Missing Validation Layer: Cross-Document Validation
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.18 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### No Content Validation**: No validation that extracted content is coherent
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...n/functional_intents/session_extract_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### Dependency Impact**: Creates a persistent gap in the session record — post-close work is invisible to future sessions
- support: 4 statements across 4 document(s)
- nearest queue item 8 is only sim 0.31 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### This file contains all extracted entities, dependency chains, execution flows, orchestration behavior, workflow stages, state transitions, validation logic, governance implications, unresolved gaps, build-order implications, canonical objects, and topology mutations suitable for topology generation 
- support: 4 statements across 4 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Missing automation reduction record blocks verification same as missing Completion Manifest.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...tional_intents/12_contract_authority_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`
  - `...ve_06_foundational_control_contracts_extraction_analysis.md`
  - `contracts/CIS_Automation_Reduction_Contract_v1.md`

### This file contains all extracted architectural intelligence including: - Core architectural discoveries - Topology mutations - Dependency discoveries - Execution-layer implications - Governance and validation implications - Knowledge-layer implications - Application-layer implications - Feedback loo
- support: 4 statements across 4 document(s)
- nearest queue item 22 is only sim 0.24 — treat as NEW
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`
  - `...n_debrief_2025_08_23_16_57_30_extraction_analysis.md#r1`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...ring_plan_checklist_arpc_v1_6_extraction_analysis.md#r3`

### Unresolved Orchestration: Extraction Pipeline Integration
- support: 4 statements across 4 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### - **Architectural Significance**: Identifies a critical missing layer between Workflow Stream (descriptive) and Application Layer (UI). The Execution Layer is the operational engine that makes the system executable by someone other than the architect. - **Affected Layers**: Workflow Stream, Applicat
- support: 4 statements across 4 document(s)
- nearest queue item 15 is only sim 0.25 — treat as NEW
  - `...5139187_x_04_master_architecture_map_extraction_analysis.md`
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...is_workflow_execution_spec_v1_extraction_analysis.md#r1`
  - `...is_workflow_execution_spec_v1_extraction_analysis.md#r3`

### Dependency Impact**: ADR-044 (operator abstraction), ADR-045 (execution ownership - CLOSED), ADR-048 (intake ownership - Phase 1/2 COMPLETE, Phase 3 DEFERRED)
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Intel Sidebar Tabs ↔ Model Registry | local/remote/agent tabs ↔ dynamic data | Not yet built (ADR-024/025)
- support: 4 statements across 4 document(s)
- nearest queue item 15 is only sim 0.40 — treat as NEW
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Architectural Significance**: The `/api/decisions` POST endpoint silently fails if the `description` field is missing.
- support: 4 statements across 4 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...26-04-21_Session close and handoff process clarification.md`
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Unresolved Application Surfaces: Dashboard Integration.** The dashboard integration is described but not specified.
- support: 4 statements across 4 document(s)
- nearest queue item 8 is only sim 0.21 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Build Impact**: Does NOT block ADR-048 Phase 2; explicitly deferred to build-plan reconstruction stage
- support: 4 statements across 4 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

### Schema validation**: No validation that corrected values match expected schema
- support: 4 statements across 4 document(s)
- nearest queue item 3 is only sim 0.23 — treat as NEW
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_015_extraction_analysis.md`

### Verification Contract**: 568 verifications run, 41 unresolved FAILs — ongoing verification process
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0413_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### This is not a minor gap—it is the defining architectural transition point.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Decided against video segmentation for Phase 0 — deferred entirely to Phase 1
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_003.md:213`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_003.md`

### Tier 7: BLOCKED (placeholder per build plan: "Do not design implementation until Tier 6 is verified stable")
- support: 4 statements across 4 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md:79`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md`
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md:9`

### The session then encountered a chain of failures in the session close process — duplicate DB entries, a missing Path import, multiple failed close attempts — before the session close finally completed cleanly.
- support: 4 statements across 4 document(s)
- nearest queue item 13 is only sim 0.39 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### No File Format Validation**: No validation that files match expected extraction format
- support: 4 statements across 4 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`
  - `...on/functional_intents/cis_preprocess_extraction_analysis.md`
  - `...raction/functional_intents/extractor_extraction_analysis.md`
  - `...unctional_intents/ingest_extractions_extraction_analysis.md`

### CREATION pipeline proven first, LIFE domains deferred.** But design decisions made with LIFE in mind may need revision based on CREATION pipeline experience.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### The prompt version tracking gap was identified and explicitly deferred as lower priority. It was not added to the task list or the next steps.
- support: 4 statements across 4 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...-24_CIS phase 1 intelligence extraction handoff.md:1062`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Governance Layer**: Cannot enforce policies without authentication/authorization
- support: 4 statements across 4 document(s)
- nearest queue item 21 is only sim 0.27 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Dashboard HTML refactor is DEFERRED** — This is a low-priority application-layer task that has been pushed back.
- support: 9 statements across 3 document(s)
- nearest queue item 2 is only sim 0.19 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### Deployment has a gap**: ensure_models_table is not wired into ensure_tables(), meaning fresh DB deployments will fail.
- support: 9 statements across 3 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### Review is the Next Dependency**: `cis_review.py` is referenced as the next step but does not exist yet.
- support: 6 statements across 3 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Conflict panel | View/register/resolve conflicts | Not implemented | /api/conflicts + dashboard
- support: 6 statements across 3 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Missing `description` field causes silent failure — no error returned, no record created.
- support: 5 statements across 3 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Missing execution-bridge layer**: Previously assumed workflow stream was sufficient; now identified as missing enforceable runtime actions, pass/fail conditions, review states, operational responsibilities
- support: 5 statements across 3 document(s)
- nearest queue item 12 is only sim 0.34 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...intents/cis_handoff_current_position_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### No Validation Layer**: There is no explicit validation of handoff package completeness, phase accuracy, or stream relevance.
- support: 5 statements across 3 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0410_extraction_analysis.md`
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### files_written polymorphism is unstable**: Workaround exists but formal fix deferred to ADR-047 - manifest structure has known instability.
- support: 5 statements across 3 document(s)
- nearest queue item 4 is only sim 0.25 — treat as NEW
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...ts/ChatGTP_Project_Primer/archive/10_OPERATIONAL_REALITY.md`

### 3. **Governance-Implementation Divergence**: Governance documents had become more mature than the implementation they govern. This creates ceremonial governance risk — contracts describing ideal states rather than actual operational behavior. Previously, governance maturity was assumed to indicate i
- support: 5 statements across 3 document(s)
- nearest queue item 21 is only sim 0.27 — treat as NEW
  - `...ayer_pivot_and_pd5_governance_extraction_analysis.md#r2`
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Next item from the corrected sequence: Write missing Phase 0 contracts — source manifest, processing profile, review states.
- support: 5 statements across 3 document(s)
- nearest queue item 2 is only sim 0.51 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Manifest Path Resolution**: runtime/manifests/ origin unresolved → cannot write there → cannot resolve without writing
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`
  - `...t_transcripts/ChatGTP_Project_Primer/09_GOVERNANCE_STATE.md`

### Intelligence Layer as Critical Missing Piece**: The system is at a hard boundary where setup is complete but intelligence is absent.
- support: 4 statements across 3 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...42767492025744_x_07_knowledge_stream_extraction_analysis.md`
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### Unresolved session-level conflicts (those go to Conflict Register)
- support: 4 statements across 3 document(s)
- nearest queue item 8 is only sim 0.29 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`
  - `HANDOFF_SCHEMA.md`

### The execution layer as the missing critical gap. The architecture map explicitly names this: the execution layer between intelligence and application is not yet unified. It currently exists as shell scripts and manual steps. The whole application layer depends on stabilizing this first.
- support: 4 statements across 3 document(s)
- nearest queue item 15 is only sim 0.22 — treat as NEW
  - `...an AI platform for professional project guidance.md:333`
  - `...cyBuildFiles/_CIS_The pattern across the CIS docs.md:26`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`

### Assessed all three model slots against CIS requirements — slot roles confirmed, Slot 3 registration deferred pending Qwen3.6-27B evaluation
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-27_2152.md`

### Gap**: Execution layer is identified as missing but not yet defined
- support: 4 statements across 3 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### Gap:** Workflow stages are defined but stage schema (input, output, validation, state transition) is not formalized.
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### The intake panel feedback gap — no visual response after clicking INTAKE — was identified but not fixed this session.
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### States**: Defined (not implemented), Active (implemented), Idle, Responding
- support: 4 statements across 3 document(s)
- nearest queue item 10 is only sim 0.30 — treat as NEW
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Session Review**: Live sessions must be resolved before close — unresolved sessions block next build
- support: 4 statements across 3 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Architectural Significance**: Human operator had become the bridge between partially completed system layers, functioning as an implicit integration layer that masked missing abstraction boundaries.
- support: 4 statements across 3 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...ions_2026_04_28_operator_layer_pivot_extraction_analysis.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Missing Layers:** The staged draft intake layer (ADR-048) and filesystem governance layer (ADR-047) are identified as missing layers that will be implemented after ADR-045 closure.
- support: 4 statements across 3 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...intents/20260502_0047_05_adr_summary_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`

### "The Human is Still the API" is an architectural gap, not a UX problem.** This reframes the entire intake problem.
- support: 4 statements across 3 document(s)
- nearest queue item 20 is only sim 0.34 — treat as NEW
  - `...intents/archive_02_next_build_target_extraction_analysis.md`
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### The `route_task.py` routing layer was described architecturally — it queries the model registry to decide which tier handles a given task — but does not exist as code.
- support: 4 statements across 3 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Authority Source** | Architecture specs and ADR-derived rules; standalone contract missing
- support: 4 statements across 3 document(s)
- nearest queue item 21 is only sim 0.27 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Gap**: No validation that returned fields match expected schema
- support: 4 statements across 3 document(s)
- nearest queue item 13 is only sim 0.22 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Missing**: No schema validation, content validation, or format validation defined
- support: 4 statements across 3 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...extraction/functional_intents/health_extraction_analysis.md`
  - `...extraction/functional_intents/record_extraction_analysis.md`
  - `...on/functional_intents/update_prefill_extraction_analysis.md`

### Architectural Significance**: Filesystem Governance and Staged Draft Intake are recognized as future layers but have no implementation yet.
- support: 4 statements across 3 document(s)
- nearest queue item 18 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_05_02_0558_extraction_analysis.md`
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### No Validation Layer**: Content is not validated for accuracy, completeness, or consistency.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`
  - `...unctional_intents/ingest_extractions_extraction_analysis.md`

### States**: Pending, L1 complete, L2 complete, (MISSING) Failed, (MISSING) Archived
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### 'DEFERRED', -- Intentionally postponed (not a gap)
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md`

### Polymorphic Structure Validation**: No validation for files_written canonicality
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.23 — treat as NEW
  - `.../functional_intents/primer_update_v3_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### State Validation**: No validation of state transitions (e.g., can't go from COMPLETE back to DECIDED)
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Description:** If state update fails after output generation, execution is incomplete.
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### No validation for draft file naming** — What if naming convention is violated?
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...primer_update_governance_contract_v1_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### POST Validation**: Returns 400 with error message for missing required fields
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.22 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...extraction/functional_intents/collab_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Gap:** Projects exist but are not connected to tasks, schedule, DAM, knowledge, or
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Gap**: No validation for field content — empty strings may be accepted
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.19 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Merge Validation** — No validation that merge produces coherent records
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.25 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...tents/1776042143355379182_x_03_state_extraction_analysis.md`

### Lifecycle:** Created → (Optional) Deferred → Active → Completed
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Workflow Output Validation**: No validation rules for workflow outputs
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Slot 1 Validation**: No validation that Slot 1 is running before L2
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### States**: Enabled, Disabled, Resolved, Unresolved.
- support: 3 statements across 3 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `...action/functional_intents/myproject3_extraction_analysis.md`
  - `...re_structure_lock_system_logic_first_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Draft States**: PRE-DRAFT (not yet built), STAGED (future), APPROVED (future), REJECTED (future), SUPERSEDED (future)
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_04_0214_extraction_analysis.md`
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`

### The fourth layer (execution bridge) was previously implicit and is now explicitly recognized as missing.
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Unresolved Application Surface: Full Application Layer
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.18 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### This was flagged as a known design flaw from the previous session that needed to be fixed as the first task of the following session but had not been fixed yet. ________________
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...e_atlas/original_CISChats/CIS_Chat_2026-04_016.md:81#r2`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### CIS Live session #020 remains unresolved — flagged in last handoff, not addressed this session, must be resolved before next session closes
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-28_0553.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### unresolved verification FAILs, and uncommitted changes before allowing close
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...tional_intents/12_contract_authority_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Session Close Fail**: Fields not generated, handoff not written, sync incomplete.
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`

### Fix CIS Live rounds form session dropdown (deferred, LOW severity)
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-05_0427.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Runtime Impact:** Bad outputs cannot silently contaminate the knowledge base.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...nal_CISChats/CIS_Canonical_Build_Sequence_Plain_Language.md`
  - `...nts/cis_plain_language_build_roadmap_extraction_analysis.md`
  - `...onical_build_sequence_plain_language_extraction_analysis.md`

### Knowledge does not exist as primary input layer**—it is generated through Intelligence processing
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...telligence_System_LegacyBuildFiles/X_01_SYSTEM_BLUEPRINT.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### No Content Index**: Full-text search not implemented
- support: 3 statements across 3 document(s)
- nearest queue item 1 is only sim 0.37 — treat as NEW
  - `...l/extraction/functional_intents/logs_extraction_analysis.md`
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Architectural Significance**: Knowledge Layer does NOT exist at system start.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`
  - `...nce_System_LegacyBuildFiles/X_01_SYSTEM_BLUEPRINT.md:86`
  - `...telligence_System_LegacyBuildFiles/X_01_SYSTEM_BLUEPRINT.md`

### Knowledge record gap**: The knowledge record in /mnt/projects/cis/knowledge/records/ does not contain infrastructure documentation
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_009_extraction_analysis.md`

### The knowledge records are the most important gap.** Those are the actual output of the system.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`
  - `claude_chat_transcripts/2026-04-17_Hand off evaluation.md`

### Manual Paste Confirmed:** Auto-fetch model responses deferred — manual paste is the confirmed input method (ADR-029)
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:36`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Architectural Significance**: A single stray `)` character in LivePanel caused complete UI failure — indicates no validation layer exists between panel code and runtime execution
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`

### Retry/Escalation Logic**: Not yet defined—this is a gap that will be discovered during runtime
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...tents/foundational_control_contracts_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Dashboard expansion** - blocked by monolith; requires modularization ADR
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Decisions API Error Surface**: Runtime error surface needed for missing `description` field.
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### ADR Numbering:** Sequential numbering with gap detection (ADR-008 out of sequence noted)
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0416_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### ADR-045 steps progress through VERIFIED COMPLETE → IN PROGRESS → NEXT → DEFERRED
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`
  - `...intents/20260502_0047_05_adr_summary_extraction_analysis.md`

### Staged Draft Intake Layer** (ADR-048) is blocked by ADR-045 completion
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### No Governance or Validation Exists**: The system has no governance layer, no validation logic, no authority structures, and no quality control mechanisms.
- support: 3 statements across 3 document(s)
- nearest queue item 3 is only sim 0.23 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...n/functional_intents/project_helpers_extraction_analysis.md`
  - `...on/functional_intents/import_session_extraction_analysis.md`

### Governance Layer**: Blocked on validation engine — cannot enforce contract without validation
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...ion/functional_intents/minutes_agent_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Governance State Machine**: Formal 6-state classification system for governance artifacts (LOCKED, OPERATIONAL, TRANSITIONAL, PRE-DRAFT, PLANNED, DEFERRED)
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.25 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Missing Validation Layer**: The validation layer for contract actions is non-functional.
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`
  - `...nts/runtime_implementation_contracts_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### ``` Field 5 — Verification Status: Manifests produced: [count] Verifications run: [count] Unresolved FAILs: [count — must be 0 to close cleanly] Verification log: /mnt/projects/cis/logs/verification_log.md ```
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`
  - `...rchChatsProjectsCodeCustomizeDesignMoreRecentsHidePhase.txt`
  - `contracts/CIS_Verification_Layer_Contract_v1.md:57`

### Queue Execution Validation**: verify_contract execution operational but patch incomplete
- support: 3 statements across 3 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### `system says success → user asks to verify → command output checked → incomplete visibility rejected → verification method corrected`
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:195`
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:365`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### The Architecture Map holds the whole layered picture together and explicitly names the execution gap.
- support: 3 statements across 3 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...em_LegacyBuildFiles/_CIS_The pattern across the CIS docs.md`
  - `...rm_for_professional_project_guidance_extraction_analysis.md`
  - `...yBuildFiles/_CIS_The pattern across the CIS docs.md:219`

### This is a critical architectural gap that must be resolved before implementation.
- support: 3 statements across 3 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...buildfiles_x_cis_reinforcement_model_extraction_analysis.md`

### ## Discovery 2: Eight-Layer Architecture (Decision 041) - **Architectural Significance**: System expanded from simple pipeline to 8-layer architecture - **Affected Layers**: Infrastructure, Core Creative Tools, Knowledge and Library, Intelligence Services, Story-First Workflow, Agent Roles, Governan
- support: 3 statements across 3 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `...Intelligence_System_LegacyBuildFiles/X_02_MEMORY.md:145`
  - `..._legacybuildfiles_x_02_memory_extraction_analysis.md#r2`
  - `...wen_vl_evaluation_april_12_2026_full_extraction_analysis.md`

### This also closes a gap that already exists: the Intel sidebar has LOCAL, REMOTE, AGENT tabs listing models, but those lists are currently decorative — not wired to anything functional.
- support: 3 statements across 3 document(s)
- nearest queue item 15 is only sim 0.21 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Write missing Phase 0 contracts — source manifest, processing profile, review states Build cis_spine_intake.py Ingest first spine — Blender documentation Install PySceneDetect and test against a video — now segments have a spine to map to Write ADR-033 — segmentation policy locked after spine and Py
- support: 3 statements across 3 document(s)
- nearest queue item 17 is only sim 0.46 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### Missing Validation Logic**: No structured validation exists for extraction quality
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Unresolved Storage Rules: Memory Archival**: The rules for archiving old memory entries are not defined.
- support: 3 statements across 3 document(s)
- nearest queue item 18 is only sim 0.48 — treat as NEW
  - `...ents/teach_me_something_about_claude_extraction_analysis.md`
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### 401 Unauthorized**: Returned when API key is missing or invalid for remote requests
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.21 — treat as NEW
  - `...ction/functional_intents/gpt_gateway_extraction_analysis.md`
  - `...el/extraction/functional_intents/app_extraction_analysis.md`
  - `...el/extraction/functional_intents/gpt_extraction_analysis.md`

### The traceback in the first terminal will show exactly what's failing. Paste it and I'll fix it. You said: Press CTRL+C to quit
- support: 3 statements across 3 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...l build sequence and architectural dependencies.md:1387`
  - `...pts/2026-04-22_Model registry API implementation.md:246`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:194`

### Let me know when that's open and we'll start with the Resolve button — that's blocking session hygiene for everything downstream. You said: open
- support: 3 statements across 3 document(s)
- nearest queue item 5 is only sim 0.36 — treat as NEW
  - `...pts/2026-04-22_Model registry API implementation.md:512`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:392`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:393`

### **Second reason it wouldn't have hard-stopped anyway:** `hard_stop_enabled: bool = False` by default. Out of the box this guardrail only *warns* — it never halts. The `[BLOCKED: ...4 times]` you saw on `search_files` was the warn/block path on the idempotent-no-progress counter, which does block at 
- support: 3 statements across 3 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...b662dad0751:Loop-breaker block-contract schema draft#r1`
  - `PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md:25`
  - `PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md:28`

### Conflict Logging**: Unresolved conflict → Log to register → Future resolution.
- support: 6 statements across 2 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`

### Missing relationship map**: No single doc governs doc hierarchy, change propagation, or archive reality updates.
- support: 5 statements across 2 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...nd_offs_cis_handoff_current_position_extraction_analysis.md`

### cis_download_watcher.py | Watch for downloads | Not implemented | Automated download management
- support: 5 statements across 2 document(s)
- nearest queue item 8 is only sim 0.29 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...s/20260505_0058_02_next_build_target_extraction_analysis.md`

### Not defined in this session** — segmentation policy deferred to ADR-033
- support: 5 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`

### Architectural Significance**: Previously implicit risk now explicitly tracked in 07; distinct from execution ownership gap and intake ownership gap
- support: 4 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### No quality → capture feedback | Capture quality not measured or fed back | **MISSING**
- support: 4 statements across 2 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### States**: Incomplete (some dependencies not mapped), Complete (all dependencies mapped), Validated (dependencies have been validated)
- support: 4 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Architectural Significance**: `cis-log insight` subcommand does not exist.
- support: 4 statements across 2 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`

### Intake ownership is a missing layer distinct from execution ownership.** Previously, intake was conflated with execution.
- support: 4 statements across 2 document(s)
- nearest queue item 11 is only sim 0.27 — treat as NEW
  - `...26-05-02_constitutional_memory_governance_primer_rewrite.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### ADR-048 intake layer is the critical missing piece** — the handoff package builder is not yet built, and human still manually transfers structured content.
- support: 4 statements across 2 document(s)
- nearest queue item 20 is only sim 0.20 — treat as NEW
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...ranscripts/ChatGTP_Project_Primer/10_OPERATIONAL_REALITY.md`

### Session-to-Project bridge**: Not yet built — sessions cannot inherit project context
- support: 4 statements across 2 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### 15 SESSION_INSIGHT_RECORD ingestion deferred until ADR-045 and ADR-048 operational
- support: 4 statements across 2 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`

### The index file — a `KNOWLEDGE_INDEX.md` that maps all records by domain, sub-domain, and spine position — was identified as missing and important but not created.
- support: 4 statements across 2 document(s)
- nearest queue item 17 is only sim 0.51 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Temperature=0.0 fix | Opus 4.7 Migration | Migration was independent | Migration blocked by `cis_verify_semantic.py` parameter
- support: 4 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...TIONS/2026-04-29_operator_layer_pivot_and_pd5_governance.md`
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Loop:** Gap identified → ADR proposed → ADR locked → Gap resolved → Knowledge base updated → Future reviews reference resolved gap
- support: 4 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...hive_11_transitional_implementations_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Architectural Significance**: The execution layer is explicitly identified as the missing bridge between stream theory and actual runtime.
- support: 4 statements across 2 document(s)
- nearest queue item 12 is only sim 0.38 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### The Resolve button form was never built.** The backend route existed but the frontend form was missing — a feature gap from the monolith refactor that blocked session hygiene.
- support: 4 statements across 2 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Direct API routing to Claude/ChatGPT is deferred** - all model communication goes through Hermes Gateway.
- support: 4 statements across 2 document(s)
- nearest queue item 20 is only sim 0.44 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`
  - `PHASE_LOG.md`

### Phase 0 video work is entirely deferred** — No video preprocessing code will be written in Phase 0.
- support: 4 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...ession_insight_record_2026_04_22_001_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Session close → Post-commit work → Session close** — work done after close has no capture path, creating a circular gap
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.32 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`

### Blocked by:** Nothing (can proceed in parallel with other setup)
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`

### FAIL Placeholder detected: "TODO" found at line 47 of /path/to/file
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### No validation at entry**: File type is inferred from extension only; no content validation; no integrity verification against source
- support: 3 statements across 2 document(s)
- nearest queue item 17 is only sim 0.22 — treat as NEW
  - `...action/functional_intents/cis_intake_extraction_analysis.md`
  - `...raction/functional_intents/librarian_extraction_analysis.md`

### Notes** — promoted from single-line input to expandable textarea with descriptive placeholder
- support: 3 statements across 2 document(s)
- nearest queue item 22 is only sim 0.12 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`

### "CRITICAL: missing builder_model_id was not detected — "
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### Application Layer | Intelligence Layer incomplete | Intelligence Layer complete
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### DeepSeek (future) | Mediation | **NOT IMPLEMENTED** — planned but not built
- support: 3 statements across 2 document(s)
- nearest queue item 20 is only sim 0.29 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Field 5 FAIL Count Loop**: Incorrect FAIL count → fix deferred → known issue → future fix → correct scope
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.44 — treat as NEW
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### Transitional Gap Tracker**: Display of named transitional gaps and their resolution targets
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.21 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Gap**: No defined rules for what constitutes canonical vs.
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.26 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Mediation Gap**: The most significant architectural gap is the missing mediation automation — the Hermes agent must manually read script output and perform mediation.
- support: 3 statements across 2 document(s)
- nearest queue item 20 is only sim 0.44 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Missing Merge Stage**: OCR + visual extraction → structured synthesis → normalized record is missing, causing fragmented outputs and inconsistent record quality.
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### No project → capture feedback | Project context not used to guide capture | **MISSING**
- support: 3 statements across 2 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Status Vocabulary Separation**: Current coarse vocabulary (PRE-DRAFT / OPERATIONAL / LOCKED / NOT YET BUILT) must be separated into hierarchical implementation state (ADR overall vs.
- support: 3 statements across 2 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...traction/functional_intents/cis_live_extraction_analysis.md`
  - `CIS_Creative_Intelligence_System_v1/CIS_LIVE.md`

### After: vLLM zombie processes are a known issue with an identified root cause (missing port pre-check) and a planned fix (Step 3).
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0836_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-29_0836.md`

### Handoff package builder**: Not yet built (ADR-048 target)
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.22 — treat as NEW
  - `...ional_intents/10_operational_reality_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### Missing Runtime Bridge: Error Handling.** The session close sequence has no defined error handling.
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Live session panel** — Required before any build work (was missing, now fixed)
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_23_0139_extraction_analysis.md`

### The verification step gets triggered by Claude, not requested by you.** After any significant build action, Claude produces the manifest and immediately asks: "Run verification now or flag this as deferred?" Deferred items are tracked and surface at session start next time.
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`

### Video Pipeline Validation**: Frame sampling quality, transcription accuracy, vision extraction validation not implemented
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.17 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Knowledge Layer**: Blocked by missing index and semantic search
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.55 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Knowledge gap detection must exist before knowledge filling** — AI cannot fill gaps without identifying them first
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`
  - `...nctional_intents/x_00_operator_model_extraction_analysis.md`

### Gap**: Knowledge formation schema is not yet validated against real archive material
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Gap**: Knowledge object schema is not fully defined; it will emerge from drive audit.
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### No automation reduction included and no "NO AUTOMATION REDUCTION FOUND" statement | Contract violation — block treated as incomplete
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`
  - `contracts/CIS_Automation_Reduction_Contract_v1.md`

### Multi-Agent Orchestration**: Blocked by agent execution layer; cannot coordinate without agent roles and protocols
- support: 3 statements across 2 document(s)
- nearest queue item 12 is only sim 0.45 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Agent tab wiring**: Deferred — no orchestration for agent discovery
- support: 3 statements across 2 document(s)
- nearest queue item 21 is only sim 0.51 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### Implication**: Agent orchestration architecture must be designed but not implemented
- support: 3 statements across 2 document(s)
- nearest queue item 21 is only sim 0.47 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`

### Gap**: No automated validation of infrastructure configuration
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`

### This is a major architectural correction. The file reveals that the missing layer is not more model capability. The missing layer is **capture, verification, and promotion infrastructure** that allows intelligence work to become trustworthy system knowledge.
- support: 3 statements across 2 document(s)
- nearest queue item 22 is only sim 0.35 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_012_extraction_analysis.md:564`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Unresolved Orchestration: Session Initialization Orchestration
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### API decisions endpoint requires description field — batch curl commands must include it or they fail silently
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### The ADR panel sort/filter improvement (newest-first toggle, status filter buttons) was identified as useful, logged as a task in the dashboard, and explicitly deferred as not blocking build work.
- support: 3 statements across 2 document(s)
- nearest queue item 7 is only sim 0.30 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Summary of gaps: Schema files missing: source manifest, processing profile, review states, project object, segment Spec docs missing: everything — no contract has a written specification document
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### First: qwen_vl_utils appeared to be missing but was actually installed — the problem was that #!/usr/bin/env python3 picked up the system Python instead of the gpu-test Python.
- support: 3 statements across 2 document(s)
- nearest queue item 8 is only sim 0.27 — treat as NEW
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Step 1: Check verification_log.md for unresolved failures
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/api/session.py`

### Primary Discovery: The Human-as-API Gap is Now a Named Architectural Problem
- support: 3 statements across 2 document(s)
- nearest queue item 20 is only sim 0.33 — treat as NEW
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...nctional_intents/2_cis_reorientation_extraction_analysis.md`

### Phase 0-to-Phase 1 Bridge**: Missing contracts identified but not blocking; must be resolved before Phase 1 exits
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Old Tier 7 (node 8, "Full Durable Router Pipeline") remains DEFERRED permanently.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`
  - `proposals/POST_TIER10_PLANNING_REVIEWER_RESPONSE.md`

### The intake system is deliberately incomplete** — Phase 3 (Commit Layer) intentionally deferred.
- support: 3 statements across 2 document(s)
- nearest queue item 11 is only sim 0.30 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...nctional_intents/13_runtime_topology_extraction_analysis.md`

### It identifies the 15 SESSION_INSIGHT_RECORDs as deferred backlog, not implemented.** They remain identified/mapped/deferred, awaiting execution layer stability.
- support: 3 statements across 2 document(s)
- nearest queue item 15 is only sim 0.47 — treat as NEW
  - `...ional_intents/adr_048_scope_predraft_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`

### Draft panel | View/Edit/Approve/Reject/Supersede drafts | Not implemented | ADR-048 Phase 1
- support: 3 statements across 2 document(s)
- nearest queue item 5 is only sim 0.33 — treat as NEW
  - `...0047_11_transitional_implementations_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Not yet built**: Phase 3 (retrieval) is after Phase 2 (knowledge layer)
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.38 — treat as NEW
  - `...ession_insight_record_2026_04_16_001_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Chunked verification not implemented**: Large contract support missing
- support: 3 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`

### Multi-pass extraction is required for scaling**: Extraction quality on multi-figure covers is a known gap.
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.18 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### If `live_rounds` does not exist when the migration runs, the migration fails.
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`
  - `ADRs/ADR-041_Artifact_Registry_Schema.md`

### Pipeline pagination**: Blocked by current single-source operator design; needs list endpoint
- support: 3 statements across 2 document(s)
- nearest queue item 1 is only sim 0.34 — treat as NEW
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Session Archive Storage**: Resolved session storage format undefined; handoff persistence rules incomplete
- support: 3 statements across 2 document(s)
- nearest queue item 14 is only sim 0.28 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### States**: Generated, Under Review, Approved, Rejected, Deferred
- support: 3 statements across 2 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...primer_update_governance_contract_v1_extraction_analysis.md`

### Validation Rules**: Missing fields, hallucination, narrative drift, incorrect tagging, missing uncertainty = FAIL
- support: 3 statements across 2 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...s/cis_legacybuildfiles_consolidation_extraction_analysis.md`

### raise except ValueError as e: raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail=str(e) ) except Exception as e: logger.error(f"Error updating provider availability: {e}") raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update provider ava
- support: 3 statements across 2 document(s)
- nearest queue item 13 is only sim 0.17 — treat as NEW
  - `swa_project/social_work_ai/01_CORE/main.py#r0`
  - `swa_project/social_work_ai/01_CORE/main.py#r1`

### Dependency Impact**: runtime/manifests/ origin and status still unresolved — do not write there.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...on/functional_intents/07_known_risks_extraction_analysis.md`

### Discovery 2: Execution Layer as Missing Bridge
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Rule:** If interface allows material to enter without producing structured output, it is incomplete.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.25 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Register Slot 1 and Slot 2 in models table (ADR-024/025) — Slot 3 registration deferred
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.25 — treat as NEW
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-27_2152.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-28_0239.md`

### Constraint:** If a workflow step cannot be executed without explanation, it is incomplete.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Primary Discovery: The Human-As-Transport-Layer Gap is the Primary Architectural Problem
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.21 — treat as NEW
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### **Deferred because:** No reliable fetch target exists today.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:12`
  - `...reative_Intelligence_System_v1/memory_additions_20260420.md`

### Discovery 4: Resolve Button Never Existed (Architectural Gap)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Distributed execution (hardware constraint makes this out of scope)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`
  - `ADRs/ADR-045_Execution_Queue_Ownership_Layer.md`

### Status**: PRE-DRAFT (scope written, not yet built)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.47 — treat as NEW
  - `...intents/archive_04_active_components_extraction_analysis.md`
  - `...ve_06_foundational_control_contracts_extraction_analysis.md`

### And critical unresolved gaps are identified for the build plan.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Auto-fetch for model responses** (deferred — ADR-029)
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.21 — treat as NEW
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Concurrent Execution Attempt**: Blocked by design in early phases
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `...nctional_intents/deepseek_mcp_bridge_extraction_analysis.md`

### Missing Manifest**: Blocks preprocessing with exit code 1
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...on/functional_intents/cis_preprocess_extraction_analysis.md`
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`

### Fail**: Missing files, invalid JSON, incomplete fields, unreviewed
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...n/functional_intents/project_helpers_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

### Then run this to replace the broken line and add the missing content:
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Missing paths**: If TUTORIAL_ROOTS don't exist, scan silently skips
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### No validation layer exists to catch this before runtime.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Project interface**: Concept defined but not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Review Layer**: Blocked by missing review workflow
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...887271442881_x_cis_critical_addition_extraction_analysis.md`
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`

### Missing**: No explicit state transition validation (e.g., cannot go from `discovered` to `active` without intermediate states)
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `.../extraction/functional_intents/state_extraction_analysis.md`
  - `...extraction/functional_intents/models_extraction_analysis.md`

### The documentation loop is supposed to capture exactly this: real behavior reveals a gap → insight documented → plan updated → new direction locked.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### This is not implemented but is identified as highly relevant.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.25 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_002_extraction_analysis.md:366`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Unresolved Application Surface: Workbench First Screen
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.25 — treat as NEW
  - `...cybuildfiles_x_cis_critical_addition_extraction_analysis.md`
  - `...onal_intents/x_cis_critical_addition_extraction_analysis.md`

### Unresolved Routing:** Output distribution mechanism
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### No Validation Layer**: No automated validation of operations
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.19 — treat as NEW
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`
  - `...lender_2_80_fundamentals_transcripts_extraction_analysis.md`

### Video preprocessing in `cis_preprocess.py` — ffmpeg frame sampling plus Whisper transcription — was identified as the next build target but was not implemented.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.25 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### '− Cancel' : '+ Add Task' 1255: e('input', { type:'text', placeholder:'Task title', value:title, onChange:ev=>setTitle(ev.target.value) }) 1267: e('button', { className:'btn btn-primary', onClick:addTask, disabled:!title.trim() }, '+ Add') 1271: ?
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.20 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`

### 1 | FAIL — required markers missing, empty, malformed, or ambiguous
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### Cannot silently preserve contradictions—escalation is required.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.22 — treat as NEW
  - `...itutional_memory_governance_revision_extraction_analysis.md`
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Build Impact**: Application development deferred indefinitely.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Build Impact**: Daemonization is deferred — not a current build target
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`

### No business rule validation**: No validation of session content against business rules
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.23 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`
  - `...xtraction/functional_intents/session_extraction_analysis.md`

### CIS Live Dropdown Bug**: Logged to conflict register — deferred
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`

### This is not a minor gap — it is the single point of failure preventing the entire CIS system from becoming operational.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...ession_insight_record_2026_04_18_002_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Corrupt Manifests**: L2 fails if manifest is malformed or missing required fields
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`
  - `...tion/functional_intents/queue_worker_extraction_analysis.md`

### files_written Polymorphism**: Workaround in place, formal fix deferred
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Cross-reference validation**: No validation that draft doesn't conflict with existing canonical records
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.20 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### DAM Panel**: Blocked by undefined DAM object schema and missing asset management infrastructure.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### Dependency Impact**: All future operations depend on documentation that does not exist.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Dependency Impact**: Current implementation provides no substantive validation; real validation logic is missing
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Previously this gap was not explicitly identified as a blocking dependency.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Insight capture is a missing architectural layer**
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Gap Naming:** Each gap must be uniquely identifiable
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.25 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Draft Content Validation**: No validation of draft file format or content
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `.../functional_intents/primer_update_v3_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Execution bridge docs are the missing runtime layer.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...nd_offs_cis_handoff_current_position_extraction_analysis.md`

### Missing Feedback Loops**: The system has no correction, governance, retrieval-improvement, archive-learning, continuity/memory, or project-output feedback loops.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### First: ChatGPT's description of Claude Projects is partially outdated or incomplete.** The document it produced describes Projects as essentially a "big shared prompt folder" with no real indexing.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.31 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Gap**: Cold start recovery may imply retry logic, but not explicitly defined
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Gap**: No retention policy for CIS_LIVE.md versions
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.41 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`
  - `...xc_container_to_sandbox_the_cis_live_extraction_analysis.md`

### Gap**: Log location specified but format not fully defined
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Gap**: payload and result are unvalidated JSON strings
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.22 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Gap**: Manifest structure is assumed but not formally defined
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.23 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Gap**: No defined translation layer between operator interface actions and runtime commands
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`

### Gap**: No document exists that makes explicit how all other docs relate and how changes propagate.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.28 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### ADR-008 and ADR-010 are missing from the display — they were logged but the harness shows gaps in the sequence.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### Gap**: No notification system for processing completion
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap**: No queue management logic (polling, priority sorting, worker assignment)
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Gap**: No tracking of how often models are used or their success rates
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap**: No validation of lifecycle state transitions
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Gap:** No validation of file paths, command strings, or timeout values
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...xtraction/functional_intents/helpers_extraction_analysis.md`

### Missing Queue Worker**: The most critical gap - jobs are enqueued but no worker exists to process them.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Gap**: Workbench requirements are identified but not defined
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Gap:** No convention for file paths or directory structure
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.25 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...xtraction/functional_intents/helpers_extraction_analysis.md`

### Gap:** Validation is required but validation rules are not defined.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.25 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Human Review**: Required when validation fails, ambiguity unresolved, retries exhausted
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...s/cis_legacybuildfiles_consolidation_extraction_analysis.md`
  - `...s_cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Preprocessing incomplete**: Intelligence cannot operate on raw sources
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...nal_intents/x_06_intelligence_stream_extraction_analysis.md`
  - `...ybuildfiles_x_06_intelligence_stream_extraction_analysis.md`

### Intake Validation**: No validation for staged content before approval
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Invalid JSON**: Missing or malformed request body causes 400
- support: 2 statements across 2 document(s)
- nearest queue item 19 is only sim 0.31 — treat as NEW
  - `...extraction/functional_intents/models_extraction_analysis.md`
  - `...traction/functional_intents/captures_extraction_analysis.md`

### *DRAFT status: This document is a Hermes-generated proposal. It does not represent an Eric-approved decision. Items classified as Deferred-unscheduled are NOT cancelled — they await scheduling by Eric after external advisor review.*
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.47 — treat as NEW
  - `PLAN_RECONCILIATION.md`
  - `PLAN_RECONCILIATION.md:31`

### Runtime Manifest Validation** — No validation layer for runtime manifest operations
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.19 — treat as NEW
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Lifecycle**: Defined at capability level; implementation deferred
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ction/functional_intents/x_02_memory_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`

### Manifest Namespace Objects**: Three classes defined but namespace separation not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.20 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`

### Unresolved Application Surface: Progress Monitoring
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`

### Missing Intel sidebar wiring**: LOCAL tab not yet connected to live model data
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Missing Runtime Bridge: Application ↔ Runtime State Synchronization
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...06278530365342_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Missing Runtime Bridge: STATE.md ↔ Phase Definitions
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Current State**: Execution bridge is missing, making stream docs incomplete.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.48 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

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

### Missing optional fields represented as `null` consistently (never omit a known field).
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### Model registry validation | No validation for model data | MEDIUM — will be needed
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.21 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Non-standard filename handling**: Not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`
  - `...ntents/automation_discussion_chatgtp_extraction_analysis.md`

### None detected**: No validation feedback that corrects user input
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.22 — treat as NEW
  - `...ion/functional_intents/ingest_spines_extraction_analysis.md`
  - `...xtraction/functional_intents/app_api_extraction_analysis.md`

### Output validation | Not defined | Quality control incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...e_system_legacybuildfiles_x_03_state_extraction_analysis.md`

### Response Validation** — No validation that pasted responses are from actual models
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.16 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### Pie Menu System**: Blocked by UI system and hotkey hold detection
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.21 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### Update Validation**: No validation that SCP transfer was successful
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.21 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Remote GUI access (Parsec/Moonlight) is deferred until after pipeline validation.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...ative Intelligence System (CIS)/cis_system_bundle/MEMORY.md`
  - `...ystem (CIS)/cis_system_bundle/Handoff_Summary_03_31_2026.md`

### Build Impact**: Adds significant UI complexity; must be deferred to later versions
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `...onal_intents/x_10_application_stream_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Manifest Storage**: runtime/manifests/ status unresolved
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.21 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Section 6 (Next Actions) depends solely on `build_plan_nodes WHERE status IN ('PENDING','IN_PROGRESS')` — empty when all nodes are COMPLETE/DEFERRED
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.46 — treat as NEW
  - `DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md`
  - `PROPOSAL_SESSION_TO_SPINE_WRITE_PATH.md`

### Slot 3 registration intentionally deferred — Qwen3.6-27B is a stronger architectural fit for CIS multimodal routing needs but requires real performance comparison before committing
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `cis_v1_vault/Phase_PD/CIS_Handoff_2026-04-27_2152.md`

### Snapping System**: Blocked by geometry query system and transformation system
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### States**: Downloaded, Evaluated, Registered, Operational, Deferred.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### States**: Initializing, Ready, Incomplete, Failed, Active, Closed
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

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
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...les_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Title handling | Project Initiation | Generate working title if missing
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.21 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Unresolved FAILs: 0 this session (41 shown is cumulative — no build actions taken)
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-01_0548.md`

### Input Validation**: No validation of user messages or session fields
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.24 — treat as NEW
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`
  - `...xtraction/functional_intents/live_db_extraction_analysis.md`

### View Layer System**: Blocked by render engine and collection system
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.25 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

### Workbench Application**: Not implemented as software
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...unctional_intents/cis_manual_mode_v1_extraction_analysis.md`

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

### Architectural Significance**: vLLM Slot 1 requires manual start each session; port pre-check fixed but daemonization incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`

### ADR-021 and ADR-023 were the original build targets and were not implemented this session.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Any session that started without the addendum silently lost the post-commit work.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### This meant decisions from any session that ended without the operator manually running SQL were silently lost.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Architectural Significance**: The root cause of recurring context and orientation loss is NOT missing features but a missing execution layer.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-04-28_0553.md`

### ADR candidate 4 — Notes field definition The Notes field in session close is defined with specific qualifying criteria: pending decisions, warnings, gotchas, partially built work, deferred context.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_011.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_012.md`

### Decision:** The Notes field in session close captures: deferred decisions, warnings, gotchas, and mid-thought work.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.37 — treat as NEW
  - `...n_execution_and_image_pipeline_setup_extraction_analysis.md`
  - `CIS_Creative_Intelligence_System_v1/Phase_PD/ADRs.md`

### Handoff File Overwrite**: The handoff file is overwritten on each session close, creating a risk of data loss if the close sequence fails silently.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.29 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`

### Memory Rule: keep decisions, rationale, deferred ideas; do not keep transient errors, repeated explanations
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.33 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...ents/1776105425887825149_x_02_memory_extraction_analysis.md`

### Memory is project-scoped.** Cross-project memory sharing does not exist.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Missing Validation Layer: Memory Validation**: The rules for validating the structure and content of the memory file are not fully defined.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.37 — treat as NEW
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Runtime Impact**: Without ingestion, each session starts with incomplete context.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.43 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### What's missing is something between a handoff and an ADR — a **branch note**.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.32 — treat as NEW
  - `...63_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### After:** The **branch note** concept fills this gap — three fields (Branched from, Why, Return point) captured as a CIS Live round at the moment of deviation.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.29 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Discovery 4: Institutional Memory Integration Gap
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `...al_intents/archive_08_open_questions_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Missing Handoff File**: Human must attach file at session start.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`

### Unresolved**: Live session is not resolved (current state of #020)
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`

### Governance Gaps**: The memory store has no access control, no audit trail, no validation, no deletion capability, and no lifecycle management.
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.39 — treat as NEW
  - `...tion/functional_intents/memory_store_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Handoff Layer**: Blocked by session close writing to wrong location
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### L2 Context Constraint Validation** — No validation for files exceeding context limit
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.22 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Memory Claim Validation Layer:** No validation of memory capability descriptions
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.35 — treat as NEW
  - `...85_2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Automated Session Close**: Blocked by manual CIS Live resolution requirement
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Missing Project Context**: All modules fail if no active project context
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...cybuildfiles_x_10_application_stream_extraction_analysis.md`
  - `...onal_intents/x_10_application_stream_extraction_analysis.md`

### Session close fix**: Blocked by reorganization (handoff folder must exist).
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Runtime Impact**: If folder is missing, session close fails — no fallback path defined
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`

### Whether the runtime code (/mnt/projects/cis/runtime/) had a git repo initialized at the time of this session was explicitly flagged as uncertain — "if initialized — verify with git status." This uncertainty about whether the code was version-controlled is a significant gap that was never formally cl
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_17_002_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Validation**: Must be called before session close if unresolved conflicts exist
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Session→Resolution→Handoff→Reorientation**: Continuity maintained through structured handoffs; unresolved sessions break continuity
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### The memory system was described as having "locking" functionality that does not exist.
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.27 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### The `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` flag must be permanently added to the gpu-test activation script.** It has been an unresolved note across every session.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### Unresolved Application Surface: Memory Search**: The application interface for searching the memory file is not defined.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `...extraction/functional_intents/memory_extraction_analysis.md`
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Session Fail**: Unresolved → block archive; no handoff → block close
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.25 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`

### Verification Layer**: Large contract verification blocked by context window limit
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### The differing knowledge record between /mnt/projects/cis/knowledge/records/ and the Obsidian vault copy was identified and deferred.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### The actual knowledge records table does not exist in this DB yet, which means `knowledge_records` is stored as files on disk (`record_001.json`) but has not been migrated into the SQLite DB as a table.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Agents blocked by lack of validated knowledge and workflow context.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.42 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`

### Knowledge scaling is blocked by review/promotion UI.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### Missing**: No validation that search results are relevant
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.44 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### Now let me document the future features before building.Searched project for “future features deferred decisions memory”Searched project for “future features deferred decisions memory”Good — the Memory doc is the right place.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `_archive/Refactoring CIS application into modular structure.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_008.md`

### Gap Knowledge:** Identified gaps become knowledge artifacts for future reviews
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Unresolved Storage Rules: Knowledge Object Lifecycle
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.31 — treat as NEW
  - `...gacybuildfiles_x_cis_runtime_spec_v1_extraction_analysis.md`
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Knowledge record storage** — naming convention defined but storage hierarchy incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### Index must be complete for reliable retrieval | Incomplete index degrades retrieval
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.45 — treat as NEW
  - `..._intents/hermes_objectives_v1_claude_extraction_analysis.md`
  - `...ctional_intents/15_inheritance_index_extraction_analysis.md`

### Fields in the real record that are missing from knowledge_v1.json: record_id, record_type, source_name, source_unit, knowledge_category, subject, tags, summary, visible_text, scene_description, layout_description, mood_style, uncertainty, retrieval_text, project_title, active_stages, source_origin, 
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_016.md`

### Gap**: Need automatic session type detection and routing
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Gap**: Records must be in source-contained directories, but no specific storage rules defined.
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.30 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### Gap:** Interface must move material toward structured knowledge but validation is not implemented.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### - "Embedded governance" is a Build Plan v2 philosophical target. The creator should eventually experience trust and continuity — not visible constitutional machinery. Governance should become ambient, not explicit.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.30 — treat as NEW
  - `...2_constitutional_memory_governance_primer_rewrite.md:17`
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### The CIS architecture has a missing layer between the Application Layer and the Knowledge Layer: the **Session Initialization Layer**.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Insight → Knowledge formation bridge not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `...ional_intents/x_cis_relationship_map_extraction_analysis.md`

### SESSION_INSIGHT_RECORD Loop**: Identified → not ingested → knowledge gap → ingestion needed
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.48 — treat as NEW
  - `...intents/20260502_0047_07_known_risks_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Validation not implemented** → Bad records pass through → Knowledge layer contaminated
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`
  - `...an_update_pack_organized_by_document_extraction_analysis.md`

### Retrieval-Improvement Loop 1: Knowledge Gap → Challenge → Fill Gaps → Knowledge Base Update
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...legacybuildfiles_x_00_operator_model_extraction_analysis.md`

### Knowledge Tier Validation**: No validation for tier classification
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...818091549056_x_10_application_stream_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### Knowledge Validation**: No validation of knowledge structures
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `...5867256194704735_cis_handoff_phase_d_extraction_analysis.md`
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Knowledge record validation | Not defined | Quality control incomplete
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Knowledge retrieval validation**: No validation for retrieval queries
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.46 — treat as NEW
  - `.../functional_intents/mnt_projects_cis_extraction_analysis.md`
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### 5. **Missing Governance Infrastructure**: The file reveals significant gaps in governance (no override mechanisms, no escalation paths, no audit trails) that must be addressed before implementation.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.37 — treat as NEW
  - `...al_intents/moved_requirements_extraction_analysis.md#r5`
  - `...extraction/functional_intents/record_extraction_analysis.md`

### Missing Validation Layers: Schema Validation.** There is no schema validation for the knowledge records or the manifest files.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Missing project context**: Agents cannot operate without project_id, stage, knowledge.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.46 — treat as NEW
  - `...775927554123130009_x_09_agent_stream_extraction_analysis.md`
  - `...functional_intents/x_09_agent_stream_extraction_analysis.md`

### Not implemented**: No mechanism to improve retrieval based on usage patterns.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.45 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Not yet defined — deferred until retrieval system is built
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.37 — treat as NEW
  - `...chat_2026_04_003_extraction_analysis_extraction_analysis.md`
  - `...s_cis_legacybuildfiles_consolidation_extraction_analysis.md`

### Storage implications**: Must be versioned; existing records never silently overwritten; retrieval priority by state
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.37 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### ChatGPT architectural insight captured in CIS Live #034 — governed state registry, drift detection, and phase-aware status taxonomy deferred to build plan rewrite
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-05_0323.md`
  - `...ects/PROJECT__CIS__BUILD__V1/CIS_Handoff_2026-05-05_0427.md`

### Swarm/multi-agent orchestration** — deferred until single-role agents are stable; prerequisites are stable knowledge layer, reliable retrieval, consistent workflow structure, controlled intelligence execution
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.43 — treat as NEW
  - `...s_cis_legacybuildfiles_consolidation_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Drift Detection, Phase-Aware Status, and Inheritance Integrity are Unified**: These three capabilities are expressions of the same missing layer (State Registry), not separate concerns.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...traction/functional_intents/cis_live_extraction_analysis.md`
  - `CIS_Creative_Intelligence_System_v1/CIS_LIVE.md`

### Intake Ownership Layer** — [DEFERRED → PRIMARY TARGET] Previously deferred, now identified as the missing architectural layer.
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.29 — treat as NEW
  - `.../2026-04-30_primer_stabilization_and_intake_architecture.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`

### Missing**: No mechanism to communicate *why* failure occurred to pipeline orchestrator beyond log
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`
  - `...onal_intents/x_cis_critical_addition_extraction_analysis.md`

### Agents (librarian, researcher, teacher, producer, guardrail, worker, orchestrator) are explicitly deferred until foundational layers (1-5) are stable.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.45 — treat as NEW
  - `...25538460345839_x_01_system_blueprint_extraction_analysis.md`
  - `...reative_Intelligence_System_LegacyBuildFiles/X_02_MEMORY.md`

### Architectural Significance**: Manual paste confirmed as input method; auto-fetch permanently deferred
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Draft Intake**: Still using human copy-paste, ADR-048 Staged Draft Intake not yet built
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`

### This is a fundamental topology gap where AI-generated structured content cannot reach CIS canonical records without human mediation.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.33 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### No Hallucination Detection**: No validation of AI model outputs
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.19 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### Gap:** No defined error handling in orchestration
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...08333796114_x_05_core_tool_stream_md_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### I correctly identified the three missing components: pipeline state table, orchestrator script, approval queue panel.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...ntents/phase_0_5_replan_orchestrator_extraction_analysis.md`
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### Later: CIS Live rounds can auto-detect “conflict/deferred” tags and log them automatically.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...st_try/insights_First_Try/_Automation_Discussion_ChatGTP.md`
  - `ADRs/ADR-048_SCOPE_PREDRAFT.md`

### Missing Orchestration: Application Layer Loading
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...tents/1776042143355379182_x_03_state_extraction_analysis.md`

### Missing Validation Layer: Pre-Snapshot Validation Automation
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.20 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`
  - `...cybuildfiles_x_cis_critical_addition_extraction_analysis.md`

### No Multi-Step Pipeline Orchestration**: Out of scope (ADR-043 scope)
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._045_execution_queue_ownership_layer_extraction_analysis.md`
  - `...nts/x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### No hallucination controls**: No validation of extraction outputs beyond human review
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.21 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `..._legacybuildfiles_x_cis_workbench_v1_extraction_analysis.md`

### No runtime bridges, undefined objects, unstable schemas, or unresolved orchestration
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...nctional_intents/cis_handoff_phase_d_extraction_analysis.md`
  - `...xtraction/functional_intents/read_me_extraction_analysis.md`

### Description**: If any pipeline component is missing, intake blocks.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...onal_intents/x_cis_critical_addition_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Unresolved Orchestration**: Domain accumulation orchestration, feedback loop orchestration.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.23 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Unresolved Orchestration:** Handoff automation or manual trigger
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.21 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Unresolved gaps and missing layers across all architectural domains
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Low effort feature deferred to next Live panel iteration.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_006.md`

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

### Dashboard Panel Additions:** Blocked by frontend modularization ADR
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.17 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`

### Gap:** `cis_review.py` exists but has no dashboard trigger
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ntents/cis_handoff_dashboard_session_extraction_analysis.md`

### Dashboard HTML Refactor Governance**: Deferred; no governance defined
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.21 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Application growth | Frontend monolith risk + missing transcript/governance surfaces
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.21 — treat as NEW
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Dashboard HTML refactor | Deferred to dedicated session | Not scheduled
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.22 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### Dependency Impact**: LivePanel rendering depends on clean form strip removal; no validation gate exists for post-removal syntax integrity.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.15 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`

### Final plan acceptance | state = awaiting_approval after full plan elaboration | Complete Build Plan v2, verification summary, open questions
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.44 — treat as NEW
  - `...ents/cis_execution_layer_contract_v1_extraction_analysis.md`
  - `contracts/CIS_Execution_Layer_Contract_v1.md`

### Gap**: Specific interface panels and their behavior are not defined.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### LivePanel Syntax Validation**: No validation gate before LivePanel deployment.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`

### Phase 1 routing (route_task.py)**: Not started — blocked by Qwen weights and registry stability
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.48 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### Session close panel**: No validation that all fields are filled before commit.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Session panel | Initialize session | Not implemented
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Structure Proposal Panel** - Shows detected, uncertain, and missing structure
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `...gacybuildfiles_x_cis_discovery_model_extraction_analysis.md`
  - `...tional_intents/x_cis_discovery_model_extraction_analysis.md`

### The model registry work to make them functional was deferred to ADR-024/025, which was still not implemented at this point.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### This means ADR-032 needs to define the full domain taxonomy including Home/Body/Mind, and note that creative production domains are built first with life management domains deferred to a later phase.
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.21 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Also need to check — ADR-008 and ADR-009 exist but there's no ADR-008 gap issue since the DB shows them both present.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Blocked by: nothing — can be drafted in parallel with ADR-045 completion.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.38 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `ADRs/ADR-047_SCOPE_PREDRAFT.md`

### Here is what is missing from the contract that would prevent this from happening again:
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...-24_CIS phase 1 intelligence extraction handoff.md:1595`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Execution jobs table** (defined but not implemented — ADR-045)
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.21 — treat as NEW
  - `...hive/orientation_backups_20260430/10_OPERATIONAL_REALITY.md`
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`

### No Governance**: The capture pipeline has zero governance — no validation, no provenance tracking, no hallucination detection, no review gates.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.28 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Governance Layer** — blocked by decision logging form
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.22 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Purpose**: Track discovered contradictions, filesystem conflicts, naming collisions, stale documentation, deferred bugs, and governance/runtime mismatches
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.35 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`
  - `CIS_CONFLICT_REGISTER.md`

### 2 | Missing contract specs or explicit deferral reasons | Governance completeness
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### ADR Generation Layer**: Blocked by ADR Numbering System
- support: 2 statements across 2 document(s)
- nearest queue item 19 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`

### Intelligence wiring | Intel sidebar tabs not wired | Blocked by ADR-024/025
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`

### ADR-044 (Operator Abstraction) and ADR-045 (Execution Ownership) are now closed, making ADR-048 the sole remaining gap in the abstraction chain.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`

### ADR-048 must be locked before any new intake work begins.** ADR-045 closure makes this the sole remaining gap.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.25 — treat as NEW
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Dependency Impact**: Blocked until ADR-045 fully closed; no implementation allowed
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### FAIL:** "FAIL: Proposal section missing", "FAIL: Proposal missing ### Summary", "FAIL: Proposal missing ### Recommendation", "FAIL: Proposal ### Summary empty", or "FAIL: Proposal ### Recommendation empty"
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md`
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### Transitional Gap Governance Loop**: Named gap → target resolution → gap resolved → reduction implemented
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Gap:** No governance for work done after commit
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### The missing bridge is the contract register that shows which expected contracts exist, which are missing, and which implementations were built without the contract-first discipline.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.23 — treat as NEW
  - `...chat_2026_04_016_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Record promotion governance**: No validation that records meet quality thresholds before promotion.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`
  - `...tents/2026_04_17_hand_off_evaluation_extraction_analysis.md`

### runtime/manifests/**: Unknown ownership, may be deprecated — creates governance gap
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### CIS_LIVE Auto-fetch Permanently Deferred**: Major models (Claude, Gemini, ChatGPT) do not expose stable public share URLs suitable for programmatic fetch.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Architectural Significance:** A result is invalid if: required fields missing, unsupported claims present, schema broken, uncertainty not expressed.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.36 — treat as NEW
  - `...06484714234540_x_cis_execution_layer_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Build Impact**: Highest priority build target above cis_spine_intake.py and missing contract specification documents
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.30 — treat as NEW
  - `...egrated_vision_cis_core_architecture_extraction_analysis.md`
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Dependency Impact**: Fresh DB deployments will fail silently — models table missing breaks all downstream services.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### Gap**: `project_id` is a field, not a storage partition
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Missing DB file**: Migration exits with error code 2
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`

### No retry logic**: If database write fails, it's silently skipped
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...action/functional_intents/cis_review_extraction_analysis.md`
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### ADR implementations**: Blocked by DB schema check (must check before ADR-021).
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### Description**: No validation that parsed data conforms to expected schema.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.34 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`

### ensure_models_table**: Not wired into ensure_tables(conn) — schema auto-creation is broken
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### The architecture reveals significant gaps** - undefined schemas, missing bridges, unresolved routing, unstable governance
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `...tional_intents/x_cis_execution_layer_extraction_analysis.md`

### Good catch. The path I stated was wrong — the actual schemas folder is at:
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.31 — treat as NEW
  - `...at_transcripts/2026-04-23_Starting a new session.md:614`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Invalid outputs**: required fields missing, unsupported claims present, schema broken, uncertainty not expressed where needed
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.37 — treat as NEW
  - `...gacybuildfiles_x_cis_execution_layer_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### LIFE domain spines are deferred until at least one CREATION domain pipeline is operational end-to-end.
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.28 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Storage Implications**: Logged to database; unresolved sessions block next build
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`

### Spine Ingestion Pipeline**: The `cis_spine_intake.py` script does not exist yet.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.51 — treat as NEW
  - `...egrated_vision_cis_core_architecture_extraction_analysis.md`
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Missing Manifest**: Blocks verification entirely.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...s/cis_verification_layer_contract_v1_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`

### Storage Implications**: Missing record blocks verification same as missing Completion Manifest
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.34 — treat as NEW
  - `...ChatGTP_Project_Primer/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`
  - `...tional_intents/12_contract_authority_extraction_analysis.md`

### Placeholder check: No TODO, ..., or placeholder strings present in contract.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.24 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`

### cis_vllm_slot1.sh port pre-check gap: zombie processes possible
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `...hive/orientation_backups_20260430/10_OPERATIONAL_REALITY.md`
  - `_archive/orientation_backups_20260430/01_CURRENT_STATE.md`

### States**: Required, Missing (blocks verification)
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `...tional_intents/12_contract_authority_extraction_analysis.md`
  - `...ts/06_foundational_control_contracts_extraction_analysis.md`

### Verification Trust:** Blocked by ADR-047 resolution
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ion/functional_intents/03_system_map_extraction_analysis.md`
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### Verification chain**: catches incomplete/incorrect artifacts
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.41 — treat as NEW
  - `...l/extraction/functional_intents/adrs_extraction_analysis.md`
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Architectural Significance**: The execution layer (headless runtime) does not exist in unified form.
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.21 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### Extraction quality on multi-figure comic covers is a known gap — do not scale ingestion until multi-pass is proven in Phase 1
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.18 — treat as NEW
  - `..._intents/cis_handoff_2026_04_23_0434_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_003.md`

### Architectural Significance:** Multiple close attempts created duplicate session rows, encountered a missing `Path` import, and exposed possible Git push/handoff completion uncertainty.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.41 — treat as NEW
  - `...chat_2026_04_006_extraction_analysis_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### Architectural Significance:** The session identifies a gap between application UI and execution reality.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`
  - `...chat_2026_04_006_extraction_analysis_extraction_analysis.md`

### The session start script (`cis-start`) becomes a gate, not just an orientation tool.** It checks for unresolved verification failures from the last session before presenting the reorientation context.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.32 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`
  - `...pts/2026-04-25_Verification mechanism for completed work.md`

### Purpose**: Canonical conflict tracking mechanism for unresolved architectural conflicts
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### process and architecture are still likely the deeper issue, but the model evaluation remains incomplete because the system has not yet been instrumented **during** inference.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...orm Chat/vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md`
  - `...vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md:1801`

### Architectural Significance:** The session close protocol has a fundamental gap — work performed after commit has no capture path to any endpoint (DB, ADRs, knowledge records, system log)
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ents/post_commit_addendum_2026_04_18_extraction_analysis.md`

### The second direction change was the decision to defer video entirely from Phase 0. Rather than partially implement video support with a known-flawed segmentation method, the session concluded that video is Phase 1 work and Phase 0 should exit cleanly on static images only. This was the correct call.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...aec072e4:CIS phase 1 intelligence extraction handoff#r6`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Architectural Significance:** The `local`, `remote`, `agent` tabs in the right sidebar are currently hardcoded model cards (lines 2484-2492) and NOT wired to anything.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.34 — treat as NEW
  - `...ts_2026_04_22_cis_build_continuation_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

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

### LIFE domains are deferred but their design is now part of the canonical architecture.
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.21 — treat as NEW
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Storage validation**: No validation that all drives are mounted.
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.34 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### The Execution Layer is the missing foundational layer that makes everything else real.**
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`
  - `...rst_try/insights_First_Try/Phase 0.5 Replan Orchestrator.md`

### This represents a significant knowledge gap that may contain architectural decisions, constraints, or requirements.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_26_1714_extraction_analysis.md`

### The eventual application layer that exposes CIS capabilities to other users is Phase 5 and was explicitly out of scope for this phase.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Everything else that was supposed to be a contract document from the roadmap — source manifest, processing profile, review states — does not exist as a file on disk.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...76_2026_04_23_starting_a_new_session_extraction_analysis.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`

### Application development** — deferred until Phase 0–4 exit criteria are met; building the app before the runtime is premature regardless of how ready it feels
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...e_atlas/cis_canonical_build_sequence_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Commit validation**: Phase 3 deferred - no commit validation layer
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Run the .tables check and paste the result.You said: How will you know when to add Frame-level data (deferred — not needed for Phase 1) to the table?How will you know when to add Frame-level data (deferred — not needed for Phase 1) to the table?Apr 23Claude responded: You will tell me.You will tell 
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.19 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_002.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### What's missing from Phase 0 exit criteria: **10–20 records from real archive material in draft state.** The commands exist but haven't been run on real archive files at scale yet.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `...transcripts/2026-04-22_Model registry API implementation.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### ADR-048 Phase 3**: Not yet started, blocked by build plan rewrite
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Planned**: Draft panel (ADR-048 Phase 3) — NOT YET BUILT
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`
  - `...s/20260505_0058_04_active_components_extraction_analysis.md`

### Intake ownership stabilization (ADR-048) — COMPLETE (Phase 3 deferred by design)
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.20 — treat as NEW
  - `..._transcripts/ChatGTP_Project_Primer/02_NEXT_BUILD_TARGET.md`
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Check the runtime manifests folder — that's likely where the manifest template or spec lives: bashls /mnt/projects/cis/runtime/manifests/ The "missing Phase 0 contracts" task from the handoff may mean the spec documents describing the rules — not the manifests themselves, which already exist.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_001.md`

### The Sound Stream file was retrieved in that search, which means it was indexed and available — I just did not draw from it heavily in the roadmap because Sound is a deferred domain that does not affect build order for the infrastructure phases.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Phase 0 is incomplete**: A sixth command (cis_review.py) is required to complete the pipeline
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0710_extraction_analysis.md`
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`

### ADR-048 Phase 3 is intentionally deferred because the ingest/draft pipeline boundary must be preserved.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Draft → Approved → Committed**: Phase 3 (commit) intentionally deferred
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Commit Object:** Not yet defined (Phase 3 deferred)
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Frame-level data deferred until Phase 1 extraction proves insufficiency.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...nts/cis_handoff_2026_04_23_0434_chat_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Lifecycle**: Phase 1 (OPERATIONAL), Phase 2 (OPERATIONAL), Phase 3 (DEFERRED)
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Phase 1 (Intelligence Extraction)**: Blocked by Phase 0 exit criteria — 10-20 draft knowledge records from real archive material
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`
  - `...uence_and_architectural_dependencies_extraction_analysis.md`

### What CIS is missing is the index file, backlinks, linting, session end hook, and daily flush process.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

### The segmentation thresholds, merge floor, and quality gate criteria mentioned in ADR-031's rationale were deferred explicitly to ADR-033, which was not written this session.
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.36 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### ADR-033 is deferred** until both spine ingestion and segmentation are proven — segmentation policy cannot be locked without operational experience.
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Dependency Impact**: Without persistent memory, system cannot enforce contract-first discipline across sessions
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.23 — treat as NEW
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`
  - `...ure_atlas/original_CISChats/CIS_Canonical_Build_Sequence.md`

### Gap**: No defined retention policy for extraction files
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.44 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### *What this enables:* The system cannot produce invalid outputs. Every object in the system has a documented, enforced history of what happened to it.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.28 — treat as NEW
  - `...Chats/CIS_Canonical_Build_Sequence_Plain_Language.md:43`
  - `...extraction/functional_intents/memory_extraction_analysis.md`

### This analysis is what triggered the recognition in subsequent sessions that session transcript extraction is the missing capability — the "session end hook" Karpathy describes is exactly what the current extraction work is building.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.38 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`
  - `...se_1_intelligence_extraction_handoff_extraction_analysis.md`

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

### ### Object 1: "Capability" - **Description**: What constitutes a "critical capability" is undefined - **Impact**: Cannot enforce primary + fallback requirement without capability definition - **Required**: Capability taxonomy, criticality criteria, mapping to tools ### Object
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...ents/x_05_core_tool_stream_md_extraction_analysis.md#r4`
  - `...nal_intents/x_05_core_tool_stream_md_extraction_analysis.md`

### Session Authority**: Resolution enforced before archive; unresolved sessions create governance violations
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### No implementation without Eric approval (Eric Gate).
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.39 — treat as NEW
  - `CIS_EXTERNAL_ADVISOR_BRIEFING_2026-06-25.md`
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Status Values**: Documented but not enforced by SQLite CHECK constraint
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `...ional_intents/migrate_execution_jobs_extraction_analysis.md`
  - `cis_v1_vault/runtime_scripts/runtime/migrate_execution_jobs.py`

### Discovery 6: Ingestion Pipeline Lacks Merge Stage (Critical Gap)
- support: 2 statements across 2 document(s)
- nearest queue item 11 is only sim 0.28 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `...em_LegacyBuildFiles/_CIS_The pattern across the CIS docs.md`

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

### Gap**: The extraction pipeline is described but not defined as a system object
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Three missing capture systems block intelligence.** Decision logging form, extraction run logging table, and review/promotion UI must exist before intelligence extraction can begin.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`

### After this file, 15 SESSION_INSIGHT_RECORDs are identified as not ingested, creating an institutional memory gap.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.41 — treat as NEW
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Archive Ingestion Layer**: Blocked by NTFS format; requires NTFS compatibility resolution
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`
  - `..._intents/cis_handoff_2026_04_22_0410_extraction_analysis.md`

### Dependency Impact**: Session close depends on `from pathlib import Path` which was missing.
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.44 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap Chunking**: Each gap is a chunk with fields: subsystem, gap_description, target_resolution
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.22 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Gap**: No minimum quality threshold for extraction
- support: 2 statements across 2 document(s)
- nearest queue item 3 is only sim 0.30 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Loop: extract → review → gap identification → prompt tuning → re-extract → improved quality.
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.27 — treat as NEW
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Missing Runtime Bridge:** **Transcript-to-Distillation Bridge** - There is no defined mechanism for how a raw transcript is transformed into a structured distillation.
- support: 2 statements across 2 document(s)
- nearest queue item 1 is only sim 0.25 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`
  - `...l_intents/1777410199041831732_readme_extraction_analysis.md`

### Spine Ingestion Validation**: Not implemented — pipeline is designed but not built
- support: 2 statements across 2 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...ession_insight_record_2026_04_23_001_extraction_analysis.md`
  - `claude_chat_transcripts/2026-04-23_Starting a new session.md`

### Two active entries exist (ADR auto-increment reset, CIS Live rounds session dropdown bug), both DEFERRED/LOW.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`
  - `...transcripts/ChatGTP_Project_Primer/Current State Updated.md`

### Empty Round 4 from "Rounds in Right Sidebar" will be silently dropped from the markdown output
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.25 — treat as NEW
  - `...04-20_Refactoring CIS application into modular structure.md`
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Missing archive audit**: System cannot be grounded in reality
- support: 2 statements across 2 document(s)
- nearest queue item 7 is only sim 0.32 — treat as NEW
  - `...9471060_cis_handoff_current_position_extraction_analysis.md`
  - `...acybuildfiles_x_cis_relationship_map_extraction_analysis.md`

### No stage validation**: Pipeline stages can be triggered in any order, with no validation that prerequisites are met.
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.18 — treat as NEW
  - `...traction/functional_intents/pipeline_extraction_analysis.md`
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Missing `system_log.md`**: The system log file did not exist and was not being written to by pipeline commands.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.31 — treat as NEW
  - `...10811_2026_04_17_hand_off_evaluation_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`

### Pipeline stages blocked by state machine**: Cannot implement pipeline stages without state machine
- support: 2 statements across 2 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...intents/cis_source_manifest_contract_extraction_analysis.md`
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

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

### Gap**: No defined dashboard for monitoring pipeline status
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`
  - `...ts/cis_pre_development_system_gemini_extraction_analysis.md`

### Modifier Stack**: Blocked by mesh data system and execution pipeline
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...2_80_fundamentals_transcripts_copy_2_extraction_analysis.md`
  - `...r_2_80_fundamentals_transcripts_copy_extraction_analysis.md`

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

### Filesystem Governance Layer:** Blocked until ADR-047 is locked (which is blocked by ADR-048).
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.30 — treat as NEW
  - `...nal_intents/archive_01_current_state_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Filesystem governance is a recognized gap** that blocks canonicality
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.23 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Unresolved Storage Rules: Handoff Storage**: The handoff document has a dual storage path (VM disk vs.
- support: 2 statements across 2 document(s)
- nearest queue item 18 is only sim 0.36 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Add or defer processing profile override with explicit gap note.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Missing FINAL_JSON | Repair prompt, then fallback text scanning | Model produces analysis but no machine-parseable verdict
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `CIS_16_FAILURE_MODES.md`
  - `DEV-PIVOT-05_HERMES_INTEGRATION_ASSESSMENT.md`

### Agent Layer**: Blocked by missing governance and upstream dependencies
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.44 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### The selectors in v2 (`textarea[placeholder*='Send a message']`, `[data-message-author-role="assistant"]`, etc.) are best guesses from the v1 script.
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.27 — treat as NEW
  - `...n/functional_intents/captures_readme_extraction_analysis.md`
  - `claude_chat_transcripts/captures/README.md`

### Gap:** Who receives Architect output after human approval?
- support: 2 statements across 2 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Missing provenance**: No timestamp, no author, no version tracking.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### Gap**: RESTRICTED actions require approval, but no approval request object is defined.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### API Key Missing: Initial → Fetching → Validating → Building Prompt → Calling Prime → Return 500
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...ction/functional_intents/idea_drafts_extraction_analysis.md`
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Gap**: No RBAC or user authentication on approval endpoints
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### The Slot 1 4096 token context limit means that L2 verification silently breaks for contracts exceeding ~300 lines.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.35 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### Gap 3: Drift Detection → Reminder System Bridge
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`
  - `...nctional_intents/x_00_operator_model_extraction_analysis.md`

### Missing storage drives** — `/mnt/models`, `/mnt/cache`, `/mnt/archive` not mounted on boot
- support: 2 statements across 2 document(s)
- nearest queue item 10 is only sim 0.24 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`

### # Transitional Implementations # Updated: 2026-04-29 # Purpose: Prevent temporary fixes from becoming invisible permanent architecture. # Every item here has a planned replacement. Track it explicitly.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.44 — treat as NEW
  - `...TP_Project_Primer/11_TRANSITIONAL_IMPLEMENTATIONS.md#r0`
  - `...n_backups_20260430/11_TRANSITIONAL_IMPLEMENTATIONS.md:0`

### ``` This block is not supported on your current device yet. ``` Understood. Before the build plan rewrite, you have things to address first. Go ahead — what are they?
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...0-4406-b978-6e0379ba80ea:Build plan rewrite preparation`
  - `...an AI platform for professional project guidance.md:147`

### /its just that the eample and the replacement code is not identical with what is there. can you tell in the picture where I start and where I end Apr 22 Claude responded: Yes.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...86e-87a3-fbbd98f2b494:Model registry API implementation`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:252`

### Conversation history — If you're on claude.ai, check your past conversations. The code should still be in the chat thread where it was built. You can scroll back and copy it out. Browser cache — If you were on a web browser, the page may still be cached if you haven't cleared it. Rebuild from spec —
- support: 2 statements across 2 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...Refactoring CIS application into modular structure.md:1`
  - `...efactoring CIS application into modular structure.md:14`

### Apr 22 Claude responded: Good question to resolve before locking the schema, because the answer changes the data model.
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.30 — treat as NEW
  - `...04-23_Video preprocessing schema definition setup.md:54`
  - `...e_atlas/original_CISChats/CIS_Chat_2026-04_003.md:43#r1`

### 1. `source_unit` table status confirmed (exists or needs to be created alongside) 2. Schema confirmed — no further field changes 3. You say write it
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...hat_transcripts/2026-04-23_Starting a new session.md:77`
  - `_archive/CIS_Handoff_2026-04-23_0434_ChAT.md:23`

### Resolve is fully working. Session #008 shows RESOLVED in green, solution text displayed, decided by and date confirmed. The full flow is proven end to end.
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:466`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:467`

### ## All other documents must defer to STATE.md for phase status.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...d-offs/X_Where Phases Are Defined (Current State).md:98`
  - `...ve_Intelligence_System_LegacyBuildFiles/X_03_STATE.md:4`

### This is a Phase 1 architectural decision that needs to be made and logged now:
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...at_transcripts/2026-04-23_Starting a new session.md:277`
  - `...at_transcripts/2026-04-23_Starting a new session.md:727`

### **Right now — manual paste is the only method.** You copy the relevant section and paste it into whichever model you're talking to. That's the current workflow.
- support: 2 statements across 2 document(s)
- nearest queue item 20 is only sim 0.22 — treat as NEW
  - `...04-18_Session execution and image pipeline setup.md:985`
  - `..._Intelligence_System_v1/memory_additions_20260420.md:11`

### 2. What failed or didn't work Nothing failed. This was a research and design session — one question, one comprehensive answer. The transcript is complete and clean.
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...-24_CIS phase 1 intelligence extraction handoff.md:1133`
  - `...action_first_try/insights_First_Try/_all_insights.md:19`

### Output is valid when: - Every failure mode is specific and reproducible - Every proposed fix is concrete and implementable - The verdict is unambiguous — pass or fail, not maybe - At least three failure modes were tested even if none were found
- support: 2 statements across 2 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...l build sequence and architectural dependencies.md:1762`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_015.md:190`

### These will take a few minutes. Paste any errors that come up — success output can be skipped, just confirm when both are done. Apr 22 Claude responded: Both installed cleanly.
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.40 — treat as NEW
  - `...pts/2026-04-22_Model registry API implementation.md:899`
  - `...ure_atlas/original_CISChats/CIS_Chat_2026-04_004.md:699`

### - command/function - input - output - validation - failure handling
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.18 — treat as NEW
  - `...e_atlas/cis_chat_2026_04_009_extraction_analysis.md:575`
  - `...uence/3 Platform Chat/CIS_Pivot_Chain of Thought.md:527`

### * input * process * output * validation * failure rules * state change
- support: 2 statements across 2 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:1504`
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:3016`

### if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor( std_logging.DEBUG ): # pragma: NO COVER _LOGGER.debug( "Created client `google.ai.generativelanguage_v1beta3.DiscussServiceAsyncClient`.", extra={ "serviceName": "google.ai.generativelanguage.v1beta3.DiscussService", "universeDomain": getattr( se
- support: 2 statements across 2 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...project/social_work_ai/01_CORE/moved_async_client.py#r5`
  - `swa_project/social_work_ai/01_CORE/async_client.py#r5`

### Result: FAIL — 2 check(s) failed Blocking: YES — do not advance until resolved Logged to: /mnt/projects/cis/logs/verification_[log.md](http://log.md) eric@creative-vm:~$
- support: 2 statements across 2 document(s)
- nearest queue item 16 is only sim 0.43 — treat as NEW
  - `...-9d9c-e83384f51db8:Starting a new session with files#r1`
  - `...-a83d-a4a21870b2d7:CIS execution layer phase 0 setup#r4`

### **Why:** Building around an unavailable capability would add complexity with no return. The manual workflow is fast when the UI is designed for it.
- support: 2 statements across 2 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `..._Intelligence_System_v1/memory_additions_20260420.md:38`
  - `cis_v1_vault/memory_additions_20260420.md`

### This is: 👉 **CAPABILITY LAYER + EXECUTION ENVIRONMENT DEFINITION** It defines: - how tools exist **inside the system** - how capability is made **usable** --- ## 🔧 NORMALIZED ADDITIONS (Core Tool Stream integrated) ### 🔹 **CAPABILITY SYSTEM (NEW COMPONENT TYPE)** **Tool Stream** - defines **how capa
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.33 — treat as NEW
  - `...es/Hand-offs/CIS_LegacyBuildFiles_Consolidation.md:1128`
  - `chatgpt_export/69dd351d-9d94-83ea-9c60-a97bf3e2e2c4#r1`

### ## Object 3: Capabilities Manifest - **Purpose:** Authoritative list of actual system capabilities for validation. - **Lifecycle:** Created → Maintained → Validated → Updated - **Authority Source:** System architecture documentation. Must be maintained by developers. - **Related Objects:** Memory (c
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `..._04_20_ai_memory_capabilities_extraction_analysis.md#r3`
  - `...insight_record_2026_04_19_001_extraction_analysis.md#r5`

### oh, I thought you were just asking if the enforcement works.Let me know if these files answer the question. 8:31 PM
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.34 — treat as NEW
  - `...ting up multi-panel control plane for model observation`
  - `claude crystallizes the vision.txt:153`

### ## Discovery 1: Guardrail as Single Source of Truth (SSOT) - **Architectural Significance**: Guardrail is NOT a safety net—it is the authoritative reference the AI must consult before ANY action - **Affected Layers**: Governance (02_GUARDRAIL), Execution (03_ENGINE), Application (04_INTERFACE) - **D
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `..._are_these_files_in_guardrail_extraction_analysis.md#r1`
  - `..._x_cis_discovery_workbench_v1_extraction_analysis.md#r1`

### [asked] I don't quite follow what claude is talking about here. can you help me understand and follow up on this issue. The bypass is gone. §3.2 now rejects with 409 instead of auto-creating, and the rationale is stated correct... The reason this defect got as far as it did is that it satisfied the 
- support: 2 statements across 2 document(s)
- nearest queue item 22 is only sim 0.38 — treat as NEW
  - `...bcd-4be2-a60a-dd490fccbe35:Awaiting ChatGPT proposal#r2`
  - `...session/glm-reviewer/session_20260614_172934_5046b0/9.3`

### Before this file, governance was a set of documents. After this file, governance is an operational system with: - Explicit provenance requirements (--approved-by, --architect) - Two-phase atomic apply with preview enforcement - Process lock enforcement - Conflict logging with structured format - Que
- support: 2 statements across 2 document(s)
- nearest queue item 21 is only sim 0.30 — treat as NEW
  - `...0260505_0058_01_current_state_extraction_analysis.md#r1`
  - `...0345839_x_01_system_blueprint_extraction_analysis.md#r6`

### ### Missing Governance: 1. **Template Governance**: Rules for template instantiation not defined. 2. **Domain Governance**: Rules for domain instantiation not defined. 3. **Phase Governance**: Rules for phase transitions not defined. 4. **Category Governance**: Rules for category definition not defi
- support: 2 statements across 2 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...app_concept_workflow_template_extraction_analysis.md#r2`
  - `...lopment_system_architecture_7_extraction_analysis.md#r2`

### implementation_artifacts | No | **Deferred-unscheduled** — no v2.0 tier
- support: 6 statements across 1 document(s)
- nearest queue item 4 is only sim 0.30 — treat as NEW
  - `PLAN_RECONCILIATION.md`

### No Reliable Fetch Target Exists**: Auto-fetch feature permanently deferred; no development resources should be allocated to it.
- support: 5 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`

### Session Resolution**: Added as mandatory governance step; resolve form implementation identified as gap
- support: 5 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Verification Pipeline Incomplete**: Despite 5 manifests produced and 0 unresolved FAILs, verification remains manual terminal-only — no automated verification pipeline exists.
- support: 5 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`

### Gap**: No application surface for writing or reviewing contract specification documents
- support: 5 statements across 1 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### The dashboard architecture has a fundamental flaw**: It attempts to load local filesystem data from a local HTML file, which is blocked by browser security models.
- support: 5 statements across 1 document(s)
- nearest queue item 10 is only sim 0.20 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### PASS WITH WARNINGS:** All required files present, phase-required streams present, optional streams missing or excluded files present
- support: 4 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Missing Runtime Bridge: Review Feedback to Implementation Process
- support: 4 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...unctional_intents/adversarial_review_extraction_analysis.md`

### No validation layer → model routing cannot escalate properly
- support: 4 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`

### Deferred Items | Shows items needing verification | Side panel
- support: 4 statements across 1 document(s)
- nearest queue item 5 is only sim 0.23 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### UI Redesign Before Frontend Modularization:** The frontend modularization is also deferred until the UI redesign (mockup integration) is complete.
- support: 4 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Every reaction must be**: correct, refine, accept, reject, or add missing structure
- support: 4 statements across 1 document(s)
- nearest queue item 1 is only sim 0.26 — treat as NEW
  - `.../x_cis_intake_knowledge_workbench_v1_extraction_analysis.md`

### Architectural Significance**: Four defined states (OPEN, DEFERRED, RESOLVED, SUPERSEDED) with implied transitions
- support: 3 statements across 1 document(s)
- nearest queue item 21 is only sim 0.26 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Queue ownership is prerequisite, not optional** - Previously assumed execution could proceed without centralized queue, now recognized as critical missing layer blocking all reliable execution
- support: 3 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...ents/2026_04_28_operator_layer_pivot_extraction_analysis.md`

### Gap**: No mechanism to improve retrieval based on reconciliation outcomes
- support: 3 statements across 1 document(s)
- nearest queue item 3 is only sim 0.35 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### No validation** of `project_id` format, uniqueness, or existence before operations.
- support: 3 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### VETO, RETURN_TO_DRAFT | Deferred to full Component 3 implementation.
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `CIS_TIER_11_UI_USABILITY_SPECIFICATION.md`

### Broken when**: ADRs fail to post (missing fields), decisions not documented
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap Retrieval Loop**: Gaps retrieved → resolution patterns identified → gap resolution improved → faster resolution
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Gap**: No full-text search, no category tags, no date range filtering
- support: 3 statements across 1 document(s)
- nearest queue item 1 is only sim 0.41 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap:** No defined quality standards for sound assets
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.21 — treat as NEW
  - `...uildfiles_x_11_sound_stream_expanded_extraction_analysis.md`

### Governed state registry and visual orchestration deferred to build plan rewrite.
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0427_extraction_analysis.md`

### Session insights**: Captured via cis-log insight subcommand (not implemented)
- support: 3 statements across 1 document(s)
- nearest queue item 15 is only sim 0.46 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### Missing Runtime Bridge: Hermes to Approved Tools/Scripts
- support: 3 statements across 1 document(s)
- nearest queue item 20 is only sim 0.50 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### SSH Key Loop:** Missing key → SCP fails → User creates key → SCP succeeds
- support: 3 statements across 1 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### ViewLayer Validation**: Check for missing collections, invalid render passes
- support: 3 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### This reveals a communication gap that must be bridged by the Session Initialization Layer.
- support: 3 statements across 1 document(s)
- nearest queue item 15 is only sim 0.33 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Deferred items logged → Session start surfaces them → Verification completed → No item forgotten
- support: 3 statements across 1 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Handoff checklist failure → Identify missing items → Complete items → Re-validate
- support: 3 statements across 1 document(s)
- nearest queue item 5 is only sim 0.22 — treat as NEW
  - `...raction/functional_intents/x_control_extraction_analysis.md`

### Session Start**: Blocked if handoff folder is missing or `cis-start` command is not installed.
- support: 3 statements across 1 document(s)
- nearest queue item 5 is only sim 0.28 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0348_extraction_analysis.md`

### Build Impact**: L2 semantic verification of execution contract deferred to next session.
- support: 3 statements across 1 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Blocked by**: Distillation pipeline, knowledge base schema
- support: 3 statements across 1 document(s)
- nearest queue item 1 is only sim 0.36 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Gap**: No bridge between session transcript extraction and runtime session memory
- support: 3 statements across 1 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Knowledge Module**: Not built — knowledge accumulation not implemented
- support: 3 statements across 1 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Video Preprocessing↔Knowledge Formation**: Video pipeline declared but not implemented; ffmpeg, Whisper, vision extraction not operational
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.20 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Commit layer bridge**: ADR-048 Phase 3 deferred - no automated commit pipeline
- support: 3 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `.../functional_intents/01_current_state_extraction_analysis.md`

### Architectural Significance**: The document explicitly identifies that execution rules, discovery-driven structure formation, reinforcement through review, and workbench behavior are **missing** from current documentation.
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### ADR panel sort/filter**: Depends on dashboard UI changes — task logged, not yet built
- support: 3 statements across 1 document(s)
- nearest queue item 7 is only sim 0.26 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`

### Conflict Logging → Resolution**: 3 conflicts resolved, 1 deferred — governance loop exists but is human-mediated
- support: 3 statements across 1 document(s)
- nearest queue item 21 is only sim 0.34 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`

### Runtime Impact**: L2 has no explicit temperature setting - this is a potential governance gap
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### Idempotent migrations are possible**: The script can be re-run safely, adding missing columns without data loss
- support: 3 statements across 1 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `...n/functional_intents/cis_migrate_041_extraction_analysis.md`

### Transitional Gap Schema**: Needs formal definition with fields for gap type, severity, target resolution, status
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Conflict Escalation Loop:** Conflict identified → Cannot resolve → Appended to conflict register → Deferred → Next audit → (repeat until resolved)
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Required file validation:** Fail if STATE.md, SYSTEM_BLUEPRINT.md, or MASTER_ARCHITECTURE_MAP.md missing
- support: 3 statements across 1 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Gap**: No defined rules for distillation deletion or archiving
- support: 3 statements across 1 document(s)
- nearest queue item 18 is only sim 0.29 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Verification ↔ Operator Abstraction**: Verification complexity exposed missing operator abstraction, but operator abstraction requires verification pipeline understanding.
- support: 3 statements across 1 document(s)
- nearest queue item 6 is only sim 0.26 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Primer update correction | Provenance validation → Missing provenance → Corrected update | Negative feedback | Stable
- support: 3 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### work by actively trying to find failure modes, edge cases, missing
- support: 2 statements across 1 document(s)
- nearest queue item 9 is only sim 0.23 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Versioning**: Versions increment (v1, v2, v3), records never silently replaced
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.26 — treat as NEW
  - `...ldfiles_x_04_master_architecture_map_extraction_analysis.md`

### None** - No validation that source_type is correct
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`

### Lifecycle**: Created OPEN, transitions through DEFERRED/RESOLVED/SUPERSEDED
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Missing file**: Returns 404 for verify-contract if file not found
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.23 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### System state visibility (users cannot easily tell if ComfyUI is running — identified gap)
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.20 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`

### Append-only log protection**: Execution logs may not be silently rewritten
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...5_operational_governance_contract_v1_extraction_analysis.md`

### Missing Merge Script**: Blocks auto record population
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Missing Validation Layer**: There is no validation that the reconciliation accurately represents the parallel responses, creating a trust gap.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### The execution layer is the missing coordinator that ties everything together.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...ntents/phase_0_5_replan_orchestrator_extraction_analysis.md`

### Execution Layer**: Blocked by unknown application runtime state
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### No placeholder strings | scan for forbidden strings list
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.27 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### GAP**: No mechanism to detect when registered sources are modified
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...raction/functional_intents/librarian_extraction_analysis.md`

### The single largest architectural gap is the **missing queue subsystem formalization**.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

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
- nearest queue item 17 is only sim 0.19 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Missing phase-required stream → blocks phase-specific execution
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.40 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Missing Content Validation**: No verification of course content quality
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### Model registry schema**: Exists but Qwen cannot be PATCHed active — schema is incomplete without weight path field
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`

### No Validation**: No verification that conflicts are real
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.23 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Not implemented**: Queue.py does not contain knowledge formation logic
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.27 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### Not implemented**: Queue.py does not expose workflow execution
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.35 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### L1 PASS → L2 rerun:** Deferred for operator abstraction flow
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.36 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### QR code URL display — deferred feature, low effort, should be a task
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Question States**: `OPEN`, `RESOLVED`, `IN PROGRESS`, `DESIGNED, NOT YET BUILT`
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Impact**: Passthrough devices can silently block future snapshots
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`

### Source File Existence**: No validation that source_path exists before processing
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.28 — treat as NEW
  - `...on/functional_intents/cis_preprocess_extraction_analysis.md`

### 2026-04-18T10:37:58.490327+00:00 | ERROR: Missing dependency: No module named 'qwen_vl_utils'
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `...ts/2026-04-18_Session execution and image pipeline setup.md`

### The fix required identifying that state variables (`showResolve`, `solution`, `decidedBy`) and a `resolve()` function existed but the JSX that renders when `showResolve` is true was simply missing.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### This is a recurring failure mode — updating the reorientation doc keeps getting deferred and added to next steps, but next steps are what get deferred first when a session runs long.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.35 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### This reveals a fundamental gap between AI self-description and actual system capabilities.
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.34 — treat as NEW
  - `...ts/2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Transitions**: Pending → Validating → Complete/Incomplete/Failed
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.38 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Conflict register must be indexed by: issue, status (open/resolved/deferred), affected files.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### 10 | Missing status reader artifact | Added tools/eric_gate/show_status.py (Section 13)
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.39 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### Absent or not root-owned → STOP: "/opt/cis-control missing/not-root — trust root must be
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.30 — treat as NEW
  - `MINIMAL_WORKER_LAUNCH_PROOF_v2.md`

### Batch curl commands with `&&` chaining fail silently on first error, preventing subsequent posts.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.20 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Missing artifact_ids in completed items → FAIL (exit 1)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.43 — treat as NEW
  - `...action/functional_intents/cis_verify_extraction_analysis.md`

### Missing documentation layer | Branch notes via CIS Live sessions | Three-field lightweight format
- support: 2 statements across 1 document(s)
- nearest queue item 20 is only sim 0.29 — treat as NEW
  - `...ts/2026_04_22_cis_build_continuation_extraction_analysis.md`

### Brush Validation**: Check for missing textures, invalid curves
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.20 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### No Review Logic**: State transitions are not enforced or validated
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.46 — treat as NEW
  - `...extraction/functional_intents/cis_db_extraction_analysis.md`

### The component status taxonomy is formalized**: OPERATIONAL, OPERATIONAL/TRANSITIONAL, OPERATIONAL/RISK, ACTIVE, PRE-DRAFT, LOCKED, MISSING.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.29 — treat as NEW
  - `...intents/archive_04_active_components_extraction_analysis.md`

### Connection Management Gap**: The connection factory creates new connections per call with no pooling, transaction management, or lifecycle management - a significant operational gap.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.25 — treat as NEW
  - `...action/functional_intents/connection_extraction_analysis.md`

### Current Alternative:** `push_cis_live()` exists but not wired
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Architectural Significance**: Executor worker is a stub that does not call any model and generates placeholder output
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.32 — treat as NEW
  - `.../functional_intents/approval_request_extraction_analysis.md`

### Discovery 13: Intel Sidebar Tabs Are Decorative — Not Wired to Any Function
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Missing file map → create**: Operator identified missing orientation document.
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.35 — treat as NEW
  - `...se_and_handoff_process_clarification_extraction_analysis.md`

### MCP is deferred to after this stack is operational.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.28 — treat as NEW
  - `...sponse_to_vscode_obsidian_and_github_extraction_analysis.md`

### Discovery**: Draft → Review → Gap Identification → Resolution → Re-review
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Draft rejection → (no path)**: Gap - no correction feedback to source
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.38 — treat as NEW
  - `...ctional_intents/04_active_components_extraction_analysis.md`

### Error Handling is Silent**: Malformed records are silently skipped, creating invisible data loss.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Execution → Intelligence | Core Tool Stream | Intelligence Layer | Not yet built
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Exit codes: 0 = success, 1 = no files found, 2 = root directory missing
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### Missing:** Explicit interface between intent detection and AI state machine
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.26 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Gap**: Form strip removal created dependency on syntax integrity
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`

### Gap**: No defined routing for UNCERTAIN verdicts
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `...nctional_intents/cis_verify_semantic_extraction_analysis.md`

### Gap**: No documentation exists for execution rules, commands, states, transitions, validation, or orchestration.
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.29 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Gap**: No mechanism for parallel mediation of multiple captures
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Gap**: No project linkage defined for reinforcement
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`

### Gap:** Storage rules for inheritance relationships not defined
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.23 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Gap:** Manual file-gathering burden not yet automated
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.33 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Gap:** Intake creates structured entries but routing to Project Pipeline is not implemented.
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...egacybuildfiles_x_08_workflow_stream_extraction_analysis.md`

### Gap:** Who detects trigger points for Architect invocation?
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Remote Access → Heavy Compute Jobs**: Blocked by GPU requirement
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.24 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`

### If workflow step cannot be executed consistently on real material → it is incomplete and must be refined
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.23 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Missing SSH Key:** If the SSH key is not set up, the push-to-live-site feature will fail.
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.23 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Intake Retry**: If project_id missing, operator must resubmit with project_id
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_18_0740_extraction_analysis.md`

### Invalid JSON**: Silently ignored (no error returned)
- support: 2 statements across 1 document(s)
- nearest queue item 19 is only sim 0.26 — treat as NEW
  - `...nctional_intents/deepseek_mcp_bridge_extraction_analysis.md`

### Architectural Significance**: The unified control surface (Layer 8) is explicitly deferred until underlying systems are mature
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.23 — treat as NEW
  - `...gacybuildfiles_x_01_system_blueprint_extraction_analysis.md`

### Manual vLLM start → Daemonized vLLM**: Incomplete transition
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.20 — treat as NEW
  - `...ional_intents/archive_07_known_risks_extraction_analysis.md`

### Material Validation**: Check for missing textures, invalid shaders
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.16 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Mediation Notes as Placeholder**: The mediation notes section exists as an empty structure, awaiting integration with a mediation workflow that doesn't yet exist.
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.28 — treat as NEW
  - `...extraction/functional_intents/readme_extraction_analysis.md`

### Merge Layer↔Knowledge Layer**: Merge layer still conceptual; no implementation exists
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Merge layer not implemented | Blocks all downstream work | CRITICAL
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### Missing Intelligence Layer**: Sound operations cannot access structure or transformation
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.20 — treat as NEW
  - `...l_intents/x_11_sound_stream_expanded_extraction_analysis.md`

### Missing Runtime Bridge: Review Dependency Tracking
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.43 — treat as NEW
  - `...unctional_intents/adversarial_review_extraction_analysis.md`

### SCP is a critical path dependency** — Without SSH key configured, the push operation fails silently.
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Missing Slot 1**: Returns 503 BLOCKED for L2 operations
- support: 2 statements across 1 document(s)
- nearest queue item 19 is only sim 0.26 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Missing**: Rules for validating across multiple sources
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...l_intents/cis_pivot_chain_of_thought_extraction_analysis.md`

### Preprocessing Validation**: Validation of preprocessing normalization quality not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `..._attempt_taking_longer_than_expected_extraction_analysis.md`

### Missing Columns:** `superseded_by`, `version`, `author`, `tags`, `category`, `references`
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.42 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Slot 3 Deferred**: Cannot register until model evaluation is complete.
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`

### No Content Validation**: No validation that new content is valid primer format
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.17 — treat as NEW
  - `.../functional_intents/primer_update_v2_extraction_analysis.md`

### No forbidden strings: "TODO", "...", "placeholder", "TBD"
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.22 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Pre-Creation Config Check**: No validation layer for config.py constant before path creation
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.20 — treat as NEW
  - `...ional_intents/adr_047_scope_predraft_extraction_analysis.md`

### Plugin Compatibility Validation**: No validation logic defined.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...action/functional_intents/myproject3_extraction_analysis.md`

### Primer Review:** Current, Stale, Updated, Deferred
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Runtime Impact**: Queue-backed operator routing exists but incomplete; worker-status endpoint operational
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### Runtime Impact:** Phase D validation checks for Intelligence Stream inclusion; missing stream blocks execution
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Runtime Impact**: Script will silently fail or capture garbage if selectors change
- support: 2 statements across 1 document(s)
- nearest queue item 9 is only sim 0.21 — treat as NEW
  - `...n/functional_intents/captures_readme_extraction_analysis.md`

### Architectural Significance**: Runtime Service Ownership Layer has a known operational gap where Slot 1 requires manual start despite automation elsewhere
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.25 — treat as NEW
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### Segment integrity | No validation on creation | Data integrity risk
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.29 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### Slot 3 is DEFERRED**: Qwen3.6-35B-A3B-FP8 (42 shards, ~35GB) is downloaded at /mnt/models2/, but registration is blocked pending Qwen3.6-27B evaluation.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

### State Registry**: Required for proper hierarchical status expression, but explicitly deferred to build-plan reconstruction stage
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

### State Taxonomy Gap Identified**: The current status vocabulary (PRE-DRAFT / OPERATIONAL / LOCKED / NOT YET BUILT) is insufficient for hierarchical implementation state expression.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `...traction/functional_intents/cis_live_extraction_analysis.md`

### Schema Validation Engine**: Referenced but not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...ntents/1775995115163043436_x_control_extraction_analysis.md`

### Architectural Significance**: The gap between foundation/setup and application layer is now formally documented.
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### Documentation Gap Pattern**: There is a systemic pattern where important infrastructure details are set up correctly in the moment but never formally documented.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `...ession_insight_record_2026_04_21_003_extraction_analysis.md`

### Validation Rejection**: Missing title/observation → 400
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...traction/functional_intents/captures_extraction_analysis.md`

### Trust Failure**: Snapshot corruption or incomplete state capture
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`

### Type-specific commit handlers**: Not yet built; required for full automation
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...ts/adr_048_staged_draft_intake_layer_extraction_analysis.md`

### Workflow Execution | Completed stage with output | Incomplete step requiring refinement
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`

### `PENDING_PROCESSING`: File awaiting downstream processing (not implemented)
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### `source_model` field**: Optional, no validation
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `.../functional_intents/advisor_external_extraction_analysis.md`

### cis-log Integration Is Unresolved:** How ADRs are logged via cis-log is not defined.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.25 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### ADR-021 implementation | Session protocol governance | Deferred for governance work
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`

### Issue:** No validation mechanism for cross-session consistency
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...ion/functional_intents/00_start_here_extraction_analysis.md`

### Runtime Impact**: 0 verifications and 0 FAILs this session from build actions, but cumulative counts show 568 verifications and 41 unresolved FAILs
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_05_02_0558_extraction_analysis.md`

### Section separation needs a visual gap/divider between SESSION START and SESSION CLOSE
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.24 — treat as NEW
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`

### This reveals a missing feedback loop: session readiness verification.
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.44 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Build Impact:** Deferred work includes full transcript archaeology.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...6608_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### Gap**: No orchestration for capturing session reasoning
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Gap:** There is no defined routing for continuity fallback.
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...ts_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Runtime Impact**: Handoff is the primary continuity mechanism between sessions; if missing, next session starts blind.
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.24 — treat as NEW
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### Live Session Resolution**: If unresolved, note in Notes field; do not block session close
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0618_extraction_analysis.md`

### Missing**: No project ID, idea ID, or context identifier attached to uploads
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### No cross-capture chunking | No linking between related captures | **MISSING**
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### No supersession tracking | Lineage gap — cannot track decision evolution | MEDIUM
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.28 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Now: Files >~300 lines may exceed L2 verification context — creates verification gap for large governance contracts
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.40 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`

### The object model is incomplete** — missing author, project linkage, supersession, versioning, and audit trail
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/decisions_extraction_analysis.md`

### Open test sessions (#002–#006) must be RESOLVED** — These are unresolved CIS Live sessions that may cause state conflicts.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.42 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0824_extraction_analysis.md`

### Resolve button** must exist before session management can function (was missing).
- support: 2 statements across 1 document(s)
- nearest queue item 14 is only sim 0.25 — treat as NEW
  - `...ession_insight_record_2026_04_22_002_extraction_analysis.md`

### Session → Insight display | Not implemented | Insights not visible at session start
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`

### Build Impact**: Embedding/vector DB implementation deferred; retrieval text generator heuristic acceptable
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.32 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### 15_INHERITANCE_INDEX.md**: Not yet populated, blocked by build plan rewrite
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### 2_CIS_REORIENTATION.md versioning**: Needed but deferred — reorientation may drift
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`

### Architect Panel:** Input area for ADRs + proposals, output area for gap lists/ADR drafts/risk flags
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### Blocked by knowledge_spine availability and segmentation policy.
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.39 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Contract panel | Browse/search contract files | Not implemented | Future contract surface
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Description**: There is no validation layer that checks if the corpus is complete before analysis.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

### Documentation Retrieval Fail:** Documentation missing or outdated
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...85_2026_04_20_ai_memory_capabilities_extraction_analysis.md`

### Exit codes: 0 = success, 1 = corpus file missing, 2 = DB write error
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### FAIL:** "FAIL: Implementation section missing" or "FAIL: no artifact evidence in Implementation section"
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.36 — treat as NEW
  - `CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md`

### Gap**: Files are saved but not routed to any processor, indexer, or workflow
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### Gap:** No link from knowledge record back to source manifest
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Knowledge capture is not implemented** — Resolved sessions do not yet feed into the knowledge base.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.35 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Governance Layer**: Blocked by undefined state management and application layer
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.27 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### New Knowledge Formation Gap**: Conversations are stored but **never processed** for knowledge extraction.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.39 — treat as NEW
  - `...xtraction/functional_intents/advisor_extraction_analysis.md`

### Pipeline keys are not wired** — Stream Deck pipeline and knowledge keys are placeholders only.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.25 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Research Module**: Not built — agent-based categorization not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.41 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Storage Implications**: Must be stored in gap tracking system with indexing by subsystem and target resolution
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.31 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Intake is a recognized gap** that blocks full automation
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...ts/20260502_0047_09_governance_state_extraction_analysis.md`

### Missing intake layer**: Blocks automated content ingestion.
- support: 2 statements across 1 document(s)
- nearest queue item 11 is only sim 0.38 — treat as NEW
  - `...20260502_0047_10_operational_reality_extraction_analysis.md`

### Manifest Gap Identified**: Session manifests exist as chat downloads only, with no automated pipeline to the canonical drop location — a significant gap in the verification architecture.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.36 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_0509_extraction_analysis.md`

### The entire automation reduction pipeline (ADR-046) is blocked by this missing layer.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Build Impact**: Queue formalization (ADR-044) is deferred until after orchestrator runtime experience, creating a deliberate implementation gap.
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Missing Execution Bridge Layer prevents reliable cross-layer coordination
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `...an_update_pack_organized_by_document_extraction_analysis.md`

### Draft intake | No validation (human copy-paste) | Schema validation at /api/drafts/stage
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.27 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Gap**: No automated validation engine that checks extraction output against contract rules
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...on_transcript_extraction_contract_v1_extraction_analysis.md`

### Gap**: No defined orchestration logic for distillation pipeline
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.21 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Gap**: Orchestration of multi-pass extraction across intelligence tiers is not defined.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `.../cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

### Intake layer is the biggest gap**: ADR-048 intake layer not yet built means human manually transfers structured content - this is the primary automation gap.
- support: 2 statements across 1 document(s)
- nearest queue item 11 is only sim 0.16 — treat as NEW
  - `...tents/archive_10_operational_reality_extraction_analysis.md`

### Missing Automation**: The entire automation layer is currently missing - no scripts, no tools, no interfaces exist for the defined pipeline.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.24 — treat as NEW
  - `...cis_handoff_phase_d_automation_start_extraction_analysis.md`

### No Validation Layers Exist**: LivePanel rendering, Decisions API, and broadcast orchestration all lack validation layers.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.21 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`

### No selector improvement loop | Broken selectors not automatically updated | **MISSING**
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Orchestration is NOT implemented in Phase C.** It is defined for later phases.
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.23 — treat as NEW
  - `...ybuildfiles_x_05_core_tool_stream_md_extraction_analysis.md`

### Unresolved Orchestration: Conditional Runtime Repo**: The logic for conditionally committing the runtime repo is not defined.
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...ssion_data_synchronization_checklist_extraction_analysis.md`

### cis_build_handoff_package.py | Build session handoff package | Not implemented | Automated at session start
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.47 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Application Layer is blocked by missing panel validation.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0336_extraction_analysis.md`

### Deferred work**: ADR-045, ADR-046, PD.5 Steps 1-6, Frontend modularization all tracked.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.27 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Grepping the archive confirmed it was missing from both the current modular dashboard and the original monolith — this was a feature that had never existed at any point in the build, not something lost during the refactor.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### No error handling exists for the dashboard**: The infinite spinner indicates a missing error state in the dashboard's state machine, providing no feedback to the user about what went wrong.
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.27 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### /api/conflicts | Not implemented | GET/POST endpoints | Future
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### ADR Panel**: Depends on decisions API — working; sort/filter deferred
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.25 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`

### Black screen root cause is a stray `)` in LivePanel** — no validation layer existed
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0350_extraction_analysis.md`

### Flask dashboard | Application surface | Deferred (Phase 5)
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.26 — treat as NEW
  - `...ession_insight_record_2026_04_21_001_extraction_analysis.md`

### Gap**: Need a Claim Audit Panel in the application surface
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`

### Gap:** No route from dashboard to decisions table
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### LivePanel Validation Bridge**: No validation layer between component assembly and render.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.23 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1418_extraction_analysis.md`

### Poll endpoint**: `/api/queue/job/<N>` referenced but not implemented in this file
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.36 — treat as NEW
  - `...traction/functional_intents/operator_extraction_analysis.md`

### Resolve Form Bridge**: Frontend resolve form now connects to backend resolve route — previously missing
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`

### Router not implemented | No task classification or model tier selection | HIGH
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.30 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### Session panel | Initialize session with handoff package | Not implemented | ADR-048 Build 7
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...ents/11_transitional_implementations_extraction_analysis.md`

### Step 6 blocked by**: Step 5 completion (dashboard polling) — NOT STARTED
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_04_30_1852_extraction_analysis.md`

### Architectural Significance**: The Resolve button in the Live panel toggled state but the form (solution textarea, decided by field, confirm button) was never implemented — backend route existed but frontend form was always missing
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.32 — treat as NEW
  - `...22_model_registry_api_implementation_extraction_analysis.md`

### PD.5 Steps 1-6 | ADR-045 Execution Queue | Queue could be built independently | Queue blocked by verification pipeline
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.27 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### L2 validation: PASS for execution contract (deferred), UNCERTAIN for governance contract (acceptable)
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.23 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### "ADR-040 synthetic: missing auditor model name is rejected",
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### "Manifest missing required 'artifact_identity' block (ADR-040)"
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### 14_GOVERNANCE_GLOSSARY.md**: Not yet populated, blocked by build plan rewrite
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### A formal governance layer is missing and must be created immediately.** The CIS_Primer_Update_Governance_Contract.md must exist and be locked before any further primer updates.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `...update_governance_contract_dicussion_extraction_analysis.md`

### ADR-044 (Operator Abstraction) not started** — blocks resolution of human-as-transport-layer gap.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...tional_intents/current_state_updated_extraction_analysis.md`

### Before**: ADR-001 through ADR-020 existed; ADR-021 through ADR-026 were attempted but failed silently
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Execution Queue Ownership Layer** (ADR-045 direction): Not yet built, but architecturally identified as required layer between operator layer and execution layer.
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.23 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Gap**: Dual-machine file sync conflicts are identified as risk, but no conflict resolution governance is defined.
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.26 — treat as NEW
  - `...ce_system_legacybuildfiles_x_control_extraction_analysis.md`

### Missing Governance:** Trigger point ownership and accountability
- support: 2 statements across 1 document(s)
- nearest queue item 11 is only sim 0.34 — treat as NEW
  - `...raction/functional_intents/architect_extraction_analysis.md`

### The gap between "decision made in conversation" and "decision in DB" was entirely dependent on remembering to run SQL at the right moment.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Non-critical failures** (column missing, test failure): Continue to log, then `sys.exit(1)`
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.29 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### Now post the 4 deferred tasks to the DB — run these one at a time:
- support: 2 statements across 1 document(s)
- nearest queue item 20 is only sim 0.25 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

### Missing DB file**: Immediate exit with no recovery
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.40 — treat as NEW
  - `...n/functional_intents/cis_verify_jobs_extraction_analysis.md`

### Missing Spine Data**: `/api/spines/<id>/nodes` returns 404 if spine_id not found
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.52 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`

### Action**: Check execution_jobs table for incomplete jobs
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `...s/20260502_0047_02_next_build_target_extraction_analysis.md`

### Blocked by:** Database must have `live_sessions` and `live_rounds` tables
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.30 — treat as NEW
  - `...ents/cis_dashboard_monolith_20260420_extraction_analysis.md`

### Dashboard insight capture → Database | Not implemented | Cannot capture from dashboard
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.22 — treat as NEW
  - `.../cis_handoff_insight_capture_session_extraction_analysis.md`

### Decision Capture** — split into ADR table (exists) and decision logging form (missing)
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.28 — treat as NEW
  - `...1_intelligence_extraction_priorities_extraction_analysis.md`

### Architectural Significance**: Database schema requirements not surfaced in error messages — created_at NOT NULL constraint fails silently
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### DB table exists but schema/spec status is incomplete at this point in the transcript.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_016_extraction_analysis.md`

### Deferred Frontend Integration**: Dashboard changes are explicitly deferred to the next session, creating a temporary gap where the schema exists but the UI cannot create records with the new fields.
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.25 — treat as NEW
  - `...nts/adr_041_artifact_registry_schema_extraction_analysis.md`

### Domain configuration loading | Configuration validated and activated | Configuration invalid or missing dependencies | Retry with corrected configuration
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Gap**: No bridge between schema files and runtime pipeline
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.27 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Gap:** The original report called this a "dual database" split.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.31 — treat as NEW
  - `CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`

### Infrastructure dependencies are unverified** — sqlite3 CLI was missing on the target VM.
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### Models table not yet defined — roster check deferred to ADR-042
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### No Output Validation**: No validation that database data matches expected format
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.19 — treat as NEW
  - `...action/functional_intents/spines_api_extraction_analysis.md`

### Schema Migration Gap**: No schema versioning or migration mechanism exists, despite having both inline and file-based schema definitions that could drift over time.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...action/functional_intents/connection_extraction_analysis.md`

### Extraction Quality Gap → Multi-Pass:** missed characters on X-Men 001 triggers multi-pass requirement.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...reprocessing_schema_definition_setup_extraction_analysis.md`

### "Audit response is missing or too short — full response must be logged verbatim"
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### "CRITICAL: missing model name was not caught — auditor identity check broken"
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify.py`

### 9 | Missing test fixture artifact | Added tools/eric_gate/seed_test_fixture.py (Section 13)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.41 — treat as NEW
  - `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`

### Sequencing Constraint**: ADR-043 must be verified (no contradictions, no undefined transitions, no missing authority boundaries, no impossible verification requirements) and frozen before any runtime implementation begins.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Requirement:** User must be able to see when AI actions are blocked by alignment check
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.26 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Condition**: Verification fails due to incomplete constraints
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.24 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### Dependency Impact**: Missing contract registry prevents clean audit trails
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...chat_2026_04_001_extraction_analysis_extraction_analysis.md`

### Discovery 1: Verification Gap Between Reported and Actual Work
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### Verification Layer Gap Identified**: The verification layer (`cis_verify.py`) is now understood to have a critical gap.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_26_1901_extraction_analysis.md`

### Previous**: verification_status may have been implicit or missing
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.38 — treat as NEW
  - `...tabilization_and_intake_architecture_extraction_analysis.md`

### Architectural Significance**: queue_worker.py invokes cis_verify.py with unsupported --file flag, indicating incomplete contract between queue worker and verification tool
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...tents/20260502_0047_01_current_state_extraction_analysis.md`

### Gap**: Raw output format is not validated against expected structure
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`

### `cis_lint.py`**: Future script for health checks (gap detection, stale data, broken links).
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.38 — treat as NEW
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Validate phase-optional streams present → note if missing
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.31 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### The missing piece is not model size anymore** — it is designing the feedback and acceptance structure around it.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.24 — treat as NEW
  - `...2471347_x_cis_discovery_workbench_v1_extraction_analysis.md`

### Architectural Significance**: Six specific bugs were identified and resolved during the audit process: empty verification checks, circular SHA extraction, model whitelist replacement, missing check_artifact_identity_block, migration re-run safety, and row_factory crash bug.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.44 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_0408_extraction_analysis.md`

### Missing MASTER_ARCHITECTURE_MAP.md → blocks all execution
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.31 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Architectural Significance**: Identifies a missing governance layer between AI output and canonical records.
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.36 — treat as NEW
  - `...tional_intents/archive_03_system_map_extraction_analysis.md`

### Verification Complexity as Architecture Revealer**: The verification pipeline's complexity was not just a technical problem — it was an architectural signal revealing missing abstraction boundaries.
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.37 — treat as NEW
  - `...rator_layer_pivot_and_pd5_governance_extraction_analysis.md`

### Architectural Significance**: Unresolved sessions create cognitive fragmentation and architectural drift; resolution became an operational governance requirement, not optional cleanup
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Filesystem canonicality is unresolved** — files_written polymorphism and runtime/manifests/ status create ambiguity about authoritative write paths.
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...ts/20260505_0058_09_governance_state_extraction_analysis.md`

### Build Impact**: Missing foundational governance artifacts.
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.23 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### The gap between current state and required state is substantial across all architectural dimensions: storage, retrieval, governance, security, and knowledge formation.
- support: 2 statements across 1 document(s)
- nearest queue item 1 is only sim 0.24 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Live sessions are architectural debt**: 5 open sessions (#002–#006) represent unresolved decisions that could affect Phase 1 design.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.32 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### Producer**: project state/workflow stage → track → return next steps/reminders/missing pieces.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `...functional_intents/x_09_agent_stream_extraction_analysis.md`

### Swarm architectures deferred (future capability, not current build target)
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.25 — treat as NEW
  - `..._system_legacybuildfiles_x_02_memory_extraction_analysis.md`

### ADR-048 Phase 1 → Stub Population**: 13, 14, 15 population deferred until after ADR-048 Phase 1.
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### It carries forward phase state, locked ADRs, completed work, next steps, open questions, and critical paths.
- support: 2 statements across 1 document(s)
- nearest queue item 11 is only sim 0.24 — treat as NEW
  - `...nctional_intents/context_compression_extraction_analysis.md`

### Commit Layer Governance:** Not yet defined (Phase 3 deferred)
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.27 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Discovery 4: ADR-048 Phase 3 — Intentionally Deferred
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Build Impact:** PM and DAM are deferred to Phase 8 (expanded application surface) with minimal scaffolding in Phase 4 (workbench).
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.21 — treat as NEW
  - `.../cis_formal_phased_construction_plan_extraction_analysis.md`

### Task API:** Accepts `phase` field with values: deferred, backlog, active, completed
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.26 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

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

### Route Task Logic**: Not yet defined — Phase 1 placeholder
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0819_extraction_analysis.md`

### Task Phases:** `deferred`, `backlog` — consistent with CIS phase terminology
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Explicitly deferred by Human Gate with logged rationale
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### Alignment logic, decision gates, parking lot for deferred ideas
- support: 2 statements across 1 document(s)
- nearest queue item 20 is only sim 0.21 — treat as NEW
  - `...tional_intents/x_01_system_blueprint_extraction_analysis.md`

### Source Model Tracking**: Model identity preserved but not enforced
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.27 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`

### The session close rule is documented but not enforced by runtime.
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.33 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Segmentation Pipeline**: Scene detection + duration fallback + transcript-assisted option (deferred to ADR-033)
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.22 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`

### No extension validation** - whitelist defined but not enforced
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.19 — treat as NEW
  - `...tion/functional_intents/idea_uploads_extraction_analysis.md`

### Missing Zone Classification**: Prevents filesystem governance enforcement
- support: 2 statements across 1 document(s)
- nearest queue item 22 is only sim 0.31 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Gap**: Need a CapabilityClaim object with validation status, provenance, and correction history
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_19_001_extraction_analysis.md`

### Knowledge Layer is a Gap**: Despite being called "knowledge records," there is no knowledge formation, semantic indexing, or ontology enforcement.
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.38 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### print("FAIL live_rounds table does not exist — ADR-040 enforcement cannot operate")
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_migrate_041.py`

### Incomplete ingest runs cluttering the active processing folder
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.38 — treat as NEW
  - `claude_chat_transcripts/2026-04-22_CIS build continuation.md`

### Not implemented**: No review/promotion states in extraction_runs
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Runtime Impact**: No validation that `source_id` corresponds to an ingested file before pipeline execution.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.33 — treat as NEW
  - `...traction/functional_intents/pipeline_extraction_analysis.md`

### /mnt/cache/catalog | **DOES NOT EXIST** — needs creation (see §3.3)
- support: 2 statements across 1 document(s)
- nearest queue item 10 is only sim 0.30 — treat as NEW
  - `DOCKER_CONTAINMENT_PROPOSAL.md`

### Current**: Execution layer gap made explicit; operational direction is multi-pass extraction
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.25 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

### extraction_run_log table (planned, does not exist)
- support: 2 statements across 1 document(s)
- nearest queue item 7 is only sim 0.29 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`

### Failure Modes**: Missing `Path` import (fixed), git push hang (temporarily disabled)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Correction feedback path is missing** — ADR-006 implies multi-pass extraction with corrections feeding back, but no mechanism exists.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.21 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### Description**: No validation of extraction file content or session file content before memory ingestion.
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.37 — treat as NEW
  - `...ction/functional_intents/seed_memory_extraction_analysis.md`

### Session Close Schema:** Missing `Path` import caused runtime error (fixed)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.35 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### Gap**: No defined interface between session completion and distillation trigger
- support: 2 statements across 1 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `...intents/session_distillations_readme_extraction_analysis.md`

### Runtime Impact**: If model is missing, extraction fails immediately.
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...ction/functional_intents/cis_extract_extraction_analysis.md`

### Review → Extraction**: Corrections may need to feed back into extraction (ADR-006) but path not implemented
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.36 — treat as NEW
  - `...ession_insight_record_2026_04_17_001_extraction_analysis.md`

### Session Close API**: Returns HTTP 500 on unhandled exceptions (e.g., missing import)
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...owing_black_screen_after_code_change_extraction_analysis.md`

### A9 | Missing required field returns error dict | cis_dispatch_drafter with empty topic | Returns dict with error key, no crash | Check error key present, no traceback
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Blocked by**: Harness initialization, pipeline setup
- support: 2 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...se_to_cis_predev_infrastructure_plan_extraction_analysis.md`

### Error returns | `{ "error": "<message>" }` if run_id missing, not Eric-approved, or dispatch fails
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md`

### Gap**: How insight records route through pipeline not defined
- support: 2 statements across 1 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0553_extraction_analysis.md`

### Gap**: No governance for verifying schema against pipeline output
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Reviewer feedback loop visibility:** The reviewer returns OBJECTIONS with specific missing/incorrect files.
- support: 2 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md`

### Backup mode selection: Snapshot mode fails silently with passthrough devices
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.21 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`

### Missing exclusion → Cancel → Reconfigure**: Impractical backup size triggers correction
- support: 2 statements across 1 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `...6_04_21_proxmox_vm_snapshot_creation_extraction_analysis.md`

### Hard Rejection**: Missing inputs, missing agent, missing key → HTTP error
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Agent Object**: Execution layer still placeholder; agent roles, capabilities, lifecycle undefined
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.51 — treat as NEW
  - `...chat_2026_04_004_extraction_analysis_extraction_analysis.md`

### Prompt File Missing**: System exits with error message
- support: 2 statements across 1 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### Contract State**: Missing → Drafted → Approved → Active
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.34 — treat as NEW
  - `..._intents/cis_handoff_2026_04_25_1551_extraction_analysis.md`

### Extraction Layer**: Blocked by missing approval workflow
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### No Governance Exists**: No approval workflow, no validation, no retry logic, no rollback mechanism
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.32 — treat as NEW
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### Commit Route is Missing**: The most critical gap — approved drafts cannot become canonical knowledge.
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.40 — treat as NEW
  - `...extraction/functional_intents/drafts_extraction_analysis.md`

### Missing Action Endpoints**: The approval flow is incomplete - only listing exists, no approve/reject actions
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.39 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Missing Provenance**: Worker 4 flags outputs without traceability
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Missing Task Context**: Approval list lacks sufficient context for informed decision-making
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.35 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### Missing**: Approval/rejection decisions should reinforce the AI's understanding of which tasks need human oversight
- support: 2 statements across 1 document(s)
- nearest queue item 21 is only sim 0.35 — treat as NEW
  - `...raction/functional_intents/approvals_extraction_analysis.md`

### None**: No validation of course content, no provenance tracking for suggestions
- support: 2 statements across 1 document(s)
- nearest queue item 3 is only sim 0.33 — treat as NEW
  - `...xtraction/functional_intents/lms_api_extraction_analysis.md`

### Primer Update Fail**: Governance approval missing, apply blocked.
- support: 2 statements across 1 document(s)
- nearest queue item 5 is only sim 0.44 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### API key must be validated before any extraction** - System exits if key is missing
- support: 2 statements across 1 document(s)
- nearest queue item 13 is only sim 0.32 — treat as NEW
  - `...raction/functional_intents/extractor_extraction_analysis.md`

### File permission**: Write permission denied → project creation fails silently (no error handling)
- support: 2 statements across 1 document(s)
- nearest queue item 6 is only sim 0.25 — treat as NEW
  - `...traction/functional_intents/projects_extraction_analysis.md`

### Processing**: Check schema conformity, unsupported claims, missing provenance, contract violations, safety/permission violations, whether frontier escalation needed
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...implementation_objectives_v1_chatgtp_extraction_analysis.md`

### Remote Dashboard Access**: Blocked by authentication layer
- support: 2 statements across 1 document(s)
- nearest queue item 12 is only sim 0.20 — treat as NEW
  - `...al_intents/memory_additions_20260420_extraction_analysis.md`

### Must Not Have**: Unsubstantiated claims, missing drift check, incomplete sections
- support: 2 statements across 1 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `...ional_intents/triangulation_workflow_extraction_analysis.md`

### Container Start Fails**: If the bind mount directory does not exist, the container fails to start with "Script exited with status 9".
- support: 2 statements across 1 document(s)
- nearest queue item 14 is only sim 0.32 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`


## Already represented on the working queue  (0)


## Single-statement recognitions — weakest evidence  (4165)

### Orchestration gap — the human is still the bridge — 464
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.22 — treat as NEW
  - `?`

### Fixed Resolve button — form was never built, added solution textarea and confirm button
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.19 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

### A cleaner inline superseded marker was noted as a future improvement but not implemented.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.29 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### Find edge cases not covered by current validation rules
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.19 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Prerequisite for remote field access workflow and full tunnel activation.","phase":"deferred","priority":3}' | python3 -m json.tool
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

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

### Enables full remote access from any device.","phase":"deferred","priority":3}' | python3 -m json.tool
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.27 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

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

### Actionable — each gap or risk must have a proposed resolution
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.31 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_015.md`

### Am I missing something that will allow this to work?
- support: 1 statements across 1 document(s)
- nearest queue item 20 is only sim 0.19 — treat as NEW
  - `_archive/_LXC container to sandbox the CIS_LIVE.md`

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

### Auto-fetch from model share URLs is deferred (no reliable targets exist).
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `...reative_Intelligence_System_v1/memory_additions_20260420.md`

### Blocked Layer | Blocked By | Unblock Condition
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.33 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Claude responded: Flask, Node, and npm are all missing.
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.37 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`

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

### Exit codes: 0 = success, 1 = input file missing
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.32 — treat as NEW
  - `DEV-PIVOT-13_CATALOG_IMPLEMENTATION_SPEC.md`

### Fail (missing title)**: Returns 400 with error message.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `.../extraction/functional_intents/tasks_extraction_analysis.md`

### Missing Validation Layer: Visual Output Quality Metrics
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.29 — treat as NEW
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`

### New Understanding:** The system is not blocked by infrastructure.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`

### Status**: Conceptually defined, not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `..._intents/cis_handoff_2026_04_29_0015_extraction_analysis.md`

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

### Black screen bug**: Fixed (missing comma between createElement calls)
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.23 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`

### Blocked By**: Infrastructure layer not operational
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...ession_insight_record_2026_04_18_001_extraction_analysis.md`

### Blocked from meaningful production use by missing run logging and review/promotion.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.27 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

### Build Impact**: CURRENT BUILD TARGET — NOT YET BUILT.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.34 — treat as NEW
  - `..._intents/20260505_0058_03_system_map_extraction_analysis.md`

### Build Impact**: Project resolution system is a missing dependency.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Build Impact**: Stage management system is not yet built.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.29 — treat as NEW
  - `...ion/functional_intents/cis_normalize_extraction_analysis.md`

### Build Impact:** Deferred pending build plan rewrite.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.38 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

### Build States**: blocked (prerequisite missing), ready (all dependencies met), in-progress
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `..._intents/cis_handoff_2026_04_22_0817_extraction_analysis.md`

### CREATION is built first; LIFE is designed now but deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.22 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_002_extraction_analysis.md`

### Canonical placement of Obsidian readable mirrors remains unresolved.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.17 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_007_extraction_analysis.md`

### Cloudflare full tunnel — deferred feature, should be a task with `deferred` status
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.39 — treat as NEW
  - `...ts/2026-04-21_App showing black screen after code change.md`

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

### Dependency Impact**: None immediate; deferred as LOW severity
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0323_extraction_analysis.md`

### Dependency**: POST fails hard if source_id is missing
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.30 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Discovery 3: Queue Subsystem as Missing Formal Layer
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

### Discovery 6: Merge Stage is Missing — Critical Gap
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`

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

### Error Recovery**: Blocked by missing retry/rollback logic
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...traction/functional_intents/pipeline_extraction_analysis.md`

### Everything after that was truncated — about 150 lines of the script are missing.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.33 — treat as NEW
  - `... canonical build sequence and architectural dependencies.md`

### Execution queue: NOT RUNNING — does not exist yet
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.31 — treat as NEW
  - `...hive/orientation_backups_20260430/10_OPERATIONAL_REALITY.md`

### Failed or deferred cycles preserve draft files.
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.38 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### File does not exist | Claude re-executes the write and produces a new manifest
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.38 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Flask/Node/npm missing; Flask was installed, React served by CDN.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.19 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`

### From the screenshots, you now have the three things that were missing in the earlier attempt:
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `_archive/ChatGTP’s response to vscode, obsidian and github.md`

### Full application remains deferred, but early operator console is required.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.32 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_011_extraction_analysis.md`

### GAP**: No mechanism to flag suspicious or corrupted files
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.27 — treat as NEW
  - `...raction/functional_intents/librarian_extraction_analysis.md`

### Gap 3 — cis-log current signature: Current cis-log commands:
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.33 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_013.md`

### Gap**: No content hash or source version tracking
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Gap**: No validation of record structure on read
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `...xtraction/functional_intents/records_extraction_analysis.md`

### Gap**: Reconciliation records are stored but not analyzed for patterns
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.37 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

### Gap: No Terminal-State Rules for Incomplete Work
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.28 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_014_extraction_analysis.md`

### Here's what the documentation reveals as missing or unconnected data capture going into intelligence:
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.39 — treat as NEW
  - `...ts/2026-04-18_Phase 1 intelligence extraction priorities.md`

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

### Input Validation**: source_id required, returns 400 if missing
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

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

### Layer 1 catches this (file does not exist = FAIL)
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Lifecycle**: Not yet populated (blocked by build plan rewrite)
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.39 — treat as NEW
  - `..._intents/cis_handoff_2026_05_05_0625_extraction_analysis.md`

### Logs may not be silently rewritten, truncated, or modified in place.
- support: 1 statements across 1 document(s)
- nearest queue item 15 is only sim 0.30 — treat as NEW
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### Missing Application Surface: Taxonomy Merge/Correction
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`

### Missing Benchmark Infrastructure**: Blocks visual output certification
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.26 — treat as NEW
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`

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

### Missing Runtime Bridge: Review Quality Metrics
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.42 — treat as NEW
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

### Missing Validation Layer: No Status Validation
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...n/functional_intents/extraction_runs_extraction_analysis.md`

### Missing Validation Layer: Relationship Integrity
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `..._wias_project_manager_version_1_xlsb_extraction_analysis.md`

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

### Missing source**: Blocks job creation with 400 error
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.34 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### Missing version control → runtime_scripts mirror.
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.23 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_013_extraction_analysis.md`

### Missing visual output generation blocks benchmarking
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.31 — treat as NEW
  - `...hase_d_architecture_visual_benchmark_extraction_analysis.md`

### Missing**: No explicit project_id in reconciliation record
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...on/functional_intents/reconciliation_extraction_analysis.md`

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

### Monitoring**: Blocked by missing metrics collection
- support: 1 statements across 1 document(s)
- nearest queue item 7 is only sim 0.30 — treat as NEW
  - `...traction/functional_intents/pipeline_extraction_analysis.md`

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

### No validation** of record `status` values — assumes they match expected state machine.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.29 — treat as NEW
  - `...n/functional_intents/project_helpers_extraction_analysis.md`

### None identified**: No validation of AI model outputs
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.26 — treat as NEW
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### None implemented**: No validation that project concept is coherent or non-contradictory
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...traction/functional_intents/projects_extraction_analysis.md`

### None implemented**: Only validation failure is missing title
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.21 — treat as NEW
  - `...traction/functional_intents/projects_extraction_analysis.md`

### None** - No validation that manifest is authentic
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.25 — treat as NEW
  - `...tion/functional_intents/cis_classify_extraction_analysis.md`

### None** — no validation or rejection; any content written is served
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.26 — treat as NEW
  - `.../functional_intents/cis_live_handoff_extraction_analysis.md`

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

### Not implemented**: No project association for captures
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.32 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Not implemented**: No promotion path from raw to processed
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.31 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Not implemented**: No retry or recovery mechanisms
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.32 — treat as NEW
  - `...xtraction/functional_intents/capture_extraction_analysis.md`

### Not implemented**: No review/promotion states exist in queue.py
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### Note**: The application layer is blocked by the execution layer.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...lligence_system_architecture_handoff_extraction_analysis.md`

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

### Question Lifecycle**: Open questions have states (OPEN, RESOLVED, IN PROGRESS, DESIGNED NOT BUILT)
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

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

### Runtime Impact**: Missing source blocks job creation
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.31 — treat as NEW
  - `.../extraction/functional_intents/queue_extraction_analysis.md`

### Runtime Impact**: Silent failure mode — operator unaware of missing records.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `..._intents/cis_handoff_2026_04_21_1446_extraction_analysis.md`

### Runtime Impact**: Synthesis requests may timeout if async not implemented; polling mechanism needed
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Runtime Impact**: Uncommitted work is considered incomplete.
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.34 — treat as NEW
  - `...on/functional_intents/implementation_extraction_analysis.md`

### Runtime Impact**: Workflow without Execution Layer is incomplete
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...ctional_intents/x_08_workflow_stream_extraction_analysis.md`

### Runtime blocker:** Without wiring, the app visually implies intelligence capability that does not exist.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_006_extraction_analysis.md`

### Runtime implementation layer: TRANSITIONAL — queue, worker, and launcher not yet built.
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.22 — treat as NEW
  - `...ation_backups_20260430/06_FOUNDATIONAL_CONTROL_CONTRACTS.md`

### SCP Retry** — Not implemented; single attempt with status reporting
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...s_application_into_modular_structure_extraction_analysis.md`

### Slot 3 → Operational**: Deferred pending evaluation.
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.37 — treat as NEW
  - `..._intents/cis_handoff_2026_04_27_2152_extraction_analysis.md`

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

### The placeholder path `/path/to/downloaded/` in the git copy command was taken literally, causing a "No such file or directory" error.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.19 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

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

### This is a documentation failure: the placeholder was not clearly marked as a placeholder and the user ran it expecting it to work.
- support: 1 statements across 1 document(s)
- nearest queue item 10 is only sim 0.24 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

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

### Unresolved Application Surface: Phase Status Display
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Unresolved Application Surface: Review Interface
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.36 — treat as NEW
  - `...lligence_routing_model_orchestration_extraction_analysis.md`

### Unresolved FAILs: [count — must be 0 to close cleanly]
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### Unresolved Routing: Status Change Notifications
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.47 — treat as NEW
  - `..._image_weird_war_tales_cover_001_001_extraction_analysis.md`

### Unresolved divergence between primer and runtime
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.17 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### Update Status**: Change conflict status (OPEN→DEFERRED, etc.)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.25 — treat as NEW
  - `...nctional_intents/cis_conflict_append_extraction_analysis.md`

### Validation Object**: No validation rules for solution quality
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.25 — treat as NEW
  - `...l/extraction/functional_intents/live_extraction_analysis.md`

### Validation Rule | Not defined per stage | Quality control incomplete
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.24 — treat as NEW
  - `...106652302527853_x_08_workflow_stream_extraction_analysis.md`

### Validation layer does not exist**—outputs that fail validation are not flagged needs_review
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.27 — treat as NEW
  - `...intents/cis_canonical_build_sequence_extraction_analysis.md`

### ValidationResult object** — defined conceptually but not implemented
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.20 — treat as NEW
  - `..._pass_to_a_new_chat_minimal_complete_extraction_analysis.md`

### Video is documented in the preprocess header but not implemented — just a comment.
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.18 — treat as NEW
  - `architecture_atlas/original_CISChats/CIS_Chat_2026-04_004.md`

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

### You’re very close — this is just a **network configuration gap**, not a system issue.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.31 — treat as NEW
  - `...orm Chat/vLLM _ Qwen VL Evaluation (April 12, 2026)_Full.md`

### \- Flag any assumption not covered by the task packet
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.27 — treat as NEW
  - `...and the Phase PD Build Plan/CIS_Phase_PD_Build_Plan.docx.md`

### \- \[BLOCKER-001\] Description of unresolved issue
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.26 — treat as NEW
  - `...and the Phase PD Build Plan/CIS_Phase_PD_Build_Plan.docx.md`

### `draft` → `published` (future state, not implemented)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...xtraction/functional_intents/cis_lms_extraction_analysis.md`

### active application) is unknown, indicating a missing state documentation requirement.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### deferred work prematurely, or misrepresent the current phase boundary.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `contracts/CIS_Primer_Update_Governance_Contract_v1.md`

### discovery of placeholder content, omitted fields, hollow writes, and incomplete
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.27 — treat as NEW
  - `contracts/CIS_Verification_Layer_Contract_v1.md`

### files["08_OPEN_QUESTIONS.md"] = """# Open Questions
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.38 — treat as NEW
  - `_archive/generated_script_artifacts/042926_Project_Primer.txt`

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

### missing queue or service ownership requiring implementation
- support: 1 statements across 1 document(s)
- nearest queue item 21 is only sim 0.26 — treat as NEW
  - `contracts/CIS_PD5_Operational_Governance_Contract_v1.md`

### on the same basis as a missing Completion Manifest.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `contracts/CIS_Automation_Reduction_Contract_v1.md`

### what else is missing from the file that is making the process fail.
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.41 — treat as NEW
  - `...s/2026-04-24_CIS phase 1 intelligence extraction handoff.md`

### ~~Execution Ownership Gap~~ — RESOLVED 2026-05-01
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.46 — treat as NEW
  - `...e_chat_transcripts/ChatGTP_Project_Primer/07_KNOWN_RISKS.md`

### “No error shown” is not sufficient if output is truncated or incomplete.
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.24 — treat as NEW
  - `architecture_atlas/cis_chat_2026_04_012_extraction_analysis.md`

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

### 13, 14, 15 are PRE-DRAFT stubs with structure reserved but content deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...nal_memory_governance_primer_rewrite_extraction_analysis.md`

### 1: File Discovery | Source path missing | `find` returns empty | Log missing paths, skip, continue with available sources
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.29 — treat as NEW
  - `SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`

### 2 — Script error (bad args, file missing, vLLM unreachable)
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.24 — treat as NEW
  - `cis_v1_vault/runtime_scripts/runtime/cis_verify_semantic.py`

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

### Application Layer (Layer 8):** Blocked by all lower layers
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.27 — treat as NEW
  - `...action/functional_intents/x_03_state_extraction_analysis.md`

### Application Layer on Underlying Layers**: Application cannot function if any underlying layer is incomplete
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.23 — treat as NEW
  - `...818091549056_x_10_application_stream_extraction_analysis.md`

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

### Async Execution Layer**: Blocked by HHR-016 (Async synthesis)
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.30 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

### Async Synthesis Bridge**: HHR-016 not implemented; no async job + polling mechanism
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.29 — treat as NEW
  - `...extraction/functional_intents/collab_extraction_analysis.md`

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

### Because this functionality is core to the intended use of the system I am not sure if it should be deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.33 — treat as NEW
  - `...transcripts/2026-04-22_Model registry API implementation.md`

### Blocked By**: Missing cis_review.py, missing insight capture
- support: 1 statements across 1 document(s)
- nearest queue item 8 is only sim 0.36 — treat as NEW
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`

### Blocked By:** Explicitly deferred to Build Plan v2
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.46 — treat as NEW
  - `..._update_completion_report_2026_05_02_extraction_analysis.md`

### Blocked By:** Phase D (Intelligence Layer) not complete
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Blocked By:** Phase F (Workflow System) not complete
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...ere_phases_are_defined_current_state_extraction_analysis.md`

### Blocked By:** STATE.md initialization, Phase definitions
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.31 — treat as NEW
  - `...with_these_files_cis_operating_model_extraction_analysis.md`

### Blocked by: Missing capture layer infrastructure
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...ession_insight_record_2026_04_18_003_extraction_analysis.md`

### Blocked by:** Vault must exist with subdirectories
- support: 1 statements across 1 document(s)
- nearest queue item 1 is only sim 0.23 — treat as NEW
  - `...ents/cis_dashboard_monolith_20260420_extraction_analysis.md`

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

### Brush**: Missing textures → Rejected → Default
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.17 — treat as NEW
  - `...traction/functional_intents/untitled_extraction_analysis.md`

### Build Impact**: CREATION domains are built first; LIFE domains are designed now but deferred for later implementation.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.26 — treat as NEW
  - `...ts/2026_04_23_starting_a_new_session_extraction_analysis.md`

### Build Impact**: Documentation updates are part of the build process, not deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `..._intents/cis_handoff_2026_04_28_0239_extraction_analysis.md`

### Build Impact**: Initial implementation must be rule-based; adaptive routing is explicitly deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.33 — treat as NEW
  - `...lligence_routing_model_orchestration_extraction_analysis.md`

### Build Impact**: Low priority but creates technical debt if deferred
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.28 — treat as NEW
  - `...functional_intents/08_open_questions_extraction_analysis.md`

### Build Impact**: Recurring failure mode - updating reorientation doc keeps getting deferred
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.34 — treat as NEW
  - `...ession_insight_record_2026_04_24_001_extraction_analysis.md`

### Build Impact**: Requires content classification before OCR invocation; merge script must handle missing OCR output
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.23 — treat as NEW
  - `...record_system_post_phase_d_extension_extraction_analysis.md`

### Build Impact**: Requires implementation of placeholder modules as swappable components.
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.24 — treat as NEW
  - `...026_05_12_cis_kernel_session_capture_extraction_analysis.md`

### Build Impact**: cis_review.py is the highest priority missing component.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.37 — treat as NEW
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`

### Build Impact:** Deferred but recognized as critical; refactoring into component files is a prerequisite for stability
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.28 — treat as NEW
  - `...ession_insight_record_2026_04_21_002_extraction_analysis.md`

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

### Build workbench**: Not yet built — interface for build sequence management
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.30 — treat as NEW
  - `...ents/cis_project_new_session_handoff_extraction_analysis.md`

### CIS does not fail because components are missing.
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.28 — treat as NEW
  - `...twiceby_accident_extraction_analysis_extraction_analysis.md`

### CIS has a feedback loop**: Review → Structure loop is the only defined feedback mechanism; all other learning loops are missing
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.25 — treat as NEW
  - `...unctional_intents/x_cis_workbench_v1_extraction_analysis.md`

### CREATION and LIFE are top-level domains** with CREATION proven first — LIFE domains (Home, Body, Mind) are deferred.
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.23 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`

### CREATION**: Primary build target; LIFE deferred
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.35 — treat as NEW
  - `..._intents/cis_handoff_2026_04_24_0530_extraction_analysis.md`

### Capture list | List of `.md` files in `captures/` | **NOT IMPLEMENTED**
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.29 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

### Capture viewer | Rendered `.md` viewer | **NOT IMPLEMENTED**
- support: 1 statements across 1 document(s)
- nearest queue item 17 is only sim 0.28 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

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

### Commit layer:** Intentionally deferred and separated
- support: 1 statements across 1 document(s)
- nearest queue item 13 is only sim 0.26 — treat as NEW
  - `...ctional_intents/02_next_build_target_extraction_analysis.md`

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

### Conflict Register State:** Open, Resolved, Deferred, Superseded
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.37 — treat as NEW
  - `...tional_intents/project_primer_update_extraction_analysis.md`

### Conflict Register** — Real-time visibility into unresolved conflicts
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.22 — treat as NEW
  - `...nctional_intents/09_governance_state_extraction_analysis.md`

### Conflict Resolution Interface**: Not yet built—currently CLI-only.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.29 — treat as NEW
  - `...tents/20260505_0058_01_current_state_extraction_analysis.md`

### Conflict Status**: Unresolved conflicts count and details
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `..._intents/archive_09_governance_state_extraction_analysis.md`

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

### Content Validation**: No validation that file content is appropriate for public consumption
- support: 1 statements across 1 document(s)
- nearest queue item 18 is only sim 0.23 — treat as NEW
  - `..._vs_cis_root_folder_for_file_hosting_extraction_analysis.md`

### Content Validation**: There is no validation of the content before it is served.
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.14 — treat as NEW
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

### Correction Validation**: No validation of correction correctness
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `...0981892284_x_cis_reinforcement_model_extraction_analysis.md`

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

### Cross-field validation**: No validation that corrections don't create inconsistencies
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.21 — treat as NEW
  - `...s/cis_handoff_review_command_session_extraction_analysis.md`

### Cross-project capture | No mechanism for other projects | **MISSING**
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.23 — treat as NEW
  - `...l_intents/1778631849236291842_readme_extraction_analysis.md`

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

### DEFERRED** | WIAS full operationalization | ⬜ After CIS complete
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.34 — treat as NEW
  - `DEV-PIVOT-06_BUILD_DIRECTION.md`

### DEFERRED_EXISTS | Deferred items | Must resolve before close
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.26 — treat as NEW
  - `...ication_mechanism_for_completed_work_extraction_analysis.md`

### DOCUMENTED: Gap has been documented with target resolution
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.40 — treat as NEW
  - `...cis_automation_reduction_contract_v1_extraction_analysis.md`

### Dead Letter Channel for out-of-scope | Unrecognized domains must not silently create work | Invalid Message Channel (Hohpe/Woolf)
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.39 — treat as NEW
  - `CIS_TIER_7R_SPECIFICATION_PROPOSAL.md`

### Deferred work identified**: Previously deferred work was undefined.
- support: 1 statements across 1 document(s)
- nearest queue item 2 is only sim 0.30 — treat as NEW
  - `...ions_2026_04_28_operator_layer_pivot_extraction_analysis.md`

### Deferred**: Application Layer depends on Execution Layer being proven first
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.26 — treat as NEW
  - `...917_x_cis_workflow_execution_spec_v1_extraction_analysis.md`

### Deferred**: Application layer (until workflow stabilized)
- support: 1 statements across 1 document(s)
- nearest queue item 12 is only sim 0.35 — treat as NEW
  - `...llm_qwen_vl_evaluation_april_12_2026_extraction_analysis.md`

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

### Dependency Impact**: References to open questions must specify which file to use
- support: 1 statements across 1 document(s)
- nearest queue item 22 is only sim 0.18 — treat as NEW
  - `..._intents/cis_handoff_2026_05_01_0548_extraction_analysis.md`

### Dependency Impact**: Requires project-to-domain mapping convention; no validation of project parameter
- support: 1 statements across 1 document(s)
- nearest queue item 4 is only sim 0.28 — treat as NEW
  - `...extraction/functional_intents/spines_extraction_analysis.md`

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

### Dependency Impact:** Requires input validation that accepts partial/evolving definitions rather than rejecting incomplete inputs.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.27 — treat as NEW
  - `...5927980563287026_x_00_operator_model_extraction_analysis.md`

### Dependency Impact:** The application layer depends on the infrastructure layer for serving, but the wiring between them is incomplete.
- support: 1 statements across 1 document(s)
- nearest queue item 11 is only sim 0.18 — treat as NEW
  - `...2026_04_20_resuming_creative_vm_work_extraction_analysis.md`

### Description**: CIS is needed to manage CIS construction, but CIS does not exist yet
- support: 1 statements across 1 document(s)
- nearest queue item 16 is only sim 0.22 — treat as NEW
  - `.../cis_predev_infrastructure_plan_docx_extraction_analysis.md`

### Description**: Human review interface for draft records does not exist
- support: 1 statements across 1 document(s)
- nearest queue item 6 is only sim 0.36 — treat as NEW
  - `...ntents/cis_master_handoff_2026_04_17_extraction_analysis.md`

### Description**: Missing document that makes explicit relationships between all other documents visible.
- support: 1 statements across 1 document(s)
- nearest queue item 3 is only sim 0.32 — treat as NEW
  - `..._cis_the_pattern_across_the_cis_docs_extraction_analysis.md`

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

### Description**: The following queue subsystems are identified as missing but required:
- support: 1 statements across 1 document(s)
- nearest queue item 5 is only sim 0.30 — treat as NEW
  - `...tents/foundational_control_contracts_extraction_analysis.md`

