"""Memory Protocol on Chroma: one collection per learner (`mem_<sha1(user_id)>`), so recall can never cross users and
delete_user drops the whole collection. Stores only mistake class / failure class / problem title - never code."""
from __future__ import annotations

import hashlib
import time
import uuid
from pathlib import Path

from ... import config
from ...contracts.models import Diagnosis


def _coll(user_id: str) -> str:
    return "mem_" + hashlib.sha1(user_id.encode()).hexdigest()[:40]


def _text(d: Diagnosis, title: str = "") -> str:
    return " ".join(x for x in (d.mistake_class, d.failure_class, title) if x) or "unknown"


class ChromaMemory:
    def __init__(self, path: str | None = None, embedding_fn=None):
        import chromadb
        path = path or config.CHROMA_PATH
        Path(path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=path)
        if embedding_fn is None:
            from .embeddings import default_embedder
            embedding_fn = default_embedder()
        self._ef = embedding_fn

    def _get(self, user_id: str, create: bool = True):
        if create:
            return self._client.get_or_create_collection(_coll(user_id), embedding_function=self._ef,
                                                         metadata={"hnsw:space": "cosine"})
        try:
            return self._client.get_collection(_coll(user_id), embedding_function=self._ef)
        except Exception:  # noqa: BLE001
            return None

    def remember(self, user_id: str, d: Diagnosis, problem_title: str) -> str:
        mid = uuid.uuid4().hex
        self._get(user_id).add(ids=[mid], documents=[_text(d, problem_title)],
                               metadatas=[{"mistake_class": d.mistake_class or "", "failure_class": d.failure_class or "",
                                           "problem": problem_title or "", "ts": int(time.time())}])
        return mid

    def recall(self, user_id: str, d: Diagnosis, k: int = 3) -> list[dict]:
        c = self._get(user_id, create=False)
        if c is None or c.count() == 0:
            return []
        res = c.query(query_texts=[_text(d)], n_results=min(max(k, 1), c.count()),
                      include=["documents", "metadatas", "distances"])
        return [{"id": i, "text": doc, "metadata": meta, "distance": dist}
                for i, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0],
                                              res["distances"][0])]

    def delete_user(self, user_id: str) -> None:
        try:
            self._client.delete_collection(_coll(user_id))
        except Exception:  # noqa: BLE001  (nothing stored)
            pass


_mem: ChromaMemory | None = None


def get_memory() -> ChromaMemory:
    global _mem
    if _mem is None:
        _mem = ChromaMemory()
    return _mem


def set_memory(m: ChromaMemory | None) -> None:
    global _mem
    _mem = m
