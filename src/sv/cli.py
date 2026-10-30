"""`notebook` command-line entry point."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer

from sv import config, tools

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _stopped(stop: Exception) -> None:
    typer.echo(f"STOPPED (progress saved): {stop}")
    raise typer.Exit(2)


@app.command()
def doctor() -> None:
    """Check what the tool needs. ffmpeg is only needed for --slides."""
    rows: list[tuple[str, str | None, bool]] = []
    try:
        exe, channel = tools.browser()
        rows.append(("browser", f"{channel}: {exe}", True))
    except FileNotFoundError as e:
        rows.append(("browser", str(e), False))
    ff = tools.find("ffmpeg")
    rows.append(("ffmpeg (for --slides only)", ff or "not installed", True))
    root = config.data_root()
    rows.append(("data folder", str(root), True))
    profile = config.load().browser_profile
    rows.append(("login", "saved session found" if profile.exists() else "run `notebook login`", True))
    for name, value, ok in rows:
        typer.echo(f"[{'OK  ' if ok else 'MISS'}] {name.ljust(26)} {value}")
    if not all(ok for *_, ok in rows):
        raise typer.Exit(1)


@app.command()
def login(url: str = "https://www.coursera.org/", timeout_min: int = 15) -> None:
    """Open a dedicated browser window so you sign in yourself. Your password is never seen or stored.

    The browser starts as a plain process, not through Playwright: Google sign-in and most
    SSO pages refuse to log in from a browser that carries automation flags.
    """
    from sv.browser import is_logged_in, session

    cfg = config.load()
    cfg.browser_profile.mkdir(parents=True, exist_ok=True)
    typer.echo("Sign in to Coursera in the window that opens (2FA/SSO as usual), then close it.")
    proc = subprocess.Popen([
        tools.browser()[0], f"--user-data-dir={cfg.browser_profile}",
        "--no-first-run", "--no-default-browser-check", "--new-window", url,
    ])
    try:
        proc.wait(timeout=timeout_min * 60)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait()
    with session(cfg, visible=False) as (ctx, _, _):
        state = "logged in" if is_logged_in(ctx) else "NOT logged in"
    typer.echo(f"login session ended ({state})")


def _modules(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out.extend(range(int(a), int(b or a) + 1))
    return out


@app.command()
def add(
    url: str = typer.Argument(..., help="A Coursera course, specialization or professional certificate link"),
    modules: str = typer.Option("", help="Only these modules, e.g. 1-3 (default: all)"),
    slides: bool = typer.Option(False, help="Also take slide frames from videos (needs ffmpeg)"),
) -> None:
    """Fetch and prepare every course behind a link; print the writing plan as JSON."""
    from sv import add as ad
    from sv.browser import StopRun

    if slides and not tools.find("ffmpeg"):
        typer.echo("--slides needs ffmpeg on PATH; install it or drop --slides")
        raise typer.Exit(1)
    try:
        plan = ad.run(config.load(), url, modules=_modules(modules) if modules else None,
                      slides=slides, echo=lambda s: typer.echo(s, err=True))
    except StopRun as stop:
        _stopped(stop)
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)
    typer.echo(json.dumps(plan, indent=2, ensure_ascii=False))


@app.command()
def ingest(
    course: str,
    modules: str = typer.Argument("", help="e.g. 2 or 1-4 or 1,3 (default: all)"),
    refresh: bool = typer.Option(False, help="Re-fetch items already in the cache"),
    video: bool = typer.Option(False, help="Download the MP4 for frame extraction"),
    dry_run: bool = typer.Option(False, help="Fetch the structure only and list what would be fetched"),
) -> None:
    """Fetch one registered course into the raw cache (each item once). Retries locked items."""
    from sv import ingest as ing
    from sv.browser import StopRun

    try:
        ing.run(config.load(), course, _modules(modules) if modules else None, refresh=refresh,
                fetch_video=video, dry_run=dry_run, echo=typer.echo)
    except StopRun as stop:
        _stopped(stop)


@app.command()
def normalize(course: str, modules: str, force: bool = typer.Option(False, help="Redo unchanged items")) -> None:
    """Turn cached raw items into normalized JSON (no network)."""
    from sv import normalize as norm

    norm.run(config.load(), course, _modules(modules), force=force, echo=typer.echo)


@app.command()
def media(course: str, modules: str, keep_video: bool = typer.Option(False)) -> None:
    """Extract slide frames from downloaded videos, then delete the videos."""
    from sv import media as med

    med.run(config.load(), course, _modules(modules), keep_video=keep_video, echo=typer.echo)


@app.command()
def pack(course: str, modules: str) -> None:
    """Write the per-lesson packs the page writers read."""
    from sv import pack as pk

    pk.run(config.load(), course, _modules(modules), echo=typer.echo)


@app.command()
def qa(course: str, apply: bool = typer.Option(False, help="Write qa.json from candidates minus qa-drop.json")) -> None:
    """Extract answered quiz questions for the Question practice page."""
    from sv import qa as q

    q.run(config.load(), course, apply=apply, echo=typer.echo)


@app.command()
def build(live: str = typer.Option("", help="Saved HTML of the live notebook, to keep its edits")) -> None:
    """Assemble notebook.html from the written pages."""
    from sv import notebook as nb

    nb.build(config.load(), Path(live) if live else None, echo=typer.echo)


if __name__ == "__main__":
    app()
