#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda env create -f env/lab.yml 2>/dev/null || conda env update -f env/lab.yml
conda activate ps
export TORCH_CUDA_ARCH_LIST="8.6"
pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu128
# pins torch==2.9.1 / torchvision==0.24.1; --no-build-isolation per gsplat README (fused-ssim etc. compile against our torch)
pip install --no-build-isolation -r third_party/gsplat/examples/requirements.txt
pip install --no-build-isolation -e third_party/gsplat           # compiles gsplat CUDA (several minutes)
pip install "git+https://github.com/facebookresearch/sam2.git"   # ponytail: unpinned; replace with @<sha> after first success
pip install "git+https://github.com/facebookresearch/segment-anything.git"
pip install open_clip_torch pycolmap hdbscan scikit-learn scipy plyfile opencv-python-headless \
            pyyaml fastapi "uvicorn[standard]" httpx pytest gdown joblib huggingface_hub
# COLMAP in its own env (CUDA build from conda-forge; VERIFY `colmap -h` mentions CUDA)
conda env list | grep -q '^colmap ' || conda create -y -n colmap -c conda-forge "colmap=4.2"
python - <<'PY'
import torch, gsplat, sam2, segment_anything, open_clip
print("torch", torch.__version__, "| cuda", torch.version.cuda, "| gpu", torch.cuda.get_device_name(0))
print("gsplat", gsplat.__version__)
PY
"$HOME/miniforge3/envs/colmap/bin/colmap" -h | head -3
