import json
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from core import export, llm, models, render

SAMPLE = json.loads((Path(__file__).parent.parent / "samples" / "sample_profile.json").read_text(encoding="utf-8"))


def test_normalize_handles_junk():
    p = models.normalize_profile({"name": " A ", "skills": ["x", "y"], "projects": [{"title": "T"}, "bad", {}], "education": None})
    assert p["name"] == "A" and p["skills"] == "x\ny"
    assert len(p["projects"]) == 1 and p["projects"][0]["tech"] == "" and p["education"] == []
    assert models.normalize_profile(None)["name"] == ""


def test_completeness():
    assert models.completeness(SAMPLE)["score"] >= 90
    empty = models.completeness({})
    assert empty["score"] == 0 and empty["tips"]


@pytest.mark.parametrize("bad", ["javascript:alert(1)", "data:text/html,x", "mailto:a@b.com", "https://", "ht tp://x"])
def test_safe_url_blocks(bad):
    assert render.safe_url(bad) == ""


def test_safe_url_accepts_and_prefixes():
    assert render.safe_url("github.com/x") == "https://github.com/x"
    assert render.safe_url("http://a.io") == "http://a.io"


def test_render_sample_has_sections():
    h = render.render(SAMPLE, "Midnight", "#ff0000")
    for s in ("Alex Sample", 'id="projects"', 'id="skills"', 'id="experience"', 'id="education"', "#ff0000", "Contact me"):
        assert s in h
    ld = h.split('application/ld+json">')[1].split("</script>")[0]
    assert json.loads(ld)["name"] == "Alex Sample"


def test_render_escapes_html_and_blocks_js_links():
    evil = {"name": "<script>alert(1)</script>", "about": "<img src=x onerror=alert(1)>",
            "github": "javascript:alert(1)", "projects": [{"title": "<b>x</b>", "github": "javascript:alert(2)"}]}
    h = render.render(evil)
    assert "<script>alert(1)" not in h and "<img src=x" not in h and "<b>x</b>" not in h
    assert "javascript:" not in h


def test_empty_sections_omitted_and_bad_accent_falls_back():
    h = render.render({"name": "Sam"}, "Nope", "red")
    assert 'id="projects"' not in h and 'id="skills"' not in h
    assert render.DEFAULT_ACCENT in h


def test_parse_skills_and_split():
    assert render.parse_skills("Languages: Python, SQL\nExcel; Git") == {"Languages": ["Python", "SQL"], "Skills": ["Excel", "Git"]}
    assert render.split_list("a; b\n- c", bullets=True) == ["a", "b", "c"]


def test_zip_contents_and_profile_roundtrip():
    h = render.render(SAMPLE)
    z = zipfile.ZipFile(BytesIO(export.build_zip(SAMPLE, h)))
    assert set(z.namelist()) == {"index.html", ".nojekyll", "README.md", "profile.json"}
    assert models.normalize_profile(json.loads(z.read("profile.json"))) == models.normalize_profile(SAMPLE)


def test_llm_parsing():
    assert llm.parse_json('blah {"tagline": "T", "about": "A"} blah')["tagline"] == "T"
    with pytest.raises(ValueError):
        llm.parse_json("nope")
    assert llm.normalize_copy({"tagline": '"Hi"', "about": " x "}) == {"tagline": "Hi", "about": "x"}
    out = llm.normalize_projects({"projects": [{"index": 1, "description": "new"}, {"index": 9, "description": "z"}, "bad"]}, ["a", "b"])
    assert out == ["a", "new"]
