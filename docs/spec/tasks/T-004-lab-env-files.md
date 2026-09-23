# T-004 — Lab environment files: conda env `ps`, COLMAP env, checkpoints

| Field | Value |
|---|---|
| Tier | [S] (you run the scripts on the lab PC) |
| Depends on | T-001, T-003 |
| Requirements | NFR-4 |
| May edit 06-contracts.md | no |

## Goal
One script creates the lab conda env `ps` (PyTorch 2.9.1 + CUDA 12.8, gsplat fork, SAM 2, SAM v1, OpenCLIP, …) and the separate `colmap` env. Another downloads the model checkpoints. Exact versions are frozen into lock files.

## Background
- **gsplat is built from our fork** (`pip install -e third_party/gsplat`), because we patch its `examples/`. Its CUDA code compiles against the installed PyTorch; `TORCH_CUDA_ARCH_LIST=8.6` (A4000) keeps the compile short.
- **COLMAP gets its own env**, so its CUDA libraries never clash with PyTorch's.
- **SAM 2 must come from GitHub**: the PyPI package called `sam2` is someone else's.
- **SAGA's CUDA extensions are not built here.** T-005 (the port spike) adds them to `setup_lab.sh`.

## Read first
1. `docs/spec/04-architecture-and-env.md` §6.3–§6.4
2. `docs/spec/05-codebase-map.md` §2
3. Upstream: `third_party/gsplat/examples/requirements.txt` (look at what it pins)

## Files
| Action | Path |
|---|---|
| create | `env/lab.yml` |
| create | `scripts/setup_lab.sh` |
| create | `scripts/download_checkpoints.sh` |

## Provenance
NEW. Checkpoint URLs are from the segment-anything README and sam2 `checkpoints/download_ckpts.sh`.

## Steps
1. `env/lab.yml` (conda handles only Python and non-Python tools; pip does the rest):
   ```yaml
   name: ps
   channels: [conda-forge]
   dependencies:
     - python=3.10
     - pip
     - ffmpeg
     - nodejs=22
   ```
2. `scripts/setup_lab.sh` (idempotent; `set -euo pipefail`):
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   cd "$(dirname "$0")/.."
   source "$HOME/miniforge3/etc/profile.d/conda.sh"
   conda env create -f env/lab.yml 2>/dev/null || conda env update -f env/lab.yml
   conda activate ps
   export TORCH_CUDA_ARCH_LIST="8.6"
   pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu128
   pip install -r third_party/gsplat/examples/requirements.txt      # VERIFY it keeps torch 2.9.1 (it pins it on main)
   pip install --no-build-isolation -e third_party/gsplat           # compiles gsplat CUDA (several minutes)
   pip install "git+https://github.com/facebookresearch/sam2.git"   # then pin: replace with @<sha> after first success
   pip install "git+https://github.com/facebookresearch/segment-anything.git"
   pip install open_clip_torch pycolmap hdbscan scikit-learn scipy plyfile opencv-python-headless \
               pyyaml fastapi "uvicorn[standard]" httpx pytest gdown joblib huggingface_hub
   # COLMAP in its own env (CUDA build from conda-forge; VERIFY `colmap -h` mentions CUDA)
   conda env list | grep -q '^colmap ' || conda create -y -n colmap -c conda-forge "colmap=4.2"
   python - <<'EOF'
   import torch, gsplat, sam2, segment_anything, open_clip
   print("torch", torch.__version__, "| cuda", torch.version.cuda, "| gpu", torch.cuda.get_device_name(0))
   print("gsplat", gsplat.__version__)
   EOF
   "$HOME/miniforge3/envs/colmap/bin/colmap" -h | head -3
   ```
3. `scripts/download_checkpoints.sh`:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   cd "$(dirname "$0")/.."
   mkdir -p checkpoints
   wget -nc -P checkpoints https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
   wget -nc -P checkpoints https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt
   source "$HOME/miniforge3/etc/profile.d/conda.sh" && conda activate ps
   python -c "import open_clip; open_clip.create_model_and_transforms('ViT-B-16', pretrained='laion2b_s34b_b88k'); print('CLIP cached')"
   ls -lh checkpoints
   ```

## Gotchas
- If the gsplat build fails with a CUDA version mismatch, `nvcc --version` must say 12.8 (T-003).
- SAM 2's optional CUDA extension may fail to build. That's allowed: SAM 2 then skips a post-processing step. Note it in Findings.
- **Never** `pip install sam2` from PyPI.

## Laptop check
```bash
bash -n scripts/setup_lab.sh && bash -n scripts/download_checkpoints.sh && echo syntax-ok
```

## Lab check
```bash
cd ~/nvs && git pull --recurse-submodules
bash scripts/setup_lab.sh 2>&1 | tail -20
bash scripts/download_checkpoints.sh
conda activate ps
pip freeze > env/lab-lock.txt
conda env export -n colmap > env/colmap-lock.yml
git add env/lab-lock.txt env/colmap-lock.yml && git commit -m "[CFG]: Add lab env lock files" && git push
```
Expected:
- `torch 2.9.1+cu128 | cuda 12.8 | gpu NVIDIA RTX A4000`;
- the gsplat version prints;
- COLMAP prints its header;
- the checkpoints are 2.4 GB (SAM) and about 0.9 GB (SAM 2.1 L);
- "CLIP cached".

Also record the sam2 / segment-anything / open_clip versions and SHAs in `THIRD_PARTY.md`.

## Done when
- [ ] Both scripts work on the lab PC; lock files committed; `THIRD_PARTY.md` updated

## Findings / Blockers
