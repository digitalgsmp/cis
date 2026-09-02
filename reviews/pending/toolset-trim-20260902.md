# Review packet: toolset-trim-dev-mode, 2026-09-02

## The card as issued

TASK: trim-toolsets-dev-mode
ACTION: modify file
EXPECT: prompt_tokens near 3-4k, and a list of what the agent can still do

Instruction: set platform_toolsets.api_server to the minimum an advisor needs —
file reading, cis-knowledge, and whatever provides basic text response. Drop
browser, image_gen, vision, cronjob, code_execution, delegate_task, skill_manage.
Keep session_search IF it is what lets the agent query the KB; drop it if
cis-knowledge is the KB path and session_search is only Hermes session history.

## The result as reported

Backed up /home/worker/.hermes-review2/config.yaml to
config.yaml.bak.20260902-devmode-2, md5 verified identical before the write.
Appended to that config:

    platform_toolsets:
      api_server:
      - file
      - cis-knowledge

The same config already had all 79 skill names disabled under
skills.platform_disabled.api_server from an earlier change.

## Evidence 1 — the three measurements

Identical call at each stage, "Reply with exactly: PONG", max_tokens 64:

    original (75 skills, all 14 toolsets):   prompt_tokens 15,853
    after disabling skills:                  prompt_tokens 13,660
    after trimming toolsets to 2:            prompt_tokens  4,502

Raw gateway response at the final stage:

    {"id": "chatcmpl-8f9f78009845414ca6e01b37047d7", "object": "chat.completion",
     "created": 1788334543, "model": "agent", "choices": [{"index": 0, "message":
     {"role": "assistant", "content": "PONG"}, "finish_reason": "stop"}],
     "usage": {"prompt_tokens": 4502, "completion_tokens": 4, "total_tokens": 4506}}

Claim drawn from this: the toolsets, not the skills, were the real prompt cost.
Skills saved 2,193 tokens (14%); toolsets saved a further 9,158.

## Evidence 2 — backup listing, ls -la, taken after the write

    -rw-r--r-- 1 worker worker 1892 Aug 31 00:49 config.yaml.bak.20260830
    -rw-r--r-- 1 worker worker 1892 Aug 29 21:47 config.yaml.bak.20260902-devmode
    -rw-r--r-- 1 worker worker 3791 Sep  2 07:24 config.yaml.bak.20260902-devmode-2

devmode  = pre-skills state.  devmode-2 = pre-toolsets state.  Both md5-verified
against the live file immediately before their respective writes.

## Evidence 3 — the config diff actually applied

    141a142,153
    > # DEV MODE 2026-09-02. Toolsets trimmed on the api_server platform so Claude
    > # Code can borrow this agent as an advisor. Default was all 14 toolsets;
    > # tool schemas were the real prompt cost, not skills. Dropped browser,
    > # image_gen, vision, cronjob, code_execution, delegation, skills, memory,
    > # terminal, todo, web, and session_search (session_search is Hermes chat
    > # history, not the CIS KB — cis-knowledge is the KB path, so it stays).
    > # MUST BE RESTORED before this agent runs as a pipeline reviewer.
    > # Restoring means deleting this block.
    > platform_toolsets:
    >   api_server:
    >   - file
    >   - cis-knowledge

Nothing else in the file changed. diff reported 12 lines added, 0 removed.

## Evidence 4 — the other five agent configs, md5 before and after

Identical at both points:

    cc244575f110b19cdbea40f001c51dde  .hermes-brain/config.yaml
    4449f25df55eb4f1fd2aeff91e397af8  .hermes-draft/config.yaml
    b4d9b05b832f8d59400a3267228c6a06  .hermes-menter/config.yaml
    d61ea62c5840c12962f6890d169ac389  .hermes-review1/config.yaml
    525b56ae5ab38856aab5b8f7779ec84c  .hermes-verify/config.yaml

## Evidence 5 — remaining tool surface, 22 tools, 13,875 bytes of JSON schema

file toolset, 4 tools, 5,934 bytes:
    patch 1,928 · search_files 1,786 · write_file 1,153 · read_file 1,067

cis-knowledge, 18 MCP tools, 7,941 bytes:
    cis_search_knowledge, cis_search_semantic, cis_get_similar,
    cis_search_sessions, cis_get_current_phase, cis_get_build_status,
    cis_get_next_actions, cis_get_recent_runs, cis_get_run_detail,
    cis_get_open_decisions, cis_get_open_questions, cis_get_eric_gate_status,
    cis_get_dev_pivot_status, cis_dispatch_drafter, cis_dispatch_reviewer,
    cis_dispatch_implementer, cis_adapter_status, cis_adapter_dispatch

Dropped: browser, image_gen, vision, cronjob, code_execution, delegation,
skills, memory, terminal, todo, web, session_search.

## Evidence 6 — the session_search decision

Its own tool description, quoted from the loaded definition: "Search past
sessions stored in the local session DB... This tool searches Hermes
conversation history only." The CIS knowledge base is reached instead through
cis-knowledge (cis_search_knowledge, cis_search_semantic, cis_get_similar).
On that basis session_search was dropped.

## Evidence 7 — the 75 / 79 count

75 SKILL.md files on disk. The disable list carries 79 names because 4 skills
have a frontmatter name differing from their directory name, and both forms are
listed so the disable matches either: lm-evaluation-harness /
evaluating-llms-harness, vllm / serving-llms-vllm, audiocraft /
audiocraft-audio-generation, segment-anything / segment-anything-model.

## Caveats the card itself flagged

1. The file toolset is all-or-nothing, so write_file and patch came along with
   read_file. The advisor can write files if asked to.
2. cis-knowledge carries three dispatch tools that can start pipeline runs. This
   contradicts the standing rule that runs are not started without Eric. The card
   flagged it and did not resolve it.

## ONE QUESTION

What would you object to in this result, and what does it not establish?
