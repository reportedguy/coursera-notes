"""Build the live demo (docs/index.html) from the original sample courses in examples/.

Runs the real `notebook build` against a throwaway data folder, so the demo is exactly
what the tool produces. No network, no Coursera.

    uv run python tools/build_demo.py
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "examples" / "sample-courses"
OUT = REPO / "docs" / "index.html"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["SV_DATA_ROOT"] = tmp
        from sv import config, notebook
        from sv.config import save_course
        from sv.models import CourseManifest, Module
        from sv.state import manifest_path, write_json

        cfg = config.load()
        for course in sorted(p for p in SAMPLES.iterdir() if p.is_dir()):
            meta = json.loads((course / "manifest.json").read_text(encoding="utf-8"))
            man = CourseManifest(
                course_key=course.name, slug=course.name, course_id=course.name, title=meta["title"],
                modules=[Module(n=i, id=f"m{i}", title=t) for i, t in enumerate(meta["modules"], start=1)],
                discovered_at=datetime.now(timezone.utc),
            )
            write_json(manifest_path(cfg, course.name), man.model_dump(mode="json"))
            save_course(cfg, course.name, course.name)
            shutil.copytree(course, cfg.path("pages", course.name), ignore=shutil.ignore_patterns("manifest.json"))
        built = notebook.build(config.load(), echo=print)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(built, OUT)
    print(f"demo: {OUT}")


if __name__ == "__main__":
    main()
