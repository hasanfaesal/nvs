# T-E05 — Mask reprojection consistency (MRC)

| Field | Value |
|---|---|
| Tier | **[M]** (multi-view geometry; get the conventions right) |
| Depends on | T-B10, T-B09 |
| Requirements | FR-E5 |
| May edit 06-contracts.md | no |

## Goal
`python -m evaluation.mrc --scene <id> --variant <v>` measures how consistently a variant's **pseudo-labels** segment the same regions across neighbouring training views. It writes `results/<scene>/<variant>/mrc.json` (C14.4).

## Background
This is our direct measure of "multi-view consistency" (hypothesis H1), computed on the masks *before* SAGA trains.
- Take a mask in frame i.
- Use the 3DGS depth to lift its pixels to 3D.
- Project them into frame j (with an occlusion test). That gives a *warped mask*.
- If the labels are consistent, some mask in frame j should overlap it well.

Do this for all masks and neighbouring frame pairs (distance 1 and 3), in both directions, and average the best-match IoUs. The **visible region** `V_ij` restricts the IoU to the part of frame j that frame i can actually see, so masks aren't punished for content outside that view.

## Read first
1. `docs/spec/09-experiments-and-evaluation.md` §5.4 (the full algorithm and constants)
2. `docs/spec/06-contracts.md` §C7, §C10.1–§C10.2, §C14.4
3. `pipeline/render.py` (`render_depth`), `pipeline/colmap_io.py`, `pipeline/camera.py` (`intrinsics`)

## Files
| Action | Path |
|---|---|
| create | `evaluation/mrc.py` |
| create | `tests/test_mrc.py` |

## Provenance
NEW (no upstream implementation exists).

## Interface
```python
def warp(depth_i, valid_i, K_i, R_i, t_i, depth_j, valid_j, K_j, R_j, t_j, rel_tol: float = 0.05) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # returns (src_flat_idx, dst_u, dst_v) for pixels of i with a visible correspondence in j
def close3(mask: np.ndarray) -> np.ndarray: ...     # 3x3 morphological close
def pair_best_ious(masks_i, masks_j, valid_i, src_idx, du, dv, h, w, min_area: int = 20, min_visible: float = 0.5) -> list[float]: ...
def mrc_for_variant(scene_id: str, variant: str, force: bool = False) -> Path: ...
```

## Steps
1. **`warp`** (vectorized numpy):
   - for the pixels `(u, v)` with `valid_i`: `X = D·K_i⁻¹[u+0.5, v+0.5, 1]`; `Xw = R_iᵀ(X − t_i)`; `Xj = R_j Xw + t_j`;
   - project: `z = Xj[2]`, `(u', v') = (K_j Xj / z)[:2]`;
   - keep `z > 0`, in bounds, and `valid_j[iv, iu]`, where `iu = floor(u')`, `iv = floor(v')`;
   - keep the occlusion test `|z − D_j[iv, iu]| < rel_tol · D_j[iv, iu]`.
2. **`pair_best_ious`:**
   - `V = close3(scatter(du, dv))`;
   - for each mask m of i with area ≥ `min_area`:
     - `src` = m ∧ valid_i; ρ = (visible src) / |src|; skip if ρ < `min_visible`;
     - `W = close3(scatter of the visible src targets)`;
   - best IoU against every mask n of j, restricted to V: `|W∧n∧V| / |(W∨n)∧V|`;
   - vectorize with a matrix product (torch if CUDA is available, else numpy) on the V pixels only;
   - 0 if j has no masks.
3. **`mrc_for_variant`:**
   - Gaussians from `web/scene.ply`; train frames in order = `variant/images` sorted;
   - per frame: `(D, A)` from `render_depth` at `(W//4, H//4)` with K scaled by 1/4, `valid = A > 0.5`, masks from `sam_masks` (`map_location="cpu"`);
   - pairs with `d ∈ {1, 3}`, both directions;
   - write `n_pairs_d1`, `n_pairs_d3`, `mrc_d1`, `mrc_d3`, `mrc = mean(mrc_d1, mrc_d3)`, `masks_per_frame`, `skipped_fraction`, `git_sha`;
   - skip-if-done.
4. `__main__` argparse `--scene --variant --force`.

## Tests (`tests/test_mrc.py`: a synthetic plane, CPU)
Setup:
- 64×64 images, `K = [[50,0,32],[0,50,32],[0,0,1]]`;
- camera i: `R = I, t = 0`; camera j: `R = I, t = (−0.5, 0, 0)` (its center is at x = +0.5);
- depth = 5 everywhere, valid everywhere.

Expected shift: a world point seen at pixel u in i appears at `u − 5` in j (`fx · 0.5 / 5 = 5 px`).
- `warp`: pixel (40, 32) of i maps to ≈ (35, 32) in j.
- Masks: i has a square [20:30, 20:30] (rows, cols); j has the square shifted 5 px left, [20:30, 15:25]. `pair_best_ious` → one value > 0.9.
- Random masks in j (5 random blobs, seed 0) → the best IoU < 0.3.

## Laptop check
```bash
pytest -q tests/test_mrc.py tests/test_imports.py
```

## Lab check
```bash
for v in sam sam2_frame sam2_track_k10; do python -m evaluation.mrc --scene figurines --variant $v; done
python -c "
import json
for v in ['sam','sam2_frame','sam2_track_k10']:
    d = json.load(open(f'results/figurines/{v}/mrc.json')); print(v, d['mrc_d1'], d['mrc_d3'], d['mrc'], d['masks_per_frame'])"
```
Expected: values in (0, 1); d1 ≥ d3 typically. H1 predicts V3 > V1/V2, but record whatever comes out.

## Done when
- [ ] Tests pass; MRC for the 3 variants on figurines

## Findings / Blockers
