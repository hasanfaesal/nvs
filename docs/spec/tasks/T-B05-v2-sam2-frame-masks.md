# T-B05 — V2 masks: SAM 2.1 automatic masks per frame (the control)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-B03 (T-B04 for the dispatcher) |
| Requirements | FR-B5 |
| May edit 06-contracts.md | no |

## Goal
`python -m pipeline masks --scene <id> --variant sam2_frame` writes SAM 2.1 "segment everything" masks for every train frame, **in exactly the same format, resolution and thresholds as V1**.

## Background
V2 exists to separate two effects: "SAM 2 is a newer model" versus "SAM 2 tracking keeps masks consistent". So V2 uses SAM 2 per frame, *without* tracking.
- **Same images and thresholds as V1.** SAGA's script hardcodes `points_per_side=32, pred_iou_thresh=0.88, stability_score_thresh=0.95, box_nms_thresh=0.7, crop_n_layers=0, min_mask_region_area=100`. The same values are in `configs/pipeline.yaml` `masks.amg`, and a test keeps them in sync.
- **Same resize code as V1.** We copy SAGA's mask-downsampling code rather than rewriting it, so V1 and V2 differ **only** in the model.

## Read first
1. `docs/spec/08-phase-b.md` §3.1, §3.3
2. `docs/spec/06-contracts.md` §C7
3. Fork: `third_party/SegAnyGAussians/extract_segment_everything_masks.py` (the COPY source: its loop and its mask resize for `--downsample_type mask`)
4. sam2: `notebooks/automatic_mask_generator_example.ipynb` (how `build_sam2(..., apply_postprocessing=False)` and `SAM2AutomaticMaskGenerator` are created)

## Files
| Action | Path |
|---|---|
| create | `pipeline/masks_sam2_frame.py` |
| create | `tests/test_masks_sam2_frame.py` |

## Provenance
COPY + adapt of SAGA's `extract_segment_everything_masks.py` (loop + resize). Header:
```python
# Source: https://github.com/Jumpat/SegAnyGAussians @ <sha>, extract_segment_everything_masks.py (loop, mask resize)
# License: Apache-2.0. Changes: SAM2AutomaticMaskGenerator instead of SAM v1; RGB input; CPU bool output; config-driven.
```

## Interface
```python
def resize_masks_like_saga(masks: "np.ndarray | torch.Tensor", h: int, w: int) -> "torch.Tensor": ...  # [M,H,W] -> bool [M,h,w]
def run(scene_id: str, variant: str = "sam2_frame", force: bool = False) -> None: ...
```

## Steps
1. Copy SAGA's resize for the `mask` downsample type into `resize_masks_like_saga`, **keeping its method** (bilinear + `>= 0.5`, per the code check). Handle M = 0 → `torch.zeros((0, h, w), dtype=torch.bool)`.
2. `run` (imports `torch`, `cv2`, `sam2` inside):
   1. `from sam2.build_sam import build_sam2`; `from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator`.
   2. `model = build_sam2(cfg["masks"]["sam2_cfg"], str(ckpt), device="cuda", apply_postprocessing=False)`.
   3. `amg = SAM2AutomaticMaskGenerator(model, **cfg["masks"]["amg"])`.
   4. For each name in `sorted(os.listdir(vdir/"images"))`:
      - `img = cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)`;
      - `ms = [m["segmentation"] for m in amg.generate(img)]`;
      - `h, w = H // down, W // down`; `stack = resize_masks_like_saga(np.stack(ms) if ms else np.zeros((0, H, W), bool), h, w)`;
      - `torch.save(stack.cpu(), vdir/"sam_masks"/f"{stem}.pt")`.
   5. Print progress every 10 frames.
3. Skip if `variant.masks_done(vdir)` and not `force`.
4. Run **in-process**, and log timing with a `run_stage`-style record: build the record dict yourself with the same C15 keys (use `vram_used_mb()` before and after, plus `torch.cuda.max_memory_allocated()`), and append it to `stages.jsonl`. Document which VRAM measure you used in Findings.

## Tests
- `resize_masks_like_saga`: a 64×64 mask with an 8×8 True block at (16:24, 16:24) → 16×16 output with a True block at (4:6, 4:6); M = 0 input → shape `(0, 16, 16)`; the output dtype is bool.
- **Config matches SAGA:** read the text of `third_party/SegAnyGAussians/extract_segment_everything_masks.py` and assert each `cfg["masks"]["amg"]` key=value (e.g. `pred_iou_thresh=0.88`) appears in it (whitespace-insensitive regex). This fails if someone changes one side only.

## Laptop check
```bash
pytest -q tests/test_masks_sam2_frame.py tests/test_imports.py
```

## Lab check
```bash
python -m pipeline variant --scene ramen --variant sam2_frame --seeds 0 1 2
python -m pipeline masks --scene ramen --variant sam2_frame && python -m pipeline masks --scene ramen --variant sam2_frame --check
```
Expected: the same frame count and `(h, w)` as V1 (T-B04), a masks-per-frame count of the same order, VRAM < 14 GB.

## Done when
- [ ] Tests pass; V2 masks exist for ramen

## Findings / Blockers
