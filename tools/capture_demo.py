"""Screenshots and the demo GIF for the README, taken from docs/index.html (the sample demo).

    uv run python tools/build_demo.py && uv run python tools/capture_demo.py

Uses the system Chrome or Edge through Playwright, headless. Writes docs/assets/*.png and demo.gif.
"""

from __future__ import annotations

import io
import re
import os
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright

from sv import tools

REPO = Path(__file__).resolve().parents[1]
DEMO = (REPO / "docs" / "index.html").as_uri()
ASSETS = REPO / "docs" / "assets"
BIZ, PY = "planning-a-small-project", "python-basics"
OPEN_BOTH = f"localStorage.setItem('nb-open', JSON.stringify({{'{BIZ}': true, '{PY}': true}}))"


def go(page: Page, page_id: str) -> None:
    page.goto(f"{DEMO}#{page_id}")
    page.reload()  # the hash alone does not re-render
    page.wait_for_timeout(1500)  # fonts, marked, mermaid


def caret_at_end(page: Page, text: str) -> None:
    """Put the caret at the end of the paragraph that starts with `text`, as a click would."""
    page.evaluate("""t => {
        const p = [...document.querySelectorAll('#doc p')].find(p => p.textContent.startsWith(t));
        p.scrollIntoView({block: 'center'});
        const r = document.createRange(); r.selectNodeContents(p); r.collapse(false);
        const s = getSelection(); s.removeAllRanges(); s.addRange(r); p.closest('[contenteditable]').focus();
    }""", text)


def shot(page: Page, name: str, **kw) -> None:
    page.screenshot(path=str(ASSETS / name), **kw)
    print(f"wrote {name}")


def frame(page: Page, frames: list[Image.Image]) -> None:
    img = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    frames.append(img.resize((img.width * 2 // 3, img.height * 2 // 3), Image.LANCZOS))


def stills(browser) -> None:
    for scheme, suffix in (("light", ""), ("dark", "-dark")):
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2,
                                  color_scheme=scheme)
        ctx.add_init_script(OPEN_BOTH)
        page = ctx.new_page()
        go(page, f"{BIZ}-m1")
        shot(page, f"hero{suffix}.png")
        if scheme == "dark":
            ctx.close()
            continue
        go(page, f"{BIZ}-m2")
        page.locator("h2", has_text="Dependencies and the critical path").scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -70)")
        shot(page, "module-business.png")
        go(page, f"{PY}-m1")
        page.locator("h2", has_text="Converting between types").scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -70)")
        shot(page, "module-technical.png")
        go(page, f"{BIZ}-mindmap")
        page.click("#mmexp")
        page.wait_for_timeout(800)
        page.click("#mmfit")
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        shot(page, "mindmap.png")
        go(page, f"{PY}-qa")
        page.locator(".q").nth(1).locator("li.opt").nth(0).click()
        page.locator(".q").nth(0).locator("li.opt").nth(0).click()
        shot(page, "questions.png")
        go(page, f"{PY}-summary")
        page.locator("h2", has_text="Errors and fixes").scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -70)")
        shot(page, "course-map.png")
        go(page, f"{BIZ}-m1")
        caret_at_end(page, "Most projects fail at the start")
        page.keyboard.type(" /")
        page.wait_for_timeout(500)
        shot(page, "editing.png")
        ctx.close()


def gif(browser) -> None:
    ctx = browser.new_context(viewport={"width": 1200, "height": 750}, color_scheme="light")
    ctx.add_init_script(OPEN_BOTH)
    page = ctx.new_page()
    frames: list[Image.Image] = []
    go(page, f"{BIZ}-m1")
    frame(page, frames)
    page.locator("h2", has_text="Stakeholders").scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    frame(page, frames)
    go(page, f"{BIZ}-mindmap")
    frame(page, frames)
    page.click("#mmexp")
    page.wait_for_timeout(700)
    page.click("#mmfit")
    page.wait_for_timeout(700)
    frame(page, frames)
    go(page, f"{BIZ}-qa")
    frame(page, frames)
    page.locator(".q").nth(0).locator("li.opt").nth(1).click()
    page.wait_for_timeout(300)
    frame(page, frames)
    page.locator(".q").nth(0).locator("li.opt").nth(2).click()
    page.wait_for_timeout(300)
    frame(page, frames)
    go(page, f"{PY}-m1")
    frame(page, frames)
    page.locator("h2", has_text="f-strings").scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    frame(page, frames)
    go(page, f"{PY}-summary")
    page.locator("h2", has_text="Cheat sheet").scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    frame(page, frames)
    go(page, f"{BIZ}-m2")
    caret_at_end(page, "A schedule is a forecast")
    page.keyboard.type(" Review it every Friday.", delay=20)
    frame(page, frames)
    page.wait_for_timeout(4800)  # autosave fires after 4 s idle
    frame(page, frames)
    ctx.close()
    durations = [1600] * len(frames)
    durations[-1] = 2600
    frames[0].save(ASSETS / "demo.gif", save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=True)
    print(f"wrote demo.gif ({len(frames)} frames)")


def terminal(browser) -> None:
    """Real `notebook --help` and `notebook add --help` output in a terminal-style frame."""
    import html
    import shutil
    import subprocess
    import sys

    def run(*args: str) -> str:
        exe = shutil.which("notebook", path=str(Path(sys.executable).parent))  # the installed command
        out = subprocess.run([exe, *args], capture_output=True, text=True,
                             encoding="utf-8", env={**os.environ, "COLUMNS": "92", "NO_COLOR": "1"})
        return re.sub(r"notebook\.exe", "notebook", out.stdout, flags=re.I)  # Windows shows the .EXE name

    body = "".join(f'<span class="p">$</span> notebook {cmd}\n{html.escape(run(*cmd.split()))}\n'
                   for cmd in ("--help", "add --help"))
    page = browser.new_page(viewport={"width": 900, "height": 400}, device_scale_factor=2)
    page.set_content(
        "<style>body{margin:0;background:#0d1117}.w{margin:24px;border-radius:12px;background:#161b22;"
        "box-shadow:0 10px 30px #0008;overflow:hidden}.b{display:flex;gap:8px;padding:12px 14px;background:#21262d}"
        ".b i{width:12px;height:12px;border-radius:50%;background:#ff5f56}.b i:nth-child(2){background:#ffbd2e}"
        ".b i:nth-child(3){background:#27c93f}pre{margin:0;padding:16px 20px;color:#c9d1d9;"
        "font:13px/1.45 ui-monospace,Consolas,monospace}.p{color:#7ee787}</style>"
        f"<div class='w'><div class='b'><i></i><i></i><i></i></div><pre>{body}</pre></div>")
    page.locator(".w").screenshot(path=str(ASSETS / "terminal.png"))
    page.close()
    print("wrote terminal.png")


def social(browser) -> None:
    """1280x640 social preview: title, pitch and the pipeline diagram."""
    svg = (ASSETS / "pipeline.svg").read_text(encoding="utf-8")
    page = browser.new_page(viewport={"width": 1280, "height": 640}, color_scheme="light")
    page.set_content(
        "<style>body{margin:0;width:1280px;height:640px;background:#fff;font-family:Inter,Segoe UI,sans-serif;"
        "display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px}"
        "h1{margin:0;font-size:64px;letter-spacing:-1.5px;color:#1a1a1a}p{margin:0;font-size:26px;color:#5d5b54}"
        "svg{width:1120px;height:auto}</style>"
        "<h1>coursera-notes</h1><p>Your Coursera courses, turned into one notebook you can learn from.</p>" + svg)
    page.screenshot(path=str(ASSETS / "social-preview.png"))
    page.close()
    print("wrote social-preview.png")


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel=tools.browser()[1], headless=True)
        stills(browser)
        gif(browser)
        terminal(browser)
        social(browser)
        browser.close()


if __name__ == "__main__":
    main()
