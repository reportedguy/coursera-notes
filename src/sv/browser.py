"""Dedicated Chrome session, request pacing, and the account-safety stop rules.

Only this module and coursera_adapter.py talk to the browser.
"""

from __future__ import annotations

import random
import time
from collections import deque
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

from playwright.sync_api import BrowserContext, Page, Response, sync_playwright

from sv import tools
from sv.config import Config, Pacing

CHALLENGE_MARKERS = ("recaptcha", "hcaptcha", "challenges.cloudflare.com", "turnstile")


class StopRun(RuntimeError):
    """Raised when Coursera shows a sign we should stop and ask the user."""


class Pacer:
    """Random human-ish delays, a periodic longer pause, and a rolling hourly cap."""

    def __init__(self, pacing: Pacing):
        self.p = pacing
        self.count = 0
        self.window: deque[float] = deque()

    def wait(self) -> None:
        now = time.monotonic()
        while self.window and now - self.window[0] > 3600:
            self.window.popleft()
        if len(self.window) >= self.p.hourly_cap:
            raise StopRun(f"hourly cap of {self.p.hourly_cap} requests reached; re-run later")
        self.count += 1
        if self.count % self.p.pause_every == 0:
            time.sleep(random.uniform(self.p.pause_min_s, self.p.pause_max_s))
        time.sleep(random.uniform(self.p.min_delay_s, self.p.max_delay_s))
        self.window.append(time.monotonic())


class Guard:
    """Watches every response; trips on rate limiting, blocks, or a login redirect."""

    def __init__(self) -> None:
        self.tripped: str | None = None
        self.forbidden: list[str] = []

    def on_response(self, resp: Response) -> None:
        host = urlparse(resp.url).hostname or ""
        if not host.endswith("coursera.org"):
            return
        if resp.status == 429:
            self.tripped = f"HTTP 429 (rate limited) on {resp.url}"
        elif resp.status == 403:
            # Page-originated 403s happen for features the account lacks; log them, and
            # let check() treat a 403 on the page document itself as a hard stop.
            self.forbidden.append(resp.url)
            if resp.request.resource_type == "document":
                self.tripped = f"HTTP 403 on page {resp.url}"

    def check(self, page: Page) -> None:
        if self.tripped:
            raise StopRun(self.tripped)
        url = page.url.lower()
        if "/login" in url or "authmode=login" in url:
            raise StopRun("Coursera asked to log in again; run `notebook login`, then re-run")
        for frame in page.frames:
            if any(m in frame.url.lower() for m in CHALLENGE_MARKERS):
                raise StopRun("captcha or bot challenge shown; solve it with `notebook login`, then re-run")


@contextmanager
def session(
    cfg: Config, *, har_path: Path | None = None, visible: bool = True, minimized: bool = False
) -> Iterator[tuple[BrowserContext, Page, Guard]]:
    """Open the dedicated persistent profile in real Chrome (never the user's normal profile)."""
    cfg.browser_profile.mkdir(parents=True, exist_ok=True)
    guard = Guard()
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(cfg.browser_profile),
            channel=tools.browser()[1],
            headless=not visible,
            viewport=None,
            args=["--start-minimized"] if minimized else [],
            record_har_path=str(har_path) if har_path else None,
            record_har_content="embed",
            record_har_url_filter="**/*coursera.org/**",
        )
        ctx.on("response", guard.on_response)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            yield ctx, page, guard
        finally:
            ctx.close()


def is_logged_in(ctx: BrowserContext) -> bool:
    return any(c["name"] == "CAUTH" for c in ctx.cookies("https://www.coursera.org"))
