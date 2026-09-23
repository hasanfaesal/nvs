"""Tests for pipeline/ingest.py with a fake COLMAP reader."""
import cv2
import numpy as np
import pytest

from pipeline import colmap_io
from pipeline.colmap_io import Cam
from pipeline.ingest import ingest_colmap

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
