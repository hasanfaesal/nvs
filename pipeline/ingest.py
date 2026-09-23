"""Ingest a posed COLMAP dataset into scenes/<id>/source/ (NEW). See C3."""
import shutil
from pathlib import Path

from pipeline import colmap_io
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

    out = scene_dir(scene_id) / "source"
    if (out / "sparse" / "0").exists() and not force:
        print(f"{scene_id}: skip (exists) {out}")
        return out
    if force and out.exists():
        shutil.rmtree(out)

    (out / "images").mkdir(parents=True)
    for name in cams:
        shutil.copy2(src / "images" / name, out / "images" / name)
    (out / "sparse" / "0").mkdir(parents=True)
    for f in sorted(sparse_src.iterdir()):
        if f.suffix in (".bin", ".txt"):
            shutil.copy2(f, out / "sparse" / "0" / f.name)
    n_labels = 0
    if labels:
        (out / "labels").mkdir()
        for f in sorted(Path(labels).glob("*.json")):
            shutil.copy2(f, out / "labels" / f.name)
            n_labels += 1

    c = next(iter(cams.values()))
    print(f"{scene_id}: {len(cams)} images, {c.model} {c.width}x{c.height}, {n_labels} labels -> {out}")
    return out


def ingest_from_config(scene_id: str, force: bool = False) -> Path:
    scenes = load_config()["scenes"]
    if scene_id not in scenes:
        raise KeyError(f"scene {scene_id!r} not in configs/scenes.yaml — add it or pass --colmap DIR")
    s = scenes[scene_id]
    if s["input_type"] != "colmap":
        raise ValueError(f"{scene_id}: input_type {s['input_type']!r} not supported yet; only 'colmap'")
    labels = repo_root() / s["labels"] if s.get("labels") else None
    return ingest_colmap(scene_id, repo_root() / s["input"], labels, force)
