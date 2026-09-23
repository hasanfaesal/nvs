# T-E03 — 3D evaluation on held-out annotated frames

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-B12, T-B10, T-E01, T-E02 |
| Requirements | FR-E3, NFR-9 |
| May edit 06-contracts.md | no |

## Goal
`python -m evaluation.eval_3d --scene <id> --variant <v> --seed <k>` computes IoU, BIoU, localization and the threshold sweep for every (annotated test frame, GT category). It writes `results/<scene>/<variant>/seed<k>.json` (C14.2) and failure renders for seed 0.

## Background
For each held-out annotated frame and each object named in its labels:
1. ask the 3D model the text query (the category name);
2. select the Gaussians scoring above the fixed threshold;
3. render that selection from the test camera;
4. compare it with the human mask.

This is the honest test: that camera was never used in training. The threshold is SAGA's default for every variant (C13), and the sweep shows sensitivity. Structure the code so the GPU parts are **injected**, which lets the whole loop be tested on the laptop with fakes.

## Read first
1. `docs/spec/09-experiments-and-evaluation.md` §5.2, §8
2. `docs/spec/06-contracts.md` §C4, §C13, §C14.2
3. `evaluation/gt.py`, `evaluation/metrics.py`
4. `server/query.py` (`GpuEngine.text_query`), `pipeline/render.py` (`render_scalar`)

## Files
| Action | Path |
|---|---|
| create | `evaluation/eval_3d.py` |
| create | `tests/test_eval_3d.py` |

## Provenance
NEW.

## Interface
```python
SWEEP = (0.875, 0.9, 0.925, 0.95, 0.975)
def evaluate(frames: list[dict], query_fn, render_fn, threshold: float) -> dict: ...
    # frames: [{"stem", "cam", "hw", "gt": {category: GTObject}, "image": np.ndarray|None}]
    # query_fn(text) -> (scores_u8 np.uint8[N], latency_ms)
    # render_fn(values np.float32[N], cam, hw) -> np.float32[H,W]
    # returns {"per_query": [...], "skipped": [...], "summary": {...}}   (C14.2 fields)
def save_failure_renders(result: dict, frames: list[dict], out_dir: Path, masks: dict) -> None: ...
def run(scene_id: str, variant: str, seed: int, force: bool = False) -> Path: ...
```

## Steps
1. `evaluate`: for each frame and each category c, with `(scores, ms) = query_fn(c)`:
   - `sel = scores >= round(threshold*255)`; `P = render_fn(sel.astype(float32), cam, hw) >= 0.5`;
   - `iou = calculate_iou(P, G)`, `biou = boundary_iou(G, P)`;
   - `heat = render_fn(scores/255, cam, hw)`; `loc = loc_hit(heat, boxes)`;
   - `iou_sweep = {str(t): calculate_iou(render_fn((scores >= round(t*255)).astype(float32), cam, hw) >= 0.5, G) for t in SWEEP}`;
   - an empty GT goes to `skipped` with the reason "empty GT";
   - the summary: `miou`, `mbiou` = means over the pairs; `loc_acc` = hits/pairs; `n_queries`.
2. `run` (GPU wiring):
   - `engine = GpuEngine()`; Gaussians from `render.load_gaussians(web/scene.ply)`;
   - the test cameras from `colmap_io` (the annotated frames are in `sparse/0`);
   - for `hw` ≠ the image size, scale K by `(w/W, h/H)` with `camera.intrinsics(..., scale=...)` (use separate x/y scales if they differ);
   - `query_fn = lambda c: (engine.text_query(scene, v, k, c).scores_u8, latency)`;
   - `render_fn` → `render.render_scalar(g, torch.from_numpy(values).cuda(), viewmat, K, w, h)`;
   - add `scene_id`, `variant`, `seed`, `threshold` and `git_sha`; write the JSON with `indent=1`; skip if it exists and not `force`.
3. `save_failure_renders` (seed 0 only):
   - for pairs with iou < 0.5, plus the 3 best, at most 20: the test image resized to the GT size, with P's contour in red and G's in green (`cv2.drawContours`);
   - resize so the long side is 480; JPEG quality 80;
   - `results/<scene>/<variant>/renders_seed0/<stem>__<query with spaces→_>.jpg`.
4. `if __name__ == "__main__":` argparse `--scene --variant --seed --force`.

## Tests (fakes, CPU)
- N = 4 Gaussians, images 4×4.
  - `render_fn` places Gaussian i's value on pixel row i (rows 0–3): `out[i, :] = values[i]`.
  - `query_fn("a")` returns scores `[255, 255, 0, 0]`; the GT for "a" is rows 0–1 → IoU = 1, with a box around rows 0–1 → loc hit.
  - `query_fn("b")` returns `[0, 0, 0, 255]`; the GT for "b" is rows 2–3 → IoU = 0.5.
  - `summary.miou == 0.75`, `n_queries == 2`.
- A category with an empty GT mask goes to `skipped`, not into the mean.

## Laptop check
```bash
pytest -q tests/test_eval_3d.py tests/test_imports.py
```

## Lab check
```bash
python -m evaluation.eval_3d --scene figurines --variant sam2_track_k10 --seed 0
python -c "import json; d=json.load(open('results/figurines/sam2_track_k10/seed0.json')); print(d['summary'], len(d['per_query']), len(d['skipped']))"
ls results/figurines/sam2_track_k10/renders_seed0 | head
```
Expected: a summary with mIoU in [0, 1]; the number of pairs ≈ the categories across the 4 annotated frames; failure renders exist.

## Done when
- [ ] Tests pass; the lab run writes a C14.2 file

## Findings / Blockers
