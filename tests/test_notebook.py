"""URL parsing, the course brief, and an offline notebook build from an invented course."""

import json
from datetime import datetime, timezone

import pytest

from sv import add, config, notebook
from sv.config import save_course
from sv.models import CourseManifest, Lesson, ManifestItem, Module
from sv.state import manifest_path, write_json


def test_parse_url_course_and_program():
    assert add.parse_url("https://www.coursera.org/learn/python-basics/home/module/2") == ("course", "python-basics")
    assert add.parse_url("coursera.org/learn/python-basics") == ("course", "python-basics")
    url = "https://www.coursera.org/organizations/acme/professional-certificates/data-analytics"
    assert add.parse_url(url) == ("program", url)
    assert add.parse_url("https://www.coursera.org/specializations/ml")[0] == "program"
    with pytest.raises(ValueError):
        add.parse_url("https://www.coursera.org/browse/business")


def test_signals():
    assert add._signals("```python\nprint(1)\n```") == ["code"]
    assert "formulas" in add._signals("the mean is $\\frac{1}{n}\\sum x$")
    assert add._signals("plain prose about stakeholders") == []


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_DATA_ROOT", str(tmp_path))
    c = config.load()
    lecture = ManifestItem(n=1, item_id="abc12", type="lecture", coursera_kind="lecture", title="Intro",
                           slug="intro", public_url="u", access_url="u", duration_s=300)
    man = CourseManifest(course_key="demo-course", slug="demo-course", course_id="x", title="Demo Course",
                         modules=[Module(n=1, id="m1", title="Basics", objectives=["Explain a thing"],
                                         lessons=[Lesson(n=1, title="Start", items=[lecture])])],
                         discovered_at=datetime.now(timezone.utc))
    write_json(manifest_path(c, "demo-course"), man.model_dump(mode="json"))
    save_course(c, "demo-course", "demo-course")
    return config.load()


def test_brief_input_lists_syllabus(cfg):
    text = add.brief_input(cfg, "demo-course")
    assert "# Demo Course" in text and "objective: Explain a thing" in text
    assert "Lesson 1: Start (5 video min, 0 quiz)" in text


def test_build_from_pages(cfg):
    pages = cfg.path("pages", "demo-course")
    pages.mkdir(parents=True)
    (pages / "m01.md").write_text("## Idea\nText.\n\n```mermaid\nflowchart LR\nA-->B\n```\n", encoding="utf-8")
    (pages / "mindmap.md").write_text("# Demo\n## Basics\n- Idea\n", encoding="utf-8")
    out = notebook.build(cfg, echo=lambda *_: None)
    html = out.read_text(encoding="utf-8")
    state = json.loads(html.split('<script id="state" type="application/json">')[1].split("</script>")[0])
    course = state["courses"][0]
    assert course["title"] == "Demo Course"
    assert [p["kind"] for p in course["pages"]] == ["module", "mindmap"]
    assert "```mermaid" in course["pages"][0]["md"]  # rendered in the browser, not at build time
