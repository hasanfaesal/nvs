"""Tests for scripts/make_fixture_scene.py: counts, hash, mask shapes and size."""
import json

import torch

from pipeline.plyio import read_xyz, xyz_hash
from scripts.make_fixture_scene import make_fixture


def test_fixture(tmp_path):
    make_fixture(tmp_path)
    xyz = read_xyz(tmp_path / "web" / "scene.ply")
    assert xyz.shape == (30_000, 3)
    manifest = json.loads((tmp_path / "web" / "manifest.json").read_text())
    assert manifest["xyz_hash"] == xyz_hash(xyz)
    assert manifest["num_gaussians"] == 30_000
    masks = sorted(tmp_path.glob("variants/*/sam_masks/*.pt"))
    assert len(masks) == 15
    for p in masks:
        m = torch.load(p, map_location="cpu")
        assert m.dtype == torch.bool and m.shape == (3, 12, 16) and m.flatten(1).any(1).all()
    assert len(list(tmp_path.glob("variants/sam2_track_k10/track_ids/*.json"))) == 5
    assert sum(p.stat().st_size for p in tmp_path.rglob("*") if p.is_file()) < 20e6
