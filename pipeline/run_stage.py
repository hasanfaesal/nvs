"""Subprocess launcher with wall-time and peak-VRAM logging (NEW). See C15."""
import json
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import REPO, load_config, scene_dir


def git_sha() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def vram_used_mb() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                              "--format=csv,noheader,nounits", "-i", "0"],
                             capture_output=True, text=True, timeout=10)
        return int(out.stdout.strip()) if out.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def run_stage(scene_id: str, stage: str, cmd: list[str], cwd: Path | None = None,
              variant: str | None = None, seed: int | None = None, saga: bool = False) -> dict:
    cmd = [str(c) for c in cmd]
    env = load_config()["envs"]["saga"]
    if saga and env:
        cmd = ["conda", "run", "--no-capture-output", "-n", env] + cmd

    baseline = vram_used_mb()
    peak = [baseline]
    stop = threading.Event()

    def poll() -> None:
        while not stop.wait(0.5):
            v = vram_used_mb()
            if v is not None and (peak[0] is None or v > peak[0]):
                peak[0] = v

    thread = threading.Thread(target=poll, daemon=True)
    thread.start()
    started = datetime.now(timezone.utc).isoformat()
    print(f"[{stage}] {' '.join(cmd)}")
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=cwd)
    seconds = time.time() - t0
    stop.set()
    thread.join()

    rec = {"stage": stage, "variant": variant, "seed": seed, "cmd": cmd,
           "seconds": round(seconds, 1), "peak_vram_mb": peak[0], "baseline_vram_mb": baseline,
           "returncode": proc.returncode, "started_utc": started, "git_sha": git_sha()}
    log = scene_dir(scene_id) / "logs" / "stages.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    if proc.returncode != 0:
        raise RuntimeError(f"stage {stage} failed with code {proc.returncode}: {' '.join(cmd)}")
    return rec
