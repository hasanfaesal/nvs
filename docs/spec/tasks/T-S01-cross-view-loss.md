# T-S01 — Stretch: cross-view contrastive term using track IDs (V3x)

| Field | Value |
|---|---|
| Tier | **[M]** |
| Depends on | T-B17, T-B07 (start only after the Phase B gate) |
| Requirements | FR-S1 |
| May edit 06-contracts.md | **yes**: add `saga.xview_weight` to C6.1 and `stretch` examples to C6.3 |

## Goal
A new variant `sam2_track_k10_xview`. It trains SAGA on **the same masks as V3**, plus a loss term that pulls together features of pixels in *different* views that carry the *same* track ID. With weight 0, it must behave exactly like V3.

## Background
SAGA's loss only compares pixels inside one view (`08-phase-b.md` §4), so SAM 2's persistent IDs are thrown away. This term uses them. The design and its motivation (Contrastive Lift, Panoptic Lifting) are in `08-phase-b.md` §11 and in reading-list papers #20 and #21. This is research code: keep it small, and behind a flag whose default is off.

## Read first
1. `docs/spec/08-phase-b.md` §4, §11
2. Fork: `third_party/SegAnyGAussians/train_contrastive_feature.py`, the loss block (≈ L145–295)
3. Fork: `scene/dataset_readers.py` (where masks are attached to cameras)
4. `pipeline/saga_stages.py`, `pipeline/cli.py` (the `masks` dispatch)

## Files
| Action | Path |
|---|---|
| modify (fork) | `train_contrastive_feature.py`: `--xview_weight` (default 0) + the extra term |
| modify (fork) | `scene/dataset_readers.py`: load `track_ids/<stem>.json` into the camera info when it exists |
| modify | `pipeline/variant.py` (`run_masks`): for `*_xview`, **symlink** `sam_masks`, `track_ids`, `mask_scales` and `clip_features` from the base variant instead of recomputing them |
| modify | `pipeline/saga_stages.py`: add `--xview_weight <cfg.saga.xview_weight>` to `train_cmd` for `*_xview` variants |
| modify | `configs/pipeline.yaml`, `docs/spec/06-contracts.md` C6.1 (`saga.xview_weight: 0.5`), C6.3 |

## Steps
1. **Loss (the fork):**
   1. After SAGA's view i loss, pick j uniformly among the train views with `0 < |i − j| ≤ 3` (camera-list order = sorted names = capture order).
   2. Render the features for j.
   3. Sample `P = num_sampled_rays // 2` pixels inside masks in each view.
   4. For each sampled pixel, find the finest containing mask (the smallest area). That gives its track ID τ and its scale s.
   5. `g = gate(q_trans(s_p))`; `corr = cos(normalize(F_i(p) ⊙ g), normalize(F_j(q) ⊙ g))` for all pairs.
   6. `L_x = mean(−corr)[τ_p == τ_q] + mean(relu(corr))[τ_p != τ_q]`; skip it when there are no positives.
   7. `loss += xview_weight · L_x`.
   8. Log `L_x` every 100 iterations.
2. **Equivalence check:** with `--xview_weight 0` the code path must not change the RNG stream. Draw the j-sampling random numbers **only when the weight > 0**.
3. **Pipeline:**
   - the variant name `sam2_track_k10_xview` passes `VARIANT_RE`;
   - the masks step links the base variant's folders; `train` passes the weight.
4. **Experiments:** `stretch: [{variant: sam2_track_k10_xview, seeds: [0,1,2]}]` in `configs/experiments.yaml`; then re-run the matrix.

## Laptop check
```bash
python -m py_compile third_party/SegAnyGAussians/train_contrastive_feature.py && pytest -q
```

## Lab check
```bash
# equivalence: weight 0 must match V3 for the same seed (compare the first logged losses)
python -m pipeline all --scene ramen --variant sam2_track_k10_xview --seeds 0
python -m evaluation.eval_3d --scene ramen --variant sam2_track_k10_xview --seed 0
```
Expected:
- with weight 0, the loss log is identical to the V3 run's for the first iterations;
- with weight 0.5, the run completes, time ≈ 1.5–2× V3's, and VRAM < 14 GB.

## Done when
- [ ] V3x trained and evaluated on all scenes; it appears in `summary.json`

## Findings / Blockers
