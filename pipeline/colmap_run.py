"""COLMAP 4.x runner: frames in source/input/ → undistorted PINHOLE model in source/ (COPY+adapt). See C6, 07-phase-a.md §3."""
# Source: https://github.com/Jumpat/SegAnyGAussians @ 2d4c5d77c857c956d747e4775d3d72c4ec5dfe16, convert.py (from graphdeco-inria/gaussian-splatting)
# License: Inria Gaussian-Splatting license (non-commercial research). Changes: COLMAP 4.x option names,
#          sequential matcher, global_mapper fallback, best-model selection, run_stage logging.
import os
import shutil
from pathlib import Path

from pipeline import colmap_io
from pipeline.config import load_config, scene_dir
from pipeline.run_stage import run_stage

MIN_REGISTERED = 0.8


def build_commands(src: Path, colmap_bin: str, matcher: str, mapper: str) -> list[list[str]]:
    src = Path(src).resolve()
    db = str(src / "distorted" / "database.db")
    images = str(src / "input")
    camera_model = load_config()["colmap"]["camera_model"]
    cmds = [
        [colmap_bin, "feature_extractor", "--database_path", db, "--image_path", images,
         "--ImageReader.single_camera", "1", "--ImageReader.camera_model", camera_model,
         "--FeatureExtraction.use_gpu", "1"],
        [colmap_bin, f"{matcher}_matcher", "--database_path", db, "--FeatureMatching.use_gpu", "1"],
        [colmap_bin, mapper, "--database_path", db, "--image_path", images,
         "--output_path", str(src / "distorted" / "sparse")],
    ]
    if mapper == "mapper":
        # The default Mapper tolerance is unnecessarily large,
        # decreasing it speeds up bundle adjustment steps.
        cmds[2].append("--Mapper.ba_global_function_tolerance=0.000001")
    return cmds


def best_model(sparse_root: Path) -> Path:
    models = [d for d in sorted(Path(sparse_root).iterdir()) if d.is_dir()]
    if not models:
        raise RuntimeError(f"COLMAP wrote no model in {sparse_root} — check the colmap_mapper log "
                           "and the capture protocol (07-phase-a.md §8)")
    return max(models, key=lambda d: len(colmap_io.load_cameras(d)))


def run_colmap(scene_id: str, matcher: str = "sequential", force: bool = False) -> Path:
    cfg = load_config()
    src = scene_dir(scene_id, cfg).resolve() / "source"
    out = src / "sparse" / "0"
    if out.exists() and not force:
        print(f"[colmap] {out} exists, skipping (use force)")
        return out

    colmap_bin = os.path.expanduser(cfg["envs"]["colmap_bin"])
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    distorted = src / "distorted" / "sparse"
    for d in (distorted, src / "sparse"):  # stale sub-models would win best_model
        shutil.rmtree(d, ignore_errors=True)
    distorted.mkdir(parents=True)

    mapper = cfg["colmap"]["mapper"]
    for step, cmd in zip(("features", "matching", "mapper"),
                         build_commands(src, colmap_bin, matcher, mapper)):
        run_stage(scene_id, f"colmap_{step}", cmd, cwd=src)

    n_input = sum(1 for p in (src / "input").iterdir() if p.is_file())
    best = best_model(distorted)
    ratio = len(colmap_io.load_cameras(best)) / n_input
    if ratio < MIN_REGISTERED and mapper == "mapper":
        print(f"[colmap] only {ratio:.1%} registered with mapper, retrying with global_mapper")
        shutil.rmtree(distorted)
        distorted.mkdir()
        run_stage(scene_id, "colmap_global_mapper",
                  build_commands(src, colmap_bin, matcher, "global_mapper")[2], cwd=src)
        best = best_model(distorted)
        ratio = len(colmap_io.load_cameras(best)) / n_input
    if ratio < MIN_REGISTERED:
        raise RuntimeError(f"COLMAP registered only {ratio:.1%} of {n_input} frames (< {MIN_REGISTERED:.0%}) — "
                           "recapture following the capture protocol (07-phase-a.md §8)")

    ## Image undistortion
    ## We need to undistort our images into ideal pinhole intrinsics.
    run_stage(scene_id, "colmap_undistort",
              [colmap_bin, "image_undistorter", "--image_path", str(src / "input"), "--input_path", str(best),
               "--output_path", str(src), "--output_type", "COLMAP"], cwd=src)
    out.mkdir(parents=True, exist_ok=True)
    for f in (src / "sparse").iterdir():
        if f.name != "0":
            shutil.move(str(f), str(out / f.name))
    print(f"[colmap] registered {ratio:.1%} of {n_input} frames → {out}")
    return out
