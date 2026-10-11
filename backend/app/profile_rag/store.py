"""Persistent ChromaDB store for LeetCode profile documents, one logical index per CodeQuest user_id.

Ported from rag_store.ProfileVectorStore. chromadb / sentence-transformers are imported lazily so the Backend
runs (and its tests pass) without the heavy RAG dependencies; the endpoints then answer with a clear error.
"""
from __future__ import annotations

from pathlib import Path

from .. import config
from .documents import profile_to_documents, question_sections

COLLECTION_NAME = "leetcode_profiles"


class RagUnavailable(RuntimeError):
    """chromadb / sentence-transformers are not installed or failed to start."""


class ProfileVectorStore:
    def __init__(self, path: str | None = None, embedding_fn=None):
        try:
            import chromadb
        except ImportError as e:
            raise RagUnavailable("chromadb is not installed (pip install -r requirements/profile_rag.txt)") from e
        path = path or config.CHROMA_PATH
        Path(path).mkdir(parents=True, exist_ok=True)
        if embedding_fn is None:
            try:
                from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
                embedding_fn = SentenceTransformerEmbeddingFunction(model_name=config.EMBEDDING_MODEL)
            except Exception as e:  # noqa: BLE001
                raise RagUnavailable(f"embedding model unavailable: {type(e).__name__}") from e
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME, embedding_function=embedding_fn, metadata={"hnsw:space": "cosine"})

    # -- helpers --
    def _ids(self, user_id: str) -> list[str]:
        return list(self.collection.get(where={"user_id": user_id}, include=["metadatas"]).get("ids") or [])

    def count(self, user_id: str) -> int:
        return len(self._ids(user_id))

    def delete_user(self, user_id: str) -> int:
        """Remove every document of this learner (used by re-sync, profile delete and delete-all)."""
        ids = self._ids(user_id)
        for start in range(0, len(ids), 500):
            self.collection.delete(ids=ids[start:start + 500])
        return len(ids)

    def upsert_profile(self, user_id: str, profile: dict) -> int:
        docs = profile_to_documents(profile, user_id)
        self.delete_user(user_id)  # replace the learner's previous snapshot
        for start in range(0, len(docs), 100):
            batch = docs[start:start + 100]
            self.collection.upsert(ids=[d["id"] for d in batch], documents=[d["text"] for d in batch],
                                   metadatas=[d["metadata"] for d in batch])
        return len(docs)

    def search(self, user_id: str, question: str, k: int = 8) -> list[dict]:
        """Broad semantic retrieval + targeted retrieval from sections the question is about, merged by distance."""
        if not user_id or not question.strip():
            return []
        user_count = self.count(user_id)
        if user_count == 0:
            return []
        n = min(max(k, 1), user_count)
        results = [self.collection.query(query_texts=[question], n_results=n, where={"user_id": user_id},
                                         include=["documents", "metadatas", "distances"])]
        for section in question_sections(question):
            try:
                results.append(self.collection.query(
                    query_texts=[question], n_results=n,
                    where={"$and": [{"user_id": user_id}, {"section": section}]},
                    include=["documents", "metadatas", "distances"]))
            except Exception:  # noqa: BLE001  (keep broad search working if a targeted query fails)
                continue
        merged: dict[str, dict] = {}
        for res in results:
            ids = (res.get("ids") or [[]])[0]
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]
            dists = (res.get("distances") or [[]])[0]
            for i, doc_id in enumerate(ids):
                dist = dists[i] if i < len(dists) else None
                row = {"id": doc_id, "text": docs[i] if i < len(docs) else "",
                       "metadata": metas[i] if i < len(metas) else {}, "distance": dist}
                old = merged.get(doc_id)
                if old is None or (dist is not None and (old["distance"] is None or dist < old["distance"])):
                    merged[doc_id] = row
        rows = sorted(merged.values(), key=lambda r: (r["distance"] is None,
                                                      r["distance"] if r["distance"] is not None else float("inf")))
        return rows[:max(k, 1)]


_store: ProfileVectorStore | None = None


def get_store() -> ProfileVectorStore:
    """Lazy singleton (the embedding model is slow to load; do it on first use, not at import)."""
    global _store
    if _store is None:
        _store = ProfileVectorStore()
    return _store


def set_store(store: ProfileVectorStore | None) -> None:
    """Tests / Agents can inject their own store (e.g. one sharing Agents' MiniLM embedder)."""
    global _store
    _store = store
