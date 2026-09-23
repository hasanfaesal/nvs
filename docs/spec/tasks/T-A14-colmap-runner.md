# T-A14 — COLMAP runner (adapted from SAGA/Inria `convert.py`)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A01, T-A02, T-004 |
| Requirements | FR-A2, FR-A3 |
| May edit 06-contracts.md | no |

## Goal
`pipeline/colmap_run.py` turns a folder of frames (`source/input/`) into undistorted images (`source/images/`) and a PINHOLE model (`source/sparse/0/`) using COLMAP 4.x, choosing the matcher by input type and falling back to the global mapper.

## Background
We **copy** the proven 4-step recipe from 3DGS's `convert.py` (vendored in SAGA):
1. extract features;
2. match them;
3. build the model (mapper);
4. undistort (so everything downstream sees simple PINHOLE cameras).

COLMAP 4.x renamed the GPU options (`FeatureExtraction.use_gpu`, `FeatureMatching.use_gpu`) and includes GLOMAP's fast `global_mapper`.
- For **video**, *sequential* matching (neighbouring frames) is fast and right.
- For **unordered photos**, use *exhaustive* matching.

COLMAP runs headless in WSL, so set `QT_QPA_PLATFORM=offscreen`.

## Read first
1. `docs/spec/07-phase-a.md` §3
2. `third_party/SegAnyGAussians/convert.py` (the COPY source)
3. `pipeline/run_stage.py`, `pipeline/colmap_io.py`
4. COLMAP CLI docs: https://colmap.github.io/cli.html

## Files
| Action | Path |
|---|---|
| create | `pipeline/colmap_run.py` |
| create | `tests/test_colmap_run.py` |

## Provenance
COPY + adapt of SAGA `convert.py` (from Inria 3DGS). Header:
```python
# Source: https://github.com/Jumpat/SegAnyGAussians @ <sha>, convert.py (from graphdeco-inria/gaussian-splatting)
# License: Inria Gaussian-Splatting license (non-commercial research). Changes: COLMAP 4.x option names,
#          sequential matcher, global_mapper fallback, best-model selection, run_stage logging.
```

## Interface
```python
def build_commands(src: Path, colmap_bin: str, matcher: str, mapper: str) -> list[list[str]]: ...
def best_model(sparse_root: Path) -> Path: ...                # sub-model with most registered images (colmap_io)
def run_colmap(scene_id: str, matcher: str = "sequential", force: bool = False) -> Path: ...
```

## Steps
1. `build_commands` returns, in order (S = `scene_dir/source`, all paths absolute):
   ```text
   [bin, feature_extractor, --database_path, S/distorted/database.db, --image_path, S/input,
         --ImageReader.single_camera, 1, --ImageReader.camera_model, OPENCV, --FeatureExtraction.use_gpu, 1]
   [bin, sequential_matcher | exhaustive_matcher, --database_path, S/distorted/database.db, --FeatureMatching.use_gpu, 1]
   [bin, mapper | global_mapper, --database_path, …, --image_path, S/input, --output_path, S/distorted/sparse]
   ```
   Add `--Mapper.ba_global_function_tolerance=0.000001` only for `mapper`. The undistorter command is built after `best_model` is known:
   `[bin, image_undistorter, --image_path, S/input, --input_path, <best>, --output_path, S, --output_type, COLMAP]`
2. `run_colmap`:
   1. `bin = os.path.expanduser(cfg["envs"]["colmap_bin"])`.
   2. Set `os.environ["QT_QPA_PLATFORM"] = "offscreen"`, and create `S/distorted/sparse`.
   3. Run the 3 commands through `run_stage(scene_id, "colmap_<step>", cmd)`.
   4. `best = best_model(S/distorted/sparse)`; compute `ratio = registered / len(input images)`.
   5. If `ratio < 0.8` and the mapper was `mapper`, delete `S/distorted/sparse/*` and re-run the mapper step with `global_mapper`, then recompute. If still < 0.8, raise `RuntimeError` with the ratio and a pointer to the capture protocol (`07-phase-a.md` §8).
   6. Run `image_undistorter`, then move `S/sparse/*.bin` into `S/sparse/0/`. This is copied from `convert.py`'s final loop.
   7. Print the registered ratio.
3. Skip if `S/sparse/0` exists and not `force`.

## Tests (pure)
- `build_commands(tmp, "colmap", "sequential", "mapper")` → 3 commands. The first contains `--FeatureExtraction.use_gpu` and `OPENCV`, the second is `sequential_matcher`, the third contains `--Mapper.ba_global_function_tolerance=0.000001`.
- With `"exhaustive", "global_mapper"` → `exhaustive_matcher`, `global_mapper`, and no Mapper tolerance flag.
- `best_model` with `colmap_io.load_cameras` monkeypatched to return 5 cams for `0/` and 9 for `1/` → returns `1/`.

## Laptop check
```bash
pytest -q tests/test_colmap_run.py tests/test_imports.py
```

## Lab check (uses LERF images as a known-good input)
```bash
mkdir -p scenes/colmap_test/source/input && cp data/raw/lerf_ovs/ramen/images/*.jpg scenes/colmap_test/source/input/
python -c "from pipeline.colmap_run import run_colmap; run_colmap('colmap_test', matcher='sequential')"
python -c "
import sys; sys.path.insert(0, 'third_party/SegAnyGAussians')
from scene.colmap_loader import read_extrinsics_binary, read_intrinsics_binary
print(len(read_extrinsics_binary('scenes/colmap_test/source/sparse/0/images.bin')), 'images readable by SAGA loader')"
```
Expected: ≥ 95% registered; SAGA's loader reads the COLMAP 4.2 output. If SAGA's loader fails on the format, record it in Findings and pin `colmap=3.11` in the `colmap` env (`setup_lab.sh`). Then `rm -rf scenes/colmap_test`.

## Done when
- [ ] Tests pass; the lab run registers ≥ 95% and SAGA reads the model

## Findings / Blockers
