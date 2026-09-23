#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv venv --python 3.10 .venv
source .venv/bin/activate
uv pip install "torch==2.9.1" --index-url https://download.pytorch.org/whl/cpu
uv pip install -r env/laptop-requirements.txt
python -c "import torch, numpy, cv2, plyfile, fastapi; print('torch', torch.__version__, 'cuda:', torch.cuda.is_available())"
