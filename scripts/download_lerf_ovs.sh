#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw && cd data/raw
if [ ! -d lerf_ovs ]; then
  if gdown 1QF1Po5p5DwTjFHu6tnTeYs_G0egMVmHt -O lerf_ovs.zip; then
    unzip -q lerf_ovs.zip && rm lerf_ovs.zip
  else
    echo "Google Drive download failed; using the Hugging Face mirror (unofficial)"
    hf download --repo-type dataset Qmh/lerf_ovs --local-dir lerf_ovs
  fi
fi
find lerf_ovs -maxdepth 2 -type d | sort
