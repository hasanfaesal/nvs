# T-A06 — Camera math (`pipeline/camera.py`) and PLY I/O (`pipeline/plyio.py`)

| Field | Value |
|---|---|
| Tier | [S] (pure math; the tests are exact) |
| Depends on | T-002 |
| Requirements | FR-A6, FR-B11 |
| May edit 06-contracts.md | no |

## Goal
Two small pure modules used everywhere:
- **camera conversions** between COLMAP/gsplat (OpenCV) and three.js (OpenGL);
- **PLY reading and writing** in gsplat/Inria layout.

Both are fully unit-tested with the C10.6 test vectors.

## Background
The #1 source of bugs in this kind of project is mixing camera conventions:
- COLMAP and gsplat cameras look down **+z** with **y down**;
- three.js cameras look down **−z** with **y up**;
- Spark shows the PLY rotated 180° about x.

Every conversion lives here, once, with tests. Nobody else re-derives it.

PLY: gsplat writes Gaussians as a PLY with fields `x,y,z,f_dc_0..2,f_rest_0..44,opacity,scale_0..2,rot_0..3` (float32). `f_rest` is **channel-major**: `f_rest[c*15 + k] = shN[k, c]`. Our writer must produce exactly that layout (the fixture scene and the tests use it).

## Read first
1. `docs/spec/06-contracts.md` §C10 (all), §C11
2. `docs/spec/07-phase-a.md` §6
3. `docs/spec/02-glossary.md` §A, §B

## Files
| Action | Path |
|---|---|
| create | `pipeline/camera.py` |
| create | `pipeline/plyio.py` |
| create | `tests/test_camera.py`, `tests/test_plyio.py` |

## Provenance
NEW. The formulas are specified in C10; `plyfile` (PIP) handles the file format.

## Interface
```python
# pipeline/camera.py   (numpy only)
S = np.diag([1.0, -1.0, -1.0])                       # PLY -> three.js world (C10.3)
def colmap_viewmat(R: np.ndarray, t: np.ndarray) -> np.ndarray: ...           # 4x4
def intrinsics(fx, fy, cx, cy, scale: float = 1.0) -> np.ndarray: ...          # 3x3
def initial_view(R, t, fy: float, height: int, points_xyz: np.ndarray) -> dict: ...   # C10.4
def threejs_to_viewmat(camera_matrix_world: list[float], mesh_matrix_world: list[float]) -> np.ndarray: ...  # C10.5
def fit_render_size(width: int, height: int, max_side: int) -> tuple[int, int, float]: ...
def fov_intrinsics(fov_y_deg: float, w: int, h: int) -> np.ndarray: ...
def pixel_to_render(u: float, v: float, s: float, w: int, h: int) -> tuple[int, int]: ...
def project(viewmat: np.ndarray, K: np.ndarray, xyz: np.ndarray) -> np.ndarray: ...   # [N,2] pixel coords
def ray_through_pixel(viewmat, K, px: int, py: int) -> tuple[np.ndarray, np.ndarray]: ...  # world origin, unit dir

# pipeline/plyio.py
def read_vertex(path: Path, fields: list[str] | None = None) -> dict[str, np.ndarray]: ...
def read_xyz(path: Path) -> np.ndarray: ...                 # [N,3] float32
def xyz_hash(xyz: np.ndarray) -> str: ...                   # C11
def write_gaussians_ply(path: Path, means, scales, quats, opacities, sh0, shN) -> None: ...
    # means [N,3], scales [N,3] (log), quats [N,4] wxyz, opacities [N] (logit), sh0 [N,1,3], shN [N,K,3]
```

## Steps
1. Implement `camera.py` exactly from C10. Notes:
   - `initial_view` returns plain lists (JSON-ready) and `fov_y_deg = degrees(2·atan(height / (2·fy)))`.
   - `threejs_to_viewmat` reshapes each 16-list to 4×4 and **transposes** (three.js is column-major).
   - `ray_through_pixel`:
     - `C_cv = inv(viewmat)`; `origin = C_cv[:3,3]`;
     - `d = C_cv[:3,:3] @ inv(K) @ [px+0.5, py+0.5, 1]`;
     - normalize d.
2. Implement `plyio.py` with `from plyfile import PlyData, PlyElement` **inside** the functions.
   - `write_gaussians_ply` builds a structured array with the field order `x,y,z,f_dc_0..2,f_rest_0..(3K−1),opacity,scale_0..2,rot_0..3`, all `<f4`;
   - `f_rest = shN.transpose(0, 2, 1).reshape(N, 3*K)`;
   - write with `PlyData([PlyElement.describe(arr, "vertex")]).write(path)` (binary little-endian is the default).

## Tests (`tests/test_camera.py`): the C10.6 vectors, exactly
1. `Mm = Mc = identity` (as 16-lists, column-major), `K = fov_intrinsics(90, 100, 100)`, `V = threejs_to_viewmat(Mc, Mm)`:
   - `project(V, K, [[0,0,-5]]) ≈ [[50, 50]]`;
   - `[[1,0,-5]]` gives u > 50;
   - `[[0,1,-5]]` gives v < 50.
2. `Mm = diag(1,−1,−1,1)`, `Mc` = translation (0,0,5) (column-major list: translation in elements 12–14):
   - `V ≈ [[1,0,0,0],[0,1,0,0],[0,0,1,5],[0,0,0,1]]`;
   - the PLY origin projects to the center;
   - `[[0,-1,0]]` gives v < center.
3. `initial_view(np.eye(3), np.array([0,0,5.]), fy=50, height=100, points_xyz=np.zeros((1,3)))`:
   - position ≈ (0,0,5), target ≈ (0,0,0), up ≈ (0,1,0), fov ≈ 90;
   - and `colmap_viewmat(np.eye(3), [0,0,5])` equals `V` from test 2 (round trip).
4. `fit_render_size(1600, 900, 800) == (800, 450, 0.5)`; `fit_render_size(640, 480, 800) == (640, 480, 1.0)`.
5. `ray_through_pixel` for test 1's camera at the center pixel (49, 49) points ≈ (0, 0, −1) in the world.

`tests/test_plyio.py`:
- write 5 random Gaussians (K=15), read them back: `x,y,z` equal, 45 `f_rest` fields, `f_rest_{c*15+k}` equals `shN[:, k, c]`;
- `xyz_hash` is stable, and changes when one coordinate changes.

## Laptop check
```bash
pytest -q tests/test_camera.py tests/test_plyio.py tests/test_imports.py
```

## Lab check
None (pure code). It's exercised by T-A07 and T-B12.

## Done when
- [x] All the vector tests pass

## Findings / Blockers
- Laptop check passes: `pytest -q tests/test_camera.py tests/test_plyio.py tests/test_imports.py`; full `pytest -q` green.
- ASSUMPTION: `threejs_to_viewmat` returns only the viewmat; render size and K come from `fit_render_size` + `fov_intrinsics`, and the clicked pixel from `pixel_to_render` (C10.5 split across the listed functions).
- ASSUMPTION: `initial_view` uses the per-axis median of `points_xyz` for `m` (C10.4 "median of sparse points3D xyz").
- Test 5 tolerance: pixel (49, 49) samples the pixel centre (49.5, 49.5), so the ray is ~0.01 off −z; the test uses `atol=0.02`.
- No blockers.
