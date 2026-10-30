"""Windows-safe naming and data-root layout.

Every path the pipeline writes goes through this module, so the rules for
length, reserved names and encoding live in one place.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

MAX_SLUG = 50
MAX_PATH = 200  # well under Windows' 260 limit, leaves room for tools that append suffixes

_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}

def slugify(text: str, max_len: int = MAX_SLUG) -> str:
    """ASCII, lowercase, hyphenated, no reserved names, no trailing dots or spaces."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    text = text[:max_len].rstrip("-.") or "untitled"
    if text in _RESERVED:
        text = f"{text}-x"
    return text


def check_path(path: Path) -> Path:
    """Raise if a path would be too long for comfortable use on Windows."""
    if len(str(path)) > MAX_PATH:
        raise ValueError(f"path longer than {MAX_PATH} chars: {path}")
    return path


def unique_names(names: list[str]) -> list[str]:
    """De-duplicate names case-insensitively (Windows file systems ignore case)."""
    seen: dict[str, int] = {}
    out = []
    for name in names:
        key = name.lower()
        if key in seen:
            seen[key] += 1
            name = f"{name}-{seen[key]}"
        else:
            seen[key] = 1
        out.append(name)
    return out
