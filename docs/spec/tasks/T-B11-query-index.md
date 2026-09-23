# T-B11 — Query index precompute (SAGA's text-query clustering, offline)

| Field | Value |
|---|---|
| Tier | **[M]** (a port of research notebook code; memory-heavy maths) |
| Depends on | T-B09, T-B10 |
| Requirements | FR-B9 |
| May edit 06-contracts.md | no |

## Goal
`python -m pipeline index --scene <id> --variant <v> --seed <k>` writes `saga/seed<k>/query_index.pt` (C9). Text queries (T-B12) then take milliseconds instead of re-running SAGA's slow notebook clustering.

## Background
SAGA answers a text query by:
1. grouping all training masks (across all frames) into **objects**, clustering masks whose 3D features agree;
2. scoring each object with CLIP.

Step 1 is slow and doesn't depend on the text, so we precompute it. For every mask m:
- **mask feature:** the average of the rendered SAGA features inside the mask, after gating them with the scale gate at the mask's own 3D scale;
- **identifier:** a random 1% of Gaussians are "anchors"; the identifier marks which anchors agree with the mask feature (cos > 0.5);
- **distance:** masks of the same object have overlapping identifiers, so `1 − IoU(identifiers)` is a distance;
- **clusters:** HDBSCAN groups masks into objects.

We port SAGA's `prompt_segmenting.ipynb` cells 41–50. Differences:
- seeded anchors;
- features rendered by our `pipeline/render.py`;
- results saved to a file instead of kept in notebook variables.

## Read first
1. `docs/spec/08-phase-b.md` §5
2. `docs/spec/06-contracts.md` §C8, §C9, §C11
3. `pipeline/render.py`, `pipeline/colmap_io.py`, `pipeline/camera.py`
4. Fork: `third_party/SegAnyGAussians/prompt_segmenting.ipynb`, cells 41–50 (read the JSON, or open it in Jupyter on the lab)
5. Fork: `train_contrastive_feature.py` (how `scale_gate` is built: `Sequential(Linear(1,32), Sigmoid())`; its state-dict keys)

## Files
| Action | Path |
|---|---|
| create | `pipeline/query_index.py` |
| modify | `pipeline/cli.py`: add `index` (`saga_stages.run_all` picks up `build_index` automatically through its try-import from T-B08) |
| create | `tests/test_query_index.py` |

## Provenance
COPY + adapt of SAGA's `prompt_segmenting.ipynb` cells 41–50. Header:
```python
# Source: https://github.com/Jumpat/SegAnyGAussians @ <sha>, prompt_segmenting.ipynb cells 41–50 (text-query preprocessing)
# License: Apache-2.0. Changes: seeded anchors; gsplat feature rendering; chunked IoU distance; saved to query_index.pt (C9).
```

## Interface
```python
def load_saga_outputs(seed_dir: Path, iteration: int) -> tuple["torch.Tensor", "torch.nn.Module", object, np.ndarray]: ...
    # pf [N,32], gate (Sequential(Linear(1,32),Sigmoid()) with the loaded state dict), q_trans, xyz [N,3]
def gates_for_scales(gate, q_trans, scales: np.ndarray) -> "torch.Tensor": ...        # [M,32]
def mask_features(F: "torch.Tensor", masks: "torch.Tensor", gates: "torch.Tensor") -> "torch.Tensor": ...  # F [h,w,32] unit-norm; masks bool [M,h,w] -> [M,32] unit-norm
def identifiers(anchors: "torch.Tensor", gates: "torch.Tensor", mfeat: "torch.Tensor", thresh: float) -> "torch.Tensor": ...  # bool [M,Na]
def iou_distance(ident: "torch.Tensor", chunk: int = 2048) -> np.ndarray: ...     # float64 [T,T]
def build_index(scene_id: str, variant: str, seed: int, force: bool = False) -> Path: ...
```

## Steps
1. `load_saga_outputs`:
   - read `point_cloud/iteration_<it>/contrastive_feature_point_cloud.ply` with `plyio.read_vertex`: `pf` = stack of `f_0..f_31`, `xyz` = x, y, z;
   - build `gate = torch.nn.Sequential(torch.nn.Linear(1, 32), torch.nn.Sigmoid())` and `load_state_dict(torch.load(scale_gate.pt, map_location="cpu"))`. VERIFY the key names; adapt if SAGA wraps it differently;
   - `q_trans = joblib.load(q_trans.joblib)`.
2. **Invariant (C11):**
   - `xyz` must equal `plyio.read_xyz(web/scene.ply)` (`np.allclose`);
   - `plyio.xyz_hash(xyz)` must equal the manifest's;
   - otherwise raise `RuntimeError("Gaussian order mismatch …")`.
3. `gates_for_scales`: `q = q_trans.transform(scales.reshape(-1, 1)).astype(np.float32)`, then `gate(torch.from_numpy(q))`.
4. `mask_features` (per mask; loop over M, M ≤ ~200):
   - `Fm = normalize(F[mask] * g, dim=-1)`;
   - `mean = Fm.mean(0)`;
   - `out[m] = normalize(mean, dim=0)`.
5. `identifiers`: for each mask `(normalize(anchors * g_m, dim=-1) @ mfeat_m) > thresh`. Vectorize per frame: `[M, Na, 32]` fits in memory.
6. `iou_distance`: on the GPU in row chunks:
   - `I = ident.half()`; `sizes = I.sum(1)`;
   - `inter = I[r] @ I.T`; `union = sizes[r, None] + sizes[None] - inter`;
   - `D[r] = 1 - inter / union.clamp(min=1)`;
   - move to the CPU as float64.
7. `build_index`:
   1. `pfn = normalize(pf)`; anchors = `rng.choice(N, round(anchor_frac·N), replace=False)` with `np.random.default_rng(seed)`; `A = pfn[anchors]`.
   2. Frames = `variant/images` sorted. If the total masks > `max_masks`, use every 2nd frame and record `frame_stride`.
   3. For each frame:
      - camera from `colmap_io`;
      - `K4 = camera.intrinsics(fx, fy, cx, cy, scale=1/down)`, `(w, h) = (W // down, H // down)`;
      - `F, _ = render.render_features(g, pfn, viewmat, K4, w, h)`, then `F = normalize(F, dim=-1)`;
      - load the masks (CPU → GPU), the scales and the CLIP features;
      - compute `gates`, `mfeat`, `ident`;
      - append everything, plus `mask_frame` and `mask_local`.
   4. `D = iou_distance(I)`; `labels = hdbscan.HDBSCAN(min_cluster_size=…, cluster_selection_epsilon=…, metric="precomputed").fit(D).labels_`.
   5. `mask_clip = normalize(clip.float()).half()`.
   6. `torch.save` the C9 dict.
   7. Print T, the number of clusters, the noise %, and the timings.
8. CLI `index --scene --variant --seed [--force]`. Nothing to change in `saga_stages.run_all`: its try-import now finds `build_index` and runs it per seed. Check this in the lab check.

## Gotchas
- Keep the per-frame loop's GPU memory bounded: delete `F` after each frame; build `ident` as bool.
- HDBSCAN on T = 20k needs a 3.2 GB matrix: fine on the lab, **never** on the laptop.

## Tests (CPU, small synthetic tensors; no hdbscan)
- `mask_features`: with F = the same unit vector v at every pixel and gate g = all 0.5, every mask gives `normalize(v * 0.5) == v`.
- `identifiers`: anchors = [e1, e2], a mask feature = e1 with a gate of ones and thresh 0.5 → `[True, False]`.
- `iou_distance` on `[[1,1,0],[1,0,0],[0,0,1]]` (bool) with `chunk=2` → `D[0,1] = 0.5`, `D[0,2] = 1`, `D[i,i] = 0`.
- `gates_for_scales` with a fitted `QuantileTransformer` on `[1..100]` and a gate of `Linear(1,32)` with zero weights and bias 0 → all values 0.5.

## Laptop check
```bash
pytest -q tests/test_query_index.py tests/test_imports.py
```

## Lab check
```bash
for v in sam sam2_frame sam2_track_k10; do python -m pipeline index --scene figurines --variant $v --seed 0; done
python -c "
import torch
for v in ['sam','sam2_frame','sam2_track_k10']:
    d = torch.load(f'scenes/figurines/variants/{v}/saga/seed0/query_index.pt', map_location='cpu')
    c = d['mask_cluster']; print(v, len(c), int(c.max())+1, 'clusters', round(float((c<0).float().mean()),3), 'noise')"
```
Expected: T in the thousands; 5–500 clusters; a noise fraction < 0.5; a runtime of minutes.

## Done when
- [ ] Tests pass; indexes exist for figurines × 3 variants

## Findings / Blockers
