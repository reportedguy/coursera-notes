"""`sv qa`: Coursera quiz questions with known answers, for the Question practice page.

Writes <data_root>/pages/<course>/qa-candidates.json. A filter agent then lists the
basic ones in qa-drop.json, and `sv qa --apply` writes qa.json (the kept questions).
Reflection prompts and acknowledgements are dropped here; they have nothing to test.
"""

from __future__ import annotations

import json
import re

from sv.config import Config
from sv.models import NormItem
from sv.state import load_manifest, write_json

REFLECT = re.compile(r"Reflect|RichText|TextReflect")


def _explanation(feedback: str | None, correct: list[int]) -> str:
    """Pick the feedback written for the correct options ('[A] text [B] text ...')."""
    if not feedback:
        return ""
    body = re.sub(r"^\([^)]*\)\s*", "", feedback)
    parts = dict(re.findall(r"\[([A-H])\]\s*(.*?)(?=\s*\[[A-H]\]|$)", body, flags=re.S))
    picked = [parts[chr(65 + i)].strip() for i in correct if chr(65 + i) in parts]
    text = " ".join(p for p in picked if p and not p.lower().startswith(("please review", "not quite", "review the")))
    return text or ""


def candidates(cfg: Config, course_key: str) -> list[dict]:
    man = load_manifest(cfg, course_key)
    out = []
    for mod in man.modules:
        for lsn in mod.lessons:
            for it in lsn.items:
                if it.type != "quiz":
                    continue
                p = cfg.path("norm", course_key, f"{it.item_id}.json")
                if not p.exists():
                    continue
                item = NormItem.model_validate_json(p.read_text(encoding="utf-8"))
                for q in item.questions:
                    if not q.options or q.correct is None or REFLECT.search(q.feedback or "") or len(q.options) < 2:
                        continue
                    out.append({
                        "id": f"{it.item_id}.{q.qid}", "module": mod.n, "quiz": it.title,
                        "question": q.stem, "options": q.options,
                        "answer": [chr(65 + i) for i in q.correct],
                        "multi": len(q.correct) > 1 or "Checkbox" in (q.feedback or ""),
                        "explanation": _explanation(q.feedback, q.correct),
                    })
    return out


def run(cfg: Config, course_key: str, apply: bool = False, echo=print) -> None:
    folder = cfg.path("pages", course_key)
    folder.mkdir(parents=True, exist_ok=True)
    if not apply:
        qs = candidates(cfg, course_key)
        write_json(folder / "qa-candidates.json", qs)
        echo(f"{len(qs)} candidate questions -> {folder / 'qa-candidates.json'}")
        return
    qs = json.loads((folder / "qa-candidates.json").read_text(encoding="utf-8"))
    drop_file = folder / "qa-drop.json"
    drop = {d["id"] for d in json.loads(drop_file.read_text(encoding="utf-8"))} if drop_file.exists() else set()
    why_file = folder / "qa-why.json"
    why = json.loads(why_file.read_text(encoding="utf-8")) if why_file.exists() else {}
    kept = [{**q, "why": why.get(q["id"]) or q.get("explanation", "")} for q in qs if q["id"] not in drop]
    write_json(folder / "qa.json", kept)
    echo(f"kept {len(kept)} of {len(qs)} questions -> {folder / 'qa.json'}")
