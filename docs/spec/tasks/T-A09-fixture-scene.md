# T-A09 — Fixture scene for laptop development

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A06 |
| Requirements | FR-A11, NFR-6 |
| May edit 06-contracts.md | no |

## Goal
`python scripts/make_fixture_scene.py` creates `scenes/_fixture/`. It is a tiny synthetic scene that satisfies the contracts, so the server, the web app and the pseudo-label viewer all run on the laptop without a GPU or datasets.

## Background
The laptop can't train or render real scenes, but the whole web UI still has to be built and clicked through there. A synthetic scene of 30,000 coloured Gaussians is small enough (≈ 7 MB), the browser renders it on the laptop's iGPU, and it has exactly the file layout of a real scene (C3, C5, C7). It is never committed: `scenes/` is gitignored, and you regenerate it at will.

## Read first
1. `docs/spec/07-phase-a.md` §10
2. `docs/spec/06-contracts.md` §C3, §C5, §C7
3. `pipeline/plyio.py`

## Files
| Action | Path |
|---|---|
| create | `scripts/make_fixture_scene.py` |
| create | `tests/test_fixture.py` |

## Provenance
NEW.

## Interface
```python
def make_fixture(out: Path, n_per_cluster: int = 10_000, seed: int = 0) -> None: ...
# CLI: python scripts/make_fixture_scene.py [--out scenes/_fixture]   (default = scenes_root()/"_fixture")
```

## Steps
1. **Gaussians** (PLY/COLMAP frame, y points **down**), `rng = np.random.default_rng(seed)`:
   - red sphere: points uniformly in a ball of radius 0.5 at (−1, 0, 0), colour (0.9, 0.1, 0.1);
   - green cube: uniform in a cube of side 0.8 at (+1, 0, 0), colour (0.1, 0.8, 0.2);
   - grey floor: uniform on the plane y = +0.6, x, z ∈ [−2, 2], colour (0.5, 0.5, 0.5);
   - `sh0 = ((rgb − 0.5) / 0.28209479177387814)[:, None, :]`, `shN = zeros(N, 15, 3)`, `scales = log(0.02)`, `quats = (1,0,0,0)`, `opacities = 2.0`;
   - write with `plyio.write_gaussians_ply(out/"web/scene.ply", ...)`.
2. **`web/manifest.json`** (C5):
   - `scene_id "_fixture"`, `title "Fixture (synthetic)"`, `dataset "fixture"`;
   - `num_gaussians`, `xyz_hash` (`plyio.xyz_hash`), `asset` (file, format ply, bytes);
   - `initial_view = {position: [0, 1.5, 4], target: [0, 0, 0], up: [0, 1, 0], fov_y_deg: 50}` (three.js world);
   - `mesh_quaternion_xyzw [1,0,0,0]`;
   - `metrics_3dgs {psnr: 30.0, ssim: 0.95, lpips: 0.05, lpips_net: "alex", num_test: 0, step: 0}`;
   - `demo_queries ["red ball", "green box"]`, `git_sha "fixture"`, `created_utc` now.
3. **Frames:** `source/images/frame_0000{1..5}.jpg`, 64×48 random noise (`cv2.imwrite`). `split.json`: all 5 in train; test, annotated and excluded empty.
4. **Masks** for each variant in `sam, sam2_frame, sam2_track_k10`:
   - `variants/<v>/sam_masks/frame_0000{i}.pt` = `torch.bool [3, 12, 16]` (H//4 = 12, W//4 = 16), 3 random rectangles, saved on the CPU;
   - for `sam2_track_k10` also `track_ids/<stem>.json = {"ids": [1, 2, 3]}`;
   - a marker `variants/<v>/saga/seed0/query_index.pt = torch.save({"version": 1, "fixture": True})`, so the server lists the variant.
5. `if __name__ == "__main__":` argparse with `--out`. Print the path and the total size.

## Tests
`make_fixture(tmp_path)`:
- `read_xyz` returns 30,000 rows;
- the manifest hash equals `xyz_hash(read_xyz(...))`;
- every mask file loads (`map_location="cpu"`) as `torch.bool` with shape `[3, 12, 16]`;
- the total size is < 20 MB.

## Laptop check
```bash
pytest -q tests/test_fixture.py && python scripts/make_fixture_scene.py && du -sh scenes/_fixture
```

## Lab check
None.

## Done when
- [x] Test passes; the fixture is generated on the laptop

## Findings / Blockers
- Laptop check passes: 30,000 Gaussians, fixture 6.9 MB on disk; full `pytest -q` green. `server.app` (PS_FAKE=1) lists `_fixture` with variants `sam`, `sam2_frame`, `sam2_track_k10` (seed 0).
- ASSUMPTION: `split.json` also carries `"scene_id": "_fixture"`, `"every": 8` and `"rule"` (all C4 keys; `rule` was added after the overnight review).
- ASSUMPTION: the script prepends the repo root to `sys.path` so `python scripts/make_fixture_scene.py` can import `pipeline/` without installing the package; the test imports it as `scripts.make_fixture_scene` via pytest's `pythonpath = ["."]`.
- Each random mask rectangle is at least 2×2 pixels, so no mask is empty; the test checks this.
