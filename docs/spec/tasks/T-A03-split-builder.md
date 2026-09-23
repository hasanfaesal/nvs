# T-A03 — Train/test split builder (`split.json`)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A02 |
| Requirements | FR-A4 |
| May edit 06-contracts.md | no |

## Goal
`python -m pipeline split --scene <id>` writes a deterministic `scenes/<id>/split.json` (C4):
- every 8th frame and **all annotated frames** are test (held out);
- mis-registered outlier cameras are excluded.

## Background
Held-out evaluation needs frames that no model ever trained on. LangSplat's labels are on specific frames (e.g. figurines `frame_00041`), so those frames must be in the test set, together with every 8th frame (the usual 3DGS convention, used for PSNR).
- An **outlier camera** is a frame COLMAP placed absurdly far away: figurines has one about 42× the orbit radius away. Training on it adds floaters, so it is excluded from both lists.
- Everything downstream (gsplat, SAGA variant dirs, evaluation) reads this one file.

## Read first
1. `docs/spec/06-contracts.md` §C4
2. `docs/spec/07-phase-a.md` §4
3. `pipeline/colmap_io.py`

## Files
| Action | Path |
|---|---|
| create | `pipeline/split.py` |
| modify | `pipeline/cli.py`: add `split` |
| create | `tests/test_split.py` |

## Provenance
NEW.

## Interface
```python
def outlier_cameras(centers: np.ndarray, names: list[str], factor: float) -> set[str]: ...
def make_split(names: list[str], annotated: set[str], every: int, excluded: set[str]) -> dict: ...
def build_split(scene_id: str, force: bool = False) -> Path: ...    # reads source/, writes split.json
```

## Steps
1. `outlier_cameras`:
   - `med = np.median(centers, 0)`; `d = np.linalg.norm(centers - med, axis=1)`;
   - return the names where `d > factor * np.median(d)`;
   - if `np.median(d) == 0`, return an empty set.
2. `make_split`: implement the C4 rule exactly. The returned dict has the keys `every`, `train`, `test`, `annotated`, `excluded`, `rule`, and sorted lists. `annotated` keeps only names that are also in `names` and not excluded.
3. `build_split`:
   - `cams = load_cameras(source/sparse/0)`; `names = sorted(cams)`; `centers = [camera_center(c) for c in cams.values()]`;
   - `annotated` = image names whose stem matches a `source/labels/*.json` stem;
   - `every` and `factor` come from `cfg["split"]`;
   - write `split.json` with `"scene_id"` added, `indent=1`;
   - print `train / test / annotated / excluded` counts, and the excluded names.
4. Skip if the file exists and not `force`.

## Tests
- 20 names, `every=8`, no annotated/excluded: test = indices 0, 8, 16; train = the other 17.
- An annotated name at index 3 is in test and not in train.
- An excluded name is in neither list, and indices are computed **after** exclusion.
- Train ∩ test = ∅; `annotated ⊆ test`; running twice gives identical output.
- `outlier_cameras`: 10 centers on a unit circle plus 1 at distance 50 → only that one is returned (factor 10).

## Laptop check
```bash
pytest -q tests/test_split.py tests/test_imports.py
```

## Lab check
```bash
for s in figurines ramen waldo_kitchen teatime; do python -m pipeline split --scene $s; done
python -c "import json; d=json.load(open('scenes/figurines/split.json')); print(len(d['train']), len(d['test']), d['annotated'], d['excluded'])"
```
Expected: the annotated counts match T-007 (4 / 7 / 5 / 6); figurines excludes ≥ 1 camera; the test sets hold about 13–15% of frames.

## Done when
- [ ] Tests pass; 4 split files exist on the lab

## Findings / Blockers
Laptop, 2026-09-24: `pytest -q` is green (6 tests in `tests/test_split.py`). The functions were also run read-only on the laptop copy of LERF-OVS (`data/raw/lerf_ovs`, `factor=10`, `every=8`). No `scenes/` files were written.

| Scene | train | test | test share | annotated | excluded |
|---|---|---|---|---|---|
| figurines | 258 | 40 | 13.4% | 4 | `frame_00162.jpg` (41.7× median distance; next highest 1.6×) |
| ramen | 109 | 22 | 16.8% | 7 | — (max 1.9×) |
| waldo_kitchen | 159 | 28 | 15.0% | 5 | — (max 2.7×) |
| teatime | 150 | 27 | 15.3% | 6 | — (max 1.8×) |

- ramen's test share (16.8%) is above the expected 13–15%. It is a small scene (131 frames), so its 7 annotated frames add more on top of every 8th frame. This is expected, not a bug.
- ASSUMPTION: `excluded` in `split.json` lists every outlier camera name, including any that are also annotated. A labelled outlier frame is dropped from `annotated` and from both lists, following the card's step 2. There were none in LERF-OVS.
- VERIFY on lab: the lab check should reproduce the numbers above after `ingest`.
