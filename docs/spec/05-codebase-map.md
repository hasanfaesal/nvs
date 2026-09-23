# 05 — Codebase map: where every file comes from

This project **builds on existing GitHub code wherever possible**. This document lists every file in the repo (layout in C1 of `06-contracts.md`) and says exactly where its code comes from:
- which upstream repo and file;
- what to copy;
- what to change;
- or, if nothing upstream fits, "write from scratch".

Line numbers were checked on 2026-09-23. They are **hints**: re-check them at the pinned SHA recorded in `THIRD_PARTY.md`.

---

## 1. Provenance types

| Type | Meaning | Rule |
|---|---|---|
| **FORK** | Upstream repo forked to `github.com/hasanfaesal/<repo>` and added as a git submodule in `third_party/`, branch `promptsplat` | Only 3 forks: SAGA, gsplat, AutoSeg-SAM2. Every change is a commit **inside the fork** (recipe in `AGENTS.md`), listed in the patch registry (section 4). |
| **PIP / NPM** | Upstream package used unmodified at a pinned version | Never edit site-packages or node_modules. Pins live in `env/*.yml`, `env/*.txt`, `web/package.json`. |
| **COPY** | A snippet of about 80 lines or fewer, copied into our file | The file must start with a `Source:` header (section 5). Keep the upstream names so a reader can diff against the original. |
| **WRAP** | Our thin Python calls an upstream script as a subprocess (through `run_stage`) | Our code only builds arguments and paths. The upstream script is unchanged, apart from fork patches. |
| **GENERATOR** | Created by an official scaffolding command, then edited | The card gives the exact command. |
| **NEW** | Written from scratch | Allowed only when no upstream code fits. The table says why. |

**Never copy from:**
- repos without a license, e.g. SAM2Object (you may read it for ideas);
- repos with non-commercial share-alike terms, e.g. DEVA (cite only).

---

## 2. Upstream repositories

`T-001` records the exact SHA of each repo in `THIRD_PARTY.md`.

| Name | URL | License | How we use it |
|---|---|---|---|
| SAGA (SegAnyGAussians) | https://github.com/Jumpat/SegAnyGAussians (default branch `v2`) | Apache-2.0. The files copied from 3DGS keep Inria's non-commercial research notice, which is fine for an FYP. | **FORK** |
| gsplat | https://github.com/nerfstudio-project/gsplat (pin a `main` commit; it uses the official PyPI `pycolmap`) | Apache-2.0 | **FORK** (library installed editable from the fork; `examples/` patched) |
| AutoSeg-SAM2 | https://github.com/zrporz/AutoSeg-SAM2 | MIT | **FORK** |
| SAM 2 / 2.1 | https://github.com/facebookresearch/sam2 | Apache-2.0 | **PIP** from git at a pinned SHA (the PyPI `sam2` is an unrelated fork, so don't use it) |
| Segment Anything v1 | https://github.com/facebookresearch/segment-anything | Apache-2.0 | **PIP** from git |
| OpenCLIP | https://github.com/mlfoundations/open_clip | MIT | **PIP** `open_clip_torch`, model `ViT-B-16` / `laion2b_s34b_b88k` |
| LangSplat | https://github.com/minghanqin/LangSplat | VERIFY (T-E01). If the license is unclear or restrictive, re-implement the ~30 lines from the description in `09-experiments-and-evaluation.md` instead of copying. | **COPY** (eval GT parsing, localization) |
| Gaussian Grouping | https://github.com/lkeab/gaussian-grouping | Apache-2.0 | **COPY** (`script/eval_lerf_mask.py`) |
| Segment-then-Splat | https://github.com/luyr/Segment-then-Splat | MIT | **COPY** (mask dedup) + read `third_party/AutoSeg-SAM2/autoseg.sh` as a usage example |
| Grounded-SAM-2 | https://github.com/IDEA-Research/Grounded-SAM-2 | Apache-2.0 | reference only: fallback design for tracking (`utils/mask_dictionary_model.py`) |
| Spark | https://github.com/sparkjsdev/spark (npm `@sparkjsdev/spark` 2.2.0) | MIT | **NPM** + **COPY** example code |
| three.js | https://github.com/mrdoob/three.js | MIT | **NPM** (version required by Spark) |
| Nuxt 4, Nuxt UI 4 | https://github.com/nuxt/nuxt, https://github.com/nuxt/ui | MIT | **GENERATOR** + NPM |
| FastAPI, Uvicorn | https://github.com/fastapi/fastapi | MIT / BSD | **PIP** |
| COLMAP 4.2 | https://github.com/colmap/colmap | BSD-3 | conda-forge binary in its own env `colmap` |
| pycolmap | https://pypi.org/project/pycolmap/ | BSD-3 | **PIP** (reading COLMAP models) |
| hdbscan | https://github.com/scikit-learn-contrib/hdbscan | BSD-3 | **PIP** (SAGA's text-query clustering) |
| plyfile | https://github.com/dranjan/python-plyfile | GPL-3.0 | **PIP** (PLY reading/writing; SAGA already needs it). OK for academic use. If the code is ever released under a permissive license, swap it for a small custom reader. |
| LERF / LERF-OVS data | https://www.lerf.io/ ; LangSplat README (LERF-OVS zip) | LERF: MIT. LERF-OVS annotations: VERIFY (T-007). | data only |

---

## 3. File-by-file map

The "Task" column links to the card in `tasks/` that creates the file.

### 3.1 Repo root, environments, scripts

| File | Type | Source → what to do | Task |
|---|---|---|---|
| `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/promptsplat.mdc` | NEW | Written together with this spec. They hold the rules for coding models. | – |
| `THIRD_PARTY.md` | NEW | Table: repo, fork URL, branch, pinned SHA, license, use. Filled by hand. | T-001 |
| `pyproject.toml` | NEW | `[tool.pytest.ini_options] pythonpath=["."] testpaths=["tests"]`, plus project name. No build backend needed. | T-002 |
| `env/laptop-requirements.txt` | NEW | CPU torch, numpy, opencv-python-headless, plyfile, pyyaml, fastapi, uvicorn, httpx, pytest, scikit-learn, scipy, pycolmap | T-002 |
| `env/lab.yml` | NEW | conda env `ps`. The torch version follows gsplat's `examples/requirements.txt` (torch 2.9.1). | T-004 |
| `env/saga-legacy.yml` | COPY+adapt | SAGA `environment.yml`, adding `pytorch3d` and `scikit-learn`. Used only if T-005 fails. | T-006 |
| `configs/pipeline.yaml`, `configs/scenes.yaml` | NEW | exactly C6.1 / C6.2 | T-A01 |
| `configs/experiments.yaml` | NEW | exactly C6.3 | T-E07 |
| `scripts/setup_laptop.sh` | NEW | `uv venv --python 3.10 .venv` + `uv pip install -r env/laptop-requirements.txt` (CPU torch index) | T-002 |
| `scripts/setup_lab.sh` | NEW | creates the conda envs `ps` and `colmap`, installs the forks editable, SAM 2 and SAM from git | T-004 |
| `scripts/download_checkpoints.sh` | NEW | URLs from the SAM README (`sam_vit_h_4b8939.pth`) and sam2 `checkpoints/download_ckpts.sh` (`sam2.1_hiera_large.pt`) | T-004 |
| `scripts/download_lerf_ovs.sh` | NEW | `gdown` of the LERF-OVS zip (Google Drive id from the LangSplat README); the Hugging Face mirror `Qmh/lerf_ovs` is the fallback | T-007 |
| `scripts/make_fixture_scene.py` | NEW | Synthetic scene for laptop development. Nothing upstream fits: it's glue for our own contracts. | T-A09 |

### 3.2 `pipeline/` (offline CLI)

| File | Type | Source → what to do | Task |
|---|---|---|---|
| `__init__.py`, `__main__.py` | NEW | `__main__` just calls `cli.main()` | T-A01 |
| `cli.py` | NEW | argparse subcommands (C16). Each stage task adds its own subcommand. | T-A01 + stage tasks |
| `config.py` | NEW | Loads the YAML into a dict; `repo_root()`, `scene_dir(id)`. About 30 lines. | T-A01 |
| `run_stage.py` | NEW | Subprocess plus an `nvidia-smi` polling thread writing C15. There is no upstream equivalent. | T-A01 |
| `colmap_io.py` | NEW (thin wrapper over **pycolmap**) | Reads `sparse/0` into `{name: (R, t, K, W, H)}` and the points' xyz. Handles pycolmap API differences (`cam_from_world` as property vs method) in one place. | T-A02 |
| `camera.py` | NEW | Pure numpy math from C10 (formulas given there). Tested with the C10.6 vectors. | T-A06 |
| `plyio.py` | NEW (uses **plyfile**) | `read_vertex(path, fields) -> dict[str, np.ndarray]`, `xyz_hash(xyz)` | T-A06 |
| `render.py` | NEW (uses **gsplat** `rasterization`) | Loads Gaussians from a PLY. `render_rgb`, `render_features` (N-D colors, `sh_degree=None`), `render_scalar`, `render_depth` (`render_mode="RGB+ED"`). Shared by server, query_index and evaluation. | T-B10 |
| `ingest.py` | NEW | Copies a posed COLMAP folder, or runs frames → COLMAP, into the canonical `source/` (C3) | T-A02, T-A15 |
| `frames.py` | NEW (ffmpeg + OpenCV) | `ffmpeg -vf fps=6`; keeps the sharpest frame (variance of `cv2.Laplacian`) per window of 2; drops frames below 0.3× the median sharpness | T-A13 |
| `colmap_run.py` | **COPY+adapt** | **SAGA `convert.py`** (identical to Inria 3DGS `convert.py`). Keep its 4 steps (`feature_extractor` → matcher → `mapper` → `image_undistorter`, then move files into `sparse/0`). Changes:<br>• COLMAP 4.x option names: `--FeatureExtraction.use_gpu 1`, `--FeatureMatching.use_gpu 1` (renamed in 3.13)<br>• `sequential_matcher` for video<br>• `global_mapper` fallback<br>• if the mapper makes several models, pick the one with the most registered images<br>• `QT_QPA_PLATFORM=offscreen` | T-A14 |
| `split.py` | NEW | Algorithm in C4 | T-A03 |
| `train_3dgs.py` | **WRAP** | **gsplat fork `examples/simple_trainer.py`**: `python simple_trainer.py mcmc --data_dir … --data_factor 1 --result_dir … --normalize_world_space False --strategy.cap-max 1000000 --save_ply --disable_viewer --split_file …` (flag style as in `examples/benchmarks/mcmc.sh`) | T-A05 |
| `export_web.py` | WRAP + NEW | **`gsplat.export_splats(..., format="ply")`**. First neutralize NaN/Inf rows (C11), because upstream drops them and that would break the index invariant. Also writes the manifest (C5) and `phase_a.json` (C14.1). | T-A07 |
| `saga_import.py` | NEW | Writes C8: the `scene_point_cloud.ply` (the export's PLY; the layout already matches Inria) and the `cfg_args` template. Nothing upstream converts gsplat → SAGA. | T-B02 |
| `variant.py` | NEW | Builds the variant dir with symlinks (C3). T-B04 adds `masks_done()`, `check_masks()` (validates any variant's masks against C7) and `run_masks()` (the dispatcher used by the CLI and by `all`). | T-B03, T-B04 |
| `masks_sam.py` | **WRAP** | **SAGA fork `extract_segment_everything_masks.py --image_root <variant> --sam_checkpoint_path … --sam_arch vit_h --downsample 4 --downsample_type mask`** | T-B04 |
| `masks_sam2_frame.py` | **COPY+adapt** | **SAGA `extract_segment_everything_masks.py`**: copy its loop and its mask-resize code. Replace `SamAutomaticMaskGenerator` with **sam2 `sam2/automatic_mask_generator.py::SAM2AutomaticMaskGenerator`** (model from `sam2.build_sam.build_sam2(cfg, ckpt, apply_postprocessing=False)`, as in sam2 `notebooks/automatic_mask_generator_example.ipynb`), with the same thresholds as SAM v1 (C6.1 `masks.amg`). | T-B05 |
| `masks_sam2_track.py` | **WRAP + COPY** | WRAP **AutoSeg-SAM2 fork `auto-mask-batch.py`** (flags as in Segment-then-Splat `third_party/AutoSeg-SAM2/autoseg.sh`: `--detect_stride K --batch_size 40`, levels large and middle, plus our `--detector sam2`). COPY **Segment-then-Splat `helpers/preprocess_mask.py::remove_overlapping_masks`** (track dedup at IoU > 0.5). NEW converter to C7 (resize code copied from SAGA as in `masks_sam2_frame.py`). | T-B07 |
| `saga_stages.py` | **WRAP** | **SAGA fork** `get_scale.py --image_root <variant> -m <seed0 dir>`; `get_clip_features.py --image_root <variant>`; `train_contrastive_feature.py -m <seed dir> -s <variant> --iterations 10000 --num_sampled_rays 1000 --seed K`. Always run with `cwd=third_party/SegAnyGAussians`, because its imports are relative to the repo root. | T-B08 |
| `query_index.py` | **COPY+adapt** | **SAGA `prompt_segmenting.ipynb` cells 41–50**: anchors, per-mask features, mask identifiers, IoU distance, HDBSCAN. Changes:<br>• seeded anchors<br>• features rendered by `pipeline/render.py` instead of SAGA's renderer, so everything runs in env `ps`<br>• output saved as C9 instead of notebook variables | T-B11 |

### 3.3 `server/`

| File | Type | Source → what to do | Task |
|---|---|---|---|
| `app.py` | NEW (**FastAPI**) | Endpoints in C12, `StaticFiles` for the built web app, SPA fallback to `200.html` | T-A08, T-B13 |
| `query.py` | NEW + **COPY** | Two engines with the same methods: `GpuEngine` and `FakeEngine` (laptop). COPY from **SAGA**:<br>• `clip_utils/__init__.py`: the 80-entry `default_template` list, and `get_scores_with_template` (negatives "object","things","stuff","texture"; score = min over negatives of `softmax(10·[pos,neg])[0]`)<br>• **`saga_gui.py::fetch_data`** (≈L572–688): the click formula `f = normalize(normalize(F)[y,x] ⊙ gate(s))`, `sim = normalize(pf ⊙ gate(s)) · f`<br>• notebook cells 50–53: the text query (clusters > 0.45, best mask per cluster → query)<br>**Fix while copying:** the notebook only uses `index=0` (the lowest cluster label, not the best cluster). We take the union (max) over all kept clusters. | T-B12 |

### 3.4 `evaluation/` (named so it doesn't shadow Python's `eval`)

| File | Type | Source → what to do | Task |
|---|---|---|---|
| `gt.py` | **COPY** + NEW | **LangSplat `eval/evaluate_iou_loc.py::eval_gt_lerfdata`**, plus `eval/utils.py::{polygon_to_mask, stack_mask}` for the LERF-OVS JSON (`info`, `objects[].category/segmentation/bbox`). NEW ~15-line parser for **labelme** JSON (`shapes[].label/points`), used for our own scenes. Both return the same `{category: (mask, [bboxes])}`. | T-E01 |
| `metrics.py` | **COPY** | **Gaussian Grouping `script/eval_lerf_mask.py::{calculate_iou, mask_to_boundary, boundary_iou}`** (dilation_ratio 0.02). **LangSplat `lerf_localization`** logic: 30×30 mean filter, argmax pixel, hit if inside any GT box. | T-E02 |
| `eval_3d.py` | NEW | For each annotated frame and query: engine text query → `render_scalar` at the test camera → metrics → C14.2 | T-E03 |
| `baseline_2d.py` | NEW + **COPY** | **segment-anything `SamAutomaticMaskGenerator`** (vit_h, C6.1 thresholds). The crop logic is COPIED from **SAGA `get_clip_features.py` / `clip_utils`** (black background, box crop, 224×224). Scoring is imported from `server/query.py`. | T-E04 |
| `mrc.py` | NEW | Mask reprojection consistency. The algorithm is in `09-experiments-and-evaluation.md` §5.4. No upstream implementation exists. | T-E05 |
| `aggregate.py` | NEW | Collects C14 files into `summary.json`; `scipy.stats.wilcoxon` for paired tests | T-E06 |
| `../experiments/run_matrix.py` | NEW | Reads C6.3 and calls the CLI commands in order; skip-if-done; `--dry-run` | T-E07 |

### 3.5 `web/` (Nuxt 4 SPA)

| File | Type | Source → what to do | Task |
|---|---|---|---|
| scaffold (`package.json`, `app/app.vue`, `nuxt.config.ts`, …) | **GENERATOR** | `npm create nuxt@latest web -- -t ui` (Nuxt UI starter template; VERIFY the exact command in the Nuxt UI docs at T-A10), then edit `nuxt.config.ts`: `ssr: false`, dev proxy `/api` → `http://127.0.0.1:8000` | T-A10 |
| `app/composables/useApi.ts` | NEW | typed `$fetch` wrappers for C12 | T-A10 |
| `app/pages/index.vue` | NEW | scene cards (Nuxt UI `UCard`) | T-A10 |
| `app/components/SplatViewer.client.vue` | **COPY+adapt** | **Spark `examples/hello-world/index.html`** (renderer, `SparkRenderer`, `SplatMesh`, animation loop) + **`examples/interactivity`** (three.js `OrbitControls`) + **`examples/nonlod`** (options with LoD off). Wrapped as a Vue client component: props `assetUrl`, `initialView`; emits `ready`, `pick`; exposes `getCameraState()` and `setColorsAndOpacities()`. | T-A11 |
| `app/pages/scene/[id].vue` | NEW | explorer: viewer + side panel (Phase A info; the Phase B query panel is added in T-B15) | T-A12, T-B15 |
| `app/utils/splatModes.ts` | NEW (pure TypeScript) | mode math (highlight, isolate, hide, transparent, recolor, heatmap), tested with vitest | T-B14 |
| `app/composables/useSplatEdits.ts` | **COPY+adapt** | **Spark `examples/splat-painter`**: per-splat RGBA through `mesh.splatRgba` + `updateGenerator()`. Fallback: **Spark `docs/splat-mesh.md` / `PackedSplats`** `forEachSplat` to cache the originals, then `setSplat(i, center, scales, quaternion, opacity, color)` + `packedSplats.needsUpdate = true`. VERIFY (T-B14): which API exists in 2.2.0. | T-B14 |
| `app/pages/labels/[id].vue` | NEW | pseudo-label viewer (3 columns of overlays from the API) | T-B16 |
| `app/pages/results.vue` | NEW | tables + inline-SVG bar charts from `/api/results` | T-E09 |
| `tests/splatModes.test.ts` | NEW (vitest) | unit tests for `splatModes.ts` | T-B14 |

### 3.6 `tests/` (CPU-only, laptop)

One file per non-trivial module, e.g. `tests/test_split.py` or `tests/test_camera.py`. Rules:
- synthetic data only;
- each file runs in under 10 s;
- no GPU;
- no downloads.

Each card names its test file.

---

## 4. Fork patch registry

Each patch is one or more commits on branch `promptsplat` in the fork, with a message starting with the task ID. Keep patches **small and surgical**. Never reformat upstream files.

### 4.1 SAGA (`third_party/SegAnyGAussians`)

| Patch | Task | Files (hint lines) | Change | Why |
|---|---|---|---|---|
| P-SAGA-1 port | T-005 | `submodules/*/cuda_rasterizer/rasterizer_impl.h`; committed `*.so`, `build/`, `*.egg-info`; `scene/gaussian_model_ff.py` (L13 import, knn uses ≈L326/347/380); `train_contrastive_feature.py:29`; `environment.yml`; `.gitmodules`; optional `saga_gui.py:552` | Add `#include <cstdint>`. Delete the committed build artefacts. Replace `pytorch3d.ops.knn_points` with cached `sklearn.neighbors.NearestNeighbors` indices (positions are frozen). Drop the unused pytorch3d import. Drop the `joblib==1.1.0` pin. Switch submodule URLs to HTTPS. `torch.eig` → `torch.linalg.eigh`. | run on Python 3.10 / PyTorch 2.9 in env `ps` |
| P-SAGA-2 split by files | T-B01 | `scene/dataset_readers.py::readColmapCameras` | Skip a camera if its image file doesn't exist (`os.path.exists` on the joined path; symlinks count), and print how many were skipped. | variant dirs hold only train images (C3) |
| P-SAGA-3 seed + q_trans | T-B01 | `train_contrastive_feature.py`, `utils/general_utils.py::safe_state` | Add `--seed` (default 0), pass it to `safe_state` / re-seed `random`, `numpy`, `torch`. Build the `QuantileTransformer` with `random_state=seed` and `joblib.dump` it as `point_cloud/iteration_<it>/q_trans.joblib`. | reproducible seeds; exact query parity (C8) |
| P-SAGA-4 mask extraction | T-B01 | `extract_segment_everything_masks.py` | Convert the image BGR→RGB before SAM (upstream feeds BGR). If an image has 0 masks, save `torch.zeros((0,h,w), dtype=torch.bool)` instead of crashing. Save on CPU. | correctness, fairness |
| P-SAGA-5 CLIP path | T-B01 | `clip_utils/clip_utils.py:14`, `clip_utils/__init__.py:170` | `pretrained="laion2b_s34b_b88k"` instead of the hardcoded `../sagav2/clip_ckpt/...` path. Remove the stray `plt.imshow`. | runs anywhere; headless |
| P-SAGA-6 cross-view (stretch) | T-S01 | `train_contrastive_feature.py` loss block (≈L145–295), `scene/dataset_readers.py` (load `track_ids`) | Add the optional cross-view term (`08-phase-b.md` §13) behind `--xview_weight` (default 0 = upstream behaviour). | stretch variant |

### 4.2 gsplat (`third_party/gsplat`)

| Patch | Task | Files (hint lines) | Change |
|---|---|---|---|
| P-GS-1 split file | T-A04 | `examples/datasets/colmap.py::Dataset.__init__` (split ≈ main L458–462), `examples/simple_trainer.py` (`Config` dataclass + both `Dataset(...)` calls) | Add `split_file: Optional[str] = None`. When set, the indices are the positions of the names in `json.load(split_file)[split]` within `parser.image_names`. Otherwise keep `test_every`. |

### 4.3 AutoSeg-SAM2 (`third_party/AutoSeg-SAM2`)

| Patch | Task | Files | Change |
|---|---|---|---|
| P-AS-1 SAM 2 detector | T-B06 | `auto-mask-batch.py` (+ the helper it uses to build the SAM v1 generator) | Add `--detector {sam1,sam2}` (default `sam1` = upstream). `sam2` builds `SAM2AutomaticMaskGenerator` with the C6.1 thresholds and keeps AutoSeg's `mask_nms` / `masks_update` / level logic. Decision rule: if the level logic can't be ported within 1 working day, stop, use `sam1`, and record this in `docs/spec/port-report.md`. |

---

## 5. Header format for COPY files

Python:

```python
# Source: https://github.com/lkeab/gaussian-grouping @ <sha from THIRD_PARTY.md>
#         script/eval_lerf_mask.py :: calculate_iou, mask_to_boundary, boundary_iou
# License: Apache-2.0. Changes: type hints; masks passed as numpy bool arrays.
```

TypeScript / Vue:

```ts
// Source: https://github.com/sparkjsdev/spark @ v2.2.0, examples/hello-world/index.html
// License: MIT. Changes: wrapped in a Vue component; LoD disabled; OrbitControls.
```

When one of our files mixes copied and new code, put the header above the copied block, and a `# --- end copied code ---` line after it.
