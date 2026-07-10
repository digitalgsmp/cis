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
    previous_outputs: List[str] = None,
    round_num: int = 1,
    conn=None,
    run_id: str = "",
) -> GuardrailReport:
    """Run all applicable Tier 1 guardrails for a phase.
    
    Which guardrails run depends on the role and phase:
      - All roles: output_schema_validator, content_specificity, honesty_reporter
      - brain/draft: scope_compliance
      - menter: claim_action_verifier, code_quality_precheck, path_contract
      - review1/review2: sycophancy_detector
      - verify: claim_action_verifier, honesty_reporter
      - All: tool_result_sandboxing (on prompt, not output)
    
    Tier 2 guardrails also run on all applicable phases:
      - context_budget_monitor (on prompt)
      - verbosity_density (on output)
      - output_sanitizer (on output)
      - loop_detector (on output, needs previous_outputs)
      - mode_collapse_detector (on output, needs previous_outputs)
      - goal_anchoring (on output, needs round_num > 1)
      - trajectory_monitor (on output, needs conn + run_id)
      - model_diversity (one-time config check)
      - version_drift (one-time config check)
    """
    report = GuardrailReport(phase=phase, role=role)
    
    # ── Tier 1: Guardrails that run on ALL agent outputs ──────────────────
    
    report.results.append(guardrail_output_schema(agent_output, role))
    report.results.append(guardrail_content_specificity(agent_output))
    report.results.append(guardrail_honesty_reporter(agent_output))
    
    # ── Tier 1: Role-specific guardrails ──────────────────────────────────
    
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
    
    # ── Tier 1: Unverified claim block (checks prompt→output relationship) ─
    if downstream_prompt:
        report.results.append(
            guardrail_unverified_claim_block(agent_output, downstream_prompt)
        )
    
    # ── Tier 1: Tool result sandboxing (checks prompt, not output) ───────
    if prompt:
        report.results.append(guardrail_tool_result_sandboxing(prompt))
    
    # ── Tier 2: Context budget monitor (on prompt) ────────────────────────
    if prompt:
        report.results.append(guardrail_context_budget(prompt, role))
    
    # ── Tier 2: Verbosity / density metric (on output) ───────────────────
    report.results.append(guardrail_verbosity_density(agent_output, role))
    
    # ── Tier 2: Output sanitizer (on output) ──────────────────────────────
    report.results.append(guardrail_output_sanitizer(agent_output))
    
    # ── Tier 2: Loop detector + mode collapse (need previous outputs) ─────
    if previous_outputs:
        report.results.append(
            guardrail_loop_detector(agent_output, previous_outputs)
        )
        report.results.append(
            guardrail_mode_collapse(agent_output, previous_outputs)
        )
    
    # ── Tier 2: Goal anchoring (needs round_num > 1) ──────────────────────
    if round_num and round_num > 1:
        report.results.append(
            guardrail_goal_anchoring(intent, agent_output, round_num)
        )
    
    # ── Tier 2: Trajectory monitor (needs DB) ─────────────────────────────
    if conn and run_id:
        report.results.append(
            guardrail_trajectory_monitor(
                agent_output, role, conn=conn, run_id=run_id, phase=phase
            )
        )
    
    # ── Tier 2: Model diversity + version drift (config checks) ───────────
    report.results.append(guardrail_model_diversity())
    report.results.append(guardrail_version_drift())
    
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


# ═══════════════════════════════════════════════════════════════════════════
# TIER 2 GUARDRAILS (items 11-20)
# Low token cost or one-time cost checks
# ═══════════════════════════════════════════════════════════════════════════

# ── 11: Context Budget Monitor (§2.9) ──────────────────────────────────────

# Context window thresholds per model (chars, approx 4 chars/token)
_CONTEXT_THRESHOLDS = {
    "brain": 120_000,   # deepseek-v4-pro ~32K tokens
    "draft": 120_000,
    "review1": 120_000,
    "review2": 120_000,
    "menter": 120_000,
    "verify": 120_000,
}
_DEFAULT_CONTEXT_THRESHOLD = 100_000  # ~25K tokens, conservative


def guardrail_context_budget(
    prompt: str,
    role: str,
) -> GuardrailResult:
    """Check that prompt is within context window budget.
    
    Catches: context window exhaustion (§2.9)
    Mode: ADVISORY — large prompts aren't proof of failure, but risk it
    """
    prompt_len = len(prompt)
    threshold = _CONTEXT_THRESHOLDS.get(role.lower(), _DEFAULT_CONTEXT_THRESHOLD)
    warn_threshold = int(threshold * 0.8)
    
    if prompt_len > threshold:
        return GuardrailResult(
            name="context_budget_monitor",
            verdict="FAIL",
            evidence=f"Prompt length: {prompt_len:,} chars, threshold: {threshold:,} chars",
            summary=f"Prompt exceeds context budget ({prompt_len:,} > {threshold:,})",
            mode="ADVISORY",
        )
    
    if prompt_len > warn_threshold:
        return GuardrailResult(
            name="context_budget_monitor",
            verdict="FAIL",
            evidence=f"Prompt length: {prompt_len:,} chars, warn at 80%: {warn_threshold:,} chars",
            summary=f"Prompt approaching context limit ({prompt_len:,} > 80% of {threshold:,})",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="context_budget_monitor",
        verdict="PASS",
        evidence=f"Prompt length: {prompt_len:,} chars (budget: {threshold:,})",
        summary=f"Prompt within budget ({prompt_len:,}/{threshold:,})",
        mode="ADVISORY",
    )


# ── 12: Mode Collapse Detector (§2.3) ──────────────────────────────────────

def guardrail_mode_collapse(
    current_output: str,
    previous_outputs: List[str],
) -> GuardrailResult:
    """Detect diversity collapse — agent producing near-identical outputs across rounds.
    
    Catches: diversity collapse in multi-agent (§2.3)
    Mode: ADVISORY — similarity isn't always wrong (could be convergence on correct answer)
    """
    if not previous_outputs:
        return GuardrailResult(
            name="mode_collapse_detector",
            verdict="SKIP",
            summary="No previous outputs to compare",
            mode="ADVISORY",
        )
    
    similarities = []
    for prev in previous_outputs:
        if prev.strip():
            sim = _jaccard_similarity(current_output, prev)
            similarities.append(sim)
    
    if not similarities:
        return GuardrailResult(
            name="mode_collapse_detector",
            verdict="SKIP",
            summary="No non-empty previous outputs",
            mode="ADVISORY",
        )
    
    max_sim = max(similarities)
    avg_sim = sum(similarities) / len(similarities)
    
    if max_sim > 0.9:
        return GuardrailResult(
            name="mode_collapse_detector",
            verdict="FAIL",
            evidence=f"Max similarity: {max_sim:.0%}, avg: {avg_sim:.0%} across {len(similarities)} previous output(s)",
            summary=f"Mode collapse: output {max_sim:.0%} identical to a previous round",
            mode="ADVISORY",
        )
    
    if avg_sim > 0.75:
        return GuardrailResult(
            name="mode_collapse_detector",
            verdict="FAIL",
            evidence=f"Avg similarity: {avg_sim:.0%}, max: {max_sim:.0%} across {len(similarities)} previous output(s)",
            summary=f"Possible mode collapse (avg similarity {avg_sim:.0%})",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="mode_collapse_detector",
        verdict="PASS",
        evidence=f"Max similarity: {max_sim:.0%}, avg: {avg_sim:.0%}",
        summary=f"Output is diverse from previous rounds (max sim {max_sim:.0%})",
        mode="ADVISORY",
    )


# ── 13: Loop Detector (§2.4) ──────────────────────────────────────────────

def guardrail_loop_detector(
    current_output: str,
    previous_outputs: List[str],
) -> GuardrailResult:
    """Detect degeneration loops — agent cycling through the same output.
    
    Catches: degeneration loops, revision cycling (§2.4)
    Mode: BLOCK — a loop means the agent is stuck, no progress will be made
    """
    if not previous_outputs:
        return GuardrailResult(
            name="loop_detector",
            verdict="SKIP",
            summary="No previous outputs to compare",
            mode="BLOCK",
        )
    
    # Hash the current output
    current_hash = hashlib.sha256(current_output.encode()).hexdigest()[:16]
    
    # Check if this exact output was produced before
    for i, prev in enumerate(previous_outputs):
        if not prev.strip():
            continue
        prev_hash = hashlib.sha256(prev.encode()).hexdigest()[:16]
        if current_hash == prev_hash:
            return GuardrailResult(
                name="loop_detector",
                verdict="FAIL",
                evidence=f"Output hash {current_hash} matches round {i+1}'s hash — identical output",
                summary=f"Degeneration loop: output identical to round {i+1}",
                mode="BLOCK",
            )
    
    # Also check near-duplicates (>95% similar is effectively a loop)
    for i, prev in enumerate(previous_outputs):
        if not prev.strip():
            continue
        sim = _jaccard_similarity(current_output, prev)
        if sim > 0.95:
            return GuardrailResult(
                name="loop_detector",
                verdict="FAIL",
                evidence=f"Output {sim:.0%} similar to round {i+1} (hash: {current_hash})",
                summary=f"Near-loop: output {sim:.0%} identical to round {i+1}",
                mode="BLOCK",
            )
    
    return GuardrailResult(
        name="loop_detector",
        verdict="PASS",
        evidence=f"Output hash: {current_hash}, no match in {len(previous_outputs)} previous round(s)",
        summary=f"No loop detected (output unique across {len(previous_outputs)} round(s))",
        mode="BLOCK",
    )


# ── 14: Goal Anchoring Check (§2.1) ────────────────────────────────────────

def guardrail_goal_anchoring(
    intent: str,
    agent_output: str,
    round_num: int = 1,
) -> GuardrailResult:
    """Check that agent output stays anchored to the original goal across rounds.
    
    Catches: task drift over long horizons (§2.1)
    Mode: ADVISORY — drift is a judgment call, not always wrong
    """
    if round_num <= 1:
        return GuardrailResult(
            name="goal_anchoring",
            verdict="SKIP",
            summary="First round — no drift possible yet",
            mode="ADVISORY",
        )
    
    # Extract significant words from intent
    stop_words = {
        "the", "a", "an", "to", "for", "of", "in", "on", "at", "by",
        "is", "are", "was", "were", "be", "and", "or", "not",
        "this", "that", "it", "with", "from", "as", "so", "if", "but",
        "about", "into", "than", "then", "also", "just", "want", "need",
        "build", "create", "add", "make", "please", "can", "you", "i",
    }
    intent_words = set(
        w.lower().strip(".,;:!?\"'()[]{}")
        for w in intent.split()
        if len(w) > 3 and w.lower() not in stop_words
    )
    output_words = set(
        w.lower().strip(".,;:!?\"'()[]{}")
        for w in agent_output.split()
        if len(w) > 3
    )
    
    if not intent_words:
        return GuardrailResult(
            name="goal_anchoring",
            verdict="SKIP",
            summary="Intent has no significant words",
            mode="ADVISORY",
        )
    
    overlap = intent_words & output_words
    overlap_ratio = len(overlap) / len(intent_words)
    
    # Drift threshold gets stricter in later rounds
    min_expected = max(0.1, 0.3 - (round_num - 1) * 0.05)
    
    if overlap_ratio < min_expected:
        return GuardrailResult(
            name="goal_anchoring",
            verdict="FAIL",
            evidence=f"Intent word overlap: {overlap_ratio:.0%} (round {round_num}, min expected: {min_expected:.0%})",
            summary=f"Goal drift: output only {overlap_ratio:.0%} anchored to intent (round {round_num})",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="goal_anchoring",
        verdict="PASS",
        evidence=f"Intent word overlap: {overlap_ratio:.0%} (round {round_num})",
        summary=f"Goal anchored ({overlap_ratio:.0%} overlap with intent)",
        mode="ADVISORY",
    )


# ── 15: Trajectory Monitor (§2.14) ────────────────────────────────────────

def guardrail_trajectory_monitor(
    current_output: str,
    role: str,
    conn=None,
    run_id: str = "",
    phase: str = "",
) -> GuardrailResult:
    """Detect repeated actions without progress at phase level.
    
    Catches: trajectory degeneration — agent doing the same thing repeatedly (§2.14)
    Mode: ADVISORY — repeated actions might be retries, not degeneration
    """
    if not conn or not run_id:
        return GuardrailResult(
            name="trajectory_monitor",
            verdict="SKIP",
            summary="No DB connection or run_id — cannot check trajectory history",
            mode="ADVISORY",
        )
    
    try:
        # Get previous outputs for this role+phase
        rows = conn.execute(
            "SELECT prompt_hash, output_hash, outcome "
            "FROM agent_trajectories "
            "WHERE run_id = ? AND role = ? "
            "ORDER BY id DESC LIMIT 5",
            (run_id, role)
        ).fetchall()
        
        if len(rows) < 2:
            return GuardrailResult(
                name="trajectory_monitor",
                verdict="PASS",
                summary=f"Only {len(rows)} trajectory entries — no repetition pattern",
                mode="ADVISORY",
            )
        
        # Check for repeated identical outputs
        output_hashes = [r["output_hash"] for r in rows if r["output_hash"]]
        if output_hashes and len(set(output_hashes)) == 1 and len(output_hashes) >= 2:
            return GuardrailResult(
                name="trajectory_monitor",
                verdict="FAIL",
                evidence=f"Last {len(output_hashes)} outputs for {role} all have identical hash: {output_hashes[0][:16]}",
                summary=f"Trajectory stuck: {role} produced identical output {len(output_hashes)} times",
                mode="ADVISORY",
            )
        
        # Check for repeated failures
        outcomes = [r["outcome"] for r in rows if r["outcome"]]
        if len(outcomes) >= 3 and all(o == "failed" for o in outcomes[:3]):
            return GuardrailResult(
                name="trajectory_monitor",
                verdict="FAIL",
                evidence=f"Last {len(outcomes)} outcomes for {role}: {outcomes}",
                summary=f"Trajectory degeneration: {role} failed {len(outcomes)} consecutive times",
                mode="ADVISORY",
            )
        
        return GuardrailResult(
            name="trajectory_monitor",
            verdict="PASS",
            evidence=f"Checked {len(rows)} trajectory entries for {role}",
            summary=f"Trajectory healthy ({len(rows)} entries, no repetition)",
            mode="ADVISORY",
        )
    except Exception as e:
        return GuardrailResult(
            name="trajectory_monitor",
            verdict="SKIP",
            summary=f"DB error: {e}",
            mode="ADVISORY",
        )


# ── 16: Verbosity / Density Metric (§2.20) ─────────────────────────────────

def guardrail_verbosity_density(
    agent_output: str,
    role: str = "",
) -> GuardrailResult:
    """Check for reward hacking via excessive length without substance.
    
    Catches: reward hacking via length (§2.20)
    Mode: ADVISORY — verbose output isn't always wrong, but high length/low density is suspicious
    """
    if not agent_output.strip():
        return GuardrailResult(
            name="verbosity_density",
            verdict="SKIP",
            summary="Empty output",
            mode="ADVISORY",
        )
    
    word_count = len(agent_output.split())
    char_count = len(agent_output)
    
    # Density = unique words / total words (low density = lots of repetition)
    words = agent_output.lower().split()
    unique_words = len(set(words))
    density = unique_words / len(words) if words else 0
    
    # Code density — how much of the output is actual code vs prose
    code_blocks = re.findall(r'```.*?```', agent_output, re.DOTALL)
    code_chars = sum(len(b) for b in code_blocks)
    code_ratio = code_chars / char_count if char_count else 0
    
    issues = []
    
    # Very long output with low density = padding
    if word_count > 2000 and density < 0.3:
        issues.append(f"Very long ({word_count} words) with low density ({density:.0%} unique) — padding suspected")
    
    # Extremely long output regardless of density
    if word_count > 5000:
        issues.append(f"Extremely long output ({word_count} words) — verbosity hacking suspected")
    
    # Very short output for a phase that should produce substance
    if role.lower() in ("brain", "draft", "menter") and word_count < 20:
        issues.append(f"Very short output ({word_count} words) for {role} — insufficient substance")
    
    if issues:
        return GuardrailResult(
            name="verbosity_density",
            verdict="FAIL",
            evidence=f"Words: {word_count}, Density: {density:.0%}, Code ratio: {code_ratio:.0%}",
            summary=f"Verbosity issue: {'; '.join(issues)}",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="verbosity_density",
        verdict="PASS",
        evidence=f"Words: {word_count}, Density: {density:.0%}, Code ratio: {code_ratio:.0%}",
        summary=f"Output density OK ({word_count} words, {density:.0%} unique)",
        mode="ADVISORY",
    )


# ── 17: Sequential Review Enforcer (§1.8) ─────────────────────────────────

def guardrail_sequential_review(
    prompt: str,
    previous_reviewer_output: str = "",
) -> GuardrailResult:
    """Check that sequential review is enforced — reviewer 2 sees reviewer 1's findings.
    
    Catches: shared blind spots in parallel review (§1.8)
    Mode: ADVISORY — parallel review is the current pipeline design, sequential is enhancement
    """
    # Check if the prompt injects previous reviewer findings
    if previous_reviewer_output.strip():
        if previous_reviewer_output[:200] in prompt:
            return GuardrailResult(
                name="sequential_review_enforcer",
                verdict="PASS",
                evidence="Previous reviewer output found in current reviewer prompt",
                summary="Sequential review: reviewer sees prior reviewer's findings",
                mode="ADVISORY",
            )
        else:
            return GuardrailResult(
                name="sequential_review_enforcer",
                verdict="FAIL",
                evidence="Previous reviewer output exists but not injected into current prompt",
                summary="Parallel review: reviewer does NOT see prior reviewer's findings",
                mode="ADVISORY",
            )
    
    return GuardrailResult(
        name="sequential_review_enforcer",
        verdict="SKIP",
        summary="No previous reviewer output — first reviewer",
        mode="ADVISORY",
    )


# ── 18: Model Diversity Enforcement (§1.6) ────────────────────────────────

def guardrail_model_diversity(
    profiles_config: Dict[str, Any] = None,
) -> GuardrailResult:
    """Check that reviewers use different model providers (not same model reviewing itself).
    
    Catches: same model reviewing its own work (§1.6)
    Mode: BLOCK — same model reviewing itself is a fundamental design violation
    """
    if not profiles_config:
        # Try to load from dispatch module
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from dispatch import PROFILES
            profiles_config = PROFILES
        except Exception:
            return GuardrailResult(
                name="model_diversity",
                verdict="SKIP",
                summary="Cannot load profiles config",
                mode="BLOCK",
            )
    
    # Get models for review1 and review2
    r1_model = profiles_config.get("review1", {}).get("model", "")
    r2_model = profiles_config.get("review2", {}).get("model", "")
    
    if not r1_model or not r2_model:
        return GuardrailResult(
            name="model_diversity",
            verdict="SKIP",
            summary="Missing model info for reviewers",
            mode="BLOCK",
        )
    
    if r1_model == r2_model:
        return GuardrailResult(
            name="model_diversity",
            verdict="FAIL",
            evidence=f"review1 model: {r1_model}, review2 model: {r2_model}",
            summary=f"Model diversity violation: both reviewers use {r1_model}",
            mode="BLOCK",
        )
    
    return GuardrailResult(
        name="model_diversity",
        verdict="PASS",
        evidence=f"review1: {r1_model}, review2: {r2_model}",
        summary=f"Reviewers use different models ({r1_model} vs {r2_model})",
        mode="BLOCK",
    )


# ── 19: Version Drift Check (§2.8) ────────────────────────────────────────

# Track known model versions at guardrail deployment time
_KNOWN_MODELS: Dict[str, str] = {}  # filled on first call


def guardrail_version_drift(
    profiles_config: Dict[str, Any] = None,
) -> GuardrailResult:
    """Check for silent model version changes since last run.
    
    Catches: silent model version changes (§2.8)
    Mode: ADVISORY — version changes aren't always wrong, but should be detected
    """
    if not profiles_config:
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from dispatch import PROFILES
            profiles_config = PROFILES
        except Exception:
            return GuardrailResult(
                name="version_drift",
                verdict="SKIP",
                summary="Cannot load profiles config",
                mode="ADVISORY",
            )
    
    global _KNOWN_MODELS
    
    current_models = {
        role: cfg.get("model", "unknown")
        for role, cfg in profiles_config.items()
    }
    
    if not _KNOWN_MODELS:
        # First call — record baseline
        _KNOWN_MODELS = current_models.copy()
        return GuardrailResult(
            name="version_drift",
            verdict="PASS",
            evidence=f"Baseline models: {json.dumps(current_models)}",
            summary="Version baseline recorded",
            mode="ADVISORY",
        )
    
    # Compare current to known
    drift = {}
    for role, model in current_models.items():
        if role in _KNOWN_MODELS and _KNOWN_MODELS[role] != model:
            drift[role] = {"was": _KNOWN_MODELS[role], "now": model}
    
    if drift:
        # Update baseline
        _KNOWN_MODELS = current_models.copy()
        return GuardrailResult(
            name="version_drift",
            verdict="FAIL",
            evidence=f"Version drift: {json.dumps(drift)}",
            summary=f"Model version changed for: {', '.join(drift.keys())}",
            mode="ADVISORY",
        )
    
    return GuardrailResult(
        name="version_drift",
        verdict="PASS",
        evidence=f"All models match baseline: {json.dumps(current_models)}",
        summary="No version drift detected",
        mode="ADVISORY",
    )


# ── 20: Output Sanitizer (§2.24) ──────────────────────────────────────────

# Common unicode tricks for steganography
_SUSPICIOUS_UNICODE = [
    # Zero-width characters
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
    "\u2060",  # word joiner
    "\u2061",  # function application
    "\u2062",  # invisible times
    "\u2063",  # invisible separator
    "\u2064",  # invisible plus
    # Homoglyphs — cyrillic letters that look like latin
    "\u0430",  # cyrillic a
    "\u0435",  # cyrillic e
    "\u043e",  # cyrillic o
    "\u0440",  # cyrillic p
    "\u0441",  # cyrillic c
    "\u0445",  # cyrillic x
    "\u0443",  # cyrillic y
]

# Control characters (except common whitespace)
_SUSPICIOUS_CONTROL = [chr(i) for i in range(0, 9)] + [chr(11), chr(12)] + [chr(i) for i in range(14, 32)]


def guardrail_output_sanitizer(
    agent_output: str,
) -> GuardrailResult:
    """Detect steganography and unicode tricks in agent output.
    
    Catches: token-level steganography, unicode tricks (§2.24)
    Mode: BLOCK — steganography is adversarial, should not propagate
    """
    found = []
    
    # Check for zero-width and invisible characters
    for char in _SUSPICIOUS_UNICODE:
        if char in agent_output:
            count = agent_output.count(char)
            found.append(f"unicode U+{ord(char):04X} ({count}x)")
    
    # Check for suspicious control characters
    for char in _SUSPICIOUS_CONTROL:
        if char in agent_output:
            count = agent_output.count(char)
            found.append(f"control char U+{ord(char):04X} ({count}x)")
    
    # Check for mixed scripts (latin + cyrillic in same text = homoglyph attack)
    has_cyrillic = any("\u0400" <= c <= "\u04FF" for c in agent_output)
    has_latin = any("\u0041" <= c <= "\u007A" for c in agent_output)
    if has_cyrillic and has_latin:
        # Count cyrillic chars
        cyrillic_count = sum(1 for c in agent_output if "\u0400" <= c <= "\u04FF")
        if cyrillic_count > 3:
            found.append(f"mixed script: {cyrillic_count} cyrillic chars in latin text")
    
    if found:
        return GuardrailResult(
            name="output_sanitizer",
            verdict="FAIL",
            evidence=f"Suspicious characters found: {'; '.join(found)}",
            summary=f"Steganography detected: {', '.join(found[:5])}",
            mode="BLOCK",
        )
    
    return GuardrailResult(
        name="output_sanitizer",
        verdict="PASS",
        evidence=f"Output is clean ASCII/UTF-8 (no zero-width, homoglyphs, or control chars)",
        summary="Output sanitized — no steganographic content",
        mode="BLOCK",
    )
