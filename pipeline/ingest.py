"""Ingest a posed COLMAP dataset, a video or a photo folder into scenes/<id>/source/ (NEW). See C3, 07-phase-a.md §1."""
import shutil
from pathlib import Path

import cv2

from pipeline import colmap_io, colmap_run, frames
from pipeline.config import load_config, repo_root, scene_dir

UNDISTORTED = ("PINHOLE", "SIMPLE_PINHOLE")


def ingest_colmap(scene_id: str, src: Path, labels: Path | None = None, force: bool = False) -> Path:
    src = Path(src)
    sparse_src = src / "sparse" / "0" if (src / "sparse" / "0").is_dir() else src / "sparse"
    cams = colmap_io.load_cameras(sparse_src)
    if not cams:
        raise ValueError(f"no registered images in {sparse_src} — check the COLMAP model")
    bad = sorted({c.model for c in cams.values()} - set(UNDISTORTED))
    if bad:
        raise ValueError(f"{sparse_src} has camera model(s) {bad}, not undistorted; run COLMAP image_undistorter first")
    missing = [n for n in cams if not (src / "images" / n).is_file()]
    if missing:
        raise FileNotFoundError(f"{len(missing)} registered images missing from {src / 'images'}: {missing[:5]}")

    out = _fresh_source(scene_id, force)
    if out is None:
        return scene_dir(scene_id) / "source"

    (out / "images").mkdir(parents=True)
    for name in cams:
        shutil.copy2(src / "images" / name, out / "images" / name)
    (out / "sparse" / "0").mkdir(parents=True)
    for f in sorted(sparse_src.iterdir()):
        if f.suffix in (".bin", ".txt"):
            shutil.copy2(f, out / "sparse" / "0" / f.name)
    n_labels = _copy_labels(out, labels)

    c = next(iter(cams.values()))
    print(f"{scene_id}: {len(cams)} images, {c.model} {c.width}x{c.height}, {n_labels} labels -> {out}")
    return out


def _copy_labels(out: Path, labels: Path | None) -> int:
    if not labels:
        return 0
    files = sorted(Path(labels).glob("*.json"))
    (out / "labels").mkdir(exist_ok=True)
    for f in files:
        shutil.copy2(f, out / "labels" / f.name)
    return len(files)


def _fresh_source(scene_id: str, force: bool) -> Path | None:
    """Return an empty source/ to fill, or None when it is already built and not force."""
    out = scene_dir(scene_id) / "source"
    if (out / "sparse" / "0").exists() and not force:
        print(f"{scene_id}: skip (exists) {out}")
        return None
    if out.exists():  # force, or a half-built source/ from a failed run
        shutil.rmtree(out)
    return out


def _summary(scene_id: str, out: Path, n_labels: int) -> None:
    n = sum(1 for p in (out / "images").iterdir() if p.is_file())
    print(f"{scene_id}: {n} undistorted images, {n_labels} labels -> {out}")


def ingest_video(scene_id: str, video: Path, labels: Path | None = None, force: bool = False) -> Path:
    out = _fresh_source(scene_id, force)
    if out is None:
        return scene_dir(scene_id) / "source"
    frames.extract_frames(Path(video), out / "input", load_config()["frames"])
    colmap_run.run_colmap(scene_id, matcher="sequential", force=force)
    _summary(scene_id, out, _copy_labels(out, labels))
    return out


def ingest_images(scene_id: str, images: Path, labels: Path | None = None,
                  matcher: str = "exhaustive", force: bool = False) -> Path:
    out = _fresh_source(scene_id, force)
    if out is None:
        return scene_dir(scene_id) / "source"
    cfg = load_config()["frames"]
    photos = sorted(p for p in Path(images).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not photos:
        raise FileNotFoundError(f"no .jpg/.jpeg/.png photos in {images} — check the --images folder")
    (out / "input").mkdir(parents=True)
    for k, p in enumerate(photos, 1):
        img = cv2.imread(str(p))  # applies EXIF orientation
        if img is None:
            raise ValueError(f"cannot read {p} — remove it or re-export the photo")
        h, w = img.shape[:2]
        if max(h, w) > cfg["max_side"]:
            f = cfg["max_side"] / max(h, w)
            img = cv2.resize(img, (round(w * f), round(h * f)), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(out / "input" / f"frame_{k:05d}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, cfg["jpeg_quality"]])
    colmap_run.run_colmap(scene_id, matcher=matcher, force=force)
    _summary(scene_id, out, _copy_labels(out, labels))
    return out


def ingest_from_config(scene_id: str, force: bool = False) -> Path:
    scenes = load_config()["scenes"]
    if scene_id not in scenes:
        raise KeyError(f"scene {scene_id!r} not in configs/scenes.yaml — add it or pass --colmap DIR")
    s = scenes[scene_id]
    ingest = {"colmap": ingest_colmap, "video": ingest_video, "images": ingest_images}.get(s["input_type"])
    if ingest is None:
        raise ValueError(f"{scene_id}: input_type {s['input_type']!r} must be colmap, video or images — fix configs/scenes.yaml")
    labels = repo_root() / s["labels"] if s.get("labels") else None
    return ingest(scene_id, repo_root() / s["input"], labels, force=force)
