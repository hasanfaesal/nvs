# T-005 — SAGA port spike: run SAGA in the modern env `ps` (timebox: 3 working days)

| Field | Value |
|---|---|
| Tier | **[M]** (the CUDA build errors need judgement; expect several lab round-trips) |
| Depends on | T-004, T-007 |
| Requirements | FR-B1, NFR-1 |
| May edit 06-contracts.md | no |

## Goal
Decide, with evidence, whether SAGA runs inside env `ps` (Python 3.10, PyTorch 2.9.1, CUDA 12.8):
- **PORT_OK:** the port patch P-SAGA-1 is committed in the fork and `setup_lab.sh` builds SAGA's extensions;
- **FALLBACK:** go to T-006.

Either way, write `docs/spec/port-report.md`.

## Background
SAGA pins Python 3.7 / PyTorch 1.12 / CUDA 11.6 (`environment.yml`). Modern PyTorch usually builds Inria-style rasterizers after two small fixes:
- add `#include <cstdint>` (newer GCC no longer includes it implicitly);
- rebuild from clean sources (SAGA commits old build artefacts).

SAGA also imports `pytorch3d` but only uses `knn_points` to find 16 nearest neighbours of **frozen** Gaussian positions. That can be replaced by scikit-learn's `NearestNeighbors`, computed once and cached. This spike runs **SAGA's own pipeline** (not ours) on one scene to prove the environment works before we depend on it.

## Read first
1. `docs/spec/05-codebase-map.md` §4.1 (P-SAGA-1)
2. `docs/spec/04-architecture-and-env.md` §7
3. Upstream (fork): `third_party/SegAnyGAussians/scene/gaussian_model_ff.py` (import at L13; `knn_points` near L326/347/380)
4. Upstream (fork): `third_party/SegAnyGAussians/environment.yml` and the `submodules/*/setup.py` files (module names)
5. Upstream (fork): `third_party/SegAnyGAussians/README.md` (v2 pipeline commands)

## Files (all inside the fork unless noted)
| Action | Path |
|---|---|
| modify | `third_party/SegAnyGAussians/submodules/*/cuda_rasterizer/rasterizer_impl.h` (3 rasterizers): add `#include <cstdint>` |
| delete (git rm) | committed build artefacts: `submodules/**/build/`, `submodules/**/*.egg-info/`, `**/*.so` |
| modify | `third_party/SegAnyGAussians/.gitignore` (ignore those artefacts) |
| modify | `third_party/SegAnyGAussians/scene/gaussian_model_ff.py`: replace `pytorch3d.ops.knn_points` |
| modify | `third_party/SegAnyGAussians/train_contrastive_feature.py`: remove the unused `import pytorch3d.ops` (L29) |
| modify | `third_party/SegAnyGAussians/.gitmodules`: SSH URLs → HTTPS |
| modify | `scripts/setup_lab.sh` (main repo): add the SAGA extension build (only if PORT_OK) |
| create | `docs/spec/port-report.md` (main repo) |

## Provenance
FORK patch **P-SAGA-1**. `knn_indices` is NEW (sklearn), a drop-in for the pytorch3d call.

## Steps
1. **Clean the artefacts** (in the fork, branch `promptsplat`):
   ```bash
   cd third_party/SegAnyGAussians && git checkout promptsplat
   git rm -r --cached --ignore-unmatch $(git ls-files | grep -E '(^|/)build/|\.egg-info/|\.so$')
   printf 'build/\n*.egg-info/\n*.so\n' >> .gitignore
   ```
2. **`#include <cstdint>`** as the first include line of each `submodules/diff-gaussian-rasterization*/cuda_rasterizer/rasterizer_impl.h`.
3. **KNN replacement.** In `scene/gaussian_model_ff.py`, add a module-level helper and replace each `pytorch3d.ops.knn_points(...)` call. **Keep the output shapes the call sites expect.** Read each call site: if it uses `.idx` with a leading batch dim `[1, N, K]`, return `idx[None]`.
   ```python
   _KNN_CACHE: dict = {}

   def knn_indices(xyz: "torch.Tensor", k: int) -> "torch.Tensor":
       """[N,k] long indices of the k nearest neighbours (incl. self), CPU KD-tree, cached (positions are frozen)."""
       key = (xyz.data_ptr(), xyz.shape[0], k)
       if key not in _KNN_CACHE:
           from sklearn.neighbors import NearestNeighbors
           pts = xyz.detach().float().cpu().numpy()
           idx = NearestNeighbors(n_neighbors=k).fit(pts).kneighbors(pts, return_distance=False)
           _KNN_CACHE[key] = torch.from_numpy(idx).to(xyz.device)
       return _KNN_CACHE[key]
   ```
   Delete `import pytorch3d.ops` (L13 here, L29 in `train_contrastive_feature.py`).
4. **`.gitmodules`:** replace `git@github.com:` with `https://github.com/`.
5. **Commit + push the fork** (AGENTS.md §7), then bump the submodule in the main repo.
6. **Build on the lab** (you):
   ```bash
   conda activate ps && export TORCH_CUDA_ARCH_LIST=8.6 && cd ~/nvs/third_party/SegAnyGAussians
   for d in submodules/diff-gaussian-rasterization submodules/diff-gaussian-rasterization_contrastive_f \
            submodules/diff-gaussian-rasterization-depth submodules/simple-knn; do
     pip install --no-build-isolation "$d" || break
   done
   pip install -e third_party/segment-anything 2>/dev/null || true      # SAGA's vendored SAM (already installed from git in T-004)
   python -c "import diff_gaussian_rasterization, simple_knn; print('ok')"   # VERIFY the other two module names from their setup.py
   ```
   Paste any compile error back to the model (Prompt B).
7. **Run SAGA's own pipeline on figurines** in a scratch dir, so raw data is never modified. Use the README's v2 commands; VERIFY the flag names in each script's argparse.
   ```bash
   mkdir -p ~/spike/figurines && cd ~/spike/figurines
   ln -sfn ~/nvs/data/raw/lerf_ovs/figurines/images images && ln -sfn ~/nvs/data/raw/lerf_ovs/figurines/sparse sparse
   cd ~/nvs/third_party/SegAnyGAussians
   python train_scene.py -s ~/spike/figurines -m ~/spike/figurines_out --iterations 7000
   python extract_segment_everything_masks.py --image_root ~/spike/figurines \
          --sam_checkpoint_path ~/nvs/checkpoints/sam_vit_h_4b8939.pth --downsample 4 --downsample_type mask
   python get_scale.py --image_root ~/spike/figurines --model_path ~/spike/figurines_out
   python train_contrastive_feature.py -m ~/spike/figurines_out --iterations 2000 --num_sampled_rays 1000
   ```
   In another tmux pane, record the peak VRAM of each step: `nvidia-smi --query-gpu=memory.used --format=csv -l 1`.
   - If `train_scene.py` writes `point_cloud.ply` instead of `scene_point_cloud.ply`, or `--iterations 7000` isn't accepted, note it in Findings.
   - The 7000 iterations only prove the pipeline runs. Our real RGB model comes from gsplat.
8. **Point-query sanity:** a ≤ 30-line script (in the report, not committed as code). It loads `contrastive_feature_point_cloud.ply` (`f_0..f_31`) with `plyfile`, takes the feature of one Gaussian near the scene center as the query, computes the cosine similarity to all features, and prints how many Gaussians have cos > 0.75. **Sane:** between 0.1% and 30% of N.
9. **Decide and write `docs/spec/port-report.md`:**
   ```markdown
   # SAGA port report (T-005)
   Decision: PORT_OK | FALLBACK      Date:      Fork SHA:
   ## Environment   (python, torch, CUDA, gcc)
   ## Build         (each extension: ok/error + fix applied)
   ## Pipeline run  (each step: ok/error, wall time, peak VRAM)
   ## Query sanity  (N, selected count)
   ## Deviations from upstream behaviour (if any)
   ## If FALLBACK: why, and what T-006 must do
   ```
10. **If PORT_OK:** append the step 6 build loop to `scripts/setup_lab.sh`.

## Gotchas
- **Timebox:** stop after 3 working days of attempts and choose FALLBACK. Do not keep patching SAGA internals.
- Build one extension at a time. Its error message tells you which one failed.
- Never commit anything under `~/spike`.

## Laptop check
```bash
cd third_party/SegAnyGAussians && python -m py_compile scene/gaussian_model_ff.py train_contrastive_feature.py && \
  ! grep -n "pytorch3d" scene/gaussian_model_ff.py train_contrastive_feature.py && echo ok
```

## Lab check
Steps 6–8 above. Expected: every step completes, every VRAM peak is < 14 GB, the query sanity check passes.

## Done when
- [ ] `port-report.md` committed with a decision
- [ ] PORT_OK: fork patch pushed, submodule bumped, `setup_lab.sh` builds SAGA
- [ ] FALLBACK: T-006 set to `todo` in `tasks/README.md`

## Findings / Blockers
