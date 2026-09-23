# T-A08 — FastAPI server, Phase A endpoints + static web app

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-A01, T-A06 |
| Requirements | FR-A8, NFR-7 |
| May edit 06-contracts.md | no |

## Goal
`uvicorn server.app:app` serves:
- `/api/health`, `/api/scenes`, `/api/scenes/{id}` and `/api/scenes/{id}/asset` (C12);
- the built Nuxt app at `/`, with SPA fallback.

## Background
- The browser downloads the scene PLY once from `/api/scenes/{id}/asset`.
- Scenes are *discovered* by looking for `scenes/*/web/manifest.json`; there is no database.
- **Security (NFR-7):**
  - never build file paths from raw request strings: only accept a `scene_id` that is in the discovered list;
  - bind to `127.0.0.1` (the tailnet reaches it through `tailscale serve`).
- The Nuxt build (`web/.output/public`) is a set of static files. Client-side routes like `/scene/figurines` don't exist as files, so unknown non-API paths must return `200.html` (SPA fallback).

## Read first
1. `docs/spec/06-contracts.md` §C5, §C12
2. `docs/spec/07-phase-a.md` §9
3. `pipeline/config.py`, `pipeline/plyio.py`

## Files
| Action | Path |
|---|---|
| create | `server/app.py` |
| create | `tests/test_app.py` |

## Provenance
NEW (FastAPI).

## Interface
```python
def discover_scenes() -> dict[str, Path]: ...        # {scene_id: scene_dir} for scenes_root()/*/web/manifest.json
def discover_variants(scene_path: Path) -> list[dict]: ...   # [{"variant": v, "seeds": [0,1,2]}] where saga/seed*/query_index.pt exists
def create_app(web_dir: Path | None) -> FastAPI: ...
app = create_app(REPO / "web" / ".output" / "public")
```

## Steps
1. Routes inside `create_app`:
   - `GET /api/health` → `{"ok": True, "gpu": torch.cuda.is_available(), "fake": os.environ.get("PS_FAKE") == "1" or not gpu}`. Import torch inside the handler.
   - `GET /api/scenes` → the list described in C12. Each item: `scene_id`, `title`, `num_gaussians`, `asset_url` = `/api/scenes/{id}/asset`, `metrics_3dgs`, `variants`.
   - `GET /api/scenes/{scene_id}` → the manifest dict + `asset_url` + `variants`. Unknown id → 404.
   - `GET /api/scenes/{scene_id}/asset` → `FileResponse(scene/"web"/manifest["asset"]["file"], media_type="application/octet-stream")`.
2. Static app, only if `web_dir` exists:
   - `app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")` **after** all API routes;
   - add an exception handler for `starlette.exceptions.HTTPException` with status 404 whose path does **not** start with `/api`: return `FileResponse(web_dir/"200.html")` if it exists. Otherwise keep the default JSON 404.
3. Uses `pipeline.config.scenes_root()`, so tests can set `PS_SCENES_DIR`.

## Tests (`tests/test_app.py`, `fastapi.testclient.TestClient`)
Setup (a helper function in the test file):
- a tmp scenes dir with scene `t1`;
- `web/manifest.json` (minimal C5 fields);
- `web/scene.ply` written with `plyio.write_gaussians_ply` (10 Gaussians);
- `monkeypatch.setenv("PS_SCENES_DIR", tmp)`.

Assertions:
- `/api/health` → 200, `ok` true.
- `/api/scenes` → one item with `scene_id == "t1"` and `variants == []`.
- `/api/scenes/t1/asset` → bytes equal to the file.
- `/api/scenes/nope` → 404; `/api/scenes/..%2Fetc/asset` → 404.
- SPA: with `create_app(tmp_web)`, where `tmp_web` contains `index.html` and `200.html` ("SPA"), `GET /scene/t1` returns the `200.html` content; `GET /api/unknown` stays a JSON 404.

## Laptop check
```bash
pytest -q tests/test_app.py tests/test_imports.py
```

## Lab check
```bash
conda activate ps && cd ~/nvs && (uvicorn server.app:app --host 127.0.0.1 --port 8000 &) && sleep 3
curl -s localhost:8000/api/health; curl -s localhost:8000/api/scenes | head -c 400; echo
curl -sI localhost:8000/api/scenes/ramen/asset | head -3; kill %1 2>/dev/null || pkill -f "uvicorn server.app"
```
Expected: health JSON; the ramen scene listed; the asset HEAD returns 200 with a large `content-length`.

## Done when
- [ ] Tests pass; the lab curl checks pass

## Findings / Blockers
- ASSUMPTION: `scene_id` in `/api/scenes` items is the scene directory name (the id the routes accept), not re-read from the manifest; for exported scenes they are equal (C3, C5).
- ASSUMPTION: `discover_variants` is implemented now (Phase A scenes have no `variants/`, so it returns `[]`); seed dirs without an integer suffix are ignored.
- Config is loaded once at import (`CFG`); `scenes_root(CFG)` still honours `PS_SCENES_DIR` on every call, so tests set it with `monkeypatch`.
- `..%2Fetc` never reaches the filesystem: the id is looked up in the discovered dict first, so any id not found → 404.
- Laptop: `pytest -q tests/test_app.py tests/test_imports.py` passes; full `pytest -q` green. Starlette warns that `httpx` in `TestClient` is deprecated (harmless, no new dependency added).
