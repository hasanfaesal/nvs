# T-A02 — COLMAP reader + ingest of posed datasets (LERF-OVS)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A01, T-007 |
| Requirements | FR-A1 |
| May edit 06-contracts.md | no |

## Goal
- `pipeline/colmap_io.py` reads any COLMAP model into simple arrays.
- `python -m pipeline ingest --scene <id>` copies a posed dataset (images + `sparse/0` + labels) into the canonical `scenes/<id>/source/` layout (C3).

## Background
COLMAP stores, for every registered image:
- its pose (world→camera rotation R and translation t);
- its camera (intrinsics K, width, height, model).

`pycolmap` reads it, but its API changed between versions (`cam_from_world` became a method in newer releases). `colmap_io.py` is the **only** module that touches pycolmap, so the rest of the code never cares.

LERF-OVS is already undistorted (PINHOLE), so ingest just validates and copies it.

## Read first
1. `docs/spec/06-contracts.md` §C3, §C10.1
2. `docs/spec/07-phase-a.md` §1.1
3. `docs/spec/tasks/T-007-download-lerf-ovs.md`, "Findings" section (actual folder names)

## Files
| Action | Path |
|---|---|
| create | `pipeline/colmap_io.py` |
| create | `pipeline/ingest.py` |
| modify | `pipeline/cli.py`: add subcommand `ingest` |
| modify | `configs/scenes.yaml`: only if T-007 found different paths |
| create | `tests/test_ingest.py` |

## Provenance
NEW (thin wrapper over **pycolmap**; copy logic).

## Interface
```python
# pipeline/colmap_io.py
@dataclass
class Cam:
    name: str; R: np.ndarray; t: np.ndarray; K: np.ndarray; width: int; height: int; model: str
def load_cameras(sparse_dir: Path) -> dict[str, Cam]: ...   # sorted by name; registered images only
def load_points(sparse_dir: Path) -> np.ndarray: ...        # [P,3] float64
def camera_center(cam: Cam) -> np.ndarray: ...              # -R.T @ t

# pipeline/ingest.py
def ingest_colmap(scene_id: str, src: Path, labels: Path | None = None, force: bool = False) -> Path: ...
def ingest_from_config(scene_id: str, force: bool = False) -> Path: ...   # uses cfg["scenes"][scene_id]
```
CLI: `python -m pipeline ingest --scene ID [--colmap DIR] [--labels DIR] [--force]`. With no `--colmap`, it uses `configs/scenes.yaml` (`input_type` must be `colmap` for now; T-A15 adds `video` and `images`).

## Steps
1. `colmap_io.py`. Import `pycolmap` **inside** the functions.
   ```python
   rec = pycolmap.Reconstruction(str(sparse_dir))
   for img in rec.images.values():
       if not getattr(img, "has_pose", getattr(img, "registered", True)):
           continue
       cfw = img.cam_from_world() if callable(img.cam_from_world) else img.cam_from_world
       R = np.asarray(cfw.rotation.matrix(), float); t = np.asarray(cfw.translation, float)
       cam = rec.cameras[img.camera_id]
       model = cam.model.name if hasattr(cam.model, "name") else str(cam.model)
       K = np.asarray(cam.calibration_matrix(), float)
   ```
   VERIFY on the lab that these attribute names work with the installed pycolmap, and note the version in Findings.
2. `ingest_colmap`:
   1. `sparse_src = src/"sparse"/"0"` if it exists, else `src/"sparse"`.
   2. Load the cameras. Every camera model must be `PINHOLE` or `SIMPLE_PINHOLE`, else raise `ValueError("… not undistorted; run COLMAP image_undistorter first")`.
   3. Every registered name must exist in `src/"images"`, else raise, listing the first 5 missing.
   4. If the destination `source/sparse/0` exists and not `force`, print `skip (exists)` and return.
   5. With `force`, delete `source/` first.
   6. Copy **only the registered images** to `source/images/`, and the model files (`*.bin` or `*.txt`) to `source/sparse/0/`.
   7. If `labels`, copy `*.json` to `source/labels/`.
   8. Print: scene, image count, camera model, image size, label count.
3. CLI subcommand.

## Gotchas
- Copy, don't symlink; the raw data may move.
- Don't read the label contents here (evaluation only).

## Tests (`tests/test_ingest.py`; monkeypatch `pipeline.colmap_io.load_cameras` and `PS_SCENES_DIR`)
- A tmp source with 3 small JPEGs (`cv2.imwrite`) and a `sparse/0/` holding dummy `cameras.bin`, `images.bin`, `points3D.bin` files. The fake `load_cameras` returns 2 PINHOLE cams → only those 2 images are copied; the labels are copied.
- A fake cam with model `OPENCV` → `ValueError`.
- A second call without `force` skips; with `force` it re-copies.

## Laptop check
```bash
pytest -q tests/test_ingest.py tests/test_imports.py
```

## Lab check
```bash
conda activate ps
for s in figurines ramen waldo_kitchen teatime; do python -m pipeline ingest --scene $s; done
python -c "
from pipeline.colmap_io import load_cameras, load_points
from pipeline.config import scene_dir
for s in ['figurines','ramen','waldo_kitchen','teatime']:
    c = load_cameras(scene_dir(s)/'source/sparse/0'); p = load_points(scene_dir(s)/'source/sparse/0')
    k = next(iter(c.values())); print(s, len(c), k.model, k.width, k.height, p.shape)"
```
Expected: 4 scenes with counts matching T-007's Findings, PINHOLE, ≈ 986×728, thousands of points.

## Done when
- [ ] Tests pass; the 4 scenes are ingested on the lab

## Findings / Blockers
Laptop run on 2026-09-24 (pycolmap **4.2.0** in `.venv`, real LERF-OVS data from T-007):
- The Step 1 attribute names work on 4.2.0: `img.has_pose` exists, `cam_from_world` is a **method**, `cam.model.name` = `"PINHOLE"`, `calibration_matrix()` gives pixel K.
- The Lab check, run here into a temp `PS_SCENES_DIR`, prints exactly T-007's counts: figurines 299 PINHOLE 986×728 (50517 pts, 4 labels), ramen 131 988×731 (29746, 7), waldo_kitchen 187 985×725 (17475, 5), teatime 177 988×730 (25503, 6). A second call printed `skip (exists)`. The 4 `source/` dirs take 343 MB in total.
- **VERIFY on lab:** the lab pycolmap version (`python -c "import pycolmap; print(pycolmap.__version__)"`) and that the Lab check prints the same numbers.
- `configs/scenes.yaml` was not changed: T-007's folder names match the configured paths. Its "VERIFY (T-007)" comment is now resolved but still in the file.
- `sparse/0` also holds `points3D.ply`; ingest copies only `*.bin`/`*.txt` (as Step 2.6 says), so the `.ply` is dropped.
- ASSUMPTION: `--labels` only applies together with `--colmap`; without `--colmap` the labels path comes from `configs/scenes.yaml` (`ingest_from_config` has no labels argument in the Interface).
- ASSUMPTION: missing registered images raise `FileNotFoundError` (the card says only "raise"); an empty model (0 registered images) raises `ValueError`.
