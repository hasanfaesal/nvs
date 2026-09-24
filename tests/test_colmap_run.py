"""Tests for pipeline/colmap_run.py: command building, best-model pick, global_mapper fallback."""
from pipeline import colmap_io, colmap_run
from pipeline.colmap_run import best_model, build_commands, run_colmap


def test_build_commands_sequential_mapper(tmp_path):
    cmds = build_commands(tmp_path, "colmap", "sequential", "mapper")
    assert len(cmds) == 3
    assert "--FeatureExtraction.use_gpu" in cmds[0] and "OPENCV" in cmds[0]
    assert cmds[1][1] == "sequential_matcher"
    assert cmds[2][1] == "mapper"
    assert "--Mapper.ba_global_function_tolerance=0.000001" in cmds[2]
    assert cmds[0][cmds[0].index("--image_path") + 1] == str(tmp_path / "input")


def test_build_commands_exhaustive_global(tmp_path):
    cmds = build_commands(tmp_path, "colmap", "exhaustive", "global_mapper")
    assert cmds[1][1] == "exhaustive_matcher"
    assert cmds[2][1] == "global_mapper"
    assert not any(c.startswith("--Mapper.") for c in cmds[2])


def test_best_model_most_registered(tmp_path, monkeypatch):
    for d in ("0", "1"):
        (tmp_path / d).mkdir()
    counts = {"0": 5, "1": 9}
    monkeypatch.setattr(colmap_io, "load_cameras", lambda d: dict.fromkeys(range(counts[d.name])))
    assert best_model(tmp_path) == tmp_path / "1"


def test_run_colmap_falls_back_to_global_mapper(tmp_path, monkeypatch):
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path))
    src = tmp_path / "s" / "source"
    (src / "input").mkdir(parents=True)
    for i in range(10):
        (src / "input" / f"frame_{i:05d}.jpg").touch()
    stages = []

    def fake_stage(scene_id, stage, cmd, cwd=None):
        assert cwd == src  # AGENTS §6: cwd set explicitly
        stages.append(stage)
        if cmd[1] in ("mapper", "global_mapper"):
            (src / "distorted" / "sparse" / "0").mkdir()
        if cmd[1] == "image_undistorter":
            (src / "sparse").mkdir()
            (src / "sparse" / "images.bin").touch()

    monkeypatch.setattr(colmap_run, "run_stage", fake_stage)
    # mapper registers 50% → retry; global_mapper registers 90%
    monkeypatch.setattr(colmap_io, "load_cameras",
                        lambda d: dict.fromkeys(range(9 if "colmap_global_mapper" in stages else 5)))
    out = run_colmap("s")
    assert stages == ["colmap_features", "colmap_matching", "colmap_mapper",
                      "colmap_global_mapper", "colmap_undistort"]
    assert (out / "images.bin").exists() and out == src / "sparse" / "0"
    assert run_colmap("s") == out and len(stages) == 5  # skip when done
