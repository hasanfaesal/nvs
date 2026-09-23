# T-B02 — `saga-import`: give SAGA the gsplat scene

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A07, T-B01 |
| Requirements | FR-B2 |
| May edit 06-contracts.md | no |

## Goal
`python -m pipeline saga-import --scene <id>` creates `scenes/<id>/saga_scene/point_cloud/iteration_30000/scene_point_cloud.ply`, the RGB Gaussians SAGA will attach features to. A helper builds SAGA's `cfg_args` text (C8) for the variant builder.

## Background
SAGA normally trains its own RGB model (`train_scene.py`). We skip that and reuse our better gsplat model:
- gsplat's exported PLY already uses the same attribute names SAGA reads (`x,y,z,f_dc_*,f_rest_*,opacity,scale_*,rot_*`), so importing is just a **copy** under the file name SAGA looks for;
- SAGA finds the model through `cfg_args`, a one-line Python `Namespace(...)` text that it `eval()`s, so the fields and their spelling must be exact (C8).

## Read first
1. `docs/spec/06-contracts.md` §C3, §C8, §C11
2. `docs/spec/08-phase-b.md` §2.1
3. `pipeline/plyio.py`, `pipeline/config.py`

## Files
| Action | Path |
|---|---|
| create | `pipeline/saga_import.py` |
| modify | `pipeline/cli.py`: add `saga-import` |
| create | `tests/test_saga_import.py` |

## Provenance
NEW (nothing upstream converts gsplat → SAGA).

## Interface
```python
def cfg_args_text(model_path: Path, source_path: Path, feature_dim: int = 32) -> str: ...   # exactly C8, absolute paths
def import_scene(scene_id: str, force: bool = False) -> Path: ...                            # returns the PLY path
```

## Steps
1. `cfg_args_text` returns exactly:
   `Namespace(data_device='cuda', eval=False, images='images', model_path='<abs>', resolution=-1, sh_degree=3, source_path='<abs>', white_background=False, feature_dim=32, allow_principle_point_shift=False, need_features=False, need_masks=False)`
   Use `Path.resolve()` for both paths.
2. `import_scene`:
   1. `dst = scene_dir/"saga_scene/point_cloud/iteration_30000/scene_point_cloud.ply"`; skip if it exists and not `force`.
   2. `shutil.copy2(web/scene.ply, dst)` (a copy, not a symlink).
   3. Check: `plyio.read_vertex(dst)` has exactly 45 `f_rest_*` fields, else raise `ValueError("SAGA needs SH degree 3 (45 f_rest)")`.
   4. `xyz_hash` equals the manifest's, else raise.
   5. Print the path, N and the hash.

## Tests
- `cfg_args_text(Path("/a/m"), Path("/a/s"))` passes `eval(text, {"Namespace": argparse.Namespace})`, and the result has every C8 field with the right values.
- `import_scene` on a tmp scene (the fixture writer, or `plyio.write_gaussians_ply` + a minimal manifest) creates the file with identical bytes.
- A PLY with SH degree 1 (9 `f_rest`) raises `ValueError`.

## Laptop check
```bash
pytest -q tests/test_saga_import.py tests/test_imports.py
```

## Lab check
```bash
python -m pipeline saga-import --scene ramen
python - <<'EOF'
import sys, numpy as np; sys.path.insert(0, "third_party/SegAnyGAussians")
from scene.gaussian_model import GaussianModel          # VERIFY the constructor signature
from pipeline.plyio import read_xyz
g = GaussianModel(3); g.load_ply("scenes/ramen/saga_scene/point_cloud/iteration_30000/scene_point_cloud.ply")
print(g.get_xyz.shape, np.allclose(g.get_xyz.detach().cpu().numpy(), read_xyz("scenes/ramen/web/scene.ply")))
EOF
```
Expected: SAGA loads the file; the shape is `[N, 3]`; `True`.

## Done when
- [ ] Tests pass; SAGA loads the imported PLY on the lab

## Findings / Blockers
