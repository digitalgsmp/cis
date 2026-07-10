#!/usr/bin/env python3
"""
guardrails.py — Tier 1 Deterministic Guardrails for CIS Pipeline

Per docs/DETERMINISTIC_GUARDRAIL_SPECIFICATION.md, these are zero-token,
highest-catch-rate checks that fire after each pipeline phase. They do NOT
replace LLM judgment — they add a deterministic floor that catches the most
common failure modes before they propagate.

Each guardrail function returns a GuardrailResult with:
  - name: guardrail identifier
  - verdict: PASS | FAIL | SKIP
  - evidence: raw command output or file state that proves the verdict
  - summary: one-line human-readable explanation
  - details: optional longer explanation

Two modes:
  - BLOCK: hard check — FAIL stops the pipeline (zero false-positive risk only)
  - ADVISORY: soft check — FAIL logs a warning but pipeline continues
              (promote to BLOCK after validation per Part 6 self-evolving harness)

Wiring: called from pipeline_relay.py after each phase output is received,
before the output is stored in deliberation_rounds or passed downstream.
"""

import os
import re
import json
import subprocess
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class GuardrailResult:
    """Result of a single guardrail check."""
    name: str
    verdict: str  # PASS | FAIL | SKIP
    evidence: str = ""
    summary: str = ""
    details: str = ""
    mode: str = "BLOCK"  # BLOCK or ADVISORY

    @property
    def blocked(self) -> bool:
        """True if this result should block the pipeline."""
        return self.verdict == "FAIL" and self.mode == "BLOCK"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "verdict": self.verdict,
            "evidence": self.evidence[:2000],
            "summary": self.summary,
            "mode": self.mode,
        }


@dataclass
class GuardrailReport:
    """Collection of guardrail results for a single phase."""
    phase: str
    role: str
    results: List[GuardrailResult] = field(default_factory=list)

    @property
    def any_blocked(self) -> bool:
        return any(r.blocked for r in self.results)

    @property
    def any_failed(self) -> bool:
        return any(r.verdict == "FAIL" for r in self.results)

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results if r.verdict == "PASS")

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results if r.verdict == "FAIL")

    @property
    def skip_count(self) -> int:
        return sum(1 for r in self.results if r.verdict == "SKIP")

    @property
    def summary(self) -> str:
        parts = []
        for r in self.results:
            icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "—"}.get(r.verdict, "?")
            parts.append(f"  {icon} {r.name}: {r.summary}")
        header = f"Guardrails [{self.phase}/{self.role}]: {self.pass_count} PASS, {self.fail_count} FAIL, {self.skip_count} SKIP"
        return header + "\n" + "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "role": self.role,
            "results": [r.to_dict() for r in self.results],
            "any_blocked": self.any_blocked,
        }


# ── Helper ──────────────────────────────────────────────────────────────

def _run_cmd(cmd: List[str], cwd: str = None, timeout: int = 15) -> Tuple[str, int]:
    """Run a command, return (stdout, returncode)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1


def _extract_claimed_files(text: str) -> List[str]:
    """Extract file paths that an agent claims to have created or modified.
    
    Looks for patterns like:
      - "Created file: path/to/file.py"
      - "Modified: path/to/file.py"
      - "Wrote /path/to/file.py"
      - "Added /path/to/file.py"
      - ```path/to/file.py``` in code blocks
      - file paths mentioned after "created", "modified", "wrote", "added"
    """
    paths = []
    # Pattern 1: explicit claims
    claim_patterns = [
        r'(?:created|modified|wrote|added|updated|deleted|removed)\s+(?:the\s+)?(?:file\s+)?([/\w\-\.]+\.\w{1,6})',
        r'(?:file|path):\s*([/\w\-\.]+\.\w{1,6})',
    ]
    for pattern in claim_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            p = m.group(1)
            if p not in paths and not p.startswith('http'):
                paths.append(p)
    
    # Pattern 2: code block filenames (```python at start of block)
    for m in re.finditer(r'```(\w+)\n', text):
        lang = m.group(1)
        # Language tags like "python", "bash", "yaml" are not file paths
        # but sometimes models put filenames there
        if '.' in lang and '/' not in lang:
            paths.append(lang)
    
    # Pattern 3: absolute paths in text (must be preceded by whitespace, quote, or start of line)
    for m in re.finditer(r'(?:^|[\s"\'])(/[a-zA-Z0-9_\-/]+\.\w{1,6})', text):
        p = m.group(1)
        if p not in paths and '/proc/' not in p and '/sys/' not in p:
            paths.append(p)
    
    return paths


def _extract_claimed_functions(text: str) -> List[str]:
    """Extract function/method names an agent claims to have created."""
    funcs = []
    # Pattern: "def function_name" or "function function_name" or "method function_name"
    for m in re.finditer(r'(?:def|function|method)\s+(\w+)\s*\(', text):
        funcs.append(m.group(1))
    # Pattern: "added function X" / "created method Y"
    for m in re.finditer(r'(?:added|created|implemented|wrote)\s+(?:function|method)\s+(\w+)', text, re.IGNORECASE):
        if m.group(1) not in funcs:
            funcs.append(m.group(1))
    return list(set(funcs))


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 1: Claim-Action Verifier (§1.2)
# ═══════════════════════════════════════════════════════════════════════════

def guardrail_claim_action(
    agent_output: str,
    role: str,
    project_root: str,
    pre_exec_head: str = "",
) -> GuardrailResult:
    """Verify that files/functions an agent claims to have created actually exist.
    
    Catches: self-report lies, fabricated files/functions (§1.2, §1.4)
    Mode: BLOCK — fabricated claims must not propagate
    """
    claimed_files = _extract_claimed_files(agent_output)
    claimed_funcs = _extract_claimed_functions(agent_output)
    
    if not claimed_files and not claimed_funcs:
        return GuardrailResult(
            name="claim_action_verifier",
            verdict="SKIP",
            summary="No file or function claims detected in output",
            mode="BLOCK",
        )
    
    missing_files = []
    existing_files = []
    
    for f in claimed_files:
        # Try both absolute and relative to project root
        if os.path.isabs(f):
            full_path = f
        else:
            full_path = os.path.join(project_root, f)
        
        if os.path.exists(full_path):
            existing_files.append(f)
        else:
            # Also check if it's relative to the runtime dir
            alt_path = os.path.join(project_root, "runtime", f)
            if os.path.exists(alt_path):
                existing_files.append(f)
            else:
                missing_files.append(f)
    
    # Check git diff if we have a pre-exec HEAD
    git_diff = ""
    if pre_exec_head:
        diff_out, _ = _run_cmd(
            ["git", "diff", "--name-only", pre_exec_head],
            cwd=project_root, timeout=10
        )
        git_diff = diff_out
    
    evidence_parts = []
    if existing_files:
        evidence_parts.append(f"Existing files: {', '.join(existing_files[:10])}")
    if missing_files:
        evidence_parts.append(f"MISSING files: {', '.join(missing_files[:10])}")
    if git_diff:
        evidence_parts.append(f"Git diff (changed files since {pre_exec_head[:8]}):\n{git_diff[:500]}")
    
    evidence = "\n".join(evidence_parts)
    
    if missing_files:
        return GuardrailResult(
            name="claim_action_verifier",
            verdict="FAIL",
            evidence=evidence,
            summary=f"{len(missing_files)} claimed file(s) do not exist on disk: {', '.join(missing_files[:5])}",
            details=f"Agent claims to have created/modified files that don't exist. "
                    f"Missing: {missing_files}",
            mode="BLOCK",
        )
    
    return GuardrailResult(
        name="claim_action_verifier",
        verdict="PASS",
        evidence=evidence,
        summary=f"All {len(existing_files)} claimed file(s) verified on disk",
        mode="BLOCK",
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 2: Unverified Claim Propagator Block (§2.13)
# ═══════════════════════════════════════════════════════════════════════════

def guardrail_unverified_claim_block(
    upstream_output: str,
    downstream_prompt: str,
) -> GuardrailResult:
    """Check that upstream claims are tagged before passing to downstream agents.
    
    Catches: collective false memories, fabrication propagation (§2.13)
    Mode: ADVISORY — tagging is prompt engineering, not a hard block
    """
    # Check if the downstream prompt contains a warning about unverified claims
    unverified_tag = "UNVERIFIED" in downstream_prompt or "CLAIM" in downstream_prompt.upper()
    
    # Look for assertive claims in upstream output
    claim_indicators = [
        r'\b(?:I have|I\'ve|I did|I created|I modified|I implemented|I fixed)\b',
        r'\b(?:the (?:file|function|code|endpoint) (?:is|was|has been))\b',
        r'\b(?:completed|done|finished|built|deployed)\b',
    ]
    
    has_claims = any(
        re.search(p, upstream_output, re.IGNORECASE)
        for p in claim_indicators
    )
    
    if not has_claims:
        return GuardrailResult(
            name="unverified_claim_block",
            verdict="SKIP",
            summary="No assertive claims in upstream output",
            mode="ADVISORY",
        )
    
    if unverified_tag:
        return GuardrailResult(
            name="unverified_claim_block",
            verdict="PASS",
            summary="Downstream prompt tags upstream claims as unverified",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="unverified_claim_block",
        verdict="FAIL",
        evidence=f"Upstream output contains claims but downstream prompt lacks UNVERIFIED tag",
        summary="Upstream claims passed to downstream agent without verification tag",
        mode="ADVISORY",
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 3: Code Quality Pre-Check (§1.9)
# ═══════════════════════════════════════════════════════════════════════════

def guardrail_code_quality(
    agent_output: str,
    project_root: str,
) -> GuardrailResult:
    """Check for code quality issues: stubs, TODOs, pass statements, hardcoded values.
    
    Catches: shortcuts, stubs, hardcoded values (§1.9, §2.22)
    Mode: ADVISORY — these are code smells, not proof of failure
    """
    # Extract Python code blocks from output
    code_blocks = re.findall(r'```python\n(.*?)```', agent_output, re.DOTALL)
    if not code_blocks:
        # Also check for bare code blocks
        code_blocks = re.findall(r'```\n?(.*?)```', agent_output, re.DOTALL)
    
    if not code_blocks:
        return GuardrailResult(
            name="code_quality_precheck",
            verdict="SKIP",
            summary="No code blocks found in output",
            mode="ADVISORY",
        )
    
    all_code = "\n".join(code_blocks)
    issues = []
    
    # Check for TODO without context
    todos = re.findall(r'#\s*TODO[:\s].*', all_code)
    if todos:
        issues.append(f"{len(todos)} TODO comment(s) found")
    
    # Check for bare `pass` in except blocks
    except_pass = re.findall(r'except[^:]*:\s*\n\s*pass', all_code)
    if except_pass:
        issues.append(f"{len(except_pass)} bare except:pass (silent error swallowing)")
    
    # Check for hardcoded values that look like keys/tokens
    hardcoded = re.findall(r'(?:key|token|password|secret)\s*[:=]\s*["\'][^"\']{8,}["\']', all_code, re.IGNORECASE)
    if hardcoded:
        issues.append(f"{len(hardcoded)} potential hardcoded secret(s)")
    
    # Check for placeholder/stub patterns
    stubs = re.findall(r'\b(?:placeholder|stub|FIXME|HACK|XXX)\b', all_code, re.IGNORECASE)
    if stubs:
        issues.append(f"{len(stubs)} placeholder/stub marker(s)")
    
    if issues:
        evidence = "\n".join(issues)
        return GuardrailResult(
            name="code_quality_precheck",
            verdict="FAIL",
            evidence=evidence,
            summary=f"Code quality issues: {'; '.join(issues)}",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="code_quality_precheck",
        verdict="PASS",
        evidence=f"Checked {len(code_blocks)} code block(s), no quality issues found",
        summary=f"Code quality OK ({len(code_blocks)} block(s))",
        mode="ADVISORY",
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 4: Sycophancy Detector (§2.2)
# ═══════════════════════════════════════════════════════════════════════════

# Sycophancy keywords — hollow agreement without substantive critique
_SYCOPHANCY_KEYWORDS = [
    "excellent", "outstanding", "perfect", "brilliant", "flawless",
    "impeccable", "masterful", "superb", "wonderful", "fantastic",
    "great work", "well done", "no issues", "no concerns", "no objections",
    "nothing to add", "fully agree", "completely agree", "spot on",
    "nailed it", "spot-on", "exactly right", "nothing wrong",
    "i have no issues", "no changes needed", "no improvements",
]

# Substantive critique keywords — evidence the reviewer actually engaged
_CRITIQUE_KEYWORDS = [
    "however", "but", "issue", "concern", "problem", "missing",
    "incorrect", "wrong", "should", "suggest", "recommend", "improve",
    "gap", "oversight", "error", "bug", "flaw", "inconsisten",
    "contradiction", "assumption", "risk", "limitation", "drawback",
]


def _jaccard_similarity(a: str, b: str) -> float:
    """Jaccard similarity between two strings (word-level)."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def guardrail_sycophancy(
    reviewer_output: str,
    other_reviewer_output: str = "",
) -> GuardrailResult:
    """Detect sycophantic reviewer output — hollow agreement without substance.
    
    Catches: false consensus, hollow agreement (§2.2, §2.17)
    Mode: ADVISORY — promote to BLOCK after validation
    """
    if not reviewer_output.strip():
        return GuardrailResult(
            name="sycophancy_detector",
            verdict="SKIP",
            summary="Empty reviewer output",
            mode="ADVISORY",
        )
    
    output_lower = reviewer_output.lower()
    
    # Count sycophancy keywords
    sycophancy_hits = sum(1 for kw in _SYCOPHANCY_KEYWORDS if kw in output_lower)
    
    # Count critique keywords — but exclude negated forms like "no issues", "no concerns"
    # These are sycophantic, not critical
    negation_patterns = ["no issues", "no concerns", "no problems", "no errors",
                         "no bugs", "nothing wrong", "nothing to add",
                         "no changes", "no improvements", "no objections"]
    critique_hits = 0
    for kw in _CRITIQUE_KEYWORDS:
        # Find all occurrences and check if preceded by negation
        for m in re.finditer(re.escape(kw), output_lower):
            start = max(0, m.start() - 15)
            context = output_lower[start:m.start()]
            # Check if preceded by "no " or "nothing "
            if re.search(r'\b(?:no|nothing|without|lacks?|zero)\s+$', context):
                continue  # Negated — don't count as critique
            critique_hits += 1
    
    # Check output length — very short consensus is suspicious
    word_count = len(reviewer_output.split())
    
    # If reviewer says consensus but has zero critique keywords and high sycophancy
    parsed = None
    try:
        # Try to extract FINAL_JSON
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', reviewer_output, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(1))
    except Exception:
        pass
    
    status = parsed.get("status", "") if parsed else ""
    is_consensus = status == "CONSENSUS_REACHED" or "CONSENSUS" in output_lower.upper()
    
    issues = []
    
    # Sycophancy = hollow agreement. If reviewer has critique keywords, it's not hollow
    # regardless of length. Only flag when consensus + sycophancy + no critique.
    if is_consensus and sycophancy_hits >= 3 and critique_hits == 0:
        issues.append(
            f"Consensus reached with {sycophancy_hits} sycophancy keyword(s) "
            f"and 0 critique keyword(s) — hollow agreement"
        )
    elif is_consensus and sycophancy_hits >= 2 and critique_hits == 0 and word_count < 50:
        # Short + no critique + some sycophancy = suspicious
        issues.append(
            f"Short consensus ({word_count} words) with no critique keywords"
        )
    
    # Check similarity with other reviewer (false consensus — both say the same hollow thing)
    if other_reviewer_output.strip():
        sim = _jaccard_similarity(reviewer_output, other_reviewer_output)
        if sim > 0.8 and is_consensus:
            issues.append(
                f"Reviewer outputs {sim:.0%} similar — possible false consensus "
                f"(shared blind spot or copying)"
            )
    
    if issues:
        evidence = (
            f"Sycophancy keywords: {sycophancy_hits}, "
            f"Critique keywords: {critique_hits}, "
            f"Word count: {word_count}, "
            f"Status: {status}\n"
            f"{''.join(issues)}"
        )
        return GuardrailResult(
            name="sycophancy_detector",
            verdict="FAIL",
            evidence=evidence,
            summary=f"Sycophancy detected: {'; '.join(issues)}",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="sycophancy_detector",
        verdict="PASS",
        evidence=f"Sycophancy: {sycophancy_hits}, Critique: {critique_hits}, Words: {word_count}",
        summary=f"Reviewer engaged substantively (critique: {critique_hits}, sycophancy: {sycophancy_hits})",
        mode="ADVISORY",
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 5: Scope Compliance Checker (§1.3)
# ═══════════════════════════════════════════════════════════════════════════

def guardrail_scope_compliance(
    intent: str,
    agent_output: str,
) -> GuardrailResult:
    """Check that agent output stays within the scope of the intent.
    
    Catches: mission drift, scope creep (§1.3, §2.1)
    Mode: ADVISORY — scope drift is a judgment call
    """
    # Extract significant words from intent (filter stop words)
    stop_words = {
        "the", "a", "an", "to", "for", "of", "in", "on", "at", "by",
        "is", "are", "was", "were", "be", "been", "and", "or", "not",
        "this", "that", "it", "with", "from", "as", "so", "if", "but",
        "about", "into", "than", "then", "also", "just", "want", "need",
        "build", "create", "add", "make", "please", "can", "you", "i",
        "we", "me", "my", "our", "us", "will", "would", "should", "could",
    }
    
    intent_words = set(
        w.lower().strip(".,;:!?\"'()[]{}") 
        for w in intent.split() 
        if len(w) > 2 and w.lower() not in stop_words
    )
    
    output_words = set(
        w.lower().strip(".,;:!?\"'()[]{}")
        for w in agent_output.split()
        if len(w) > 2
    )
    
    if not intent_words:
        return GuardrailResult(
            name="scope_compliance",
            verdict="SKIP",
            summary="Intent has no significant words to compare",
            mode="ADVISORY",
        )
    
    # How many intent words appear in the output?
    overlap = intent_words & output_words
    overlap_ratio = len(overlap) / len(intent_words) if intent_words else 0
    
    # Find words in output that are NOT in intent and NOT common English words
    # (potential scope drift indicators)
    output_unique = output_words - intent_words - stop_words - {
        "file", "code", "function", "method", "class", "import", "return",
        "def", "self", "none", "true", "false", "error", "exception",
        "status", "json", "role", "summary", "reviewer", "brain", "draft",
        "verify", "menter", "consensus", "objections", "escalate",
        "final_json", "proposal", "directive", "pipeline", "phase",
        "round", "run", "agent", "gate", "eric", "cis", "runtime",
        "config", "api", "endpoint", "route", "table", "schema",
        "migration", "sqlite", "database", "query", "insert", "update",
        "select", "commit", "branch", "merge", "push", "pull", "request",
    }
    
    # If output has a lot of unique words unrelated to intent, flag it
    if len(output_unique) > 100 and overlap_ratio < 0.1:
        return GuardrailResult(
            name="scope_compliance",
            verdict="FAIL",
            evidence=f"Intent word overlap: {overlap_ratio:.0%} ({len(overlap)}/{len(intent_words)}), "
                    f"Output unique words: {len(output_unique)}",
            summary=f"Possible scope drift — output barely overlaps with intent ({overlap_ratio:.0%})",
            mode="ADVISORY",
        )
    
    if overlap_ratio < 0.05:
        return GuardrailResult(
            name="scope_compliance",
            verdict="FAIL",
            evidence=f"Intent word overlap: {overlap_ratio:.0%} ({len(overlap)}/{len(intent_words)})",
            summary=f"Very low overlap with intent ({overlap_ratio:.0%}) — possible scope mismatch",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="scope_compliance",
        verdict="PASS",
        evidence=f"Intent word overlap: {overlap_ratio:.0%} ({len(overlap)}/{len(intent_words)})",
        summary=f"Output stays within intent scope ({overlap_ratio:.0%} keyword overlap)",
        mode="ADVISORY",
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 6: Output Schema Validator (§2.15)
# ═══════════════════════════════════════════════════════════════════════════

# Valid status values per role
_VALID_STATUSES = {
    "brain": {"READY", "NEEDS_CLARIFICATION"},
    "draft": {"PROPOSAL_READY", "REVISION_READY"},
    "reviewer": {"CONSENSUS_REACHED", "OBJECTIONS", "ESCALATE"},
    "review1": {"CONSENSUS_REACHED", "OBJECTIONS", "ESCALATE"},
    "review2": {"CONSENSUS_REACHED", "OBJECTIONS", "ESCALATE"},
    "menter": {"CONSENSUS_REACHED", "DONE", "COMPLETE"},
    "verify": {"PASS", "FAIL"},
}

# Required fields in FINAL_JSON
_REQUIRED_FIELDS = {"role", "status"}


def guardrail_output_schema(
    agent_output: str,
    role: str,
) -> GuardrailResult:
    """Validate that FINAL_JSON is parseable and contains required fields.
    
    Catches: malformed outputs, format gaming (§2.15, §2.21)
    Mode: BLOCK — invalid FINAL_JSON must not be accepted as a valid signal
    """
    # Try to extract FINAL_JSON
    json_match = re.search(
        r'```json\s*(\{.*?\})\s*```|FINAL_JSON[:\s]*(\{.*?\})',
        agent_output,
        re.DOTALL
    )
    
    if not json_match:
        # Check if there's a bare JSON object at the end
        bare_match = re.search(r'(\{[^{}]*"role"[^{}]*\})\s*$', agent_output, re.DOTALL)
        if bare_match:
            json_str = bare_match.group(1)
        else:
            return GuardrailResult(
                name="output_schema_validator",
                verdict="FAIL",
                evidence="No FINAL_JSON block found in output",
                summary="Output missing FINAL_JSON — cannot parse signal",
                mode="BLOCK",
            )
    else:
        json_str = json_match.group(1) or json_match.group(2)
    
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        return GuardrailResult(
            name="output_schema_validator",
            verdict="FAIL",
            evidence=f"FINAL_JSON parse error: {e}\nRaw: {json_str[:200]}",
            summary=f"FINAL_JSON is not valid JSON: {e}",
            mode="BLOCK",
        )
    
    # Check required fields
    missing_fields = _REQUIRED_FIELDS - set(parsed.keys())
    if missing_fields:
        return GuardrailResult(
            name="output_schema_validator",
            verdict="FAIL",
            evidence=f"FINAL_JSON missing required fields: {missing_fields}\nParsed: {json.dumps(parsed)[:200]}",
            summary=f"FINAL_JSON missing fields: {', '.join(missing_fields)}",
            mode="BLOCK",
        )
    
    # Check status is valid for this role
    role_key = role.lower()
    valid_statuses = _VALID_STATUSES.get(role_key, set())
    if valid_statuses:
        status = parsed.get("status", "")
        if status not in valid_statuses:
            return GuardrailResult(
                name="output_schema_validator",
                verdict="FAIL",
                evidence=f"Role '{role}' status '{status}' not in valid set: {valid_statuses}\n"
                        f"Parsed: {json.dumps(parsed)[:200]}",
                summary=f"Invalid status '{status}' for role '{role}'",
                mode="BLOCK",
            )
    
    return GuardrailResult(
        name="output_schema_validator",
        verdict="PASS",
        evidence=f"Parsed FINAL_JSON: {json.dumps(parsed)[:200]}",
        summary=f"Valid FINAL_JSON (role={parsed.get('role')}, status={parsed.get('status')})",
        mode="BLOCK",
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 7: Content Specificity Check (§2.21)
# ═══════════════════════════════════════════════════════════════════════════

# Project-specific terms that should appear in substantive output
_PROJECT_TERMS = [
    "pipeline", "spine", "guardrail", "relay", "workflow", "run_id",
    "deliberation", "consensus", "brain", "draft", "review", "menter",
    "verify", "eric", "gate", "migration", "schema", "sqlite",
    "container", "docker", "flask", "endpoint", "api",
    "final_json", "trajectory", "circuit_breaker", "soul",
]


def guardrail_content_specificity(
    agent_output: str,
    project_terms: List[str] = None,
) -> GuardrailResult:
    """Check that output contains project-specific terms, not just boilerplate.
    
    Catches: format compliance gaming, boilerplate (§2.21)
    Mode: ADVISORY — generic output isn't proof of failure
    """
    terms = project_terms or _PROJECT_TERMS
    output_lower = agent_output.lower()
    
    hits = sum(1 for term in terms if term.lower() in output_lower)
    hit_ratio = hits / len(terms) if terms else 0
    
    if hit_ratio < 0.05:
        # Very few project terms — check if it's just generic filler
        return GuardrailResult(
            name="content_specificity",
            verdict="FAIL",
            evidence=f"Project term hits: {hits}/{len(terms)} ({hit_ratio:.0%})",
            summary=f"Output lacks project-specific content ({hit_ratio:.0%} term match)",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="content_specificity",
        verdict="PASS",
        evidence=f"Project term hits: {hits}/{len(terms)} ({hit_ratio:.0%})",
        summary=f"Output is project-specific ({hit_ratio:.0%} term match)",
        mode="ADVISORY",
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 8: Honesty Reporter (§1.7)
# ═══════════════════════════════════════════════════════════════════════════

# Dishonest PASSED/COMPLETE patterns — claiming success without evidence
_DISHONEST_PATTERNS = [
    r'\b(?:PASS|PASSED)\b\s*(?:\n|$|\.)\s*(?:[#\n]|$)',  # Bare PASSED with no context
    r'\ball\s+(?:tests|checks)\s+pass(?:ed)?\b',  # "all tests pass" with no evidence
    r'\b(?:no|zero)\s+(?:errors|bugs|issues|problems)\b',  # Claiming zero issues
    r'\b(?:everything|all)\s+(?:works|is working|is correct|is fine)\b',
]

# Evidence patterns — actual proof of work
_EVIDENCE_PATTERNS = [
    r'\bgit\s+diff\b', r'\btest\s+(?:output|result|pass)', r'\bpytest\b',
    r'\bcurl\s+', r'\bHTTP\s+\d{3}\b', r'\bexit_code\b',
    r'\bfile\s+(?:exists|created|modified)\b', r'\b\d+\s+bytes\b',
    r'\bSELECT\b.*\bFROM\b',  # SQL query evidence
    r'\bassert\b',  # assertions in code
]


def guardrail_honesty_reporter(
    agent_output: str,
) -> GuardrailResult:
    """Detect dishonest PASSED banners — claiming success without evidence.
    
    Catches: dishonest PASSED banners (§1.7)
    Mode: ADVISORY — missing evidence is suspicious but not always failure
    """
    output_upper = agent_output.upper()
    
    # Check for PASSED/COMPLETE claims
    has_pass_claim = any(
        re.search(p, agent_output, re.IGNORECASE)
        for p in _DISHONEST_PATTERNS
    )
    
    # Check for actual evidence
    has_evidence = any(
        re.search(p, agent_output, re.IGNORECASE)
        for p in _EVIDENCE_PATTERNS
    )
    
    if has_pass_claim and not has_evidence:
        # Found a pass claim but no evidence to back it up
        return GuardrailResult(
            name="honesty_reporter",
            verdict="FAIL",
            evidence=f"Pass claim found but no evidence patterns detected",
            summary="Dishonest PASSED — success claimed without supporting evidence",
            mode="ADVISORY",
        )
    
    if has_pass_claim and has_evidence:
        return GuardrailResult(
            name="honesty_reporter",
            verdict="PASS",
            evidence="Pass claim backed by evidence in output",
            summary="Honest PASSED — success claim includes evidence",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="honesty_reporter",
        verdict="SKIP",
        summary="No pass/fail claims in output",
        mode="ADVISORY",
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 9: Path Contract Validator (§2.16)
# ═══════════════════════════════════════════════════════════════════════════

def guardrail_path_contract(
    agent_output: str,
    project_root: str,
) -> GuardrailResult:
    """Validate that file paths mentioned by the agent are within the project root.
    
    Catches: wrong file paths, writes to wrong location (§2.16)
    Mode: BLOCK — writing outside the project is a containment violation
    """
    # Extract absolute paths from output
    abs_paths = re.findall(r'(/[a-zA-Z0-9_\-./]+\.\w{1,6})', agent_output)
    
    if not abs_paths:
        return GuardrailResult(
            name="path_contract_validator",
            verdict="SKIP",
            summary="No absolute file paths in output",
            mode="BLOCK",
        )
    
    # Normalize project root
    project_root_norm = os.path.normpath(project_root)
    
    violations = []
    checked = []
    
    for p in abs_paths:
        # Skip system paths that are just references, not writes
        if any(p.startswith(s) for s in ('/proc/', '/sys/', '/dev/', '/tmp/', '/etc/')):
            continue
        
        p_norm = os.path.normpath(p)
        checked.append(p_norm)
        
        # Check if path is within project root
        if not p_norm.startswith(project_root_norm):
            violations.append(p_norm)
    
    if violations:
        return GuardrailResult(
            name="path_contract_validator",
            verdict="FAIL",
            evidence="Paths outside project root ({}):\n{}".format(
                project_root_norm, "\n".join(violations[:10])
            ),
            summary=f"{len(violations)} path(s) outside project root — containment violation",
            mode="BLOCK",
        )
    
    return GuardrailResult(
        name="path_contract_validator",
        verdict="PASS",
        evidence=f"Checked {len(checked)} path(s), all within {project_root_norm}",
        summary=f"All {len(checked)} path(s) within project root",
        mode="BLOCK",
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARDRAIL 10: Tool Result Sandboxing (§2.18)
# ═══════════════════════════════════════════════════════════════════════════

def guardrail_tool_result_sandboxing(
    prompt: str,
) -> GuardrailResult:
    """Check that tool results in prompts are wrapped/sandboxed to prevent injection.
    
    Catches: prompt injection via tool results (§2.18)
    Mode: ADVISORY — sandboxing is prompt engineering, not a hard block
    """
    # Check if the prompt contains tool results that are unwrapped
    # Tool results typically appear as "Output: ..." or "Result: ..." or raw command output
    # They should be wrapped in markers like [TOOL_OUTPUT] or ```tool_result
    
    # Look for raw command output patterns that aren't wrapped
    raw_patterns = [
        r'root@\w+.*#\s',  # Shell prompts (unwrapped terminal output)
        r'>>> \w+',  # Python REPL output
        r'\{\}.*error.*\{\}',  # Raw error objects
    ]
    
    # Check for sandboxing markers
    sandbox_markers = ["[TOOL_OUTPUT]", "[EVIDENCE]", "[TOOL_RESULT]", "```tool",
                        "TOOL_OUTPUT", "EVIDENCE", "L1_DETERMINISTIC"]
    
    has_sandbox = any(m.lower() in prompt.lower() for m in sandbox_markers)
    
    if not any(re.search(p, prompt) for p in raw_patterns):
        return GuardrailResult(
            name="tool_result_sandboxing",
            verdict="PASS",
            summary="No raw tool results detected in prompt",
            mode="ADVISORY",
        )
    
    if has_sandbox:
        return GuardrailResult(
            name="tool_result_sandboxing",
            verdict="PASS",
            summary="Tool results in prompt are wrapped with sandbox markers",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="tool_result_sandboxing",
        verdict="FAIL",
        evidence="Raw tool output patterns found without sandbox markers",
        summary="Tool results in prompt may be unwrapped — injection risk",
        mode="ADVISORY",
    )


# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR: Run all guardrails for a phase
# ═══════════════════════════════════════════════════════════════════════════

def run_guardrails(
    phase: str,
    role: str,
    agent_output: str,
    intent: str = "",
    project_root: str = "/mnt/projects/cis",
    pre_exec_head: str = "",
    other_reviewer_output: str = "",
    downstream_prompt: str = "",
    prompt: str = "",
) -> GuardrailReport:
    """Run all applicable Tier 1 guardrails for a phase.
    
    Which guardrails run depends on the role and phase:
      - All roles: output_schema_validator, content_specificity, honesty_reporter
      - brain/draft: scope_compliance
      - menter: claim_action_verifier, code_quality_precheck, path_contract
      - review1/review2: sycophancy_detector
      - verify: claim_action_verifier, honesty_reporter
      - All: tool_result_sandboxing (on prompt, not output)
    """
    report = GuardrailReport(phase=phase, role=role)
    
    # ── Guardrails that run on ALL agent outputs ──────────────────────────
    
    report.results.append(guardrail_output_schema(agent_output, role))
    report.results.append(guardrail_content_specificity(agent_output))
    report.results.append(guardrail_honesty_reporter(agent_output))
    
    # ── Role-specific guardrails ──────────────────────────────────────────
    
    if role.lower() in ("brain", "draft"):
        report.results.append(guardrail_scope_compliance(intent, agent_output))
    
    if role.lower() == "menter":
        report.results.append(
            guardrail_claim_action(agent_output, role, project_root, pre_exec_head)
        )
        report.results.append(guardrail_code_quality(agent_output, project_root))
        report.results.append(guardrail_path_contract(agent_output, project_root))
    
    if role.lower() in ("review1", "review2"):
        report.results.append(
            guardrail_sycophancy(agent_output, other_reviewer_output)
        )
    
    if role.lower() == "verify":
        report.results.append(
            guardrail_claim_action(agent_output, role, project_root, pre_exec_head)
        )
    
    # ── Unverified claim block (checks prompt→output relationship) ────────
    if downstream_prompt:
        report.results.append(
            guardrail_unverified_claim_block(agent_output, downstream_prompt)
        )
    
    # ── Tool result sandboxing (checks prompt, not output) ───────────────
    if prompt:
        report.results.append(guardrail_tool_result_sandboxing(prompt))
    
    return report


def record_gate_outcomes(
    conn,
    run_id: str,
    report: GuardrailReport,
):
    """Record guardrail results in the gate_outcomes table for the self-evolving harness.
    
    This is Part 6 of the spec — stores every gate pass/fail alongside run results
    so thresholds can tune from observed data.
    """
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    
    for result in report.results:
        conn.execute(
            """INSERT INTO gate_outcomes
               (run_id, phase, role, guardrail_name, verdict, mode, summary, evidence, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, report.phase, report.role, result.name,
             result.verdict, result.mode, result.summary, result.evidence[:2000], ts)
        )
    conn.commit()
