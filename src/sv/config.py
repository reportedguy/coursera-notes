"""Load settings from <data_root>/config/sv.toml (optional) and config/courses.json.

The data root comes from the SV_DATA_ROOT environment variable, else ~/StudyNotebook.
`notebook add` registers courses in courses.json; sv.toml [courses] still works.
"""

from __future__ import annotations

import json
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_data_path

DEFAULT_DATA_ROOT = Path.home() / "StudyNotebook"
PACKAGE_DIR = Path(__file__).resolve().parent


@dataclass
class Pacing:
    min_delay_s: float = 2.0
    max_delay_s: float = 4.0
    pause_every: int = 40
    pause_min_s: float = 20
    pause_max_s: float = 60
    hourly_cap: int = 600


@dataclass
class Config:
    data_root: Path
    browser_profile: Path
    pacing: Pacing = field(default_factory=Pacing)
    courses: dict[str, str] = field(default_factory=dict)  # course key -> Coursera slug
    titles: dict[str, str] = field(default_factory=dict)  # course key -> display title

    def path(self, *parts: str) -> Path:
        return self.data_root.joinpath(*parts)


def data_root() -> Path:
    return Path(os.environ.get("SV_DATA_ROOT", DEFAULT_DATA_ROOT)).expanduser()


def load() -> Config:
    root = data_root()
    cfg_file = root / "config" / "sv.toml"
    raw = tomllib.loads(cfg_file.read_text(encoding="utf-8")) if cfg_file.exists() else {}
    paths = raw.get("paths", {})
    # The login profile lives outside the data root so backups never copy session cookies.
    profile = paths.get("browser_profile") or user_data_path("study-notebook") / "chrome-profile"
    reg = root / "config" / "courses.json"
    courses = {**raw.get("courses", {}),
               **(json.loads(reg.read_text(encoding="utf-8")) if reg.exists() else {})}
    return Config(
        data_root=Path(paths.get("data_root", root)),
        browser_profile=Path(os.path.expandvars(str(profile))),
        pacing=Pacing(**raw.get("pacing", {})),
        courses=courses,
        titles=raw.get("titles", {}),
    )


def save_course(cfg: Config, key: str, slug: str) -> None:
    reg = cfg.path("config", "courses.json")
    reg.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(reg.read_text(encoding="utf-8")) if reg.exists() else {}
    data[key] = slug
    reg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    cfg.courses[key] = slug
