import json

import numpy as np
from fastapi.testclient import TestClient

from pipeline.plyio import write_gaussians_ply
from server.app import create_app


def make_scene(root, scene_id="t1"):
    web = root / scene_id / "web"
    web.mkdir(parents=True)
    rng = np.random.default_rng(0)
    N = 10
    write_gaussians_ply(web / "scene.ply", rng.normal(size=(N, 3)), rng.normal(size=(N, 3)),
                        rng.normal(size=(N, 4)), rng.normal(size=N), rng.normal(size=(N, 1, 3)),
                        rng.normal(size=(N, 15, 3)))
    manifest = {"scene_id": scene_id, "title": "T1", "num_gaussians": N,
                "asset": {"file": "scene.ply", "format": "ply", "bytes": (web / "scene.ply").stat().st_size},
                "metrics_3dgs": {"psnr": 20.0}}
    (web / "manifest.json").write_text(json.dumps(manifest))
    return web / "scene.ply"


def test_api(tmp_path, monkeypatch):
    ply = make_scene(tmp_path)
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path))
    c = TestClient(create_app(None))

    r = c.get("/api/health")
    assert r.status_code == 200 and r.json()["ok"] is True

    items = c.get("/api/scenes").json()
    assert len(items) == 1
    assert items[0]["scene_id"] == "t1" and items[0]["variants"] == []
    assert items[0]["asset_url"] == "/api/scenes/t1/asset" and items[0]["num_gaussians"] == 10

    m = c.get("/api/scenes/t1").json()
    assert m["title"] == "T1" and m["asset"]["file"] == "scene.ply" and m["variants"] == []

    r = c.get("/api/scenes/t1/asset")
    assert r.status_code == 200 and r.content == ply.read_bytes()
    assert r.headers["content-type"] == "application/octet-stream"

    assert c.get("/api/scenes/nope").status_code == 404
    assert c.get("/api/scenes/..%2Fetc/asset").status_code == 404


def test_variants_listed(tmp_path, monkeypatch):
    make_scene(tmp_path)
    for v, s in [("sam", 0), ("sam", 2), ("sam2_frame", 1)]:
        d = tmp_path / "t1" / "variants" / v / "saga" / f"seed{s}"
        d.mkdir(parents=True)
        (d / "query_index.pt").write_bytes(b"")
    (tmp_path / "t1" / "variants" / "empty" / "saga" / "seed0").mkdir(parents=True)
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path))
    items = TestClient(create_app(None)).get("/api/scenes").json()
    assert items[0]["variants"] == [{"variant": "sam", "seeds": [0, 2]}, {"variant": "sam2_frame", "seeds": [1]}]


def test_spa_fallback(tmp_path, monkeypatch):
    make_scene(tmp_path / "scenes")
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path / "scenes"))
    web = tmp_path / "public"
    web.mkdir()
    (web / "index.html").write_text("INDEX")
    (web / "200.html").write_text("SPA")
    c = TestClient(create_app(web))

    assert c.get("/").text == "INDEX"
    r = c.get("/scene/t1")
    assert r.status_code == 200 and r.text == "SPA"
    r = c.get("/api/unknown")
    assert r.status_code == 404 and r.json() == {"detail": "Not Found"}
    assert c.get("/api/scenes/t1").json()["scene_id"] == "t1"
