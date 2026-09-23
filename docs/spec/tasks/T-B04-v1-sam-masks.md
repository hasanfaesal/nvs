# T-B04 — V1 masks (SAM v1, SAGA's script) + `masks` dispatcher + mask checker

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-B03 |
| Requirements | FR-B4 |
| May edit 06-contracts.md | no |

## Goal
- `python -m pipeline masks --scene <id> --variant sam` produces V1 masks by running SAGA's own `extract_segment_everything_masks.py`.
- The `masks` command dispatches to the right module by variant name.
- `--check` validates any variant's masks against C7.

## Background
V1 is SAGA's original supervision: SAM v1 ViT-H "segment everything" on each frame independently, with SAGA's hardcoded thresholds. We **wrap** the script unchanged (after the T-B01 fixes).
- SAGA scripts are always launched as `python <script>` with `cwd` = the SAGA root. They import local modules, and in the fallback case `python` must be the `saga` env's Python, reached through `run_stage(..., saga=True)`.
- Don't use `sys.executable` for SAGA scripts.

## Read first
1. `docs/spec/06-contracts.md` §C7
2. `docs/spec/08-phase-b.md` §3.1–§3.2
3. `pipeline/run_stage.py`, `pipeline/variant.py`
4. Fork: `third_party/SegAnyGAussians/extract_segment_everything_masks.py` (argparse)

## Files
| Action | Path |
|---|---|
| create | `pipeline/masks_sam.py` |
| modify | `pipeline/variant.py`: add `masks_done`, `check_masks`, `run_masks` (the dispatcher) |
| modify | `pipeline/cli.py`: add `masks` (calls `variant.run_masks`, or `check_masks` with `--check`) |
| create | `tests/test_masks_common.py` |

## Provenance
- `masks_sam.py`: WRAP of the SAGA fork's `extract_segment_everything_masks.py`.
- `check_masks`: NEW.

## Interface
```python
# pipeline/masks_sam.py
SAGA = REPO / "third_party" / "SegAnyGAussians"
def build_command(vdir: Path, cfg: dict) -> list[str]: ...
def run(scene_id: str, variant: str = "sam", force: bool = False) -> None: ...

# pipeline/variant.py
def masks_done(vdir: Path) -> bool: ...          # every images/<name> has sam_masks/<stem>.pt
def check_masks(vdir: Path) -> dict: ...          # {"frames", "missing", "shape_ok", "dtype_ok", "masks_per_frame": {"mean","min","max"}, "hw": [h, w]}
def run_masks(scene_id: str, variant: str, force: bool = False) -> None: ...   # the dispatcher (used by the CLI and by `all`)
```
- **Dispatch rules** in `run_masks`, with lazy imports inside the function:
  - `sam` → `masks_sam.run`;
  - `sam2_frame` → `masks_sam2_frame.run` (T-B05);
  - `sam2_track_k<K>` → `masks_sam2_track.run(scene_id, K)` (T-B07);
  - a module that doesn't exist yet raises `NotImplementedError("… (T-B05/T-B07)")`.
- **CLI:** `masks --scene ID --variant V [--force] [--check]`.

## Steps
1. `build_command`:
   `["python", "extract_segment_everything_masks.py", "--image_root", str(vdir.resolve()), "--sam_checkpoint_path", str((REPO/cfg["masks"]["sam_ckpt"]).resolve()), "--sam_arch", cfg["masks"]["sam_arch"], "--downsample", str(cfg["masks"]["downsample"]), "--downsample_type", "mask"]`
2. `run`: skip if `masks_done(vdir)` and not `force`; otherwise `run_stage(scene_id, "masks_sam", cmd, cwd=SAGA, variant=variant, saga=True)`.
3. `check_masks`:
   - H, W from the first image (`cv2.imread`); expected `(h, w) = (H // down, W // down)`;
   - load each `.pt` with `map_location="cpu"` and check `dtype == torch.bool`, `ndim == 3`, `shape[1:] == (h, w)`;
   - collect the M statistics.

## Tests
- `check_masks` on a tmp variant with 2 JPEGs of 64×48 and masks of `bool [3,12,16]` → all ok, `masks_per_frame.mean == 3`. A wrong dtype → `dtype_ok` false; a missing file → counted in `missing`.
- `build_command` contains `--downsample_type mask` and absolute paths.
- `run_masks("s", "sam2_track_k5")` calls the track module's `run` with K = 5 (monkeypatch the run functions); `run_masks("s", "sam")` calls `masks_sam.run`.

## Laptop check
```bash
pytest -q tests/test_masks_common.py tests/test_imports.py
```

## Lab check
```bash
python -m pipeline masks --scene ramen --variant sam && python -m pipeline masks --scene ramen --variant sam --check
tail -1 scenes/ramen/logs/stages.jsonl
```
Expected: `frames == len(train)`, 0 missing, shape and dtype ok, about 20–150 masks per frame, peak VRAM < 14 GB.

## Done when
- [ ] Tests pass; V1 masks exist for ramen

## Findings / Blockers
