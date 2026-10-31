"""Layer-2 semantic continuity contract for meaningful CIS transactions.

Inference is deliberately replaceable.  This module retrieves evidence,
obtains a source-linked assessment from an injected backend, and produces an
authorization bound to exact input, output, evidence, and contract hashes.
Only compact hashes and provenance references belong in the durable ledger.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
from typing import Any, Callable, Optional

import httpx


CONTRACT_VERSION = "cis.continuity/v1"
TRANSACTION_KINDS = (
    "INGEST", "RETRIEVAL", "INTERPRETATION", "MODEL_OUTPUT",
    "KNOWLEDGE_FORMATION", "PLAN", "APPROVAL", "EXECUTION",
    "VERIFICATION", "PROMOTION", "REUSE",
)
CRITICALITIES = ("OBSERVE", "CANDIDATE", "AUTHORITATIVE")
VERDICTS = (
    "ALIGNED", "ANTECEDENT_FOUND", "MISMATCH",
    "INSUFFICIENT_EVIDENCE", "UNAVAILABLE",
)
DECISIONS = ("ALLOW", "ANNOTATE", "HOLD")
LEDGER_STATUSES = (
    "EVALUATED", "COMMITTED", "FAILED", "INVALIDATED", "SUPERSEDED",
)
TERMINAL_REJECTION_STATUSES = {"INVALIDATED", "SUPERSEDED"}

# The only verdicts that may accompany an ALLOW decision. Any other
# combination is a forgery or a bug, never something to dispatch on.
ALLOWING_VERDICTS = ("ALIGNED", "ANTECEDENT_FOUND")

# Fields that may leave the evaluating process — into a run artifact on
# disk, into a downstream backend prompt, or into an HTTP response body.
# Binding hashes, the verdict/decision, the retrieval-validated source
# refs, the deterministic retrieval notes, and the check time. Deliberately
# absent: `antecedents` (raw retrieved excerpt text) and every
# model-generated free-form field (summary, concepts, required_changes,
# uncertainty). Those live only in the in-memory authorization, where they
# serve the immediate HOLD explanation to the operator.
BOUNDED_FIELDS = (
    "transaction_id", "contract_version", "input_hash", "output_hash",
    "evidence_set_hash", "verdict", "decision", "source_refs",
    "retrieval_notes", "checked_at",
)
# Deterministic marks the caller adds after attempting ledger persistence.
LEDGER_MARK_FIELDS = ("ledger_recorded", "ledger_status")
BOUNDED_ALLOWED_FIELDS = frozenset(BOUNDED_FIELDS + LEDGER_MARK_FIELDS)

LEDGER_MARK_RECORDED = "evaluated"
LEDGER_MARK_MIGRATION_ABSENT = "migration_0041_not_applied"
# The one — and only — persistence failure that may degrade instead of
# failing closed: migration 0041 has not been applied to this spine.
MISSING_LEDGER_TABLE_MESSAGE = "no such table: continuity_transactions"


def is_missing_ledger_table(exc: BaseException) -> bool:
    """True only for the specific absent-migration-0041 SQLite error."""
    return (isinstance(exc, sqlite3.OperationalError)
            and MISSING_LEDGER_TABLE_MESSAGE in str(exc).lower())


def bounded_authorization_dict(value: dict) -> dict:
    """Keep only bounded metadata, whatever the caller handed in."""
    return {key: data for key, data in value.items()
            if key in BOUNDED_ALLOWED_FIELDS}

_STOPWORDS = {
    "about", "after", "again", "also", "been", "before", "being", "between",
    "build", "can", "could", "does", "doing", "from", "have", "into", "just",
    "like", "more", "need", "only", "other", "should", "some", "something",
    "that", "their", "them", "then", "there", "these", "they", "thing", "think",
    "this", "through", "what", "when", "where", "which", "will", "with", "would",
    "your", "you", "cis",
}

SYSTEM_PROMPT = """You are the CIS Semantic Continuity Agent. Compare the
proposed semantic transaction with only the supplied historical evidence.
Detect rediscovery, mismatch with Eric's intent, flattened relationships,
unsupported novelty, and insufficient evidence. Original user language has
ranking preference over later model summaries, but no excerpt is authority by
itself. Return exactly one JSON object with verdict, summary, concepts,
source_refs, required_changes, and uncertainty. Never invent a source ref."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def make_openai_compatible_caller(
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = "agent",
    max_tokens: int = 1200,
    timeout: float = 60.0,
) -> Callable[[list], tuple[Optional[str], Optional[str]]]:
    """Return one replaceable OpenAI-compatible analysis-backend adapter."""
    endpoint = url or os.environ.get(
        "CIS_CONTINUITY_URL", "http://127.0.0.1:8643/v1/chat/completions"
    )
    key = api_key if api_key is not None else os.environ.get(
        "CIS_CONTINUITY_API_KEY", os.environ.get("CIS_REVIEW1_API_KEY", "")
    )

    def call(messages: list) -> tuple[Optional[str], Optional[str]]:
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        try:
            response = httpx.post(
                endpoint,
                json={"model": model, "messages": messages,
                      "max_tokens": int(max_tokens), "temperature": 0},
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            body = response.json()
            choices = body.get("choices") if isinstance(body, dict) else None
            hermes = body.get("hermes") if isinstance(body, dict) else None
            finish = (choices[0].get("finish_reason")
                      if isinstance(choices, list) and choices else None)
            if isinstance(hermes, dict) and (
                hermes.get("failed") is True or hermes.get("completed") is False
            ):
                return None, "continuity backend reported a failed generation"
            if finish == "error":
                return None, "continuity backend finish_reason='error'"
            content = (choices[0].get("message", {}).get("content", "")
                       if isinstance(choices, list) and choices else "")
            return ((content, None) if content else
                    (None, "continuity backend returned an empty response"))
        except Exception as exc:  # adapter boundary must report, not obscure
            return None, f"{type(exc).__name__}: {exc}"

    return call


@dataclass(frozen=True)
class SemanticTransaction:
    kind: str
    criticality: str
    actor: str
    operation: str
    input_payload: Any
    proposed_output: Any
    project_id: Optional[str] = None
    domain: Optional[str] = None
    process: Optional[str] = None
    loop: Optional[str] = None
    input_refs: tuple[str, ...] = ()
    parent_transaction_ids: tuple[str, ...] = ()
    request_id: Optional[str] = None
    contract_version: str = CONTRACT_VERSION
    transaction_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def __post_init__(self) -> None:
        if self.kind not in TRANSACTION_KINDS:
            raise ValueError(f"unknown semantic transaction kind: {self.kind}")
        if self.criticality not in CRITICALITIES:
            raise ValueError(f"unknown transaction criticality: {self.criticality}")
        if not self.actor.strip() or not self.operation.strip():
            raise ValueError("actor and operation are required")
        if self.contract_version != CONTRACT_VERSION:
            raise ValueError(f"unsupported continuity contract: {self.contract_version}")

    @property
    def input_hash(self) -> str:
        return content_hash(self.input_payload)

    @property
    def output_hash(self) -> str:
        return content_hash(self.proposed_output)


@dataclass(frozen=True)
class ContinuityAuthorization:
    transaction_id: str
    contract_version: str
    input_hash: str
    output_hash: str
    evidence_set_hash: str
    verdict: str
    decision: str
    summary: str
    concepts: tuple[str, ...]
    source_refs: tuple[str, ...]
    required_changes: tuple[str, ...]
    uncertainty: str
    antecedents: tuple[dict, ...]
    retrieval_notes: tuple[str, ...]
    checked_at: str

    def permits(self, transaction: SemanticTransaction,
                evidence_set_hash: str) -> bool:
        return (
            self.decision in ("ALLOW", "ANNOTATE")
            and transaction.transaction_id == self.transaction_id
            and transaction.contract_version == self.contract_version
            and transaction.input_hash == self.input_hash
            and transaction.output_hash == self.output_hash
            and evidence_set_hash == self.evidence_set_hash
        )

    def as_dict(self) -> dict:
        data = asdict(self)
        for key in ("concepts", "source_refs", "required_changes",
                    "antecedents", "retrieval_notes"):
            data[key] = list(data[key])
        return data

    def bounded_dict(self) -> dict:
        """Genuinely metadata-only view (BOUNDED_FIELDS): binding hashes,
        verdict/decision, retrieval-validated source refs, deterministic
        retrieval notes, and the check time. No retrieved excerpt text and
        no model-generated free-form text — summary, concepts,
        required_changes, uncertainty and antecedents are all dropped. This
        is the only form safe to write to a run artifact or to send into a
        downstream backend prompt."""
        data = self.as_dict()
        return {key: data[key] for key in BOUNDED_FIELDS}


def _terms(text: str, limit: int = 24) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for token in re.findall(r"[A-Za-z0-9_'-]{3,}", (text or "").lower()):
        token = token.strip("'-")
        if not token or token in _STOPWORDS or token in seen or token.isdigit():
            continue
        seen.add(token)
        result.append(token)
        if len(result) >= limit:
            break
    return result


def _source_ref(row: sqlite3.Row) -> str:
    keys = set(row.keys())
    source_key = (row["source_key"] if "source_key" in keys else "") or ""
    source = (row["source"] if "source" in keys else "") or "unknown"
    row_id = row["id"] if "id" in keys else None
    return source_key or (f"{source}:knowledge_messages:{row_id}"
                          if row_id is not None else source)


def _normalize_hit(value: dict, search_type: str) -> Optional[dict]:
    if not isinstance(value, dict):
        return None
    ref = str(value.get("source_ref") or "").strip()
    excerpt = str(value.get("excerpt") or value.get("content") or "").strip()
    if not ref or not excerpt:
        return None
    return {
        "source_ref": ref,
        "source": str(value.get("source") or "unknown").strip(),
        "role": str(value.get("role") or "").strip(),
        "excerpt": excerpt[:1200],
        "search_type": search_type,
    }


def _fts_hits(conn: sqlite3.Connection, query: str, limit: int) -> tuple[list[dict], list[str]]:
    terms = _terms(query)
    if not terms:
        return [], ["fts:no_discriminating_terms"]
    match = " OR ".join(f'"{term}"' for term in terms)
    try:
        rows = conn.execute(
            """SELECT km.id, km.content, km.source, km.role, km.source_key
               FROM knowledge_messages_fts fts
               JOIN knowledge_messages km ON km.id = fts.rowid
               WHERE knowledge_messages_fts MATCH ?
               ORDER BY rank LIMIT ?""",
            (match, int(limit * 5)),
        ).fetchall()
    except sqlite3.Error as exc:
        return [], [f"fts:failed:{type(exc).__name__}"]
    hits = [{
        "source_ref": _source_ref(row),
        "source": str(row["source"] or "unknown"),
        "role": str(row["role"] or ""),
        "excerpt": str(row["content"] or "")[:1200],
        "search_type": "fts5",
    } for row in rows if str(row["content"] or "").strip()]
    return hits, [f"fts:ok:{len(hits)}"]


def retrieve_antecedents(
    conn: sqlite3.Connection,
    transaction: SemanticTransaction,
    limit: int = 10,
    semantic_retriever: Optional[Callable[[str, int], list[dict]]] = None,
) -> tuple[list[dict], list[str]]:
    """Deterministically merge FTS and an optional semantic retrieval adapter."""
    query = "\n".join(str(value) for value in (
        transaction.operation, transaction.domain or "",
        transaction.process or "", transaction.loop or "",
        canonical_json(transaction.input_payload),
        canonical_json(transaction.proposed_output),
    ) if value)
    fts, notes = _fts_hits(conn, query, limit)
    semantic: list[dict] = []
    if semantic_retriever is None:
        notes.append("semantic:not_configured")
    else:
        try:
            raw = semantic_retriever(query, int(limit * 3)) or []
            semantic = [hit for value in raw
                        if (hit := _normalize_hit(value, "semantic"))]
            notes.append(f"semantic:ok:{len(semantic)}")
        except Exception as exc:
            notes.append(f"semantic:failed:{type(exc).__name__}")

    # Round-robin sources, with original-user language first inside each source.
    combined = fts + semantic
    by_ref: dict[str, dict] = {}
    for hit in combined:
        ref = hit["source_ref"]
        if ref not in by_ref:
            by_ref[ref] = hit
        elif hit["search_type"] not in by_ref[ref]["search_type"]:
            by_ref[ref]["search_type"] += "+" + hit["search_type"]
    ranked = sorted(
        by_ref.values(),
        key=lambda hit: (
            0 if hit["role"].lower() in {"user", "human", "eric"} else 1,
            hit["source"], hit["source_ref"], hit["search_type"],
        ),
    )
    selected: list[dict] = []
    per_source: dict[str, int] = {}
    for hit in ranked:
        if per_source.get(hit["source"], 0) >= 2:
            continue
        selected.append(hit)
        per_source[hit["source"]] = per_source.get(hit["source"], 0) + 1
        if len(selected) >= limit:
            break
    notes.append(f"coverage:selected:{len(selected)};sources:{len(per_source)}")
    if not selected:
        notes.append("coverage:no_antecedents")
    return selected, notes


def evidence_hash(antecedents: list[dict] | tuple[dict, ...]) -> str:
    material = [{
        "source_ref": hit["source_ref"],
        "excerpt_hash": content_hash(hit["excerpt"]),
        "search_type": hit["search_type"],
    } for hit in antecedents]
    return content_hash(material)


def _parse_agent_report(raw: str, allowed_refs: set[str]) -> tuple[Optional[dict], Optional[str]]:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text,
                      flags=re.I | re.S)
    try:
        data = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return None, f"invalid JSON:{type(exc).__name__}"
    if not isinstance(data, dict) or data.get("verdict") not in VERDICTS[:4]:
        return None, "invalid verdict"
    for name in ("concepts", "source_refs", "required_changes"):
        if not isinstance(data.get(name), list):
            return None, f"field {name!r} is not an array"
    refs = tuple(str(value) for value in data["source_refs"])
    if any(ref not in allowed_refs for ref in refs):
        return None, "invented source reference"
    return {
        "verdict": data["verdict"],
        "summary": str(data.get("summary") or "").strip(),
        "concepts": tuple(str(v).strip() for v in data["concepts"] if str(v).strip())[:10],
        "source_refs": refs[:16],
        "required_changes": tuple(str(v).strip() for v in data["required_changes"]
                                  if str(v).strip())[:10],
        "uncertainty": str(data.get("uncertainty") or "").strip(),
    }, None


def decision_for(criticality: str, verdict: str) -> str:
    if verdict in ALLOWING_VERDICTS:
        return "ALLOW"
    return "ANNOTATE" if criticality == "OBSERVE" else "HOLD"


def evaluate(
    conn: sqlite3.Connection,
    transaction: SemanticTransaction,
    call_agent: Callable[[list], tuple[Optional[str], Optional[str]]],
    antecedent_limit: int = 10,
    semantic_retriever: Optional[Callable[[str, int], list[dict]]] = None,
) -> ContinuityAuthorization:
    """Evaluate outside a write transaction and bind all mutable inputs."""
    if conn.in_transaction:
        raise RuntimeError("continuity evaluation cannot run inside a SQLite transaction")
    antecedents, notes = retrieve_antecedents(
        conn, transaction, antecedent_limit, semantic_retriever
    )
    checked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if not antecedents:
        verdict = "INSUFFICIENT_EVIDENCE"
        report = {
            "summary": "No historical antecedent was recovered.",
            "concepts": (), "source_refs": (), "required_changes": (),
            "uncertainty": "The corpus or configured indexes may not cover the history.",
        }
    else:
        evidence = "\n\n".join(
            f"SOURCE_REF: {h['source_ref']}\nROLE: {h['role'] or 'unknown'}\n"
            f"EXCERPT: {h['excerpt']}" for h in antecedents
        )
        payload = {
            "transaction_id": transaction.transaction_id,
            "kind": transaction.kind, "criticality": transaction.criticality,
            "actor": transaction.actor, "operation": transaction.operation,
            "project_id": transaction.project_id, "domain": transaction.domain,
            "process": transaction.process, "loop": transaction.loop,
            "input_refs": list(transaction.input_refs),
            "input": transaction.input_payload,
            "proposed_output": transaction.proposed_output,
        }
        raw, error = call_agent([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "SEMANTIC TRANSACTION:\n" +
             json.dumps(payload, indent=2, ensure_ascii=False) +
             "\n\nRETRIEVED HISTORICAL EVIDENCE:\n" + evidence},
        ])
        parsed, parse_error = (None, error) if error else _parse_agent_report(
            raw or "", {h["source_ref"] for h in antecedents}
        )
        if parse_error:
            verdict = "UNAVAILABLE"
            report = {
                "summary": "The continuity backend could not supply a usable report.",
                "concepts": (), "source_refs": (), "required_changes": (),
                "uncertainty": parse_error,
            }
        else:
            assert parsed is not None
            verdict = parsed.pop("verdict")
            report = parsed
    return ContinuityAuthorization(
        transaction_id=transaction.transaction_id,
        contract_version=transaction.contract_version,
        input_hash=transaction.input_hash,
        output_hash=transaction.output_hash,
        evidence_set_hash=evidence_hash(antecedents),
        verdict=verdict,
        decision=decision_for(transaction.criticality, verdict),
        summary=report["summary"], concepts=tuple(report["concepts"]),
        source_refs=tuple(report["source_refs"]),
        required_changes=tuple(report["required_changes"]),
        uncertainty=report["uncertainty"], antecedents=tuple(antecedents),
        retrieval_notes=tuple(notes), checked_at=checked_at,
    )


def latest_status(conn: sqlite3.Connection, transaction_id: str) -> Optional[str]:
    row = conn.execute(
        "SELECT status FROM continuity_transactions WHERE transaction_id=? "
        "ORDER BY id DESC LIMIT 1", (transaction_id,),
    ).fetchone()
    return str(row[0]) if row else None


def assert_permitted(
    authorization: ContinuityAuthorization,
    transaction: SemanticTransaction,
    evidence_set_hash: str,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """Reject held, changed, stale-contract, invalidated, or superseded work."""
    if authorization.decision == "HOLD":
        raise PermissionError(
            f"semantic transaction held: {authorization.verdict}: "
            f"{authorization.summary}"
        )
    if not authorization.permits(transaction, evidence_set_hash):
        raise PermissionError("semantic transaction binding changed after evaluation")
    if conn is not None and latest_status(conn, transaction.transaction_id) in \
            TERMINAL_REJECTION_STATUSES:
        raise PermissionError("semantic transaction was invalidated or superseded")


def persist_check(
    conn: sqlite3.Connection,
    transaction: SemanticTransaction,
    authorization: ContinuityAuthorization,
    status: str = "EVALUATED",
) -> str:
    """Append one metadata-only ledger event; never commits the connection."""
    if status not in LEDGER_STATUSES:
        raise ValueError("invalid continuity ledger status")
    if (authorization.transaction_id != transaction.transaction_id or
            authorization.contract_version != transaction.contract_version or
            authorization.input_hash != transaction.input_hash or
            authorization.output_hash != transaction.output_hash):
        raise ValueError("authorization does not bind this transaction")
    event_id = uuid.uuid4().hex
    envelope = {
        "contract_version": transaction.contract_version,
        "input_refs": list(transaction.input_refs),
        "parent_transaction_ids": list(transaction.parent_transaction_ids),
        "input_hash": transaction.input_hash,
        "output_hash": transaction.output_hash,
        "evidence_set_hash": authorization.evidence_set_hash,
    }
    check = {
        "contract_version": authorization.contract_version,
        "verdict": authorization.verdict,
        "decision": authorization.decision,
        "source_refs": list(authorization.source_refs),
        "retrieval_notes": list(authorization.retrieval_notes),
        "evidence_set_hash": authorization.evidence_set_hash,
    }
    conn.execute(
        """INSERT INTO continuity_transactions
           (ledger_event_id, transaction_id, request_id, project_id, kind,
            criticality, actor, operation, contract_version, input_hash,
            output_hash, evidence_set_hash, envelope_json, verdict, decision,
            check_json, status, checked_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (event_id, transaction.transaction_id, transaction.request_id,
         transaction.project_id, transaction.kind, transaction.criticality,
         transaction.actor, transaction.operation, transaction.contract_version,
         transaction.input_hash, transaction.output_hash,
         authorization.evidence_set_hash, canonical_json(envelope),
         authorization.verdict, authorization.decision, canonical_json(check),
         status, authorization.checked_at),
    )
    return event_id
