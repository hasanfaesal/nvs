# T-B07 — V3 masks: run AutoSeg-SAM2 and convert its tracks to SAGA format

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-B05 (`resize_masks_like_saga`), T-B06 (output format in its Findings) |
| Requirements | FR-B6 |
| May edit 06-contracts.md | no |

## Goal
`python -m pipeline masks --scene <id> --variant sam2_track_k<K>`:
1. runs the AutoSeg-SAM2 fork on the variant's ordered train frames, for levels `large` and `middle`, with `--detect_stride K --detector sam2`;
2. merges the levels, removes duplicate tracks, and writes `sam_masks/<stem>.pt` (C7) plus `track_ids/<stem>.json`.

## Background
AutoSeg-SAM2 gives each tracked object an ID that persists across frames. SAGA only needs per-frame mask stacks, so we flatten the tracks into frames. We also keep the IDs, for:
- the pseudo-label viewer (same object = same colour);
- the stretch cross-view loss.

Running two granularity levels (`large`, `middle`) gives SAGA both whole objects and parts, like SAM "everything" does. Segment-then-Splat ran it the same way.
- **Duplicate tracks:** the same object found at both levels, or twice. They are removed with Segment-then-Splat's `remove_overlapping_masks` logic (IoU > 0.5), which we copy.
- **Frame names:** SAM 2 needs frames named `0.jpg, 1.jpg…` (or zero-padded), so we build a folder of symlinks.

## Read first
1. `docs/spec/08-phase-b.md` §3.4
2. `docs/spec/06-contracts.md` §C7
3. `docs/spec/tasks/T-B06-autoseg-sam2-fork-patch.md`, **Findings** (the exact flags and output format)
4. Segment-then-Splat: `helpers/preprocess_mask.py::remove_overlapping_masks` (the COPY source), https://github.com/luyr/Segment-then-Splat
5. `pipeline/masks_sam2_frame.py` (`resize_masks_like_saga`)

## Files
| Action | Path |
|---|---|
| create | `pipeline/masks_sam2_track.py` |
| create | `tests/test_masks_sam2_track.py` |

## Provenance
- WRAP of the AutoSeg-SAM2 fork's `auto-mask-batch.py`.
- COPY of Segment-then-Splat `remove_overlapping_masks` (MIT), with this header:
  ```python
  # Source: https://github.com/luyr/Segment-then-Splat @ <sha>, helpers/preprocess_mask.py :: remove_overlapping_masks
  # License: MIT. Changes: operates on our {track_id: {frame: mask}} dict; threshold from config.
  ```
- The converter is NEW.

## Interface
```python
Tracks = dict[int, dict[int, "np.ndarray"]]        # global_track_id -> {frame_index: bool HxW}
def prepare_frames(vdir: Path) -> tuple[Path, list[str]]: ...           # autoseg_raw/frames/00000.jpg… symlinks, names in order
def build_command(frames_dir: Path, out_dir: Path, level: str, k: int, cfg: dict) -> list[str]: ...
def load_tracks(level_dir: Path, level_index: int) -> Tracks: ...       # per T-B06 Findings; id = level_index*10000 + local_id
def remove_overlapping_tracks(tracks: Tracks, iou_thresh: float) -> Tracks: ...   # COPY-adapted
def write_saga_masks(tracks: Tracks, names: list[str], vdir: Path, h: int, w: int, min_area: int) -> dict: ...
def run(scene_id: str, k: int, force: bool = False) -> None: ...
```

## Steps
1. `prepare_frames`:
   - names = `sorted(os.listdir(vdir/"images"))`;
   - symlink `autoseg_raw/frames/{i:05d}.jpg` → the resolved image;
   - write `autoseg_raw/frames.json` with the names.
2. For each `level` in `cfg["autoseg"]["levels"]`: `run_stage(scene_id, f"autoseg_{level}", build_command(...), cwd=REPO/"third_party/AutoSeg-SAM2", variant=v)`, with flags exactly as recorded in T-B06 plus `--detect_stride K --batch_size <cfg> --detector sam2`.
3. `load_tracks` for each level; merge the dicts (the IDs don't collide thanks to the offset).
4. `remove_overlapping_tracks`:
   - for each pair of tracks, IoU = Σ_frames |a∧b| / Σ_frames |a∨b| over the frames where either is present;
   - if > threshold, drop the track with the smaller total area;
   - follow the copied function's logic, adapted.
5. `write_saga_masks`. For each frame index t with name n:
   - collect `(id, mask)` for the tracks with `mask.sum() >= min_area` (full-res pixels, `cfg["masks"]["amg"]["min_mask_region_area"]`);
   - `resize_masks_like_saga`;
   - save `sam_masks/<stem>.pt` and `track_ids/<stem>.json = {"ids": [...]}` in the same order; empty frames → `[0,h,w]` and `{"ids": []}`;
   - return statistics: tracks per level, tracks kept, mean track length, masks per frame.
6. `run`: skip if `masks_done(vdir)` and not `force`. Print the statistics and add them to Findings on the lab.

## Tests (synthetic, CPU)
- `remove_overlapping_tracks`: track A (a 10×10 square in frames 0–2) and track B (the same square shifted 1 px) have IoU > 0.5, so the smaller one is removed; track C (disjoint) is kept.
- `write_saga_masks` with 3 frames and 2 tracks (one missing from frame 1):
  - frame 1's `.pt` has M = 1 and its JSON `ids` has length 1;
  - the shapes are `(M, h, w)`, bool;
  - `track_ids` lengths equal M.
- `prepare_frames` creates `00000.jpg…` symlinks in sorted-name order.

## Laptop check
```bash
pytest -q tests/test_masks_sam2_track.py tests/test_imports.py
```

## Lab check
```bash
python -m pipeline variant --scene ramen --variant sam2_track_k10 --seeds 0 1 2
python -m pipeline masks --scene ramen --variant sam2_track_k10 && python -m pipeline masks --scene ramen --variant sam2_track_k10 --check
```
Expected:
- all train frames covered; shape and dtype ok;
- the printed statistics are plausible (tracks spanning several frames);
- every AutoSeg stage peaks < 14 GB in `stages.jsonl`.

## Done when
- [ ] Tests pass; V3 masks + track IDs exist for ramen; the statistics are recorded in Findings

## Findings / Blockers
