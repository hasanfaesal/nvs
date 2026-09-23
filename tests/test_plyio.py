"""Tests for pipeline/plyio.py: Inria layout round trip and the C11 hash."""
import numpy as np

from pipeline.plyio import read_vertex, read_xyz, write_gaussians_ply, xyz_hash


def test_write_read_round_trip(tmp_path):
    rng = np.random.default_rng(0)
    N, K = 5, 15
    means = rng.normal(size=(N, 3)).astype(np.float32)
    shN = rng.normal(size=(N, K, 3)).astype(np.float32)
    p = tmp_path / "g.ply"
    write_gaussians_ply(p, means, rng.normal(size=(N, 3)), rng.normal(size=(N, 4)),
                        rng.normal(size=N), rng.normal(size=(N, 1, 3)), shN)
    assert np.array_equal(read_xyz(p), means)
    v = read_vertex(p)
    names = list(v)
    rest = [n for n in names if n.startswith("f_rest_")]
    assert len(rest) == 45
    assert names[:6] == ["x", "y", "z", "f_dc_0", "f_dc_1", "f_dc_2"]
    assert names[-8:] == ["opacity", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]
    for c in range(3):
        for k in range(K):
            assert np.array_equal(v[f"f_rest_{c * 15 + k}"], shN[:, k, c])
    assert b"binary_little_endian" in p.read_bytes()[:100]


def test_xyz_hash_stable_and_sensitive():
    xyz = np.arange(30, dtype=np.float64).reshape(10, 3)
    h = xyz_hash(xyz)
    assert h == xyz_hash(xyz.astype(np.float32).copy())
    xyz2 = xyz.copy()
    xyz2[3, 1] += 1
    assert xyz_hash(xyz2) != h
