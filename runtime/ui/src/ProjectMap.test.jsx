import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProjectMap from "./ProjectMap";

// In-memory fake of runtime/api/project_intelligence.py's single GET route.
//
// The mock exposes exactly three api.js functions, and no mutating one. Two of
// them are there only because ProjectMap REUSES the components that own them —
// CurrentBuildPanel from BuildPath.jsx and DestinationArchitecture.jsx — and
// their call counts are themselves asserted:
//
//   getBuildPath              must NEVER be called. The Current Build area
//                             renders from the build-path payload the
//                             project-intelligence response already embedded,
//                             which is what "reuse, not a second fetch" means.
//   getDestinationArchitecture called exactly when the Destination area is
//                             shown, by the component that owns that question.
//
// If this screen ever reached for a mutating function it would be undefined
// here, which is the guard that the Project Map stays read-only.
const state = {
  handler: null,
  buildPathCalls: 0,
  destinationCalls: 0,
  renderCalls: [],
};

vi.mock("./api", () => ({
  getProjectIntelligence: (...args) => state.handler(...args),
  getBuildPath: () => {
    state.buildPathCalls += 1;
    return Promise.resolve({ ok: false, error: "must not be called" });
  },
  getDestinationArchitecture: () => {
    state.destinationCalls += 1;
    return Promise.resolve({ ok: true, data: destinationPayload() });
  },
}));

// Mermaid does real layout measurement, which jsdom has no engine for. Stubbed
// so these tests assert what THIS component does with Mermaid's answer; that the
// generated source actually parses is proven server-side against the real
// generator in runtime/tests/test_project_intelligence_api.py.
vi.mock("mermaid", () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn(async (id, source) => {
      state.renderCalls.push({ id, source });
      return { svg: `<svg data-source-lines="${source.split("\n").length}"></svg>` };
    }),
  },
}));

const MISSING_LINK = "No authoritative link recorded yet.";
const MISSING_PLAIN = "Plain-language explanation not yet recorded.";

function ok(data) {
  return { ok: true, data };
}

function fail(error) {
  return { ok: false, error };
}

function destinationPayload() {
  return {
    read_model: "cis_destination_architecture",
    present: true,
    generated_at: "2026-10-02T12:00:00+00:00",
    state_revision: "rev-1",
    architecture_scope: "destination",
    counts: { decisions: 3, nodes: 2, edges: 1, relationship_types: 1, problems: 0 },
    node_kinds: ["root", "substrate"],
    nodes: [
      {
        id: "WIASW", label: "WIASW — Word · Image · Action · Sound + Web", kind: "root",
        depth: 0, description: "the overarching destination architecture",
        activation_state: "NOT_ACTIVATED",
        authority_ref: { decision_id: "ADR-WIASW-001", clause: "DESTINATION GRAPH NODES",
                         declaration: 'WIASW [root] "WIASW" = the destination' },
        activation_authority_ref: { decision_id: "ADR-WIASW-001", clause: "ACTIVATION",
                                    declaration: "default NOT_ACTIVATED" },
      },
      {
        id: "CIS", label: "CIS — deterministic AI / control substrate", kind: "substrate",
        depth: 0, description: "the substrate beneath WIASW",
        activation_state: "TRACKED_ELSEWHERE",
        authority_ref: { decision_id: "ADR-WIASW-002", clause: "DESTINATION GRAPH NODES",
                         declaration: 'CIS [substrate] "CIS" = the substrate' },
        activation_authority_ref: { decision_id: "ADR-WIASW-002", clause: "ACTIVATION",
                                    declaration: "CIS = TRACKED_ELSEWHERE" },
      },
    ],
    edges: [{
      source: "WIASW", relationship: "uses", target: "CIS",
      source_declared: true, target_declared: true, relationship_defined: true,
      authority_ref: { decision_id: "ADR-WIASW-001", clause: "DESTINATION GRAPH EDGES",
                       declaration: "WIASW uses CIS" },
    }],
    relationships: [{ name: "uses", definition: "built on top of",
                      authority_ref: { decision_id: "ADR-WIASW-001" } }],
    relationship_types_used: ["uses"],
    activation: { default: "NOT_ACTIVATED", vocabulary: [], exceptions: {},
                  note: "activation is not build progress" },
    levels: [{ id: "overview", label: "Level 1 — why", question: "why?", max_depth: 0,
               node_ids: ["WIASW", "CIS"], node_count: 2, mermaid: "flowchart TD\n  WIASW" }],
    mermaid: "flowchart TD\n  WIASW",
    decisions: [], problems: [],
    authority: {},
  };
}

function buildPathPayload() {
  return {
    read_model: "cis_build_path",
    generated_at: "2026-10-02T12:00:00+00:00",
    state_revision: "rev-1",
    status_vocabulary: ["complete", "active", "next", "pending"],
    authority: {
      sequencing: "project_decisions + project_state.pipeline_roadmap (ADR-PIPE-006)",
      work_items: "queue_items + queue_edges (ADR-PIPE-006)",
    },
    roadmap_source: { state_key: "pipeline_roadmap", row_id: 7, recorded_at: null,
                      raw: "P0 (activate the first slice) -> TRIAGE (56 unclassified)",
                      constraints_text: "CONSTRAINTS: triage after P0.", parse_note: null },
    progress: { total_phases: 2, complete: 0, current_order: 0, current_phase_note: null },
    current: {
      phase_id: "P0", label: "P0", status: "active", blocked: true,
      status_label: "active / blocked", task: "WB.1",
      evidence: { state_key: "build_phase", row_id: 9, recorded_at: null,
                  value: "Phase P0 of the P0-P6 sequence" },
    },
    next: { phase_id: "TRIAGE", label: "TRIAGE", status: "next",
            description: "56 unclassified" },
    next_action: { recorded_at: null, source: "manual", text: "Finish P0 closeout." },
    current_direction: { recorded_at: null, source: "manual", text: "P0 blocked." },
    phases: [
      { id: "P0", label: "P0", order: 0, description: "activate the first slice",
        status: "active", blocked: true, status_label: "active / blocked",
        is_current: true, is_next: false, migrations: [], queue_hooks: [],
        constraints: [], discoveries: { counts: { blocking: 1 }, blocking: [], open: [],
                                        deferred: [], resolved: [] }, task: "WB.1" },
      { id: "TRIAGE", label: "TRIAGE", order: 1, description: "56 unclassified",
        status: "next", blocked: false, status_label: "next", is_current: false,
        is_next: true, migrations: [], queue_hooks: [], constraints: [],
        discoveries: null,
        queue_classification: { total_items: 132, unclassified: 56,
                                unclassified_definition: "neither scope nor need_status" } },
    ],
    blockers: [], discoveries: { counts: {}, blocking: [], open: [], deferred: [],
                                 resolved: [] },
    discoveries_note: null,
    queue: { total_items: 132, unclassified: 56 },
    checkpoint: { present: true, lifecycle_state: "REMOTE_REVIEW_REQUIRED",
                  latest_pushed_sha: "abc123", latest_remote_verified_sha: null,
                  pushed_sha_is_independently_verified: false, remote_ref: "origin/master" },
    decisions: [{ id: "ADR-PIPE-001", label: "forward sequence", status: "DECIDED" }],
    mermaid: "flowchart TD\n  P0\n  TRIAGE",
  };
}

function model(overrides = {}) {
  return {
    read_model: "cis_project_intelligence",
    generated_at: "2026-10-02T12:00:00+00:00",
    state_revision: "rev-1",
    missing_link_text: MISSING_LINK,
    missing_plain_language_text: MISSING_PLAIN,
    authority: {
      role: "this is a COMPOSITION layer, not an authority.",
      composes: [{ read_model: "cis_build_path", module: "tools/state/build_path.py",
                   answers: "what are we building now", note: "CALLED, never restated." }],
      reads_directly: [{ source: "queue_items + queue_edges", why: "work-item authority" }],
      never_reads: ["docs/UNIFIED_BUILD_LIST.md"],
      write_paths: "none — the spine is opened mode=ro",
      llm_runtime_calls: "none. No model client is imported",
      status_separation: "five different vocabularies",
    },
    read_only_boundary: ["no queue item is classified, scoped, renumbered, merged or re-titled"],
    confidence_classes: [
      { id: "authoritative", label: "Stated by an authority",
        plain_english: "A decision says this outright.", technical_note: "project_decisions" },
      { id: "derived_from_evidence", label: "Derived from quoted evidence",
        plain_english: "Something checkable implies it.", technical_note: "a literal match" },
      { id: "not_yet_linked", label: "No authoritative link recorded yet",
        plain_english: "Nothing records a connection here.", technical_note: "a deliberate gap" },
    ],
    modes: [
      { id: "simple", label: "Simple", default: true,
        plain_english: "Plain language only.", shows: ["plain_english"] },
      { id: "detail", label: "More Detail", default: false,
        plain_english: "Adds capability and build position.", shows: ["capability"] },
      { id: "technical", label: "Technical", default: false,
        plain_english: "Adds exact identifiers.", shows: ["paths"] },
    ],
    vocabulary_source: { path: "tools/state/project_intelligence_vocabulary.json",
                         provenance_class: "reviewed_static_explanatory_metadata",
                         schema_version: 1, present: true,
                         what_this_is: "reviewed plain-language layer" },
    glossary: [
      { term: "Blueprint", plain_english: "A bundle of web routes that can be plugged into the live application.",
        technical_note: "A Flask Blueprint." },
      { term: "Migration", plain_english: "A controlled database update.",
        technical_note: "A numbered .sql file." },
    ],
    areas: [
      { id: "overview", label: "Overview", plain_question: "How do the parts fit together?",
        plain_english: "A starting point for the other five views." },
      { id: "current_build", label: "Current Build", plain_question: "What are we building now?",
        plain_english: "The sequence the project is working through." },
      { id: "queue_problems", label: "Queue / Problems",
        plain_question: "What work and unresolved problems exist?",
        plain_english: "Two different lists kept apart." },
      { id: "system_anatomy", label: "System Anatomy",
        plain_question: "What capabilities and code exist?",
        plain_english: "The major working parts of CIS." },
      { id: "destination", label: "Destination",
        plain_question: "What are we ultimately building toward?",
        plain_english: "WIASW, the product architecture CIS supports." },
      { id: "trajectory", label: "Trajectory",
        plain_question: "How does today's work move toward that destination?",
        plain_english: "Today's steps, then a separate explanatory link." },
    ],
    counts: { phases: 2, problems: 2, blocking_problems: 1, unresolved_problems: 2,
              queue_items: 132, awaiting_triage: 56, capabilities: 2,
              capabilities_registered: 1, anatomy_areas: 2, destination_nodes: 2,
              relationships: 5, not_yet_linked: 3, problems_reported: 0 },
    current_build: { available: true, error: null, read_model: "cis_build_path",
                     build_path: buildPathPayload() },
    destination: {
      available: true, error: null, read_model: "cis_destination_architecture",
      present: true, architecture_scope: "destination",
      counts: { nodes: 2, edges: 1 },
      activation_note: "activation_state is NOT a build status",
      nodes: [{ id: "WIASW", label: "WIASW", kind: "root",
                activation_state: "NOT_ACTIVATED", authority_ref: {} },
              { id: "CIS", label: "CIS", kind: "substrate",
                activation_state: "TRACKED_ELSEWHERE", authority_ref: {} }],
      endpoint: "GET /api/workbench/destination-architecture",
      note: "referenced, never duplicated",
    },
    capability_model: {
      provenance: {
        class: "derived_from_evidence", authority_exists: false,
        statement: "CIS has no capability authority.",
        candidates_inspected: [{ candidate: "functional_spec", verdict: "rejected",
                                 detail: "a document-block extraction" }],
      },
      states: [
        { id: "REGISTERED", plain_english: "Switched on — the server plugs this in.",
          technical_note: "its blueprint appears in a register_blueprint call" },
        { id: "BUILT_NOT_REGISTERED", plain_english: "Built, but deliberately switched off.",
          technical_note: "the blueprint is not registered" },
      ],
      capabilities: [
        {
          id: "braingate_conversation", label: "Braingate Conversation", anatomy_id: "braingate",
          plain_english: "Allows Eric to talk with Braingate about a project.",
          plain_language_recorded: true, provenance_class: "derived_from_evidence",
          provenance_note: "membership from reviewed static metadata",
          status: "REGISTERED",
          registration: { blueprint: "braingate_conversation_bp", surface: "blueprint",
                          endpoint: "GET/POST /api/workbench/projects …",
                          observed_in: "runtime/container_app.py", registered: true,
                          evidence: "runtime/container_app.py:134 — app.register_blueprint(braingate_conversation_bp)" },
          files: [{ path: "runtime/braingate_conversation.py", exists: true, bytes: 10, lines: 420 }],
          migrations: [{ migration: "0035", applied: true, tables: { workbench_projects: true },
                         detected_by: "presence of the tables 0035 creates" }],
          decision_ids: [], identifier_terms: ["Braingate"],
          build_position: [{ phase_id: "P0", phase_label: "P0", phase_status: "active",
                             confidence_class: "derived_from_evidence",
                             authority_refs: [{ kind: "project_state_row",
                                                state_key: "pipeline_roadmap",
                                                quote: "P0 (activate the first slice)",
                                                matched_term: "first slice" }] }],
          build_position_note: null,
          authority_mentions: [{ source: "build_phase", matched_term: "Braingate",
                                 quote: "Braingate is REGISTERED and PROVEN." }],
          destination_link: { confidence_class: "not_yet_linked",
                              explanation: "No decision links this capability to a destination node." },
          problem_ids: ["WB1-D15"],
        },
        {
          id: "card_factory", label: "Card Factory", anatomy_id: "dormant_execution",
          plain_english: "Would draft a work card using a paid model. Deliberately not plugged in.",
          plain_language_recorded: true, provenance_class: "derived_from_evidence",
          provenance_note: "membership from reviewed static metadata",
          status: "BUILT_NOT_REGISTERED",
          registration: { blueprint: "card_factory_bp", surface: "blueprint", endpoint: null,
                          observed_in: "runtime/container_app.py", registered: false,
                          evidence: "no app.register_blueprint(card_factory_bp) in runtime/container_app.py" },
          files: [{ path: "runtime/card_factory_app.py", exists: true, bytes: 10, lines: 300 }],
          migrations: [{ migration: "0036", applied: false, tables: { card_drafts: false },
                         detected_by: "presence of the tables 0036 creates" }],
          decision_ids: ["ADR-PIPE-005"], identifier_terms: ["Card Factory"],
          build_position: [],
          build_position_note: `No phase in the recorded roadmap names this capability. ${MISSING_LINK}`,
          authority_mentions: [],
          destination_link: { confidence_class: "not_yet_linked",
                              explanation: "No decision links this capability to a destination node." },
          problem_ids: [],
        },
      ],
    },
    anatomy: {
      root: "CIS", note: "major functional areas only — deliberately not the repository tree.",
      mermaid: "flowchart TD\n  CIS\n  BRAINGATE",
      areas: [
        { id: "braingate", label: "Braingate",
          plain_english: "Talking to the system about a project.",
          what_it_does: "Carries project conversation to a model.",
          why_cis_needs_it: "It is the first safe slice of the Workbench.",
          status: "ACTIVE", status_plain: "At least one part of this is switched on.",
          status_derivation: "rolled up from the observed status of the capabilities below",
          capability_ids: ["braingate_conversation"],
          capabilities: [{ id: "braingate_conversation", label: "Braingate Conversation",
                           status: "REGISTERED",
                           plain_english: "Allows Eric to talk with Braingate about a project." }],
          unresolved_capability_ids: [], files: ["runtime/braingate_conversation.py"] },
        { id: "dormant_execution", label: "Dormant Execution Features",
          plain_english: "Finished features that are deliberately switched off.",
          what_it_does: "Card Factory can draft a work card.",
          why_cis_needs_it: "Keeping them unregistered guarantees nothing spends money.",
          status: "DORMANT", status_plain: "Built, and deliberately switched off.",
          status_derivation: "rolled up from the observed status of the capabilities below",
          capability_ids: ["card_factory"],
          capabilities: [{ id: "card_factory", label: "Card Factory",
                           status: "BUILT_NOT_REGISTERED",
                           plain_english: "Would draft a work card using a paid model." }],
          unresolved_capability_ids: [], files: ["runtime/card_factory_app.py"] },
      ],
      files: [
        { path: "runtime/container_app.py",
          plain_english: "The main switchboard for the live CIS server.",
          what_it_does: "Turns specific backend features on by registering them with Flask.",
          why_it_matters: "A capability may exist in code but remain unavailable until this application registers it.",
          technical_role: "Flask application entry point" },
        { path: "runtime/braingate_conversation.py",
          plain_english: "The safety wrapper that permits project conversation while blocking later proposal and execution functions.",
          what_it_does: "Exposes only the project and message routes.",
          why_it_matters: "The boundary is enforced by which routes exist.",
          technical_role: "Flask Blueprint / stage boundary" },
      ],
    },
    problems: {
      note: null,
      statement: "findings recorded during the work",
      items: [
        {
          id: "WB1-D15", task: "WB.1", revision: 65,
          plain_english: "Braingate cannot currently get a real response from DeepSeek.",
          why_it_matters: "The conversation feature is turned on, but its configured model credential is rejected.",
          plain_language_recorded: true,
          plain_language_provenance: "reviewed_static_explanatory_metadata",
          display_status: "blocking", disposition: "BEFORE_STAGE_CLOSEOUT",
          blocking: true, resolved: false, malformed: false,
          status_systems: { discovery_disposition: "BEFORE_STAGE_CLOSEOUT",
                            discovery_display_status: "blocking",
                            note: "a discovery disposition is NOT a build-phase status" },
          summary: "WB1-D15: the Braingate conversation route is live but DEEPSEEK_API_KEY is rejected.",
          summary_truncated: false,
          solution_direction: { confidence_class: "not_yet_linked", text: null,
                                explanation: "Current solution direction: not formally recorded.",
                                authority_refs: [] },
          deferral: null, originating_stage: "WB.1 activation",
          named_in_state: [{ state_key: "next_action", quote: "WB1-D15 is blocked on a credential.",
                             confidence_class: "derived_from_evidence", matched_term: "WB1-D15" }],
          is_current_task: true,
          evidence: { table: "dev_continuity_events", task: "WB.1", revision: 65,
                      recorded_at: "2026-10-01T00:00:00+00:00", kind: "unfinished_work" },
          capability_ids: ["braingate_conversation"],
          build_position: { confidence_class: "derived_from_evidence", phase_id: "P0",
                            phase_label: "P0", phase_status: "active / blocked",
                            explanation: "Recorded against task WB.1, the current task.",
                            authority_refs: [{ kind: "project_state_row",
                                               state_key: "current_queue_item", value: "WB.1" }] },
        },
        {
          id: null, task: "4.32", revision: 2,
          plain_english: MISSING_PLAIN, why_it_matters: null,
          plain_language_recorded: false, plain_language_provenance: null,
          display_status: "open", disposition: "BEFORE_STAGE_CLOSEOUT",
          blocking: false, resolved: false, malformed: false,
          status_systems: { discovery_disposition: "BEFORE_STAGE_CLOSEOUT",
                            discovery_display_status: "open",
                            note: "a discovery disposition is NOT a build-phase status" },
          summary: "An unexplained finding recorded against another task entirely.",
          summary_truncated: false,
          solution_direction: { confidence_class: "not_yet_linked", text: null,
                                explanation: "Current solution direction: not formally recorded.",
                                authority_refs: [] },
          deferral: null, originating_stage: null, named_in_state: [],
          is_current_task: false,
          evidence: { table: "dev_continuity_events", task: "4.32", revision: 2,
                      recorded_at: "2026-09-01T00:00:00+00:00", kind: "unfinished_work" },
          capability_ids: [],
          build_position: { confidence_class: "not_yet_linked",
                            explanation: `This finding is recorded against task 4.32, which is not the current task. ${MISSING_LINK}` },
        },
      ],
    },
    queue: {
      counts: { total_items: 132, unclassified: 56, missing_need_status: 56,
                missing_scope: 69, counts_by_need_status: {},
                unclassified_definition: "neither scope nor need_status" },
      total_items: 132, awaiting_triage: 56, classified: 76,
      distributions: {
        need_status: [{ value: null, count: 56 }, { value: "OPEN", count: 47 }],
        scope: [{ value: null, count: 69 }, { value: "CONTAINER", count: 63 }],
        tier: [{ value: 0, count: 7 }, { value: 1, count: 28 }],
        check_class: [{ value: "RUNNABLE", count: 20 }],
      },
      edge_count: 45,
      items: [
        { item_num: "1.23", tier: 1, title: "A code run has never completed end to end",
          need_status: "OPEN", scope: "CONTAINER", check_class: "RUNNABLE",
          source_line: 412, source_sha: "deadbeef",
          body_excerpt: "### 1.23 A code run has never completed end to end",
          body_truncated: true, awaiting_triage: false, classification_status: "CLASSIFIED",
          plain_english: "A run that actually writes code has never completed from start to finish.",
          why_it_matters: "The pipeline has only been proved on a documentation task.",
          plain_language_recorded: true,
          plain_language_provenance: "reviewed_static_explanatory_metadata",
          phase_hooks: [{ phase_id: "P0", phase_label: "P0",
                          confidence_class: "authoritative",
                          authority_refs: [{ kind: "project_state_row",
                                             state_key: "pipeline_roadmap",
                                             quote: "P0 (activate the first slice)" }] }],
          edges: [{ other: "1.1", direction: "in", kind: "depends_on",
                    confidence_class: "derived_from_evidence", stored_confidence: "prose",
                    evidence: "No run has ever gone intake -> gate." }] },
        { item_num: "2.17", tier: 2, title: "An untriaged work item", need_status: null,
          scope: null, check_class: null, source_line: 800, source_sha: "cafe1234",
          body_excerpt: "### 2.17 An untriaged work item", body_truncated: false,
          awaiting_triage: true, classification_status: "AWAITING TRIAGE",
          plain_english: MISSING_PLAIN, why_it_matters: null,
          plain_language_recorded: false, plain_language_provenance: null,
          phase_hooks: [], edges: [] },
      ],
      stale_vocabulary_item_nums: [],
      triage_state: {
        performed_here: false,
        statement: "Queue triage has NOT been performed by this screen.",
        sequencing: { stage_label: "TRIAGE", stage_status: "next",
                      stage_description: "56 unclassified", authority: "ADR-PIPE-006",
                      constraints_quote: "CONSTRAINTS: triage after P0.",
                      note: "the stage comes from the Build Path read model" },
      },
      authority: "queue_items + queue_edges are the work-item authority",
    },
    trajectory: {
      question: "How does today's work move toward that destination?",
      build_sequence_authority: "the order comes from the Build Path read model",
      mermaid: "flowchart TD\n  P0\n  TRIAGE\n  D_CIS\n  TRIAGE -.-> D_CIS",
      separation_note: "The build steps are chronological. The destination is architectural.",
      steps: [
        { kind: "build_phase", id: "P0", label: "P0", description: "activate the first slice",
          status: "active", status_label: "active / blocked", blocked: true, is_current: true,
          order: 0, queue_hooks: [], capability_ids: [],
          source: "tools/state/build_path.py (project_state.pipeline_roadmap + ADR-PIPE-001)",
          confidence_class: "authoritative" },
        { kind: "build_phase", id: "TRIAGE", label: "TRIAGE", description: "56 unclassified",
          status: "next", status_label: "next", blocked: false, is_current: false, order: 1,
          queue_hooks: [{ item_num: "0.4", found: true, title: "Override plane" }],
          capability_ids: [],
          source: "tools/state/build_path.py (project_state.pipeline_roadmap + ADR-PIPE-001)",
          confidence_class: "authoritative" },
      ],
      destination_relationship: {
        confidence_class: "authoritative", is_phase_ordering: false,
        warning: "Destination relationship — not an automatic next phase.",
        explanation: "This is an explanatory relationship, not a step in the build order. "
                     + "Completing the last build phase does not start destination work.",
        nodes: [
          { node_id: "CIS", label: "CIS — deterministic AI / control substrate",
            kind: "substrate", activation_state: "TRACKED_ELSEWHERE",
            confidence_class: "authoritative",
            explanation: "The destination architecture records CIS as the substrate.",
            authority_refs: [{ kind: "decision_clause", decision_id: "ADR-WIASW-002",
                               clause: "ACTIVATION", declaration: "CIS = TRACKED_ELSEWHERE" }] },
          { node_id: "WIASW", label: "WIASW — Word · Image · Action · Sound + Web",
            kind: "root", activation_state: "NOT_ACTIVATED",
            confidence_class: "authoritative",
            explanation: "The destination architecture states that WIASW uses CIS.",
            authority_refs: [{ kind: "decision_clause", decision_id: "ADR-WIASW-001",
                               clause: "DESTINATION GRAPH EDGES",
                               declaration: "WIASW uses CIS" }] },
        ],
        authority_refs: [],
      },
    },
    relationships: [
      { source: "WB1-D15", target: "braingate_conversation",
        relationship: "problem_concerns_capability",
        confidence_class: "derived_from_evidence",
        authority_refs: [{ kind: "discovery_record", matched_term: "Braingate" }],
        explanation: "The finding's own text names 'Braingate'." },
      { source: "card_factory", target: null,
        relationship: "capability_supports_destination_node",
        confidence_class: "not_yet_linked", authority_refs: [],
        explanation: "No decision links this capability to a destination node." },
    ],
    overview_mermaid: "flowchart LR\n  CURRENT_BUILD\n  QUEUE_PROBLEMS",
    problems_found: [],
    ...overrides,
  };
}

async function renderMap(handler = () => Promise.resolve(ok(model()))) {
  state.handler = handler;
  state.buildPathCalls = 0;
  state.destinationCalls = 0;
  state.renderCalls = [];
  const utils = render(<ProjectMap onBack={() => {}} onOpenBuildPath={() => {}} />);
  await waitFor(() => expect(screen.queryByText("Loading the project map…")).toBeNull());
  return utils;
}

async function goTo(label) {
  await userEvent.click(screen.getByRole("tab", { name: label }));
}

async function setMode(label) {
  await userEvent.click(screen.getByRole("button", { name: label }));
}

beforeEach(() => {
  cleanup();
  state.handler = null;
  state.buildPathCalls = 0;
  state.destinationCalls = 0;
  state.renderCalls = [];
});

describe("ProjectMap — loading and failure", () => {
  it("shows a loading state and then the map", async () => {
    await renderMap();
    expect(screen.getByText("Project Map")).toBeInTheDocument();
    expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual([
      "Overview", "Current Build", "Queue / Problems", "System Anatomy",
      "Destination", "Trajectory",
    ]);
  });

  it("never renders a map from a failed load", async () => {
    await renderMap(() => Promise.resolve(fail("Network error: down")));
    expect(screen.getByText(/Could not load the project map/)).toBeInTheDocument();
    expect(screen.getByText(/filled in from memory or assumption/)).toBeInTheDocument();
    expect(screen.queryByRole("tab")).toBeNull();
  });

  it("keeps a prior successful load visible but marks it STALE", async () => {
    let first = true;
    await renderMap(() => {
      const result = first ? ok(model()) : fail("gateway down");
      first = false;
      return Promise.resolve(result);
    });
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    await waitFor(() => expect(screen.getByText(/^STALE/)).toBeInTheDocument());
    expect(screen.getByText(/may no longer reflect the project's current state/))
      .toBeInTheDocument();
  });

  it("reports one composed view failing without losing the rest of the map", async () => {
    await renderMap(() => Promise.resolve(ok(model({
      current_build: { available: false, error: "RuntimeError: spine unreachable",
                       read_model: null, build_path: null },
    }))));
    await goTo("Current Build");
    expect(screen.getByText(/current-build view is unavailable/)).toBeInTheDocument();
    expect(screen.getByText(/rest of this map still loaded/)).toBeInTheDocument();
    // The other areas still work.
    await goTo("Trajectory");
    expect(screen.getByText("Destination relationship — not an automatic next phase."))
      .toBeInTheDocument();
  });
});

describe("ProjectMap — Overview", () => {
  it("leads with plain language for every area and navigates on click", async () => {
    await renderMap();
    expect(screen.getByText("A starting point for the other five views.")).toBeInTheDocument();
    expect(screen.getByText("What work and unresolved problems exist?")).toBeInTheDocument();
    expect(screen.getByText("56 items awaiting triage", { exact: false })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /System Anatomy →/ }));
    expect(screen.getByText("The working parts of CIS")).toBeInTheDocument();
  });

  it("explains the provenance labels in plain language", async () => {
    await renderMap();
    expect(screen.getByText("A decision says this outright.")).toBeInTheDocument();
    expect(screen.getByText("Nothing records a connection here.")).toBeInTheDocument();
  });

  it("explains every technical term it uses, from the reviewed vocabulary", async () => {
    await renderMap();
    await userEvent.click(screen.getByRole("button", { name: /Show 2 terms/ }));
    expect(screen.getByText("Blueprint")).toBeInTheDocument();
    expect(screen.getByText(
      "A bundle of web routes that can be plugged into the live application.")).toBeInTheDocument();
    expect(screen.getByText("A controlled database update.")).toBeInTheDocument();
    // The technical note is one mode away, not absent.
    expect(screen.queryByText("A Flask Blueprint.")).toBeNull();
    await setMode("More Detail");
    expect(screen.getByText("A Flask Blueprint.")).toBeInTheDocument();
  });

  it("states that it writes nothing and calls no model at page load", async () => {
    await renderMap();
    await setMode("More Detail");
    expect(screen.getByText(/none — the spine is opened mode=ro/)).toBeInTheDocument();
    expect(screen.getByText(/No model client is imported/)).toBeInTheDocument();
    expect(screen.getByText(/no queue item is classified/)).toBeInTheDocument();
  });

  it("names the reviewed vocabulary file as the source of the plain wording", async () => {
    await renderMap();
    expect(screen.getByText("tools/state/project_intelligence_vocabulary.json"))
      .toBeInTheDocument();
    expect(screen.getByText(/never generated while this page loads/)).toBeInTheDocument();
  });
});

describe("ProjectMap — Current Build area reuses the Build Path view", () => {
  it("renders the Build Path panels from the embedded payload without refetching", async () => {
    await renderMap();
    await goTo("Current Build");
    // Panels that live in BuildPath.jsx, rendered here by CurrentBuildPanel.
    expect(screen.getByText("Where the build is")).toBeInTheDocument();
    expect(screen.getByText("P0 → P6 sequence")).toBeInTheDocument();
    expect(screen.getByText("you are here")).toBeInTheDocument();
    // Twice on purpose: the headline and the phase card, both from BuildPath.jsx.
    expect(screen.getAllByText("active / blocked").length).toBe(2);
    // Technical is the level at which the embedded panel shows what the
    // standalone screen shows, which is where the LAST of its panels appears.
    await setMode("Technical");
    expect(screen.getByText("Checkpoint and authority")).toBeInTheDocument();
    // The reuse claim, asserted: the build-path route is never called.
    expect(state.buildPathCalls).toBe(0);
  });

  it("says it is the existing view rather than a second copy", async () => {
    await renderMap();
    await goTo("Current Build");
    expect(screen.getByText(/not a second copy of it/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Open the full Build Path screen/ }))
      .toBeInTheDocument();
  });
});

describe("ProjectMap — Destination area reuses the Destination view", () => {
  it("embeds the destination component, which fetches its own authority", async () => {
    await renderMap();
    expect(state.destinationCalls).toBe(0);
    await goTo("Destination");
    await waitFor(() => expect(state.destinationCalls).toBe(1));
    expect(screen.getByText(/records what CIS is ultimately being built to support/))
      .toBeInTheDocument();
  });

  it("keeps the destination marked not activated", async () => {
    await renderMap();
    await goTo("Destination");
    await waitFor(() => expect(state.destinationCalls).toBe(1));
    expect(screen.getAllByText("not activated").length).toBeGreaterThan(0);
  });
});

describe("ProjectMap — Queue / Problems", () => {
  it("distinguishes the 56 untriaged items from classified work, and triages nothing", async () => {
    await renderMap();
    await goTo("Queue / Problems");
    expect(screen.getByText("56 items awaiting formal triage")).toBeInTheDocument();
    expect(screen.getByText("76 already classified")).toBeInTheDocument();
    expect(screen.getByText("Queue triage has not been performed.")).toBeInTheDocument();
    expect(screen.getByText(/Queue triage has NOT been performed by this screen/))
      .toBeInTheDocument();
  });

  // NEGATIVE TEST for the Workbench projection defect measured 2026-10-08.
  // Already recorded twice as an observation and deliberately left unfixed:
  // project_state.queue_projection_observation row 163, and
  // project_state.external_dev_checkpoint row 184 non-blocking observation 3.
  //
  // The headline below used to be a HARDCODED LITERAL rendered
  // unconditionally, so against the live production counts (awaiting_triage 0
  // of 133) this panel asserted the classification pass was outstanding while
  // its own pills, two lines above, read "0 items awaiting formal triage" and
  // "133 already classified". The literal also DROPPED the "by this screen"
  // qualifier that the read model's own triage_state.statement carries,
  // converting a true statement about this component's read-only nature into a
  // false one about the project's state.
  //
  // This asserts the unscoped claim is gone once the queue authority reports
  // zero awaiting, and that the read model's scoped statement still shows. It
  // deliberately asserts NOTHING about whether the QUEUE_TRIAGE *stage* is
  // complete: stage status is phase authority (ADR-PIPE-006,
  // project_state.pipeline_roadmap) and is not this component's to derive. The
  // sequencing line below the headline still reports the stage exactly as the
  // Build Path read model gives it.
  it("does not claim the classification pass is outstanding once the queue authority reports zero awaiting", async () => {
    const base = model();
    await renderMap(() => Promise.resolve(ok(model({
      queue: {
        ...base.queue,
        total_items: 133,
        awaiting_triage: 0,
        classified: 133,
        counts: { ...base.queue.counts, total_items: 133, unclassified: 0,
                  missing_need_status: 0 },
      },
    }))));
    await goTo("Queue / Problems");
    expect(screen.getByText("0 items awaiting formal triage")).toBeInTheDocument();
    expect(screen.getByText("133 already classified")).toBeInTheDocument();
    // The defect: this unscoped sentence must not survive a zero count.
    expect(screen.queryByText("Queue triage has not been performed.")).toBeNull();
    // The read model's own scoped statement is a read-only-boundary
    // disclosure and must still be present either way.
    expect(screen.getByText(/Queue triage has NOT been performed by this screen/))
      .toBeInTheDocument();
  });

  it("keeps problems and queue items as two separate lists", async () => {
    await renderMap();
    await goTo("Queue / Problems");
    expect(screen.getByText(/are not the same list/)).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Problems \/ discoveries/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Queue items/ })).toBeInTheDocument();
  });

  it("drills into a blocking problem and refuses to invent a solution", async () => {
    await renderMap();
    await goTo("Queue / Problems");
    await userEvent.click(screen.getByRole("button", { name: /WB1-D15/ }));
    // In the list and again in the detail panel — the list is plain-language too.
    expect(screen.getAllByText(
      "Braingate cannot currently get a real response from DeepSeek.").length).toBe(2);
    expect(screen.getByText(/configured model credential is rejected/)).toBeInTheDocument();
    expect(screen.getByText("Current solution direction")).toBeInTheDocument();
    expect(screen.getByText(MISSING_LINK)).toBeInTheDocument();
    expect(screen.getByText(/not formally recorded/)).toBeInTheDocument();
    // The technical text is kept, not replaced by the plain wording.
    expect(screen.getByText(/DEEPSEEK_API_KEY/)).toBeInTheDocument();
  });

  it("shows the build relationship and the capability only in More Detail", async () => {
    await renderMap();
    await goTo("Queue / Problems");
    await userEvent.click(screen.getByRole("button", { name: /WB1-D15/ }));
    expect(screen.queryByText("Build relationship")).toBeNull();
    await setMode("More Detail");
    expect(screen.getByText("Build relationship")).toBeInTheDocument();
    expect(screen.getByText("Capability this concerns")).toBeInTheDocument();
    expect(screen.getByText(/Named in the project's own recorded state/)).toBeInTheDocument();
    expect(screen.getByText(/WB1-D15 is blocked on a credential/)).toBeInTheDocument();
  });

  it("breaks the chain for a finding recorded against a different task", async () => {
    await renderMap();
    await goTo("Queue / Problems");
    await setMode("More Detail");
    await userEvent.click(screen.getByRole("button", { name: /#2/ }));
    expect(screen.getByText(MISSING_PLAIN)).toBeInTheDocument();
    expect(screen.getAllByText(MISSING_LINK).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/which is not the current task/)).toBeInTheDocument();
  });

  it("marks an untriaged queue item AWAITING TRIAGE without classifying it", async () => {
    await renderMap();
    await goTo("Queue / Problems");
    await userEvent.click(screen.getByRole("tab", { name: /Queue items/ }));
    await userEvent.click(screen.getByRole("button", { name: /2\.17/ }));
    expect(screen.getAllByText("AWAITING TRIAGE").length).toBeGreaterThan(0);
    expect(screen.getByText(/Nothing on this screen assigns either one/)).toBeInTheDocument();
    expect(screen.getByText(MISSING_PLAIN)).toBeInTheDocument();
    expect(screen.getByText("### 2.17 An untriaged work item")).toBeInTheDocument();
  });

  it("shows a classified item's roadmap link as authoritative, with the roadmap quoted", async () => {
    await renderMap();
    await goTo("Queue / Problems");
    await userEvent.click(screen.getByRole("tab", { name: /Queue items/ }));
    await userEvent.click(screen.getByRole("button", { name: /Classified \(76\)/ }));
    await userEvent.click(screen.getByRole("button", { name: /1\.23/ }));
    expect(screen.getByText(
      "A run that actually writes code has never completed from start to finish."))
      .toBeInTheDocument();
    expect(screen.getByText("Build-phase relationship")).toBeInTheDocument();
    expect(screen.getByText("Stated by an authority")).toBeInTheDocument();
    await setMode("Technical");
    expect(screen.getByText(/P0 \(activate the first slice\)/)).toBeInTheDocument();
    expect(screen.getByText(/queue_items.item_num = 1.23/)).toBeInTheDocument();
  });

  it("does not upgrade a prose queue edge to authoritative", async () => {
    await renderMap();
    await goTo("Queue / Problems");
    await setMode("Technical");
    await userEvent.click(screen.getByRole("tab", { name: /Queue items/ }));
    await userEvent.click(screen.getByRole("button", { name: /Classified \(76\)/ }));
    await userEvent.click(screen.getByRole("button", { name: /1\.23/ }));
    expect(screen.getByText("Known relationships to other items")).toBeInTheDocument();
    expect(screen.getByText(/stored confidence/)).toBeInTheDocument();
    expect(screen.getByText("prose")).toBeInTheDocument();
  });
});

describe("ProjectMap — System Anatomy", () => {
  it("shows major functional areas, not a repository tree", async () => {
    await renderMap();
    await goTo("System Anatomy");
    expect(screen.getByText(/deliberately not the repository tree/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Braingate active/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Dormant Execution Features dormant/ }))
      .toBeInTheDocument();
  });

  it("answers what / does / why / on for an area", async () => {
    await renderMap();
    await goTo("System Anatomy");
    expect(screen.getByText("What is this?")).toBeInTheDocument();
    expect(screen.getByText("What does it do?")).toBeInTheDocument();
    expect(screen.getByText("Why does CIS need it?")).toBeInTheDocument();
    expect(screen.getByText("Is it on?")).toBeInTheDocument();
    expect(screen.getByText("At least one part of this is switched on."))
      .toBeInTheDocument();
  });

  it("declares the capability view derived, with no authority behind it", async () => {
    await renderMap();
    await goTo("System Anatomy");
    expect(screen.getByText(/CIS does not record a list of capabilities anywhere/))
      .toBeInTheDocument();
    expect(screen.getByText("CIS has no capability authority.")).toBeInTheDocument();
    await setMode("Technical");
    expect(screen.getByText("functional_spec")).toBeInTheDocument();
    expect(screen.getByText("rejected")).toBeInTheDocument();
  });

  it("drills from an area into a capability and shows observed registration", async () => {
    await renderMap();
    await goTo("System Anatomy");
    await userEvent.click(screen.getByRole("button", { name: "Braingate Conversation →" }));
    expect(screen.getByText("Is it switched on?")).toBeInTheDocument();
    expect(screen.getByText("Switched on — the server plugs this in.")).toBeInTheDocument();
    expect(screen.getByText(/app\.register_blueprint\(braingate_conversation_bp\)/))
      .toBeInTheDocument();
    expect(screen.getByText(/Braingate is REGISTERED and PROVEN/)).toBeInTheDocument();
  });

  it("shows a dormant capability as built-but-switched-off with its migration not applied",
     async () => {
    await renderMap();
    await goTo("System Anatomy");
    await userEvent.click(screen.getByRole("button", { name: /Dormant Execution Features/ }));
    await userEvent.click(screen.getByRole("button", { name: "Card Factory →" }));
    expect(screen.getByText("Built, but deliberately switched off.")).toBeInTheDocument();
    expect(screen.getByText(/no app\.register_blueprint\(card_factory_bp\)/))
      .toBeInTheDocument();
    expect(screen.getByText("not applied")).toBeInTheDocument();
  });

  it("drills from a capability into a file and explains it in plain language", async () => {
    await renderMap();
    await goTo("System Anatomy");
    await userEvent.click(screen.getByRole("button", { name: "Braingate Conversation →" }));
    await userEvent.click(screen.getByRole("button",
                                           { name: "runtime/braingate_conversation.py" }));
    expect(screen.getByText(/safety wrapper that permits project conversation/))
      .toBeInTheDocument();
    expect(screen.getByText(/boundary is enforced by which routes exist/)).toBeInTheDocument();
  });

  it("breaks the capability → destination chain rather than inventing it", async () => {
    await renderMap();
    await goTo("System Anatomy");
    await setMode("More Detail");
    await userEvent.click(screen.getByRole("button", { name: "Braingate Conversation →" }));
    expect(screen.getByText("Larger goal it supports")).toBeInTheDocument();
    expect(screen.getByText(MISSING_LINK)).toBeInTheDocument();
    expect(screen.getByText(/No decision links this capability to a destination node/))
      .toBeInTheDocument();
  });

  it("breaks the capability → build-phase chain where the roadmap does not name it",
     async () => {
    await renderMap();
    await goTo("System Anatomy");
    await setMode("More Detail");
    await userEvent.click(screen.getByRole("button", { name: /Dormant Execution Features/ }));
    await userEvent.click(screen.getByRole("button", { name: "Card Factory →" }));
    expect(screen.getByText("Where it fits in the current build")).toBeInTheDocument();
    expect(screen.getByText(/No phase in the recorded roadmap names this capability/))
      .toBeInTheDocument();
  });
});

describe("ProjectMap — Trajectory", () => {
  it("shows today's steps in the composed order", async () => {
    await renderMap();
    await goTo("Trajectory");
    const steps = screen.getAllByRole("listitem")
      .filter((li) => li.className.includes("pm-step"));
    expect(steps.map((li) => li.querySelector("strong").textContent)).toEqual(["P0", "TRIAGE"]);
    expect(screen.getByText("you are here")).toBeInTheDocument();
  });

  it("marks the destination relationship as explanatory, not a next phase", async () => {
    await renderMap();
    await goTo("Trajectory");
    expect(screen.getByText("Destination relationship — not an automatic next phase."))
      .toBeInTheDocument();
    expect(screen.getByText(/does not start destination work/)).toBeInTheDocument();
    expect(screen.getByText(/The build steps are chronological/)).toBeInTheDocument();
  });

  it("shows the destination nodes as not activated, with their decision quoted", async () => {
    await renderMap();
    await goTo("Trajectory");
    expect(screen.getByText("tracked elsewhere")).toBeInTheDocument();
    expect(screen.getByText("not activated")).toBeInTheDocument();
    await setMode("Technical");
    expect(screen.getByText("ADR-WIASW-002")).toBeInTheDocument();
    expect(screen.getByText(/CIS = TRACKED_ELSEWHERE/)).toBeInTheDocument();
    // The edge appears as the quoted declaration AND inside the explanation.
    expect(screen.getAllByText(/WIASW uses CIS/).length).toBe(2);
    expect(screen.getByText(/is_phase_ordering/)).toBeInTheDocument();
    expect(screen.getByText("false")).toBeInTheDocument();
  });

  it("names what a step establishes only where the roadmap supports it", async () => {
    await renderMap();
    await goTo("Trajectory");
    await setMode("More Detail");
    // P0's description names the capability's declared term, so it resolves.
    expect(screen.getByText(/What this step is meant to establish/)).toBeInTheDocument();
    expect(screen.getByText(/Braingate Conversation/)).toBeInTheDocument();
    // The other step does not, and the chain is broken rather than filled in.
    expect(screen.getAllByText(MISSING_LINK).length).toBe(1);
    expect(screen.getAllByText(/does not name a capability/).length).toBe(1);
    expect(screen.getByText(/work items the roadmap names here/)).toBeInTheDocument();
  });
});

describe("ProjectMap — progressive disclosure", () => {
  it("defaults to Simple and never discards technical truth, only defers it", async () => {
    await renderMap();
    expect(screen.getByRole("button", { name: "Simple" })).toHaveAttribute(
      "aria-pressed", "true");
    await goTo("System Anatomy");
    await userEvent.click(screen.getByRole("button", { name: "Braingate Conversation →" }));
    // Simple: plain language and the file path, no line counts or endpoints.
    expect(screen.getByText("Allows Eric to talk with Braingate about a project."))
      .toBeInTheDocument();
    expect(screen.queryByText(/GET\/POST \/api\/workbench\/projects/)).toBeNull();
    expect(screen.queryByText(/\(420 lines\)/)).toBeNull();

    await setMode("Technical");
    expect(screen.getByText(/GET\/POST \/api\/workbench\/projects/)).toBeInTheDocument();
    expect(screen.getByText("(420 lines)")).toBeInTheDocument();
    expect(screen.getByText(/presence of the tables 0035 creates/)).toBeInTheDocument();
    expect(screen.getByText("derived_from_evidence")).toBeInTheDocument();
  });

  it("offers exactly the three modes the read model declares", async () => {
    await renderMap();
    for (const label of ["Simple", "More Detail", "Technical"]) {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    }
  });
});

// PM-D3. The mode selector is one GLOBAL control, and before this it reached
// only the four areas this component draws itself: the Current Build area
// handed <CurrentBuildPanel> no mode and the Destination area handed
// <DestinationArchitecture/> none, so the two largest areas did not respond to
// it at all. Every assertion below is about WHAT IS DISCLOSED, never about how
// much text a mode produces — a character-count contract would pass on a screen
// that deferred the wrong things.
describe("ProjectMap — PM-D3: the mode reaches the two reused views", () => {
  it("drives the reused Current Build view: where we are, then the evidence, then the ids",
     async () => {
    await renderMap();
    await goTo("Current Build");

    // Simple — where we are, whether blocked, what is next, the roadmap, and
    // the phase in plain language. No row ids, no migration mechanics, no
    // provenance, no checkpoint block.
    expect(screen.getAllByText("active / blocked").length).toBe(2);
    expect(screen.getByText(/stage 1 of 2/)).toBeInTheDocument();
    expect(screen.getByText("Next stage")).toBeInTheDocument();
    expect(screen.getByText("Finish P0 closeout.")).toBeInTheDocument();
    expect(screen.getByText("activate the first slice")).toBeInTheDocument();
    expect(screen.queryByText("Checkpoint and authority")).toBeNull();
    expect(screen.queryByText(/project_state.next_action/)).toBeNull();
    expect(screen.queryByText("Triage subject")).toBeNull();
    expect(screen.queryByText(/current task: WB\.1/)).toBeNull();

    // More Detail — the blockers' context, the queue hooks and the triage
    // subject, the checkpoint state. Still no identifiers.
    await setMode("More Detail");
    expect(screen.getByText("Triage subject")).toBeInTheDocument();
    expect(screen.getByText(/56 unclassified of 132 queue_items/)).toBeInTheDocument();
    expect(screen.getByText("Checkpoint and authority")).toBeInTheDocument();
    expect(screen.getByText(/current task: WB\.1/)).toBeInTheDocument();
    expect(screen.queryByText(/abc123/)).toBeNull();
    expect(screen.queryByText(/row 9/)).toBeNull();

    // Technical — the exact identifiers and the evidence behind them, including
    // the way into the quoted roadmap row and the decisions it rests on.
    await setMode("Technical");
    expect(screen.getByText("abc123")).toBeInTheDocument();
    expect(screen.getByText(/project_state.next_action/)).toBeInTheDocument();
    // Twice: the build model's own revision line, and the map's footer.
    expect(screen.getAllByText(/state revision/).length).toBe(2);
    await userEvent.click(screen.getByRole("button", { name: /Show the roadmap row/ }));
    expect(screen.getByText(/P0 \(activate the first slice\) -> TRIAGE/)).toBeInTheDocument();
    expect(screen.getByText(/ADR-PIPE-001/)).toBeInTheDocument();
  });

  it("drives the reused Destination view: the hierarchy, then the meanings, then the ADRs",
     async () => {
    await renderMap();
    await goTo("Destination");
    await waitFor(() => expect(state.destinationCalls).toBe(1));

    // Simple — the plain-language hierarchy and the relationships that are not
    // just nesting, named by LABEL. No ids, no kinds, no decision clauses.
    expect(screen.getByTestId("da-outline")).toBeInTheDocument();
    expect(screen.getByText("WIASW — Word · Image · Action · Sound + Web"))
      .toBeInTheDocument();
    expect(screen.getByText("CIS — deterministic AI / control substrate"))
      .toBeInTheDocument();
    expect(screen.getByText("the substrate beneath WIASW")).toBeInTheDocument();
    // "WIASW uses CIS", written with the target's label rather than its id.
    expect(screen.getByText(/→ CIS — deterministic AI \/ control substrate/))
      .toBeInTheDocument();
    expect(screen.getAllByText("not activated").length).toBeGreaterThan(0);
    expect(screen.queryByText("Every recorded element")).toBeNull();
    expect(screen.queryByText("Authority")).toBeNull();
    expect(screen.queryByText(/declared by ADR-WIASW-001/)).toBeNull();
    expect(screen.queryByText("2 nodes")).toBeNull();

    // More Detail — what the relationships and the activation states MEAN, and
    // every node as a card. The decision ids stay deferred.
    await setMode("More Detail");
    expect(screen.getByText("Every recorded element")).toBeInTheDocument();
    expect(screen.getByText("What the relationships mean")).toBeInTheDocument();
    expect(screen.getByText(/built on top of/)).toBeInTheDocument();
    expect(screen.getByText(/activation is not build progress/)).toBeInTheDocument();
    expect(screen.getByText("2 nodes")).toBeInTheDocument();
    expect(screen.queryByText(/declared by ADR-WIASW-001/)).toBeNull();
    expect(screen.queryByText("Authority")).toBeNull();

    // Technical — the node ids, kinds, depths, the declaring ADR and clause.
    await setMode("Technical");
    expect(screen.getByText("Authority")).toBeInTheDocument();
    expect(screen.getByText(/declared by ADR-WIASW-001 \(DESTINATION GRAPH NODES\)/))
      .toBeInTheDocument();
    expect(screen.getByText(/root · depth 0/)).toBeInTheDocument();
    expect(screen.getByText("WIASW")).toBeInTheDocument();
    expect(screen.getByText(/→ CIS$/)).toBeInTheDocument();
  });

  it("does not duplicate either view to do it", async () => {
    // The reuse the fix had to preserve: Current Build still renders from the
    // EMBEDDED build payload (no second fetch), and Destination still fetches
    // its own authority exactly once, through the component that owns it.
    await renderMap();
    await goTo("Current Build");
    await setMode("Technical");
    expect(state.buildPathCalls).toBe(0);
    await goTo("Destination");
    await waitFor(() => expect(state.destinationCalls).toBe(1));
    await setMode("Simple");
    await setMode("Technical");
    // Changing the level of detail is presentation only: it re-reads nothing.
    expect(state.destinationCalls).toBe(1);
    expect(state.buildPathCalls).toBe(0);
  });
});

describe("ProjectMap — PM-D3: the control acknowledges the tap", () => {
  it("says what the selected level means, in the read model's own words", async () => {
    await renderMap();
    const note = screen.getByTestId("pm-mode-note");
    // Eric found PM-D3 on a phone, where what a mode reveals can be a long
    // scroll below the buttons. The acknowledgement sits with the control.
    expect(note.textContent).toBe("Simple — Plain language only.");
    await setMode("More Detail");
    expect(screen.getByTestId("pm-mode-note").textContent)
      .toBe("More Detail — Adds capability and build position.");
    await setMode("Technical");
    expect(screen.getByTestId("pm-mode-note").textContent)
      .toBe("Technical — Adds exact identifiers.");
  });

  it("announces the change rather than only colouring it", async () => {
    await renderMap();
    const note = screen.getByTestId("pm-mode-note");
    expect(note).toHaveAttribute("role", "status");
    expect(note).toHaveAttribute("aria-live", "polite");
    // The pressed state is on the buttons themselves, and exactly one of them.
    const pressed = () => ["Simple", "More Detail", "Technical"]
      .filter((l) => screen.getByRole("button", { name: l })
        .getAttribute("aria-pressed") === "true");
    expect(pressed()).toEqual(["Simple"]);
    await setMode("Technical");
    expect(pressed()).toEqual(["Technical"]);
  });

  it("is reachable and operable from the keyboard", async () => {
    await renderMap();
    const technical = screen.getByRole("button", { name: "Technical" });
    technical.focus();
    expect(technical).toHaveFocus();
    await userEvent.keyboard("{Enter}");
    expect(technical).toHaveAttribute("aria-pressed", "true");
    const simple = screen.getByRole("button", { name: "Simple" });
    simple.focus();
    await userEvent.keyboard(" ");
    expect(simple).toHaveAttribute("aria-pressed", "true");
    expect(technical).toHaveAttribute("aria-pressed", "false");
  });

  it("keeps the screen-reader separators between adjacent list spans", async () => {
    // The accessibility correction made alongside the Project Map itself: three
    // pm-list-item call sites rendered adjacent spans with no separator, so a
    // screen reader announced "BraingateactiveTalking to the system…".
    await renderMap();
    await goTo("System Anatomy");
    const item = screen.getByRole("button", { name: /^Braingate active/ });
    expect(item.textContent).toBe(
      "Braingate active Talking to the system about a project.");
  });
});

// §8 of the card: these two areas measured as under-differentiated. The
// additions below are DERIVED from rows the response already carries — no
// content is manufactured to make a level look different, and where a level has
// nothing valid to add, the subsection is left alone.
describe("ProjectMap — PM-D3: Queue / Problems and System Anatomy differentiation", () => {
  it("defines the two lists at More Detail and names their authority at Technical",
     async () => {
    await renderMap();
    await goTo("Queue / Problems");
    expect(screen.queryByText(/^Findings:/)).toBeNull();
    expect(screen.queryByText(/Awaiting triage means/)).toBeNull();
    expect(screen.queryByText(/ADR-PIPE-006/)).toBeNull();

    await setMode("More Detail");
    expect(screen.getByText(/findings recorded during the work/)).toBeInTheDocument();
    expect(screen.getByText(/neither scope nor need_status/)).toBeInTheDocument();
    expect(screen.getByText(/CONSTRAINTS: triage after P0/)).toBeInTheDocument();
    expect(screen.queryByText(/ADR-PIPE-006/)).toBeNull();

    await setMode("Technical");
    expect(screen.getByText("ADR-PIPE-006")).toBeInTheDocument();
    expect(screen.getByText(/queue_items \+ queue_edges are the work-item authority/))
      .toBeInTheDocument();
    expect(screen.getByText(/records 45 relationships between items/)).toBeInTheDocument();
  });

  it("relates an anatomy area to its capabilities and findings at More Detail", async () => {
    await renderMap();
    await goTo("System Anatomy");
    // Simple: what it is, what it does, why, whether it is on.
    expect(screen.getByText("Is it on?")).toBeInTheDocument();
    expect(screen.queryByText("How much of this area is switched on")).toBeNull();
    expect(screen.queryByText("Problems recorded against this area")).toBeNull();

    await setMode("More Detail");
    expect(screen.getByText("How much of this area is switched on")).toBeInTheDocument();
    expect(screen.getByText(/1 of 1 capability is plugged into the live application/))
      .toBeInTheDocument();
    expect(screen.getByText("Problems recorded against this area")).toBeInTheDocument();
    expect(screen.getByText("WB1-D15")).toBeInTheDocument();
    // Still no paths or derivations — those are Technical.
    expect(screen.queryByText("Files that implement it")).toBeNull();

    await setMode("Technical");
    expect(screen.getByText("Files that implement it")).toBeInTheDocument();
    expect(screen.getByText(/rolled up from the observed status/)).toBeInTheDocument();
  });

  it("reports a dormant area's capabilities as switched off, from their own status",
     async () => {
    await renderMap();
    await goTo("System Anatomy");
    await setMode("More Detail");
    await userEvent.click(screen.getByRole("button", { name: /^Dormant Execution Features/ }));
    expect(screen.getByText(/0 of 1 capability is plugged into the live application/))
      .toBeInTheDocument();
    expect(screen.getByText(/Still off: Card Factory/)).toBeInTheDocument();
    expect(screen.getByText(/No recorded finding names a capability in this area/))
      .toBeInTheDocument();
  });
});

describe("ProjectMap — read-only", () => {
  it("imports no mutating api.js function", async () => {
    const api = await import("./api");
    expect(Object.keys(api).sort()).toEqual([
      "getBuildPath", "getDestinationArchitecture", "getProjectIntelligence",
    ]);
  });

  it("asks the server for the map once per load and sends it nothing", async () => {
    const calls = [];
    await renderMap((...args) => {
      calls.push(args);
      return Promise.resolve(ok(model()));
    });
    expect(calls).toEqual([[]]);
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    await waitFor(() => expect(calls.length).toBe(2));
    expect(calls.every((c) => c.length === 0)).toBe(true);
  });

  it("holds no roadmap, destination graph or capability list of its own", async () => {
    // Every area rendered against a model whose content is deliberately not
    // production's. Nothing from the real project may appear.
    await renderMap(() => Promise.resolve(ok(model({
      areas: [{ id: "overview", label: "Overview", plain_question: "q?",
                plain_english: "only this" }],
      counts: { ...model().counts, awaiting_triage: 0 },
      overview_mermaid: "flowchart LR\n  ONLY",
      glossary: [],
    }))));
    expect(screen.getByText("only this")).toBeInTheDocument();
    expect(screen.queryByText(/WIASW/)).toBeNull();
    expect(screen.queryByText(/Braingate/)).toBeNull();
    expect(screen.getAllByRole("tab").length).toBe(1);
  });

  it("renders the diagrams the server generated, never one it composed", async () => {
    await renderMap();
    await waitFor(() => expect(state.renderCalls.length).toBeGreaterThan(0));
    expect(state.renderCalls.at(-1).source).toBe("flowchart LR\n  CURRENT_BUILD\n  QUEUE_PROBLEMS");
    await goTo("Trajectory");
    await waitFor(() => expect(state.renderCalls.at(-1).source)
      .toBe("flowchart TD\n  P0\n  TRIAGE\n  D_CIS\n  TRIAGE -.-> D_CIS"));
  });
});
