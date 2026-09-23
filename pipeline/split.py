"""Train/test split builder for scenes/<id>/split.json (NEW). See C4."""
import json
from pathlib import Path

import numpy as np

from pipeline import colmap_io
from pipeline.config import load_config, scene_dir

RULE = "names = sorted(images) minus excluded; test = {names[i] : i % every == 0} ∪ annotated; train = names − test"


def outlier_cameras(centers: np.ndarray, names: list[str], factor: float) -> set[str]:
    centers = np.asarray(centers, float)
    d = np.linalg.norm(centers - np.median(centers, 0), axis=1)
    med = np.median(d)
    if med == 0:
        return set()
    return {n for n, di in zip(names, d) if di > factor * med}


def make_split(names: list[str], annotated: set[str], every: int, excluded: set[str]) -> dict:
    names = sorted(n for n in names if n not in excluded)
    annotated = {n for n in names if n in annotated}
    test = {names[i] for i in range(0, len(names), every)} | annotated
    return {
        "every": every,
        "train": [n for n in names if n not in test],
        "test": sorted(test),
        "annotated": sorted(annotated),
        "excluded": sorted(excluded),
        "rule": RULE,
    }


def build_split(scene_id: str, force: bool = False) -> Path:
    cfg = load_config()
    source = scene_dir(scene_id, cfg) / "source"
    out = scene_dir(scene_id, cfg) / "split.json"
    if out.exists() and not force:
        print(f"{scene_id}: skip (exists) {out}")
        return out
    cams = colmap_io.load_cameras(source / "sparse" / "0")
    if not cams:
        raise ValueError(f"no registered images in {source / 'sparse' / '0'} — run `python -m pipeline ingest --scene {scene_id}`")
    names = sorted(cams)
    centers = np.array([colmap_io.camera_center(cams[n]) for n in names])
    excluded = outlier_cameras(centers, names, cfg["split"]["outlier_factor"])
    stems = {p.stem for p in (source / "labels").glob("*.json")}
    annotated = {n for n in names if Path(n).stem in stems}
    split = {"scene_id": scene_id, **make_split(names, annotated, cfg["split"]["every"], excluded)}
    out.write_text(json.dumps(split, indent=1))
    print(f"{scene_id}: train {len(split['train'])} / test {len(split['test'])} / "
          f"annotated {len(split['annotated'])} / excluded {len(split['excluded'])} {split['excluded']} -> {out}")
    return out
