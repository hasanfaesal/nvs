# T-B13 — API, Phase B: query, debug-render, frames, label-overlay and results endpoints

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-B12, T-A08 |
| Requirements | FR-B10, FR-B11, FR-B12, FR-B15, NFR-7 |
| May edit 06-contracts.md | no |

## Goal
`server/app.py` gains every C12 endpoint marked T-B13, with strict input validation. They are tested on the laptop through the FakeEngine and the fixture scene.

## Background
- The browser sends a text query, or a click (the camera matrices + pixel), and receives one byte per Gaussian as base64.
- The pseudo-label viewer needs the training frames and coloured mask overlays.
- **All user input is untrusted:**
  - check `scene_id`, `variant`, `seed` and `stem` against what exists on disk;
  - bound the string lengths and numbers;
  - never build a path from raw input.

## Read first
1. `docs/spec/06-contracts.md` §C12, §C13
2. `docs/spec/08-phase-b.md` §7
3. `server/app.py`, `server/query.py`

## Files
| Action | Path |
|---|---|
| modify | `server/app.py` |
| modify | `tests/test_app.py` |

## Provenance
NEW (FastAPI + pydantic).

## Interface (pydantic request models)
```python
class CameraIn(BaseModel):
    matrix_world: list[float] = Field(min_length=16, max_length=16)
    fov_y_deg: float = Field(gt=1, lt=179)
    width: int = Field(gt=0, le=8192)
    height: int = Field(gt=0, le=8192)
class TextQueryIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    variant: str
    seed: int = 0
class ClickQueryIn(BaseModel):
    variant: str; seed: int = 0; camera: CameraIn
    mesh_matrix_world: list[float] = Field(min_length=16, max_length=16)
    pixel: tuple[float, float]
    scale: float = Field(ge=0, le=1)
class RenderIn(BaseModel):
    camera: CameraIn
    mesh_matrix_world: list[float] = Field(min_length=16, max_length=16)
```

## Steps
1. A helper `_variant_or_404(scene_path, variant, seed)` checks the pair against `discover_variants(scene_path)`.
2. `POST /api/scenes/{id}/query/text`:
   - `text.strip()` must be non-empty (else 422);
   - `r = get_engine().text_query(...)`;
   - respond with the C12 `QueryResponse`: `query_id = sha1(f"{id}|{variant}|{seed}|text|{text}")`, `n`, `scores_b64 = base64.b64encode(r.scores_u8.tobytes()).decode()`, `default_threshold`, `info`, `latency_ms`, `cached = r.info.pop("cached", False)`.
3. `POST …/query/click`:
   - the pixel must lie within `[0, width) × [0, height)`, else 422;
   - `Background` → `HTTPException(409, "clicked background")`;
   - the `query_id` includes the rounded pixel and the scale.
4. `POST …/debug/render` → `Response(cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))[1].tobytes(), media_type="image/png")`.
5. `GET …/frames` → `{"frames": [Path(n).stem for n in split["train"]]}`.
6. `GET …/frames/{stem}/image`: look the stem up in the train list to get the file name, else 404; then `FileResponse(source/images/<name>)`.
7. `GET …/frames/{stem}/labels/{variant}`:
   - validate the stem, and the variant against `discover_variants`;
   - load `variants/<v>/sam_masks/<stem>.pt` (`map_location="cpu"`) and the source image;
   - upscale the masks to image size with nearest-neighbour (`cv2.resize(..., interpolation=cv2.INTER_NEAREST)`);
   - IDs: `track_ids/<stem>.json` if it exists, else `range(M)`;
   - colour `hsv(((id * 0.618034) % 1), 0.65, 0.95)`;
   - paint by descending area with alpha 0.5, then `cv2.drawContours` in white, 1 px;
   - PNG; `functools.lru_cache(maxsize=256)` on `(scene, variant, stem)`.
8. `GET /api/results` → the JSON of `results_root()/"summary.json"`, or 404.
9. The engine is fetched lazily with `get_engine()` inside handlers, so the app still imports without CUDA.

## Tests (`tests/test_app.py`; `PS_FAKE=1`, `PS_SCENES_DIR=tmp`, fixture made with `make_fixture`)
- Text query → 200; `base64` decodes to `num_gaussians` bytes; a second identical call has `cached` true.
- Unknown variant → 404; seed 5 → 404; `text` of 201 characters → 422; whitespace-only text → 422.
- Click with the T-B12 red-sphere camera (center pixel) → 200. Pixel `(500, 5)` on a 200×200 canvas → 422. The camera aimed at empty space → 409.
- Debug render → 200, the body starts with `b"\x89PNG"`.
- Frames → 5 stems; frame image → 200; labels for each fixture variant → PNG; unknown stem → 404.
- `/api/results` → 404 when the file is missing; with a tmp `summary.json` (`PS_RESULTS_DIR`), 200 and the same JSON.

## Laptop check
```bash
pytest -q tests/test_app.py tests/test_imports.py
```

## Lab check
```bash
uvicorn server.app:app --host 127.0.0.1 --port 8000 &
sleep 5; curl -s -X POST localhost:8000/api/scenes/figurines/query/text -H 'content-type: application/json' \
  -d '{"text":"<a category from the labels>","variant":"sam2_track_k10","seed":0}' | head -c 300; echo
curl -s localhost:8000/api/scenes/figurines/frames | head -c 200; echo
curl -s -o /tmp/l.png localhost:8000/api/scenes/figurines/frames/<first stem>/labels/sam2_track_k10 && file /tmp/l.png
```
Expected: JSON with `scores_b64` and a `latency_ms` < 2000; the frame list; a PNG overlay.

## Done when
- [ ] Laptop tests pass; the lab curl checks work

## Findings / Blockers
