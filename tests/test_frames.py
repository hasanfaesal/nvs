import shutil

import cv2
import numpy as np
import pytest

from pipeline.frames import extract_frames, select_sharp, sharpness


def test_select_sharp_windows_ties_and_blur_cut():
    assert select_sharp([1, 5, 2, 2, 9, 1, 0.1, 0.2], keep_every=2, min_ratio=0.3) == [1, 2, 4]


def test_sharpness_drops_with_blur():
    img = np.random.default_rng(0).integers(0, 256, (240, 320, 3), dtype=np.uint8)
    assert sharpness(img) > sharpness(cv2.GaussianBlur(img, (15, 15), 5))


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_extract_frames_end_to_end(tmp_path):
    video = tmp_path / "v.mp4"
    tex = np.random.default_rng(0).integers(0, 256, (240, 400, 3), dtype=np.uint8)
    w = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
    for f in range(30):
        frame = np.ascontiguousarray(tex[:, f * 2:f * 2 + 320])
        w.write(cv2.GaussianBlur(frame, (15, 15), 5) if f % 4 == 0 else frame)
    w.release()

    cfg = {"extract_fps": 6, "keep_every": 2, "min_sharpness_ratio": 0.3, "max_side": 200, "jpeg_quality": 95}
    paths = extract_frames(video, tmp_path / "out", cfg)
    assert len(paths) >= 5
    assert [p.name for p in paths] == [f"frame_{k:05d}.jpg" for k in range(1, len(paths) + 1)]
    for p in paths:
        assert max(cv2.imread(str(p)).shape[:2]) <= 200
