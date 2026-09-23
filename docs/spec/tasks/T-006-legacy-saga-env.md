# T-006 — Fallback: legacy conda env `saga` for SAGA scripts (only if T-005 = FALLBACK)

| Field | Value |
|---|---|
| Tier | [S] (you run it on the lab) |
| Depends on | T-005 (decision FALLBACK), T-A01 |
| Requirements | FR-B1 |
| May edit 06-contracts.md | no |

## Goal
SAGA's scripts run in a separate env `saga` (Python 3.7, PyTorch 1.12.1, CUDA 11.6). Our pipeline sends them there because `configs/pipeline.yaml` has `envs.saga: saga`.

## Background
`run_stage(..., saga=True)` (T-A01) prefixes SAGA commands with `conda run --no-capture-output -n saga` when `envs.saga` is set. Nothing else changes, because SAGA stages only exchange files with the rest of the pipeline (C7, C8).
- **No pytorch3d is needed:** the fork's P-SAGA-1 already replaced `knn_points` with scikit-learn.
- **The extensions must compile with nvcc 11.6** (not the system 12.8), so the env installs its own CUDA 11.6 toolkit.
- CUDA 11.6 needs GCC ≤ 11. Ubuntu 22.04 has GCC 11. On 24.04, `sudo apt install gcc-11 g++-11` and export `CC=gcc-11 CXX=g++-11`.

## Read first
1. `docs/spec/port-report.md` (why the port failed)
2. `third_party/SegAnyGAussians/environment.yml`
3. `docs/spec/04-architecture-and-env.md` §7

## Files
| Action | Path |
|---|---|
| create | `env/saga-legacy.yml` |
| modify | `scripts/setup_lab.sh`: add a `--legacy-saga` option that creates env `saga` and builds the extensions in it |
| modify | `configs/pipeline.yaml`: `envs.saga: saga` |

## Provenance
`env/saga-legacy.yml` is COPY + adapt of SAGA's `environment.yml`:
- keep Python 3.7.13 and PyTorch 1.12.1 with CUDA 11.6;
- add `scikit-learn=1.0.2`, `plyfile`, `hdbscan`, `open-clip-torch`;
- add the CUDA 11.6 toolkit (`nvidia/label/cuda-11.6.2::cuda-toolkit`; VERIFY the channel label);
- drop `pytorch3d`.

## Steps
1. Write `env/saga-legacy.yml` as above.
2. In `setup_lab.sh`, when `--legacy-saga` is passed:
   - `conda env create -f env/saga-legacy.yml`;
   - `conda activate saga`;
   - `export CUDA_HOME=$CONDA_PREFIX TORCH_CUDA_ARCH_LIST=8.6`;
   - build the 4 SAGA extensions with `pip install --no-build-isolation`;
   - `pip install -e third_party/SegAnyGAussians/third_party/segment-anything`.
3. Set `envs.saga: saga` in `configs/pipeline.yaml`.

## Laptop check
```bash
python -c "import yaml; yaml.safe_load(open('env/saga-legacy.yml')); print('ok')" && bash -n scripts/setup_lab.sh
```

## Lab check
```bash
bash scripts/setup_lab.sh --legacy-saga
conda run -n saga python -c "import torch, diff_gaussian_rasterization; print(torch.__version__, torch.cuda.is_available())"
```
Then re-run the T-005 step 7 pipeline with the same commands, prefixed by `conda run --no-capture-output -n saga`. Expected: every step completes.

## Done when
- [ ] SAGA's pipeline runs in env `saga`; `envs.saga: saga` is committed; `port-report.md` has a "Fallback result" section

## Findings / Blockers
