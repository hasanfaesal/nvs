"""Tests for pipeline/train_3dgs.py: command building, step-file picking, skip-if-done."""
from pathlib import Path

from pipeline import train_3dgs
from pipeline.config import load_config
from pipeline.train_3dgs import build_command, latest_step_file, train


def test_build_command_full_run():
    cmd = build_command("figurines", load_config())
    assert cmd[1:3] == ["simple_trainer.py", "mcmc"]
    assert "--no-normalize-world-space" in cmd
    assert cmd[cmd.index("--strategy.cap-max") + 1] == "1000000"
    assert cmd[cmd.index("--max_steps") + 1] == "30000"
    for flag in ("--data_dir", "--result_dir", "--split_file"):
        assert Path(cmd[cmd.index(flag) + 1]).is_absolute()
    assert cmd[cmd.index("--split_file") + 1].endswith("figurines/split.json")
    assert "--eval_steps" not in cmd


def test_build_command_smoke_run():
    cmd = build_command("figurines", load_config(), max_steps=500)
    for flag in ("--max_steps", "--eval_steps", "--save_steps", "--ply_steps"):
        assert cmd[cmd.index(flag) + 1] == "500"


def test_latest_step_file(tmp_path):
    assert latest_step_file(tmp_path, "ckpt_*_rank0.pt") is None
    for s in (6999, 29999):
        (tmp_path / f"ckpt_{s}_rank0.pt").touch()
    assert latest_step_file(tmp_path, "ckpt_*_rank0.pt").name == "ckpt_29999_rank0.pt"


def test_train_skips_then_force_wipes(tmp_path, monkeypatch):
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path))
    calls = []
    monkeypatch.setattr(train_3dgs, "run_stage", lambda *a, **k: calls.append(a))
    ckpts = tmp_path / "s" / "3dgs" / "ckpts"
    ckpts.mkdir(parents=True)
    (ckpts / "ckpt_29999_rank0.pt").touch()
    (tmp_path / "s" / "split.json").write_text("{}")
    train("s")
    assert calls == []
    train("s", max_steps=10, force=True)
    assert len(calls) == 1 and calls[0][1] == "train_3dgs"
    assert not ckpts.exists()
