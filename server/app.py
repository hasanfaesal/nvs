"""FastAPI server, Phase A endpoints + static web app (NEW). See C12."""
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from pipeline.config import REPO, load_config, scenes_root

CFG = load_config()


def discover_scenes() -> dict[str, Path]:
    """{scene_id: scene_dir} for every scenes_root()/*/web/manifest.json."""
    return {m.parents[1].name: m.parents[1] for m in sorted(scenes_root(CFG).glob("*/web/manifest.json"))}


def discover_variants(scene_path: Path) -> list[dict]:
    """[{"variant": v, "seeds": [...]}] for variants with saga/seed*/query_index.pt (empty in Phase A)."""
    out = []
    for vdir in sorted((scene_path / "variants").glob("*")):
        seeds = sorted(int(p.parent.name[4:]) for p in vdir.glob("saga/seed*/query_index.pt")
                       if p.parent.name[4:].isdigit())
        if seeds:
            out.append({"variant": vdir.name, "seeds": seeds})
    return out


def _scene(scene_id: str) -> tuple[Path, dict]:
    # NFR-7: only ids from the discovered list ever become paths.
    scene = discover_scenes().get(scene_id)
    if scene is None:
        raise HTTPException(404, f"unknown scene {scene_id!r}")
    manifest = json.loads((scene / "web" / "manifest.json").read_text())
    manifest["asset_url"] = f"/api/scenes/{scene_id}/asset"
    manifest["variants"] = discover_variants(scene)
    return scene, manifest


class SpaStaticFiles(StaticFiles):
    """Static web app; unknown non-API paths get 200.html with status 200 (client-side routes).

    Must live here, not in an exception handler: `nuxi generate` writes 404.html, which
    StaticFiles(html=True) would otherwise serve itself with status 404.
    """

    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
            if response.status_code != 404:
                return response
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
        spa = Path(self.directory) / "200.html"
        if scope["path"].startswith("/api") or not spa.is_file():
            raise StarletteHTTPException(404)
        return FileResponse(spa)


def create_app(web_dir: Path | None) -> FastAPI:
    app = FastAPI()

    @app.get("/api/health")
    def health() -> dict:
        import torch

        gpu = torch.cuda.is_available()
        return {"ok": True, "gpu": gpu, "fake": os.environ.get("PS_FAKE") == "1" or not gpu}

    @app.get("/api/scenes")
    def scenes() -> list[dict]:
        keys = ("scene_id", "title", "num_gaussians", "asset_url", "metrics_3dgs", "variants")
        out = []
        for sid in discover_scenes():
            m = _scene(sid)[1]
            out.append({k: m.get(k) for k in keys} | {"scene_id": sid})
        return out

    @app.get("/api/scenes/{scene_id}")
    def scene(scene_id: str) -> dict:
        return _scene(scene_id)[1]

    @app.get("/api/scenes/{scene_id}/asset")
    def asset(scene_id: str) -> FileResponse:
        scene_path, m = _scene(scene_id)
        return FileResponse(scene_path / "web" / m["asset"]["file"], media_type="application/octet-stream")

    if web_dir is not None and web_dir.is_dir():
        app.mount("/", SpaStaticFiles(directory=web_dir, html=True), name="web")
    return app


app = create_app(REPO / "web" / ".output" / "public")
