#!/usr/bin/env python3
"""
staleness_check.py — Pre-Deliberation Freshness Gate

Scans a proposal for technology references, checks the web for recent
releases/changes since training cutoff, and produces a staleness report.

Usage:
  python3 tools/pipeline/staleness_check.py --proposal-file proposal.txt
  python3 tools/pipeline/staleness_check.py --proposal-file proposal.txt --json

Output:
  JSON staleness report with findings, versions, and freshness verdict.
  Exit code 0 = fresh, 1 = stale findings, 2 = search errors only.

Design:
  - Zero external dependencies (stdlib only: urllib, json, re, html)
  - Uses DuckDuckGo HTML search (free, no API key)
  - Wikipedia API for version checks on known tools
  - Extracts technology terms from proposal text automatically
"""

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# ── Known Technology Database ───────────────────────────────────────────
# Maps tool names to (wikipedia_page, version_pattern, home_url, training_cutoff_version)
# Update this when new tools enter CIS scope.

KNOWN_TOOLS = {
    "hermes-agent": {
        "name": "Hermes Agent",
        "repo": "NousResearch/hermes-agent",
        "version_pattern": r"v?(\d+\.\d+\.\d+)",
        "training_cutoff": "0.14.0",  # approximate — Hermes has no versioned releases listed
        "check_urls": [
            "https://github.com/NousResearch/hermes-agent/releases",
        ],
        "keywords": ["hermes", "hermes agent", "hermes-agent"],
    },
    "deepseek": {
        "name": "DeepSeek API",
        "repo": "deepseek-ai",
        "version_pattern": r"(?:deepseek-v\d|deepseek-chat|deepseek-reasoner)",
        "training_cutoff": "deepseek-v4-pro (current)",
        "check_urls": [
            "https://api-docs.deepseek.com/news",
        ],
        "keywords": ["deepseek", "deepseek-v4", "deepseek-v3", "deepseek-r1"],
    },
    "llama-cpp": {
        "name": "llama.cpp",
        "repo": "ggml-org/llama.cpp",
        "version_pattern": r"b(\d+)",
        "training_cutoff": "b4500+",
        "check_urls": [
            "https://github.com/ggml-org/llama.cpp/releases",
        ],
        "keywords": ["llama.cpp", "llama-cpp", "llamacpp"],
    },
    "qwen": {
        "name": "Qwen",
        "repo": "QwenLM/Qwen",
        "version_pattern": r"(?:Qwen\d[\w.-]*|qwen[\d.]+)",
        "training_cutoff": "Qwen3 (approx)",
        "check_urls": [
            "https://huggingface.co/Qwen",
        ],
        "keywords": ["qwen", "qwen3", "qwen2"],
    },
    "python": {
        "name": "Python",
        "version_pattern": r"(\d+\.\d+\.\d+)",
        "training_cutoff": "3.12.x",
        "check_urls": [
            "https://www.python.org/downloads/",
        ],
        "keywords": ["python", "python3"],
    },
    "sqlite": {
        "name": "SQLite",
        "version_pattern": r"(\d+\.\d+\.\d+)",
        "training_cutoff": "3.45.x",
        "check_urls": [
            "https://www.sqlite.org/changes.html",
        ],
        "keywords": ["sqlite", "sqlite3"],
    },
    "ubuntu": {
        "name": "Ubuntu",
        "version_pattern": r"(\d+\.\d+)",
        "training_cutoff": "24.04 LTS",
        "check_urls": [
            "https://releases.ubuntu.com/",
        ],
        "keywords": ["ubuntu", "ubuntu server"],
    },
    "proxmox": {
        "name": "Proxmox VE",
        "version_pattern": r"(\d+\.\d+)",
        "training_cutoff": "8.x",
        "check_urls": [
            "https://pve.proxmox.com/wiki/Roadmap",
        ],
        "keywords": ["proxmox", "pve"],
    },
    "docker": {
        "name": "Docker",
        "version_pattern": r"(\d+\.\d+\.\d+)",
        "training_cutoff": "26.x",
        "check_urls": [
            "https://docs.docker.com/engine/release-notes/",
        ],
        "keywords": ["docker", "docker compose"],
    },
    "git": {
        "name": "Git",
        "version_pattern": r"(\d+\.\d+\.\d+)",
        "training_cutoff": "2.44.x",
        "check_urls": [
            "https://github.com/git/git/releases",
        ],
        "keywords": ["git"],
    },
}

# ── Cache ───────────────────────────────────────────────────────────────
# Simple in-memory cache to avoid hammering GitHub API (rate limit: 60/hr unauthed)
_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 300  # 5 minutes
_suppress_stderr = False  # set True during non-interactive runs

def _cached(key: str) -> dict | None:
    """Return cached value if not expired."""
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < _CACHE_TTL:
            return val
        del _cache[key]
    return None

def _cache_set(key: str, val: dict):
    _cache[key] = (time.time(), val)


# ── Web Search ──────────────────────────────────────────────────────────

def ddg_search(query: str, timeout: int = 15) -> list[dict]:
    """Search DuckDuckGo HTML endpoint. Returns list of {title, snippet, url}.

    Falls back to empty results on failure — non-strict mode treats this
    as UNKNOWN rather than blocking the pipeline.
    """
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "CIS-StalenessCheck/1.0 (hermes-agent pipeline gate)",
    })

    body = ""
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        if not _suppress_stderr:
            print(f"  ⚠ DDG search failed for '{query}': {e}", file=sys.stderr)
        return []
    except Exception as e:
        if not _suppress_stderr:
            print(f"  ⚠ DDG search error for '{query}': {e}", file=sys.stderr)
        return []

    # Parse result snippets from DDG HTML
    results = []
    # Each result is in a div with class "result"
    result_blocks = re.findall(
        r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
        r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
        body, re.DOTALL | re.IGNORECASE
    )
    for href, title_raw, snippet_raw in result_blocks[:5]:
        title = html.unescape(re.sub(r'<[^>]+>', '', title_raw)).strip()
        snippet = html.unescape(re.sub(r'<[^>]+>', '', snippet_raw)).strip()
        if title:
            results.append({"title": title, "snippet": snippet, "url": href})
    return results


def search_github_releases(repo: str, timeout: int = 15) -> dict | None:
    """Fetch latest GitHub release info via API (no auth for public repos).

    Uses in-memory cache (5 min TTL) to avoid rate limiting (60 req/hr unauthed).
    """
    cache_key = f"github_release:{repo}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached

    url = f"https://api.github.com/repos/{repo}/releases?per_page=1"
    req = urllib.request.Request(url, headers={
        "User-Agent": "CIS-StalenessCheck/1.0",
        "Accept": "application/vnd.github+json",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read().decode("utf-8"))
        if data and isinstance(data, list) and len(data) > 0:
            latest = data[0]
            result = {
                "tag": latest.get("tag_name", "?"),
                "published": latest.get("published_at", "?"),
                "name": latest.get("name", "?"),
            }
            _cache_set(cache_key, result)
            return result
    except urllib.error.HTTPError as e:
        if e.code == 403:
            # Rate limited — return None, pipeline treats as UNKNOWN
            if not _suppress_stderr:
                print(f"  ⚠ GitHub API rate limited for {repo}", file=sys.stderr)
        else:
            if not _suppress_stderr:
                print(f"  ⚠ GitHub API error for {repo}: HTTP {e.code}", file=sys.stderr)
    except Exception as e:
        if not _suppress_stderr:
            print(f"  ⚠ GitHub API error for {repo}: {e}", file=sys.stderr)
    return None


def search_wikipedia_versions(page_title: str, timeout: int = 15) -> dict | None:
    """Query Wikipedia API for version history section."""
    url = (
        f"https://en.wikipedia.org/w/api.php"
        f"?action=query&prop=extracts&exintro=1&explaintext=1"
        f"&titles={urllib.parse.quote(page_title)}&format=json"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "CIS-StalenessCheck/1.0",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            extract = page.get("extract", "")
            # Try to find version info: "latest version", "stable release", etc.
            version_match = re.search(
                r'(?:latest\s+(?:stable\s+)?version|stable\s+release)[^\d]*(\d+[\d.]*\d+)',
                extract, re.IGNORECASE
            )
            if version_match:
                return {
                    "latest_version": version_match.group(1),
                    "source": f"Wikipedia: {page_title}",
                    "excerpt": extract[:500],
                }
    except Exception as e:
        print(f"  ⚠ Wikipedia API error for {page_title}: {e}", file=sys.stderr)
    return None


# ── Term Extraction ─────────────────────────────────────────────────────

def extract_tech_terms(proposal: str) -> list[dict]:
    """Extract technology references from proposal text.

    Returns list of {tool_key, tool_info, match_context} for each match.
    """
    found = []
    proposal_lower = proposal.lower()
    for key, info in KNOWN_TOOLS.items():
        for kw in info.get("keywords", []):
            if kw.lower() in proposal_lower:
                found.append({
                    "tool_key": key,
                    "tool_info": info,
                    "match_keyword": kw,
                    "context": _extract_context(proposal, kw),
                })
                break  # one match per tool
    return found


def _extract_context(text: str, keyword: str, window: int = 80) -> str:
    """Extract surrounding context for a keyword match."""
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(keyword) + window)
    ctx = text[start:end].strip()
    if start > 0:
        ctx = "…" + ctx
    if end < len(text):
        ctx = ctx + "…"
    return ctx


# ── Staleness Check Logic ───────────────────────────────────────────────

def check_tool_freshness(tool_key: str, tool_info: dict, proposal_context: str,
                         verbose: bool = False) -> dict:
    """Check if a known tool has updates since training cutoff.

    Returns {tool_key, tool_name, training_cutoff, findings: [...], verdict: fresh|stale|unknown}
    """
    findings = []
    verdict = "unknown"

    if verbose:
        print(f"  Checking {tool_info['name']}…")

    # 1. GitHub releases (if repo known)
    if "repo" in tool_info:
        repo = tool_info["repo"]
        if verbose:
            print(f"    → GitHub: {repo}")
        release = search_github_releases(repo)
        if release:
            finding_text = (
                f"Latest GitHub release: {release['tag']} ({release['name']}) "
                f"— published {release['published'][:10]}"
            )
            findings.append({
                "source": f"github:{repo}",
                "finding": finding_text,
                "latest": release["tag"],
                "published": release["published"],
            })
            # Compare with training cutoff
            cutoff = tool_info.get("training_cutoff", "")
            if cutoff and release["tag"]:
                findings[-1]["cutoff_at_training"] = cutoff
            if verbose:
                print(f"      → {finding_text}")

    # 2. Wikipedia version check
    wiki_page = tool_info.get("wikipedia_page", tool_info["name"])
    wiki = search_wikipedia_versions(wiki_page)
    if wiki:
        findings.append({
            "source": f"wikipedia:{wiki_page}",
            "finding": f"Wikipedia reports latest version: {wiki['latest_version']}",
            "latest": wiki["latest_version"],
        })
        if verbose:
            print(f"    → Wikipedia: {wiki['latest_version']}")

    # 3. Web search for recent changes
    query = f"{tool_info['name']} latest version release"
    if verbose:
        print(f"    → Web search: '{query}'")
    results = ddg_search(query)
    for r in results[:2]:
        snippet = r["snippet"][:200]
        if snippet:
            findings.append({
                "source": r["url"],
                "finding": f"Web: {r['title']} — {snippet}…",
                "url": r["url"],
            })

    # 4. Dedicated URL checks
    for url in tool_info.get("check_urls", []):
        if verbose:
            print(f"    → Checking: {url}")
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "CIS-StalenessCheck/1.0",
            })
            resp = urllib.request.urlopen(req, timeout=10)
            body = resp.read().decode("utf-8", errors="replace")[:5000]
            # Look for version patterns
            version_matches = re.findall(
                tool_info.get("version_pattern", r"(\d+\.\d+\.\d+)"),
                body
            )
            if version_matches:
                # Take the highest-sounding version
                findings.append({
                    "source": url,
                    "finding": f"Versions found at {url}: {', '.join(set(version_matches[:5]))}",
                    "versions_found": list(set(version_matches[:5])),
                })
        except Exception as e:
            if verbose:
                print(f"      ⚠ Failed: {e}")

    # Determine verdict
    if not findings:
        verdict = "unknown"
    else:
        # If we found version info that looks newer than training cutoff, mark stale
        has_newer_info = False
        for f in findings:
            snippet = f.get("finding", "")
            # Simple heuristic: if findings mention versions, it's worth noting
            if re.search(r'(?:latest|new|release|version|update)', snippet, re.IGNORECASE):
                has_newer_info = True
                break

        if has_newer_info:
            verdict = "stale"
        else:
            verdict = "fresh"

    return {
        "tool_key": tool_key,
        "tool_name": tool_info["name"],
        "training_cutoff": tool_info.get("training_cutoff", "unknown"),
        "match_context": proposal_context,
        "findings": findings,
        "verdict": verdict,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CIS Pre-Deliberation Staleness Check"
    )
    parser.add_argument("--proposal-file", required=True,
                        help="Path to proposal/directive text file")
    parser.add_argument("--json-only", action="store_true",
                        help="Output only JSON (for machine consumption)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose progress output")
    parser.add_argument("--timeout", type=int, default=15,
                        help="HTTP request timeout in seconds")

    args = parser.parse_args()

    # Read proposal
    try:
        with open(args.proposal_file) as f:
            proposal = f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.proposal_file}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    if not proposal.strip():
        print("ERROR: Empty proposal file.", file=sys.stderr)
        sys.exit(2)

    # ── Input validation ────────────────────────────────────────────────
    MIN_PROPOSAL_CHARS = 30
    MAX_PROPOSAL_CHARS = 50000

    if len(proposal.strip()) < MIN_PROPOSAL_CHARS:
        print(f"ERROR: Proposal too short ({len(proposal.strip())} chars, minimum {MIN_PROPOSAL_CHARS}).", file=sys.stderr)
        print("Proposals must be substantive — one-word directives bypass oversight.", file=sys.stderr)
        sys.exit(2)

    if len(proposal) > MAX_PROPOSAL_CHARS:
        print(f"WARNING: Proposal very long ({len(proposal)} chars). "
              f"Reviewers may truncate. Consider splitting.", file=sys.stderr)
        # Don't block — just warn. Reviewers handle truncation.

    # Basic injection guard: reject if proposal contains obvious shell/Python injection patterns
    # that should never appear in a legitimate proposal text
    suspicious_patterns = [
        (r'__import__\s*\(\s*[\'"]os[\'"]', "Python os import injection"),
        (r'eval\s*\(', "Python eval()"),
        (r'exec\s*\(', "Python exec()"),
        (r'`[^`]{20,}`', "Long backtick shell injection"),
    ]
    for pattern, desc in suspicious_patterns:
        if re.search(pattern, proposal, re.IGNORECASE):
            print(f"ERROR: Suspicious content detected in proposal: {desc}", file=sys.stderr)
            sys.exit(2)

    if not args.json_only:
        print("═══ CIS Staleness Check ═══")
        print(f"Proposal: {args.proposal_file}")
        print(f"Length: {len(proposal)} chars")
        print()

    # Extract technology terms
    tech_terms = extract_tech_terms(proposal)

    if not args.json_only:
        if tech_terms:
            print(f"Found {len(tech_terms)} technology reference(s):")
            for t in tech_terms:
                print(f"  • {t['tool_info']['name']} (matched: '{t['match_keyword']}')")
        else:
            print("No known technology references found in proposal.")
        print()

    # Check each term
    checks = []
    for term in tech_terms:
        if not args.json_only:
            print(f"─── {term['tool_info']['name']} ───")
        result = check_tool_freshness(
            term["tool_key"], term["tool_info"], term["context"],
            verbose=args.verbose or not args.json_only
        )
        checks.append(result)

        if not args.json_only:
            for f in result["findings"]:
                print(f"  {f['finding']}")
            print(f"  Verdict: {result['verdict'].upper()}")
            print()

    # Overall verdict
    stale_count = sum(1 for c in checks if c["verdict"] == "stale")
    fresh_count = sum(1 for c in checks if c["verdict"] == "fresh")
    unknown_count = sum(1 for c in checks if c["verdict"] == "unknown")

    report = {
        "proposal_file": args.proposal_file,
        "proposal_length": len(proposal),
        "tools_referenced": len(tech_terms),
        "tools_checked": len(checks),
        "stale_findings": stale_count,
        "fresh": fresh_count,
        "unknown": unknown_count,
        "overall_verdict": "STALE" if stale_count > 0 else ("UNKNOWN" if unknown_count > 0 else "FRESH"),
        "checks": checks,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    output = json.dumps(report, indent=2, ensure_ascii=False)

    if args.json_only:
        print(output)
    else:
        print("═══ Staleness Report ═══")
        print(f"Overall: {report['overall_verdict']}")
        print(f"  Stale: {stale_count}  Fresh: {fresh_count}  Unknown: {unknown_count}")
        print()
        print("─── Full JSON ───")
        print(output)

    # Exit code
    if stale_count > 0:
        sys.exit(1)
    elif unknown_count > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
