"""AI tests never reach a real model: Gemini is stubbed out; tests inject fakes via providers.register_llm."""
import pytest

from app import providers


@pytest.fixture(autouse=True)
def _no_real_llm(monkeypatch):
    from app.crew import llm
    monkeypatch.setattr(llm, "_gemini", lambda system, prompt: None)
    yield
    providers._llm = None
