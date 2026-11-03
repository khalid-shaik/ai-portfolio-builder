from pathlib import Path

from streamlit.testing.v1 import AppTest

from core import llm

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _loaded(monkeypatch=None):
    at = AppTest.from_file(APP, default_timeout=60).run()
    [b for b in at.sidebar.button if b.label == "Load sample data"][0].click().run()
    return at


def test_app_loads_sample_and_scores():
    at = _loaded()
    assert not at.exception
    assert [m.value for m in at.metric if m.label == "Profile completeness"][0] != "0%"
    assert [t.value for t in at.text_input if t.key == "name"][0] == "Alex Sample"


def test_ai_copy_updates_fields(monkeypatch):
    monkeypatch.setattr(llm, "generate_copy", lambda *a, **k: {"tagline": "AI tagline", "about": "AI about"})
    monkeypatch.setattr(llm, "list_models", lambda host=None: ["llama3.2:latest"])
    at = _loaded()
    [b for b in at.button if "tagline" in b.label][0].click().run()
    assert not at.exception
    assert [t.value for t in at.text_input if t.key == "tagline"][0] == "AI tagline"


def test_ai_failure_shows_error(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("down")
    monkeypatch.setattr(llm, "generate_copy", boom)
    at = _loaded()
    [b for b in at.button if "tagline" in b.label][0].click().run()
    assert not at.exception and any("Could not reach Ollama" in e.value for e in at.error)
