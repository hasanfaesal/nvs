# T-A15 — Ingest from a phone video or a photo folder

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A13, T-A14 |
| Requirements | FR-A2, FR-A3 |
| May edit 06-contracts.md | no |

## Goal
`python -m pipeline ingest --scene <id> --video FILE` and `--images DIR` produce the same canonical `source/` as posed ingest (C3). The same happens when `configs/scenes.yaml` says `input_type: video` or `images`.

## Background
This connects `frames.py` (T-A13) and `colmap_run.py` (T-A14):
- **video:** frames → `source/input/` → COLMAP with the sequential matcher;
- **photos:** resized copies → `source/input/` → COLMAP with the exhaustive matcher.

Labels (for your own scenes, T-C03) are copied exactly as in posed ingest.

## Read first
1. `docs/spec/07-phase-a.md` §1.2–§1.3
2. `pipeline/ingest.py`, `pipeline/frames.py`, `pipeline/colmap_run.py`

## Files
| Action | Path |
|---|---|
| modify | `pipeline/ingest.py`: add `ingest_video`, `ingest_images`; extend `ingest_from_config` |
| modify | `pipeline/cli.py`: `--video`, `--images`, `--matcher` flags |
| modify | `tests/test_ingest.py`: add dispatch tests |

## Provenance
NEW glue.

## Interface
```python
def ingest_video(scene_id: str, video: Path, labels: Path | None = None, force: bool = False) -> Path: ...
def ingest_images(scene_id: str, images: Path, labels: Path | None = None,
                  matcher: str = "exhaustive", force: bool = False) -> Path: ...
```

## Steps
1. `ingest_video`:
   - `frames.extract_frames(video, source/"input", cfg["frames"])`;
   - `colmap_run.run_colmap(scene_id, matcher="sequential", force=force)`;
   - copy the labels;
   - print a summary.
2. `ingest_images`:
   - copy the images sorted by name to `source/input/` as `frame_{k:05d}.jpg`;
   - resize them with `cv2.INTER_AREA` if the long side > `frames.max_side`;
   - `run_colmap(scene_id, matcher=matcher)`; copy the labels.
3. Both skip if `source/sparse/0` exists and not `force`. With `force`, remove `source/` first.
4. `ingest_from_config` dispatches on `input_type` (`colmap` | `video` | `images`).
5. CLI: `ingest --scene ID (--colmap DIR | --video FILE | --images DIR) [--labels DIR] [--matcher sequential|exhaustive] [--force]`. The three input flags are mutually exclusive; with none, use the config.

## Tests (monkeypatch `extract_frames` and `run_colmap` to fakes that create the expected files)
- `ingest_video` calls the fakes in order, with `matcher="sequential"`.
- `ingest_images` renames to `frame_00001.jpg`… and uses `"exhaustive"` by default.
- `ingest_from_config` with a fake `cfg["scenes"]` entry of `input_type: video` routes to `ingest_video`.

## Laptop check
```bash
pytest -q tests/test_ingest.py tests/test_imports.py
```

## Lab check
Record a 30–60 s phone video following `07-phase-a.md` §8, and copy it to the lab PC as `data/raw/custom/test_video.mp4`.
```bash
python -m pipeline ingest --scene test_video --video data/raw/custom/test_video.mp4
python -m pipeline split --scene test_video && python -m pipeline train3dgs --scene test_video --max-steps 3000 \
  && python -m pipeline export --scene test_video
```
Expected: ≥ 80% of frames registered; the scene opens in the browser (`/scene/test_video`).

## Done when
- [ ] Tests pass; one real phone video goes end to end

## Findings / Blockers
- Laptop check passes (`pytest -q tests/test_ingest.py tests/test_imports.py`; full `pytest -q` green).
- ASSUMPTION: `--matcher` only affects `--images` (default `exhaustive`); `ingest_video` has no matcher parameter per the Interface, so video always uses `sequential`. `input_type: images` in `configs/scenes.yaml` uses `exhaustive` (no new config key).
- ASSUMPTION: photos are always re-encoded as JPEG (`frames.jpeg_quality`), so `.png` inputs become `frame_XXXXX.jpg` too; only `.jpg/.jpeg/.png` files are taken. `cv2.imread` applies the EXIF orientation, so portrait phone photos come out upright.
- Shared helper `_fresh_source` also clears a half-built `source/` (no `sparse/0`) from a failed run, so a re-run never mixes stale frames in `source/input/`. `ingest_colmap` now uses it too (same skip/force behaviour).
- VERIFY on lab: ≥ 80% of the phone video's frames register (run_colmap raises otherwise) and the scene opens at `/scene/test_video`.
