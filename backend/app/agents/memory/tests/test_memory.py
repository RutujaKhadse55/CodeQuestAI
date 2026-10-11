from app.agents.memory.embeddings import FakeEmbedder
from app.agents.memory.vector_store import ChromaMemory
from app.contracts.models import Diagnosis


def test_scoped_remember_recall_delete(tmp_path):
    m = ChromaMemory(path=str(tmp_path / "chroma"), embedding_fn=FakeEmbedder())
    d = Diagnosis(mistake_class="off_by_one", failure_class="boundary")
    assert m.recall("a", d) == []
    m.remember("a", d, "Two Sum")
    m.remember("b", Diagnosis(mistake_class="other"), "Zig Zag")
    got = m.recall("a", d, k=3)
    assert len(got) == 1 and got[0]["metadata"]["problem"] == "Two Sum"
    m.delete_user("a")
    assert m.recall("a", d) == []
    assert len(m.recall("b", d)) == 1
    m.delete_user("a")  # idempotent


def test_register_hook():
    from app import providers
    from app.agents import memory
    memory.register()
    assert "memory" in providers._deletion_hooks
