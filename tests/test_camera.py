"""Tests for pipeline/camera.py: the C10.6 test vectors."""
import numpy as np

from pipeline.camera import (
    colmap_viewmat,
    fit_render_size,
    fov_intrinsics,
    initial_view,
    pixel_to_render,
    project,
    ray_through_pixel,
    threejs_to_viewmat,
)

I16 = np.eye(4).flatten().tolist()
MESH16 = np.diag([1.0, -1.0, -1.0, 1.0]).flatten().tolist()  # diagonal: same in column-major
CAM_Z5 = I16[:12] + [0.0, 0.0, 5.0, 1.0]  # column-major: translation in elements 12-14
V_Z5 = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 5], [0, 0, 0, 1]], float)


def test_identity_mesh_camera_at_origin():
    K = fov_intrinsics(90, 100, 100)
    V = threejs_to_viewmat(I16, I16)
    assert np.allclose(project(V, K, [[0, 0, -5]]), [[50, 50]])
    assert project(V, K, [[1, 0, -5]])[0, 0] > 50
    assert project(V, K, [[0, 1, -5]])[0, 1] < 50


def test_spark_mesh_camera_at_z5():
    K = fov_intrinsics(90, 100, 100)
    V = threejs_to_viewmat(CAM_Z5, MESH16)
    assert np.allclose(V, V_Z5)
    assert np.allclose(project(V, K, [[0, 0, 0]]), [[50, 50]])
    assert project(V, K, [[0, -1, 0]])[0, 1] < 50


def test_initial_view_round_trip():
    iv = initial_view(np.eye(3), np.array([0, 0, 5.0]), fy=50, height=100, points_xyz=np.zeros((1, 3)))
    assert np.allclose(iv["position"], [0, 0, 5])
    assert np.allclose(iv["target"], [0, 0, 0])
    assert np.allclose(iv["up"], [0, 1, 0])
    assert np.isclose(iv["fov_y_deg"], 90)
    assert all(isinstance(iv[k], list) for k in ("position", "target", "up"))
    assert np.allclose(colmap_viewmat(np.eye(3), [0, 0, 5]), threejs_to_viewmat(CAM_Z5, MESH16))


def test_fit_render_size_and_pixel():
    assert fit_render_size(1600, 900, 800) == (800, 450, 0.5)
    assert fit_render_size(640, 480, 800) == (640, 480, 1.0)
    assert pixel_to_render(1599.9, -3, 0.5, 800, 450) == (799, 0)


def test_ray_through_center_pixel():
    origin, d = ray_through_pixel(threejs_to_viewmat(I16, I16), fov_intrinsics(90, 100, 100), 49, 49)
    assert np.allclose(origin, 0)
    assert np.isclose(np.linalg.norm(d), 1)
    assert np.allclose(d, [0, 0, -1], atol=0.02)
