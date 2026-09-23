# T-E04 — 2D-only baseline: SAM masks + best CLIP score on the test photo

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-E01, T-E02, T-B12 |
| Requirements | FR-E4 |
| May edit 06-contracts.md | no |

## Goal
`python -m evaluation.baseline_2d --scene <id>` answers each held-out query **without any 3D**: segment the test photo with SAM v1 and pick the mask CLIP likes best. It writes `results/<scene>/baseline_2d.json` (C14.3).

## Background
This baseline shows what the 3D representation adds (H4). It sees the test photo directly (an advantage), but it has no multi-view information. It uses only models we already have:
- SAM v1 ViT-H automatic masks, with the same thresholds as V1;
- CLIP mask crops, using SAGA's recipe (black background, box crop, 224×224);
- the same text scoring as the 3D query (`server/query.py`).

## Read first
1. `docs/spec/09-experiments-and-evaluation.md` §5.3
2. Fork: `third_party/SegAnyGAussians/get_clip_features.py` + `clip_utils/__init__.py` (the crop recipe to COPY)
3. `server/query.py` (`text_mask_scores`, `GpuEngine.text_embeddings`, `clip_model`, `clip_preprocess`)
4. `evaluation/gt.py`, `evaluation/metrics.py`

## Files
| Action | Path |
|---|---|
| create | `evaluation/baseline_2d.py` |
| create | `tests/test_baseline_2d.py` |

## Provenance
- NEW + COPY of the SAGA mask-crop code, with a Source header.
- `segment_anything.SamAutomaticMaskGenerator` (PIP).

## Interface
```python
def best_mask(scores: np.ndarray, masks: np.ndarray) -> tuple[np.ndarray, int]: ...          # masks bool [M,H,W]
def score_map(scores: np.ndarray, masks: np.ndarray) -> np.ndarray: ...                      # float [H,W], max over covering masks
def crop_for_clip(image_rgb: np.ndarray, mask: np.ndarray) -> np.ndarray: ...                # COPY: black bg, bbox crop, 224x224
def run(scene_id: str, force: bool = False) -> Path: ...
```

## Steps
1. For each annotated test frame, run the SAM v1 automatic mask generator once:
   - `SamAutomaticMaskGenerator(sam_model_registry["vit_h"](checkpoint=...).cuda(), **cfg["masks"]["amg"])` on the RGB image resized to the GT size;
   - masks `[M, H, W]`.
2. Embed every mask crop with `engine.clip_model` (the same preprocessing as SAGA's script) and L2-normalize.
3. For each category: `pos, negs = engine.text_embeddings(c)`; `s = text_mask_scores(E, pos, negs)`.
   - `P = masks[argmax s]` → IoU, BIoU;
   - `loc_hit(score_map(s, masks), boxes)`.
4. Write C14.3: `variant "baseline_2d"`, `seed null`, `per_query` (no `iou_sweep`), `skipped`, `summary`, `git_sha`.
5. `__main__` argparse `--scene --force`.

## Tests (pure)
- `best_mask` picks the highest-score mask.
- `score_map` with two overlapping masks gives the max where they overlap and 0 outside.
- `crop_for_clip` on a 50×40 image with a 10×10 mask returns 224×224×3 uint8, with black outside the mask region.

## Laptop check
```bash
pytest -q tests/test_baseline_2d.py tests/test_imports.py
```

## Lab check
```bash
python -m evaluation.baseline_2d --scene figurines && python -c "import json; print(json.load(open('results/figurines/baseline_2d.json'))['summary'])"
```

## Done when
- [ ] Tests pass; the lab run writes C14.3

## Findings / Blockers
