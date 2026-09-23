# T-B03 — Variant builder: one SAGA source dir per mask source

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-B02, T-A03 |
| Requirements | FR-B3 |
| May edit 06-contracts.md | no |

## Goal
`python -m pipeline variant --scene <id> --variant <v> [--seeds 0 1 2]` builds:
- `scenes/<id>/variants/<v>/`, holding symlinks to the **train images only** plus `sparse`;
- one SAGA model dir per seed, with `cfg_args` and the linked RGB model (C3, C8).

## Background
SAGA reads a fixed folder layout from one "source path". A separate variant dir per mask source (`sam`, `sam2_frame`, `sam2_track_k10`, …) lets the same unmodified SAGA scripts run three times without overwriting each other.
- Because `images/` holds only the train images, and the patched loader (P-SAGA-2) skips missing images, **test views never reach SAM, SAM 2 or SAGA**. That is the held-out protocol.
- **Relative** symlinks keep the tree movable.

## Read first
1. `docs/spec/06-contracts.md` §C2, §C3, §C8
2. `docs/spec/08-phase-b.md` §2.2
3. `pipeline/saga_import.py` (`cfg_args_text`)

## Files
| Action | Path |
|---|---|
| create | `pipeline/variant.py` |
| modify | `pipeline/cli.py`: add `variant` |
| create | `tests/test_variant.py` |

## Provenance
NEW.

## Interface
```python
VARIANT_RE = re.compile(r"^(sam|sam2_frame|sam2_track_k\d+)(_xview)?$")
def variant_dir(scene_id: str, variant: str) -> Path: ...
def make_variant(scene_id: str, variant: str, seeds: list[int], force: bool = False) -> Path: ...
```

## Steps
1. Validate `variant` with `VARIANT_RE`, else `ValueError`.
2. `vdir/images/`: for each name in `split["train"]`, create a symlink `vdir/images/<name>` → `os.path.relpath(source/images/<name>, vdir/images)`, unless it exists. Remove any symlink in `vdir/images` whose name isn't in train (keeps it correct after a re-split).
3. `vdir/sparse` → relative symlink to `source/sparse`.
4. For each seed k:
   - `sd = vdir/"saga"/f"seed{k}"`; `(sd/"point_cloud").mkdir(parents=True)`;
   - `sd/point_cloud/iteration_30000` → relative symlink to `saga_scene/point_cloud/iteration_30000`;
   - write `sd/"cfg_args"` with `cfg_args_text(sd, vdir)`.
5. Never delete masks, features or training outputs. With `force`, only recreate the links and `cfg_args`.
6. Print: variant, number of train images linked, seeds.

## Tests (tmp scene: `source/images` with 4 files, `source/sparse/0/`, `split.json` with 3 train and 1 test, `saga_scene/point_cloud/iteration_30000/scene_point_cloud.ply`)
- `make_variant("t", "sam", [0, 1])` →
  - `images/` has exactly the 3 train names, and `Path.resolve()` of each points into `source/images`;
  - `sparse` resolves to `source/sparse`;
  - `seed0/point_cloud/iteration_30000/scene_point_cloud.ply` exists through the link;
  - `cfg_args` evals (as in T-B02) with `source_path == str(vdir.resolve())`.
- A second call is idempotent (no error).
- `make_variant("t", "bad name", [0])` raises `ValueError`.

## Laptop check
```bash
pytest -q tests/test_variant.py tests/test_imports.py
```

## Lab check
```bash
python -m pipeline variant --scene ramen --variant sam --seeds 0 1 2
python -c "
import sys, json; sys.path.insert(0,'third_party/SegAnyGAussians')
from scene.dataset_readers import readColmapSceneInfo
i = readColmapSceneInfo('scenes/ramen/variants/sam', 'images', False)     # VERIFY the signature
s = json.load(open('scenes/ramen/split.json')); print(len(i.train_cameras), len(s['train']))"
```
Expected: both numbers equal, and the patched loader prints `skipped <len(test)+len(excluded)> cameras`.

## Done when
- [ ] Tests pass; SAGA sees exactly the train cameras on the lab

## Findings / Blockers
