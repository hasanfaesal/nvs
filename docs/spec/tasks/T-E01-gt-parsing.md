# T-E01 — Ground-truth parsing (LERF-OVS JSON + labelme JSON)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-002 |
| Requirements | FR-E1 |
| May edit 06-contracts.md | no |

## Goal
`evaluation/gt.py` reads a label file in either format and returns, for each category, one binary mask (all instances unioned) and its bounding boxes.

## Background
- **LERF-OVS labels** (LangSplat) look like:
  `{"info": {"name", "width", "height"}, "objects": [{"category", "segmentation": [[x,y],…], "bbox": [x1,y1,x2,y2]}]}`.
- **Our own scenes** are annotated with **labelme**, whose files look different:
  `{"imageWidth", "imageHeight", "shapes": [{"label", "points": [[x,y],…], "shape_type": "polygon"}]}`.

The same category can appear several times (e.g. two cups). The GT for the query "cup" is the **union**, with one box per instance. We copy LangSplat's polygon rasterization and per-label union, and add a small labelme reader.

## Read first
1. `docs/spec/09-experiments-and-evaluation.md` §5.2
2. LangSplat: `eval/evaluate_iou_loc.py::eval_gt_lerfdata` and `eval/utils.py::polygon_to_mask, stack_mask` (https://github.com/minghanqin/LangSplat)
3. `docs/spec/tasks/T-007-download-lerf-ovs.md`, **Findings** (the JSON keys actually seen)

## Files
| Action | Path |
|---|---|
| create | `evaluation/gt.py` |
| create | `tests/test_gt.py` |

## Provenance
- COPY of LangSplat's `polygon_to_mask` / `stack_mask` logic (**check LangSplat's license first**; record it in `THIRD_PARTY.md`).
- If the license isn't permissive, re-implement it from this description (`cv2.fillPoly` on int32 points, union by logical OR) and write `# Re-implemented from description (license)` instead of a Source header.
- The labelme reader is NEW.

## Interface
```python
@dataclass
class GTObject:
    mask: np.ndarray                          # bool [H,W]
    boxes: list[tuple[int, int, int, int]]    # (x1, y1, x2, y2) per instance

def polygon_to_mask(hw: tuple[int, int], points: list[list[float]]) -> np.ndarray: ...
def load_gt(json_path: Path) -> tuple[tuple[int, int], dict[str, GTObject]]: ...   # ((H, W), {category: GTObject})
def scene_gt(scene_id: str) -> dict[str, tuple[tuple[int, int], dict[str, GTObject]]]: ...   # stem -> parsed labels
```

## Steps
1. Normalize category names with `.strip().lower()`.
2. **LERF-OVS:**
   - `(H, W) = (info["height"], info["width"])`;
   - each object: `polygon_to_mask`, then OR it into its category's mask;
   - box = `bbox` as given (x1,y1,x2,y2; VERIFY against a real file: if it's x,y,w,h, convert it and note that in Findings).
3. **labelme:**
   - `(H, W) = (imageHeight, imageWidth)`;
   - each shape with `shape_type` "polygon" (or missing): mask from `points`, box = the min/max of the points;
   - ignore other shape types, with a printed warning.
4. Unknown format → `ValueError`.
5. `scene_gt`: iterate over `source/labels/*.json` and key the results by stem.

## Tests
- LERF-OVS-style dict with two "cup" polygons (two squares) + one "plate": "cup" is the union of both, with 2 boxes.
- A labelme-style dict with the same geometry gives identical masks.
- The mask of the triangle `[[0,0],[9,0],[0,9]]` on a 10×10 grid has about 55 pixels (between 45 and 60).
- Unknown keys → `ValueError`.

## Laptop check
```bash
pytest -q tests/test_gt.py tests/test_imports.py
```

## Lab check
```bash
python -c "
from evaluation.gt import scene_gt
g = scene_gt('figurines'); stem = sorted(g)[0]; hw, objs = g[stem]
print(len(g), 'frames', hw, len(objs), 'categories', {k: int(v.mask.sum()) for k, v in list(objs.items())[:5]})"
```
Expected: 4 frames for figurines; the H×W matches the images (VERIFY; if not, note it: `eval_3d` renders at GT size); non-empty masks.

## Done when
- [ ] Tests pass; the lab check parses the real labels

## Findings / Blockers
