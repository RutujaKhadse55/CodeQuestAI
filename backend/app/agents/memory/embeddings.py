"""Embedders for per-user memory. Real: the same MiniLM model profile_rag uses (config.EMBEDDING_MODEL, lazy).
Fake: deterministic hashed bag-of-words (no model download) for tests and offline use."""
from __future__ import annotations

import hashlib
import math
import re

import chromadb

from ... import config

DIM = 64


def _embed(text: str) -> list[float]:
    v = [0.0] * DIM
    for tok in re.findall(r"\w+", (text or "").lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        v[h % DIM] += 1.0 if (h >> 8) & 1 else -1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class FakeEmbedder(chromadb.EmbeddingFunction):
    def __init__(self):
        pass

    def __call__(self, input):  # noqa: A002
        return [_embed(t) for t in input]

    @staticmethod
    def name() -> str:
        return "agents-fake-hash-embedder"

    def get_config(self):
        return {}


def default_embedder():
    """MiniLM if available, else the fake embedder (memory still works, just less semantic)."""
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        return SentenceTransformerEmbeddingFunction(model_name=config.EMBEDDING_MODEL)
    except Exception:  # noqa: BLE001
        return FakeEmbedder()
