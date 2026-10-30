"""`sv notebook`: assemble the Study Notebook artifact from <data_root>/pages.

Each course contributes its module pages (mNN.md), a summary (summary.md) and a
Question practice page (qa.json). Mermaid blocks stay as code and render in the
browser. Images referenced as `assets/...` are downscaled and embedded as data URIs
so the artifact is one self-contained page.

When the artifact already exists, pass its current HTML (`--live`): pages you edited
there (`html` set) and questions you removed are kept; only untouched pages update.
"""

from __future__ import annotations

import base64
import html
import io
import json
import re
from pathlib import Path

from PIL import Image

from sv.config import PACKAGE_DIR, Config
from sv.state import State, load_manifest, write_atomic

IMG = re.compile(r"!\[[^\]]*\]\(((?:assets/|frame:)[^)\s]+)\)")
MAX_W = 1100


def _data_uri(path: Path) -> str | None:
    if path.suffix.lower() == ".svg":
        return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode()
    try:
        return _jpeg_uri(path)
    except OSError:  # unreadable image: leave it out rather than fail the build
        return None


def _jpeg_uri(path: Path) -> str:
    with Image.open(path) as im:
        im = im.convert("RGB")
        if im.width > MAX_W:
            im = im.resize((MAX_W, round(im.height * MAX_W / im.width)))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def outline_tree(md: str) -> dict | None:
    """Markdown outline (# / ## / ### headings, then nested '-' bullets) -> markmap node tree."""
    root, stack = None, []  # stack of (depth, node)
    for line in md.splitlines():
        if not line.strip():
            continue
        if m := re.match(r"^(#{1,6})\s+(.*)$", line):
            depth, text = len(m.group(1)) * 10, m.group(2)
        elif m := re.match(r"^(\s*)[-*]\s+(.*)$", line):
            depth, text = 100 + len(m.group(1).expandtabs(2)), m.group(2)
        else:
            continue
        node = {"content": html.escape(text.strip()), "children": []}
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if stack:
            stack[-1][1]["children"].append(node)
        elif root is None:
            root = node
        else:
            root["children"].append(node)
        stack.append((depth, node))
    return root


def sort_glossary(md: str) -> str:
    """Alphabetize the rows of the table under a `## Glossary` heading."""
    m = re.search(r"(## Glossary\s*\n(?:[^\n]*\n)*?\|[^\n]*\|\n\|[-| :]+\|\n)((?:\|[^\n]*\|\n?)+)", md)
    if not m:
        return md
    rows = [r for r in m.group(2).splitlines() if r.strip()]
    rows.sort(key=lambda r: r.strip("| ").lower())
    return md[:m.start(2)] + "\n".join(rows) + "\n" + md[m.end(2):]


def _image_source(cfg: Config, course_key: str, ref: str) -> Path | None:
    """`assets/...` lives in the vault; `frame:<itemId>:<n>` is a slide frame in the raw cache."""
    if ref.startswith("assets/"):
        return cfg.path("vault", ref)
    m = re.match(r"frame:([\w-]+):(\d+)$", ref)
    if not m:
        return None
    st = State(cfg, course_key).get(f"{course_key}.{m.group(1)}")
    folder = st.fetched.detail.get("dir")
    return cfg.data_root / folder / "frames" / f"f{int(m.group(2)):02d}.jpg" if folder else None


def course_state(cfg: Config, course_key: str, title: str) -> tuple[dict, dict]:
    folder = cfg.path("pages", course_key)
    man = load_manifest(cfg, course_key)
    pages, images = [], {}
    for mod in man.modules:
        f = folder / f"m{mod.n:02d}.md"
        if f.exists():
            md = f.read_text(encoding="utf-8")
            pages.append({"id": f"m{mod.n}", "kind": "module", "nav": mod.title,
                          "title": f"Module {mod.n}: {mod.title}", "md": md, "html": None})
    course_md = folder / "course.md" if (folder / "course.md").exists() else folder / "summary.md"
    if course_md.exists():
        pages.append({"id": "summary", "kind": "summary", "nav": "Course map", "title": "Course map",
                      "md": course_md.read_text(encoding="utf-8"), "html": None})
    if (folder / "mindmap.md").exists():
        tree = outline_tree((folder / "mindmap.md").read_text(encoding="utf-8"))
        if tree:
            pages.append({"id": "mindmap", "kind": "mindmap", "nav": "Mind map", "title": "Mind map", "tree": tree})
    qa = json.loads((folder / "qa.json").read_text(encoding="utf-8")) if (folder / "qa.json").exists() else []
    if qa:
        pages.append({"id": "qa", "kind": "qa", "nav": "Question practice", "title": "Question practice"})
    for p in pages:
        if p.get("md"):
            p["md"] = sort_glossary(p["md"])
        for rel in IMG.findall(p.get("md") or ""):
            src = _image_source(cfg, course_key, rel)
            if src and src.exists() and rel not in images and (uri := _data_uri(src)):
                images[rel] = uri
    qa = [{k: q[k] for k in ("id", "module", "question", "options", "answer", "multi", "why")} for q in qa]
    return {"key": course_key, "title": title, "pages": pages, "qa": qa, "qaRemoved": []}, images


def merge_live(new: dict, live_html: str) -> dict:
    """Keep the viewer's edits from the live artifact: edited pages, removed questions."""
    m = re.search(r'<script id="state" type="application/json">(.*?)</script>', live_html, re.S)
    if not m:
        return new
    live = json.loads(m.group(1))
    for course in new["courses"]:
        old = next((c for c in live.get("courses", []) if c["key"] == course["key"]), None)
        if not old:
            continue
        course["qaRemoved"] = old.get("qaRemoved", [])
        for p in course["pages"]:
            op = next((x for x in old["pages"] if x["id"] == p["id"]), None)
            if op and op.get("html"):
                p["html"], p["md"] = op["html"], op.get("md", p.get("md"))
    new["images"] = {**live.get("images", {}), **new["images"]}
    return new


def build(cfg: Config, live: Path | None = None, echo=print) -> Path:
    state = {"courses": [], "images": {}}
    for ck in cfg.courses:
        if not (cfg.path("pages", ck).exists() and any(cfg.path("pages", ck).glob("m*.md"))):
            continue
        course, imgs = course_state(cfg, ck, cfg.titles.get(ck) or load_manifest(cfg, ck).title)
        state["courses"].append(course)
        state["images"].update(imgs)
    if live and live.exists():
        state = merge_live(state, live.read_text(encoding="utf-8"))
    template = (PACKAGE_DIR / "template.html").read_text(encoding="utf-8")
    html = template.replace("__STATE__", json.dumps(state, ensure_ascii=False).replace("<", "\\u003c"))
    out = cfg.path("notebook", "notebook.html")
    write_atomic(out, html)
    pages = sum(len(c["pages"]) for c in state["courses"])
    echo(f"notebook: {out} ({pages} pages, {len(state['images'])} images, {len(html) // 1024} KB)")
    return out
