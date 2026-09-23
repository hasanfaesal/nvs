# T-A13 — Frame extraction from video + blur filter

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A01 |
| Requirements | FR-A2 |
| May edit 06-contracts.md | no |

## Goal
`pipeline/frames.py` turns a phone video into ~3 fps of **sharp**, sequentially numbered JPEG frames (`frame_00001.jpg` …), with the long side ≤ 1600 px.

## Background
- **Why filter:** COLMAP and 3DGS suffer badly from motion blur.
- **Sharpness score:** the variance of the Laplacian; blurry images have weak edges, so a low variance.
- **Method:** oversample the video at 6 fps, then keep the sharpest frame in each pair (≈ 3 fps), then drop frames far blurrier than typical (< 0.3 × median).
- **Why sequential names:** SAM 2 tracking (Phase B) needs frames in capture order, and our names encode that order (C2).

## Read first
1. `docs/spec/07-phase-a.md` §2
2. `docs/spec/06-contracts.md` §C2, §C6.1 (`frames`)
3. `pipeline/config.py`

## Files
| Action | Path |
|---|---|
| create | `pipeline/frames.py` |
| create | `tests/test_frames.py` |

## Provenance
NEW (ffmpeg CLI + OpenCV; no upstream code fits).

## Interface
```python
def sharpness(img_bgr: np.ndarray) -> float: ...        # var of cv2.Laplacian on gray, resized to 640 px width if wider
def select_sharp(scores: list[float], keep_every: int, min_ratio: float) -> list[int]: ...   # indices to keep, sorted
def extract_frames(video: Path, out_dir: Path, cfg: dict) -> list[Path]: ...
```

## Steps
1. `select_sharp`:
   - split the indices into consecutive windows of `keep_every` (the last window may be shorter);
   - keep the argmax of each window;
   - then drop the kept indices whose score < `min_ratio × median(kept scores)`.
2. `extract_frames`:
   1. A temp dir (`tempfile.TemporaryDirectory`).
   2. `ffmpeg -loglevel error -i VIDEO -vf "fps=<extract_fps>,scale='if(gt(iw,ih),min(<max_side>,iw),-2)':'if(gt(iw,ih),-2,min(<max_side>,ih))'" -q:v 2 TMP/%05d.jpg`, run with `subprocess.run(check=True)`. ffmpeg is on the laptop and in the lab env.
   3. Read them sorted, compute `sharpness`, then `select_sharp`.
   4. `out_dir.mkdir(parents=True, exist_ok=True)`, and write the survivors as `frame_{k:05d}.jpg` (k from 1) with `cv2.IMWRITE_JPEG_QUALITY` = `jpeg_quality`.
   5. Print `extracted N, kept K, dropped D`, and return the paths.

## Tests
- `select_sharp([1,5, 2,2, 9,1, 0.1,0.2], keep_every=2, min_ratio=0.3) == [1, 2, 4]`:
  - ties keep the **first** max (`np.argmax`), so window [2,3] keeps 2;
  - the window winners are 1, 2, 4, 7 with scores 5, 2, 9, 0.2; their median is 3.5, so the cut-off is 0.3 × 3.5 = 1.05;
  - index 7 (0.2) is dropped.
- `sharpness` of a random-noise image > the `sharpness` of the same image after `cv2.GaussianBlur(…, (15,15), 5)`.
- End to end:
  - write a 3 s, 10 fps synthetic video (`cv2.VideoWriter`, `mp4v`) of shifting random texture, 320×240, with every 4th frame blurred;
  - `extract_frames` with `max_side=200` writes ≥ 5 files named `frame_00001.jpg`…, each with a long side ≤ 200;
  - skip the test if `shutil.which("ffmpeg")` is None.

## Laptop check
```bash
pytest -q tests/test_frames.py tests/test_imports.py
```

## Lab check
Covered by T-A15 (a real phone video).

## Done when
- [x] Tests pass

## Findings / Blockers
- ASSUMPTION: `cfg` in `extract_frames` is the `frames` section of `pipeline.yaml` (T-A15 calls it with `cfg["frames"]`).
- ASSUMPTION: "dropped D" in the progress line counts frames removed by the blur cut only (window winners − kept), matching `dropped_blur` in 07-phase-a.md §2; the 1-of-`keep_every` window loss is implied by extracted vs kept.
- ASSUMPTION: status set to `done`, not `lab`: this card has no lab step of its own (Done when = tests pass); the real-video check happens in T-A15.
- Added a `RuntimeError` when ffmpeg produces no frames, so a bad video path fails with a clear message instead of an empty scene.
- Laptop check: `pytest -q tests/test_frames.py tests/test_imports.py` passes (ffmpeg present; synthetic run: extracted 18, kept 9); full `pytest -q` green.
