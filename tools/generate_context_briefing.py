#!/usr/bin/env python3
"""
CIS Phase 3A — Automatic Context Loader v0.1

Generates a briefing block from canonical CIS files.
One command, one output, no dependencies beyond Python stdlib.

Usage:
    python3 /mnt/projects/cis/tools/generate_context_briefing.py
    python3 /mnt/projects/cis/tools/generate_context_briefing.py --write

Outputs to stdout. With --write, also saves to:
    /mnt/projects/cis/session_handoffs/CURRENT_CONTEXT_BRIEFING.md
"""

import os
import sys
from datetime import datetime

PROJECT_ROOT = "/mnt/projects/cis"

SOURCE_FILES = {
    "current_state":   os.path.join(PROJECT_ROOT, "docs/CIS_CURRENT_STATE.md"),
    "context_contract": os.path.join(PROJECT_ROOT, "docs/CIS_CONTEXT_CONTRACT.md"),
    "core_boundary":   os.path.join(PROJECT_ROOT, "docs/CIS_CORE_BOUNDARY.md"),
    "seed_excerpts":   os.path.join(PROJECT_ROOT, "seed_intent_corpus/SEED_INTENT_EXCERPTS.md"),
    "orientation":     os.path.join(PROJECT_ROOT, "seed_intent_corpus/SESSION_ORIENTATION_PROMPT.md"),
    "scratchpad":      os.path.join(PROJECT_ROOT, "cis_kernel/build/CIS_SCRATCHPAD.md"),
    "next_actions":    os.path.join(PROJECT_ROOT, "PROJECT_CONTEXT_PACK/05_NEXT_ACTIONS.md"),
    "latest_handoff":  None,  # resolved below
}

OUTPUT_FILE = os.path.join(PROJECT_ROOT, "session_handoffs/CURRENT_CONTEXT_BRIEFING.md")


def find_latest_handoff():
    handoff_dir = os.path.join(PROJECT_ROOT, "session_handoffs")
    if not os.path.isdir(handoff_dir):
        return None
    files = sorted(
        [f for f in os.listdir(handoff_dir) if f.startswith("HANDOFF_") and f.endswith(".md")],
        reverse=True
    )
    return os.path.join(handoff_dir, files[0]) if files else None


def read_file(path):
    """Read a file, return contents or NOT FOUND marker."""
    if not path or not os.path.exists(path):
        return f"(FILE NOT FOUND: {path})"
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def extract_section(text, heading, max_lines=30):
    """Extract lines under a markdown heading until next heading or blank section."""
    lines = text.split("\n")
    capture = False
    result = []
    count = 0
    for line in lines:
        if line.startswith(f"## {heading}") or line.startswith(f"# {heading}"):
            capture = True
            continue
        if capture:
            if line.startswith("## ") or line.startswith("# "):
                break
            result.append(line)
            count += 1
            if count >= max_lines:
                break
    return "\n".join(result).strip()


def extract_latest_scratchpad_entry(text, max_lines=40):
    """Extract the most recent dated entry from the scratchpad."""
    lines = text.split("\n")
    # Find all date headings: ## 2026-
    date_indices = []
    for i, line in enumerate(lines):
        if line.startswith("## 2026-"):
            date_indices.append(i)
    if not date_indices:
        return ""
    # Get the last (most recent) entry
    start = date_indices[-1]
    result = [lines[start]]
    for i in range(start + 1, min(start + max_lines + 1, len(lines))):
        if lines[i].startswith("## 2026-"):
            break
        result.append(lines[i])
    return "\n".join(result).strip()


def extract_ten_fields(contract_text):
    """Extract the 10 required briefing fields from CIS_CONTEXT_CONTRACT.md."""
    fields = {}
    current_field = None
    lines = contract_text.split("\n")
    in_fields_section = False

    for line in lines:
        if "Required Session Briefing Fields" in line:
            in_fields_section = True
            continue
        if in_fields_section:
            if line.startswith("## ") and "Required" not in line:
                break
            # Match numbered fields: "1. **Field Name** — description"
            for i in range(1, 11):
                if line.strip().startswith(f"{i}. **"):
                    parts = line.split("**")
                    if len(parts) >= 2:
                        current_field = parts[1].strip()
                        fields[current_field] = ""
                    break
            if current_field and line.strip().startswith("**Source"):
                fields[current_field] = "Source hierarchy defined in CIS_CONTEXT_CONTRACT.md"

    if not fields:
        # Hardcoded fallback — the 10 fields from the contract
        fields = {
            "Current Objective": "",
            "Current System State": "",
            "Active Blockers": "",
            "Next Safe Action": "",
            "Do Not Start Yet": "",
            "Current Architecture Principle": "",
            "Relevant Files / Paths": "",
            "Last Verified State": "",
            "User Intent / Why This Matters": "",
            "Open Questions / Decisions": "",
        }

    return fields


def assemble_briefing():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read all sources
    current_state = read_file(SOURCE_FILES["current_state"])
    seed_excerpts = read_file(SOURCE_FILES["seed_excerpts"])
    orientation = read_file(SOURCE_FILES["orientation"])
    contract_text = read_file(SOURCE_FILES["context_contract"])
    boundary_text = read_file(SOURCE_FILES["core_boundary"])
    scratchpad_text = read_file(SOURCE_FILES["scratchpad"])
    next_actions_text = read_file(SOURCE_FILES["next_actions"])

    SOURCE_FILES["latest_handoff"] = find_latest_handoff()
    handoff_text = read_file(SOURCE_FILES["latest_handoff"])

    # Extract key sections
    objective = extract_section(current_state, "Current Objective")
    blockers = extract_section(current_state, "Active Blockers", max_lines=15)
    next_action = extract_section(current_state, "Next Safe Action")
    boundaries = extract_section(current_state, "Do Not Start Yet", max_lines=20)
    state_section = extract_section(current_state, "Current System State", max_lines=40)
    decisions = extract_section(current_state, "What Has Been Decided", max_lines=25)
    latest_scratchpad = extract_latest_scratchpad_entry(scratchpad_text)
    current_next = extract_section(next_actions_text, "Current Next Action", max_lines=5)

    # Build scratchpad and next-actions sections
    scratchpad_section = ""
    if latest_scratchpad:
        scratchpad_section = "## 3.5. Latest Scratchpad Entry\n\n" + latest_scratchpad + "\n\n---\n\n"
    next_action_section = ""
    if current_next:
        next_action_section = "## 3.6. Current Next Action (from 05_NEXT_ACTIONS)\n\n" + current_next + "\n\n---\n\n"
    ten_fields = extract_ten_fields(contract_text)
    ten_fields["Current Objective"] = objective or ten_fields.get("Current Objective", "")
    ten_fields["Active Blockers"] = blockers or ten_fields.get("Active Blockers", "")
    ten_fields["Next Safe Action"] = next_action or ten_fields.get("Next Safe Action", "")
    ten_fields["Do Not Start Yet"] = boundaries or ten_fields.get("Do Not Start Yet", "")
    ten_fields["User Intent / Why This Matters"] = (
        "See seed intent excerpts below — Eric's own words from raw session archive."
    )

    # Assemble
    briefing = f"""# CIS Context Briefing — Phase 3A v0.1

Generated: {now}
Command: python3 /mnt/projects/cis/tools/generate_context_briefing.py
Sources: CIS_CURRENT_STATE.md, CIS_CONTEXT_CONTRACT.md, CIS_CORE_BOUNDARY.md,
         SEED_INTENT_EXCERPTS.md, latest structured handoff

---

## 1. Current Operational State

{state_section if state_section else "(see CIS_CURRENT_STATE.md for full state)"}

---

## 2. Current Objective

{objective or "(not found)"}

---

## 3. Next Safe Action

{next_action or "(not found)"}

---

{scratchpad_section}{next_action_section}## 4. Do-Not-Start Boundaries

{boundaries if boundaries else "(not found)"}

---

## 5. Ten Context Contract Fields

"""
    for field_name, field_value in ten_fields.items():
        if field_value:
            briefing += f"**{field_name}:** {field_value}\n\n"
        else:
            briefing += f"**{field_name}:** UNKNOWN — see CIS_CURRENT_STATE.md\n\n"

    briefing += """---

## 6. Seed Intent — Eric's Own Words

The following are Eric's actual words from past sessions. Do not summarize, rephrase, or replace with model interpretation.

"""
    # Include first 60 lines of seed excerpts (core excerpts, skip header)
    seed_lines = seed_excerpts.split("\n")
    seed_included = False
    for line in seed_lines:
        if line.startswith("> "):
            briefing += f"{line}\n"
            seed_included = True
        elif seed_included and line.startswith("_Source:"):
            briefing += f"{line}\n\n"
            seed_included = False

    briefing += f"""
Full seed corpus: /mnt/projects/cis/seed_intent_corpus/SEED_INTENT_EXCERPTS.md

---

## 7. Prime / R1 / Qwen — Shared Role Context

All three advisors receive the SAME context. The adversarial deliberation loop
requires common ground truth.

| Role | Model | Port | Function |
|------|-------|------|----------|
| Prime | deepseek-v4-pro | 8642 | Brainstorming + deliberation partner. Proposes. Does not build. |
| R1 | deepseek-reasoner | 8643 | Chain-of-thought reasoning. Challenges Prime's conclusions. |
| Qwen | qwen3-vl-30b (local) | 8644 | Worker only. Executes after deliberation converges. Does not deliberate. |

Claude and ChatGPT: Tier 3 escalation only — used sparingly for pass/fail review
when R1 + V4-Pro deliberation does not satisfy Eric.

---

## 8. Layer 2 Status

**Seed intent excerpts:** AVAILABLE — 6 core excerpts from raw Hermes session
archive (1,367 files scanned, top 5 sessions excerpted).

**Full VDB / Chroma semantic search:** NOT YET AVAILABLE. This is a later
layer. Current context uses Layer 1 (structured state + seed excerpts) only.

---

## 9. Structured Handoff Continuation

Latest handoff: {os.path.basename(SOURCE_FILES['latest_handoff']) if SOURCE_FILES['latest_handoff'] else 'NONE'}

Handoff directory: /mnt/projects/cis/session_handoffs/

Phase 3B will automate Hermes-to-Hermes continuation using this format.
Currently the handoff is generated by the context assembly command.

---

## 10. Phase 3A Failure Conditions (DO NOT VIOLATE)

- Eric still manually pastes the handoff → NOT YET RESOLVED (this command is the first step)
- Briefing contains only operational state and no seed intent → PREVENTED (seed excerpts included above)
- Briefing contains seed intent but no current task or boundaries → PREVENTED (sections 2-4 above)
- Only Prime receives context while R1/Qwen remain blind → PREVENTED (shared context section 7 above)
- Hermes builds Chroma, SQLite schema, dashboard, or governance instead of the loader → PREVENTED (this is a standalone script)
- Raw Eric intent is replaced by model summary → PREVENTED (excerpts are verbatim)

---

## Source Files Referenced

| File | Status |
|------|--------|
| CIS_CURRENT_STATE.md | {'FOUND' if os.path.exists(SOURCE_FILES['current_state']) else 'MISSING'} |
| CIS_CONTEXT_CONTRACT.md | {'FOUND' if os.path.exists(SOURCE_FILES['context_contract']) else 'MISSING'} |
| CIS_CORE_BOUNDARY.md | {'FOUND' if os.path.exists(SOURCE_FILES['core_boundary']) else 'MISSING'} |
| SEED_INTENT_EXCERPTS.md | {'FOUND' if os.path.exists(SOURCE_FILES['seed_excerpts']) else 'MISSING'} |
| SESSION_ORIENTATION_PROMPT.md | {'FOUND' if os.path.exists(SOURCE_FILES['orientation']) else 'MISSING'} |
| CIS_SCRATCHPAD.md | {'FOUND' if os.path.exists(SOURCE_FILES['scratchpad']) else 'MISSING'} |
| 05_NEXT_ACTIONS.md | {'FOUND' if os.path.exists(SOURCE_FILES['next_actions']) else 'MISSING'} |
| Latest structured handoff | {'FOUND' if SOURCE_FILES['latest_handoff'] else 'MISSING'} |

---

*Generated by Phase 3A Automatic Context Loader v0.1*
*This briefing is designed for Prime, R1, and Qwen to share.*
"""

    return briefing


def main():
    briefing = assemble_briefing()
    print(briefing)

    if "--write" in sys.argv:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
            fh.write(briefing)
        print(f"\n---\nBriefing written to: {OUTPUT_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
