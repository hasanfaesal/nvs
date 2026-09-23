"""COLMAP model reader, the only module that touches pycolmap (NEW). See C10.1."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Cam:
    name: str
    R: np.ndarray  # [3,3] world->camera rotation
    t: np.ndarray  # [3] world->camera translation
    K: np.ndarray  # [3,3] pixels
    width: int
    height: int
    model: str


def _reconstruction(sparse_dir: Path):
    import pycolmap  # imported here: pycolmap is heavy and version-sensitive

    return pycolmap.Reconstruction(str(sparse_dir))


def load_cameras(sparse_dir: Path) -> dict[str, Cam]:
    """Registered images only, sorted by name."""
    rec = _reconstruction(sparse_dir)
    cams = {}
    for img in rec.images.values():
        if not getattr(img, "has_pose", getattr(img, "registered", True)):
            continue
        # cam_from_world is a method in pycolmap >= 3.12 and a property before that
        cfw = img.cam_from_world() if callable(img.cam_from_world) else img.cam_from_world
        cam = rec.cameras[img.camera_id]
        cams[img.name] = Cam(
            name=img.name,
            R=np.asarray(cfw.rotation.matrix(), float),
            t=np.asarray(cfw.translation, float),
            K=np.asarray(cam.calibration_matrix(), float),
            width=int(cam.width),
            height=int(cam.height),
            model=cam.model.name if hasattr(cam.model, "name") else str(cam.model),
        )
    return dict(sorted(cams.items()))


def load_points(sparse_dir: Path) -> np.ndarray:
    """[P,3] float64 sparse point positions."""
    rec = _reconstruction(sparse_dir)
    return np.array([p.xyz for p in rec.points3D.values()], float).reshape(-1, 3)


def camera_center(cam: Cam) -> np.ndarray:
    return -cam.R.T @ cam.t
