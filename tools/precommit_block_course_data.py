"""Pre-commit hook: refuse to commit anything that looks like Coursera course data.

Course data belongs in the data folder (default ~/StudyNotebook), never in this repo.
Run by pre-commit with the staged file names as arguments.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

BLOCKED_EXT = {".vtt", ".srt", ".har", ".apkg", ".mp4", ".webm", ".m4a"}
BLOCKED_DIRS = ("sv-data/", "data/", "vault/", "raw/", "norm/", "user-notes/", "pages/", "work/", "notebook/")
MAX_BYTES = 500_000
# README images and the demo GIF, built from the original samples in examples/: exempt from the size cap only.
DEMO_ASSETS = ("docs/assets/",)
# Markers that appear in captured course content or session cookies.
CONTENT_MARKERS = re.compile(rb"coursera\.org/learn/[^\s)]+/(lecture|supplement|quiz|exam)/|CAUTH=")
# Files allowed to mention the markers (code and docs that describe them).
ALLOW = {"tools/precommit_block_course_data.py"}


def problems(path: Path) -> list[str]:
    rel = path.as_posix()
    if rel in ALLOW:
        return []
    found = []
    if path.suffix.lower() in BLOCKED_EXT:
        found.append(f"blocked file type {path.suffix}")
    if rel.startswith(BLOCKED_DIRS):
        found.append("inside a course-data folder")
    if path.is_file():
        if path.stat().st_size > MAX_BYTES and not rel.startswith(DEMO_ASSETS):
            found.append(f"larger than {MAX_BYTES // 1000} KB")
        if CONTENT_MARKERS.search(path.read_bytes()):
            found.append("contains Coursera item URLs or a session cookie")
    return found


def main(argv: list[str]) -> int:
    bad = {f: p for f in argv if (p := problems(Path(f)))}
    for f, reasons in bad.items():
        print(f"BLOCKED {f}: {'; '.join(reasons)}")
    if bad:
        print("Course data must stay in the data folder (~/StudyNotebook). Commit aborted.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
