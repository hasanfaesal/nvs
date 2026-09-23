# T-B08 — SAGA stage wrappers (scale, CLIP, contrastive training) + the `all` command

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-B04 |
| Requirements | FR-B1, FR-B2, FR-B7, NFR-10 |
| May edit 06-contracts.md | no |

## Goal
- `python -m pipeline saga --scene <id> --variant <v> --stage scale|clip|train [--seed k]` runs SAGA's three scripts on a variant.
- `python -m pipeline all --scene <id> --variant <v> --seeds 0 1 2` runs every missing Phase B step for that variant, in order.

## Background
SAGA's three stages (`08-phase-b.md` §4):
- `get_scale.py` gives each mask a 3D size (it needs the RGB model to render depth);
- `get_clip_features.py` gives each mask a CLIP embedding;
- `train_contrastive_feature.py` learns a 32-D affinity feature per Gaussian.

The first two are **per variant**; training is **per seed**. All three are WRAPped unchanged (fork-patched), launched as `python <script>` with `cwd` = the SAGA root and `saga=True` (legacy-env fallback). `MPLBACKEND=Agg` keeps any matplotlib use headless.

## Read first
1. `docs/spec/08-phase-b.md` §4
2. `docs/spec/06-contracts.md` §C3, §C8, §C16
3. `pipeline/masks_sam.py` (same WRAP pattern), `pipeline/variant.py`
4. Fork: argparse blocks of `get_scale.py`, `get_clip_features.py`, `train_contrastive_feature.py` (VERIFY the flag names: `-m` vs `--model_path`, `-s`)

## Files
| Action | Path |
|---|---|
| create | `pipeline/saga_stages.py` |
| modify | `pipeline/cli.py`: add `saga` and `all` |
| create | `tests/test_saga_stages.py` |

## Provenance
WRAP of the SAGA fork's scripts.

## Interface
```python
def scale_cmd(vdir: Path) -> list[str]: ...                 # ["python","get_scale.py","--image_root",vdir,"--model_path",vdir/"saga/seed0"]
def clip_cmd(vdir: Path) -> list[str]: ...                  # ["python","get_clip_features.py","--image_root",vdir]
def train_cmd(vdir: Path, seed: int, cfg: dict) -> list[str]: ...   # ["python","train_contrastive_feature.py","-m",seed_dir,"-s",vdir,"--iterations",…,"--num_sampled_rays",…,"--seed",seed]
def stage_done(vdir: Path, stage: str, seed: int | None, cfg: dict) -> bool: ...
def run_saga(scene_id: str, variant: str, stage: str, seed: int | None = None, force: bool = False) -> None: ...
def run_all(scene_id: str, variant: str, seeds: list[int], force: bool = False) -> None: ...
```

## Steps
1. All paths absolute (`resolve()`).
2. `stage_done`:
   - `scale`: every stem in `sam_masks/` has `mask_scales/<stem>.pt`;
   - `clip`: the same with `clip_features/`;
   - `train`: `saga/seed<k>/point_cloud/iteration_<cfg.saga.iterations>/scale_gate.pt` **and** `q_trans.joblib` exist.
3. `run_saga`:
   - `os.environ["MPLBACKEND"] = "Agg"`;
   - skip if done and not `force`;
   - otherwise `run_stage(scene_id, f"saga_{stage}", cmd, cwd=SAGA, variant=variant, seed=seed, saga=True)`.
4. `run_all(scene, v, seeds)`, in order, each step skip-if-done:
   1. `saga_import.import_scene`;
   2. `variant.make_variant(v, seeds)`;
   3. `variant.run_masks(scene, v)` (the dispatcher from T-B04);
   4. `scale`; 5. `clip`;
   6. `train` for each seed;
   7. then, **if `pipeline.query_index` exists** (T-B11), `build_index` per seed (a `try: import … except ImportError`). Leave a comment.
5. CLI: `saga --scene --variant --stage {scale,clip,train} [--seed K] [--force]`; `all --scene --variant --seeds K [K ...] [--force]`.

## Tests
- `train_cmd(Path("/v"), 2, cfg)` contains `--seed 2`, `--iterations 10000`, `--num_sampled_rays 1000`, `-m /v/saga/seed2`.
- `stage_done` with a tmp variant: `scale` is false with 2 masks and 1 scale, true with 2 and 2; `train` needs both files.
- `run_all` with every step monkeypatched to append to a list → the order is import, variant, masks, scale, clip, train(0), train(1).

## Laptop check
```bash
pytest -q tests/test_saga_stages.py tests/test_imports.py
```

## Lab check
```bash
python -m pipeline all --scene ramen --variant sam --seeds 0
ls scenes/ramen/variants/sam/mask_scales | wc -l; ls scenes/ramen/variants/sam/clip_features | wc -l
ls scenes/ramen/variants/sam/saga/seed0/point_cloud/iteration_10000/
python - <<'EOF'
import json
for l in open("scenes/ramen/logs/stages.jsonl"):
    r = json.loads(l)
    if r["stage"].startswith("saga_"):
        print(r["stage"], r["seed"], round(r["seconds"]), (r["peak_vram_mb"] or 0) - (r["baseline_vram_mb"] or 0))
EOF
```
Expected:
- the scale and CLIP counts equal the mask count;
- `contrastive_feature_point_cloud.ply`, `scale_gate.pt` and `q_trans.joblib` exist;
- every VRAM delta < 14,000 MB; the training takes about 15–30 min.

## Done when
- [ ] Tests pass; one full SAGA run on ramen/sam/seed0 completes on the lab

## Findings / Blockers
