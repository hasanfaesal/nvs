"""gsplat MCMC training of scenes/<id>/3dgs/ (WRAP of fork examples/simple_trainer.py). See C3, C15."""
import re
import shutil
import sys
from pathlib import Path

from pipeline.config import REPO, load_config, scene_dir
from pipeline.run_stage import run_stage


def build_command(scene_id: str, cfg: dict, max_steps: int | None = None) -> list[str]:
    g = cfg["gsplat"]
    d = scene_dir(scene_id, cfg).resolve()
    steps = max_steps or g["max_steps"]
    # TODO(figurines scale): gsplat's scene_scale (examples/datasets/colmap.py) still counts cameras that
    # split.json excludes, so figurines' outlier frame_00162 (41.7x median distance) inflates it ~20-40x and,
    # with it, means_lr and the MCMC noise. Undecided fix: extend P-GS-1 to skip excluded cameras, or pass
    # --global_scale for figurines. Until then, compare figurines' PSNR with the other scenes at T-A16.
    cmd = [sys.executable, "simple_trainer.py", "mcmc",
           "--data_dir", str(d / "source"), "--data_factor", str(g["data_factor"]),
           "--result_dir", str(d / "3dgs"),
           "--split_file", str(d / "split.json"), "--no-normalize-world-space",
           "--strategy.cap-max", str(g["cap_max"]), "--max_steps", str(steps),
           "--lpips_net", g["lpips_net"], "--save_ply", "--disable_viewer"]
    if max_steps:
        # smoke run: the default 7k/30k step lists would never fire, so eval/save/ply at the last step
        cmd += ["--eval_steps", str(steps), "--save_steps", str(steps), "--ply_steps", str(steps)]
    return cmd


def latest_step_file(folder: Path, pattern: str) -> Path | None:
    files = [(int(m.group()), p) for p in folder.glob(pattern) if (m := re.search(r"\d+", p.name))]
    return max(files)[1] if files else None


def train(scene_id: str, max_steps: int | None = None, force: bool = False) -> Path:
    cfg = load_config()
    out = scene_dir(scene_id, cfg) / "3dgs"
    ckpt = latest_step_file(out / "ckpts", "ckpt_*_rank0.pt")
    if ckpt and not force:
        print(f"[train_3dgs] {ckpt} exists, skipping (use --force to retrain)")
        return out
    split = scene_dir(scene_id, cfg) / "split.json"
    if not split.exists():
        raise FileNotFoundError(f"{split} missing — run `python -m pipeline split --scene {scene_id}` first")
    if out.exists():
        shutil.rmtree(out)  # a stale higher-step ckpt from an older run would win latest_step_file
    run_stage(scene_id, "train_3dgs", build_command(scene_id, cfg, max_steps),
              cwd=REPO / "third_party" / "gsplat" / "examples")
    return out
