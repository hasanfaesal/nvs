"""Tests for pipeline/ingest.py with a fake COLMAP reader, frame extractor and COLMAP runner."""
import cv2
import numpy as np
import pytest

from pipeline import colmap_io, colmap_run, config, frames, ingest
from pipeline.colmap_io import Cam
from pipeline.ingest import ingest_colmap, ingest_images, ingest_video

NAMES = ["frame_00001.jpg", "frame_00002.jpg", "frame_00003.jpg"]


def _cam(name: str, model: str = "PINHOLE") -> Cam:
    return Cam(name, np.eye(3), np.zeros(3), np.eye(3), 8, 6, model)


@pytest.fixture
def src(tmp_path, monkeypatch):
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path / "scenes"))
    src = tmp_path / "raw"
    (src / "images").mkdir(parents=True)
    for n in NAMES:
        cv2.imwrite(str(src / "images" / n), np.zeros((6, 8, 3), np.uint8))
    (src / "sparse" / "0").mkdir(parents=True)
    for f in ("cameras.bin", "images.bin", "points3D.bin", "points3D.ply"):
        (src / "sparse" / "0" / f).write_bytes(b"x")
    (src / "labels").mkdir()
    (src / "labels" / "frame_00001.json").write_text("{}")
    (src / "labels" / "frame_00001.jpg").write_bytes(b"x")
    return src


def _fake(monkeypatch, cams: list[Cam]) -> None:
    monkeypatch.setattr(colmap_io, "load_cameras", lambda d: {c.name: c for c in cams})


def test_copies_registered_images_model_and_labels(src, monkeypatch, tmp_path):
    _fake(monkeypatch, [_cam(NAMES[0]), _cam(NAMES[2])])
    out = ingest_colmap("s1", src, src / "labels")
    assert out == tmp_path / "scenes" / "s1" / "source"
    assert sorted(p.name for p in (out / "images").iterdir()) == [NAMES[0], NAMES[2]]
    assert sorted(p.name for p in (out / "sparse" / "0").iterdir()) == ["cameras.bin", "images.bin", "points3D.bin"]
    assert [p.name for p in (out / "labels").iterdir()] == ["frame_00001.json"]


def test_distorted_camera_raises(src, monkeypatch):
    _fake(monkeypatch, [_cam(NAMES[0], "OPENCV")])
    with pytest.raises(ValueError, match="undistort"):
        ingest_colmap("s1", src)


def test_missing_image_raises(src, monkeypatch):
    _fake(monkeypatch, [_cam("frame_09999.jpg")])
    with pytest.raises(FileNotFoundError, match="frame_09999.jpg"):
        ingest_colmap("s1", src)


def test_skip_without_force_recopy_with_force(src, monkeypatch):
    _fake(monkeypatch, [_cam(NAMES[0])])
    out = ingest_colmap("s1", src)
    marker = out / "images" / "stale.jpg"
    marker.write_bytes(b"x")
    ingest_colmap("s1", src)
    assert marker.exists()  # skipped
    _fake(monkeypatch, [_cam(NAMES[0]), _cam(NAMES[1])])
    ingest_colmap("s1", src, force=True)
    assert sorted(p.name for p in (out / "images").iterdir()) == NAMES[:2]


def test_camera_center():
    R = np.array([[0.0, -1, 0], [1, 0, 0], [0, 0, 1]])
    C = np.array([1.0, 2, 3])
    cam = Cam("a", R, -R @ C, np.eye(3), 1, 1, "PINHOLE")
    assert np.allclose(colmap_io.camera_center(cam), C)


@pytest.fixture
def calls(tmp_path, monkeypatch):
    """Fake extract_frames/run_colmap that write the files the real ones would."""
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path / "scenes"))
    log = []

    def fake_extract(video, out_dir, cfg):
        log.append(("extract", video))
        out_dir.mkdir(parents=True)
        cv2.imwrite(str(out_dir / "frame_00001.jpg"), np.zeros((6, 8, 3), np.uint8))

    def fake_colmap(scene_id, matcher="sequential", force=False):
        src = tmp_path / "scenes" / scene_id / "source"
        log.append(("colmap", matcher, sorted(p.name for p in (src / "input").iterdir())))
        (src / "sparse" / "0").mkdir(parents=True)
        (src / "images").mkdir()
        for p in (src / "input").iterdir():
            (src / "images" / p.name).write_bytes(b"x")

    monkeypatch.setattr(frames, "extract_frames", fake_extract)
    monkeypatch.setattr(colmap_run, "run_colmap", fake_colmap)
    return log


def test_ingest_video_extracts_then_sequential_colmap(calls, src, tmp_path):
    out = ingest_video("v", tmp_path / "clip.mp4", src / "labels")
    assert calls == [("extract", tmp_path / "clip.mp4"), ("colmap", "sequential", ["frame_00001.jpg"])]
    assert [p.name for p in (out / "labels").iterdir()] == ["frame_00001.json"]
    ingest_video("v", tmp_path / "clip.mp4")
    assert len(calls) == 2  # skipped: sparse/0 exists


def test_ingest_images_renames_resizes_and_uses_exhaustive(calls, tmp_path, monkeypatch):
    photos = tmp_path / "photos"
    photos.mkdir()
    cv2.imwrite(str(photos / "b.png"), np.zeros((50, 100, 3), np.uint8))
    cv2.imwrite(str(photos / "a.jpg"), np.zeros((6, 8, 3), np.uint8))
    (photos / "notes.txt").write_text("x")
    cfg = config.load_config()
    monkeypatch.setattr(ingest, "load_config", lambda: {**cfg, "frames": {**cfg["frames"], "max_side": 20}})
    out = ingest_images("p", photos)
    assert calls == [("colmap", "exhaustive", ["frame_00001.jpg", "frame_00002.jpg"])]
    assert cv2.imread(str(out / "input" / "frame_00001.jpg")).shape == (6, 8, 3)  # a.jpg, small: kept size
    assert cv2.imread(str(out / "input" / "frame_00002.jpg")).shape == (10, 20, 3)  # b.png, long side -> 20


def test_ingest_from_config_routes_video(tmp_path, monkeypatch):
    cfg = config.load_config()
    scenes = {"mine": {"input_type": "video", "input": "data/raw/custom/mine.mp4"}}
    monkeypatch.setattr(ingest, "load_config", lambda: {**cfg, "scenes": scenes})
    seen = []
    monkeypatch.setattr(ingest, "ingest_video", lambda *a, **k: seen.append((a, k)))
    ingest.ingest_from_config("mine", force=True)
    assert seen == [(("mine", config.repo_root() / "data/raw/custom/mine.mp4", None), {"force": True})]
