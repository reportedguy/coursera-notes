"""`notebook add <url>`: resolve a Coursera link to its courses, then fetch and prepare each one.

Writes everything the writing skills need and prints it as one JSON plan, so the agent
never has to explore the data folder:
- work/packs/<course>/mNN-lLL.md   lesson packs (source for module pages)
- work/brief/<course>.md           syllabus + content signals (input to the course brief)
"""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from sv import ingest, normalize, pack, qa
from sv.browser import Pacer, session
from sv.config import Config, save_course
from sv.coursera_adapter import AdapterError
from sv.state import load_manifest, write_atomic

LEARN = re.compile(r"/learn/([\w-]+)")
PROGRAM = re.compile(r"/(?:specializations|professional-certificates)/[\w-]+")


def parse_url(url: str) -> tuple[str, str]:
    """('course', slug) for a /learn/ link, ('program', url) for a specialization or certificate."""
    path = urlparse(url if "//" in url else f"https://{url}").path
    if m := LEARN.search(path):
        return "course", m.group(1)
    if PROGRAM.search(path):
        return "program", url
    raise ValueError(f"not a Coursera course or program link: {url}")


def program_courses(cfg: Config, url: str) -> list[str]:
    """Course slugs linked from a program page, in page order."""
    with session(cfg, minimized=True) as (_, page, guard):
        Pacer(cfg.pacing).wait()
        page.goto(url, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass  # long-polling pages never go idle; what loaded is enough
        guard.check(page)
        hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
    slugs: list[str] = []
    for h in hrefs:
        # Only bare course links ending in /learn/<slug> (item links have more after it).
        m = re.search(r"/learn/([\w-]+)/?$", urlparse(urljoin(url, h)).path)
        if m and m.group(1) not in slugs:
            slugs.append(m.group(1))
    return slugs


def _signals(text: str) -> list[str]:
    found = []
    if text.count("```") >= 2 or re.search(r"\b(def|import|SELECT|function|print\()\b", text):
        found.append("code")
    if re.search(r"\$[^$\n]+\$|\\frac|\\sum|[=≈≤≥]\s*\d|\bformula\b", text):
        found.append("formulas")
    return found


def brief_input(cfg: Config, course_key: str) -> str:
    """Syllabus plus cheap content signals: everything the course brief needs, nothing more."""
    man = load_manifest(cfg, course_key)
    lines = [f"# {man.title}", f"slug: {man.slug}", ""]
    packs = sorted(cfg.path("work", "packs", course_key).glob("m*.md"))
    sample = "".join(p.read_text(encoding="utf-8")[:20000] for p in packs[:6])
    lines.append(f"content signals: {', '.join(_signals(sample)) or 'none'}")
    for mod in man.modules:
        lines += ["", f"## Module {mod.n}: {mod.title}"]
        lines += [f"- objective: {o}" for o in mod.objectives]
        for lsn in mod.lessons:
            mins = sum(i.duration_s or 0 for i in lsn.items if i.type == "lecture") // 60
            quizzes = sum(i.type == "quiz" for i in lsn.items)
            lines.append(f"- Lesson {lsn.n}: {lsn.title} ({mins} video min, {quizzes} quiz)")
            lines += [f"  - {i.type}: {i.title}" for i in lsn.items if not i.skip_reason]
    return "\n".join(lines) + "\n"


def prepare(cfg: Config, slug: str, *, modules: list[int] | None, slides: bool, echo=print) -> dict:
    key = slug  # the slug is already short, unique and filesystem-safe
    save_course(cfg, key, slug)
    ingest.run(cfg, key, modules, fetch_video=slides, echo=echo)
    man = load_manifest(cfg, key)
    mods = modules or [m.n for m in man.modules]
    normalize.run(cfg, key, mods, echo=echo)
    if slides:
        from sv import media  # optional extra: imagehash, scenedetect

        media.run(cfg, key, mods, echo=echo)
    packs = pack.run(cfg, key, mods, echo=echo)
    qa.run(cfg, key, echo=echo)
    brief = cfg.path("work", "brief", f"{key}.md")
    write_atomic(brief, brief_input(cfg, key))
    pages = cfg.path("pages", key)
    return {
        "course": key, "title": man.title, "brief": str(brief),
        "profile": str(pages / "profile.json"),
        "qa_candidates": str(pages / "qa-candidates.json"),
        "locked": [i.title for m in man.modules for lsn in m.lessons for i in lsn.items
                   if (i.skip_reason or "").startswith("locked")],
        "modules": [{"n": m.n, "title": m.title, "output": str(pages / f"m{m.n:02d}.md"),
                     "packs": [str(p) for p in packs if p.name.startswith(f"m{m.n:02d}-")]}
                    for m in man.modules if m.n in mods],
    }


def run(cfg: Config, url: str, *, modules: list[int] | None = None, slides: bool = False,
        echo=print) -> dict:
    kind, value = parse_url(url)
    slugs = [value] if kind == "course" else program_courses(cfg, value)
    if not slugs:
        raise ValueError(f"no courses found on {url}; open it in a browser and copy one course link")
    plan = {"data_root": str(cfg.data_root), "notebook": str(cfg.path("notebook", "notebook.html")),
            "courses": []}
    for s in slugs:
        try:
            plan["courses"].append(prepare(cfg, s, modules=modules, slides=slides, echo=echo))
        except AdapterError as exc:  # e.g. not enrolled; StopRun is not caught and stops the run
            plan["courses"].append({"course": s, "error": str(exc)})
            echo(f"skipped {s}: {exc}")
    out = cfg.path("work", "plan.json")
    write_atomic(out, json.dumps(plan, indent=2, ensure_ascii=False))
    return plan
