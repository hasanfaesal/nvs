# T-A01 — Config loader, CLI skeleton, `run_stage` (time + VRAM logging)

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-002 |
| Requirements | FR-A7, NFR-4, NFR-10 |
| May edit 06-contracts.md | no |

## Goal
Every later card can:
- read settings with `load_config()`;
- find folders with `scene_dir()`;
- add a CLI subcommand;
- launch long GPU jobs with `run_stage()`, which logs wall time and peak VRAM to `scenes/<id>/logs/stages.jsonl`.

## Background
All defaults live in YAML (C6), never in code. `run_stage` is our single way to launch subprocesses (upstream scripts, COLMAP, gsplat):
- it streams their output to the terminal;
- it samples `nvidia-smi` every 0.5 s in a background thread to find the peak GPU memory;
- it appends one JSON line per stage (C15).

On the laptop there is no `nvidia-smi`, so the VRAM fields are `null`. When `saga=True` and `envs.saga` is set, the command is prefixed with `conda run --no-capture-output -n <env>` (T-006 fallback).

## Read first
1. `AGENTS.md`
2. `docs/spec/06-contracts.md` §C2, §C6, §C15, §C16

## Files
| Action | Path |
|---|---|
| create | `configs/pipeline.yaml` (copy C6.1 exactly) |
| create | `configs/scenes.yaml` (copy C6.2 exactly) |
| create | `pipeline/config.py` |
| create | `pipeline/run_stage.py` |
| create | `pipeline/cli.py`, `pipeline/__main__.py` |
| create | `tests/test_config.py`, `tests/test_run_stage.py` |

## Provenance
All NEW.

## Interface
```python
# pipeline/config.py
REPO: Path                                     # repo root = Path(__file__).resolve().parents[1]
def repo_root() -> Path: ...
def load_config() -> dict: ...                 # pipeline.yaml + cfg["scenes"] from scenes.yaml
def scenes_root(cfg: dict | None = None) -> Path: ...    # PS_SCENES_DIR overrides paths.scenes
def results_root(cfg: dict | None = None) -> Path: ...   # PS_RESULTS_DIR overrides paths.results
def validate_scene_id(scene_id: str) -> str: ...         # regex ^[a-z0-9_]{1,40}$ else ValueError
def scene_dir(scene_id: str, cfg: dict | None = None) -> Path: ...

# pipeline/run_stage.py
def git_sha() -> str: ...                      # `git rev-parse --short HEAD` in REPO, "unknown" on error
def vram_used_mb() -> int | None: ...          # nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 0
def run_stage(scene_id: str, stage: str, cmd: list[str], cwd: Path | None = None,
              variant: str | None = None, seed: int | None = None, saga: bool = False) -> dict: ...
```
CLI: `python -m pipeline info` prints the repo root, the scenes root, the scene ids found in `configs/scenes.yaml`, whether `nvidia-smi` exists, and the git SHA.

## Steps
1. Copy C6.1 into `configs/pipeline.yaml` and C6.2 into `configs/scenes.yaml`, exactly.
2. `config.py` as in the interface. `load_config` reads both files with `yaml.safe_load`.
3. `run_stage`:
   1. `cmd` = list of strings; `str()` every element.
   2. If `saga` and `cfg["envs"]["saga"]`: `cmd = ["conda", "run", "--no-capture-output", "-n", env] + cmd`.
   3. `baseline = vram_used_mb()`. Start a daemon thread that polls `vram_used_mb()` every 0.5 s until an `Event` is set, keeping the max.
   4. `t0 = time.time()`; `proc = subprocess.run(cmd, cwd=cwd)` (no capture: output goes to the terminal).
   5. Stop the thread and build the C15 record, including `started_utc` (ISO format, UTC) and `git_sha()`.
   6. Append it to `scene_dir(scene_id)/"logs"/"stages.jsonl"` (create the folders).
   7. If `proc.returncode != 0`, raise `RuntimeError(f"stage {stage} failed with code {rc}: {' '.join(cmd)}")` **after** logging.
4. `cli.py`: an `argparse` parser with `add_subparsers(dest="command", required=True)` and one `info` subcommand. Each subcommand sets `func=`. `main(argv=None) -> int` returns `args.func(args) or 0`. Leave a comment `# Stage cards add their subcommands below.`
5. `__main__.py`: `from pipeline.cli import main` then `raise SystemExit(main())`.

## Gotchas
- `vram_used_mb()` must never raise. Return `None` when `nvidia-smi` is missing or fails.
- Don't import torch here (it isn't needed and it slows the CLI down).

## Tests
- `test_config.py`:
  - `load_config()` has the keys `paths, envs, gsplat, masks, saga, query, scenes`;
  - `validate_scene_id("../x")` raises;
  - with `PS_SCENES_DIR=tmp`, `scene_dir("abc") == tmp/"abc"`.
- `test_run_stage.py` (monkeypatch `PS_SCENES_DIR` to `tmp_path`):
  - `run_stage("s1", "hello", [sys.executable, "-c", "print('hi')"])` returns a dict with `returncode == 0`, `seconds >= 0`, and adds one line to `tmp/s1/logs/stages.jsonl`;
  - a failing command (`sys.exit(3)`) raises `RuntimeError` **and** is still logged with `returncode == 3`.

## Laptop check
```bash
source .venv/bin/activate && pytest -q tests/test_config.py tests/test_run_stage.py tests/test_imports.py && python -m pipeline info
```

## Lab check
```bash
cd ~/nvs && git pull && conda activate ps && python -m pipeline info
python -c "from pipeline.run_stage import vram_used_mb; print(vram_used_mb())"
```
Expected: `info` lists 4 scenes and nvidia-smi found; the VRAM value is an integer.

## Done when
- [ ] Tests pass on the laptop; `info` works on both machines

## Findings / Blockers
