# T-E02 — Segmentation metrics: IoU, Boundary IoU, localization hit

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-002 |
| Requirements | FR-E2 |
| May edit 06-contracts.md | no |

## Goal
`evaluation/metrics.py` provides the three per-query metrics used in every table, copied from the reference implementations.

## Background
- **IoU:** the overlap of predicted and GT masks.
- **Boundary IoU:** the same, computed only in a thin band around each contour (2% of the image diagonal). It rewards crisp edges.
- **Localization hit** (LangSplat's metric): blur the predicted score map with a 30×30 mean filter, take the brightest pixel, and check whether it falls inside a GT box.

Copying the reference code (Gaussian Grouping for IoU/BIoU; LangSplat's localization logic) keeps our numbers computed the standard way.

## Read first
1. `docs/spec/09-experiments-and-evaluation.md` §5.2
2. Gaussian Grouping: `script/eval_lerf_mask.py`: `calculate_iou`, `mask_to_boundary`, `boundary_iou` (https://github.com/lkeab/gaussian-grouping)
3. LangSplat: `eval/evaluate_iou_loc.py::lerf_localization` (for the localization rule only)

## Files
| Action | Path |
|---|---|
| create | `evaluation/metrics.py` |
| create | `tests/test_metrics.py` |

## Provenance
- COPY of Gaussian Grouping (Apache-2.0) `calculate_iou`, `mask_to_boundary`, `boundary_iou`, with a Source header; keep the names.
- `loc_hit` re-implements LangSplat's rule: mean filter 30×30, argmax, point-in-box. Credit it in a comment.

## Interface
```python
def calculate_iou(mask1: np.ndarray, mask2: np.ndarray) -> float: ...                 # copied
def mask_to_boundary(mask: np.ndarray, dilation_ratio: float = 0.02) -> np.ndarray: ...  # copied
def boundary_iou(gt: np.ndarray, dt: np.ndarray, dilation_ratio: float = 0.02) -> float: ...   # copied
def loc_hit(heatmap: np.ndarray, boxes: list[tuple[int, int, int, int]], k: int = 30) -> bool: ...
```

## Steps
1. Copy the three Gaussian Grouping functions verbatim, only adapting the input types to bool/uint8 numpy arrays. They use `cv2.copyMakeBorder` + `cv2.erode` with dilation = `max(1, round(ratio · diag))`.
2. `loc_hit`:
   - `f = cv2.blur(heatmap.astype(np.float32), (k, k))`;
   - `y, x = np.unravel_index(np.argmax(f), f.shape)`;
   - return True if any box has `x1 ≤ x ≤ x2 and y1 ≤ y ≤ y2`.

## Tests
- IoU of identical masks = 1; of disjoint masks = 0; two 10×10 squares offset by 5 px horizontally in a 20×20 image: IoU = 50/150.
- Boundary IoU of identical masks = 1; of a mask vs the same mask shifted by 10 px inside a 100×100 image < 0.5.
- `loc_hit`: a heatmap with a hot 20×20 block centered at (60, 40) and a box (50,30,70,50) → True; box (0,0,10,10) → False.

## Laptop check
```bash
pytest -q tests/test_metrics.py tests/test_imports.py
```

## Lab check
None (pure).

## Done when
- [ ] Tests pass; the Source header is present

## Findings / Blockers
