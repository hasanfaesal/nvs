"""Tests for pipeline/split.py with synthetic names and a fake COLMAP reader."""
import json

import numpy as np

from pipeline import colmap_io
from pipeline.colmap_io import Cam
from pipeline.split import build_split, make_split, outlier_cameras

NAMES = [f"frame_{i:05d}.jpg" for i in range(1, 21)]


def test_every_8th_is_test():
    s = make_split(NAMES, set(), 8, set())
    assert s["test"] == [NAMES[0], NAMES[8], NAMES[16]]
    assert s["train"] == [n for i, n in enumerate(NAMES) if i not in (0, 8, 16)]
    assert len(s["train"]) == 17


def test_annotated_is_test_only():
    s = make_split(NAMES, {NAMES[3], "not_a_frame.jpg"}, 8, set())
    assert NAMES[3] in s["test"] and NAMES[3] not in s["train"]
    assert s["annotated"] == [NAMES[3]]


def test_excluded_in_neither_and_indices_after_exclusion():
    s = make_split(NAMES, {NAMES[5]}, 8, {NAMES[0], NAMES[5]})
    assert NAMES[0] not in s["train"] + s["test"]
    assert NAMES[5] not in s["train"] + s["test"]
    assert s["annotated"] == []
    rest = NAMES[1:5] + NAMES[6:]
    assert s["test"] == [rest[0], rest[8], rest[16]]
    assert s["excluded"] == [NAMES[0], NAMES[5]]


def test_invariants_and_deterministic():
    args = (list(reversed(NAMES)), {NAMES[3], NAMES[9]}, 8, {NAMES[12]})
    s = make_split(*args)
    assert not set(s["train"]) & set(s["test"])
    assert set(s["annotated"]) <= set(s["test"])
    assert s["train"] == sorted(s["train"]) and s["test"] == sorted(s["test"])
    assert set(s["train"]) | set(s["test"]) == set(NAMES) - {NAMES[12]}
    assert make_split(*args) == s


def test_outlier_cameras():
    a = np.linspace(0, 2 * np.pi, 10, endpoint=False)
    centers = np.vstack([np.c_[np.cos(a), np.sin(a), np.zeros(10)], [[50, 0, 0]]])
    names = [f"c{i}" for i in range(11)]
    assert outlier_cameras(centers, names, 10.0) == {"c10"}
    assert outlier_cameras(np.zeros((3, 3)), names[:3], 10.0) == set()


def test_build_split_writes_file(tmp_path, monkeypatch):
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path))
    labels = tmp_path / "s1" / "source" / "labels"
    labels.mkdir(parents=True)
    (labels / "frame_00004.json").write_text("{}")
    a = np.linspace(0, 2 * np.pi, 20, endpoint=False)
    cams = {n: Cam(n, np.eye(3), -np.array([np.cos(x), np.sin(x), 0.0]), np.eye(3), 8, 6, "PINHOLE")
            for n, x in zip(NAMES, a)}
    cams[NAMES[19]].t = np.array([-100.0, 0, 0])
    monkeypatch.setattr(colmap_io, "load_cameras", lambda d: cams)
    out = build_split("s1")
    d = json.loads(out.read_text())
    assert d["scene_id"] == "s1" and d["every"] == 8
    assert d["annotated"] == [NAMES[3]] and d["excluded"] == [NAMES[19]]
    assert d["test"] == [NAMES[0], NAMES[3], NAMES[8], NAMES[16]]
    out.write_text("{}")
    build_split("s1")
    assert out.read_text() == "{}"  # skipped without force
    build_split("s1", force=True)
    assert json.loads(out.read_text()) == d
