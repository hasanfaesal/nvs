# 06 — Contracts (frozen interfaces)

This file defines every shared interface: folder layouts, file formats, config keys, coordinate conventions, the HTTP API and result files. Task cards cite its sections as **C1–C16**.

**Rules**
- If code and this file disagree, this file wins.
- Only a task whose card says "may edit 06-contracts.md" can change it. That task changes this file first, then the code, in the same commit.
- All paths are relative to the repo root.
- "Laptop" is the Arch Linux laptop with no GPU. "Lab" is the lab PC running WSL2 Ubuntu with the RTX A4000.

---

## C1. Repository layout

```text
nvs/                                   # repo root (laptop: ~/code3/gsp, lab: ~/nvs)
├── AGENTS.md  CLAUDE.md  .cursor/rules/promptsplat.mdc   # rules for coding models
├── THIRD_PARTY.md                     # upstream repos, pinned SHAs, licenses (T-001)
├── pyproject.toml                     # pytest config, package list (T-002)
├── env/
│   ├── laptop-requirements.txt        # CPU-only Python deps (T-002)
│   ├── lab.yml                        # conda env "ps" (T-004)
│   └── saga-legacy.yml                # only if the SAGA port fails (T-006)
├── configs/
│   ├── pipeline.yaml                  # all stage defaults (C6.1)
│   ├── scenes.yaml                    # scene registry (C6.2)
│   └── experiments.yaml               # run matrix (C6.3)
├── scripts/                           # setup_*.sh, download_*.sh, make_fixture_scene.py
├── third_party/                       # git submodules = our forks (T-001)
│   ├── SegAnyGAussians/               # fork of Jumpat/SegAnyGAussians (branch promptsplat, from v2)
│   ├── gsplat/                        # fork of nerfstudio-project/gsplat (branch promptsplat, from main)
│   └── AutoSeg-SAM2/                  # fork of zrporz/AutoSeg-SAM2 (branch promptsplat)
├── pipeline/                          # offline CLI package: python -m pipeline <cmd>
│   ├── __init__.py  __main__.py  cli.py  config.py  run_stage.py
│   ├── colmap_io.py  camera.py  plyio.py  render.py
│   ├── ingest.py  frames.py  colmap_run.py  split.py  train_3dgs.py  export_web.py
│   ├── saga_import.py  variant.py  masks_sam.py  masks_sam2_frame.py  masks_sam2_track.py
│   └── saga_stages.py  query_index.py
├── server/                            # FastAPI app + query engine
│   ├── __init__.py  app.py  query.py
├── evaluation/                        # NOT "eval/" (that name shadows Python's built-in eval)
│   ├── __init__.py  gt.py  metrics.py  eval_3d.py  baseline_2d.py  mrc.py  aggregate.py
├── experiments/run_matrix.py
├── tests/                             # CPU-only pytest files, synthetic data
├── web/                               # Nuxt 4 app (SPA)
├── checkpoints/                       # lab only, gitignored (SAM, SAM 2 weights)
├── data/raw/                          # gitignored: downloaded datasets, phone videos
├── scenes/                            # gitignored: processed scenes (C3)
├── results/                           # small JSON results (C14); committed
└── docs/                              # proposals (read-only) + this spec
```

---

## C2. Naming rules

| Thing | Rule | Example |
|---|---|---|
| `scene_id` | regex `^[a-z0-9_]{1,40}$`. `_fixture` is reserved for the laptop fixture scene. | `figurines`, `desk_01` |
| `variant_id` | one of `sam`, `sam2_frame`, `sam2_track_k{K}` (K = AutoSeg `--detect_stride`), stretch `sam2_track_k{K}_xview` | `sam2_track_k10` |
| seed dir | `seed{k}`, with k an integer from 0 to 9 | `seed0` |
| image name | file name inside `scenes/<id>/source/images/`, with extension | `frame_00041.jpg` |
| stem | image name without extension | `frame_00041` |
| frame order | Python `sorted()` of image names, which is capture order. Ingest guarantees zero-padded names. | |

Variant labels in the report and UI: `sam` = "V1 SAM (per-frame)", `sam2_frame` = "V2 SAM 2 (per-frame)", `sam2_track_k10` = "V3 SAM 2 (tracked)".

---

## C3. Scene directory layout

The "Producer" column gives the task that creates each item. Nothing under `scenes/` is committed to git.

```text
scenes/<scene_id>/
├── source/                                  # canonical input
│   ├── input/                               # raw frames before undistortion (video/images ingest only)  T-A15
│   ├── distorted/{database.db, sparse/0/}   # COLMAP work dir (video/images ingest only)              T-A14
│   ├── images/                              # UNDISTORTED RGB, PINHOLE camera, sorted = capture order  T-A02/T-A15
│   ├── sparse/0/{cameras,images,points3D}.bin                                                         T-A02/T-A14
│   └── labels/                              # GT JSON for held-out frames (evaluation only)           T-A02/T-C03
├── split.json                               # C4                                                       T-A03
├── 3dgs/                                    # gsplat result_dir                                        T-A05
│   ├── ckpts/ckpt_<step>_rank0.pt
│   ├── ply/point_cloud_<step>.ply
│   └── stats/val_step<step>.json            # psnr, ssim, lpips, num_GS, ...
├── web/
│   ├── scene.ply                            # web asset, Inria PLY layout, row i == Gaussian i (C11)   T-A07
│   └── manifest.json                        # C5                                                       T-A07
├── saga_scene/                              # imported RGB model shared by all variants                T-B02
│   └── point_cloud/iteration_30000/scene_point_cloud.ply   (same bytes as web/scene.ply)
├── variants/<variant_id>/                   # one SAGA "source dir" per mask source                    T-B03
│   ├── images/<name>  -> symlink to ../../source/images/<name>   (TRAIN images only!)
│   ├── sparse         -> symlink to ../../source/sparse
│   ├── sam_masks/<stem>.pt                  # C7                                                        T-B04/B05/B07
│   ├── mask_scales/<stem>.pt                # C7                                                        T-B08
│   ├── clip_features/<stem>.pt              # C7                                                        T-B08
│   ├── track_ids/<stem>.json                # C7, sam2_track_* only                                    T-B07
│   ├── autoseg_raw/                         # AutoSeg-SAM2 raw output, deletable                       T-B07
│   └── saga/seed<k>/                        # SAGA model dir, C8                                        T-B03/T-B08
│       ├── cfg_args
│       ├── point_cloud/iteration_30000  -> symlink to ../../../../saga_scene/point_cloud/iteration_30000
│       ├── point_cloud/iteration_10000/{contrastive_feature_point_cloud.ply, scale_gate.pt, q_trans.joblib}
│       └── query_index.pt                   # C9                                                        T-B11
└── logs/stages.jsonl                        # C15                                                       every stage
```

**Why the variant dirs exist.** SAGA's scripts read a fixed layout (`images/`, `sparse/`, `sam_masks/`, …) from one "source path".
- One variant dir per mask source lets SAGA run on the three sources without code changes.
- Because `images/` holds only train images, SAGA, SAM and SAM 2 never see test views. The split is enforced by the data, not by a flag.

---

## C4. `split.json`

Produced by `python -m pipeline split --scene <id>` (T-A03). Read by the gsplat fork patch (T-A04), the variant builder (T-B03) and the evaluation (T-E03).

```json
{
  "scene_id": "figurines",
  "every": 8,
  "train": ["frame_00002.jpg", "frame_00003.jpg"],
  "test": ["frame_00001.jpg", "frame_00009.jpg", "frame_00041.jpg"],
  "annotated": ["frame_00041.jpg"],
  "excluded": ["frame_00187.jpg"],
  "rule": "names = sorted(images) minus excluded; test = {names[i] : i % every == 0} ∪ annotated; train = names − test"
}
```

Rules:
- `train` and `test` are disjoint and sorted. `annotated ⊆ test`.
- **`annotated`** = image names that have a GT label file (stem match with `source/labels/*.json`). They are always test images (held-out protocol).
- **`excluded`** = cameras whose center is more than 10× the median distance from the median camera center. These are mis-registered frames; LERF-OVS figurines has at least one. They are in neither list.
- Training code must only use `train`. Only evaluation code may read `annotated` frames and labels.

---

## C5. `web/manifest.json`

Produced by `python -m pipeline export --scene <id>` (T-A07). Served through `GET /api/scenes/{id}` (C12).

```json
{
  "scene_id": "figurines",
  "title": "Figurines (LERF-OVS)",
  "dataset": "lerf_ovs",
  "num_gaussians": 1000000,
  "xyz_hash": "3f1c...e9",
  "asset": {"file": "scene.ply", "format": "ply", "bytes": 248000123},
  "initial_view": {
    "position": [0.1, -0.2, 3.0],
    "target": [0.0, 0.0, 0.0],
    "up": [0.0, 1.0, 0.0],
    "fov_y_deg": 52.3
  },
  "mesh_quaternion_xyzw": [1, 0, 0, 0],
  "metrics_3dgs": {"psnr": 27.1, "ssim": 0.91, "lpips": 0.12, "lpips_net": "alex", "num_test": 41, "step": 29999},
  "demo_queries": ["..."],
  "git_sha": "abc1234",
  "created_utc": "2026-10-01T12:00:00Z"
}
```

- `xyz_hash` is defined in C11. `initial_view` is defined in C10.4.
- `mesh_quaternion_xyzw` is always `[1,0,0,0]`, a 180° rotation about x (C10.3). The viewer applies it to the `SplatMesh`.
- `demo_queries` comes from `configs/scenes.yaml` (may be empty).

---

## C6. Config files

Loaded by `pipeline/config.py` (T-A01). Never hardcode these values in code. Read them from the config dict.

### C6.1 `configs/pipeline.yaml` (defaults; complete key list)

```yaml
paths:
  scenes: scenes
  data: data
  checkpoints: checkpoints
  results: results
envs:
  saga: null            # null = run SAGA scripts in the current env ("ps"); "saga" = conda run -n saga (T-006 fallback)
  colmap_bin: ~/miniforge3/envs/colmap/bin/colmap   # expanduser() before use; COLMAP lives in its own env (T-004)
split:
  every: 8
  outlier_factor: 10.0
frames:
  extract_fps: 6        # ffmpeg oversampling rate
  keep_every: 2         # keep the sharpest frame of each window of 2 -> ~3 fps
  min_sharpness_ratio: 0.3   # drop frames sharper than < 0.3 x median sharpness
  max_side: 1600        # resize long side (px) before COLMAP; gsplat then uses data_factor 1
  jpeg_quality: 95
colmap:
  camera_model: OPENCV
  matcher: sequential   # video; "exhaustive" for unordered photos
  mapper: mapper        # fallback: global_mapper
gsplat:
  data_factor: 1
  max_steps: 30000
  cap_max: 1000000
  sh_degree: 3
  lpips_net: alex
masks:
  downsample: 4         # all mask sources: segment at full res, resize masks by 1/4 (C7)
  sam_ckpt: checkpoints/sam_vit_h_4b8939.pth
  sam_arch: vit_h
  sam2_cfg: configs/sam2.1/sam2.1_hiera_l.yaml      # name inside the sam2 package
  sam2_ckpt: checkpoints/sam2.1_hiera_large.pt
  amg:                  # identical for SAM v1 and SAM 2 AMG (fairness)
    points_per_side: 32
    pred_iou_thresh: 0.88
    stability_score_thresh: 0.95
    box_nms_thresh: 0.7
    crop_n_layers: 0
    min_mask_region_area: 100
autoseg:
  levels: [large, middle]
  batch_size: 40
  dedup_iou: 0.5
saga:
  iterations: 10000
  num_sampled_rays: 1000
  feature_dim: 32
query_index:
  anchor_frac: 0.01
  identifier_thresh: 0.5
  hdbscan_min_cluster_size: 30
  hdbscan_epsilon: 0.25
  max_masks: 20000      # if more masks, use every 2nd frame (recorded in query_index params)
query:
  clip_model: ViT-B-16
  clip_pretrained: laion2b_s34b_b88k
  cluster_keep_thresh: 0.45
  text_threshold: 0.925   # = (0.85 + 1) / 2, SAGA notebook
  click_threshold: 0.875  # = (0.75 + 1) / 2, SAGA notebook
  render_max_side: 800
  default_scale: 0.5      # click granularity slider default (quantile)
server:
  host: 127.0.0.1
  port: 8000
  default_variant: sam2_track_k10
```

**Environment overrides (tests and laptop only):** `PS_SCENES_DIR` and `PS_RESULTS_DIR` replace `paths.scenes` and `paths.results` when set. `PS_FAKE=1` makes the server use the CPU fake engine (§6.4 of `08-phase-b.md`). These are the only environment variables the code reads.

### C6.2 `configs/scenes.yaml`

```yaml
scenes:
  figurines:
    title: Figurines (LERF-OVS)
    dataset: lerf_ovs
    input_type: colmap                 # colmap | images | video
    input: data/raw/lerf_ovs/figurines # VERIFY (T-007): exact folder names after unzip
    labels: data/raw/lerf_ovs/label/figurines
    demo_queries: []                   # filled at T-B17 from label categories
  ramen:        {title: Ramen (LERF-OVS), dataset: lerf_ovs, input_type: colmap, input: data/raw/lerf_ovs/ramen, labels: data/raw/lerf_ovs/label/ramen, demo_queries: []}
  waldo_kitchen: {title: Waldo kitchen (LERF-OVS), dataset: lerf_ovs, input_type: colmap, input: data/raw/lerf_ovs/waldo_kitchen, labels: data/raw/lerf_ovs/label/waldo_kitchen, demo_queries: []}
  teatime:      {title: Teatime (LERF-OVS), dataset: lerf_ovs, input_type: colmap, input: data/raw/lerf_ovs/teatime, labels: data/raw/lerf_ovs/label/teatime, demo_queries: []}
```

Custom scenes are added in T-C02 with `input_type: video` and `labels: data/raw/custom/<id>/labels` (labelme JSON).

### C6.3 `configs/experiments.yaml`

```yaml
scenes: [figurines, ramen, waldo_kitchen, teatime]    # + desk_01, shelf_01 after T-C04
core:
  variants: [sam, sam2_frame, sam2_track_k10]
  seeds: [0, 1, 2]
ablations:
  - {variant: sam2_track_k5,  seeds: [0]}
  - {variant: sam2_track_k20, seeds: [0]}
baseline_2d: true
mrc: true
stretch: []            # e.g. [{variant: sam2_track_k10_xview, seeds: [0,1,2]}] after T-S01
```

---

## C7. Mask files (one set per variant dir)

| File | dtype / shape | Meaning |
|---|---|---|
| `sam_masks/<stem>.pt` | `torch.bool`, `[M, h, w]`, `h = H // 4`, `w = W // 4` | M binary masks for this train frame. M may be 0 (shape `[0,h,w]`). Overlaps are allowed (parts and wholes). |
| `mask_scales/<stem>.pt` | `torch.float32`, `[M]` | 3D physical scale of each mask, from SAGA `get_scale.py` |
| `clip_features/<stem>.pt` | `torch.float16`, `[M, 512]` | CLIP image embedding of each mask crop, from SAGA `get_clip_features.py`. **Not** normalized. |
| `track_ids/<stem>.json` | `{"ids": [int, ...]}`, length M | global track ID of each mask, same order as `sam_masks`. Only for `sam2_track_*`. |

**Resolution rule (fairness).** Every source segments the full-resolution image. The masks are then resized to `(w, h) = (W // 4, H // 4)` with bilinear interpolation and thresholded at `>= 0.5`. This matches SAGA `extract_segment_everything_masks.py --downsample 4 --downsample_type mask`. T-B05 and T-B07 copy SAGA's resize code so the results are bit-identical in behaviour.

**Loading rule.** SAGA's own script saves CUDA tensors. Always load with `torch.load(path, map_location="cpu")`.

---

## C8. SAGA model directory (`variants/<v>/saga/seed<k>/`) and `cfg_args`

SAGA reads `<model_dir>/cfg_args` with Python `eval()`, so it must be exactly one line: the `repr` of an `argparse.Namespace`. The fields below are required. The last four are missing from vanilla 3DGS models, and SAGA crashes without them.

```text
Namespace(data_device='cuda', eval=False, images='images', model_path='/ABS/scenes/figurines/variants/sam/saga/seed0', resolution=-1, sh_degree=3, source_path='/ABS/scenes/figurines/variants/sam', white_background=False, feature_dim=32, allow_principle_point_shift=False, need_features=False, need_masks=False)
```

- Paths are **absolute** (lab paths). `scripts` must build them from `Path.resolve()`, never type them by hand.
- `point_cloud/iteration_30000` is a relative symlink to `saga_scene/point_cloud/iteration_30000`. SAGA picks the highest iteration folder containing a file with "scene" in its name, so the file must be named `scene_point_cloud.ply`.
- Training writes `point_cloud/iteration_10000/contrastive_feature_point_cloud.ply` (fields x,y,z,nx,ny,nz,f_0..f_31,opacity,scale_*,rot_*) plus `scale_gate.pt` (state_dict of `Sequential(Linear(1,32), Sigmoid())`). After the T-B01 patch it also writes `q_trans.joblib` (the fitted `sklearn.preprocessing.QuantileTransformer`).

---

## C9. `query_index.pt` (one per variant and seed)

A `torch.save`d dict, produced by T-B11 and read by the server (T-B12).

| Key | Type / shape | Meaning |
|---|---|---|
| `version` | int = 1 | |
| `num_gaussians`, `xyz_hash` | int, str | must equal the manifest (C11) |
| `frames` | list[str] | train stems in order |
| `mask_frame` | LongTensor `[T]` | index into `frames` for each mask (T = total masks used) |
| `mask_local` | LongTensor `[T]` | index of the mask inside its frame's `sam_masks` stack |
| `mask_cluster` | LongTensor `[T]` | HDBSCAN label, −1 = noise |
| `mask_clip` | HalfTensor `[T, 512]` | L2-normalized CLIP embedding |
| `mask_feat` | FloatTensor `[T, 32]` | L2-normalized SAGA mask feature at its own scale gate |
| `mask_scale` | FloatTensor `[T]` | raw 3D scale of the mask |
| `params` | dict | anchor_frac, identifier_thresh, hdbscan params, seed, frame_stride, SAGA iteration |

---

## C10. Coordinate conventions and camera math

All camera math lives in `pipeline/camera.py` (T-A06) and is unit-tested with the test vectors in C10.6. **Never re-derive it inline anywhere else. Import it.**

### C10.1 Frames of reference

| Frame | Axes | Notes |
|---|---|---|
| COLMAP / OpenCV camera | x right, y down, z forward | COLMAP stores world→camera: `X_cam = R·X_world + t` (R from `qvec` wxyz, t = `tvec`). Camera center `C = −Rᵀt`. |
| gsplat | same as COLMAP | `viewmats` = world→camera 4×4 `[[R,t],[0,0,0,1]]`. `Ks` = `[[fx,0,cx],[0,fy,cy],[0,0,1]]` in pixels at the render size. |
| PLY world | = COLMAP world | guaranteed by `normalize_world_space=False` (T-A05) and raw export (T-A07) |
| three.js camera | x right, y up, looks along −z | `camera.matrixWorld` = camera→world. `camera.fov` = vertical FOV in degrees. |
| three.js world | = `M_mesh · PLY world` | the `SplatMesh` has `quaternion (x,y,z,w) = (1,0,0,0)`, so `M_mesh = diag(1,−1,−1,1)` (180° about x). This is what Spark's docs call "re-orient from OpenCV to OpenGL". |

### C10.2 COLMAP camera → gsplat inputs

```python
R = qvec2rotmat(qvec)                         # 3x3
viewmat = [[R, t], [0, 0, 0, 1]]              # 4x4 world->camera
K = [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]     # PINHOLE params; scale fx,fy,cx,cy by s when rendering at s * size
```

### C10.3 Mesh rotation

`S = diag(1, −1, −1)`. A PLY point `p` is shown at three.js world point `S·p`.

### C10.4 Initial view (manifest `initial_view`), from the first train camera

```python
C   = -R.T @ t                  # camera center (PLY world)
fwd = R.T @ [0, 0, 1]           # viewing direction
up  = R.T @ [0, -1, 0]          # camera up (OpenCV -y)
m   = median of sparse points3D xyz
d   = max(0.1, dot(m - C, fwd)) # orbit distance = depth of scene median along the view ray
position = S @ C
target   = S @ (C + d * fwd)
up_three = S @ up
fov_y_deg = degrees(2 * atan(H / (2 * fy)))
```

The client sets `camera.position`, `camera.up`, `controls.target` and `camera.fov` from these values.

### C10.5 Browser camera → gsplat viewmat and K (click query, debug render)

Request fields: `camera.matrix_world` (16 floats, three.js `elements`, **column-major**), `mesh_matrix_world` (16 floats, column-major), `camera.fov_y_deg`, `camera.width`, `camera.height` (canvas CSS pixels), `pixel = [u, v]` (CSS pixels from the canvas's top-left).

```python
Mc = np.array(camera_matrix_world, float).reshape(4, 4).T   # column-major -> row-major
Mm = np.array(mesh_matrix_world, float).reshape(4, 4).T
C_gl = np.linalg.inv(Mm) @ Mc                 # camera->world in PLY frame, OpenGL camera axes
C_cv = C_gl @ np.diag([1, -1, -1, 1])         # flip camera y and z -> OpenCV axes
viewmat = np.linalg.inv(C_cv)                 # world->camera for gsplat
s = min(1.0, max_side / max(W, H)); w = round(W * s); h = round(H * s)
fy = 0.5 * h / tan(0.5 * radians(fov_y_deg)); fx = fy; cx = w / 2; cy = h / 2
px = min(w - 1, max(0, int(u * s))); py = min(h - 1, max(0, int(v * s)))
```

### C10.6 Test vectors (must pass in `tests/test_camera.py`)

1. **Identity mesh, three.js camera at the origin with default orientation.** `Mm = Mc = I`, W = H = 100, fov 90°.
   - PLY point `(0,0,−5)` projects to the center `(50, 50)`.
   - Point `(1,0,−5)` projects with `u > 50`.
   - Point `(0,1,−5)` projects with `v < 50` (up is up).
2. **Spark mesh, camera at three.js `(0,0,5)` looking at the origin.** `Mm = diag(1,−1,−1,1)`, `Mc` = translation `(0,0,5)`.
   - `viewmat` must equal `[[1,0,0,0],[0,1,0,0],[0,0,1,5],[0,0,0,1]]`.
   - PLY origin projects to the center.
   - PLY point `(0,−1,0)` projects with `v < center`.
3. **Round trip.** A COLMAP camera with `R = I, t = (0,0,5)` gives `initial_view.position = (0,0,5)`, `up = (0,1,0)`, and a target on the −z side of the position. Feeding that pose back through C10.5, with `Mm = diag(1,−1,−1,1)`, reproduces `viewmat = [[I, t]]`.

---

## C11. Gaussian index invariant

Row `i` is the same Gaussian in all of these:
1. the gsplat checkpoint `splats[*][i]`;
2. `web/scene.ply`;
3. `saga_scene/.../scene_point_cloud.ply` (same bytes as the web PLY);
4. every `contrastive_feature_point_cloud.ply`;
5. every `scores` array in the API.

How it is guarded:
- `xyz_hash = sha1(np.ascontiguousarray(xyz[:1000], dtype="<f4").tobytes()).hexdigest()`, where `xyz` is the `[N,3]` position array.
- Export (T-A07) writes `num_gaussians` + `xyz_hash` into the manifest.
- `query_index` (T-B11) and the server (T-B12) recompute both from the PLYs they load and **raise** on mismatch.
- NaN/Inf rows are neutralized, never dropped (T-A07). Nothing in the pipeline sorts, prunes or densifies after export. SAGA freezes geometry during feature training.

---

## C12. HTTP API (FastAPI, `server/app.py`)

- Base URL: lab `http://127.0.0.1:8000`, tailnet `https://<machine>.<tailnet>.ts.net` (through `tailscale serve`).
- All JSON. Validation errors return 422 (pydantic).

| Method, path | Task | Request | Response |
|---|---|---|---|
| `GET /api/health` | T-A08 | – | `{"ok": true, "gpu": bool, "fake": bool}` |
| `GET /api/scenes` | T-A08 | – | `[{"scene_id","title","num_gaussians","asset_url","metrics_3dgs","variants":[{"variant","seeds":[0,1,2]}]}]` |
| `GET /api/scenes/{scene_id}` | T-A08 | – | the manifest (C5) + `"asset_url"` + `"variants"` (same shape as above) |
| `GET /api/scenes/{scene_id}/asset` | T-A08 | – | `scene.ply` bytes (`application/octet-stream`) |
| `POST /api/scenes/{scene_id}/query/text` | T-B13 | `{"text": str (1–200 chars), "variant": str, "seed": int = 0}` | QueryResponse |
| `POST /api/scenes/{scene_id}/query/click` | T-B13 | `{"variant", "seed", "camera": {"matrix_world": [16], "fov_y_deg", "width", "height"}, "mesh_matrix_world": [16], "pixel": [u, v], "scale": float in [0,1]}` | QueryResponse |
| `POST /api/scenes/{scene_id}/debug/render` | T-B13 | `{"camera": {...}, "mesh_matrix_world": [16]}` | `image/png` RGB render at the fitted size (C10.5) |
| `GET /api/scenes/{scene_id}/frames` | T-B13 | – | `{"frames": [train stems in order]}` |
| `GET /api/scenes/{scene_id}/frames/{stem}/image` | T-B13 | – | `image/jpeg` (source image) |
| `GET /api/scenes/{scene_id}/frames/{stem}/labels/{variant}` | T-B13 | – | `image/png`: masks over the image. Colors: by track ID for `sam2_track_*` (same object, same color in every frame), by mask index otherwise. Drawn largest-first, alpha 0.5, white 1-px contours. |
| `GET /api/results` | T-B13 | – | contents of `results/summary.json` (C14.5), or 404 |
| `GET /api/results/file/{rel_path:path}` | T-E09 | – | a file under `results/` (e.g. `figurines/sam/renders_seed0/x.jpg`). The resolved path **must** stay inside `results/`, else 404. |
| `GET /` and any other non-`/api` path | T-A08 | – | the built Nuxt app. Unknown paths return `200.html` (SPA fallback). |

**QueryResponse**

```json
{
  "query_id": "sha1(scene|variant|seed|kind|payload)",
  "n": 1000000,
  "scores_b64": "<base64 of uint8[n]>",
  "default_threshold": 0.925,
  "info": {"kept_clusters": [{"cluster": 3, "score": 0.61}], "pixel_alpha": null},
  "latency_ms": 143.2,
  "cached": false
}
```

**Errors**

| Status | When |
|---|---|
| 404 | unknown `scene_id`, or `variant` / `seed` with no `query_index.pt` |
| 409 | click on background (rendered alpha at the pixel < 0.5) |
| 422 | invalid body |

**Validation (trust boundary):**
- `scene_id` must be in the discovered scene list; paths are never built from raw user strings.
- `stem` must be in the scene's frame list.
- `text` is stripped and 1–200 characters.
- `pixel` must lie inside `width × height`.
- `width`, `height` ≤ 8192.

---

## C13. Score encoding and thresholds

- `score = (cos + 1) / 2 ∈ [0, 1]`; `score_u8 = round(clip(score, 0, 1) * 255)`.
- The client selects Gaussian i iff `score_u8[i] >= round(t * 255)`, where t is the slider value.
- Defaults: text `t = 0.925` (cos 0.85), click `t = 0.875` (cos 0.75). Both come from SAGA's `prompt_segmenting.ipynb`.
- Evaluation uses exactly these defaults for every variant (no per-variant tuning).

---

## C14. Result files (`results/`, committed)

### C14.1 `results/<scene>/phase_a.json` (T-A07)

`{"scene_id", "psnr", "ssim", "lpips", "lpips_net", "num_test", "num_gaussians", "train_seconds", "train_peak_vram_mb", "asset_mb", "fps_lab": null, "git_sha"}`

`fps_lab` is filled in by hand at T-A16.

### C14.2 `results/<scene>/<variant>/seed<k>.json` (T-E03)

```json
{
  "scene_id": "figurines", "variant": "sam2_track_k10", "seed": 0,
  "threshold": 0.925,
  "per_query": [{"frame": "frame_00041", "query": "rubber duck", "iou": 0.71, "biou": 0.52, "loc_hit": true, "latency_ms": 45.0,
                 "iou_sweep": {"0.875": 0.66, "0.9": 0.69, "0.925": 0.71, "0.95": 0.70, "0.975": 0.61}}],
  "skipped": [{"frame": "frame_00105", "query": "...", "reason": "empty GT"}],
  "summary": {"miou": 0.63, "mbiou": 0.45, "loc_acc": 0.82, "n_queries": 17},
  "git_sha": "abc1234"
}
```

### C14.3 `results/<scene>/baseline_2d.json` (T-E04)

Same shape as C14.2, with `"variant": "baseline_2d"` and `"seed": null`.

### C14.4 `results/<scene>/<variant>/mrc.json` (T-E05)

`{"scene_id", "variant", "n_pairs_d1", "n_pairs_d3", "mrc_d1", "mrc_d3", "mrc", "masks_per_frame": float, "git_sha"}`

### C14.5 `results/summary.json` (T-E06)

```json
{
  "generated_utc": "...",
  "main": [{"scene": "figurines", "variant": "sam", "miou_mean": 0.5, "miou_std": 0.02, "mbiou_mean": 0.4, "mbiou_std": 0.01, "loc_acc_mean": 0.8, "loc_acc_std": 0.0, "n_seeds": 3, "mrc": 0.61}],
  "overall": [{"variant": "sam", "miou_mean": 0.5, "miou_std_across_scenes": 0.05, "mrc_mean": 0.6}],
  "ablation_k": [{"scene": "figurines", "k": 5, "miou": 0.6, "mrc": 0.8}],
  "baseline_2d": [{"scene": "figurines", "miou": 0.3, "mbiou": 0.2, "loc_acc": 0.7}],
  "phase_a": [{"scene": "figurines", "psnr": 27.1, "ssim": 0.91, "lpips": 0.12}],
  "systems": [{"scene": "figurines", "stage": "train_3dgs", "seconds": 1500, "peak_vram_mb": 9100}],
  "wilcoxon": [{"a": "sam2_track_k10", "b": "sam", "p_value": 0.03, "n": 68}]
}
```

### C14.6 `results/<scene>/latency.json` (T-B17 benchmark snippet)

`{"scene_id", "variant", "seed", "n_text": 20, "text_median_ms", "text_p90_ms", "n_click": 20, "click_median_ms", "click_p90_ms", "warm": true, "git_sha"}`

---

## C15. Stage log (`scenes/<id>/logs/stages.jsonl`)

`run_stage` (T-A01) appends one JSON object per line:

`{"stage": "train_3dgs", "variant": null, "seed": null, "cmd": [...], "seconds": 1512.3, "peak_vram_mb": 9120, "baseline_vram_mb": 850, "returncode": 0, "started_utc": "...", "git_sha": "..."}`

`peak_vram_mb` is the maximum of `nvidia-smi --query-gpu=memory.used` sampled every 0.5 s. It includes other processes, which is why the baseline measured before the stage starts is logged too. Both are `null` when `nvidia-smi` is missing (laptop).

---

## C16. CLI (`python -m pipeline <command>`)

| Command | Task | Effect |
|---|---|---|
| `info` | T-A01 | prints the repo root, the scenes root, configured scenes, whether `nvidia-smi` exists, and the git SHA |
| `ingest --scene ID (--colmap DIR \| --images DIR \| --video FILE) [--labels DIR] [--matcher sequential\|exhaustive]` | T-A02/T-A15 | builds `source/` |
| `split --scene ID` | T-A03 | writes `split.json` |
| `train3dgs --scene ID [--max-steps N]` | T-A05 | gsplat MCMC training |
| `export --scene ID` | T-A07 | `web/scene.ply`, `manifest.json`, `results/<id>/phase_a.json` |
| `saga-import --scene ID` | T-B02 | `saga_scene/` |
| `variant --scene ID --variant V [--seeds 0 1 2]` | T-B03 | variant dir + seed model dirs |
| `masks --scene ID --variant V` | T-B04/B05/B07 | dispatches on the variant prefix |
| `saga --scene ID --variant V --stage scale\|clip\|train [--seed K]` | T-B08 | SAGA stages |
| `index --scene ID --variant V --seed K` | T-B11 | `query_index.pt` |
| `all --scene ID --variant V --seeds 0 [1 2]` | T-B08 | runs every missing stage in order (skip-if-done) |

Every command:
- is idempotent: it skips work whose outputs exist unless `--force` is given;
- logs through `run_stage` when it launches a subprocess;
- exits non-zero on failure.

Evaluation and experiments use `python -m evaluation.<module> ...` and `python -m experiments.run_matrix ...` (see their cards).
