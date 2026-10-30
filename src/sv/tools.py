"""Locate external executables: PATH first, then standard install paths on Windows,
macOS and Linux (a fresh install is often not on PATH until a new shell starts).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_PF = [os.environ.get(v, "") for v in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
_FALLBACKS: dict[str, list[Path]] = {
    "chrome": [Path(p, "Google", "Chrome", "Application", "chrome.exe") for p in _PF if p]
    + [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")],
    "msedge": [Path(p, "Microsoft", "Edge", "Application", "msedge.exe") for p in _PF if p]
    + [Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")],
}
_ALIASES = {"chrome": ["chrome", "google-chrome", "google-chrome-stable"],
            "msedge": ["msedge", "microsoft-edge", "microsoft-edge-stable"]}


def find(name: str) -> str | None:
    for alias in _ALIASES.get(name, [name]):
        if exe := shutil.which(alias):
            return exe
    for candidate in _FALLBACKS.get(name, []):
        if candidate.exists():
            return str(candidate)
    return None


def require(name: str) -> str:
    exe = find(name)
    if not exe:
        raise FileNotFoundError(f"{name} not found; run `notebook doctor`")
    return exe


def browser() -> tuple[str, str]:
    """(executable, Playwright channel) for the installed Chrome, else Edge."""
    for channel in ("chrome", "msedge"):
        if exe := find(channel):
            return exe, channel
    raise FileNotFoundError("Google Chrome or Microsoft Edge is required; install one and re-run")
