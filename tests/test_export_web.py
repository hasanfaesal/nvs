"""Tests for pipeline/export_web.py: NaN neutralization, manifest keys, phase_a VRAM."""
import torch

from pipeline.export_web import build_manifest, build_phase_a, neutralize

METRICS = {"psnr": 27.1, "ssim": 0.91, "lpips": 0.12, "lpips_net": "alex", "num_test": 41, "step": 29999}


def _splats(n: int = 10) -> dict:
    g = torch.Generator().manual_seed(0)
    return {"means": torch.randn(n, 3, generator=g), "scales": torch.randn(n, 3, generator=g),
            "quats": torch.randn(n, 4, generator=g), "opacities": torch.randn(n, generator=g),
            "sh0": torch.randn(n, 1, 3, generator=g), "shN": torch.randn(n, 15, 3, generator=g)}


def test_neutralize_fixes_bad_rows_only():
    s = _splats()
    s["means"][2, 1] = float("nan")
    s["shN"][7, 3, 2] = float("inf")
    before = {k: v.clone() for k, v in s.items()}
    assert neutralize(s) == 2
    for v in s.values():
        assert torch.isfinite(v).all()
    assert s["opacities"][2] == -20 and s["opacities"][7] == -20
    assert torch.equal(s["quats"][7], torch.tensor([1.0, 0, 0, 0]))
    assert (s["scales"][2] == -10).all() and (s["means"][7] == 0).all() and (s["shN"][2] == 0).all()
    keep = [i for i in range(10) if i not in (2, 7)]
    for k in s:
        assert torch.equal(s[k][keep], before[k][keep])


def test_manifest_has_exactly_c5_keys():
    cfg = {"scenes": {"ramen": {"title": "Ramen (LERF-OVS)", "dataset": "lerf_ovs", "demo_queries": ["bowl"]}}}
    view = {"position": [0, 0, 0], "target": [0, 0, -1], "up": [0, 1, 0], "fov_y_deg": 50.0}
    m = build_manifest("ramen", cfg, 5, "abc", 1234, view, METRICS, "deadbee")
    assert set(m) == {"scene_id", "title", "dataset", "num_gaussians", "xyz_hash", "asset", "initial_view",
                      "mesh_quaternion_xyzw", "metrics_3dgs", "demo_queries", "git_sha", "created_utc"}
    assert m["title"] == "Ramen (LERF-OVS)" and m["demo_queries"] == ["bowl"]
    assert m["mesh_quaternion_xyzw"] == [1, 0, 0, 0] and m["asset"]["bytes"] == 1234
    other = build_manifest("x", cfg, 5, "abc", 1, view, METRICS, "deadbee")
    assert other["title"] == "x" and other["demo_queries"] == []


def test_phase_a_uses_last_train_line_and_subtracts_baseline():
    log = [{"stage": "train_3dgs", "seconds": 10.0, "peak_vram_mb": 5000, "baseline_vram_mb": 100},
           {"stage": "other", "seconds": 1.0, "peak_vram_mb": 1, "baseline_vram_mb": 0},
           {"stage": "train_3dgs", "seconds": 1512.3, "peak_vram_mb": 9120, "baseline_vram_mb": 850}]
    r = build_phase_a("ramen", METRICS, 5, 3 * 2**20, log, "deadbee")
    assert r["train_peak_vram_mb"] == 9120 - 850 and r["train_seconds"] == 1512.3
    assert r["asset_mb"] == 3.0 and r["fps_lab"] is None and r["psnr"] == 27.1
    assert set(r) == {"scene_id", "psnr", "ssim", "lpips", "lpips_net", "num_test", "num_gaussians",
                      "train_seconds", "train_peak_vram_mb", "asset_mb", "fps_lab", "git_sha"}
    log[-1]["peak_vram_mb"] = None
    assert build_phase_a("ramen", METRICS, 5, 1, log, "x")["train_peak_vram_mb"] is None
