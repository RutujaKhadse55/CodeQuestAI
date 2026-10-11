"""ProfileRAGService: the contract from the RAG Integration Specification §5.

The agent layer calls THIS (structured results, clear errors) and never touches ChromaDB or the CLI. Every call
is scoped to the authenticated CodeQuest learner id; a LeetCode username only names the profile to fetch.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from sqlmodel import Session

from . import answerer, service


@dataclass
class SyncResult:
    username: str
    indexed_document_count: int
    section_status: dict
    snapshot_path: str | None
    warnings: list[str] = field(default_factory=list)
    status: str = "synced"  # synced | cached


@dataclass
class EvidenceDocument:
    username: str
    section: str | None
    title: str | None
    content: str
    source: dict
    score: float | None  # cosine distance (lower = closer); None when unavailable


@dataclass
class ProfileAnswer:
    answer: str
    evidence: list[dict]
    provider_status: str  # ok | not_configured | failed | not_called
    fallback_used: bool
    mode: str


class ProfileRAGServiceProtocol(Protocol):
    def sync_profile(self, user_id: str, leetcode_username: str) -> SyncResult: ...
    def retrieve_profile_evidence(self, user_id: str, question: str, top_k: int = 8) -> list[EvidenceDocument]: ...
    def answer_profile_question(self, user_id: str, question: str) -> ProfileAnswer: ...


class ProfileRAGService:
    def __init__(self, session: Session):
        self.s = session

    def sync_profile(self, user_id: str, leetcode_username: str, force: bool = False) -> SyncResult:
        r = service.sync(self.s, user_id, leetcode_username, force)
        return SyncResult(username=r["username"], indexed_document_count=r["documents"],
                          section_status=r.get("section_status") or r.get("summary", {}).get("sections", {}),
                          snapshot_path=r.get("snapshot_path"), warnings=r.get("warnings", []), status=r["status"])

    def retrieve_profile_evidence(self, user_id: str, question: str, top_k: int = 8) -> list[EvidenceDocument]:
        top_k = max(1, min(top_k, 16))
        return [EvidenceDocument(username=h["metadata"].get("username", ""), section=h["metadata"].get("section"),
                                 title=h["metadata"].get("title"), content=h["text"], source=h["metadata"],
                                 score=h.get("distance"))
                for h in service.retrieve_evidence(self.s, user_id, question, top_k)]

    def answer_profile_question(self, user_id: str, question: str) -> ProfileAnswer:
        r = service.ask(self.s, user_id, question)
        return ProfileAnswer(answer=r["answer"], evidence=r["evidence"], provider_status=r["provider_status"],
                             fallback_used=r["fallback_used"], mode=r["mode"])


__all__ = ["ProfileRAGService", "ProfileRAGServiceProtocol", "SyncResult", "EvidenceDocument", "ProfileAnswer",
           "answerer"]
