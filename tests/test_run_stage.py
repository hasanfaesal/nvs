"""Tests for pipeline/run_stage.py."""
import json
import sys

import pytest

from pipeline.run_stage import run_stage


def _log_lines(tmp_path):
    return [json.loads(l) for l in (tmp_path / "s1" / "logs" / "stages.jsonl").read_text().splitlines()]


def test_run_stage_success_logs_one_line(tmp_path, monkeypatch):
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path))
    rec = run_stage("s1", "hello", [sys.executable, "-c", "print('hi')"])
    assert rec["returncode"] == 0 and rec["seconds"] >= 0
    lines = _log_lines(tmp_path)
    assert len(lines) == 1 and lines[0]["stage"] == "hello"
    for key in ("variant", "seed", "cmd", "peak_vram_mb", "baseline_vram_mb", "started_utc", "git_sha"):
        assert key in lines[0]


def test_run_stage_failure_raises_and_logs(tmp_path, monkeypatch):
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path))
    with pytest.raises(RuntimeError, match="code 3"):
        run_stage("s1", "boom", [sys.executable, "-c", "import sys; sys.exit(3)"])
    assert _log_lines(tmp_path)[-1]["returncode"] == 3
