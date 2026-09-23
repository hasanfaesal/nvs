# T-002 — Code skeleton, laptop environment, test runner

| Field | Value |
|---|---|
| Tier | [S] |
| Depends on | T-001 |
| Requirements | NFR-6, NFR-8, NFR-12 |
| May edit 06-contracts.md | no |

## Goal
The Python package folders exist, the laptop has a CPU-only virtual environment, `pytest` runs, and `.gitignore` keeps big files out of git.

## Background
The laptop has **no GPU** and only ~17 GB of free disk, so:
- the laptop environment installs **CPU-only PyTorch** from PyTorch's CPU index. The default PyPI torch pulls several GB of CUDA libraries.
- GPU libraries (gsplat, SAM 2, …) are **not** installed on the laptop. That's why every module must import them lazily, inside functions.
- A guard test enforces this for all future modules automatically.

## Read first
1. `AGENTS.md` (repo root)
2. `docs/spec/06-contracts.md` §C1
3. `docs/spec/04-architecture-and-env.md` §5, §6.3

## Files
| Action | Path |
|---|---|
| create | `pyproject.toml` |
| create | `env/laptop-requirements.txt` |
| create | `scripts/setup_laptop.sh` |
| modify | `.gitignore` (append; keep the existing lines) |
| create | `pipeline/__init__.py`, `server/__init__.py`, `evaluation/__init__.py`, `experiments/__init__.py` (empty, or a one-line docstring) |
| create | `results/.gitkeep`, `tests/test_imports.py` |

## Provenance
All NEW (project scaffolding).

## Steps
1. `pyproject.toml`:
   ```toml
   [project]
   name = "promptsplat"
   version = "0.1.0"
   requires-python = ">=3.10"

   [tool.pytest.ini_options]
   pythonpath = ["."]
   testpaths = ["tests"]
   addopts = "-q"
   ```
2. `env/laptop-requirements.txt` (torch is **not** listed here; the setup script installs it from the CPU index):
   ```text
   numpy
   opencv-python-headless
   plyfile
   pyyaml
   fastapi
   uvicorn
   httpx
   pytest
   scikit-learn
   scipy
   pycolmap
   joblib
   ```
3. `scripts/setup_laptop.sh` (make it executable):
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   cd "$(dirname "$0")/.."
   uv venv --python 3.10 .venv
   source .venv/bin/activate
   uv pip install "torch==2.9.1" --index-url https://download.pytorch.org/whl/cpu
   uv pip install -r env/laptop-requirements.txt
   python -c "import torch, numpy, cv2, plyfile, fastapi; print('torch', torch.__version__, 'cuda:', torch.cuda.is_available())"
   ```
4. Append to `.gitignore`:
   ```text
   # Python
   .venv/
   __pycache__/
   *.pyc
   .pytest_cache/
   # Big local data — never commit (NFR-8)
   data/
   scenes/
   checkpoints/
   *.pt
   *.pth
   *.ply
   *.spz
   *.npy
   *.npz
   *.joblib
   # Web
   web/node_modules/
   web/.output/
   web/.nuxt/
   web/.data/
   ```
5. `tests/test_imports.py`, the guard that every module imports on the laptop **without** GPU libraries:
   ```python
   """Every module must import on the laptop without pulling GPU libraries (AGENTS.md rule 5)."""
   import importlib
   import pkgutil
   import sys

   GPU_MODULES = ("gsplat", "sam2", "segment_anything", "open_clip", "hdbscan")
   PACKAGES = ("pipeline", "server", "evaluation", "experiments")


   def test_all_modules_import_without_gpu_libs():
       for name in PACKAGES:
           pkg = importlib.import_module(name)
           for info in pkgutil.walk_packages(pkg.__path__, name + "."):
               if info.name.endswith("__main__"):
                   continue  # importing __main__ would run the CLI
               importlib.import_module(info.name)
       loaded = [m for m in GPU_MODULES if m in sys.modules]
       assert not loaded, f"GPU libraries imported at module level: {loaded}"
   ```

## Gotchas
- Don't add CUDA packages to the laptop requirements.
- `uv` is already installed on the laptop (`/usr/bin/uv`). Python 3.10 is downloaded by `uv venv --python 3.10` if it's missing.

## Laptop check
```bash
bash scripts/setup_laptop.sh
source .venv/bin/activate && pytest
du -sh .venv          # expect < 2 GB
```
Expected: `torch 2.9.1+cpu cuda: False`, `1 passed`.

## Lab check
None (the lab env is T-004).

## Done when
- [ ] Setup script works from scratch; `pytest` passes; `.venv` < 2 GB
- [ ] `git status` shows no `.venv` files after running it

## Findings / Blockers
- 2026-09-24 laptop check passed: `torch 2.9.1+cpu cuda: False`, `pytest` → `1 passed`, `.venv` = 1.3 GB, `git status` shows no `.venv` files.
- Resolved versions of note: pycolmap 4.2.0, scikit-learn 1.7.2, scipy 1.15.3, fastapi on starlette 1.7.0, pytest 9.1.1.
- ASSUMPTION: package `__init__.py` files each hold a one-line docstring (AGENTS.md §6 wants a docstring as the first line of each module).
