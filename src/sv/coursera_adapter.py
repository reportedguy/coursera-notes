"""Everything Coursera-specific lives here. See docs/endpoints.md.

Each fetch tries layer 1 (in-page fetch of the JSON/HTML the web app uses), then
layer 2 (navigate to the item page and read what it loaded). Results are checked
for the fields we need; a failure falls through to the next layer and the layer
that worked is reported back for the state manifest.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

from playwright.sync_api import BrowserContext, Page

from sv.browser import Guard, Pacer, StopRun
from sv.config import PACKAGE_DIR, Config
from sv.models import CourseManifest, Lesson, ManifestItem, Module
from sv.paths import slugify

BASE = "https://www.coursera.org"

MATERIALS_INCLUDES = (
    "modules,lessons,passableItemGroups,passableItemGroupChoices,passableLessonElements,"
    "items,tracks,gradePolicy,gradingParameters,embeddedContentMapping"
)
MATERIALS_FIELDS = (
    "moduleIds,onDemandCourseMaterialModules.v1(name,slug,description,timeCommitment,lessonIds,"
    "optional,learningObjectives),onDemandCourseMaterialLessons.v1(name,slug,timeCommitment,"
    "elementIds,optional,trackId),onDemandCourseMaterialItems.v2(name,originalName,slug,"
    "timeCommitment,contentSummary,isLocked,trackId,customDisplayTypenameOverride)"
)

# Coursera typeName -> (our item type, URL path segment)
KINDS = {
    "lecture": ("lecture", "lecture"),
    "supplement": ("reading", "supplement"),
    "ungradedAssignment": ("quiz", "assignment-submission"),
    "staffGraded": ("quiz", "assignment-submission"),
    "exam": ("quiz", "exam"),
    "quiz": ("quiz", "quiz"),
    "peer": ("assignment", "peer"),
    "gradedPeer": ("assignment", "peer"),
    "discussionPrompt": ("discussion", "discussionPrompt"),
    "ungradedWidget": ("other", "ungradedWidget"),
    "ungradedLti": ("other", "ungradedLti"),
    "gradedLti": ("other", "gradedLti"),
    "ungradedLab": ("lab", "ungradedLab"),
}
SKIP_KINDS = {
    "ungradedWidget": "interactive widget; no readable content via API",
    "ungradedLti": "external LTI tool",
    "gradedLti": "external LTI tool",
    "ungradedLab": "hands-on lab environment",
}

# Read-only GraphQL operations the adapter may POST. Anything else is refused.
GRAPHQL_ALLOW = {"QueryState", "AssignmentFeedback"}

_JS_FETCH = """async ({url, method, headers, body}) => {
  const r = await fetch(url, {method, headers, body, credentials: 'include'});
  return {status: r.status, url: r.url, text: await r.text()};
}"""


class AdapterError(RuntimeError):
    pass


class Coursera:
    def __init__(self, cfg: Config, ctx: BrowserContext, page: Page, guard: Guard, pacer: Pacer):
        self.cfg, self.ctx, self.page, self.guard, self.pacer = cfg, ctx, page, guard, pacer

    # --- transport -------------------------------------------------------------

    def open(self, url: str) -> None:
        self.pacer.wait()
        self.page.goto(url, wait_until="domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        self.guard.check(self.page)

    def _fetch(self, url: str, method: str = "GET", headers: dict | None = None,
               body: str | None = None) -> str:
        if method != "GET" and not url.startswith(f"{BASE}/graphql-gateway?opname="):
            raise AdapterError(f"refusing non-GET request to {url}")
        self.pacer.wait()
        r = self.page.evaluate(_JS_FETCH, {"url": url, "method": method,
                                           "headers": headers or {}, "body": body})
        self._check_status(r["status"], url, r["url"])
        return r["text"]

    def _check_status(self, status: int, url: str, final_url: str = "") -> None:
        if status == 429:
            raise StopRun(f"HTTP 429 (rate limited) on {url}")
        if status == 403:
            raise StopRun(f"HTTP 403 on {url}")
        if status == 401 or "/login" in final_url:
            raise StopRun("Coursera asked to log in again; run `notebook login`, then re-run")
        if status >= 400:
            raise AdapterError(f"HTTP {status} on {url}")
        self.guard.check(self.page)

    def get_json(self, path: str) -> dict:
        return json.loads(self._fetch(BASE + path))

    def download(self, url: str, dest: Path, paced: bool = True) -> Path:
        """Binary download through the session (shares cookies). Signed CDN URLs work too."""
        if paced:
            self.pacer.wait()
        resp = self.ctx.request.get(url, timeout=600_000)
        host = urlparse(url).hostname or ""
        if not host.endswith("coursera.org") and resp.status >= 400:
            # A third-party site refusing a file says nothing about the Coursera account.
            raise AdapterError(f"HTTP {resp.status} on {url}")
        self._check_status(resp.status, url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.body())
        return dest

    # --- course structure ------------------------------------------------------

    def materials(self, slug: str) -> dict:
        data = self.get_json(
            f"/api/onDemandCourseMaterials.v2/?q=slug&slug={quote(slug)}"
            f"&includes={MATERIALS_INCLUDES}&fields={quote(MATERIALS_FIELDS, safe='(),.')}"
            "&showLockedItems=true"
        )
        if not data.get("elements") or "onDemandCourseMaterialItems.v2" not in data.get("linked", {}):
            raise AdapterError("course materials response missing modules/items")
        return data

    def course_title(self, slug: str) -> str | None:
        try:
            data = self.get_json(f"/api/courses.v1?q=slug&slug={quote(slug)}&fields=name")
        except AdapterError:
            return None  # the title is cosmetic; never fail a run over it
        return next((e.get("name") for e in data.get("elements", []) if e.get("name")), None)

    def objectives(self, ids: list[str]) -> dict[str, str]:
        if not ids:
            return {}
        data = self.get_json(
            f"/api/onDemandLearningObjectives.v2/?ids={quote(','.join(ids))}&fields=category,description"
        )
        return {e["id"]: e.get("description", "") for e in data.get("elements", [])}

    def manifest(self, course_key: str, slug: str, program: dict) -> tuple[CourseManifest, dict]:
        mat = self.materials(slug)
        linked = mat["linked"]
        mods = {m["id"]: m for m in linked["onDemandCourseMaterialModules.v1"]}
        lessons = {lsn["id"]: lsn for lsn in linked["onDemandCourseMaterialLessons.v1"]}
        items = {i["id"]: i for i in linked["onDemandCourseMaterialItems.v2"]}
        all_obj_ids = [o for m in mods.values() for o in m.get("learningObjectives", [])]
        obj_text = self.objectives(all_obj_ids)

        modules = []
        for mn, mid in enumerate(mat["elements"][0]["moduleIds"], start=1):
            m = mods[mid]
            mod = Module(n=mn, id=mid, title=m["name"].strip(),
                         objectives=[obj_text.get(o, "") for o in m.get("learningObjectives", [])])
            item_n = 0
            for ln, lid in enumerate(m.get("lessonIds", []), start=1):
                lsn = lessons[lid]
                lesson = Lesson(n=ln, title=lsn["name"].strip())
                ids = lsn.get("itemIds") or [e.split("~", 1)[1] for e in lsn.get("elementIds", [])
                                             if e.startswith("item~")]
                for iid in ids:
                    it = items.get(iid)
                    if not it:
                        continue
                    item_n += 1
                    kind = it["contentSummary"]["typeName"]
                    our_type, segment = KINDS.get(kind, ("other", "item"))
                    url = f"{BASE}/learn/{slug}/{segment}/{iid}/{it['slug']}"
                    dur = it["contentSummary"].get("definition", {}).get("duration")
                    lesson.items.append(ManifestItem(
                        n=item_n, item_id=iid, type=our_type, coursera_kind=kind,
                        title=it["name"].strip(), slug=slugify(it["slug"]),
                        public_url=url, access_url=url,
                        duration_s=round(dur / 1000) if dur else None,
                        # Locked items 403 if requested; skip them (not marked done, so a later run retries).
                        skip_reason="locked on Coursera" if it.get("isLocked") else SKIP_KINDS.get(kind),
                    ))
                mod.lessons.append(lesson)
            modules.append(mod)

        manifest = CourseManifest(
            course_key=course_key, slug=slug, course_id=mat["elements"][0]["id"],
            title=program.get("course_title") or self.course_title(slug) or slug, program=program, modules=modules,
            discovered_at=datetime.now(timezone.utc).replace(microsecond=0),
        )
        return manifest, mat

    # --- items -----------------------------------------------------------------

    @staticmethod
    def _video_store(html: str) -> dict | None:
        i = html.find('"VideoItemStore"')
        if i < 0:
            return None
        j = html.find("{", html.find(":", i))
        store, _ = json.JSONDecoder().raw_decode(html[j:])
        return store if store.get("videoData", {}).get("sources") else None

    def lecture(self, item: ManifestItem) -> tuple[dict, str]:
        """Return (videoData, layer). Layer 1 fetches the page HTML; layer 2 navigates."""
        try:
            store = self._video_store(self._fetch(item.access_url))
            if store:
                return store["videoData"], "fetch"
        except (AdapterError, json.JSONDecodeError):
            pass
        self.open(item.access_url)
        store = self.page.evaluate(
            "() => window.App?.context?.dispatcher?.stores?.VideoItemStore ?? null")
        if store and store.get("videoData", {}).get("sources"):
            return store["videoData"], "capture"
        raise AdapterError(f"no video data for {item.item_id}")

    def lecture_assets(self, course_id: str, item_id: str) -> dict:
        return self.get_json(
            f"/api/onDemandLectureAssets.v1/{course_id}~{item_id}/?includes=openCourseAssets")

    def supplement(self, course_id: str, item: ManifestItem) -> tuple[dict, str]:
        path = (f"/api/onDemandSupplements.v1/{course_id}~{item.item_id}?includes=asset"
                "&fields=openCourseAssets.v1(typeName),openCourseAssets.v1(definition)")
        try:
            data = self.get_json(path)
            if self.reading_html(data):
                return data, "fetch"
        except (AdapterError, json.JSONDecodeError):
            pass
        # Layer 3: the rendered reading body.
        self.open(item.access_url)
        html = self.page.eval_on_selector(".cmlToHtml-content-container", "e => e.outerHTML")
        if html:
            return {"dom_html": html}, "dom"
        raise AdapterError(f"no reading content for {item.item_id}")

    @staticmethod
    def reading_html(data: dict) -> str | None:
        if "dom_html" in data:
            return data["dom_html"]
        for asset in data.get("linked", {}).get("openCourseAssets.v1", []):
            r = asset.get("definition", {}).get("renderableHtmlWithMetadata") or {}
            if r.get("renderableHtml"):
                return r["renderableHtml"]
        return None

    def quiz_state(self, course_id: str, item_id: str) -> dict:
        """Your attempts and last submission (prompts, options, chosen answers)."""
        return self._graphql("QueryState", course_id, item_id)

    def quiz_feedback(self, course_id: str, item_id: str) -> dict:
        """Per-question correctness and option feedback, as on the View feedback page."""
        return self._graphql("AssignmentFeedback", course_id, item_id)

    def _graphql(self, op: str, course_id: str, item_id: str) -> dict:
        if op not in GRAPHQL_ALLOW:
            raise AdapterError(f"GraphQL op {op} not allow-listed")
        # A copy in <data_root>/config/graphql overrides the bundled one (if Coursera changes it).
        query_file = self.cfg.path("config", "graphql", f"{op}.graphql")
        if not query_file.exists():
            query_file = PACKAGE_DIR / "graphql" / f"{op}.graphql"
        query = query_file.read_text(encoding="utf-8")
        if re.search(r"^\s*mutation\b", query, re.M):
            raise AdapterError(f"{op}.graphql contains a mutation; refusing")
        csrf = next((c["value"] for c in self.ctx.cookies(BASE) if c["name"] == "CSRF3-Token"), "")
        body = json.dumps([{"operationName": op, "variables": {"courseId": course_id, "itemId": item_id},
                            "query": query}])
        text = self._fetch(
            f"{BASE}/graphql-gateway?opname={op}", method="POST", body=body,
            headers={"content-type": "application/json", "accept": "application/json",
                     "apollographql-client-name": "ondemand", "operation-name": op,
                     "x-csrf3-token": csrf},
        )
        data = json.loads(text)
        data = data[0] if isinstance(data, list) else data
        if "errors" in data and not data.get("data"):
            raise AdapterError(f"{op} errors: {str(data['errors'])[:300]}")
        return data


def best_video_url(video_data: dict, prefer: str = "540p") -> str | None:
    by_res = video_data.get("sources", {}).get("byResolution", {})
    for res in (prefer, "360p", "720p", *by_res.keys()):
        url = by_res.get(res, {}).get("mp4VideoUrl")
        if url:
            return url
    return None


def subtitle_url(video_data: dict, lang: str = "en") -> str | None:
    path = (video_data.get("subtitlesVtt") or {}).get(lang)
    return BASE + path if path and urlparse(path).scheme == "" else path
