"""Synthetic fixture scene for laptop development (NEW). See C3, C5, C7."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so `python scripts/...` finds pipeline/
from pipeline import plyio  # noqa: E402
from pipeline.config import scenes_root  # noqa: E402
from pipeline.split import RULE  # noqa: E402

SH_C0 = 0.28209479177387814
STEMS = [f"frame_{i:05d}" for i in range(1, 6)]
VARIANTS = ["sam", "sam2_frame", "sam2_track_k10"]
W, H = 64, 48


def _gaussians(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Means [3n,3] and rgb [3n,3] of the red sphere, green cube and grey floor (PLY frame, y down)."""
    d = rng.normal(size=(n, 3))
    sphere = d / np.linalg.norm(d, axis=1, keepdims=True) * 0.5 * rng.random((n, 1)) ** (1 / 3) + [-1, 0, 0]
    cube = rng.uniform(-0.4, 0.4, size=(n, 3)) + [1, 0, 0]
    floor = np.stack([rng.uniform(-2, 2, n), np.full(n, 0.6), rng.uniform(-2, 2, n)], axis=1)
    means = np.concatenate([sphere, cube, floor]).astype(np.float32)
    rgb = np.repeat([[0.9, 0.1, 0.1], [0.1, 0.8, 0.2], [0.5, 0.5, 0.5]], n, axis=0)
    return means, rgb


def make_fixture(out: Path, n_per_cluster: int = 10_000, seed: int = 0) -> None:
    import cv2
    import torch

    rng = np.random.default_rng(seed)
    (out / "web").mkdir(parents=True, exist_ok=True)

    means, rgb = _gaussians(rng, n_per_cluster)
    N = len(means)
    ply = out / "web" / "scene.ply"
    plyio.write_gaussians_ply(
        ply, means, np.full((N, 3), np.log(0.02)), np.tile([1.0, 0, 0, 0], (N, 1)),
        np.full(N, 2.0), ((rgb - 0.5) / SH_C0)[:, None, :], np.zeros((N, 15, 3)),
    )
    manifest = {
        "scene_id": "_fixture",
        "title": "Fixture (synthetic)",
        "dataset": "fixture",
        "num_gaussians": N,
        "xyz_hash": plyio.xyz_hash(plyio.read_xyz(ply)),
        "asset": {"file": "scene.ply", "format": "ply", "bytes": ply.stat().st_size},
        "initial_view": {"position": [0, 1.5, 4], "target": [0, 0, 0], "up": [0, 1, 0], "fov_y_deg": 50},
        "mesh_quaternion_xyzw": [1, 0, 0, 0],
        "metrics_3dgs": {"psnr": 30.0, "ssim": 0.95, "lpips": 0.05, "lpips_net": "alex", "num_test": 0, "step": 0},
        "demo_queries": ["red ball", "green box"],
        "git_sha": "fixture",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (out / "web" / "manifest.json").write_text(json.dumps(manifest, indent=2))

    images = out / "source" / "images"
    images.mkdir(parents=True, exist_ok=True)
    for stem in STEMS:
        cv2.imwrite(str(images / f"{stem}.jpg"), rng.integers(0, 256, (H, W, 3), dtype=np.uint8))
    split = {"scene_id": "_fixture", "rule": RULE, "every": 8, "train": [f"{s}.jpg" for s in STEMS],
             "test": [], "annotated": [], "excluded": []}
    (out / "split.json").write_text(json.dumps(split, indent=2))

    h, w = H // 4, W // 4
    for v in VARIANTS:
        vdir = out / "variants" / v
        (vdir / "sam_masks").mkdir(parents=True, exist_ok=True)
        for stem in STEMS:
            masks = torch.zeros(3, h, w, dtype=torch.bool)
            for m in masks:
                y0, x0 = rng.integers(0, h - 2), rng.integers(0, w - 2)
                m[y0:rng.integers(y0 + 2, h + 1), x0:rng.integers(x0 + 2, w + 1)] = True
            torch.save(masks, vdir / "sam_masks" / f"{stem}.pt")
            if v.startswith("sam2_track"):
                (vdir / "track_ids").mkdir(exist_ok=True)
                (vdir / "track_ids" / f"{stem}.json").write_text(json.dumps({"ids": [1, 2, 3]}))
        (vdir / "saga" / "seed0").mkdir(parents=True, exist_ok=True)
        torch.save({"version": 1, "fixture": True}, vdir / "saga" / "seed0" / "query_index.pt")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Write the synthetic fixture scene.")
    ap.add_argument("--out", type=Path, default=scenes_root() / "_fixture")
    args = ap.parse_args()
    make_fixture(args.out.resolve())
    size = sum(p.stat().st_size for p in args.out.rglob("*") if p.is_file())
    print(f"fixture scene: {args.out.resolve()} ({size / 1e6:.1f} MB)")
