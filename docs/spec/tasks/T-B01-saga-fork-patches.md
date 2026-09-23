# T-B01 — SAGA fork patches: split by files, seeds + saved quantile transform, RGB masks, CLIP path

| Field | Value |
|---|---|
| Tier | [S] (FORK-patch card: use the submodule recipe) |
| Depends on | T-005 |
| Requirements | FR-B3, FR-B7, NFR-5 |
| May edit 06-contracts.md | no |

## Goal
The four functional patches P-SAGA-2 … P-SAGA-5 (`05-codebase-map.md` §4.1) are committed on the SAGA fork's `promptsplat` branch, each minimal and surgical.

## Background
- **P-SAGA-2, split by files:** our variant dirs contain only train images (C3). SAGA's camera loader must skip cameras whose image file doesn't exist; otherwise it crashes on test views.
- **P-SAGA-3, seeds:** SAGA always seeds with 0 (`safe_state`), but we need seeds 0/1/2. SAGA also maps mask scales through a `QuantileTransformer` fitted at training time. We save it, so queries later use *exactly* the same mapping.
- **P-SAGA-4, masks:** SAGA feeds SAM a **BGR** image (OpenCV's default), and it crashes on images with no masks. We fix both, so all mask sources get identical treatment.
- **P-SAGA-5, CLIP:** the CLIP checkpoint path is hardcoded to the authors' machine, and a stray `plt.imshow` runs for every mask.

## Read first
1. `docs/spec/05-codebase-map.md` §4.1
2. Fork: `third_party/SegAnyGAussians/scene/dataset_readers.py`: `readColmapCameras` (≈ L100–150) and `readColmapSceneInfo` (≈ L149–180)
3. Fork: `third_party/SegAnyGAussians/train_contrastive_feature.py`: argparse, `get_quantile_func` (≈ L42), the save block (≈ L318–319); and `utils/general_utils.py::safe_state`
4. Fork: `third_party/SegAnyGAussians/extract_segment_everything_masks.py`
5. Fork: `third_party/SegAnyGAussians/clip_utils/clip_utils.py` (≈ L14) and `clip_utils/__init__.py` (≈ L170)

## Files (inside the fork)
| Action | Path |
|---|---|
| modify | `scene/dataset_readers.py` |
| modify | `train_contrastive_feature.py` |
| modify | `extract_segment_everything_masks.py` |
| modify | `clip_utils/clip_utils.py`, `clip_utils/__init__.py` |
| modify | submodule pointer in the main repo |

## Provenance
FORK patches P-SAGA-2 … P-SAGA-5. Keep each change as small as possible and don't reformat.

## Steps
1. `git -C third_party/SegAnyGAussians checkout promptsplat`
2. **P-SAGA-2.** In `readColmapCameras`, right after the image path is computed (before any image, mask or scale is loaded):
   ```python
   if not os.path.exists(image_path):
       skipped += 1
       continue
   ```
   Initialize `skipped = 0` before the loop, and after it add `print(f"[promptsplat] skipped {skipped} cameras without image files")`. Keep the variable names upstream uses; VERIFY them.
3. **P-SAGA-3:**
   - add `parser.add_argument("--seed", type=int, default=0)`;
   - right after the existing `safe_state(...)` call:
     `random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed); torch.cuda.manual_seed_all(args.seed)` (add the imports if missing);
   - in `get_quantile_func`, construct `QuantileTransformer(output_distribution="uniform", random_state=<seed>)`, passing the seed in as a parameter. Make the fitted transformer reachable where the scale gate is saved: e.g. return it alongside the function, or set `func.transformer = qt`. Choose the smallest change and describe it in Findings.
   - next to the `scale_gate.pt` save: `joblib.dump(<transformer>, os.path.join(<same dir>, "q_trans.joblib"))`.
4. **P-SAGA-4.** In `extract_segment_everything_masks.py`:
   - after `cv2.imread(...)`, add `img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)` before the generator sees it;
   - where the masks are stacked, if the list is empty, create `torch.zeros((0, h, w), dtype=torch.bool)` with the output `h, w` of that branch;
   - make sure the saved tensor is on the CPU (`.cpu()`).
5. **P-SAGA-5:**
   - in `clip_utils/clip_utils.py`, change the `pretrained=` argument to the string `"laion2b_s34b_b88k"` (open_clip downloads or caches it);
   - delete the `plt.imshow(...)` line (and any matching `plt.show()`) in `clip_utils/__init__.py`.
6. One commit per patch, messages `T-B01: P-SAGA-2 skip cameras without images` etc. Push the fork, then bump the submodule (AGENTS.md §7).
7. Add the rows to `05-codebase-map.md` §4.1 only if something differs from what's written there.

## Laptop check
```bash
cd third_party/SegAnyGAussians && python -m py_compile scene/dataset_readers.py train_contrastive_feature.py \
  extract_segment_everything_masks.py clip_utils/clip_utils.py clip_utils/__init__.py && \
grep -n "skipped" scene/dataset_readers.py && grep -n "q_trans.joblib\|--seed" train_contrastive_feature.py && \
grep -n "COLOR_BGR2RGB" extract_segment_everything_masks.py && grep -n "laion2b_s34b_b88k" clip_utils/clip_utils.py
```

## Lab check (uses the T-005 scratch scene `~/spike/figurines`, `~/spike/figurines_out`)
```bash
cd ~/nvs && git pull --recurse-submodules && conda activate ps && cd third_party/SegAnyGAussians
# P-SAGA-2: a dir with only 20 of the images
mkdir -p ~/spike/half/images && ln -sfn ~/spike/figurines/sparse ~/spike/half/sparse
ls ~/spike/figurines/images | head -20 | xargs -I{} ln -sfn ~/spike/figurines/images/{} ~/spike/half/images/{}
python -c "import sys; sys.path.insert(0,'.'); from scene.dataset_readers import readColmapSceneInfo; i=readColmapSceneInfo('$HOME/spike/half','images',False); print(len(i.train_cameras))"
# P-SAGA-4 + P-SAGA-5: masks and CLIP on the 20 images
python extract_segment_everything_masks.py --image_root ~/spike/half --sam_checkpoint_path ~/nvs/checkpoints/sam_vit_h_4b8939.pth --downsample 4 --downsample_type mask
MPLBACKEND=Agg python get_clip_features.py --image_root ~/spike/half
python -c "import torch,glob; f=sorted(glob.glob('$HOME/spike/half/sam_masks/*.pt'))[0]; m=torch.load(f,map_location='cpu'); print(m.dtype, m.device, m.shape)"
# P-SAGA-3: seeds + q_trans (200 iterations: run 1 and 2 with seed 1, run 3 with seed 2)
i=0; for s in 1 1 2; do i=$((i+1))
  python train_contrastive_feature.py -m ~/spike/figurines_out --iterations 200 --num_sampled_rays 1000 --seed ${s}
  cp ~/spike/figurines_out/point_cloud/iteration_200/scale_gate.pt /tmp/gate_run${i}_seed${s}.pt; done
ls ~/spike/figurines_out/point_cloud/iteration_200/
python -c "
import torch
a, b, c = (torch.load(f'/tmp/gate_run{i}.pt', map_location='cpu') for i in ['1_seed1', '2_seed1', '3_seed2'])
d = lambda x, y: max((x[k] - y[k]).abs().max().item() for k in x)
print('same seed max diff', d(a, b), '| different seed max diff', d(a, c))"
```
Expected:
- the number of train cameras is 20, and the "skipped" count equals the total minus 20;
- the masks are `torch.bool cpu [M, H/4, W/4]`;
- `clip_features/` exist and no plot windows open;
- `q_trans.joblib` exists.

For the seed check, compare the saved gates. Same seed: difference ≈ 0 (GPU nondeterminism may leave a tiny difference). Different seed: a clearly larger difference. Report both max-abs-diffs in Findings.

## Done when
- [ ] 4 patches pushed on `promptsplat`; submodule bumped; lab check as expected

## Findings / Blockers
