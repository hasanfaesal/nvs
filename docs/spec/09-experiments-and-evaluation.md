# 09 — Experiments and evaluation

This document defines exactly what is run, what is measured, how each number is computed, and how it is reported. The research question and hypotheses are in `00-overview.md` §4.

## 1. Variables

| Kind | Variable | Values |
|---|---|---|
| Independent (main) | mask source | V1 `sam`, V2 `sam2_frame`, V3 `sam2_track_k10` |
| Independent (ablation) | AutoSeg keyframe stride K for V3 | 5, 10, 20 |
| Independent (stretch) | cross-view term | V3 vs V3x `sam2_track_k10_xview` |
| Controlled | scene, split, RGB 3DGS model (one per scene), images seen by SAM/SAM 2/SAGA (train only), mask resolution (÷4), AMG thresholds, SAGA hyper-parameters (10k iterations, 1,000 rays, 32-D), query thresholds (C13), CLIP model, evaluation frames and queries | fixed |
| Random | SAGA training seed | 0, 1, 2 |
| Dependent | mIoU, mBIoU, localization accuracy, MRC, runtime, peak VRAM, latency | §5 |

## 2. Data

| Scene | Source | Frames (approx.) | Annotated held-out frames | Distinct query categories |
|---|---|---|---|---|
| figurines | LERF-OVS | 299 | 4 | 17 |
| ramen | LERF-OVS | 131 | 7 | 14 |
| waldo_kitchen | LERF-OVS | 187 | 5 | 17 |
| teatime | LERF-OVS | 177 | 6 | 16 |
| desk_01 (custom) | phone video | ~180–270 | 5–8 | 8–12 |
| shelf_01 (custom) | phone video | ~180–270 | 5–8 | 8–12 |

The LERF-OVS counts come from inspecting the zip. VERIFY (T-007) after download.

**Held-out protocol (the only protocol we report):**
- Every annotated frame is in `split.test` (C4), so it is never seen by gsplat, SAM, SAM 2, AutoSeg-SAM2 or SAGA.
- Every 8th frame is also held out, for PSNR/SSIM/LPIPS.
- Labels are read **only** by `evaluation/`.
- Our numbers are therefore **not comparable** with LangSplat/SAGA papers, which train on the annotated frames. Say so in the report.

**Query text:** the GT category string exactly as annotated, stripped and lower-cased. No synonyms and no rewriting (`00-overview.md` §5).

## 3. Run matrix (`configs/experiments.yaml`, C6.3)

| Block | Runs | Count (4 LERF + 2 custom) |
|---|---|---|
| Phase A 3DGS | 1 per scene | 6 |
| Masks + scale + CLIP | per (scene, variant) for V1, V2, V3-K10, V3-K5, V3-K20 | 30 |
| SAGA training | core: 6 scenes × 3 variants × 3 seeds; ablation: 6 × {K5, K20} × seed 0 | 54 + 12 = 66 |
| Query index | one per SAGA training | 66 |
| 3D evaluation | one per SAGA training | 66 |
| 2D baseline | per scene | 6 |
| MRC | per (scene, variant) | 30 |
| Stretch V3x | 6 × 3 seeds (only after T-B17) | 18 |

**Compute estimate** (A4000, sequential):
- 3DGS ≈ 3 h;
- masks ≈ 6–10 h (V3 is the slowest);
- scale + CLIP ≈ 7 h;
- SAGA ≈ 66 × 25 min ≈ 27 h;
- index ≈ 66 × 5–10 min ≈ 8 h;
- evaluation ≈ 3 h.

Total **≈ 55–60 GPU-hours ≈ 2.5 days** of unattended tmux time. Run the LERF scenes first (T-E08), and the custom scenes after T-C04.

## 4. Protocol per scene (what `experiments/run_matrix.py` executes, in this order)

```text
ingest → split → train3dgs → export → saga-import
for v in variants(core ∪ ablations):
    variant --seeds S(v) → masks → saga scale → saga clip
    for k in S(v): saga train --seed k → index --seed k → evaluation.eval_3d --variant v --seed k
    evaluation.mrc --variant v
evaluation.baseline_2d
(after all scenes) evaluation.aggregate
```

Every step is skip-if-done, so the runner can be restarted at any time.

## 5. Metrics — exact definitions

### 5.1 Reconstruction (Phase A)
- PSNR, SSIM and LPIPS come from gsplat's `stats/val_step<last>.json`, computed on **all** `split.test` images at training resolution. LPIPS uses AlexNet (`lpips_net: alex`), and this is reported.
- Also report the number of Gaussians (`num_GS`), the training seconds and the peak VRAM (C15).

### 5.2 3D segmentation on held-out frames (T-E03, `evaluation/eval_3d.py`)

For every annotated test frame f, and every GT category c present in f (FR-E1 gives `{c: (G_c, boxes_c)}`):
1. `scores_u8 = engine.text_query(scene, v, seed, c).scores_u8`. This is `GpuEngine` directly, not HTTP.
2. **Predicted mask:**
   - `sel = scores_u8 >= round(0.925 · 255)`, i.e. `query.text_threshold` (C13);
   - render `sel` as a 1-channel colour at f's camera (C10.2) at GT resolution: `P = render_scalar(sel.float()) >= 0.5`.
3. `iou = |P ∧ G_c| / |P ∨ G_c|`. If both are empty, iou = 1. If `G_c` is empty, skip the category and log it.
4. `biou = boundary_iou(G_c, P, dilation_ratio=0.02)` (copied from Gaussian Grouping).
5. **Localization:**
   - `H = render_scalar(scores_u8 / 255)`;
   - `Hf = cv2.blur(H, (30, 30))`;
   - `(y, x) = argmax(Hf)`;
   - hit iff `(x, y)` lies inside any box in `boxes_c` (LangSplat rule).
6. **Threshold sweep** (robustness figure, not a headline number): repeat step 2 and the IoU for t ∈ {0.875, 0.9, 0.925, 0.95, 0.975} and store `iou_sweep`.
7. **Per scene:**
   - `miou` = mean of iou over all (f, c) pairs, each pair weighted equally;
   - `mbiou` = the same for biou;
   - `loc_acc` = hits / pairs.
8. **Failure renders:** for seed 0, save a JPEG (long side 480 px, quality 80) of the test image with P (red) and G (green) outlines for each pair with iou < 0.5, plus the 3 best pairs, to `results/<scene>/<variant>/renders_seed0/<frame>__<query>.jpg`. At most 20 per (scene, variant).

Output: C14.2.

### 5.3 2D-only baseline (T-E04, `evaluation/baseline_2d.py`)

For every annotated test frame f and category c:
1. Run SAM v1 automatic masks on the full-resolution RGB test image, with the C6.1 thresholds (once per frame, cached).
2. For each mask, compute a CLIP image embedding using SAGA's crop recipe: black background, crop to the mask's bounding box, resize to 224×224, OpenCLIP ViT-B/16 (COPY from SAGA).
3. Compute the text score of each mask for c with the same `get_scores_with_template` logic as the 3D text query (imported from `server/query.py`).
4. **Prediction** P = the mask with the highest score. IoU and BIoU as in §5.2.
5. **Localization:** a per-pixel score map (each pixel takes the max score of the masks covering it, 0 elsewhere) → 30×30 blur → argmax → box hit.

Output: C14.3. This baseline has no 3D and no cross-view information. It shows what 3D consistency adds (H4).

### 5.4 Mask reprojection consistency — MRC (T-E05, `evaluation/mrc.py`)

It measures whether **the pseudo-labels themselves** agree across neighbouring views, before SAGA ever trains. This is the direct test of H1.

**Setup** for a variant v:
- the train frames in order `f_0 … f_{n−1}`;
- masks at `h × w = H/4 × W/4` (C7);
- cameras `(R_i, t_i)` and `K_i` scaled by 1/4;
- for every frame, the expected depth `D_i` and alpha `A_i`, rendered from the scene's RGB Gaussians at `(w, h)` (`render_depth`, gsplat `"RGB+ED"`);
- `valid_i = A_i > 0.5`.

**Warp from frame i to frame j:**
```text
for every pixel (u, v) with valid_i:
    X_cam = D_i[v,u] · K_i⁻¹ · [u + 0.5, v + 0.5, 1]ᵀ
    X_w   = R_iᵀ (X_cam − t_i)
    X_j   = R_j X_w + t_j;   z = X_j[2];   (u', v') = (K_j X_j / z)[:2]
    in_bounds = z > 0 and 0 ≤ u' < w and 0 ≤ v' < h;   (iu, iv) = floor(u'), floor(v')
    visible   = in_bounds and valid_j[iv, iu] and |z − D_j[iv, iu]| < 0.05 · D_j[iv, iu]     # occlusion test
V_ij = morphological_close(set of visible target pixels (iu, iv), 3×3)       # region of j that frame i can see
```

**Per mask m of frame i** (area ≥ 20 px):
```text
src = m ∧ valid_i;   ρ = |visible pixels of src| / |src|;   if ρ < 0.5: skip m (mostly occluded / out of view)
W   = morphological_close(target pixels of the visible src pixels, 3×3)      # the warped mask
best_m = max over masks n in frame j of  |W ∧ n ∧ V_ij| / |(W ∨ n) ∧ V_ij|    (0 if frame j has no masks)
```

**Aggregate:**
- `MRC_d` = mean of `best_m` over all masks, over all pairs (i, i+d) in **both** directions (i→j and j→i), for d ∈ {1, 3};
- `MRC = (MRC_1 + MRC_3) / 2`;
- also report `masks_per_frame` and the skipped fraction.

**Implementation notes:**
- Compute the best-match IoUs as a matrix product: `W` stack `[M_i, P]` × `n` stack `[M_j, P]`ᵀ, restricted to `V_ij` pixels, in torch on the GPU (CPU works too, just slower).
- Put the warp and pair-scoring functions in pure numpy/torch, so they are unit-tested on the laptop with a synthetic plane scene: identical masks → MRC ≈ 1; random masks → MRC < 0.3.

**Interpretation:**
- MRC is high when the same region is segmented the same way in neighbouring views.
- Multi-granular masks are fine: a part mask should find the same part in view j.
- **Caveat:** V3 is consistent partly *by construction* (propagation). That is the claim being tested, and the 3D mIoU (§5.2) is the independent check that consistency translates into better 3D segmentation.

Output: C14.4.

### 5.5 Systems measurements

| Measure | Source |
|---|---|
| Stage wall time, peak VRAM (`peak − baseline`) | `scenes/<id>/logs/stages.jsonl` (C15) |
| Text- and click-query latency (median, p90, warm) | `results/<id>/latency.json` (C14.6); text latency also per query in C14.2 |
| Browser FPS | `results/<id>/phase_a.json` `fps_lab` (manual, T-A16) |
| Web asset size, Gaussian count | manifest (C5) |

## 6. Statistics (T-E06, `evaluation/aggregate.py`)

- **Per scene and variant:** the mean ± std over seeds of `miou`, `mbiou` and `loc_acc`.
- **Overall per variant:** the mean over scenes of the per-scene seed-means, ± std **across scenes**.
- **Paired tests:** for the pairs (V3, V1), (V3, V2) and (V2, V1):
  - take the per-(scene, frame, category) IoU averaged over seeds;
  - keep the items present for both variants;
  - `scipy.stats.wilcoxon(a, b, zero_method="wilcox", alternative="two-sided")`;
  - report n, the mean difference and p.
  - Three planned tests; also report Holm-adjusted p-values.
- **K ablation:** seed 0 only; report mIoU, MRC, number of tracks and mask runtime for K = 5, 10, 20.
- **Never** drop a scene, seed or query from the aggregates. Skipped categories (empty GT) are listed.

Output: C14.5.

## 7. Report tables and figures (checklist)

| # | Content | Built from |
|---|---|---|
| Table A | Phase A: PSNR/SSIM/LPIPS, #Gaussians, training time, peak VRAM per scene | `phase_a` in summary |
| Table 1 | Held-out mIoU (mean ± std over seeds) per scene × variant, plus an overall row; same for mBIoU and localization accuracy | `main`, `overall` |
| Table 2 | MRC (d=1, d=3, mean) and masks/frame per scene × variant | C14.4 files |
| Table 3 | K ablation | `ablation_k` |
| Table 4 | 2D baseline vs 3D variants | `baseline_2d` + `main` |
| Table 5 | Systems: stage times, VRAM, query latency, FPS, asset size | `systems`, latency, phase_a |
| Table 6 | Wilcoxon tests | `wilcoxon` |
| Fig. 1 | Architecture | `docs/figures/` (existing) |
| Fig. 2 | Pseudo-label consistency strip: the same object over 5 consecutive frames, V1 vs V3 | pseudo-label viewer screenshots |
| Fig. 3 | Qualitative grid: test image, GT, V1, V2, V3 for 3 queries per scene | `renders_seed0/` |
| Fig. 4 | Threshold sweep: mIoU vs t per variant | `iou_sweep` |
| Fig. 5 | Failure cases, with an explanation | `renders_seed0/` with iou < 0.5 |

## 8. Honest-reporting rules

1. Report every scene, every seed and every query. Nothing is cherry-picked.
2. Thresholds are fixed from SAGA's defaults for all variants (C13). The sweep figure shows how sensitive the results are.
3. If V3 does not beat V1/V2, say so, and use MRC, the failure cases and the literature (Gaga, LaGa, SAM 2's reliance on small inter-frame motion) to explain why.
4. State the protocol difference from published papers (held-out vs trained-on-annotated).
5. Keep `results/` in git, with the `git_sha` of the code that produced each file.
