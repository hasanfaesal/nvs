"""Web export: scene.ply, manifest.json, phase_a.json (WRAP of gsplat export_splats + NEW glue). See C5, C11, C14.1."""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from pipeline import camera, colmap_io, plyio
from pipeline.config import load_config, results_root, scene_dir
from pipeline.run_stage import git_sha
from pipeline.train_3dgs import latest_step_file


def neutralize(splats: dict) -> int:
    """Make NaN/Inf rows invisible in place so export_splats keeps them (C11); returns the bad-row count."""
    import torch

    bad = ~(torch.isfinite(splats["means"]).all(1) & torch.isfinite(splats["scales"]).all(1)
            & torch.isfinite(splats["quats"]).all(1) & torch.isfinite(splats["opacities"])
            & torch.isfinite(splats["sh0"]).flatten(1).all(1) & torch.isfinite(splats["shN"]).flatten(1).all(1))
    splats["means"][bad] = 0.0
    splats["scales"][bad] = -10.0
    splats["quats"][bad] = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=splats["quats"].dtype)
    splats["opacities"][bad] = -20.0
    splats["sh0"][bad] = 0.0
    splats["shN"][bad] = 0.0
    return int(bad.sum())


def build_manifest(scene_id: str, cfg: dict, num: int, xyz_hash: str, asset_bytes: int,
                   initial_view: dict, metrics: dict, git_sha: str) -> dict:
    sc = cfg["scenes"].get(scene_id, {})
    return {
        "scene_id": scene_id,
        "title": sc.get("title", scene_id),
        "dataset": sc.get("dataset"),
        "num_gaussians": num,
        "xyz_hash": xyz_hash,
        "asset": {"file": "scene.ply", "format": "ply", "bytes": asset_bytes},
        "initial_view": initial_view,
        "mesh_quaternion_xyzw": [1, 0, 0, 0],
        "metrics_3dgs": metrics,
        "demo_queries": sc.get("demo_queries") or [],
        "git_sha": git_sha,
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def build_phase_a(scene_id: str, metrics: dict, num: int, asset_bytes: int,
                  stage_log: list[dict], git_sha: str) -> dict:
    train = [r for r in stage_log if r.get("stage") == "train_3dgs"]
    if not train:
        raise ValueError(f"no train_3dgs line in logs/stages.jsonl of {scene_id} — run train3dgs first")
    last = train[-1]
    peak, base = last.get("peak_vram_mb"), last.get("baseline_vram_mb")
    return {
        "scene_id": scene_id,
        **{k: metrics[k] for k in ("psnr", "ssim", "lpips", "lpips_net", "num_test")},
        "num_gaussians": num,
        "train_seconds": last["seconds"],
        "train_peak_vram_mb": None if peak is None or base is None else peak - base,
        "asset_mb": round(asset_bytes / 2**20, 1),
        "fps_lab": None,
        "git_sha": git_sha,
    }


def export(scene_id: str, force: bool = False) -> Path:
    cfg = load_config()
    d = scene_dir(scene_id, cfg)
    web = d / "web"
    manifest_path = web / "manifest.json"
    if manifest_path.exists() and not force:
        print(f"[export] {manifest_path} exists, skipping (use --force to re-export)")
        return manifest_path

    ckpt = latest_step_file(d / "3dgs" / "ckpts", "ckpt_*_rank0.pt")
    stats = latest_step_file(d / "3dgs" / "stats", "val_step*.json")
    if ckpt is None or stats is None:
        raise FileNotFoundError(f"no checkpoint or val stats under {d / '3dgs'} — run train3dgs first")
    import torch
    from gsplat import export_splats

    splats = torch.load(ckpt, map_location="cpu")["splats"]
    n_bad = neutralize(splats)

    web.mkdir(parents=True, exist_ok=True)
    ply = web / "scene.ply"
    export_splats(splats["means"], splats["scales"], splats["quats"], splats["opacities"],
                  splats["sh0"], splats["shN"], format="ply", save_to=str(ply))
    means = splats["means"].numpy()
    xyz = plyio.read_xyz(ply)
    if len(xyz) != len(means) or not np.allclose(xyz, means):
        raise RuntimeError(f"{ply}: {len(xyz)} rows / xyz differ from checkpoint ({len(means)}) — C11 broken")

    split = json.loads((d / "split.json").read_text())
    sparse = d / "source" / "sparse" / "0"
    cam = colmap_io.load_cameras(sparse)[split["train"][0]]
    view = camera.initial_view(cam.R, cam.t, cam.K[1, 1], cam.height, colmap_io.load_points(sparse))

    s = json.loads(stats.read_text())
    metrics = {"psnr": s["psnr"], "ssim": s["ssim"], "lpips": s["lpips"],
               "lpips_net": cfg["gsplat"]["lpips_net"], "num_test": len(split["test"]),
               "step": int(stats.stem.removeprefix("val_step"))}

    sha = git_sha()
    N, asset_bytes = len(xyz), ply.stat().st_size
    manifest = build_manifest(scene_id, cfg, N, plyio.xyz_hash(xyz), asset_bytes, view, metrics, sha)
    manifest_path.write_text(json.dumps(manifest, indent=1))

    log = [json.loads(line) for line in (d / "logs" / "stages.jsonl").read_text().splitlines() if line.strip()]
    out = results_root(cfg) / scene_id / "phase_a.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_phase_a(scene_id, metrics, N, asset_bytes, log, sha), indent=1))

    print(f"[export] N={N} neutralized={n_bad} asset={asset_bytes / 2**20:.1f} MB psnr={metrics['psnr']:.2f}")
    return manifest_path
