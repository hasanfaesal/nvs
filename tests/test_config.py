"""Tests for pipeline/config.py."""
import pytest

from pipeline.config import load_config, scene_dir, validate_scene_id


def test_load_config_has_top_level_keys():
    cfg = load_config()
    for key in ("paths", "envs", "gsplat", "masks", "saga", "query", "scenes"):
        assert key in cfg
    assert "figurines" in cfg["scenes"]


@pytest.mark.parametrize("bad", ["../x", "", "Abc", "a-b", "a" * 41])
def test_validate_scene_id_rejects(bad):
    with pytest.raises(ValueError):
        validate_scene_id(bad)


def test_validate_scene_id_accepts():
    assert validate_scene_id("desk_01") == "desk_01"


def test_scene_dir_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("PS_SCENES_DIR", str(tmp_path))
    assert scene_dir("abc") == tmp_path / "abc"
