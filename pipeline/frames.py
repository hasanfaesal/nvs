"""Video → sharp sequential frames with a Laplacian blur filter (NEW). See C2, C6.1 `frames`."""
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np


def sharpness(img_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    if w > 640:
        gray = cv2.resize(gray, (640, round(h * 640 / w)), interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def select_sharp(scores: list[float], keep_every: int, min_ratio: float) -> list[int]:
    kept = [i + int(np.argmax(scores[i:i + keep_every])) for i in range(0, len(scores), keep_every)]
    if not kept:
        return []
    cut = min_ratio * float(np.median([scores[i] for i in kept]))
    return [i for i in kept if scores[i] >= cut]


def extract_frames(video: Path, out_dir: Path, cfg: dict) -> list[Path]:
    """cfg is the `frames` section of configs/pipeline.yaml."""
    s = cfg["max_side"]
    scale = f"scale='if(gt(iw,ih),min({s},iw),-2)':'if(gt(iw,ih),-2,min({s},ih))'"
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-i", str(Path(video).resolve()),
             "-vf", f"fps={cfg['extract_fps']},{scale}", "-q:v", "2", str(Path(tmp) / "%05d.jpg")],
            check=True,
        )
        imgs = [cv2.imread(str(p)) for p in sorted(Path(tmp).glob("*.jpg"))]
        if not imgs:
            raise RuntimeError(f"ffmpeg extracted no frames from {video} — check the file is a readable video")
        keep = select_sharp([sharpness(im) for im in imgs], cfg["keep_every"], cfg["min_sharpness_ratio"])
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for k, i in enumerate(keep, 1):
            p = out_dir / f"frame_{k:05d}.jpg"
            cv2.imwrite(str(p), imgs[i], [cv2.IMWRITE_JPEG_QUALITY, cfg["jpeg_quality"]])
            paths.append(p)
    n_windows = -(-len(imgs) // cfg["keep_every"])
    print(f"extracted {len(imgs)}, kept {len(paths)}, dropped {n_windows - len(paths)}")
    return paths
