"""Per-course state manifest: what has been fetched, normalized, generated, validated.

Writes are atomic (temp file + replace) so a crash never leaves a half-written manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sv.config import Config
from sv.models import CourseManifest, ItemState, StepState


def now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def write_json(path: Path, data) -> None:
    write_atomic(path, json.dumps(data, indent=2, ensure_ascii=False, default=str))


class State:
    def __init__(self, cfg: Config, course_key: str):
        self.path = cfg.path("state", f"{course_key}.state.json")
        raw = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        self.items: dict[str, ItemState] = {k: ItemState(**v) for k, v in raw.items()}

    def get(self, item_id: str) -> ItemState:
        return self.items.setdefault(item_id, ItemState())

    def mark(self, item_id: str, step: str, **fields) -> None:
        st = self.get(item_id)
        old: StepState = getattr(st, step)
        if old.at:
            st.history.append({"step": step, **old.model_dump(mode="json")})
        setattr(st, step, StepState(at=now(), **fields))
        self.save()

    def save(self) -> None:
        write_json(self.path, {k: v.model_dump(mode="json") for k, v in self.items.items()})


def manifest_path(cfg: Config, course_key: str) -> Path:
    return cfg.path("state", f"{course_key}.course.json")


def load_manifest(cfg: Config, course_key: str) -> CourseManifest:
    return CourseManifest.model_validate_json(manifest_path(cfg, course_key).read_text(encoding="utf-8"))
