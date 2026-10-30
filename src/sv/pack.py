"""`sv pack`: build the compact input files the generation subagents read.

- work/packs/<course>/mNN-lLL.md: one file per lesson with every item's source text,
  frame and image references, and quiz attempts.

Packs contain everything an agent needs so it never reads raw data itself.
"""

from __future__ import annotations

from pathlib import Path

from sv.config import Config
from sv.models import ManifestItem, NormItem
from sv.state import State, load_manifest, sha256_bytes, write_atomic


def _mmss(s: float) -> str:
    return f"{int(s // 60):02d}:{int(s % 60):02d}"


def item_block(cfg: Config, course_key: str, mod_n: int, lsn_n: int, it: ManifestItem, item: NormItem) -> str:
    head = [f"## Item {item.order} ({it.type}): {it.title}", "",
            f"- id: `{item.id}` (frames: `frame:{it.item_id}:<n>`)", f"- url: {item.url}"]
    if item.duration_s:
        head.append(f"- duration: {_mmss(item.duration_s)}")
    sheet = next((a for a in item.assets if a.kind == "contact-sheet"), None)
    if sheet:
        n = sum(1 for a in item.assets if a.kind == "frame")
        head.append(f"- contact sheet (frames #1–#{n}): `{cfg.data_root / sheet.path}`")
    imgs = [a for a in item.assets if a.kind == "image"]
    for a in imgs:
        head.append(f"- image: link as `![<alt>]({a.path})`; view at `{cfg.path('vault', a.path)}`"
                    + (f" ({a.caption})" if a.caption else ""))
    for a in item.assets:
        if a.kind in ("pdf", "docx", "xlsx", "pptx", "other"):
            head.append(f"- resource: `resource:{a.path}`" + (f" ({a.caption})" if a.caption else ""))
    if item.flags:
        head.append(f"- flags: {', '.join(item.flags)}")
    body = [""]

    if item.transcript:
        body += ["### Transcript segments", ""]
        body += [f"[s{c.i} | {_mmss(c.start)}–{_mmss(c.end)} | t={int(c.start)}] {c.text}"
                 for c in item.transcript.cues]
    elif item.paragraphs:
        body += ["### Paragraphs", ""]
        body += [f"[{p.pid}] {p.md}" for p in item.paragraphs]
    elif it.type == "quiz":
        body += ["### Quiz (from your past attempt)", ""]
        if not item.questions:
            body.append("(no submission captured: write only `## What this quiz tests` if the title makes it clear, else a one-line note that it wasn't attempted)")
        for q in item.questions:
            body.append(f"**{q.qid.upper()}.** {q.stem}")
            for i, o in enumerate(q.options):
                body.append(f"  {chr(65 + i)}. {o}")
            fmt = lambda v: ", ".join(chr(65 + i) for i in v) if isinstance(v, list) else (v or "—")  # noqa: E731
            body.append(f"  your answer: {fmt(q.my_answer) if q.options else '(free text, not shown)'}"
                        f" | key: {fmt(q.correct)} ({q.correct_source})")
            if q.feedback:
                body.append(f"  feedback: {q.feedback}")
            body.append("")
    return "\n".join(head + body) + "\n"


def run(cfg: Config, course_key: str, modules: list[int], echo=print) -> list[Path]:
    manifest = load_manifest(cfg, course_key)
    state = State(cfg, course_key)
    packs = []
    for mod in (m for m in manifest.modules if m.n in modules):
        for lsn in mod.lessons:
            blocks = []
            for it in lsn.items:
                norm = cfg.path("norm", course_key, f"{it.item_id}.json")
                if it.skip_reason or not norm.exists():
                    continue
                item = NormItem.model_validate_json(norm.read_text(encoding="utf-8"))
                blocks.append(item_block(cfg, course_key, mod.n, lsn.n, it, item))
            if not blocks:
                continue
            header = f"# Pack: {manifest.title}, Module {mod.n}: {mod.title}, Lesson {lsn.n}: {lsn.title}\n\n"
            path = cfg.path("work", "packs", course_key, f"m{mod.n:02d}-l{lsn.n:02d}.md")
            write_atomic(path, header + "\n---\n\n".join(blocks))
            digest = sha256_bytes(path.read_bytes())
            for it in lsn.items:
                if not it.skip_reason:
                    st = state.get(f"{course_key}.{it.item_id}")
                    st.generated.detail["pack"] = str(path.relative_to(cfg.data_root))
                    st.generated.detail["pack_sha256"] = digest
            packs.append(path)
            echo(f"{path}  ({len(blocks)} items, ~{len(path.read_text(encoding='utf-8')) // 4} tokens)")
    state.save()
    return packs
