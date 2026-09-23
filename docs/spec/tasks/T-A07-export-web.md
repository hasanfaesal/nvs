# T-A07 — `export`: web PLY, manifest, Phase A results

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A05, T-A06 |
| Requirements | FR-A6, NFR-4 |
| May edit 06-contracts.md | no |

## Goal
`python -m pipeline export --scene <id>` writes:
- `scenes/<id>/web/scene.ply` (Gaussian order preserved);
- `scenes/<id>/web/manifest.json` (C5);
- `results/<id>/phase_a.json` (C14.1).

## Background
- gsplat's `export_splats` writes the standard PLY but **silently drops rows containing NaN/Inf**, which would shift every later index and break the invariant (C11). So we first *neutralize* bad rows (make them invisible) and then export, so nothing is dropped.
- The manifest tells the web app what to load and where to put the camera. Its `initial_view` comes from the first training camera, using the math in `pipeline/camera.py`.

## Read first
1. `docs/spec/06-contracts.md` §C5, §C11, §C14.1
2. `docs/spec/07-phase-a.md` §7
3. `pipeline/camera.py`, `pipeline/plyio.py`, `pipeline/train_3dgs.py` (`latest_step_file`)
4. Upstream: gsplat `gsplat/exporter.py::export_splats` (signature: `export_splats(means, scales, quats, opacities, sh0, shN, format="ply", save_to=None) -> bytes`)

## Files
| Action | Path |
|---|---|
| create | `pipeline/export_web.py` |
| modify | `pipeline/cli.py`: add `export` |
| create | `tests/test_export_web.py` |

## Provenance
WRAP of **`gsplat.export_splats`** + NEW glue.

## Interface
```python
def neutralize(splats: dict[str, "torch.Tensor"]) -> int: ...     # in place; returns number of bad rows
def build_manifest(scene_id: str, cfg: dict, num: int, xyz_hash: str, asset_bytes: int,
                   initial_view: dict, metrics: dict, git_sha: str) -> dict: ...
def build_phase_a(scene_id: str, metrics: dict, num: int, asset_bytes: int,
                  stage_log: list[dict], git_sha: str) -> dict: ...
def export(scene_id: str, force: bool = False) -> Path: ...
```

## Steps
1. `neutralize` (keys `means, scales, quats, opacities, sh0, shN`; N rows):
   - `bad = ~(isfinite(means).all(1) & isfinite(scales).all(1) & isfinite(quats).all(1) & isfinite(opacities) & isfinite(sh0).flatten(1).all(1) & isfinite(shN).flatten(1).all(1))`;
   - for bad rows set `means = 0`, `scales = -10`, `quats = [1,0,0,0]`, `opacities = -20`, `sh0 = 0`, `shN = 0`;
   - return `int(bad.sum())`.
2. `export`:
   1. `ckpt = torch.load(latest ckpt, map_location="cpu")["splats"]`; `n_bad = neutralize(ckpt)`.
   2. `from gsplat import export_splats` (inside the function); `export_splats(..., format="ply", save_to=str(web/"scene.ply"))`.
   3. `xyz = plyio.read_xyz(web/"scene.ply")`; assert `len(xyz) == N` and `np.allclose(xyz, means)`, else raise.
   4. Initial view:
      - `split = json.load(split.json)`; `cam = colmap_io.load_cameras(source/sparse/0)[split["train"][0]]`;
      - `pts = colmap_io.load_points(...)`;
      - `camera.initial_view(cam.R, cam.t, cam.K[1,1], cam.height, pts)`.
   5. Metrics:
      - the latest `3dgs/stats/val_step*.json` → `psnr, ssim, lpips`;
      - `lpips_net` from config; `num_test = len(split["test"])`; `step` from the file name.
   6. Write the manifest: `json.dumps(indent=1)`, the `mesh_quaternion_xyzw` constant `[1,0,0,0]`, `demo_queries` and `title` from `cfg["scenes"][scene_id]` (empty list and scene_id if missing).
   7. `phase_a.json`:
      - take the **last** `train_3dgs` line of `logs/stages.jsonl`;
      - `train_seconds`;
      - `train_peak_vram_mb = peak_vram_mb − baseline_vram_mb` (null if either is null);
      - `asset_mb`;
      - `fps_lab = null`.
   8. Print N, `n_bad`, the asset size in MB and the PSNR.
3. Skip if `manifest.json` exists and not `force`.

## Tests (`tests/test_export_web.py`, CPU torch)
- `neutralize`: 10 rows with NaN injected in rows 2 (means) and 7 (shN) → returns 2, the rows are finite afterwards, `opacities[2] == -20`, other rows untouched.
- `build_manifest(...)` has exactly the C5 top-level keys (compare with a set literal).
- `build_phase_a` with a fake stage log → `train_peak_vram_mb == peak - baseline`.

## Laptop check
```bash
pytest -q tests/test_export_web.py tests/test_imports.py
```

## Lab check
```bash
python -m pipeline export --scene ramen --force
python -c "import json; m=json.load(open('scenes/ramen/web/manifest.json')); print(m['num_gaussians'], m['metrics_3dgs'], m['initial_view'])"
cat results/ramen/phase_a.json
```
Expected: `num_gaussians` ≈ the checkpoint's N (≤ 1,000,000 after the full run); plausible metrics; the initial view has a `fov_y_deg` of about 40–70.

## Done when
- [ ] Tests pass; export works on the smoke checkpoint from T-A05

## Findings / Blockers
- Confirmed in `third_party/gsplat/gsplat/exporter.py`: `export_splats` drops any row with NaN/Inf in means/scales/quats/opacities/sh0/shN (so `neutralize` checks exactly that set), and `splat2ply_bytes` writes `x,y,z` first as little-endian float32, which `plyio.read_xyz` reads back. A laptop round-trip of the copied `splat2ply_bytes` + `read_xyz` on 50 rows with one NaN row kept all 50 rows with matching xyz.
- Confirmed in `examples/simple_trainer.py`: checkpoints hold `{"splats": state_dict}` with keys `means, scales, quats, opacities, sh0, shN`; val stats hold `psnr, ssim, lpips, num_GS, …`, file name `val_step<step>.json`. `step` is parsed from that name (e.g. 29999).
- ASSUMPTION: the manifest's `dataset` comes from `cfg["scenes"][id]["dataset"]` (`null` if the scene is missing from scenes.yaml), like `title`/`demo_queries`.
- ASSUMPTION: `asset_mb` = bytes / 2**20, rounded to 0.1. `created_utc` uses the `YYYY-MM-DDTHH:MM:SSZ` form from C5.
- ASSUMPTION: `build_phase_a` raises if `stages.jsonl` has no `train_3dgs` line (it can't report training time/VRAM otherwise).
- The `gsplat`/`torch` imports in `export()` come after the skip check, so a skipped export does not need gsplat.
- VERIFY on lab: the end-to-end run on the smoke/full checkpoint (gsplat isn't installed on the laptop).
