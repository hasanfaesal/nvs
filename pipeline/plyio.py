"""Gaussian PLY read/write in gsplat/Inria layout and the C11 xyz hash (NEW). See C11."""
import hashlib
from pathlib import Path

import numpy as np


def read_vertex(path: Path, fields: list[str] | None = None) -> dict[str, np.ndarray]:
    """Vertex fields of a PLY as {name: [N] array}; all fields when `fields` is None."""
    from plyfile import PlyData

    v = PlyData.read(str(path))["vertex"].data
    names = fields if fields is not None else list(v.dtype.names)
    missing = [f for f in names if f not in v.dtype.names]
    if missing:
        raise KeyError(f"{path}: vertex fields {missing} not found — check the PLY was written by gsplat export")
    return {f: np.asarray(v[f]) for f in names}


def read_xyz(path: Path) -> np.ndarray:
    """[N,3] float32 Gaussian positions."""
    v = read_vertex(path, ["x", "y", "z"])
    return np.stack([v["x"], v["y"], v["z"]], axis=1).astype(np.float32)


def xyz_hash(xyz: np.ndarray) -> str:
    """sha1 of the first 1000 positions as little-endian float32 (C11)."""
    return hashlib.sha1(np.ascontiguousarray(xyz[:1000], dtype="<f4").tobytes()).hexdigest()


def write_gaussians_ply(path: Path, means, scales, quats, opacities, sh0, shN) -> None:
    """Binary PLY: x,y,z,f_dc_0..2,f_rest_0..3K-1,opacity,scale_0..2,rot_0..3 (float32).

    means [N,3], scales [N,3] (log), quats [N,4] wxyz, opacities [N] (logit),
    sh0 [N,1,3], shN [N,K,3]. f_rest is channel-major: f_rest[c*K + k] = shN[k, c].
    """
    from plyfile import PlyData, PlyElement

    N = len(means)
    K = shN.shape[1]
    cols = [
        np.asarray(means).reshape(N, 3),
        np.asarray(sh0).reshape(N, 3),
        np.asarray(shN).transpose(0, 2, 1).reshape(N, 3 * K),
        np.asarray(opacities).reshape(N, 1),
        np.asarray(scales).reshape(N, 3),
        np.asarray(quats).reshape(N, 4),
    ]
    names = (
        ["x", "y", "z"]
        + [f"f_dc_{i}" for i in range(3)]
        + [f"f_rest_{i}" for i in range(3 * K)]
        + ["opacity"]
        + [f"scale_{i}" for i in range(3)]
        + [f"rot_{i}" for i in range(4)]
    )
    data = np.concatenate(cols, axis=1).astype("<f4")
    arr = np.empty(N, dtype=[(n, "<f4") for n in names])
    for i, n in enumerate(names):
        arr[n] = data[:, i]
    PlyData([PlyElement.describe(arr, "vertex")]).write(str(path))
