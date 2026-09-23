#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p checkpoints
wget -nc -P checkpoints https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
wget -nc -P checkpoints https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt
source "$HOME/miniforge3/etc/profile.d/conda.sh" && conda activate ps
python -c "import open_clip; open_clip.create_model_and_transforms('ViT-B-16', pretrained='laion2b_s34b_b88k'); print('CLIP cached')"
ls -lh checkpoints
