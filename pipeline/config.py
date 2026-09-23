"""Config loader and scene paths (NEW). See C2, C6."""
import os
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SCENE_ID_RE = re.compile(r"^[a-z0-9_]{1,40}$")


def repo_root() -> Path:
    return REPO


def load_config() -> dict:
    cfg = yaml.safe_load((REPO / "configs" / "pipeline.yaml").read_text())
    cfg["scenes"] = yaml.safe_load((REPO / "configs" / "scenes.yaml").read_text())["scenes"]
    return cfg


def _root(env: str, key: str, cfg: dict | None) -> Path:
    if os.environ.get(env):
        return Path(os.environ[env])
    return REPO / (cfg or load_config())["paths"][key]


def scenes_root(cfg: dict | None = None) -> Path:
    return _root("PS_SCENES_DIR", "scenes", cfg)


def results_root(cfg: dict | None = None) -> Path:
    return _root("PS_RESULTS_DIR", "results", cfg)


def validate_scene_id(scene_id: str) -> str:
    if not SCENE_ID_RE.match(scene_id):
        raise ValueError(f"bad scene id {scene_id!r}: must match {SCENE_ID_RE.pattern} (C2)")
    return scene_id


def scene_dir(scene_id: str, cfg: dict | None = None) -> Path:
    return scenes_root(cfg) / validate_scene_id(scene_id)
