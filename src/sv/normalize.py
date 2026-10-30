"""`sv normalize`: raw cache -> one NormItem JSON per item (deterministic, no network).

- Lectures: VTT cues merged into sentence-sized segments (<= 20 s), glossary
  corrections applied and logged, transcript/duration mismatch flagged.
- Readings: HTML -> GFM via markdownify, split into paragraphs p1..pn,
  images copied into the vault.
- Quizzes: questions, options, your answers and feedback from the last submission.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from html import escape
from pathlib import Path

import yaml

from markdownify import markdownify

from sv import quiz_parse
from sv.config import Config
from sv.models import Asset, Cue, ManifestItem, NormItem, Paragraph, Transcript
from sv.state import State, load_manifest, now, sha256_bytes, write_json

_TS = re.compile(r"(\d+):(\d\d):(\d\d)[.,](\d{3})\s*-->\s*(\d+):(\d\d):(\d\d)[.,](\d{3})")
SEGMENT_MAX_S = 20.0
SEGMENT_MIN_S = 6.0


def _secs(h, m, s, ms) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_vtt(text: str) -> list[Cue]:
    cues, i = [], 0
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = [ln for ln in block.strip().split("\n") if ln.strip()]
        for k, ln in enumerate(lines):
            if m := _TS.search(ln):
                body = " ".join(lines[k + 1:]).strip()
                body = re.sub(r"<[^>]+>", "", body)
                if body:
                    cues.append(Cue(i=i, start=_secs(*m.groups()[:4]), end=_secs(*m.groups()[4:]), text=body))
                    i += 1
                break
    return cues


def segment(cues: list[Cue]) -> list[Cue]:
    """Merge caption fragments into segments that end at a sentence when possible."""
    out: list[Cue] = []
    cur: list[Cue] = []
    for c in cues:
        cur.append(c)
        dur = cur[-1].end - cur[0].start
        sentence_end = c.text.rstrip().endswith((".", "?", "!"))
        if dur >= SEGMENT_MAX_S or (sentence_end and dur >= SEGMENT_MIN_S):
            out.append(Cue(i=len(out), start=cur[0].start, end=cur[-1].end,
                           text=" ".join(x.text for x in cur)))
            cur = []
    if cur:
        out.append(Cue(i=len(out), start=cur[0].start, end=cur[-1].end, text=" ".join(x.text for x in cur)))
    return out


class Glossary:
    def __init__(self, cfg: Config):
        path = cfg.path("registry", "glossary.yml")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.rules = [(re.compile(r["from"], re.I if "i" in r.get("flags", "") else 0), r["to"])
                      for r in (data or {}).get("corrections", [])]
        self.log_path = cfg.path("registry", "corrections.jsonl")

    def apply(self, item_id: str, cues: list[Cue]) -> list[Cue]:
        if not self.rules:
            return cues
        logs = []
        for c in cues:
            for rx, to in self.rules:
                new = rx.sub(to, c.text)
                if new != c.text:
                    logs.append({"id": item_id, "t": c.start, "from": rx.pattern, "to": to,
                                 "before": c.text[:120]})
                    c.text = new
        if logs:
            with self.log_path.open("a", encoding="utf-8") as f:
                for rec in logs:
                    f.write(json.dumps({"at": now().isoformat(), **rec}, ensure_ascii=False) + "\n")
        return cues


def _flatten_tables(html: str) -> str:
    """GFM pipe tables can't hold block content; pandoc then emits [TABLE]. Reduce
    every cell to inline text (paragraph breaks become '; ') so tables survive."""
    from selectolax.lexbor import LexborHTMLParser

    tree = LexborHTMLParser(html)
    cells = tree.css("td, th")
    if not cells:
        return html
    for cell in cells:
        blocks = cell.css("li") or cell.css("p") or [cell]  # li may wrap p: take one level only
        parts = []
        for n in blocks:
            t = re.sub(r"\s+", " ", n.text(separator="")).strip()
            if t and t not in parts:
                parts.append(t)
        cell.inner_html = escape("; ".join(parts), quote=False)
    return tree.html


def html_to_paragraphs(html: str) -> list[Paragraph]:
    html = _flatten_tables(html)
    # markdownify drops whitespace-only <strong> </strong>, gluing the words around it.
    html = re.sub(r"<(strong|b|em|i)>(?:\s|&nbsp;)+</\1>", " ", html)
    md = markdownify(html, heading_style="ATX", bullets="-", strip=["script", "style"])
    blocks = [b.strip() for b in re.split(r"\n\s*\n", md) if b.strip()]
    return [Paragraph(pid=f"p{n}", md=b) for n, b in enumerate(blocks, start=1)]


def _swap_url(html: str, url: str, local: str) -> str:
    """Replace a URL in raw HTML, where it may appear with & escaped as &amp;."""
    return html.replace(url, local).replace(escape(url, quote=False), local)


def frame_assets(cfg: Config, raw: Path) -> list[Asset]:
    """Frame and contact-sheet assets written by `sv media`, if it has run."""
    frames_file = raw / "frames.json"
    if not frames_file.exists():
        return []
    frames = json.loads(frames_file.read_text(encoding="utf-8"))
    rel = lambda p: str((raw / p).relative_to(cfg.data_root)).replace("\\", "/")  # noqa: E731
    out = []
    if frames:
        out.append(Asset(kind="contact-sheet", path=rel("contact-sheet.jpg"),
                         sha256=sha256_bytes((raw / "contact-sheet.jpg").read_bytes())))
    for f in frames:
        out.append(Asset(kind="frame", path=rel(f["file"]), caption=f"#{f['n']} at {f['t']:.0f}s",
                         sha256=sha256_bytes((raw / f["file"]).read_bytes())))
    return out


def _latest_raw(cfg: Config, course_key: str, item_id: str) -> Path | None:
    base = cfg.path("raw", course_key, item_id)
    dirs = sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []
    return dirs[-1] if dirs else None


def normalize_item(cfg: Config, course_key: str, order: str, it: ManifestItem,
                   glossary: Glossary, fetched_at: datetime) -> NormItem | None:
    raw = _latest_raw(cfg, course_key, it.item_id)
    if raw is None:
        return None
    sid = f"{course_key}.{it.item_id}"
    item = NormItem(id=sid, type=it.type, order=order, title=it.title, url=it.public_url,
                    duration_s=it.duration_s, fetched_at=fetched_at, raw_sha256="")
    files = sorted(p for p in raw.rglob("*") if p.is_file())
    item.raw_sha256 = sha256_bytes(b"".join(p.read_bytes() for p in files))

    if it.type == "lecture":
        vtt = raw / "transcript.en.vtt"
        if vtt.exists():
            cues = glossary.apply(sid, segment(parse_vtt(vtt.read_text(encoding="utf-8"))))
            item.transcript = Transcript(source="coursera-manual", cues=cues)
            if it.duration_s and cues:
                ratio = cues[-1].end / it.duration_s
                if not 0.9 <= ratio <= 1.05:
                    item.flags.append(f"transcript_mismatch:{ratio:.2f}")
        else:
            item.flags.append("no_transcript")
        item.assets.extend(frame_assets(cfg, raw))
    elif it.type == "reading":
        html = (raw / "reading.html").read_text(encoding="utf-8")
        assets = json.loads((raw / "assets.json").read_text(encoding="utf-8"))
        img_dir = cfg.path("vault", "assets", "img", course_key, it.item_id)
        for a in assets:
            if a.get("file") and a["kind"] == "image":
                img_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(raw / "assets" / a["file"], img_dir / a["file"])
                rel = f"assets/img/{course_key}/{it.item_id}/{a['file']}"
                html = _swap_url(html, a["src"], rel)
                item.assets.append(Asset(kind="image", path=rel, caption=a.get("alt") or None,
                                         sha256=sha256_bytes((img_dir / a["file"]).read_bytes())))
            elif a.get("file"):
                rel = str((raw / a["file"]).relative_to(cfg.data_root)).replace("\\", "/")
                html = _swap_url(html, a["src"], rel)  # signed URLs expire; point at the cached copy
                item.assets.append(Asset(kind=a["kind"] if a["kind"] in ("pdf", "xlsx", "docx", "pptx") else "other",
                                         path=rel, caption=a.get("label"),
                                         sha256=sha256_bytes((raw / a["file"]).read_bytes())))
            elif a.get("error"):
                item.flags.append(f"resource_unavailable:{a['src']}")
        item.paragraphs = html_to_paragraphs(html)
    elif it.type == "quiz":
        data = json.loads((raw / "quiz_state.json").read_text(encoding="utf-8"))
        fb_file = raw / "quiz_feedback.json"
        feedback = json.loads(fb_file.read_text(encoding="utf-8")) if fb_file.exists() else None
        item.questions, quiz_flags = quiz_parse.parse(data, feedback)
        item.flags.extend(quiz_flags)
    return item


def run(cfg: Config, course_key: str, modules: list[int], force: bool = False, echo=print) -> None:
    manifest = load_manifest(cfg, course_key)
    state = State(cfg, course_key)
    glossary = Glossary(cfg)
    counts: dict[str, int] = {}
    for mod in manifest.modules:
        if mod.n not in modules:
            continue
        for lsn in mod.lessons:
            for it in lsn.items:
                sid = f"{course_key}.{it.item_id}"
                st = state.get(sid)
                if not st.fetched.at or st.fetched.detail.get("skipped"):
                    continue
                if not force and st.normalized.input_sha256 == st.fetched.sha256 and cfg.path("norm", course_key, f"{it.item_id}.json").exists():
                    continue  # unchanged since last run
                order = f"{mod.n:02d}.{lsn.n:02d}.{it.n:02d}"
                item = normalize_item(cfg, course_key, order, it, glossary, st.fetched.at)
                if item is None:
                    continue
                out = cfg.path("norm", course_key, f"{it.item_id}.json")
                write_json(out, item.model_dump(mode="json"))
                state.mark(sid, "normalized", sha256=sha256_bytes(out.read_bytes()),
                           input_sha256=st.fetched.sha256, detail={"flags": item.flags})
                counts[it.type] = counts.get(it.type, 0) + 1
                for flag in item.flags:
                    echo(f"  flag {it.item_id}: {flag}")
    echo(f"normalized: {counts or 'nothing new'}")
