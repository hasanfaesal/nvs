"""Camera conventions: COLMAP/gsplat (OpenCV) <-> three.js (OpenGL) (NEW). See C10."""
import math

import numpy as np

S = np.diag([1.0, -1.0, -1.0])  # PLY -> three.js world (C10.3)
FLIP_YZ = np.diag([1.0, -1.0, -1.0, 1.0])  # OpenGL <-> OpenCV camera axes


def colmap_viewmat(R: np.ndarray, t: np.ndarray) -> np.ndarray:
    """4x4 world->camera [[R, t], [0, 0, 0, 1]] (C10.2)."""
    V = np.eye(4)
    V[:3, :3] = R
    V[:3, 3] = t
    return V


def intrinsics(fx: float, fy: float, cx: float, cy: float, scale: float = 1.0) -> np.ndarray:
    """3x3 K; all four params scaled by `scale` when rendering at scale * size (C10.2)."""
    return np.array([[fx * scale, 0.0, cx * scale], [0.0, fy * scale, cy * scale], [0.0, 0.0, 1.0]])


def initial_view(R: np.ndarray, t: np.ndarray, fy: float, height: int, points_xyz: np.ndarray) -> dict:
    """Manifest initial_view from a COLMAP camera, as JSON-ready lists (C10.4)."""
    R = np.asarray(R, float)
    t = np.asarray(t, float)
    C = -R.T @ t
    fwd = R.T @ np.array([0.0, 0.0, 1.0])
    up = R.T @ np.array([0.0, -1.0, 0.0])
    m = np.median(np.asarray(points_xyz, float), axis=0)
    d = max(0.1, float(np.dot(m - C, fwd)))
    return {
        "position": (S @ C).tolist(),
        "target": (S @ (C + d * fwd)).tolist(),
        "up": (S @ up).tolist(),
        "fov_y_deg": math.degrees(2 * math.atan(height / (2 * fy))),
    }


def threejs_to_viewmat(camera_matrix_world: list[float], mesh_matrix_world: list[float]) -> np.ndarray:
    """gsplat world->camera viewmat from three.js column-major matrixWorld lists (C10.5)."""
    Mc = np.array(camera_matrix_world, float).reshape(4, 4).T
    Mm = np.array(mesh_matrix_world, float).reshape(4, 4).T
    C_cv = np.linalg.inv(Mm) @ Mc @ FLIP_YZ
    return np.linalg.inv(C_cv)


def fit_render_size(width: int, height: int, max_side: int) -> tuple[int, int, float]:
    """(w, h, s): shrink so the longer side is <= max_side, never upscale (C10.5)."""
    s = min(1.0, max_side / max(width, height))
    return round(width * s), round(height * s), s


def fov_intrinsics(fov_y_deg: float, w: int, h: int) -> np.ndarray:
    """K from a vertical FOV, square pixels, centred principal point (C10.5)."""
    fy = 0.5 * h / math.tan(0.5 * math.radians(fov_y_deg))
    return intrinsics(fy, fy, w / 2, h / 2)


def pixel_to_render(u: float, v: float, s: float, w: int, h: int) -> tuple[int, int]:
    """CSS pixel (u, v) -> clamped integer pixel at the render size (C10.5)."""
    return min(w - 1, max(0, int(u * s))), min(h - 1, max(0, int(v * s)))


def project(viewmat: np.ndarray, K: np.ndarray, xyz: np.ndarray) -> np.ndarray:
    """[N,3] world points -> [N,2] pixel coords (no clipping)."""
    xyz = np.atleast_2d(np.asarray(xyz, float))
    cam = xyz @ viewmat[:3, :3].T + viewmat[:3, 3]
    uvw = cam @ K.T
    return uvw[:, :2] / uvw[:, 2:3]


def ray_through_pixel(viewmat: np.ndarray, K: np.ndarray, px: int, py: int) -> tuple[np.ndarray, np.ndarray]:
    """World-space origin and unit direction of the ray through pixel centre (px, py)."""
    C_cv = np.linalg.inv(viewmat)
    d = C_cv[:3, :3] @ np.linalg.inv(K) @ np.array([px + 0.5, py + 0.5, 1.0])
    return C_cv[:3, 3], d / np.linalg.norm(d)
