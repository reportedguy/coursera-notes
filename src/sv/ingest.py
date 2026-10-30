"""`sv ingest`: fetch the named modules into the raw cache, each item exactly once.

Raw layout: <data_root>/raw/<course>/<itemId>/<YYYYMMDD>/ (append-only by date).
Videos go to <data_root>/media/<course>/<itemId>/video.mp4 and are deleted after
frame extraction (M3).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from selectolax.lexbor import LexborHTMLParser as HTMLParser

from sv.browser import Pacer, session
from sv.config import Config
from sv.coursera_adapter import BASE, AdapterError, Coursera, best_video_url, subtitle_url
from sv.models import ManifestItem
from sv.paths import slugify
from sv.state import State, manifest_path, now, sha256_files, write_json

GOOGLE_DOC = re.compile(r"https://docs\.google\.com/(document|spreadsheets|presentation)/d/([\w-]+)")
GOOGLE_EXPORT = {"document": "docx", "spreadsheets": "xlsx", "presentation": "pptx"}
FILE_EXT = re.compile(r"\.(pdf|docx?|xlsx?|pptx?|csv)(\?|$)", re.I)
# Coursera serves some files from an extensionless download endpoint.
COURSERA_DOWNLOAD = re.compile(r"/api/rest/v1/asset/download/(pdf|docx?|xlsx?|pptx?)/", re.I)


def _file_ext(href: str) -> str | None:
    m = FILE_EXT.search(href) or COURSERA_DOWNLOAD.search(href)
    return m.group(1).lower() if m else None


def _log(cfg: Config, name: str, record: dict) -> None:
    path = cfg.path("registry", name)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": now().isoformat(), **record}, ensure_ascii=False) + "\n")


def _reading_assets(cz: Coursera, html: str, out: Path) -> list[dict]:
    """Download images and downloadable resources a reading links to."""
    found = []
    tree = HTMLParser(html)
    for n, img in enumerate(tree.css("img"), start=1):
        src = img.attributes.get("src") or ""
        if src.startswith("http"):
            ext = Path(src.split("?")[0]).suffix.lower() or ".png"
            dest = out / "assets" / f"img{n:02d}{ext if len(ext) <= 5 else '.png'}"
            cz.download(src, dest, paced=False)
            found.append({"kind": "image", "src": src, "file": dest.name,
                          "alt": img.attributes.get("alt") or ""})
    for a in tree.css("a[href]"):
        href = urljoin(BASE, a.attributes.get("href") or "")
        label = a.text(strip=True)
        if m := GOOGLE_DOC.match(href):
            kind, doc_id = m.groups()
            ext = GOOGLE_EXPORT[kind]
            dest = out / "resources" / f"{slugify(label or doc_id, 40)}.{ext}"
            try:
                cz.download(f"https://docs.google.com/{kind}/d/{doc_id}/export?format={ext}", dest)
                found.append({"kind": ext, "src": href, "file": f"resources/{dest.name}", "label": label})
            except (AdapterError, Exception) as exc:  # private docs need a Google login
                found.append({"kind": "link", "src": href, "label": label, "error": str(exc)[:120]})
        elif ext := _file_ext(href):
            dest = out / "resources" / f"{slugify(label or Path(href.split('?')[0]).stem, 40)}.{ext}"
            try:
                cz.download(href, dest)
                found.append({"kind": ext, "src": href, "file": f"resources/{dest.name}", "label": label})
            except AdapterError as exc:  # dead link (404 etc.): note it, keep going
                found.append({"kind": "link", "src": href, "label": label, "error": str(exc)[:120]})
    return found


def fetch_item(cz: Coursera, cfg: Config, course_key: str, course_id: str,
               item: ManifestItem, fetch_video: bool) -> tuple[Path, str, dict]:
    out = cfg.path("raw", course_key, item.item_id, datetime.now().strftime("%Y%m%d"))
    out.mkdir(parents=True, exist_ok=True)
    detail: dict = {}

    if item.type == "lecture":
        video, layer = cz.lecture(item)
        write_json(out / "video.json", video)
        sub = subtitle_url(video, "en")
        if sub:
            cz.download(sub, out / "transcript.en.vtt")
        else:
            detail["flag"] = "no_en_transcript"
        write_json(out / "lecture_assets.json", cz.lecture_assets(course_id, item.item_id))
        if fetch_video and (url := best_video_url(video)):
            cz.download(url, cfg.path("media", course_key, item.item_id, "video.mp4"), paced=False)
            detail["video"] = True
    elif item.type == "reading":
        data, layer = cz.supplement(course_id, item)
        write_json(out / "supplement.json", data)
        html = cz.reading_html(data) or ""
        (out / "reading.html").write_text(html, encoding="utf-8")
        write_json(out / "assets.json", _reading_assets(cz, html, out))
    elif item.type == "quiz":
        data = cz.quiz_state(course_id, item.item_id)
        write_json(out / "quiz_state.json", data)
        layer = "fetch"
        attempts = (((data.get("data") or {}).get("SubmissionState") or {}).get("queryState") or {}).get("attempts") or {}
        detail["attempts_made"] = attempts.get("attemptsMade")
        if attempts.get("lastSubmission"):
            write_json(out / "quiz_feedback.json", cz.quiz_feedback(course_id, item.item_id))
    else:
        raise AdapterError(f"no fetcher for type {item.type} ({item.coursera_kind})")

    files = [p for p in out.rglob("*") if p.is_file()]
    return out, layer, {**detail, "raw_sha256": sha256_files(files)}


def run(cfg: Config, course_key: str, modules: list[int] | None = None, *, refresh: bool = False,
        fetch_video: bool = True, dry_run: bool = False,
        echo: Callable[[str], None] = print) -> None:
    slug = cfg.courses.get(course_key)
    if not slug:
        raise SystemExit(f"unknown course key {course_key!r}; add it under [courses] in sv.toml")
    state = State(cfg, course_key)

    with session(cfg, minimized=True) as (ctx, page, guard):
        cz = Coursera(cfg, ctx, page, guard, Pacer(cfg.pacing))
        cz.open(f"{BASE}/learn/{slug}/home/module/{modules[0] if modules else 1}")
        manifest, materials = cz.manifest(course_key, slug, {"key": course_key})
        stamp = datetime.now().strftime("%Y%m%d")
        write_json(cfg.path("raw", course_key, "_course", stamp, "materials.json"), materials)
        write_json(manifest_path(cfg, course_key), manifest.model_dump(mode="json"))
        modules = modules or [m.n for m in manifest.modules]  # none given: every module

        todo = [it for m in manifest.modules if m.n in modules
                for lsn in m.lessons for it in lsn.items
                if refresh or not state.get(f"{course_key}.{it.item_id}").fetched.at]
        echo(f"{manifest.title}: {len(todo)} items to fetch in modules {modules}")
        if dry_run:
            for it in todo:
                echo(f"  {it.type:9} {it.item_id} {it.title}" + (f"  [skip: {it.skip_reason}]" if it.skip_reason else ""))
            return

        # Backfill: quizzes cached before feedback capture existed get only the feedback call.
        for m in manifest.modules:
            for it in (i for lsn in m.lessons for i in lsn.items if m.n in modules and i.type == "quiz"):
                st = state.get(f"{course_key}.{it.item_id}")
                d = st.fetched.detail
                if st.fetched.at and d.get("attempts_made") and d.get("dir"):
                    raw = cfg.data_root / d["dir"]
                    if not (raw / "quiz_feedback.json").exists():
                        write_json(raw / "quiz_feedback.json", cz.quiz_feedback(manifest.course_id, it.item_id))
                        state.mark(f"{course_key}.{it.item_id}", "fetched",
                                   sha256=sha256_files([p for p in raw.rglob("*") if p.is_file()]),
                                   detail={**d, "feedback": True})
                        echo(f"feedback backfilled: {it.item_id} {it.title}")

        # Backfill: reading files the link detector missed in earlier runs.
        for m in manifest.modules:
            for it in (i for lsn in m.lessons for i in lsn.items if m.n in modules and i.type == "reading"):
                sid = f"{course_key}.{it.item_id}"
                d = state.get(sid).fetched.detail
                if not d.get("dir"):
                    continue
                raw = cfg.data_root / d["dir"]
                assets = json.loads((raw / "assets.json").read_text(encoding="utf-8"))
                have = {a["src"] for a in assets}
                html = (raw / "reading.html").read_text(encoding="utf-8")
                for a in HTMLParser(html).css("a[href]"):
                    href = urljoin(BASE, a.attributes.get("href") or "")
                    if href in have or GOOGLE_DOC.match(href) or not (ext := _file_ext(href)):
                        continue
                    label = a.text(strip=True)
                    dest = raw / "resources" / f"{slugify(label or Path(href.split('?')[0]).stem, 40)}.{ext}"
                    cz.download(href, dest)
                    assets.append({"kind": ext, "src": href, "file": f"resources/{dest.name}", "label": label})
                    have.add(href)
                    echo(f"resource backfilled: {it.item_id} {dest.name}")
                write_json(raw / "assets.json", assets)
                state.mark(sid, "fetched", sha256=sha256_files([p for p in raw.rglob("*") if p.is_file()]),
                           detail=d)

        for n, it in enumerate(todo, start=1):
            sid = f"{course_key}.{it.item_id}"
            if it.skip_reason:
                _log(cfg, "skips.jsonl", {"id": sid, "kind": it.coursera_kind, "title": it.title,
                                          "reason": it.skip_reason})
                if it.skip_reason.startswith("locked"):
                    echo(f"[{n}/{len(todo)}] locked, skipped for now: {it.title}")
                else:
                    state.mark(sid, "fetched", detail={"skipped": it.skip_reason})
                continue
            out, layer, detail = fetch_item(cz, cfg, course_key, manifest.course_id, it, fetch_video)
            state.mark(sid, "fetched", sha256=detail.pop("raw_sha256"),
                       detail={"layer": layer, "dir": str(out.relative_to(cfg.data_root)), **detail})
            echo(f"[{n}/{len(todo)}] {it.type:8} {it.item_id} via {layer}  {it.title}")
