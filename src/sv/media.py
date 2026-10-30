"""`sv media`: slide frames from lecture videos, then delete the video.

Per lecture: PySceneDetect finds visual cuts -> one frame per scene (plus a frame
every 45 s through long static scenes) -> perceptual-hash dedupe -> a numbered
contact sheet the note generator picks informative frames from.

Frames and the contact sheet go into the raw cache (they can't be regenerated
once the video is gone). The normalized item gets them as assets.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import imagehash
from PIL import Image, ImageDraw, ImageFont

from sv.config import Config
from sv.models import NormItem
from sv.state import State, load_manifest, write_json

MAX_FRAMES = 24
PHASH_DISTANCE = 6
STATIC_STEP_S = 45.0
THUMB = (320, 180)
COLS = 4


def scene_times(video: Path, duration: float) -> list[float]:
    from scenedetect import ContentDetector, detect

    scenes = detect(str(video), ContentDetector(threshold=27.0), show_progress=False)
    spans = [(s.get_seconds(), e.get_seconds()) for s, e in scenes] or [(0.0, duration)]
    times = []
    for start, end in spans:
        # Each scene gets a frame once it settles and one just before it ends (when
        # slide bullets that animate in are all visible); long static scenes also get a
        # sample every 45 s. Dedupe drops the repeats.
        times.append(round(start + min(1.0, (end - start) / 4), 2))
        t = start + STATIC_STEP_S
        while t < end - STATIC_STEP_S / 2:
            times.append(round(t, 2))
            t += STATIC_STEP_S
        times.append(round(end - min(1.0, (end - start) / 2), 2))
    return sorted(set(times))


def grab(video: Path, t: float, dest: Path) -> None:
    # A seek at the very end can land past the last decodable frame; skipping one
    # candidate is harmless, so failures are not fatal (the caller checks dest exists).
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{t:.2f}", "-i", str(video),
                    "-frames:v", "1", "-q:v", "3", str(dest)], check=False)


def dedupe(frames: list[tuple[float, Path]]) -> list[tuple[float, Path]]:
    kept: list[tuple[float, Path, imagehash.ImageHash]] = []
    for t, path in frames:
        with Image.open(path) as img:
            dark = max(img.convert("L").getextrema()) < 30  # black/fade frame
            h = imagehash.phash(img)
        if dark:
            path.unlink()
            continue
        if all(h - kh > PHASH_DISTANCE for _, _, kh in kept):
            kept.append((t, path, h))
        else:
            path.unlink()
    if len(kept) > MAX_FRAMES:  # keep an even spread
        step = len(kept) / MAX_FRAMES
        keep_idx = {int(i * step) for i in range(MAX_FRAMES)}
        for i, (_, path, _) in enumerate(kept):
            if i not in keep_idx:
                path.unlink()
        kept = [k for i, k in enumerate(kept) if i in keep_idx]
    return [(t, p) for t, p, _ in kept]


def contact_sheet(frames: list[tuple[float, Path]], dest: Path) -> None:
    rows = (len(frames) + COLS - 1) // COLS
    label_h = 22
    sheet = Image.new("RGB", (COLS * THUMB[0], rows * (THUMB[1] + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    for n, (t, path) in enumerate(frames):
        x, y = (n % COLS) * THUMB[0], (n // COLS) * (THUMB[1] + label_h)
        with Image.open(path) as img:
            sheet.paste(img.convert("RGB").resize(THUMB), (x, y + label_h))
        draw.text((x + 4, y + 2), f"#{n + 1}  {int(t // 60):02d}:{int(t % 60):02d}", fill="black", font=font)
    sheet.save(dest, quality=85)


def process(cfg: Config, course_key: str, item_id: str, raw_dir: Path, duration: float) -> list[dict]:
    video = cfg.path("media", course_key, item_id, "video.mp4")
    out = raw_dir / "frames"
    out.mkdir(exist_ok=True)
    grabbed = []
    for n, t in enumerate(scene_times(video, duration), start=1):
        dest = out / f"c{n:03d}.jpg"
        grab(video, t, dest)
        if dest.exists():
            grabbed.append((t, dest))
    kept = dedupe(grabbed)
    frames = []
    for n, (t, path) in enumerate(kept, start=1):
        final = out / f"f{n:02d}.jpg"
        path.rename(final)
        frames.append({"n": n, "t": t, "file": f"frames/{final.name}"})
    if frames:
        contact_sheet([(f["t"], raw_dir / f["file"]) for f in frames], raw_dir / "contact-sheet.jpg")
    write_json(raw_dir / "frames.json", frames)
    return frames


def run(cfg: Config, course_key: str, modules: list[int], keep_video: bool = False, echo=print) -> None:
    manifest = load_manifest(cfg, course_key)
    state = State(cfg, course_key)
    for mod in manifest.modules:
        if mod.n not in modules:
            continue
        for it in (i for lsn in mod.lessons for i in lsn.items if i.type == "lecture"):
            sid = f"{course_key}.{it.item_id}"
            st = state.get(sid)
            if not st.fetched.detail.get("dir"):
                continue  # not fetched (locked or skipped)
            raw_dir = cfg.data_root / st.fetched.detail["dir"]
            video = cfg.path("media", course_key, it.item_id, "video.mp4")
            if not (raw_dir / "frames.json").exists():
                if not video.exists():
                    echo(f"  {it.item_id}: no video and no frames; flagged")
                    continue
                frames = process(cfg, course_key, it.item_id, raw_dir, float(it.duration_s or 0))
                echo(f"  {it.item_id}: {len(frames)} frames  {it.title}")
            if video.exists() and not keep_video:
                video.unlink()
                video.parent.rmdir()
            _attach(cfg, course_key, it.item_id, raw_dir)


def _attach(cfg: Config, course_key: str, item_id: str, raw_dir: Path) -> None:
    """Add frame and contact-sheet assets to the normalized item."""
    from sv.normalize import frame_assets

    norm_path = cfg.path("norm", course_key, f"{item_id}.json")
    item = NormItem.model_validate_json(norm_path.read_text(encoding="utf-8"))
    item.assets = [a for a in item.assets if a.kind not in ("frame", "contact-sheet")]
    item.assets.extend(frame_assets(cfg, raw_dir))
    write_json(norm_path, item.model_dump(mode="json"))
